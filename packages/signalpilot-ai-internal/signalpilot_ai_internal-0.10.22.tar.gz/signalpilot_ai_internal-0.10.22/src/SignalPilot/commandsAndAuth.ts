/**
 * SignalPilot Commands and Authentication Module
 *
 * Handles command registration, keyboard shortcuts, and authentication setup
 */

import { JupyterFrontEnd } from '@jupyterlab/application';
import { ICommandPalette, WidgetTracker } from '@jupyterlab/apputils';
import { INotebookTracker } from '@jupyterlab/notebook';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { Widget } from '@lumino/widgets';
import { addIcon } from '@jupyterlab/ui-components';

import { NotebookContextManager } from '../Notebook/NotebookContextManager';
import { AppStateService } from '../AppState';
import { JWTAuthModalService } from '../Services/JWTAuthModalService';
import { JupyterAuthService } from '../Services/JupyterAuthService';
import { JwtTokenDialog, MessageDialog } from '../Components/JwtTokenDialog';
import { attachChatboxToLauncher, registerCommands } from '../commands';
import { registerEvalCommands } from '../eval_commands';
import { runWelcomeDemo } from '../demo';
import { getGlobalSnippetCreationWidget } from '../globalWidgets';
import { NotebookSettingsContainer } from '../NotebookSettingsContainer';

/**
 * Register all commands including custom commands for snippets and test mode
 */
export function registerAllCommands(
  app: JupyterFrontEnd,
  palette: ICommandPalette,
  documentManager: IDocumentManager,
  tracker: WidgetTracker<Widget>,
  notebooks: INotebookTracker,
  notebookContextManager: NotebookContextManager
): void {
  // Register base commands
  registerCommands(app, palette);
  registerEvalCommands(app, palette, documentManager);

  const { commands } = app;

  // Log selected code command
  const logSelectedCodeCommandId = 'signalpilot-ai-internal:log-selected-code';
  palette.addItem({
    command: logSelectedCodeCommandId,
    category: 'SignalPilot AI'
  });
  app.commands.addKeyBinding({
    command: logSelectedCodeCommandId,
    keys: ['Accel Shift K'],
    selector: '.jp-Notebook.jp-mod-editMode' // only trigger in edit mode
  });

  commands.addCommand(logSelectedCodeCommandId, {
    label: 'Log Selected Code',
    execute: () => {
      const current = tracker.currentWidget;
      if (!current) {
        console.warn('No active notebook');
        return;
      }

      const activeCell = notebooks.activeCell;
      if (!activeCell) {
        console.warn('No active cell');
        return;
      }

      const editor = activeCell.editor;
      const selection = editor?.getSelection();
      if (selection) {
        console.log('Selection:', selection);
      } else {
        console.log('No selection');
      }

      const selectedText = editor?.model.sharedModel.source.substring(
        editor.getOffsetAt(selection?.start || { line: 0, column: 0 }),
        editor.getOffsetAt(selection?.end || { line: 0, column: 0 })
      );

      if (selectedText) {
        console.log('Selected text:', selectedText);
      } else {
        console.log('No text selected');
      }
    }
  });

  // Inline edit command (Cmd+K / Ctrl+K)
  const inlineEditCommandId = 'signalpilot-ai-internal:inline-edit';
  palette.addItem({
    command: inlineEditCommandId,
    category: 'SignalPilot AI'
  });
  app.commands.addKeyBinding({
    command: inlineEditCommandId,
    keys: ['Accel K'],
    selector: '.jp-Notebook .jp-Cell.jp-mod-active'
  });

  commands.addCommand(inlineEditCommandId, {
    label: 'Inline Edit Cell',
    execute: () => {
      const activeCell = notebooks.activeCell;
      if (!activeCell) {
        console.warn('[Inline Edit] No active cell');
        return;
      }

      // Check if quick gen is already open
      const isBoxOpened = activeCell.node.querySelector(
        '.sage-ai-quick-gen-prompt-container'
      );
      if (isBoxOpened) {
        console.log('[Inline Edit] Quick gen already open');
        return;
      }

      // Find the generate button and trigger its click event
      const generateButton = activeCell.node.querySelector(
        '.sage-ai-quick-generation'
      ) as HTMLButtonElement;
      if (generateButton) {
        generateButton.click();
        console.log('[Inline Edit] Triggered inline edit');
      } else {
        console.warn('[Inline Edit] Generate button not found');
      }
    }
  });

  // Snippet creation widget command
  const snippetCommandId = 'signalpilot-ai-internal:open-snippet-creation';

  commands.addCommand(snippetCommandId, {
    label: 'Open Rule Creation',
    execute: () => {
      const globalSnippetCreationWidget = getGlobalSnippetCreationWidget();
      if (
        globalSnippetCreationWidget &&
        !globalSnippetCreationWidget.isDisposed
      ) {
        if (globalSnippetCreationWidget.getIsVisible()) {
          globalSnippetCreationWidget.hide();
        } else {
          globalSnippetCreationWidget.show();
          app.shell.activateById(globalSnippetCreationWidget.id);
        }
      }
    }
  });

  palette.addItem({ command: snippetCommandId, category: 'SignalPilot AI' });

  // Test mode command - allows setting JWT token directly
  const testModeCommandId = 'signalpilot-ai-internal:activate-test-mode';

  commands.addCommand(testModeCommandId, {
    label: 'Activate Test Mode (Set JWT Token)',
    execute: async () => {
      try {
        const jwtDialog = new JwtTokenDialog();
        const result = await jwtDialog.showDialog();

        if (result.accepted && result.value) {
          console.log('[Test Mode] Setting JWT token...');
          await JupyterAuthService.storeJwtToken(result.value);
          AppStateService.updateClaudeSettings({ claudeApiKey: result.value });

          console.log('[Test Mode] JWT token set successfully');

          // Show success message
          await MessageDialog.showMessage(
            'Test Mode',
            'JWT token has been set successfully in the state database.'
          );
        } else {
          console.log('[Test Mode] JWT token setting cancelled');
        }
      } catch (error) {
        console.error('[Test Mode] Failed to set JWT token:', error);

        const errorMessage =
          error instanceof Error ? error.message : String(error);

        // Show error message
        await MessageDialog.showMessage(
          'Test Mode - Error',
          `Failed to set JWT token: ${errorMessage}`,
          true
        );
      }
    }
  });

  palette.addItem({ command: testModeCommandId, category: 'SignalPilot AI' });
}

/**
 * Set up active cell tracking to update button state
 */
export function setupActiveCellTracking(
  notebooks: INotebookTracker,
  notebookContextManager: NotebookContextManager
): void {
  notebooks.activeCellChanged.connect((_, cell) => {
    if (cell) {
      // Get the current notebook ID from centralized AppStateService
      const notebookId = AppStateService.getCurrentNotebookId();
      if (!notebookId) {
        return;
      }

      // Check if the cell has tracking ID metadata
      const metadata = cell.model.sharedModel.getMetadata() || {};
      let trackingId = '';

      if (
        metadata &&
        typeof metadata === 'object' &&
        'cell_tracker' in metadata &&
        metadata.cell_tracker &&
        typeof metadata.cell_tracker === 'object' &&
        'trackingId' in metadata.cell_tracker
      ) {
        trackingId = String(metadata.cell_tracker.trackingId);
      }

      // Update the button state based on whether this cell is in context
      const isInContext = trackingId
        ? notebookContextManager.isCellInContext(notebookId, trackingId)
        : notebookContextManager.isCellInContext(notebookId, cell.model.id);

      // Find the button
      const buttonNode = document.querySelector(
        '.jp-ToolbarButtonComponent[data-command="sage-ai-add-to-context"]'
      );
      if (buttonNode) {
        if (isInContext) {
          // Set to "Remove from Chat" state
          buttonNode.classList.add('in-context');

          const icon = buttonNode.querySelector('.jp-icon3');
          if (icon) {
            // Create a minus icon
            const minusIcon =
              '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M5 13v-2h14v2z"/></svg>';
            icon.innerHTML = minusIcon;
          }

          const textSpan = buttonNode.querySelector('.button-text');
          if (textSpan) {
            textSpan.textContent = 'Remove from Chat';
          }
        } else {
          // Set to "Add to Chat" state
          buttonNode.classList.remove('in-context');

          const icon = buttonNode.querySelector('.jp-icon3');
          if (icon) {
            icon.innerHTML = addIcon.svgstr;
          }

          const textSpan = buttonNode.querySelector('.button-text');
          if (textSpan) {
            textSpan.textContent = 'Add to Context';
          }
        }
      }
    }
  });
}

/**
 * Initialize JWT authentication check and modal display
 */
export async function initializeJWTAuthenticationModal(
  app: JupyterFrontEnd,
  settingsContainer: NotebookSettingsContainer
): Promise<void> {
  const jwtModalService = JWTAuthModalService.getInstance();

  // Listen for settings widget state changes to detect authentication
  const settingsWidget = settingsContainer.getSettingsWidget();
  settingsWidget.stateChanged.connect(() => {
    const state = settingsWidget.getState();
    if (state.isAuthenticated) {
      // User has authenticated, hide the JWT modal if it's showing
      void jwtModalService.checkAndHideIfAuthenticated();
    }
  });

  // Check authentication status after initialization
  void app.restored.then(async () => {
    // Wait a bit for everything to settle, then check authentication
    setTimeout(async () => {
      await jwtModalService.showIfNeeded();
    }, 1000);

    // Check if we're starting on the launcher page
    setTimeout(async () => {
      const isLauncher = app.shell.currentWidget?.title.label === 'Launcher';
      if (isLauncher) {
        console.log('[Startup] Starting on launcher page - attaching chatbox');
        AppStateService.setLauncherActive(true);
        try {
          if (app.commands.isToggled('application:toggle-right-area')) {
            void app.commands.execute('application:toggle-right-area');
          }
        } catch (error) {
          console.warn('Could not toggle right area:', error);
        }
        attachChatboxToLauncher();

        // Check if welcome tour has been completed
        const tourCompleted = await AppStateService.hasCompletedWelcomeTour();
        const isAuthenticated = await JupyterAuthService.isAuthenticated();
        const isDemoMode = AppStateService.isDemoMode();

        if (!tourCompleted && isAuthenticated && !isDemoMode) {
          console.log(
            '[Startup] Welcome tour not completed and user is authenticated - showing tour'
          );
          // Wait a bit for the chatbox to be fully attached
          setTimeout(() => {
            runWelcomeDemo(app);
          }, 1000);
        } else {
          if (tourCompleted) {
            console.log('[Startup] Welcome tour already completed');
          } else if (!isAuthenticated) {
            console.log(
              '[Startup] User not authenticated - skipping welcome tour'
            );
          } else if (isDemoMode) {
            console.log('[Startup] Demo mode enabled - skipping welcome tour');
          }
        }
      } else {
        console.log('[Startup] Not starting on launcher page');
        AppStateService.setLauncherActive(false);
      }
    }, 500); // Small delay to ensure the shell is fully initialized
  });
}
