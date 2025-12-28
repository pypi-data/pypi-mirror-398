/**
 * Type definitions for MCP Manager Widget
 */

export type MCPConnectionType = 'command' | 'http' | 'sse';
export type MCPServerStatus =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'error';

export interface IMCPServerConfig {
  id: string;
  name?: string; // Optional for command-based (uses id as fallback)
  type?: MCPConnectionType; // Optional, inferred from command vs url
  enabled?: boolean; // Optional, defaults to true
  enabledTools?: string[]; // Optional, list of enabled tool names
  // For command-based
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  // For HTTP/SSE
  url?: string;
  token?: string;
}

export interface IMCPServer extends IMCPServerConfig {
  status: MCPServerStatus;
  error?: string;
  errorOutput?: string; // Detailed error output for display
  toolCount?: number;
  enabled?: boolean; // Optional, defaults to true
  enabledTools?: string[]; // Optional, list of enabled tool names
}

export interface IMCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, any>;
    required?: string[];
  };
  serverId: string;
  serverName: string;
}

export interface IMCPServerInfo {
  serverId: string;
  name: string;
  status: 'connected';
  type: MCPConnectionType;
  toolCount: number;
  tools: IMCPTool[];
  enabledTools?: string[];
}

export interface IMCPServerFormData {
  name: string;
  type: MCPConnectionType;
  command?: string;
  args?: string;
  env?: string;
  url?: string;
  token?: string;
}
