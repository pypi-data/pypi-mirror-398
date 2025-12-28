/**
 * SignalPilot Activation Entry Point
 *
 * Main activation function that coordinates all SignalPilot initialization
 */

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { INotebookTracker } from '@jupyterlab/notebook';
import {
  ICommandPalette,
  IThemeManager,
  IToolbarWidgetRegistry
} from '@jupyterlab/apputils';
import { IStateDB } from '@jupyterlab/statedb';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { ISettingRegistry } from '@jupyterlab/settingregistry';

import { AppStateService } from '../AppState';
import {
  handleNotebookRestoration,
  handleReplayInitialization,
  handleTakeoverModeReentry
} from './replayHandlers';
import {
  handleNotebookSwitch,
  setupFileChangeDetection,
  setupNotebookTracking
} from './notebookManagement';
import {
  fetchWorkspaceContext,
  initializeAppState,
  initializeAsyncServices,
  initializeAuthentication,
  initializeCaching,
  initializeCoreServices,
  initializeDemoMode,
  initializeTheme,
  loadSettings,
  loadSnippets,
  setupDebugUtilities
} from './initialization';
import {
  initializeAllWidgets,
  setupDiffNavigationWidgetTracking
} from './widgetInitialization';
import {
  initializeJWTAuthenticationModal,
  registerAllCommands,
  setupActiveCellTracking
} from './commandsAndAuth';

export async function activateSignalPilot(
  app: JupyterFrontEnd,
  notebooks: INotebookTracker,
  palette: ICommandPalette,
  themeManager: IThemeManager,
  db: IStateDB,
  documentManager: IDocumentManager,
  settingRegistry: ISettingRegistry | null,
  toolbarRegistry: IToolbarWidgetRegistry | null,
  plugin: JupyterFrontEndPlugin<void>,
  replayId: string | null = null,
  replayIdFromUrl: boolean = false
) {
  console.log('JupyterLab extension signalpilot-ai-internal is activated!');

  // Log replay parameter if present
  if (replayId) {
    console.log(
      `[Replay] Replay ID passed to activateSignalPilot (from ${replayIdFromUrl ? 'URL' : 'localStorage'}):`,
      replayId
    );

    // Ensure replayId is stored in localStorage
    const { storeReplayId } = await import('../utils/replayIdManager');
    storeReplayId(replayId);
  }

  // ===== INITIALIZATION PHASE =====

  // Initialize caching services
  await initializeCaching(settingRegistry);

  // Initialize demo mode and database state
  await initializeDemoMode(replayId);

  // Initialize JWT authentication
  await initializeAuthentication();

  // Load snippets from StateDB
  await loadSnippets();

  // Initialize AppState with registry and extensions
  initializeAppState(app, settingRegistry);

  const contentManager = app.serviceManager.contents;

  // Set dark theme if not already set
  await initializeTheme(themeManager);

  // Load settings if available
  loadSettings(settingRegistry, plugin.id);

  // ===== CORE SERVICES INITIALIZATION =====

  const coreServices = initializeCoreServices(app, notebooks, documentManager);

  const {
    toolService,
    notebookContextManager,
    actionHistory,
    notebookTools,
    planStateDisplay,
    llmStateDisplay,
    waitingUserReplyBoxManager,
    cellTrackingService,
    trackingIDUtility,
    contextCellHighlighter,
    diffManager
  } = coreServices;

  // Initialize async services (tab completion, cloud upload, database cache, etc.)
  await initializeAsyncServices(notebooks);

  // Fetch and cache workspace context
  void fetchWorkspaceContext();

  // Set up debug utilities
  setupDebugUtilities(notebooks);

  // ===== WIDGET INITIALIZATION =====

  const widgets = await initializeAllWidgets(
    app,
    notebooks,
    toolService,
    notebookContextManager,
    diffManager,
    actionHistory,
    contextCellHighlighter,
    contentManager
  );

  const {
    tracker,
    settingsContainer,
    snippetCreationWidget,
    diffNavigationWidget,
    databaseManagerWidget,
    fileExplorerWidget
  } = widgets;

  // Set up DiffNavigationWidget tracking
  setupDiffNavigationWidgetTracking(notebooks);

  // ===== NOTEBOOK MANAGEMENT =====

  // Set up file change detection early in the activation process
  setupFileChangeDetection(
    app,
    notebooks,
    documentManager,
    contentManager,
    diffManager,
    cellTrackingService,
    trackingIDUtility,
    contextCellHighlighter,
    notebookTools
  );

  // Initialize the tracking ID utility
  trackingIDUtility.fixTrackingIDs();

  // Set up notebook tracking to switch to the active notebook
  setupNotebookTracking(
    notebooks,
    contentManager,
    diffManager,
    cellTrackingService,
    trackingIDUtility,
    contextCellHighlighter,
    notebookTools,
    app
  );

  // Handle current notebook if one is already open
  if (notebooks.currentWidget) {
    await handleNotebookSwitch(
      notebooks.currentWidget,
      contentManager,
      diffManager,
      cellTrackingService,
      trackingIDUtility,
      contextCellHighlighter,
      notebookTools
    );

    // Auto-render the welcome CTA on notebook switch
    setTimeout(() => {
      app.commands.execute('sage-ai:add-cta-div').catch(error => {
        console.warn(
          '[Plugin] Failed to auto-render welcome CTA on notebook switch:',
          error
        );
      });
    }, 300);
  }

  // ===== COMMANDS AND AUTHENTICATION =====

  // Register all commands
  registerAllCommands(
    app,
    palette,
    documentManager,
    tracker,
    notebooks,
    notebookContextManager
  );

  // Set up active cell tracking
  setupActiveCellTracking(notebooks, notebookContextManager);

  // Initialize JWT authentication modal
  await initializeJWTAuthenticationModal(app, settingsContainer);

  // ===== SIGNAL INITIALIZATION COMPLETE =====

  // Signal that SignalPilot is fully initialized
  // This triggers callbacks for components that need to run after backend cache is ready
  console.log(
    '[SignalPilot] All components loaded, signaling initialization complete'
  );
  const { signalSignalpilotInitialized } = await import('../plugin');
  signalSignalpilotInitialized();

  // ===== REPLAY AND SPECIAL MODES (After Initialization) =====

  // Handle replay if replay ID was passed AND it came from the URL (not from localStorage cache)
  // Run this AFTER signaling initialization to ensure backend cache is ready
  if (replayId && replayIdFromUrl) {
    console.log(
      '[Replay] Starting replay initialization for ID (from URL):',
      replayId
    );
    void handleReplayInitialization(replayId, app);
  } else if (replayId && !replayIdFromUrl) {
    console.log(
      '[Replay] ReplayId found in cache but not triggering replay (already played)'
    );
  }

  // Check if there's a stored notebook path to restore (from "Login to Chat" flow)
  const { getStoredLastNotebookPath } = await import(
    '../utils/replayIdManager'
  );
  const storedNotebookPath = getStoredLastNotebookPath();

  if (storedNotebookPath) {
    console.log(
      '[Notebook Restore] Found stored notebook path, restoring:',
      storedNotebookPath
    );
    void handleNotebookRestoration(storedNotebookPath);
  }
  // Handle takeover mode: if user clicked "Takeover" and is now signed in
  // Check from AppState which is set during plugin initialization
  else if (AppStateService.isTakeoverMode()) {
    console.log('[Takeover] Takeover mode detected, handling re-entry...');
    void handleTakeoverModeReentry();
  }

  return;
}
