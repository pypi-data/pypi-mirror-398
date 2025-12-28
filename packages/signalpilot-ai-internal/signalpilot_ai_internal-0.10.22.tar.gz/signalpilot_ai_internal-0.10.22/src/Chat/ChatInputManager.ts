import { ChatHistoryManager } from './ChatHistoryManager';
import {
  ChatContextMenu,
  IMentionContext
} from './ChatContextMenu/ChatContextMenu';
import { Contents } from '@jupyterlab/services';
import { ToolService } from '../Services/ToolService';
import { RichTextChatInput } from './RichTextChatInput';
import { IChatService } from '../Services/IChatService';
import { ConversationService } from './ConversationService';
import { ChatMessages } from './ChatMessages';
import { ChatUIHelper } from './ChatUIHelper';
import { ChatboxContext } from '../Components/ChatboxContext';
import { ChatRequestStatus, IChatMessage, ICheckpoint } from '../types';
import { AppStateService } from '../AppState';
import { NotebookCellStateService } from '../Services/NotebookCellStateService';
import { convertMentionsToContextTags } from '../utils/contextTagUtils';
import {
  AGENT_MODE_ICON,
  AGENT_MODE_SHINY_ICON,
  ASK_ICON,
  HANDS_ON_MODE_ICON,
  OPEN_MODE_SELECTOR_ICON,
  SEND_ICON
} from '../Components/icons';
import { NotebookCellTools } from '../Notebook/NotebookCellTools';
import { checkTokenLimit, MAX_RECOMMENDED_TOKENS } from '../utils/tokenUtils';
import { ChatBoxWidget } from '../Components/chatbox';

/**
 * Input element type that supports both textarea and rich text input
 */
type ChatInputElement = HTMLTextAreaElement | RichTextChatInput;

/**
 * Manages chat input functionality and creates the complete input container
 */
export class ChatInputManager {
  private chatInput: ChatInputElement;
  private chatHistoryManager: ChatHistoryManager;
  private userMessageHistory: string[] = [];
  private historyPosition: number = -1;
  private unsavedInput: string = '';
  private mentionDropdown!: ChatContextMenu;

  // Add map to track all currently active mentions by context.id
  private activeContexts: Map<string, IMentionContext> = new Map();

  private onContextSelected: ((context: IMentionContext) => void) | null = null;
  private onContextRemoved: ((context_id: string) => void) | null = null;
  private onResetChat: (() => void) | null = null;

  // Dependencies for sendMessage and revertAndSend
  private chatBoxWidget: ChatBoxWidget;
  private chatService?: IChatService;
  private conversationService?: ConversationService;
  private messageComponent?: ChatMessages;
  private uiHelper?: ChatUIHelper;
  private contextHandler?: ChatboxContext;
  private sendButton?: HTMLButtonElement;
  private modeSelector?: HTMLElement;
  private tokenProgressWrapper?: HTMLElement;
  private tokenProgressCircle?: HTMLElement;
  private compressButton?: HTMLButtonElement;
  private modeName: 'agent' | 'ask' | 'fast' = 'agent';
  private isProcessingMessage: boolean = false;
  private checkpointToRestore: ICheckpoint | null = null;
  private cancelMessage?: () => void;
  private onMessageSent?: () => void;
  private onModeSelected?: (mode: 'agent' | 'ask' | 'fast') => void;

  // Input container elements
  private inputContainer?: HTMLElement;
  private chatboxWrapper?: HTMLElement;
  private contextRow?: HTMLElement;
  private inputRow?: HTMLElement;
  private contextDisplay?: HTMLElement;
  private modeSelectorDropdown?: HTMLElement;
  private addContextButton?: HTMLButtonElement;

  // Store dependencies for mention dropdown
  private contentManager: Contents.IManager;
  private toolService: ToolService;

  constructor(
    chatInput: ChatInputElement,
    chatHistoryManager: ChatHistoryManager,
    contentManager: Contents.IManager,
    toolService: ToolService,
    chatBoxWidget: ChatBoxWidget,
    onContextSelected?: (context: IMentionContext) => void,
    onContextRemoved?: (context_id: string) => void,
    onResetChat?: () => void,
    onModeSelected?: (mode: 'agent' | 'ask' | 'fast') => void
  ) {
    this.chatInput = chatInput;
    this.chatHistoryManager = chatHistoryManager;
    this.contentManager = contentManager;
    this.toolService = toolService;
    this.chatBoxWidget = chatBoxWidget;
    this.onContextSelected = onContextSelected || null;
    this.onContextRemoved = onContextRemoved || null;
    this.onResetChat = onResetChat || null;
    this.onModeSelected = onModeSelected;

    // Set up event handlers for textarea
    this.setupEventHandlers();

    // Load user message history
    void this.loadUserMessageHistory();
  }

  /**
   * Set up event handlers for textarea
   */
  private setupEventHandlers(): void {
    const inputElement = this.isRichTextInput(this.chatInput)
      ? this.chatInput.getInputElement()
      : this.chatInput;

    // Auto-resize the textarea as content grows
    if (this.isRichTextInput(this.chatInput)) {
      this.chatInput.addInputEventListener('input', () => {
        this.resizeTextarea();
      });
    } else {
      inputElement.addEventListener('input', () => {
        this.resizeTextarea();
      });
    }

    // Handle keydown events for submission and special key combinations
    const keydownHandler = (event: Event) => {
      const keyEvent = event as KeyboardEvent;

      // Handle tab and enter when mention dropdown is visible
      if (this.mentionDropdown.getIsVisible()) {
        if (keyEvent.key === 'Tab') {
          keyEvent.preventDefault();
          this.handleTabCompletion();
          return;
        }
        if (keyEvent.key === 'Enter') {
          keyEvent.preventDefault();
          this.handleEnterWithMention();
          return;
        }
      }

      // Handle enter for message submission
      if (keyEvent.key === 'Enter') {
        if (keyEvent.shiftKey) {
          // Allow Shift+Enter for new lines
          return;
        }

        // Check if we have a complete mention that should be processed first
        if (this.hasCompleteMentionAtCursor()) {
          keyEvent.preventDefault();
          this.processCompleteMention();
          return;
        }

        // Normal enter - send message
        keyEvent.preventDefault();
        void this.sendMessage();
        return;
      }

      // Message history navigation with arrow keys
      if (keyEvent.key === 'ArrowUp') {
        // Only navigate history if cursor is at the beginning of the text or input is empty
        if (this.getSelectionStart() === 0 || this.getInputValue() === '') {
          keyEvent.preventDefault();
          this.navigateHistory('up');
        }
      } else if (keyEvent.key === 'ArrowDown') {
        // Only navigate history if cursor is at the end of the text or input is empty
        if (
          this.getSelectionStart() === this.getInputLength() ||
          this.getInputValue() === ''
        ) {
          keyEvent.preventDefault();
          this.navigateHistory('down');
        }
      }
    };

    if (this.isRichTextInput(this.chatInput)) {
      this.chatInput.addInputEventListener('keydown', keydownHandler);
    } else {
      inputElement.addEventListener('keydown', keydownHandler);
    }
  }

  /**
   * Load the user's message history from all chat threads
   */
  public async loadUserMessageHistory(): Promise<void> {
    this.userMessageHistory = [];

    // Iterate through all notebooks
    const notebookIds = await this.chatHistoryManager.getNotebookIds();
    for (const notebookId of notebookIds) {
      // Get all threads for this notebook
      const threads = this.chatHistoryManager.getThreadsForNotebook(notebookId);
      if (!threads) {
        continue;
      }

      // Extract user messages from each thread
      for (const thread of threads) {
        const userMessages = thread.messages
          .filter(msg => msg.role === 'user' && typeof msg.content === 'string')
          .map(msg => (typeof msg.content === 'string' ? msg.content : ''));

        // Add non-empty messages to history
        userMessages.forEach(msg => {
          if (msg && !this.userMessageHistory.includes(msg)) {
            this.userMessageHistory.push(msg);
          }
        });
      }
    }

    // Reset the position to start at the most recent message
    this.historyPosition = -1;
    this.unsavedInput = '';

    // Sort the history so the most recently used messages are at the end
    // This makes arrow-key navigation more intuitive
    this.userMessageHistory.sort((a, b) => {
      // Keep shorter messages (which tend to be more general/reusable) at the end
      if (a.length !== b.length) {
        return a.length - b.length;
      }
      return a.localeCompare(b);
    });

    console.log(
      `[ChatInputManager] Loaded ${this.userMessageHistory.length} user messages for history navigation`
    );
  }

  /**
   * Navigate through user message history
   * @param direction 'up' for older messages, 'down' for newer messages
   */
  public navigateHistory(direction: 'up' | 'down'): void {
    // If no history, nothing to do
    if (this.userMessageHistory.length === 0) {
      return;
    }

    // Save current input if this is the first navigation action
    if (this.historyPosition === -1) {
      this.unsavedInput = this.getInputValue();
    }

    if (direction === 'up') {
      // Navigate to previous message (older)
      if (this.historyPosition < this.userMessageHistory.length - 1) {
        this.historyPosition++;
        const historyMessage =
          this.userMessageHistory[
            this.userMessageHistory.length - 1 - this.historyPosition
          ];
        this.setInputValue(historyMessage);
        // Place cursor at end of text
        const length = historyMessage.length;
        this.setSelectionRange(length, length);
      }
    } else {
      // Navigate to next message (newer)
      if (this.historyPosition > 0) {
        this.historyPosition--;
        const historyMessage =
          this.userMessageHistory[
            this.userMessageHistory.length - 1 - this.historyPosition
          ];
        this.setInputValue(historyMessage);
        // Place cursor at end of text
        const length = historyMessage.length;
        this.setSelectionRange(length, length);
      } else if (this.historyPosition === 0) {
        // Restore the unsaved input when reaching the bottom of history
        this.historyPosition = -1;
        this.setInputValue(this.unsavedInput);
        // Place cursor at end of text
        const length = this.unsavedInput.length;
        this.setSelectionRange(length, length);
      }
    }

    // Resize the textarea to fit the content
    this.resizeTextarea();
  }
  /**
   * Resize the textarea based on its content
   */
  public resizeTextarea(): void {
    if (this.isRichTextInput(this.chatInput)) {
      // Reset height to auto to get the correct scrollHeight
      this.chatInput.setHeight('auto');
      // Set the height to match the content (with a max height)
      const maxHeight = 150; // Maximum height in pixels
      const scrollHeight = this.chatInput.getScrollHeight();
      if (scrollHeight <= maxHeight) {
        this.chatInput.setHeight(scrollHeight + 'px');
        this.chatInput.setOverflowY('hidden');
      } else {
        this.chatInput.setHeight(maxHeight + 'px');
        this.chatInput.setOverflowY('auto');
      }
    } else {
      // Reset height to auto to get the correct scrollHeight
      this.chatInput.style.height = 'auto';
      // Set the height to match the content (with a max height)
      const maxHeight = 150; // Maximum height in pixels
      const scrollHeight = this.chatInput.scrollHeight;
      if (scrollHeight <= maxHeight) {
        this.chatInput.style.height = scrollHeight + 'px';
        this.chatInput.style.overflowY = 'hidden';
      } else {
        this.chatInput.style.height = maxHeight + 'px';
        this.chatInput.style.overflowY = 'auto';
      }
    }
  }

  /**
   * Set the value for either input type
   */
  public setInputValue(value: string): void {
    if (this.isRichTextInput(this.chatInput)) {
      this.chatInput.setPlainText(value);
    } else {
      this.chatInput.value = value;
    }

    // Trigger input event to detect removed contexts
    // this.detectDeletedContexts();
  }

  /**
   * Get the plain text value from either input type
   */
  private getInputValue(): string {
    if (this.isRichTextInput(this.chatInput)) {
      return this.chatInput.getPlainText().trim();
    } else {
      return this.chatInput.value.trim();
    }
  }

  /**
   * Check if the input is a RichTextChatInput
   */
  private isRichTextInput(input: ChatInputElement): input is RichTextChatInput {
    return input instanceof RichTextChatInput;
  }

  /**
   * Get selection start position for either input type
   */
  private getSelectionStart(): number {
    if (this.isRichTextInput(this.chatInput)) {
      return this.chatInput.getSelectionStart();
    } else {
      return this.chatInput.selectionStart || 0;
    }
  }

  /**
   * Set selection range for either input type
   */
  private setSelectionRange(start: number, end: number): void {
    if (this.isRichTextInput(this.chatInput)) {
      this.chatInput.setSelectionRange(start, end);
    } else {
      this.chatInput.selectionStart = start;
      this.chatInput.selectionEnd = end;
    }
  }

  /**
   * Get the current input text length
   */
  private getInputLength(): number {
    return this.getInputValue().length;
  }

  /**
   * Clear the input
   */
  public clearInput(): void {
    if (this.isRichTextInput(this.chatInput)) {
      this.chatInput.clear();
    } else {
      this.chatInput.value = '';
      this.chatInput.style.height = 'auto'; // Reset height after clearing
    }
    this.focus();
  }

  /**
   * Add a message to history
   */
  public addToHistory(message: string): void {
    if (!this.userMessageHistory.includes(message)) {
      this.userMessageHistory.push(message);
    }

    // Reset history navigation
    this.historyPosition = -1;
    this.unsavedInput = '';
  }

  /**
   * Focus the input
   */
  public focus(): void {
    if (this.isRichTextInput(this.chatInput)) {
      this.chatInput.focus();
    } else {
      this.chatInput.focus();
    }
  }

  /**
   * Get the current input value (public method)
   */
  public getCurrentInputValue(): string {
    return this.getInputValue();
  }

  /**
   * Set the dependencies needed for sendMessage and revertAndSend functionality
   */
  public setDependencies(dependencies: {
    chatService: IChatService;
    conversationService: ConversationService;
    messageComponent: ChatMessages;
    uiHelper: ChatUIHelper;
    contextHandler: ChatboxContext;
    sendButton: HTMLButtonElement;
    modeSelector: HTMLElement;
    cancelMessage: () => void;
    onMessageSent?: () => void;
  }): void {
    this.chatService = dependencies.chatService;
    this.conversationService = dependencies.conversationService;
    this.messageComponent = dependencies.messageComponent;
    this.uiHelper = dependencies.uiHelper;
    this.contextHandler = dependencies.contextHandler;
    this.sendButton = dependencies.sendButton;
    this.modeSelector = dependencies.modeSelector;
    this.cancelMessage = dependencies.cancelMessage;
    this.onMessageSent = dependencies.onMessageSent;
  }

  /**
   * Set the mode name
   */
  public setModeName(modeName: 'agent' | 'ask' | 'fast'): void {
    this.modeName = modeName;
  }

  /**
   * Get the current processing state
   */
  public getIsProcessingMessage(): boolean {
    return this.isProcessingMessage;
  }

  /**
   * Set the processing state
   */
  public setIsProcessingMessage(value: boolean): void {
    this.isProcessingMessage = value;
  }

  /**
   * Get the current checkpoint to restore
   */
  public getCheckpointToRestore(): ICheckpoint | null {
    return this.checkpointToRestore;
  }

  /**
   * Set the checkpoint to restore
   */
  public setCheckpointToRestore(checkpoint: ICheckpoint | null): void {
    this.checkpointToRestore = checkpoint;
  }

  /**
   * Send a message to the AI service
   */
  public async sendMessage(
    cell_context?: string,
    hidden?: boolean
  ): Promise<void> {
    const perfStart = performance.now();
    console.log('[PERF] ChatInputManager.sendMessage - START');

    // Check if dependencies are set
    if (
      !this.chatService ||
      !this.conversationService ||
      !this.messageComponent ||
      !this.uiHelper ||
      !this.contextHandler ||
      !this.sendButton ||
      !this.modeSelector
    ) {
      console.error(
        'ChatInputManager dependencies not set. Call setDependencies() first.'
      );
      return;
    }

    const userInput = this.getCurrentInputValue();
    if (!userInput || this.isProcessingMessage) {
      return;
    }

    if (this.checkpointToRestore) {
      await this.conversationService.finishCheckpointRestoration(
        this.checkpointToRestore
      );
    }

    // Hide the waiting reply box when user sends a message
    AppStateService.getWaitingUserReplyBoxManager().hide();

    // Special command to reset the chat
    if (userInput.toLowerCase() === 'reset') {
      // We'll need to add a callback for this
      if (this.onResetChat) {
        this.onResetChat();
      }
      this.clearInput();
      return;
    }

    // Add message to history navigation
    this.addToHistory(userInput);

    // Notify that a message is being sent (triggers switch to history widget)
    if (this.onMessageSent) {
      this.onMessageSent();
    }

    // Set processing state
    this.isProcessingMessage = true;
    this.uiHelper.updateSendButton(this.sendButton, true);
    AppStateService.getPlanStateDisplay().setLoading(true);
    this.uiHelper.updateAgentModeElement(this.modeSelector, true);

    // Reset LLM state display to generating state, clearing any diff state
    this.uiHelper.resetToGeneratingState('Generating...');

    // Check if the chat client has been properly initialized
    if (!this.chatService.isInitialized()) {
      this.messageComponent.addSystemMessage(
        '❌ API key is not set. Please configure it in the settings.'
      );
      this.isProcessingMessage = false;
      this.uiHelper.updateSendButton(this.sendButton, false);
      AppStateService.getPlanStateDisplay().setLoading(false);
      this.uiHelper.updateAgentModeElement(this.modeSelector, false);
      this.uiHelper.hideLoadingIndicator();
      return;
    }
    const system_messages: string[] = [];
    // Clear the input
    this.clearInput();

    // Convert @mentions to context tags for message processing
    const processedUserInput = convertMentionsToContextTags(
      userInput,
      this.activeContexts
    );
    console.log('[ChatInputManager] Original message:', userInput);
    console.log(
      '[ChatInputManager] Processed message with context tags:',
      processedUserInput
    );

    // Display the user message in the UI (with context tags for proper styling)
    this.messageComponent.addUserMessage(processedUserInput, hidden);

    // Initialize messages with the user query (with context tags for API processing)
    const newUserMessage = { role: 'user', content: processedUserInput };

    try {
      // Make sure the conversation service knows which notebook we're targeting
      const currentNotebookId = AppStateService.getCurrentNotebookId();
      if (currentNotebookId) {
        this.conversationService.setNotebookId(currentNotebookId);

        const cellChanges =
          await NotebookCellStateService.detectChanges(currentNotebookId);
        const changesSummary =
          NotebookCellStateService.generateChangeSummaryMessage(cellChanges);
        if (changesSummary) {
          system_messages.push(changesSummary);
          console.log(
            '[ChatInputManager] Detected notebook changes, added to system messages'
          );
        }
      }

      // Add cell changes to system messages if there are any

      const messages = [newUserMessage];
      if (cell_context) {
        system_messages.push(cell_context);
      }
      const mentionContexts = this.messageComponent.getMentionContexts();
      if (mentionContexts.size > 0) {
        system_messages.push(this.contextHandler.getCurrentContextMessage());
      }

      system_messages.push(
        this.contextHandler.getCurrentWorkingDirectoryMessage()
      );

      // Proceed with sending the message

      AppStateService.getNotebookDiffManager().clearDiffs();

      const perfBeforeConversation = performance.now();
      console.log(
        `[PERF] ChatInputManager.sendMessage - Before processConversation (${(perfBeforeConversation - perfStart).toFixed(2)}ms elapsed)`
      );

      await this.conversationService.processConversation(
        messages,
        system_messages,
        this.modeName
      );

      const perfAfterConversation = performance.now();
      console.log(
        `[PERF] ChatInputManager.sendMessage - After processConversation (${(perfAfterConversation - perfBeforeConversation).toFixed(2)}ms)`
      );

      // Cache the current notebook state after successful message processing
      if (currentNotebookId) {
        await NotebookCellStateService.cacheCurrentNotebookState(
          currentNotebookId
        );
      }
      console.log(
        '[ChatInputManager] Cached notebook state after message processing'
      );
    } catch (error) {
      console.error('Error in conversation processing:', error);

      // Only show error if we're not cancelled
      if (this.chatService.getRequestStatus() !== ChatRequestStatus.CANCELLED) {
        // Check if this is a subscription/authentication error
        const errorMessage =
          error instanceof Error ? error.message : String(error);

        // Check for authentication errors in the error message
        const isAuthError =
          errorMessage.includes('authentication_error') ||
          errorMessage.includes('Invalid API key') ||
          (errorMessage.includes('401') && errorMessage.includes('error'));

        if (isAuthError) {
          // Display subscription card instead of error message
          this.messageComponent.displaySubscriptionCard();
        } else {
          // Display regular error message
          this.messageComponent.addErrorMessage(`❌ ${errorMessage}`);
        }
      }
    } finally {
      // Reset state
      this.isProcessingMessage = false;
      this.uiHelper.updateSendButton(this.sendButton, false);
      AppStateService.getPlanStateDisplay().setLoading(false);
      this.uiHelper.updateAgentModeElement(this.modeSelector, false);
    }
  }

  /**
   * Continue the LLM loop without requiring new user input
   * This continues processing without creating or displaying a new user message
   */
  public async continueMessage(cell_context?: string): Promise<void> {
    // Check if dependencies are set
    if (
      !this.chatService ||
      !this.conversationService ||
      !this.messageComponent ||
      !this.uiHelper ||
      !this.contextHandler ||
      !this.sendButton ||
      !this.modeSelector
    ) {
      console.error(
        'ChatInputManager dependencies not set. Call setDependencies() first.'
      );
      return;
    }

    if (this.isProcessingMessage) {
      return;
    }

    if (this.checkpointToRestore) {
      await this.conversationService.finishCheckpointRestoration(
        this.checkpointToRestore
      );
    }

    // Hide the waiting reply box when continuing
    AppStateService.getWaitingUserReplyBoxManager().hide();

    // Set processing state
    this.isProcessingMessage = true;
    this.uiHelper.updateSendButton(this.sendButton, true);
    AppStateService.getPlanStateDisplay().setLoading(true);
    this.uiHelper.updateAgentModeElement(this.modeSelector, true);

    // Reset LLM state display to generating state, clearing any diff state
    this.uiHelper.resetToGeneratingState('Generating...');

    // Check if the chat client has been properly initialized
    if (!this.chatService.isInitialized()) {
      this.messageComponent.addSystemMessage(
        '❌ API key is not set. Please configure it in the settings.'
      );
      this.isProcessingMessage = false;
      this.uiHelper.updateSendButton(this.sendButton, false);
      AppStateService.getPlanStateDisplay().setLoading(false);
      this.uiHelper.updateAgentModeElement(this.modeSelector, false);
      this.uiHelper.hideLoadingIndicator();
      return;
    }

    const system_messages: string[] = [];

    try {
      // Make sure the conversation service knows which notebook we're targeting
      const currentNotebookId = AppStateService.getCurrentNotebookId();
      if (currentNotebookId) {
        this.conversationService.setNotebookId(currentNotebookId);

        const cellChanges =
          await NotebookCellStateService.detectChanges(currentNotebookId);
        const changesSummary =
          NotebookCellStateService.generateChangeSummaryMessage(cellChanges);
        if (changesSummary) {
          system_messages.push(changesSummary);
          console.log(
            '[ChatInputManager] Detected notebook changes, added to system messages'
          );
        }
      }

      // Continue without adding a new user message
      const messages: Array<{ role: string; content: string }> = [];
      if (cell_context) {
        system_messages.push(cell_context);
      }
      const mentionContexts = this.messageComponent.getMentionContexts();
      if (mentionContexts.size > 0) {
        system_messages.push(this.contextHandler.getCurrentContextMessage());
      }

      system_messages.push(
        this.contextHandler.getCurrentWorkingDirectoryMessage()
      );

      // Proceed with continuing the conversation

      AppStateService.getNotebookDiffManager().clearDiffs();

      await this.conversationService.processConversation(
        messages,
        system_messages,
        this.modeName
      );

      // Cache the current notebook state after successful message processing
      if (currentNotebookId) {
        await NotebookCellStateService.cacheCurrentNotebookState(
          currentNotebookId
        );
      }
      console.log(
        '[ChatInputManager] Cached notebook state after continuing message'
      );
    } catch (error) {
      console.error('Error in conversation processing:', error);

      // Only show error if we're not cancelled
      if (this.chatService.getRequestStatus() !== ChatRequestStatus.CANCELLED) {
        // Check if this is a subscription/authentication error
        const errorMessage =
          error instanceof Error ? error.message : String(error);

        // Check for authentication errors in the error message
        const isAuthError =
          errorMessage.includes('authentication_error') ||
          errorMessage.includes('Invalid API key') ||
          (errorMessage.includes('401') && errorMessage.includes('error'));

        if (isAuthError) {
          // Display subscription card instead of error message
          this.messageComponent.displaySubscriptionCard();
        } else {
          // Display regular error message
          this.messageComponent.addErrorMessage(`❌ ${errorMessage}`);
        }
      }
    } finally {
      // Reset state
      this.isProcessingMessage = false;
      this.uiHelper.updateSendButton(this.sendButton, false);
      AppStateService.getPlanStateDisplay().setLoading(false);
      this.uiHelper.updateAgentModeElement(this.modeSelector, false);

      // Set needsContinue to false after continueMessage finishes
      const currentThread = this.chatHistoryManager.getCurrentThread();
      if (currentThread && currentThread.needsContinue) {
        currentThread.needsContinue = false;
        console.log(
          '[ChatInputManager] Set needsContinue to false after continueMessage finished'
        );
      }
    }
  }

  /**
   * Handle tab completion for mentions
   */
  private handleTabCompletion(): void {
    // Use the dropdown's own selection mechanism which handles highlighted items
    this.mentionDropdown.selectHighlightedItem();
  }

  /**
   * Handle enter key when mention dropdown is visible
   */
  private handleEnterWithMention(): void {
    // Use the dropdown's own selection mechanism which handles highlighted items
    this.mentionDropdown.selectHighlightedItem();
  }

  /**
   * Complete a mention with the given name
   */
  private completeMentionWithName(name: string): void {
    const currentInput = this.getInputValue();
    const cursorPos = this.getSelectionStart();

    // Find the @ symbol before the cursor
    let mentionStart = -1;
    for (let i = cursorPos - 1; i >= 0; i--) {
      if (currentInput[i] === '@') {
        mentionStart = i;
        break;
      }
      if (currentInput[i] === ' ' || currentInput[i] === '\n') {
        break;
      }
    }

    if (mentionStart === -1) {
      return;
    }

    // Replace the partial mention with the complete one - replace spaces with underscores
    const beforeMention = currentInput.substring(0, mentionStart);
    const afterCursor = currentInput.substring(cursorPos);
    const displayName = name.replace(/\s+/g, '_');
    const replacement = `@${displayName} `;

    this.setInputValue(beforeMention + replacement + afterCursor);

    // Set cursor after the completed mention
    const newCursorPos = mentionStart + replacement.length;
    this.setSelectionRange(newCursorPos, newCursorPos);

    // The mention dropdown should already handle adding to context
  }

  /**
   * Check if there's a complete mention at the cursor position
   */
  private hasCompleteMentionAtCursor(): boolean {
    const currentInput = this.getInputValue();
    const cursorPos = this.getSelectionStart();

    // Look for @mention pattern before cursor
    const beforeCursor = currentInput.substring(0, cursorPos);
    const mentionMatch = beforeCursor.match(/@(\w+)\s*$/);

    return mentionMatch !== null;
  }

  /**
   * Process a complete mention (add to context without sending message)
   */
  private processCompleteMention(): void {
    const currentInput = this.getInputValue();
    const cursorPos = this.getSelectionStart();

    // Look for @mention pattern before cursor
    const beforeCursor = currentInput.substring(0, cursorPos);
    const mentionMatch = beforeCursor.match(/@(\w+)\s*$/);

    if (mentionMatch) {
      const mentionName = mentionMatch[1];

      // Try to find this mention in the available contexts
      // This is a simplified approach - in a real implementation you'd want to
      // search through all context categories for a matching name
      console.log(`Processing complete mention: ${mentionName}`);

      // Focus back to input for continued typing
      this.focus();
    }
  }

  /**
   * Create the complete input container with all its components
   */
  public createInputContainer(): HTMLElement {
    // Create input container with text input and send button
    this.inputContainer = document.createElement('div');
    this.inputContainer.className = 'sage-ai-input-container';
    this.inputContainer.style.position = 'relative'; // Add relative positioning

    // Create inner chatbox wrapper for the focused styling
    this.chatboxWrapper = document.createElement('div');
    this.chatboxWrapper.className = 'sage-ai-chatbox-wrapper';

    // Create context row (first row)
    this.createContextRow();

    // Create input row (second row)
    this.createInputRow();

    // Assemble the input structure
    this.chatboxWrapper.appendChild(this.contextRow!);
    this.chatboxWrapper.appendChild(this.inputRow!);
    this.inputContainer.appendChild(this.chatboxWrapper);

    // Initialize the mention dropdown with the input container
    const inputElement = this.isRichTextInput(this.chatInput)
      ? this.chatInput.getInputElement()
      : this.chatInput;
    this.mentionDropdown = new ChatContextMenu(
      inputElement as HTMLElement,
      this.inputContainer,
      this.getContentManager(),
      this.getToolService()
    );

    // Set up the context selection callback for the mention dropdown
    this.mentionDropdown.setContextSelectedCallback(
      (context: IMentionContext) => {
        // Store the context when selected
        this.activeContexts.set(context.id, context);

        // Update rich text input contexts if applicable
        if (this.isRichTextInput(this.chatInput)) {
          this.chatInput.setActiveContexts(this.activeContexts);
        }

        if (this.onContextSelected) {
          this.onContextSelected(context);
        }
      }
    );

    return this.inputContainer;
  }

  /**
   * Create the context row with "Add Context" button
   */
  private createContextRow(): void {
    this.contextRow = document.createElement('div');
    this.contextRow.className = 'sage-ai-context-row';

    // Create "Add Context" button with @ icon
    this.addContextButton = document.createElement('button');

    const atIcon = document.createElement('span');
    atIcon.className = 'sage-ai-at-icon';
    atIcon.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="13" viewBox="0 0 12 13" fill="none">\n' +
      '  <g clip-path="url(#clip0_590_6942)">\n' +
      '    <path d="M8.00001 4.5V7C8.00001 7.39783 8.15804 7.77936 8.43935 8.06066C8.72065 8.34197 9.10218 8.5 9.50001 8.5C9.89783 8.5 10.2794 8.34197 10.5607 8.06066C10.842 7.77936 11 7.39783 11 7V6.5C11 5.37366 10.6197 4.2803 9.92071 3.39709C9.22172 2.51387 8.24499 1.89254 7.14877 1.63376C6.05255 1.37498 4.90107 1.49391 3.88089 1.97128C2.86071 2.44865 2.03159 3.2565 1.52787 4.26394C1.02415 5.27137 0.875344 6.41937 1.10556 7.52194C1.33577 8.62452 1.93151 9.61706 2.79627 10.3388C3.66102 11.0605 4.74413 11.4691 5.87009 11.4983C6.99606 11.5276 8.09893 11.1758 9.00001 10.5M8 6.5C8 7.60457 7.10457 8.5 6 8.5C4.89543 8.5 4 7.60457 4 6.5C4 5.39543 4.89543 4.5 6 4.5C7.10457 4.5 8 5.39543 8 6.5Z" stroke="#949494" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>\n' +
      '  </g>\n' +
      '  <defs>\n' +
      '    <clipPath id="clip0_590_6942">\n' +
      '      <rect width="12" height="12" fill="white" transform="translate(0 0.5)"/>\n' +
      '    </clipPath>\n' +
      '  </defs>\n' +
      '</svg>';

    const contextText = document.createElement('p');
    contextText.className = 'sage-ai-context-text';
    contextText.textContent = 'Add Context';

    this.addContextButton.className = 'sage-ai-add-context-button';
    this.addContextButton.appendChild(atIcon);
    this.addContextButton.appendChild(contextText);
    this.addContextButton.title = 'Add context';
    this.addContextButton.type = 'button';

    // Add click handler for the Add Context button
    this.addContextButton.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      // Focus the input and trigger mention dropdown by inserting @
      this.chatInput.focus();
      const currentText = this.getInputValue();
      const cursorPosition = this.getSelectionStart();
      const newText =
        currentText.slice(0, cursorPosition) +
        '@' +
        currentText.slice(cursorPosition);
      this.setInputValue(newText);
      // Set cursor position after the @
      setTimeout(() => {
        this.setSelectionRange(cursorPosition + 1, cursorPosition + 1);
        // Trigger input event to activate mention dropdown
        const inputEvent = new Event('input', { bubbles: true });
        const inputElement = this.isRichTextInput(this.chatInput)
          ? this.chatInput.getInputElement()
          : this.chatInput;
        inputElement.dispatchEvent(inputEvent);
      }, 0);
    });

    // Create context display container
    this.contextDisplay = document.createElement('div');
    this.contextDisplay.className = 'sage-ai-context-display-inline';

    this.contextRow.appendChild(this.addContextButton);
    this.contextRow.appendChild(this.contextDisplay);
  }

  /**
   * Create the input row with rich text input, send button, and mode selector
   */
  private createInputRow(): void {
    this.inputRow = document.createElement('div');
    this.inputRow.className = 'sage-ai-input-row';

    // Add the rich text input to the input row
    if (this.isRichTextInput(this.chatInput)) {
      this.inputRow.appendChild(this.chatInput.getElement());
    } else {
      this.inputRow.appendChild(this.chatInput);
    }

    // Create token progress wrapper (contains circle and compress button)
    this.createTokenProgressWrapper();

    // Create send button
    this.createSendButton();

    // Create mode selector
    this.createModeSelector();

    // Add token progress wrapper, send button and mode selector to input row
    this.inputRow.appendChild(this.tokenProgressWrapper!);
    this.inputRow.appendChild(this.sendButton!);
    this.inputRow.appendChild(this.modeSelector!);
  }

  /**
   * Create the send button with proper styling and event handlers
   */
  private createSendButton(): void {
    this.sendButton = document.createElement('button');
    SEND_ICON.render(this.sendButton);
    this.sendButton.className = 'sage-ai-send-button disabled';
    this.sendButton.style.position = 'absolute'; // Set absolute positioning
    this.sendButton.style.bottom = '12px'; // Position at bottom
    this.sendButton.style.right = '12px'; // Position at right
    this.sendButton.addEventListener('click', event => {
      console.log('[ChatInputManager] Send/Cancel button clicked', {
        isProcessingMessage: this.isProcessingMessage,
        hasCancelMessage: !!this.cancelMessage,
        buttonClassName: this.sendButton?.className,
        buttonDisabled: this.sendButton?.disabled
      });

      if (this.isProcessingMessage) {
        // CRITICAL: Always cancel when processing, no matter what
        console.log('[ChatInputManager] Cancelling message via send button');

        // Try the callback first
        if (this.cancelMessage) {
          console.log('[ChatInputManager] Calling cancelMessage callback');
          this.cancelMessage();
        } else {
          // Fallback: try to call the chatbox widget's cancelMessage directly
          console.warn(
            '[ChatInputManager] cancelMessage callback is not defined! Using fallback...'
          );
          const chatWidget = AppStateService.getChatContainerSafe()?.chatWidget;
          if (chatWidget) {
            console.log(
              '[ChatInputManager] Calling cancelMessage via AppState fallback'
            );
            chatWidget.cancelMessage();
          } else {
            console.error(
              '[ChatInputManager] CRITICAL: Could not find chat widget to cancel message'
            );
          }
        }
      } else if (this.getInputValue().trim() !== '') {
        void this.sendMessage();
      }
    });

    // Update send button state based on input content
    const updateSendButtonState = () => {
      const hasContent = this.getInputValue().trim() !== '';
      if (this.isProcessingMessage) {
        // When processing, button becomes cancel button and MUST be enabled
        this.sendButton!.classList.add('enabled');
        this.sendButton!.classList.remove('disabled');
        this.sendButton!.disabled = false;
      } else if (hasContent) {
        this.sendButton!.classList.add('enabled');
        this.sendButton!.classList.remove('disabled');
        this.sendButton!.disabled = false;
      } else {
        this.sendButton!.classList.remove('enabled');
        this.sendButton!.classList.add('disabled');
        this.sendButton!.disabled = true;
      }
    };

    // Initial state - disabled since input starts empty
    this.sendButton.disabled = true;

    // Listen for input changes to update button state
    this.chatInput.addEventListener('input', updateSendButtonState);
    this.chatInput.addEventListener('keyup', updateSendButtonState);
    this.chatInput.addEventListener('paste', () => {
      // Use setTimeout to ensure paste content is processed
      setTimeout(updateSendButtonState, 0);
    });
  }

  /**
   * Create the wrapper for token progress circle and compress button
   */
  private createTokenProgressWrapper(): void {
    // Create wrapper container
    this.tokenProgressWrapper = document.createElement('div');
    this.tokenProgressWrapper.className = 'sage-ai-token-progress-wrapper';
    this.tokenProgressWrapper.style.position = 'absolute';
    this.tokenProgressWrapper.style.bottom = '13px';
    this.tokenProgressWrapper.style.right = '48px'; // Position to the left of send button (28px button + 8px spacing)
    this.tokenProgressWrapper.style.display = 'flex';
    this.tokenProgressWrapper.style.alignItems = 'center';
    this.tokenProgressWrapper.style.gap = '4px';
    this.tokenProgressWrapper.style.zIndex = '10';
    this.tokenProgressWrapper.style.padding = '0 2px';
    this.tokenProgressWrapper.style.borderRadius = '4px';

    // Create token progress circle
    this.createTokenProgressCircle();

    // Create compress button (initially hidden)
    this.createCompressButton();

    // Add circle and button to wrapper
    this.tokenProgressWrapper.appendChild(this.tokenProgressCircle!);
    this.tokenProgressWrapper.appendChild(this.compressButton!);
  }

  /**
   * Create the token progress circle to show token usage
   */
  private createTokenProgressCircle(): void {
    this.tokenProgressCircle = document.createElement('div');
    this.tokenProgressCircle.className = 'sage-ai-token-progress-container';
    this.tokenProgressCircle.style.position = 'relative';
    this.tokenProgressCircle.style.width = '24px';
    this.tokenProgressCircle.style.height = '24px';

    // Create SVG for circular progress
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '16');
    svg.setAttribute('height', '16');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.style.transform = 'rotate(-90deg)'; // Start from top

    // Background circle
    const bgCircle = document.createElementNS(
      'http://www.w3.org/2000/svg',
      'circle'
    );
    bgCircle.setAttribute('cx', '12');
    bgCircle.setAttribute('cy', '12');
    bgCircle.setAttribute('r', '9');
    bgCircle.setAttribute('fill', 'none');
    bgCircle.setAttribute('stroke', 'var(--jp-border-color3)');
    bgCircle.setAttribute('stroke-width', '3');

    // Progress circle
    const progressCircle = document.createElementNS(
      'http://www.w3.org/2000/svg',
      'circle'
    );
    progressCircle.setAttribute('cx', '12');
    progressCircle.setAttribute('cy', '12');
    progressCircle.setAttribute('r', '9');
    progressCircle.setAttribute('fill', 'none');
    progressCircle.setAttribute('stroke', '#4a90e2');
    progressCircle.setAttribute('stroke-width', '3');
    progressCircle.setAttribute('stroke-linecap', 'round');
    progressCircle.setAttribute('stroke-dasharray', '0 56.55'); // 2 * π * 9 ≈ 56.55
    progressCircle.setAttribute('data-progress', '0');
    progressCircle.classList.add('sage-ai-token-progress-stroke');

    // Create tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'sage-ai-token-progress-tooltip';
    tooltip.textContent = 'Token usage: 0 / 60,000 tokens (0%)';

    svg.appendChild(bgCircle);
    svg.appendChild(progressCircle);
    this.tokenProgressCircle.appendChild(svg);
    this.tokenProgressCircle.appendChild(tooltip);
  }

  /**
   * Create the compress button that appears when token usage >= 40%
   */
  private createCompressButton(): void {
    this.compressButton = document.createElement('button');
    this.compressButton.className = 'sage-ai-compress-button';
    this.compressButton.style.borderRadius = '4px';
    this.compressButton.style.border = 'none';
    this.compressButton.style.background = 'transparent';
    this.compressButton.style.cursor = 'pointer';
    this.compressButton.style.display = 'none'; // Hidden by default, shown when >= 40%
    this.compressButton.style.padding = '0';
    this.compressButton.style.flexShrink = '0';
    this.compressButton.style.alignItems = 'center';
    this.compressButton.style.justifyContent = 'center';
    this.compressButton.style.fontSize = '9px';
    this.compressButton.style.padding = '2px 4px';
    this.compressButton.title = 'Compact tokens';
    this.compressButton.innerHTML = 'Compact';

    // Add click handler
    this.compressButton.addEventListener('click', async e => {
      e.stopPropagation();
      await this.handleCompressHistory();
    });

    // Add hover effect
    this.compressButton.addEventListener('mouseenter', () => {
      this.compressButton!.style.background =
        'var(--jp-layout-color3, #e0e0e0)';
    });
    this.compressButton.addEventListener('mouseleave', () => {
      this.compressButton!.style.background =
        'var(--jp-layout-color2, #f5f5f5)';
    });
  }

  /**
   * Handle compress history button click
   * Sends a hidden message to trigger the compress_history tool
   */
  private async handleCompressHistory(): Promise<void> {
    if (!this.messageComponent || this.isProcessingMessage) {
      return;
    }

    // Disable button during compression
    if (this.compressButton) {
      this.compressButton.disabled = true;
      this.compressButton.style.opacity = '0.5';
      this.compressButton.style.cursor = 'wait';
    }

    try {
      // Save current input value
      const currentInput = this.getInputValue();

      // Set input to a message that will trigger compression
      this.setInputValue(
        'Please compress the chat history to reduce token usage. Keep the 10 most recent messages uncompressed.'
      );

      // Send as hidden message
      await this.sendMessage(undefined, true);

      // Restore original input value
      this.setInputValue(currentInput);
    } catch (error) {
      console.error(
        '[ChatInputManager] Error sending compress message:',
        error
      );
      if (this.messageComponent) {
        this.messageComponent.addSystemMessage(
          `⚠️ Error compressing chat history: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    } finally {
      // Re-enable button after a short delay to allow message processing to start
      setTimeout(() => {
        if (this.compressButton) {
          this.compressButton.disabled = false;
          this.compressButton.style.opacity = '1';
          this.compressButton.style.cursor = 'pointer';
        }
      }, 500);
    }
  }

  /**
   * Update the token progress circle based on current conversation history
   * Uses persisted usage data from Claude responses when available, falls back to estimation
   */
  public updateTokenProgress(messages?: IChatMessage[]): void {
    const conversationHistory =
      messages || this.messageComponent?.getMessageHistory() || [];

    // Try to calculate tokens from persisted usage data first
    let totalTokens = 0;
    let hasUsageData = false;

    for (const message of conversationHistory) {
      if (message.usage) {
        hasUsageData = true;
        // Sum: cache_creation + cache_read + input + output tokens
        totalTokens +=
          (message.usage.cache_creation_input_tokens || 0) +
          (message.usage.cache_read_input_tokens || 0) +
          (message.usage.input_tokens || 0) +
          (message.usage.output_tokens || 0);
      }
    }

    // Fall back to estimation if no usage data is available
    const tokenLimitCheck = checkTokenLimit(conversationHistory);
    const actualTokens = hasUsageData
      ? totalTokens
      : tokenLimitCheck.estimatedTokens;
    const percentage = Math.min(
      Math.round((actualTokens / MAX_RECOMMENDED_TOKENS) * 100),
      100
    );
    const circumference = 2 * Math.PI * 9; // radius is 9
    const offset = circumference - (percentage / 100) * circumference;

    const progressCircle = this.tokenProgressCircle?.querySelector(
      '.sage-ai-token-progress-stroke'
    ) as SVGCircleElement;
    const tooltip = this.tokenProgressCircle?.querySelector(
      '.sage-ai-token-progress-tooltip'
    ) as HTMLElement;

    if (progressCircle) {
      progressCircle.setAttribute(
        'stroke-dasharray',
        `${circumference} ${circumference}`
      );
      progressCircle.setAttribute('stroke-dashoffset', `${offset}`);

      // Change color based on percentage
      if (percentage >= 70) {
        progressCircle.setAttribute('stroke', '#e74c3c'); // Red for high usage
      } else if (percentage >= 40) {
        progressCircle.setAttribute('stroke', '#f39c12'); // Orange for medium-high usage
      } else {
        progressCircle.setAttribute('stroke', '#4a90e2'); // Blue for normal usage
      }
    }

    // Update tooltip
    if (tooltip) {
      let tokenDisplay: string;
      if (actualTokens >= 1000) {
        // Show e.g. 1.2k, 10.5k
        tokenDisplay =
          (actualTokens / 1000).toFixed(actualTokens < 10000 ? 1 : 0) + 'k';
      } else {
        tokenDisplay = actualTokens.toLocaleString();
      }
      const maxTokens =
        MAX_RECOMMENDED_TOKENS >= 1000
          ? (MAX_RECOMMENDED_TOKENS / 1000).toFixed(
              MAX_RECOMMENDED_TOKENS < 10000 ? 1 : 0
            ) + 'k'
          : MAX_RECOMMENDED_TOKENS.toLocaleString();
      tooltip.textContent = `${tokenDisplay} / ${maxTokens} tokens (${percentage}%)`;
    }

    // Show/hide compress button based on percentage
    if (this.compressButton) {
      if (percentage >= 40) {
        this.compressButton.style.display = 'flex';
        this.compressButton.style.visibility = 'visible';
        if (this.tokenProgressWrapper) {
          this.tokenProgressWrapper.style.backgroundColor =
            'var(--jp-layout-color1);';
        }
      } else {
        this.compressButton.style.display = 'none';
        this.compressButton.style.visibility = 'hidden';
        if (this.tokenProgressWrapper) {
          this.tokenProgressWrapper.style.backgroundColor = 'transparent';
        }
      }
    }

    // Update new prompt CTA visibility based on token percentage
    this.chatBoxWidget.updateNewPromptCtaVisibility(percentage);
  }

  /**
   * Create the mode selector with dropdown
   */
  private createModeSelector(): void {
    this.modeSelector = document.createElement('div');
    this.modeSelector.className = 'sage-ai-mode-selector';
    this.modeSelector.title = 'Select chat mode';

    // Create dropdown container
    this.modeSelectorDropdown = document.createElement('div');
    this.modeSelectorDropdown.className = 'sage-ai-mode-dropdown hidden';

    // Create content wrapper for flexbox layout
    const dropdownContent = document.createElement('div');
    dropdownContent.className = 'sage-ai-mode-dropdown-content';

    // Create options
    const agentOption = this.createModeOption(
      'agent',
      'Agent',
      AGENT_MODE_ICON.svgstr,
      'Prepare datasets. Build models. Test ideas.'
    );
    const askOption = this.createModeOption(
      'ask',
      'Ask',
      ASK_ICON.svgstr,
      'Ask SignalPilot about your notebook or your data.'
    );
    const handsOnOption = this.createModeOption(
      'fast',
      'Hands-on',
      HANDS_ON_MODE_ICON.svgstr,
      'Manually decide what gets added to the context.'
    );

    dropdownContent.appendChild(agentOption);
    dropdownContent.appendChild(askOption);
    dropdownContent.appendChild(handsOnOption);
    this.modeSelectorDropdown.append(dropdownContent);

    // Set initial display (Agent selected by default)
    this.updateModeSelectorDisplay('agent');

    // Add click handler to toggle dropdown
    this.modeSelector.addEventListener('click', e => {
      e.stopPropagation();
      if (this.modeSelector!.getAttribute('data-is-disabled') === 'true') {
        return;
      }
      this.toggleModeDropdown();
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
      this.closeModeDropdown();
    });
  }

  /**
   * Create a mode option for the dropdown
   */
  private createModeOption(
    mode: string,
    title: string,
    iconSvg: string,
    description: string
  ): HTMLElement {
    const option = document.createElement('div');
    option.className = 'sage-ai-mode-option';
    option.setAttribute('data-mode', mode);

    const iconContainer = document.createElement('div');
    iconContainer.className = 'sage-ai-mode-option-icon';
    iconContainer.innerHTML = iconSvg;

    const textContainer = document.createElement('div');
    textContainer.className = 'sage-ai-mode-option-text';

    const titleElement = document.createElement('div');
    titleElement.className = 'sage-ai-mode-option-title';
    titleElement.textContent = title;

    const descriptionElement = document.createElement('div');
    descriptionElement.className = 'sage-ai-mode-option-description';
    descriptionElement.textContent = description;

    textContainer.appendChild(titleElement);
    textContainer.appendChild(descriptionElement);

    option.appendChild(iconContainer);
    option.appendChild(textContainer);

    // Add click handler
    option.addEventListener('click', e => {
      e.stopPropagation();
      this.selectMode(mode as 'agent' | 'ask' | 'fast');
      this.closeModeDropdown();
    });

    return option;
  }

  /**
   * Toggle the mode dropdown visibility
   */
  private toggleModeDropdown(): void {
    if (this.modeSelectorDropdown!.classList.contains('hidden')) {
      this.openModeDropdown();
    } else {
      this.closeModeDropdown();
    }
  }

  /**
   * Open the mode dropdown
   */
  private openModeDropdown(): void {
    if (!this.modeSelector || !this.modeSelectorDropdown) {
      return;
    }

    // Add opening class to mode selector
    this.modeSelector.classList.add('open');

    // Position the dropdown above the selector
    const rect = this.modeSelector.getBoundingClientRect();
    this.modeSelectorDropdown.style.position = 'absolute';
    this.modeSelectorDropdown.style.bottom = `${window.innerHeight - rect.top + 8}px`;
    this.modeSelectorDropdown.style.left = `${rect.left}px`;
    this.modeSelectorDropdown.style.minWidth = `${rect.width}px`;

    // Append to body to ensure it appears above other elements
    document.body.appendChild(this.modeSelectorDropdown);

    // Remove hidden class and add visible class with slight delay for animation
    this.modeSelectorDropdown.classList.remove('hidden');
    this.modeSelectorDropdown.classList.add('opening');

    // Use requestAnimationFrame to ensure the element is rendered before adding visible class
    requestAnimationFrame(() => {
      this.modeSelectorDropdown?.classList.add('visible');
    });

    // Clean up animation class after animation completes
    setTimeout(() => {
      this.modeSelectorDropdown?.classList.remove('opening');
    }, 300);
  }

  /**
   * Close the mode dropdown
   */
  private closeModeDropdown(): void {
    if (!this.modeSelector || !this.modeSelectorDropdown) {
      return;
    }

    // Remove open class from mode selector
    this.modeSelector.classList.remove('open');

    // Add closing animation
    this.modeSelectorDropdown.classList.add('closing');
    this.modeSelectorDropdown.classList.remove('visible');

    // Remove from DOM after animation completes
    setTimeout(() => {
      if (!this.modeSelectorDropdown) {
        return;
      }
      this.modeSelectorDropdown.classList.add('hidden');
      this.modeSelectorDropdown.classList.remove('closing');

      // Remove from body if it was appended there
      if (this.modeSelectorDropdown.parentNode === document.body) {
        document.body.removeChild(this.modeSelectorDropdown);
      }
    }, 200);
  }

  /**
   * Select a mode and update the display
   */
  private selectMode(mode: 'agent' | 'ask' | 'fast'): void {
    this.modeName = mode;
    this.updateModeSelectorDisplay(mode);

    this.onModeSelected?.(mode);
  }

  /**
   * Update the mode selector display
   */
  private updateModeSelectorDisplay(mode: 'agent' | 'ask' | 'fast'): void {
    const selectedOption = this.modeSelectorDropdown!.querySelector(
      `[data-mode="${mode}"]`
    );
    if (selectedOption) {
      // Clear current display
      this.modeSelector!.innerHTML = '';

      // Create a display option without description
      const displayOption = document.createElement('div');
      displayOption.className = 'sage-ai-mode-display';

      const iconContainer = document.createElement('div');
      iconContainer.className = 'sage-ai-mode-option-icon';
      iconContainer.innerHTML = AGENT_MODE_SHINY_ICON.svgstr;
      displayOption.appendChild(iconContainer);

      // Create text element with only the title (no description)
      const originalText = selectedOption.querySelector(
        '.sage-ai-mode-option-text'
      );
      if (originalText) {
        const titleElement = originalText.querySelector(
          '.sage-ai-mode-option-title'
        );
        if (titleElement) {
          const textElement = document.createElement('div');
          textElement.className = 'sage-ai-mode-option-text';
          textElement.innerHTML = titleElement.innerHTML;
          displayOption.appendChild(textElement);
        }
      }

      // Add dropdown arrow
      const arrow = document.createElement('div');
      arrow.className = 'sage-ai-mode-selector-arrow';
      OPEN_MODE_SELECTOR_ICON.render(arrow);

      this.modeSelector!.appendChild(displayOption);
      this.modeSelector!.appendChild(arrow);
      this.modeSelector!.setAttribute('data-mode', mode);
    }
  }

  /**
   * Get the input container element
   */
  public getInputContainer(): HTMLElement | undefined {
    return this.inputContainer;
  }

  /**
   * Get the send button element
   */
  public getSendButton(): HTMLButtonElement | undefined {
    return this.sendButton;
  }

  /**
   * Get the mode selector element
   */
  public getModeSelector(): HTMLElement | undefined {
    return this.modeSelector;
  }

  /**
   * Get the context display element
   */
  public getContextDisplay(): HTMLElement | undefined {
    return this.contextDisplay;
  }

  /**
   * Get the content manager
   */
  private getContentManager(): Contents.IManager {
    return this.contentManager;
  }

  /**
   * Get the tool service
   */
  private getToolService(): ToolService {
    return this.toolService;
  }
}
