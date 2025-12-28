import { Client } from '@modelcontextprotocol/sdk/client/index';
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';

/**
 * Interface for MCP server configuration
 */
export interface IMCPServerConfig {
  name: string;
  /**
   * Browser-friendly transport URL (recommended for JupyterLab/web).
   * Example: "http://localhost:3000/sse" or "/signalpilot-ai-internal/mcp/sse"
   */
  url?: string;

  /**
   * Node-only stdio launch settings (not supported in browsers).
   * These are kept for compatibility with environments that can spawn processes.
   */
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  enabled?: boolean;
}

/**
 * Interface for a connected MCP server instance
 */
interface IConnectedServer {
  name: string;
  client: Client;
  tools: any[];
  // Transport type varies (SSE vs stdio), keep it generic.
  transport: any;
}

/**
 * Service for managing MCP (Model Context Protocol) client connections
 * Handles multiple MCP server connections and aggregates their tools
 */
export class MCPClientManager {
  private connectedServers: Map<string, IConnectedServer> = new Map();
  private initializationPromises: Map<string, Promise<void>> = new Map();

  private isNodeLike(): boolean {
    // In JupyterLab (browser) this will be false.
    return (
      typeof process !== 'undefined' &&
      !!(process as any).versions &&
      !!(process as any).versions.node
    );
  }

  private resolveServerUrl(rawUrl: string): URL {
    // Support absolute and relative URLs
    if (typeof window !== 'undefined' && window.location) {
      return new URL(rawUrl, window.location.href);
    }
    return new URL(rawUrl);
  }

  /**
   * Initialize all configured MCP servers
   * @param configs Array of server configurations to initialize
   */
  async initializeServers(configs: IMCPServerConfig[]): Promise<void> {
    console.log('[MCPClientManager] Initializing MCP servers:', configs);

    const enabledConfigs = configs.filter(config => config.enabled !== false);

    if (enabledConfigs.length === 0) {
      console.log('[MCPClientManager] No enabled MCP servers to initialize');
      return;
    }

    const initPromises = enabledConfigs.map(config =>
      this.connectToServer(config)
    );

    const results = await Promise.allSettled(initPromises);

    results.forEach((result, index) => {
      if (result.status === 'rejected') {
        console.error(
          `[MCPClientManager] Failed to initialize server ${enabledConfigs[index].name}:`,
          result.reason
        );
      }
    });

    console.log(
      `[MCPClientManager] Initialized ${this.connectedServers.size} out of ${enabledConfigs.length} servers`
    );
  }

  /**
   * Connect to a single MCP server
   * @param config Server configuration
   */
  async connectToServer(config: IMCPServerConfig): Promise<void> {
    if (this.connectedServers.has(config.name)) {
      console.log(
        `[MCPClientManager] Server ${config.name} already connected, skipping`
      );
      return;
    }

    if (this.initializationPromises.has(config.name)) {
      console.log(
        `[MCPClientManager] Server ${config.name} is already being initialized`
      );
      return this.initializationPromises.get(config.name)!;
    }

    const initPromise = this.doConnectToServer(config);
    this.initializationPromises.set(config.name, initPromise);

    try {
      await initPromise;
    } finally {
      this.initializationPromises.delete(config.name);
    }
  }

  /**
   * Internal method to perform actual server connection
   * @param config Server configuration
   */
  private async doConnectToServer(config: IMCPServerConfig): Promise<void> {
    console.log(`[MCPClientManager] Connecting to MCP server: ${config.name}`);

    const client = new Client(
      {
        name: `sage-ai-mcp-client-${config.name}`,
        version: '1.0.0'
      },
      {
        capabilities: {}
      }
    );

    const transport = await this.createTransport(config);

    await client.connect(transport);

    console.log(
      `[MCPClientManager] Connected to ${config.name}, listing tools`
    );

    const capabilities = (await client.listTools()) as any;

    const tools = capabilities.tools.map((tool: any) => ({
      name: `mcp-${config.name}-${tool.name}`,
      description: tool.description || '',
      input_schema: tool.inputSchema || {},
      _mcpServerName: config.name,
      _mcpToolName: tool.name
    }));

    this.connectedServers.set(config.name, {
      name: config.name,
      client,
      tools,
      transport
    });

    console.log(
      `[MCPClientManager] Successfully connected to ${config.name}, loaded ${tools.length} tools`
    );
  }

  private async createTransport(config: IMCPServerConfig): Promise<any> {
    // Preferred path for browser/JupyterLab: connect to an MCP server over SSE.
    if (config.url) {
      const url = this.resolveServerUrl(config.url);
      return new SSEClientTransport(url);
    }

    // Optional Node path: connect by spawning the server over stdio.
    // IMPORTANT: Browsers cannot spawn processes, so this requires a Node-like runtime.
    if (this.isNodeLike() && config.command) {
      // Avoid bundling/including Node-only transport in the browser build.
      const { StdioClientTransport } = await import(
        /* webpackIgnore: true */ '@modelcontextprotocol/sdk/client/stdio.js'
      );

      return new StdioClientTransport({
        command: config.command,
        args: config.args || [],
        env: config.env || {}
      });
    }

    throw new Error(
      `[MCPClientManager] Server '${config.name}' missing 'url'. ` +
        'Browser environments require an SSE URL (config.url).'
    );
  }

  /**
   * Disconnect from a specific server
   * @param serverName Name of the server to disconnect
   */
  async disconnectServer(serverName: string): Promise<void> {
    const server = this.connectedServers.get(serverName);
    if (!server) {
      console.warn(
        `[MCPClientManager] Server ${serverName} not found, cannot disconnect`
      );
      return;
    }

    try {
      await server.client.close();
      this.connectedServers.delete(serverName);
      console.log(`[MCPClientManager] Disconnected from server: ${serverName}`);
    } catch (error) {
      console.error(
        `[MCPClientManager] Error disconnecting from ${serverName}:`,
        error
      );
      throw error;
    }
  }

  /**
   * Get all tools from all connected servers
   * @returns Array of all available MCP tools
   */
  getAggregatedTools(): any[] {
    const allTools: any[] = [];
    for (const server of this.connectedServers.values()) {
      allTools.push(...server.tools);
    }
    return allTools;
  }

  /**
   * Get tools from a specific server
   * @param serverName Name of the server
   * @returns Array of tools from the specified server
   */
  getToolsForServer(serverName: string): any[] {
    const server = this.connectedServers.get(serverName);
    return server ? server.tools : [];
  }

  /**
   * Execute a tool on a specific MCP server
   * @param serverName Name of the server to execute the tool on
   * @param toolName Name of the tool to execute
   * @param args Arguments to pass to the tool
   * @returns Result from the tool execution
   */
  async executeToolOnServer(
    serverName: string,
    toolName: string,
    args: any
  ): Promise<any> {
    const server = this.connectedServers.get(serverName);
    if (!server) {
      throw new Error(`MCP server not found: ${serverName}`);
    }

    console.log(
      `[MCPClientManager] Executing tool ${toolName} on server ${serverName}`
    );

    const result = await server.client.callTool({
      name: toolName,
      arguments: args
    });

    console.log(
      `[MCPClientManager] Tool ${toolName} execution completed on ${serverName}`
    );

    return result;
  }

  /**
   * Check if a server is connected
   * @param serverName Name of the server to check
   * @returns True if the server is connected
   */
  isServerConnected(serverName: string): boolean {
    return this.connectedServers.has(serverName);
  }

  /**
   * Get list of all connected server names
   * @returns Array of connected server names
   */
  getConnectedServerNames(): string[] {
    return Array.from(this.connectedServers.keys());
  }

  /**
   * Disconnect from all servers
   */
  async disconnectAll(): Promise<void> {
    console.log('[MCPClientManager] Disconnecting all servers');

    const disconnectPromises = Array.from(this.connectedServers.values()).map(
      async server => {
        try {
          await server.client.close();
        } catch (error) {
          console.error(
            `[MCPClientManager] Error closing server ${server.name}:`,
            error
          );
        }
      }
    );

    await Promise.allSettled(disconnectPromises);
    this.connectedServers.clear();

    console.log('[MCPClientManager] All servers disconnected');
  }

  /**
   * Reload a server by disconnecting and reconnecting
   * @param config Server configuration to reload
   */
  async reloadServer(config: IMCPServerConfig): Promise<void> {
    console.log(`[MCPClientManager] Reloading server: ${config.name}`);

    if (this.connectedServers.has(config.name)) {
      await this.disconnectServer(config.name);
    }

    await this.connectToServer(config);
  }
}
