"""
Snowflake schema service handlers for SignalPilot AI.
Provides REST API handlers for Snowflake database schema retrieval and query execution.
Supports multiple databases within a single Snowflake connection.

Behavior:
- If a warehouse is specified in the config, it will be used directly.
- Otherwise, picks the smallest RUNNING warehouse.
- If none running, resumes the smallest SUSPENDED warehouse.
- If none exist, attempts to CREATE a tiny warehouse (requires privilege).
- If a database is specified in the config, only that database will be processed.
- Otherwise, all accessible databases will be processed.
- Builds a catalog with parallel schema processing for performance.
- For each table, includes detailed column information: name, type, ordinal position,
  nullable, description, default value, and type-specific attributes.
"""

import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Optional, List

from jupyter_server.base.handlers import APIHandler
import tornado

SIZE_ORDER = ["XSMALL", "SMALL", "MEDIUM", "LARGE", "XLARGE", "XXLARGE", "XXXLARGE", "X4LARGE", "X5LARGE", "X6LARGE"]


class SnowflakeSchemaHandler(APIHandler):
    """Handler for Snowflake schema operations"""
    
    def _setup_snowflake_environment(self):
        """Install required Snowflake packages if not available"""
        def install_package(package_name):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                return True
            except subprocess.CalledProcessError:
                return False

        missing_packages = []
        
        try:
            import snowflake.connector
        except ImportError:
            if install_package("snowflake-connector-python"):
                try:
                    import snowflake.connector
                except ImportError as e:
                    missing_packages.append(f"snowflake-connector-python: {str(e)}")
            else:
                missing_packages.append("snowflake-connector-python: installation failed")

        if missing_packages:
            raise ImportError("Required modules could not be installed: " + ", ".join(missing_packages))
        
        import snowflake.connector
        return snowflake.connector

    def _get_snowflake_config(self, provided_config: Optional[Dict] = None) -> Optional[Dict]:
        """Get Snowflake configuration from request or environment variables"""
        if provided_config:
            return provided_config
        
        # Look for Snowflake database configuration in the environment
        for key, value in os.environ.items():
            if key.endswith('_CONNECTION_JSON'):
                try:
                    config = json.loads(value)
                    if config.get('type') == 'snowflake':
                        return config
                except Exception as e:
                    print(f"[SnowflakeSchemaHandler] Error parsing database config {key}: {e}")
                    continue
        
        return None
    
    def _get_connection_params(self, config: Dict) -> Dict[str, Any]:
        """Build Snowflake connection parameters from configuration"""
        # Extract account from connectionUrl
        connection_url = config.get('connectionUrl', '')
        if not connection_url:
            raise ValueError("connectionUrl is required for Snowflake")
        
        # Extract the account identifier from the connectionUrl
        url_match = re.match(r'https?://([^/]+)', connection_url)
        if not url_match:
            raise ValueError(f"Invalid Snowflake connectionUrl format: {connection_url}")
        
        account = url_match.group(1)
        # Strip .snowflakecomputing.com if present
        account_identifier = account.replace('.snowflakecomputing.com', '')
        
        conn_params = {
            'account': account_identifier,
            'user': config['username'],
            'password': config['password'],
        }
        
        warehouse = config.get('warehouse')
        database = config.get('database')
        role = config.get('role')
        
        if warehouse:
            conn_params['warehouse'] = warehouse
        if database:
            conn_params['database'] = database
        if role:
            conn_params['role'] = role
        
        return conn_params
    
    def _fetch_result_scan(self, cur, sql: str, name_col: str = "name") -> List[str]:
        """Execute SQL and fetch results using RESULT_SCAN"""
        cur.execute(sql)
        cur.execute(f'SELECT "{name_col}" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))')
        rows = cur.fetchall()
        # Handle both DictCursor (returns dicts) and regular cursor (returns tuples)
        if rows and isinstance(rows[0], dict):
            return [r[name_col] for r in rows]
        return [r[0] for r in rows]
    
    def _get_warehouses(self, cur) -> List[Dict]:
        """Get all warehouses with their state and size"""
        cur.execute("SHOW WAREHOUSES")
        cur.execute("""
            SELECT "name","state","size","auto_suspend","auto_resume"
            FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
        """)
        rows = cur.fetchall()
        # Handle DictCursor (returns dicts) and regular cursor (returns tuples)
        if rows and isinstance(rows[0], dict):
            # DictCursor: normalize keys to lowercase
            return [{k.lower(): v for k, v in row.items()} for row in rows]
        else:
            # Regular cursor: manually create dicts
            cols = [d[0].lower() for d in cur.description]
            return [dict(zip(cols, row)) for row in rows]
    
    def _size_rank(self, sz: str) -> int:
        """Get the numeric rank of a warehouse size"""
        s = (sz or "").upper()
        return SIZE_ORDER.index(s) if s in SIZE_ORDER else len(SIZE_ORDER) + 1
    
    def _choose_smallest_running(self, warehouses: List[Dict]) -> Optional[str]:
        """Choose the smallest running warehouse"""
        running = [w for w in warehouses if (w.get("state") or "").upper() == "STARTED"]
        if not running:
            return None
        running.sort(key=lambda w: self._size_rank(w.get("size")))
        return running[0]["name"]
    
    def _choose_smallest_suspended(self, warehouses: List[Dict]) -> Optional[str]:
        """Choose the smallest suspended warehouse"""
        suspended = [w for w in warehouses if (w.get("state") or "").upper() in ("SUSPENDED", "RESIZING")]
        if not suspended:
            return None
        suspended.sort(key=lambda w: self._size_rank(w.get("size")))
        return suspended[0]["name"]
    
    def _resume_warehouse(self, cur, name: str) -> None:
        """Resume a suspended warehouse"""
        cur.execute(f'ALTER WAREHOUSE "{name}" RESUME')
    
    def _create_tiny_warehouse(self, cur, name: str = "SPAI_TINY_WH") -> str:
        """Create a tiny warehouse (requires proper privilege)"""
        cur.execute(f'''
            CREATE WAREHOUSE IF NOT EXISTS "{name}"
            WITH WAREHOUSE_SIZE = XSMALL
                 AUTO_SUSPEND = 60
                 AUTO_RESUME = TRUE
                 INITIALLY_SUSPENDED = TRUE
        ''')
        # Start it
        cur.execute(f'ALTER WAREHOUSE "{name}" RESUME')
        return name
    
    def _ensure_warehouse(self, cur, preferred: Optional[str]) -> str:
        """Ensure a warehouse is available and running"""
        # Respect an explicitly provided warehouse first, if any
        if preferred:
            try:
                cur.execute(f'SHOW WAREHOUSES LIKE \'{preferred}\'')
                cur.execute('SELECT "name","state","size" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))')
                row = cur.fetchone()
                if row:
                    # Handle DictCursor vs regular cursor
                    state = (row["state"] if isinstance(row, dict) else row[1] or "").upper()
                    if state != "STARTED":
                        self._resume_warehouse(cur, preferred)
                    return preferred
            except Exception as e:
                # Fall back to discovery below
                print(f"Note: preferred warehouse '{preferred}' not available or cannot be resumed ({e}). Falling back.")

        warehouses = self._get_warehouses(cur)
        name = self._choose_smallest_running(warehouses)
        if name:
            return name

        name = self._choose_smallest_suspended(warehouses)
        if name:
            self._resume_warehouse(cur, name)
            return name

        # None exist → create tiny one
        return self._create_tiny_warehouse(cur)
    
    def _list_databases(self, cur) -> List[str]:
        """List all databases"""
        return self._fetch_result_scan(cur, "SHOW DATABASES", "name")
    
    def _list_schemas_for_db(self, cur, db: str) -> List[str]:
        """List all schemas for a database (excluding INFORMATION_SCHEMA)"""
        cur.execute(f'USE DATABASE "{db}"')
        schemas = self._fetch_result_scan(cur, "SHOW SCHEMAS", "name")
        return [s for s in schemas if s.upper() != "INFORMATION_SCHEMA"]

    def _list_tables_with_columns_for_schema(self, connector, conn, db: str, schema: str, limit: int = 5000) -> List[Dict]:
        """Get tables and their columns for a schema using optimized bulk query."""
        cur = conn.cursor(connector.DictCursor)
        try:
            cur.execute(f'USE DATABASE "{db}"')
            cur.execute(f'USE SCHEMA "{schema}"')
            
            # Get all tables and columns in one query for better performance
            cur.execute("""
                SELECT 
                    t.TABLE_SCHEMA,
                    t.TABLE_NAME,
                    t.TABLE_TYPE,
                    c.COLUMN_NAME,
                    c.DATA_TYPE,
                    c.ORDINAL_POSITION,
                    c.IS_NULLABLE,
                    c.COLUMN_DEFAULT,
                    c.CHARACTER_MAXIMUM_LENGTH,
                    c.NUMERIC_PRECISION,
                    c.NUMERIC_SCALE,
                    c.COMMENT
                FROM INFORMATION_SCHEMA.TABLES t
                LEFT JOIN INFORMATION_SCHEMA.COLUMNS c
                    ON t.TABLE_SCHEMA = c.TABLE_SCHEMA 
                    AND t.TABLE_NAME = c.TABLE_NAME
                WHERE t.TABLE_SCHEMA = %s
                ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION
                LIMIT 50000
            """, (schema,))
            rows = cur.fetchall()
            
            # Group by table
            tables_dict = {}
            for r in rows:
                if isinstance(r, dict):
                    table_key = r["TABLE_NAME"]
                    if table_key not in tables_dict:
                        tables_dict[table_key] = {
                            "schema": r["TABLE_SCHEMA"],
                            "table": r["TABLE_NAME"],
                            "type": r["TABLE_TYPE"],
                            "columns": []
                        }
                    
                    if r.get("COLUMN_NAME"):
                        col = {
                            "name": r["COLUMN_NAME"],
                            "type": r["DATA_TYPE"],
                            "ordinal": r["ORDINAL_POSITION"],
                            "nullable": r["IS_NULLABLE"] == "YES",
                        }
                        if r.get("COMMENT"):
                            col["description"] = r["COMMENT"]
                        if r.get("COLUMN_DEFAULT"):
                            col["default"] = r["COLUMN_DEFAULT"]
                        if r.get("CHARACTER_MAXIMUM_LENGTH"):
                            col["max_length"] = r["CHARACTER_MAXIMUM_LENGTH"]
                        if r.get("NUMERIC_PRECISION"):
                            col["precision"] = r["NUMERIC_PRECISION"]
                        if r.get("NUMERIC_SCALE") is not None:
                            col["scale"] = r["NUMERIC_SCALE"]
                        tables_dict[table_key]["columns"].append(col)
                else:
                    table_key = r[1]
                    if table_key not in tables_dict:
                        tables_dict[table_key] = {
                            "schema": r[0],
                            "table": r[1],
                            "type": r[2],
                            "columns": []
                        }
                    
                    if r[3]:  # COLUMN_NAME
                        col = {
                            "name": r[3],
                            "type": r[4],
                            "ordinal": r[5],
                            "nullable": r[6] == "YES",
                        }
                        if r[11]:  # COMMENT
                            col["description"] = r[11]
                        if r[7]:  # COLUMN_DEFAULT
                            col["default"] = r[7]
                        if r[8]:  # CHARACTER_MAXIMUM_LENGTH
                            col["max_length"] = r[8]
                        if r[9]:  # NUMERIC_PRECISION
                            col["precision"] = r[9]
                        if r[10] is not None:  # NUMERIC_SCALE
                            col["scale"] = r[10]
                        tables_dict[table_key]["columns"].append(col)
            
            return list(tables_dict.values())[:limit]
        finally:
            cur.close()
    
    def _process_schema(self, connector, conn, db: str, schema: str) -> Dict:
        """Process a single schema with its tables and columns."""
        try:
            tables = self._list_tables_with_columns_for_schema(connector, conn, db, schema)
            return {"schema": schema, "tables": tables, "error": None}
        except Exception as e:
            print(f"Warning: Error processing schema {db}.{schema}: {e}", file=sys.stderr)
            return {"schema": schema, "tables": [], "error": str(e)}
    
    def _build_catalog(self, connector, conn, max_workers: int = 5, specified_database: Optional[str] = None, specified_warehouse: Optional[str] = None) -> Dict:
        """Build complete catalog with parallel schema processing
        
        Args:
            connector: Snowflake connector module
            conn: Active Snowflake connection
            max_workers: Number of parallel workers for schema processing
            specified_database: If provided, only process this database
            specified_warehouse: If provided, use this warehouse (don't auto-select)
        """
        cur = conn.cursor(connector.DictCursor)
        try:
            # 1) Handle warehouse selection
            if specified_warehouse:
                # Use the explicitly specified warehouse
                wh = specified_warehouse
                cur.execute(f'USE WAREHOUSE "{wh}"')
            else:
                # Auto-select a warehouse using existing logic
                preferred_wh = None
                # Extract warehouse from conn if available
                try:
                    cur.execute("SELECT CURRENT_WAREHOUSE()")
                    row = cur.fetchone()
                    if row:
                        preferred_wh = row[0] if isinstance(row, tuple) else row.get("CURRENT_WAREHOUSE()")
                except:
                    pass
                
                wh = self._ensure_warehouse(cur, preferred_wh)
                cur.execute(f'USE WAREHOUSE "{wh}"')

            # 2) Handle database selection
            if specified_database:
                # Only process the specified database
                dbs = [specified_database]
            else:
                # List all databases
                dbs = self._list_databases(cur)
            cur.close()

            catalog = []
            print(f"Processing {len(dbs)} databases...", file=sys.stderr)
            
            for db in dbs:
                print(f"  Processing database: {db}", file=sys.stderr)
                cur = conn.cursor(connector.DictCursor)
                try:
                    schemas = self._list_schemas_for_db(cur, db)
                    print(f"    Found {len(schemas)} schemas", file=sys.stderr)
                finally:
                    cur.close()
                
                # Process schemas in parallel for this database
                schema_objs = []
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_schema = {
                        executor.submit(self._process_schema, connector, conn, db, s): s 
                        for s in schemas
                    }
                    
                    for future in as_completed(future_to_schema):
                        schema_name = future_to_schema[future]
                        try:
                            result = future.result()
                            schema_objs.append(result)
                            print(f"      Completed schema: {schema_name} ({len(result['tables'])} tables)", file=sys.stderr)
                        except Exception as e:
                            print(f"      Error with schema {schema_name}: {e}", file=sys.stderr)
                            schema_objs.append({"schema": schema_name, "tables": [], "error": str(e)})
                
                catalog.append({"database": db, "schemas": schema_objs})

            return {"warehouse": wh, "databases": catalog}
        finally:
            if not cur.is_closed():
                cur.close()
    
    def _format_catalog_as_json(self, catalog: Dict) -> Dict:
        """Format the catalog for JSON response"""
        return catalog

    @tornado.web.authenticated
    def post(self):
        """Get Snowflake database schema information"""
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
            
            # Get Snowflake configuration from request or environment
            config = self._get_snowflake_config(body.get('config'))
            
            if not config:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No Snowflake configuration provided and no Snowflake configurations found in environment"
                }))
                return
            
            # Setup Snowflake environment
            try:
                connector = self._setup_snowflake_environment()
            except ImportError as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": str(e)
                }))
                return
            
            # Get database schema using optimized catalog building
            try:
                conn_params = self._get_connection_params(config)
                max_workers = int(body.get('max_workers', 5))
                
                # Extract database and warehouse from config for filtering
                specified_database = config.get('database')
                specified_warehouse = config.get('warehouse')
                
                print(f"[SnowflakeSchemaHandler] Connecting with account={conn_params['account']}, user={conn_params['user']}, warehouse={conn_params.get('warehouse')}, database={conn_params.get('database')}, role={conn_params.get('role')}")
                
                connection = connector.connect(**conn_params, client_session_keep_alive=False)
                
                try:
                    catalog = self._build_catalog(
                        connector, 
                        connection, 
                        max_workers=max_workers,
                        specified_database=specified_database,
                        specified_warehouse=specified_warehouse
                    )
                    result = self._format_catalog_as_json(catalog)
                    self.finish(json.dumps(result, indent=2))
                finally:
                    connection.close()
                
            except Exception as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": f"Error connecting to Snowflake: {str(e)}"
                }))
                
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class SnowflakeQueryHandler(APIHandler):
    """Handler for Snowflake query execution"""
    
    def _setup_snowflake_environment(self):
        """Install required Snowflake packages if not available"""
        def install_package(package_name):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                return True
            except subprocess.CalledProcessError:
                return False

        missing_packages = []
        
        try:
            import snowflake.connector
        except ImportError:
            if install_package("snowflake-connector-python"):
                try:
                    import snowflake.connector
                except ImportError as e:
                    missing_packages.append(f"snowflake-connector-python: {str(e)}")
            else:
                missing_packages.append("snowflake-connector-python: installation failed")

        if missing_packages:
            raise ImportError("Required modules could not be installed: " + ", ".join(missing_packages))
        
        import snowflake.connector
        return snowflake.connector
    
    def _get_snowflake_config(self, provided_config: Optional[Dict] = None) -> Optional[Dict]:
        """Get Snowflake configuration from request or environment variables"""
        if provided_config:
            return provided_config
        
        # Look for Snowflake database configuration in the environment
        for key, value in os.environ.items():
            if key.endswith('_CONNECTION_JSON'):
                try:
                    config = json.loads(value)
                    if config.get('type') == 'snowflake':
                        return config
                except Exception as e:
                    print(f"[SnowflakeQueryHandler] Error parsing database config {key}: {e}")
                    continue
        
        return None
    
    def _get_connection_params(self, config: Dict) -> Dict[str, Any]:
        """Build Snowflake connection parameters from configuration"""
        # Extract account from connectionUrl
        connection_url = config.get('connectionUrl', '')
        if not connection_url:
            raise ValueError("connectionUrl is required for Snowflake")
        
        # Extract the account identifier from the connectionUrl
        # Expected format: https://account.snowflakecomputing.com or https://account-region.snowflakecomputing.com
        import re
        url_match = re.match(r'https?://([^/]+)', connection_url)
        if not url_match:
            raise ValueError(f"Invalid Snowflake connectionUrl format: {connection_url}")
        
        account = url_match.group(1)
        # Strip .snowflakecomputing.com if present
        account_identifier = account.replace('.snowflakecomputing.com', '')
        
        conn_params = {
            'account': account_identifier,
            'user': config['username'],
            'password': config['password'],
        }
        
        warehouse = config.get('warehouse')
        database = config.get('database')
        role = config.get('role')
        
        if warehouse:
            conn_params['warehouse'] = warehouse
        if database:
            conn_params['database'] = database
        if role:
            conn_params['role'] = role
        
        return conn_params
    
    @tornado.web.authenticated
    def post(self):
        """Execute a read-only SQL query on Snowflake"""
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
            if not normalized_query.startswith('SELECT') and not normalized_query.startswith('WITH') and not normalized_query.startswith('SHOW') and not normalized_query.startswith('DESCRIBE'):
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Only SELECT, WITH, SHOW, or DESCRIBE statements are allowed for read queries."
                }))
                return
            
            # Get Snowflake configuration from request or environment
            config = self._get_snowflake_config(body.get('config'))
            
            if not config:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No Snowflake configuration provided and no Snowflake configurations found in environment"
                }))
                return
            
            # Setup Snowflake environment
            try:
                connector = self._setup_snowflake_environment()
            except ImportError as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": str(e)
                }))
                return
            
            # Execute query
            try:
                conn_params = self._get_connection_params(config)
                
                # Allow specifying a specific database for the query
                database = body.get('database')
                if database:
                    conn_params['database'] = database
                
                # Ensure we have a warehouse for querying
                if not conn_params.get('warehouse'):
                    raise ValueError("A warehouse is required to execute queries.")
                
                connection = connector.connect(**conn_params)
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
                    "error": f"Snowflake query failed: {str(e)}"
                }))
                
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))
