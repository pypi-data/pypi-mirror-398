/**
 * SignalPilot Initialization Module
 *
 * Handles core service initialization including:
 * - Caching services (settings and StateDB)
 * - Database state
 * - JWT authentication
 * - Snippets loading
 * - Workspace context fetching
 */

import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { IStateDB } from '@jupyterlab/statedb';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { IThemeManager } from '@jupyterlab/apputils';
import { INotebookTracker } from '@jupyterlab/notebook';
import { JupyterFrontEnd } from '@jupyterlab/application';
import { ListModel } from '@jupyterlab/extensionmanager';

import { CachingService, SETTING_KEYS } from '../utils/caching';
import { StateDBCachingService } from '../utils/backendCaching';
import { AppStateService } from '../AppState';
import { ConfigService } from '../Config/ConfigService';
import { ToolService } from '../Services/ToolService';
import { NotebookContextManager } from '../Notebook/NotebookContextManager';
import { ActionHistory } from '../Chat/ActionHistory';
import { NotebookTools } from '../Notebook/NotebookTools';
import { CellTrackingService } from '../CellTrackingService';
import { TrackingIDUtility } from '../TrackingIDUtility';
import { ContextCellHighlighter } from '../Chat/ChatContextMenu/ContextCellHighlighter';
import { TabCompletionService } from '../Services/TabCompletionService';
import { CompletionManager } from '../Services/CompletionManager';
import { DatabaseMetadataCache } from '../Services/DatabaseMetadataCache';
import { ContextCacheService } from '../Chat/ChatContextMenu/ContextCacheService';
import { KernelExecutionListener } from '../Chat/ChatContextMenu/KernelExecutionListener';
import { CloudUploadService } from '../Services/CloudUploadService';
import { JWTAuthModalService } from '../Services/JWTAuthModalService';
import { PlanStateDisplay } from '../Components/PlanStateDisplay';
import { LLMStateDisplay } from '../Components/LLMStateDisplay';
import { WaitingUserReplyBoxManager } from '../Notebook/WaitingUserReplyBoxManager';
import { NotebookDiffManager } from '../Notebook/NotebookDiffManager';
import { NotebookDiffTools } from '../Notebook/NotebookDiffTools';
import { KernelUtils } from '../utils/kernelUtils';

export interface InitializationContext {
  app: JupyterFrontEnd;
  notebooks: INotebookTracker;
  themeManager: IThemeManager;
  db: IStateDB;
  documentManager: IDocumentManager;
  settingRegistry: ISettingRegistry | null;
  replayId: string | null;
}

export interface CoreServices {
  toolService: ToolService;
  notebookContextManager: NotebookContextManager;
  actionHistory: ActionHistory;
  notebookTools: NotebookTools;
  planStateDisplay: PlanStateDisplay;
  llmStateDisplay: LLMStateDisplay;
  waitingUserReplyBoxManager: WaitingUserReplyBoxManager;
  cellTrackingService: CellTrackingService;
  trackingIDUtility: TrackingIDUtility;
  contextCellHighlighter: ContextCellHighlighter;
  diffManager: NotebookDiffManager;
}

/**
 * Initialize all caching services
 */
export async function initializeCaching(
  settingRegistry: ISettingRegistry | null
): Promise<void> {
  // Initialize the caching service with settings registry
  CachingService.initialize(settingRegistry);

  // Initialize the state database caching service for chat histories
  StateDBCachingService.initialize();

  // Move old chat histories to StateDB
  const moveToChatHistory = async () => {
    const oldHistories = await CachingService.getSetting(
      SETTING_KEYS.CHAT_HISTORIES,
      {}
    );
    if (oldHistories && Object.keys(oldHistories).length > 0) {
      console.log('MOVING ALL SETTINGS TO THE STATE DB');
      await StateDBCachingService.setValue(
        SETTING_KEYS.CHAT_HISTORIES,
        oldHistories
      );
      console.log('SUCCESSFULLY MOVED ALL SETTINGS TO THE STATE DB');
      await CachingService.setSetting(SETTING_KEYS.CHAT_HISTORIES, {});
    }
  };

  void moveToChatHistory();
}

/**
 * Initialize demo mode and database state service
 */
export async function initializeDemoMode(
  replayId: string | null
): Promise<void> {
  // Load demo mode from cache on startup
  await AppStateService.loadDemoMode();

  // If replay is present, set demo mode to true
  if (replayId) {
    console.log('[Replay] Setting demo mode to true');
    await AppStateService.setDemoMode(true);
  }

  // Initialize the database state service with StateDB (async, non-blocking)
  console.log('[Plugin] Initializing database state service...');
  void import('../DatabaseStateService').then(({ DatabaseStateService }) => {
    DatabaseStateService.initializeWithStateDB().catch(error => {
      console.warn(
        '[Plugin] Database state service initialization failed:',
        error
      );
    });
  });
}

/**
 * Initialize JWT authentication
 */
export async function initializeAuthentication(): Promise<void> {
  console.log('[Plugin] Initializing JWT authentication on startup...');
  try {
    const jwtInitialized = await JWTAuthModalService.initializeJWTOnStartup();
    if (jwtInitialized) {
      console.log(
        '[Plugin] JWT authentication initialized successfully on startup'
      );

      // Load user profile if authenticated
      try {
        const { JupyterAuthService } = await import(
          '../Services/JupyterAuthService'
        );
        const isAuthenticated = await JupyterAuthService.isAuthenticated();

        if (isAuthenticated) {
          const userProfile = await JupyterAuthService.getUserProfile();
          AppStateService.setUserProfile(userProfile);
          console.log('[Plugin] User profile loaded and stored in AppState');
        }
      } catch (profileError) {
        console.warn('[Plugin] Failed to load user profile:', profileError);
      }
    } else {
      console.log('[Plugin] No JWT token found during startup initialization');
    }
  } catch (error) {
    console.error('[Plugin] Failed to initialize JWT on startup:', error);
  }
}

/**
 * Load snippets and inserted snippets from StateDB
 */
export async function loadSnippets(): Promise<void> {
  // Load snippets from StateDB (async, non-blocking)
  AppStateService.loadSnippets().catch(error => {
    console.warn('[Plugin] Failed to load snippets from StateDB:', error);
  });

  // Load inserted snippets from StateDB (async, non-blocking)
  AppStateService.loadInsertedSnippets().catch(error => {
    console.warn(
      '[Plugin] Failed to load inserted snippets from StateDB:',
      error
    );
  });
}

/**
 * Initialize AppState with registry and extensions
 */
export function initializeAppState(
  app: JupyterFrontEnd,
  settingRegistry: ISettingRegistry | null
): void {
  // Store settings registry in AppState
  AppStateService.setSettingsRegistry(settingRegistry);

  const serviceManager = app.serviceManager;

  // Store service manager in AppState
  AppStateService.setServiceManager(serviceManager);

  const extensions = new ListModel(serviceManager as any);

  // Store extensions in AppState for UpdateBanner to use
  AppStateService.setExtensions(extensions);
}

/**
 * Set dark theme if not already set
 */
export async function initializeTheme(
  themeManager: IThemeManager
): Promise<void> {
  const checkAndSetTheme = async () => {
    const alreadySet = await CachingService.getBooleanSetting(
      SETTING_KEYS.DARK_THEME_APPLIED,
      false
    );
    if (!alreadySet) {
      console.log('Setting theme to JupyterLab Dark (first time)');
      void themeManager.setTheme('JupyterLab Dark');
      await CachingService.setBooleanSetting(
        SETTING_KEYS.DARK_THEME_APPLIED,
        true
      );
    }
  };
  void checkAndSetTheme();
}

/**
 * Load and configure settings from registry
 */
export function loadSettings(
  settingRegistry: ISettingRegistry | null,
  pluginId: string
): void {
  if (settingRegistry) {
    settingRegistry
      .load(pluginId)
      .then(settings => {
        console.log('Loaded settings for signalpilot-ai-internal');
        const defaultService = settings.get('defaultService')
          .composite as string;
        // Store the default service in ConfigService
        if (defaultService) {
          ConfigService.setActiveModelType(defaultService);
        }

        // Watch for setting changes
        settings.changed.connect(() => {
          const newDefaultService = settings.get('defaultService')
            .composite as string;
          ConfigService.setActiveModelType(newDefaultService);
          console.log(`Default service changed to ${newDefaultService}`);
        });
      })
      .catch(error => {
        console.error('Failed to load settings for signalpilot-ai-internal', error);
      });
  }
}

/**
 * Fetch and cache workspace context
 */
export async function fetchWorkspaceContext(): Promise<void> {
  try {
    const { requestAPI } = await import('../handler');
    const workspaceData = await requestAPI<any>('read-all-files');
    AppStateService.setWorkspaceContext(workspaceData);
    console.log('[Plugin] Workspace context cached at startup');
  } catch (error) {
    console.warn('[Plugin] Failed to fetch workspace context:', error);
  }
}

/**
 * Initialize all core services and components
 */
export function initializeCoreServices(
  app: JupyterFrontEnd,
  notebooks: INotebookTracker,
  documentManager: IDocumentManager
): CoreServices {
  const contentManager = app.serviceManager.contents;

  // Create shared instances
  const planStateDisplay = new PlanStateDisplay();
  const llmStateDisplay = new LLMStateDisplay();
  const waitingUserReplyBoxManager = new WaitingUserReplyBoxManager();
  const toolService = new ToolService();
  const notebookTools = new NotebookTools(
    notebooks,
    waitingUserReplyBoxManager
  );
  const notebookContextManager = new NotebookContextManager(toolService);
  const actionHistory = new ActionHistory();

  // Configure tool service
  toolService.setNotebookTracker(notebooks, waitingUserReplyBoxManager);
  toolService.setContentManager(contentManager);
  toolService.setContextManager(notebookContextManager);

  // Initialize the AppState with core services
  AppStateService.initializeCoreServices(
    toolService,
    notebooks,
    notebookTools,
    notebookContextManager,
    contentManager,
    documentManager,
    null
  );

  // Initialize managers in AppState
  AppStateService.initializeManagers(
    planStateDisplay,
    llmStateDisplay,
    waitingUserReplyBoxManager
  );

  // Initialize additional services
  const cellTrackingService = new CellTrackingService(notebookTools, notebooks);
  const trackingIDUtility = new TrackingIDUtility(notebooks);
  const contextCellHighlighter = new ContextCellHighlighter(
    notebooks,
    notebookContextManager,
    notebookTools
  );

  AppStateService.initializeAdditionalServices(
    actionHistory,
    cellTrackingService,
    trackingIDUtility,
    contextCellHighlighter
  );

  // Initialize NotebookDiffManager
  const diffManager = new NotebookDiffManager(notebookTools, actionHistory);
  AppStateService.setState({ notebookDiffManager: diffManager });

  // Initialize diff2html theme detection
  NotebookDiffTools.initializeThemeDetection();

  return {
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
  };
}

/**
 * Initialize async services (tab completion, cloud upload, database cache, etc.)
 */
export async function initializeAsyncServices(
  notebooks: INotebookTracker
): Promise<void> {
  // Initialize tab completion service (async, non-blocking)
  const tabCompletionService = TabCompletionService.getInstance();
  tabCompletionService.initialize().catch(error => {
    console.warn(
      '[Plugin] Tab completion service initialization failed:',
      error
    );
  });

  // Initialize cloud upload services (async, non-blocking)
  const cloudUploadService = CloudUploadService.getInstance();
  Promise.all([cloudUploadService.initialize()]).catch(error => {
    console.warn(
      '[Plugin] Cloud upload services initialization failed:',
      error
    );
  });

  // Initialize completion manager
  const completionManager = CompletionManager.getInstance();
  completionManager.initialize(notebooks);

  // Initialize database metadata cache (async, non-blocking)
  const databaseCache = DatabaseMetadataCache.getInstance();
  databaseCache.initializeOnStartup().catch(error => {
    console.warn('[Plugin] Database cache initialization failed:', error);
  });

  // Initialize context cache service and kernel execution listener
  const contextCacheService = ContextCacheService.getInstance();
  const kernelExecutionListener = KernelExecutionListener.getInstance();

  // Set up delayed initialization to ensure all core services are ready
  setTimeout(async () => {
    try {
      await contextCacheService.initialize();
      console.log('[Plugin] Context cache service initialized');

      // Initialize kernel execution listener after context cache service
      await kernelExecutionListener.initialize(notebooks);
      console.log('[Plugin] Kernel execution listener initialized');

      // Start initial context loading (non-blocking)
      contextCacheService.loadAllContexts().catch(error => {
        console.warn('[Plugin] Initial context loading failed:', error);
      });

      // Subscribe to notebook changes for context refreshing
      contextCacheService.subscribeToNotebookChanges();
    } catch (error) {
      console.warn(
        '[Plugin] Context cache service initialization failed:',
        error
      );
    }
  }, 1000); // Wait 1 second for core services to be ready
}

/**
 * Set up debug utilities on window object
 */
export function setupDebugUtilities(notebooks: INotebookTracker): void {
  const databaseCache = DatabaseMetadataCache.getInstance();
  const contextCacheService = ContextCacheService.getInstance();
  const kernelExecutionListener = KernelExecutionListener.getInstance();

  if (!(window as any).debugDBURL) {
    (window as any).debugDBURL = {
      check: () => KernelUtils.checkDbUrlInKernel(),
      debug: () => KernelUtils.debugAppStateDatabaseUrl(),
      set: (url?: string) => KernelUtils.setDbUrlInKernel(url),
      retry: () => KernelUtils.setDbUrlInKernelWithRetry(),
      setAllDatabases: () => KernelUtils.setDatabaseEnvironmentsInKernel(),
      retryAllDatabases: () =>
        KernelUtils.setDatabaseEnvironmentsInKernelWithRetry()
    };
  }

  if (!(window as any).debugDBCache) {
    (window as any).debugDBCache = {
      getStatus: () => databaseCache.getCacheStatus(),
      refresh: () => databaseCache.refreshMetadata(),
      clear: () => databaseCache.clearCache(),
      onKernelReady: () => databaseCache.onKernelReady(),
      onSettingsChanged: () => databaseCache.onSettingsChanged()
    };
  }

  if (!(window as any).debugContextCache) {
    (window as any).debugContextCache = {
      getContexts: () => contextCacheService.getContexts(),
      refresh: () => contextCacheService.forceRefresh()
    };
  }

  if (!(window as any).debugKernelListener) {
    (window as any).debugKernelListener = {
      getDebugInfo: () => kernelExecutionListener.getDebugInfo(),
      triggerRefresh: () => kernelExecutionListener.triggerVariableRefresh(),
      dispose: () => kernelExecutionListener.dispose(),
      reinitialize: () => kernelExecutionListener.initialize(notebooks)
    };
  }

  if (!(window as any).debugLoginSuccess) {
    (window as any).debugLoginSuccess = {
      show: async () => {
        try {
          const { LoginSuccessModalService } = await import(
            '../Services/LoginSuccessModalService'
          );
          LoginSuccessModalService.debugShow();
          console.log('✅ Login success modal triggered from debug');
        } catch (error) {
          console.error('❌ Failed to show login success modal:', error);
        }
      },
      getDebugInfo: async () => {
        try {
          const { LoginSuccessModalService } = await import(
            '../Services/LoginSuccessModalService'
          );
          const instance = LoginSuccessModalService.getInstance();
          return instance.getDebugInfo();
        } catch (error) {
          console.error('❌ Failed to get debug info:', error);
          return null;
        }
      }
    };
  }

  if (!(window as any).debugJWTAuth) {
    (window as any).debugJWTAuth = {
      show: () => {
        const jwtModalService = JWTAuthModalService.getInstance();
        jwtModalService.show();
        console.log('✅ JWT auth modal shown from debug');
      },
      hide: () => {
        const jwtModalService = JWTAuthModalService.getInstance();
        jwtModalService.hide();
        console.log('✅ JWT auth modal hidden from debug');
      },
      forceShow: () => {
        const jwtModalService = JWTAuthModalService.getInstance();
        jwtModalService.forceShow();
        console.log('✅ JWT auth modal force shown from debug');
      },
      checkAndHide: async () => {
        const jwtModalService = JWTAuthModalService.getInstance();
        await jwtModalService.checkAndHideIfAuthenticated();
        console.log('✅ JWT auth modal check and hide completed');
      },
      getDebugInfo: async () => {
        const jwtModalService = JWTAuthModalService.getInstance();
        return await jwtModalService.getDebugInfo();
      }
    };
  }
}
