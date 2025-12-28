import * as React from 'react';
import { Form } from 'react-bootstrap';
import { DatabaseType } from '../../DatabaseStateService';

/**
 * Connection method type for SQL databases
 */
export type SQLConnectionMethod = 'url' | 'config';

/**
 * SQL-specific form data interface (for MySQL and PostgreSQL)
 */
export interface ISQLFormData {
  connectionMethod: SQLConnectionMethod;
  // URL-based connection
  connectionUrl: string;
  // Config-based connection
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
}

/**
 * Props for the SQLDataForm component
 */
export interface ISQLDataFormProps {
  databaseType: DatabaseType.MySQL | DatabaseType.PostgreSQL;
  formData: ISQLFormData;
  errors: Partial<ISQLFormData>;
  isSubmitting: boolean;
  onFieldChange: (
    field: keyof ISQLFormData,
    value: string | number | SQLConnectionMethod
  ) => void;
}

/**
 * SQL database (MySQL/PostgreSQL) connection form component
 */
export function SQLDataForm({
  databaseType,
  formData,
  errors,
  isSubmitting,
  onFieldChange
}: ISQLDataFormProps): JSX.Element {
  const getDocumentationLink = () => {
    if (databaseType === DatabaseType.PostgreSQL) {
      return 'https://docs.signalpilot.ai/guide/core/connecting-databases/connecting-a-postgresql-database';
    } else if (databaseType === DatabaseType.MySQL) {
      return 'https://docs.signalpilot.ai/guide/core/connecting-databases/connecting-a-mysql-database';
    }
    return '';
  };

  const getDatabaseName = () => {
    return databaseType === DatabaseType.PostgreSQL ? 'PostgreSQL' : 'MySQL';
  };

  return (
    <>
      {/* Documentation Link */}
      <div className="form-section-compact">
        <div className="form-row-compact form-row-compact-reduced">
          <div className="form-input-wrapper" style={{ width: '100%' }}>
            <a
              href={getDocumentationLink()}
              target="_blank"
              rel="noopener noreferrer"
              className="documentation-link"
            >
              <svg className="docs-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M16 13H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M16 17H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M10 9H9H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span className="docs-text">View {getDatabaseName()} connection instructions</span>
            </a>
          </div>
        </div>
      </div>

      {/* Connection Method */}
      <div className="form-section-compact">
        <div className="form-row-compact">
          <label className="form-label-inline">
            Connection Method <span className="text-danger">*</span>
          </label>
          <div className="form-input-wrapper">
            <div className="connection-method-buttons-compact">
              <button
                type="button"
                className={`method-btn-compact ${formData.connectionMethod === 'url' ? 'selected' : ''}`}
                onClick={() =>
                  !isSubmitting && onFieldChange('connectionMethod', 'url')
                }
                disabled={isSubmitting}
              >
                🔗 Connection URL
              </button>
              <button
                type="button"
                className={`method-btn-compact ${formData.connectionMethod === 'config' ? 'selected' : ''}`}
                onClick={() =>
                  !isSubmitting && onFieldChange('connectionMethod', 'config')
                }
                disabled={isSubmitting}
              >
                ⚙️ Configuration
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Connection URL Section */}
      {formData.connectionMethod === 'url' && (
        <div className="form-section-compact">
          <div className="form-row-compact">
            <label htmlFor="connectionUrl" className="form-label-inline">
              Connection URL <span className="text-danger">*</span>
            </label>
            <div className="form-input-wrapper">
              <Form.Control
                id="connectionUrl"
                type="text"
                value={formData.connectionUrl}
                onChange={e => onFieldChange('connectionUrl', e.target.value)}
                isInvalid={!!errors.connectionUrl}
                placeholder={
                  databaseType === DatabaseType.MySQL
                    ? 'mysql://username:password@host:port/database'
                    : 'postgresql://username:password@host:port/database'
                }
                disabled={isSubmitting}
                className="form-control-compact"
                autoComplete="off"
                data-form-type="other"
                spellCheck={false}
              />
              {errors.connectionUrl && (
                <div className="invalid-feedback-inline">
                  {errors.connectionUrl}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Server Configuration Section */}
      {formData.connectionMethod === 'config' && (
        <div className="form-section-compact">
          {/* Host and Port */}
          <div className="form-row-compact form-row-compact-reduced">
            <label htmlFor="host" className="form-label-inline">
              Host <span className="text-danger">*</span>
            </label>
            <div className="form-input-wrapper">
              <div className="input-group-compact">
                <Form.Control
                  id="host"
                  type="text"
                  value={formData.host}
                  onChange={e => onFieldChange('host', e.target.value)}
                  isInvalid={!!errors.host}
                  placeholder="localhost or db.example.com"
                  disabled={isSubmitting}
                  className="form-control-compact flex-grow-1"
                  autoComplete="off"
                  data-form-type="other"
                  spellCheck={false}
                />
                <Form.Control
                  id="port"
                  type="number"
                  value={formData.port}
                  onChange={e =>
                    onFieldChange('port', parseInt(e.target.value))
                  }
                  isInvalid={!!errors.port}
                  min="1"
                  max="65535"
                  disabled={isSubmitting}
                  className="form-control-compact port-input"
                  autoComplete="off"
                  data-form-type="other"
                  placeholder="Port"
                />
              </div>
              {(errors.host || errors.port) && (
                <div className="invalid-feedback-inline">
                  {errors.host || String(errors.port || '')}
                </div>
              )}
            </div>
          </div>

          {/* Database */}
          <div className="form-row-compact form-row-compact-reduced">
            <label htmlFor="database" className="form-label-inline">
              Database <span className="text-danger">*</span>
            </label>
            <div className="form-input-wrapper">
              <Form.Control
                id="database"
                type="text"
                value={formData.database}
                onChange={e => onFieldChange('database', e.target.value)}
                isInvalid={!!errors.database}
                placeholder="Database name"
                disabled={isSubmitting}
                className="form-control-compact"
                autoComplete="off"
                data-form-type="other"
                spellCheck={false}
              />
              {errors.database && (
                <div className="invalid-feedback-inline">{errors.database}</div>
              )}
            </div>
          </div>

          {/* Username */}
          <div className="form-row-compact form-row-compact-reduced">
            <label htmlFor="username" className="form-label-inline">
              Username <span className="text-danger">*</span>
            </label>
            <div className="form-input-wrapper">
              <Form.Control
                id="username"
                type="text"
                value={formData.username}
                onChange={e => onFieldChange('username', e.target.value)}
                isInvalid={!!errors.username}
                placeholder="Database username"
                disabled={isSubmitting}
                className="form-control-compact"
                autoComplete="off"
                data-form-type="other"
                spellCheck={false}
              />
              {errors.username && (
                <div className="invalid-feedback-inline">{errors.username}</div>
              )}
            </div>
          </div>

          {/* Password */}
          <div className="form-row-compact form-row-compact-reduced">
            <label htmlFor="password" className="form-label-inline">
              Password <span className="text-danger">*</span>
            </label>
            <div className="form-input-wrapper">
              <Form.Control
                id="password"
                type="password"
                value={formData.password}
                onChange={e => onFieldChange('password', e.target.value)}
                isInvalid={!!errors.password}
                placeholder="Database password"
                disabled={isSubmitting}
                className="form-control-compact"
                autoComplete="new-password"
                data-form-type="other"
              />
              {errors.password && (
                <div className="invalid-feedback-inline">{errors.password}</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Security Notice */}
      <div className="security-notice-compact">
        <span className="notice-icon-small">🛡️</span>
        <span className="notice-text-compact">
          All credentials are encrypted using AES-256 encryption and never leave
          your local machine
        </span>
      </div>
    </>
  );
}
