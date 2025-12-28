import { PartialJSONValue } from '@lumino/coreutils';
import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

/**
 * Backend Cache Service - Replaces StateDBCachingService with HTTP-based caching
 * This service provides the same API as StateDBCachingService but stores data
 * in the robust backend cache system instead of JupyterLab's StateDB.
 */
export class BackendCacheService {
  private static readonly NAMESPACE = 'signalpilot-ai-internal';
  private static serverSettings: ServerConnection.ISettings;

  /**
   * Initialize the backend cache service
   */
  public static initialize(serverSettings?: ServerConnection.ISettings): void {
    BackendCacheService.serverSettings =
      serverSettings || ServerConnection.makeSettings();
  }

  /**
   * Get the server settings, creating default ones if not initialized
   */
  private static getServerSettings(): ServerConnection.ISettings {
    if (!BackendCacheService.serverSettings) {
      BackendCacheService.serverSettings = ServerConnection.makeSettings();
    }
    return BackendCacheService.serverSettings;
  }

  /**
   * Make a request to the backend cache API
   */
  private static async makeRequest(
    endpoint: string,
    method: 'GET' | 'POST' | 'DELETE' = 'GET',
    body?: any
  ): Promise<any> {
    const settings = BackendCacheService.getServerSettings();
    const url = URLExt.join(
      settings.baseUrl,
      'signalpilot-ai-internal',
      'cache',
      endpoint
    );

    const requestInit: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    if (body !== undefined) {
      requestInit.body = JSON.stringify(body);
    }

    try {
      const response = await ServerConnection.makeRequest(
        url,
        requestInit,
        settings
      );

      if (!response.ok) {
        const errorText = await response.text();
        console.error(
          `Backend cache request failed: ${response.status} ${errorText}`
        );
        throw new Error(`Cache request failed: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Backend cache service error for ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * Determine if a key should be stored as chat history or app value
   */
  private static isChatHistoryKey(key: string): boolean {
    const chatKeys = [
      'chatHistories',
      'chat-history-notebook-',
      'chat-thread-',
      'chat-message-'
    ];
    return chatKeys.some(prefix => key.includes(prefix));
  }

  /**
   * Get a value from the backend cache
   * @param key The setting key
   * @param defaultValue The default value if setting doesn't exist
   * @returns The setting value or default
   */
  public static async getValue<T>(key: string, defaultValue: T): Promise<T> {
    try {
      if (BackendCacheService.isChatHistoryKey(key)) {
        // Handle chat history keys
        if (key === 'chatHistories') {
          const response =
            await BackendCacheService.makeRequest('chat-histories');
          return (response.chat_histories || defaultValue) as T;
        } else {
          // Individual chat history
          const response = await BackendCacheService.makeRequest(
            `chat-histories/${encodeURIComponent(key)}`
          );
          return (response.history || defaultValue) as T;
        }
      } else {
        // Handle app values
        const response = await BackendCacheService.makeRequest(
          `app-values/${encodeURIComponent(key)}`
        );
        return (
          response.value !== undefined && response.value !== null
            ? response.value
            : defaultValue
        ) as T;
      }
    } catch (error) {
      console.warn(
        `[BackendCacheService] Failed to get value '${key}':`,
        error
      );
      return defaultValue;
    }
  }

  /**
   * Set a value in the backend cache
   * @param key The setting key
   * @param value The value to set
   */
  public static async setValue(
    key: string,
    value: PartialJSONValue
  ): Promise<void> {
    try {
      if (BackendCacheService.isChatHistoryKey(key)) {
        // Handle chat history keys
        if (key === 'chatHistories') {
          await BackendCacheService.makeRequest('chat-histories', 'POST', {
            chat_histories: value
          });
        } else {
          // Individual chat history
          await BackendCacheService.makeRequest(
            `chat-histories/${encodeURIComponent(key)}`,
            'POST',
            {
              history: value
            }
          );
        }
      } else {
        // Handle app values
        await BackendCacheService.makeRequest(
          `app-values/${encodeURIComponent(key)}`,
          'POST',
          {
            value: value
          }
        );
      }
    } catch (error) {
      console.error(
        `[BackendCacheService] Failed to set value '${key}':`,
        error
      );
      throw error;
    }
  }

  /**
   * Remove a value from the backend cache
   * @param key The setting key to remove
   */
  public static async removeValue(key: string): Promise<void> {
    try {
      if (BackendCacheService.isChatHistoryKey(key)) {
        // Handle chat history keys
        if (key === 'chatHistories') {
          await BackendCacheService.makeRequest('chat-histories', 'DELETE');
        } else {
          // Individual chat history
          await BackendCacheService.makeRequest(
            `chat-histories/${encodeURIComponent(key)}`,
            'DELETE'
          );
        }
      } else {
        // Handle app values
        await BackendCacheService.makeRequest(
          `app-values/${encodeURIComponent(key)}`,
          'DELETE'
        );
      }
    } catch (error) {
      console.error(
        `[BackendCacheService] Failed to remove value '${key}':`,
        error
      );
      throw error;
    }
  }

  /**
   * Get an object value (for complex data like arrays, objects)
   */
  public static async getObjectValue<T>(
    key: string,
    defaultValue: T
  ): Promise<T> {
    return BackendCacheService.getValue(key, defaultValue);
  }

  /**
   * Set an object value (for complex data like arrays, objects)
   */
  public static async setObjectValue<T>(key: string, value: T): Promise<void> {
    return BackendCacheService.setValue(key, value as PartialJSONValue);
  }

  /**
   * Check if the backend cache service is available
   */
  public static async isAvailable(): Promise<boolean> {
    try {
      const response = await BackendCacheService.makeRequest('info');
      return response.available === true;
    } catch (error) {
      console.warn(
        '[BackendCacheService] Service availability check failed:',
        error
      );
      return false;
    }
  }

  /**
   * List all keys in the namespace (for debugging purposes)
   */
  public static async listKeys(): Promise<string[]> {
    try {
      const [chatResponse, appResponse] = await Promise.all([
        BackendCacheService.makeRequest('chat-histories'),
        BackendCacheService.makeRequest('app-values')
      ]);

      const chatKeys = Object.keys(chatResponse.chat_histories || {});
      const appKeys = Object.keys(appResponse.app_values || {});

      return [...chatKeys, ...appKeys];
    } catch (error) {
      console.error('[BackendCacheService] Failed to list keys:', error);
      return [];
    }
  }

  /**
   * Get cache service information
   */
  public static async getCacheInfo(): Promise<any> {
    try {
      return await BackendCacheService.makeRequest('info');
    } catch (error) {
      console.error('[BackendCacheService] Failed to get cache info:', error);
      return {
        available: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }
}

// State DB key constants for chat-related data (kept for compatibility)
export const STATE_DB_KEYS = {
  // Chat settings
  CHAT_HISTORIES: 'chatHistories',
  // Checkpoint data
  NOTEBOOK_CHECKPOINTS: 'notebookCheckpoints',
  // Error logging
  ERROR_LOGS: 'errorLogs',
  // Snippets
  SNIPPETS: 'snippets',
  // Inserted snippets
  INSERTED_SNIPPETS: 'insertedSnippets',
  // Authentication
  JWT_TOKEN: 'jupyter_auth_jwt',
  // Welcome tour
  WELCOME_TOUR_COMPLETED: 'welcomeTourCompleted',
  // Demo mode
  IS_DEMO_MODE: 'isDemoMode'
} as const;

// Alias for backward compatibility
export const StateDBCachingService = BackendCacheService;
