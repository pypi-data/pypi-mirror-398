import * as React from 'react';
import { useState } from 'react';
import { AppStateService } from '../../AppState';
import { IMentionContext } from '../../Chat/ChatContextMenu/ChatContextLoaders';
import { IDatabaseColumn, ITableSchema } from '../../DatabaseStateService';

/**
 * Interface for database schema (collection of tables)
 */
export interface IDatabaseSchema {
  [tableName: string]: ITableSchema;
}

/**
 * Props for the DatabaseSchemaExplorer component
 */
export interface IDatabaseSchemaExplorerProps {
  schema: IDatabaseSchema;
  databaseName: string;
  onBack?: () => void;
}

/**
 * Component for exploring database schema - shows tables and their details
 */
export function DatabaseSchemaExplorer({
  schema,
  databaseName,
  onBack
}: IDatabaseSchemaExplorerProps) {
  console.log('schema', schema);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Get list of tables, filtered by search term
  const tables = Object.keys(schema).filter(
    tableName =>
      tableName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      schema[tableName].table_name
        .toLowerCase()
        .includes(searchTerm.toLowerCase())
  );

  const handleTableClick = (tableName: string) => {
    setSelectedTable(tableName);
  };

  const handleBackToTables = () => {
    setSelectedTable(null);
  };

  const formatDataType = (column: IDatabaseColumn): string => {
    let type = column.data_type;

    if (column.character_maximum_length) {
      type += `(${column.character_maximum_length})`;
    } else if (column.numeric_precision && column.numeric_scale !== null) {
      type += `(${column.numeric_precision},${column.numeric_scale})`;
    } else if (column.numeric_precision) {
      type += `(${column.numeric_precision})`;
    }

    return type;
  };

  const handleAddTableToContext = async (
    tableSchema: ITableSchema
  ): Promise<void> => {
    try {
      const chatMessages =
        AppStateService.getState().chatContainer?.chatWidget.messageComponent;
      if (!chatMessages) {
        console.error('[DatabaseSchemaExplorer] Chat messages not available');
        return;
      }

      // Create table schema content with detailed information
      const tableContent = `Table: ${tableSchema.full_name}
Schema: ${tableSchema.schema}

Columns (${tableSchema.columns.length}):
${tableSchema.columns
  .map(
    col =>
      `- ${col.column_name}: ${formatDataType(col)}${col.is_nullable === 'YES' ? ' (nullable)' : ' (not null)'}${col.column_default ? ` default: ${col.column_default}` : ''}`
  )
  .join('\n')}

${tableSchema.primary_keys.length > 0 ? `Primary Keys: ${tableSchema.primary_keys.join(', ')}` : ''}

${
  tableSchema.foreign_keys.length > 0
    ? `Foreign Keys:\n${tableSchema.foreign_keys
        .map(
          fk =>
            `- ${fk.column_name} → ${fk.foreign_table_schema}.${fk.foreign_table_name}.${fk.foreign_column_name}`
        )
        .join('\n')}`
    : ''
}

${
  tableSchema.indices.length > 0
    ? `Indices:\n${tableSchema.indices
        .map(idx => `- ${idx.indexname}: ${idx.indexdef}`)
        .join('\n')}`
    : ''
}`;

      const context: IMentionContext = {
        type: 'data',
        id: `table-${tableSchema.full_name}`,
        name: tableSchema.table_name,
        description: `Database table: ${tableSchema.full_name} (${tableSchema.columns.length} columns)`,
        content: tableContent,
        path: tableSchema.full_name
      };

      chatMessages.addMentionContext(context);
      console.log(
        `[DatabaseSchemaExplorer] Added table ${tableSchema.table_name} to context`
      );
    } catch (error) {
      console.error(
        '[DatabaseSchemaExplorer] Error adding table to context:',
        error
      );
    }
  };

  // If a table is selected, show table details
  if (selectedTable) {
    const tableSchema = schema[selectedTable];

    return (
      <div className="database-schema-explorer">
        <div className="schema-explorer-header">
          <button
            onClick={handleBackToTables}
            className="back-button"
            title="Back to tables"
          >
            ← Back
          </button>
          <div className="table-title-section">
            <h3 className="table-title">{tableSchema.table_name}</h3>
            <span className="table-full-name">{tableSchema.full_name}</span>
          </div>
          {/*<button*/}
          {/*  className="add-to-context-button detail-view-button"*/}
          {/*  onClick={() => handleAddTableToContext(tableSchema)}*/}
          {/*  title={`Add ${tableSchema.table_name} to context`}*/}
          {/*>*/}
          {/*  <span className="add-to-context-icon">+</span>*/}
          {/*  Add to Context*/}
          {/*</button>*/}
        </div>

        <div className="table-details">
          {/* Columns Section */}
          <div className="schema-section">
            <h4 className="section-title">
              Columns ({tableSchema.columns.length})
            </h4>
            <div className="columns-table">
              <div className="columns-header">
                <div className="column-name-header">Name</div>
                <div className="column-type-header">Type</div>
                <div className="column-nullable-header">Nullable</div>
                <div className="column-default-header">Default</div>
              </div>
              {tableSchema.columns.map((column, index) => (
                <div key={index} className="column-row">
                  <div className="column-name">
                    <span
                      className={`column-name-text ${tableSchema.primary_keys.includes(column.column_name) ? 'primary-key' : ''}`}
                    >
                      {column.column_name}
                    </span>
                    {tableSchema.primary_keys.includes(column.column_name) && (
                      <span
                        className="primary-key-indicator"
                        title="Primary Key"
                      >
                        🔑
                      </span>
                    )}
                    {tableSchema.foreign_keys.some(
                      fk => fk.column_name === column.column_name
                    ) && (
                      <span
                        className="foreign-key-indicator"
                        title="Foreign Key"
                      >
                        🔗
                      </span>
                    )}
                  </div>
                  <div className="column-type">{formatDataType(column)}</div>
                  <div className="column-nullable">
                    {column.is_nullable === 'YES' ? '✓' : '✗'}
                  </div>
                  <div className="column-default">
                    {column.column_default || '-'}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Primary Keys Section */}
          {tableSchema.primary_keys.length > 0 && (
            <div className="schema-section">
              <h4 className="section-title">
                Primary Keys ({tableSchema.primary_keys.length})
              </h4>
              <div className="keys-list">
                {tableSchema.primary_keys.map((key, index) => (
                  <span key={index} className="key-item primary-key-item">
                    🔑 {key}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Foreign Keys Section */}
          {tableSchema.foreign_keys.length > 0 && (
            <div className="schema-section">
              <h4 className="section-title">
                Foreign Keys ({tableSchema.foreign_keys.length})
              </h4>
              <div className="foreign-keys-list">
                {tableSchema.foreign_keys.map((fk, index) => (
                  <div key={index} className="foreign-key-item">
                    <span className="fk-column">🔗 {fk.column_name}</span>
                    <span className="fk-arrow">→</span>
                    <span className="fk-reference">
                      {fk.foreign_table_schema}.{fk.foreign_table_name}.
                      {fk.foreign_column_name}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Indices Section */}
          {tableSchema.indices.length > 0 && (
            <div className="schema-section">
              <h4 className="section-title">
                Indices ({tableSchema.indices.length})
              </h4>
              <div className="indices-list">
                {tableSchema.indices.map((index, idx) => (
                  <div key={idx} className="index-item">
                    <div className="index-name">📊 {index.indexname}</div>
                    <div className="index-definition">{index.indexdef}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Show tables list
  return (
    <div className="database-schema-explorer">
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
        <h3 className="database-title">{databaseName} Schema</h3>
        {/*<span className="tables-count">({tables.length} tables)</span>*/}
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
        {tables.length === 0 ? (
          <div className="no-tables">
            {searchTerm
              ? 'No tables match your search.'
              : 'No tables found in this database.'}
          </div>
        ) : (
          tables.map(tableName => {
            const tableSchema = schema[tableName];
            return (
              <div
                key={tableName}
                className="table-item"
                title={`Click to view ${tableSchema.table_name} schema`}
              >
                <div
                  className="table-item-content"
                  onClick={() => handleTableClick(tableName)}
                >
                  <div className="table-item-header">
                    <div className="table-name-section">
                      <div className="table-name">{tableSchema.table_name}</div>
                      <div className="table-full-name">
                        {tableSchema.full_name}
                      </div>
                    </div>
                    <button
                      className="add-to-context-button"
                      onClick={e => {
                        e.stopPropagation();
                        void handleAddTableToContext(tableSchema);
                      }}
                      title={`Add ${tableSchema.table_name} to context`}
                    >
                      <span className="add-to-context-icon">+</span>
                      Add to Context
                    </button>
                  </div>
                  <div className="table-item-stats">
                    <span className="table-stat">
                      � {tableSchema.columns.length} columns
                    </span>
                    {tableSchema.primary_keys.length > 0 && (
                      <span className="table-stat">
                        � {tableSchema.primary_keys.length} primary keys
                      </span>
                    )}
                    {tableSchema.foreign_keys.length > 0 && (
                      <span className="table-stat">
                        🔗 {tableSchema.foreign_keys.length} foreign keys
                      </span>
                    )}
                    {tableSchema.indices.length > 0 && (
                      <span className="table-stat">
                        📊 {tableSchema.indices.length} indices
                      </span>
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
