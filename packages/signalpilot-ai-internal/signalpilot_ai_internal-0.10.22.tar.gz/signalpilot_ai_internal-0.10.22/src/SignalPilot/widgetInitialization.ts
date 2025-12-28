/**
 * SignalPilot Widget Initialization Module
 *
 * Handles initialization of all UI widgets including:
 * - Chat container
 * - Settings container
 * - Snippet creation widget
 * - File explorer widget
 * - Diff navigation widget
 * - Database manager widget
 */

import { JupyterFrontEnd } from '@jupyterlab/application';
import { INotebookTracker } from '@jupyterlab/notebook';
import { WidgetTracker } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

import { AppStateService } from '../AppState';
import { ToolService } from '../Services/ToolService';
import { NotebookContextManager } from '../Notebook/NotebookContextManager';
import { NotebookDiffManager } from '../Notebook/NotebookDiffManager';
import { ActionHistory } from '../Chat/ActionHistory';
import { NotebookChatContainer } from '../Notebook/NotebookChatContainer';
import { NotebookSettingsContainer } from '../NotebookSettingsContainer';
import { SnippetCreationWidget } from '../Components/SnippetCreationWidget';
import { FileExplorerWidget } from '../Components/FileExplorerWidget';
import { DiffNavigationWidget } from '../Components/DiffNavigationWidget';
import { DatabaseManagerWidget } from '../Components/DatabaseManagerWidget/DatabaseManagerWidget';
import { MCPManagerWidget } from '../Components/MCPManagerWidget';
import { ContextCellHighlighter } from '../Chat/ChatContextMenu/ContextCellHighlighter';
import {
  getGlobalDiffNavigationWidget,
  setGlobalDiffNavigationWidget,
  setGlobalSnippetCreationWidget
} from '../globalWidgets';

export interface WidgetInstances {
  tracker: WidgetTracker<Widget>;
  settingsContainer: NotebookSettingsContainer;
  snippetCreationWidget: SnippetCreationWidget;
  diffNavigationWidget: DiffNavigationWidget | undefined;
  databaseManagerWidget: DatabaseManagerWidget;
  fileExplorerWidget: FileExplorerWidget;
  mcpManagerWidget: MCPManagerWidget;
}

/**
 * Create the widget tracker
 */
export function createWidgetTracker(): WidgetTracker<Widget> {
  return new WidgetTracker<Widget>({
    namespace: 'sage-ai-widgets'
  });
}

/**
 * Initialize the chat container
 */
export async function initializeChatContainer(
  app: JupyterFrontEnd,
  notebooks: INotebookTracker,
  tracker: WidgetTracker<Widget>,
  toolService: ToolService,
  notebookContextManager: NotebookContextManager,
  actionHistory: ActionHistory,
  contextCellHighlighter: ContextCellHighlighter,
  contentManager: any
): Promise<NotebookChatContainer> {
  // Get existing chat container from AppState
  const existingChatContainer = AppStateService.getState().chatContainer;

  // Create a new chat container
  const createContainer = async () => {
    console.log('[Plugin] Creating new NotebookChatContainer');
    // Pass the shared tool service, diff manager, and notebook context manager to the container
    const newContainer = new NotebookChatContainer(
      toolService,
      notebookContextManager,
      actionHistory
    );
    await tracker.add(newContainer);

    // Add the container to the right side panel
    app.shell.add(newContainer, 'right', { rank: 1, activate: true }); // Activate the chat container to make it visible and expanded by default

    // If there's a current notebook, set its path
    if (notebooks.currentWidget) {
      // Use the centralized notebook ID from AppStateService
      const currentNotebookId = AppStateService.getCurrentNotebookId();
      if (currentNotebookId) {
        await newContainer.switchToNotebook(currentNotebookId);
      } else {
        // Try to get unique_id from current notebook metadata first
        try {
          const nbFile = await contentManager.get(
            notebooks.currentWidget.context.path
          );
          const notebookUniqueId =
            nbFile?.content?.metadata?.sage_ai?.unique_id;
          if (notebookUniqueId) {
            await newContainer.switchToNotebook(notebookUniqueId);
          } else {
            // Fallback to path if unique_id not available
            await newContainer.switchToNotebook(
              notebooks.currentWidget.context.path
            );
          }
        } catch (error) {
          console.warn(
            'Could not get notebook metadata in initializeChatContainer:',
            error
          );
          // Fallback to path if metadata retrieval fails
          await newContainer.switchToNotebook(
            notebooks.currentWidget.context.path
          );
        }
      }
    }

    // Store in AppState
    AppStateService.setChatContainer(newContainer);

    return newContainer;
  };

  if (!existingChatContainer || existingChatContainer.isDisposed) {
    const chatContainer = await createContainer();

    // Set the chat container reference in the context cell highlighter
    contextCellHighlighter.setChatContainer(chatContainer);

    void app.restored.then(() => {
      // Only activate chat sidebar if we're not on the launcher
      const isLauncher = app.shell.currentWidget?.title.label === 'Launcher';
      if (!isLauncher) {
        app.shell.activateById('sage-ai-chat-container');
      }

      // Auto-render the welcome CTA after chat container is loaded
      // Use a small delay to ensure the chat widget is fully initialized
      setTimeout(() => {
        if (notebooks.currentWidget) {
          app.commands.execute('sage-ai:add-cta-div').catch(error => {
            console.warn('[Plugin] Failed to auto-render welcome CTA:', error);
          });
        }
      }, 300);
    });

    return chatContainer;
  }

  return existingChatContainer;
}

/**
 * Initialize the settings container
 */
export function initializeSettingsContainer(
  app: JupyterFrontEnd,
  tracker: WidgetTracker<Widget>,
  toolService: ToolService,
  diffManager: NotebookDiffManager,
  notebookContextManager: NotebookContextManager
): NotebookSettingsContainer {
  const newContainer = new NotebookSettingsContainer(
    toolService,
    diffManager,
    notebookContextManager
  );
  void tracker.add(newContainer);

  // Add the container to the right side panel
  app.shell.add(newContainer, 'right', { rank: 2 });

  return newContainer;
}

/**
 * Initialize the snippet creation widget
 */
export function initializeSnippetCreationWidget(
  app: JupyterFrontEnd,
  tracker: WidgetTracker<Widget>
): SnippetCreationWidget {
  const newWidget = new SnippetCreationWidget();
  void tracker.add(newWidget);

  // Add the widget to the left side panel
  app.shell.add(newWidget, 'left', { rank: 1000 });

  return newWidget;
}

/**
 * Initialize the file explorer widget
 */
export function initializeFileExplorerWidget(
  app: JupyterFrontEnd,
  tracker: WidgetTracker<Widget>
): FileExplorerWidget {
  const newWidget = new FileExplorerWidget();

  // Set the app instance for file browser operations
  newWidget.setApp(app);

  void tracker.add(newWidget);

  // Add the widget to the left side panel with a different rank
  app.shell.add(newWidget, 'left', { rank: 1001 });

  return newWidget;
}

/**
 * Initialize the diff navigation widget
 */
export function initializeDiffNavigationWidget(
  notebooks: INotebookTracker,
  tracker: WidgetTracker<Widget>
): DiffNavigationWidget | undefined {
  const newWidget = new DiffNavigationWidget();
  void tracker.add(newWidget);

  // Append to current notebook only - do not create widget if no notebook
  const currentNotebook = notebooks.currentWidget;
  if (currentNotebook) {
    // Find the notebook panel element with the specified classes
    const notebookElement = currentNotebook.node.querySelector('.jp-Notebook');
    if (notebookElement) {
      notebookElement.appendChild(newWidget.node);
    } else {
      // Fallback to notebook panel if .jp-Notebook not found
      currentNotebook.node.appendChild(newWidget.node);
    }
    return newWidget;
  } else {
    // Do not create widget if no notebook is available
    console.log(
      'DiffNavigationWidget: No current notebook available, skipping widget creation'
    );
    return undefined;
  }
}

/**
 * Initialize the database manager widget
 */
export function initializeDatabaseManagerWidget(
  app: JupyterFrontEnd,
  tracker: WidgetTracker<Widget>
): DatabaseManagerWidget {
  const newWidget = new DatabaseManagerWidget();
  void tracker.add(newWidget);

  // Add the widget to the left side panel
  app.shell.add(newWidget, 'left', { rank: 1001 });

  return newWidget;
}

/**
 * Initialize the MCP manager widget
 */
export function initializeMCPManagerWidget(
  app: JupyterFrontEnd,
  tracker: WidgetTracker<Widget>
): MCPManagerWidget {
  const newWidget = new MCPManagerWidget();
  void tracker.add(newWidget);

  // Add the widget to the right side panel
  app.shell.add(newWidget, 'right', { rank: 3 });

  return newWidget;
}

/**
 * Initialize all widgets and store references
 */
export async function initializeAllWidgets(
  app: JupyterFrontEnd,
  notebooks: INotebookTracker,
  toolService: ToolService,
  notebookContextManager: NotebookContextManager,
  diffManager: NotebookDiffManager,
  actionHistory: ActionHistory,
  contextCellHighlighter: ContextCellHighlighter,
  contentManager: any
): Promise<WidgetInstances> {
  const tracker = createWidgetTracker();

  // Initialize all containers
  await initializeChatContainer(
    app,
    notebooks,
    tracker,
    toolService,
    notebookContextManager,
    actionHistory,
    contextCellHighlighter,
    contentManager
  );

  const settingsContainer = initializeSettingsContainer(
    app,
    tracker,
    toolService,
    diffManager,
    notebookContextManager
  );

  const snippetCreationWidget = initializeSnippetCreationWidget(app, tracker);
  const fileExplorerWidget = initializeFileExplorerWidget(app, tracker);
  const diffNavigationWidget = initializeDiffNavigationWidget(
    notebooks,
    tracker
  );
  const databaseManagerWidget = initializeDatabaseManagerWidget(app, tracker);
  const mcpManagerWidget = initializeMCPManagerWidget(app, tracker);

  // Store widget references in AppState for global access
  AppStateService.setState({
    fileExplorerWidget,
    databaseManagerWidget,
    diffNavigationWidget
  });

  // Store widget references globally for cleanup
  setGlobalSnippetCreationWidget(snippetCreationWidget);
  if (diffNavigationWidget) {
    setGlobalDiffNavigationWidget(diffNavigationWidget);
  }

  // Register DiffNavigationWidget with AppStateService
  if (diffNavigationWidget) {
    AppStateService.setDiffNavigationWidget(diffNavigationWidget);
  }

  return {
    tracker,
    settingsContainer,
    snippetCreationWidget,
    diffNavigationWidget,
    databaseManagerWidget,
    fileExplorerWidget,
    mcpManagerWidget
  };
}

/**
 * Set up DiffNavigationWidget to respond to notebook changes
 */
export function setupDiffNavigationWidgetTracking(
  notebooks: INotebookTracker
): void {
  AppStateService.onNotebookChanged().subscribe(({ newNotebookId }) => {
    const globalDiffNavigationWidget = getGlobalDiffNavigationWidget();
    if (globalDiffNavigationWidget && !globalDiffNavigationWidget.isDisposed) {
      globalDiffNavigationWidget.setNotebookId(newNotebookId);

      // Re-attach widget to the new notebook (only if notebook exists)
      const currentNotebook = notebooks.currentWidget;
      if (currentNotebook && globalDiffNavigationWidget.node.parentNode) {
        // Remove from current parent
        globalDiffNavigationWidget.node.parentNode.removeChild(
          globalDiffNavigationWidget.node
        );

        // Find the notebook panel element and re-attach
        const notebookElement =
          currentNotebook.node.querySelector('.jp-Notebook');
        if (notebookElement) {
          notebookElement.appendChild(globalDiffNavigationWidget.node);
        } else {
          // Fallback to notebook panel if .jp-Notebook not found
          currentNotebook.node.appendChild(globalDiffNavigationWidget.node);
        }
      } else if (!currentNotebook) {
        // If no notebook available, remove widget from DOM but don't dispose
        if (globalDiffNavigationWidget.node.parentNode) {
          globalDiffNavigationWidget.node.parentNode.removeChild(
            globalDiffNavigationWidget.node
          );
        }
      }
    } else if (!globalDiffNavigationWidget && newNotebookId) {
      // Try to create widget if one doesn't exist and we have a notebook
      const newDiffWidget = initializeDiffNavigationWidget(
        notebooks,
        new WidgetTracker<Widget>({ namespace: 'sage-ai-widgets' })
      );
      if (newDiffWidget) {
        setGlobalDiffNavigationWidget(newDiffWidget);
        AppStateService.setDiffNavigationWidget(newDiffWidget);
      }
    }
  });
}
