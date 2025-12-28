import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';
import {
  IMCPServer,
  IMCPServerConfig,
  IMCPServerInfo,
  IMCPTool
} from '../Components/MCPManagerWidget/types';

/**
 * Service for managing MCP client connections and tool calls
 * Handles communication between frontend and backend MCP proxy
 */
export class MCPClientService {
  private static instance: MCPClientService;
  private settings: ServerConnection.ISettings;
  private connectedServers: Map<string, IMCPServerInfo> = new Map();
  private allToolsCache: IMCPTool[] = [];
  private lastToolsUpdate: number = 0;
  private readonly CACHE_DURATION = 5000; // 5 seconds

  private constructor() {
    this.settings = ServerConnection.makeSettings();
  }

  static getInstance(): MCPClientService {
    if (!MCPClientService.instance) {
      MCPClientService.instance = new MCPClientService();
    }
    return MCPClientService.instance;
  }

  /**
   * Get all configured MCP servers
   */
  async getServers(): Promise<IMCPServer[]> {
    try {
      const url = URLExt.join(
        this.settings.baseUrl,
        'signalpilot-ai-internal/mcp/servers'
      );
      const response = await ServerConnection.makeRequest(
        url,
        {},
        this.settings
      );
      const data = await response.json();
      return data.servers || [];
    } catch (error) {
      console.error('Error fetching MCP servers:', error);
      return [];
    }
  }

  /**
   * Save MCP server configuration
   */
  async saveServer(config: IMCPServerConfig): Promise<void> {
    const url = URLExt.join(
      this.settings.baseUrl,
      'signalpilot-ai-internal/mcp/servers'
    );
    const response = await ServerConnection.makeRequest(
      url,
      {
        method: 'POST',
        body: JSON.stringify(config)
      },
      this.settings
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to save server configuration');
    }
  }

  /**
   * Update MCP server configuration
   */
  async updateServer(
    serverId: string,
    config: Partial<IMCPServerConfig>
  ): Promise<void> {
    const url = URLExt.join(
      this.settings.baseUrl,
      `signalpilot-ai-internal/mcp/servers/${serverId}`
    );
    const response = await ServerConnection.makeRequest(
      url,
      {
        method: 'PUT',
        body: JSON.stringify(config)
      },
      this.settings
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update server configuration');
    }
  }

  /**
   * Enable an MCP server
   */
  async enableServer(serverId: string): Promise<void> {
    const url = URLExt.join(
      this.settings.baseUrl,
      `signalpilot-ai-internal/mcp/servers/${serverId}/enable`
    );
    const response = await ServerConnection.makeRequest(
      url,
      {
        method: 'POST'
      },
      this.settings
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to enable server');
    }
  }

  /**
   * Disable an MCP server
   */
  async disableServer(serverId: string): Promise<void> {
    const url = URLExt.join(
      this.settings.baseUrl,
      `signalpilot-ai-internal/mcp/servers/${serverId}/disable`
    );
    const response = await ServerConnection.makeRequest(
      url,
      {
        method: 'POST'
      },
      this.settings
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to disable server');
    }
  }

  /**
   * Get the raw JSON config file content
   */
  async getConfigFile(): Promise<string> {
    const url = URLExt.join(
      this.settings.baseUrl,
      'signalpilot-ai-internal/mcp/config-file'
    );
    const response = await ServerConnection.makeRequest(url, {}, this.settings);

    if (!response.ok) {
      // Try to parse as JSON, but handle HTML error pages
      let errorMessage = 'Failed to get config file';
      try {
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
          const error = await response.json();
          errorMessage = error.error || errorMessage;
        } else {
          // If it's HTML (like a 404 page), just use status text
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
      } catch (e) {
        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return await response.text();
    } else {
      // If we get HTML instead of JSON, something is wrong
      const text = await response.text();
      if (
        text.trim().startsWith('<!DOCTYPE') ||
        text.trim().startsWith('<html')
      ) {
        throw new Error(
          'Received HTML instead of JSON. The endpoint may not be configured correctly.'
        );
      }
      return text;
    }
  }

  /**
   * Update the entire config file
   */
  async updateConfigFile(jsonContent: string): Promise<any> {
    const url = URLExt.join(
      this.settings.baseUrl,
      'signalpilot-ai-internal/mcp/config-file'
    );
    const response = await ServerConnection.makeRequest(
      url,
      {
        method: 'PUT',
        body: jsonContent
      },
      this.settings
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update config file');
    }

    return await response.json();
  }

  /**
   * Connect to all enabled servers
   */
  async connectAllEnabled(): Promise<void> {
    // This will be handled by the backend on startup
    // For now, we'll just trigger a refresh
    const servers = await this.getServers();
    const enabledServers = servers.filter(s => s.enabled !== false);

    // Connect to each enabled server
    for (const server of enabledServers) {
      if (server.status !== 'connected') {
        try {
          await this.connect(server.id);
        } catch (error) {
          console.error(`Failed to auto-connect server ${server.id}:`, error);
        }
      }
    }
  }

  /**
   * Delete MCP server configuration
   */
  async deleteServer(serverId: string): Promise<void> {
    const url = URLExt.join(
      this.settings.baseUrl,
      `signalpilot-ai-internal/mcp/servers/${serverId}`
    );
    const response = await ServerConnection.makeRequest(
      url,
      {
        method: 'DELETE'
      },
      this.settings
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to delete server');
    }

    // Remove from connected servers
    this.connectedServers.delete(serverId);
    this.invalidateToolsCache();
  }

  /**
   * Connect to MCP server
   */
  async connect(serverId: string): Promise<IMCPServerInfo> {
    console.log(`[MCP Client] Attempting to connect to server: ${serverId}`);

    const url = URLExt.join(
      this.settings.baseUrl,
      'signalpilot-ai-internal/mcp/connect'
    );

    try {
      const response = await ServerConnection.makeRequest(
        url,
        {
          method: 'POST',
          body: JSON.stringify({ server_id: serverId })
        },
        this.settings
      );

      if (!response.ok) {
        let errorData: any;
        try {
          errorData = await response.json();
        } catch (e) {
          console.error('[MCP Client] Failed to parse error response:', e);
          throw new Error(
            `Failed to connect to MCP server (HTTP ${response.status})`
          );
        }

        console.error('[MCP Client] Connection error details:', errorData);

        // Create detailed error message
        const errorMsg = errorData.error || 'Failed to connect to MCP server';
        const errorType = errorData.errorType || 'Unknown';
        const details = errorData.details || '';
        const stackTrace = errorData.stackTrace || '';

        let fullError = `[${errorType}] ${errorMsg}`;
        if (details) {
          fullError += `\n\nDetails: ${details}`;
        }
        if (stackTrace) {
          console.error('[MCP Client] Server stack trace:\n', stackTrace);
        }

        throw new Error(fullError);
      }

      const data = await response.json();
      const serverInfo = data.server as IMCPServerInfo;

      // Cache connection info
      this.connectedServers.set(serverId, serverInfo);
      this.invalidateToolsCache();

      console.log(`[MCP Client] Successfully connected to ${serverId}`);
      return serverInfo;
    } catch (error) {
      console.error(
        `[MCP Client] Error connecting to server ${serverId}:`,
        error
      );
      throw error;
    }
  }

  /**
   * Disconnect from MCP server
   */
  async disconnect(serverId: string): Promise<void> {
    const url = URLExt.join(
      this.settings.baseUrl,
      `signalpilot-ai-internal/mcp/servers/${serverId}/disconnect`
    );
    const response = await ServerConnection.makeRequest(
      url,
      {
        method: 'POST'
      },
      this.settings
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to disconnect from MCP server');
    }

    // Remove from cache
    this.connectedServers.delete(serverId);
    this.invalidateToolsCache();
  }

  /**
   * Get available tools from a specific connected server
   */
  async getTools(serverId: string): Promise<IMCPTool[]> {
    try {
      const url = URLExt.join(
        this.settings.baseUrl,
        `signalpilot-ai-internal/mcp/servers/${serverId}/tools`
      );
      const response = await ServerConnection.makeRequest(
        url,
        {},
        this.settings
      );

      if (!response.ok) {
        throw new Error('Failed to fetch tools');
      }

      const data = await response.json();
      return data.tools || [];
    } catch (error) {
      console.error(`Error fetching tools for server ${serverId}:`, error);
      return [];
    }
  }

  /**
   * Get all tools from all connected servers
   * Uses caching to avoid excessive backend calls
   * Filters tools based on enabledTools from server configs
   */
  async getAllTools(forceRefresh: boolean = false): Promise<IMCPTool[]> {
    const now = Date.now();

    // Return cached tools if still valid
    if (
      !forceRefresh &&
      this.allToolsCache.length > 0 &&
      now - this.lastToolsUpdate < this.CACHE_DURATION
    ) {
      return this.allToolsCache;
    }

    try {
      // Fetch all tools from backend
      const url = URLExt.join(
        this.settings.baseUrl,
        'signalpilot-ai-internal/mcp/tools'
      );
      const response = await ServerConnection.makeRequest(
        url,
        {},
        this.settings
      );

      if (!response.ok) {
        throw new Error('Failed to fetch all tools');
      }

      const data = await response.json();
      const allTools: IMCPTool[] = data.tools || [];

      // Fetch server configs to get enabledTools
      const servers = await this.getServers();
      const serverConfigs = new Map<string, IMCPServer>();
      servers.forEach(server => {
        serverConfigs.set(server.id, server);
      });

      // Filter tools based on enabledTools from server configs
      const filteredTools = allTools.filter(tool => {
        const serverConfig = serverConfigs.get(tool.serverId);
        if (!serverConfig) {
          // If server config not found, include tool (backward compatibility)
          return true;
        }

        const enabledTools = serverConfig.enabledTools;
        // If enabledTools is undefined/null, include all tools (backward compatibility for old configs)
        if (enabledTools === undefined || enabledTools === null) {
          return true;
        }

        // If enabledTools is an array (even if empty), use it to filter
        return enabledTools.includes(tool.name);
      });

      console.log(
        `[MCP Client] Tool filtering: ${filteredTools.length} of ${allTools.length} tools enabled`
      );
      this.allToolsCache = filteredTools;
      this.lastToolsUpdate = now;

      return this.allToolsCache;
    } catch (error) {
      console.error('Error fetching all MCP tools:', error);
      return [];
    }
  }

  /**
   * Call a tool via backend proxy
   */
  async callTool(serverId: string, toolName: string, args: any): Promise<any> {
    const url = URLExt.join(
      this.settings.baseUrl,
      'signalpilot-ai-internal/mcp/call-tool'
    );
    const response = await ServerConnection.makeRequest(
      url,
      {
        method: 'POST',
        body: JSON.stringify({
          server_id: serverId,
          tool_name: toolName,
          arguments: args
        })
      },
      this.settings
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to call tool');
    }

    const data = await response.json();
    return data.result;
  }

  /**
   * Convert MCP tools to Anthropic tool format
   */
  convertToAnthropicTools(mcpTools: IMCPTool[]): any[] {
    return mcpTools.map(tool => ({
      name: tool.name,
      description: tool.description || `Tool from ${tool.serverName}`,
      input_schema: tool.inputSchema
    }));
  }

  /**
   * Check if a tool name belongs to an MCP server
   */
  isMCPTool(toolName: string): boolean {
    return this.allToolsCache.some(tool => tool.name === toolName);
  }

  /**
   * Get the server ID for a given tool name
   */
  getServerIdForTool(toolName: string): string | null {
    const tool = this.allToolsCache.find(t => t.name === toolName);
    return tool ? tool.serverId : null;
  }

  /**
   * Get connection status for all servers
   */
  getConnectionStatus(): Map<string, 'connected' | 'disconnected'> {
    const status = new Map<string, 'connected' | 'disconnected'>();
    for (const [serverId, _] of this.connectedServers) {
      status.set(serverId, 'connected');
    }
    return status;
  }

  /**
   * Invalidate the tools cache
   */
  private invalidateToolsCache(): void {
    this.allToolsCache = [];
    this.lastToolsUpdate = 0;
  }

  /**
   * Update enabled/disabled state for a specific tool
   */
  async updateToolEnabled(
    serverId: string,
    toolName: string,
    enabled: boolean
  ): Promise<void> {
    const url = URLExt.join(
      this.settings.baseUrl,
      `signalpilot-ai-internal/mcp/servers/${serverId}/tools/${toolName}`
    );
    const response = await ServerConnection.makeRequest(
      url,
      {
        method: 'PUT',
        body: JSON.stringify({ enabled })
      },
      this.settings
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update tool enabled state');
    }

    // Invalidate cache to force refresh
    this.invalidateToolsCache();
  }

  /**
   * Refresh all tools from backend
   */
  async refreshTools(): Promise<IMCPTool[]> {
    return this.getAllTools(true);
  }
}

// Export singleton instance getter
export const getMCPClientService = () => MCPClientService.getInstance();
