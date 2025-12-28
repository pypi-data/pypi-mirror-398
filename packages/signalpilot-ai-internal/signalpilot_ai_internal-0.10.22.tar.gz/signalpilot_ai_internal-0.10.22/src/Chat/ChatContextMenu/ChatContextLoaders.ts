/**
 * Constants and loading methods for chat context menu
 */
import { Contents } from '@jupyterlab/services';
import { ToolService } from '../../Services/ToolService';
import { DatabaseMetadataCache } from '../../Services/DatabaseMetadataCache';
import { KernelPreviewUtils } from '../../utils/kernelPreview';
import { AppStateService } from '../../AppState';
import { DataLoaderService } from './DataLoaderService';
import { DatabaseStateService } from '../../DatabaseStateService';

export interface IMentionContext {
  type:
    | 'snippets'
    | 'data'
    | 'variable'
    | 'cell'
    | 'directory'
    | 'table'
    | 'database';
  id: string;
  name: string;
  content?: string;
  description?: string;
  path?: string; // For directories and files, store the relative path
  isDirectory?: boolean; // Flag to indicate if this is a directory
  parentPath?: string; // For navigation back to parent
}

// Constants
export const VARIABLE_TYPE_BLACKLIST = [
  'module',
  'type',
  'function',
  'ZMQExitAutocall',
  'method'
];

export const VARIABLE_NAME_BLACKLIST = ['In', 'Out'];

export const MENTION_CATEGORIES = [
  {
    id: 'snippets',
    name: 'Rules',
    icon: '📄',
    description: 'Reusable code and prompt templates'
  },
  {
    id: 'data',
    name: 'Data',
    icon: '📊',
    description: 'Dataset references and info'
  },
  {
    id: 'database',
    name: 'Database',
    icon: '🗄️',
    description: 'Database connections and info'
  },
  {
    id: 'variables',
    name: 'Variables',
    icon: '🔤',
    description: 'Code variables and values'
  },
  {
    id: 'cells',
    name: 'Cells',
    icon: '📝',
    description: 'Notebook cell references'
  },
  {
    id: 'tables',
    name: 'Tables',
    icon: '📋',
    description: 'Database table references'
  }
];

/**
 * Class responsible for loading different types of context items
 */
export class ChatContextLoaders {
  private contentManager: Contents.IManager;
  private toolService: ToolService;

  constructor(contentManager: Contents.IManager, toolService: ToolService) {
    this.contentManager = contentManager;
    this.toolService = toolService;
  }

  /**
   * Initialize context items for each category
   */
  public async initializeContextItems(): Promise<
    Map<string, IMentionContext[]>
  > {
    const contextItems = new Map<string, IMentionContext[]>();

    // Load snippets from AppState (empty initially)
    contextItems.set('snippets', []);
    contextItems.set('data', []);
    contextItems.set('database', []);
    contextItems.set('variables', []);
    contextItems.set('cells', []);
    contextItems.set('tables', []);

    console.log(
      'All context items after initialization:',
      Array.from(contextItems.entries())
    ); // Debug log

    return contextItems;
  }

  /**
   * Load snippets from AppState
   */
  public async loadSnippets(): Promise<IMentionContext[]> {
    const snippets = AppStateService.getSnippets();
    return snippets.map(snippet => ({
      type: 'snippets' as const,
      id: snippet.id,
      name: snippet.title,
      description:
        snippet.description.length > 100
          ? snippet.description.substring(0, 100) + '...'
          : snippet.description,
      content: snippet.content
    }));
  }

  /**
   * Load datasets from the data directory using optimized Python kernel script
   * Supports directory traversal and shows directories at the top
   */
  public async loadDatasets(
    currentPath: string = './data'
  ): Promise<IMentionContext[]> {
    const datasetContexts: IMentionContext[] = [];

    // First, try to add database metadata from cache (never retry pulling it)
    // Only show this at the root level
    if (currentPath === './data') {
      try {
        const dbCache = DatabaseMetadataCache.getInstance();
        const cachedMetadata = await dbCache.getCachedMetadata();
        const db_prompt =
          'Database Connection Available:\n' +
          '- DB_URL environment variable is configured in your Python kernel\n' +
          '- You can connect to the database using standard Python libraries like psycopg2 or sqlalchemy\n' +
          '\n' +
          'Database Schema:\n';
        if (cachedMetadata) {
          datasetContexts.push({
            type: 'data' as const,
            id: 'database-schema',
            name: 'Database Schema',
            description: 'Current database schema information',
            content: `${db_prompt} \n \n ${cachedMetadata}`,
            isDirectory: false
          });
          console.log(
            '[ChatContextLoaders] Added database schema to data contexts'
          );
        }
      } catch (error) {
        console.warn(
          '[ChatContextLoaders] Could not load database metadata:',
          error
        );
      }
    }

    // Load file-based datasets using optimized Python kernel script
    try {
      const fileContexts = await DataLoaderService.loadDatasets();
      datasetContexts.push(...fileContexts);
    } catch (error) {
      console.error('Error loading datasets from', currentPath, ':', error);
    }

    return datasetContexts;
  }

  /**
   * Load table names from all databases in DatabaseStateService
   */
  public async loadTables(): Promise<IMentionContext[]> {
    try {
      console.log(
        '[ChatContextLoaders] Starting to load tables from DatabaseStateService...'
      );

      // Get all database configurations from DatabaseStateService
      const configurations = DatabaseStateService.getConfigurations();
      console.log(
        `[ChatContextLoaders] Found ${configurations.length} database configurations`
      );

      const tables: IMentionContext[] = [];

      // Iterate through each database configuration
      for (const config of configurations) {
        if (!config.database_schema) {
          console.log(
            `[ChatContextLoaders] No schema available for database: ${config.name}`
          );
          continue;
        }

        console.log(
          `[ChatContextLoaders] Processing schema for database: ${config.name}, type: ${config.type}`
        );

        // Handle MySQL/PostgreSQL schema format
        if ('table_schemas' in config.database_schema) {
          const mysqlPostgresSchema = config.database_schema;
          console.log(
            `[ChatContextLoaders] Processing MySQL/PostgreSQL schema with ${Object.keys(mysqlPostgresSchema.table_schemas).length} tables`
          );

          for (const [fullTableName, tableInfo] of Object.entries(
            mysqlPostgresSchema.table_schemas
          )) {
            // Build detailed table schema information
            const schemaInfo = this.buildTableSchemaInfo(tableInfo);

            const table_prompt =
              `Database: ${config.name} (${config.type})\n` +
              'Database Connection Available:\n' +
              '- DB_URL environment variable is configured in your Python kernel\n' +
              '- You can connect to the database using standard Python libraries like psycopg2 or sqlalchemy\n' +
              '\n' +
              `Table Schema for ${tableInfo.table_name}:\n` +
              schemaInfo;

            tables.push({
              type: 'table' as const,
              id: `table-${config.id}-${fullTableName}`,
              name: `${config.name}.${tableInfo.table_name}`,
              description: `${tableInfo.table_name} in ${tableInfo.schema} schema (${config.name})`,
              content: table_prompt
            });
          }
        }
        // Handle Snowflake schema format
        else if ('databases' in config.database_schema) {
          const snowflakeSchema = config.database_schema;
          console.log(
            `[ChatContextLoaders] Processing Snowflake schema with ${snowflakeSchema.databases.length} databases`
          );

          for (const db of snowflakeSchema.databases) {
            for (const schema of db.schemas) {
              if (schema.error) {
                console.log(
                  `[ChatContextLoaders] Skipping schema ${schema.schema} due to error: ${schema.error}`
                );
                continue;
              }

              for (const table of schema.tables) {
                // Build Snowflake table schema information
                const schemaInfo = this.buildSnowflakeTableSchemaInfo(
                  db.database,
                  schema.schema,
                  table
                );

                const table_prompt =
                  `Database: ${config.name} (Snowflake)\n` +
                  'Database Connection Available:\n' +
                  '- DB_URL environment variable is configured in your Python kernel\n' +
                  '- You can connect to Snowflake using snowflake-connector-python or snowflake-sqlalchemy\n' +
                  '\n' +
                  `Table Schema for ${table.table}:\n` +
                  schemaInfo;

                const fullName = `${db.database}.${schema.schema}.${table.table}`;
                tables.push({
                  type: 'table' as const,
                  id: `table-${config.id}-${fullName}`,
                  name: `${config.name}.${table.table}`,
                  description: `${table.table} in ${db.database}.${schema.schema} (${config.name})`,
                  content: table_prompt
                });
              }
            }
          }
        }
      }

      console.log(
        `[ChatContextLoaders] Loaded ${tables.length} database tables from all databases`
      );
      return tables;
    } catch (error) {
      console.warn(
        '[ChatContextLoaders] Error loading database tables:',
        error
      );
      return [];
    }
  }

  /**
   * Build detailed table schema information from table info
   */
  private buildTableSchemaInfo(tableInfo: any): string {
    let schemaInfo = `Schema: ${tableInfo.schema}\n`;
    schemaInfo += `Table: ${tableInfo.table_name}\n\n`;

    // Add columns
    if (tableInfo.columns && tableInfo.columns.length > 0) {
      schemaInfo += `Columns (${tableInfo.columns.length}):\n`;
      for (const col of tableInfo.columns) {
        let dataType = col.data_type;

        // Format data type with precision/scale
        if (col.character_maximum_length) {
          dataType += `(${col.character_maximum_length})`;
        } else if (col.numeric_precision && col.numeric_scale !== null) {
          dataType += `(${col.numeric_precision},${col.numeric_scale})`;
        } else if (col.numeric_precision) {
          dataType += `(${col.numeric_precision})`;
        }

        // Add constraints
        const constraints = [];
        if (col.is_nullable === 'NO') {
          constraints.push('NOT NULL');
        }
        if (col.column_default) {
          constraints.push(`DEFAULT ${col.column_default}`);
        }
        if (
          tableInfo.primary_keys &&
          tableInfo.primary_keys.includes(col.column_name)
        ) {
          constraints.push('PRIMARY KEY');
        }

        const constraintText =
          constraints.length > 0 ? ` (${constraints.join(', ')})` : '';
        schemaInfo += `- ${col.column_name}: ${dataType}${constraintText}\n`;
      }
      schemaInfo += '\n';
    }

    // Add primary keys
    if (tableInfo.primary_keys && tableInfo.primary_keys.length > 0) {
      schemaInfo += `Primary Keys: ${tableInfo.primary_keys.join(', ')}\n`;
    }

    // Add foreign keys
    if (tableInfo.foreign_keys && tableInfo.foreign_keys.length > 0) {
      schemaInfo += 'Foreign Keys:\n';
      for (const fk of tableInfo.foreign_keys) {
        schemaInfo += `- ${fk.column_name} → ${fk.foreign_table_schema}.${fk.foreign_table_name}(${fk.foreign_column_name})\n`;
      }
    }

    return schemaInfo;
  }

  /**
   * Build detailed table schema information for Snowflake tables
   */
  private buildSnowflakeTableSchemaInfo(
    database: string,
    schema: string,
    table: any
  ): string {
    let schemaInfo = `Database: ${database}\n`;
    schemaInfo += `Schema: ${schema}\n`;
    schemaInfo += `Table: ${table.table}\n`;
    schemaInfo += `Type: ${table.type}\n\n`;

    // Add columns
    if (table.columns && table.columns.length > 0) {
      schemaInfo += `Columns (${table.columns.length}):\n`;
      for (const col of table.columns) {
        let dataType = col.type;

        // Format data type with precision/scale for NUMBER columns
        if (col.type === 'NUMBER' && 'precision' in col && 'scale' in col) {
          dataType += `(${col.precision},${col.scale})`;
        } else if (col.type === 'TEXT' && 'max_length' in col) {
          dataType += `(${col.max_length})`;
        }

        // Add nullable constraint
        const nullable = col.nullable ? 'NULL' : 'NOT NULL';
        schemaInfo += `- ${col.name}: ${dataType} (${nullable})\n`;
      }
      schemaInfo += '\n';
    }

    return schemaInfo;
  }

  /**
   * Load datasets using the new DataLoaderService (fast, synchronous loading)
   */
  private async loadDatasetsViaKernel(
    currentPath: string = '/data'
  ): Promise<IMentionContext[]> {
    try {
      // Fast synchronous load from cache/JSON file
      const mentionContexts = await DataLoaderService.loadDatasets([
        currentPath
      ]);
      console.log(
        `[ChatContextLoaders] Successfully loaded ${mentionContexts.length} items from ${currentPath}`
      );
      return mentionContexts;
    } catch (error) {
      console.error(
        '[ChatContextLoaders] Error loading datasets via kernel:',
        error
      );
      return [];
    }
  }

  /**
   * Trigger async refresh of data directory (non-blocking)
   * This should be called when the @ menu is opened
   */
  public triggerAsyncDataRefresh(): void {
    // Start async refresh in the background (don't await it)
    DataLoaderService.refreshDatasets('./data')
      .then(() => {
        console.log(
          '[ChatContextLoaders] Data refresh completed in background'
        );
      })
      .catch((error: any) => {
        console.warn('[ChatContextLoaders] Data refresh failed:', error);
      });
  }

  /**
   * Get the parent path from a given path
   */
  private getParentPath(path: string): string {
    const parts = path.split('/');
    parts.pop(); // Remove the last part
    return parts.join('/') || './data';
  }

  /**
   * Load notebook cells
   */
  public async loadCells(): Promise<IMentionContext[]> {
    // console.log('Loading cells... ======================');
    const notebook = this.toolService.getCurrentNotebook();
    if (!notebook) {
      console.warn('No notebook available');
      return [];
    }

    const cellContexts: IMentionContext[] = [];
    const cells = notebook.widget.model.cells as any;

    for (const cell of cells) {
      const tracker = cell.metadata.cell_tracker;
      if (tracker) {
        cellContexts.push({
          type: 'cell',
          id: tracker.trackingId,
          name: tracker.trackingId,
          description: '',
          content: cell.sharedModel.getSource()
        });
      }
    }

    return cellContexts;
  }

  /**
   * Load variables from the current kernel
   */
  public async loadVariables(): Promise<IMentionContext[]> {
    console.log('Loading variables... ======================');
    const kernel = this.toolService.getCurrentNotebook()?.kernel;
    if (!kernel) {
      console.warn('No kernel available');
      return [];
    }

    try {
      // Use the shared kernel preview utilities to get detailed variable information
      const kernelVariables = await KernelPreviewUtils.getKernelVariables();

      if (!kernelVariables) {
        console.log('No kernel variables available');
        return [];
      }

      const variableContexts: IMentionContext[] = [];

      for (const [varName, varInfo] of Object.entries(kernelVariables)) {
        // Skip variables in blacklists
        if (VARIABLE_NAME_BLACKLIST.includes(varName)) {
          continue;
        }
        if (VARIABLE_TYPE_BLACKLIST.includes(varInfo.type)) {
          continue;
        }

        // Create a description based on the variable info
        let description = varInfo.type || 'unknown';
        if (varInfo.shape) {
          description += ` (shape: ${JSON.stringify(varInfo.shape)})`;
        } else if (varInfo.size !== undefined && varInfo.size !== null) {
          description += ` (size: ${varInfo.size})`;
        }

        // Create content for the variable
        let content = '';
        if (varInfo.value !== undefined) {
          content = JSON.stringify(varInfo.value);
        } else if (varInfo.preview !== undefined) {
          content = JSON.stringify(varInfo.preview);
        } else if (varInfo.repr) {
          content = varInfo.repr;
        }

        variableContexts.push({
          type: 'variable',
          id: varName,
          name: varName,
          description: description,
          content: content
        });
      }

      console.log(
        `[ChatContextLoaders] Loaded ${variableContexts.length} variables`
      );
      return variableContexts;
    } catch (error) {
      console.error('Error loading variables:', error);
      return [];
    }
  }

  /**
   * Load database configurations from DatabaseStateService
   */
  public async loadDatabases(): Promise<IMentionContext[]> {
    console.log('=== LOADING DATABASSES ===');
    try {
      // Import the getDatabases function dynamically to avoid circular imports
      const { getDatabases } = await import('./databaseHelper');
      const credentials = DatabaseStateService.getState().configurations;
      const databaseContexts = await getDatabases();

      // console.log('===== DATABASE CONTEXTS =====');
      // console.log(databaseContexts);
      // console.log('==== DATABASE CREDENTIALS =====');
      // console.log(credentials);

      for (const database of credentials) {
        console.log(database);
        if (database.database_schema) {
          console.log(database.database_schema);
        }
      }

      console.log(
        `[ChatContextLoaders] Loaded ${databaseContexts.length} database configurations`
      );

      // Convert DatabaseContext to IMentionContext
      return databaseContexts.map(db => ({
        type: db.type,
        id: db.id,
        name: db.name,
        description: db.description,
        content: db.content,
        isDirectory: db.isDirectory
      }));
    } catch (error) {
      console.error('Error loading database configurations:', error);
      return [];
    }
  }
}
