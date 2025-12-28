import * as React from 'react';
import { Widget } from '@lumino/widgets';
import { ReactWidget } from '@jupyterlab/ui-components';
import { ISignal, Signal } from '@lumino/signaling';
import { ToolService } from '../../Services/ToolService';
import { CodebaseManager } from '../../CodebaseManager';
import { AppStateService } from '../../AppState';
import { CachingService, SETTING_KEYS } from '../../utils/caching';
import { KernelUtils } from '../../utils/kernelUtils';
import { DatabaseMetadataCache } from '../../Services/DatabaseMetadataCache';
import { JupyterAuthService } from '../../Services/JupyterAuthService';
import {
  DatabaseCreationModal,
  IDatabaseFormData
} from '../DatabaseCreationModal/DatabaseCreationModal';
import {
  DatabaseStateService,
  IDatabaseConfig,
  DatabaseType
} from '../../DatabaseStateService';


// Free trial duration in days
const FREE_TRIAL_DAYS = 7;

/**
 * Interface for user profile data
 */
export interface IUserProfile {
  id: string;
  clerk_id: string;
  email: string;
  created_at: string;
  updated_at: string;
  subscription_expiry: string | null;
  subscription_price_id: string | null;
  subscribed_at: string | null;
  is_free_trial: boolean;
}

/**
 * Interface for the Settings state
 */
export interface ISettingsState {
  isVisible: boolean;
  sageTokenMode: boolean;
  tabAutocompleteEnabled: boolean;
  claudeApiKey: string;
  claudeModelId: string;
  claudeModelUrl: string;
  databaseUrl: string;
  jwtToken: string;
  isAuthenticated: boolean;
  userProfile: IUserProfile | null;
}

/**
 * Helper function to calculate remaining free trial time
 */
function calculateFreeTrialRemaining(createdAt: string): {
  isExpired: boolean;
  remainingText: string;
} {
  const createdDate = new Date(createdAt);
  const expiryDate = new Date(createdDate);
  expiryDate.setDate(expiryDate.getDate() + FREE_TRIAL_DAYS);

  const now = new Date();
  const diffMs = expiryDate.getTime() - now.getTime();

  if (diffMs <= 0) {
    return { isExpired: true, remainingText: '' };
  }

  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays >= 1) {
    return {
      isExpired: false,
      remainingText: `${diffDays} day${diffDays > 1 ? 's' : ''}`
    };
  } else if (diffHours >= 1) {
    return {
      isExpired: false,
      remainingText: `${diffHours} hour${diffHours > 1 ? 's' : ''}`
    };
  } else {
    return {
      isExpired: false,
      remainingText: `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''}`
    };
  }
}

/**
 * React component for displaying Settings content
 */
function SettingsContent({
  isVisible,
  sageTokenMode,
  tabAutocompleteEnabled,
  claudeApiKey,
  claudeModelId,
  claudeModelUrl,
  databaseUrl,
  jwtToken,
  isAuthenticated,
  userProfile,
  onTokenModeChange,
  onTabAutocompleteChange,
  onDatabaseUrlChange,
  onLoginClick,
  onLogoutClick,
  toolService
}: {
  isVisible: boolean;
  sageTokenMode: boolean;
  tabAutocompleteEnabled: boolean;
  claudeApiKey: string;
  claudeModelId: string;
  claudeModelUrl: string;
  databaseUrl: string;
  jwtToken: string;
  isAuthenticated: boolean;
  userProfile: IUserProfile | null;
  onTokenModeChange: (enabled: boolean) => void;
  onTabAutocompleteChange: (enabled: boolean) => void;
  onDatabaseUrlChange: (value: string) => void;
  onLoginClick: () => void;
  onLogoutClick: () => void;
  toolService: ToolService;
}): JSX.Element | null {
  const [codebaseManager, setCodebaseManager] =
    React.useState<CodebaseManager | null>(null);
  const codebaseContainerRef = React.useRef<HTMLDivElement>(null);

  // Database creation modal state
  const [isDatabaseModalVisible, setIsDatabaseModalVisible] =
    React.useState<boolean>(false);
  const [, setDatabaseConfigs] = React.useState<IDatabaseConfig[]>([]);

  // Database cache state
  const [, setCacheStatus] = React.useState<{
    isCached: boolean;
    lastUpdated: number | null;
    isExpired: boolean;
  }>({ isCached: false, lastUpdated: null, isExpired: false });



  // Get database cache instance
  const databaseCache = React.useMemo(
    () => DatabaseMetadataCache.getInstance(),
    []
  );

  // Load database configurations on mount
  React.useEffect(() => {
    const loadDatabaseConfigs = async () => {
      try {
        await DatabaseStateService.loadConfigurationsFromStateDB();
        const configs = DatabaseStateService.getState().configurations;
        setDatabaseConfigs(configs);
      } catch (error) {
        console.error(
          '[SettingsWidget] Failed to load database configurations:',
          error
        );
      }
    };

    void loadDatabaseConfigs();
  }, []);

  const handleCloseDatabaseModal = () => {
    setIsDatabaseModalVisible(false);
  };

  const handleCreateDatabase = async (
    dbConfig: IDatabaseFormData
  ): Promise<void> => {
    try {
      let newConfig: IDatabaseConfig;

      switch (dbConfig.type) {
        case DatabaseType.PostgreSQL:
          newConfig =
            await DatabaseStateService.createAndPersistPostgreSQLConfig(
              dbConfig.name,
              dbConfig.description,
              dbConfig.host,
              dbConfig.port,
              dbConfig.database,
              dbConfig.username,
              dbConfig.password
            );
          break;

        case DatabaseType.MySQL:
          newConfig = await DatabaseStateService.createAndPersistMySQLConfig(
            dbConfig.name,
            dbConfig.description,
            dbConfig.host,
            dbConfig.port,
            dbConfig.database,
            dbConfig.username,
            dbConfig.password
          );
          break;

        case DatabaseType.Snowflake:
          newConfig =
            await DatabaseStateService.createAndPersistSnowflakeConfig(
              dbConfig.name,
              dbConfig.description,
              dbConfig.snowflakeConnectionUrl,
              dbConfig.username,
              dbConfig.password,
              dbConfig.database || undefined,
              dbConfig.warehouse || undefined,
              dbConfig.role || undefined
            );
          break;

        case DatabaseType.Databricks:
          newConfig =
            await DatabaseStateService.createAndPersistDatabricksConfig(
              dbConfig.name,
              dbConfig.description,
              dbConfig.databricksConnectionUrl || '',
              dbConfig.databricksAuthType || 'pat',
              dbConfig.databricksCatalog || '',
              dbConfig.databricksAccessToken,
              dbConfig.databricksClientId,
              dbConfig.databricksClientSecret,
              dbConfig.databricksWarehouseHttpPath,
              dbConfig.databricksSchema
            );
          break;

        default:
          throw new Error(`Unsupported database type: ${dbConfig.type}`);
      }

      // Update local state
      setDatabaseConfigs(prev => [...prev, newConfig]);

      console.log(
        '[SettingsWidget] ✅ Database configuration created successfully:',
        newConfig.id
      );
    } catch (error) {
      console.error(
        '[SettingsWidget] ❌ Failed to create database configuration:',
        error
      );
      throw error; // Re-throw to let modal handle the error
    }
  };

  // Update cache status periodically
  React.useEffect(() => {
    const updateCacheStatus = () => {
      setCacheStatus(databaseCache.getCacheStatus());
    };

    // Initial update
    updateCacheStatus();

    // Subscribe to cache updates
    const subscription = databaseCache.metadata$.subscribe(() => {
      updateCacheStatus();
    });

    // Update status every second to show accurate time
    const interval = setInterval(updateCacheStatus, 1000);

    return () => {
      subscription.unsubscribe();
      clearInterval(interval);
    };
  }, [databaseCache]);

  // Initialize codebase manager when toolService is available
  React.useEffect(() => {
    if (toolService && codebaseContainerRef.current && !codebaseManager) {
      const manager = new CodebaseManager(toolService);
      setCodebaseManager(manager);
      codebaseContainerRef.current.appendChild(manager.getElement());
    }
  }, [toolService, codebaseManager]);

  // Cleanup codebase manager on unmount
  React.useEffect(() => {
    return () => {
      if (codebaseManager && codebaseContainerRef.current) {
        const element = codebaseManager.getElement();
        if (element.parentNode) {
          element.parentNode.removeChild(element);
        }
      }
    };
  }, [codebaseManager]);

  if (!isVisible) {
    return null;
  }

  const handleTokenModeChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    onTokenModeChange(event.target.checked);
  };

  const handleTabAutocompleteChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    onTabAutocompleteChange(event.target.checked);
  };

  // Check if user is subscribed
  const isUserSubscribed = React.useMemo(() => {
    if (!userProfile?.subscription_expiry) {
      return false;
    }

    try {
      const expiryDate = new Date(userProfile.subscription_expiry);
      const now = new Date();
      return expiryDate > now;
    } catch (error) {
      console.error(
        '[SettingsWidget] Invalid subscription_expiry date:',
        error
      );
      return false;
    }
  }, [userProfile?.subscription_expiry]);

  // Check if user has any subscription fields set
  const hasSubscription = React.useMemo(() => {
    if (!userProfile) {
      return false;
    }
    return !!(
      userProfile.subscription_expiry ||
      userProfile.subscription_price_id ||
      userProfile.subscribed_at
    );
  }, [userProfile]);

  // Calculate free trial status
  const freeTrialStatus = React.useMemo(() => {
    if (!userProfile || hasSubscription) {
      return null;
    }

    if (userProfile.is_free_trial) {
      return calculateFreeTrialRemaining(userProfile.created_at);
    }

    // If not in free trial and no subscription, show expired
    return { isExpired: true, remainingText: '' };
  }, [userProfile, hasSubscription]);



  return (
    <div className="sage-ai-settings-container">
      <h3 className="sage-ai-settings-title">SignalPilot Settings</h3>

      {/* Free Trial Banner */}
      {freeTrialStatus && (
        <div
          className={`sage-ai-free-trial-banner ${
            freeTrialStatus.isExpired
              ? 'sage-ai-free-trial-expired'
              : 'sage-ai-free-trial-active'
          }`}
        >
          {freeTrialStatus.isExpired ? (
            <>
              <span className="sage-ai-free-trial-icon">⚠️</span>
              <span className="sage-ai-free-trial-text">FREE TRIAL ENDED</span>
            </>
          ) : (
            <>
              <span className="sage-ai-free-trial-icon">🎁</span>
              <span className="sage-ai-free-trial-text">
                Free Trial for {freeTrialStatus.remainingText}
              </span>
            </>
          )}
        </div>
      )}

      {/* Codebase Manager Container */}
      <div ref={codebaseContainerRef} />

      <div className="sage-ai-config-section">
        <div className="sage-ai-field-container">
          <div className="sage-ai-auth-buttons">
            {isAuthenticated ? (
              <div className="sage-ai-user-info">
                <div className="sage-ai-logged-in-as">
                  <div className="sage-ai-logged-in-label">Logged In As:</div>
                  <div className="sage-ai-logged-in-email">
                    {userProfile?.email || 'Loading...'}
                  </div>
                </div>

                {/* Subscription Status Badge */}
                {isUserSubscribed && (
                  <div className="sage-ai-subscription-badge-container">
                    <span className="sage-ai-tool-call-badge sage-ai-subscription-badge">
                      ✓ Subscribed
                    </span>
                  </div>
                )}

                <button
                  onClick={onLogoutClick}
                  className="sage-ai-button sage-ai-button-secondary"
                >
                  Logout
                </button>
              </div>
            ) : (
              <button
                onClick={onLoginClick}
                className="sage-ai-button sage-ai-button-primary"
              >
                Login
              </button>
            )}
          </div>
        </div>
      </div>

      {/* SignalPilot Token Mode Checkbox */}
      <div className="sage-token-mode-container">
        <label className="sage-token-mode-label">
          <input
            type="checkbox"
            checked={sageTokenMode}
            onChange={handleTokenModeChange}
            className="sage-token-mode-checkbox"
          />
          <span>SignalPilot Token Debug Mode</span>
        </label>
      </div>

      {/* Tab Autocomplete Checkbox */}
      <div className="sage-tab-autocomplete-container">
        <label className="sage-tab-autocomplete-label">
          <input
            type="checkbox"
            checked={tabAutocompleteEnabled}
            onChange={handleTabAutocompleteChange}
            className="sage-tab-autocomplete-checkbox"
          />
          <span>Enable Tab Autocomplete</span>
        </label>
      </div>

      {/* Database Creation Modal */}
      <DatabaseCreationModal
        isVisible={isDatabaseModalVisible}
        onClose={handleCloseDatabaseModal}
        onCreateDatabase={handleCreateDatabase}
      />
    </div>
  );
}

/**
 * React-based Widget that contains the settings for SignalPilot AI
 */
export class SettingsWidget extends ReactWidget {
  private toolService: ToolService;
  private _state: ISettingsState;
  private _stateChanged = new Signal<this, ISettingsState>(this);
  public static SAGE_TOKEN_MODE: boolean = false;
  private static readonly SAGE_TOKEN_MODE_KEY = 'sage-ai-token-mode';
  private static readonly CLAUDE_API_KEY_KEY = 'sage-ai-claude-api-key';
  private static readonly CLAUDE_MODEL_ID_KEY = 'sage-ai-claude-model-id';
  private static readonly CLAUDE_MODEL_URL_KEY = 'sage-ai-claude-model-url';
  private static readonly DATABASE_URL_KEY = 'sage-ai-database-url';

  constructor(toolService: ToolService) {
    super();

    this.id = 'sage-ai-settings';
    this.title.label = 'Settings';
    this.title.closable = false;
    this.addClass('sage-ai-settings');

    this.toolService = toolService;

    // Initialize state with defaults, then load async
    this._state = {
      isVisible: true,
      sageTokenMode: false,
      tabAutocompleteEnabled: true,
      claudeApiKey: '',
      claudeModelId: 'claude-sonnet-4-20250514',
      claudeModelUrl: 'https://sage.alpinex.ai:8760',
      databaseUrl: '',
      jwtToken: '',
      isAuthenticated: false,
      userProfile: null
    };

    // Load settings asynchronously
    void this.initializeSettings();

    // Check for authentication callback
    void this.checkAuthCallback();
  }

  /**
   * Initialize settings from storage
   */
  private async initializeSettings(): Promise<void> {
    try {
      // Load cached settings from settings registry and update AppState
      await this.loadAndSyncSettings();

      // Get updated state from AppState
      const appSettings = AppStateService.getClaudeSettings();
      await this.loadTokenModeSetting(); // This sets SettingsWidget.SAGE_TOKEN_MODE
      await this.loadTabAutocompleteSetting(); // Load tab autocomplete setting
      const tokenMode = SettingsWidget.SAGE_TOKEN_MODE;

      // Update AppState with token mode
      AppStateService.updateSettings({ tokenMode });

      // Check for authentication and use JWT token as API key if available
      const jwtToken = await JupyterAuthService.getJwtToken();
      const isAuthenticated = await JupyterAuthService.isAuthenticated();
      let claudeApiKey = appSettings.claudeApiKey;

      if (isAuthenticated && jwtToken) {
        console.log(
          '[SettingsWidget] User is authenticated, using JWT token as Claude API key'
        );
        claudeApiKey = jwtToken;
        // IMPORTANT: Do NOT save JWT token to settings registry - only update AppState
        console.log(
          '[SettingsWidget] JWT token will NOT be saved to settings registry (per requirements)'
        );
        // Update AppState with JWT token
        AppStateService.updateClaudeSettings({ claudeApiKey: jwtToken });
        console.log(
          '[SettingsWidget] JWT token set in AppState as Claude API key'
        );
      }

      // HARDCODED API CONFIGURATION - Remove user customization per requirements
      const HARDCODED_MODEL_ID = 'claude-sonnet-4-5';
      const HARDCODED_MODEL_URL = 'https://sage.alpinex.ai:8760';

      console.log('[SettingsWidget] Using hardcoded API configuration:', {
        modelId: HARDCODED_MODEL_ID,
        modelUrl: HARDCODED_MODEL_URL
      });

      // Update AppState with hardcoded values and tab autocomplete
      AppStateService.updateClaudeSettings({
        claudeModelId: HARDCODED_MODEL_ID,
        claudeModelUrl: HARDCODED_MODEL_URL,
        tabAutocompleteEnabled: this._state.tabAutocompleteEnabled
      });

      // Update state
      this._state = {
        isVisible: true,
        sageTokenMode: tokenMode,
        tabAutocompleteEnabled: this._state.tabAutocompleteEnabled,
        claudeApiKey,
        claudeModelId: HARDCODED_MODEL_ID,
        claudeModelUrl: HARDCODED_MODEL_URL,
        databaseUrl: appSettings.databaseUrl,
        jwtToken: jwtToken || '',
        isAuthenticated,
        userProfile: null
      };

      // Update authentication state
      await this.updateAuthState();

      this.update();
    } catch (error) {
      console.error('Failed to initialize settings:', error);
    }
  }

  /**
   * Get the signal that fires when state changes
   */
  public get stateChanged(): ISignal<this, ISettingsState> {
    return this._stateChanged;
  }

  /**
   * Render the React component
   */
  render(): JSX.Element {
    return (
      <SettingsContent
        isVisible={this._state.isVisible}
        sageTokenMode={this._state.sageTokenMode}
        tabAutocompleteEnabled={this._state.tabAutocompleteEnabled}
        claudeApiKey={this._state.claudeApiKey}
        claudeModelId={this._state.claudeModelId}
        claudeModelUrl={this._state.claudeModelUrl}
        databaseUrl={this._state.databaseUrl}
        jwtToken={this._state.jwtToken}
        isAuthenticated={this._state.isAuthenticated}
        userProfile={this._state.userProfile}
        onTokenModeChange={this.handleTokenModeChange.bind(this)}
        onTabAutocompleteChange={this.handleTabAutocompleteChange.bind(this)}
        onDatabaseUrlChange={this.handleDatabaseUrlChange.bind(this)}
        onLoginClick={this.handleLoginClick.bind(this)}
        onLogoutClick={this.handleLogoutClick.bind(this)}
        toolService={this.toolService}
      />
    );
  }

  /**
   * Load the SignalPilot Token Mode setting from settings registry
   */
  private async loadTokenModeSetting(): Promise<void> {
    const cached = await CachingService.getBooleanSetting(
      SETTING_KEYS.SAGE_TOKEN_MODE,
      false
    );
    SettingsWidget.SAGE_TOKEN_MODE = cached;
  }

  /**
   * Save the SignalPilot Token Mode setting to settings registry
   */
  private async saveTokenModeSetting(value: boolean): Promise<void> {
    await CachingService.setBooleanSetting(SETTING_KEYS.SAGE_TOKEN_MODE, value);
  }

  /**
   * Load the Tab Autocomplete setting from settings registry
   */
  private async loadTabAutocompleteSetting(): Promise<void> {
    const cached = await CachingService.getBooleanSetting(
      SETTING_KEYS.TAB_AUTOCOMPLETE_ENABLED,
      true
    );
    this._state = { ...this._state, tabAutocompleteEnabled: cached };
  }

  /**
   * Save the Tab Autocomplete setting to settings registry
   */
  private async saveTabAutocompleteSetting(value: boolean): Promise<void> {
    await CachingService.setBooleanSetting(
      SETTING_KEYS.TAB_AUTOCOMPLETE_ENABLED,
      value
    );
  }

  /**
   * Generic method to load a setting from settings registry
   */
  private async loadSetting(
    key: string,
    defaultValue: string
  ): Promise<string> {
    return await CachingService.getStringSetting(key, defaultValue);
  }

  /**
   * Generic method to save a setting to settings registry
   */
  private async saveSetting(key: string, value: string): Promise<void> {
    await CachingService.setStringSetting(key, value);
  }

  /**
   * Load settings from settings registry and sync with AppState
   */
  private async loadAndSyncSettings(): Promise<void> {
    let claudeApiKey = await this.loadSetting(SETTING_KEYS.CLAUDE_API_KEY, '');

    // Try to load API key from optional_env.json only if not already set in settings registry
    if (!claudeApiKey || claudeApiKey.trim() === '') {
      try {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const optionalEnv = require('../../Config/optional_env.json');
        if (optionalEnv.api_key) {
          claudeApiKey = optionalEnv.api_key;
          // Cache the API key from optional_env.json to the settings registry
          console.log(
            '[SettingsWidget] Caching API key from optional_env.json to settings registry'
          );
          await this.saveSetting(SETTING_KEYS.CLAUDE_API_KEY, claudeApiKey);
        }
      } catch (error) {
        console.log('No optional_env.json found or error loading it:', error);
      }
    } else {
      console.log(
        '[SettingsWidget] API key already exists in settings registry, not loading from optional_env.json'
      );
    }

    // HARDCODED API CONFIGURATION - Do not load from settings
    const HARDCODED_MODEL_ID = 'claude-sonnet-4-5';
    const HARDCODED_MODEL_URL = 'https://sage.alpinex.ai:8760';

    console.log(
      '[SettingsWidget] Using hardcoded model configuration (ignoring saved settings):',
      {
        modelId: HARDCODED_MODEL_ID,
        modelUrl: HARDCODED_MODEL_URL
      }
    );

    const databaseUrl = await this.loadSetting(SETTING_KEYS.DATABASE_URL, '');

    // Update AppState with loaded settings (hardcoded model values)
    AppStateService.updateClaudeSettings({
      claudeApiKey,
      claudeModelId: HARDCODED_MODEL_ID,
      claudeModelUrl: HARDCODED_MODEL_URL,
      databaseUrl
    });

    // Set DB_URL environment variable in kernel if configured
    console.log('[SettingsWidget] Database URL from settings:', databaseUrl);
    if (databaseUrl && databaseUrl.trim() !== '') {
      console.log(
        '[SettingsWidget] Setting DB_URL in kernel during settings load'
      );
      // Use retry mechanism since kernel might not be ready yet
      void KernelUtils.setDbUrlInKernelWithRetry(databaseUrl);
    } else {
      console.log(
        '[SettingsWidget] No database URL configured, skipping DB_URL setup'
      );
    }
  }

  /**
   * Handle token mode change
   */
  private async handleTokenModeChange(enabled: boolean): Promise<void> {
    SettingsWidget.SAGE_TOKEN_MODE = enabled;
    await this.saveTokenModeSetting(enabled);

    // Update AppState
    AppStateService.updateSettings({ tokenMode: enabled });

    // Update state
    this._state = {
      ...this._state,
      sageTokenMode: enabled
    };

    this._stateChanged.emit(this._state);
    this.update();
  }

  /**
   * Handle tab autocomplete change
   */
  private async handleTabAutocompleteChange(enabled: boolean): Promise<void> {
    await this.saveTabAutocompleteSetting(enabled);

    // Update AppState
    AppStateService.updateClaudeSettings({ tabAutocompleteEnabled: enabled });

    this._state = {
      ...this._state,
      tabAutocompleteEnabled: enabled
    };

    this._stateChanged.emit(this._state);
    this.update();
  }

  /**
   * Handle Claude API key change
   */
  private async handleClaudeApiKeyChange(value: string): Promise<void> {
    await this.saveSetting(SETTING_KEYS.CLAUDE_API_KEY, value);

    // Update AppState
    AppStateService.updateClaudeSettings({ claudeApiKey: value });

    this._state = {
      ...this._state,
      claudeApiKey: value
    };

    this._stateChanged.emit(this._state);
    this.update();
  }

  /**
   * Handle Claude model ID change
   */
  /**
   * Handle database URL change
   */
  private async handleDatabaseUrlChange(value: string): Promise<void> {
    await this.saveSetting(SETTING_KEYS.DATABASE_URL, value);

    // Update AppState
    AppStateService.updateClaudeSettings({ databaseUrl: value });

    // Set DB_URL environment variable in the current kernel
    KernelUtils.setDbUrlInKernel(value);

    // Clear metadata cache if database URL is empty
    if (!value || value.trim() === '') {
      console.log(
        '[SettingsWidget] Database URL cleared, clearing metadata cache'
      );
      const databaseCache = DatabaseMetadataCache.getInstance();
      databaseCache.clearCache();
    }

    this._state = {
      ...this._state,
      databaseUrl: value
    };

    this._stateChanged.emit(this._state);
    this.update();
  }

  /**
   * Handle login button click
   */
  private async handleLoginClick(): Promise<void> {
    try {
      // Open the web app login page
      JupyterAuthService.openLoginPage();
    } catch (error) {
      console.error('Failed to open login page:', error);
    }
  }

  /**
   * Handle logout button click
   */
  private async handleLogoutClick(): Promise<void> {
    try {
      // First, attempt to revoke the JWT token on the server
      try {
        const currentToken = await JupyterAuthService.getJwtToken();
        if (currentToken) {
          console.log(
            '[SettingsWidget] Attempting to revoke JWT token on server...'
          );
          const revoked = await JupyterAuthService.revokeJwtToken(currentToken);
          if (revoked) {
            console.log(
              '[SettingsWidget] ✅ JWT token successfully revoked on server'
            );
          } else {
            console.warn(
              '[SettingsWidget] ⚠️ Failed to revoke JWT token on server, continuing with local logout'
            );
          }
        }
      } catch (revokeError) {
        console.error(
          '[SettingsWidget] ❌ Error during token revocation, continuing with local logout:',
          revokeError
        );
      }

      // Always clear the JWT token from StateDB (regardless of revocation success)
      await JupyterAuthService.clearJwtToken();

      // Clear the API key completely to invalidate LLM session
      // Remove from CachingService instead of just setting to empty string
      await CachingService.removeSetting(SETTING_KEYS.CLAUDE_API_KEY);

      // Clear from AppStateService to invalidate the current LLM session
      AppStateService.updateClaudeSettings({ claudeApiKey: '' });

      // Update state
      this._state = {
        ...this._state,
        jwtToken: '',
        isAuthenticated: false,
        claudeApiKey: '',
        userProfile: null
      };

      this._stateChanged.emit(this._state);
      this.update();

      // Refresh the page to ensure clean state
      window.location.reload();
    } catch (error) {
      console.error('Failed to logout:', error);
    }
  }

  /**
   * Check for authentication callback and update state
   */
  private async checkAuthCallback(): Promise<void> {
    try {
      // Check if this is an auth callback
      const wasCallback = await JupyterAuthService.handleAuthCallback();

      if (wasCallback) {
        // Update authentication state
        await this.updateAuthState();
      }
    } catch (error) {
      console.error('Failed to handle auth callback:', error);
    }
  }

  /**
   * Update authentication state from stored JWT
   */
  private async updateAuthState(): Promise<void> {
    try {
      console.log('[SettingsWidget] Updating authentication state...');
      const jwtToken = await JupyterAuthService.getJwtToken();
      const isAuthenticated = await JupyterAuthService.isAuthenticated();

      // console.log('[SettingsWidget] Auth state:', {
      //   hasJWT: !!jwtToken,
      //   jwtLength: jwtToken?.length || 0,
      //   isAuthenticated
      // });

      // Get user profile if authenticated
      let userProfile = null;
      if (isAuthenticated && jwtToken) {
        try {
          // console.log('[SettingsWidget] Loading user profile...');
          userProfile = await JupyterAuthService.getUserProfile();
          // console.log('[SettingsWidget] User profile loaded:', userProfile);
        } catch (error) {
          console.error('[SettingsWidget] Failed to load user profile:', error);
          // Continue without profile data
        }
      }

      // Automatically use JWT token as Claude API key when authenticated
      let claudeApiKey = this._state.claudeApiKey;
      if (isAuthenticated && jwtToken) {
        console.log(
          '[SettingsWidget] User is authenticated, setting JWT as Claude API key'
        );
        claudeApiKey = jwtToken;
        // IMPORTANT: Do NOT save JWT token to settings registry - only update AppState
        console.log(
          '[SettingsWidget] JWT token will NOT be saved to settings registry (per requirements)'
        );
        // Update AppState with JWT token
        AppStateService.updateClaudeSettings({ claudeApiKey: jwtToken });
        console.log(
          '[SettingsWidget] JWT token set in AppState as Claude API key'
        );
      } else {
        console.log(
          '[SettingsWidget] User not authenticated or no JWT token available'
        );
      }

      // HARDCODED API CONFIGURATION - Ensure values remain hardcoded
      const HARDCODED_MODEL_ID = 'claude-sonnet-4-5';
      const HARDCODED_MODEL_URL = 'https://sage.alpinex.ai:8760';

      this._state = {
        ...this._state,
        jwtToken: jwtToken || '',
        isAuthenticated,
        claudeApiKey,
        claudeModelId: HARDCODED_MODEL_ID,
        claudeModelUrl: HARDCODED_MODEL_URL,
        userProfile
      };

      this._stateChanged.emit(this._state);
      this.update();
    } catch (error) {
      console.error('Failed to update auth state:', error);
    }
  }

  /**
   * Show the settings widget
   */
  public show(): void {
    this._state = {
      ...this._state,
      isVisible: true
    };
    this._stateChanged.emit(this._state);
    this.update();
  }

  /**
   * Hide the settings widget
   */
  public hide(): void {
    this._state = {
      ...this._state,
      isVisible: false
    };
    this._stateChanged.emit(this._state);
    this.update();
  }

  /**
   * Get the current state
   */
  public getState(): ISettingsState {
    return { ...this._state };
  }

  /**
   * Check if the widget is currently visible
   */
  public getIsVisible(): boolean {
    return this._state.isVisible;
  }

  /**
   * Get the current Claude API key
   */
  public getClaudeApiKey(): string {
    return this._state.claudeApiKey;
  }

  /**
   * Get the current Claude model ID
   */
  public getClaudeModelId(): string {
    return this._state.claudeModelId;
  }

  /**
   * Get the current Claude model URL
   */
  public getClaudeModelUrl(): string {
    return this._state.claudeModelUrl;
  }

  /**
   * Get the current database URL
   */
  public getDatabaseUrl(): string {
    return this._state.databaseUrl;
  }

  /**
   * Get the current tab autocomplete setting
   */
  public getTabAutocompleteEnabled(): boolean {
    return this._state.tabAutocompleteEnabled;
  }

  /**
   * Get all Claude settings as an object
   */
  public getClaudeSettings(): {
    apiKey: string;
    modelId: string;
    modelUrl: string;
  } {
    return {
      apiKey: this._state.claudeApiKey,
      modelId: this._state.claudeModelId,
      modelUrl: this._state.claudeModelUrl
    };
  }

  /**
   * Get the widget for adding to layout (for backwards compatibility)
   */
  public getWidget(): Widget {
    return this;
  }
}
