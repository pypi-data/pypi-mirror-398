"""
Unified database schema service handlers for SignalPilot AI.
Provides REST API handlers for PostgreSQL and MySQL database schema retrieval and query execution.
"""

import json
import os
import subprocess
import sys
from typing import Any, Dict, Optional

from jupyter_server.base.handlers import APIHandler
import tornado


class UnifiedDatabaseSchemaHandler(APIHandler):
    """Handler for unified database schema operations (PostgreSQL and MySQL)"""
    
    def _setup_database_environment(self, db_type: str = 'postgresql'):
        """Install required database packages if not available"""
        def install_package(package_name):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                return True
            except subprocess.CalledProcessError:
                return False

        missing_packages = []
        
        try:
            import sqlalchemy
            from sqlalchemy import create_engine, text
        except ImportError:
            if install_package("sqlalchemy"):
                try:
                    import sqlalchemy
                    from sqlalchemy import create_engine, text
                except ImportError as e:
                    missing_packages.append(f"sqlalchemy: {str(e)}")
            else:
                missing_packages.append("sqlalchemy: installation failed")

        # Install database-specific drivers
        if db_type == 'mysql':
            try:
                import pymysql
            except ImportError:
                if install_package("pymysql"):
                    try:
                        import pymysql
                    except ImportError as e:
                        missing_packages.append(f"pymysql: {str(e)}")
                else:
                    missing_packages.append("pymysql: installation failed")
        else:  # postgresql
            try:
                import psycopg2
            except ImportError:
                if install_package("psycopg2-binary"):
                    try:
                        import psycopg2
                    except ImportError as e:
                        missing_packages.append(f"psycopg2: {str(e)}")
                else:
                    missing_packages.append("psycopg2: installation failed")

        if missing_packages:
            raise ImportError("Required modules could not be installed: " + ", ".join(missing_packages))
        
        from sqlalchemy import create_engine, text
        return create_engine, text
    
    def _detect_database_type(self, db_url: str) -> str:
        """Detect database type from connection URL"""
        if db_url.startswith('mysql'):
            return 'mysql'
        elif db_url.startswith('postgresql') or db_url.startswith('postgres'):
            return 'postgresql'
        else:
            # Default to postgresql for backward compatibility
            return 'postgresql'
    
    def _get_database_url(self, provided_url: Optional[str] = None, db_type: Optional[str] = None) -> tuple[Optional[str], str]:
        """Get database URL from request or environment variables
        Returns: (db_url, db_type)
        """
        if provided_url:
            detected_type = self._detect_database_type(provided_url)
            return provided_url, detected_type
        
        # First try the new multi-database environment format
        # Look for any database configuration in the environment
        db_configs = {}
        
        # Scan environment for database configurations
        for key, value in os.environ.items():
            if key.endswith('_CONNECTION_JSON'):
                try:
                    config = json.loads(value)
                    db_name = key.replace('_CONNECTION_JSON', '')
                    db_configs[db_name] = config
                    
                    # Use the first available database configuration matching the requested type
                    # Or use the first one if no specific type requested
                    config_type = config.get('type', 'postgresql')
                    if db_type is None or config_type == db_type:
                        if 'connectionUrl' in config:
                            db_url = config['connectionUrl']
                        else:
                            # Build connection URL from components
                            if config_type == 'postgresql':
                                db_url = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
                            elif config_type == 'mysql':
                                db_url = f"mysql+pymysql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
                        
                        if db_url:
                            return db_url, config_type
                except Exception as e:
                    print(f"[UnifiedDatabaseSchemaHandler] Error parsing database config {key}: {e}")
                    continue
        
        # Fallback to legacy DB_URL environment variable if no multi-db config found
        db_url = os.environ.get('DB_URL')
        if db_url:
            detected_type = self._detect_database_type(db_url)
            return db_url, detected_type
        
        return None, db_type or 'postgresql'
    
    def _get_mysql_schema(self, conn, text):
        """Get MySQL database schema"""
        # Get the current database name
        db_name_result = conn.execute(text("SELECT DATABASE()"))
        current_db = db_name_result.scalar()
        
        # Get all tables from the current database
        tables_query = """
            SELECT TABLE_SCHEMA, TABLE_NAME 
            FROM information_schema.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            AND TABLE_SCHEMA = :schema
            ORDER BY TABLE_NAME
            LIMIT 50;
        """
        
        tables_result = conn.execute(text(tables_query), {"schema": current_db})
        tables = [dict(row._mapping) for row in tables_result]
        
        if not tables:
            return {
                "result": "Database connected successfully, but no tables found.",
                "table_schemas": {}
            }
        
        # Start building markdown formatted output
        markdown_output = f"# MySQL Database Schema: {current_db}\n\nFound **{len(tables)}** table(s)\n\n"
        
        # Store individual table schemas for mention context
        table_schemas = {}
        
        # Get detailed information for each table
        for table in tables:
            table_schema = table['TABLE_SCHEMA']
            table_name = table['TABLE_NAME']
            full_table_name = f"{table_schema}.{table_name}"
            
            # Get columns
            columns_query = """
                SELECT 
                    COLUMN_NAME as column_name,
                    DATA_TYPE as data_type,
                    IS_NULLABLE as is_nullable,
                    COLUMN_DEFAULT as column_default,
                    CHARACTER_MAXIMUM_LENGTH as character_maximum_length,
                    NUMERIC_PRECISION as numeric_precision,
                    NUMERIC_SCALE as numeric_scale,
                    COLUMN_KEY as column_key,
                    EXTRA as extra
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
                ORDER BY ORDINAL_POSITION
                LIMIT 30;
            """
            
            columns_result = conn.execute(text(columns_query), 
                                        {"schema": table_schema, "table": table_name})
            columns = [dict(row._mapping) for row in columns_result]
            
            # Get primary keys
            pk_query = """
                SELECT COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = :schema 
                    AND TABLE_NAME = :table
                    AND CONSTRAINT_NAME = 'PRIMARY'
                ORDER BY ORDINAL_POSITION;
            """
            
            pk_result = conn.execute(text(pk_query), 
                                   {"schema": table_schema, "table": table_name})
            primary_keys = [row[0] for row in pk_result]
            
            # Get foreign keys
            fk_query = """
                SELECT 
                    COLUMN_NAME as column_name,
                    REFERENCED_TABLE_SCHEMA as foreign_table_schema,
                    REFERENCED_TABLE_NAME as foreign_table_name,
                    REFERENCED_COLUMN_NAME as foreign_column_name
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = :schema 
                    AND TABLE_NAME = :table
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY ORDINAL_POSITION;
            """
            
            fk_result = conn.execute(text(fk_query), 
                                   {"schema": table_schema, "table": table_name})
            foreign_keys = [dict(row._mapping) for row in fk_result]
            
            # Get indices (excluding primary key)
            index_query = """
                SELECT 
                    INDEX_NAME as index_name,
                    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as columns,
                    INDEX_TYPE as index_type,
                    NON_UNIQUE as non_unique
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = :schema 
                    AND TABLE_NAME = :table
                    AND INDEX_NAME != 'PRIMARY'
                GROUP BY INDEX_NAME, INDEX_TYPE, NON_UNIQUE
                ORDER BY INDEX_NAME;
            """
            
            index_result = conn.execute(text(index_query), 
                                      {"schema": table_schema, "table": table_name})
            indices = [dict(row._mapping) for row in index_result]
            
            # Store individual table schema for mention context
            table_info = {
                'schema': table_schema,
                'table_name': table_name,
                'full_name': full_table_name,
                'columns': [dict(col) for col in columns],
                'primary_keys': primary_keys,
                'foreign_keys': [dict(fk) for fk in foreign_keys],
                'indices': [dict(idx) for idx in indices]
            }
            table_schemas[full_table_name] = table_info
            
            # Build table section
            markdown_output += f"## {full_table_name}\n\n"
            
            # Columns section
            markdown_output += f"### Columns ({len(columns)})\n\n"
            for col in columns:
                col_name = col['column_name']
                data_type = col['data_type']
                
                # Format data type with precision/scale
                if col['character_maximum_length']:
                    data_type += f"({col['character_maximum_length']})"
                elif col['numeric_precision'] and col['numeric_scale'] is not None:
                    data_type += f"({col['numeric_precision']},{col['numeric_scale']})"
                elif col['numeric_precision']:
                    data_type += f"({col['numeric_precision']})"
                
                # Add constraints
                constraints = []
                if col['is_nullable'] == 'NO':
                    constraints.append("NOT NULL")
                if col['column_default']:
                    constraints.append(f"DEFAULT {col['column_default']}")
                if col['column_key'] == 'PRI':
                    constraints.append("PRIMARY KEY")
                if col['extra'] and 'auto_increment' in col['extra'].lower():
                    constraints.append("AUTO_INCREMENT")
                
                constraint_text = f" ({', '.join(constraints)})" if constraints else ""
                
                markdown_output += f"- **{col_name}**: {data_type}{constraint_text}\n"
            
            # Primary keys section
            if primary_keys:
                markdown_output += f"\n### Primary Keys\n\n"
                markdown_output += f"- {', '.join([f'**{pk}**' for pk in primary_keys])}\n"
            
            # Foreign keys section
            if foreign_keys:
                markdown_output += f"\n### Foreign Keys\n\n"
                for fk in foreign_keys:
                    markdown_output += f"- **{fk['column_name']}** → {fk['foreign_table_schema']}.{fk['foreign_table_name']}({fk['foreign_column_name']})\n"
            
            # Indices section
            if indices:
                markdown_output += f"\n### Indices\n\n"
                for idx in indices:
                    unique_text = "" if idx['non_unique'] else "UNIQUE "
                    markdown_output += f"- **{idx['index_name']}**: {unique_text}{idx['index_type']} on ({idx['columns']})\n"
            
            markdown_output += "\n---\n\n"
        
        return {
            "result": markdown_output.strip(),
            "table_schemas": table_schemas
        }
    
    def _get_postgresql_schema(self, conn, text):
        """Get PostgreSQL database schema"""
        # Get all tables from public and custom schemas (excluding system schemas)
        tables_query = """
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_type = 'BASE TABLE' 
            AND table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY table_schema, table_name
            LIMIT 50;
        """
        
        tables_result = conn.execute(text(tables_query))
        tables = [dict(row._mapping) for row in tables_result]
        
        if not tables:
            return {
                "result": "Database connected successfully, but no tables found.",
                "table_schemas": {}
            }
        
        # Start building markdown formatted output
        markdown_output = f"# PostgreSQL Database Schema\n\nFound **{len(tables)}** table(s)\n\n"
        
        # Store individual table schemas for mention context
        table_schemas = {}
        
        # Get detailed information for each table
        for table in tables:
            table_schema = table['table_schema']
            table_name = table['table_name']
            full_table_name = f"{table_schema}.{table_name}"
            
            # Get columns
            columns_query = """
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable, 
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_schema = :schema AND table_name = :table
                ORDER BY ordinal_position
                LIMIT 30;
            """
            
            columns_result = conn.execute(text(columns_query), 
                                        {"schema": table_schema, "table": table_name})
            columns = [dict(row._mapping) for row in columns_result]
            
            # Get primary keys
            pk_query = """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY' 
                    AND tc.table_schema = :schema 
                    AND tc.table_name = :table
                ORDER BY kcu.ordinal_position;
            """
            
            pk_result = conn.execute(text(pk_query), 
                                   {"schema": table_schema, "table": table_name})
            primary_keys = [row[0] for row in pk_result]
            
            # Get foreign keys
            fk_query = """
                SELECT 
                    kcu.column_name,
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_schema = :schema 
                    AND tc.table_name = :table
                ORDER BY kcu.ordinal_position;
            """
            
            fk_result = conn.execute(text(fk_query), 
                                   {"schema": table_schema, "table": table_name})
            foreign_keys = [dict(row._mapping) for row in fk_result]
            
            # Get indices
            index_query = """
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = :schema 
                    AND tablename = :table
                    AND indexname NOT LIKE '%_pkey'
                ORDER BY indexname;
            """
            
            index_result = conn.execute(text(index_query), 
                                      {"schema": table_schema, "table": table_name})
            indices = [dict(row._mapping) for row in index_result]
            
            # Store individual table schema for mention context
            table_info = {
                'schema': table_schema,
                'table_name': table_name,
                'full_name': full_table_name,
                'columns': [dict(col) for col in columns],
                'primary_keys': primary_keys,
                'foreign_keys': [dict(fk) for fk in foreign_keys],
                'indices': [dict(idx) for idx in indices]
            }
            table_schemas[full_table_name] = table_info
            
            # Build table section
            markdown_output += f"## {full_table_name}\n\n"
            
            # Columns section
            markdown_output += f"### Columns ({len(columns)})\n\n"
            for col in columns:
                col_name = col['column_name']
                data_type = col['data_type']
                
                # Format data type with precision/scale
                if col['character_maximum_length']:
                    data_type += f"({col['character_maximum_length']})"
                elif col['numeric_precision'] and col['numeric_scale'] is not None:
                    data_type += f"({col['numeric_precision']},{col['numeric_scale']})"
                elif col['numeric_precision']:
                    data_type += f"({col['numeric_precision']})"
                
                # Add constraints
                constraints = []
                if col['is_nullable'] == 'NO':
                    constraints.append("NOT NULL")
                if col['column_default']:
                    constraints.append(f"DEFAULT {col['column_default']}")
                if col_name in primary_keys:
                    constraints.append("PRIMARY KEY")
                
                constraint_text = f" ({', '.join(constraints)})" if constraints else ""
                
                markdown_output += f"- **{col_name}**: {data_type}{constraint_text}\n"
            
            # Primary keys section
            if primary_keys:
                markdown_output += f"\n### Primary Keys\n\n"
                markdown_output += f"- {', '.join([f'**{pk}**' for pk in primary_keys])}\n"
            
            # Foreign keys section
            if foreign_keys:
                markdown_output += f"\n### Foreign Keys\n\n"
                for fk in foreign_keys:
                    markdown_output += f"- **{fk['column_name']}** → {fk['foreign_table_schema']}.{fk['foreign_table_name']}({fk['foreign_column_name']})\n"
            
            # Indices section
            if indices:
                markdown_output += f"\n### Indices\n\n"
                for idx in indices:
                    markdown_output += f"- **{idx['indexname']}**: {idx['indexdef']}\n"
            
            markdown_output += "\n---\n\n"
        
        return {
            "result": markdown_output.strip(),
            "table_schemas": table_schemas
        }
    
    @tornado.web.authenticated
    def post(self):
        """Get database schema information for PostgreSQL or MySQL"""
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
            
            # Get database URL and type from request or environment
            db_url, db_type = self._get_database_url(body.get('dbUrl'))
            
            if not db_url:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No database URL provided and no database configurations found in environment"
                }))
                return
            
            # Ensure MySQL URL uses pymysql driver
            if db_type == 'mysql' and db_url.startswith('mysql://'):
                db_url = db_url.replace('mysql://', 'mysql+pymysql://', 1)
            
            # Setup database environment
            try:
                create_engine, text = self._setup_database_environment(db_type)
            except ImportError as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": str(e)
                }))
                return
            
            # Get database schema
            try:
                engine = create_engine(db_url)
                
                with engine.connect() as conn:
                    # Get schema based on database type
                    if db_type == 'mysql':
                        result = self._get_mysql_schema(conn, text)
                    else:  # postgresql
                        result = self._get_postgresql_schema(conn, text)
                    
                    self.finish(json.dumps(result))
                    
            except Exception as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": f"Error connecting to {db_type} database: {str(e)}"
                }))
                
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class UnifiedDatabaseQueryHandler(APIHandler):
    """Handler for unified database query execution (PostgreSQL and MySQL)"""
    
    def _setup_database_environment(self, db_type: str = 'postgresql'):
        """Install required database packages if not available"""
        def install_package(package_name):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                return True
            except subprocess.CalledProcessError:
                return False

        missing_packages = []
        
        try:
            import sqlalchemy
            from sqlalchemy import create_engine, text
        except ImportError:
            if install_package("sqlalchemy"):
                try:
                    import sqlalchemy
                    from sqlalchemy import create_engine, text
                except ImportError as e:
                    missing_packages.append(f"sqlalchemy: {str(e)}")
            else:
                missing_packages.append("sqlalchemy: installation failed")

        # Install database-specific drivers
        if db_type == 'mysql':
            try:
                import pymysql
            except ImportError:
                if install_package("pymysql"):
                    try:
                        import pymysql
                    except ImportError as e:
                        missing_packages.append(f"pymysql: {str(e)}")
                else:
                    missing_packages.append("pymysql: installation failed")
        else:  # postgresql
            try:
                import psycopg2
            except ImportError:
                if install_package("psycopg2-binary"):
                    try:
                        import psycopg2
                    except ImportError as e:
                        missing_packages.append(f"psycopg2: {str(e)}")
                else:
                    missing_packages.append("psycopg2: installation failed")

        if missing_packages:
            raise ImportError("Required modules could not be installed: " + ", ".join(missing_packages))
        
        from sqlalchemy import create_engine, text
        return create_engine, text
    
    def _detect_database_type(self, db_url: str) -> str:
        """Detect database type from connection URL"""
        if db_url.startswith('mysql'):
            return 'mysql'
        elif db_url.startswith('postgresql') or db_url.startswith('postgres'):
            return 'postgresql'
        else:
            # Default to postgresql for backward compatibility
            return 'postgresql'
    
    def _get_database_url(self, provided_url: Optional[str] = None, db_type: Optional[str] = None) -> tuple[Optional[str], str]:
        """Get database URL from request or environment variables
        Returns: (db_url, db_type)
        """
        if provided_url:
            detected_type = self._detect_database_type(provided_url)
            return provided_url, detected_type
        
        # First try the new multi-database environment format
        # Look for any database configuration in the environment
        db_configs = {}
        
        # Scan environment for database configurations
        for key, value in os.environ.items():
            if key.endswith('_CONNECTION_JSON'):
                try:
                    config = json.loads(value)
                    db_name = key.replace('_CONNECTION_JSON', '')
                    db_configs[db_name] = config
                    
                    # Use the first available database configuration matching the requested type
                    # Or use the first one if no specific type requested
                    config_type = config.get('type', 'postgresql')
                    if db_type is None or config_type == db_type:
                        if 'connectionUrl' in config:
                            db_url = config['connectionUrl']
                        else:
                            # Build connection URL from components
                            if config_type == 'postgresql':
                                db_url = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
                            elif config_type == 'mysql':
                                db_url = f"mysql+pymysql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
                        
                        if db_url:
                            return db_url, config_type
                except Exception as e:
                    print(f"[UnifiedDatabaseQueryHandler] Error parsing database config {key}: {e}")
                    continue
        
        # Fallback to legacy DB_URL environment variable if no multi-db config found
        db_url = os.environ.get('DB_URL')
        if db_url:
            detected_type = self._detect_database_type(db_url)
            return db_url, detected_type
        
        return None, db_type or 'postgresql'
    
    @tornado.web.authenticated
    def post(self):
        """Execute a read-only SQL query on PostgreSQL or MySQL"""
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
            if not normalized_query.startswith('SELECT') and not normalized_query.startswith('WITH'):
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Only SELECT or WITH statements are allowed for read queries."
                }))
                return
            
            # Get database URL and type from request or environment
            db_url, db_type = self._get_database_url(body.get('dbUrl'))
            
            if not db_url:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "No database URL provided and no database configurations found in environment"
                }))
                return
            
            # Ensure MySQL URL uses pymysql driver
            if db_type == 'mysql' and db_url.startswith('mysql://'):
                db_url = db_url.replace('mysql://', 'mysql+pymysql://', 1)
            
            # Setup database environment
            try:
                create_engine, text = self._setup_database_environment(db_type)
            except ImportError as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": str(e)
                }))
                return
            
            # Execute query
            try:
                engine = create_engine(db_url)
                
                with engine.connect() as conn:
                    result = conn.execute(text(query))
                    
                    # Convert result to list of dictionaries
                    rows = [dict(row._mapping) for row in result]
                    
                    self.finish(json.dumps({
                        "result": rows
                    }))
                    
            except Exception as e:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": f"{db_type.title()} query failed: {str(e)}"
                }))
                
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))
