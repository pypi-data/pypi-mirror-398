"""
MCP Connection Service - Manages connections to Model Context Protocol servers
Supports command-based (stdio), HTTP, and SSE connection types

IMPORTANT: On Windows, asyncio subprocess support requires ProactorEventLoop, but Jupyter/Tornado
uses SelectorEventLoop. Instead of using asyncio.create_subprocess_*, we use subprocess.Popen
with asyncio wrappers for cross-platform compatibility.
"""
import asyncio
import json
import logging
import uuid
import traceback
import sys
import platform
import subprocess
import threading
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiohttp
from .cache_service import get_cache_service, RobustFileOperations

logger = logging.getLogger(__name__)

# Set logger to DEBUG level for comprehensive debugging
logger.setLevel(logging.DEBUG)

# Check current event loop (for debugging)
try:
    loop = asyncio.get_running_loop()
    loop_type = type(loop).__name__
    logger.debug(f"[MCP] Current event loop type: {loop_type}")
    if platform.system() == 'Windows' and 'ProactorEventLoop' not in loop_type:
        logger.warning(f"[MCP] Windows using {loop_type} - will use subprocess.Popen instead of asyncio subprocesses")
except RuntimeError:
    logger.debug(f"[MCP] No running event loop yet")



class MCPConnectionService:
    """Service for managing MCP server connections and tool calls"""
    
    _instance = None
    
    # Default whitelist of tools grouped by server type
    DEFAULT_WHITELISTED_TOOLS_BY_SERVER = {
        'Dbt': [
            'query_metrics',
            'get_metrics_compiled_sql',
            'get_all_models',
            'get_mart_models',
            'get_model_details',
            'get_model_parents',
            'get_model_children',
            'get_related_models',
            'list_metrics',
            'get_semantic_model_details',
        ],
        'Google': [
            'start_google_auth',
            'search_docs',
            'get_doc_content',
            'list_docs_in_folder',
            'inspect_doc_structure',
            'read_document_comments',
            'create_document_comment',
            'reply_to_document_comment',
            'resolve_document_comment',
            'search_drive_files',
            'list_drive_items',
            'get_drive_file_content',
            'get_drive_file_download_url',
            'list_drive_items_in_folder',
        ],
        'Slack': [
            'conversations_search_messages',
            'conversations_history',
            'conversations_replies',
            'channels_list',
        ],
        'Notion': [
            'API-post-search',
            'API-get-block-children',
            'API-retrieve-a-page',
            'API-retrieve-a-database',
            'API-post-database-query',
        ],
    }
    
    # Flattened list for backward compatibility and general checks
    DEFAULT_WHITELISTED_TOOLS = [
        tool for tools in DEFAULT_WHITELISTED_TOOLS_BY_SERVER.values() for tool in tools
    ]
    
    def __init__(self):
        self.connections: Dict[str, 'MCPConnection'] = {}
        self.tools_cache: Dict[str, List[Dict]] = {}
        self.cache = get_cache_service()
        self.mcp_config_key = 'mcp_servers'
        self._migrated_from_cache = False
        self._ensure_migration()
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance of MCP service"""
        if cls._instance is None:
            cls._instance = MCPConnectionService()
        return cls._instance
    
    def get_mcp_config_path(self) -> Path:
        """Get the path to the MCP configuration JSON file (Cursor format)"""
        # Use the same cache directory as other SignalPilot files for consistency
        from .cache_service import CacheDirectoryManager
        cache_dir = CacheDirectoryManager.find_usable_cache_directory()
        if cache_dir:
            return cache_dir / 'mcp.json'
        else:
            # Fallback to old location if cache directory not available
            if platform.system() == 'Windows':
                config_dir = Path(os.environ.get('USERPROFILE', Path.home())) / '.signalpilot-ai-internal'
            else:
                config_dir = Path.home() / '.signalpilot-ai-internal'
            config_dir.mkdir(parents=True, exist_ok=True)
            return config_dir / 'mcp.json'
    
    def _infer_server_type(self, config: Dict) -> str:
        """Infer server type from config structure (Cursor format)"""
        if 'command' in config:
            return 'command'
        elif 'url' in config:
            return 'http'  # HTTP/SSE both use 'url'
        else:
            # Fallback: try to infer from old format
            return config.get('type', 'command')
    
    def _normalize_config_from_storage(self, server_id: str, config: Dict) -> Dict:
        """Convert Cursor schema format to internal format"""
        # Cursor format: server config may have 'command'/'args' or 'name'/'url'
        # Internal format: always has 'id', 'name', 'type', and type-specific fields
        
        normalized = {
            'id': server_id,
            'type': self._infer_server_type(config)
        }
        
        # Copy all fields
        normalized.update(config)
        
        # Ensure name exists (use server_id as fallback for command-based)
        if 'name' not in normalized:
            if normalized['type'] == 'command':
                normalized['name'] = server_id
            else:
                normalized['name'] = config.get('name', server_id)
        
        # Handle enabled field (defaults to True)
        if 'enabled' not in normalized:
            normalized['enabled'] = True
        
        return normalized
    
    def _normalize_config_for_storage(self, config: Dict) -> Dict:
        """Convert internal format to Cursor schema format"""
        # Remove internal-only fields
        storage_config = {}
        
        # Copy relevant fields based on type
        server_type = config.get('type', 'command')
        
        if server_type == 'command':
            if 'command' in config:
                storage_config['command'] = config['command']
            if 'args' in config:
                storage_config['args'] = config['args']
            if 'env' in config:
                storage_config['env'] = config['env']
        else:  # http/sse
            if 'name' in config:
                storage_config['name'] = config['name']
            if 'url' in config:
                storage_config['url'] = config['url']
            if 'token' in config:
                storage_config['token'] = config['token']
        
        # Add enabled if not default (True)
        enabled = config.get('enabled', True)
        if not enabled:
            storage_config['enabled'] = False
        
        # Add enabledTools if present
        if 'enabledTools' in config:
            storage_config['enabledTools'] = config['enabledTools']
        
        return storage_config
    
    def _ensure_migration(self):
        """Migrate from cache-based storage to JSON file if needed"""
        if self._migrated_from_cache:
            return
        
        config_path = self.get_mcp_config_path()
        
        # If JSON file already exists, migration already done
        if config_path.exists():
            self._migrated_from_cache = True
            return
        
        # Try to migrate from cache
        try:
            cache_data = self.cache.get_app_value(self.mcp_config_key)
            if cache_data:
                old_configs = json.loads(cache_data)
                if old_configs:
                    logger.info(f"[MCP] Migrating {len(old_configs)} servers from cache to JSON file")
                    
                    # Convert to Cursor format
                    cursor_format = {'mcpServers': {}}
                    for server_id, config in old_configs.items():
                        # Normalize old config
                        if 'id' not in config:
                            config['id'] = server_id
                        if 'enabled' not in config:
                            config['enabled'] = True
                        
                        # Convert to storage format
                        storage_config = self._normalize_config_for_storage(config)
                        cursor_format['mcpServers'][server_id] = storage_config
                    
                    # Write to JSON file
                    if RobustFileOperations.safe_write_json(config_path, cursor_format):
                        logger.info(f"[MCP] Successfully migrated to {config_path}")
                        # Optionally delete old cache entry (commented for safety)
                        # self.cache.delete_app_value(self.mcp_config_key)
                    else:
                        logger.error(f"[MCP] Failed to write migrated config to {config_path}")
        except Exception as e:
            logger.warning(f"[MCP] Migration from cache failed: {e}, starting fresh")
        
        self._migrated_from_cache = True
    
    def save_server_config(self, server_config: Dict) -> Dict:
        """Save MCP server configuration to JSON file (Cursor format)"""
        try:
            # Ensure server has an ID
            if 'id' not in server_config:
                server_config['id'] = str(uuid.uuid4())
            
            server_id = server_config['id']
            
            # Load existing configs
            config_path = self.get_mcp_config_path()
            cursor_data = RobustFileOperations.safe_read_json(config_path, {})
            mcp_servers = cursor_data.get('mcpServers', {})
            
            # Convert to storage format and add/update
            storage_config = self._normalize_config_for_storage(server_config)
            mcp_servers[server_id] = storage_config
            
            # Write back to file
            cursor_data['mcpServers'] = mcp_servers
            if not RobustFileOperations.safe_write_json(config_path, cursor_data):
                raise RuntimeError(f"Failed to write MCP config to {config_path}")
            
            logger.info(f"Saved MCP server config: {server_config.get('name', server_id)}")
            return server_config
        except Exception as e:
            logger.error(f"Error saving MCP server config: {e}")
            logger.error(f"Stack trace:\n{traceback.format_exc()}")
            raise
    
    def load_all_configs(self) -> Dict[str, Dict]:
        """Load all MCP server configurations from JSON file (Cursor format)"""
        try:
            config_path = self.get_mcp_config_path()
            
            if not config_path.exists():
                return {}
            
            # Read JSON file
            cursor_data = RobustFileOperations.safe_read_json(config_path, {})
            
            # Extract mcpServers object
            mcp_servers = cursor_data.get('mcpServers', {})
            
            # Convert from Cursor format to internal format
            configs = {}
            for server_id, server_config in mcp_servers.items():
                configs[server_id] = self._normalize_config_from_storage(server_id, server_config)
            
            return configs
        except Exception as e:
            logger.error(f"Error loading MCP configs: {e}")
            logger.error(f"Stack trace:\n{traceback.format_exc()}")
            return {}
    
    def get_server_config(self, server_id: str) -> Optional[Dict]:
        """Get a specific server configuration"""
        configs = self.load_all_configs()
        return configs.get(server_id)
    
    def delete_server_config(self, server_id: str) -> bool:
        """Delete a server configuration from JSON file"""
        try:
            config_path = self.get_mcp_config_path()
            
            if not config_path.exists():
                return False
            
            # Load current config
            cursor_data = RobustFileOperations.safe_read_json(config_path, {})
            mcp_servers = cursor_data.get('mcpServers', {})
            
            if server_id in mcp_servers:
                del mcp_servers[server_id]
                
                # Write back to file
                cursor_data['mcpServers'] = mcp_servers
                if not RobustFileOperations.safe_write_json(config_path, cursor_data):
                    raise RuntimeError(f"Failed to write MCP config to {config_path}")
                
                # Also disconnect if connected
                if server_id in self.connections:
                    asyncio.create_task(self.disconnect(server_id))
                
                logger.info(f"Deleted MCP server config: {server_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting MCP server config: {e}")
            logger.error(f"Stack trace:\n{traceback.format_exc()}")
            return False
    
    async def connect(self, server_id: str) -> Dict:
        """Connect to an MCP server"""
        try:
            logger.debug(f"[MCP] Attempting to connect to server {server_id}")
            config = self.get_server_config(server_id)
            if not config:
                error_msg = f"Server configuration not found: {server_id}"
                logger.error(f"[MCP] {error_msg}")
                raise ValueError(error_msg)
            
            # Check if server is enabled
            if not config.get('enabled', True):
                error_msg = f"Server {server_id} is disabled"
                logger.warning(f"[MCP] {error_msg}")
                raise ValueError(error_msg)
            
            logger.debug(f"[MCP] Server config loaded: name={config.get('name')}, type={config.get('type')}")
            
            # Check if already connected
            if server_id in self.connections:
                connection = self.connections[server_id]
                if connection.is_connected():
                    logger.info(f"[MCP] Already connected to MCP server: {config.get('name', server_id)}")
                    return self._get_server_info(server_id, config)
                else:
                    logger.warning(f"[MCP] Stale connection found for {server_id}, removing")
                    del self.connections[server_id]
            
            # Determine connection type (infer if not set)
            connection_type = config.get('type')
            if not connection_type:
                connection_type = self._infer_server_type(config)
                config['type'] = connection_type
            
            logger.debug(f"[MCP] Connection type: {connection_type}")
            
            if connection_type == 'command':
                connection = MCPCommandConnection(server_id, config)
            elif connection_type in ['http', 'sse']:
                connection = MCPHTTPConnection(server_id, config)
            else:
                error_msg = f"Unknown connection type: {connection_type}"
                logger.error(f"[MCP] {error_msg}")
                raise ValueError(error_msg)
            
            # Connect and store
            logger.debug(f"[MCP] Starting connection to {config.get('name')}...")
            await connection.connect()
            self.connections[server_id] = connection
            logger.debug(f"[MCP] Connection established, listing tools...")
            
            # List and cache tools
            tools = await connection.list_tools()
            self.tools_cache[server_id] = tools
            
            # Auto-whitelist tools on first connection or ensure default whitelisted tools are enabled
            tool_names = [tool['name'] for tool in tools]
            self._ensure_default_whitelisted_tools(server_id, config, tool_names)
            
            logger.info(f"[MCP] ✓ Connected to MCP server: {config['name']} ({len(tools)} tools)")
            
            # Ensure default whitelisted tools are enabled (final check)
            self._ensure_default_whitelisted_tools(server_id, config, tool_names)
            
            return self._get_server_info(server_id, config)
        except ValueError as e:
            # Re-raise ValueError with original message
            logger.error(f"[MCP] Configuration error for {server_id}: {str(e)}")
            logger.error(f"[MCP] Stack trace:\n{traceback.format_exc()}")
            raise
        except Exception as e:
            error_msg = f"Failed to connect to MCP server {server_id}: {type(e).__name__}: {str(e)}"
            logger.error(f"[MCP] {error_msg}")
            logger.error(f"[MCP] Full stack trace:\n{traceback.format_exc()}")
            # Include the original exception type in the error message
            raise RuntimeError(error_msg) from e
    
    async def disconnect(self, server_id: str) -> bool:
        """Disconnect from an MCP server"""
        try:
            if server_id in self.connections:
                connection = self.connections[server_id]
                await connection.disconnect()
                del self.connections[server_id]
                
                if server_id in self.tools_cache:
                    del self.tools_cache[server_id]
                
                logger.info(f"Disconnected from MCP server: {server_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error disconnecting from MCP server {server_id}: {e}")
            return False
    
    async def list_tools(self, server_id: str) -> List[Dict]:
        """List tools available from a connected MCP server"""
        try:
            # Check cache first
            if server_id in self.tools_cache:
                tools = self.tools_cache[server_id]
                # Ensure default whitelisted tools are enabled even when using cache
                config = self.get_server_config(server_id)
                if config:
                    tool_names = [tool['name'] for tool in tools]
                    self._ensure_default_whitelisted_tools(server_id, config, tool_names)
                return tools
            
            # Otherwise fetch from connection
            if server_id not in self.connections:
                raise ValueError(f"Not connected to server: {server_id}")
            
            connection = self.connections[server_id]
            tools = await connection.list_tools()
            self.tools_cache[server_id] = tools
            
            # Ensure default whitelisted tools are enabled
            config = self.get_server_config(server_id)
            if config:
                tool_names = [tool['name'] for tool in tools]
                self._ensure_default_whitelisted_tools(server_id, config, tool_names)
            
            return tools
        except Exception as e:
            logger.error(f"Error listing tools from MCP server {server_id}: {e}")
            raise
    
    async def get_all_tools(self) -> List[Dict]:
        """Get all tools from all connected servers"""
        all_tools = []
        for server_id in self.connections.keys():
            try:
                tools = await self.list_tools(server_id)
                config = self.get_server_config(server_id)
                
                # Add server info to each tool
                for tool in tools:
                    tool['serverId'] = server_id
                    tool['serverName'] = config.get('name', server_id)
                
                all_tools.extend(tools)
            except Exception as e:
                logger.error(f"Error getting tools from server {server_id}: {e}")
        
        return all_tools
    
    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict) -> Any:
        """Call a tool on an MCP server"""
        try:
            if server_id not in self.connections:
                raise ValueError(f"Not connected to server: {server_id}")
            
            connection = self.connections[server_id]
            result = await connection.call_tool(tool_name, arguments)
            
            logger.info(f"Called tool {tool_name} on server {server_id}")
            return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on server {server_id}: {e}")
            raise
    
    def get_connection_status(self, server_id: str) -> str:
        """Get connection status for a server"""
        if server_id in self.connections:
            return 'connected' if self.connections[server_id].is_connected() else 'error'
        return 'disconnected'
    
    def _get_server_info(self, server_id: str, config: Dict) -> Dict:
        """Get server information for response"""
        tools = self.tools_cache.get(server_id, [])
        enabled_tools = config.get('enabledTools', [])
        return {
            'serverId': server_id,
            'name': config.get('name', server_id),
            'status': self.get_connection_status(server_id),
            'type': config.get('type', 'command'),
            'toolCount': len(tools),
            'tools': tools,
            'enabled': config.get('enabled', True),
            'enabledTools': enabled_tools
        }
    
    def enable_server(self, server_id: str) -> bool:
        """Enable an MCP server"""
        try:
            config = self.get_server_config(server_id)
            if not config:
                return False
            
            config['enabled'] = True
            self.save_server_config(config)
            logger.info(f"Enabled MCP server: {server_id}")
            return True
        except Exception as e:
            logger.error(f"Error enabling MCP server {server_id}: {e}")
            return False
    
    def disable_server(self, server_id: str) -> bool:
        """Disable an MCP server and disconnect if connected"""
        try:
            config = self.get_server_config(server_id)
            if not config:
                return False
            
            config['enabled'] = False
            self.save_server_config(config)
            
            # Disconnect if connected
            if server_id in self.connections:
                asyncio.create_task(self.disconnect(server_id))
            
            logger.info(f"Disabled MCP server: {server_id}")
            return True
        except Exception as e:
            logger.error(f"Error disabling MCP server {server_id}: {e}")
            return False
    
    def _ensure_default_whitelisted_tools(self, server_id: str, config: Dict, available_tool_names: List[str]) -> None:
        """Ensure default whitelisted tools are always enabled for a server"""
        try:
            existing_enabled = set(config.get('enabledTools', []))
            available_tools = set(available_tool_names)
            
            # Get server name to determine which tools to whitelist
            server_name = config.get('name', server_id)
            
            # Check if this server should use selective whitelisting
            # Only apply selective whitelisting for servers named "Notion", "Dbt", "Slack", or "Google"
            should_use_selective_whitelist = any(
                server_name.startswith(prefix) for prefix in ['Notion', 'Dbt', 'Slack', 'Google']
            )
            
            if should_use_selective_whitelist:
                # Determine which server type based on name prefix
                server_type = None
                for prefix in ['Notion', 'Dbt', 'Slack', 'Google']:
                    if server_name.startswith(prefix):
                        server_type = prefix
                        break
                
                # Get default whitelisted tools for this server type
                if server_type and server_type in self.DEFAULT_WHITELISTED_TOOLS_BY_SERVER:
                    default_whitelisted = set(self.DEFAULT_WHITELISTED_TOOLS_BY_SERVER[server_type])
                else:
                    # Fallback: use all default whitelisted tools
                    default_whitelisted = set(self.DEFAULT_WHITELISTED_TOOLS)
            else:
                # For other servers, use all default whitelisted tools
                default_whitelisted = set(self.DEFAULT_WHITELISTED_TOOLS)
            
            # Find default whitelisted tools that are available
            available_default_tools = default_whitelisted & available_tools
            
            if 'enabledTools' not in config or not config.get('enabledTools'):
                # First connection
                if should_use_selective_whitelist:
                    # Only enable default whitelisted tools for this server type
                    config['enabledTools'] = list(available_default_tools)
                    self.save_server_config(config)
                    logger.info(f"[MCP] Auto-whitelisted {len(available_default_tools)} default whitelisted tools for {server_id} ({server_type}) (out of {len(available_tool_names)} available): {sorted(available_default_tools)}")
                else:
                    # Enable all tools for other servers
                    config['enabledTools'] = list(available_tools)
                    self.save_server_config(config)
                    logger.info(f"[MCP] Auto-whitelisted all {len(available_tools)} tools for {server_id} (not a selective whitelist server)")
            else:
                # On reconnect or update, ensure all default whitelisted tools are enabled
                # This will re-enable any default whitelisted tools that were disabled
                final_enabled = existing_enabled | available_default_tools
                
                if final_enabled != existing_enabled:
                    tools_added = final_enabled - existing_enabled
                    config['enabledTools'] = list(final_enabled)
                    self.save_server_config(config)
                    logger.info(f"[MCP] Auto-enabled {len(tools_added)} default whitelisted tools for {server_id}: {sorted(tools_added)}")
        except Exception as e:
            logger.error(f"Error ensuring default whitelisted tools for {server_id}: {e}")
            logger.error(f"Stack trace:\n{traceback.format_exc()}")
    
    def update_tool_enabled(self, server_id: str, tool_name: str, enabled: bool) -> bool:
        """Update enabled/disabled state for a specific tool"""
        try:
            config = self.get_server_config(server_id)
            if not config:
                return False
            
            # Check if this is a default whitelisted tool
            is_default_whitelisted = tool_name in self.DEFAULT_WHITELISTED_TOOLS
            
            # If trying to disable a default whitelisted tool, warn but allow it
            # (it will be re-enabled on next reconnect)
            if not enabled and is_default_whitelisted:
                logger.warning(f"Attempting to disable default whitelisted tool {tool_name} for server {server_id}. It will be re-enabled on reconnect.")
            
            # Get current enabled tools, or initialize with all available tools if not set
            enabled_tools = config.get('enabledTools')
            if enabled_tools is None:
                # If enabledTools is not set, initialize with all available tools from cache
                if server_id in self.tools_cache:
                    tool_names = [tool['name'] for tool in self.tools_cache[server_id]]
                    enabled_tools = tool_names
                    logger.info(f"Initializing enabledTools for {server_id} with {len(tool_names)} tools")
                else:
                    # If tools not cached, start with empty list (will be populated on next connect)
                    enabled_tools = []
                    logger.warning(f"No tools cached for {server_id}, starting with empty enabledTools")
            
            enabled_tools_set = set(enabled_tools)
            
            if enabled:
                enabled_tools_set.add(tool_name)
            else:
                # Allow disabling even default whitelisted tools (they'll be re-enabled on reconnect)
                enabled_tools_set.discard(tool_name)
            
            config['enabledTools'] = list(enabled_tools_set)
            self.save_server_config(config)
            
            logger.info(f"{'Enabled' if enabled else 'Disabled'} tool {tool_name} for server {server_id}. Enabled tools: {len(enabled_tools_set)}")
            return True
        except Exception as e:
            logger.error(f"Error updating tool enabled state for {server_id}/{tool_name}: {e}")
            logger.error(f"Stack trace:\n{traceback.format_exc()}")
            return False
    
    async def connect_all_enabled(self) -> Dict[str, Dict]:
        """Connect to all enabled MCP servers"""
        results = {}
        configs = self.load_all_configs()
        
        for server_id, config in configs.items():
            if config.get('enabled', True):
                try:
                    logger.info(f"[MCP] Auto-connecting enabled server: {server_id}")
                    server_info = await self.connect(server_id)
                    results[server_id] = {'success': True, 'server': server_info}
                except Exception as e:
                    logger.error(f"[MCP] Failed to auto-connect {server_id}: {e}")
                    results[server_id] = {'success': False, 'error': str(e)}
            else:
                logger.debug(f"[MCP] Skipping disabled server: {server_id}")
        
        return results
    
    def update_config_file(self, new_json_content: str) -> Dict[str, Any]:
        """Update the entire config file and apply diff-based changes"""
        try:
            config_path = self.get_mcp_config_path()
            
            # Parse new JSON
            try:
                new_data = json.loads(new_json_content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
            
            if 'mcpServers' not in new_data:
                raise ValueError("JSON must contain 'mcpServers' object")
            
            new_servers = new_data.get('mcpServers', {})
            
            # Load current configs
            old_configs = self.load_all_configs()
            old_server_ids = set(old_configs.keys())
            new_server_ids = set(new_servers.keys())
            
            changes = {
                'added': [],
                'removed': [],
                'modified': [],
                'enabled_changes': []
            }
            
            # Detect added servers
            for server_id in new_server_ids - old_server_ids:
                changes['added'].append(server_id)
            
            # Detect removed servers
            for server_id in old_server_ids - new_server_ids:
                changes['removed'].append(server_id)
                # Disconnect removed servers
                if server_id in self.connections:
                    asyncio.create_task(self.disconnect(server_id))
            
            # Detect modified servers
            for server_id in new_server_ids & old_server_ids:
                old_config = old_configs[server_id]
                new_storage_config = new_servers[server_id]
                new_config = self._normalize_config_from_storage(server_id, new_storage_config)
                
                # Check if enabled status changed
                old_enabled = old_config.get('enabled', True)
                new_enabled = new_config.get('enabled', True)
                
                if old_enabled != new_enabled:
                    changes['enabled_changes'].append({
                        'server_id': server_id,
                        'old_enabled': old_enabled,
                        'new_enabled': new_enabled
                    })
                
                # Check if config changed (simple comparison)
                old_storage = self._normalize_config_for_storage(old_config)
                if old_storage != new_storage_config:
                    changes['modified'].append(server_id)
            
            # Write new config to file
            if not RobustFileOperations.safe_write_json(config_path, new_data):
                raise RuntimeError(f"Failed to write updated config to {config_path}")
            
            # Apply changes asynchronously
            async def apply_changes():
                # Connect newly added enabled servers
                for server_id in changes['added']:
                    new_config = self._normalize_config_from_storage(server_id, new_servers[server_id])
                    if new_config.get('enabled', True):
                        try:
                            await self.connect(server_id)
                        except Exception as e:
                            logger.error(f"Failed to connect added server {server_id}: {e}")
                
                # Handle enabled/disabled changes
                for change in changes['enabled_changes']:
                    server_id = change['server_id']
                    if change['new_enabled']:
                        try:
                            await self.connect(server_id)
                        except Exception as e:
                            logger.error(f"Failed to connect enabled server {server_id}: {e}")
                    else:
                        await self.disconnect(server_id)
                
                # Handle modified servers (disconnect and reconnect if enabled)
                for server_id in changes['modified']:
                    new_config = self._normalize_config_from_storage(server_id, new_servers[server_id])
                    # Disconnect old connection
                    if server_id in self.connections:
                        await self.disconnect(server_id)
                    # Reconnect if enabled
                    if new_config.get('enabled', True):
                        try:
                            await self.connect(server_id)
                        except Exception as e:
                            logger.error(f"Failed to reconnect modified server {server_id}: {e}")
            
            # Schedule async changes
            asyncio.create_task(apply_changes())
            
            logger.info(f"[MCP] Config file updated: {len(changes['added'])} added, {len(changes['removed'])} removed, {len(changes['modified'])} modified")
            
            return {
                'success': True,
                'changes': changes
            }
            
        except Exception as e:
            logger.error(f"Error updating config file: {e}")
            logger.error(f"Stack trace:\n{traceback.format_exc()}")
            raise
    
    def get_config_file_content(self) -> str:
        """Get the raw JSON file content"""
        try:
            config_path = self.get_mcp_config_path()
            if not config_path.exists():
                return json.dumps({'mcpServers': {}}, indent=2)
            
            cursor_data = RobustFileOperations.safe_read_json(config_path, {'mcpServers': {}})
            return json.dumps(cursor_data, indent=2)
        except Exception as e:
            logger.error(f"Error reading config file: {e}")
            return json.dumps({'mcpServers': {}}, indent=2)


class MCPConnection:
    """Base class for MCP connections"""
    
    def __init__(self, server_id: str, config: Dict):
        self.server_id = server_id
        self.config = config
        self.connected = False
    
    async def connect(self):
        """Connect to the MCP server"""
        raise NotImplementedError
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        raise NotImplementedError
    
    async def list_tools(self) -> List[Dict]:
        """List available tools"""
        raise NotImplementedError
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call a tool"""
        raise NotImplementedError
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.connected


class MCPCommandConnection(MCPConnection):
    """Command-based MCP connection using stdio"""
    
    def __init__(self, server_id: str, config: Dict):
        super().__init__(server_id, config)
        self.process = None
        self.request_id = 0
        self._stdout_queue = asyncio.Queue()
        self._stderr_queue = asyncio.Queue()
        self._reader_tasks = []
    
    async def connect(self):
        """Start subprocess and establish stdio connection using subprocess.Popen (Windows-compatible)"""
        try:
            command = self.config.get('command')
            args = self.config.get('args', [])
            env = self.config.get('env', {})
            
            if not command:
                raise ValueError("Command is required for command-based MCP")
            
            # Merge environment variables
            import os
            import shlex
            full_env = os.environ.copy()
            full_env.update(env)
            
            is_windows = platform.system() == 'Windows'
            logger.debug(f"[MCP] Platform: {platform.system()} (Windows={is_windows})")
            logger.debug(f"[MCP] Python version: {sys.version}")
            logger.debug(f"[MCP] Working directory: {os.getcwd()}")
            
            # Build command as a list (works on all platforms, including Windows)
            # This is the proper way to handle subprocess on Windows
            cmd_list = [command] + args
            
            logger.info(f"[MCP] Executing command: {' '.join(cmd_list)}")
            logger.debug(f"[MCP] Command as list: {cmd_list}")
            
            # Log PATH for debugging
            path_var = full_env.get('PATH', '')
            if is_windows:
                # On Windows, also check Path and path (case-insensitive)
                for key in full_env.keys():
                    if key.lower() == 'path':
                        path_var = full_env[key]
                        break
            
            if path_var:
                path_entries = path_var.split(os.pathsep)
                logger.debug(f"[MCP] PATH has {len(path_entries)} entries:")
                for i, entry in enumerate(path_entries[:5]):  # Log first 5 entries
                    logger.debug(f"[MCP]   [{i}] {entry}")
                if len(path_entries) > 5:
                    logger.debug(f"[MCP]   ... and {len(path_entries) - 5} more entries")
            else:
                logger.warning(f"[MCP] PATH environment variable not found!")
            
            # Log custom environment variables (helpful for debugging)
            if env:
                logger.debug(f"[MCP] Custom env vars: {list(env.keys())}")
                for key, value in env.items():
                    # Log first 100 chars of each env var value
                    value_preview = str(value)[:100] + ('...' if len(str(value)) > 100 else '')
                    logger.debug(f"[MCP]   {key}={value_preview}")
            
            # Create subprocess using subprocess.Popen (works on all platforms, all event loops)
            # This is more reliable than asyncio.create_subprocess_* which requires ProactorEventLoop on Windows
            logger.debug(f"[MCP] Creating subprocess using subprocess.Popen (cross-platform compatible)")
            
            try:
                # Use subprocess.Popen which works with any event loop
                self.process = subprocess.Popen(
                    [command] + args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=full_env,
                    # Important: on Windows, don't create a visible console window
                    creationflags=subprocess.CREATE_NO_WINDOW if is_windows else 0
                )
                logger.debug(f"[MCP] Subprocess created with PID: {self.process.pid}")
                
                # Start background tasks to read stdout/stderr asynchronously
                self._start_reader_tasks()
                
            except FileNotFoundError as e:
                error_msg = f"Command not found: {command}. Make sure the executable is in PATH or provide full path."
                logger.error(f"[MCP] {error_msg}")
                logger.error(f"[MCP] FileNotFoundError details: {e}")
                
                # On Windows, try with .exe, .cmd, .bat extensions
                if is_windows and not any(command.endswith(ext) for ext in ['.exe', '.cmd', '.bat']):
                    logger.debug(f"[MCP] Windows: Trying with common executable extensions...")
                    for ext in ['.exe', '.cmd', '.bat']:
                        try:
                            logger.debug(f"[MCP] Trying: {command}{ext}")
                            self.process = subprocess.Popen(
                                [command + ext] + args,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=full_env,
                                creationflags=subprocess.CREATE_NO_WINDOW if is_windows else 0
                            )
                            logger.debug(f"[MCP] Success with {command}{ext}, PID: {self.process.pid}")
                            self._start_reader_tasks()
                            break
                        except FileNotFoundError:
                            continue
                    else:
                        # None of the extensions worked
                        raise RuntimeError(error_msg) from e
                else:
                    raise RuntimeError(error_msg) from e
            except Exception as e:
                error_msg = f"Failed to start subprocess: {type(e).__name__}: {str(e)}"
                logger.error(f"[MCP] {error_msg}")
                logger.error(f"[MCP] Stack trace:\n{traceback.format_exc()}")
                raise RuntimeError(error_msg) from e
            
            # Give the process a moment to start
            await asyncio.sleep(0.5)
            
            # Check if process is still running
            poll_result = self.process.poll()
            if poll_result is not None:
                # Process already exited, try to capture stderr
                stderr_text = "No error output"
                try:
                    # With subprocess.Popen, we need to read synchronously from stderr
                    # But do it in a non-blocking way via a thread
                    loop = asyncio.get_event_loop()
                    stderr_data = await loop.run_in_executor(None, self.process.stderr.read)
                    if stderr_data:
                        stderr_text = stderr_data.decode('utf-8', errors='replace')
                except Exception as e:
                    stderr_text = f"Could not read stderr: {e}"
                
                error_msg = f"MCP server exited immediately with code {poll_result}. Error output: {stderr_text}"
                logger.error(f"[MCP] {error_msg}")
                raise RuntimeError(error_msg)
            
            logger.debug(f"[MCP] Process started successfully, sending initialization request...")
            self.connected = True
            
            # Send initialization request
            try:
                await self._send_request('initialize', {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {},
                    'clientInfo': {
                        'name': 'signalpilot-ai-internal',
                        'version': '0.10.1'
                    }
                })
                logger.debug(f"[MCP] Initialization successful")
            except Exception as e:
                error_msg = f"Failed to initialize MCP protocol: {type(e).__name__}: {str(e)}"
                logger.error(f"[MCP] {error_msg}")
                raise RuntimeError(error_msg) from e
            
        except Exception as e:
            logger.error(f"[MCP] Error starting MCP command: {type(e).__name__}: {str(e)}")
            logger.error(f"[MCP] Full stack trace:\n{traceback.format_exc()}")
            self.connected = False
            
            # Try to capture stderr if process exists
            if self.process and hasattr(self.process, 'stderr') and self.process.stderr:
                try:
                    # Use run_in_executor for sync read
                    loop = asyncio.get_event_loop()
                    stderr_data = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: self.process.stderr.read(4096)),
                        timeout=1.0
                    )
                    if stderr_data:
                        stderr_text = stderr_data.decode('utf-8', errors='replace')
                        logger.error(f"[MCP] Server stderr output:\n{stderr_text}")
                        # Re-raise with stderr included
                        raise RuntimeError(f"{str(e)}\n\nServer error output:\n{stderr_text}") from e
                except asyncio.TimeoutError:
                    logger.warning(f"[MCP] Timeout reading stderr")
                except Exception as stderr_e:
                    logger.warning(f"[MCP] Could not read stderr: {stderr_e}")
            
            raise
    
    def _start_reader_tasks(self):
        """Start background tasks to read from stdout/stderr"""
        loop = asyncio.get_event_loop()
        
        # Start stdout reader
        stdout_task = loop.create_task(self._read_stream(self.process.stdout, self._stdout_queue, 'stdout'))
        stderr_task = loop.create_task(self._read_stream(self.process.stderr, self._stderr_queue, 'stderr'))
        
        self._reader_tasks = [stdout_task, stderr_task]
    
    async def _read_stream(self, stream, queue, name):
        """Read from a stream in a background thread and put lines into a queue"""
        loop = asyncio.get_event_loop()
        try:
            while True:
                # Read line in executor to avoid blocking
                line = await loop.run_in_executor(None, stream.readline)
                if not line:
                    logger.debug(f"[MCP] {name} stream closed")
                    break
                await queue.put(line)
        except Exception as e:
            logger.error(f"[MCP] Error reading {name}: {e}")
    
    async def disconnect(self):
        """Terminate subprocess"""
        if self.process:
            try:
                # Cancel reader tasks
                for task in self._reader_tasks:
                    task.cancel()
                
                # Terminate process
                self.process.terminate()
                
                # Wait for process to exit (with timeout)
                loop = asyncio.get_event_loop()
                try:
                    await asyncio.wait_for(
                        loop.run_in_executor(None, self.process.wait),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"[MCP] Process did not terminate, killing...")
                    self.process.kill()
                    await loop.run_in_executor(None, self.process.wait)
            except Exception as e:
                logger.error(f"[MCP] Error during disconnect: {e}")
            finally:
                self.connected = False
    
    async def list_tools(self) -> List[Dict]:
        """List tools via JSON-RPC"""
        try:
            response = await self._send_request('tools/list', {})
            tools = response.get('result', {}).get('tools', [])
            
            # Convert to standard format
            return [self._convert_tool_schema(tool) for tool in tools]
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call a tool via JSON-RPC"""
        try:
            response = await self._send_request('tools/call', {
                'name': tool_name,
                'arguments': arguments
            })
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise
    
    async def _send_request(self, method: str, params: Dict) -> Dict:
        """Send JSON-RPC request and get response (works with subprocess.Popen)"""
        if not self.process or not self.connected:
            raise RuntimeError("Not connected to MCP server")
        
        # Check if process is still alive
        poll_result = self.process.poll()
        if poll_result is not None:
            # Try to get stderr from queue
            stderr_lines = []
            while not self._stderr_queue.empty():
                try:
                    line = self._stderr_queue.get_nowait()
                    stderr_lines.append(line.decode('utf-8', errors='replace'))
                except:
                    break
            
            stderr_text = ''.join(stderr_lines) if stderr_lines else "No error output available"
            error_msg = f"MCP server process has exited with code {poll_result}. Server output: {stderr_text}"
            logger.error(f"[MCP] {error_msg}")
            raise RuntimeError(error_msg)
        
        self.request_id += 1
        request = {
            'jsonrpc': '2.0',
            'id': self.request_id,
            'method': method,
            'params': params
        }
        
        # Send request to stdin
        request_data = json.dumps(request) + '\n'
        logger.debug(f"[MCP] Sending request: {request_data.strip()}")
        
        try:
            # Write to stdin (synchronously via executor)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.process.stdin.write, request_data.encode())
            await loop.run_in_executor(None, self.process.stdin.flush)
        except Exception as e:
            error_msg = f"Failed to send request to MCP server: {type(e).__name__}: {str(e)}"
            logger.error(f"[MCP] {error_msg}")
            raise RuntimeError(error_msg) from e
        
        # Read response from stdout queue with timeout
        try:
            response_line = await asyncio.wait_for(
                self._stdout_queue.get(),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            # Try to get stderr from queue
            stderr_lines = []
            while not self._stderr_queue.empty():
                try:
                    line = self._stderr_queue.get_nowait()
                    stderr_lines.append(line.decode('utf-8', errors='replace'))
                except:
                    break
            
            stderr_text = ''.join(stderr_lines) if stderr_lines else "No error output"
            error_msg = f"MCP server response timeout after 30 seconds for method '{method}'. Server stderr: {stderr_text}"
            logger.error(f"[MCP] {error_msg}")
            raise RuntimeError(error_msg)
        
        if not response_line:
            # Try to get stderr from queue
            stderr_lines = []
            while not self._stderr_queue.empty():
                try:
                    line = self._stderr_queue.get_nowait()
                    stderr_lines.append(line.decode('utf-8', errors='replace'))
                except:
                    break
            
            stderr_text = ''.join(stderr_lines) if stderr_lines else "No error output"
            error_msg = f"MCP server closed connection. Server stderr: {stderr_text}"
            logger.error(f"[MCP] {error_msg}")
            raise RuntimeError(error_msg)
        
        response_text = response_line.decode('utf-8', errors='replace').strip()
        logger.debug(f"[MCP] Received response: {response_text}")
        
        try:
            response = json.loads(response_text)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse MCP server response as JSON: {e}. Response: {response_text[:200]}"
            logger.error(f"[MCP] {error_msg}")
            raise RuntimeError(error_msg) from e
        
        if 'error' in response:
            error_details = response['error']
            error_msg = f"MCP server error for method '{method}': {json.dumps(error_details, indent=2)}"
            logger.error(f"[MCP] {error_msg}")
            raise RuntimeError(error_msg)
        
        return response
    
    def _convert_tool_schema(self, tool: Dict) -> Dict:
        """Convert MCP tool schema to standard format"""
        return {
            'name': tool.get('name'),
            'description': tool.get('description', ''),
            'inputSchema': tool.get('inputSchema', {
                'type': 'object',
                'properties': {}
            })
        }


class MCPHTTPConnection(MCPConnection):
    """HTTP/SSE-based MCP connection"""
    
    def __init__(self, server_id: str, config: Dict):
        super().__init__(server_id, config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = config.get('url', '').rstrip('/')
    
    async def connect(self):
        """Establish HTTP/SSE connection"""
        try:
            if not self.base_url:
                raise ValueError("URL is required for HTTP/SSE MCP")
            
            # Create session with timeout
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Test connection by listing tools
            await self._request('POST', '/tools/list', {})
            
            self.connected = True
            logger.info(f"Connected to MCP HTTP server: {self.base_url}")
        except Exception as e:
            logger.error(f"Error connecting to MCP HTTP server: {e}")
            if self.session:
                await self.session.close()
            self.connected = False
            raise
    
    async def disconnect(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            self.connected = False
    
    async def list_tools(self) -> List[Dict]:
        """List tools via HTTP"""
        try:
            response = await self._request('POST', '/tools/list', {})
            tools = response.get('tools', [])
            
            return [self._convert_tool_schema(tool) for tool in tools]
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call a tool via HTTP"""
        try:
            response = await self._request('POST', '/tools/call', {
                'name': tool_name,
                'arguments': arguments
            })
            return response
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise
    
    async def _request(self, method: str, path: str, data: Dict) -> Dict:
        """Make HTTP request to MCP server"""
        if not self.session or not self.connected:
            raise RuntimeError("Not connected to MCP server")
        
        url = f"{self.base_url}{path}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add auth token if provided
        token = self.config.get('token')
        if token:
            headers['Authorization'] = f"Bearer {token}"
        
        async with self.session.request(method, url, json=data, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    def _convert_tool_schema(self, tool: Dict) -> Dict:
        """Convert MCP tool schema to standard format"""
        return {
            'name': tool.get('name'),
            'description': tool.get('description', ''),
            'inputSchema': tool.get('inputSchema', {
                'type': 'object',
                'properties': {}
            })
        }


def get_mcp_service() -> MCPConnectionService:
    """Get singleton instance of MCP service"""
    return MCPConnectionService.get_instance()

