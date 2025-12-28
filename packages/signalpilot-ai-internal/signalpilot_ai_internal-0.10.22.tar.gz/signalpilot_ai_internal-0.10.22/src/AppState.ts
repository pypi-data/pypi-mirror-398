import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';
import { Contents } from '@jupyterlab/services';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { ToolService } from './Services/ToolService';
import { NotebookTools } from './Notebook/NotebookTools';
import { NotebookContextManager } from './Notebook/NotebookContextManager';
import { PlanStateDisplay } from './Components/PlanStateDisplay';
import { WaitingUserReplyBoxManager } from './Notebook/WaitingUserReplyBoxManager';
import { ActionHistory } from './Chat/ActionHistory';
import { NotebookDiffManager } from './Notebook/NotebookDiffManager';
import { CellTrackingService } from './CellTrackingService';
import { TrackingIDUtility } from './TrackingIDUtility';
import { ContextCellHighlighter } from './Chat/ChatContextMenu/ContextCellHighlighter';
import { NotebookChatContainer } from './Notebook/NotebookChatContainer';
import { ListModel } from '@jupyterlab/extensionmanager';
import { IChatService } from './Services/IChatService';
import { IConfig } from './Config/ConfigService';
import { ServiceManager } from '@jupyterlab/services';
import { StateDBCachingService, STATE_DB_KEYS } from './utils/backendCaching';
import { IMentionContext } from './Chat/ChatContextMenu/ChatContextLoaders';
import { DiffNavigationWidget } from './Components/DiffNavigationWidget';
import { v4 as uuidv4 } from 'uuid';
import { LLMStateDisplay } from './Components/LLMStateDisplay';
import { IDocumentManager } from '@jupyterlab/docmanager';

/**
 * Interface for a Snippet stored in IAppState
 */
export interface ISnippet {
  id: string;
  title: string;
  description: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

interface IAppState {
  // Core services
  toolService: ToolService | null;
  notebookTracker: INotebookTracker | null;
  notebookTools: NotebookTools | null;
  notebookContextManager: NotebookContextManager | null;
  contentManager: Contents.IManager | null;
  documentManager: IDocumentManager | null;
  settingsRegistry: ISettingRegistry | null;
  chatService: IChatService | null;
  config: IConfig | null;
  serviceManager: ServiceManager.IManager | null;

  // Extension manager
  extensions: ListModel | null;

  // Managers
  planStateDisplay: PlanStateDisplay | null;
  llmStateDisplay: LLMStateDisplay | null;
  waitingUserReplyBoxManager: WaitingUserReplyBoxManager | null;
  notebookDiffManager: NotebookDiffManager | null;

  // Additional services
  actionHistory: ActionHistory | null;
  cellTrackingService: CellTrackingService | null;
  trackingIDUtility: TrackingIDUtility | null;
  contextCellHighlighter: ContextCellHighlighter | null;

  // UI Containers
  chatContainer: NotebookChatContainer | null;
  diffNavigationWidget: DiffNavigationWidget | null;
  fileExplorerWidget: any | null; // FileExplorerWidget
  databaseManagerWidget: any | null; // DatabaseManagerWidget

  // Application state
  currentNotebookId: string | null;
  currentNotebook: NotebookPanel | null;
  isInitialized: boolean;
  isLauncherActive: boolean;
  currentWorkingDirectory: string | null;
  isDemoMode: boolean; // True when replay parameter is present
  isTakeoverMode: boolean; // True when takeover mode is active
  takeoverPrompt: string | null; // First message to send in takeover mode
  userProfile: any | null; // User profile from authentication

  // Context cache for async loading
  contextCache: Map<string, IMentionContext[]>;
  contextCacheTimestamp: number;
  isContextLoading: boolean;

  // Workspace context cache
  workspaceContext: any | null;

  // File scanning
  scannedDirectories: any[] | null;
  initialFileScanComplete: boolean;

  // Snippets
  snippets: ISnippet[];
  insertedSnippets: string[]; // Array of snippet IDs that have been inserted

  // Tool call limit
  maxToolCallLimit: number | null;

  // Auto-run mode
  autoRun: boolean;

  // Settings
  settings: {
    theme: string;
    tokenMode: boolean;
    tabAutocompleteEnabled: boolean;
    claudeApiKey: string;
    claudeModelId: string;
    claudeModelUrl: string;
    databaseUrl: string;
  };
}

const initialState: IAppState = {
  // Core services
  toolService: null,
  notebookTracker: null,
  notebookTools: null,
  notebookContextManager: null,
  contentManager: null,
  documentManager: null,
  settingsRegistry: null,
  chatService: null,
  config: null,
  serviceManager: null,

  // Extension manager
  extensions: null,

  // Managers
  planStateDisplay: null,
  llmStateDisplay: null,
  waitingUserReplyBoxManager: null,
  notebookDiffManager: null,

  // Additional services
  actionHistory: null,
  cellTrackingService: null,
  trackingIDUtility: null,
  contextCellHighlighter: null,

  // UI Containers
  chatContainer: null,
  diffNavigationWidget: null,
  fileExplorerWidget: null,
  databaseManagerWidget: null,

  // Application state
  currentNotebookId: null,
  currentNotebook: null,
  isInitialized: false,
  isLauncherActive: false,
  currentWorkingDirectory: null,
  isDemoMode: false,
  isTakeoverMode: false,
  takeoverPrompt: null,
  userProfile: null,

  // Context cache for async loading
  contextCache: new Map(),
  contextCacheTimestamp: 0,
  isContextLoading: false,

  // Workspace context cache
  workspaceContext: null,

  // File scanning
  scannedDirectories: null,
  initialFileScanComplete: false,

  // Snippets
  snippets: [],
  insertedSnippets: [],

  // Tool call limit
  maxToolCallLimit: null,

  // Auto-run mode
  autoRun: false,

  // Settings
  settings: {
    theme: 'light',
    tokenMode: false,
    tabAutocompleteEnabled: false,
    claudeApiKey: '',
    claudeModelId: 'claude-3-7-sonnet-20250219',
    claudeModelUrl: 'https://sage.alpinex.ai:8760',
    databaseUrl: ''
  }
};

const state$ = new BehaviorSubject<IAppState>(initialState);

// Events for notebook changes
const notebookChanged$ = new Subject<{
  oldNotebookId: string | null;
  newNotebookId: string | null;
  fromLauncher?: boolean;
}>();
const notebookRenamed$ = new Subject<{
  oldNotebookId: string;
  newNotebookId: string;
}>();

export const AppStateService = {
  /**
   * Get the current application state
   */
  getState: () => state$.getValue(),

  /**
   * Update the application state with partial values
   */
  setState: (partial: Partial<IAppState>) =>
    state$.next({ ...state$.getValue(), ...partial }),

  /**
   * Subscribe to state changes
   */
  changes: state$.asObservable(),

  /**
   * Initialize core services
   */
  initializeCoreServices: (
    toolService: ToolService,
    notebookTracker: INotebookTracker,
    notebookTools: NotebookTools,
    notebookContextManager: NotebookContextManager,
    contentManager: Contents.IManager,
    documentManager: IDocumentManager,
    settingsRegistry?: ISettingRegistry | null
  ) => {
    AppStateService.setState({
      toolService,
      notebookTracker,
      notebookTools,
      notebookContextManager,
      contentManager,
      documentManager,
      settingsRegistry: settingsRegistry || null
    });
  },

  /**
   * Initialize managers
   */
  initializeManagers: (
    planStateDisplay: PlanStateDisplay,
    llmStateDisplay: LLMStateDisplay,
    waitingUserReplyBoxManager: WaitingUserReplyBoxManager,
    notebookDiffManager?: NotebookDiffManager
  ) => {
    AppStateService.setState({
      planStateDisplay,
      llmStateDisplay,
      waitingUserReplyBoxManager,
      notebookDiffManager
    });
  },

  /**
   * Initialize additional services
   */
  initializeAdditionalServices: (
    actionHistory: ActionHistory,
    cellTrackingService: CellTrackingService,
    trackingIDUtility: TrackingIDUtility,
    contextCellHighlighter: ContextCellHighlighter
  ) => {
    AppStateService.setState({
      actionHistory,
      cellTrackingService,
      trackingIDUtility,
      contextCellHighlighter
    });
  },

  /**
   * Mark the application as initialized
   */
  markAsInitialized: () => {
    AppStateService.setState({ isInitialized: true });
  },

  /**
   * Get the current notebook ID
   */
  getCurrentNotebookId: (): string | null => {
    return AppStateService.getState().currentNotebookId;
  },

  /**
   * Get the current notebook
   */
  getCurrentNotebook: (): NotebookPanel | null => {
    return AppStateService.getState().currentNotebook;
  },

  /**
   * Set the current notebook and its ID
   */
  setCurrentNotebook: (
    notebook: NotebookPanel | null,
    notebookId?: string | null
  ) => {
    const currentState = AppStateService.getState();
    const oldNotebookId = currentState.currentNotebookId;
    const newNotebookId = notebookId || (notebook ? 'unknown' : null);

    if (oldNotebookId !== newNotebookId) {
      AppStateService.setState({
        currentNotebook: notebook,
        currentNotebookId: newNotebookId
      });
      // Emit notebook change event
      notebookChanged$.next({ oldNotebookId, newNotebookId });
    } else {
      // Just update the notebook reference if ID is the same
      AppStateService.setState({ currentNotebook: notebook });
    }
  },

  /**
   * Update the current notebook ID
   */
  setCurrentNotebookId: (notebookId: string | null) => {
    const currentState = AppStateService.getState();
    const oldNotebookId = currentState.currentNotebookId;

    if (oldNotebookId !== notebookId) {
      AppStateService.setState({
        currentNotebookId: notebookId,
        currentNotebook: null // Clear notebook reference when only ID is set
      });
      // Emit notebook change event
      notebookChanged$.next({ oldNotebookId, newNotebookId: notebookId });
    }
  },

  /**
   * Update notebook ID when a notebook is renamed
   */
  updateNotebookId: (oldNotebookId: string, newNotebookId: string) => {
    const currentState = AppStateService.getState();

    // Update current notebook ID if it matches the old one
    if (currentState.currentNotebookId === oldNotebookId) {
      AppStateService.setState({
        currentNotebookId: newNotebookId,
        currentNotebook: null // Clear notebook reference during rename
      });
    }

    // Emit notebook rename event
    notebookRenamed$.next({ oldNotebookId, newNotebookId });
  },

  /**
   * Subscribe to notebook change events
   */
  onNotebookChanged: (): Observable<{
    oldNotebookId: string | null;
    newNotebookId: string | null;
    fromLauncher?: boolean;
  }> => {
    return notebookChanged$.asObservable();
  },

  /**
   * Trigger a notebook change event (used for special cases like switching from launcher)
   */
  triggerNotebookChange: (
    oldNotebookId: string | null,
    newNotebookId: string | null,
    fromLauncher: boolean = false
  ) => {
    notebookChanged$.next({ oldNotebookId, newNotebookId, fromLauncher });
  },

  /**
   * Subscribe to notebook rename events
   */
  onNotebookRenamed: (): Observable<{
    oldNotebookId: string;
    newNotebookId: string;
  }> => {
    return notebookRenamed$.asObservable();
  },

  /**
   * Set launcher active state
   */
  setLauncherActive: (isActive: boolean) => {
    const currentState = AppStateService.getState();
    if (currentState.isLauncherActive !== isActive) {
      AppStateService.setState({ isLauncherActive: isActive });
      console.log(`[IAppState] Launcher active state changed: ${isActive}`);
    }
  },

  /**
   * Get launcher active state
   */
  isLauncherActive: (): boolean => {
    return AppStateService.getState().isLauncherActive;
  },

  /**
   * Update settings
   */
  updateSettings: (settings: Partial<IAppState['settings']>) => {
    const currentState = AppStateService.getState();
    AppStateService.setState({
      settings: { ...currentState.settings, ...settings }
    });
  },

  /**
   * Update Claude settings specifically
   */
  updateClaudeSettings: (settings: {
    claudeApiKey?: string;
    claudeModelId?: string;
    claudeModelUrl?: string;
    databaseUrl?: string;
    tabAutocompleteEnabled?: boolean;
  }) => {
    const currentState = AppStateService.getState();
    AppStateService.setState({
      settings: { ...currentState.settings, ...settings }
    });
  },

  /**
   * Get Claude settings
   */
  getClaudeSettings: (): {
    claudeApiKey: string;
    claudeModelId: string;
    claudeModelUrl: string;
    databaseUrl: string;
    tabAutocompleteEnabled: boolean;
  } => {
    const { settings } = AppStateService.getState();
    return {
      claudeApiKey: settings.claudeApiKey,
      claudeModelId: settings.claudeModelId,
      claudeModelUrl: settings.claudeModelUrl,
      databaseUrl: settings.databaseUrl,
      tabAutocompleteEnabled: settings.tabAutocompleteEnabled
    };
  },

  /**
   * Get Claude API key
   */
  getClaudeApiKey: (): string => {
    return AppStateService.getState().settings.claudeApiKey;
  },

  /**
   * Get Claude model URL
   */
  getClaudeModelUrl: (): string => {
    return AppStateService.getState().settings.claudeModelUrl;
  },

  /**
   * Get Claude model ID
   */
  getClaudeModelId: (): string => {
    return AppStateService.getState().settings.claudeModelId;
  },

  /**
   * Set the extensions manager
   */
  setExtensions: (extensions: ListModel) => {
    AppStateService.setState({ extensions });
  },

  /**
   * Get the extensions manager
   */
  getExtensions: (): ListModel | null => {
    return AppStateService.getState().extensions;
  },

  /**
   * Set the settings registry
   */
  setSettingsRegistry: (settingsRegistry: ISettingRegistry | null) => {
    AppStateService.setState({ settingsRegistry });
  },

  /**
   * Get the settings registry
   */
  getSettingsRegistry: (): ISettingRegistry | null => {
    return AppStateService.getState().settingsRegistry;
  },

  /**
   * Set the service manager
   */
  setServiceManager: (serviceManager: ServiceManager.IManager) => {
    AppStateService.setState({ serviceManager });
  },

  /**
   * Get the service manager
   */
  getServiceManager: (): ServiceManager.IManager | null => {
    return AppStateService.getState().serviceManager;
  },

  /**
   * Get a specific service safely
   */
  getToolService: (): ToolService => {
    const toolService = AppStateService.getState().toolService;
    if (!toolService) {
      throw new Error('ToolService not initialized in IAppState');
    }
    return toolService;
  },

  getNotebookTracker: (): INotebookTracker => {
    const notebookTracker = AppStateService.getState().notebookTracker;
    if (!notebookTracker) {
      throw new Error('NotebookTracker not initialized in IAppState');
    }
    return notebookTracker;
  },

  getNotebookTools: (): NotebookTools => {
    const notebookTools = AppStateService.getState().notebookTools;
    if (!notebookTools) {
      throw new Error('NotebookTools not initialized in IAppState');
    }
    return notebookTools;
  },

  getNotebookContextManager: (): NotebookContextManager => {
    const notebookContextManager =
      AppStateService.getState().notebookContextManager;
    if (!notebookContextManager) {
      throw new Error('NotebookContextManager not initialized in IAppState');
    }
    return notebookContextManager;
  },

  getContentManager: (): Contents.IManager => {
    const contentManager = AppStateService.getState().contentManager;
    if (!contentManager) {
      throw new Error('ContentManager not initialized in IAppState');
    }
    return contentManager;
  },

  getDocumentManager: (): IDocumentManager => {
    const documentManager = AppStateService.getState().documentManager;
    if (!documentManager) {
      throw new Error('DocumentManager not initialized in IAppState');
    }
    return documentManager;
  },

  getPlanStateDisplay: (): PlanStateDisplay => {
    const planStateDisplay = AppStateService.getState().planStateDisplay;
    if (!planStateDisplay) {
      throw new Error('PlanStateDisplay not initialized in IAppState');
    }
    return planStateDisplay;
  },

  getLlmStateDisplay: (): LLMStateDisplay | null => {
    const llmStateDisplay = AppStateService.getState().llmStateDisplay;
    if (!llmStateDisplay) {
      throw new Error('LLMStateDisplay not initialized in IAppState');
    }
    return llmStateDisplay;
  },

  getWaitingUserReplyBoxManager: (): WaitingUserReplyBoxManager => {
    const waitingUserReplyBoxManager =
      AppStateService.getState().waitingUserReplyBoxManager;
    if (!waitingUserReplyBoxManager) {
      throw new Error(
        'WaitingUserReplyBoxManager not initialized in IAppState'
      );
    }
    return waitingUserReplyBoxManager;
  },

  getActionHistory: (): ActionHistory => {
    const actionHistory = AppStateService.getState().actionHistory;
    if (!actionHistory) {
      throw new Error('ActionHistory not initialized in IAppState');
    }
    return actionHistory;
  },

  getCellTrackingService: (): CellTrackingService => {
    const cellTrackingService = AppStateService.getState().cellTrackingService;
    if (!cellTrackingService) {
      throw new Error('CellTrackingService not initialized in IAppState');
    }
    return cellTrackingService;
  },

  getNotebookDiffManager: (): NotebookDiffManager => {
    const notebookDiffManager = AppStateService.getState().notebookDiffManager;
    if (!notebookDiffManager) {
      throw new Error('NotebookDiffManager not initialized in IAppState');
    }
    return notebookDiffManager;
  },

  getTrackingIDUtility: (): TrackingIDUtility => {
    const trackingIDUtility = AppStateService.getState().trackingIDUtility;
    if (!trackingIDUtility) {
      throw new Error('TrackingIDUtility not initialized in IAppState');
    }
    return trackingIDUtility;
  },

  getContextCellHighlighter: (): ContextCellHighlighter => {
    const contextCellHighlighter =
      AppStateService.getState().contextCellHighlighter;
    if (!contextCellHighlighter) {
      throw new Error('ContextCellHighlighter not initialized in IAppState');
    }
    return contextCellHighlighter;
  },

  getChatContainer: (): NotebookChatContainer => {
    const chatContainer = AppStateService.getState().chatContainer;
    if (!chatContainer) {
      throw new Error('ChatContainer not initialized in IAppState');
    }
    return chatContainer;
  },

  /**
   * Set the chat container
   */
  setChatContainer: (chatContainer: NotebookChatContainer) => {
    AppStateService.setState({ chatContainer });
  },

  /**
   * Get the chat container safely (returns null if not initialized)
   */
  getChatContainerSafe: (): NotebookChatContainer | null => {
    return AppStateService.getState().chatContainer;
  },

  /**
   * Wait for the chatbox to be fully ready (after launcher setup completes)
   * This is crucial for replay mode to avoid race conditions
   * @param maxRetries Maximum number of retries (default: 100, ~10 seconds)
   * @param delayMs Delay between retries in milliseconds (default: 100ms)
   * @returns Promise that resolves when chatbox is ready, rejects on timeout
   */
  waitForChatboxReady: async (
    maxRetries: number = 100,
    delayMs: number = 100
  ): Promise<void> => {
    console.log('[AppState] Waiting for chatbox to be fully ready...');
    
    let retries = maxRetries;
    while (retries > 0) {
      const chatContainer = AppStateService.getChatContainerSafe();
      
      if (chatContainer && chatContainer.chatWidget && chatContainer.chatWidget.isFullyReady()) {
        console.log('[AppState] Chatbox is fully ready!');
        return;
      }
      
      await new Promise(resolve => setTimeout(resolve, delayMs));
      retries--;
      
      if (retries % 10 === 0) {
        console.log(`[AppState] Still waiting for chatbox... (${retries} retries left)`);
      }
    }
    
    throw new Error('Timeout waiting for chatbox to be fully ready');
  },

  /**
   * Set the diff navigation widget
   */
  setDiffNavigationWidget: (diffNavigationWidget: DiffNavigationWidget) => {
    AppStateService.setState({ diffNavigationWidget });
  },

  /**
   * Get the diff navigation widget
   */
  getDiffNavigationWidget: (): DiffNavigationWidget => {
    const diffNavigationWidget =
      AppStateService.getState().diffNavigationWidget;
    if (!diffNavigationWidget) {
      throw new Error('DiffNavigationWidget not initialized in IAppState');
    }
    return diffNavigationWidget;
  },

  /**
   * Get the diff navigation widget safely (returns null if not initialized)
   */
  getDiffNavigationWidgetSafe: (): DiffNavigationWidget | null => {
    return AppStateService.getState().diffNavigationWidget;
  },

  /**
   * Set the chat service
   */
  setChatService: (chatService: IChatService) => {
    AppStateService.setState({ chatService });
  },

  getChatService: (): IChatService => {
    const chatService = AppStateService.getState().chatService;
    if (!chatService) {
      throw new Error('ChatService not initialized in IAppState');
    }
    return chatService;
  },

  setConfig: (config: IConfig) => {
    AppStateService.setState({ config });
  },

  getConfig: (): IConfig => {
    const config = AppStateService.getState().config;
    if (!config) {
      throw new Error('Config not initialized in IAppState');
    }
    return config;
  },

  /**
   * Update chat container with new notebook ID
   */
  updateChatContainerNotebookId: (
    oldNotebookId: string,
    newNotebookId: string
  ) => {
    const chatContainer = AppStateService.getState().chatContainer;
    if (chatContainer && !chatContainer.isDisposed) {
      chatContainer.updateNotebookId(oldNotebookId, newNotebookId);
    }
  },

  /**
   * Get all snippets
   */
  getSnippets: (): ISnippet[] => {
    return AppStateService.getState().snippets;
  },

  /**
   * Set snippets and persist to StateDB
   */
  setSnippets: async (snippets: ISnippet[]) => {
    AppStateService.setState({ snippets });
    try {
      await StateDBCachingService.setObjectValue(
        STATE_DB_KEYS.SNIPPETS,
        snippets
      );
    } catch (error) {
      console.error(
        '[AppStateService] Failed to persist snippets to StateDB:',
        error
      );
    }
  },

  /**
   * Add a snippet and persist to StateDB
   */
  addSnippet: async (snippet: ISnippet) => {
    const currentSnippets = AppStateService.getState().snippets;
    const newSnippets = [...currentSnippets, snippet];
    AppStateService.setState({ snippets: newSnippets });
    try {
      await StateDBCachingService.setObjectValue(
        STATE_DB_KEYS.SNIPPETS,
        newSnippets
      );
    } catch (error) {
      console.error(
        '[AppStateService] Failed to persist snippets to StateDB:',
        error
      );
    }
  },

  /**
   * Update a snippet and persist to StateDB
   */
  updateSnippet: async (snippetId: string, updates: Partial<ISnippet>) => {
    console.log('[AppStateService] Updating snippet with ID:', snippetId);
    console.log('[AppStateService] Updates:', updates);

    const currentSnippets = AppStateService.getState().snippets;
    console.log(
      '[AppStateService] Current snippets count:',
      currentSnippets.length
    );

    const updatedSnippets = currentSnippets.map(snippet => {
      if (snippet.id === snippetId) {
        console.log(
          '[AppStateService] Found snippet to update:',
          snippet.title
        );
        return { ...snippet, ...updates };
      }
      return snippet;
    });

    console.log(
      '[AppStateService] Updated snippets count:',
      updatedSnippets.length
    );

    AppStateService.setState({ snippets: updatedSnippets });
    try {
      await StateDBCachingService.setObjectValue(
        STATE_DB_KEYS.SNIPPETS,
        updatedSnippets
      );
      console.log(
        '[AppStateService] Successfully persisted updated snippets to StateDB'
      );
    } catch (error) {
      console.error(
        '[AppStateService] Failed to persist snippets to StateDB:',
        error
      );
    }
  },

  /**
   * Remove a snippet and persist to StateDB
   */
  removeSnippet: async (snippetId: string) => {
    const currentSnippets = AppStateService.getState().snippets;
    const filteredSnippets = currentSnippets.filter(
      snippet => snippet.id !== snippetId
    );
    AppStateService.setState({ snippets: filteredSnippets });
    try {
      await StateDBCachingService.setObjectValue(
        STATE_DB_KEYS.SNIPPETS,
        filteredSnippets
      );
    } catch (error) {
      console.error(
        '[AppStateService] Failed to persist snippets to StateDB:',
        error
      );
    }
  },

  /**
   * Load snippets from StateDB with migration for unique IDs
   */
  loadSnippets: async (): Promise<void> => {
    try {
      const snippets = await StateDBCachingService.getObjectValue<ISnippet[]>(
        STATE_DB_KEYS.SNIPPETS,
        []
      );

      // Migrate snippets to ensure all have unique IDs
      const migratedSnippets =
        await AppStateService.migrateSnippetsForUniqueIds(snippets);

      AppStateService.setState({ snippets: migratedSnippets });
      console.log(
        '[AppStateService] Loaded',
        migratedSnippets.length,
        'snippets from StateDB'
      );
    } catch (error) {
      console.error(
        '[AppStateService] Failed to load snippets from StateDB:',
        error
      );
    }
  },

  /**
   * Migrate snippets to ensure all have unique IDs
   */
  migrateSnippetsForUniqueIds: async (
    snippets: ISnippet[]
  ): Promise<ISnippet[]> => {
    let needsUpdate = false;
    const usedIds = new Set<string>();

    console.log(
      '[AppStateService] Checking',
      snippets.length,
      'snippets for unique IDs'
    );

    const migratedSnippets = snippets.map((snippet, index) => {
      // Check if snippet has no ID, invalid ID, or duplicate ID
      const hasValidId =
        snippet.id &&
        typeof snippet.id === 'string' &&
        snippet.id.trim().length > 0;
      const isDuplicate = hasValidId && usedIds.has(snippet.id);

      if (!hasValidId || isDuplicate) {
        needsUpdate = true;
        const newId = AppStateService.generateSnippetId();
        usedIds.add(newId);
        console.log(
          `[AppStateService] Migrating snippet #${index} "${snippet.title}" with new ID: ${newId}` +
            (isDuplicate ? ' (duplicate ID)' : ' (missing/invalid ID)')
        );
        return {
          ...snippet,
          id: newId,
          updatedAt: new Date().toISOString()
        };
      }

      usedIds.add(snippet.id);
      return snippet;
    });

    // If any snippets were updated, save back to StateDB
    if (needsUpdate) {
      try {
        await StateDBCachingService.setObjectValue(
          STATE_DB_KEYS.SNIPPETS,
          migratedSnippets
        );
        console.log(
          '[AppStateService] Successfully migrated snippet IDs to StateDB'
        );
      } catch (error) {
        console.error(
          '[AppStateService] Failed to save migrated snippets:',
          error
        );
      }
    } else {
      console.log(
        '[AppStateService] All snippets already have valid unique IDs'
      );
    }

    return migratedSnippets;
  },

  /**
   * Generate a unique ID for a snippet
   */
  generateSnippetId: (): string => {
    return uuidv4();
  },

  /**
   * Load inserted snippets from StateDB
   */
  loadInsertedSnippets: async (): Promise<void> => {
    try {
      const insertedSnippets = await StateDBCachingService.getObjectValue<
        string[]
      >(STATE_DB_KEYS.INSERTED_SNIPPETS, []);

      AppStateService.setState({ insertedSnippets });
      console.log(
        '[AppStateService] Loaded',
        insertedSnippets.length,
        'inserted snippets from StateDB'
      );
    } catch (error) {
      console.error(
        '[AppStateService] Failed to load inserted snippets from StateDB:',
        error
      );
    }
  },

  /**
   * Save inserted snippets to StateDB
   */
  saveInsertedSnippets: async (): Promise<void> => {
    try {
      const currentState = AppStateService.getState();
      const insertedSnippets = currentState.insertedSnippets || [];
      await StateDBCachingService.setObjectValue(
        STATE_DB_KEYS.INSERTED_SNIPPETS,
        insertedSnippets
      );
      console.log(
        '[AppStateService] Saved',
        insertedSnippets.length,
        'inserted snippets to StateDB'
      );
    } catch (error) {
      console.error(
        '[AppStateService] Failed to save inserted snippets to StateDB:',
        error
      );
    }
  },

  /**
   * Add a snippet ID to the inserted snippets list
   */
  addInsertedSnippet: async (snippetId: string): Promise<void> => {
    const currentState = AppStateService.getState();
    const insertedSnippets = currentState.insertedSnippets || [];
    if (!insertedSnippets.includes(snippetId)) {
      const newInsertedSnippets = [...insertedSnippets, snippetId];
      AppStateService.setState({
        insertedSnippets: newInsertedSnippets
      });

      // Persist to StateDB
      try {
        await StateDBCachingService.setObjectValue(
          STATE_DB_KEYS.INSERTED_SNIPPETS,
          newInsertedSnippets
        );
        console.log(
          '[AppStateService] Added inserted snippet to StateDB:',
          snippetId
        );
      } catch (error) {
        console.error(
          '[AppStateService] Failed to save inserted snippet to StateDB:',
          error
        );
      }
    }
  },

  /**
   * Remove a snippet ID from the inserted snippets list
   */
  removeInsertedSnippet: async (snippetId: string): Promise<void> => {
    const currentState = AppStateService.getState();
    const insertedSnippets = currentState.insertedSnippets || [];
    const newInsertedSnippets = insertedSnippets.filter(id => id !== snippetId);

    AppStateService.setState({
      insertedSnippets: newInsertedSnippets
    });

    // Persist to StateDB
    try {
      await StateDBCachingService.setObjectValue(
        STATE_DB_KEYS.INSERTED_SNIPPETS,
        newInsertedSnippets
      );
      console.log(
        '[AppStateService] Removed inserted snippet from StateDB:',
        snippetId
      );
    } catch (error) {
      console.error(
        '[AppStateService] Failed to remove inserted snippet from StateDB:',
        error
      );
    }
  },

  /**
   * Get all inserted snippets with their content
   */
  getInsertedSnippets: (): ISnippet[] => {
    const currentState = AppStateService.getState();
    const insertedSnippets = currentState.insertedSnippets || [];
    return currentState.snippets.filter(snippet =>
      insertedSnippets.includes(snippet.id)
    );
  },

  /**
   * Get the array of inserted snippet IDs safely (never null/undefined)
   */
  getInsertedSnippetIds: (): string[] => {
    const currentState = AppStateService.getState();
    return currentState.insertedSnippets || [];
  },

  /**
   * Check if a snippet is currently inserted
   */
  isSnippetInserted: (snippetId: string): boolean => {
    const currentState = AppStateService.getState();
    const insertedSnippets = currentState.insertedSnippets || [];
    return insertedSnippets.includes(snippetId);
  },

  /**
   * Clear all inserted snippets
   */
  clearInsertedSnippets: async (): Promise<void> => {
    AppStateService.setState({ insertedSnippets: [] });

    // Persist to StateDB
    try {
      await StateDBCachingService.setObjectValue(
        STATE_DB_KEYS.INSERTED_SNIPPETS,
        []
      );
      console.log(
        '[AppStateService] Cleared all inserted snippets from StateDB'
      );
    } catch (error) {
      console.error(
        '[AppStateService] Failed to clear inserted snippets from StateDB:',
        error
      );
    }
  },

  /**
   * Switch chat container to a notebook
   */
  switchChatContainerToNotebook: (notebookId: string) => {
    const chatContainer = AppStateService.getState().chatContainer;
    if (chatContainer && !chatContainer.isDisposed) {
      void chatContainer.switchToNotebook(notebookId);
    }
  },

  /**
   * Find a notebook by its unique sage_ai.unique_id
   * @param uniqueId The unique ID to search for
   * @returns The notebook widget if found, null otherwise
   */
  getNotebookByID: async (uniqueId: string): Promise<NotebookPanel | null> => {
    const notebookTracker = AppStateService.getState().notebookTracker;
    const contentManager = AppStateService.getState().contentManager;

    if (!notebookTracker || !contentManager) {
      console.warn('NotebookTracker or ContentManager not initialized');
      return null;
    }

    // Convert forEach to a proper async iteration
    const notebooks: any[] = [];
    notebookTracker.forEach(notebook => {
      notebooks.push(notebook);
    });

    for (const notebook of notebooks) {
      try {
        const nbFile = await contentManager.get(notebook.context.path);
        if (nbFile) {
          const nbMetadata = nbFile.content.metadata || {};
          if (nbMetadata.sage_ai && nbMetadata.sage_ai.unique_id === uniqueId) {
            return notebook;
          }
        }
      } catch (error) {
        console.warn(
          `Error checking notebook ${notebook.context.path}:`,
          error
        );
      }
    }

    return notebookTracker.currentWidget;
  },

  /**
   * Get cached contexts
   */
  getCachedContexts: (): Map<string, IMentionContext[]> => {
    return AppStateService.getState().contextCache;
  },

  /**
   * Set cached contexts
   */
  setCachedContexts: (contexts: Map<string, IMentionContext[]>) => {
    AppStateService.setState({
      contextCache: contexts,
      contextCacheTimestamp: Date.now(),
      isContextLoading: false
    });
  },

  /**
   * Update a specific context category
   */
  updateContextCategory: (category: string, contexts: IMentionContext[]) => {
    const currentCache = AppStateService.getState().contextCache;
    const newCache = new Map(currentCache);
    newCache.set(category, contexts);
    AppStateService.setState({
      contextCache: newCache,
      contextCacheTimestamp: Date.now()
    });
  },

  /**
   * Check if contexts are being loaded
   */
  isContextLoading: (): boolean => {
    return AppStateService.getState().isContextLoading;
  },

  /**
   * Set context loading state
   */
  setContextLoading: (loading: boolean) => {
    AppStateService.setState({ isContextLoading: loading });
  },

  /**
   * Get the age of cached contexts in milliseconds
   */
  getContextCacheAge: (): number => {
    return Date.now() - AppStateService.getState().contextCacheTimestamp;
  },

  /**
   * Check if contexts need refreshing (older than 30 seconds)
   */
  shouldRefreshContexts: (): boolean => {
    const cacheAge = AppStateService.getContextCacheAge();
    return cacheAge > 30000; // 30 seconds
  },

  /**
   * Set the maximum tool call limit
   */
  setMaxToolCallLimit: (limit: number | null) => {
    AppStateService.setState({ maxToolCallLimit: limit });
  },

  /**
   * Get the maximum tool call limit
   */
  getMaxToolCallLimit: (): number | null => {
    return AppStateService.getState().maxToolCallLimit;
  },

  /**
   * Set the workspace context
   */
  setWorkspaceContext: (workspaceContext: any) => {
    AppStateService.setState({ workspaceContext });
  },

  /**
   * Get the workspace context
   */
  getWorkspaceContext: (): any | null => {
    return AppStateService.getState().workspaceContext;
  },

  /**
   * Check if the welcome tour has been completed
   */
  hasCompletedWelcomeTour: async (): Promise<boolean> => {
    const completed = await StateDBCachingService.getValue(
      STATE_DB_KEYS.WELCOME_TOUR_COMPLETED,
      false
    );
    return completed as boolean;
  },

  /**
   * Mark the welcome tour as completed
   */
  markWelcomeTourCompleted: async (): Promise<void> => {
    await StateDBCachingService.setValue(
      STATE_DB_KEYS.WELCOME_TOUR_COMPLETED,
      true
    );
    console.log('[AppStateService] Welcome tour marked as completed');
  },

  /**
   * Set demo mode and persist to cache
   */
  setDemoMode: async (isDemoMode: boolean): Promise<void> => {
    AppStateService.setState({ isDemoMode });
    await StateDBCachingService.setValue(
      STATE_DB_KEYS.IS_DEMO_MODE,
      isDemoMode
    );
    console.log('[AppStateService] Demo mode set to:', isDemoMode);
  },

  /**
   * Get current demo mode status
   */
  isDemoMode: (): boolean => {
    return AppStateService.getState().isDemoMode;
  },

  /**
   * Load demo mode from cache and set in state
   */
  loadDemoMode: async (): Promise<void> => {
    try {
      const isDemoMode = await StateDBCachingService.getValue(
        STATE_DB_KEYS.IS_DEMO_MODE,
        false
      );
      AppStateService.setState({ isDemoMode: isDemoMode as boolean });
      console.log('[AppStateService] Loaded demo mode from cache:', isDemoMode);
    } catch (error) {
      console.error(
        '[AppStateService] Failed to load demo mode from cache:',
        error
      );
      AppStateService.setState({ isDemoMode: false });
    }
  },

  /**
   * Set takeover mode state
   */
  setTakeoverMode: (isTakeoverMode: boolean, takeoverPrompt: string | null = null) => {
    AppStateService.setState({ isTakeoverMode, takeoverPrompt });
    console.log('[AppStateService] Takeover mode set to:', isTakeoverMode, 'with prompt:', takeoverPrompt);
  },

  /**
   * Get takeover mode state
   */
  isTakeoverMode: (): boolean => {
    return AppStateService.getState().isTakeoverMode;
  },

  /**
   * Get takeover prompt
   */
  getTakeoverPrompt: (): string | null => {
    return AppStateService.getState().takeoverPrompt;
  },

  /**
   * Set user profile
   */
  setUserProfile: (userProfile: any | null) => {
    AppStateService.setState({ userProfile });
    console.log('[AppStateService] User profile set:', userProfile ? 'loaded' : 'cleared');
  },

  /**
   * Get user profile
   */
  getUserProfile: (): any | null => {
    return AppStateService.getState().userProfile;
  },

  /**
   * Set auto-run mode
   */
  setAutoRun: (enabled: boolean) => {
    AppStateService.setState({ autoRun: enabled });
    console.log(`[AppStateService] Auto-run mode ${enabled ? 'enabled' : 'disabled'}`);
  },

  /**
   * Get auto-run mode
   */
  getAutoRun: (): boolean => {
    return AppStateService.getState().autoRun;
  }
};

// Example usage:

// Read from state
// const { toolService, settings } = AppStateService.getState();

// Update state
// AppStateService.setState({ currentNotebookPath: '/path/to/notebook.ipynb' });

// Subscribe to changes
// AppStateService.changes.subscribe(state => {
//   console.log('New state!', state);
// });

// Use convenience methods
// const toolService = AppStateService.getToolService();
// AppStateService.updateSettings({ theme: 'dark' });
