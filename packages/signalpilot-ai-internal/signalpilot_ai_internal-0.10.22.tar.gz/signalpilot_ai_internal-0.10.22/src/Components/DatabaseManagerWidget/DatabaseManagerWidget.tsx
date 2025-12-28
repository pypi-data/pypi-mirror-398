import * as React from 'react';
import { ReactWidget } from '@jupyterlab/ui-components';
import { ISignal, Signal } from '@lumino/signaling';
import { Subscription } from 'rxjs';
import {
  DatabaseStateService,
  DatabaseType,
  IDatabaseConfig,
  IMySQLPostgreSQLSchema,
  ISnowflakeSchemaData
} from '../../DatabaseStateService';
import {
  DatabaseCreationModal,
  IDatabaseFormData
} from '../DatabaseCreationModal/DatabaseCreationModal';
import { DATABASE_ICON } from '../../Chat/ChatContextMenu/icons';
import { AppStateService } from '../../AppState';
import { DatabaseSchemaExplorer } from './DatabaseSchemaExplorer';
import { SnowflakeSchemaViewer } from './SnowflakeSchemaViewer';
import { KernelUtils } from '../../utils/kernelUtils';
import { MYSQL_ICON, POSTGRESQL_ICON, SNOWFLAKE_ICON } from '../databaseIcons';

/**
 * Interface for the DatabaseManager widget state
 */
export interface IDatabaseManagerState {
  databases: IDatabaseConfig[];
  isLoading: boolean;
  isModalVisible: boolean;
  activeConfigId: string | null;
  editingConfig: IDatabaseConfig | null; // Config being edited
  loadingSchemaId: string | null; // ID of database currently loading schema
  selectedDatabaseForSchema: IDatabaseConfig | null; // Database selected for schema exploration
  initialDatabaseType: DatabaseType; // Initial database type to pre-select when opening modal
}

/**
 * Component for displaying database management content
 */
function DatabaseManagerContent({
  state,
  onAddDatabase,
  onEditDatabase,
  onDeleteDatabase,
  onSetActiveDatabase,
  onCloseModal,
  onCreateDatabase,
  onValidateSchema,
  onRefreshSchema,
  onSelectDatabaseForSchema,
  onBackToDatabaseList
}: {
  state: IDatabaseManagerState;
  onAddDatabase: () => void;
  onEditDatabase: (config: IDatabaseConfig) => void;
  onDeleteDatabase: (configId: string) => void;
  onSetActiveDatabase: (configId: string | null) => void;
  onCloseModal: () => void;
  onCreateDatabase: (formData: IDatabaseFormData) => Promise<void>;
  onValidateSchema: (
    formData: IDatabaseFormData
  ) => Promise<{ success: boolean; error?: string; schema?: string }>;
  onRefreshSchema: (config: IDatabaseConfig) => Promise<void>;
  onSelectDatabaseForSchema: (config: IDatabaseConfig) => void;
  onBackToDatabaseList: () => void;
}): JSX.Element {
  const getTypeIcon = (type: DatabaseType): JSX.Element => {
    switch (type) {
      case DatabaseType.PostgreSQL:
        return <POSTGRESQL_ICON.react className="db-icon" tag="span" />;
      case DatabaseType.MySQL:
        return <MYSQL_ICON.react className="db-icon" tag="span" />;
      case DatabaseType.Snowflake:
        return <SNOWFLAKE_ICON.react className="db-icon" tag="span" />;
      default:
        return <span className="db-icon">🗄️</span>; // Generic database
    }
  };

  const getTypeColor = (type: DatabaseType): string => {
    switch (type) {
      case DatabaseType.PostgreSQL:
        return '#336791';
      case DatabaseType.MySQL:
        return '#4479A1';
      case DatabaseType.Snowflake:
        return '#29B5E8';
      default:
        return '#666666';
    }
  };

  const formatDateTime = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return (
        date.toLocaleDateString() +
        ' ' +
        date.toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit'
        })
      );
    } catch {
      return 'Unknown';
    }
  };

  const handleAddToContext = async (config: IDatabaseConfig): Promise<void> => {
    console.log('[DatabaseManagerWidget] Add to context:', config.name);
    const chatContainer = AppStateService.getChatContainerSafe();
    if (!chatContainer) {
      console.error('[DatabaseManagerWidget] Chat container not available');
      return;
    }

    const chatMessages = chatContainer.chatWidget.messageComponent;
    if (!chatMessages) {
      console.error('[DatabaseManagerWidget] Chat messages not available');
      return;
    }

    try {
      // Use the same database helper as the context picker to create the context
      const { getDatabaseById } = await import(
        '../../Chat/ChatContextMenu/databaseHelper'
      );
      const databaseContext = await getDatabaseById(config.id);

      if (!databaseContext) {
        console.error(
          '[DatabaseManagerWidget] Could not create database context'
        );
        return;
      }

      // Add the context using the same method as the context picker
      // This ensures the exact same format and integration
      chatMessages.addMentionContext(databaseContext);

      console.log(
        '[DatabaseManagerWidget] Database context added through context picker flow:',
        databaseContext.name
      );
    } catch (error) {
      console.error(
        '[DatabaseManagerWidget] Failed to add database context:',
        error
      );
    }
  };

  const handleMenuAction = (
    configId: string,
    action: 'edit' | 'delete' | 'addToContext' | 'refreshSchema' | 'viewSchema'
  ) => {
    const config = state.databases.find(db => db.id === configId);
    if (!config) {
      return;
    }

    switch (action) {
      case 'edit':
        onEditDatabase(config);
        break;
      case 'delete':
        if (
          window.confirm(`Are you sure you want to delete "${config.name}"?`)
        ) {
          onDeleteDatabase(configId);
        }
        break;
      case 'addToContext':
        void handleAddToContext(config);
        break;
      case 'refreshSchema':
        void onRefreshSchema(config);
        break;
      case 'viewSchema':
        onSelectDatabaseForSchema(config);
        break;
    }
  };

  return (
    <div className="database-manager-widget">
      {/* If a database is selected for schema exploration, show the schema explorer */}
      {state.selectedDatabaseForSchema ? (
        <div className="database-schema-container">
          {state.selectedDatabaseForSchema.database_schema ? (
            // Check if this is a Snowflake database
            state.selectedDatabaseForSchema.type === DatabaseType.Snowflake ? (
              <SnowflakeSchemaViewer
                schemaData={
                  state.selectedDatabaseForSchema
                    .database_schema as ISnowflakeSchemaData
                }
                databaseName={state.selectedDatabaseForSchema.name}
                onBack={onBackToDatabaseList}
              />
            ) : (
              <DatabaseSchemaExplorer
                schema={
                  (
                    state.selectedDatabaseForSchema
                      .database_schema as IMySQLPostgreSQLSchema
                  ).table_schemas
                }
                databaseName={state.selectedDatabaseForSchema.name}
                onBack={onBackToDatabaseList}
              />
            )
          ) : (
            <div className="schema-not-loaded">
              <div className="schema-error-content">
                <h3>Schema Not Available</h3>
                <p>
                  Schema has not been loaded for "
                  {state.selectedDatabaseForSchema.name}".
                </p>
                <div className="schema-error-actions">
                  <button
                    onClick={() =>
                      onRefreshSchema(state.selectedDatabaseForSchema!)
                    }
                    className="refresh-schema-button"
                  >
                    🔄 Load Schema
                  </button>
                  <button
                    onClick={onBackToDatabaseList}
                    className="back-button"
                  >
                    ← Back to Databases
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Normal database list view */
        <>
          <div className="database-manager-header">
            <h3 className="database-manager-title">Databases</h3>
            <button
              className="database-add-button"
              onClick={onAddDatabase}
              title="Add new database"
            >
              <span className="add-icon">+</span>
              Add Database
            </button>
          </div>

          <div className="database-manager-content">
            {state.isLoading ? (
              <div className="database-loading">
                <div className="loading-spinner"></div>
                <span>Loading databases...</span>
              </div>
            ) : state.databases.length === 0 ? (
              <div className="database-empty-state">
                <div className="empty-icon">🗄️</div>
                <p>No databases configured</p>
                <p className="empty-description">
                  Add your first database connection to get started
                </p>
                <button
                  className="database-add-button-primary"
                  onClick={onAddDatabase}
                >
                  Add Your First Database
                </button>
              </div>
            ) : (
              <div className="database-list">
                {state.databases.map(database => (
                  <div
                    key={database.id}
                    className={`database-item ${database.id === state.activeConfigId ? 'active' : ''} ${!database.database_schema ? 'schema-warning' : ''}`}
                  >
                    {state.loadingSchemaId === database.id && (
                      <div className="loading-schema-overlay">
                        <div className="loading-schema-badge">
                          <div className="loading-spinner-small"></div>
                          Loading Schema
                        </div>
                      </div>
                    )}
                    <div className="database-item-header">
                      <div className="database-info">
                        <div className="database-type-indicator">
                          <span
                            className="database-type-icon"
                            style={{ color: getTypeColor(database.type) }}
                          >
                            {getTypeIcon(database.type)}
                          </span>
                          <span className="database-type-text">
                            {database.type.toUpperCase()}
                          </span>
                          {!database.database_schema && (
                            <span
                              className="schema-warning-icon"
                              title="Schema not loaded for this database"
                            >
                              ⚠️
                            </span>
                          )}
                        </div>
                        <h4 className="database-name">{database.name}</h4>
                        {database.name && (
                          <p className="database-description">
                            {database.credentials?.description || database.type}
                          </p>
                        )}
                      </div>

                      <div className="database-actions">
                        <div className="database-action-buttons">
                          <button
                            className="database-action-btn add-context-btn"
                            onClick={e => {
                              e.stopPropagation();
                              handleMenuAction(database.id, 'addToContext');
                            }}
                            title="Add to Context"
                          >
                            <svg
                              width="16"
                              height="16"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <circle cx="12" cy="12" r="10" />
                              <line x1="12" y1="8" x2="12" y2="16" />
                              <line x1="8" y1="12" x2="16" y2="12" />
                            </svg>
                          </button>

                          <button
                            className="database-action-btn view-schema-btn"
                            onClick={e => {
                              e.stopPropagation();
                              handleMenuAction(database.id, 'viewSchema');
                            }}
                            disabled={!database.database_schema}
                            title={
                              database.database_schema
                                ? 'View Schema'
                                : 'Schema not loaded'
                            }
                          >
                            <svg
                              width="16"
                              height="16"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                              <circle cx="12" cy="12" r="3" />
                            </svg>
                          </button>

                          <button
                            className="database-action-btn refresh-schema-btn"
                            onClick={e => {
                              e.stopPropagation();
                              handleMenuAction(database.id, 'refreshSchema');
                            }}
                            title="Refresh Schema"
                          >
                            <svg
                              width="16"
                              height="16"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <polyline points="23 4 23 10 17 10" />
                              <polyline points="1 20 1 14 7 14" />
                              <path d="m3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                            </svg>
                          </button>

                          <button
                            className="database-action-btn edit-btn"
                            onClick={e => {
                              e.stopPropagation();
                              handleMenuAction(database.id, 'edit');
                            }}
                            title="Edit Database"
                          >
                            <svg
                              width="16"
                              height="16"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                              <path d="m18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                            </svg>
                          </button>

                          <button
                            className="database-action-btn delete-btn"
                            onClick={e => {
                              e.stopPropagation();
                              handleMenuAction(database.id, 'delete');
                            }}
                            title="Delete Database"
                          >
                            <svg
                              width="16"
                              height="16"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <polyline points="3,6 5,6 21,6" />
                              <path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2" />
                              <line x1="10" y1="11" x2="10" y2="17" />
                              <line x1="14" y1="11" x2="14" y2="17" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>

                    <div className="database-item-details">
                      <div className="database-detail">
                        <span className="detail-label">Host:</span>
                        <span className="detail-value">
                          {database.type === DatabaseType.Snowflake || database.type === DatabaseType.Databricks
                            ? (database.credentials as any)?.connectionUrl ||
                              'N/A'
                            : `${database.credentials?.host || 'N/A'}:${database.credentials?.port || 'N/A'}`}
                        </span>
                      </div>
                      <div className="database-detail">
                        <span className="detail-label">Database:</span>
                        <span className="detail-value">
                          {database.credentials?.database || 'N/A'}
                        </span>
                      </div>
                      <div className="database-detail">
                        <span className="detail-label">Schema Loaded:</span>
                        <span className="detail-value">
                          {database.schema_last_updated
                            ? formatDateTime(database.schema_last_updated)
                            : 'Never'}
                        </span>
                      </div>
                    </div>

                    {database.id === state.activeConfigId && (
                      <div className="database-active-indicator">
                        <span className="active-badge">Active</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <DatabaseCreationModal
            isVisible={state.isModalVisible}
            onClose={onCloseModal}
            onCreateDatabase={onCreateDatabase}
            onValidateSchema={onValidateSchema}
            editConfig={state.editingConfig || undefined}
            initialType={state.initialDatabaseType || undefined}
          />
        </>
      )}
    </div>
  );
}

/**
 * Widget for managing database connections in the left sidebar
 */
export class DatabaseManagerWidget extends ReactWidget {
  private _state: IDatabaseManagerState;
  private _stateChanged = new Signal<this, IDatabaseManagerState>(this);
  private _subscriptions: Subscription[] = [];

  constructor() {
    super();
    this._state = {
      databases: [],
      isLoading: true,
      isModalVisible: false,
      activeConfigId: null,
      editingConfig: null,
      loadingSchemaId: null,
      selectedDatabaseForSchema: null,
      initialDatabaseType: DatabaseType.PostgreSQL
    };

    this.addClass('sage-ai-database-manager-widget');
    this.id = 'sage-ai-database-manager';
    this.title.icon = DATABASE_ICON;
    // this.title.label = 'Databases';
    this.title.closable = true;

    this.initializeSubscriptions();
    void this.loadDatabases();
  }

  /**
   * Get the signal that fires when state changes
   */
  public get stateChanged(): ISignal<this, IDatabaseManagerState> {
    return this._stateChanged;
  }

  /**
   * Initialize RxJS subscriptions to the DatabaseStateService
   */
  private initializeSubscriptions(): void {
    // Subscribe to state changes
    const stateChanges = DatabaseStateService.changes.subscribe(state => {
      this.updateState({
        databases: state.configurations,
        activeConfigId: state.activeConfigId
      });
    });
    this._subscriptions.push(stateChanges);

    // Subscribe to individual events for finer control
    const configAdded = DatabaseStateService.onConfigurationAdded().subscribe(
      () => {
        void this.loadDatabases();
      }
    );
    this._subscriptions.push(configAdded);

    const configRemoved =
      DatabaseStateService.onConfigurationRemoved().subscribe(() => {
        void this.loadDatabases();
      });
    this._subscriptions.push(configRemoved);

    const configUpdated =
      DatabaseStateService.onConfigurationUpdated().subscribe(() => {
        void this.loadDatabases();
      });
    this._subscriptions.push(configUpdated);

    const activeChanged =
      DatabaseStateService.onActiveConfigurationChanged().subscribe(event => {
        this.updateState({
          activeConfigId: event.newConfigId
        });
      });
    this._subscriptions.push(activeChanged);
  }

  /**
   * Load databases from the DatabaseStateService
   */
  private async loadDatabases(): Promise<void> {
    try {
      this.updateState({ isLoading: true });

      // Get current state from service
      const currentState = DatabaseStateService.getState();

      this.updateState({
        databases: currentState.configurations,
        activeConfigId: currentState.activeConfigId,
        isLoading: false
      });
    } catch (error) {
      console.error('[DatabaseManagerWidget] Failed to load databases:', error);
      this.updateState({ isLoading: false });
    }
  }

  /**
   * Update the internal state and emit changes
   */
  private updateState(partial: Partial<IDatabaseManagerState>): void {
    this._state = { ...this._state, ...partial };
    this._stateChanged.emit(this._state);
    this.update();
  }

  /**
   * Handle adding a new database
   */
  private handleAddDatabase = (databaseType?: DatabaseType): void => {
    this.updateState({
      isModalVisible: true,
      editingConfig: null,
      initialDatabaseType: databaseType || DatabaseType.PostgreSQL
    });
  };

  /**
   * Handle editing an existing database
   */
  private handleEditDatabase = (config: IDatabaseConfig): void => {
    console.log('[DatabaseManagerWidget] Edit database:', config.name);
    this.updateState({
      isModalVisible: true,
      editingConfig: config
    });
  };

  /**
   * Handle deleting a database
   */
  private handleDeleteDatabase = async (configId: string): Promise<void> => {
    try {
      await DatabaseStateService.removeConfigurationAndPersist(configId);
      console.log('[DatabaseManagerWidget] Database deleted successfully');
    } catch (error) {
      console.error(
        '[DatabaseManagerWidget] Failed to delete database:',
        error
      );
      // Could show an error notification here
    }
  };

  /**
   * Handle setting active database
   */
  private handleSetActiveDatabase = (configId: string | null): void => {
    try {
      DatabaseStateService.setActiveConfiguration(configId);
      console.log('[DatabaseManagerWidget] Active database changed:', configId);
    } catch (error) {
      console.error(
        '[DatabaseManagerWidget] Failed to set active database:',
        error
      );
    }
  };

  /**
   * Handle refreshing database schema
   */
  private handleRefreshSchema = async (
    config: IDatabaseConfig
  ): Promise<void> => {
    console.log('[DatabaseManagerWidget] Refreshing schema for:', config.name);

    try {
      // Set loading state
      this.updateState({ loadingSchemaId: config.id });

      // Build database URL from config based on type
      let databaseUrl: string | undefined;
      let snowflakeConfig: any;
      let databricksConfig: any;
      let dbType: any;

      switch (config.type) {
        case DatabaseType.PostgreSQL:
          databaseUrl = `postgresql://${config.credentials?.username}:${config.credentials?.password}@${config.credentials?.host}:${config.credentials?.port}/${config.credentials?.database}`;
          dbType = 'postgresql';
          break;
        case DatabaseType.MySQL:
          databaseUrl = `mysql://${config.credentials?.username}:${config.credentials?.password}@${config.credentials?.host}:${config.credentials?.port}/${config.credentials?.database}`;
          dbType = 'mysql';
          break;
        case DatabaseType.Snowflake:
          // eslint-disable-next-line no-case-declarations
          const snowflakeCredentials = config.credentials as any; // Type assertion for Snowflake-specific properties
          // For Snowflake, build a config object with connectionUrl
          snowflakeConfig = {
            type: 'snowflake',
            connectionUrl: snowflakeCredentials?.connectionUrl,
            username: config.credentials?.username,
            password: config.credentials?.password,
            warehouse: snowflakeCredentials?.warehouse || undefined,
            database: config.credentials?.database || undefined,
            role: snowflakeCredentials?.role || undefined
          };
          dbType = 'snowflake';
          break;
        case DatabaseType.Databricks:
          // eslint-disable-next-line no-case-declarations
          const databricksCredentials = config.credentials as any;
          // For Databricks, build a config object
          databricksConfig = {
            type: 'databricks',
            connectionUrl: databricksCredentials?.connectionUrl,
            authType: databricksCredentials?.authType || 'pat',
            accessToken: databricksCredentials?.accessToken,
            clientId: databricksCredentials?.clientId,
            clientSecret: databricksCredentials?.clientSecret,
            warehouseHttpPath: databricksCredentials?.warehouseHttpPath,
            catalog: databricksCredentials?.catalog,
            schema: databricksCredentials?.schema
          };
          dbType = 'databricks';
          break;
        default:
          throw new Error(`Unsupported database type: ${config.type}`);
      }

      // Create DatabaseTools instance and fetch schema
      const DatabaseTools = (await import('../../BackendTools/DatabaseTools'))
        .DatabaseTools;
      const databaseTools = new DatabaseTools();

      let schemaResult: string;
      if (dbType === 'snowflake' && snowflakeConfig) {
        // Import DatabaseType enum
        const { DatabaseType: DBToolsType } = await import(
          '../../BackendTools/DatabaseTools'
        );
        schemaResult = await databaseTools.getDatabaseMetadata(
          undefined,
          DBToolsType.Snowflake,
          snowflakeConfig
        );
      } else if (dbType === 'databricks' && databricksConfig) {
        // Import DatabaseType enum
        const { DatabaseType: DBToolsType } = await import(
          '../../BackendTools/DatabaseTools'
        );
        schemaResult = await databaseTools.getDatabaseMetadata(
          undefined,
          DBToolsType.Databricks,
          databricksConfig
        );
      } else {
        // Import DatabaseType enum
        const { DatabaseType: DBToolsType } = await import(
          '../../BackendTools/DatabaseTools'
        );
        const toolsDbType =
          dbType === 'postgresql' ? DBToolsType.PostgreSQL : DBToolsType.MySQL;
        schemaResult = await databaseTools.getDatabaseMetadata(
          databaseUrl,
          toolsDbType
        );
      }

      // Parse the result
      let parsedResult;
      try {
        parsedResult = JSON.parse(schemaResult);
      } catch (parseError) {
        throw new Error(`Failed to parse schema result: ${parseError}`);
      }

      if (parsedResult.error) {
        throw new Error(parsedResult.error);
      }

      // Store the parsed schema object directly
      const schemaToStore = parsedResult.schema_info
        ? typeof parsedResult.schema_info === 'string'
          ? JSON.parse(parsedResult.schema_info)
          : parsedResult.schema_info
        : parsedResult;

      // Update the configuration with new schema information
      const updateSuccess = DatabaseStateService.updateConfiguration(
        config.id,
        {
          database_schema: schemaToStore,
          schema_last_updated: new Date().toISOString()
        }
      );

      if (updateSuccess) {
        // Save the updated configuration to StateDB
        await DatabaseStateService.saveConfigurationsToStateDB();
        console.log('[DatabaseManagerWidget] Schema refreshed successfully');

        // Load database variables into kernel after successful schema refresh
        console.log(
          '[DatabaseManagerWidget] Loading database variables into kernel after schema refresh...'
        );
        try {
          await KernelUtils.setDatabaseEnvironmentsInKernelWithRetry();
          console.log(
            '[DatabaseManagerWidget] Database variables loaded into kernel successfully after schema refresh'
          );
        } catch (kernelError) {
          console.warn(
            '[DatabaseManagerWidget] Failed to load database variables into kernel after schema refresh:',
            kernelError
          );
          // Don't throw error since schema refresh was successful
          // Just log the warning and continue
        }
      } else {
        throw new Error(
          'Failed to update configuration with schema information'
        );
      }
    } catch (error) {
      console.error('[DatabaseManagerWidget] Failed to refresh schema:', error);
      alert(
        `Failed to refresh schema: ${error instanceof Error ? error.message : String(error)}`
      );
    } finally {
      // Clear loading state
      this.updateState({ loadingSchemaId: null });
    }
  };

  /**
   * Handle closing the creation modal
   */
  private handleCloseModal = (): void => {
    this.updateState({
      isModalVisible: false,
      editingConfig: null,
      initialDatabaseType: DatabaseType.PostgreSQL
    });
  };

  /**
   * Handle creating a new database from the modal
   */
  private handleCreateDatabase = async (
    formData: IDatabaseFormData
  ): Promise<void> => {
    try {
      let configId: string;

      // Check if we're editing an existing config
      if (formData.id && this._state.editingConfig) {
        // Update existing configuration
        await DatabaseStateService.updateConfigurationFromFormDataAndPersist(
          formData.id,
          formData.name,
          formData.description,
          formData.type,
          formData.connectionMethod === 'config'
            ? 'credentials'
            : formData.connectionMethod,
          formData.host,
          formData.port,
          formData.database,
          formData.username,
          formData.password,
          formData.type === DatabaseType.Snowflake
            ? formData.snowflakeConnectionUrl
            : formData.type === DatabaseType.Databricks
            ? formData.databricksConnectionUrl
            : formData.connectionUrl,
          formData.warehouse,
          undefined, // account is no longer used for Snowflake
          formData.role,
          formData.databricksAuthType,
          formData.databricksAccessToken,
          formData.databricksClientId,
          formData.databricksClientSecret,
          formData.databricksWarehouseHttpPath,
          formData.databricksCatalog || '',
          formData.databricksSchema
        );
        configId = formData.id;
        console.log('[DatabaseManagerWidget] Database updated successfully');
      } else {
        // Create new configuration based on type
        let createdConfig: IDatabaseConfig;

        switch (formData.type) {
          case DatabaseType.MySQL:
            createdConfig =
              await DatabaseStateService.createAndPersistMySQLConfig(
                formData.name,
                formData.description,
                formData.host,
                formData.port,
                formData.database,
                formData.username,
                formData.password
              );
            break;
          case DatabaseType.PostgreSQL:
            createdConfig =
              await DatabaseStateService.createAndPersistPostgreSQLConfig(
                formData.name,
                formData.description,
                formData.host,
                formData.port,
                formData.database,
                formData.username,
                formData.password
              );
            break;
          case DatabaseType.Snowflake:
            createdConfig =
              await DatabaseStateService.createAndPersistSnowflakeConfig(
                formData.name,
                formData.description,
                formData.snowflakeConnectionUrl,
                formData.username,
                formData.password,
                formData.database || undefined,
                formData.warehouse || undefined,
                formData.role || undefined
              );
            break;
          case DatabaseType.Databricks:
            createdConfig =
              await DatabaseStateService.createAndPersistDatabricksConfig(
                formData.name,
                formData.description,
                formData.databricksConnectionUrl || '',
                formData.databricksAuthType || 'pat',
                formData.databricksCatalog || '',
                formData.databricksAccessToken,
                formData.databricksClientId,
                formData.databricksClientSecret,
                formData.databricksWarehouseHttpPath,
                formData.databricksSchema
              );
            break;
          default:
            throw new Error(`Unsupported database type: ${formData.type}`);
        }
        configId = createdConfig.id;
        console.log('[DatabaseManagerWidget] Database created successfully');
      }

      // If we have schema information from validation, update the configuration
      if (formData.schema && formData.schemaLastUpdated) {
        console.log(
          '[DatabaseManagerWidget] Updating configuration with schema information...'
        );

        // Parse the schema string to the appropriate type
        let parsedSchema: IMySQLPostgreSQLSchema | ISnowflakeSchemaData | null =
          null;
        try {
          parsedSchema =
            typeof formData.schema === 'string'
              ? JSON.parse(formData.schema)
              : formData.schema;
        } catch (error) {
          console.error(
            '[DatabaseManagerWidget] Failed to parse schema:',
            error
          );
        }

        const updateSuccess = DatabaseStateService.updateConfiguration(
          configId,
          {
            database_schema: parsedSchema,
            schema_last_updated: formData.schemaLastUpdated
          }
        );

        if (updateSuccess) {
          // Save the updated configuration to StateDB
          await DatabaseStateService.saveConfigurationsToStateDB();
          console.log(
            '[DatabaseManagerWidget] Schema information cached successfully'
          );
        } else {
          console.warn(
            '[DatabaseManagerWidget] Failed to update configuration with schema information'
          );
        }
      }

      this.updateState({
        isModalVisible: false,
        editingConfig: null,
        initialDatabaseType: DatabaseType.PostgreSQL
      });

      // Load database variables into kernel after successful database creation/update
      console.log(
        '[DatabaseManagerWidget] Loading database variables into kernel...'
      );
      try {
        await KernelUtils.setDatabaseEnvironmentsInKernelWithRetry();
        console.log(
          '[DatabaseManagerWidget] Database variables loaded into kernel successfully'
        );
      } catch (kernelError) {
        console.warn(
          '[DatabaseManagerWidget] Failed to load database variables into kernel:',
          kernelError
        );
        // Don't throw error since database creation/update was successful
        // Just log the warning and continue
      }
    } catch (error) {
      console.error(
        '[DatabaseManagerWidget] Failed to create/update database:',
        error
      );
      throw error; // Re-throw to let modal handle the error
    }
  };

  /**
   * Handle schema validation for a database configuration
   */
  private handleValidateSchema = async (
    formData: IDatabaseFormData
  ): Promise<{ success: boolean; error?: string; schema?: string }> => {
    try {
      console.log(
        '[DatabaseManagerWidget] Validating schema for database:',
        formData.name
      );

      // Build database URL from form data
      let databaseUrl: string | undefined;
      let snowflakeConfig: any;
      let databricksConfig: any;
      let dbType: string;

      if (formData.connectionMethod === 'url') {
        databaseUrl = formData.connectionUrl;
        // Detect type from URL
        if (databaseUrl.startsWith('postgresql://')) {
          dbType = 'postgresql';
        } else if (databaseUrl.startsWith('mysql://')) {
          dbType = 'mysql';
        } else if (databaseUrl.startsWith('snowflake://')) {
          dbType = 'snowflake';
        } else {
          dbType = 'postgresql'; // Default
        }
      } else {
        // Build connection URL based on database type from credentials
        switch (formData.type) {
          case DatabaseType.PostgreSQL:
            databaseUrl = `postgresql://${formData.username}:${formData.password}@${formData.host}:${formData.port}/${formData.database}`;
            dbType = 'postgresql';
            break;
          case DatabaseType.MySQL:
            databaseUrl = `mysql://${formData.username}:${formData.password}@${formData.host}:${formData.port}/${formData.database}`;
            dbType = 'mysql';
            break;
          case DatabaseType.Snowflake:
            // For Snowflake, build a config object
            snowflakeConfig = {
              type: 'snowflake',
              connectionUrl: formData.snowflakeConnectionUrl,
              username: formData.username,
              password: formData.password,
              warehouse: formData.warehouse,
              database: formData.database,
              role: formData.role
            };
            dbType = 'snowflake';
            break;
          case DatabaseType.Databricks:
            // For Databricks, build a config object
            databricksConfig = {
              type: 'databricks',
              connectionUrl: formData.databricksConnectionUrl,
              authType: formData.databricksAuthType || 'pat',
              accessToken: formData.databricksAccessToken,
              clientId: formData.databricksClientId,
              clientSecret: formData.databricksClientSecret,
              warehouseHttpPath: formData.databricksWarehouseHttpPath,
              catalog: formData.databricksCatalog,
              schema: formData.databricksSchema
            };
            dbType = 'databricks';
            break;
          default:
            return {
              success: false,
              error: 'Unsupported database type for schema validation'
            };
        }
      }

      // Create DatabaseTools instance and test connection by fetching schema
      const DatabaseTools = (await import('../../BackendTools/DatabaseTools'))
        .DatabaseTools;
      const { DatabaseType: DBToolsType } = await import(
        '../../BackendTools/DatabaseTools'
      );
      const databaseTools = new DatabaseTools();

      let schemaResult: string;
      if (dbType === 'snowflake' && snowflakeConfig) {
        schemaResult = await databaseTools.getDatabaseMetadata(
          undefined,
          DBToolsType.Snowflake,
          snowflakeConfig
        );
      } else if (dbType === 'databricks' && databricksConfig) {
        schemaResult = await databaseTools.getDatabaseMetadata(
          undefined,
          DBToolsType.Databricks,
          databricksConfig
        );
      } else {
        const toolsDbType =
          dbType === 'postgresql' ? DBToolsType.PostgreSQL : DBToolsType.MySQL;
        schemaResult = await databaseTools.getDatabaseMetadata(
          databaseUrl,
          toolsDbType
        );
      }

      // Parse the result
      let parsedResult;
      try {
        parsedResult = JSON.parse(schemaResult);
      } catch (parseError) {
        return {
          success: false,
          error: `Failed to parse schema result: ${parseError}`
        };
      }

      if (parsedResult.error) {
        return { success: false, error: parsedResult.error };
      }

      // Parse the schema if it's a string
      const schemaToReturn = parsedResult.schema_info
        ? typeof parsedResult.schema_info === 'string'
          ? JSON.parse(parsedResult.schema_info)
          : parsedResult.schema_info
        : parsedResult;

      console.log('[DatabaseManagerWidget] Schema validation successful');
      return {
        success: true,
        schema: schemaToReturn
      };
    } catch (error) {
      console.error('[DatabaseManagerWidget] Schema validation error:', error);
      return {
        success: false,
        error: `Schema validation failed: ${error instanceof Error ? error.message : String(error)}`
      };
    }
  };

  /**
   * Handle selecting a database for schema exploration
   */
  private handleSelectDatabaseForSchema = (config: IDatabaseConfig): void => {
    this._state = {
      ...this._state,
      selectedDatabaseForSchema: config
    };
    this._stateChanged.emit(this._state);
    this.update();
  };

  /**
   * Handle navigating back to the database list from schema view
   */
  private handleBackToDatabaseList = (): void => {
    this._state = {
      ...this._state,
      selectedDatabaseForSchema: null
    };
    this._stateChanged.emit(this._state);
    this.update();
  };

  /**
   * Render the React component
   */
  render(): JSX.Element {
    return (
      <DatabaseManagerContent
        state={this._state}
        onAddDatabase={this.handleAddDatabase}
        onEditDatabase={this.handleEditDatabase}
        onDeleteDatabase={this.handleDeleteDatabase}
        onSetActiveDatabase={this.handleSetActiveDatabase}
        onCloseModal={this.handleCloseModal}
        onCreateDatabase={this.handleCreateDatabase}
        onValidateSchema={this.handleValidateSchema}
        onRefreshSchema={this.handleRefreshSchema}
        onSelectDatabaseForSchema={this.handleSelectDatabaseForSchema}
        onBackToDatabaseList={this.handleBackToDatabaseList}
      />
    );
  }

  /**
   * Dispose of the widget and clean up subscriptions
   */
  dispose(): void {
    if (this.isDisposed) {
      return;
    }

    // Clean up all subscriptions
    this._subscriptions.forEach(subscription => subscription.unsubscribe());
    this._subscriptions = [];

    super.dispose();
  }
}
