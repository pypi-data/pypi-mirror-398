import * as React from 'react';
import { CloudUploadService } from '../../Services/CloudUploadService';
import {
  DeploymentStateService,
  IDeploymentData
} from '../../Services/DeploymentStateService';
import { StatusBall } from '../common/StatusBall';

interface IExportOptions {
  include_input: boolean;
  include_output: boolean;
  include_images: boolean;
}

interface IHTMLPreviewContentProps {
  notebookPath: string;
  onClose: () => void;
}

interface IHTMLPreviewContentState {
  htmlContent: string;
  ipynbContent: string | null;
  exportOptions: IExportOptions;
  currentDeployment: IDeploymentData | null;
  uploadState: 'idle' | 'uploading' | 'success' | 'error';
  workspaceNotebookPath: string;
  error: string | null;
}

export function HTMLPreviewContent({
  notebookPath,
  onClose
}: IHTMLPreviewContentProps): JSX.Element {
  const [state, setState] = React.useState<IHTMLPreviewContentState>({
    htmlContent: '',
    ipynbContent: null,
    exportOptions: {
      include_input: true,
      include_output: true,
      include_images: true
    },
    currentDeployment: null,
    uploadState: 'idle',
    workspaceNotebookPath: '',
    error: null
  });

  const cloudUploadService = React.useMemo(
    () => CloudUploadService.getInstance(),
    []
  );
  const deploymentStateService = React.useMemo(
    () => DeploymentStateService.getInstance(),
    []
  );

  const syncDeploymentStateForPath = React.useCallback(
    async (path: string): Promise<void> => {
      try {
        console.log('[HTMLPreview] Syncing deployment state from backend');

        const response = await cloudUploadService.listUserFiles();
        const appUrl = cloudUploadService.getAppUrl();
        const deployment =
          await deploymentStateService.loadDeploymentFromBackend(
            path,
            response.data,
            appUrl
          );

        if (deployment) {
          console.log(
            '[HTMLPreview] Found existing deployment:',
            deployment.slug
          );
          setState(prev => ({ ...prev, currentDeployment: deployment }));
        } else {
          console.log('[HTMLPreview] No existing deployment found');
          setState(prev => ({ ...prev, currentDeployment: null }));
        }
      } catch (error) {
        console.warn('[HTMLPreview] Failed to sync deployment state:', error);
        const deployment = deploymentStateService.getDeployment(path);
        setState(prev => ({
          ...prev,
          currentDeployment: deployment || null
        }));
      }
    },
    [cloudUploadService, deploymentStateService]
  );

  const initializeWidget = React.useCallback(async (): Promise<void> => {
    const workspacePath = await generateHTML();
    await syncDeploymentStateForPath(workspacePath);
  }, []);

  React.useEffect(() => {
    void initializeWidget();
  }, [initializeWidget]);

  const generateHTML = async (): Promise<string> => {
    try {
      setState(prev => ({ ...prev, error: null }));

      const { requestAPI } = await import('../../handler');
      const response = await requestAPI<any>('notebook/to-html', {
        method: 'POST',
        body: JSON.stringify({
          notebook_path: notebookPath,
          ...state.exportOptions
        })
      });

      if (response.success) {
        const workspaceNotebookPath =
          response.workspace_notebook_path || notebookPath;

        // Read IPYNB content for upload
        let ipynbContent: string | null = null;
        try {
          const { AppStateService } = await import('../../AppState');
          const contentManager = AppStateService.getContentManager();
          const notebookFile = await contentManager.get(notebookPath);

          if (notebookFile && notebookFile.content) {
            ipynbContent = JSON.stringify(notebookFile.content);
            console.log('[HTMLPreview] Loaded IPYNB content for upload');
          }
        } catch (error) {
          console.warn('[HTMLPreview] Failed to read IPYNB content:', error);
          // Continue without IPYNB content
        }

        setState(prev => ({
          ...prev,
          htmlContent: response.html_content,
          ipynbContent,
          workspaceNotebookPath,
          error: null
        }));
        return workspaceNotebookPath;
      } else {
        throw new Error(response.error || 'Failed to generate HTML');
      }
    } catch (error) {
      console.error('Error generating HTML:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : String(error)
      }));
      return notebookPath;
    }
  };

  const downloadHTML = (): void => {
    if (!state.htmlContent) {
      console.warn('No HTML content to download');
      return;
    }

    const blob = new Blob([state.htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `${
      notebookPath.split('/').pop()?.replace('.ipynb', '') || 'notebook'
    }.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
  };

  const handleUploadToCloud = async (): Promise<void> => {
    if (!state.htmlContent) {
      console.warn('No HTML content to upload');
      return;
    }

    try {
      setState(prev => ({ ...prev, uploadState: 'uploading' }));

      const filename = `${
        notebookPath.split('/').pop()?.replace('.ipynb', '') || 'notebook'
      }.html`;

      console.log('[HTMLPreview] Starting upload workflow for:', filename);

      const deploymentData = await cloudUploadService.uploadWorkflow(
        filename,
        state.htmlContent,
        state.workspaceNotebookPath,
        state.ipynbContent
      );

      setState(prev => ({
        ...prev,
        currentDeployment: deploymentData,
        uploadState: 'success'
      }));

      console.log('[HTMLPreview] Upload completed successfully');
    } catch (error) {
      console.error('[HTMLPreview] Upload failed:', error);
      setState(prev => ({
        ...prev,
        uploadState: 'error',
        error: error instanceof Error ? error.message : String(error)
      }));
    }
  };

  const handleDeleteDeployment = async (): Promise<void> => {
    if (!state.currentDeployment) {
      return;
    }

    const confirmed = confirm(
      'Are you sure you want to delete this deployment?\n\n' +
        `File: ${state.currentDeployment.filename}\n` +
        `URL: ${state.currentDeployment.deployedUrl}\n\n` +
        'This action cannot be undone.'
    );

    if (!confirmed) {
      return;
    }

    try {
      console.log(
        '[HTMLPreview] Starting delete workflow for:',
        state.currentDeployment.slug
      );

      await cloudUploadService.deleteWorkflow(
        state.currentDeployment.slug,
        state.workspaceNotebookPath
      );

      setState(prev => ({
        ...prev,
        currentDeployment: null,
        uploadState: 'idle'
      }));

      console.log('[HTMLPreview] Delete completed successfully');
    } catch (error) {
      console.error('[HTMLPreview] Delete failed:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : String(error)
      }));
    }
  };

  const handleInputChange =
    (option: keyof IExportOptions) =>
    (e: React.ChangeEvent<HTMLInputElement>): void => {
      setState(prev => ({
        ...prev,
        exportOptions: {
          ...prev.exportOptions,
          [option]: e.target.checked
        }
      }));
    };

  const handleReload = (): void => {
    void generateHTML();
  };

  const getDeploymentStatus = ():
    | 'deployed'
    | 'uploading'
    | 'error'
    | 'idle' => {
    if (state.currentDeployment) {
      return 'deployed';
    }
    if (state.uploadState === 'uploading') {
      return 'uploading';
    }
    if (state.uploadState === 'error') {
      return 'error';
    }
    return 'idle';
  };

  const getUploadButtonText = (): string => {
    if (state.uploadState === 'uploading') {
      return 'Uploading...';
    }
    if (state.currentDeployment) {
      return 'Re-deploy';
    }
    return 'Deploy Snapshot';
  };

  return (
    <div className="html-preview-widget">
      <div className="html-preview-container">
        <div className="html-preview-toolbar">
          <div className="html-preview-config">
            <label className="html-preview-checkbox">
              <input
                type="checkbox"
                id="include-input"
                checked={state.exportOptions.include_input}
                onChange={handleInputChange('include_input')}
              />
              <span>Include Code Inputs</span>
            </label>

            <label className="html-preview-checkbox">
              <input
                type="checkbox"
                id="include-output"
                checked={state.exportOptions.include_output}
                onChange={handleInputChange('include_output')}
              />
              <span>Include Outputs</span>
            </label>

            <label className="html-preview-checkbox">
              <input
                type="checkbox"
                id="include-images"
                checked={state.exportOptions.include_images}
                onChange={handleInputChange('include_images')}
              />
              <span>Include Images</span>
            </label>
            <button
              className="html-preview-button-secondary"
              onClick={handleReload}
            >
              Reload Preview
            </button>
            <button
              className="html-preview-button-secondary"
              onClick={downloadHTML}
            >
              Download
            </button>
          </div>

          <div className="html-preview-status-container">
            <button
              className={`html-preview-button-primary ${
                !state.currentDeployment && state.uploadState !== 'uploading'
                  ? 'html-preview-not-deployed'
                  : ''
              }`}
              id="upload-cloud-button"
              onClick={handleUploadToCloud}
              disabled={state.uploadState === 'uploading'}
            >
              {getUploadButtonText()}
            </button>
            <div className="html-preview-status-ball-container">
              <StatusBall
                popoverPosition="left"
                id="html-preview-status-ball"
                className={`html-preview-status-ball ${getDeploymentStatus()}`}
                status={getDeploymentStatus()}
                deployment={state.currentDeployment}
                onDelete={handleDeleteDeployment}
              />
            </div>
          </div>
        </div>

        <div className="html-preview-area">
          {!state.htmlContent && !state.error && (
            <div className="html-preview-loading">
              Generating HTML preview...
            </div>
          )}

          {state.error && (
            <div className="html-preview-error">
              <div>Failed to generate HTML preview</div>
              <div style={{ marginTop: '8px', fontSize: '12px' }}>
                {state.error}
              </div>
            </div>
          )}

          {state.htmlContent && (
            <iframe
              className="html-preview-iframe"
              srcDoc={state.htmlContent}
              title="HTML Preview"
            />
          )}
        </div>
      </div>
    </div>
  );
}
