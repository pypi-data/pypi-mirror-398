import {
  DatabaseStateService,
  DatabaseType,
  ISnowflakeSchemaData,
  IMySQLPostgreSQLSchema
} from '../DatabaseStateService';
import { DatabaseSearchUtil, ISearchableTable } from './DatabaseSearchUtil';

/**
 * Tools for searching database tables across configurations
 */
export class DatabaseSearchTools {
  /**
   * Search database tables using semantic queries with fuzzy matching
   * @param options Configuration options
   * @param options.queries List of search queries to find relevant tables (required)
   * @param options.database_names list of database names to limit the search scope
   * @returns JSON string with top 10 most relevant tables per query and their metadata
   */
  static async search_tables(options: {
    queries: string[];
    database_names: string[];
  }): Promise<string> {
    try {
      const queries = options.queries || [];
      const databaseNames = options.database_names || [];

      if (queries.length === 0) {
        return JSON.stringify({
          error: 'At least one query is required'
        });
      }

      // Get all database configurations
      const state = DatabaseStateService.getState();
      const configurations = state.configurations;

      if (!configurations || configurations.length === 0) {
        return JSON.stringify({
          error:
            'No database configurations found. Please connect to a database first.'
        });
      }

      // Filter configurations by database names if provided
      let configsToSearch = configurations;
      if (databaseNames.length > 0) {
        configsToSearch = configurations.filter(config =>
          databaseNames.includes(config.name)
        );

        if (configsToSearch.length === 0) {
          return JSON.stringify({
            error: `No database configurations found matching names: ${databaseNames.join(', ')}`
          });
        }
      }

      // Collect all results from all matching configurations
      const allResults: any = {
        databases: [],
        query_results: []
      };

      // Search across all configurations
      for (const config of configsToSearch) {
        // Get schema information for this config
        const schemaInfo = DatabaseStateService.getSchemaInfo(config.id);
        if (!schemaInfo || !schemaInfo.schema) {
          console.warn(
            `[DatabaseSearchTools] No schema information available for ${config.name}`
          );
          continue;
        }

        allResults.databases.push({
          name: config.name,
          type: config.type
        });

        const parsedSchema = schemaInfo.schema;

        // Handle Snowflake schema structure
        if (
          config.type === DatabaseType.Snowflake &&
          'databases' in parsedSchema
        ) {
          const snowflakeSchema = parsedSchema as ISnowflakeSchemaData;

          // Build a flat list of all tables across all databases
          const allTables: ISearchableTable[] = [];
          for (const db of snowflakeSchema.databases) {
            for (const schema of db.schemas) {
              if (schema.error) {
                continue;
              }

              for (const table of schema.tables) {
                allTables.push({
                  config_name: config.name,
                  config_type: config.type,
                  database: db.database,
                  schema: schema.schema,
                  table_name: table.table,
                  full_name: `${db.database}.${schema.schema}.${table.table}`,
                  type: table.type,
                  columns: table.columns,
                  column_count: table.columns.length
                });
              }
            }
          }

          // Search for each query in this config's tables using fuzzy search
          for (let i = 0; i < queries.length; i++) {
            const query = queries[i];

            // Use fuzzy search to find top 10 matches
            const topTables = DatabaseSearchUtil.search(query, allTables, 10);

            // Add results for this query (or update existing)
            if (!allResults.query_results[i]) {
              allResults.query_results[i] = {
                query,
                total_matches: 0,
                tables: []
              };
            }

            allResults.query_results[i].total_matches += topTables.length;
            allResults.query_results[i].tables.push(
              ...topTables.map(table => ({
                config_name: table.config_name,
                config_type: table.config_type,
                database: table.database,
                schema: table.schema,
                table_name: table.table_name,
                full_name: table.full_name,
                type: table.type,
                columns: table.column_count,
                column_names: table.columns.map((col: any) => col.name),
                relevance_score: table.relevance_score
              }))
            );
          }
        }
        // Handle MySQL/PostgreSQL schema structure
        else if ('table_schemas' in parsedSchema) {
          const mysqlPostgresSchema = parsedSchema as IMySQLPostgreSQLSchema;
          const allTables: ISearchableTable[] = Object.values(
            mysqlPostgresSchema.table_schemas
          ).map(table => ({
            config_name: config.name,
            config_type: config.type,
            schema: table.schema,
            table_name: table.table_name,
            full_name: table.full_name,
            columns: table.columns,
            column_count: table.columns.length,
            primary_keys: table.primary_keys,
            foreign_keys: table.foreign_keys
          }));

          // Search for each query in this config's tables using fuzzy search
          for (let i = 0; i < queries.length; i++) {
            const query = queries[i];

            // Use fuzzy search to find top 10 matches
            const topTables = DatabaseSearchUtil.search(query, allTables, 10);

            // Add results for this query (or update existing)
            if (!allResults.query_results[i]) {
              allResults.query_results[i] = {
                query,
                total_matches: 0,
                tables: []
              };
            }

            allResults.query_results[i].total_matches += topTables.length;
            allResults.query_results[i].tables.push(
              ...topTables.map(table => ({
                config_name: table.config_name,
                config_type: table.config_type,
                schema: table.schema,
                table_name: table.table_name,
                full_name: table.full_name,
                columns: table.columns.length,
                column_names: table.columns.map((col: any) => col.column_name),
                primary_keys: table.primary_keys || [],
                foreign_keys: table.foreign_keys || [],
                relevance_score: table.relevance_score
              }))
            );
          }
        }
      }

      // Sort tables within each query result by relevance score
      for (const queryResult of allResults.query_results) {
        queryResult.tables.sort(
          (a: any, b: any) => a.relevance_score - b.relevance_score
        );
        // Keep only top 10 overall across all configs
        queryResult.tables = queryResult.tables.slice(0, 10);
      }

      // Format results as a human-readable string
      let formattedOutput = 'QUERY RESULTS:\n\n';

      for (const queryResult of allResults.query_results) {
        formattedOutput += `Query: "${queryResult.query}"\n`;
        formattedOutput += `Total Matches: ${queryResult.total_matches}\n\n`;

        for (const table of queryResult.tables) {
          formattedOutput += `=== Start ${table.table_name} ===\n`;
          formattedOutput += `Database: ${table.config_name} (${table.config_type})\n`;
          if (table.database) {
            formattedOutput += `Database Schema: ${table.database}\n`;
          }
          if (table.schema) {
            formattedOutput += `Schema: ${table.schema}\n`;
          }
          formattedOutput += `Table: ${table.table_name}\n`;
          formattedOutput += `Full Name: ${table.full_name}\n`;
          if (table.type) {
            formattedOutput += `Type: ${table.type}\n`;
          }
          formattedOutput += `Columns (${table.columns}):\n\n`;

          // Add column details
          for (const columnName of table.column_names) {
            formattedOutput += `  - ${columnName}\n`;
          }
          formattedOutput += '\n';

          // Add primary keys if available
          if (table.primary_keys && table.primary_keys.length > 0) {
            formattedOutput += `Primary Keys: ${table.primary_keys.join(', ')}\n`;
          }

          // Add foreign keys if available
          if (table.foreign_keys && table.foreign_keys.length > 0) {
            formattedOutput += 'Foreign Keys:\n';
            for (const fk of table.foreign_keys) {
              formattedOutput += `  - ${fk.column_name} -> ${fk.referenced_table}.${fk.referenced_column}\n`;
            }
          }

          formattedOutput += `Relevance Score: ${table.relevance_score}\n`;
          formattedOutput += '=============\n\n';
        }
      }

      if (allResults.query_results.length === 0) {
        formattedOutput += 'No matching tables found.\n';
      }

      return formattedOutput;
    } catch (error) {
      return JSON.stringify({
        error: `Failed to search tables: ${error instanceof Error ? error.message : String(error)}`
      });
    }
  }
}
