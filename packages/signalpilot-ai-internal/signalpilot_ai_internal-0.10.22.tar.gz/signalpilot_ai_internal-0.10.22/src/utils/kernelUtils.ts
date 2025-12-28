import { AppStateService } from '../AppState';
import { KernelPreviewUtils } from './kernelPreview';
import { DatabaseStateService, IDatabaseConfig } from '../DatabaseStateService';

/**
 * Utility functions for kernel operations
 */
export class KernelUtils {
  /**
   * Set database environment variables for all configured databases in the current kernel
   * Each database gets environment variables in format: {DB_NAME}_{CONNECTION_DETAILS}
   * Connection details are stored as JSON strings containing host, port, username, password, etc.
   */
  static setDatabaseEnvironmentsInKernel(): void {
    try {
      const toolService = AppStateService.getToolService();
      const kernel = toolService?.getCurrentNotebook()?.kernel;

      if (!kernel) {
        console.warn(
          '[KernelUtils] No kernel available to set database environments'
        );
        return;
      }

      // Get all database configurations from DatabaseStateService
      const databaseConfigs = DatabaseStateService.getConfigurations();

      console.log(
        `[KernelUtils] Setting environment variables for ${databaseConfigs.length} database configurations`
      );

      if (databaseConfigs.length === 0) {
        console.log('[KernelUtils] No database configurations found');
        // Clean up any existing database environment variables
        const cleanupCode = `
import os
import json

# Remove any existing database environment variables
db_env_vars = [key for key in os.environ.keys() if '_HOST' in key or '_PORT' in key or '_DATABASE' in key or '_USERNAME' in key or '_PASSWORD' in key or '_CONNECTION_JSON' in key]
for var in db_env_vars:
    if var.startswith(('DB_', 'DATABASE_')):
        del os.environ[var]

print("[KernelUtils] Cleaned up existing database environment variables")
        `;
        kernel.requestExecute({ code: cleanupCode, silent: true });
        return;
      }

      // Generate Python code to set environment variables for all databases
      let code = `
import os
import json

print("[KernelUtils] Setting database environment variables...")

`;

      databaseConfigs.forEach((config: IDatabaseConfig) => {
        const dbName = config.name.toUpperCase().replace(/[^A-Z0-9]/g, '_');

        if (config.connectionType === 'credentials' && config.credentials) {
          const creds = config.credentials;

          // Set individual connection detail environment variables
          code += `
# Database: ${config.name} (${config.type})
os.environ['${dbName}_HOST'] = '${creds.host.replace(/'/g, "\\'")}'
os.environ['${dbName}_PORT'] = '${creds.port}'
os.environ['${dbName}_DATABASE'] = '${creds.database.replace(/'/g, "\\'")}'
os.environ['${dbName}_USERNAME'] = '${creds.username.replace(/'/g, "\\'")}'
os.environ['${dbName}_PASSWORD'] = '${creds.password.replace(/'/g, "\\'")}'
os.environ['${dbName}_TYPE'] = '${creds.type}'
`;

          // Add Snowflake-specific variables
          if (config.type === 'snowflake' && 'connectionUrl' in creds) {
            const connectionUrl = (creds as any).connectionUrl;
            code += `os.environ['${dbName}_CONNECTION_URL'] = '${connectionUrl.replace(/'/g, "\\'")}'
`;

            // Extract account from connection URL (e.g., qfmxivq-do76898 from https://qfmxivq-do76898.snowflakecomputing.com)
            const accountMatch = connectionUrl.match(/https?:\/\/([^./]+)/);
            if (accountMatch && accountMatch[1]) {
              const account = accountMatch[1];
              code += `os.environ['${dbName}_ACCOUNT'] = '${account.replace(/'/g, "\\'")}'
`;
            }

            if ('warehouse' in creds && (creds as any).warehouse) {
              code += `os.environ['${dbName}_WAREHOUSE'] = '${((creds as any).warehouse as string).replace(/'/g, "\\'")}'
`;
            }
            if ('role' in creds && (creds as any).role) {
              code += `os.environ['${dbName}_ROLE'] = '${((creds as any).role as string).replace(/'/g, "\\'")}'
`;
            }
          }

          // Add Databricks-specific variables
          if (config.type === 'databricks' && 'connectionUrl' in creds) {
            const connectionUrl = (creds as any).connectionUrl;
            code += `os.environ['${dbName}_CONNECTION_URL'] = '${connectionUrl.replace(/'/g, "\\'")}'
`;

            if ('authType' in creds) {
              code += `os.environ['${dbName}_AUTH_TYPE'] = '${((creds as any).authType as string).replace(/'/g, "\\'")}'
`;
            }
            if ('accessToken' in creds && (creds as any).accessToken) {
              code += `os.environ['${dbName}_ACCESS_TOKEN'] = '${((creds as any).accessToken as string).replace(/'/g, "\\'")}'
`;
            }
            if ('clientId' in creds && (creds as any).clientId) {
              code += `os.environ['${dbName}_CLIENT_ID'] = '${((creds as any).clientId as string).replace(/'/g, "\\'")}'
`;
            }
            if ('clientSecret' in creds && (creds as any).clientSecret) {
              code += `os.environ['${dbName}_CLIENT_SECRET'] = '${((creds as any).clientSecret as string).replace(/'/g, "\\'")}'
`;
            }
            if ('oauthTokenUrl' in creds && (creds as any).oauthTokenUrl) {
              code += `os.environ['${dbName}_OAUTH_TOKEN_URL'] = '${((creds as any).oauthTokenUrl as string).replace(/'/g, "\\'")}'
`;
            }
            if ('warehouseId' in creds && (creds as any).warehouseId) {
              code += `os.environ['${dbName}_WAREHOUSE_ID'] = '${((creds as any).warehouseId as string).replace(/'/g, "\\'")}'
`;
            }
            if ('warehouseHttpPath' in creds && (creds as any).warehouseHttpPath) {
              code += `os.environ['${dbName}_WAREHOUSE_HTTP_PATH'] = '${((creds as any).warehouseHttpPath as string).replace(/'/g, "\\'")}'
`;
            }
            if ('catalog' in creds && (creds as any).catalog) {
              code += `os.environ['${dbName}_CATALOG'] = '${((creds as any).catalog as string).replace(/'/g, "\\'")}'
`;
            }
            if ('schema' in creds && (creds as any).schema) {
              code += `os.environ['${dbName}_SCHEMA'] = '${((creds as any).schema as string).replace(/'/g, "\\'")}'
`;
            }
          }

          // Set JSON connection details
          const connectionJson = {
            id: config.id,
            name: config.name,
            type: config.type,
            host: creds.host,
            port: creds.port,
            database: creds.database,
            username: creds.username,
            password: creds.password,
            ...(config.type === 'snowflake' && 'connectionUrl' in creds
              ? {
                  connectionUrl: (creds as any).connectionUrl,
                  ...('warehouse' in creds && (creds as any).warehouse
                    ? { warehouse: (creds as any).warehouse }
                    : {}),
                  ...('role' in creds && (creds as any).role
                    ? { role: (creds as any).role }
                    : {})
                }
              : {}),
            ...(config.type === 'databricks' && 'connectionUrl' in creds
              ? {
                  connectionUrl: (creds as any).connectionUrl,
                  ...('authType' in creds
                    ? { authType: (creds as any).authType }
                    : {}),
                  ...('accessToken' in creds && (creds as any).accessToken
                    ? { accessToken: (creds as any).accessToken }
                    : {}),
                  ...('clientId' in creds && (creds as any).clientId
                    ? { clientId: (creds as any).clientId }
                    : {}),
                  ...('clientSecret' in creds && (creds as any).clientSecret
                    ? { clientSecret: (creds as any).clientSecret }
                    : {}),
                  ...('oauthTokenUrl' in creds && (creds as any).oauthTokenUrl
                    ? { oauthTokenUrl: (creds as any).oauthTokenUrl }
                    : {}),
                  ...('warehouseId' in creds && (creds as any).warehouseId
                    ? { warehouseId: (creds as any).warehouseId }
                    : {}),
                  ...('warehouseHttpPath' in creds && (creds as any).warehouseHttpPath
                    ? { warehouseHttpPath: (creds as any).warehouseHttpPath }
                    : {}),
                  ...('catalog' in creds && (creds as any).catalog
                    ? { catalog: (creds as any).catalog }
                    : {}),
                  ...('schema' in creds && (creds as any).schema
                    ? { schema: (creds as any).schema }
                    : {})
                }
              : {})
          };

          code += `os.environ['${dbName}_CONNECTION_JSON'] = '''${JSON.stringify(connectionJson).replace(/'/g, "\\'")}'''
`;
        } else if (config.connectionType === 'url' && config.urlConnection) {
          // For URL-based connections, store the URL and parse basic info
          const urlConn = config.urlConnection;

          code += `
# Database: ${config.name} (${config.type} - URL)
os.environ['${dbName}_CONNECTION_URL'] = '${urlConn.connectionUrl.replace(/'/g, "\\'")}'
os.environ['${dbName}_TYPE'] = '${urlConn.type}'
`;

          const connectionJson = {
            id: config.id,
            name: config.name,
            type: config.type,
            connectionUrl: urlConn.connectionUrl
          };

          code += `os.environ['${dbName}_CONNECTION_JSON'] = '''${JSON.stringify(connectionJson).replace(/'/g, "\\'")}'''
`;
        }

        code += `print(f"[KernelUtils] Set environment variables for database: ${config.name}")
`;
      });

      code += `
print(f"[KernelUtils] Database environment setup complete. Total databases: ${databaseConfigs.length}")
`;

      console.log(
        '[KernelUtils] Setting database environment variables in kernel'
      );
      kernel.requestExecute({ code, silent: true });
    } catch (error) {
      console.error(
        '[KernelUtils] Error setting database environments in kernel:',
        error
      );
    }
  }

  /**
   * Set database environments with retry mechanism for when kernel is not ready
   * @param maxRetries Maximum number of retry attempts
   * @param delay Delay between retries in ms
   */
  static async setDatabaseEnvironmentsInKernelWithRetry(
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<void> {
    if (this.isRetrying) {
      console.log(
        '[KernelUtils] Already retrying database environment setup, skipping duplicate attempt'
      );
      return;
    }

    this.isRetrying = true;
    console.log(
      '[KernelUtils] Starting database environments retry process...'
    );

    try {
      for (let i = 0; i < maxRetries; i++) {
        try {
          const toolService = AppStateService.getToolService();
          const kernel = toolService?.getCurrentNotebook()?.kernel;

          if (kernel) {
            console.log(
              `[KernelUtils] Kernel available on attempt ${i + 1}, setting database environments`
            );
            this.setDatabaseEnvironmentsInKernel();
            console.log(
              '[KernelUtils] Database environments retry process completed successfully'
            );
            return;
          } else {
            console.log(
              `[KernelUtils] Kernel not ready, attempt ${i + 1}/${maxRetries}, waiting ${delay}ms...`
            );
            if (i < maxRetries - 1) {
              await new Promise(resolve => setTimeout(resolve, delay));
            }
          }
        } catch (error) {
          console.error(`[KernelUtils] Error on attempt ${i + 1}:`, error);
          if (i < maxRetries - 1) {
            await new Promise(resolve => setTimeout(resolve, delay));
          }
        }
      }

      console.warn(
        '[KernelUtils] Failed to set database environments after all retry attempts'
      );
    } finally {
      this.isRetrying = false;
    }
  }

  /**
   * @deprecated Use setDatabaseEnvironmentsInKernel() instead
   * Set DB_URL environment variable in the current kernel
   * @param databaseUrl The database URL to set, or null to use from AppState
   */
  static setDbUrlInKernel(databaseUrl?: string | null): void {
    try {
      // Get database URL from parameter or AppState
      const dbUrl =
        databaseUrl ?? AppStateService.getState().settings.databaseUrl;

      console.log(
        '[KernelUtils] Attempting to set DB_URL in kernel:',
        dbUrl ? 'configured' : 'not configured'
      );
      console.log('[KernelUtils] Database URL value:', dbUrl);

      const toolService = AppStateService.getToolService();
      const kernel = toolService?.getCurrentNotebook()?.kernel;

      if (!kernel) {
        console.warn('[KernelUtils] No kernel available to set DB_URL');
        return;
      }

      if (dbUrl && dbUrl.trim() !== '') {
        const code = `
import os
os.environ['DB_URL'] = '${dbUrl.replace(/'/g, "\\'")}'
print(f"[KernelUtils] DB_URL environment variable set: {os.environ.get('DB_URL', 'Not set')}")
        `;

        console.log(
          '[KernelUtils] Setting DB_URL environment variable in kernel. URL:',
          dbUrl.length > 50 ? dbUrl.substring(0, 50) + '...' : dbUrl
        );
        kernel.requestExecute({ code, silent: true });
      } else {
        // Remove DB_URL if empty
        const code = `
import os
if 'DB_URL' in os.environ:
    del os.environ['DB_URL']
    print("[KernelUtils] DB_URL environment variable removed")
else:
    print("[KernelUtils] DB_URL environment variable was not set")
        `;

        console.log(
          '[KernelUtils] Removing DB_URL environment variable from kernel'
        );
        kernel.requestExecute({ code, silent: true });
      }
    } catch (error) {
      console.error('[KernelUtils] Error setting DB_URL in kernel:', error);
    }
  }

  /**
   * Check current DB_URL in kernel
   */
  static checkDbUrlInKernel(): void {
    try {
      const toolService = AppStateService.getToolService();
      const kernel = toolService?.getCurrentNotebook()?.kernel;

      if (!kernel) {
        console.warn('[KernelUtils] No kernel available to check DB_URL');
        return;
      }

      const code = `
import os
db_url = os.environ.get('DB_URL')
print(f"[KernelUtils Check] Current DB_URL: {db_url}")
if db_url:
    print(f"[KernelUtils Check] DB_URL length: {len(db_url)}")
    print(f"[KernelUtils Check] DB_URL starts with: {db_url[:50]}...")
else:
    print("[KernelUtils Check] DB_URL is not set")
      `;

      console.log('[KernelUtils] Checking current DB_URL in kernel');
      kernel.requestExecute({ code, silent: true });
    } catch (error) {
      console.error('[KernelUtils] Error checking DB_URL in kernel:', error);
    }
  }

  /**
   * Debug AppState database URL
   */
  static debugAppStateDatabaseUrl(): void {
    try {
      const appState = AppStateService.getState();
      console.log('[KernelUtils] AppState settings:', appState.settings);
      console.log(
        '[KernelUtils] Database URL from AppState:',
        appState.settings.databaseUrl
      );
      console.log(
        '[KernelUtils] Database URL type:',
        typeof appState.settings.databaseUrl
      );
      console.log(
        '[KernelUtils] Database URL length:',
        appState.settings.databaseUrl?.length
      );
    } catch (error) {
      console.error('[KernelUtils] Error debugging AppState:', error);
    }
  }

  // Guard to prevent multiple simultaneous retry attempts
  private static isRetrying = false;

  /**
   * @deprecated Use setDatabaseEnvironmentsInKernelWithRetry() instead
   * Set DB_URL with retry mechanism for when kernel is not ready
   * @param databaseUrl The database URL to set
   * @param maxRetries Maximum number of retry attempts
   * @param delay Delay between retries in ms
   */
  static async setDbUrlInKernelWithRetry(
    databaseUrl?: string | null,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<void> {
    if (this.isRetrying) {
      console.log(
        '[KernelUtils] Already retrying DB_URL setup, skipping duplicate attempt'
      );
      return;
    }

    this.isRetrying = true;
    console.log('[KernelUtils] Starting DB_URL retry process...');
    this.debugAppStateDatabaseUrl();

    try {
      for (let i = 0; i < maxRetries; i++) {
        try {
          const toolService = AppStateService.getToolService();
          const kernel = toolService?.getCurrentNotebook()?.kernel;

          if (kernel) {
            console.log(
              `[KernelUtils] Kernel available on attempt ${i + 1}, setting DB_URL`
            );
            this.setDbUrlInKernel(databaseUrl);
            console.log(
              '[KernelUtils] DB_URL retry process completed successfully'
            );
            return;
          } else {
            console.log(
              `[KernelUtils] Kernel not ready, attempt ${i + 1}/${maxRetries}, waiting ${delay}ms...`
            );
            if (i < maxRetries - 1) {
              await new Promise(resolve => setTimeout(resolve, delay));
            }
          }
        } catch (error) {
          console.error(`[KernelUtils] Error on attempt ${i + 1}:`, error);
          if (i < maxRetries - 1) {
            await new Promise(resolve => setTimeout(resolve, delay));
          }
        }
      }

      console.warn(
        '[KernelUtils] Failed to set DB_URL after all retry attempts'
      );
    } finally {
      this.isRetrying = false;
    }
  }

  /**
   * Gets a preview of all variables, dicts, and objects in the current kernel
   */
  static async getKernelPreview(): Promise<string | null> {
    return KernelPreviewUtils.getKernelPreview();
  }
}
