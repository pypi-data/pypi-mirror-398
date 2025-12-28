import { JupyterAuthService } from './JupyterAuthService';
import {
  DeploymentStateService,
  IDeploymentData
} from './DeploymentStateService';

export interface ISignedUrlResponse {
  upload_url: string;
  s3_key: string;
  expires_in: number;
}

export interface ISaveMetadataResponse {
  data: {
    id: string;
    slug: string;
    filename: string;
    file_size: number;
    s3_key_ipynb?: string | null;
    is_active: boolean;
    created_at: string;
  };
  message: string;
}

export interface IFileDownloadResponse {
  filename: string;
  download_url: string;
}

export interface IDeployedFileData {
  id: string;
  slug: string;
  filename: string;
  file_size: number | null;
  workspace_notebook_path: string | null;
  is_active: boolean;
  user_email: string;
  created_at: string;
}

export interface IListFilesResponse {
  data: IDeployedFileData[];
}

export class CloudUploadService {
  private static instance: CloudUploadService;
  private readonly PROD_API_URL = 'https://sage.alpinex.ai:8761';
  private readonly DEV_API_URL = 'http://localhost:8000';

  private constructor() {}

  public static getInstance(): CloudUploadService {
    if (!CloudUploadService.instance) {
      CloudUploadService.instance = new CloudUploadService();
    }
    return CloudUploadService.instance;
  }

  /**
   * Get the appropriate API base URL based on environment
   */
  private getApiBaseUrl(): string {
    // const isDev = process.env.NODE_ENV === 'development';

    // if (isDev) {
    //   return this.DEV_API_URL;
    // }

    return this.PROD_API_URL;
  }

  /**
   * Get the appropriate app URL based on environment
   */
  public getAppUrl(): string {
    // const isDev = process.env.NODE_ENV === 'development';

    // if (isDev) {
    //   return 'http://localhost:3000';
    // }

    return 'https://app.signalpilot.ai';
  }

  /**
   * Get authentication headers
   */
  private async getAuthHeaders(): Promise<HeadersInit> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json'
    };

    try {
      // Try to get JWT token from JupyterAuthService
      const token = await JupyterAuthService.getJwtToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        return headers;
      }
    } catch (error) {
      console.warn('[CloudUpload] Failed to get JWT token:', error);
    }

    return headers;
  }

  /**
   * Request a presigned URL for uploading
   */
  public async getSignedUrl(filename: string): Promise<ISignedUrlResponse> {
    const apiUrl = this.getApiBaseUrl();
    const headers = await this.getAuthHeaders();

    try {
      const response = await fetch(`${apiUrl}/files/upload-url`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ filename })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Failed to get signed URL: ${response.status} ${errorText}`
        );
      }

      const data = await response.json();
      console.log('[CloudUpload] Got signed URL for:', filename);
      return data;
    } catch (error) {
      console.error('[CloudUpload] Error getting signed URL:', error);
      throw error;
    }
  }

  /**
   * Upload HTML content to S3 using presigned URL
   */
  public async uploadToS3(
    signedUrl: string,
    htmlContent: string
  ): Promise<void> {
    try {
      const response = await fetch(signedUrl, {
        method: 'PUT',
        body: htmlContent,
        headers: {
          'Content-Type': 'text/html'
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Failed to upload to S3: ${response.status} ${errorText}`
        );
      }

      console.log('[CloudUpload] Successfully uploaded to S3');
    } catch (error) {
      console.error('[CloudUpload] Error uploading to S3:', error);
      throw error;
    }
  }

  /**
   * Save file metadata after successful upload
   */
  public async saveMetadata(
    s3_key: string,
    s3_key_ipynb: string | null,
    filename: string,
    fileSize: number,
    workspace_notebook_path: string
  ): Promise<ISaveMetadataResponse> {
    const apiUrl = this.getApiBaseUrl();
    const headers = await this.getAuthHeaders();

    try {
      const payload: any = {
        s3_key,
        filename,
        file_size: fileSize,
        workspace_notebook_path
      };

      // Only include s3_key_ipynb if it's not null
      if (s3_key_ipynb) {
        payload.s3_key_ipynb = s3_key_ipynb;
      }

      const response = await fetch(`${apiUrl}/files/save`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Failed to save metadata: ${response.status} ${errorText}`
        );
      }

      const data = await response.json();
      console.log('[CloudUpload] Saved metadata, got slug:', data.data.slug);
      return data;
    } catch (error) {
      console.error('[CloudUpload] Error saving metadata:', error);
      throw error;
    }
  }

  /**
   * Get download URL for a file by slug
   */
  public async getFileBySlug(slug: string): Promise<IFileDownloadResponse> {
    const apiUrl = this.getApiBaseUrl();
    const headers = await this.getAuthHeaders();

    try {
      const response = await fetch(`${apiUrl}/files/${slug}`, {
        method: 'GET',
        headers
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to get file: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      console.log('[CloudUpload] Got download URL for slug:', slug);
      return data;
    } catch (error) {
      console.error('[CloudUpload] Error getting file by slug:', error);
      throw error;
    }
  }

  /**
   * Deactivate/delete a deployed file
   */
  public async deactivateFile(slug: string): Promise<void> {
    const apiUrl = this.getApiBaseUrl();
    const headers = await this.getAuthHeaders();

    try {
      const response = await fetch(`${apiUrl}/files/${slug}`, {
        method: 'DELETE',
        headers
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Failed to deactivate file: ${response.status} ${errorText}`
        );
      }

      console.log('[CloudUpload] Successfully deactivated file:', slug);
    } catch (error) {
      console.error('[CloudUpload] Error deactivating file:', error);
      throw error;
    }
  }

  /**
   * List all deployed files for the current user
   */
  public async listUserFiles(): Promise<IListFilesResponse> {
    const apiUrl = this.getApiBaseUrl();
    const headers = await this.getAuthHeaders();

    try {
      const response = await fetch(`${apiUrl}/files`, {
        method: 'GET',
        headers
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Failed to list files: ${response.status} ${errorText}`
        );
      }

      const data = await response.json();
      console.log(
        '[CloudUpload] Retrieved user files:',
        data.data?.length || 0
      );
      return data;
    } catch (error) {
      console.error('[CloudUpload] Error listing files:', error);
      throw error;
    }
  }

  /**
   * Redeploy an existing file (replaces old version)
   */
  public async redeployFile(
    slug: string,
    s3_key: string,
    s3_key_ipynb: string | null,
    filename: string,
    fileSize: number,
    workspace_notebook_path: string
  ): Promise<ISaveMetadataResponse> {
    const apiUrl = this.getApiBaseUrl();
    const headers = await this.getAuthHeaders();

    try {
      const payload: any = {
        s3_key,
        filename,
        file_size: fileSize,
        workspace_notebook_path
      };

      // Only include s3_key_ipynb if it's not null
      if (s3_key_ipynb) {
        payload.s3_key_ipynb = s3_key_ipynb;
      }

      const response = await fetch(`${apiUrl}/files/redeploy/${slug}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Failed to redeploy file: ${response.status} ${errorText}`
        );
      }

      const data = await response.json();
      console.log('[CloudUpload] Successfully redeployed file:', slug);
      return data;
    } catch (error) {
      console.error('[CloudUpload] Error redeploying file:', error);
      throw error;
    }
  }

  /**
   * Complete upload workflow
   */
  public async uploadWorkflow(
    filename: string,
    htmlContent: string,
    notebookPath: string,
    ipynbContent: string | null = null
  ): Promise<IDeploymentData> {
    try {
      console.log('[CloudUpload] Starting upload workflow for:', filename);

      // Check if notebook is already deployed
      const deploymentState = DeploymentStateService.getInstance();
      const existingDeployment = deploymentState.getDeployment(notebookPath);

      let metadataResponse: ISaveMetadataResponse;
      let s3_key_ipynb: string | null = null;

      // Step 1: Upload HTML file
      const signedUrlData = await this.getSignedUrl(filename);
      const s3_key = signedUrlData.s3_key;
      await this.uploadToS3(signedUrlData.upload_url, htmlContent);
      console.log('[CloudUpload] HTML file uploaded to:', s3_key);

      // Step 2: Upload IPYNB file if content is provided
      if (ipynbContent) {
        try {
          const ipynbFilename = filename.replace('.html', '.ipynb');
          const ipynbSignedUrlData = await this.getSignedUrl(ipynbFilename);
          s3_key_ipynb = ipynbSignedUrlData.s3_key;

          // Upload as JSON content type
          const response = await fetch(ipynbSignedUrlData.upload_url, {
            method: 'PUT',
            body: ipynbContent,
            headers: {
              'Content-Type': 'text/html'
            }
          });

          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
              `Failed to upload IPYNB to S3: ${response.status} ${errorText}`
            );
          }

          console.log('[CloudUpload] IPYNB file uploaded to:', s3_key_ipynb);
        } catch (error) {
          console.warn('[CloudUpload] Failed to upload IPYNB file:', error);
          // Continue with HTML-only upload if IPYNB upload fails
          s3_key_ipynb = null;
        }
      }

      // Step 3: Save or redeploy metadata
      if (existingDeployment) {
        // Existing deployment: use redeploy endpoint
        console.log(
          '[CloudUpload] Redeploying existing deployment:',
          existingDeployment.slug
        );

        metadataResponse = await this.redeployFile(
          existingDeployment.slug,
          s3_key,
          s3_key_ipynb,
          filename,
          htmlContent.length,
          notebookPath
        );
      } else {
        // New deployment: use standard flow
        metadataResponse = await this.saveMetadata(
          s3_key,
          s3_key_ipynb,
          filename,
          htmlContent.length,
          notebookPath
        );
      }

      // Step 4: Create deployment data
      const deploymentData: IDeploymentData = {
        slug: metadataResponse.data.slug,
        deployedUrl: `${this.getAppUrl()}/notebooks/${metadataResponse.data.slug}`,
        filename: metadataResponse.data.filename,
        deployedAt: metadataResponse.data.created_at,
        s3_key: s3_key,
        fileSize: metadataResponse.data.file_size
      };

      // Step 5: Save to deployment state
      await deploymentState.saveDeployment(notebookPath, deploymentData);

      console.log('[CloudUpload] Upload workflow completed successfully');
      return deploymentData;
    } catch (error) {
      console.error('[CloudUpload] Upload workflow failed:', error);
      throw error;
    }
  }

  /**
   * Complete deletion workflow
   */
  public async deleteWorkflow(
    slug: string,
    notebookPath: string
  ): Promise<void> {
    try {
      console.log('[CloudUpload] Starting delete workflow for:', slug);

      // Step 1: Deactivate file on backend
      await this.deactivateFile(slug);

      // Step 2: Remove from deployment state
      const deploymentState = DeploymentStateService.getInstance();
      await deploymentState.removeDeployment(notebookPath);

      console.log('[CloudUpload] Delete workflow completed successfully');
    } catch (error) {
      console.error('[CloudUpload] Delete workflow failed:', error);
      throw error;
    }
  }

  /**
   * Initialize the service and sync with backend
   */
  public async initialize(): Promise<void> {
    try {
      console.log('[CloudUpload] Initializing CloudUploadService');

      // TODO: Implement listUserFiles() when backend supports it
      // For now, we'll rely on local state only
      console.log('[CloudUpload] CloudUploadService initialized');
    } catch (error) {
      console.error(
        '[CloudUpload] Failed to initialize CloudUploadService:',
        error
      );
    }
  }

  /**
   * Get debug information
   */
  public getDebugInfo(): any {
    return {
      apiBaseUrl: this.getApiBaseUrl(),
      isDev: this.getApiBaseUrl() === this.DEV_API_URL,
      deploymentState: DeploymentStateService.getInstance().getDebugInfo()
    };
  }
}
