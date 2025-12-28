import { JupyterFrontEnd } from '@jupyterlab/application';
import { ICommandPalette } from '@jupyterlab/apputils';
import { runDemoSequence, createSampleDemoSequence } from './demo';
import { AppStateService } from '../AppState';

/**
 * Register demo commands for the sage-ai extension
 */
export function registerDemoCommands(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  registerStartDemoCommand(app, palette);
}

/**
 * Register the start demo command
 */
function registerStartDemoCommand(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): void {
  const startDemoCommand: string = 'signalpilot:demo';

  app.commands.addCommand(startDemoCommand, {
    label: 'Start SignalPilot Demo',
    execute: async () => {
      console.log('[Demo] Starting demo...');

      try {
        // Ensure we have a notebook open
        const currentNotebookId = AppStateService.getCurrentNotebookId();
        if (!currentNotebookId) {
          alert('Please open a notebook before starting the demo.');
          return;
        }

        // Show the chat widget
        AppStateService.getState().chatContainer?.chatWidget.showHistoryWidget();

        // Create sample demo sequence
        const { messages: demoMessages, originalThreadData } =
          createSampleDemoSequence();

        // Run the demo with control panel (15ms delay for smoother streaming)
        await runDemoSequence(demoMessages, 15, true, originalThreadData);

        console.log('[Demo] Demo initiated successfully');
      } catch (error) {
        console.error('[Demo] Error during demo:', error);
        alert(
          `Demo failed: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }
  });

  // Add command to palette
  palette.addItem({ command: startDemoCommand, category: 'SignalPilot AI' });
  console.log('[Demo] Demo command registered');
}
