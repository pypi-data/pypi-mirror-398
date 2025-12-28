import { Subject, Observable } from 'rxjs';

export interface IDeploymentData {
  slug: string;
  deployedUrl: string;
  filename: string;
  deployedAt: string;
  s3_key: string;
  fileSize: number;
}

export interface IBackendFileData {
  id: string;
  slug: string;
  filename: string;
  file_size: number | null;
  workspace_notebook_path: string | null;
  is_active: boolean;
  user_email: string;
  created_at: string;
}

export interface IDeploymentChange {
  type: 'added' | 'removed' | 'updated' | 'cleared';
  notebookPath: string | null;
  deployment: IDeploymentData | null;
}

export class DeploymentStateService {
  private static instance: DeploymentStateService;
  private deployments: Map<string, IDeploymentData> = new Map();
  private changes$ = new Subject<IDeploymentChange>();

  private constructor() {}

  /**
   * Observable for deployment state changes
   */
  public get changes(): Observable<IDeploymentChange> {
    return this.changes$.asObservable();
  }

  public static getInstance(): DeploymentStateService {
    if (!DeploymentStateService.instance) {
      DeploymentStateService.instance = new DeploymentStateService();
    }
    return DeploymentStateService.instance;
  }

  /**
   * Save deployment data for a notebook
   */
  public async saveDeployment(
    notebookPath: string,
    deploymentData: IDeploymentData
  ): Promise<void> {
    try {
      const isUpdate = this.deployments.has(notebookPath);
      this.deployments.set(notebookPath, deploymentData);
      console.log(`[DeploymentState] Saved deployment for: ${notebookPath}`);
      this.changes$.next({
        type: isUpdate ? 'updated' : 'added',
        notebookPath,
        deployment: deploymentData
      });
    } catch (error) {
      console.error('[DeploymentState] Failed to save deployment:', error);
      throw error;
    }
  }

  /**
   * Get deployment data for a specific notebook
   */
  public getDeployment(notebookPath: string): IDeploymentData | undefined {
    return this.deployments.get(notebookPath);
  }

  /**
   * Get all deployments
   */
  public getAllDeployments(): Map<string, IDeploymentData> {
    return new Map(this.deployments);
  }

  /**
   * Remove deployment data for a notebook (after deletion)
   */
  public async removeDeployment(notebookPath: string): Promise<void> {
    try {
      this.deployments.delete(notebookPath);
      console.log(`[DeploymentState] Removed deployment for: ${notebookPath}`);
      this.changes$.next({
        type: 'removed',
        notebookPath,
        deployment: null
      });
    } catch (error) {
      console.error('[DeploymentState] Failed to remove deployment:', error);
      throw error;
    }
  }

  /**
   * Delete deployment both locally and from backend
   */
  public async deleteDeployment(notebookPath: string): Promise<void> {
    const deployment = this.getDeployment(notebookPath);
    if (!deployment) {
      console.warn(
        `[DeploymentState] No deployment found for: ${notebookPath}`
      );
      return;
    }

    try {
      // Remove from local state
      await this.removeDeployment(notebookPath);
      console.log(`[DeploymentState] Deleted deployment for: ${notebookPath}`);
    } catch (error) {
      console.error('[DeploymentState] Failed to delete deployment:', error);
      throw error;
    }
  }

  /**
   * Sync local state with backend files
   */
  public async syncWithBackend(backendFiles: any[]): Promise<void> {
    try {
      // Create a map of backend files by slug for quick lookup
      const backendFileMap = new Map();
      backendFiles.forEach(file => {
        if (file.slug) {
          backendFileMap.set(file.slug, file);
        }
      });

      // Check if any local deployments are no longer active on backend
      const deploymentsToRemove: string[] = [];

      for (const [notebookPath, deployment] of this.deployments) {
        const backendFile = backendFileMap.get(deployment.slug);
        if (!backendFile || !backendFile.is_active) {
          deploymentsToRemove.push(notebookPath);
        }
      }

      // Remove inactive deployments
      for (const notebookPath of deploymentsToRemove) {
        await this.removeDeployment(notebookPath);
      }

      console.log(
        `[DeploymentState] Synced with backend, removed ${deploymentsToRemove.length} inactive deployments`
      );
    } catch (error) {
      console.error('[DeploymentState] Failed to sync with backend:', error);
    }
  }

  /**
   * Check if a notebook is deployed
   */
  public isDeployed(notebookPath: string): boolean {
    return this.deployments.has(notebookPath);
  }

  /**
   * Get deployment count
   */
  public getDeploymentCount(): number {
    return this.deployments.size;
  }

  /**
   * Clear all deployments (for testing or reset)
   */
  public async clearAllDeployments(): Promise<void> {
    try {
      this.deployments.clear();
      console.log('[DeploymentState] Cleared all deployments');
      this.changes$.next({
        type: 'cleared',
        notebookPath: null,
        deployment: null
      });
    } catch (error) {
      console.error('[DeploymentState] Failed to clear deployments:', error);
      throw error;
    }
  }

  /**
   * Find and load deployment from backend files by workspace_notebook_path
   */
  public async loadDeploymentFromBackend(
    workspaceNotebookPath: string,
    backendFiles: IBackendFileData[],
    appUrl: string
  ): Promise<IDeploymentData | null> {
    try {
      // Filter active files matching the workspace_notebook_path
      const matchingFiles = backendFiles.filter(
        file =>
          file.is_active &&
          file.workspace_notebook_path === workspaceNotebookPath
      );

      if (matchingFiles.length === 0) {
        return null;
      }

      // Get most recent if multiple (shouldn't happen, but handle it)
      const mostRecent = matchingFiles.sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )[0];

      const deploymentData: IDeploymentData = {
        slug: mostRecent.slug,
        deployedUrl: `${appUrl}/notebooks/${mostRecent.slug}`,
        filename: mostRecent.filename,
        deployedAt: mostRecent.created_at,
        s3_key: mostRecent.slug, // Use slug as fallback if s3_key not available
        fileSize: mostRecent.file_size || 0
      };

      // Save to local state
      const isUpdate = this.deployments.has(workspaceNotebookPath);
      this.deployments.set(workspaceNotebookPath, deploymentData);

      console.log(
        `[DeploymentState] Loaded deployment from backend for: ${workspaceNotebookPath}`
      );

      this.changes$.next({
        type: isUpdate ? 'updated' : 'added',
        notebookPath: workspaceNotebookPath,
        deployment: deploymentData
      });

      return deploymentData;
    } catch (error) {
      console.error(
        '[DeploymentState] Failed to load deployment from backend:',
        error
      );
      return null;
    }
  }

  /**
   * Get debug information
   */
  public getDebugInfo(): any {
    return {
      deploymentCount: this.deployments.size,
      deployments: Array.from(this.deployments.entries()).map(
        ([path, data]) => ({
          notebookPath: path,
          slug: data.slug,
          filename: data.filename,
          deployedAt: data.deployedAt,
          deployedUrl: data.deployedUrl
        })
      )
    };
  }
}
