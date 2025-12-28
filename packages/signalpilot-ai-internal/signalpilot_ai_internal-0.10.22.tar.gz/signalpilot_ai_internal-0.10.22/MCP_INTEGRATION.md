# MCP Integration - Implementation Complete

This document describes the MCP (Model Context Protocol) integration that has been implemented in SignalPilot.

## Overview

The MCP integration allows users to connect to external MCP servers and use their tools directly within the SignalPilot agent. The implementation includes:

- **Backend MCP Service**: Python service managing MCP connections (command-based, HTTP, and SSE)
- **Backend API Handlers**: REST API endpoints for managing MCP servers
- **Frontend MCP Manager Widget**: UI for configuring and managing MCP connections
- **Frontend MCP Client Service**: Service for communicating with the backend
- **Anthropic Integration**: Automatic tool discovery and execution through the LLM agent

## Architecture

```
┌─────────────────────────────────────┐
│         Frontend (TypeScript)        │
├─────────────────────────────────────┤
│ MCPManagerWidget                     │
│   ├─ JSON Configuration Editor      │
│   ├─ Server List with Status        │
│   └─ Tool Explorer                  │
│                                      │
│ MCPClientService                     │
│   ├─ Server Management               │
│   ├─ Tool Discovery                  │
│   └─ Tool Execution Proxy           │
│                                      │
│ AnthropicService Integration         │
│   └─ Automatic MCP Tool Injection   │
└─────────────────────────────────────┘
                  ↕ HTTP API
┌─────────────────────────────────────┐
│    Jupyter Server Extension (Python) │
├─────────────────────────────────────┤
│ MCP Handlers (API Endpoints)        │
│   ├─ GET/POST /mcp/servers          │
│   ├─ POST /mcp/connect               │
│   ├─ GET /mcp/tools                  │
│   └─ POST /mcp/call-tool             │
│                                      │
│ MCPConnectionService                 │
│   ├─ Command-based (stdio)           │
│   ├─ HTTP Connections                │
│   └─ SSE Connections                 │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│        External MCP Servers          │
└─────────────────────────────────────┘
```

## Files Created/Modified

### Backend (Python)
- **Created:**
  - `signalpilot_ai_internal/mcp_service.py` - Core MCP connection management service
  - `signalpilot_ai_internal/mcp_handlers.py` - Tornado API handlers for MCP endpoints

- **Modified:**
  - `signalpilot_ai_internal/handlers.py` - Registered MCP handlers and routes
  - `pyproject.toml` - Added `aiohttp>=3.9.0` dependency

### Frontend (TypeScript)
- **Created:**
  - `src/Components/MCPManagerWidget/MCPManagerWidget.tsx` - Main widget class
  - `src/Components/MCPManagerWidget/MCPManagerContent.tsx` - React UI component
  - `src/Components/MCPManagerWidget/MCPConnectionCard.tsx` - Server card component
  - `src/Components/MCPManagerWidget/types.ts` - TypeScript type definitions
  - `src/Components/MCPManagerWidget/index.ts` - Module exports
  - `src/Services/MCPClientService.ts` - Frontend service for MCP communication
  - `style/mcp-manager.css` - Widget styling

- **Modified:**
  - `src/Services/AnthropicService.ts` - Added MCP tool injection
  - `src/Services/ToolService.ts` - Added MCP tool execution handling
  - `src/SignalPilot/widgetInitialization.ts` - Registered MCP Manager widget
  - `style/index.css` - Imported MCP styles

## Usage

### 1. Access the MCP Manager Widget

The MCP Manager widget is available in the right sidebar of JupyterLab. Click on the "MCP Servers" tab to open it.

### 2. Add an MCP Server

Use the JSON editor to configure an MCP server. Examples:

**Command-based (stdio):**
```json
{
  "name": "filesystem",
  "type": "command",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"]
}
```

**HTTP/SSE:**
```json
{
  "name": "my-http-server",
  "type": "http",
  "url": "http://localhost:8080/sse",
  "token": "optional-auth-token"
}
```

### 3. Connect to Server

After adding a server configuration, click the "Connect" button. The server status will change to "Connected" and available tools will be displayed.

### 4. Use MCP Tools in Chat

Once connected, MCP tools are automatically available to the LLM agent. Simply ask the agent to perform tasks that the MCP tools can handle. For example:

- "List the files in the directory" (if using filesystem MCP)
- "Search for X using tool Y" (if using a custom MCP server)

The agent will automatically discover and use the appropriate MCP tools.

## API Endpoints

The backend exposes the following REST API endpoints:

- `GET /signalpilot-ai-internal/mcp/servers` - Get all configured servers
- `POST /signalpilot-ai-internal/mcp/servers` - Save a server configuration
- `DELETE /signalpilot-ai-internal/mcp/servers/{server_id}` - Delete a server
- `POST /signalpilot-ai-internal/mcp/connect` - Connect to a server
- `POST /signalpilot-ai-internal/mcp/servers/{server_id}/disconnect` - Disconnect from a server
- `GET /signalpilot-ai-internal/mcp/servers/{server_id}/tools` - Get tools from a server
- `GET /signalpilot-ai-internal/mcp/tools` - Get all tools from all connected servers
- `POST /signalpilot-ai-internal/mcp/call-tool` - Execute an MCP tool

## Configuration Storage

MCP server configurations are stored using the existing cache service at:
- Storage key: `mcp_servers`
- Location: User-specific cache directory managed by the cache service

## Testing

### Test Command-based MCP Server

1. Install an MCP server (e.g., filesystem server):
   ```bash
   npm install -g @modelcontextprotocol/server-filesystem
   ```

2. Add the server configuration in the MCP Manager widget:
   ```json
   {
     "name": "test-filesystem",
     "type": "command",
     "command": "npx",
     "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
   }
   ```

3. Click "Connect" and verify the connection status

4. Ask the agent: "What files are in /tmp?"

### Test HTTP/SSE MCP Server

1. Run an HTTP MCP server (if available)

2. Add the server configuration with the appropriate URL

3. Connect and test tool execution through the chat interface

### Verify Tool Integration

1. Connect to an MCP server
2. Open the browser console
3. Check for log messages indicating MCP tools were added:
   ```
   [AnthropicService] Added N MCP tools to request
   ```

4. Send a message to the agent that would use an MCP tool
5. Verify the tool is executed and results are returned

## Troubleshooting

### Connection Issues

- **Command-based servers**: Verify the command and arguments are correct
- **HTTP/SSE servers**: Check the URL is accessible and CORS is properly configured
- **Authentication**: Ensure tokens are valid if required

### Tool Execution Errors

- Check the browser console for error messages
- Verify the MCP server is still connected
- Ensure tool arguments are in the correct format

### Backend Logs

Check Jupyter server logs for detailed error information:
```bash
jupyter lab --debug
```

Look for messages prefixed with `[mcp_service]` or `[mcp_handlers]`.

## Security Considerations

1. **Command Execution**: Command-based MCPs run on the server with the privileges of the Jupyter process
2. **Network Access**: HTTP/SSE MCPs can access any network endpoints
3. **Tool Arguments**: All tool arguments are passed through to MCP servers without modification
4. **Authentication**: Token-based authentication is supported for HTTP/SSE connections

Users should only connect to trusted MCP servers and validate configurations before connecting.

## Future Enhancements

Potential improvements for future releases:

- Tool permission system (approve/deny specific tools)
- Per-conversation MCP server selection
- MCP server templates/presets
- Better error recovery and reconnection logic
- Tool usage analytics and logging
- Support for MCP server discovery/registry

