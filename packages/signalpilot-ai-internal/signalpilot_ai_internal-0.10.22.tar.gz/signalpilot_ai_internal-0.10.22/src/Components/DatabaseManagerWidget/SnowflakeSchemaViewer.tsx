import * as React from 'react';
import { useState } from 'react';
import { AppStateService } from '../../AppState';
import { IMentionContext } from '../../Chat/ChatContextMenu/ChatContextLoaders';
import {
  INumberColumn,
  ITextColumn,
  Column,
  ITableEntry,
  ISnowflakeSchemaData
} from '../../DatabaseStateService';
import { SNOWFLAKE_ICON } from '../databaseIcons';

/**
 * Props for the SnowflakeSchemaViewer component
 */
export interface ISnowflakeSchemaViewerProps {
  schemaData: ISnowflakeSchemaData;
  databaseName: string;
  onBack?: () => void;
}

/**
 * Component for exploring Snowflake database schemas
 */
export function SnowflakeSchemaViewer({
  schemaData,
  databaseName,
  onBack
}: ISnowflakeSchemaViewerProps) {
  const [selectedDatabase, setSelectedDatabase] = useState<string | null>(null);
  const [selectedSchema, setSelectedSchema] = useState<string | null>(null);
  const [selectedTable, setSelectedTable] = useState<ITableEntry | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const handleBackToSchemas = () => {
    setSelectedTable(null);
  };

  const handleBackToDatabases = () => {
    setSelectedSchema(null);
    setSelectedTable(null);
  };

  const handleBackToDatabaseList = () => {
    setSelectedDatabase(null);
    setSelectedSchema(null);
    setSelectedTable(null);
  };

  const formatColumnType = (column: Column): string => {
    switch (column.type) {
      case 'NUMBER':
        // eslint-disable-next-line no-case-declarations
        const numCol = column as INumberColumn;
        return `NUMBER(${numCol.precision},${numCol.scale})`;
      case 'TEXT':
        // eslint-disable-next-line no-case-declarations
        const textCol = column as ITextColumn;
        return `TEXT(${textCol.max_length})`;
      case 'DATE':
        return 'DATE';
      default:
        return column.type;
    }
  };

  const handleAddTableToContext = async (
    table: ITableEntry,
    database: string
  ): Promise<void> => {
    try {
      const chatMessages =
        AppStateService.getState().chatContainer?.chatWidget.messageComponent;
      if (!chatMessages) {
        console.error('[SnowflakeSchemaViewer] Chat messages not available');
        return;
      }

      const fullTableName = `${database}.${table.schema}.${table.table}`;

      // Create table schema content
      const tableContent = `Table: ${fullTableName}
Type: ${table.type}

Columns (${table.columns.length}):
${table.columns
  .sort((a, b) => a.ordinal - b.ordinal)
  .map(col => {
    const typeStr = formatColumnType(col);
    const nullableStr = col.nullable ? ' (nullable)' : ' (not null)';
    const descStr =
      'description' in col && col.description ? ` - ${col.description}` : '';
    return `- ${col.name}: ${typeStr}${nullableStr}${descStr}`;
  })
  .join('\n')}`;

      const context: IMentionContext = {
        type: 'data',
        id: `snowflake-table-${fullTableName}`,
        name: table.table,
        description: `Snowflake table: ${fullTableName} (${table.columns.length} columns)`,
        content: tableContent,
        path: fullTableName
      };

      chatMessages.addMentionContext(context);
      console.log(
        `[SnowflakeSchemaViewer] Added table ${table.table} to context`
      );
    } catch (error) {
      console.error(
        '[SnowflakeSchemaViewer] Error adding table to context:',
        error
      );
    }
  };

  // VIEW: Table details
  if (selectedTable && selectedDatabase && selectedSchema) {
    const fullTableName = `${selectedDatabase}.${selectedSchema}.${selectedTable.table}`;

    return (
      <div className="database-schema-explorer snowflake-schema-viewer">
        <div className="schema-explorer-header">
          <button
            onClick={handleBackToSchemas}
            className="back-button"
            title="Back to tables"
          >
            ← Back
          </button>
          <div className="table-title-section">
            <button
              className="add-to-context-button detail-view-button"
              onClick={() =>
                handleAddTableToContext(selectedTable, selectedDatabase)
              }
              title={`Add ${selectedTable.table} to context`}
            >
              <span className="add-to-context-icon">+</span>
              Add to Context
            </button>
            <h3 className="table-title">{selectedTable.table}</h3>
            <span className="table-full-name">{fullTableName}</span>
          </div>
        </div>

        <div className="table-details">
          <div className="schema-section">
            <h4 className="section-title">
              Columns ({selectedTable.columns.length})
            </h4>
            <div className="columns-table">
              <div className="columns-header">
                <div className="column-name-header">Name</div>
                <div className="column-type-header">Type</div>
                <div className="column-nullable-header">Nullable</div>
                <div className="column-ordinal-header">Position</div>
              </div>
              {selectedTable.columns
                .sort((a, b) => a.ordinal - b.ordinal)
                .map((column, index) => (
                  <div key={index} className="column-row">
                    <div className="column-name">
                      <span className="column-name-text">{column.name}</span>
                    </div>
                    <div className="column-type">
                      {formatColumnType(column)}
                    </div>
                    <div className="column-nullable">
                      {column.nullable ? '✓' : '✗'}
                    </div>
                    <div className="column-ordinal">{column.ordinal}</div>
                  </div>
                ))}
            </div>
            {'description' in selectedTable.columns[0] && (
              <div className="column-descriptions">
                {selectedTable.columns.filter(
                  col => 'description' in col && col.description
                ).length > 0 && (
                  <>
                    <h5 className="subsection-title">Column Descriptions</h5>
                    {selectedTable.columns
                      .filter(col => 'description' in col && col.description)
                      .map((col, idx) => (
                        <div key={idx} className="description-item">
                          <strong>{col.name}:</strong>{' '}
                          {(col as ITextColumn).description}
                        </div>
                      ))}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // VIEW: Schema tables list
  if (selectedDatabase && selectedSchema) {
    const database = schemaData.databases.find(
      db => db.database === selectedDatabase
    );
    const schema = database?.schemas.find(s => s.schema === selectedSchema);

    if (!schema) {
      return (
        <div className="database-schema-explorer snowflake-schema-viewer">
          <div className="schema-explorer-header">
            <button onClick={handleBackToDatabases} className="back-button">
              ← Back
            </button>
            <h3>Schema not found</h3>
          </div>
        </div>
      );
    }

    if (schema.error) {
      return (
        <div className="database-schema-explorer snowflake-schema-viewer">
          <div className="schema-explorer-header">
            <button onClick={handleBackToDatabases} className="back-button">
              ← Back
            </button>
            <h3 className="database-title">{schema.schema}</h3>
          </div>
          <div className="schema-error-message">
            <span className="error-icon">⚠️</span>
            <p>Error loading tables: {schema.error}</p>
          </div>
        </div>
      );
    }

    const filteredTables = schema.tables.filter(table =>
      table.table.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
      <div className="database-schema-explorer snowflake-schema-viewer">
        <div className="schema-explorer-header">
          <button onClick={handleBackToDatabases} className="back-button">
            ← Back
          </button>
          <h3 className="database-title">{schema.schema}</h3>
          {/*<span className="tables-count">({filteredTables.length} tables)</span>*/}
        </div>

        <div className="tables-search">
          <input
            type="text"
            placeholder="Search tables..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="tables-list">
          {filteredTables.length === 0 ? (
            <div className="no-tables">
              {searchTerm
                ? 'No tables match your search.'
                : 'No tables found in this schema.'}
            </div>
          ) : (
            filteredTables.map((table, index) => (
              <div
                key={index}
                className="table-item"
                title={`Click to view ${table.table} schema`}
              >
                <div
                  className="table-item-content"
                  onClick={() => setSelectedTable(table)}
                >
                  <div className="table-item-header">
                    <div className="table-name-section">
                      <button
                        className="add-to-context-button"
                        onClick={e => {
                          e.stopPropagation();
                          void handleAddTableToContext(table, selectedDatabase);
                        }}
                        title={`Add ${table.table} to context`}
                      >
                        <span className="add-to-context-icon">+</span>
                        Add to Context
                      </button>
                      <div className="table-name">{table.table}</div>
                      <div className="table-full-name">
                        {selectedDatabase}.{schema.schema}.{table.table}
                      </div>
                    </div>
                  </div>
                  <div className="table-item-stats">
                    <span className="table-stat">📊 {table.type}</span>
                    <span className="table-stat">
                      📋 {table.columns.length} columns
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  // VIEW: Database schemas list
  if (selectedDatabase) {
    const database = schemaData.databases.find(
      db => db.database === selectedDatabase
    );

    if (!database) {
      return (
        <div className="database-schema-explorer snowflake-schema-viewer">
          <div className="schema-explorer-header">
            <button onClick={handleBackToDatabaseList} className="back-button">
              ← Back
            </button>
            <h3>Database not found</h3>
          </div>
        </div>
      );
    }

    const filteredSchemas = database.schemas.filter(schema =>
      schema.schema.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
      <div className="database-schema-explorer snowflake-schema-viewer">
        <div className="schema-explorer-header">
          <button onClick={handleBackToDatabaseList} className="back-button">
            ← Back
          </button>
          <h3 className="database-title">{database.database}</h3>
          {/*<span className="tables-count">*/}
          {/*  ({filteredSchemas.length} schemas)*/}
          {/*</span>*/}
        </div>

        <div className="tables-search">
          <input
            type="text"
            placeholder="Search schemas..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="tables-list snowflake-schemas-list">
          {filteredSchemas.length === 0 ? (
            <div className="no-tables">
              {searchTerm
                ? 'No schemas match your search.'
                : 'No schemas found in this database.'}
            </div>
          ) : (
            filteredSchemas.map((schema, index) => {
              const tableCount = schema.tables.length;
              const hasError = schema.error !== null;

              return (
                <div
                  key={index}
                  className={`table-item schema-item ${hasError ? 'schema-error' : ''}`}
                  title={
                    hasError
                      ? `Error: ${schema.error}`
                      : `Click to view ${schema.schema} tables`
                  }
                >
                  <div
                    className="table-item-content"
                    onClick={() =>
                      !hasError && setSelectedSchema(schema.schema)
                    }
                  >
                    <div className="table-item-header">
                      <div className="table-name-section">
                        <div className="table-name">
                          {hasError && <span className="error-icon">⚠️ </span>}
                          {schema.schema}
                        </div>
                        {!hasError && (
                          <div className="table-full-name">
                            {database.database}.{schema.schema}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="table-item-stats">
                      {hasError ? (
                        <span className="table-stat error-stat">
                          Error loading tables
                        </span>
                      ) : (
                        <>
                          <span className="table-stat">
                            📊 {tableCount}{' '}
                            {tableCount === 1 ? 'table' : 'tables'}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    );
  }

  // VIEW: Databases list
  const filteredDatabases = schemaData.databases.filter(db =>
    db.database.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="database-schema-explorer snowflake-schema-viewer">
      <div className="schema-explorer-header">
        {onBack && (
          <button
            onClick={onBack}
            className="back-button"
            title="Back to databases"
          >
            ← Back
          </button>
        )}
        <h3 className="database-title">{databaseName}</h3>
        {/*<span className="tables-count">*/}
        {/*  ({filteredDatabases.length} databases)*/}
        {/*</span>*/}
      </div>

      <div className="tables-search">
        <input
          type="text"
          placeholder="Search databases..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="tables-list snowflake-databases-list">
        {filteredDatabases.length === 0 ? (
          <div className="no-tables">
            {searchTerm
              ? 'No databases match your search.'
              : 'No databases found.'}
          </div>
        ) : (
          filteredDatabases.map((database, index) => {
            const schemaCount = database.schemas.length;
            const totalTables = database.schemas.reduce(
              (sum, schema) => sum + (schema.error ? 0 : schema.tables.length),
              0
            );

            return (
              <div
                key={index}
                className="table-item database-item"
                title={`Click to view ${database.database} schemas`}
              >
                <div
                  className="table-item-content"
                  onClick={() => setSelectedDatabase(database.database)}
                >
                  <div className="table-item-header">
                    <div className="table-name-section">
                      <div className="table-name">
                        <SNOWFLAKE_ICON.react className="db-icon" tag="span" />{' '}
                        {database.database}
                      </div>
                    </div>
                  </div>
                  <div className="table-item-stats">
                    <span className="table-stat">
                      📂 {schemaCount}{' '}
                      {schemaCount === 1 ? 'schema' : 'schemas'}
                    </span>
                    <span className="table-stat">
                      📊 {totalTables} {totalTables === 1 ? 'table' : 'tables'}
                    </span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
