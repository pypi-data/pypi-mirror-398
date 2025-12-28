/**
 * SignalPilot Replay and Demo Mode Module
 *
 * Handles replay initialization, notebook restoration, and takeover mode
 */

import { JupyterFrontEnd } from '@jupyterlab/application';
import { AppStateService } from '../AppState';
import { ReplayLoadingOverlayWidget } from '../Components/ReplayLoadingOverlay/ReplayLoadingOverlayWidget';
import {
  disableTakeoverMode,
  removeStoredReplayId
} from '../utils/replayIdManager';

// Global variable to manage the replay loading overlay
let replayLoadingOverlay: ReplayLoadingOverlayWidget | null = null;

/**
 * Wait logic with race condition:
 * EITHER: Wait 500ms
 * OR: Check the URL, if ?reset param is added and removed then add a 50ms wait and stop
 */
async function raceWaitCondition(): Promise<void> {
  return new Promise<void>(resolve => {
    let resolved = false;
    let resetParamDetected = false;

    // Option 1: 500ms timeout
    const timeoutId = setTimeout(() => {
      if (!resolved) {
        resolved = true;
        cleanup();
        console.log('[Replay Wait] 500ms timeout completed');
        resolve();
      }
    }, 500);

    // Option 2: Watch for ?reset param being added and removed using events
    const handleUrlChange = () => {
      if (resolved) {
        return;
      }

      const urlParams = new URLSearchParams(window.location.search);
      const hasResetParam = urlParams.has('reset');

      if (hasResetParam && !resetParamDetected) {
        // Reset param was just added
        resetParamDetected = true;
        console.log('[Replay Wait] Reset param detected in URL');
      } else if (!hasResetParam && resetParamDetected) {
        // Reset param was removed after being added
        console.log('[Replay Wait] Reset param removed, waiting 50ms');
        setTimeout(() => {
          if (!resolved) {
            resolved = true;
            cleanup();
            console.log('[Replay Wait] Reset param condition completed');
            resolve();
          }
        }, 50);
      }
    };

    const cleanup = () => {
      clearTimeout(timeoutId);
      window.removeEventListener('popstate', handleUrlChange);
      window.removeEventListener('hashchange', handleUrlChange);
    };

    // Listen for URL changes via browser navigation events
    window.addEventListener('popstate', handleUrlChange);
    window.addEventListener('hashchange', handleUrlChange);

    // Check initial state in case the param is already present/removed
    handleUrlChange();
  });
}

/**
 * Handle replay initialization after all services are ready
 * This waits for SignalPilot to fully initialize before starting the demo
 */
export async function handleReplayInitialization(
  replayId: string,
  app: JupyterFrontEnd
): Promise<void> {
  console.log('[Replay] Handling replay initialization...');

  // Create and show loading overlay
  replayLoadingOverlay = new ReplayLoadingOverlayWidget();
  document.body.appendChild(replayLoadingOverlay.node);
  replayLoadingOverlay.show();
  console.log('[Replay] Loading overlay shown');

  try {
    // Import replay functionality
    const { fetchReplayData } = await import('../Demo/replay');
    const { runDemoSequence } = await import('../Demo/demo');

    // Start fetching replay data immediately (in parallel with initialization)
    console.log('[Replay] Starting to fetch replay data from backend...');
    const replayDataPromise = fetchReplayData(replayId);

    // CRITICAL: Wait for launcher to be fully rendered and chatbox to be fully loaded
    // This prevents race conditions where replay tries to open a notebook before
    // the chatbox has been attached to the launcher and cleared
    console.log('[Replay] Waiting for chatbox to be fully ready...');
    await AppStateService.waitForChatboxReady(100, 100); // Wait up to 10 seconds
    console.log(
      '[Replay] Chatbox is fully ready, proceeding with replay initialization'
    );

    // Wait for essential services to be initialized
    // Poll until AppState services are ready
    let retries = 50; // 50 retries * 200ms = 10 seconds max wait
    while (retries > 0) {
      const notebookTools = AppStateService.getNotebookTools();
      const chatContainer = AppStateService.getChatContainerSafe();

      if (notebookTools && chatContainer && chatContainer.chatWidget) {
        console.log('[Replay] All services are ready, proceeding with replay');
        break;
      }

      console.log(
        `[Replay] Waiting for services to initialize... (${retries} retries left)`
      );
      await new Promise(resolve => setTimeout(resolve, 200));
      retries--;
    }

    if (retries === 0) {
      throw new Error('Timeout waiting for SignalPilot services to initialize');
    }

    // Small additional delay to ensure everything is fully ready
    await new Promise(resolve => setTimeout(resolve, 500));

    // Create a new notebook for the replay demo
    const notebookTools = AppStateService.getNotebookTools();
    if (!notebookTools) {
      throw new Error('NotebookTools not available');
    }

    // Generate a unique notebook name with timestamp
    const timestamp = new Date()
      .toISOString()
      .replace(/[:.]/g, '-')
      .slice(0, -5);
    const notebookName = `replay-demo-${timestamp}.ipynb`;

    console.log('[Replay] Creating new notebook with tracking:', notebookName);
    const result = await notebookTools.createNotebookWithTracking(notebookName);

    if (!result.success) {
      throw new Error('Failed to create notebook for replay');
    }

    console.log(`[Replay] Notebook created with ID: ${result.notebookId}`);

    // Wait for the notebook to be fully initialized
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Wait for the replay data fetch to complete (started earlier)
    console.log('[Replay] Waiting for replay data to finish loading...');
    const { messages: demoMessages, originalThreadData } =
      await replayDataPromise;

    if (!demoMessages || demoMessages.length === 0) {
      throw new Error('No demo messages received from replay API');
    }

    console.log(
      `[Replay] Received ${demoMessages.length} messages, starting demo...`
    );

    // Extract and display the first user message in the loading overlay
    const firstUserMessage = demoMessages.find(msg => msg.role === 'user');
    if (firstUserMessage && typeof firstUserMessage.content === 'string') {
      console.log('[Replay] Displaying first user prompt in loading overlay');
      replayLoadingOverlay.updateMessage(firstUserMessage.content);
    }

    // Show the chat widget
    const chatContainer = AppStateService.getChatContainerSafe();
    if (chatContainer && chatContainer.chatWidget) {
      chatContainer.chatWidget.showHistoryWidget();
    }

    // Start pre-loading the welcome message immediately (in parallel with demo)
    console.log('[Replay] Starting welcome message pre-load...');
    const welcomeMessagePromise = chatContainer?.chatWidget.startWelcomeMessagePreload();

    // Small delay before starting the demo
    await new Promise(resolve => setTimeout(resolve, 500));

    // Wait logic before starting replay:
    // EITHER: Wait 500ms OR check if ?reset param is added and removed (with 50ms wait after)
    await raceWaitCondition();

    // Start the demo with the fetched data and original thread data
    // Pass the loading overlay so it can be hidden when first message is sent
    await runDemoSequence(
      demoMessages,
      8,
      true,
      originalThreadData,
      replayLoadingOverlay,
      app
    );

    console.log('[Replay] Replay demo completed successfully');

    // Show the welcome message now that the demo is complete
    if (chatContainer && chatContainer.chatWidget) {
      console.log('[Replay] Demo complete, showing welcome message...');
      await chatContainer.chatWidget.showWelcomeMessage();
    }

    // Clear the replayId from localStorage after first replay to prevent re-triggering
    removeStoredReplayId();
    console.log(
      '[Replay] Cleared replayId from localStorage to prevent re-triggering'
    );

    // Save the notebook after replay completes
    try {
      const currentNotebook = AppStateService.getCurrentNotebook();
      if (currentNotebook) {
        await currentNotebook.context.save();
        console.log('[Replay] Notebook saved successfully');
      } else {
        console.warn('[Replay] No current notebook found to save');
      }
    } catch (saveError) {
      console.error('[Replay] Error saving notebook:', saveError);
    }
  } catch (error) {
    console.error('[Replay] Error during replay initialization:', error);

    // Hide the loading overlay on error
    if (replayLoadingOverlay) {
      replayLoadingOverlay.hide();
      setTimeout(() => {
        if (replayLoadingOverlay && replayLoadingOverlay.node.parentNode) {
          replayLoadingOverlay.node.parentNode.removeChild(
            replayLoadingOverlay.node
          );
        }
        replayLoadingOverlay = null;
      }, 300);
    }

    alert(
      `Replay failed: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

/**
 * Handle notebook restoration after user logs in via "Login to Chat"
 * Opens the stored notebook and bypasses welcome message
 */
export async function handleNotebookRestoration(
  notebookPath: string
): Promise<void> {
  console.log('[Notebook Restore] Handling notebook restoration...');

  try {
    // Wait for services to initialize (using the race condition like replay does)
    await raceWaitCondition();
    console.log('[Notebook Restore] Wait condition completed');

    // Wait for essential services to be initialized
    let retries = 50;
    while (retries > 0) {
      const notebookTools = AppStateService.getNotebookTools();
      const chatContainer = AppStateService.getChatContainerSafe();

      if (notebookTools && chatContainer && chatContainer.chatWidget) {
        console.log('[Notebook Restore] All services are ready');
        break;
      }

      await new Promise(resolve => setTimeout(resolve, 200));
      retries--;
    }

    if (retries === 0) {
      throw new Error('Timeout waiting for services to initialize');
    }

    const notebookTools = AppStateService.getNotebookTools();
    if (!notebookTools) {
      throw new Error('NotebookTools not available');
    }

    // Clear the stored notebook path from localStorage
    const { removeStoredLastNotebookPath } = await import(
      '../utils/replayIdManager'
    );
    removeStoredLastNotebookPath();
    console.log(
      '[Notebook Restore] Cleared stored notebook path from localStorage'
    );

    // Open the stored notebook
    console.log('[Notebook Restore] Opening notebook:', notebookPath);
    const opened = await notebookTools.open_notebook({
      path_of_notebook: notebookPath,
      create_new: false
    });

    if (!opened) {
      throw new Error('Failed to open stored notebook');
    }

    // Wait for notebook to be fully loaded
    await new Promise(resolve => setTimeout(resolve, 1000));

    console.log(
      '[Notebook Restore] Notebook restoration completed successfully'
    );
  } catch (error) {
    console.error(
      '[Notebook Restore] Error during notebook restoration:',
      error
    );
    // Clear the stored path even on error
    const { removeStoredLastNotebookPath } = await import(
      '../utils/replayIdManager'
    );
    removeStoredLastNotebookPath();
    alert(
      `Notebook restoration failed: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

/**
 * Handle takeover mode re-entry after user signs in
 * Creates new notebook, puts prompt in chatbox, and sends message
 */
export async function handleTakeoverModeReentry(): Promise<void> {
  console.log('[Takeover] Handling takeover mode re-entry...');

  try {
    // Get the takeover prompt from AppState
    const firstMessage = AppStateService.getTakeoverPrompt();
    if (!firstMessage) {
      console.error('[Takeover] No takeover prompt found in AppState');
      AppStateService.setTakeoverMode(false, null);
      disableTakeoverMode();
      return;
    }

    console.log('[Takeover] Takeover prompt from AppState:', { firstMessage });
    // Add waits like how we wait for replay (500ms or reset url hits race condition)
    await new Promise(resolve => setTimeout(resolve, 500));
    console.log('[Takeover] Initial wait completed');

    // Clear takeover flag and data from localStorage immediately
    disableTakeoverMode();
    console.log('[Takeover] Cleared takeover mode from localStorage');

    // Clear from AppState
    AppStateService.setTakeoverMode(false, null);
    console.log('[Takeover] Cleared takeover mode from AppState');

    // Wait for essential services to be initialized
    let retries = 50;
    while (retries > 0) {
      const notebookTools = AppStateService.getNotebookTools();
      const chatContainer = AppStateService.getChatContainerSafe();

      if (notebookTools && chatContainer && chatContainer.chatWidget) {
        console.log('[Takeover] All services are ready');
        break;
      }

      await new Promise(resolve => setTimeout(resolve, 200));
      retries--;
    }

    if (retries === 0) {
      throw new Error('Timeout waiting for services to initialize');
    }

    const notebookTools = AppStateService.getNotebookTools();
    if (!notebookTools) {
      throw new Error('NotebookTools not available');
    }

    // Create a new notebook
    console.log('[Takeover] Creating new notebook with tracking');
    const timestamp = new Date()
      .toISOString()
      .replace(/[:.]/g, '-')
      .slice(0, -5);
    const notebookName = `takeover-${timestamp}.ipynb`;

    const result = await notebookTools.createNotebookWithTracking(notebookName);

    if (!result.success) {
      throw new Error('Failed to create notebook for takeover');
    }

    console.log(`[Takeover] Notebook created with ID: ${result.notebookId}`);

    // Wait for notebook to open
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Get the chat container and set up the message
    const chatContainer = AppStateService.getChatContainerSafe();
    if (!chatContainer || !chatContainer.chatWidget) {
      throw new Error('Chat container not available');
    }

    const chatWidget = chatContainer.chatWidget;
    const inputManager = chatWidget.inputManager;

    // Create a new chat thread for this takeover session
    console.log('[Takeover] Creating new chat thread');
    const newThread = await chatWidget.threadManager.createNewThread();
    if (!newThread) {
      console.warn('[Takeover] Failed to create new thread, continuing anyway');
    } else {
      console.log('[Takeover] Created new thread:', newThread.id);
    }

    // Show the chat widget
    chatWidget.showHistoryWidget();

    // Wait a bit for UI to be ready
    await new Promise(resolve => setTimeout(resolve, 500));

    // Put the takeover prompt in the chatbox
    inputManager.setInputValue(firstMessage);
    console.log('[Takeover] Set first message in chatbox:', firstMessage);

    // Send the message
    await inputManager.sendMessage();
    console.log('[Takeover] Sent first message');

    console.log('[Takeover] Takeover mode re-entry completed successfully');
  } catch (error) {
    console.error('[Takeover] Error during takeover mode re-entry:', error);
    disableTakeoverMode(); // Clean up even on error
    alert(
      `Takeover mode failed: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}
