import React, { useState, useEffect } from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { StatusBall } from './common/StatusBall';
import {
  DeploymentStateService,
  IDeploymentData
} from '../Services/DeploymentStateService';
import { CloudUploadService } from '../Services/CloudUploadService';
import { JupyterFrontEnd } from '@jupyterlab/application';
import { AppStateService } from '../AppState';

interface INotebookDeploymentButtonProps {
  app: JupyterFrontEnd;
  notebookPath: string;
  isNotebookReady: boolean;
}

/**
 * React component for the notebook preview snapshot button
 */
function NotebookDeploymentButton({
  app,
  notebookPath,
  isNotebookReady
}: INotebookDeploymentButtonProps) {
  const [currentWorkingDirectory, setCurrentWorkingDirectory] = useState(
    AppStateService.getState().currentWorkingDirectory
  );
  const path = `${currentWorkingDirectory || ''}/${notebookPath}`;
  const [isOpening, setIsOpening] = useState(false);
  const [currentDeployment, setCurrentDeployment] =
    useState<IDeploymentData | null>(null);

  // Subscribe to AppStateService changes to track currentWorkingDirectory
  useEffect(() => {
    const subscription = AppStateService.changes.subscribe(state => {
      setCurrentWorkingDirectory(state.currentWorkingDirectory);
    });
    return () => subscription.unsubscribe();
  }, []);

  const cloudUploadService = React.useMemo(
    () => CloudUploadService.getInstance(),
    []
  );
  const deploymentStateService = React.useMemo(
    () => DeploymentStateService.getInstance(),
    []
  );

  // Load deployment status
  useEffect(() => {
    const loadDeployment = async () => {
      try {
        const deployment = deploymentStateService.getDeployment(path);
        if (deployment) {
          setCurrentDeployment(deployment);
        }

        // Sync with backend
        const response = await cloudUploadService.listUserFiles();
        const appUrl = cloudUploadService.getAppUrl();
        const synced = await deploymentStateService.loadDeploymentFromBackend(
          path,
          response.data,
          appUrl
        );
        if (synced) {
          setCurrentDeployment(synced);
        }
      } catch (error) {
        console.warn(
          '[PreviewButton] Failed to load deployment status:',
          error
        );
      }
    };

    void loadDeployment();
  }, [path, cloudUploadService, deploymentStateService]);

  // Subscribe to deployment state changes
  useEffect(() => {
    const subscription = deploymentStateService.changes.subscribe(change => {
      // Update state when this notebook's deployment changes
      if (change.notebookPath === path) {
        if (change.type === 'removed') {
          setCurrentDeployment(null);
        } else if (change.deployment) {
          setCurrentDeployment(change.deployment);
        }
      } else if (change.type === 'cleared') {
        // All deployments cleared
        setCurrentDeployment(null);
      }
    });
    return () => subscription.unsubscribe();
  }, [path, deploymentStateService]);

  const handlePreview = async () => {
    if (!isNotebookReady) {
      return;
    }

    setIsOpening(true);

    try {
      console.log(
        '[PreviewButton] Executing export command for:',
        notebookPath
      );

      // Execute the registered command
      await app.commands.execute('signalpilot-ai-internal:export-notebook-html');
      console.log('[PreviewButton] ✅ HTML preview widget opened via command');
    } catch (error) {
      console.error('[PreviewButton] Failed to open preview:', error);
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      alert(`Failed to open preview: ${errorMessage}`);
    } finally {
      setIsOpening(false);
    }
  };

  const getDeploymentStatus = ():
    | 'deployed'
    | 'uploading'
    | 'error'
    | 'idle' => {
    if (currentDeployment) {
      return 'deployed';
    }
    return 'idle';
  };

  const getStatusTitle = (): string => {
    if (currentDeployment) {
      return 'Deployed';
    }
    return 'Not Deployed';
  };

  const handleDeleteDeployment = async (): Promise<void> => {
    if (!currentDeployment) {
      return;
    }

    const confirmed = confirm(
      'Are you sure you want to delete this deployment?\n\n' +
        `File: ${currentDeployment.filename}\n` +
        `URL: ${currentDeployment.deployedUrl}\n\n` +
        'This action cannot be undone.'
    );

    if (!confirmed) {
      return;
    }

    try {
      console.log(
        '[NotebookDeploymentButton] Starting delete workflow for:',
        currentDeployment.slug
      );

      await cloudUploadService.deleteWorkflow(currentDeployment.slug, path);

      // Clear deployment from state
      setCurrentDeployment(null);

      console.log('[NotebookDeploymentButton] Delete completed successfully');
    } catch (error) {
      console.error('[NotebookDeploymentButton] Delete failed:', error);
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      alert(`Failed to delete deployment: ${errorMessage}`);
    }
  };

  const buttonText = 'Preview Snapshot';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        margin: '0 4px',
        position: 'relative',
        border: '1px solid var(--jp-border-color3)',
        padding: '2px 3px 2px 6px',
        borderRadius: '4px'
      }}
    >
      {/* Status Ball */}
      <StatusBall
        popoverPosition="center"
        id="html-preview-status-ball"
        className={`html-preview-status-ball ${getDeploymentStatus()} small`}
        status={getDeploymentStatus()}
        title={getStatusTitle()}
        deployment={currentDeployment}
        onDelete={handleDeleteDeployment}
      />

      {/* Preview Snapshot Button */}
      <button
        onClick={handlePreview}
        disabled={isOpening || !isNotebookReady}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '2px 4px',
          fontSize: '9px',
          border: '1px solid var(--jp-border-color1)',
          borderRadius: '4px',
          backgroundColor: 'transparent',
          color: 'white',
          cursor: isOpening || !isNotebookReady ? 'not-allowed' : 'pointer',
          opacity: isOpening || !isNotebookReady ? 0.5 : 1,
          fontWeight: '500'
        }}
        title={isOpening ? 'Opening...' : buttonText}
      >
        {isOpening ? '⏳ Opening...' : buttonText}
      </button>

      <button
        onClick={async () => {
          try {
            await app.commands.execute('signalpilot-ai-internal:publish-report');
          } catch (e) {
            console.error('[PreviewButton] publish-report failed:', e);
          }
        }}
        disabled={!isNotebookReady}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '2px 4px',
          fontSize: '9px',
          border: '1px solid var(--jp-border-color1)',
          borderRadius: '4px',
          backgroundColor: 'transparent',
          color: 'white',
          cursor: !isNotebookReady ? 'not-allowed' : 'pointer',
          opacity: !isNotebookReady ? 0.5 : 1,
          fontWeight: '500'
        }}
        title={'Build AI Report'}
      >
        Build AI Report
      </button>
    </div>
  );
}

/**
 * Widget class that wraps the React component
 */
export class NotebookDeploymentButtonWidget extends ReactWidget {
  private notebookPath: string;
  private isNotebookReady: boolean;
  private app: JupyterFrontEnd;

  constructor(app: any, notebookPath: string, isNotebookReady: boolean) {
    super();
    this.app = app;
    this.notebookPath = notebookPath;
    this.isNotebookReady = isNotebookReady;
    this.addClass('jp-NotebookDeploymentButton');
  }

  protected render(): React.ReactElement<any> {
    return (
      <NotebookDeploymentButton
        app={this.app}
        notebookPath={this.notebookPath}
        isNotebookReady={this.isNotebookReady}
      />
    );
  }
}
