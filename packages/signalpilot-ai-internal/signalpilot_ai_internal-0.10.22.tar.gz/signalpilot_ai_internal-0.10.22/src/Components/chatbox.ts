import { ChatMessages } from '../Chat/ChatMessages';
import { ConversationService } from '../Chat/ConversationService';
import { PanelLayout, Widget } from '@lumino/widgets';
import { ConfigService } from '../Config/ConfigService';
import { IChatService } from '../Services/IChatService';
import { ServiceFactory, ServiceProvider } from '../Services/ServiceFactory';
import { ChatHistoryManager, IChatThread } from '../Chat/ChatHistoryManager';
import { ThreadManager } from '../ThreadManager';
import { ChatInputManager } from '../Chat/ChatInputManager';
import { RichTextChatInput } from '../Chat/RichTextChatInput';
import { ChatUIHelper } from '../Chat/ChatUIHelper';
import { AppStateService } from '../AppState';
import { ChatboxContext } from './ChatboxContext';
import { NewChatDisplayWidget } from './NewChatDisplayWidget';
import { LLMStateDisplay } from './LLMStateDisplay/LLMStateDisplay';
import { PlanStateDisplay } from './PlanStateDisplay';
import { MoreOptionsDisplay } from './MoreOptionsDisplay';
import { UpdateBannerWidget } from './UpdateBanner/UpdateBannerWidget';
import { Subscription } from 'rxjs';
import { ActionHistory } from '../Chat/ActionHistory';
import { BackendCacheService, STATE_DB_KEYS } from '../utils/backendCaching';
import { JupyterAuthService } from '../Services/JupyterAuthService';

// Recommended prompts for new chat display
const RECOMMENDED_PROMPTS: string[] = [
  // 'Analyze the data in my notebook'
  // 'Create a visualization from my data',
  // 'Help me clean and preprocess this dataset',
  // 'Build a machine learning model',
  // 'Explain this code and suggest improvements'
];

/**
 * ChatBoxWidget: A widget for interacting with AI services via a chat interface
 */
export class ChatBoxWidget extends Widget {
  private chatHistory: HTMLDivElement;
  private chatInput: RichTextChatInput;
  private newChatButton: HTMLButtonElement;
  private undoButton: HTMLButtonElement;
  public autorunCheckbox: HTMLInputElement;
  private lastNotebookId: string | null = null;

  private threadSelectorButton: HTMLButtonElement;
  private threadNameDisplay: HTMLSpanElement;

  // Widget management
  private historyWidget: Widget | null = null;
  private newChatDisplayWidget: NewChatDisplayWidget | null = null;
  public llmStateDisplay: LLMStateDisplay;
  private planStateDisplay: PlanStateDisplay;
  private chatHistoryLoadingOverlay: HTMLDivElement | null = null;
  private moreOptionsDisplay: MoreOptionsDisplay;
  private updateBanner: UpdateBannerWidget | null = null;
  private scrollDownButton: HTMLButtonElement;
  private stateDisplayContainer: HTMLDivElement | null = null;

  // Chat services
  public messageComponent: ChatMessages;
  private chatService: IChatService;
  public conversationService: ConversationService;
  private currentServiceProvider: ServiceProvider = ServiceProvider.ANTHROPIC;
  public chatHistoryManager: ChatHistoryManager;

  // Helper classes
  public threadManager: ThreadManager;
  public inputManager: ChatInputManager;
  private uiHelper: ChatUIHelper;
  private contextHandler: ChatboxContext;

  // New prompt CTA element
  private newPromptCTA: HTMLDivElement | null = null;

  // Observer cleanup
  private resizeObserver?: ResizeObserver;
  private mutationObserver?: MutationObserver;
  private llmStateConnection?: any;
  private planStateConnection?: any;
  private appStateSubscription?: Subscription;
  private lastClaudeSettings?: {
    claudeApiKey: string;
    claudeModelId: string;
    claudeModelUrl: string;
  };

  // Track if welcome message has been shown
  private hasShownWelcomeMessage: boolean = false;

  // Track welcome message state for pre-loading during demos
  private welcomeMessagePromise: Promise<void> | null = null;
  private isWelcomeMessageReady: boolean = false;
  private isWelcomeMessageHidden: boolean = false;

  // Track if chatbox is fully ready (after launcher setup completes)
  private isReady: boolean = false;

  constructor(actionHistory: ActionHistory) {
    super();
    this.id = 'sage-ai-chat';
    this.title.label = 'AI Chat';
    this.title.closable = true;
    this.addClass('sage-ai-chatbox');

    // Initialize the chat history manager
    this.chatHistoryManager = new ChatHistoryManager();

    // Initialize services
    this.chatService = ServiceFactory.createService(
      this.currentServiceProvider
    );

    AppStateService.setChatService(this.chatService);

    // Create layout for the chat box
    const layout = new PanelLayout();
    this.layout = layout;

    // Create toolbar
    const toolbar = document.createElement('div');
    toolbar.className = 'sage-ai-toolbar';

    // Create thread selector button
    this.threadSelectorButton = document.createElement('button');
    this.threadSelectorButton.className =
      'sage-ai-icon-button-md sage-ai-thread-selector-button';

    // Add chat icon SVG
    this.threadSelectorButton.innerHTML = `
     <svg width="20" height="21" viewBox="0 0 20 21" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2.5 10.5H17.5M2.5 5.5H17.5M2.5 15.5H17.5" stroke="#949494" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
    this.threadSelectorButton.title = 'Select conversation thread';

    toolbar.appendChild(this.threadSelectorButton);

    // Create thread name display
    this.threadNameDisplay = document.createElement('span');
    this.threadNameDisplay.className = 'sage-ai-thread-name';
    this.threadNameDisplay.textContent =
      this.chatHistoryManager.getCurrentThread()?.name || 'New Chat';
    toolbar.appendChild(this.threadNameDisplay);

    // Create autorun checkbox container
    const checkboxContainer = document.createElement('div');
    checkboxContainer.className =
      'sage-ai-checkbox-container sage-ai-autorun-toggle sage-ai-control-base';

    this.autorunCheckbox = document.createElement('input');
    this.autorunCheckbox.id = 'sage-ai-autorun';
    this.autorunCheckbox.type = 'checkbox';
    this.autorunCheckbox.className = 'sage-ai-checkbox sage-ai-toggle-input';
    this.autorunCheckbox.title = 'Automatically run code without confirmation';

    const checkboxLabel = document.createElement('label');
    checkboxLabel.htmlFor = 'sage-ai-autorun';
    checkboxLabel.className = 'sage-ai-checkbox-label sage-ai-toggle-label';
    checkboxLabel.innerHTML = `
      <span class="sage-ai-toggle-switch"></span>
      Auto Run
    `;
    checkboxLabel.title = 'Automatically run code without confirmation';

    checkboxContainer.appendChild(this.autorunCheckbox);
    checkboxContainer.appendChild(checkboxLabel);

    // Create new chat button (previously reset button)
    this.newChatButton = document.createElement('button');
    this.newChatButton.className = 'sage-ai-reset-button sage-ai-control-base';
    this.newChatButton.innerHTML = `
      <svg width="16" height="17" viewBox="0 0 16 17" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3.3335 8.49992H12.6668M8.00016 3.83325V13.1666" stroke="var(--jp-ui-font-color0)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
    this.newChatButton.title = 'Start a new chat';
    this.newChatButton.addEventListener('click', () => this.createNewChat());

    // Create undo button
    this.undoButton = document.createElement('button');
    this.undoButton.className = 'sage-ai-undo-button sage-ai-control-base';
    this.undoButton.innerHTML = `
      <svg width="16" height="17" viewBox="0 0 16 17" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M5.99984 9.83341L2.6665 6.50008M2.6665 6.50008L5.99984 3.16675M2.6665 6.50008H9.6665C10.148 6.50008 10.6248 6.59492 11.0697 6.77919C11.5145 6.96346 11.9187 7.23354 12.2592 7.57402C12.5997 7.9145 12.8698 8.31871 13.0541 8.76357C13.2383 9.20844 13.3332 9.68523 13.3332 10.1667C13.3332 10.6483 13.2383 11.1251 13.0541 11.5699C12.8698 12.0148 12.5997 12.419 12.2592 12.7595C11.9187 13.1 11.5145 13.37 11.0697 13.5543C10.6248 13.7386 10.148 13.8334 9.6665 13.8334H7.33317" stroke="var(--jp-ui-font-color0)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
    this.undoButton.disabled = true;
    this.undoButton.title = 'No action to undo';
    this.undoButton.addEventListener('click', () => this.undoLastAction());

    // Create a button to show more options
    const moreOptionsButton = document.createElement('button');
    moreOptionsButton.className =
      'sage-ai-more-options-button sage-ai-icon-button-md';
    moreOptionsButton.innerHTML = `
      <svg width="18" height="19" viewBox="0 0 18 19" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M9 10.25C9.41421 10.25 9.75 9.91421 9.75 9.5C9.75 9.08579 9.41421 8.75 9 8.75C8.58579 8.75 8.25 9.08579 8.25 9.5C8.25 9.91421 8.58579 10.25 9 10.25Z" stroke="var(--jp-ui-font-color0)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M14.25 10.25C14.6642 10.25 15 9.91421 15 9.5C15 9.08579 14.6642 8.75 14.25 8.75C13.8358 8.75 13.5 9.08579 13.5 9.5C13.5 9.91421 13.8358 10.25 14.25 10.25Z" stroke="var(--jp-ui-font-color0)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M3.75 10.25C4.16421 10.25 4.5 9.91421 4.5 9.5C4.5 9.08579 4.16421 8.75 3.75 8.75C3.33579 8.75 3 9.08579 3 9.5C3 9.91421 3.33579 10.25 3.75 10.25Z" stroke="var(--jp-ui-font-color0)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
    moreOptionsButton.title = 'More options';
    moreOptionsButton.addEventListener('click', () => this.showMoreOptions());

    // Add buttons to toolbar
    toolbar.appendChild(checkboxContainer);
    // toolbar.appendChild(this.undoButton);
    toolbar.appendChild(this.newChatButton);
    toolbar.appendChild(moreOptionsButton);

    // Create chat history container
    const historyContainer = document.createElement('div');
    historyContainer.className = 'sage-ai-history-container';
    this.chatHistory = document.createElement('div');
    this.chatHistory.className = 'sage-ai-chat-history';
    this.chatHistory.setAttribute('data-is-scrolled-to-bottom', 'true');
    historyContainer.appendChild(this.chatHistory);

    // Create loading overlay for chat history
    // Start visible since we'll be loading chat history on initial load
    this.chatHistoryLoadingOverlay = document.createElement('div');
    this.chatHistoryLoadingOverlay.className =
      'sage-ai-chat-history-loading-overlay';
    this.chatHistoryLoadingOverlay.innerHTML = `
      <div class="sage-ai-loading-spinner"></div>
      <div class="sage-ai-loading-text">Loading chat history...</div>
    `;
    historyContainer.appendChild(this.chatHistoryLoadingOverlay);
    
    // Set the loading state in chat history manager from the start
    this.chatHistoryManager.startLoading();

    this.scrollDownButton = document.createElement('button');
    this.scrollDownButton.className = 'sage-ai-scroll-down-button hidden';
    this.scrollDownButton.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M8 10.25L12.5 5.75L13.25 6.5L8 11.75L2.75 6.5L3.5 5.75L8 10.25Z" fill="var(--jp-ui-font-color1" />
      </svg>
    `;
    this.scrollDownButton.addEventListener('click', () => {
      this.messageComponent.scrollToBottom();
      this.hideScrollDownButton();
    });
    historyContainer.appendChild(this.scrollDownButton);

    const chatHistoryResizeObserver = new ResizeObserver(() =>
      this.handleChatHistoryResize()
    );
    chatHistoryResizeObserver.observe(this.chatHistory);

    let userScrolled = false;
    let userScrollTimeout: NodeJS.Timeout | null = null;

    // Mark user-initiated scroll
    ['wheel', 'touchstart', 'keydown'].forEach(eventType => {
      window.addEventListener(eventType, () => {
        userScrolled = true;

        userScrollTimeout && clearTimeout(userScrollTimeout);
        userScrollTimeout = setTimeout(() => {
          userScrolled = false;
        }, 1000); // reset after 1s
      });
    });
    this.chatHistory.addEventListener('scroll', () => {
      // As the chat-history height change, we need to check if the user is scrolling
      // or the chat-history is being resized
      if (userScrolled) {
        const isScrolledToBottom = this.updateScrollAttribute();

        if (isScrolledToBottom) {
          this.hideScrollDownButton();
        } else {
          this.showScrollDownButton();
        }
      }
    });

    // Create the initial history widget
    this.historyWidget = new Widget({ node: historyContainer });

    this.llmStateDisplay = AppStateService.getLlmStateDisplay()!;

    this.planStateDisplay = AppStateService.getPlanStateDisplay();

    // Initialize more options display
    this.moreOptionsDisplay = new MoreOptionsDisplay({
      onRenameChat: () => this.handleRenameChat(),
      onDeleteChat: () => this.handleDeleteChat()
    });

    // Initialize message component with the chat history manager
    this.messageComponent = new ChatMessages(
      this.chatHistory,
      this.chatHistoryManager,
      AppStateService.getNotebookTools(),
      () => this.handleDisplayScrollDownButton()
    );

    setTimeout(async () => {
      const isAuthenticated = await JupyterAuthService.isAuthenticated();
      const isDemoMode = AppStateService.getState().isDemoMode;
      if (isDemoMode && !isAuthenticated) {
        this.chatInput.setPlaceholder(
          'Demo is read-only. Click Take Over to chat with SignalPilot about this notebook'
        );
      }
    }, 200);

    this.chatInput = new RichTextChatInput(
      'What would you like me to generate or analyze?'
    );

    this.newPromptCTA = document.createElement('div');
    this.newPromptCTA.className = 'sage-ai-new-prompt-cta';
    const text = document.createElement('p');
    text.textContent = 'Context bloated?';
    const chatCTA = document.createElement('a');
    chatCTA.textContent = 'Start a New Chat';
    chatCTA.onclick = () => {
      void this.createNewChat();
      return false; // Prevent default link behavior
    };
    this.newPromptCTA.appendChild(text);
    this.newPromptCTA.appendChild(chatCTA);
    this.newPromptCTA.style.display = 'none';

    this.newChatDisplayWidget = new NewChatDisplayWidget(
      {
        onPromptSelected: prompt => {
          this.inputManager.setInputValue(prompt);
          void this.inputManager.sendMessage();
          this.showHistoryWidget();
        },
        onRemoveDisplay: () => {
          this.showHistoryWidget();
        }
      },
      RECOMMENDED_PROMPTS
    );

    // Initialize UpdateBanner
    const extensions = AppStateService.getExtensions();
    if (extensions) {
      this.updateBanner = new UpdateBannerWidget(extensions);
      // Show banner on first launch
      this.updateBanner.showBanner();
    }

    // Add components to the layout
    layout.addWidget(new Widget({ node: toolbar }));
    layout.addWidget(this.historyWidget);
    layout.addWidget(this.newChatDisplayWidget);

    document.body.appendChild(
      this.updateBanner?.node || document.createElement('div')
    );

    this.inputManager = new ChatInputManager(
      this.chatInput,
      this.chatHistoryManager,
      AppStateService.getContentManager(),
      AppStateService.getToolService(),
      this,
      context => {
        // Handle context selection - add to ChatMessages
        this.messageComponent.addMentionContext(context);
        this.contextHandler.updateContextDisplay();
        console.log('Context added:', context);
      },
      contextId => {
        // Handle context removal - remove from ChatMessages
        this.messageComponent.removeMentionContext(contextId);
        this.contextHandler.updateContextDisplay();
        console.log(`Context removed: ${contextId}`);
      },
      () => this.createNewChat(), // Handle reset chat
      mode => {
        let displayName = '';
        let tools = [];

        switch (mode) {
          case 'ask':
            displayName = 'Ask';
            tools = AppStateService.getToolService().getAskModeTools();
            break;
          case 'fast':
            displayName = 'Hands-on';
            tools = AppStateService.getToolService().getFastModeTools();
            break;
          default:
            displayName = 'Agent';
            tools = AppStateService.getToolService().getTools();
        }

        this.messageComponent.addSystemMessage(
          `Mode switched to: ${displayName}`
        );

        if (tools.length > 0) {
          this.messageComponent.addSystemMessage(
            `Enabled tools: ${tools.map(t => t.name).join(', ')}`
          );
        }
      }
    );

    this.showHistoryWidget();
    void this.updateBanner?.checkForUpdates();

    this.messageComponent.setInputManager(this.inputManager);

    // Create the input container using the input manager
    const inputContainer = this.inputManager.createInputContainer();

    const inputContainerWidget = new Widget({
      node: this.inputManager.getInputContainer()!
    });

    // Create wrapper for state displays with fixed positioning and flexbox
    const stateDisplayContainer = document.createElement('div');
    stateDisplayContainer.className = 'sage-ai-state-display-container';
    this.stateDisplayContainer = stateDisplayContainer;

    // Widget nodes will get their styles from CSS classes
    const planStateNode = this.planStateDisplay.getWidget().node;
    const llmStateNode = this.llmStateDisplay.getWidget().node;

    // Helper function to check if an element is hidden
    const isElementHidden = (element: HTMLElement): boolean => {
      // Check if element has hidden class
      if (element.classList.contains('hidden')) {
        return true;
      }

      // Check computed display style (this accounts for inline styles)
      const computedStyle = window.getComputedStyle(element);
      if (computedStyle.display === 'none') {
        return true;
      }

      // Also check inline style directly as a fallback
      if (element.style.display === 'none') {
        return true;
      }

      return false;
    };

    // Function to update dynamic bottom positioning based on visible siblings
    const updateDynamicBottomPositions = () => {
      // Use requestAnimationFrame to ensure DOM is fully updated
      requestAnimationFrame(() => {
        // Small delay to ensure all class changes are applied
        setTimeout(() => {
          const children = Array.from(
            stateDisplayContainer.children
          ) as HTMLElement[];

          children.forEach((child, index) => {
            // Count visible siblings after this element
            let visibleSiblingsAfter = 0;
            for (let i = index + 1; i < children.length; i++) {
              if (!isElementHidden(children[i])) {
                visibleSiblingsAfter++;
              }
            }

            // Calculate bottom value: -12px for each visible sibling after + -12px for itself
            // If this element is the last visible one, it should be -12px
            const bottomValue = -12 * (1 + visibleSiblingsAfter);
            child.style.bottom = `${bottomValue}px`;
          });
        }, 0);
      });
    };

    // Function to update container positioning based on input container height
    const updateWrapperPositions = () => {
      // Update dynamic bottom positions first
      updateDynamicBottomPositions();

      // Use requestAnimationFrame to ensure DOM updates are complete before calculating heights
      requestAnimationFrame(() => {
        setTimeout(() => {
          this.handleDisplayScrollDownButton();
        }, 200); // Additional delay to ensure transitions/animations complete
      });
    };

    // Store the positioning function for later use
    (this as any).updateStateDisplayPositions = updateWrapperPositions;

    // // Connect to state change signals instead of overriding methods
    // this.llmStateConnection = this.llmStateDisplay.stateChanged.connect(() => {
    //   setTimeout(updateWrapperPositions, 100);
    // });

    this.planStateConnection = this.planStateDisplay.stateChanged.connect(
      () => {
        setTimeout(() => {
          updateDynamicBottomPositions();
          updateWrapperPositions();
        }, 100);
      }
    );

    // Initial positioning
    setTimeout(() => {
      updateDynamicBottomPositions();
      updateWrapperPositions();
    }, 100); // Increased timeout to ensure DOM is rendered

    // Update positioning when window resizes or layout changes
    this.resizeObserver = new ResizeObserver(updateWrapperPositions);
    this.resizeObserver.observe(inputContainer);

    // Add MutationObserver to watch for content changes in state displays
    this.mutationObserver = new MutationObserver(mutations => {
      // Check if any mutation is a class change or child list change that might affect visibility
      const hasRelevantChange = mutations.some(
        mutation =>
          (mutation.type === 'attributes' &&
            mutation.attributeName === 'class') ||
          mutation.type === 'childList'
      );

      if (hasRelevantChange) {
        // Update dynamic bottom positions when visibility changes or children are added/removed
        updateDynamicBottomPositions();
      }

      setTimeout(updateWrapperPositions, 100); // Increased delay to ensure DOM updates complete
    });

    // Observe both state displays for changes (mainly for expanded content size changes)
    this.mutationObserver.observe(this.llmStateDisplay.node, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class'] // Focus on class changes like 'hidden'
    });

    this.mutationObserver.observe(this.planStateDisplay.node, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class'] // Focus on class changes and content size changes
    });

    // Observe the container itself for child changes (e.g., when demo panel is added/removed)
    this.mutationObserver.observe(stateDisplayContainer, {
      childList: true,
      attributes: true,
      attributeFilter: ['class'],
      subtree: false
    });

    // Store the update function so it can be called externally if needed
    (this as any).updateDynamicBottomPositions = updateDynamicBottomPositions;

    // Initial positioning
    updateDynamicBottomPositions();

    // Add widgets directly to container in order: plan state, LLM state, input spacer
    stateDisplayContainer.appendChild(planStateNode);
    stateDisplayContainer.appendChild(llmStateNode);

    // Add the container to the layout
    layout.addWidget(new Widget({ node: stateDisplayContainer }));
    layout.addWidget(inputContainerWidget);
    layout.addWidget(new Widget({ node: this.newPromptCTA }));
    layout.addWidget(this.moreOptionsDisplay);

    // Initialize helper classes
    this.threadManager = new ThreadManager(
      this.chatHistoryManager,
      this.messageComponent,
      this.chatService,
      this.threadNameDisplay,
      this.node
    );

    this.uiHelper = new ChatUIHelper(
      this.chatHistory,
      this.messageComponent,
      this.llmStateDisplay
    );

    // Initialize context handler early so it can be used in other components
    this.contextHandler = new ChatboxContext(
      this.messageComponent,
      this.inputManager,
      this.node
    );

    // Initialize the conversation service with the diffManager
    this.conversationService = new ConversationService(
      this.chatService,
      AppStateService.getToolService(),
      AppStateService.getContentManager(),
      this.messageComponent,
      this.chatHistory,
      actionHistory,
      {
        updateLoadingIndicator: (text?: string) =>
          this.updateLoadingIndicator(text),
        removeLoadingIndicator: () => this.removeLoadingIndicator(),
        hideLoadingIndicator: () => this.llmStateDisplay.hide()
      }
    );

    // Set the diff manager in the conversation service if available
    const diffManager = AppStateService.getState().notebookDiffManager;
    if (diffManager) {
      this.conversationService.setDiffManager(diffManager);
    }

    // Set up event handlers
    this.setupEventHandlers();

    // Initialize services
    void this.initializeServices();

    // Subscribe to AppState changes to re-initialize services when Claude settings change
    this.subscribeToAppStateChanges();

    // Set dependencies in input manager for sendMessage and revertAndSend
    this.inputManager.setDependencies({
      chatService: this.chatService,
      conversationService: this.conversationService,
      messageComponent: this.messageComponent,
      uiHelper: this.uiHelper,
      contextHandler: this.contextHandler,
      sendButton: this.inputManager.getSendButton()!,
      modeSelector: this.inputManager.getModeSelector()!,
      cancelMessage: () => this.cancelMessage(),
      onMessageSent: () => this.showHistoryWidget()
    });

    // Set up polling to update undo button state
    setInterval(() => this.updateUndoButtonState(), 1000);

    // Initialize managers

    const waitingUserReplyBoxManager =
      AppStateService.getWaitingUserReplyBoxManager();
    waitingUserReplyBoxManager.initialize(this.chatHistory);

    // Set up the continue callback to send "Continue" message
    waitingUserReplyBoxManager.setContinueCallback(() => {
      this.sendContinueMessage();
    });

    // Set up the prompt callback to send custom prompt messages
    waitingUserReplyBoxManager.setPromptCallback((prompt: string) => {
      this.sendPromptMessage(prompt);
    });

    // Initialize context display after everything is set up
    this.contextHandler.updateContextDisplay();

    // Note: Don't show new chat display here - it will be handled by setNotebookId()
    // and restoreLastThreadForNotebook() which run after the constructor completes.
    // Showing it here causes a race condition where the new chat display appears
    // before the actual chat is restored.

    // Mark as ready initially - will be set to false if launcher mode is activated
    this.isReady = true;
  }

  private handleDisplayScrollDownButton(): void {
    if (this.isScrolledToBottom()) {
      this.hideScrollDownButton();
    } else {
      this.showScrollDownButton();
    }
  }

  private showScrollDownButton(): void {
    this.scrollDownButton.classList.remove('hidden');
  }

  private hideScrollDownButton(): void {
    this.scrollDownButton.classList.add('hidden');
  }

  private handleChatHistoryResize(): void {
    if (this.isScrolledToBottom()) {
      this.scrollChatHistoryToBottom();
    } else {
      this.handleDisplayScrollDownButton();
    }
  }

  public scrollChatHistoryToBottom(): void {
    this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
  }

  private updateScrollAttribute(): boolean {
    const scrollTop = this.chatHistory.scrollTop;
    const scrollHeight = this.chatHistory.scrollHeight;
    const isScrolledToBottom =
      Math.ceil(scrollTop + this.chatHistory.clientHeight) >= scrollHeight;

    this.chatHistory.setAttribute(
      'data-is-scrolled-to-bottom',
      isScrolledToBottom.toString()
    );

    return isScrolledToBottom;
  }

  private isScrolledToBottom(): boolean {
    return (
      this.chatHistory.getAttribute('data-is-scrolled-to-bottom') === 'true'
    );
  }

  /**
   * Show the chat history loading overlay
   */
  private showChatHistoryLoader(): void {
    if (this.chatHistoryLoadingOverlay) {
      this.chatHistoryLoadingOverlay.classList.remove('hidden');
    }
  }

  /**
   * Hide the chat history loading overlay
   */
  private hideChatHistoryLoader(): void {
    if (this.chatHistoryLoadingOverlay) {
      this.chatHistoryLoadingOverlay.classList.add('hidden');
    }
  }

  public updateNotebookId(newId: string): void {
    AppStateService.setCurrentNotebookId(newId);
    this.threadManager.updateNotebookId(newId);
    this.conversationService.updateNotebookId(newId);
  }

  // Backward compatibility method
  public updateNotebookPath(newPath: string): void {
    this.updateNotebookId(newPath);
  }

  /**
   * Get the state display container element
   * @returns The state display container HTMLDivElement or null if not initialized
   */
  public getStateDisplayContainer(): HTMLDivElement | null {
    return this.stateDisplayContainer;
  }

  /**
   * Public method to update dynamic bottom positions
   * Can be called externally when needed
   */
  public updateDynamicBottomPositions(): void {
    // This will be set by the internal function
    if ((this as any).updateDynamicBottomPositions) {
      (this as any).updateDynamicBottomPositions();
    }
  }

  /**
   * Setup event handlers
   */
  private setupEventHandlers(): void {
    // Add click event to open left side banner
    this.threadSelectorButton.addEventListener('click', () => {
      this.threadManager.openBanner();
    });

    // Add event listener to autorun checkbox to update the conversation service
    this.autorunCheckbox.addEventListener('change', () => {
      this.conversationService.setAutoRun(this.autorunCheckbox.checked);

      // Display a system message to confirm the change
      if (this.autorunCheckbox.checked) {
        this.messageComponent.addSystemMessage(
          'Auto-run mode enabled. Code will execute automatically without confirmation.'
        );
      } else {
        this.messageComponent.addSystemMessage(
          'Auto-run mode disabled. You will be prompted for code execution.'
        );
      }
    });
  }

  /**
   * Initialize all services
   */
  private async initializeServices(): Promise<void> {
    try {
      // Get configuration from server
      AppStateService.setConfig(await ConfigService.getConfig());

      // Initialize chat service with config from server
      const initialized = await this.chatService.initialize();
      console.log('Chat service initialized:', initialized);

      if (initialized) {
        // const modelName = this.chatService.getModelName();
        // this.messageComponent.addSystemMessage(
        //   `✅ Configuration loaded successfully. Using model: ${modelName}`
        // );
      } else {
        // this.messageComponent.addSystemMessage(
        //   '⚠️ Failed to initialize with API key from config. Please check the server.'
        // );
      }

      // Initialize tool service
      const toolService = AppStateService.getToolService();
      await toolService.initialize();
      console.log('Connected to MCP server successfully.');
      console.log(
        `Loaded ${toolService.getTools().length} tools from MCP server.`
      );
    } catch (error) {
      console.error('Failed to connect to MCP server:', error);
      this.messageComponent.addSystemMessage(
        '❌ Failed to connect to MCP server. Some features may not work.'
      );
    }
  }

  /**
   * Update the notebook ID and load its chat history
   * @param notebookId ID of the notebook
   */
  public async setNotebookId(notebookId: string | undefined): Promise<void> {
    if (!notebookId) {
      AppStateService.setCurrentNotebookId(null);
      this.threadManager.setNotebookId(null);
      return;
    }

    if (this.lastNotebookId === notebookId) {
      return;
    }

    this.lastNotebookId = notebookId;

    // Show loading overlay while chat history is being loaded
    this.showChatHistoryLoader();

    // Set loading state BEFORE triggering the notebook change
    // This ensures the loader stays visible during the actual loading
    this.chatHistoryManager.startLoading();

    AppStateService.setCurrentNotebookId(notebookId);

    // Update the thread manager with the current notebook ID
    this.threadManager.setNotebookId(notebookId);

    // Update conversation service with the current notebook ID
    this.conversationService.setNotebookId(notebookId);

    // Wait for the chat history manager to finish loading
    // This triggers the loading in ChatHistoryManager.setCurrentNotebook
    while (this.chatHistoryManager.isLoading()) {
      await new Promise(resolve => setTimeout(resolve, 50));
    }

    // Restore the last thread for this notebook (this will also handle showing the appropriate widget)
    await this.restoreLastThreadForNotebook(notebookId);

    // Hide loading overlay once everything is loaded
    this.hideChatHistoryLoader();

    // Refresh user message history when switching notebooks
    void this.inputManager.loadUserMessageHistory();

    // Update context cells indicator when switching notebooks
    const contextManager = AppStateService.getState().notebookContextManager;
    if (contextManager) {
      const contextCells = contextManager.getContextCells(notebookId);
      this.contextHandler.updateContextCellsIndicator(contextCells.length);
    }

    // Update plan state display based on the notebook's plan cell (similar to activateSage.ts)
    const notebookTools = AppStateService.getState().notebookTools;
    if (notebookTools) {
      const planCell = notebookTools.getPlanCell(notebookId);

      if (planCell) {
        const currentStep =
          (planCell.model.sharedModel.getMetadata().custom as any)
            ?.current_step_string || '';
        const nextStep =
          (planCell.model.sharedModel.getMetadata().custom as any)
            ?.next_step_string || '';
        const source = planCell.model.sharedModel.getSource() || '';

        void this.planStateDisplay.updatePlan(
          currentStep || 'Plan active',
          nextStep,
          source,
          false
        );
      } else {
        // No plan cell found, hide the plan display
        void this.planStateDisplay.updatePlan(undefined, undefined, undefined);
      }
    }

    // Hide LLM state display when switching notebooks (will be shown if needed during chat)
    this.llmStateDisplay.hide();
  }

  /**
   * Completely re-initialize the chatbox state for a notebook transition
   * This ensures clean state when transitioning from launcher to notebook
   * @param notebookId ID of the notebook to reinitialize for
   */
  public async reinitializeForNotebook(notebookId: string): Promise<void> {
    console.log(`[ChatBoxWidget] Re-initializing for notebook: ${notebookId}`);

    // Cancel any ongoing requests
    if (this.inputManager.getIsProcessingMessage()) {
      this.cancelMessage();
    } else {
      this.chatService.cancelRequest();
    }

    // Reset the lastNotebookId to force a full reload
    this.lastNotebookId = null;

    // Show loading overlay
    this.showChatHistoryLoader();

    // Set loading state BEFORE re-initializing
    this.chatHistoryManager.startLoading();

    // Update AppStateService with the notebook ID
    AppStateService.setCurrentNotebookId(notebookId);

    // Update the thread manager with the current notebook ID
    this.threadManager.setNotebookId(notebookId);

    // Update conversation service with the current notebook ID
    this.conversationService.setNotebookId(notebookId);

    // Re-initialize the chat history manager for this notebook
    // This will force a fresh load from storage

    const currentThread =
      await this.chatHistoryManager.reinitializeForNotebook(notebookId);

    // Restore the thread UI
    await this.restoreLastThreadForNotebook(notebookId);

    // Hide loading overlay
    this.hideChatHistoryLoader();

    // Refresh user message history
    await this.inputManager.loadUserMessageHistory();

    // Update context cells indicator
    this.contextHandler.updateContextDisplay();

    // Update notebook state - find plan cell if present
    const notebookTools = AppStateService.getNotebookTools();
    if (notebookTools) {
      const planCell = notebookTools.getPlanCell(notebookId);

      if (planCell) {
        const currentStep =
          (planCell.model.sharedModel.getMetadata().custom as any)
            ?.current_step_string || '';
        const nextStep =
          (planCell.model.sharedModel.getMetadata().custom as any)
            ?.next_step_string || '';
        const source = planCell.model.sharedModel.getSource() || '';

        void this.planStateDisplay.updatePlan(
          currentStep || 'Plan active',
          nextStep,
          source,
          false
        );
      } else {
        // No plan cell found, hide the plan display
        void this.planStateDisplay.updatePlan(undefined, undefined, undefined);
      }
    }

    // Hide LLM state display
    this.llmStateDisplay.hide();

    // Set the lastNotebookId to prevent duplicate reloads
    this.lastNotebookId = notebookId;

    console.log(
      `[ChatBoxWidget] Re-initialization complete for notebook: ${notebookId}`
    );

    console.log(
      '[ChatBoxWidget] Current thread after reinitialization:',
      currentThread
    );
    console.log(
      '[ChatBoxWidget] Current thread messages:',
      currentThread?.messages
    );

    if (currentThread.needsContinue) {
      console.log('CONTINUING MESSAGE...');
      await this.inputManager.continueMessage();
    }
  }

  /**
   * Try to restore the last selected thread for a notebook
   * @param notebookId ID of the notebook
   */
  private async restoreLastThreadForNotebook(
    notebookId: string
  ): Promise<void> {
    try {
      // Get the current thread that was already set by ChatHistoryManager.setCurrentNotebook
      // This uses localStorage first, then falls back to other logic
      const currentThread = this.chatHistoryManager.getCurrentThread();

      if (currentThread && currentThread.messages.length > 0) {
        // Found a thread with messages, load it
        console.log(
          `[ChatBoxWidget] Restoring current thread: ${currentThread.name} for notebook ${notebookId}`
        );

        await this.showHistoryWidgetFromThread(currentThread);
        return;
      } else if (currentThread) {
        // Thread exists but is empty, show new chat display
        console.log(
          `[ChatBoxWidget] Current thread is empty for notebook ${notebookId}, showing new chat display`
        );
        await this.messageComponent.loadFromThread(currentThread);
        if (currentThread.messages.length === 0) {
          this.showNewChatDisplay();
        }
        return;
      } else {
        // No thread at all (shouldn't happen after setCurrentNotebook)
        console.log(
          `[ChatBoxWidget] No current thread for notebook ${notebookId}, showing default view`
        );
        await this.createNewChat();
        this.showNewChatDisplay();
        return;
      }
    } catch (error) {
      console.warn(
        `[ChatBoxWidget] Failed to restore last thread for notebook ${notebookId}:`,
        error
      );
      // Fallback to default behavior
      await this.showNewChatDisplayOrHistory();
    }
  }

  /**
   * Create a new chat thread
   */
  private async createNewChat(): Promise<void> {
    // Hide the waiting reply box when user cancels
    AppStateService.getWaitingUserReplyBoxManager().hide();

    // Check if we're in launcher mode
    const isLauncherActive = AppStateService.isLauncherActive();

    if (isLauncherActive) {
      // In launcher mode, just clear the chat without creating a thread or saving
      console.log(
        '[ChatBox] New Chat in launcher mode - clearing without saving'
      );

      // Cancel any ongoing request
      if (this.inputManager.getIsProcessingMessage()) {
        this.cancelMessage();
      } else {
        this.chatService.cancelRequest();
      }

      // Clear the message history directly without saving
      this.messageComponent.messageHistory = [];
      this.chatHistory.innerHTML = '';

      // Clear action history
      this.conversationService.clearActionHistory();
      this.updateUndoButtonState();

      // Clear mention contexts
      this.messageComponent.setMentionContexts(new Map());
      this.contextHandler.updateContextDisplay();

      // Hide displays
      this.llmStateDisplay.hide();
      this.planStateDisplay.hide();

      // Hide DiffNavigationWidget
      const diffNavigationWidget =
        AppStateService.getDiffNavigationWidgetSafe();
      if (diffNavigationWidget) {
        diffNavigationWidget.hidePendingDiffs();
      }

      // Explicitly set the thread name display to "New Chat" for launcher mode
      this.threadNameDisplay.textContent = 'New Chat';

      // Show the new chat display
      this.showNewChatDisplay();

      return;
    }

    // Normal mode - require notebook and create proper thread
    const currentNotebookId = AppStateService.getCurrentNotebookId();
    if (!currentNotebookId) {
      this.messageComponent.addSystemMessage('Please open a notebook first.');
      return;
    }

    // Cancel any ongoing request - make sure to update the UI state as well
    if (this.inputManager.getIsProcessingMessage()) {
      this.cancelMessage();
    } else {
      // Even if not visibly processing, cancel any pending requests
      this.chatService.cancelRequest();
    }

    // Create a new thread
    const newThread = await this.threadManager.createNewThread();

    if (newThread) {
      // Clear action history
      this.conversationService.clearActionHistory();
      this.updateUndoButtonState();
      this.contextHandler.updateContextDisplay();

      // Switch to new chat display since there are no messages
      this.showNewChatDisplay();
      this.llmStateDisplay.hide();

      // Also hide DiffNavigationWidget when creating new chat
      const diffNavigationWidget =
        AppStateService.getDiffNavigationWidgetSafe();
      if (diffNavigationWidget) {
        diffNavigationWidget.hidePendingDiffs();
      }
    }
  }

  /**
   * Update the state of the undo button based on available actions
   */
  private updateUndoButtonState(): void {
    if (this.conversationService.canUndo()) {
      const actionDesc = this.conversationService.getLastActionDescription();
      this.undoButton.disabled = false;
      this.undoButton.title = `Undo: ${actionDesc}`;
    } else {
      this.undoButton.disabled = true;
      this.undoButton.title = 'No action to undo';
    }
  }

  /**
   * Undo the last action
   */
  private async undoLastAction(): Promise<void> {
    if (!this.conversationService.canUndo()) {
      return;
    }

    // Disable the button during undo
    this.undoButton.disabled = true;
    this.undoButton.title = 'Undoing...';

    try {
      // Perform the undo operation
      await this.conversationService.undoLastAction();
    } catch (error) {
      console.error('Error during undo:', error);
      this.messageComponent.addErrorMessage(
        `Error during undo: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    } finally {
      // Update the button state after undo completes
      this.updateUndoButtonState();
    }
  }

  /**
   * Cancel the current message processing
   */
  public cancelMessage(): void {
    if (!this.inputManager.getIsProcessingMessage()) {
      return;
    }

    console.log('Cancelling message...');
    console.log(this.inputManager.getIsProcessingMessage());

    // Cancel the request in the chatService
    this.chatService.cancelRequest();

    // Update state immediately to prevent any further processing
    this.inputManager.setIsProcessingMessage(false);

    // Remove loading indicator
    this.uiHelper.removeLoadingIndicator();

    // this.messageComponent.addSystemMessage('Request cancelled by user.');
    this.messageComponent.removeLoadingText();
    this.uiHelper.updateSendButton(this.inputManager.getSendButton()!, false);
    this.uiHelper.disableSendButton(this.inputManager.getSendButton()!);
    AppStateService.getPlanStateDisplay().setLoading(false);
    this.uiHelper.updateAgentModeElement(
      this.inputManager.getModeSelector()!,
      false
    );

    // Set needsContinue to false when user cancels the request
    const currentThread = this.chatHistoryManager.getCurrentThread();
    if (currentThread && currentThread.needsContinue) {
      currentThread.needsContinue = false;
      console.log(
        '[ChatBoxWidget] Set needsContinue to false after user cancelled request'
      );
    }

    // Check if there are pending diffs and show approval dialog if needed
    const diffManager = AppStateService.getState().notebookDiffManager;
    if (
      diffManager &&
      diffManager.hasPendingDiffs() &&
      !diffManager.isDialogOpen()
    ) {
      // Show pending diffs in LLMStateDisplay
      if (this.llmStateDisplay) {
        const currentNotebookId = AppStateService.getCurrentNotebookId();
        this.llmStateDisplay.showPendingDiffs(currentNotebookId);

        // Also show diffs in DiffNavigationWidget for synchronized display
        const diffNavigationWidget =
          AppStateService.getDiffNavigationWidgetSafe();
        if (diffNavigationWidget) {
          diffNavigationWidget.showPendingDiffs(currentNotebookId);
        }
      }

      // Use setTimeout to ensure UI updates before showing the dialog
      setTimeout(async () => {
        const currentNotebookId = AppStateService.getCurrentNotebookId();
        await diffManager?.showCancellationApprovalDialog(
          this.chatHistory,
          currentNotebookId // Pass the notebook ID
        );
      }, 100);
    } else {
      this.llmStateDisplay.show();
      this.llmStateDisplay.hide();
    }
  }

  protected onAfterShow(): void {
    this.inputManager.focus();
  }

  /**
   * Update the loading indicator - exposed for the conversation service to use
   */
  public updateLoadingIndicator(text: string = 'Generating...'): void {
    this.uiHelper.updateLoadingIndicator(text);
  }

  /**
   * Remove the loading indicator - exposed for the conversation service to use
   */
  public removeLoadingIndicator(): void {
    this.uiHelper.removeLoadingIndicator();
  }

  /**
   * Handle a cell being added to context
   * @param notebookPath Path of the notebook containing the cell
   * @param cellId ID of the cell added to context
   */
  public onCellAddedToContext(notebookPath: string): void {
    this.contextHandler.onCellAddedToContext(notebookPath);
  }

  /**
   * Handle a cell being removed from context
   * @param notebookPath Path of the notebook containing the cell
   * @param cellId ID of the cell removed from context
   */
  public onCellRemovedFromContext(notebookPath: string): void {
    this.contextHandler.onCellRemovedFromContext(notebookPath);
  }

  /**
   * Show new chat display or history based on current thread state
   */
  public async showNewChatDisplayOrHistory(): Promise<void> {
    const currentThread = this.chatHistoryManager.getCurrentThread();
    const hasMessages = currentThread && currentThread.messages.length > 0;

    if (hasMessages) {
      await this.showHistoryWidgetFromThread(currentThread);
    } else {
      this.showNewChatDisplay();
    }
  }

  public showNewChatCta(): void {
    if (this.newPromptCTA) {
      this.newPromptCTA.style.display = 'flex';
    }
  }

  public hideNewChatCta(): void {
    if (this.newPromptCTA) {
      this.newPromptCTA.style.display = 'none';
    }
  }

  /**
   * Update new prompt CTA visibility based on token usage percentage
   * Shows when token usage >= 40%
   */
  public updateNewPromptCtaVisibility(tokenPercentage: number): void {
    if (this.newPromptCTA) {
      if (tokenPercentage >= 40) {
        this.newPromptCTA.style.display = 'flex';
      } else {
        this.newPromptCTA.style.display = 'none';
      }
    }
  }

  /**
   * Show the new chat display widget
   */
  public showNewChatDisplay(): void {
    if (this.messageComponent.getMessageHistory().length > 0) {
      return;
    }
    if (this.newChatDisplayWidget) {
      this.newChatDisplayWidget.node.style.display = 'flex';
    }
    if (this.historyWidget) {
      this.historyWidget.node.style.display = 'none';
    }

    this.hideNewChatCta();
  }

  /**
   * Show the history widget
   */
  public showHistoryWidget(): void {
    if (this.newChatDisplayWidget) {
      this.newChatDisplayWidget.node.style.display = 'none';
    }
    if (this.historyWidget) {
      this.historyWidget.node.style.display = 'block';
    }

    // Update CTA visibility based on current token percentage
    // This will be set correctly by updateTokenProgress, but we trigger it here
    // to ensure immediate update when history widget is shown
    this.inputManager.updateTokenProgress();
  }

  public async showHistoryWidgetFromThread(thread: IChatThread): Promise<void> {
    await this.threadManager.selectThread(thread.id);
    this.showHistoryWidget();
  }

  /**
   * Show the more options popover
   */
  private showMoreOptions(): void {
    const moreOptionsButton = this.node.querySelector(
      '.sage-ai-more-options-button'
    ) as HTMLButtonElement;
    if (moreOptionsButton && this.moreOptionsDisplay) {
      this.moreOptionsDisplay.showPopover(moreOptionsButton);
    }
  }

  /**
   * Handle rename chat action
   */
  private async handleRenameChat(): Promise<void> {
    const currentThread = this.chatHistoryManager.getCurrentThread();
    if (!currentThread) {
      this.messageComponent.addSystemMessage('No active chat to rename.');
      return;
    }

    const newName = prompt('Enter new chat name:', currentThread.name);
    if (newName && newName.trim() !== '' && newName !== currentThread.name) {
      const success = this.chatHistoryManager.renameCurrentThread(
        newName.trim()
      );
      if (success) {
        this.threadNameDisplay.textContent = newName.trim();
        this.messageComponent.addSystemMessage(
          `Chat renamed to: ${newName.trim()}`
        );
      } else {
        this.messageComponent.addSystemMessage('Failed to rename chat.');
      }
    }
  }

  /**
   * Handle delete chat action
   */
  private async handleDeleteChat(): Promise<void> {
    const currentThread = this.chatHistoryManager.getCurrentThread();
    if (!currentThread) {
      this.messageComponent.addSystemMessage('No active chat to delete.');
      return;
    }

    const confirmDelete = confirm(
      `Are you sure you want to delete the chat "${currentThread.name}"? This action cannot be undone.`
    );
    if (confirmDelete) {
      const deletedThreadName = currentThread.name;
      const success = this.chatHistoryManager.deleteThread(currentThread.id);
      if (success) {
        this.messageComponent.addSystemMessage(
          `Chat "${deletedThreadName}" has been deleted.`
        );

        // Update thread name display for the new current thread
        const newCurrentThread = this.chatHistoryManager.getCurrentThread();
        if (newCurrentThread) {
          this.threadNameDisplay.textContent = newCurrentThread.name;
          await this.messageComponent.loadFromThread(newCurrentThread);
          if (newCurrentThread.messages.length > 0) {
            this.showHistoryWidget();
          } else {
            this.showNewChatDisplay();
          }
        } else {
          this.showNewChatDisplay();
        }
      } else {
        this.messageComponent.addSystemMessage('Failed to delete chat.');
      }
    }
  }

  /**
   * Subscribe to AppState changes to re-initialize services when Claude settings change
   */
  private subscribeToAppStateChanges(): void {
    // Store initial Claude settings to compare against
    const initialClaudeSettings = AppStateService.getClaudeSettings();
    this.lastClaudeSettings = {
      claudeApiKey: initialClaudeSettings.claudeApiKey,
      claudeModelId: initialClaudeSettings.claudeModelId,
      claudeModelUrl: initialClaudeSettings.claudeModelUrl
    };

    let lastLauncherState = AppStateService.isLauncherActive();
    let lastAutoRunState = AppStateService.getAutoRun();

    this.appStateSubscription = AppStateService.changes.subscribe(state => {
      // Check if auto-run state has changed
      const currentAutoRunState = state.autoRun;
      if (lastAutoRunState !== currentAutoRunState) {
        console.log(`[ChatBox] Auto-run state changed: ${currentAutoRunState}`);
        lastAutoRunState = currentAutoRunState;

        // Sync the checkbox without triggering the change event
        this.autorunCheckbox.checked = currentAutoRunState;
      }

      // Check if launcher state has changed
      const currentLauncherState = state.isLauncherActive;
      if (lastLauncherState !== currentLauncherState) {
        console.log(
          `[ChatBox] Launcher state changed: ${currentLauncherState}`
        );
        lastLauncherState = currentLauncherState;

        if (currentLauncherState) {
          // Switched to launcher - clear chat without saving and hide plan display
          this.handleSwitchToLauncher();
        }
        // No else needed - when switching from launcher to notebook,
        // setNotebookId() will be called via NotebookChatContainer.switchToNotebook()
      }

      // Check if Claude settings have changed
      const currentClaudeSettings = {
        claudeApiKey: state.settings.claudeApiKey,
        claudeModelId: state.settings.claudeModelId,
        claudeModelUrl: state.settings.claudeModelUrl
      };

      const hasChanged =
        !this.lastClaudeSettings ||
        this.lastClaudeSettings.claudeApiKey !==
          currentClaudeSettings.claudeApiKey ||
        this.lastClaudeSettings.claudeModelId !==
          currentClaudeSettings.claudeModelId ||
        this.lastClaudeSettings.claudeModelUrl !==
          currentClaudeSettings.claudeModelUrl;

      if (hasChanged) {
        console.log(
          'Claude settings changed, re-initializing chat service...',
          {
            previous: this.lastClaudeSettings,
            current: currentClaudeSettings
          }
        );

        this.lastClaudeSettings = currentClaudeSettings;
        void this.reinitializeChatService();
      }
    });
  }

  /**
   * Re-initialize the chat service with updated settings
   */
  private async reinitializeChatService(): Promise<void> {
    try {
      console.log(
        'Re-initializing chat service with updated Claude settings...'
      );

      // Re-initialize the chat service (it will automatically pick up new settings from AppState)
      const initialized = await this.chatService.initialize();
      console.log('Chat service re-initialized:', initialized);

      if (initialized) {
        // const modelName = this.chatService.getModelName();
        // this.messageComponent.addSystemMessage(
        //   `✅ Settings updated successfully. Using model: ${modelName}`
        // );
      } else {
        this.messageComponent.addSystemMessage(
          '⚠️ Failed to re-initialize with updated settings. Please check your API key.'
        );
      }
    } catch (error) {
      console.error('Failed to re-initialize chat service:', error);
      this.messageComponent.addSystemMessage(
        '⚠️ Error updating settings. Please try again.'
      );
    }
  }

  /**
   * Handle switching to launcher mode - save current chat then clear
   */
  private handleSwitchToLauncher(): void {
    console.log(
      '[ChatBox] Switching to launcher mode - saving current chat before clearing'
    );

    // Mark as not ready while we're setting up launcher mode
    this.isReady = false;
    console.log('[ChatBox] Marked as not ready during launcher setup');

    // Hide the chat history loader if it's showing
    this.hideChatHistoryLoader();

    // Save the current chat state before switching to launcher
    // This ensures we don't lose the notebook's chat when switching away
    const currentNotebookId = AppStateService.getCurrentNotebookId();
    if (currentNotebookId && this.messageComponent.messageHistory.length > 0) {
      console.log(
        `[ChatBox] Saving chat state for notebook ${currentNotebookId} before switching to launcher`
      );
      this.chatHistoryManager.updateCurrentThreadMessages(
        this.messageComponent.messageHistory,
        this.messageComponent.getMentionContexts()
      );
    }

    // Cancel any ongoing request
    if (this.inputManager.getIsProcessingMessage()) {
      this.cancelMessage();
    } else {
      this.chatService.cancelRequest();
    }

    // Clear the message history directly (already saved above)
    this.messageComponent.messageHistory = [];
    this.chatHistory.innerHTML = '';

    // Clear action history
    this.conversationService.clearActionHistory();
    this.updateUndoButtonState();

    // Clear mention contexts
    this.messageComponent.setMentionContexts(new Map());
    this.contextHandler.updateContextDisplay();

    // Update thread manager to clear notebook ID (will show "No notebook selected" in All Chats menu)
    this.threadManager.setNotebookId(null);

    // CRITICAL: Clear the ChatHistoryManager's current notebook ID
    // This prevents launcher chat messages from being saved to the last notebook's thread
    this.chatHistoryManager.clearCurrentNotebook();

    // Explicitly set the thread name display to "New Chat" for launcher mode
    this.threadNameDisplay.textContent = 'New Chat';

    // Clear lastNotebookId so that switching back to a notebook will properly reload
    this.lastNotebookId = null;

    // Hide the plan display
    this.planStateDisplay.hide();

    // Hide LLM state display
    this.llmStateDisplay.hide();

    // Hide DiffNavigationWidget
    const diffNavigationWidget = AppStateService.getDiffNavigationWidgetSafe();
    if (diffNavigationWidget) {
      diffNavigationWidget.hidePendingDiffs();
    }

    // Show the new chat display
    this.showNewChatDisplay();

    // Mark chatbox as ready after launcher setup is complete
    this.isReady = true;
    console.log('[ChatBox] Launcher setup complete, chatbox marked as ready');

    // Automatically send welcome message after a short delay to ensure UI is ready
    setTimeout(async () => {
      await this.sendWelcomeMessage();
    }, 100);

    console.log('[ChatBox] Launcher mode: Chat cleared without saving');
  }

  /**
   * Start the welcome message immediately (pre-load during demo)
   * This sends the message but keeps it hidden until showWelcomeMessage is called
   */
  public startWelcomeMessagePreload(): Promise<void> {
    // Only start welcome message once
    if (this.welcomeMessagePromise) {
      console.log(
        '[ChatBox] Welcome message already started, returning existing promise'
      );
      return this.welcomeMessagePromise;
    }

    console.log('[ChatBox] Starting welcome message pre-load');
    this.isWelcomeMessageHidden = true;

    // Tell the message component to hide streaming welcome messages
    this.messageComponent.setWelcomeMessageHiddenMode(true);

    this.welcomeMessagePromise = this.sendWelcomeMessageInternal().then(() => {
      this.isWelcomeMessageReady = true;
      console.log('[ChatBox] Welcome message pre-load complete');
    });

    return this.welcomeMessagePromise;
  }

  /**
   * Show the welcome message if it's ready, or wait for it to complete
   */
  public async showWelcomeMessage(): Promise<void> {
    console.log('[ChatBox] showWelcomeMessage called');

    // Unhide the welcome message
    this.isWelcomeMessageHidden = false;

    // Tell the message component to stop hiding streaming welcome messages
    this.messageComponent.setWelcomeMessageHiddenMode(false);

    // If welcome message is already ready, find it and show it
    if (this.isWelcomeMessageReady) {
      console.log('[ChatBox] Welcome message is ready, showing it now');
      this.unhideWelcomeMessageInDOM();
      return;
    }

    // If welcome message is still loading, wait for it and show when ready
    if (this.welcomeMessagePromise) {
      console.log('[ChatBox] Waiting for welcome message to complete...');
      await this.welcomeMessagePromise;
      this.unhideWelcomeMessageInDOM();
      return;
    }

    // If no welcome message was started, start it now
    console.log('[ChatBox] No welcome message started, starting now');
    await this.sendWelcomeMessage();
  }

  /**
   * Unhide the welcome message in the DOM
   */
  private unhideWelcomeMessageInDOM(): void {
    // Find the hidden welcome message elements in the chat history
    const hiddenUserMessage =
      this.chatHistory.querySelector(
        '.sage-ai-user-message[style*="display: none"]'
      ) ||
      this.chatHistory.querySelector(
        '.sage-ai-user-message[style="display: none;"]'
      );
    const hiddenAssistantMessage =
      this.chatHistory.querySelector(
        '.sage-ai-assistant-message[style*="display: none"]'
      ) ||
      this.chatHistory.querySelector(
        '.sage-ai-ai-message[style*="display: none"]'
      ) ||
      this.chatHistory.querySelector(
        '.sage-ai-ai-message[style="display: none;"]'
      );

    // Show the messages
    if (hiddenUserMessage instanceof HTMLElement) {
      hiddenUserMessage.style.display = '';
      console.log('[ChatBox] Unhid welcome user message');
    }
    if (hiddenAssistantMessage instanceof HTMLElement) {
      hiddenAssistantMessage.style.display = '';
      console.log('[ChatBox] Unhid welcome assistant message');
    }

    // Scroll to bottom to show the welcome message
    this.messageComponent.scrollToBottom();
  }

  /**
   * Send the welcome message trigger automatically in launcher mode
   */
  public async sendWelcomeMessage(): Promise<void> {
    return this.sendWelcomeMessageInternal();
  }

  /**
   * Internal implementation of welcome message sending
   */
  private async sendWelcomeMessageInternal(): Promise<void> {
    // Only send welcome message once per session
    if (this.hasShownWelcomeMessage) {
      console.log('[ChatBox] Welcome message already shown, skipping');
      return;
    }

    // Skip welcome message if in demo mode (check AppState)
    if (AppStateService.isDemoMode()) {
      console.log('[ChatBox] Skipping welcome message - demo mode active');
      this.hasShownWelcomeMessage = true;
      return;
    }

    // Skip welcome message if in takeover mode (check AppState)
    if (AppStateService.isTakeoverMode()) {
      console.log('[ChatBox] Skipping welcome message - takeover mode active');
      this.hasShownWelcomeMessage = true;
      return;
    }

    // Skip welcome message if there's a stored notebook path (user logging back in after "Login to Chat")
    const { getStoredLastNotebookPath } = await import(
      '../utils/replayIdManager'
    );
    if (getStoredLastNotebookPath()) {
      console.log(
        '[ChatBox] Skipping welcome message - notebook restoration pending'
      );
      this.hasShownWelcomeMessage = true;
      return;
    }

    // Check if we're on the launcher and if the tour has been completed
    const isLauncher = AppStateService.getState().isLauncherActive;

    if (isLauncher) {
      // On launcher: only send welcome message if tour is completed
      const tourCompleted = await BackendCacheService.getValue(
        STATE_DB_KEYS.WELCOME_TOUR_COMPLETED,
        false
      );

      if (!tourCompleted) {
        console.log(
          '[ChatBox] Tour not completed - skipping welcome message on launcher'
        );
        return;
      }

      console.log(
        '[ChatBox] Tour completed - sending welcome message on launcher'
      );
    }

    console.log('[ChatBox] Sending automatic welcome message');

    // Set the input value to the welcome trigger phrase
    this.inputManager.setInputValue('Create Welcome Message');

    // Send the message
    await this.inputManager.sendMessage(undefined, this.isWelcomeMessageHidden);

    // Mark that we've shown the welcome message
    this.hasShownWelcomeMessage = true;
  }

  /**
   * Send a "Continue" message when the continue button is pressed
   */
  public sendContinueMessage(): void {
    // Set the input value to "Continue"
    this.inputManager.setInputValue('Continue');

    // Send the message
    void this.inputManager.sendMessage();

    // Hide the waiting reply box since user has responded
    this.messageComponent.hideWaitingReplyBox();
  }

  public sendPromptMessage(prompt: string, hidden?: boolean): void {
    // Set the input value to the selected prompt
    this.inputManager.setInputValue(prompt);

    // Send the message
    void this.inputManager.sendMessage(undefined, hidden);

    // Hide the waiting reply box since user has responded
    this.messageComponent.hideWaitingReplyBox();
  }

  /**
   * Gets the message component for external access
   */
  public getMessageComponent(): ChatMessages {
    return this.messageComponent;
  }

  /**
   * Check if the chatbox is fully ready (after launcher setup completes)
   * @returns True if chatbox is ready for operations
   */
  public isFullyReady(): boolean {
    return this.isReady;
  }

  /**
   * Mark the chatbox as fully ready
   */
  public setReady(): void {
    this.isReady = true;
    console.log('[ChatBox] Marked as fully ready');
  }

  public dispose(): void {
    this.resizeObserver?.disconnect();
    this.mutationObserver?.disconnect();
    this.llmStateConnection?.dispose();
    this.planStateConnection?.dispose();
    this.moreOptionsDisplay?.dispose();
    this.updateBanner?.dispose();
    this.appStateSubscription?.unsubscribe();
    super.dispose();
  }
}
