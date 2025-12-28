import * as React from 'react';
import { Form } from 'react-bootstrap';
import { DatabricksAuthType } from '../../DatabaseStateService';

/**
 * Databricks-specific form data interface
 */
export interface IDatabricksFormData {
  connectionUrl: string;
  authType: DatabricksAuthType;
  // PAT authentication
  accessToken?: string;
  // Service Principal authentication
  clientId?: string;
  clientSecret?: string;
  // Optional fields
  warehouseHttpPath?: string;
  catalog: string;
  schema?: string;
}

/**
 * Props for the DatabricksDataForm component
 */
export interface IDatabricksDataFormProps {
  formData: IDatabricksFormData;
  errors: Partial<IDatabricksFormData>;
  isSubmitting: boolean;
  onFieldChange: (field: keyof IDatabricksFormData, value: string) => void;
}

/**
 * Databricks database connection form component
 */
export function DatabricksDataForm({
  formData,
  errors,
  isSubmitting,
  onFieldChange
}: IDatabricksDataFormProps): JSX.Element {
  return (
    <>
      {/* Documentation Link */}
      <div className="form-section-compact">
        <div className="form-row-compact form-row-compact-reduced">
          <div className="form-input-wrapper" style={{ width: '100%' }}>
            <a
              href="https://docs.databricks.com/en/dev-tools/sql-connector.html"
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
              <span className="docs-text">View Databricks connection instructions</span>
            </a>
          </div>
        </div>
      </div>

      <div className="form-section-compact">
        {/* Databricks Host */}
        <div className="form-row-compact form-row-compact-reduced">
          <label htmlFor="connectionUrl" className="form-label-inline">
            Databricks Host <span className="text-danger">*</span>
          </label>
          <div className="form-input-wrapper">
            <Form.Control
              id="connectionUrl"
              type="text"
              value={formData.connectionUrl}
              onChange={e => onFieldChange('connectionUrl', e.target.value)}
              isInvalid={!!errors.connectionUrl}
              placeholder="https://dbc-xxxxxx-xxxx.cloud.databricks.com"
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
            <div className="form-text text-muted small mt-1">
              Your Databricks host (e.g.,
              https://dbc-xxxxxx-xxxx.cloud.databricks.com)
            </div>
          </div>
        </div>

        {/* SQL Warehouse HTTP Path */}
        <div className="form-row-compact form-row-compact-reduced">
          <label htmlFor="warehouseHttpPath" className="form-label-inline">
            SQL Warehouse HTTP Path <span className="text-danger">*</span>
          </label>
          <div className="form-input-wrapper">
            <Form.Control
              id="warehouseHttpPath"
              type="text"
              value={formData.warehouseHttpPath || ''}
              onChange={e => onFieldChange('warehouseHttpPath', e.target.value)}
              isInvalid={!!errors.warehouseHttpPath}
              placeholder="/sql/1.0/warehouses/abc123"
              disabled={isSubmitting}
              className="form-control-compact"
              autoComplete="off"
              data-form-type="other"
              spellCheck={false}
            />
            {errors.warehouseHttpPath && (
              <div className="invalid-feedback-inline">
                {errors.warehouseHttpPath}
              </div>
            )}
            <div className="form-text text-muted small mt-1">
              Found in SQL Warehouse → Connection details → HTTP path
            </div>
          </div>
        </div>

        {/* Authentication Type - Modern Card Style */}
        <div className="form-row-compact form-row-compact-reduced">
          <label className="form-label-inline">
            Authentication <span className="text-danger">*</span>
          </label>
          <div className="form-input-wrapper">
            <div className="auth-type-selector">
              {/* Personal Access Token Option */}
              <div
                className={`auth-option-card ${
                  formData.authType === 'pat' ? 'selected' : ''
                } ${isSubmitting ? 'disabled' : ''}`}
                onClick={() =>
                  !isSubmitting && onFieldChange('authType', 'pat')
                }
                role="button"
                tabIndex={0}
                onKeyPress={e => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    !isSubmitting && onFieldChange('authType', 'pat');
                  }
                }}
              >
                <div className="auth-radio-indicator" />
                <div className="auth-option-content">
                  <div className="auth-option-title">Personal Access Token</div>
                  <div className="auth-option-description">
                    Simple token-based auth
                  </div>
                </div>
                <input
                  type="radio"
                  name="authType"
                  value="pat"
                  checked={formData.authType === 'pat'}
                  onChange={() => onFieldChange('authType', 'pat')}
                  className="auth-radio-hidden"
                  disabled={isSubmitting}
                />
              </div>

              {/* Service Principal Option */}
              <div
                className={`auth-option-card ${
                  formData.authType === 'service_principal' ? 'selected' : ''
                } ${isSubmitting ? 'disabled' : ''}`}
                onClick={() =>
                  !isSubmitting &&
                  onFieldChange('authType', 'service_principal')
                }
                role="button"
                tabIndex={0}
                onKeyPress={e => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    !isSubmitting &&
                      onFieldChange('authType', 'service_principal');
                  }
                }}
              >
                <div className="auth-radio-indicator" />
                <div className="auth-option-content">
                  <div className="auth-option-title">Service Principal</div>
                  <div className="auth-option-description">
                    OAuth with client credentials
                  </div>
                </div>
                <input
                  type="radio"
                  name="authType"
                  value="service_principal"
                  checked={formData.authType === 'service_principal'}
                  onChange={() =>
                    onFieldChange('authType', 'service_principal')
                  }
                  className="auth-radio-hidden"
                  disabled={isSubmitting}
                />
              </div>
            </div>
          </div>
        </div>

        {/* PAT Authentication Fields */}
        {formData.authType === 'pat' && (
          <div className="form-row-compact form-row-compact-reduced">
            <label htmlFor="accessToken" className="form-label-inline">
              Access Token <span className="text-danger">*</span>
            </label>
            <div className="form-input-wrapper">
              <Form.Control
                id="accessToken"
                type="password"
                value={formData.accessToken || ''}
                onChange={e => onFieldChange('accessToken', e.target.value)}
                isInvalid={!!errors.accessToken}
                placeholder="dapi..."
                disabled={isSubmitting}
                className="form-control-compact"
                autoComplete="new-password"
                data-form-type="other"
              />
              {errors.accessToken && (
                <div className="invalid-feedback-inline">
                  {errors.accessToken}
                </div>
              )}
              <div className="form-text text-muted small mt-1">
                Generate in User Settings → Developer → Access tokens
              </div>
            </div>
          </div>
        )}

        {/* Service Principal Authentication Fields */}
        {formData.authType === 'service_principal' && (
          <>
            <div className="form-row-compact form-row-compact-reduced">
              <label htmlFor="clientId" className="form-label-inline">
                Client ID <span className="text-danger">*</span>
              </label>
              <div className="form-input-wrapper">
                <Form.Control
                  id="clientId"
                  type="text"
                  value={formData.clientId || ''}
                  onChange={e => onFieldChange('clientId', e.target.value)}
                  isInvalid={!!errors.clientId}
                  placeholder="Application (client) ID"
                  disabled={isSubmitting}
                  className="form-control-compact"
                  autoComplete="off"
                  data-form-type="other"
                  spellCheck={false}
                />
                {errors.clientId && (
                  <div className="invalid-feedback-inline">
                    {errors.clientId}
                  </div>
                )}
              </div>
            </div>

            <div className="form-row-compact form-row-compact-reduced">
              <label htmlFor="clientSecret" className="form-label-inline">
                Client Secret <span className="text-danger">*</span>
              </label>
              <div className="form-input-wrapper">
                <Form.Control
                  id="clientSecret"
                  type="password"
                  value={formData.clientSecret || ''}
                  onChange={e => onFieldChange('clientSecret', e.target.value)}
                  isInvalid={!!errors.clientSecret}
                  placeholder="Service principal secret"
                  disabled={isSubmitting}
                  className="form-control-compact"
                  autoComplete="new-password"
                  data-form-type="other"
                />
                {errors.clientSecret && (
                  <div className="invalid-feedback-inline">
                    {errors.clientSecret}
                  </div>
                )}
              </div>
            </div>

            <div
              className="alert alert-info mt-2 mb-3"
              style={{ fontSize: '0.85rem' }}
            >
              <strong>Note:</strong> Service Principal requires:
              <ul className="mb-0 mt-1">
                <li>Admin-configured service principal in Databricks</li>
                <li>Permissions to access the SQL warehouse and catalogs</li>
                <li>For Azure: uses Azure AD OAuth automatically</li>
              </ul>
            </div>
          </>
        )}

        {/* Catalog (Required) */}
        <div className="form-row-compact form-row-compact-reduced">
          <label htmlFor="catalog" className="form-label-inline">
            Default Catalog <span className="text-danger">*</span>
          </label>
          <div className="form-input-wrapper">
            <Form.Control
              id="catalog"
              type="text"
              value={formData.catalog || ''}
              onChange={e => onFieldChange('catalog', e.target.value)}
              isInvalid={!!errors.catalog}
              placeholder="e.g., main"
              disabled={isSubmitting}
              className="form-control-compact"
              autoComplete="off"
              data-form-type="other"
              spellCheck={false}
            />
            {errors.catalog && (
              <div className="invalid-feedback-inline">
                {errors.catalog}
              </div>
            )}
            <div className="form-text text-muted small mt-1">
              Unity Catalog name (required for proper schema access)
            </div>
          </div>
        </div>

        {/* Schema (Optional) */}
        <div className="form-row-compact form-row-compact-reduced">
          <label htmlFor="schema" className="form-label-inline">
            Default Schema
          </label>
          <div className="form-input-wrapper">
            <Form.Control
              id="schema"
              type="text"
              value={formData.schema || ''}
              onChange={e => onFieldChange('schema', e.target.value)}
              placeholder="Optional default schema"
              disabled={isSubmitting}
              className="form-control-compact"
              autoComplete="off"
              data-form-type="other"
              spellCheck={false}
            />
          </div>
        </div>

        {/* Security Notice */}
        <div className="security-notice-compact mt-3">
          <span className="notice-icon-small">🛡️</span>
          <span className="notice-text-compact">
            All credentials are encrypted using AES-256 encryption and never
            leave your local machine
          </span>
        </div>
      </div>
    </>
  );
}
