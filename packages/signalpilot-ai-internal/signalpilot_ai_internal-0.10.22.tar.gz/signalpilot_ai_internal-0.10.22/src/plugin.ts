import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ISettingRegistry } from '@jupyterlab/settingregistry';
import {
  ICommandPalette,
  IThemeManager,
  IToolbarWidgetRegistry
} from '@jupyterlab/apputils';
import {
  INotebookTracker,
  NotebookPanel,
  INotebookModel
} from '@jupyterlab/notebook';
import { NotebookDiffTools } from './Notebook/NotebookDiffTools';
import { KernelExecutionListener } from './Chat/ChatContextMenu/KernelExecutionListener';
import { IStateDB } from '@jupyterlab/statedb';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { IDisposable } from '@lumino/disposable';
import { activateSignalPilot } from './SignalPilot';
import { NotebookDeploymentButtonWidget } from './Components/NotebookDeploymentButton';
import {
  getGlobalDiffNavigationWidget,
  getGlobalSnippetCreationWidget,
  setGlobalDiffNavigationWidget,
  setGlobalSnippetCreationWidget
} from './globalWidgets';
import { posthogService } from './Services/PostHogService';
import { initializeReplayIdManagement } from './utils/replayIdManager';
import { AppStateService } from './AppState';
import { SessionTimerBannerWidget } from './Components/SessionTimerBanner/SessionTimerBannerWidget';
import { TrialBannerWidget } from './Components/TrialBanner/TrialBannerWidget';
import {
  isCloudDemoSession,
  shouldShowSessionTimerBanner
} from './sessionUtils';

/**
 * SignalPilot Initialization State
 * Tracks when all SignalPilot components have finished loading
 */
let isSignalpilotInitialized = false;
const onInitializeCallbacks: Array<() => void | Promise<void>> = [];

/**
 * Register a callback to run after SignalPilot is fully initialized
 * This ensures components like banners display correctly after backend cache is ready
 */
export function onSignalpilotInitialize(callback: () => void | Promise<void>): void {
  if (isSignalpilotInitialized) {
    // Already initialized, run immediately (non-blocking)
    void Promise.resolve().then(() => callback());
  } else {
    // Not yet initialized, queue for later
    onInitializeCallbacks.push(callback);
  }
}

/**
 * Signal that SignalPilot initialization is complete
 * Runs all queued callbacks in a non-blocking manner
 */
export function signalSignalpilotInitialized(): void {
  if (isSignalpilotInitialized) {
    console.log('[Plugin] SignalPilot already initialized, skipping signal');
    return;
  }

  console.log('[Plugin] SignalPilot initialization complete, running callbacks');
  isSignalpilotInitialized = true;

  // Run all callbacks asynchronously (non-blocking)
  onInitializeCallbacks.forEach(callback => {
    void Promise.resolve().then(() => callback()).catch(error => {
      console.error('[Plugin] Error in onSignalpilotInitialize callback:', error);
    });
  });

  // Clear callbacks array
  onInitializeCallbacks.length = 0;
}

/**
 * Initialization data for the sage-ai extension
 */
export const plugin: JupyterFrontEndPlugin<void> = {
  id: 'signalpilot-ai-internal:plugin',
  description: 'SignalPilot AI - Your AI Data Partner',
  autoStart: true,
  requires: [
    INotebookTracker,
    ICommandPalette,
    IThemeManager,
    IStateDB,
    IDocumentManager
  ],
  optional: [ISettingRegistry, IToolbarWidgetRegistry],
  activate: (
    app: JupyterFrontEnd,
    notebooks: INotebookTracker,
    palette: ICommandPalette,
    themeManager: IThemeManager,
    db: IStateDB,
    documentManager: IDocumentManager,
    settingRegistry: ISettingRegistry | null,
    toolbarRegistry: IToolbarWidgetRegistry | null
  ) => {
    console.log('JupyterLab extension signalpilot-ai-internal is activated!');
    console.log(window.location.href);

    // Initialize PostHog
    void posthogService.initialize();

    // Add a toolbar button to Notebook panels (only applies to .ipynb documents)
    class NotebookToolbarButtonExtension
      implements
        DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel>
    {
      createNew(
        panel: NotebookPanel,
        context: DocumentRegistry.IContext<INotebookModel>
      ): IDisposable {
        // Create deployment button widget
        const notebookPath = context.path;
        const isNotebookReady = !context.model.isDisposed;
        const button = new NotebookDeploymentButtonWidget(
          app,
          notebookPath,
          isNotebookReady
        );

        // Insert the button into the notebook toolbar
        panel.toolbar.insertItem(
          10,
          'signalpilot-ai-internal:deployment-button',
          button
        );

        // Return the button as disposable
        return button;
      }
    }

    // Register the extension for Notebook documents
    const buttonExtension = new NotebookToolbarButtonExtension();
    app.docRegistry.addWidgetExtension('Notebook', buttonExtension);

    // Handle authentication callback and replay parameter early in the initialization process
    const handleEarlyAuth = async () => {
      // Check for replay parameter FIRST to determine if we need the timer banner
      const urlParams = new URLSearchParams(window.location.search);
      const hasReplayParam = urlParams.has('replay');

      if (hasReplayParam) {
        console.log(
          '[Plugin] Replay parameter detected - setting demo mode early'
        );
        await AppStateService.setDemoMode(true);
      }

      // Variable to hold the current timer banner instance
      let timerBannerInstance: SessionTimerBannerWidget | null = null;

      // Function to add the timer banner to the DOM
      const addTimerBanner = () => {
        if (timerBannerInstance) {
          console.log('[Plugin] Timer banner already exists, skipping');
          return;
        }

        const isDemoMode = AppStateService.isDemoMode();
        console.log('[Plugin] Adding timer banner - isDemoMode:', isDemoMode);
        timerBannerInstance = new SessionTimerBannerWidget(isDemoMode);

        // Add banner to the DOM at the top, before the main shell
        const mainShell = document.querySelector(
          '.lm-Widget.jp-LabShell.jp-ThemedContainer'
        );
        if (mainShell && mainShell.parentNode) {
          mainShell.parentNode.insertBefore(
            timerBannerInstance.node,
            mainShell
          );
          console.log('[Plugin] Timer banner added to DOM before main shell');
        } else {
          console.warn(
            '[Plugin] Could not find main shell, trying document.body'
          );
          // Fallback: add to beginning of body
          document.body.insertBefore(
            timerBannerInstance.node,
            document.body.firstChild
          );
          console.log('[Plugin] Timer banner added to document.body');
        }
        // Add class to body to apply margin for the banner
        document.body.classList.add('sage-timer-banner-visible');
        console.log('[Plugin] Added sage-timer-banner-visible class to body');
      };

      // Function to remove the timer banner from the DOM
      const removeTimerBanner = () => {
        if (!timerBannerInstance) {
          console.log('[Plugin] No timer banner to remove');
          return;
        }

        console.log('[Plugin] Removing timer banner');
        timerBannerInstance.node.remove();
        timerBannerInstance.dispose();
        timerBannerInstance = null;
        // Remove class from body
        document.body.classList.remove('sage-timer-banner-visible');
        console.log(
          '[Plugin] Removed sage-timer-banner-visible class from body'
        );
      };

      // Function to check and update banner visibility
      const updateBannerVisibility = () => {
        const shouldShow = shouldShowSessionTimerBanner();
        const isShowing = timerBannerInstance !== null;

        console.log(
          '[Plugin] Banner visibility check - shouldShow:',
          shouldShow,
          'isShowing:',
          isShowing,
          'isDemoMode:',
          AppStateService.isDemoMode()
        );

        if (shouldShow && !isShowing) {
          addTimerBanner();
        } else if (!shouldShow && isShowing) {
          removeTimerBanner();
        }
      };

      // ===== Trial Banner Management =====
      // Variable to hold the current trial banner instance
      let trialBannerInstance: TrialBannerWidget | null = null;

      // Function to add the trial banner to the DOM
      const addTrialBanner = () => {
        if (trialBannerInstance) {
          console.log('[Plugin] Trial banner already exists, skipping');
          return;
        }

        console.log('[Plugin] Adding trial banner');
        trialBannerInstance = new TrialBannerWidget();

        // Add banner to the DOM at the top, before the main shell (or after session timer if it exists)
        const mainShell = document.querySelector(
          '.lm-Widget.jp-LabShell.jp-ThemedContainer'
        );
        if (mainShell && mainShell.parentNode) {
          // If session timer banner exists, insert trial banner after it
          const sessionTimerBanner = document.querySelector(
            '.sage-timer-banner-widget'
          );
          if (sessionTimerBanner && sessionTimerBanner.nextSibling) {
            mainShell.parentNode.insertBefore(
              trialBannerInstance.node,
              sessionTimerBanner.nextSibling
            );
            console.log(
              '[Plugin] Trial banner added to DOM after session timer banner'
            );
          } else {
            mainShell.parentNode.insertBefore(
              trialBannerInstance.node,
              mainShell
            );
            console.log('[Plugin] Trial banner added to DOM before main shell');
          }
        } else {
          console.warn(
            '[Plugin] Could not find main shell for trial banner, trying document.body'
          );
          // Fallback: add to beginning of body
          const sessionTimerBanner = document.querySelector(
            '.sage-timer-banner-widget'
          );
          if (sessionTimerBanner && sessionTimerBanner.nextSibling) {
            document.body.insertBefore(
              trialBannerInstance.node,
              sessionTimerBanner.nextSibling
            );
          } else {
            document.body.insertBefore(
              trialBannerInstance.node,
              document.body.firstChild
            );
          }
          console.log('[Plugin] Trial banner added to document.body');
        }
        // Add class to body to apply margin for the banner
        document.body.classList.add('sage-trial-banner-visible');
        console.log('[Plugin] Added sage-trial-banner-visible class to body');
      };

      // Function to remove the trial banner from the DOM
      const removeTrialBanner = () => {
        if (!trialBannerInstance) {
          console.log('[Plugin] No trial banner to remove');
          return;
        }

        console.log('[Plugin] Removing trial banner');
        trialBannerInstance.node.remove();
        trialBannerInstance.dispose();
        trialBannerInstance = null;
        // Remove class from body
        document.body.classList.remove('sage-trial-banner-visible');
        console.log(
          '[Plugin] Removed sage-trial-banner-visible class from body'
        );
      };

      // Function to check and update trial banner visibility
      const updateTrialBannerVisibility = async () => {
        try {
          const { JupyterAuthService } = await import(
            './Services/JupyterAuthService'
          );
          const isAuth = await JupyterAuthService.isAuthenticated();

          if (!isAuth) {
            // Not authenticated, hide trial banner
            if (trialBannerInstance) {
              removeTrialBanner();
            }
            return;
          }

          // User is authenticated, check if they should see trial banner
          const profile = await JupyterAuthService.getUserProfile();
          const hasSubscription = !!(
            profile?.subscription_expiry ||
            profile?.subscription_price_id ||
            profile?.subscribed_at
          );

          const shouldShow = profile?.is_free_trial && !hasSubscription;
          const isShowing = trialBannerInstance !== null;

          console.log(
            '[Plugin] Trial banner visibility check - shouldShow:',
            shouldShow,
            'isShowing:',
            isShowing,
            'is_free_trial:',
            profile?.is_free_trial,
            'hasSubscription:',
            hasSubscription
          );

          if (shouldShow && !isShowing) {
            addTrialBanner();
          } else if (!shouldShow && isShowing) {
            removeTrialBanner();
          }
        } catch (error) {
          console.error(
            '[Plugin] Error updating trial banner visibility:',
            error
          );
          // On error, hide the banner
          if (trialBannerInstance) {
            removeTrialBanner();
          }
        }
      };

      // Wait for both shell and SignalPilot initialization to be ready
      // This ensures backend cache is ready before checking banner visibility
      app.restored.then(() => {
        onSignalpilotInitialize(() => {
          console.log('[Plugin] Running banner initialization after SignalPilot ready');
          
          // Initial check and add if needed
          updateBannerVisibility();
          void updateTrialBannerVisibility();

          // Poll every 30 seconds to check if we should show/hide the banner
          setInterval(() => {
            updateBannerVisibility();
            void updateTrialBannerVisibility();
          }, 30000); // 30 seconds
          console.log(
            '[Plugin] Started polling for banner visibility every 30 seconds'
          );
        });
      });

      let replayId: string | null = null;
      let replayIdFromUrl = false; // Track if replayId came from URL

      try {
        // Import StateDBCachingService and JupyterAuthService dynamically to avoid circular dependencies
        const { StateDBCachingService } = await import(
          './utils/backendCaching'
        );
        const { JupyterAuthService } = await import(
          './Services/JupyterAuthService'
        );
        const {
          isTakeoverModeEnabled,
          getTakeoverReplayData,
          disableTakeoverMode
        } = await import('./utils/replayIdManager');

        // Initialize StateDB caching service early so authentication can use it
        StateDBCachingService.initialize();

        // Check takeover mode from localStorage and set in AppState
        if (isTakeoverModeEnabled()) {
          const takeoverData = getTakeoverReplayData();
          if (takeoverData && takeoverData.messages) {
            AppStateService.setTakeoverMode(true, takeoverData.messages);
            console.log(
              '[Plugin] Takeover mode detected in localStorage, set in AppState'
            );
          } else {
            // Invalid takeover data, clean it up
            disableTakeoverMode();
            console.warn('[Plugin] Invalid takeover data found, cleared');
          }
        }

        // Check for temp_token in URL and handle authentication callback
        const urlParams = new URLSearchParams(window.location.search);
        const tempToken = urlParams.get('temp_token');
        const isCallback = urlParams.get('auth_callback') === 'true';

        // Check if replayId is in URL BEFORE initializing
        const urlReplayId = urlParams.get('replay');
        if (urlReplayId) {
          replayIdFromUrl = true;
          console.log('[Replay] ReplayId found in URL:', urlReplayId);
        }

        // Initialize replayId management (checks localStorage and restores URL if needed)
        replayId = await initializeReplayIdManagement();
        if (replayId) {
          console.log(
            `[Replay] ReplayId initialized (from ${replayIdFromUrl ? 'URL' : 'localStorage'}):`,
            replayId
          );

          // Remove replay ID from URL immediately after reading it
          const url = new URL(window.location.href);
          if (url.searchParams.has('replay')) {
            url.searchParams.delete('replay');
            window.history.replaceState({}, '', url.toString());
            console.log('[Replay] Removed replay ID from URL');
          }
        }

        if (isCallback && tempToken) {
          console.log(
            'Processing temp_token during plugin initialization:',
            tempToken
          );

          // Handle the auth callback early
          const authSuccess = await JupyterAuthService.handleAuthCallback();
          if (authSuccess) {
            console.log(
              'Authentication successful during plugin initialization'
            );
            void posthogService.identifyUser();
            // User identification is now handled by PostHogService
            console.log('Authentication callback handled');
          } else {
            console.error('Authentication failed during plugin initialization');
          }
        }
      } catch (error) {
        console.error('Error processing early authentication:', error);
      }

      // Continue with normal activation regardless of auth result
      // Pass replayId and whether it came from URL to activateSignalPilot
      void activateSignalPilot(
        app,
        notebooks,
        palette,
        themeManager,
        db,
        documentManager,
        settingRegistry,
        toolbarRegistry,
        plugin,
        replayId,
        replayIdFromUrl
      );
    };

    // Start the async authentication handling
    void handleEarlyAuth();
  },
  deactivate: () => {
    console.log('JupyterLab extension signalpilot-ai-internal is deactivated!');

    // Cleanup snippet creation widget
    const snippetWidget = getGlobalSnippetCreationWidget();
    if (snippetWidget && !snippetWidget.isDisposed) {
      snippetWidget.dispose();
      setGlobalSnippetCreationWidget(undefined);
    }

    // Cleanup diff navigation widget
    const diffWidget = getGlobalDiffNavigationWidget();
    if (diffWidget && !diffWidget.isDisposed) {
      // Remove from DOM (could be attached to notebook or document.body)
      if (diffWidget.node.parentNode) {
        diffWidget.node.parentNode.removeChild(diffWidget.node);
      }
      diffWidget.dispose();
      setGlobalDiffNavigationWidget(undefined);
    }

    // Cleanup kernel execution listener
    const kernelExecutionListener = KernelExecutionListener.getInstance();
    kernelExecutionListener.dispose();

    // Cleanup theme detection
    NotebookDiffTools.cleanupThemeDetection();
  }
};
