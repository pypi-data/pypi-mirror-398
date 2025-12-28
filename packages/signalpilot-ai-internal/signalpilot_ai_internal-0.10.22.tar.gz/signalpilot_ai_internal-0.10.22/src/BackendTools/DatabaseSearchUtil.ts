import Fuse from 'fuse.js';

/**
 * Interface for searchable table data
 */
export interface ISearchableTable {
  config_name: string;
  config_type: string;
  database?: string;
  schema?: string;
  schema_name?: string;
  table_name: string;
  table?: string;
  full_name: string;
  type?: string;
  columns: any[];
  column_count?: number;
  primary_keys?: string[];
  foreign_keys?: any[];
}

/**
 * Interface for search results
 */
export interface ISearchResult extends ISearchableTable {
  relevance_score: number;
  match_details?: string;
}

/**
 * Utility class for performing fuzzy search on database tables
 */
export class DatabaseSearchUtil {
  /**
   * Perform fuzzy search on tables using Fuse.js
   * @param query The search query string
   * @param tables Array of searchable tables
   * @param topN Number of top results to return (default: 10)
   * @returns Array of search results with relevance scores
   */
  static fuzzySearch(
    query: string,
    tables: ISearchableTable[],
    topN: number = 10
  ): ISearchResult[] {
    if (!query || tables.length === 0) {
      return [];
    }

    // Configure Fuse.js options for optimal database table search
    const fuseOptions = {
      // Include score and matched indices for debugging
      includeScore: true,
      includeMatches: true,

      // Lower threshold = more strict matching (0.0 = perfect match, 1.0 = match anything)
      threshold: 0.4,

      // Location and distance affect how fuzzy matching works
      // location: 0 means we prefer matches at the beginning
      location: 0,

      // Distance: how far from location we'll search
      distance: 100,

      // Minimum character length that must be matched
      minMatchCharLength: 1,

      // Keys to search with their weights (higher weight = more important)
      keys: [
        { name: 'table_name', weight: 3.0 }, // Table name is most important
        { name: 'table', weight: 3.0 }, // Alternate table name field
        { name: 'full_name', weight: 2.5 }, // Full qualified name
        { name: 'schema', weight: 1.5 }, // Schema name
        { name: 'schema_name', weight: 1.5 }, // Alternate schema field
        { name: 'database', weight: 1.2 }, // Database name
        { name: 'columnNames', weight: 1.8 }, // Column names (searchable string)
        { name: 'type', weight: 0.8 } // Table type (less important)
      ]
    };

    // Prepare tables for search by extracting column names
    const searchableTables = tables.map(table => {
      const columnNames = table.columns
        .map((col: any) => col.column_name || col.name || '')
        .filter(name => name.length > 0)
        .join(' ');

      return {
        ...table,
        columnNames,
        table_name: table.table_name || table.table || '',
        schema_name: table.schema_name || table.schema || ''
      };
    });

    // Create Fuse instance and perform search
    const fuse = new Fuse(searchableTables, fuseOptions);
    const fuseResults = fuse.search(query);

    // Transform Fuse results to our ISearchResult format
    const results: ISearchResult[] = fuseResults
      .slice(0, topN)
      .map((result, index) => {
        const item = result.item;
        const score = result.score || 0;

        // Generate match details for debugging
        let matchDetails = '';
        if (result.matches && result.matches.length > 0) {
          const matchedKeys = result.matches
            .map(match => match.key)
            .filter((key, idx, arr) => arr.indexOf(key) === idx);
          matchDetails = `Matched: ${matchedKeys.join(', ')}`;
        }

        return {
          config_name: item.config_name,
          config_type: item.config_type,
          database: item.database,
          schema: item.schema || item.schema_name,
          schema_name: item.schema_name || item.schema,
          table_name: item.table_name || item.table || '',
          table: item.table || item.table_name,
          full_name: item.full_name,
          type: item.type,
          columns: item.columns,
          column_count: item.column_count || item.columns.length,
          primary_keys: item.primary_keys,
          foreign_keys: item.foreign_keys,
          relevance_score: score,
          match_details: matchDetails
        };
      });

    return results;
  }

  /**
   * Legacy scoring algorithm (kept for backward compatibility)
   * Lower score is better
   * @param query Search query
   * @param table Table to score
   * @returns Relevance score (1 = exact match, higher = less relevant, 1000 = no match)
   */
  static calculateLegacyRelevance(query: string, table: any): number {
    const lowerQuery = query.toLowerCase();
    const tableName = (table.table_name || table.table || '').toLowerCase();
    const schemaName = (table.schema_name || table.schema || '').toLowerCase();
    const fullName = (
      table.full_name || `${schemaName}.${tableName}`
    ).toLowerCase();

    // Check column names and types
    const columns = table.columns || [];
    const columnNames = columns
      .map((col: any) => (col.column_name || col.name || '').toLowerCase())
      .join(' ');

    // Exact match is best (score 1)
    if (tableName === lowerQuery || fullName === lowerQuery) {
      return 1;
    }

    // Table name starts with query (score 2)
    if (tableName.startsWith(lowerQuery)) {
      return 2;
    }

    // Table name contains query (score 3)
    if (tableName.includes(lowerQuery)) {
      return 3;
    }

    // Full name contains query (score 4)
    if (fullName.includes(lowerQuery)) {
      return 4;
    }

    // Column names contain query (score 5)
    if (columnNames.includes(lowerQuery)) {
      return 5;
    }

    // Partial column match (score 6)
    if (
      columnNames.split(' ').some((col: string) => col.includes(lowerQuery))
    ) {
      return 6;
    }

    // No match
    return 1000;
  }

  /**
   * Perform search with automatic fallback
   * Tries fuzzy search first, falls back to legacy if no results
   * @param query Search query
   * @param tables Array of tables to search
   * @param topN Number of results to return (default: 10)
   * @returns Array of search results
   */
  static search(
    query: string,
    tables: ISearchableTable[],
    topN: number = 10
  ): ISearchResult[] {
    // Try fuzzy search first
    const fuzzyResults = this.fuzzySearch(query, tables, topN);

    // If we have good fuzzy results (score < 0.5), use them
    if (fuzzyResults.length > 0 && fuzzyResults[0].relevance_score < 0.5) {
      return fuzzyResults;
    }

    // Fall back to legacy search if fuzzy search didn't find good matches
    const legacyResults = tables
      .map(table => ({
        ...table,
        table_name: table.table_name || table.table || '',
        schema_name: table.schema_name || table.schema || '',
        column_count: table.column_count || table.columns.length,
        relevance_score: this.calculateLegacyRelevance(query, table)
      }))
      .filter(t => t.relevance_score < 1000)
      .sort((a, b) => a.relevance_score - b.relevance_score)
      .slice(0, topN);

    // If legacy found results, use them
    if (legacyResults.length > 0) {
      return legacyResults;
    }

    // Otherwise return fuzzy results even if scores are high
    return fuzzyResults;
  }
}
