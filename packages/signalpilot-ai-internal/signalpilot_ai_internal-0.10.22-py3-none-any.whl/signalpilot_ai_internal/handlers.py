import json
import os
import re
from pathlib import Path
from datetime import datetime

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado

from .cache_service import get_cache_service
from .cache_handlers import ChatHistoriesHandler, AppValuesHandler, CacheInfoHandler
from .unified_database_schema_service import UnifiedDatabaseSchemaHandler, UnifiedDatabaseQueryHandler
from .snowflake_schema_service import SnowflakeSchemaHandler, SnowflakeQueryHandler
from .databricks_schema_service import DatabricksSchemaHandler, DatabricksQueryHandler, DatabricksTestHandler
from .file_scanner_service import get_file_scanner_service
from .schema_search_service import SchemaSearchHandler
from .mcp_handlers import (
    MCPServersHandler,
    MCPServerHandler,
    MCPConnectHandler,
    MCPDisconnectHandler,
    MCPToolsHandler,
    MCPAllToolsHandler,
    MCPToolCallHandler,
    MCPServerEnableHandler,
    MCPServerDisableHandler,
    MCPToolEnableHandler,
    MCPConfigFileHandler
)


class HelloWorldHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": "Hello World from SignalPilot AI backend!",
            "message": "This is a simple hello world endpoint from the sage agent backend."
        }))


class ReadAllFilesHandler(APIHandler):
    """Handler for reading all notebook and data files in the workspace"""
    
    # Common data file extensions
    DATA_EXTENSIONS = {'.csv', '.json', '.xlsx', '.xls', '.parquet', '.pkl', '.pickle', 
                       '.feather', '.hdf5', '.h5', '.sql', '.db', '.sqlite', '.tsv', '.txt'}
    
    # Directories to exclude from search
    EXCLUDE_DIRS = {'.git', '.ipynb_checkpoints', 'node_modules', '__pycache__', 
                    '.venv', 'venv', 'env', '.pytest_cache', '.mypy_cache', 
                    'dist', 'build', '.tox', 'logs', '.vscode'}
    
    @tornado.web.authenticated
    def get(self):
        try:
            # Get the root directory where Jupyter Lab is running
            root_dir = Path(os.getcwd())
            
            # Find all notebook files
            notebooks = self._find_notebooks(root_dir)
            
            # Find all data files
            data_files = self._find_data_files(root_dir)
            
            # Get the 10 most recently edited notebooks
            recent_notebooks = self._get_recent_notebooks(notebooks, limit=10)
            
            # Analyze each notebook for data dependencies
            notebook_info = []
            all_data_dependencies = set()
            for notebook_path in recent_notebooks:
                info = self._analyze_notebook(notebook_path, data_files, root_dir)
                notebook_info.append(info)
                # Collect all data dependencies from recent notebooks
                all_data_dependencies.update(info['data_dependencies'])
            
            # Filter data files to only those referenced by recent notebooks
            referenced_data_files = []
            for data_file in data_files:
                rel_path = str(data_file.relative_to(root_dir))
                rel_path_forward = rel_path.replace('\\', '/')
                file_name = data_file.name
                
                # Check if this data file is referenced in any dependency
                if any(dep in [file_name, rel_path, rel_path_forward] or 
                       file_name in dep or rel_path in dep or rel_path_forward in dep 
                       for dep in all_data_dependencies):
                    referenced_data_files.append(data_file)
            
            # Generate the LLM-optimized context string with only referenced data
            welcome_context = self._generate_welcome_context(notebook_info, referenced_data_files, root_dir)
            
            self.finish(json.dumps({
                "welcome_context": welcome_context,
                "notebook_count": len(notebooks),
                "data_file_count": len(data_files),
                "recent_notebook_count": len(recent_notebooks),
                "referenced_data_count": len(referenced_data_files)
            }))
            
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))
    
    def _find_notebooks(self, root_dir: Path) -> list:
        """Find all .ipynb files in the workspace"""
        notebooks = []
        for path in root_dir.rglob('*.ipynb'):
            # Skip excluded directories
            if any(excluded in path.parts for excluded in self.EXCLUDE_DIRS):
                continue
            notebooks.append(path)
        return notebooks
    
    def _find_data_files(self, root_dir: Path) -> list:
        """Find all data files in the workspace"""
        data_files = []
        for path in root_dir.rglob('*'):
            # Skip excluded directories
            if any(excluded in path.parts for excluded in self.EXCLUDE_DIRS):
                continue
            # Check if file has a data extension
            if path.is_file() and path.suffix.lower() in self.DATA_EXTENSIONS:
                data_files.append(path)
        return data_files
    
    def _get_recent_notebooks(self, notebooks: list, limit: int = 10) -> list:
        """Get the most recently modified notebooks"""
        # Sort by modification time (most recent first)
        notebooks_with_mtime = [(nb, nb.stat().st_mtime) for nb in notebooks]
        notebooks_with_mtime.sort(key=lambda x: x[1], reverse=True)
        
        # Return only the paths, limited to the specified number
        return [nb for nb, _ in notebooks_with_mtime[:limit]]
    
    def _analyze_notebook(self, notebook_path: Path, data_files: list, root_dir: Path) -> dict:
        """Analyze a notebook to find data dependencies"""
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook_content = f.read()
            
            # Find data file references in the notebook
            referenced_data_files = self._find_data_references(notebook_content, data_files, root_dir)
            
            # Get relative path from root
            relative_path = notebook_path.relative_to(root_dir)
            
            # Get last modified time
            mtime = datetime.fromtimestamp(notebook_path.stat().st_mtime)
            
            return {
                'name': notebook_path.name,
                'path': str(relative_path),
                'last_modified': mtime.strftime('%Y-%m-%d %H:%M:%S'),
                'data_dependencies': referenced_data_files
            }
        except Exception as e:
            # If we can't read the notebook, return basic info
            relative_path = notebook_path.relative_to(root_dir)
            return {
                'name': notebook_path.name,
                'path': str(relative_path),
                'last_modified': 'unknown',
                'data_dependencies': [],
                'error': str(e)
            }
    
    def _find_data_references(self, content: str, data_files: list, root_dir: Path) -> list:
        """Find references to data files in notebook content"""
        referenced_files = []
        
        # Create a set of data file names and paths for matching
        data_file_patterns = set()
        for data_file in data_files:
            # Add the filename
            data_file_patterns.add(data_file.name)
            # Add relative path
            try:
                rel_path = str(data_file.relative_to(root_dir))
                data_file_patterns.add(rel_path)
                # Also add with forward slashes (common in code)
                data_file_patterns.add(rel_path.replace('\\', '/'))
            except ValueError:
                pass
        
        # Search for data file references
        # Common patterns: pd.read_csv('file.csv'), open('file.csv'), 'path/to/file.csv'
        patterns = [
            r'["\']([^"\']+\.(?:csv|json|xlsx?|parquet|pkl|pickle|feather|hdf5|h5|sql|db|sqlite|tsv|txt))["\']',
            r'read_(?:csv|json|excel|parquet|pickle|feather|hdf|sql|table)\(["\']([^"\']+)["\']',
            r'to_(?:csv|json|excel|parquet|pickle|feather|hdf|sql)\(["\']([^"\']+)["\']',
        ]
        
        found_references = set()
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                file_ref = match.group(1)
                # Check if this reference matches any of our data files
                if file_ref in data_file_patterns or any(file_ref in str(df) for df in data_files):
                    found_references.add(file_ref)
        
        # Also check for database connection strings
        db_patterns = [
            r'(?:postgresql|mysql|sqlite|mongodb)://[^\s\'"]+',
            r'(?:DATABASE_URL|DB_URL|CONNECTION_STRING)\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in db_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                found_references.add(f"Database: {match.group(0)[:50]}...")
        
        return sorted(list(found_references))
    
    def _generate_welcome_context(self, notebook_info: list, data_files: list, root_dir: Path) -> str:
        """Generate an LLM-optimized, human-readable context string"""
        lines = []
        lines.append("# Workspace Overview\n")
        
        if not notebook_info:
            lines.append("No notebooks found in the workspace.\n")
        else:
            lines.append(f"## Recent Notebooks ({len(notebook_info)})\n")
            
            for i, info in enumerate(notebook_info, 1):
                lines.append(f"\n### {i}. {info['name']}")
                lines.append(f"   - Path: {info['path']}")
                lines.append(f"   - Last Modified: {info['last_modified']}")
                
                if info.get('error'):
                    lines.append(f"   - Note: Could not fully analyze ({info['error']})")
                
                if info['data_dependencies']:
                    lines.append(f"   - Data Dependencies:")
                    for dep in info['data_dependencies']:
                        lines.append(f"     • {dep}")
                else:
                    lines.append(f"   - Data Dependencies: None detected")
        
        # Add summary of data files referenced by recent notebooks
        if data_files:
            lines.append(f"\n## Data Files Referenced by Recent Notebooks ({len(data_files)} total)\n")
            
            # Group by extension
            by_extension = {}
            for df in data_files:
                ext = df.suffix.lower()
                if ext not in by_extension:
                    by_extension[ext] = []
                try:
                    rel_path = str(df.relative_to(root_dir))
                    by_extension[ext].append(rel_path)
                except ValueError:
                    by_extension[ext].append(str(df))
            
            for ext in sorted(by_extension.keys()):
                files = by_extension[ext]
                lines.append(f"\n### {ext} files ({len(files)})")
                # Show all referenced files (they should be limited already)
                for f in sorted(files):
                    lines.append(f"   - {f}")
        else:
            lines.append(f"\n## Data Files Referenced by Recent Notebooks\n")
            lines.append("No data file dependencies found in recent notebooks.\n")
        
        return '\n'.join(lines)


class SelectFolderHandler(APIHandler):
    """Handler to open a native folder picker and return the selected absolute path"""
    
    # Class-level flag to prevent multiple dialogs
    _dialog_open = False

    @tornado.web.authenticated
    def get(self):
        # Check if a dialog is already open
        if SelectFolderHandler._dialog_open:
            self.set_status(409)  # Conflict status
            self.finish(json.dumps({
                "error": "A folder selection dialog is already open"
            }))
            return
            
        try:
            import tkinter as tk
            from tkinter import filedialog
            import threading
            import time

            # Set flag to prevent multiple dialogs
            SelectFolderHandler._dialog_open = True
            
            # Create a fresh tkinter instance
            root = tk.Tk()
            
            # Position the root window in the center of the screen BEFORE withdrawing
            try:
                # Get screen dimensions
                screen_width = root.winfo_screenwidth()
                screen_height = root.winfo_screenheight()
                
                # Calculate center position
                x = (screen_width // 2) - 200  # Dialog is roughly 400px wide
                y = (screen_height // 2) - 150  # Dialog is roughly 300px tall
                
                # Set window position and make it visible briefly for positioning
                root.geometry(f"400x300+{x}+{y}")
                root.update_idletasks()
                
                # Now withdraw the window
                root.withdraw()
                
                # Enhanced topmost settings for better visibility
                root.attributes('-topmost', True)
                root.lift()
                root.focus_force()
                
                # Final positioning update
                root.update_idletasks()
            except Exception:
                # Fallback: just withdraw if positioning fails
                root.withdraw()

            folder = None
            
            try:
                # Show the dialog with proper positioning
                folder = filedialog.askdirectory(
                    parent=root,
                    title="Select Folder",
                    initialdir=os.path.expanduser("~")  # Start in user's home directory
                )
            except Exception as e:
                raise e
            finally:
                # Comprehensive cleanup
                try:
                    # Force close and destroy all tkinter components
                    root.quit()
                    root.destroy()
                    
                    # Additional cleanup for macOS - ensure complete destruction
                    try:
                        root.update_idletasks()
                        root.update()
                        # Force garbage collection of tkinter objects
                        import gc
                        gc.collect()
                    except Exception:
                        pass
                        
                except Exception:
                    pass
                finally:
                    # Reset flag and add small delay to ensure cleanup
                    SelectFolderHandler._dialog_open = False
                    time.sleep(0.1)  # Small delay to ensure cleanup completes

            # Normalize and return absolute path or null
            if folder:
                folder_path = os.path.abspath(folder)
                self.finish(json.dumps({"path": folder_path}))
            else:
                self.finish(json.dumps({"path": None}))
                
        except Exception as e:
            # Reset flag on error
            SelectFolderHandler._dialog_open = False
            self.set_status(400)
            self.finish(json.dumps({
                "error": str(e)
            }))

class FileScanHandler(APIHandler):
    """Handler for scanning directories for files"""
    
    @tornado.web.authenticated
    async def post(self):
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            paths = data.get('paths', [])
            
            if not paths:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No paths provided"
                }))
                return
            
            file_scanner = get_file_scanner_service()
            # Pass the current working directory as the workspace root for relative path calculation
            result = await file_scanner.scan_directories(paths, workspace_root=os.getcwd())
            
            # Update scanned directories tracking
            scanned_dirs = file_scanner.get_scanned_directories()
            current_dirs = scanned_dirs.get('directories', [])
            
            # Update directory metadata
            for new_dir in result['scanned_directories']:
                # Check if directory already exists
                existing_dir = None
                for existing in current_dirs:
                    if existing['path'] == new_dir['path']:
                        existing_dir = existing
                        break
                
                if existing_dir:
                    # Update existing directory
                    existing_dir['file_count'] = new_dir['file_count']
                    existing_dir['scanned_at'] = new_dir['scanned_at']
                else:
                    # Add new directory
                    current_dirs.append(new_dir)
            
            # Save updated directories list
            file_scanner.update_scanned_directories(current_dirs)
            
            self.finish(json.dumps(result))
            
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))


class ScannedDirectoriesHandler(APIHandler):
    """Handler for getting scanned directories list"""
    
    @tornado.web.authenticated
    def get(self):
        try:
            file_scanner = get_file_scanner_service()
            result = file_scanner.get_scanned_directories()
            
            self.finish(json.dumps(result))
            
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))


class WorkDirHandler(APIHandler):
    """Handler for returning current working directory"""

    @tornado.web.authenticated
    def get(self):
        try:
            self.finish(json.dumps({"workdir": os.getcwd()}))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))


class TerminalExecuteHandler(APIHandler):
    """Handler for executing terminal commands"""

    @tornado.web.authenticated
    def post(self):
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            command = data.get('command')

            if not command:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No command provided"
                }))
                return

            import subprocess
            result = subprocess.run(
                command,
                shell=True,
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=300
            )

            def truncate_output(output: str, max_lines: int = 50) -> str:
                if not output:
                    return output
                lines = output.splitlines()
                if len(lines) <= max_lines * 2:
                    return output
                first_lines = lines[:max_lines]
                last_lines = lines[-max_lines:]
                truncated_count = len(lines) - (max_lines * 2)
                return '\n'.join(first_lines + [f'\n... {truncated_count} lines truncated ...\n'] + last_lines)

            self.finish(json.dumps({
                "stdout": truncate_output(result.stdout),
                "stderr": truncate_output(result.stderr),
                "exit_code": result.returncode
            }))

        except subprocess.TimeoutExpired:
            self.set_status(408)
            self.finish(json.dumps({
                "error": "Command timed out after 300 seconds"
            }))
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))


class DeleteScannedDirectoryHandler(APIHandler):
    """Handler for deleting a scanned directory"""
    
    @tornado.web.authenticated
    def post(self):
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            directory_path = data.get('path')
            
            if not directory_path:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No directory path provided"
                }))
                return
            
            file_scanner = get_file_scanner_service()
            
            # Get current scanned directories
            current_directories = file_scanner.get_scanned_directories()
            directories = current_directories.get('directories', [])
            
            # Filter out the directory to be deleted
            filtered_directories = [
                dir_info for dir_info in directories 
                if dir_info.get('path') != directory_path
            ]
            
            # Check if directory was actually found and removed
            if len(filtered_directories) == len(directories):
                self.set_status(404)
                self.finish(json.dumps({
                    "error": f"Directory '{directory_path}' not found in scanned directories"
                }))
                return
            
            # Update the scanned directories list
            success = file_scanner.update_scanned_directories(filtered_directories)
            
            if success:
                self.finish(json.dumps({
                    "success": True,
                    "message": f"Directory '{directory_path}' removed from scanning"
                }))
            else:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": "Failed to update scanned directories"
                }))
            
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))


class NotebookCellsHandler(APIHandler):
    """Handler for reading specific cell ranges from notebooks"""

    @tornado.web.authenticated
    def post(self):
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            file_path = data.get('file_path')
            start_cell = data.get('start_cell', 0)
            end_cell = data.get('end_cell', 5)

            if not file_path:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No file_path provided"
                }))
                return

            file_scanner = get_file_scanner_service()
            result = file_scanner.extract_schema(file_path, start_cell=start_cell, end_cell=end_cell)

            self.finish(json.dumps(result))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))


class NotebookToHTMLHandler(APIHandler):
    """Handler for converting notebooks to HTML using nbconvert"""

    @tornado.web.authenticated
    def post(self):
        try:
            # Parse request body
            try:
                data = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Invalid JSON in request body"
                }))
                return

            # Get notebook path
            notebook_path = data.get('notebook_path')
            if not notebook_path:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No notebook path provided"
                }))
                return

            # Get export options with defaults
            include_input = data.get('include_input', True)
            include_output = data.get('include_output', True)
            include_images = data.get('include_images', True)

            # Convert to nbconvert options
            exclude_input = not include_input
            exclude_output = not include_output

            try:
                # Import nbconvert and nbformat
                from nbconvert import HTMLExporter
                from nbconvert.preprocessors import ExtractOutputPreprocessor
                from nbformat import read

                # Read the notebook file using nbformat
                notebook_file_path = Path(notebook_path)
                if not notebook_file_path.exists():
                    self.set_status(404)
                    self.finish(json.dumps({
                        "error": f"Notebook file not found: {notebook_path}"
                    }))
                    return

                # Load notebook using nbformat.read (more robust)
                with open(notebook_file_path, 'r', encoding='utf-8') as f:
                    notebook_content = read(f, as_version=4)

                # Get the custom template path (relative to this file)
                template_dir = Path(__file__).parent / 'html_export_template'
                template_path = str(template_dir.resolve())

                # Configure the HTML exporter with custom template
                exporter = HTMLExporter(template_name=template_path)

                # Set export options
                exporter.exclude_input = exclude_input
                exporter.exclude_output = exclude_output
                exporter.exclude_input_prompt = True
                exporter.exclude_output_prompt = True

                # Configure image handling
                if not include_images:
                    # Add preprocessor to exclude images
                    exporter.register_preprocessor(ExtractOutputPreprocessor(), enabled=True)

                # Convert notebook to HTML - nbconvert handles everything
                html_content, _ = exporter.from_notebook_node(notebook_content)

                # Get absolute path for the notebook
                workspace_notebook_path = str(notebook_file_path.absolute())

                # Return the HTML content
                self.finish(json.dumps({
                    "success": True,
                    "html_content": html_content,
                    "notebook_path": notebook_path,
                    "workspace_notebook_path": workspace_notebook_path,
                    "export_options": {
                        "include_input": include_input,
                        "include_output": include_output,
                        "include_images": include_images
                    }
                }))

            except ImportError as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": f"Required packages not installed: {str(e)}. Please install them with: pip install nbconvert nbformat"
                }))
            except Exception as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": f"Failed to convert notebook to HTML: {str(e)}"
                }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    
    # Original hello world endpoint
    hello_route = url_path_join(base_url, "signalpilot-ai-internal", "hello-world")
    
    # Read all files endpoint
    read_all_files_route = url_path_join(base_url, "signalpilot-ai-internal", "read-all-files")
    
    # File scanning endpoints
    file_scan_route = url_path_join(base_url, "signalpilot-ai-internal", "files", "scan")
    scanned_directories_route = url_path_join(base_url, "signalpilot-ai-internal", "files", "directories")
    select_folder_route = url_path_join(base_url, "signalpilot-ai-internal", "files", "select-folder")
    workdir_route = url_path_join(base_url, "signalpilot-ai-internal", "files", "workdir")
    delete_scanned_directory_route = url_path_join(base_url, "signalpilot-ai-internal", "files", "directories", "delete")

    # Notebook endpoints
    notebook_cells_route = url_path_join(base_url, "signalpilot-ai-internal", "notebook", "cells")

    # Cache service endpoints
    chat_histories_route = url_path_join(base_url, "signalpilot-ai-internal", "cache", "chat-histories")
    chat_history_route = url_path_join(base_url, "signalpilot-ai-internal", "cache", "chat-histories", "([^/]+)")
    
    app_values_route = url_path_join(base_url, "signalpilot-ai-internal", "cache", "app-values")
    app_value_route = url_path_join(base_url, "signalpilot-ai-internal", "cache", "app-values", "([^/]+)")
    
    cache_info_route = url_path_join(base_url, "signalpilot-ai-internal", "cache", "info")
    
    # Database service endpoints
    database_schema_route = url_path_join(base_url, "signalpilot-ai-internal", "database", "schema")
    database_query_route = url_path_join(base_url, "signalpilot-ai-internal", "database", "query")
    database_schema_search_route = url_path_join(base_url, "signalpilot-ai-internal", "database", "schema-search")
    
    # MySQL service endpoints
    mysql_schema_route = url_path_join(base_url, "signalpilot-ai-internal", "mysql", "schema")
    mysql_query_route = url_path_join(base_url, "signalpilot-ai-internal", "mysql", "query")
    
    # Snowflake service endpoints
    snowflake_schema_route = url_path_join(base_url, "signalpilot-ai-internal", "snowflake", "schema")
    snowflake_query_route = url_path_join(base_url, "signalpilot-ai-internal", "snowflake", "query")

    # Databricks service endpoints
    databricks_schema_route = url_path_join(base_url, "signalpilot-ai-internal", "databricks", "schema")
    databricks_query_route = url_path_join(base_url, "signalpilot-ai-internal", "databricks", "query")
    databricks_test_route = url_path_join(base_url, "signalpilot-ai-internal", "databricks", "test")

    # Notebook HTML export endpoint
    notebook_html_route = url_path_join(base_url, "signalpilot-ai-internal", "notebook", "to-html")

    # Terminal endpoint
    terminal_execute_route = url_path_join(base_url, "signalpilot-ai-internal", "terminal", "execute")
    
    # MCP service endpoints
    mcp_servers_route = url_path_join(base_url, "signalpilot-ai-internal", "mcp", "servers")
    mcp_server_route = url_path_join(base_url, "signalpilot-ai-internal", "mcp", "servers", "([^/]+)")
    mcp_connect_route = url_path_join(base_url, "signalpilot-ai-internal", "mcp", "connect")
    mcp_disconnect_route = url_path_join(base_url, "signalpilot-ai-internal", "mcp", "servers", "([^/]+)", "disconnect")
    mcp_tools_route = url_path_join(base_url, "signalpilot-ai-internal", "mcp", "servers", "([^/]+)", "tools")
    mcp_all_tools_route = url_path_join(base_url, "signalpilot-ai-internal", "mcp", "tools")
    mcp_tool_call_route = url_path_join(base_url, "signalpilot-ai-internal", "mcp", "call-tool")
    mcp_tool_enable_route = url_path_join(base_url, "signalpilot-ai-internal", "mcp", "servers", "([^/]+)", "tools", "([^/]+)")
    mcp_server_enable_route = url_path_join(base_url, "signalpilot-ai-internal", "mcp", "servers", "([^/]+)", "enable")
    mcp_server_disable_route = url_path_join(base_url, "signalpilot-ai-internal", "mcp", "servers", "([^/]+)", "disable")
    mcp_config_file_route = url_path_join(base_url, "signalpilot-ai-internal", "mcp", "config-file")

    handlers = [
        # Original endpoint
        (hello_route, HelloWorldHandler),

        # Read all files endpoint
        (read_all_files_route, ReadAllFilesHandler),

        # File scanning endpoints
        (file_scan_route, FileScanHandler),
        (scanned_directories_route, ScannedDirectoriesHandler),
        (select_folder_route, SelectFolderHandler),
        (workdir_route, WorkDirHandler),
        (delete_scanned_directory_route, DeleteScannedDirectoryHandler),

        # Terminal endpoint
        (terminal_execute_route, TerminalExecuteHandler),

        # Notebook endpoints
        (notebook_cells_route, NotebookCellsHandler),

        # Chat histories endpoints
        (chat_histories_route, ChatHistoriesHandler),
        (chat_history_route, ChatHistoriesHandler),
        
        # App values endpoints
        (app_values_route, AppValuesHandler),
        (app_value_route, AppValuesHandler),
        
        # Cache info endpoint
        (cache_info_route, CacheInfoHandler),
        
        # Database service endpoints (unified for PostgreSQL and MySQL)
        (database_schema_route, UnifiedDatabaseSchemaHandler),
        (database_query_route, UnifiedDatabaseQueryHandler),
        (database_schema_search_route, SchemaSearchHandler),
        
        # MySQL service endpoints (use unified handler)
        (mysql_schema_route, UnifiedDatabaseSchemaHandler),
        (mysql_query_route, UnifiedDatabaseQueryHandler),
        
        # Snowflake service endpoints
        (snowflake_schema_route, SnowflakeSchemaHandler),
        (snowflake_query_route, SnowflakeQueryHandler),

        # Databricks service endpoints
        (databricks_schema_route, DatabricksSchemaHandler),
        (databricks_query_route, DatabricksQueryHandler),
        (databricks_test_route, DatabricksTestHandler),

        # Notebook HTML export endpoint
        (notebook_html_route, NotebookToHTMLHandler),
        
        # MCP service endpoints
        # Note: More specific routes should come before parameterized routes
        (mcp_config_file_route, MCPConfigFileHandler),
        (mcp_servers_route, MCPServersHandler),
        (mcp_server_route, MCPServerHandler),
        (mcp_connect_route, MCPConnectHandler),
        (mcp_disconnect_route, MCPDisconnectHandler),
        (mcp_tools_route, MCPToolsHandler),
        (mcp_all_tools_route, MCPAllToolsHandler),
        (mcp_tool_call_route, MCPToolCallHandler),
        (mcp_tool_enable_route, MCPToolEnableHandler),
        (mcp_server_enable_route, MCPServerEnableHandler),
        (mcp_server_disable_route, MCPServerDisableHandler),
    ]
    
    web_app.add_handlers(host_pattern, handlers)
    
    # Initialize cache service on startup
    cache_service = get_cache_service()
    if cache_service.is_available():
        print(f"SignalPilot AI cache service initialized successfully")
        print(f"Cache directory: {cache_service.cache_dir}")
    else:
        print("WARNING: SignalPilot AI cache service failed to initialize!")
    
    # Register cleanup handler for MCP servers on shutdown
    from .mcp_server_manager import get_mcp_server_manager
    
    def cleanup_mcp_servers():
        """Stop all MCP servers on shutdown"""
        manager = get_mcp_server_manager()
        manager.stop_all_servers()
    
    # Register cleanup with web app
    import atexit
    atexit.register(cleanup_mcp_servers)
    
    print("SignalPilot AI backend handlers registered:")
    print(f"  - Hello World: {hello_route}")
    print(f"  - Read All Files: {read_all_files_route}")
    print(f"  - Chat Histories: {chat_histories_route}")
    print(f"  - Chat History (by ID): {chat_history_route}")
    print(f"  - App Values: {app_values_route}")
    print(f"  - App Value (by key): {app_value_route}")
    print(f"  - Cache Info: {cache_info_route}")
    print(f"  - Database Schema: {database_schema_route}")
    print(f"  - Database Query: {database_query_route}")
    print(f"  - Database Schema Search: {database_schema_search_route}")
    print(f"  - MySQL Schema: {mysql_schema_route}")
    print(f"  - MySQL Query: {mysql_query_route}")
    print(f"  - Snowflake Schema: {snowflake_schema_route}")
    print(f"  - Snowflake Query: {snowflake_query_route}")
    print(f"  - Databricks Schema: {databricks_schema_route}")
    print(f"  - Databricks Query: {databricks_query_route}")
    print(f"  - Databricks Test: {databricks_test_route}")
    print(f"  - Notebook Cells: {notebook_cells_route}")
    print(f"  - Notebook to HTML: {notebook_html_route}")
    print(f"  - MCP Servers: {mcp_servers_route}")
    print(f"  - MCP Connect: {mcp_connect_route}")
    print(f"  - MCP Tools: {mcp_all_tools_route}")
    print(f"  - MCP Tool Call: {mcp_tool_call_route}")
