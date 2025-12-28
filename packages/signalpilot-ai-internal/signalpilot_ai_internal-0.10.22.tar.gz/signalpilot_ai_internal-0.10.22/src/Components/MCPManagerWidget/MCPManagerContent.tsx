import * as React from 'react';
import { EditorView } from '@codemirror/view';
import { EditorState } from '@codemirror/state';
import { json } from '@codemirror/lang-json';
import { jupyterTheme } from '@jupyterlab/codemirror';
import { IMCPServer, IMCPTool } from './types';
import { MCPConnectionCard } from './MCPConnectionCard';
import { MCPClientService } from '../../Services/MCPClientService';
import { CLOSE_ICON } from './icons';

// Use require to avoid TypeScript errors with react-dom
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { createRoot } = require('react-dom/client');

interface IMCPManagerContentProps {}

interface IJSONEditorModalProps {
  isOpen: boolean;
  content: string;
  onClose: () => void;
  onSave: (content: string) => Promise<void>;
}

const JSONEditorModal: React.FC<IJSONEditorModalProps> = ({
  isOpen,
  content,
  onClose,
  onSave
}) => {
  const viewRef = React.useRef<EditorView | null>(null);
  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const rootRef = React.useRef<any>(null);
  const [jsonError, setJsonError] = React.useState('');
  const [isSaving, setIsSaving] = React.useState(false);
  const [editorElement, setEditorElement] =
    React.useState<HTMLDivElement | null>(null);

  const formatJSON = React.useCallback(() => {
    if (!viewRef.current) {
      return;
    }

    try {
      const currentContent = viewRef.current.state.doc.toString();
      const parsed = JSON.parse(currentContent);
      const formatted = JSON.stringify(parsed, null, 2);

      viewRef.current.dispatch({
        changes: {
          from: 0,
          to: viewRef.current.state.doc.length,
          insert: formatted
        }
      });
      setJsonError('');
    } catch (e) {
      setJsonError('Cannot format: Invalid JSON');
    }
  }, []);

  const handleSave = React.useCallback(async () => {
    if (!viewRef.current) {
      return;
    }

    try {
      setJsonError('');

      let jsonContent = viewRef.current.state.doc.toString();

      // Validate and format JSON
      try {
        const parsed = JSON.parse(jsonContent);
        // Format the JSON
        const formatted = JSON.stringify(parsed, null, 2);

        // Update the editor with formatted content
        viewRef.current.dispatch({
          changes: {
            from: 0,
            to: viewRef.current.state.doc.length,
            insert: formatted
          }
        });

        jsonContent = formatted;
      } catch (e) {
        setJsonError('Invalid JSON format');
        return;
      }

      setIsSaving(true);
      await onSave(jsonContent);
      onClose();
    } catch (error) {
      setJsonError(error instanceof Error ? error.message : 'Failed to save');
    } finally {
      setIsSaving(false);
    }
  }, [onClose, onSave]);

  const handleKeyDown = React.useCallback(
    (e: React.KeyboardEvent) => {
      // Format on Cmd/Ctrl + Shift + F
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'F') {
        e.preventDefault();
        formatJSON();
      }
      // Close on Escape
      if (e.key === 'Escape') {
        onClose();
      }
    },
    [formatJSON, onClose]
  );

  // Create container in document.body and render modal there
  React.useEffect(() => {
    if (!isOpen) {
      // Clean up container when modal closes
      if (rootRef.current) {
        rootRef.current.unmount();
        rootRef.current = null;
      }
      if (containerRef.current) {
        if (containerRef.current.parentNode) {
          containerRef.current.parentNode.removeChild(containerRef.current);
        }
        containerRef.current = null;
      }
      return;
    }

    // Create container in document.body
    if (!containerRef.current) {
      containerRef.current = document.createElement('div');
      containerRef.current.id = 'mcp-json-editor-modal-container';
      document.body.appendChild(containerRef.current);
    }

    // Create root if it doesn't exist
    if (!rootRef.current) {
      rootRef.current = createRoot(containerRef.current);
    }

    // Render modal to the container
    const modalElement = (
      <div
        className="mcp-modal-overlay mcp-modal-overlay-fullscreen"
        onClick={onClose}
        onKeyDown={handleKeyDown}
        tabIndex={-1}
      >
        <div
          className="mcp-modal-content mcp-modal-content-fullscreen"
          onClick={e => e.stopPropagation()}
        >
          <div className="mcp-modal-header">
            <h3>Edit MCP Configuration</h3>
            <button className="mcp-modal-close" onClick={onClose}>
              <CLOSE_ICON.react tag="span" className="mcp-icon" />
            </button>
          </div>
          <div className="mcp-modal-body">
            <div
              ref={el => {
                if (el) {
                  setEditorElement(el);
                } else {
                  setEditorElement(null);
                }
              }}
              className="mcp-codemirror-container"
            />
            {jsonError && <div className="mcp-error-message">{jsonError}</div>}
            <div className="mcp-config-examples">
              <details>
                <summary>Configuration Examples</summary>
                <div className="mcp-examples-content">
                  <h4>Command-based (stdio):</h4>
                  <pre>
                    {JSON.stringify(
                      {
                        filesystem: {
                          command: 'npx',
                          args: [
                            '-y',
                            '@modelcontextprotocol/server-filesystem',
                            '/Users/me/Documents'
                          ]
                        }
                      },
                      null,
                      2
                    )}
                  </pre>
                  <h4>HTTP/SSE:</h4>
                  <pre>
                    {JSON.stringify(
                      {
                        'my-http-server': {
                          name: 'my-http-server',
                          url: 'http://localhost:8080/sse',
                          enabled: true
                        }
                      },
                      null,
                      2
                    )}
                  </pre>
                  <h4>Command with environment variables:</h4>
                  <pre>
                    {JSON.stringify(
                      {
                        'dbt-server': {
                          command: 'uvx',
                          args: ['dbt-mcp'],
                          env: {
                            DBT_TOKEN: 'your-token-here',
                            DBT_PROJECT_DIR: '/path/to/project'
                          }
                        }
                      },
                      null,
                      2
                    )}
                  </pre>
                </div>
              </details>
            </div>
          </div>
          <div className="mcp-modal-footer">
            <button
              className="mcp-button mcp-button-secondary"
              onClick={onClose}
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              className="mcp-button mcp-button-secondary"
              onClick={formatJSON}
              disabled={isSaving}
              title="Format JSON (Cmd/Ctrl+Shift+F)"
            >
              Format
            </button>
            <button
              className="mcp-button mcp-button-primary"
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    );

    rootRef.current.render(modalElement);

    return () => {
      if (rootRef.current) {
        rootRef.current.unmount();
        rootRef.current = null;
      }
      if (containerRef.current) {
        if (containerRef.current.parentNode) {
          containerRef.current.parentNode.removeChild(containerRef.current);
        }
        containerRef.current = null;
      }
    };
  }, [
    isOpen,
    jsonError,
    isSaving,
    content,
    onClose,
    onSave,
    formatJSON,
    handleSave,
    handleKeyDown
  ]);

  // Initialize CodeMirror editor - wait for modal to be rendered
  React.useEffect(() => {
    if (!isOpen || !editorElement) {
      // Clean up when modal closes
      if (viewRef.current) {
        viewRef.current.destroy();
        viewRef.current = null;
      }
      return;
    }

    // Don't reinitialize if editor already exists
    if (viewRef.current) {
      return;
    }

    // Small delay to ensure the DOM is ready
    const timeoutId = setTimeout(() => {
      if (!editorElement || viewRef.current) {
        return;
      }

      // Double-check the element exists in the DOM
      if (!document.body.contains(editorElement)) {
        return;
      }

      const updateListener = EditorView.updateListener.of(update => {
        if (update.docChanged) {
          setJsonError('');
        }
      });

      const startState = EditorState.create({
        doc: content,
        extensions: [
          json(),
          jupyterTheme,
          updateListener,
          EditorView.theme({
            '&': {
              height: '100%',
              fontSize: '13px'
            },
            '.cm-content': {
              padding: '12px',
              minHeight: '400px',
              fontFamily: 'var(--jp-code-font-family)'
            },
            '.cm-focused': {
              outline: 'none'
            },
            '.cm-editor': {
              height: '100%'
            },
            '.cm-scroller': {
              overflow: 'auto'
            }
          }),
          EditorView.lineWrapping
        ]
      });

      viewRef.current = new EditorView({
        state: startState,
        parent: editorElement
      });
    }, 50);

    return () => {
      clearTimeout(timeoutId);
      if (viewRef.current) {
        viewRef.current.destroy();
        viewRef.current = null;
      }
    };
  }, [isOpen, content, editorElement]);

  // Update editor content when content prop changes (only on initial open)
  React.useEffect(() => {
    if (viewRef.current && isOpen) {
      const currentContent = viewRef.current.state.doc.toString();
      if (currentContent !== content) {
        viewRef.current.dispatch({
          changes: {
            from: 0,
            to: viewRef.current.state.doc.length,
            insert: content
          }
        });
      }
    }
  }, [content, isOpen]);

  // Return null - modal is rendered to document.body via ReactDOM
  return null;
};

const AddNewServerCard: React.FC<{ onClick: () => void }> = ({ onClick }) => {
  return (
    <div className="mcp-add-server-card" onClick={onClick}>
      <div className="mcp-add-server-content">
        <span className="mcp-add-server-icon">+</span>
        <span className="mcp-add-server-text">Add new MCP Server</span>
      </div>
    </div>
  );
};

export const MCPManagerContent: React.FC<IMCPManagerContentProps> = () => {
  const [mcpServers, setMcpServers] = React.useState<IMCPServer[]>([]);
  const [serverTools, setServerTools] = React.useState<
    Record<string, IMCPTool[]>
  >({});
  const [loading, setLoading] = React.useState(true);
  const [jsonEditorOpen, setJsonEditorOpen] = React.useState(false);
  const [configFileContent, setConfigFileContent] = React.useState('');

  const mcpClient = MCPClientService.getInstance();

  // Load servers on mount and auto-connect enabled ones
  React.useEffect(() => {
    const initialize = async () => {
      await loadServers();
      // Also call backend connectAllEnabled for any servers that might have been missed
      try {
        await mcpClient.connectAllEnabled();
      } catch (error) {
        console.error('Error in connectAllEnabled:', error);
      }
    };
    void initialize();
  }, []);

  const loadServers = async () => {
    try {
      setLoading(true);
      const servers = await mcpClient.getServers();
      // Show servers immediately with their current states
      setMcpServers(servers);
      setLoading(false);

      // Load tools for connected servers (non-blocking)
      for (const server of servers) {
        if (server.status === 'connected') {
          mcpClient
            .getTools(server.id)
            .then(tools => {
              setServerTools(prev => ({ ...prev, [server.id]: tools }));
            })
            .catch(error => {
              console.error(
                `Error loading tools for server ${server.id}:`,
                error
              );
            });
        }
      }

      // Auto-connect enabled servers that aren't connected (non-blocking)
      const enabledServers = servers.filter(
        s =>
          s.enabled !== false &&
          s.status !== 'connected' &&
          s.status !== 'connecting'
      );
      for (const server of enabledServers) {
        // Connect in background without blocking
        handleConnect(server.id).catch(error => {
          console.error(`Failed to auto-connect ${server.id}:`, error);
        });
      }
    } catch (error) {
      console.error('Error loading MCP servers:', error);
      setLoading(false);
    }
  };

  const handleConnect = async (serverId: string) => {
    try {
      console.log(`[MCP Manager] Connecting to server: ${serverId}`);

      // Update status to connecting
      setMcpServers(servers =>
        servers.map(s =>
          s.id === serverId ? { ...s, status: 'connecting' as const } : s
        )
      );

      const serverInfo = await mcpClient.connect(serverId);

      console.log(
        '[MCP Manager] Connected successfully, tools:',
        serverInfo.toolCount
      );

      // Update server status and tools
      setMcpServers(servers =>
        servers.map(s =>
          s.id === serverId
            ? {
                ...s,
                status: 'connected' as const,
                toolCount: serverInfo.toolCount,
                enabledTools: serverInfo.enabledTools || s.enabledTools || [],
                error: undefined,
                errorOutput: undefined
              }
            : s
        )
      );

      setServerTools(tools => ({
        ...tools,
        [serverId]: serverInfo.tools || []
      }));
    } catch (error) {
      console.error('[MCP Manager] Error connecting to MCP server:', error);

      // Extract detailed error message
      const errorMessage =
        error instanceof Error ? error.message : 'Connection failed';

      console.error('[MCP Manager] Full error details:', {
        message: errorMessage,
        error: error
      });

      setMcpServers(servers =>
        servers.map(s =>
          s.id === serverId
            ? {
                ...s,
                status: 'error' as const,
                error: errorMessage,
                errorOutput: errorMessage
              }
            : s
        )
      );
    }
  };

  const handleDisconnect = async (serverId: string) => {
    try {
      await mcpClient.disconnect(serverId);

      // Update server status
      setMcpServers(servers =>
        servers.map(s =>
          s.id === serverId ? { ...s, status: 'disconnected' as const } : s
        )
      );

      // Clear tools
      setServerTools(tools => {
        const newTools = { ...tools };
        delete newTools[serverId];
        return newTools;
      });
    } catch (error) {
      console.error('Error disconnecting from MCP server:', error);
    }
  };

  const handleDelete = async (serverId: string) => {
    if (
      !confirm('Are you sure you want to delete this MCP server configuration?')
    ) {
      return;
    }

    try {
      await mcpClient.deleteServer(serverId);

      // Remove from list
      setMcpServers(servers => servers.filter(s => s.id !== serverId));
      setServerTools(tools => {
        const newTools = { ...tools };
        delete newTools[serverId];
        return newTools;
      });
    } catch (error) {
      console.error('Error deleting MCP server:', error);
      alert(error instanceof Error ? error.message : 'Failed to delete server');
    }
  };

  const handleEnable = async (serverId: string) => {
    try {
      await mcpClient.enableServer(serverId);
      setMcpServers(servers =>
        servers.map(s => (s.id === serverId ? { ...s, enabled: true } : s))
      );
      // Auto-connect if enabled
      await handleConnect(serverId);
    } catch (error) {
      console.error('Error enabling server:', error);
    }
  };

  const handleDisable = async (serverId: string) => {
    try {
      await mcpClient.disableServer(serverId);
      setMcpServers(servers =>
        servers.map(s => (s.id === serverId ? { ...s, enabled: false } : s))
      );
      // Disconnect if connected
      if (mcpServers.find(s => s.id === serverId)?.status === 'connected') {
        await handleDisconnect(serverId);
      }
    } catch (error) {
      console.error('Error disabling server:', error);
    }
  };

  const handleToolToggle = async (
    serverId: string,
    toolName: string,
    enabled: boolean
  ) => {
    try {
      console.log(
        `[MCP Manager] Toggling tool ${toolName} to ${enabled ? 'enabled' : 'disabled'} for server ${serverId}`
      );
      await mcpClient.updateToolEnabled(serverId, toolName, enabled);

      // Reload server config to get updated enabledTools from backend
      const updatedServers = await mcpClient.getServers();
      const updatedServer = updatedServers.find(s => s.id === serverId);
      console.log(
        `[MCP Manager] Updated server ${serverId} enabledTools:`,
        updatedServer?.enabledTools
      );

      if (!updatedServer) {
        console.warn(
          `[MCP Manager] Server ${serverId} not found in updated servers`
        );
        return;
      }

      // Update state with the server from backend (preserving other properties)
      setMcpServers(prevServers => {
        const newServers = prevServers.map(prevServer => {
          if (prevServer.id === serverId) {
            const newServer = {
              ...prevServer,
              enabledTools: updatedServer.enabledTools
                ? [...updatedServer.enabledTools]
                : undefined,
              toolCount: updatedServer.toolCount ?? prevServer.toolCount
            };
            console.log(`[MCP Manager] Updating server ${serverId} state:`, {
              old: prevServer.enabledTools,
              new: newServer.enabledTools
            });
            return newServer;
          }
          return prevServer;
        });
        return newServers;
      });

      // Invalidate tools cache to force refresh
      await mcpClient.refreshTools();
    } catch (error) {
      console.error('Error toggling tool:', error);
      alert(error instanceof Error ? error.message : 'Failed to toggle tool');
    }
  };

  const handleEdit = async (serverId: string | null) => {
    try {
      const content = await mcpClient.getConfigFile();
      setConfigFileContent(content);
      setJsonEditorOpen(true);
    } catch (error) {
      console.error('Error loading config file:', error);
      alert('Failed to load configuration file');
    }
  };

  const handleAddNew = () => {
    void handleEdit(null);
  };

  const handleSaveConfig = async (content: string) => {
    try {
      // Get current server IDs before update to detect new servers
      const currentServerIds = new Set(mcpServers.map(s => s.id));

      await mcpClient.updateConfigFile(content);

      // Reload server list immediately (without waiting for connections)
      const servers = await mcpClient.getServers();
      setMcpServers(servers);

      // Detect newly added servers and show connecting state
      const newServers = servers.filter(
        s => !currentServerIds.has(s.id) && s.enabled !== false
      );

      for (const server of newServers) {
        // Show connecting state immediately
        setMcpServers(prev =>
          prev.map(s =>
            s.id === server.id ? { ...s, status: 'connecting' as const } : s
          )
        );

        // Connect in background
        handleConnect(server.id).catch(error => {
          console.error(`Failed to connect new server ${server.id}:`, error);
        });
      }

      // Load tools for already connected servers (non-blocking)
      for (const server of servers) {
        if (server.status === 'connected') {
          mcpClient
            .getTools(server.id)
            .then(tools => {
              setServerTools(prev => ({ ...prev, [server.id]: tools }));
            })
            .catch(error => {
              console.error(
                `Error loading tools for server ${server.id}:`,
                error
              );
            });
        }
      }

      // Trigger background refresh after a delay to pick up connection status
      // This allows the backend's async connection tasks to complete
      setTimeout(async () => {
        try {
          const updatedServers = await mcpClient.getServers();
          setMcpServers(updatedServers);

          // Load tools for newly connected servers (non-blocking)
          for (const server of updatedServers) {
            if (server.status === 'connected') {
              mcpClient
                .getTools(server.id)
                .then(tools => {
                  setServerTools(prev => ({ ...prev, [server.id]: tools }));
                })
                .catch(error => {
                  console.error(
                    `Error loading tools for server ${server.id}:`,
                    error
                  );
                });
            }
          }
        } catch (error) {
          console.error('Error refreshing servers:', error);
        }
      }, 1000);
    } catch (error) {
      console.error('Error saving config file:', error);
      throw error;
    }
  };

  return (
    <div className="mcp-manager-container">
      <div className="mcp-manager-header">
        <h2>MCP Servers</h2>
        <p className="mcp-manager-description">
          Manage Model Context Protocol server connections to extend your
          agent's capabilities.
        </p>
      </div>

      <div className="mcp-server-list">
        <h3>Installed Servers</h3>
        {loading ? (
          <div className="mcp-loading">Loading servers...</div>
        ) : mcpServers.length === 0 ? (
          <div className="mcp-empty-state">
            No MCP servers configured. Click "Add new MCP Server" below to get
            started.
          </div>
        ) : (
          <>
            {mcpServers.map(server => (
              <MCPConnectionCard
                key={server.id}
                server={server}
                tools={serverTools[server.id] || []}
                onConnect={handleConnect}
                onDisconnect={handleDisconnect}
                onDelete={handleDelete}
                onEnable={handleEnable}
                onDisable={handleDisable}
                onEdit={() => handleEdit(server.id)}
                onToolToggle={handleToolToggle}
              />
            ))}
            <AddNewServerCard onClick={handleAddNew} />
          </>
        )}
        {!loading && mcpServers.length === 0 && (
          <AddNewServerCard onClick={handleAddNew} />
        )}
      </div>

      <JSONEditorModal
        isOpen={jsonEditorOpen}
        content={configFileContent}
        onClose={() => setJsonEditorOpen(false)}
        onSave={handleSaveConfig}
      />
    </div>
  );
};
