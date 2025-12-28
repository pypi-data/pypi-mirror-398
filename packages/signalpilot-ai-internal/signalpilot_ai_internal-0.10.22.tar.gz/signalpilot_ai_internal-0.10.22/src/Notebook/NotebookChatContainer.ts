import { PanelLayout, Widget } from '@lumino/widgets';
import { ChatBoxWidget } from '../Components/chatbox';
import { ToolService } from '../Services/ToolService';
import { NotebookContextManager } from './NotebookContextManager';
import { AppStateService } from '../AppState';
import { ActionHistory } from '../Chat/ActionHistory';

/**
 * Container widget that holds only the chat widget
 */
export class NotebookChatContainer extends Widget {
  public chatWidget: ChatBoxWidget;
  private toolService: ToolService;
  private contextManager: NotebookContextManager | null;
  private currentNotebookId: string | null = null;

  constructor(
    toolService: ToolService,
    contextManager: NotebookContextManager | null | undefined,
    actionHistory: ActionHistory
  ) {
    super();

    this.id = 'sage-ai-chat-container';
    this.title.label = 'SignalPilot AI Chat';
    this.title.closable = true;
    this.addClass('sage-ai-chat-container');
    this.toolService = toolService;
    this.contextManager = contextManager || null;

    // Set the minimum width of the widget's node
    this.node.style.minWidth = '320px';

    // Create chat widget with contextCellHighlighter
    this.chatWidget = new ChatBoxWidget(actionHistory);

    // Create layout for the container
    const layout = new PanelLayout();
    layout.addWidget(this.chatWidget);

    // Set the layout properly
    this.layout = layout;

    // Subscribe to notebook changes from AppStateService
    AppStateService.onNotebookChanged().subscribe(
      async ({ newNotebookId, fromLauncher }) => {
        // Force switch when coming from launcher, even if notebook ID is the same
        // This ensures chat history and context are properly loaded
        if (
          newNotebookId &&
          (fromLauncher || newNotebookId !== this.currentNotebookId)
        ) {
          await this.switchToNotebook(newNotebookId, fromLauncher);
        }
      }
    );

    // AppStateService.onNotebookRenamed().subscribe(
    //   ({ oldNotebookId, newNotebookId }) => {
    //     this.updateNotebookId(oldNotebookId, newNotebookId);
    //   }
    // );
  }

  public updateNotebookId(oldNotebookId: string, newNotebookId: string): void {
    this.contextManager?.updateNotebookId(oldNotebookId, newNotebookId);

    this.chatWidget.chatHistoryManager.updateNotebookId(
      oldNotebookId,
      newNotebookId
    );

    this.chatWidget.updateNotebookPath(newNotebookId);

    this.toolService.updateNotebookId(oldNotebookId, newNotebookId);

    this.currentNotebookId = newNotebookId;
  }

  /**
   * Switch to a different notebook
   * @param notebookId ID of the notebook
   * @param fromLauncher Whether this switch is coming from the launcher state
   */
  public async switchToNotebook(
    notebookId: string,
    fromLauncher?: boolean
  ): Promise<void> {
    console.log('SWITCH TO NOTEBOOK CALLED');
    console.log('FROM LAUNCHER VALUE: ', fromLauncher);
    // Skip check if coming from launcher - we want to force refresh in this case
    if (!fromLauncher && this.currentNotebookId === notebookId) {
      // Already on this notebook, nothing to do
      return;
    }

    console.log(`[NotebookChatContainer] Switching to notebook: ${notebookId}`);

    const previousNotebookId = this.currentNotebookId;

    this.currentNotebookId = notebookId;

    // Update the tool service with the new notebook ID
    this.toolService.setCurrentNotebookId(notebookId);

    // Update the notebook context manager if available
    if (this.contextManager) {
      this.contextManager.getContext(notebookId);
    }

    // If we're coming from launcher state or had no previous notebook,
    // do a full re-initialization to ensure clean state
    if (fromLauncher || !previousNotebookId) {
      console.log(
        '[NotebookChatContainer] Coming from launcher state, performing full re-initialization'
      );
      // In demo mode, wait 100ms to allow the UI to fully switch to the notebook before re-initializing
      // This prevents the chatbox from appearing blank
      if (AppStateService.isDemoMode()) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      await this.chatWidget.reinitializeForNotebook(notebookId);
    } else {
      // Normal notebook switch - use the standard method
      await this.chatWidget.setNotebookId(notebookId);
    }
  }

  /**
   * Handle a cell added to context
   * @param notebookId ID of the notebook containing the cell
   * @param cellId ID of the cell added to context
   */
  public onCellAddedToContext(notebookId: string): void {
    if (!this.currentNotebookId || this.currentNotebookId !== notebookId) {
      console.warn(
        `Cannot add cell from ${notebookId} to context when current notebook is ${this.currentNotebookId}`
      );
      return;
    }

    // Pass the event to the chatbox
    this.chatWidget.onCellAddedToContext(notebookId);
  }

  /**
   * Handle a cell removed from context
   * @param notebookId ID of the notebook containing the cell
   */
  public onCellRemovedFromContext(notebookId: string): void {
    if (!this.currentNotebookId || this.currentNotebookId !== notebookId) {
      console.warn(
        `Cannot remove cell from ${notebookId} context when current notebook is ${this.currentNotebookId}`
      );
      return;
    }

    // Pass the event to the chatbox
    this.chatWidget.onCellRemovedFromContext(notebookId);
  }
}
