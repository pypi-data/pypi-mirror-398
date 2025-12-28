"""
Databricks schema service handlers for SignalPilot AI.
Provides REST API handlers for Databricks SQL Warehouse schema retrieval and query execution.

Supports two authentication methods:
- Personal Access Token (PAT): User pastes token directly
- Service Principal: OAuth client credentials flow with automatic token refresh

Uses Unity Catalog with 3-level namespace: catalog.schema.table
"""

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import threading

from jupyter_server.base.handlers import APIHandler
import tornado


# In-memory token cache for Service Principal OAuth tokens
# Key: connection_id or hash of client credentials
# Value: {"access_token": str, "expires_at": float}
_sp_token_cache: Dict[str, Dict[str, Any]] = {}


class DatabricksSchemaHandler(APIHandler):
    """Handler for Databricks schema operations"""

    def _setup_databricks_environment(self):
        """Install required Databricks packages if not available"""
        def install_package(package_name):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                return True
            except subprocess.CalledProcessError:
                return False

        missing_packages = []

        try:
            from databricks import sql as databricks_sql
        except ImportError:
            if install_package("databricks-sql-connector"):
                try:
                    from databricks import sql as databricks_sql
                except ImportError as e:
                    missing_packages.append(f"databricks-sql-connector: {str(e)}")
            else:
                missing_packages.append("databricks-sql-connector: installation failed")

        if missing_packages:
            raise ImportError("Required modules could not be installed: " + ", ".join(missing_packages))

        from databricks import sql as databricks_sql
        return databricks_sql

    def _get_databricks_config(self, provided_config: Optional[Dict] = None) -> Optional[Dict]:
        """Get Databricks configuration from request or environment variables"""
        if provided_config:
            return provided_config

        # Look for Databricks database configuration in the environment
        for key, value in os.environ.items():
            if key.endswith('_CONNECTION_JSON'):
                try:
                    config = json.loads(value)
                    if config.get('type') == 'databricks':
                        return config
                except Exception as e:
                    print(f"[DatabricksSchemaHandler] Error parsing database config {key}: {e}")
                    continue

        return None

    def _get_access_token(self, config: Dict) -> str:
        """Get access token for authentication.

        For PAT: returns the token directly
        For Service Principal: obtains OAuth token via client credentials flow
        """
        auth_type = config.get('authType', 'pat')

        if auth_type == 'pat':
            # Personal Access Token - use directly
            token = config.get('accessToken')
            if not token:
                raise ValueError("Personal Access Token is required for PAT authentication")
            return token

        elif auth_type == 'service_principal':
            # Service Principal - OAuth client credentials flow
            return self._get_sp_access_token(config)

        else:
            raise ValueError(f"Unknown authentication type: {auth_type}")

    def _get_sp_access_token(self, config: Dict) -> str:
        """Get access token via Service Principal OAuth client credentials flow."""
        client_id = config.get('clientId')
        client_secret = config.get('clientSecret')

        if not client_id or not client_secret:
            raise ValueError("Client ID and Client Secret are required for Service Principal authentication")

        # Create cache key from client credentials
        cache_key = f"{client_id}:{hash(client_secret)}"

        # Check cache for valid token
        cached = _sp_token_cache.get(cache_key)
        if cached:
            # Refresh if within 60 seconds of expiry
            if cached.get('expires_at', 0) > time.time() + 60:
                return cached['access_token']

        # Get OAuth token URL
        # Default to Azure AD endpoint if not specified
        token_url = config.get('oauthTokenUrl')
        if not token_url:
            # Try to derive from workspace URL for Azure
            workspace_url = config.get('connectionUrl', '')
            if 'azuredatabricks.net' in workspace_url:
                # Azure Databricks - use Azure AD
                tenant_id = config.get('tenantId', 'common')
                token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            else:
                # AWS/GCP - use Databricks OAuth endpoint
                # Extract host from workspace URL
                import re
                match = re.match(r'https?://([^/]+)', workspace_url)
                if match:
                    host = match.group(1)
                    token_url = f"https://{host}/oidc/v1/token"
                else:
                    raise ValueError("Cannot determine OAuth token URL. Please provide oauthTokenUrl in config.")

        # Request new token
        import urllib.request
        import urllib.parse

        # Prepare token request
        scopes = config.get('scopes', ['2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default'])
        if isinstance(scopes, str):
            scopes = [scopes]

        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': ' '.join(scopes)
        }

        encoded_data = urllib.parse.urlencode(data).encode('utf-8')

        req = urllib.request.Request(
            token_url,
            data=encoded_data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))

                access_token = result.get('access_token')
                expires_in = result.get('expires_in', 3600)

                if not access_token:
                    raise ValueError("No access_token in OAuth response")

                # Cache the token
                _sp_token_cache[cache_key] = {
                    'access_token': access_token,
                    'expires_at': time.time() + expires_in
                }

                return access_token

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            raise ValueError(f"OAuth token request failed: {e.code} - {error_body}")
        except Exception as e:
            raise ValueError(f"Failed to obtain OAuth token: {str(e)}")

    def _get_connection_params(self, config: Dict) -> Dict[str, Any]:
        """Build Databricks connection parameters from configuration"""
        import re

        # Extract host from connectionUrl
        connection_url = config.get('connectionUrl', '')
        if not connection_url:
            raise ValueError("connectionUrl (workspace URL) is required for Databricks")

        # Extract host from URL
        url_match = re.match(r'https?://([^/]+)', connection_url)
        if not url_match:
            raise ValueError(f"Invalid Databricks connectionUrl format: {connection_url}")

        server_hostname = url_match.group(1)

        # Get HTTP path for SQL warehouse
        http_path = config.get('warehouseHttpPath') or config.get('httpPath')
        if not http_path:
            warehouse_id = config.get('warehouseId')
            if warehouse_id:
                http_path = f"/sql/1.0/warehouses/{warehouse_id}"
            else:
                raise ValueError("Either warehouseHttpPath or warehouseId is required")

        # Get access token
        access_token = self._get_access_token(config)

        conn_params = {
            'server_hostname': server_hostname,
            'http_path': http_path,
            'access_token': access_token,
        }

        # Optional catalog (Unity Catalog)
        catalog = config.get('catalog')
        if catalog:
            conn_params['catalog'] = catalog

        # Optional schema
        schema = config.get('schema')
        if schema:
            conn_params['schema'] = schema

        return conn_params

    def _list_catalogs(self, cursor) -> List[str]:
        """List all accessible catalogs"""
        cursor.execute("SHOW CATALOGS")
        rows = cursor.fetchall()
        return [row[0] for row in rows if row[0] not in ('system', 'samples')]

    def _list_schemas(self, cursor, catalog: str) -> List[str]:
        """List all schemas in a catalog"""
        cursor.execute(f"SHOW SCHEMAS IN `{catalog}`")
        rows = cursor.fetchall()
        return [row[0] for row in rows if row[0] not in ('information_schema',)]

    def _list_tables(self, cursor, catalog: str, schema: str) -> List[Dict]:
        """List all tables in a schema with their type"""
        cursor.execute(f"SHOW TABLES IN `{catalog}`.`{schema}`")
        rows = cursor.fetchall()
        tables = []
        for row in rows:
            # SHOW TABLES returns: database, tableName, isTemporary
            table_name = row[1] if len(row) > 1 else row[0]
            tables.append({
                'table_name': table_name,
                'table_type': 'TABLE'
            })
        return tables

    def _get_table_columns(self, cursor, catalog: str, schema: str, table: str) -> List[Dict]:
        """Get column information for a table"""
        try:
            cursor.execute(f"DESCRIBE TABLE `{catalog}`.`{schema}`.`{table}`")
            rows = cursor.fetchall()
            columns = []
            for row in rows:
                # DESCRIBE TABLE returns: col_name, data_type, comment
                col_name = row[0]

                # Skip metadata rows (partition info, etc.)
                if col_name.startswith('#') or not col_name.strip():
                    continue

                columns.append({
                    'column_name': col_name,
                    'data_type': row[1] if len(row) > 1 else 'unknown',
                    'is_nullable': 'YES',  # Databricks doesn't always expose this
                    'column_default': None,
                    'description': row[2] if len(row) > 2 and row[2] else None
                })
            return columns
        except Exception as e:
            print(f"[DatabricksSchemaHandler] Error getting columns for {catalog}.{schema}.{table}: {e}")
            return []

    def _fetch_table_with_columns(self, databricks_sql, conn_params: Dict, catalog: str, schema: str, table_info: Dict) -> Dict:
        """Fetch a single table with its columns using a new connection (for parallel execution)"""
        connection = None
        try:
            connection = databricks_sql.connect(**conn_params)
            cursor = connection.cursor()
            
            table_name = table_info['table_name']
            columns = self._get_table_columns(cursor, catalog, schema, table_name)
            
            cursor.close()
            
            return {
                'catalog': catalog,
                'schema': schema,
                'table': table_name,
                'type': table_info.get('table_type', 'TABLE'),
                'columns': columns,
                'error': None
            }
        except Exception as e:
            print(f"[DatabricksSchemaHandler] Error fetching table {catalog}.{schema}.{table_info.get('table_name', 'unknown')}: {e}")
            return {
                'catalog': catalog,
                'schema': schema,
                'table': table_info.get('table_name', 'unknown'),
                'type': table_info.get('table_type', 'TABLE'),
                'columns': [],
                'error': str(e)
            }
        finally:
            if connection:
                try:
                    connection.close()
                except:
                    pass

    def _fetch_schema_tables(self, databricks_sql, conn_params: Dict, catalog: str, schema: str) -> Dict:
        """Fetch all tables for a schema with parallel column fetching"""
        connection = None
        try:
            # Get list of tables first
            connection = databricks_sql.connect(**conn_params)
            cursor = connection.cursor()
            
            tables = self._list_tables(cursor, catalog, schema)
            cursor.close()
            connection.close()
            connection = None
            
            print(f"      Schema {schema}: {len(tables)} tables - fetching in parallel...")
            
            # Fetch table details in parallel
            schema_obj = {
                'schema': schema,
                'tables': [],
                'error': None
            }
            
            if not tables:
                return schema_obj
            
            # Use ThreadPoolExecutor for parallel table fetching
            max_workers = min(10, len(tables))  # Limit concurrent connections
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_table = {
                    executor.submit(
                        self._fetch_table_with_columns,
                        databricks_sql,
                        conn_params,
                        catalog,
                        schema,
                        table_info
                    ): table_info for table_info in tables
                }
                
                for future in as_completed(future_to_table):
                    try:
                        table_obj = future.result()
                        schema_obj['tables'].append(table_obj)
                    except Exception as e:
                        table_info = future_to_table[future]
                        print(f"        Error processing table {table_info.get('table_name')}: {e}")
            
            return schema_obj
            
        except Exception as e:
            print(f"      Error processing schema {schema}: {e}")
            return {
                'schema': schema,
                'tables': [],
                'error': str(e)
            }
        finally:
            if connection:
                try:
                    connection.close()
                except:
                    pass

    def _build_catalog(self, databricks_sql, conn_params: Dict, specified_catalog: Optional[str] = None, specified_schema: Optional[str] = None) -> Dict:
        """Build complete catalog structure with parallel processing"""
        connection = databricks_sql.connect(**conn_params)
        cursor = connection.cursor()

        try:
            catalog_data = []

            # Get catalogs to process
            if specified_catalog:
                catalogs = [specified_catalog]
            else:
                catalogs = self._list_catalogs(cursor)

            print(f"[DatabricksSchemaHandler] Processing {len(catalogs)} catalogs with parallel optimization...")

            for catalog in catalogs:
                print(f"  Processing catalog: {catalog}")
                catalog_obj = {
                    'catalog': catalog,
                    'schemas': []
                }

                try:
                    schemas_list = self._list_schemas(cursor, catalog)
                    
                    # Filter schemas if specified_schema is provided
                    if specified_schema:
                        schemas = [s for s in schemas_list if s == specified_schema]
                    else:
                        schemas = schemas_list
                    
                    print(f"    Found {len(schemas)} schemas - processing in parallel...")

                    if not schemas:
                        catalog_data.append(catalog_obj)
                        continue

                    # Process schemas in parallel
                    max_workers = min(5, len(schemas))  # Limit concurrent schema processing
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        future_to_schema = {
                            executor.submit(
                                self._fetch_schema_tables,
                                databricks_sql,
                                conn_params,
                                catalog,
                                schema
                            ): schema for schema in schemas
                        }
                        
                        for future in as_completed(future_to_schema):
                            try:
                                schema_obj = future.result()
                                catalog_obj['schemas'].append(schema_obj)
                            except Exception as e:
                                schema = future_to_schema[future]
                                print(f"      Error processing schema {schema}: {e}")
                                catalog_obj['schemas'].append({
                                    'schema': schema,
                                    'tables': [],
                                    'error': str(e)
                                })

                except Exception as e:
                    print(f"    Error processing catalog {catalog}: {e}")
                    catalog_obj['schemas'].append({
                        'schema': 'default',
                        'tables': [],
                        'error': str(e)
                    })

                catalog_data.append(catalog_obj)

            return {'catalogs': catalog_data}

        finally:
            cursor.close()
            connection.close()

    def _format_catalog_as_markdown(self, catalog_data: Dict) -> Tuple[str, Dict]:
        """Format the catalog as markdown and build table_schemas dict"""
        lines = ["# Databricks Database Schema\n"]
        table_schemas = {}

        total_tables = 0
        for cat in catalog_data.get('catalogs', []):
            for sch in cat.get('schemas', []):
                total_tables += len(sch.get('tables', []))

        lines.append(f"Found **{total_tables}** table(s)\n")

        for cat in catalog_data.get('catalogs', []):
            catalog_name = cat['catalog']

            for sch in cat.get('schemas', []):
                schema_name = sch['schema']

                if sch.get('error'):
                    lines.append(f"\n## {catalog_name}.{schema_name}\n")
                    lines.append(f"Error: {sch['error']}\n")
                    continue

                for table in sch.get('tables', []):
                    table_name = table['table']
                    full_name = f"{catalog_name}.{schema_name}.{table_name}"

                    lines.append(f"\n## {full_name}\n")

                    columns = table.get('columns', [])
                    lines.append(f"\n### Columns ({len(columns)})\n")

                    for col in columns:
                        col_name = col.get('column_name', 'unknown')
                        data_type = col.get('data_type', 'unknown')
                        description = col.get('description')

                        if description:
                            lines.append(f"- **{col_name}**: {data_type} - {description}\n")
                        else:
                            lines.append(f"- **{col_name}**: {data_type}\n")

                    # Store in table_schemas
                    table_schemas[full_name] = {
                        'catalog': catalog_name,
                        'schema': schema_name,
                        'table_name': table_name,
                        'full_name': full_name,
                        'columns': [dict(col) for col in columns],
                        'primary_keys': [],  # Databricks doesn't always expose PK info
                        'foreign_keys': [],
                        'indices': []
                    }

                    lines.append("\n---\n")

        return ''.join(lines).strip(), table_schemas

    @tornado.web.authenticated
    def post(self):
        """Get Databricks database schema information"""
        try:
            # Parse request body
            try:
                body = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Invalid JSON in request body"
                }))
                return

            # Get Databricks configuration from request or environment
            config = self._get_databricks_config(body.get('config'))

            if not config:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No Databricks configuration provided and no Databricks configurations found in environment"
                }))
                return

            # Setup Databricks environment
            try:
                databricks_sql = self._setup_databricks_environment()
            except ImportError as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": str(e)
                }))
                return

            # Get database schema
            try:
                conn_params = self._get_connection_params(config)
                specified_catalog = config.get('catalog')
                specified_schema = config.get('schema')

                print(f"[DatabricksSchemaHandler] Connecting to {conn_params['server_hostname']}")
                if specified_catalog:
                    print(f"[DatabricksSchemaHandler] Filtering to catalog: {specified_catalog}")
                if specified_schema:
                    print(f"[DatabricksSchemaHandler] Filtering to schema: {specified_schema}")

                catalog_data = self._build_catalog(
                    databricks_sql,
                    conn_params,
                    specified_catalog=specified_catalog,
                    specified_schema=specified_schema
                )

                markdown_result, table_schemas = self._format_catalog_as_markdown(catalog_data)

                self.finish(json.dumps({
                    "result": markdown_result,
                    "table_schemas": table_schemas,
                    "catalogs": catalog_data.get('catalogs', [])
                }))

            except Exception as e:
                error_msg = str(e)
                # Provide helpful error messages
                if 'PAT' in error_msg.upper() or 'token' in error_msg.lower():
                    error_msg = f"Authentication failed: {error_msg}. If PATs are disabled in your workspace, try Service Principal authentication."
                elif 'warehouse' in error_msg.lower():
                    error_msg = f"SQL Warehouse error: {error_msg}. Ensure your warehouse is running and accessible."

                self.set_status(500)
                self.finish(json.dumps({
                    "error": f"Error connecting to Databricks: {error_msg}"
                }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class DatabricksQueryHandler(APIHandler):
    """Handler for Databricks query execution"""

    def _setup_databricks_environment(self):
        """Install required Databricks packages if not available"""
        def install_package(package_name):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                return True
            except subprocess.CalledProcessError:
                return False

        missing_packages = []

        try:
            from databricks import sql as databricks_sql
        except ImportError:
            if install_package("databricks-sql-connector"):
                try:
                    from databricks import sql as databricks_sql
                except ImportError as e:
                    missing_packages.append(f"databricks-sql-connector: {str(e)}")
            else:
                missing_packages.append("databricks-sql-connector: installation failed")

        if missing_packages:
            raise ImportError("Required modules could not be installed: " + ", ".join(missing_packages))

        from databricks import sql as databricks_sql
        return databricks_sql

    def _get_databricks_config(self, provided_config: Optional[Dict] = None) -> Optional[Dict]:
        """Get Databricks configuration from request or environment variables"""
        if provided_config:
            return provided_config

        # Look for Databricks database configuration in the environment
        for key, value in os.environ.items():
            if key.endswith('_CONNECTION_JSON'):
                try:
                    config = json.loads(value)
                    if config.get('type') == 'databricks':
                        return config
                except Exception as e:
                    print(f"[DatabricksQueryHandler] Error parsing database config {key}: {e}")
                    continue

        return None

    def _get_access_token(self, config: Dict) -> str:
        """Get access token for authentication - delegates to schema handler logic"""
        # Reuse the schema handler's token logic
        handler = DatabricksSchemaHandler(self.application, self.request)
        return handler._get_access_token(config)

    def _get_connection_params(self, config: Dict) -> Dict[str, Any]:
        """Build Databricks connection parameters from configuration"""
        import re

        connection_url = config.get('connectionUrl', '')
        if not connection_url:
            raise ValueError("connectionUrl (workspace URL) is required for Databricks")

        url_match = re.match(r'https?://([^/]+)', connection_url)
        if not url_match:
            raise ValueError(f"Invalid Databricks connectionUrl format: {connection_url}")

        server_hostname = url_match.group(1)

        http_path = config.get('warehouseHttpPath') or config.get('httpPath')
        if not http_path:
            warehouse_id = config.get('warehouseId')
            if warehouse_id:
                http_path = f"/sql/1.0/warehouses/{warehouse_id}"
            else:
                raise ValueError("Either warehouseHttpPath or warehouseId is required")

        access_token = self._get_access_token(config)

        conn_params = {
            'server_hostname': server_hostname,
            'http_path': http_path,
            'access_token': access_token,
        }

        catalog = config.get('catalog')
        if catalog:
            conn_params['catalog'] = catalog

        schema = config.get('schema')
        if schema:
            conn_params['schema'] = schema

        return conn_params

    @tornado.web.authenticated
    def post(self):
        """Execute a read-only SQL query on Databricks"""
        try:
            # Parse request body
            try:
                body = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Invalid JSON in request body"
                }))
                return

            # Get query from request
            query = body.get('query')
            if not query:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Missing 'query' field in request body"
                }))
                return

            # Basic validation for read-only queries
            normalized_query = query.strip().upper()
            allowed_starts = ['SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'EXPLAIN']

            if not any(normalized_query.startswith(start) for start in allowed_starts):
                self.set_status(400)
                self.finish(json.dumps({
                    "error": f"Only {', '.join(allowed_starts)} statements are allowed for read queries."
                }))
                return

            # Get Databricks configuration from request or environment
            config = self._get_databricks_config(body.get('config'))

            if not config:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No Databricks configuration provided and no Databricks configurations found in environment"
                }))
                return

            # Setup Databricks environment
            try:
                databricks_sql = self._setup_databricks_environment()
            except ImportError as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": str(e)
                }))
                return

            # Execute query
            try:
                conn_params = self._get_connection_params(config)

                # Allow specifying a specific catalog for the query
                catalog = body.get('catalog')
                if catalog:
                    conn_params['catalog'] = catalog

                connection = databricks_sql.connect(**conn_params)
                cursor = connection.cursor()

                try:
                    cursor.execute(query)

                    # Get column names from cursor description
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []

                    # Fetch all results
                    rows = cursor.fetchall()

                    # Convert result to list of dictionaries
                    result_rows = [
                        {columns[i]: row[i] for i in range(len(columns))}
                        for row in rows
                    ]

                    self.finish(json.dumps({
                        "result": result_rows
                    }))

                finally:
                    cursor.close()
                    connection.close()

            except Exception as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": f"Databricks query failed: {str(e)}"
                }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class DatabricksTestHandler(APIHandler):
    """Handler for testing Databricks connection"""

    @tornado.web.authenticated
    def post(self):
        """Test Databricks connection and return status"""
        try:
            # Parse request body
            try:
                body = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Invalid JSON in request body"
                }))
                return

            config = body.get('config')
            if not config:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No configuration provided"
                }))
                return

            # Setup environment
            schema_handler = DatabricksSchemaHandler(self.application, self.request)
            try:
                databricks_sql = schema_handler._setup_databricks_environment()
            except ImportError as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "ok": False,
                    "error": str(e)
                }))
                return

            # Test connection
            try:
                import time
                start_time = time.time()

                conn_params = schema_handler._get_connection_params(config)
                connection = databricks_sql.connect(**conn_params)
                cursor = connection.cursor()

                try:
                    # Test basic query
                    cursor.execute("SELECT 1 as test")
                    cursor.fetchall()

                    sql_latency = int((time.time() - start_time) * 1000)

                    # Try to get current user
                    identity_info = {"type": "unknown", "name": "unknown"}
                    try:
                        cursor.execute("SELECT current_user() as user")
                        user_row = cursor.fetchone()
                        if user_row:
                            auth_type = config.get('authType', 'pat')
                            identity_info = {
                                "type": "user" if auth_type == 'pat' else "service_principal",
                                "name": user_row[0]
                            }
                    except Exception:
                        pass

                    self.finish(json.dumps({
                        "ok": True,
                        "identity": identity_info,
                        "sql": {"ok": True, "latency_ms": sql_latency},
                        "api": {"ok": True}
                    }))

                finally:
                    cursor.close()
                    connection.close()

            except Exception as e:
                error_msg = str(e)
                self.finish(json.dumps({
                    "ok": False,
                    "error": error_msg,
                    "identity": None,
                    "sql": {"ok": False, "error": error_msg},
                    "api": {"ok": False}
                }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "ok": False,
                "error": "Internal server error",
                "message": str(e)
            }))
