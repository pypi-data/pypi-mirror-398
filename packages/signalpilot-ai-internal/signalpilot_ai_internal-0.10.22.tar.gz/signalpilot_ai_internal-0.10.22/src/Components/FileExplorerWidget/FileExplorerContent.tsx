import * as React from 'react';
import { FileType, IFileExplorerState, ISupportedFileEntry } from './types';
import { buildFileTree } from './treeUtils';
import { FolderItem } from './FolderItem';
import { IScannedDirectory } from '../../handler';
import { ConfirmationDialog } from '../ConfirmationDialog';
import { AppStateService } from '../../AppState';

// Utility function to truncate directory paths
const truncatePath = (fullPath: string, workDir?: string): string => {
  let path = fullPath;

  // Normalize separators to /
  path = path.replace(/\\/g, '/');

  // If workDir is provided and the path is inside the working directory, show relative path
  if (workDir) {
    const normalizedWorkDir = workDir.replace(/\\/g, '/');
    if (
      path.startsWith(normalizedWorkDir + '/') ||
      path === normalizedWorkDir
    ) {
      const relativePath =
        path === normalizedWorkDir
          ? '.'
          : path.substring(normalizedWorkDir.length + 1);
      return relativePath || '.';
    }
  }

  // For paths outside working directory, show last two folders
  const pathParts = path.split('/').filter(part => part.length > 0);

  if (pathParts.length <= 2) {
    return pathParts.join('/') || fullPath;
  }

  // Show last two parts with ellipsis
  const lastTwo = pathParts.slice(-2);
  return '.../' + lastTwo.join('/');
};

interface IFileUploadBoxProps {
  onFileUpload: (files: FileList) => void;
  disabled?: boolean;
}

const FileUploadBox: React.FC<IFileUploadBoxProps> = ({
  onFileUpload,
  disabled
}) => {
  const [isDragOver, setIsDragOver] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    if (disabled) {
      return;
    }

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onFileUpload(files);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileUpload(files);
    }
    // Reset input value so same file can be selected again
    e.target.value = '';
  };

  const handleClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div
      className={`file-upload-box ${isDragOver ? 'drag-over' : ''} ${disabled ? 'disabled' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".csv,.tsv,.parquet,.pkl,.pickle,.json,.jsonl,.xlsx"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        disabled={disabled}
      />
      <div className="upload-text">
        <span className="upload-primary">
          Drop files here or click to upload
        </span>
        <span className="upload-secondary">
          Supports CSV, TSV, Parquet, Pickle, JSON and XLSX files
        </span>
      </div>
    </div>
  );
};

interface IFileExplorerContentProps {
  state: IFileExplorerState;
  onOpenInBrowser: (file: ISupportedFileEntry) => void;
  onFileUpload: (files: FileList) => void;
  onAddToContext: (file: ISupportedFileEntry) => void;
  onAddFolder: () => void;
  onDeleteFolder: (dirPath: string) => void;
  onCancelScanning: () => void;
  onDismissSuccess?: () => void;
}

export const FileExplorerContent: React.FC<IFileExplorerContentProps> = ({
  state,
  onOpenInBrowser,
  onFileUpload,
  onAddToContext,
  onAddFolder,
  onDeleteFolder,
  onCancelScanning,
  onDismissSuccess
}) => {
  const { scannedDirectories, workDir } = state;

  // State for tracking collapsed directories
  const [collapsedDirectories, setCollapsedDirectories] = React.useState<
    Set<string>
  >(new Set());

  // State for tracking which directory menu is open
  const [openMenuDir, setOpenMenuDir] = React.useState<string | null>(null);

  // State for demo mode
  const [isDemoMode, setIsDemoMode] = React.useState<boolean>(
    AppStateService.isDemoMode()
  );

  // Subscribe to demo mode changes
  React.useEffect(() => {
    const subscription = AppStateService.changes.subscribe(state => {
      setIsDemoMode(state.isDemoMode);
    });
    return () => subscription.unsubscribe();
  }, []);

  // Toggle directory collapse state
  const toggleDirectoryCollapse = (dirPath: string) => {
    setCollapsedDirectories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(dirPath)) {
        newSet.delete(dirPath);
      } else {
        newSet.add(dirPath);
      }
      return newSet;
    });
  };

  // Toggle directory menu
  const toggleDirectoryMenu = (dirPath: string) => {
    setOpenMenuDir(prev => (prev === dirPath ? null : dirPath));
  };

  // Close directory menu
  const closeDirectoryMenu = () => {
    setOpenMenuDir(null);
  };

  // Handle remove folder action
  const handleRemoveFolder = (dirPath: string) => {
    closeDirectoryMenu();
    void ConfirmationDialog.showConfirmation(
      'Remove Folder',
      `Are you sure you want to remove this folder from the file scanner?\n\n${dirPath}`,
      'Remove',
      'Cancel'
    ).then(confirmed => {
      if (confirmed) {
        onDeleteFolder(dirPath);
      }
    });
  };

  // Close menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (openMenuDir) {
        const target = event.target as Element;
        if (!target.closest('.dir-menu-container')) {
          closeDirectoryMenu();
        }
      }
    };

    if (openMenuDir) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [openMenuDir]);

  if (!state.isVisible) {
    return null;
  }

  // Filter and convert files to supported format
  const supportedFiles: ISupportedFileEntry[] = state.files
    .filter(file => {
      // Only show non-directory, non-binary files
      if (file.is_directory) {
        return false;
      }

      // Check for supported file types
      const filePath =
        (
          file.path ||
          file.absolute_path ||
          file.relative_path
        )?.toLowerCase() || '';
      return (
        filePath.endsWith('.csv') ||
        filePath.endsWith('.tsv') ||
        filePath.endsWith('.parquet') ||
        filePath.endsWith('.pkl') ||
        filePath.endsWith('.pickle') ||
        filePath.endsWith('.xlsx') ||
        filePath.endsWith('.json') ||
        filePath.endsWith('.jsonl') ||
        filePath.endsWith('.ipynb')
      );
    })
    .map(file => ({
      ...file,
      displayPath: file.relative_path,
      fileType: (file.path.split('.').pop() || '').toLowerCase() as FileType,
      schema: file.schema,
      hasSchema: file.schema ? true : false
    }));

  // Determine directories to render: scanned or sensible defaults
  const directories: IScannedDirectory[] = (() => {
    if (scannedDirectories && scannedDirectories.length > 0) {
      return scannedDirectories.sort((a, b) => {
        const aRelativePath = a.path.replace(workDir || '', '');
        const bRelativePath = b.path.replace(workDir || '', '');
        const aIsDefault = aRelativePath === '/data';
        const bIsDefault = bRelativePath === '/data';
        const aIsLoading = !a.scanned_at;
        const bIsLoading = !b.scanned_at;

        // 1. Default directories first
        if (aIsDefault && !bIsDefault) {
          return -1;
        }
        if (!aIsDefault && bIsDefault) {
          return 1;
        }

        // 2. Loading directories second (among non-default or after default)
        if (aIsLoading && !bIsLoading) {
          return -1;
        }
        if (!aIsLoading && bIsLoading) {
          return 1;
        }

        // 3. Then by scanned_at desc (most recent first)
        if (a.scanned_at && b.scanned_at) {
          return (
            new Date(b.scanned_at).getTime() - new Date(a.scanned_at).getTime()
          );
        }
        if (a.scanned_at && !b.scanned_at) {
          return -1;
        }
        if (!a.scanned_at && b.scanned_at) {
          return 1;
        }

        // Fallback to path comparison
        return a.path.localeCompare(b.path);
      });
    }
    return [
      {
        path: './data',
        file_count: 0,
        scanned_at: ''
      }
    ];
  })();

  // Group supported files by directory and build a tree per directory
  const treesByDirectory = (() => {
    const map = new Map<string, ISupportedFileEntry[]>();
    for (const dir of directories) {
      map.set(dir.path, []);
    }

    for (const file of supportedFiles) {
      // Use absolute path for matching
      const absPath = file.absolute_path.replace(/\\/g, '/');

      // Compute absolute directory path for each scanned dir
      // If dir.path is absolute, use as-is; if relative, join with workDir
      // Normalize separators to '/'
      // Prefer the longest matching scanned directory prefix
      let match: string | null = null;
      for (const dir of directories) {
        const dirPathRaw = dir.path;
        const isAbsolute =
          dirPathRaw.startsWith('/') || /^[A-Za-z]:\\/.test(dirPathRaw);

        let base: string;
        if (isAbsolute) {
          base = dirPathRaw;
        } else if (workDir) {
          base = `${workDir}/${dirPathRaw.replace(/^\.\/?/, '')}`;
        } else {
          base = dirPathRaw;
        }

        const normalizedDir = base.replace(/\\/g, '/');
        const prefix = normalizedDir.endsWith('/')
          ? normalizedDir
          : `${normalizedDir}/`;
        if (absPath === normalizedDir || absPath.startsWith(prefix)) {
          if (!match || dir.path.length > match.length) {
            match = dir.path;
          }
        }
      }
      if (!match) {
        // Fallback: if absolute path contains '/data/', associate with './data'; else '.'
        match = absPath.includes('/data/') ? './data' : '.';
        if (!map.has(match)) {
          map.set(match, []);
        }
      }
      map.get(match)!.push(file);
    }

    const trees = new Map<string, ReturnType<typeof buildFileTree>>();
    for (const [dirPath, files] of map.entries()) {
      // Compute absolute base path for dirPath when possible to make files relative
      let baseAbs: string | undefined = undefined;
      const dir = directories.find(d => d.path === dirPath);
      if (dir) {
        const dirPathRaw = dir.path;
        const isAbsolute =
          dirPathRaw.startsWith('/') || /^[A-Za-z]:\\/.test(dirPathRaw);
        if (isAbsolute) {
          baseAbs = dirPathRaw.replace(/\\/g, '/');
        } else if (workDir) {
          baseAbs = `${workDir}/${dirPathRaw.replace(/^\.\/?/, '')}`.replace(
            /\\/g,
            '/'
          );
        }
      }
      trees.set(dirPath, buildFileTree(files, baseAbs));
    }
    return trees;
  })();

  const isScanningDir = state.scannedDirectories.some(dir => !dir.scanned_at);
  const isScanningFiles = supportedFiles.some(
    file => !file.schema || file.schema.loading === true
  );

  // Handler to dismiss success toast
  const handleDismissSuccess = () => {
    if (onDismissSuccess) {
      onDismissSuccess();
    }
  };

  return (
    <div className="sage-ai-file-explorer-content">
      <div className="file-explorer-header">
        <h3>File Scanner</h3>
      </div>

      {state.isLoading && (
        <div className="loading-indicator">
          <div className="loading-spinner"></div>
          <span>Loading files...</span>
        </div>
      )}

      {state.error && (
        <div className="error-message">
          <div className="error-icon">⚠️</div>
          <span>{state.error}</span>
        </div>
      )}

      {!state.isLoading && !state.error && (
        <>
          {/* File Upload Component */}
          <div className="file-upload-container">
            {isDemoMode && (
              <div className="file-upload-overlay">
                <button
                  className="file-upload-overlay-button"
                  onClick={() => {
                    window.open('https://signalpilot.ai/download', '_blank');
                  }}
                >
                  Install SignalPilot to try it
                </button>
              </div>
            )}
            <div className="file-upload-info">
              <strong>Upload your files</strong>
            </div>
            <FileUploadBox
              onFileUpload={onFileUpload}
              disabled={state.isUploading || isDemoMode}
            />
            <span style={{ margin: '0 auto' }}>
              <strong>Or</strong>
            </span>
            <button
              className="add-folder-button"
              onClick={onAddFolder}
              disabled={state.isUploading || isDemoMode}
            >
              Add Folder
            </button>
          </div>

          {/* Loading/Progress Toast */}
          {(state.isUploading || isScanningDir || isScanningFiles) && (
            <div className="upload-progress">
              <div className="loading-spinner"></div>
              <span>
                Loading file schemas...
                {state.uploadProgress &&
                  ` (${state.uploadProgress.completed}/${state.uploadProgress.total})`}
              </span>
              <button
                className="cancel-scan-button"
                onClick={onCancelScanning}
                title="Cancel scanning"
              >
                Cancel
              </button>
            </div>
          )}

          {/* Success Toast */}
          {!state.isUploading && !isScanningDir && !isScanningFiles && (
            <>
              {state.uploadSuccess && (
                <div className="upload-progress upload-success">
                  <span>
                    {state.uploadSuccess.fileCount === 1
                      ? '1 file added to data folder'
                      : `${state.uploadSuccess.fileCount} files added to data folder`}
                  </span>
                  <div
                    style={{ display: 'flex', gap: '8px', marginLeft: 'auto' }}
                  >
                    <button
                      className="close-toast-button"
                      onClick={handleDismissSuccess}
                      title="Close"
                    >
                      ×
                    </button>
                  </div>
                </div>
              )}
              {state.folderAddedSuccess && (
                <div className="upload-progress upload-success">
                  <span>Folder added</span>
                  <div
                    style={{ display: 'flex', gap: '8px', marginLeft: 'auto' }}
                  >
                    <button
                      className="close-toast-button"
                      onClick={handleDismissSuccess}
                      title="Close"
                    >
                      ×
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          <div className="file-list">
            {directories.map(dir => {
              const tree = treesByDirectory.get(dir.path) || [];
              const relativePath = dir.path.replace(workDir || '', '');
              const isDefault = relativePath === '/data';
              const hasFiles = tree.length > 0;
              const folderCount = tree.filter(
                node => node.type === 'folder'
              ).length;
              const isLoading = !dir.scanned_at;
              const isCollapsed = collapsedDirectories.has(dir.path);

              return (
                <div
                  className={`scanned-dir-section ${isLoading ? 'skeleton-loading' : ''} ${isCollapsed ? 'collapsed' : ''}`}
                  key={dir.path}
                >
                  <div
                    className="scanned-dir-header"
                    onClick={() => toggleDirectoryCollapse(dir.path)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="scanned-dir-header-left">
                      <span className="scanned-dir-path" title={dir.path}>
                        {truncatePath(dir.path, workDir || undefined)}
                      </span>
                      <span
                        className={`dir-badge ${isDefault ? 'default' : 'added'}`}
                      >
                        {isDefault ? 'Default' : 'Added'}
                      </span>
                      <span className="dir-count">
                        {isLoading && 'Scanning...'}
                        {(hasFiles &&
                          folderCount &&
                          `${folderCount} folder${folderCount !== 1 ? 's, ' : ', '}`) ||
                          ''}
                        {(hasFiles &&
                          dir.file_count &&
                          `${dir.file_count} file${dir.file_count !== 1 ? 's' : ''}`) ||
                          ''}
                      </span>
                    </div>
                    {!isDefault && (
                      <div className="dir-menu-container">
                        <button
                          className="dir-menu-button"
                          onClick={e => {
                            e.stopPropagation();
                            toggleDirectoryMenu(dir.path);
                          }}
                          title="Folder options"
                        >
                          ⋮
                        </button>
                        {openMenuDir === dir.path && (
                          <div className="dir-menu-dropdown">
                            <button
                              className="dir-menu-item"
                              onClick={e => {
                                e.stopPropagation();
                                handleRemoveFolder(dir.path);
                              }}
                            >
                              Remove folder
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  {!isCollapsed && (
                    <div className="dir-content">
                      {isLoading ? (
                        <div className="file-tree">
                          {/* Show skeleton file items while loading */}
                          {Array.from({ length: 3 }, (_, index) => (
                            <div
                              key={`skeleton-${index}`}
                              className="file-item"
                            >
                              <div className="file-header">
                                <div className="file-icon">📄</div>
                                <div className="file-info">
                                  <div className="file-name">
                                    <span className="file-name-text">
                                      Loading...
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : hasFiles ? (
                        <div className="file-tree">
                          {tree.map((node, index) => (
                            <FolderItem
                              key={
                                node.type === 'file'
                                  ? node.file.id
                                  : `${node.name}-${index}`
                              }
                              node={node}
                              onOpenInBrowser={onOpenInBrowser}
                              onAddToContext={onAddToContext}
                            />
                          ))}
                        </div>
                      ) : (
                        <div className="empty-message small">
                          <span>No supported data files found</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="file-count-info">
            <span className="count-text">
              Showing {supportedFiles.length} files
            </span>
          </div>
        </>
      )}
    </div>
  );
};
