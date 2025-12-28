import * as React from 'react';
import { ReactWidget } from '@jupyterlab/ui-components';
import { ISignal, Signal } from '@lumino/signaling';
import { JupyterFrontEnd } from '@jupyterlab/application';
import { AppStateService } from '../../AppState';
import {
  DataLoaderService,
  IFileEntry
} from '../../Chat/ChatContextMenu/DataLoaderService';
import { FileType, IFileExplorerState, ISupportedFileEntry } from './types';
import { FileExplorerContent } from './FileExplorerContent';
import { fileIcon } from '@jupyterlab/ui-components';
import { Message } from '@lumino/messaging';
import {
  scanFiles,
  getScannedDirectories,
  deleteScannedDirectory
} from '../../handler';
import { getWorkDir } from '../../handler';
import { IScannedDirectory } from '../../handler';
import { FileCacheService } from '../../Services/FileCacheService';

/**
 * Widget for exploring data files in the left sidebar
 */
export class FileExplorerWidget extends ReactWidget {
  private _state: IFileExplorerState;
  private _stateChanged = new Signal<this, IFileExplorerState>(this);
  private _app: JupyterFrontEnd | null = null;
  private _pollingTimer: NodeJS.Timeout | null = null;
  private _isPolling = false;
  private _fileCacheService: FileCacheService;
  private _abortController: AbortController | null = null;

  constructor() {
    super();
    this._fileCacheService = FileCacheService.getInstance();
    this._state = {
      workDir: null,
      scannedDirectories: [],
      isVisible: true,
      files: [],
      isLoading: true,
      totalFileCount: 0,
      isUploading: false
    };

    this.addClass('sage-ai-file-explorer-widget');
    this.id = 'sage-ai-file-explorer';
    this.title.closable = true;
    this.title.icon = fileIcon;

    // Set initial visibility state
    if (!this._state.isVisible) {
      this.addClass('hidden');
    }

    // Listen to cache updates
    this._fileCacheService.cacheUpdated.connect(this.onCacheUpdated, this);

    // Initialize and load files from backend
    void this.initialize();
  }

  /**
   * Dispose of the widget and clean up resources
   */
  dispose(): void {
    this._fileCacheService.cacheUpdated.disconnect(this.onCacheUpdated, this);
    this.stopPolling();
    super.dispose();
  }

  /**
   * Handle cache updates from FileCacheService
   */
  private onCacheUpdated(sender: FileCacheService, cacheState: any): void {
    this.updateState({ ...this._state, ...cacheState });
  }

  /**
   * Set the JupyterLab app instance for file browser operations
   */
  public setApp(app: JupyterFrontEnd): void {
    this._app = app;
  }

  /**
   * When the widget becomes visible after being hidden, refresh
   */
  protected onAfterShow(msg: Message): void {
    super.onAfterShow(msg);
    try {
      // Refresh files from backend
      void this.refreshFiles();
    } catch (error) {
      console.error(
        '[FileExplorerWidget] Failed to refresh files on show:',
        error
      );
    }
  }

  /**
   * Get the signal that fires when state changes
   */
  public get stateChanged(): ISignal<this, IFileExplorerState> {
    return this._stateChanged;
  }

  /**
   * Dismiss success messages
   */
  private dismissSuccess(): void {
    this.updateState({
      uploadSuccess: undefined,
      folderAddedSuccess: undefined
    });
  }

  /**
   * Render the React component
   */
  render(): JSX.Element {
    return (
      <FileExplorerContent
        state={this._state}
        onOpenInBrowser={this.handleOpenInBrowser.bind(this)}
        onFileUpload={this.handleFileUpload.bind(this)}
        onAddToContext={this.handleAddToContext.bind(this)}
        onAddFolder={this.handleAddFolder.bind(this)}
        onDeleteFolder={this.handleDeleteFolder.bind(this)}
        onCancelScanning={this.cancelScanning.bind(this)}
        onDismissSuccess={this.dismissSuccess.bind(this)}
      />
    );
  }

  /**
   * Initialize the widget
   */
  private async initialize(): Promise<void> {
    // Load files from backend
    try {
      const workdirResp = await getWorkDir();
      this._fileCacheService.updateWorkDir(workdirResp.workdir);

      AppStateService.setState({
        currentWorkingDirectory: workdirResp.workdir
      });

      await this.loadScannedDirectories();

      void this.startPollingForFiles();
    } catch (e) {
      console.warn('[FileExplorerWidget] Failed to fetch workdir:', e);
    }
  }

  /**
   * Load scanned directories from backend
   */
  private async loadScannedDirectories(): Promise<void> {
    try {
      const response = await getScannedDirectories();
      this._fileCacheService.updateCache({
        ...this._fileCacheService.getCacheState(),
        scannedDirectories: response.directories
      });
    } catch (error) {
      console.error(
        '[FileExplorerWidget] Failed to load scanned directories:',
        error
      );
    }
  }

  /**
   * Refresh files from backend
   */
  private async refreshFiles(): Promise<void> {
    try {
      // Create new AbortController for this scan
      this._abortController = new AbortController();

      const paths = this._state.scannedDirectories.map(dir => dir.path);
      if (paths.length === 0) {
        // If no directories scanned, use defaults
        paths.push('./data');
      }

      const response = await scanFiles(
        paths,
        false,
        this._abortController.signal
      );

      // Update the centralized cache
      this._fileCacheService.updateCache({
        files: response.files,
        scannedDirectories: response.scanned_directories,
        totalFileCount: response.total_files
      });
    } catch (error) {
      // Ignore abort errors
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('[FileExplorerWidget] File scan cancelled');
        return;
      }
      console.error('[FileExplorerWidget] Failed to refresh files:', error);
    }
  }

  /**
   * Handle Add Folder action: select a folder and trigger a scan
   */
  private async handleAddFolder(): Promise<void> {
    try {
      // Clear previous success states
      this.updateState({
        uploadSuccess: undefined,
        folderAddedSuccess: undefined
      });

      // Dynamically import to avoid circular deps in tests
      const { selectFolder } = await import('../../handler');

      const result = await selectFolder();
      const selectedPath = result?.path;
      if (!selectedPath) {
        return; // user cancelled
      }

      // Optimistically update scanned directories locally to include the new path
      const exists = this._state.scannedDirectories.some(
        d => d.path === selectedPath
      );
      if (!exists) {
        const newDir: IScannedDirectory = {
          path: selectedPath,
          file_count: 0
        };
        this._fileCacheService.updateCache({
          ...this._fileCacheService.getCacheState(),
          scannedDirectories: [...this._state.scannedDirectories, newDir]
        });

        // Set success state for folder addition
        this.updateState({
          folderAddedSuccess: { folderPath: selectedPath }
        });
      }
    } catch (error) {
      console.error('[FileExplorerWidget] Failed to add folder:', error);
      this.updateState({
        error: error instanceof Error ? error.message : 'Failed to add folder'
      });
    }
  }

  /**
   * Handle Delete Folder action: remove a folder from scanning
   */
  private async handleDeleteFolder(dirPath: string): Promise<void> {
    try {
      // Call backend to delete the directory
      await deleteScannedDirectory(dirPath);

      // Update local scanned directories list
      this._fileCacheService.updateCache({
        ...this._fileCacheService.getCacheState(),
        scannedDirectories: this._state.scannedDirectories.filter(
          dir => dir.path !== dirPath
        )
      });
    } catch (error) {
      console.error('[FileExplorerWidget] Failed to delete folder:', error);
      this.updateState({
        error:
          error instanceof Error ? error.message : 'Failed to delete folder'
      });
    }
  }

  private async handleAddToContext(file: ISupportedFileEntry): Promise<void> {
    console.log('[FileExplorerWidget] Add to context:', file);
    const chatMessages =
      AppStateService.getState().chatContainer?.chatWidget.messageComponent;
    if (!chatMessages) {
      console.error('[FileExplorerWidget] Chat messages not available');
      return;
    }

    // Convert file entry to mention context format
    const fileContext =
      DataLoaderService.convertFileEntryToMentionContext(file);
    if (!fileContext) {
      console.error('[FileExplorerWidget] File context not found');
      return;
    }

    chatMessages.addMentionContext(fileContext);
  }

  /**
   * Handle opening file in browser
   */
  private async handleOpenInBrowser(file: ISupportedFileEntry): Promise<void> {
    console.log('[FileExplorerWidget] Open in browser:', file);

    if (!this._app) {
      console.error('[FileExplorerWidget] JupyterLab app not available');
      return;
    }

    try {
      // Get the directory path (remove filename)
      const filePath = file.path.startsWith('./')
        ? file.path.slice(2)
        : file.path;
      const directoryPath = filePath.includes('/')
        ? filePath.substring(0, filePath.lastIndexOf('/'))
        : '';

      // First, activate the file browser tab
      await this._app.commands.execute('filebrowser:activate');

      // Navigate to the directory containing the file
      if (directoryPath) {
        await this._app.commands.execute('filebrowser:go-to-path', {
          path: directoryPath
        });
      }

      // Wait a moment for the file browser to update
      await new Promise(resolve => setTimeout(resolve, 300));

      // Try to select/highlight the specific file
      try {
        await this._app.commands.execute('filebrowser:go-to-path', {
          path: filePath
        });
      } catch (selectError) {
        // If specific file selection fails, at least we're in the right directory
        console.warn(
          '[FileExplorerWidget] Could not select specific file, but navigated to directory:',
          selectError
        );
      }

      // Open the file in the main area using the default document factory
      try {
        await this._app.commands.execute('docmanager:open', {
          path: filePath
        });
      } catch (openError) {
        console.error('[FileExplorerWidget] Failed to open file:', openError);
      }

      console.log(`[FileExplorerWidget] Opened file browser at: ${filePath}`);
    } catch (error) {
      console.error(
        '[FileExplorerWidget] Error opening file in browser:',
        error
      );

      // Fallback: just try to activate the file browser
      try {
        await this._app.commands.execute('filebrowser:activate');
      } catch (fallbackError) {
        console.error(
          '[FileExplorerWidget] Fallback file browser activation failed:',
          fallbackError
        );
      }
    }
  }

  /**
   * Update the widget state and trigger re-render
   */
  private updateState(updates: Partial<IFileExplorerState>): void {
    this._state = { ...this._state, ...updates };
    this._stateChanged.emit(this._state);
    this.update();
  }

  /**
   * Infer file info from file name and path
   */
  private inferFileInfo(name: string, path: string): any {
    const extension = name.substring(name.lastIndexOf('.')).toLowerCase();
    return {
      extension,
      is_csv: extension === '.csv',
      is_tsv: extension === '.tsv',
      is_json: extension === '.json',
      is_parquet: extension === '.parquet',
      is_pkl: ['.pkl', '.pickle'].includes(extension),
      is_data: [
        '.csv',
        '.tsv',
        '.json',
        '.parquet',
        '.pkl',
        '.pickle'
      ].includes(extension),
      is_binary: ['.parquet', '.pkl', '.pickle'].includes(extension),
      size_bytes: 0 // We don't have size info from MentionContext
    };
  }

  /**
   * Infer CSV info from content
   */
  private inferCsvInfo(content?: string): any {
    if (!content) {
      return undefined;
    }

    const lines = content.split('\n');
    const header = lines[0];
    const sampleRows = lines.slice(1, 6);

    return {
      type: 'csv',
      preview_type: 'header_and_sample',
      header,
      sample_rows: sampleRows,
      estimated_columns: header ? header.split(',').length : 0
    };
  }

  /**
   * Automatically extract schemas for supported data files in the background
   */

  /**
   * Start continuous polling for files and auto-extract schemas when files become available
   */
  private async startPollingForFiles(): Promise<void> {
    if (this._isPolling) {
      console.log(
        '[FileExplorerWidget] Polling already active, skipping start'
      );
      return;
    }

    this._isPolling = true;
    console.log('[FileExplorerWidget] Starting continuous file polling...');

    const pollForFiles = async () => {
      if (!this._isPolling) {
        return; // Stop if polling was disabled
      }

      try {
        // Create new AbortController for this poll cycle
        this._abortController = new AbortController();

        // Get paths to scan
        const paths = this._state.scannedDirectories.map(dir => dir.path);
        if (paths.length === 0) {
          // If no directories scanned, use defaults
          paths.push('./data');
        }

        // Scan files from backend
        const response = await scanFiles(
          paths,
          false,
          this._abortController.signal
        );
        const { files, scanned_directories, total_files } = response;

        const mergedDirectories = [
          ...this._state.scannedDirectories,
          ...scanned_directories
        ];
        const mergedDirectoriesMap = new Map(
          mergedDirectories.map(dir => [dir.path, dir])
        );
        const uniqueDirectories = Array.from(mergedDirectoriesMap.values());

        // Update the centralized cache
        this._fileCacheService.updateCache({
          files: files,
          totalFileCount: total_files,
          scannedDirectories: uniqueDirectories
        });

        // const oldFilesMap = new Map(
        //   this._state.files.map(f => [f.absolute_path, f])
        // );
        // const newFilesMap = new Map(files.map(f => [f.absolute_path, f]));

        // // Find new files (in backend response, not in state)
        // const newFiles = files.filter(f => !oldFilesMap.has(f.absolute_path));
        // // Find files that still exist (in both backend response and state)
        // const existingFiles = this._state.files.filter(f =>
        //   newFilesMap.has(f.absolute_path)
        // );
        // // Remove files that were deleted from backend (i.e., not in newFilesMap)
        // // Only keep files that are in the backend response and not uploaded
        // const updatedFiles = [...newFiles, ...existingFiles].filter(
        //   file => !file.uploaded
        // );

        // // Only update state if there are changes (new files or deleted files)
        // const currentPaths = new Set(
        //   this._state.files.map(f => f.absolute_path)
        // );
        // const updatedPaths = new Set(updatedFiles.map(f => f.absolute_path));

        // if (!this.setsAreEqual(currentPaths, updatedPaths)) {
        //   this.updateState({
        //     files: updatedFiles,
        //     isLoading: false,
        //     totalFileCount: response.total_files
        //   });
        // }

        // Continue polling - never stop
        if (this._isPolling) {
          this._pollingTimer = setTimeout(pollForFiles, 3000); // Poll every 3 seconds
        }
      } catch (error) {
        // Handle abort errors - just continue polling after a short delay
        if (error instanceof Error && error.name === 'AbortError') {
          console.log(
            '[FileExplorerWidget] File scan cancelled during polling, continuing...'
          );
          // Continue polling after cancellation
          if (this._isPolling) {
            this._pollingTimer = setTimeout(pollForFiles, 1000); // Short delay after cancel
          }
          return;
        }

        console.error('[FileExplorerWidget] Error during polling:', error);

        // Continue polling even on error
        if (this._isPolling) {
          this._pollingTimer = setTimeout(pollForFiles, 5000); // Longer interval on error
        }
      }
    };

    // Start first poll immediately
    await pollForFiles();
  }

  /**
   * Helper method to compare two sets for equality
   */
  private setsAreEqual<T>(set1: Set<T>, set2: Set<T>): boolean {
    if (set1.size !== set2.size) {
      return false;
    }
    for (const item of set1) {
      if (!set2.has(item)) {
        return false;
      }
    }
    return true;
  }

  /**
   * Stop the polling timer and disable polling
   */
  private stopPolling(): void {
    console.log('[FileExplorerWidget] Stopping file polling...');
    this._isPolling = false;
    if (this._pollingTimer) {
      clearTimeout(this._pollingTimer);
      this._pollingTimer = null;
    }
  }

  /**
   * Cancel ongoing file scanning operations
   * Note: This only cancels the current scan request, polling will continue
   */
  public cancelScanning(): void {
    console.log('[FileExplorerWidget] Cancelling current file scan...');

    // Abort any ongoing requests (this will cause the current poll cycle to catch AbortError)
    if (this._abortController) {
      this._abortController.abort();
      this._abortController = null;
    }

    // Remove directories that were being scanned (don't have scanned_at)
    // These are directories that were added but scanning was cancelled
    const completedDirectories = this._state.scannedDirectories.filter(
      dir => dir.scanned_at !== undefined && dir.scanned_at !== ''
    );

    // Update cache service to remove incomplete directories
    this._fileCacheService.updateCache({
      files: this._fileCacheService.getFiles(),
      scannedDirectories: completedDirectories,
      totalFileCount: this._fileCacheService.getTotalFileCount()
    });

    // Set loading to false
    this._fileCacheService.setLoading(false);

    // Reload scanned directories from backend to ensure consistency
    void this.loadScannedDirectories();

    // Update state to reflect cancellation
    this.updateState({
      isLoading: false
    });

    // Note: Polling continues automatically - the next poll cycle will start after the timeout
    // The AbortError in the polling loop is already handled and polling will continue
  }

  /**
   * Handle file upload
   */
  private async handleFileUpload(files: FileList): Promise<void> {
    try {
      const totalFileCount = files.length;
      console.log(
        '[FileExplorerWidget] Starting file upload:',
        totalFileCount,
        'files'
      );

      this.updateState({
        isUploading: true,
        uploadProgress: { completed: 0, total: totalFileCount },
        error: undefined,
        uploadSuccess: undefined,
        folderAddedSuccess: undefined
      });

      const contentManager = AppStateService.getState().contentManager;
      if (!contentManager) {
        throw new Error('Content manager not available');
      }

      const uploadedFiles: IFileEntry[] = [];

      for (let i = 0; i < files.length; i++) {
        const file = files[i];

        try {
          // Upload file to /data directory
          const filePath = `data/${file.name}`;
          const content = await this.readFileAsText(file);

          const model = {
            type: 'file' as const,
            format: 'text' as const,
            content
          };

          await contentManager.save(filePath, model);
          console.log('[FileExplorerWidget] Uploaded file:', filePath);

          // Create FileEntry for the uploaded file
          const fileEntry: ISupportedFileEntry = {
            uploaded: true,
            absolute_path: filePath,
            id: filePath,
            name: file.name,
            path: `./${filePath}`,
            relative_path: file.name,
            is_directory: false,
            file_info: this.inferFileInfo(file.name, filePath),
            content_preview: content.substring(0, 5000), // First 5000 chars
            csv_info:
              file.name.endsWith('.csv') || file.name.endsWith('.tsv')
                ? this.inferCsvInfo(content)
                : undefined,
            schema: {
              success: false,
              loading: true,
              error: false
            },
            displayPath: file.name,
            fileType: file.name.split('.').pop()?.toLowerCase() as FileType,
            hasSchema: false,
            isExpanded: false
          };

          uploadedFiles.push(fileEntry);

          // Update progress
          this.updateState({
            uploadProgress: { completed: i + 1, total: totalFileCount }
          });
        } catch (error) {
          console.error(
            '[FileExplorerWidget] Failed to upload file:',
            file.name,
            error
          );
          // Continue with other files even if one fails
        }
      }

      // Add uploaded files to state immediately for instant feedback
      if (uploadedFiles.length > 0) {
        // Add to current state
        const currentFiles = [...this._state.files];
        const newFiles = [...uploadedFiles, ...currentFiles];

        this.updateState({
          files: newFiles,
          totalFileCount: newFiles.length
        });

        console.log(
          '[FileExplorerWidget] Files uploaded successfully. Schemas can be extracted on-demand.'
        );
      }

      // Refresh files from backend to include uploaded files
      // void this.refreshFiles();

      this.updateState({
        isUploading: false,
        uploadProgress: undefined,
        uploadSuccess:
          uploadedFiles.length > 0 ? { fileCount: totalFileCount } : undefined
      });

      console.log('[FileExplorerWidget] File upload completed successfully');
    } catch (error) {
      console.error('[FileExplorerWidget] File upload failed:', error);
      this.updateState({
        isUploading: false,
        uploadProgress: undefined,
        uploadSuccess: undefined,
        error: error instanceof Error ? error.message : 'Upload failed'
      });
    }
  }

  /**
   * Read file as text
   */
  private readFileAsText(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = e => {
        resolve((e.target?.result as string) || '');
      };
      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };
      reader.readAsText(file);
    });
  }

  /**
   * Get file type from path
   */
  private getFileTypeFromPath(path: string): string | null {
    const extension = path.toLowerCase().split('.').pop();
    switch (extension) {
      case 'csv':
        return 'csv';
      case 'tsv':
        return 'tsv';
      case 'json':
        return 'json';
      case 'parquet':
        return 'parquet';
      case 'pkl':
      case 'pickle':
        return 'pkl';
      default:
        return null;
    }
  }
}
