import * as React from 'react';
import { TreeNode, ISupportedFileEntry } from './types';
import { ARROW_DOWN_ICON, FOLDER_ICON, FILE_ICON } from './icons';
import { countFilesInTree } from './treeUtils';
import { DataLoaderService } from '../../Chat/ChatContextMenu/DataLoaderService';
import { AppStateService } from '../../AppState';

// Helper function to format file size
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

// Helper function to format date
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleString();
  } catch {
    return dateString;
  }
};

interface IFolderItemProps {
  node: TreeNode;
  onOpenInBrowser: (file: ISupportedFileEntry) => void;
  onAddToContext: (file: ISupportedFileEntry) => void;
  depth?: number;
}

interface IFileItemProps {
  file: ISupportedFileEntry;
  onOpenInBrowser: (file: ISupportedFileEntry) => void;
  onAddToContext: (file: ISupportedFileEntry) => void;
  depth?: number;
}

export const FolderItem: React.FC<IFolderItemProps> = ({
  node,
  onOpenInBrowser,
  onAddToContext,
  depth = 0
}) => {
  if (node.type === 'file') {
    return (
      <FileItem
        file={node.file}
        onOpenInBrowser={onOpenInBrowser}
        onAddToContext={onAddToContext}
        depth={depth}
      />
    );
  }

  const [isExpanded, setIsExpanded] = React.useState(false);
  const fileCount = countFilesInTree(node.children);

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div className="folder-item">
      <div
        className="folder-header"
        onClick={handleToggle}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        <ARROW_DOWN_ICON.react
          transform={isExpanded ? 'rotate(0deg)' : 'rotate(270deg)'}
          opacity={0.5}
          className="folder-arrow"
        />
        <FOLDER_ICON.react className="folder-icon" width={20} height={20} />
        <div className="folder-info">
          <div className="folder-name">
            <span className="folder-name-text">{node.name}</span>
            <span className="folder-file-count">{fileCount} files</span>
          </div>
        </div>
      </div>

      {isExpanded && (
        <div className="folder-children">
          {node.children.map((child, index) => (
            <FolderItem
              key={
                child.type === 'file' ? child.file.id : `${child.name}-${index}`
              }
              node={child}
              onOpenInBrowser={onOpenInBrowser}
              onAddToContext={onAddToContext}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const FileItem: React.FC<IFileItemProps> = ({
  file,
  onOpenInBrowser,
  onAddToContext,
  depth = 0
}) => {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [showPreview, setShowPreview] = React.useState(false);
  const [showTooltip, setShowTooltip] = React.useState(false);
  const [tooltipPosition, setTooltipPosition] = React.useState<{
    top: number;
    left: number;
  } | null>(null);
  const tooltipElementRef = React.useRef<HTMLDivElement | null>(null);
  const fileNameRef = React.useRef<HTMLSpanElement>(null);
  const hideTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  const showTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  // Import DataLoaderService dynamically to avoid circular dependencies
  const formattedContent = React.useMemo(() => {
    try {
      return DataLoaderService.getFormattedFileContent(file);
    } catch (error) {
      console.warn('Could not load DataLoaderService:', error);
      return '';
    }
  }, [file]);

  // Cleanup timeouts
  React.useEffect(() => {
    return () => {
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
      }
      if (showTimeoutRef.current) {
        clearTimeout(showTimeoutRef.current);
      }
    };
  }, []);

  const handleMouseEnter = () => {
    // Clear any pending hide timeout
    if (hideTimeoutRef.current) {
      clearTimeout(hideTimeoutRef.current);
      hideTimeoutRef.current = null;
    }
    // Add delay before showing tooltip
    showTimeoutRef.current = setTimeout(() => {
      setShowTooltip(true);
      showTimeoutRef.current = null;
    }, 500); // 500ms delay
  };

  const handleMouseLeave = () => {
    // Clear any pending show timeout
    if (showTimeoutRef.current) {
      clearTimeout(showTimeoutRef.current);
      showTimeoutRef.current = null;
    }
    // Hide tooltip after delay
    hideTimeoutRef.current = setTimeout(() => {
      if (
        !fileNameRef.current?.matches(':hover') &&
        !tooltipElementRef.current?.matches(':hover')
      ) {
        setShowTooltip(false);
      }
      hideTimeoutRef.current = null;
    }, 200);
  };

  // Build tooltip content
  const tooltipContent = React.useMemo(() => {
    const parts: string[] = [];
    if (file.absolute_path || file.path) {
      parts.push(`Path: ${file.absolute_path || file.path}`);
    }
    if (file.file_info?.size_bytes !== undefined) {
      parts.push(`Size: ${formatFileSize(file.file_info.size_bytes)}`);
    }
    if (file.file_info?.last_modified) {
      parts.push(`Modified: ${formatDate(file.file_info.last_modified)}`);
    }
    return parts;
  }, [file]);

  // Calculate tooltip position and manage tooltip DOM element
  React.useEffect(() => {
    if (showTooltip && fileNameRef.current && tooltipContent.length > 0) {
      const rect = fileNameRef.current.getBoundingClientRect();
      const position = {
        top: rect.top - 4,
        left: rect.left
      };
      setTooltipPosition(position);

      // Create and append tooltip element to document.body
      const tooltipElement = document.createElement('div');
      tooltipElement.className = 'file-name-tooltip';
      tooltipElement.style.position = 'fixed';
      tooltipElement.style.top = `${position.top}px`;
      tooltipElement.style.left = `${position.left}px`;
      tooltipElement.style.transform = 'translateY(-100%)';
      tooltipElement.style.zIndex = '10000';

      // Add content
      tooltipContent.forEach(line => {
        const lineDiv = document.createElement('div');
        lineDiv.textContent = line;
        tooltipElement.appendChild(lineDiv);
      });

      // Add event handlers
      const handleMouseEnter = () => {
        if (hideTimeoutRef.current) {
          clearTimeout(hideTimeoutRef.current);
          hideTimeoutRef.current = null;
        }
      };

      const handleMouseLeave = () => {
        hideTimeoutRef.current = setTimeout(() => {
          if (
            !fileNameRef.current?.matches(':hover') &&
            !tooltipElement.matches(':hover')
          ) {
            setShowTooltip(false);
          }
          hideTimeoutRef.current = null;
        }, 200);
      };

      tooltipElement.addEventListener('mouseenter', handleMouseEnter);
      tooltipElement.addEventListener('mouseleave', handleMouseLeave);

      document.body.appendChild(tooltipElement);
      tooltipElementRef.current = tooltipElement;

      // Cleanup function
      return () => {
        tooltipElement.removeEventListener('mouseenter', handleMouseEnter);
        tooltipElement.removeEventListener('mouseleave', handleMouseLeave);
        if (tooltipElement.parentNode) {
          tooltipElement.parentNode.removeChild(tooltipElement);
        }
        tooltipElementRef.current = null;
      };
    } else {
      setTooltipPosition(null);
      // Cleanup tooltip if it exists
      if (tooltipElementRef.current && tooltipElementRef.current.parentNode) {
        tooltipElementRef.current.parentNode.removeChild(
          tooltipElementRef.current
        );
        tooltipElementRef.current = null;
      }
    }
  }, [showTooltip, tooltipContent]);

  return (
    <div
      className="file-item"
      style={{ paddingLeft: depth === 0 ? 0 : `${depth * 16}px` }}
    >
      <div className="file-header" onClick={() => setIsExpanded(!isExpanded)}>
        <ARROW_DOWN_ICON.react
          transform={isExpanded ? 'rotate(0deg)' : 'rotate(270deg)'}
          opacity={0.5}
          visibility={file.schema?.success ? 'visible' : 'hidden'}
        />
        <FILE_ICON.react width={20} height={20} />
        <div className="file-info">
          <div className="file-name">
            <span
              ref={fileNameRef}
              className="file-name-text"
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
            >
              {file.name}
            </span>
            <div className="file-actions">
              <button
                className="file-add-to-context-button"
                onClick={e => {
                  e.stopPropagation();
                  onAddToContext(file);
                }}
              >
                <span className="add-icon">+</span>
                <span className="add-text">Add to context</span>
              </button>
              {file.schema &&
                file.schema.success &&
                file.schema.totalColumns > 0 && (
                  <span className="column-count">
                    {file.schema.totalColumns}{' '}
                    {file.schema.fileType === 'json' ? 'keys' : 'cols'}
                  </span>
                )}
              {(!file.schema || file.schema.loading === true) && (
                <div className="loading-spinner"></div>
              )}
              <FileActionsMenu file={file} onOpenInBrowser={onOpenInBrowser} />
            </div>
          </div>
          {file.schema && file.schema.error && (
            <span title={file.schema.error} className="file-error-message">
              {file.schema.error}
            </span>
          )}
        </div>
      </div>

      {isExpanded && (
        <button
          className="toggle-preview-button"
          onClick={e => {
            e.stopPropagation();
            setShowPreview(!showPreview);
          }}
        >
          <span style={{ marginLeft: 6 }}>
            {showPreview ? '- Hide' : '+ View'} Agent Context
          </span>
        </button>
      )}

      {showPreview && isExpanded && (
        <pre className="file-content-preview">
          <code>{formattedContent}</code>
        </pre>
      )}

      {isExpanded &&
        file.schema &&
        file.schema.success &&
        file.schema.columns && (
          <div className="file-columns">
            {file.schema.columns.map((column: any) => (
              <div key={column.name} className="column-item">
                <span className="column-name">{column.name}</span>
                <span className="column-type">
                  {column.dataType.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        )}
    </div>
  );
};

interface IFileActionsMenuProps {
  file: ISupportedFileEntry;
  onOpenInBrowser: (file: ISupportedFileEntry) => void;
}

const FileActionsMenu: React.FC<IFileActionsMenuProps> = ({
  file,
  onOpenInBrowser
}) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleAction = (action: () => void) => {
    action();
    setIsOpen(false);
  };

  const isFileInWorkDirectory = file.absolute_path?.startsWith(
    AppStateService.getState().currentWorkingDirectory || ''
  );

  return (
    <div
      className="file-actions-menu"
      ref={menuRef}
      style={{ display: isFileInWorkDirectory ? undefined : 'none' }}
    >
      <button
        className="three-dot-button"
        onClick={e => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        title="More actions"
      >
        ⋯
      </button>
      {isOpen && (
        <div className="actions-dialog">
          <button
            className="action-menu-item"
            onClick={e => {
              e.stopPropagation();
              handleAction(() => onOpenInBrowser(file));
            }}
          >
            Go to file
          </button>
        </div>
      )}
    </div>
  );
};
