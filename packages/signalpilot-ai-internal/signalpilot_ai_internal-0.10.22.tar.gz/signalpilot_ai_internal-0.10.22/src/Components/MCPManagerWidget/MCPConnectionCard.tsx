import * as React from 'react';
import { IMCPServer, IMCPTool } from './types';
import { EDIT_ICON, DELETE_ICON, ARROW_RIGHT_ICON } from './icons';

interface IMCPConnectionCardProps {
  server: IMCPServer;
  tools: IMCPTool[];
  onConnect: (serverId: string) => Promise<void>;
  onDisconnect: (serverId: string) => Promise<void>;
  onDelete: (serverId: string) => Promise<void>;
  onEnable: (serverId: string) => Promise<void>;
  onDisable: (serverId: string) => Promise<void>;
  onEdit: (serverId: string) => void;
  onToolToggle?: (
    serverId: string,
    toolName: string,
    enabled: boolean
  ) => Promise<void>;
}

export const MCPConnectionCard: React.FC<IMCPConnectionCardProps> = ({
  server,
  tools,
  onConnect,
  onDisconnect,
  onDelete,
  onEnable,
  onDisable,
  onEdit,
  onToolToggle
}) => {
  const [isConnecting, setIsConnecting] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [toolsExpanded, setToolsExpanded] = React.useState(false);
  const [errorExpanded, setErrorExpanded] = React.useState(false);

  const handleConnect = async () => {
    setIsConnecting(true);
    try {
      await onConnect(server.id);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    setIsConnecting(true);
    try {
      await onDisconnect(server.id);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleToggleEnabled = async (enabled: boolean) => {
    setIsConnecting(true);
    try {
      if (enabled) {
        await onEnable(server.id);
        // Auto-connect when enabled
        if (server.status !== 'connected' && server.status !== 'connecting') {
          await handleConnect();
        }
      } else {
        // Disconnect if disabling
        if (server.status === 'connected') {
          await onDisconnect(server.id);
        }
        await onDisable(server.id);
      }
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      // Disconnect first if connected
      if (server.status === 'connected') {
        await onDisconnect(server.id);
      }
      // Then delete
      await onDelete(server.id);
    } finally {
      setIsDeleting(false);
    }
  };

  const getStatusDot = () => {
    const status = server.status;
    const isEnabled = server.enabled !== false;

    if (!isEnabled) {
      return (
        <span
          className="mcp-status-dot mcp-status-dot-disabled"
          title="Disabled"
        ></span>
      );
    }

    switch (status) {
      case 'connected':
        return (
          <span
            className="mcp-status-dot mcp-status-dot-connected"
            title="Connected"
          ></span>
        );
      case 'connecting':
        return (
          <span
            className="mcp-status-dot mcp-status-dot-connecting"
            title="Connecting..."
          ></span>
        );
      case 'error':
        return (
          <span
            className="mcp-status-dot mcp-status-dot-error"
            title="Error"
          ></span>
        );
      default:
        return (
          <span
            className="mcp-status-dot mcp-status-dot-disconnected"
            title="Disconnected"
          ></span>
        );
    }
  };

  const serverName = server.name || server.id;
  const isEnabled = server.enabled !== false;
  const enabledTools = server.enabledTools;

  // Debug logging to track state changes
  React.useEffect(() => {
    console.log(
      `[MCPConnectionCard] Server ${server.id} enabledTools:`,
      enabledTools
    );
  }, [server.id, enabledTools]);
  // Count only enabled tools
  // If enabledTools is undefined/null, count all tools (backward compatibility)
  // If enabledTools is an array (even if empty), count only enabled ones
  const enabledToolCount =
    enabledTools === undefined || enabledTools === null
      ? tools.length
      : tools.filter(tool => enabledTools.includes(tool.name)).length;
  const toolCount = enabledToolCount || server.toolCount || 0;
  const hasError =
    server.status === 'error' && (server.error || server.errorOutput);

  const isToolEnabled = (toolName: string): boolean => {
    // If enabledTools is undefined/null, all tools are enabled (backward compatibility)
    if (enabledTools === undefined || enabledTools === null) {
      return true;
    }
    // If enabledTools is an array, check if tool is in it
    return enabledTools.includes(toolName);
  };

  const handleToolClick = async (toolName: string) => {
    if (!onToolToggle) return;

    const toolIsEnabled = isToolEnabled(toolName);
    await onToolToggle(server.id, toolName, !toolIsEnabled);
  };

  return (
    <div className="mcp-connection-card">
      <div className="mcp-card-single-line">
        <div className="mcp-card-left">
          {getStatusDot()}
          <span className="mcp-server-name">{serverName}</span>
        </div>
        <div className="mcp-card-right">
          <div className="mcp-card-actions-hover">
            <button
              className="mcp-button-icon-clean"
              onClick={() => onEdit(server.id)}
              title="Edit server configuration"
            >
              <EDIT_ICON.react tag="span" className="mcp-icon" />
            </button>
            <button
              className="mcp-button-icon-clean"
              onClick={handleDelete}
              disabled={isDeleting || isConnecting}
              title="Delete server"
            >
              <DELETE_ICON.react tag="span" className="mcp-icon" />
            </button>
          </div>
          <label className="mcp-toggle-container">
            <input
              type="checkbox"
              className="mcp-toggle"
              checked={isEnabled}
              onChange={e => handleToggleEnabled(e.target.checked)}
              disabled={isConnecting}
            />
          </label>
        </div>
      </div>

      {server.status === 'connected' && toolCount > 0 && (
        <button
          className="mcp-expand-button-inline"
          onClick={() => setToolsExpanded(!toolsExpanded)}
          aria-label={toolsExpanded ? 'Collapse tools' : 'Expand tools'}
        >
          <span className="mcp-tools-count">{toolCount} tools enabled</span>
          <ARROW_RIGHT_ICON.react
            tag="span"
            className={`mcp-expand-icon-inline ${toolsExpanded ? 'expanded' : ''}`}
          />
        </button>
      )}

      {server.status === 'connected' && toolCount > 0 && toolsExpanded && (
        <div className="mcp-tools-chips">
          {tools.map(tool => {
            const toolIsEnabled = isToolEnabled(tool.name);
            return (
              <span
                key={`${server.id}-${tool.name}`}
                className={`mcp-tool-chip ${!toolIsEnabled ? 'mcp-tool-chip-disabled' : ''}`}
                onClick={() => handleToolClick(tool.name)}
                title={toolIsEnabled ? 'Click to disable' : 'Click to enable'}
              >
                {tool.name}
              </span>
            );
          })}
        </div>
      )}

      {hasError && (
        <>
          <button
            className="mcp-expand-button-inline"
            onClick={() => setErrorExpanded(!errorExpanded)}
            aria-label={errorExpanded ? 'Collapse error' : 'Expand error'}
          >
            <span className="mcp-tools-count">Error - Show Output</span>
            <ARROW_RIGHT_ICON.react
              tag="span"
              className={`mcp-expand-icon-inline ${errorExpanded ? 'expanded' : ''}`}
            />
          </button>
          {errorExpanded && (
            <div className="mcp-error-output">
              <pre>{server.errorOutput || server.error || 'Unknown error'}</pre>
            </div>
          )}
        </>
      )}
    </div>
  );
};
