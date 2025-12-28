"""
MCP Handlers - Tornado HTTP handlers for MCP API endpoints
Provides REST API for managing MCP server connections and tool calls
"""
import json
import logging
import traceback
import tornado
from jupyter_server.base.handlers import APIHandler
from .mcp_service import get_mcp_service

logger = logging.getLogger(__name__)

# Enable debug logging
logger.setLevel(logging.DEBUG)


class MCPServersHandler(APIHandler):
    """Handler for managing MCP server configurations"""
    
    @tornado.web.authenticated
    async def get(self):
        """Get all configured MCP servers"""
        try:
            mcp_service = get_mcp_service()
            configs = mcp_service.load_all_configs()
            
            # Add connection status to each server
            servers = []
            for server_id, config in configs.items():
                server_info = {
                    **config,
                    'status': mcp_service.get_connection_status(server_id),
                    'enabled': config.get('enabled', True)
                }
                
                # Add tool count if connected
                if server_id in mcp_service.tools_cache:
                    server_info['toolCount'] = len(mcp_service.tools_cache[server_id])
                
                servers.append(server_info)
            
            self.finish(json.dumps({
                'servers': servers
            }))
        except Exception as e:
            logger.error(f"Error getting MCP servers: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e)
            }))
    
    @tornado.web.authenticated
    async def post(self):
        """Save a new MCP server configuration"""
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            
            # Validate required fields
            if 'name' not in data:
                self.set_status(400)
                self.finish(json.dumps({
                    'error': 'Server name is required'
                }))
                return
            
            # Determine connection type (default to 'command' if not specified)
            connection_type = data.get('type', 'command')
            data['type'] = connection_type  # Ensure type is set in the data
            
            if connection_type == 'command':
                if 'command' not in data:
                    self.set_status(400)
                    self.finish(json.dumps({
                        'error': 'Command is required for command-based MCP'
                    }))
                    return
            elif connection_type in ['http', 'sse']:
                if 'url' not in data:
                    self.set_status(400)
                    self.finish(json.dumps({
                        'error': 'URL is required for HTTP/SSE MCP'
                    }))
                    return
            else:
                self.set_status(400)
                self.finish(json.dumps({
                    'error': f'Invalid connection type: {connection_type}'
                }))
                return
            
            # Save configuration
            mcp_service = get_mcp_service()
            saved_config = mcp_service.save_server_config(data)
            
            self.finish(json.dumps({
                'success': True,
                'server': saved_config
            }))
        except json.JSONDecodeError:
            self.set_status(400)
            self.finish(json.dumps({
                'error': 'Invalid JSON in request body'
            }))
        except Exception as e:
            logger.error(f"Error saving MCP server: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e)
            }))


class MCPServerHandler(APIHandler):
    """Handler for individual MCP server operations"""
    
    @tornado.web.authenticated
    async def delete(self, server_id):
        """Delete an MCP server configuration"""
        try:
            mcp_service = get_mcp_service()
            success = mcp_service.delete_server_config(server_id)
            
            if success:
                self.finish(json.dumps({
                    'success': True,
                    'message': f'Server {server_id} deleted'
                }))
            else:
                self.set_status(404)
                self.finish(json.dumps({
                    'error': 'Server not found'
                }))
        except Exception as e:
            logger.error(f"Error deleting MCP server: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e)
            }))
    
    @tornado.web.authenticated
    async def put(self, server_id):
        """Update an MCP server configuration"""
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            mcp_service = get_mcp_service()
            
            # Get existing config
            config = mcp_service.get_server_config(server_id)
            if not config:
                self.set_status(404)
                self.finish(json.dumps({
                    'error': 'Server not found'
                }))
                return
            
            # Update config with new data
            config.update(data)
            config['id'] = server_id  # Ensure ID is preserved
            
            # Save updated config
            saved_config = mcp_service.save_server_config(config)
            
            self.finish(json.dumps({
                'success': True,
                'server': saved_config
            }))
        except json.JSONDecodeError:
            self.set_status(400)
            self.finish(json.dumps({
                'error': 'Invalid JSON in request body'
            }))
        except Exception as e:
            logger.error(f"Error updating MCP server: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e)
            }))


class MCPConnectHandler(APIHandler):
    """Handler for connecting to MCP servers"""
    
    @tornado.web.authenticated
    async def post(self):
        """Connect to a specific MCP server"""
        server_id = None
        try:
            logger.debug(f"[MCP Handler] Received connect request")
            data = json.loads(self.request.body.decode('utf-8'))
            server_id = data.get('server_id')
            
            logger.debug(f"[MCP Handler] Request data: {data}")
            
            if not server_id:
                logger.warning(f"[MCP Handler] Missing server_id in request")
                self.set_status(400)
                self.finish(json.dumps({
                    'error': 'server_id is required'
                }))
                return
            
            logger.info(f"[MCP Handler] Attempting to connect to server: {server_id}")
            mcp_service = get_mcp_service()
            server_info = await mcp_service.connect(server_id)
            
            logger.info(f"[MCP Handler] Successfully connected to {server_id}")
            self.finish(json.dumps({
                'success': True,
                'server': server_info
            }))
        except json.JSONDecodeError as e:
            logger.error(f"[MCP Handler] Invalid JSON in request body: {e}")
            logger.error(f"[MCP Handler] Stack trace:\n{traceback.format_exc()}")
            self.set_status(400)
            self.finish(json.dumps({
                'error': f'Invalid JSON in request body: {str(e)}'
            }))
        except ValueError as e:
            logger.error(f"[MCP Handler] ValueError for server {server_id}: {e}")
            logger.error(f"[MCP Handler] Stack trace:\n{traceback.format_exc()}")
            self.set_status(404)
            self.finish(json.dumps({
                'error': str(e),
                'errorType': 'ValueError',
                'serverId': server_id
            }))
        except RuntimeError as e:
            logger.error(f"[MCP Handler] RuntimeError connecting to {server_id}: {e}")
            logger.error(f"[MCP Handler] Stack trace:\n{traceback.format_exc()}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e),
                'errorType': 'RuntimeError',
                'serverId': server_id,
                'details': 'Check server logs for detailed error information'
            }))
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"[MCP Handler] Unexpected error ({error_type}) connecting to {server_id}: {error_msg}")
            logger.error(f"[MCP Handler] Full stack trace:\n{traceback.format_exc()}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': error_msg,
                'errorType': error_type,
                'serverId': server_id,
                'stackTrace': traceback.format_exc(),
                'details': 'An unexpected error occurred. Check server logs for more information.'
            }))


class MCPDisconnectHandler(APIHandler):
    """Handler for disconnecting from MCP servers"""
    
    @tornado.web.authenticated
    async def post(self, server_id):
        """Disconnect from a specific MCP server"""
        try:
            mcp_service = get_mcp_service()
            success = await mcp_service.disconnect(server_id)
            
            if success:
                self.finish(json.dumps({
                    'success': True,
                    'message': f'Disconnected from server {server_id}'
                }))
            else:
                self.set_status(404)
                self.finish(json.dumps({
                    'error': 'Server not found or not connected'
                }))
        except Exception as e:
            logger.error(f"Error disconnecting from MCP server: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e)
            }))


class MCPToolsHandler(APIHandler):
    """Handler for listing MCP tools"""
    
    @tornado.web.authenticated
    async def get(self, server_id):
        """Get available tools from a connected MCP server"""
        try:
            mcp_service = get_mcp_service()
            tools = await mcp_service.list_tools(server_id)
            
            self.finish(json.dumps({
                'tools': tools
            }))
        except ValueError as e:
            self.set_status(404)
            self.finish(json.dumps({
                'error': str(e)
            }))
        except Exception as e:
            logger.error(f"Error listing MCP tools: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e)
            }))


class MCPAllToolsHandler(APIHandler):
    """Handler for getting all tools from all connected servers"""
    
    @tornado.web.authenticated
    async def get(self):
        """Get all tools from all connected MCP servers"""
        try:
            mcp_service = get_mcp_service()
            tools = await mcp_service.get_all_tools()
            
            self.finish(json.dumps({
                'tools': tools
            }))
        except Exception as e:
            logger.error(f"Error getting all MCP tools: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e)
            }))


class MCPToolCallHandler(APIHandler):
    """Handler for calling MCP tools"""
    
    @tornado.web.authenticated
    async def post(self):
        """Call a tool on an MCP server"""
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            
            server_id = data.get('server_id')
            tool_name = data.get('tool_name')
            arguments = data.get('arguments', {})
            
            if not server_id or not tool_name:
                self.set_status(400)
                self.finish(json.dumps({
                    'error': 'server_id and tool_name are required'
                }))
                return
            
            mcp_service = get_mcp_service()
            result = await mcp_service.call_tool(server_id, tool_name, arguments)
            
            self.finish(json.dumps({
                'success': True,
                'result': result
            }))
        except ValueError as e:
            self.set_status(404)
            self.finish(json.dumps({
                'error': str(e)
            }))
        except Exception as e:
            logger.error(f"Error calling MCP tool: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e)
            }))


class MCPServerEnableHandler(APIHandler):
    """Handler for enabling MCP servers"""
    
    @tornado.web.authenticated
    async def post(self, server_id):
        """Enable an MCP server"""
        try:
            mcp_service = get_mcp_service()
            success = mcp_service.enable_server(server_id)
            
            if success:
                self.finish(json.dumps({
                    'success': True,
                    'message': f'Server {server_id} enabled'
                }))
            else:
                self.set_status(404)
                self.finish(json.dumps({
                    'error': 'Server not found'
                }))
        except Exception as e:
            logger.error(f"Error enabling MCP server: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e)
            }))


class MCPServerDisableHandler(APIHandler):
    """Handler for disabling MCP servers"""
    
    @tornado.web.authenticated
    async def post(self, server_id):
        """Disable an MCP server"""
        try:
            mcp_service = get_mcp_service()
            success = mcp_service.disable_server(server_id)
            
            if success:
                self.finish(json.dumps({
                    'success': True,
                    'message': f'Server {server_id} disabled'
                }))
            else:
                self.set_status(404)
                self.finish(json.dumps({
                    'error': 'Server not found'
                }))
        except Exception as e:
            logger.error(f"Error disabling MCP server: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e)
            }))


class MCPToolEnableHandler(APIHandler):
    """Handler for enabling/disabling individual MCP tools"""
    
    @tornado.web.authenticated
    async def put(self, server_id, tool_name):
        """Update enabled/disabled state for a specific tool"""
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            enabled = data.get('enabled', True)
            
            mcp_service = get_mcp_service()
            success = mcp_service.update_tool_enabled(server_id, tool_name, enabled)
            
            if success:
                self.finish(json.dumps({
                    'success': True,
                    'message': f'Tool {tool_name} {"enabled" if enabled else "disabled"}'
                }))
            else:
                self.set_status(404)
                self.finish(json.dumps({
                    'error': 'Server not found'
                }))
        except Exception as e:
            logger.error(f"Error updating tool enabled state: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e)
            }))


class MCPConfigFileHandler(APIHandler):
    """Handler for managing the entire MCP config file"""
    
    @tornado.web.authenticated
    async def get(self):
        """Get the raw JSON config file content"""
        try:
            logger.debug(f"[MCP ConfigFile Handler] GET request received")
            mcp_service = get_mcp_service()
            content = mcp_service.get_config_file_content()
            
            # Ensure content is valid JSON string
            if not content:
                content = json.dumps({'mcpServers': {}}, indent=2)
            
            # Validate it's valid JSON
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Config file content is not valid JSON: {e}")
                content = json.dumps({'mcpServers': {}}, indent=2)
            
            logger.debug(f"[MCP ConfigFile Handler] Returning config file content ({len(content)} chars)")
            self.set_header('Content-Type', 'application/json; charset=utf-8')
            self.finish(content)
        except Exception as e:
            logger.error(f"Error reading config file: {e}")
            logger.error(f"Stack trace:\n{traceback.format_exc()}")
            self.set_status(500)
            self.set_header('Content-Type', 'application/json')
            self.finish(json.dumps({
                'error': str(e)
            }))
    
    @tornado.web.authenticated
    async def put(self):
        """Update the entire config file with diff detection"""
        try:
            content = self.request.body.decode('utf-8')
            mcp_service = get_mcp_service()
            
            result = mcp_service.update_config_file(content)
            
            self.finish(json.dumps(result))
        except ValueError as e:
            self.set_status(400)
            self.finish(json.dumps({
                'error': str(e)
            }))
        except Exception as e:
            logger.error(f"Error updating config file: {e}")
            self.set_status(500)
            self.finish(json.dumps({
                'error': str(e)
            }))
