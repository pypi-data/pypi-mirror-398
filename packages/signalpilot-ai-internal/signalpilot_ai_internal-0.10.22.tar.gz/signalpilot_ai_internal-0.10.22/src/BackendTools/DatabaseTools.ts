import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

/**
 * Database types supported by the system
 */
export enum DatabaseType {
  PostgreSQL = 'postgresql',
  MySQL = 'mysql',
  Snowflake = 'snowflake',
  Databricks = 'databricks'
}

export interface ISchemaSearchOptions {
  queries: string[];
  limit?: number;
  dbUrl?: string;
}

/**
 * Tools for interacting with database systems via API service
 */
export class DatabaseTools {
  constructor() {
    // No initialization needed
  }

  /**
   * Detect database type from connection URL
   */
  private detectDatabaseType(dbUrl?: string): DatabaseType {
    if (!dbUrl) {
      return DatabaseType.PostgreSQL; // Default
    }

    const lowerUrl = dbUrl.toLowerCase();

    if (lowerUrl.startsWith('mysql')) {
      return DatabaseType.MySQL;
    } else if (lowerUrl.startsWith('snowflake')) {
      return DatabaseType.Snowflake;
    } else if (
      lowerUrl.startsWith('databricks') ||
      lowerUrl.includes('databricks.net') ||
      lowerUrl.includes('azuredatabricks.net')
    ) {
      return DatabaseType.Databricks;
    } else if (
      lowerUrl.startsWith('postgresql') ||
      lowerUrl.startsWith('postgres')
    ) {
      return DatabaseType.PostgreSQL;
    }

    return DatabaseType.PostgreSQL; // Default
  }

  /**
   * Get the base URL for the database API
   */
  private getApiBaseUrl(
    dbType: DatabaseType = DatabaseType.PostgreSQL
  ): string {
    const settings = ServerConnection.makeSettings();
    if (dbType === DatabaseType.Snowflake) {
      return URLExt.join(settings.baseUrl, 'signalpilot-ai-internal', 'snowflake');
    }
    if (dbType === DatabaseType.MySQL) {
      return URLExt.join(settings.baseUrl, 'signalpilot-ai-internal', 'mysql');
    }
    if (dbType === DatabaseType.Databricks) {
      return URLExt.join(settings.baseUrl, 'signalpilot-ai-internal', 'databricks');
    }
    return URLExt.join(settings.baseUrl, 'signalpilot-ai-internal', 'database');
  }

  /**
   * Make an authenticated API request
   */
  private async makeApiRequest(
    endpoint: string,
    body: any,
    dbType: DatabaseType = DatabaseType.PostgreSQL
  ): Promise<any> {
    const settings = ServerConnection.makeSettings();
    const url = URLExt.join(this.getApiBaseUrl(dbType), endpoint);

    const response = await ServerConnection.makeRequest(
      url,
      {
        method: 'POST',
        body: JSON.stringify(body),
        headers: {
          'Content-Type': 'application/json'
        }
      },
      settings
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        error: `HTTP ${response.status}: ${response.statusText}`
      }));
      throw new Error(
        errorData.error || `API request failed: ${response.statusText}`
      );
    }

    return await response.json();
  }

  /**
   * Run schema_search against the backend service to find matching tables.
   * @param options.queries One or more natural language or identifier queries.
   * @param options.limit Optional maximum number of results per query (defaults to 5, capped at 10).
   * @param options.dbUrl Optional database connection string to override the environment configuration.
   */
  async schemaSearch(options: ISchemaSearchOptions): Promise<any> {
    const queries = (options.queries || [])
      .map(query => (typeof query === 'string' ? query.trim() : ''))
      .filter(query => query.length > 0);

    if (queries.length === 0) {
      throw new Error('At least one query is required');
    }

    const boundedLimit = Math.min(Math.max(options.limit ?? 5, 1), 10);
    const body: any = {
      queries,
      limit: boundedLimit
    };

    if (options.dbUrl) {
      body.dbUrl = options.dbUrl.trim();
    }

    return this.makeApiRequest('schema-search', body, DatabaseType.PostgreSQL);
  }

  /**
   * Get database metadata as a formatted text string by calling the API
   * @param dbUrl Database connection string (optional, will use environment if not provided)
   * @param dbType Database type (PostgreSQL, MySQL, Snowflake, or Databricks) - auto-detected from URL if not provided
   * @param config For Snowflake/Databricks: configuration object with connectionUrl, credentials, etc.
   * @param databases For Snowflake: array of specific databases to query (optional)
   * @returns Promise<string> Formatted database metadata text
   */
  async getDatabaseMetadataAsText(
    dbUrl?: string,
    dbType?: DatabaseType,
    config?: any,
    databases?: string[]
  ): Promise<string> {
    try {
      // Auto-detect database type if not provided
      if (!dbType) {
        dbType = this.detectDatabaseType(dbUrl);
      }

      console.log(`[DatabaseTools] Fetching ${dbType} schema info via API...`);

      const requestBody: any = {};

      if (dbType === DatabaseType.Snowflake) {
        // For Snowflake, use config object
        if (config) {
          requestBody.config = config;
        }
        if (databases && databases.length > 0) {
          requestBody.databases = databases;
        }
      } else if (dbType === DatabaseType.Databricks) {
        // For Databricks, use config object
        if (config) {
          requestBody.config = config;
        }
      } else {
        // For PostgreSQL/MySQL, use dbUrl (backend will auto-detect)
        if (dbUrl) {
          requestBody.dbUrl = dbUrl;
        }
      }

      const result = await this.makeApiRequest('schema', requestBody, dbType);

      if (result.error) {
        return `Error: ${result.error}`;
      }

      console.log(
        `[DatabaseTools] ${dbType} schema info retrieved successfully`
      );
      return JSON.stringify(result);
    } catch (error) {
      console.error(
        `[DatabaseTools] Error getting ${dbType} schema info:`,
        error
      );
      return `Error: ${error instanceof Error ? error.message : String(error)}`;
    }
  }

  /**
   * Get database metadata as structured JSON
   * @param dbUrl Database connection string (optional, will use environment if not provided)
   * @param dbType Database type (PostgreSQL, MySQL, or Snowflake) - auto-detected from URL if not provided
   * @param config For Snowflake: configuration object
   * @param databases For Snowflake: array of specific databases to query (optional)
   * @returns Promise<string> JSON string with database metadata
   */
  async getDatabaseMetadata(
    dbUrl?: string,
    dbType?: DatabaseType,
    config?: any,
    databases?: string[]
  ): Promise<string> {
    try {
      const textResult = await this.getDatabaseMetadataAsText(
        dbUrl,
        dbType,
        config,
        databases
      );

      if (textResult.startsWith('Error:')) {
        return JSON.stringify({
          error: textResult
        });
      }

      return JSON.stringify({
        schema_info: textResult,
        db_url_configured: !!dbUrl || !!config || !!process.env.DB_URL
      });
    } catch (error) {
      console.error('[DatabaseTools] Error getting database metadata:', error);
      return JSON.stringify({
        error: `Failed to get database metadata: ${error instanceof Error ? error.message : String(error)}`
      });
    }
  }

  /**
   * Execute a read-only SQL query via the API
   * @param query SQL query to execute
   * @param dbUrl Optional database URL (will use environment if not provided)
   * @param dbType Database type (PostgreSQL, MySQL, Snowflake, or Databricks) - auto-detected from URL if not provided
   * @param config For Snowflake/Databricks: configuration object
   * @param database For Snowflake/Databricks: specific database/catalog to query
   * @returns Promise<string> JSON string with query results
   */
  async executeQuery(
    query: string,
    dbUrl?: string,
    dbType?: DatabaseType,
    config?: any,
    database?: string
  ): Promise<string> {
    try {
      // Auto-detect database type if not provided
      if (!dbType) {
        dbType = this.detectDatabaseType(dbUrl);
      }

      console.log(
        `[DatabaseTools] Executing SQL query via API on ${dbType}...`
      );

      // Basic validation for read-only queries
      const normalizedQuery = query.trim().toUpperCase();
      const allowedStarts = ['SELECT', 'WITH'];

      // Snowflake and Databricks allow additional read-only commands
      if (
        dbType === DatabaseType.Snowflake ||
        dbType === DatabaseType.Databricks
      ) {
        allowedStarts.push('SHOW', 'DESCRIBE', 'EXPLAIN');
      }

      if (!allowedStarts.some(start => normalizedQuery.startsWith(start))) {
        return JSON.stringify({
          error: `Only ${allowedStarts.join(', ')} statements are allowed for read queries.`
        });
      }

      const requestBody: any = { query };

      if (dbType === DatabaseType.Snowflake) {
        // For Snowflake, use config object
        if (config) {
          requestBody.config = config;
        }
        if (database) {
          requestBody.database = database;
        }
      } else if (dbType === DatabaseType.Databricks) {
        // For Databricks, use config object
        if (config) {
          requestBody.config = config;
        }
        if (database) {
          requestBody.catalog = database;
        }
      } else {
        // For PostgreSQL/MySQL, use dbUrl (backend will auto-detect)
        if (dbUrl) {
          requestBody.dbUrl = dbUrl;
        }
      }

      const result = await this.makeApiRequest('query', requestBody, dbType);

      console.log(`[DatabaseTools] Query executed successfully on ${dbType}`);
      return JSON.stringify(result);
    } catch (error) {
      console.error(
        `[DatabaseTools] Error executing SQL query on ${dbType}:`,
        error
      );
      return JSON.stringify({
        error: `Failed to execute SQL query: ${error instanceof Error ? error.message : String(error)}`
      });
    }
  }
}
