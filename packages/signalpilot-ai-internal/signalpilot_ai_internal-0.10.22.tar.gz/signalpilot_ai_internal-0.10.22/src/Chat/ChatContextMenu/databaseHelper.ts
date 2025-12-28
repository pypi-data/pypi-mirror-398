/**
 * Database helper utilities for context menu integration
 */
import {
  DatabaseStateService,
  IDatabaseConfig,
  DatabaseType,
  IMySQLPostgreSQLSchema,
  ISnowflakeSchemaData
} from '../../DatabaseStateService';
import { IMentionContext } from './ChatContextLoaders';

/**
 * Interface for database context items in the context picker
 */
export interface IDatabaseContext extends IMentionContext {
  type: 'database';
  databaseType: DatabaseType;
  connectionType: 'credentials' | 'url';
  isActive: boolean;
}

/**
 * Get database type display name
 */
function getDatabaseTypeDisplayName(type: DatabaseType): string {
  switch (type) {
    case DatabaseType.PostgreSQL:
      return 'PostgreSQL';
    case DatabaseType.MySQL:
      return 'MySQL';
    case DatabaseType.Snowflake:
      return 'Snowflake';
    default:
      return 'Database';
  }
}

/**
 * Get database description from configuration
 */
function getDatabaseDescription(config: IDatabaseConfig): string {
  if (config.connectionType === 'url' && config.urlConnection) {
    return config.urlConnection.description;
  } else if (config.connectionType === 'credentials' && config.credentials) {
    return config.credentials.description;
  }
  return '';
}

/**
 * Create database context content for the mention system
 */
function createDatabaseContextContent(config: IDatabaseConfig): string {
  let content = `${config.name}\n\n`;

  // Add description if available
  const description = getDatabaseDescription(config);
  if (description && description.trim()) {
    content += 'DESCRIPTION\n';
    content += '===========\n';
    content += `${description.trim()}\n\n`;
  }

  // Add table list if database schema is available
  if (config.database_schema) {
    content += 'TABLES\n';
    content += '======\n';

    // Handle different schema formats
    if ('table_schemas' in config.database_schema) {
      // MySQL/PostgreSQL schema format
      const schema = config.database_schema as IMySQLPostgreSQLSchema;
      const tableNames = Object.keys(schema.table_schemas);
      if (tableNames.length > 0) {
        tableNames.forEach(tableName => {
          const tableSchema = schema.table_schemas[tableName];
          content += `${tableSchema.table_name}\n`;
        });
      } else {
        content += 'No tables found\n';
      }
    } else if ('databases' in config.database_schema) {
      // Snowflake schema format
      const schema = config.database_schema as ISnowflakeSchemaData;
      const databases = schema.databases;
      databases.forEach(db => {
        db.schemas.forEach(schema => {
          if (!schema.error && schema.tables.length > 0) {
            schema.tables.forEach(table => {
              content += `${db.database}.${schema.schema}.${table.table}\n`;
            });
          }
        });
      });

      // Check if no tables were found
      const totalTables = databases.reduce(
        (sum, db) =>
          sum +
          db.schemas.reduce(
            (schemaSum, schema) =>
              schemaSum + (schema.error ? 0 : schema.tables.length),
            0
          ),
        0
      );

      if (totalTables === 0) {
        content += 'No tables found\n';
      }
    }
  } else {
    content += 'TABLES\n';
    content += '======\n';
    content += 'Schema not loaded - refresh schema to see tables\n';
  }

  return content;
}

/**
 * Get all database configurations as MentionContext items for the context picker
 * This function retrieves database configurations from DatabaseStateService
 * and formats them for use in the chat context menu
 *
 * @returns Array of IDatabaseContext items ready for the context picker
 */
export async function getDatabases(): Promise<IDatabaseContext[]> {
  console.log('[DatabaseHelper] Loading database configurations...');

  try {
    // Get all database configurations from the service
    const configurations = DatabaseStateService.getConfigurations();
    const activeConfigId = DatabaseStateService.getState().activeConfigId;

    console.log(
      `[DatabaseHelper] Found ${configurations.length} database configurations`
    );

    // Convert database configs to context items
    const databaseContexts: IDatabaseContext[] = configurations.map(config => {
      const typeDisplayName = getDatabaseTypeDisplayName(config.type);
      const isActive = config.id === activeConfigId;

      // Create a concise description for the context picker
      let description =
        getDatabaseDescription(config) ||
        `${typeDisplayName} database connection`;
      if (description.length > 80) {
        description = description.substring(0, 77) + '...';
      }

      // Add connection type and active status to description
      const statusInfo = [];
      if (isActive) {
        statusInfo.push('Active');
      }
      statusInfo.push(
        config.connectionType === 'url'
          ? 'URL Connection'
          : 'Credential Connection'
      );

      if (statusInfo.length > 0) {
        description += ` (${statusInfo.join(', ')})`;
      }

      return {
        type: 'database' as const,
        id: `database-${config.id}`,
        name: config.name,
        description,
        content: createDatabaseContextContent(config),
        databaseType: config.type,
        connectionType: config.connectionType,
        isActive,
        isDirectory: false
      };
    });

    // Sort databases: active first, then by name
    databaseContexts.sort((a, b) => {
      if (a.isActive && !b.isActive) {
        return -1;
      }
      if (!a.isActive && b.isActive) {
        return 1;
      }
      return a.name.localeCompare(b.name);
    });

    console.log(
      `[DatabaseHelper] Converted ${databaseContexts.length} database contexts`
    );
    return databaseContexts;
  } catch (error) {
    console.error(
      '[DatabaseHelper] Error loading database configurations:',
      error
    );
    return [];
  }
}

/**
 * Get a specific database configuration by ID for context usage
 *
 * @param databaseId The database configuration ID (without 'database-' prefix)
 * @returns IDatabaseContext item or null if not found
 */
export async function getDatabaseById(
  databaseId: string
): Promise<IDatabaseContext | null> {
  try {
    const config = DatabaseStateService.getConfiguration(databaseId);
    if (!config) {
      return null;
    }

    const activeConfigId = DatabaseStateService.getState().activeConfigId;
    const typeDisplayName = getDatabaseTypeDisplayName(config.type);
    const isActive = config.id === activeConfigId;

    let description =
      getDatabaseDescription(config) ||
      `${typeDisplayName} database connection`;
    if (description.length > 80) {
      description = description.substring(0, 77) + '...';
    }

    return {
      type: 'database' as const,
      id: `database-${config.id}`,
      name: config.name,
      description,
      content: createDatabaseContextContent(config),
      databaseType: config.type,
      connectionType: config.connectionType,
      isActive,
      isDirectory: false
    };
  } catch (error) {
    console.error(
      `[DatabaseHelper] Error loading database ${databaseId}:`,
      error
    );
    return null;
  }
}

/**
 * Refresh database contexts - useful when database configurations change
 * This function can be called to invalidate any caching and reload fresh data
 *
 * @returns Promise that resolves when refresh is complete
 */
export async function refreshDatabaseContexts(): Promise<void> {
  console.log('[DatabaseHelper] Refreshing database contexts...');
  // Since we're reading directly from DatabaseStateService, no caching to clear
  // This function serves as a placeholder for future caching mechanisms
  return Promise.resolve();
}

/**
 * Check if databases are available for context
 *
 * @returns true if there are database configurations available
 */
export function hasDatabases(): boolean {
  const configurations = DatabaseStateService.getConfigurations();
  return configurations.length > 0;
}
