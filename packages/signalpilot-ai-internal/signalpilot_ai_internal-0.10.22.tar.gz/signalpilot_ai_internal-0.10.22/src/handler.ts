import { URLExt } from '@jupyterlab/coreutils';

import { ServerConnection } from '@jupyterlab/services';

/**
 * Call the API extension
 *
 * @param endPoint API REST end point for the extension
 * @param init Initial values for the request
 * @returns The response body interpreted as JSON
 */
export async function requestAPI<T>(
  endPoint = '',
  init: RequestInit = {}
): Promise<T> {
  // Make request to Jupyter API
  const settings = ServerConnection.makeSettings();
  const requestUrl = URLExt.join(
    settings.baseUrl,
    'signalpilot-ai-internal', // API Namespace
    endPoint
  );

  let response: Response;
  try {
    response = await ServerConnection.makeRequest(requestUrl, init, settings);
  } catch (error) {
    // Check if the error is due to abort
    if (error instanceof Error && error.name === 'AbortError') {
      throw error;
    }
    throw new ServerConnection.NetworkError(error as any);
  }

  let data: any = await response.text();

  if (data.length > 0) {
    try {
      data = JSON.parse(data);
    } catch (error) {
      console.log('Not a JSON response body.', response);
    }
  }

  if (!response.ok) {
    throw new ServerConnection.ResponseError(
      response,
      data.message || data.error || data
    );
  }

  return data;
}

/**
 * File scanning API interfaces
 */
export interface IFileScanRequest {
  paths: string[];
  force_refresh?: boolean;
}

export interface IFileScanResponse {
  files: any[];
  scanned_directories: IScannedDirectory[];
  cached: boolean;
  total_files: number;
}

export interface IScannedDirectory {
  path: string;
  file_count: number;
  scanned_at?: string;
}

export interface IScannedDirectoriesResponse {
  directories: IScannedDirectory[];
}

export interface IWorkDirResponse {
  workdir: string;
}

/**
 * Open a native folder picker and return the selected absolute path
 */
export async function selectFolder(): Promise<{ path: string | null }> {
  return await requestAPI<{ path: string | null }>('files/select-folder');
}

/**
 * Scan directories for files
 */
export async function scanFiles(
  paths: string[],
  forceRefresh: boolean = false,
  signal?: AbortSignal
): Promise<IFileScanResponse> {
  const request: IFileScanRequest = {
    paths,
    force_refresh: forceRefresh
  };

  return await requestAPI<IFileScanResponse>('files/scan', {
    method: 'POST',
    body: JSON.stringify(request),
    headers: {
      'Content-Type': 'application/json'
    },
    signal
  });
}

/**
 * Get list of scanned directories
 */
export async function getScannedDirectories(): Promise<IScannedDirectoriesResponse> {
  return await requestAPI<IScannedDirectoriesResponse>('files/directories');
}

/**
 * Get current working directory from backend
 */
export async function getWorkDir(): Promise<IWorkDirResponse> {
  return await requestAPI<IWorkDirResponse>('files/workdir');
}

/**
 * Delete a scanned directory
 */
export async function deleteScannedDirectory(path: string): Promise<void> {
  return await requestAPI<void>('files/directories/delete', {
    method: 'POST',
    body: JSON.stringify({ path }),
    headers: {
      'Content-Type': 'application/json'
    }
  });
}
