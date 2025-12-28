import * as React from 'react';
import { Modal, Button, Form, Alert } from 'react-bootstrap';
import {
  DatabaseType,
  IDatabaseConfig,
  DatabaseStateService,
  IDatabricksCredentials,
  DatabricksAuthType
} from '../../DatabaseStateService';
import { SQLDataForm, SQLConnectionMethod } from './SQLDataForm';
import { SnowflakeDataForm } from './SnowflakeDataForm';
import { DatabricksDataForm } from './DatabricksDataForm';
import {
  POSTGRESQL_ICON,
  MYSQL_ICON,
  SNOWFLAKE_ICON,
  DATABRICKS_ICON,
  CONNECTION_ICON
} from '../databaseIcons';

/**
 * Props for the DatabaseCreationModal component
 */
export interface IDatabaseCreationModalProps {
  isVisible: boolean;
  onClose: () => void;
  onCreateDatabase: (dbConfig: IDatabaseFormData) => Promise<void>;
  onValidateSchema?: (
    dbConfig: IDatabaseFormData
  ) => Promise<{ success: boolean; error?: string; schema?: string }>;
  editConfig?: IDatabaseConfig; // Optional config to edit
  initialType?: DatabaseType; // Optional initial database type to pre-select
}

/**
 * Connection method type
 */
export type ConnectionMethod = 'url' | 'config';

/**
 * Database form data interface
 */
export interface IDatabaseFormData {
  id?: string; // Include ID for updates
  name: string;
  description: string;
  type: DatabaseType;
  connectionMethod: ConnectionMethod;
  connectionUrl: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  // Snowflake-specific fields
  snowflakeConnectionUrl: string; // Snowflake connection URL
  warehouse?: string; // Optional for Snowflake
  role?: string; // Optional for Snowflake
  // Databricks-specific fields
  databricksConnectionUrl?: string;
  databricksAuthType?: DatabricksAuthType;
  databricksAccessToken?: string;
  databricksClientId?: string;
  databricksClientSecret?: string;
  databricksWarehouseHttpPath?: string;
  databricksCatalog?: string;
  databricksSchema?: string;
  // Legacy field - to be removed
  account: string;
  // Schema information (populated after successful validation)
  schema?: string;
  schemaLastUpdated?: string;
}

/**
 * Database creation modal component for adding database configurations
 */
export function DatabaseCreationModal({
  isVisible,
  onClose,
  onCreateDatabase,
  onValidateSchema,
  editConfig,
  initialType
}: IDatabaseCreationModalProps): JSX.Element | null {
  const [formData, setFormData] = React.useState<IDatabaseFormData>({
    name: '',
    description: '',
    type: DatabaseType.PostgreSQL,
    connectionMethod: 'config',
    connectionUrl: '',
    host: 'localhost',
    port: 5432,
    database: '',
    username: '',
    password: '',
    snowflakeConnectionUrl: '',
    warehouse: '',
    account: '',
    role: '',
    databricksConnectionUrl: '',
    databricksAuthType: 'pat',
    databricksAccessToken: '',
    databricksClientId: '',
    databricksClientSecret: '',
    databricksWarehouseHttpPath: '',
    databricksCatalog: '',
    databricksSchema: '',
    schema: undefined,
    schemaLastUpdated: undefined
  });

  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [isCheckingSchema, setIsCheckingSchema] = React.useState(false);
  const [errors, setErrors] = React.useState<Partial<IDatabaseFormData>>({});
  const [databaseError, setDatabaseError] = React.useState<string>('');
  const [duplicateNameWarning, setDuplicateNameWarning] =
    React.useState<string>('');
  const [schemaError, setSchemaError] = React.useState<{
    show: boolean;
    message: string;
    formData?: IDatabaseFormData;
  }>({ show: false, message: '' });

  // Helper function to get default form data
  const getDefaultFormData = (dbType?: DatabaseType): IDatabaseFormData => {
    const type = dbType || DatabaseType.PostgreSQL;
    const defaultPorts: { [key: string]: number } = {
      [DatabaseType.PostgreSQL]: 5432,
      [DatabaseType.MySQL]: 3306,
      [DatabaseType.Snowflake]: 443,
      [DatabaseType.Databricks]: 443
    };

    return {
      name: '',
      description: '',
      type: type,
      connectionMethod: 'config',
      connectionUrl: '',
      host: 'localhost',
      port: defaultPorts[type] || 5432,
      database: '',
      username: '',
      password: '',
      snowflakeConnectionUrl: '',
      warehouse: '',
      account: '',
      role: '',
      databricksConnectionUrl: '',
      databricksAuthType: 'pat',
      databricksAccessToken: '',
      databricksClientId: '',
      databricksClientSecret: '',
      databricksWarehouseHttpPath: '',
      databricksCatalog: '',
      databricksSchema: '',
      schema: undefined,
      schemaLastUpdated: undefined
    };
  };

  // Helper function to convert database config to form data for editing
  const configToFormData = (config: IDatabaseConfig): IDatabaseFormData => {
    const baseData: IDatabaseFormData = {
      id: config.id, // Include ID for updates
      name: config.name,
      description:
        config.credentials?.description ||
        config.urlConnection?.description ||
        '',
      type: config.type,
      connectionMethod:
        config.connectionType === 'credentials' ? 'config' : 'url',
      connectionUrl: config.urlConnection?.connectionUrl || '',
      host: config.credentials?.host || 'localhost',
      port: config.credentials?.port || 5432,
      database:
        config.credentials?.database || config.urlConnection?.name || '',
      username: config.credentials?.username || '',
      password: config.credentials?.password || '',
      snowflakeConnectionUrl: '',
      warehouse: '',
      account: '',
      role: '',
      databricksConnectionUrl: '',
      databricksAuthType: 'pat',
      databricksAccessToken: '',
      databricksClientId: '',
      databricksClientSecret: '',
      databricksWarehouseHttpPath: '',
      databricksCatalog: '',
      databricksSchema: '',
      // Include existing schema information - convert to string for form
      schema: config.database_schema
        ? JSON.stringify(config.database_schema)
        : undefined,
      schemaLastUpdated: config.schema_last_updated || undefined
    };

    // Handle Snowflake-specific fields
    if (
      config.type === DatabaseType.Snowflake &&
      config.credentials &&
      'connectionUrl' in config.credentials
    ) {
      const snowflakeCredentials = config.credentials as any;
      baseData.snowflakeConnectionUrl =
        snowflakeCredentials.connectionUrl || '';
      baseData.warehouse = snowflakeCredentials.warehouse || '';
      baseData.role = snowflakeCredentials.role || '';
      // Also extract database, username, and password specifically for Snowflake
      if (snowflakeCredentials.database) {
        baseData.database = snowflakeCredentials.database;
      }
      if (snowflakeCredentials.username) {
        baseData.username = snowflakeCredentials.username;
      }
      if (snowflakeCredentials.password) {
        baseData.password = snowflakeCredentials.password;
      }
    }

    // Handle Databricks-specific fields
    if (
      config.type === DatabaseType.Databricks &&
      config.credentials &&
      'connectionUrl' in config.credentials
    ) {
      const databricksCredentials = config.credentials as IDatabricksCredentials;
      baseData.databricksConnectionUrl =
        databricksCredentials.connectionUrl || '';
      baseData.databricksAuthType = databricksCredentials.authType || 'pat';
      baseData.databricksAccessToken = databricksCredentials.accessToken || '';
      baseData.databricksClientId = databricksCredentials.clientId || '';
      baseData.databricksClientSecret = databricksCredentials.clientSecret || '';
      baseData.databricksWarehouseHttpPath =
        databricksCredentials.warehouseHttpPath || '';
      baseData.databricksCatalog = databricksCredentials.catalog || '';
      baseData.databricksSchema = databricksCredentials.schema || '';
    }

    return baseData;
  };

  // Reset form when modal closes or when editConfig changes
  React.useEffect(() => {
    if (!isVisible) {
      setFormData(getDefaultFormData());
      setErrors({});
      setDatabaseError('');
      setDuplicateNameWarning('');
      setIsSubmitting(false);
      setIsCheckingSchema(false);
      setSchemaError({ show: false, message: '' });
    } else if (editConfig) {
      // Modal is opening with edit config
      setFormData(configToFormData(editConfig));
      setErrors({});
      setDatabaseError('');
      setDuplicateNameWarning('');
      setIsSubmitting(false);
      setIsCheckingSchema(false);
      setSchemaError({ show: false, message: '' });
    } else {
      // Modal is opening for new creation - use initialType if provided
      setFormData(getDefaultFormData(initialType));
      setErrors({});
      setDatabaseError('');
      setDuplicateNameWarning('');
      setIsSubmitting(false);
      setIsCheckingSchema(false);
      setSchemaError({ show: false, message: '' });
    }
  }, [isVisible, editConfig, initialType]);

  // Update default port when database type changes
  React.useEffect(() => {
    const defaultPorts: { [key: string]: number } = {
      [DatabaseType.PostgreSQL]: 5432,
      [DatabaseType.MySQL]: 3306,
      [DatabaseType.Snowflake]: 443,
      [DatabaseType.Databricks]: 443
    };

    setFormData(prev => ({
      ...prev,
      port: defaultPorts[prev.type] || 5432,
      // Force config method for Snowflake and Databricks since they don't support URL connections
      connectionMethod:
        prev.type === DatabaseType.Snowflake ||
        prev.type === DatabaseType.Databricks
          ? 'config'
          : prev.connectionMethod
    }));
  }, [formData.type]);

  const handleInputChange = (
    field: keyof IDatabaseFormData,
    value: string | number | DatabaseType
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }

    // Clear database error when user modifies form
    if (databaseError) {
      setDatabaseError('');
    }

    // Clear duplicate name warning when user modifies name field
    if (field === 'name' && duplicateNameWarning) {
      setDuplicateNameWarning('');
    }

    // Run duplicate name validation in real-time for name field
    if (field === 'name' && typeof value === 'string') {
      const trimmedName = value.trim();
      if (trimmedName) {
        const existingConfigs = DatabaseStateService.getConfigurations();
        const duplicateConfig = existingConfigs.find(
          config =>
            config.name.toLowerCase() === trimmedName.toLowerCase() &&
            config.id !== formData.id // Exclude current config when editing
        );

        if (duplicateConfig) {
          setDuplicateNameWarning(
            `A database with the name "${trimmedName}" already exists. Database names must be unique.`
          );
        }
      }
    }
  };

  const parseConnectionUrl = (url: string) => {
    try {
      const urlObj = new URL(url);

      // Get default port based on protocol
      let defaultPort = 5432; // PostgreSQL default
      if (urlObj.protocol === 'mysql:') {
        defaultPort = 3306;
      }

      return {
        host: urlObj.hostname,
        port: parseInt(urlObj.port) || defaultPort,
        database: urlObj.pathname.slice(1) || '',
        username: urlObj.username,
        password: urlObj.password
      };
    } catch {
      return null;
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<IDatabaseFormData> = {};

    // Common validation
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else {
      // Check for duplicate names
      const existingConfigs = DatabaseStateService.getConfigurations();
      const duplicateConfig = existingConfigs.find(
        config =>
          config.name.toLowerCase() === formData.name.trim().toLowerCase() &&
          config.id !== formData.id // Exclude current config when editing
      );

      if (duplicateConfig) {
        setDuplicateNameWarning(
          `A database with the name "${formData.name.trim()}" already exists. Database names must be unique.`
        );
      } else {
        setDuplicateNameWarning('');
      }
    }

    // Snowflake-specific validation
    if (formData.type === DatabaseType.Snowflake) {
      if (!formData.snowflakeConnectionUrl.trim()) {
        newErrors.snowflakeConnectionUrl = 'Connection URL is required' as any;
      }
      if (!formData.username.trim()) {
        newErrors.username = 'Username is required';
      }
      if (!formData.password.trim()) {
        newErrors.password = 'Password is required';
      }
      // warehouse, role, and database are optional - no validation needed
    } else if (formData.type === DatabaseType.Databricks) {
      // Databricks-specific validation
      if (!formData.databricksConnectionUrl?.trim()) {
        newErrors.databricksConnectionUrl =
          'Workspace URL is required' as any;
      }
      if (!formData.databricksWarehouseHttpPath?.trim()) {
        newErrors.databricksWarehouseHttpPath =
          'SQL Warehouse HTTP Path is required' as any;
      }
      // PAT authentication
      if (formData.databricksAuthType === 'pat') {
        if (!formData.databricksAccessToken?.trim()) {
          newErrors.databricksAccessToken = 'Access Token is required' as any;
        }
      } else if (formData.databricksAuthType === 'service_principal') {
        // Service Principal authentication
        if (!formData.databricksClientId?.trim()) {
          newErrors.databricksClientId = 'Client ID is required' as any;
        }
        if (!formData.databricksClientSecret?.trim()) {
          newErrors.databricksClientSecret = 'Client Secret is required' as any;
        }
      }
      // catalog is required
      if (!formData.databricksCatalog?.trim()) {
        newErrors.databricksCatalog = 'Catalog is required' as any;
      }
      // schema is optional - no validation needed
    } else {
      // SQL database validation (MySQL/PostgreSQL)
      if (formData.connectionMethod === 'url') {
        // URL-based validation
        if (!formData.connectionUrl.trim()) {
          newErrors.connectionUrl = 'Connection URL is required' as any;
        } else {
          const parsed = parseConnectionUrl(formData.connectionUrl);
          if (!parsed) {
            newErrors.connectionUrl = 'Invalid connection URL format' as any;
          } else {
            if (!parsed.host) {
              newErrors.connectionUrl =
                'Host is required in connection URL' as any;
            }
            if (!parsed.database) {
              newErrors.connectionUrl =
                'Database name is required in connection URL' as any;
            }
            if (!parsed.username) {
              newErrors.connectionUrl =
                'Username is required in connection URL' as any;
            }
            if (!parsed.password) {
              newErrors.connectionUrl =
                'Password is required in connection URL' as any;
            }
          }
        }
      } else {
        // Config-based validation
        if (!formData.host.trim()) {
          newErrors.host = 'Host is required';
        }
        if (!formData.database.trim()) {
          newErrors.database = 'Database name is required';
        }
        if (!formData.username.trim()) {
          newErrors.username = 'Username is required';
        }
        if (!formData.password.trim()) {
          newErrors.password = 'Password is required';
        }
        if (formData.port <= 0 || formData.port > 65535) {
          newErrors.port = 'Port must be between 1 and 65535' as any;
        }
      }
    }

    setErrors(newErrors);

    // Also check if there's a duplicate name warning - this should prevent submission
    const hasValidationErrors =
      Object.keys(newErrors).length > 0 || duplicateNameWarning !== '';
    return !hasValidationErrors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setDatabaseError(''); // Clear previous database errors

    let submitData = { ...formData };

    try {
      // If using URL method, parse URL and populate individual fields
      if (formData.connectionMethod === 'url') {
        const parsed = parseConnectionUrl(formData.connectionUrl);
        if (parsed) {
          submitData = {
            ...submitData,
            host: parsed.host,
            port: parsed.port,
            database: parsed.database,
            username: parsed.username,
            password: parsed.password
          };
        }
      }

      // Validate schema FIRST (for both new connections and updates)
      if (onValidateSchema) {
        setIsCheckingSchema(true);

        try {
          const schemaResult = await onValidateSchema(submitData);

          if (!schemaResult.success) {
            // Show schema error modal
            setSchemaError({
              show: true,
              message: schemaResult.error || 'Unknown schema validation error',
              formData: submitData
            });
            setIsCheckingSchema(false);
            return;
          }

          // Schema validation succeeded, store schema information and continue to create/update database
          if (schemaResult.schema) {
            submitData.schema = schemaResult.schema;
            submitData.schemaLastUpdated = new Date().toISOString();
          }
          setIsCheckingSchema(false);
        } catch (schemaValidationError) {
          // Show schema error modal for connection errors during schema loading
          const errorMessage =
            schemaValidationError instanceof Error
              ? schemaValidationError.message
              : String(schemaValidationError);
          setSchemaError({
            show: true,
            message: `Database connection failed: ${errorMessage}`,
            formData: submitData
          });
          setIsCheckingSchema(false);
          return;
        }
      }

      // Now create/update the database (only after schema validation passes)
      setIsSubmitting(true);

      try {
        await onCreateDatabase(submitData);
        // Only close if everything succeeded
        onClose();
      } catch (dbError) {
        // Database creation/update failed - show error modal
        const errorMessage =
          dbError instanceof Error ? dbError.message : String(dbError);
        setSchemaError({
          show: true,
          message: `Database ${editConfig ? 'update' : 'creation'} failed: ${errorMessage}`,
          formData: submitData
        });
        return; // Don't close modal
      }
    } catch (error) {
      console.error('[DatabaseCreationModal] Unexpected error:', error);
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      setSchemaError({
        show: true,
        message: `Unexpected error: ${errorMessage}`,
        formData: submitData
      });
    } finally {
      setIsSubmitting(false);
      setIsCheckingSchema(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting && !isCheckingSchema) {
      onClose();
    }
  };

  // Schema error modal handlers
  const handleSchemaRetry = async () => {
    if (!schemaError.formData) {
      return;
    }

    // Clear the error state and go back to the original modal view
    setSchemaError({ show: false, message: '' });

    // Set the form data back to what was being submitted
    setFormData(schemaError.formData);

    // Redo the "Loading Schema" state - this follows the same flow as handleSubmit
    if (onValidateSchema) {
      setIsCheckingSchema(true);

      try {
        const schemaResult = await onValidateSchema(schemaError.formData);

        if (!schemaResult.success) {
          // Show schema error modal again
          setSchemaError({
            show: true,
            message: schemaResult.error || 'Unknown schema validation error',
            formData: schemaError.formData
          });
          setIsCheckingSchema(false);
          return;
        }

        // Schema validation succeeded, store schema information and continue to create/update database
        if (schemaResult.schema) {
          schemaError.formData.schema = schemaResult.schema;
          schemaError.formData.schemaLastUpdated = new Date().toISOString();
        }
        setIsCheckingSchema(false);
        setIsSubmitting(true);

        try {
          await onCreateDatabase(schemaError.formData);
          // Success! Close the modal
          onClose();
        } catch (dbError) {
          const errorMessage =
            dbError instanceof Error ? dbError.message : String(dbError);
          setSchemaError({
            show: true,
            message: `Database ${editConfig ? 'update' : 'creation'} failed: ${errorMessage}`,
            formData: schemaError.formData
          });
          setIsSubmitting(false);
        }
      } catch (schemaValidationError) {
        // Show schema error modal for connection errors during schema loading
        const errorMessage =
          schemaValidationError instanceof Error
            ? schemaValidationError.message
            : String(schemaValidationError);
        setSchemaError({
          show: true,
          message: `Database connection failed: ${errorMessage}`,
          formData: schemaError.formData
        });
        setIsCheckingSchema(false);
      }
    }
  };

  const handleSchemaEdit = () => {
    // Close schema error modal and return to editing
    setSchemaError({ show: false, message: '' });
  };

  const handleSaveWithoutSchema = async () => {
    if (!schemaError.formData) {
      return;
    }

    // User explicitly wants to save without schema validation
    setSchemaError({ show: false, message: '' });
    setIsSubmitting(true);
    setDatabaseError(''); // Clear any previous errors

    try {
      await onCreateDatabase(schemaError.formData);
      // Successfully saved, close the modal
      onClose();
    } catch (dbError) {
      // Database creation/update failed - show error
      const errorMessage =
        dbError instanceof Error ? dbError.message : String(dbError);
      setDatabaseError(
        `Database ${editConfig ? 'update' : 'creation'} failed: ${errorMessage}`
      );
      setSchemaError({
        show: true,
        message: `Database ${editConfig ? 'update' : 'creation'} failed: ${errorMessage}`,
        formData: schemaError.formData
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isVisible) {
    return null;
  }

  const getDatabaseIcon = (type: DatabaseType) => {
    switch (type) {
      case DatabaseType.PostgreSQL:
        return <POSTGRESQL_ICON.react className="db-icon" tag="span" />;
      case DatabaseType.MySQL:
        return <MYSQL_ICON.react className="db-icon" tag="span" />;
      case DatabaseType.Snowflake:
        return <SNOWFLAKE_ICON.react className="db-icon" tag="span" />;
      case DatabaseType.Databricks:
        return <DATABRICKS_ICON.react className="db-icon" tag="span" />;
      default:
        return <span className="db-icon">🗃️</span>;
    }
  };

  return (
    <Modal
      show={isVisible}
      onHide={handleClose}
      backdrop={isSubmitting || isCheckingSchema ? 'static' : true}
      keyboard={!isSubmitting && !isCheckingSchema}
      centered
      dialogClassName="sage-ai-database-creation-modal"
      size="lg"
      scrollable={true}
    >
      <Modal.Header closeButton={!isSubmitting} className="modal-header-modern">
        <div className="modal-title-section">
          <div className="modal-icon">
            <CONNECTION_ICON.react className="icon-database" tag="span" />
          </div>
          <div className="modal-title-text">
            <Modal.Title className="sage-ai-database-modal-title">
              {editConfig
                ? 'Edit Database Connection'
                : 'Add Database Connection'}
            </Modal.Title>
            <p className="modal-subtitle">
              {editConfig
                ? 'Update your database connection settings'
                : 'Connect to your database securely'}
            </p>
          </div>
        </div>
      </Modal.Header>

      <Modal.Body className="sage-ai-database-modal-body">
        {schemaError.show ? (
          // Error display content
          <>
            {/* Error Details */}
            <Alert variant="danger" className="mb-4">
              <Alert.Heading className="h6 mb-2">
                <span className="me-2">🚨</span>
                Connection Error Details
              </Alert.Heading>
              <div className="error-message-container">
                <code className="text-danger">{schemaError.message}</code>
              </div>
            </Alert>

            {/* Warning Message */}
            <Alert variant="warning" className="mb-4">
              <Alert.Heading className="h6 mb-2">
                <span className="me-2">⚠️</span>
                Important Notice
              </Alert.Heading>
              <p className="mb-0">
                <strong>
                  If you continue without schema information, SignalPilot will
                  have significantly reduced accuracy when answering questions
                  about your database.
                </strong>
              </p>
              <p className="mb-0 mt-2 text-muted small">
                Schema information helps SignalPilot understand your database
                structure, table relationships, and column types for more
                accurate query generation and data analysis.
              </p>
            </Alert>

            {/* Action Options */}
            <div className="action-options">
              <h6 className="mb-3">What would you like to do?</h6>

              <div className="option-cards">
                <button
                  className="option-card recommended"
                  onClick={handleSchemaRetry}
                  disabled={isCheckingSchema}
                  type="button"
                >
                  <div className="option-icon">🔄</div>
                  <div className="option-content">
                    <div className="option-title">
                      {isCheckingSchema ? 'Retrying...' : 'Retry Schema Fetch'}
                    </div>
                    <div className="option-description">
                      Try connecting to the database again to retrieve schema
                      information
                    </div>
                  </div>
                  <div className="option-badge">Recommended</div>
                </button>

                <button
                  className="option-card"
                  onClick={handleSchemaEdit}
                  disabled={isCheckingSchema}
                  type="button"
                >
                  <div className="option-icon">✏️</div>
                  <div className="option-content">
                    <div className="option-title">Edit Connection Settings</div>
                    <div className="option-description">
                      Modify database connection parameters and try again
                    </div>
                  </div>
                </button>

                <button
                  className="option-card warning"
                  onClick={handleSaveWithoutSchema}
                  disabled={isCheckingSchema}
                  type="button"
                >
                  <div className="option-icon">⚠️</div>
                  <div className="option-content">
                    <div className="option-title">Continue Without Schema</div>
                    <div className="option-description">
                      Save the connection but with limited AI accuracy
                    </div>
                  </div>
                  <div className="option-badge warning">Limited Accuracy</div>
                </button>
              </div>
            </div>
          </>
        ) : (
          // Form content (existing form)
          <Form onSubmit={handleSubmit}>
            {/* Database Error Alert */}
            {databaseError && (
              <div
                className="alert alert-danger d-flex align-items-center mb-3"
                role="alert"
              >
                <div className="alert-icon me-2">⚠️</div>
                <div className="flex-grow-1">
                  <strong>Connection Failed</strong>
                  <div className="mt-1 small">{databaseError}</div>
                </div>
                <button
                  type="button"
                  className="btn-close"
                  aria-label="Close"
                  onClick={() => setDatabaseError('')}
                ></button>
              </div>
            )}
            {/* Duplicate Name Warning */}
            {duplicateNameWarning && (
              <div
                className="alert alert-danger d-flex align-items-center mb-3"
                role="alert"
              >
                <div className="alert-icon me-2" style={{ color: '#dc3545' }}>
                  🚨
                </div>
                <div className="flex-grow-1">
                  <strong>Duplicate Name Warning</strong>
                  <div className="mt-1 small">{duplicateNameWarning}</div>
                </div>
              </div>
            )}
            {/* Connection Info Section */}
            <div className="form-section-compact">
              {/* Connection Name */}
              <div className="form-row-compact">
                <label htmlFor="connectionName" className="form-label-inline">
                  Connection Name <span className="text-danger">*</span>
                </label>
                <div className="form-input-wrapper">
                  <Form.Control
                    id="connectionName"
                    type="text"
                    value={formData.name}
                    onChange={e => handleInputChange('name', e.target.value)}
                    isInvalid={!!errors.name}
                    placeholder="e.g., Production DB, Analytics DB"
                    disabled={isSubmitting}
                    className="form-control-compact"
                    autoComplete="off"
                    data-form-type="other"
                    spellCheck={false}
                  />
                  {errors.name && (
                    <div className="invalid-feedback-inline">{errors.name}</div>
                  )}
                </div>
              </div>

              {/* Description */}
              <div className="form-row-compact">
                <label
                  htmlFor="connectionDescription"
                  className="form-label-inline"
                >
                  Description
                </label>
                <div className="form-input-wrapper">
                  <Form.Control
                    id="connectionDescription"
                    as="textarea"
                    rows={5}
                    value={formData.description}
                    onChange={e =>
                      handleInputChange('description', e.target.value)
                    }
                    placeholder="Optional description that will be passed to the LLM (e.g., specific tables to focus on, data conventions, business context)"
                    disabled={isSubmitting}
                    className="form-control-compact"
                    autoComplete="off"
                    data-form-type="other"
                    spellCheck={false}
                  />
                </div>
              </div>

              {/* Database Type */}
              <div className="form-row-compact">
                <label className="form-label-inline">
                  Database Type <span className="text-danger">*</span>
                </label>
                <div className="form-input-wrapper">
                  <div className="database-type-buttons-compact">
                    <button
                      type="button"
                      className={`db-type-btn-compact ${formData.type === DatabaseType.PostgreSQL ? 'selected' : ''}`}
                      onClick={() =>
                        !isSubmitting &&
                        handleInputChange('type', DatabaseType.PostgreSQL)
                      }
                      disabled={isSubmitting}
                    >
                      <span className="db-icon-small">
                        {getDatabaseIcon(DatabaseType.PostgreSQL)}
                      </span>
                      PostgreSQL
                    </button>
                    <button
                      type="button"
                      className={`db-type-btn-compact ${formData.type === DatabaseType.MySQL ? 'selected' : ''}`}
                      onClick={() =>
                        !isSubmitting &&
                        handleInputChange('type', DatabaseType.MySQL)
                      }
                      disabled={isSubmitting}
                    >
                      <span className="db-icon-small">
                        {getDatabaseIcon(DatabaseType.MySQL)}
                      </span>
                      MySQL
                    </button>
                    <button
                      type="button"
                      className={`db-type-btn-compact ${formData.type === DatabaseType.Snowflake ? 'selected' : ''}`}
                      onClick={() =>
                        !isSubmitting &&
                        handleInputChange('type', DatabaseType.Snowflake)
                      }
                      disabled={isSubmitting}
                    >
                      <span className="db-icon-small">
                        {getDatabaseIcon(DatabaseType.Snowflake)}
                      </span>
                      Snowflake
                    </button>
                    <button
                      type="button"
                      className={`db-type-btn-compact ${formData.type === DatabaseType.Databricks ? 'selected' : ''}`}
                      onClick={() =>
                        !isSubmitting &&
                        handleInputChange('type', DatabaseType.Databricks)
                      }
                      disabled={isSubmitting}
                    >
                      <span className="db-icon-small">
                        {getDatabaseIcon(DatabaseType.Databricks)}
                      </span>
                      Databricks
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Render appropriate form based on database type */}
            {formData.type === DatabaseType.Snowflake ? (
              <SnowflakeDataForm
                formData={{
                  connectionUrl: formData.snowflakeConnectionUrl,
                  username: formData.username,
                  password: formData.password,
                  database: formData.database,
                  warehouse: formData.warehouse,
                  role: formData.role
                }}
                errors={{
                  connectionUrl: errors.snowflakeConnectionUrl,
                  username: errors.username,
                  password: errors.password
                }}
                isSubmitting={isSubmitting}
                onFieldChange={(field, value) => {
                  if (field === 'connectionUrl') {
                    handleInputChange('snowflakeConnectionUrl', value);
                  } else {
                    handleInputChange(field as keyof IDatabaseFormData, value);
                  }
                }}
              />
            ) : formData.type === DatabaseType.Databricks ? (
              <DatabricksDataForm
                formData={{
                  connectionUrl: formData.databricksConnectionUrl || '',
                  authType: formData.databricksAuthType || 'pat',
                  accessToken: formData.databricksAccessToken,
                  clientId: formData.databricksClientId,
                  clientSecret: formData.databricksClientSecret,
                  warehouseHttpPath: formData.databricksWarehouseHttpPath,
                  catalog: formData.databricksCatalog || '',
                  schema: formData.databricksSchema
                }}
                errors={{
                  connectionUrl: errors.databricksConnectionUrl,
                  accessToken: errors.databricksAccessToken,
                  clientId: errors.databricksClientId,
                  clientSecret: errors.databricksClientSecret,
                  warehouseHttpPath: errors.databricksWarehouseHttpPath,
                  catalog: errors.databricksCatalog,
                  schema: errors.databricksSchema
                }}
                isSubmitting={isSubmitting}
                onFieldChange={(field, value) => {
                  const fieldMap: {
                    [key: string]: keyof IDatabaseFormData;
                  } = {
                    connectionUrl: 'databricksConnectionUrl',
                    authType: 'databricksAuthType',
                    accessToken: 'databricksAccessToken',
                    clientId: 'databricksClientId',
                    clientSecret: 'databricksClientSecret',
                    warehouseHttpPath: 'databricksWarehouseHttpPath',
                    catalog: 'databricksCatalog',
                    schema: 'databricksSchema'
                  };
                  const mappedField = fieldMap[field] || field;
                  handleInputChange(
                    mappedField as keyof IDatabaseFormData,
                    value
                  );
                }}
              />
            ) : (
              <SQLDataForm
                databaseType={
                  formData.type as DatabaseType.MySQL | DatabaseType.PostgreSQL
                }
                formData={{
                  connectionMethod:
                    formData.connectionMethod as SQLConnectionMethod,
                  connectionUrl: formData.connectionUrl,
                  host: formData.host,
                  port: formData.port,
                  database: formData.database,
                  username: formData.username,
                  password: formData.password
                }}
                errors={{
                  connectionMethod: errors.connectionMethod,
                  connectionUrl: errors.connectionUrl,
                  host: errors.host,
                  port: errors.port,
                  database: errors.database,
                  username: errors.username,
                  password: errors.password
                }}
                isSubmitting={isSubmitting}
                onFieldChange={(field, value) => {
                  handleInputChange(field as keyof IDatabaseFormData, value);
                }}
              />
            )}
          </Form>
        )}
      </Modal.Body>

      <Modal.Footer className="modal-footer-modern">
        {schemaError.show ? (
          // Error state - no footer buttons, actions are in the modal body
          <div className="footer-info-text">
            <span className="text-muted small">
              Please select an action above to continue
            </span>
          </div>
        ) : (
          // Normal state buttons
          <>
            <Button
              variant="outline-secondary"
              onClick={handleClose}
              disabled={isSubmitting || isCheckingSchema}
              className="btn-cancel"
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSubmit}
              disabled={isSubmitting || isCheckingSchema}
              className="sage-ai-database-create-btn"
            >
              {isSubmitting ? (
                <>
                  <div className="spinner-modern"></div>
                  {editConfig
                    ? 'Updating Connection...'
                    : 'Creating Connection...'}
                </>
              ) : isCheckingSchema ? (
                <>
                  <div className="spinner-modern"></div>
                  Loading Schema...
                </>
              ) : (
                <>{editConfig ? 'Update Connection' : 'Create Connection'}</>
              )}
            </Button>
          </>
        )}
      </Modal.Footer>
    </Modal>
  );
}
