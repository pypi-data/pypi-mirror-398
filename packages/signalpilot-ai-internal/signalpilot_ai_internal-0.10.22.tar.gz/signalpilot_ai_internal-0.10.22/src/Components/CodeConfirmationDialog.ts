import { ChatMessages } from '../Chat/ChatMessages';
import hljs from 'highlight.js';
import 'highlight.js/styles/default.css';

/**
 * Interface for tracking individual dialog state
 */
interface DialogState {
  resolver: (value: boolean) => void;
  container: HTMLDivElement;
  keyboardHandler: (event: KeyboardEvent) => void;
  dialogId: string;
}

/**
 * A component for displaying a code execution confirmation dialog
 * Supports multiple concurrent dialogs
 */
export class CodeConfirmationDialog {
  private chatHistory: HTMLDivElement;
  private messageComponent: ChatMessages;

  // Map to store multiple concurrent dialogs keyed by dialog ID
  private activeDialogs: Map<string, DialogState> = new Map();
  private dialogIdCounter: number = 0;

  constructor(chatHistory: HTMLDivElement, messageComponent: ChatMessages) {
    this.chatHistory = chatHistory;
    this.messageComponent = messageComponent;
  }

  /**
   * Externally trigger approval of the most recent confirmation dialog
   * This can be called from LLMStateDisplay buttons
   */
  public triggerApproval(): void {
    // Approve the most recently added dialog
    const mostRecentDialog = this.getMostRecentDialog();
    if (mostRecentDialog) {
      this.executeApproval(mostRecentDialog.dialogId);
    }
  }

  /**
   * Externally trigger rejection of the most recent confirmation dialog
   * This can be called from LLMStateDisplay buttons
   */
  public triggerRejection(): void {
    // Reject the most recently added dialog
    const mostRecentDialog = this.getMostRecentDialog();
    if (mostRecentDialog) {
      this.executeRejection(mostRecentDialog.dialogId);
    }
  }

  /**
   * Get the most recently added dialog
   */
  private getMostRecentDialog(): DialogState | null {
    if (this.activeDialogs.size === 0) {
      return null;
    }
    // Return the last dialog in the map (most recently added)
    const dialogs = Array.from(this.activeDialogs.values());
    return dialogs[dialogs.length - 1];
  }

  /**
   * Execute the approval logic for a specific dialog
   */
  private executeApproval(dialogId: string): void {
    const dialogState = this.activeDialogs.get(dialogId);
    if (!dialogState) {
      return;
    }

    // Remove the container from DOM
    if (this.chatHistory.contains(dialogState.container)) {
      this.chatHistory.removeChild(dialogState.container);
    }

    // Resolve the promise
    dialogState.resolver(true);

    // Clean up
    this.cleanup(dialogId);
  }

  /**
   * Execute the rejection logic for a specific dialog
   */
  private executeRejection(dialogId: string): void {
    const dialogState = this.activeDialogs.get(dialogId);
    if (!dialogState) {
      return;
    }

    // Remove the container from DOM
    if (this.chatHistory.contains(dialogState.container)) {
      this.chatHistory.removeChild(dialogState.container);
    }

    // Resolve the promise
    dialogState.resolver(false);

    // Clean up
    this.cleanup(dialogId);
  }

  /**
   * Clean up a specific dialog's state
   */
  private cleanup(dialogId: string): void {
    const dialogState = this.activeDialogs.get(dialogId);
    if (dialogState) {
      // Remove keyboard event listener
      document.removeEventListener('keydown', dialogState.keyboardHandler);
      // Remove from active dialogs
      this.activeDialogs.delete(dialogId);
    }
  }

  /**
   * Generate a unique dialog ID
   */
  private generateDialogId(cellId?: string): string {
    this.dialogIdCounter++;
    const baseId = cellId || `dialog_${this.dialogIdCounter}`;
    return `${baseId}_${this.dialogIdCounter}_${Date.now()}`;
  }

  /**
   * Show a confirmation dialog for code execution
   * @param cellId The cell id to be executed
   * @param isProcessingStopped Whether the processing has been stopped
   * @returns A promise that resolves to true if execution is approved, false otherwise
   */
  public async showConfirmation(
    cellId?: string,
    isProcessingStopped?: boolean
  ): Promise<boolean> {
    // If processing has been stopped, don't show the dialog and return false
    if (isProcessingStopped) {
      return false;
    }

    // Check if this is a terminal command (doesn't start with "cell_")
    const isTerminalCommand = cellId && !cellId.startsWith('cell_');

    if (isTerminalCommand) {
      return this.showCommandConfirmation(cellId);
    } else {
      return this.showCellConfirmation(cellId);
    }
  }

  /**
   * Show a confirmation dialog for terminal command execution
   * @param command The command to be executed
   * @returns A promise that resolves to true if execution is approved, false otherwise
   */
  private async showCommandConfirmation(command: string): Promise<boolean> {
    const dialogId = this.generateDialogId(command);

    return new Promise<boolean>(resolve => {
      // Create an inline confirmation message in the chat
      const confirmationContainer = document.createElement('div');
      confirmationContainer.className = 'sage-ai-code-confirmation';
      confirmationContainer.style.display = 'flex';
      confirmationContainer.style.flexDirection = 'column';
      confirmationContainer.style.alignItems = 'stretch';

      // Extract command parts (main commands from the shell command)
      const extractCommandParts = (cmd: string): string[] => {
        // Helper function to split command while respecting quotes and parentheses
        const smartSplit = (text: string, separators: string[]): string[] => {
          const result: string[] = [];
          let current = '';
          let inQuotes = false;
          let quoteChar = '';
          let parenDepth = 0;
          let i = 0;

          while (i < text.length) {
            const char = text[i];
            const nextTwo = text.substring(i, i + 2);

            // Handle quotes
            if (
              (char === '"' || char === "'") &&
              (i === 0 || text[i - 1] !== '\\')
            ) {
              if (!inQuotes) {
                inQuotes = true;
                quoteChar = char;
              } else if (char === quoteChar) {
                inQuotes = false;
                quoteChar = '';
              }
              current += char;
              i++;
              continue;
            }

            // Handle parentheses (for regex patterns, etc.)
            if (!inQuotes) {
              if (char === '(') {
                parenDepth++;
              } else if (char === ')') {
                parenDepth--;
              }
            }

            // Check for separators (only when not in quotes/parens)
            if (!inQuotes && parenDepth === 0) {
              let foundSeparator = false;
              for (const sep of separators) {
                // Check if separator matches (handle both single and multi-char separators)
                const matches =
                  sep.length === 1 ? char === sep : nextTwo === sep;

                if (matches) {
                  if (current.trim()) {
                    result.push(current.trim());
                  }
                  current = '';
                  i += sep.length;
                  foundSeparator = true;
                  break;
                }
              }
              if (foundSeparator) {
                continue;
              }
            }

            current += char;
            i++;
          }

          if (current.trim()) {
            result.push(current.trim());
          }

          return result;
        };

        // Split by both && and |, respecting quotes and parentheses
        const segments = smartSplit(cmd, ['&&', '||']);

        // Also split each segment by | (pipes) if not inside quotes/parens
        const allParts: string[] = [];
        for (const segment of segments) {
          const pipeParts = smartSplit(segment, ['|']);
          allParts.push(...pipeParts);
        }

        // Extract command names from each part
        const commands = allParts
          .map(part => {
            // Remove redirects (2>/dev/null, >file, etc.)
            let trimmed = part
              .trim()
              .replace(/\d+[<>]\s*\S+/g, '') // Remove numbered redirects like "2>/dev/null"
              .replace(/[<>]\s*\S+/g, '') // Remove other redirects
              .trim();

            // Remove quoted strings and parentheses patterns for command extraction
            // This handles cases like grep -E "(PATH|PYTHON|...)"
            trimmed = trimmed
              .replace(/\([^)]*\)/g, '') // Remove parentheses and their contents
              .replace(/["'].*?["']/g, '') // Remove quoted strings
              .trim();

            // Get the first word (the command)
            const words = trimmed.split(/\s+/).filter(w => w.length > 0);
            const firstWord = words[0];

            return firstWord;
          })
          .filter(cmd => {
            if (!cmd || cmd.length === 0) return false;

            // Filter out invalid patterns
            if (
              cmd.startsWith('$') ||
              cmd.match(/^\d+$/) ||
              cmd.startsWith('-') ||
              cmd.includes('|') ||
              cmd.includes('(') ||
              cmd.includes(')') ||
              cmd.includes('"') ||
              cmd.includes("'")
            ) {
              return false;
            }

            // Filter out all-caps words that look like environment variables or pattern parts
            // (like PATH, PYTHON, JUPYTER, etc.)
            if (
              cmd === cmd.toUpperCase() &&
              cmd.length > 2 &&
              cmd.includes('_')
            ) {
              return false;
            }

            // Only allow valid command names (lowercase or mixed case, alphanumeric with dashes/underscores)
            // Commands are typically lowercase or have some lowercase letters
            const hasLowercase = /[a-z]/.test(cmd);
            if (!hasLowercase && cmd.length > 3) {
              return false; // Likely an environment variable or constant
            }

            return cmd.match(/^[a-zA-Z_][a-zA-Z0-9_-]*$/); // Valid command name pattern
          });

        // Remove duplicates while preserving order
        return Array.from(new Set(commands));
      };

      const commandParts = extractCommandParts(command);
      const commandPartsText =
        commandParts.length > 0 ? commandParts.join(', ') : 'command';

      // Create the "Run command: X, Y, Z" text
      const runCommandText = document.createElement('div');
      runCommandText.style.fontSize = 'var(--jp-ui-font-size1)';
      runCommandText.style.color = 'var(--jp-ui-font-color2)';
      runCommandText.style.fontWeight = '500';
      runCommandText.style.marginBottom = '8px';
      runCommandText.textContent = `Run command: ${commandPartsText}`;
      confirmationContainer.appendChild(runCommandText);

      // Add divider
      const divider = document.createElement('div');
      divider.style.height = '1px';
      divider.style.backgroundColor = 'var(--jp-border-color1)';
      divider.style.marginBottom = '12px';
      confirmationContainer.appendChild(divider);

      // Create the command display with $ prompt
      const commandDisplay = document.createElement('div');
      commandDisplay.style.fontFamily = 'var(--jp-code-font-family)';
      commandDisplay.style.fontSize = 'var(--jp-code-font-size)';
      commandDisplay.style.color = 'var(--jp-content-font-color1)';
      commandDisplay.style.backgroundColor = 'var(--jp-layout-color0)';
      commandDisplay.style.padding = '12px';
      commandDisplay.style.borderRadius = '4px';
      commandDisplay.style.marginBottom = '12px';
      commandDisplay.style.whiteSpace = 'pre-wrap';
      commandDisplay.style.wordBreak = 'break-word';

      // Create the $ prompt (styled like a terminal)
      const promptSpan = document.createElement('span');
      promptSpan.textContent = '$ ';
      promptSpan.style.color = 'var(--jp-ui-font-color2)';
      commandDisplay.appendChild(promptSpan);

      // Add syntax highlighting using highlight.js
      const codeElement = document.createElement('code');
      codeElement.className = 'language-bash hljs';
      codeElement.textContent = command;
      codeElement.style.backgroundColor = 'var(--jp-layout-color0)';

      // Highlight the code (highlight.js will apply its default styling)
      hljs.highlightElement(codeElement);

      commandDisplay.appendChild(codeElement);

      confirmationContainer.appendChild(commandDisplay);

      // Create and append buttons
      const buttonContainer = this.createButtonContainer();
      confirmationContainer.appendChild(buttonContainer);

      // Add the confirmation container to the chat history
      this.chatHistory.appendChild(confirmationContainer);

      this.messageComponent.handleScroll();

      // Set up event handlers with dialog ID
      const keyboardHandler = this.setupEventHandlers(
        buttonContainer,
        dialogId
      );

      // Store dialog state
      this.activeDialogs.set(dialogId, {
        resolver: resolve,
        container: confirmationContainer,
        keyboardHandler: keyboardHandler,
        dialogId: dialogId
      });
    });
  }

  /**
   * Show a confirmation dialog for cell execution
   * @param cellId The cell id to be executed
   * @returns A promise that resolves to true if execution is approved, false otherwise
   */
  private async showCellConfirmation(cellId?: string): Promise<boolean> {
    const dialogId = this.generateDialogId(cellId);

    return new Promise<boolean>(resolve => {
      // Create an inline confirmation message in the chat
      const confirmationContainer = document.createElement('div');
      confirmationContainer.className = 'sage-ai-code-confirmation';

      const codeIcon =
        '<svg width="14px" height="14px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path fill-rule="evenodd" clip-rule="evenodd" d="M4.5 6L5.25 5.25H18.75L19.5 6V18L18.75 18.75H5.25L4.5 18V6ZM6 6.75V17.25H18V6.75H6ZM10.1894 12L7.71973 9.5303L8.78039 8.46964L12.3107 12L8.78039 15.5303L7.71973 14.4696L10.1894 12ZM12 15.75H15.75V14.25H12V15.75Z" fill="var(--jp-ui-font-color0)"></path> </g></svg>';

      // Add heading
      const heading = document.createElement('span');
      heading.innerHTML = `${codeIcon} SignalPilot is trying to run ${cellId || 'cell'}`;
      heading.className = 'sage-ai-code-confirmation-heading';
      confirmationContainer.appendChild(heading);

      // Create and append buttons
      const buttonContainer = this.createButtonContainer();
      const bottomContainer = document.createElement('div');
      bottomContainer.className = 'sage-ai-confirmation-bottom-container';
      bottomContainer.appendChild(buttonContainer);
      confirmationContainer.appendChild(bottomContainer);

      // Add the confirmation container to the chat history
      this.chatHistory.appendChild(confirmationContainer);

      this.messageComponent.handleScroll();

      // Set up event handlers with dialog ID
      const keyboardHandler = this.setupEventHandlers(
        buttonContainer,
        dialogId
      );

      // Store dialog state
      this.activeDialogs.set(dialogId, {
        resolver: resolve,
        container: confirmationContainer,
        keyboardHandler: keyboardHandler,
        dialogId: dialogId
      });
    });
  }

  /**
   * Create the button container with confirm and reject buttons
   * @returns The button container element
   */
  private createButtonContainer(): HTMLDivElement {
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'sage-ai-confirmation-button-container';
    // Align buttons to the right
    buttonContainer.style.display = 'flex';
    buttonContainer.style.justifyContent = 'flex-end';
    buttonContainer.style.gap = '8px';

    const cancelButton = document.createElement('button');
    cancelButton.textContent = 'Reject';
    cancelButton.className = 'sage-ai-reject-button';

    const confirmButton = document.createElement('button');
    // Detect platform for modifier key
    const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform);
    // Unicode icons for Cmd, Ctrl, and Enter
    const cmdIcon = '\u2318'; // ⌘
    const ctrlIcon = '\u2303'; // ⌃
    const enterIcon = '\u23CE'; // ⏎

    // Compose label: [Cmd|Ctrl] + Enter
    const modifierIcon = isMac ? cmdIcon : ctrlIcon;

    // Create a span for the button label
    const labelSpan = document.createElement('span');
    labelSpan.style.display = 'flex';
    labelSpan.style.alignItems = 'center';

    // Add modifier icon/text
    const modSpan = document.createElement('span');
    modSpan.style.display = 'inline-flex';
    modSpan.style.alignItems = 'center';
    modSpan.style.fontFamily = 'monospace';
    modSpan.style.fontWeight = 'bold';
    modSpan.style.marginLeft = '4px';
    modSpan.style.marginRight = '2px';
    modSpan.textContent = modifierIcon;

    // Add enter icon/text
    const enterSpan = document.createElement('span');
    enterSpan.style.display = 'inline-flex';
    enterSpan.style.alignItems = 'center';
    enterSpan.style.fontFamily = 'monospace';
    enterSpan.style.fontWeight = 'bold';
    enterSpan.textContent = enterIcon;

    // Add "Run" label
    const runSpan = document.createElement('span');
    runSpan.style.fontSize = 'var(--jp-ui-font-size1)';
    runSpan.textContent = 'Run';

    // Compose the label: [Run] [Cmd/Ctrl icon + text] + [Enter icon + text]
    labelSpan.appendChild(runSpan);
    labelSpan.appendChild(modSpan);
    labelSpan.appendChild(enterSpan);

    confirmButton.appendChild(labelSpan);
    confirmButton.className = 'sage-ai-confirm-button';

    buttonContainer.appendChild(cancelButton);
    buttonContainer.appendChild(confirmButton);

    return buttonContainer;
  }

  /**
   * Set up event handlers for keyboard and button interactions
   * @param buttonContainer The button container element
   * @param dialogId The unique ID for this dialog
   * @returns The keyboard handler function for cleanup
   */
  private setupEventHandlers(
    buttonContainer: HTMLDivElement,
    dialogId: string
  ): (event: KeyboardEvent) => void {
    const confirmButton = buttonContainer.querySelector(
      '.sage-ai-confirm-button'
    ) as HTMLButtonElement;
    const cancelButton = buttonContainer.querySelector(
      '.sage-ai-reject-button'
    ) as HTMLButtonElement;

    // Keyboard event handler for this specific dialog
    const keyboardHandler = (event: KeyboardEvent) => {
      // Check for Cmd+Enter (macOS) or Ctrl+Enter (Windows/Linux)
      // Only handle if this dialog is still active
      if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
        if (this.activeDialogs.has(dialogId)) {
          event.preventDefault();
          this.executeApproval(dialogId);
        }
      }
    };

    // Add keyboard event listener
    document.addEventListener('keydown', keyboardHandler);

    // Set up button event handlers
    confirmButton.addEventListener('click', () => {
      this.executeApproval(dialogId);
    });

    cancelButton.addEventListener('click', () => {
      this.executeRejection(dialogId);
    });

    return keyboardHandler;
  }

  /**
   * Check if any confirmation dialog is currently showing
   */
  public isDialogShowing(): boolean {
    return this.activeDialogs.size > 0;
  }
}
