"""
MCP Server Manager

Handles automatic startup and management of MCP servers (like dbt-mcp) when SignalPilot AI starts.
"""
import subprocess
import sys
import os
import logging
from pathlib import Path
from typing import Optional, Dict, List
import atexit

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manages MCP server processes"""
    
    def __init__(self):
        self._processes: Dict[str, subprocess.Popen] = {}
        self._server_configs: List[Dict] = []
        
        # Register cleanup on exit
        atexit.register(self.stop_all_servers)
    
    def add_server_config(self, name: str, command: List[str], cwd: Optional[str] = None, 
                         env: Optional[Dict[str, str]] = None, transport: str = "stdio"):
        """
        Add an MCP server configuration
        
        Args:
            name: Server identifier
            command: Command to start the server (as list)
            cwd: Working directory for the server process
            env: Environment variables for the server
            transport: MCP transport type (stdio, sse, etc.)
        """
        config = {
            'name': name,
            'command': command,
            'cwd': cwd,
            'env': env or {},
            'transport': transport
        }
        self._server_configs.append(config)
        logger.info(f"Added MCP server config: {name}")
    
    def start_server(self, name: str) -> bool:
        """
        Start a specific MCP server
        
        Args:
            name: Server identifier
            
        Returns:
            True if server started successfully, False otherwise
        """
        # Find the server config
        config = None
        for cfg in self._server_configs:
            if cfg['name'] == name:
                config = cfg
                break
        
        if not config:
            logger.error(f"No configuration found for server: {name}")
            return False
        
        # Check if already running
        if name in self._processes:
            if self._processes[name].poll() is None:
                logger.info(f"MCP server '{name}' is already running")
                return True
            else:
                # Process ended, remove it
                del self._processes[name]
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(config['env'])
            env['MCP_TRANSPORT'] = config['transport']
            
            # Start the process
            logger.info(f"Starting MCP server '{name}' with command: {' '.join(config['command'])}")
            process = subprocess.Popen(
                config['command'],
                cwd=config['cwd'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                bufsize=0  # Unbuffered for stdio transport
            )
            
            self._processes[name] = process
            logger.info(f"MCP server '{name}' started with PID: {process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MCP server '{name}': {e}")
            return False
    
    def start_all_servers(self) -> Dict[str, bool]:
        """
        Start all configured MCP servers
        
        Returns:
            Dictionary mapping server names to start success status
        """
        results = {}
        for config in self._server_configs:
            name = config['name']
            results[name] = self.start_server(name)
        return results
    
    def stop_server(self, name: str) -> bool:
        """
        Stop a specific MCP server
        
        Args:
            name: Server identifier
            
        Returns:
            True if server stopped successfully, False otherwise
        """
        if name not in self._processes:
            logger.warning(f"MCP server '{name}' is not running")
            return False
        
        try:
            process = self._processes[name]
            
            # Try graceful termination first
            process.terminate()
            
            try:
                process.wait(timeout=5)
                logger.info(f"MCP server '{name}' terminated gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                process.kill()
                process.wait()
                logger.warning(f"MCP server '{name}' was force killed")
            
            del self._processes[name]
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop MCP server '{name}': {e}")
            return False
    
    def stop_all_servers(self):
        """Stop all running MCP servers"""
        server_names = list(self._processes.keys())
        for name in server_names:
            self.stop_server(name)
    
    def get_server_status(self, name: str) -> Optional[str]:
        """
        Get the status of a specific server
        
        Args:
            name: Server identifier
            
        Returns:
            'running', 'stopped', or None if not configured
        """
        # Check if configured
        if not any(cfg['name'] == name for cfg in self._server_configs):
            return None
        
        if name not in self._processes:
            return 'stopped'
        
        if self._processes[name].poll() is None:
            return 'running'
        else:
            return 'stopped'
    
    def get_all_server_status(self) -> Dict[str, str]:
        """
        Get status of all configured servers
        
        Returns:
            Dictionary mapping server names to their status
        """
        status = {}
        for config in self._server_configs:
            name = config['name']
            status[name] = self.get_server_status(name)
        return status
    
    def get_server_logs(self, name: str, num_lines: int = 50) -> Dict[str, str]:
        """
        Get recent stdout/stderr logs from a server
        
        Args:
            name: Server identifier
            num_lines: Number of recent lines to retrieve (approximate)
            
        Returns:
            Dictionary with 'stdout' and 'stderr' keys containing log output
        """
        if name not in self._processes:
            return {"stdout": "", "stderr": "", "error": "Server not running"}
        
        process = self._processes[name]
        logs = {"stdout": "", "stderr": ""}
        
        try:
            # Try to read from stdout (non-blocking)
            import select
            import sys
            
            if process.stdout and hasattr(select, 'select'):
                # Unix-like systems
                if select.select([process.stdout], [], [], 0)[0]:
                    logs["stdout"] = process.stdout.read(4096).decode('utf-8', errors='ignore')
            elif process.stdout:
                # Windows fallback - attempt read
                try:
                    logs["stdout"] = process.stdout.read(4096).decode('utf-8', errors='ignore')
                except:
                    logs["stdout"] = "(Unable to read stdout on Windows - pipe may be blocking)"
            
            if process.stderr and hasattr(select, 'select'):
                if select.select([process.stderr], [], [], 0)[0]:
                    logs["stderr"] = process.stderr.read(4096).decode('utf-8', errors='ignore')
            elif process.stderr:
                try:
                    logs["stderr"] = process.stderr.read(4096).decode('utf-8', errors='ignore')
                except:
                    logs["stderr"] = "(Unable to read stderr on Windows - pipe may be blocking)"
                    
        except Exception as e:
            logs["error"] = f"Error reading logs: {e}"
        
        return logs


# Global instance
_mcp_server_manager: Optional[MCPServerManager] = None


def get_mcp_server_manager() -> MCPServerManager:
    """Get the global MCP server manager instance"""
    global _mcp_server_manager
    if _mcp_server_manager is None:
        _mcp_server_manager = MCPServerManager()
    return _mcp_server_manager


def configure_default_servers():
    """Configure default MCP servers for SignalPilot AI"""
    manager = get_mcp_server_manager()
    
    # Configure dbt-mcp server
    signalpilot_ai_internal_dir = Path(__file__).parent
    dbt_mcp_dir = signalpilot_ai_internal_dir / "dbt-mcp"
    
    if dbt_mcp_dir.exists():
        # Use the Python executable that's running this process
        python_executable = sys.executable
        
        # Command to run dbt-mcp using the main module
        dbt_mcp_command = [
            python_executable,
            "-m",
            "dbt_mcp.main"
        ]
        
        manager.add_server_config(
            name="dbt-mcp",
            command=dbt_mcp_command,
            cwd=str(dbt_mcp_dir),
            env={},
            transport="stdio"
        )
        logger.info(f"Configured dbt-mcp server at {dbt_mcp_dir}")
    else:
        logger.warning(f"dbt-mcp directory not found at {dbt_mcp_dir}")


def autostart_mcp_servers():
    """Automatically start all configured MCP servers"""
    configure_default_servers()
    manager = get_mcp_server_manager()
    results = manager.start_all_servers()
    
    for name, success in results.items():
        if success:
            logger.info(f"✓ MCP server '{name}' started successfully")
        else:
            logger.error(f"✗ MCP server '{name}' failed to start")
    
    return results
