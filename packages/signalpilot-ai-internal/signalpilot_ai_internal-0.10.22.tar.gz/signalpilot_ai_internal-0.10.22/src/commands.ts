import { JupyterFrontEnd } from '@jupyterlab/application';
import { ICommandPalette } from '@jupyterlab/apputils';
import { AppStateService } from './AppState';
import { StateDBCachingService, STATE_DB_KEYS } from './utils/backendCaching';
import { requestAPI } from './handler';
import { registerAddCtaDivCommand } from './welcomeCta';
import { runWelcomeDemo } from './demo';
import { registerDemoCommands } from './Demo/demo_commands';
import { v4 as uuidv4 } from 'uuid';
import { removeStoredReplayId } from './utils/replayIdManager';


/**
 * Helper function to attach the chatbox widget to the launcher
 * Uses the existing chatbox from AppStateService instead of creating a new one
 * Includes retry mechanism to wait for launcher content to render
 */
export function attachChatboxToLauncher(
  retries: number = 10,
  delay: number = 100
): void {
  const launcherBody = document.querySelector('.jp-Launcher-content');
  if (!launcherBody) {
    if (retries > 0) {
      console.log(
        `[Launcher] Launcher content not found, retrying... (${retries} attempts left)`
      );
      setTimeout(() => attachChatboxToLauncher(retries - 1, delay), delay);
      return;
    }
    console.warn(
      '[Launcher] jp-Launcher-content not found after retries. ChatBox could not be attached.'
    );
    return;
  }

  // Check if chatbox is already attached
  const existingWrapper = launcherBody.querySelector(
    '.sage-chatbox-launcher-wrapper'
  );
  if (existingWrapper) {
    console.log('[Launcher] ChatBox already attached to launcher, skipping');
    return;
  }

  // Get the existing chatbox from AppStateService
  const chatContainer = AppStateService.getChatContainerSafe();
  if (!chatContainer) {
    if (retries > 0) {
      console.log(
        `[Launcher] ChatContainer not ready, retrying... (${retries} attempts left)`
      );
      setTimeout(() => attachChatboxToLauncher(retries - 1, delay), delay);
      return;
    }
    console.warn(
      '[Launcher] ChatContainer not found in AppStateService after retries. Cannot attach chatbox to launcher.'
    );
    return;
  }

  const chatboxWidget = chatContainer.chatWidget;

  // Create a wrapper for the chatbox
  const wrapper = document.createElement('div');
  wrapper.className = 'sage-chatbox-launcher-wrapper';

  // Attach the chatbox widget to the wrapper
  wrapper.appendChild(chatboxWidget.node);

  // Insert the chatbox at the beginning of launcher body (before launcher sections)
  launcherBody.insertBefore(wrapper, launcherBody.firstChild);

  console.log('[Launcher] ChatBox widget attached to launcher');

  // Mark the chatbox as ready after attachment completes
  // This ensures replay mode can proceed even if the subscription-based
  // handleSwitchToLauncher hasn't fired yet
  setTimeout(() => {
    if (chatboxWidget && typeof chatboxWidget.setReady === 'function') {
      chatboxWidget.setReady();
      console.log('[Launcher] Chatbox marked as ready after attachment');
    }
  }, 200); // Small delay to ensure DOM is fully updated

  // Close the chat tab and sidebar when in launcher mode
  closeChatTabAndSidebar();
}

/**
 * Helper function to detach the chatbox from the launcher and restore it to the sidebar
 */
export function detachChatboxFromLauncher(app: JupyterFrontEnd): void {
  console.log('[Launcher] Detaching chatbox from launcher');

  // Find the wrapper in the launcher
  const launcherBody = document.querySelector('.jp-Launcher-content');
  const wrapper = launcherBody?.querySelector('.sage-chatbox-launcher-wrapper');

  if (!wrapper) {
    console.log(
      '[Launcher] No chatbox wrapper found in launcher, nothing to detach'
    );
    return;
  }

  // Get the chatbox widget node
  const chatContainer = AppStateService.getChatContainerSafe();
  if (!chatContainer) {
    console.warn('[Launcher] ChatContainer not found in AppStateService');
    return;
  }

  const chatboxWidget = chatContainer.chatWidget;

  // Remove the wrapper from the launcher
  wrapper.remove();

  // Re-attach the chatbox to the chat container widget
  // The chat container is a Lumino Widget, so we need to append to its node
  chatContainer.node.appendChild(chatboxWidget.node);

  console.log(
    '[Launcher] ChatBox widget detached from launcher and restored to sidebar'
  );

  // Re-open the sidebar and show the chat tab
  reopenChatSidebar(app);
}

/**
 * Helper function to close the chat tab and sidebar when in launcher mode
 */
export function closeChatTabAndSidebar(): void {
  console.log('[Launcher] Closing chat tab and sidebar');

  // Skip hiding chat tab if in demo mode
  if (AppStateService.isDemoMode()) {
    console.log('[Launcher] Demo mode active - keeping chat tab visible');
    return;
  }

  // Find and hide the chat tab in the tab bar
  const chatTab = document.querySelector(
    'li.lm-TabBar-tab[role="tab"][data-id="sage-ai-chat-container"]'
  ) as HTMLElement;
  if (chatTab) {
    chatTab.style.display = 'none';
    console.log('[Launcher] Chat tab hidden');
  }
}

/**
 * Helper function to reopen the chat sidebar and show the tab when leaving launcher
 */
export function reopenChatSidebar(app: JupyterFrontEnd): void {
  console.log('[Launcher] Reopening chat sidebar');

  // Show the chat tab in the tab bar
  const chatTab = document.querySelector(
    'li.lm-TabBar-tab[role="tab"][data-id="sage-ai-chat-container"]'
  ) as HTMLElement;
  if (chatTab) {
    chatTab.style.display = '';
    console.log('[Launcher] Chat tab shown');
  }

  // Activate the chat container to open the sidebar
  try {
    app.shell.activateById('sage-ai-chat-container');
    console.log('[Launcher] Chat sidebar activated');
  } catch (error) {
    console.warn('[Launcher] Failed to activate chat sidebar:', error);
  }
}

/**
 * Register the test session timer banner command
 */
function registerTestSessionTimerBannerCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const testTimerBannerCommandId = 'signalpilot-ai-internal:test-timer-banner';
  let testTimerBannerWidget: any = null;

  app.commands.addCommand(testTimerBannerCommandId, {
    label: 'Test Session Timer Banner',
    execute: async () => {
      try {
        // Import the SessionTimerBannerWidget
        const { SessionTimerBannerWidget } = await import(
          './Components/SessionTimerBanner/SessionTimerBannerWidget'
        );

        // If banner already exists, remove it
        if (testTimerBannerWidget && testTimerBannerWidget.node.parentNode) {
          testTimerBannerWidget.node.parentNode.removeChild(testTimerBannerWidget.node);
          testTimerBannerWidget.dispose();
          testTimerBannerWidget = null;
          // Remove the class that adds margin
          document.body.classList.remove('sage-timer-banner-visible');
          console.log('[Test] Timer banner removed and margin class removed');
          return;
        }

        // Create and add the banner with forceDisplay=true
        testTimerBannerWidget = new SessionTimerBannerWidget(true);
        
        const mainShell = document.querySelector('.lm-Widget.jp-LabShell');
        if (mainShell && mainShell.parentNode) {
          mainShell.parentNode.insertBefore(testTimerBannerWidget.node, mainShell);
          // Add class to body to apply margin for the banner
          document.body.classList.add('sage-timer-banner-visible');
          console.log('[Test] Timer banner added to DOM and margin class applied');
        } else {
          console.warn('[Test] Could not find main shell to attach timer banner');
        }
      } catch (error) {
        console.error('[Test] Failed to add timer banner:', error);
      }
    }
  });

  palette.addItem({ command: testTimerBannerCommandId, category: 'SignalPilot AI' });
}

/**
 * Register the test session expired modal command
 */
function registerTestSessionExpiredModalCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const testExpiredModalCommandId = 'signalpilot-ai-internal:test-expired-modal';

  app.commands.addCommand(testExpiredModalCommandId, {
    label: 'Test Session Expired Modal',
    execute: async () => {
      try {
        // Import the widget and create a test instance
        const { SessionTimerBannerWidget } = await import(
          './Components/SessionTimerBanner/SessionTimerBannerWidget'
        );

        // Create a test widget that forces the modal to show
        class TestModalWidget extends SessionTimerBannerWidget {
          constructor() {
            super();
            // Force the modal to show immediately
            (this as any).showExpiredModal = true;
            this.update();
          }
        }

        const testWidget = new TestModalWidget();
        
        // Add to body temporarily
        document.body.appendChild(testWidget.node);
        
        console.log('[Test] Session expired modal displayed');
        
        // Clean up after 30 seconds or when user interacts
        setTimeout(() => {
          if (testWidget.node.parentNode) {
            testWidget.node.parentNode.removeChild(testWidget.node);
            testWidget.dispose();
          }
        }, 30000);
      } catch (error) {
        console.error('[Test] Failed to show expired modal:', error);
      }
    }
  });

  palette.addItem({ command: testExpiredModalCommandId, category: 'SignalPilot AI' });
}

/**
 * Register the exit demo mode command
 */
function registerExitDemoModeCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const exitDemoModeCommand: string = 'signalpilot-ai-internal:exit-demo-mode';

  console.log('[Commands] Registering exit demo mode command...');

  app.commands.addCommand(exitDemoModeCommand, {
    label: 'Exit Demo Mode',
    execute: async () => {
      console.log('[Commands] 🎯 Exit demo mode command executed!');

      try {
        // Set demo mode to false in AppState and cache
        await AppStateService.setDemoMode(false);
        console.log('[Commands] Demo mode set to false');

        // Remove the replay ID from localStorage
        removeStoredReplayId();
        console.log('[Commands] Replay ID removed from localStorage');

        console.log('[Commands] ✅ Successfully exited demo mode');
        alert('Demo mode has been exited. The page will now reload.');

        // Reload the page to reflect the changes
        window.location.reload();
      } catch (error) {
        console.error('[Commands] ❌ Error exiting demo mode:', error);
        alert(
          `Failed to exit demo mode: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }
  });

  // Add the command to the command palette
  palette.addItem({
    command: exitDemoModeCommand,
    category: 'SignalPilot AI'
  });
  console.log(
    '[Commands] ✅ Exit demo mode command registered and added to palette'
  );
}

/**
 * Register all commands for the sage-ai extension
 */
export function registerCommands(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  // Register test notebook command
  registerTestNotebookCommand(app, palette);

  // Register test add with diff command
  registerTestAddWithDiffCommand(app, palette);

  // Register test edit with diff command
  registerTestEditWithDiffCommand(app, palette);

  // Register test multiple diffs command
  registerTestMultipleDiffsCommand(app, palette);

  // Register test tracking persistence command
  registerTestTrackingPersistenceCommand(app, palette);

  // Register tracking report command
  registerTrackingReportCommand(app, palette);

  // Register fix tracking IDs command
  registerFixTrackingIDsCommand(app, palette);

  // Register export error logs command
  registerExportErrorLogsCommand(app, palette);

  // Register clear error logs command
  registerClearErrorLogsCommand(app, palette);

  // Register add CTA div command
  registerAddCtaDivCommand(app, palette);

  registerHelloWorldCommand(app, palette);

  registerReadAllFilesCommand(app, palette);

  // Register welcome demo command
  registerWelcomeDemoCommand(app, palette);

  // Register export to HTML command
  registerExportToHTMLCommand(app, palette);

  // Register Publish Report and Deploy & Share commands
  registerPublishReportCommand(app, palette);
  registerDeployAndShareCommand(app, palette);

  // Register download thread command
  registerDownloadThreadCommand(app, palette);
  registerDemoCommands(app, palette);

  // Register session timer test commands
  registerTestSessionTimerBannerCommand(app, palette);
  registerTestSessionExpiredModalCommand(app, palette);

  // Register exit demo mode command
  registerExitDemoModeCommand(app, palette);
}

/**
 * Register the test notebook command
 */
function registerTestNotebookCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const testNotebookCommand: string = 'sage-ai:test-notebook';

  app.commands.addCommand(testNotebookCommand, {
    label: 'Test Notebook',
    execute: async () => {
      const notebookTools = AppStateService.getNotebookTools();

      // Test our NotebookTools class by adding a cell with tracking
      const trackingId = notebookTools.add_cell({
        cell_type: 'code',
        source:
          '# This is a test cell created by NotebookTools\nprint("Hello from SignalPilot AI!")\nimport time\ntime.sleep(1)\nprint("Cell with stable tracking ID!")',
        summary: 'Test cell created with tracking ID',
        position: null // Append to the end
      });

      // Add a second cell with tracking ID
      const trackingId2 = notebookTools.add_cell({
        cell_type: 'markdown',
        source:
          '# This is a test markdown cell\n\nWith stable tracking ID!\n\n* List item 1\n* List item 2',
        summary: 'Test markdown cell created with tracking ID',
        position: null // Append to the end
      });

      // Show all cells info with their tracking IDs
      console.log('Cell tracking ID 1:', trackingId);
      console.log('Cell tracking ID 2:', trackingId2);

      // Wait 2 seconds then find cells by tracking ID
      setTimeout(() => {
        const cell1 = notebookTools.findCellByAnyId(trackingId);
        const cell2 = notebookTools.findCellByAnyId(trackingId2);

        console.log('Found cell 1 by tracking ID:', cell1 ? 'Yes' : 'No');
        console.log('Found cell 2 by tracking ID:', cell2 ? 'Yes' : 'No');

        // Update cell content to demonstrate persistence
        if (cell1) {
          notebookTools.edit_cell({
            cell_id: trackingId,
            new_source:
              '# Updated cell content\nprint("This cell was found by tracking ID!")\nimport time\ntime.sleep(1)\nprint("Success!")',
            summary: 'Updated test cell',
            is_tracking_id: true
          });
        }
      }, 2000);
    }
  });

  // Add the test notebook command to the command palette
  palette.addItem({ command: testNotebookCommand, category: 'AI Tools' });
}

/**
 * Register the Publish Report command (duplicates notebook and runs chat subagent)
 */
function registerPublishReportCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const commandId = 'signalpilot-ai-internal:publish-report';

  app.commands.addCommand(commandId, {
    label: 'Publish Report (AI-enhanced copy)',
    execute: async () => {
      try {
        const notebooks = AppStateService.getNotebookTracker();
        const currentNotebook = notebooks.currentWidget;
        if (!currentNotebook) {
          console.warn('[PublishReport] No active notebook');
          return;
        }

        const contentManager = AppStateService.getContentManager();
        const documentManager = AppStateService.getDocumentManager();

        const originalPath = currentNotebook.context.path;
        const baseName = originalPath.split('/').pop() || 'notebook.ipynb';
        const dir = originalPath.slice(
          0,
          originalPath.length - baseName.length
        );
        const nameNoExt = baseName.replace(/\.ipynb$/i, '');
        const targetName = nameNoExt.endsWith('_report')
          ? `${nameNoExt}_v2.ipynb`
          : `${nameNoExt}_report.ipynb`;
        const targetPath = `${dir}${targetName}`;

        // Read original to inherit minimal metadata and capture original notebook ID
        let originalMetadata: any = {};
        let originalNotebookId: string | null = null;
        try {
          const nbFile = await contentManager.get(originalPath);
          originalMetadata = nbFile?.content?.metadata || {};
          originalNotebookId = originalMetadata?.sage_ai?.unique_id || null;
        } catch (e) {
          console.warn('[PublishReport] Failed to read original metadata:', e);
        }

        // Create empty notebook content for the report copy
        const newReportId = uuidv4();
        const emptyNotebook = {
          cells: [],
          metadata: {
            ...originalMetadata,
            sage_ai: {
              ...(originalMetadata?.sage_ai || {}),
              unique_id: newReportId
            }
          },
          nbformat: 4,
          nbformat_minor: 5
        };

        await contentManager.save(targetPath, {
          type: 'notebook',
          format: 'json',
          content: emptyNotebook
        });

        // Open the new notebook
        documentManager.open(targetPath);
        // Ensure chat is bound to the new notebook ID before sending
        AppStateService.setCurrentNotebookId(newReportId);
        AppStateService.switchChatContainerToNotebook(newReportId);

        const chatContainer = AppStateService.getChatContainerSafe();
        if (chatContainer?.chatWidget?.reinitializeForNotebook) {
          await chatContainer.chatWidget.reinitializeForNotebook(newReportId);
        }

        // Build user instruction for the agent
        const userInstruction = originalNotebookId
          ? `Transform the contents of the ORIGINAL notebook (ID: ${originalNotebookId}) into a polished report inside the CURRENT notebook (ID: ${newReportId}). Follow the system prompt instructions strictly. Perform all edits in the current (empty) report notebook without a plan.`
          : `Transform the previous active notebook into a polished report inside the CURRENT notebook (ID: ${newReportId}). Follow the system prompt instructions strictly. Perform all edits in the current (empty) report notebook.`;

        // Enable auto-run mode for seamless report generation
        chatContainer?.chatWidget?.conversationService?.setAutoRun(true);

        // Show a quick banner message in chat
        chatContainer?.chatWidget?.messageComponent?.addSystemMessage(
          'Report Creator is enhancing your notebook...'
        );

        const hiddenMessage = true;

        // Set persistent agent so iterations keep using the Report Creator prompt
        chatContainer?.chatWidget?.chatHistoryManager?.updateCurrentThreadAgent(
          'report_creator'
        );

        chatContainer?.chatWidget?.sendPromptMessage(
          userInstruction,
          hiddenMessage
        );
      } catch (error) {
        console.error('[PublishReport] Failed:', error);
        alert(
          `Failed to publish report: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }
  });

  palette.addItem({ command: commandId, category: 'SignalPilot AI' });
}

/**
 * Register the Deploy & Share command (HTML export + upload)
 */
function registerDeployAndShareCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const commandId = 'signalpilot-ai-internal:deploy-and-share';

  app.commands.addCommand(commandId, {
    label: 'Deploy & Share (HTML + Link)',
    execute: async () => {
      try {
        const notebooks = AppStateService.getNotebookTracker();
        const currentNotebook = notebooks.currentWidget;
        if (!currentNotebook) {
          console.warn('[DeployShare] No active notebook');
          return;
        }
        const notebookPath = currentNotebook.context.path;

        // Generate HTML via existing handler
        const response = await requestAPI<any>('notebook/to-html', {
          method: 'POST',
          body: JSON.stringify({
            notebook_path: notebookPath,
            include_input: true,
            include_output: true,
            include_images: true
          })
        });

        if (!response?.success) {
          throw new Error(response?.error || 'Failed to generate HTML');
        }

        const htmlContent = response.html_content as string;

        // Load IPYNB content for paired upload
        let ipynbContent: string | null = null;
        try {
          const contentManager = AppStateService.getContentManager();
          const file = await contentManager.get(notebookPath);
          if (file?.content) {
            ipynbContent = JSON.stringify(file.content);
          }
        } catch (e) {
          console.warn('[DeployShare] Failed to read notebook JSON:', e);
        }

        // Upload via CloudUploadService
        const { CloudUploadService } = await import(
          './Services/CloudUploadService'
        );
        const svc = CloudUploadService.getInstance();
        const filename =
          (notebookPath.split('/').pop() || 'notebook.ipynb').replace(
            /\.ipynb$/i,
            ''
          ) + '.html';

        const deployment = await svc.uploadWorkflow(
          filename,
          htmlContent,
          notebookPath,
          ipynbContent
        );

        // Surface the link
        const url = deployment.deployedUrl;
        console.log('[DeployShare] Deployed URL:', url);
        alert(`Report deployed.\n\n${url}`);
      } catch (error) {
        console.error('[DeployShare] Failed:', error);
        alert(
          `Failed to deploy & share: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }
  });

  palette.addItem({ command: commandId, category: 'SignalPilot AI' });
}

/**
 * Register the test add with diff command
 */
function registerTestAddWithDiffCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const testAddWithDiffCommand: string = 'sage-ai:test-add-with-diff';

  app.commands.addCommand(testAddWithDiffCommand, {
    label: 'Test Add Cell With Diff',
    execute: async () => {
      const notebookTools = AppStateService.getNotebookTools();
      const diffManager = AppStateService.getNotebookDiffManager();
      const notebooks = AppStateService.getNotebookTracker();

      // Step 1: Add a new cell with tracking ID
      const trackingId = notebookTools.add_cell({
        cell_type: 'code',
        source:
          '# Test cell with diff view\nprint("This cell demonstrates diff view")\nfor i in range(5):\n    print(f"Count: {i}")',
        summary: 'Test cell with diff view',
        position: null
      });

      // Step 2: Find the added cell by tracking ID
      const cellInfo = notebookTools.findCellByAnyId(trackingId);
      if (!cellInfo) {
        console.error('Could not find the newly added cell by tracking ID');
        return;
      }

      // Get current notebook path
      const notebookPath = notebooks.currentWidget?.context.path || null;

      // Step 3: Track the diff in the diff manager with notebook path
      diffManager.trackAddCell(
        trackingId,
        cellInfo.cell.model.sharedModel.getSource(),
        'Test cell with diff view',
        notebookPath
      );

      // Step 4: Display the diff view
      console.log('Displaying diff view...');
      const diffResult = notebookTools.display_diff(
        cellInfo.cell,
        '', // Original content (empty for new cell)
        cellInfo.cell.model.sharedModel.getSource(),
        'add'
      );

      // Store the updated cell ID and update the mapping in diff manager
      const updatedCellId = diffResult.cellId;
      console.log(
        `Original tracking ID: ${trackingId}, Updated cell ID: ${updatedCellId}`
      );
      diffManager.updateCellIdMapping(trackingId, updatedCellId, notebookPath);

      // Step 5: Show approval dialog using the notebook widget for proper positioning
      const activeNotebook = notebooks.currentWidget;

      // Get unique_id from notebook metadata to use as notebook ID
      let notebookUniqueId: string | null = null;
      if (activeNotebook) {
        try {
          const contentManager = AppStateService.getContentManager();
          const nbFile = await contentManager?.get(activeNotebook.context.path);
          if (nbFile?.content?.metadata?.sage_ai?.unique_id) {
            notebookUniqueId = nbFile.content.metadata.sage_ai.unique_id;
          }
        } catch (error) {
          console.warn('Could not get notebook metadata in commands:', error);
        }
      }

      const result = await diffManager.showApprovalDialog(
        activeNotebook ? activeNotebook.node : document.body,
        false, // Use standard dialog mode for notebook context
        false, // Not a run context
        notebookUniqueId ||
          (activeNotebook ? activeNotebook.context.path : null) // Pass the unique_id as notebook ID
      );
      console.log('Diff approval result:', result);

      // Step 7: Demonstrate finding the cell by tracking ID after diff approval
      setTimeout(() => {
        const updatedCellInfo = notebookTools.findCellByAnyId(
          trackingId,
          notebookPath
        );
        console.log(
          'Found cell after diff approval:',
          updatedCellInfo ? 'Yes' : 'No'
        );
      }, 1000);
    }
  });

  // Add the test add with diff command to the command palette
  palette.addItem({ command: testAddWithDiffCommand, category: 'AI Tools' });
}

/**
 * Register the test edit with diff command
 */
function registerTestEditWithDiffCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const testEditWithDiffCommand: string = 'sage-ai:test-edit-with-diff';

  app.commands.addCommand(testEditWithDiffCommand, {
    label: 'Test Edit Cell With Diff',
    execute: async () => {
      const notebookTools = AppStateService.getNotebookTools();
      const diffManager = AppStateService.getNotebookDiffManager();
      const notebooks = AppStateService.getNotebookTracker();

      // Step 1: Add a new cell with tracking ID
      console.log('Step 1: Adding new cell...');
      const trackingId = notebookTools.add_cell({
        cell_type: 'code',
        source:
          '# Original cell content\nprint("This is the original content")\nvalue = 42',
        summary: 'Original test cell',
        position: null
      });

      // Get original content
      const originalContent =
        '# Original cell content\nprint("This is the original content")\nvalue = 42';

      // Step 2: Wait 2 seconds before editing to ensure cell is rendered
      setTimeout(() => {
        console.log('Step 2: Editing cell after 2 seconds...');

        // Step 3: Edit the cell using tracking ID
        const newContent =
          '# Modified cell content\nprint("This content has been modified!")\nvalue = 42\nprint(f"The value is {value}")\n\n# Added a new comment';

        const editSuccess = notebookTools.edit_cell({
          cell_id: trackingId,
          new_source: newContent,
          summary: 'Modified test cell',
          is_tracking_id: true // Indicate we're using a tracking ID
        });

        if (!editSuccess) {
          console.error('Could not edit the cell with tracking ID');
          return;
        }

        // Get current notebook path
        const notebookPath = notebooks.currentWidget?.context.path || null;

        // Step 4: Track the diff in the manager using tracking ID and notebook path
        diffManager.trackEditCell(
          trackingId,
          originalContent,
          newContent,
          'Modified test cell',
          notebookPath
        );

        // Step 5: Wait 2 seconds before showing diff
        setTimeout(async () => {
          console.log('Step 3: Showing diff after edit...');

          // Step 7: Show approval dialog
          const result = await diffManager.showApprovalDialog(
            document.body,
            false, // Standard dialog mode
            false, // Not a run context
            notebooks.currentWidget?.context.path || null // Pass the current notebook path
          );
          console.log('Diff approval result:', result);

          // Step 8: Apply approved diffs and handle rejected ones
          await diffManager.applyApprovedDiffs();
          await diffManager.handleRejectedDiffs();

          // Step 9: Find the cell again by tracking ID after approval
          setTimeout(() => {
            const finalCellInfo = notebookTools.findCellByAnyId(
              trackingId,
              notebookPath
            );
            console.log(
              'Found cell after diff approval:',
              finalCellInfo ? 'Yes' : 'No'
            );
          }, 2000);
        }, 2000);
      }, 2000);
    }
  });

  // Add the test edit with diff command to the command palette
  palette.addItem({ command: testEditWithDiffCommand, category: 'AI Tools' });
}

/**
 * Register the test multiple diffs command
 */
function registerTestMultipleDiffsCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const testMultipleDiffsCommand: string = 'sage-ai:test-multiple-diffs';

  app.commands.addCommand(testMultipleDiffsCommand, {
    label: 'Test Multiple Diffs',
    execute: async () => {
      const notebookTools = AppStateService.getNotebookTools();
      const diffManager = AppStateService.getNotebookDiffManager();
      const notebooks = AppStateService.getNotebookTracker();

      console.log('Running multiple diffs test with tracking IDs...');

      // Step 1: Add multiple cells with different content and get tracking IDs
      const trackingIds: any = [];

      // Add first cell (code)
      const trackingId1 = notebookTools.add_cell({
        cell_type: 'code',
        source: '# First cell\nx = 10\ny = 20\nprint(f"Sum: {x + y}")',
        summary: 'First test cell',
        position: null
      });
      trackingIds.push(trackingId1);
      console.log(`Added cell 1 with tracking ID: ${trackingId1}`);

      // Add second cell (markdown)
      const trackingId2 = notebookTools.add_cell({
        cell_type: 'markdown',
        source:
          '# Second Cell\nThis is a markdown cell for testing multiple diffs.',
        summary: 'Second test cell',
        position: null
      });
      trackingIds.push(trackingId2);
      console.log(`Added cell 2 with tracking ID: ${trackingId2}`);

      // Add third cell (code)
      const trackingId3 = notebookTools.add_cell({
        cell_type: 'code',
        source:
          '# Third cell\nimport matplotlib.pyplot as plt\nplt.figure(figsize=(8, 6))\nplt.plot([1, 2, 3, 4])\nplt.title("Test Plot")',
        summary: 'Third test cell',
        position: null
      });
      trackingIds.push(trackingId3);
      console.log(`Added cell 3 with tracking ID: ${trackingId3}`);

      // Wait to ensure cells are properly created and rendered
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Step 2: Prepare new content for the cells
      const newContents = [
        '# First cell - MODIFIED\nx = 10\ny = 20\nz = 30\nprint(f"Sum: {x + y + z}")', // Modified code
        '# Second Cell - MODIFIED\nThis is a **modified** markdown cell for testing multiple diffs.\n\n- Item 1\n- Item 2', // Modified markdown
        '# Third cell - MODIFIED\nimport matplotlib.pyplot as plt\nimport numpy as np\nx = np.linspace(0, 10, 100)\nplt.figure(figsize=(10, 8))\nplt.plot(x, np.sin(x))\nplt.title("Modified Plot")' // Modified code with plot
      ];

      // Step 3: Track all the diffs but find and display each cell individually
      for (let i = 0; i < trackingIds.length; i++) {
        const trackingId = trackingIds[i];
        // Find the cell by tracking ID
        const cellInfo = notebookTools.findCellByAnyId(trackingId);
        if (!cellInfo) {
          console.error(`Could not find cell with tracking ID ${trackingId}`);
          continue;
        }

        // Get original content
        const originalContent = cellInfo.cell.model.sharedModel.getSource();

        // Get current notebook path
        const notebookPath = notebooks.currentWidget?.context.path || null;

        // Track the diff using tracking ID and notebook path
        diffManager.trackEditCell(
          trackingId,
          originalContent,
          newContents[i],
          `Modified test cell ${i + 1}`,
          notebookPath
        );

        // Display the diff
        console.log(
          `Displaying diff for cell ${i + 1} with tracking ID ${trackingId}...`
        );
      }

      // Step 4: Show approval dialog
      const activeNotebook = notebooks.currentWidget;
      const result = await diffManager.showApprovalDialog(
        activeNotebook ? activeNotebook.node : document.body,
        false, // Use standard dialog mode
        false, // Not a run context
        activeNotebook ? activeNotebook.context.path : null // Pass the notebook path
      );
      console.log('Multiple diffs approval result:', result);

      // Step 5: Apply approved diffs and handle rejected ones
      // await diffManager.applyApprovedDiffs();
      // await diffManager.handleRejectedDiffs();

      // Step 6: Verify all cells can still be found by tracking ID
      setTimeout(() => {
        for (let i = 0; i < trackingIds.length; i++) {
          const trackingId = trackingIds[i];
          const cellInfo = notebookTools.findCellByAnyId(trackingId);
          console.log(
            `Found cell ${i + 1} after diff approval: ${cellInfo ? 'Yes' : 'No'}`
          );
        }
      }, 1000);
    }
  });

  // Add the test multiple diffs command to the command palette
  palette.addItem({
    command: testMultipleDiffsCommand,
    category: 'AI Tools'
  });
}

/**
 * Register the test tracking persistence command
 */
function registerTestTrackingPersistenceCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const testTrackingPersistenceCommand: string =
    'sage-ai:test-tracking-persistence';

  app.commands.addCommand(testTrackingPersistenceCommand, {
    label: 'Test Tracking ID Persistence',
    execute: async () => {
      const notebookTools = AppStateService.getNotebookTools();
      const cellTrackingService = AppStateService.getCellTrackingService();

      console.log('Testing tracking ID persistence...');

      // Get all existing tracking IDs
      const allTrackingIds = cellTrackingService.getAllTrackingIds();
      console.log(`Found ${allTrackingIds.length} cells with tracking IDs`);
      console.log('Tracking IDs:', allTrackingIds);

      // Initialize tracking for any cells without tracking IDs
      cellTrackingService.initializeExistingCells();

      // Get updated list of tracking IDs
      const updatedTrackingIds = cellTrackingService.getAllTrackingIds();
      console.log(
        `Now have ${updatedTrackingIds.length} cells with tracking IDs`
      );

      // Add a new cell and then find it by tracking ID
      const newTrackingId = notebookTools.add_cell({
        cell_type: 'markdown',
        source:
          '# Persistence Test\n\nThis cell tests tracking ID persistence across notebook operations.',
        summary: 'Persistence test cell',
        position: null
      });

      console.log(`Added new cell with tracking ID: ${newTrackingId}`);

      // Find the cell right away
      const immediateFind = notebookTools.findCellByAnyId(newTrackingId);
      console.log('Found cell immediately:', immediateFind ? 'Yes' : 'No');

      // Wait and then find it again
      setTimeout(() => {
        const laterFind = notebookTools.findCellByAnyId(newTrackingId);
        console.log('Found cell after delay:', laterFind ? 'Yes' : 'No');

        if (laterFind) {
          // Edit the cell to show persistence
          notebookTools.edit_cell({
            cell_id: newTrackingId,
            new_source:
              '# Persistence Test - UPDATED\n\nThis cell was successfully found by its tracking ID after a delay!',
            summary: 'Updated persistence test cell',
            is_tracking_id: true
          });

          console.log('Cell updated successfully through tracking ID');
        }
      }, 2000);
    }
  });

  // Add the tracking persistence test to the command palette
  palette.addItem({
    command: testTrackingPersistenceCommand,
    category: 'AI Tools'
  });
}

/**
 * Register the tracking report command
 */
function registerTrackingReportCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const trackingReportCommand: string = 'sage-ai:tracking-id-report';

  app.commands.addCommand(trackingReportCommand, {
    label: 'Show Cell Tracking ID Report',
    execute: () => {
      const trackingIDUtility = AppStateService.getTrackingIDUtility();
      const report = trackingIDUtility.getTrackingIDReport();
      console.log('Cell Tracking ID Report:');
      console.table(report);
    }
  });

  // Add this command to the command palette
  palette.addItem({ command: trackingReportCommand, category: 'AI Tools' });
}

/**
 * Register the fix tracking IDs command
 */
function registerFixTrackingIDsCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const fixTrackingIDsCommand: string = 'sage-ai:fix-tracking-ids';

  app.commands.addCommand(fixTrackingIDsCommand, {
    label: 'Fix Cell Tracking IDs',
    execute: () => {
      const trackingIDUtility = AppStateService.getTrackingIDUtility();
      const fixedCount = trackingIDUtility.fixTrackingIDs();
      console.log(`Fixed tracking IDs for ${fixedCount} cells`);
    }
  });

  // Add this command to the command palette
  palette.addItem({ command: fixTrackingIDsCommand, category: 'AI Tools' });
}

/**
 * Register the export error logs command
 */
function registerExportErrorLogsCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const exportErrorLogsCommand: string = 'sage-ai:export-error-logs';

  app.commands.addCommand(exportErrorLogsCommand, {
    label: 'Export Error Logs to File',
    execute: async () => {
      try {
        // Get error logs from stateDB
        const errorLogs = await StateDBCachingService.getValue(
          STATE_DB_KEYS.ERROR_LOGS,
          ''
        );

        if (!errorLogs.trim()) {
          console.log('No error logs found to export');
          return;
        }

        // Get content manager to save the file
        const contentManager = AppStateService.getContentManager();

        // Save the error logs to error_dump.txt
        await contentManager.save('./error_dump.txt', {
          type: 'file',
          format: 'text',
          content: errorLogs
        });

        console.log('Error logs exported successfully to error_dump.txt');
      } catch (error) {
        console.error('Failed to export error logs:', error);
      }
    }
  });

  // Add this command to the command palette
  palette.addItem({ command: exportErrorLogsCommand, category: 'AI Tools' });
}

/**
 * Register the clear error logs command
 */
function registerClearErrorLogsCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const clearErrorLogsCommand: string = 'sage-ai:clear-error-logs';

  app.commands.addCommand(clearErrorLogsCommand, {
    label: 'Clear Error Logs',
    execute: async () => {
      try {
        // Clear error logs from stateDB
        await StateDBCachingService.setValue(STATE_DB_KEYS.ERROR_LOGS, '');
        console.log('Error logs cleared successfully');
      } catch (error) {
        console.error('Failed to clear error logs:', error);
      }
    }
  });

  // Add this command to the command palette
  palette.addItem({ command: clearErrorLogsCommand, category: 'AI Tools' });
}

function registerHelloWorldCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const helloWorldCommand: string = 'sage-ai:hello-world';

  app.commands.addCommand(helloWorldCommand, {
    label: 'Test Backend Hello World',
    execute: async () => {
      try {
        // Call the hello world endpoint
        const data = await requestAPI<any>('hello-world');
        console.log('Backend response:', data);

        // Show a notification or log the response
        if (data && data.data) {
          console.log('✅ Backend connection successful!');
          console.log('📩 Message:', data.data);
          if (data.message) {
            console.log('📝 Details:', data.message);
          }
        }
      } catch (error) {
        console.error('❌ Failed to connect to backend:', error);
        console.error(
          'The signalpilot-ai-internal server extension appears to be missing or not running.'
        );
      }
    }
  });

  // Add the hello world command to the command palette
  palette.addItem({ command: helloWorldCommand, category: 'AI Tools' });
}

/**
 * Register the read all files command
 */
function registerReadAllFilesCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const readAllFilesCommand: string = 'sage-ai:read-all-files';

  app.commands.addCommand(readAllFilesCommand, {
    label: 'Get Workspace Context',
    execute: async () => {
      try {
        // Call the read-all-files endpoint
        const data = await requestAPI<any>('read-all-files');
        console.log('=== Workspace Context ===');
        console.log(data);

        if (data && data.welcome_context) {
          console.log('\n=== Welcome Context ===');
          console.log(data.welcome_context);
          console.log('\n=== Summary ===');
          console.log(`Total notebooks found: ${data.notebook_count}`);
          console.log(`Total data files found: ${data.data_file_count}`);
        }

        // Attach the existing chatbox from AppStateService to the launcher
        attachChatboxToLauncher();

        // Optionally trigger a welcome message
        // You can customize this to send an initial message if desired
      } catch (error) {
        console.error('❌ Failed to read workspace files:', error);
      }
    }
  });

  // Add the command to the command palette
  palette.addItem({ command: readAllFilesCommand, category: 'AI Tools' });
}

/**
 * Register the welcome demo command
 */
function registerWelcomeDemoCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const welcomeDemoCommand: string = 'sage-ai:welcome-demo';

  console.log('[Commands] Registering welcome demo command...');

  app.commands.addCommand(welcomeDemoCommand, {
    label: 'Show Welcome Tour',
    execute: () => {
      console.log('[Commands] 🎯 Welcome tour command executed!');
      console.log('[Commands] Calling runWelcomeDemo...');
      try {
        runWelcomeDemo(app);
        console.log('[Commands] ✅ runWelcomeDemo call completed');
      } catch (error) {
        console.error('[Commands] ❌ Error calling runWelcomeDemo:', error);
        console.error(
          '[Commands] Error stack:',
          error instanceof Error ? error.stack : 'No stack trace'
        );
      }
    }
  });

  // Add the command to the command palette
  palette.addItem({ command: welcomeDemoCommand, category: 'AI Tools' });
  console.log(
    '[Commands] ✅ Welcome demo command registered and added to palette'
  );
}

/**
 * Register the export to HTML command
 */
function registerExportToHTMLCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const exportToHTMLCommand: string = 'signalpilot-ai-internal:export-notebook-html';

  console.log('[Commands] Registering export to HTML command...');

  app.commands.addCommand(exportToHTMLCommand, {
    label: 'Export Notebook to HTML',
    execute: () => {
      console.log('[Commands] 🎯 Export to HTML command executed!');

      try {
        // Get current notebook
        const notebooks = AppStateService.getNotebookTracker();
        const currentNotebook = notebooks.currentWidget;

        if (!currentNotebook) {
          console.warn('[Commands] No active notebook found');
          return;
        }

        const notebookPath = currentNotebook.context.path;
        console.log('[Commands] Exporting notebook:', notebookPath);

        // Import the HTMLPreviewWidget dynamically
        import('./Components/HTMLPreviewWidget')
          .then(({ HTMLPreviewWidget }) => {
            // Create the preview widget
            const previewWidget = new HTMLPreviewWidget(notebookPath, () => {
              // Close handler - dispose the widget
              previewWidget.dispose();
            });

            // Add widget to the main area
            app.shell.add(previewWidget, 'main');
            app.shell.activateById(previewWidget.id);

            console.log('[Commands] ✅ HTML preview widget opened');
          })
          .catch(error => {
            console.error(
              '[Commands] ❌ Error creating HTML preview widget:',
              error
            );
          });
      } catch (error) {
        console.error('[Commands] ❌ Error in export to HTML command:', error);
      }
    }
  });

  // Add the command to the command palette
  palette.addItem({ command: exportToHTMLCommand, category: 'SignalPilot AI' });
  console.log(
    '[Commands] ✅ Export to HTML command registered and added to palette'
  );
}

/**
 * Register the download thread command
 */
function registerDownloadThreadCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const downloadThreadCommand: string = 'signalpilot-ai-internal:download-thread';

  console.log('[Commands] Registering download thread command...');

  app.commands.addCommand(downloadThreadCommand, {
    label: 'Download Current Thread as JSON',
    execute: async () => {
      console.log('[Commands] 🎯 Download thread command executed!');

      try {
        // Get the chat container and current thread
        const chatContainer = AppStateService.getChatContainerSafe();
        if (!chatContainer) {
          console.warn('[Commands] No chat container found');
          alert('Chat is not initialized. Please open a notebook first.');
          return;
        }

        const chatHistoryManager = chatContainer.chatWidget.chatHistoryManager;
        const currentThread = chatHistoryManager.getCurrentThread();

        if (!currentThread) {
          console.warn('[Commands] No active thread found');
          alert(
            'No active chat thread found. Please start a conversation first.'
          );
          return;
        }

        // Create the thread export data in the backend format
        // Backend format is an array of thread objects matching test_sp.json structure
        const threadExport = [
          {
            id: currentThread.id,
            name: currentThread.name,
            messages: currentThread.messages,
            lastUpdated: currentThread.lastUpdated,
            contexts: currentThread.contexts
              ? Object.fromEntries(currentThread.contexts)
              : {},
            message_timestamps: currentThread.message_timestamps
              ? Object.fromEntries(currentThread.message_timestamps)
              : {},
            continueButtonShown: currentThread.continueButtonShown || false
          }
        ];

        // Convert to JSON string with formatting
        const jsonContent = JSON.stringify(threadExport, null, 2);

        // Create a download link and trigger download
        const blob = new Blob([jsonContent], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        // Create a safe filename
        const safeThreadName = currentThread.name
          .replace(/[^a-z0-9]/gi, '_')
          .toLowerCase();
        const timestamp = new Date()
          .toISOString()
          .replace(/[:.]/g, '-')
          .split('T')[0];
        a.download = `thread_${safeThreadName}_${timestamp}.json`;

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log('[Commands] ✅ Thread downloaded successfully');
        console.log('[Commands] Thread data:', threadExport);
      } catch (error) {
        console.error('[Commands] ❌ Error downloading thread:', error);
        alert(
          `Failed to download thread: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }
  });

  // Add the command to the command palette
  palette.addItem({
    command: downloadThreadCommand,
    category: 'SignalPilot AI'
  });
  console.log(
    '[Commands] ✅ Download thread command registered and added to palette'
  );
}


