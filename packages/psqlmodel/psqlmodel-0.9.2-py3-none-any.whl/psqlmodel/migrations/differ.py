"""
PSQLModel Migration System - Schema Differ

Compares model definitions against database state to detect changes.
"""

from typing import Type, Dict, Any, List, Optional, Tuple, TYPE_CHECKING
import psycopg
import asyncpg
import asyncio

from .diff import DiffItem, DiffResult
from .hasher import SchemaHasher

if TYPE_CHECKING:
    from ..orm.model import PSQLModel
    from ..core.engine import Engine


class SchemaDiffer:
    """Compares model schemas against database state.
    
    Detects granular changes at the column attribute level including:
    - Type changes
    - Nullable changes
    - Default value changes
    - Primary key changes
    - Foreign key changes
    - Unique constraint changes
    - Index changes
    - Table/Column renames (configurable)
    """
    
    def __init__(self, engine: "Engine", *, detect_renames: bool = True, rename_threshold: float = 0.8):
        """
        Args:
            engine: Database engine
            detect_renames: If True, attempt to detect table/column renames instead of drop+create
            rename_threshold: Similarity threshold for rename detection (0.0-1.0, higher=stricter)
        """
        self.engine = engine
        self.hasher = SchemaHasher()
        self.detect_renames = detect_renames
        self.rename_threshold = rename_threshold

    def _detect_renamed_tables(self, model_tables: dict, db_tables: dict,
                                new_tables: set, removed_tables: set) -> list:
        """Detect tables that were renamed rather than dropped+created.
        
        Returns list of (old_name, new_name) tuples.
        """
        renames = []
        
        for old_key in list(removed_tables):
            old_data = db_tables[old_key]
            old_cols = set(old_data.get("columns", {}).keys())
            
            for new_key in list(new_tables):
                new_data = model_tables[new_key]
                new_cols = set(new_data.get("columns", {}).keys())
                
                if old_cols and new_cols:
                    # Calculate Jaccard similarity
                    similarity = len(old_cols & new_cols) / len(old_cols | new_cols)
                    if similarity >= self.rename_threshold:
                        renames.append((old_key, new_key))
                        removed_tables.discard(old_key)
                        new_tables.discard(new_key)
                        break
        
        return renames

    def _detect_renamed_columns(self, model_cols: dict, db_cols: dict,
                                 added_cols: set, removed_cols: set) -> list:
        """Detect columns that were renamed within a table.
        
        Returns list of (old_col, new_col) tuples.
        """
        renames = []
        
        for old_col in list(removed_cols):
            old_def = db_cols[old_col]
            
            for new_col in list(added_cols):
                new_def = model_cols[new_col]
                
                # Same type, nullable, and pk = likely rename
                if (old_def.get("type") == new_def.get("type") and
                    old_def.get("nullable") == new_def.get("nullable") and
                    old_def.get("primary_key") == new_def.get("primary_key")):
                    renames.append((old_col, new_col))
                    removed_cols.discard(old_col)
                    added_cols.discard(new_col)
                    break
        
        return renames
    
    def _get_db_tables(self) -> Dict[str, Dict[str, Any]]:
        """Introspect database to get table definitions."""
        dsn = self.engine._build_sync_dsn()
        tables = {}
        
        try:
            conn = psycopg.connect(dsn)
            try:
                cur = conn.cursor()
                
                # Get all tables
                cur.execute("""
                    SELECT table_schema, table_name 
                    FROM information_schema.tables 
                    WHERE table_type = 'BASE TABLE' 
                    AND table_schema NOT IN ('pg_catalog', 'information_schema')
                    AND table_name NOT LIKE '\\_%' ESCAPE '\\'
                """)
                table_rows = cur.fetchall()
                
                for schema, table_name in table_rows:
                    key = f"{schema}.{table_name}"
                    tables[key] = self._introspect_table(cur, schema, table_name)
                
                cur.close()
            finally:
                conn.close()
        except Exception:
            pass
        
        return tables
    
    async def _get_db_tables_async(self) -> Dict[str, Dict[str, Any]]:
        """Introspect database to get table definitions (Async)."""
        dsn = self.engine._build_async_dsn()
        tables = {}
        
        try:
            conn = await asyncpg.connect(dsn)
            try:
                # Get all tables
                table_rows = await conn.fetch("""
                    SELECT table_schema, table_name 
                    FROM information_schema.tables 
                    WHERE table_type = 'BASE TABLE' 
                    AND table_schema NOT IN ('pg_catalog', 'information_schema')
                    AND table_name NOT LIKE '\\_%' ESCAPE '\\'
                """)
                
                for row in table_rows:
                    schema, table_name = row['table_schema'], row['table_name']
                    key = f"{schema}.{table_name}"
                    tables[key] = await self._introspect_table_async(conn, schema, table_name)
                    
            finally:
                await conn.close()
        except Exception:
            pass
        
        return tables
    
    def _introspect_table(self, cur, schema: str, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table."""
        table_info = {
            "schema": schema,
            "name": table_name,
            "columns": {},
            "constraints": [],
            "indexes": [],
            "unique_together": [],  # Multi-column unique constraints
        }
        
        # Get columns
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                udt_name,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, table_name))
        
        for row in cur.fetchall():
            col_name = row[0]
            data_type = row[1].upper()
            udt_name = row[2]
            max_len = row[3]
            precision = row[4]
            scale = row[5]
            is_nullable = row[6] == 'YES'
            default_value = row[7]
            
            # Normalize type name
            type_str = self._normalize_type(data_type, udt_name, max_len, precision, scale)
            
            table_info["columns"][col_name] = {
                "name": col_name,
                "type": type_str,
                "nullable": is_nullable,
                "default": default_value,
            }
        
        # Get primary keys
        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_schema = %s AND tc.table_name = %s
        """, (schema, table_name))
        
        pk_columns = {row[0] for row in cur.fetchall()}
        for col_name in pk_columns:
            if col_name in table_info["columns"]:
                table_info["columns"][col_name]["primary_key"] = True
        
        # Get unique constraints - only mark columns that are the ONLY column in a constraint
        # (multi-column unique constraints should be handled as unique_together, not individual uniques)
        cur.execute("""
            SELECT kcu.column_name, tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'UNIQUE'
            AND tc.table_schema = %s AND tc.table_name = %s
        """, (schema, table_name))
        
        # Group columns by constraint name
        constraint_columns = {}
        for row in cur.fetchall():
            col_name, constraint_name = row[0], row[1]
            if constraint_name not in constraint_columns:
                constraint_columns[constraint_name] = []
            constraint_columns[constraint_name].append(col_name)
        
        # Only mark as unique if it's a single-column constraint
        # Store multi-column constraints separately in unique_together (with real names for DROP)
        for constraint_name, columns in constraint_columns.items():
            if len(columns) == 1:
                col_name = columns[0]
                if col_name in table_info["columns"]:
                    table_info["columns"][col_name]["unique"] = True
            else:
                # Multi-column unique constraint - store as dict with name and columns
                table_info["unique_together"].append({
                    "name": constraint_name,
                    "columns": tuple(sorted(columns))
                })
        
        # Get foreign keys
        cur.execute("""
            SELECT 
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu 
                ON tc.constraint_name = ccu.constraint_name
            JOIN information_schema.referential_constraints rc
                ON tc.constraint_name = rc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = %s AND tc.table_name = %s
        """, (schema, table_name))
        
        for row in cur.fetchall():
            col_name = row[0]
            fk_schema = row[1]
            fk_table = row[2]
            fk_col = row[3]
            on_delete = row[4]
            if col_name in table_info["columns"]:
                table_info["columns"][col_name]["foreign_key"] = f"{fk_schema}.{fk_table}.{fk_col}"
                table_info["columns"][col_name]["on_delete"] = on_delete
        
        # Get indexes and mark indexed columns
        # First, get index names that back constraints (PK, UNIQUE) - we should ignore these
        cur.execute("""
            SELECT c.conname, i.indexrelid::regclass::text as indexname
            FROM pg_constraint c
            JOIN pg_index i ON i.indexrelid = c.conindid
            WHERE c.conrelid = (
                SELECT oid FROM pg_class 
                WHERE relname = %s 
                AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
            )
            AND c.contype IN ('p', 'u')
        """, (table_name, schema))
        constraint_indexes = {row[1].split('.')[-1] for row in cur.fetchall()}
        
        cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = %s AND tablename = %s
        """, (schema, table_name))
        
        import re
        for row in cur.fetchall():
            index_name = row[0]
            index_def = row[1]
            
            # Extract column name from index definition 
            # Format: CREATE INDEX idx_xxx ON schema.table (column)
            # or: CREATE INDEX idx_xxx ON schema.table USING btree (column)
            match = re.search(r'\(([^)]+)\)$', index_def)
            if match:
                indexed_cols = [c.strip() for c in match.group(1).split(',')]
                # Only consider it a "column index" if it's a single column
                # Composite indexes don't satisfy simple column index=True requirements
                if len(indexed_cols) == 1:
                    col_name = indexed_cols[0].split()[0].strip('"')
                    if col_name in table_info["columns"]:
                        table_info["columns"][col_name]["index"] = True

            # Skip primary key indexes
            if '_pkey' in index_name:
                continue
            
            # Skip indexes that back unique constraints (they shouldn't count as separate indexes)
            if index_name in constraint_indexes:
                continue
            
            table_info["indexes"].append({
                "name": index_name,
                "definition": index_def,
            })
        
        return table_info

    async def _introspect_table_async(self, conn, schema: str, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table (Async)."""
        table_info = {
            "schema": schema,
            "name": table_name,
            "columns": {},
            "constraints": [],
            "indexes": [],
            "unique_together": [],  # Multi-column unique constraints
        }
        
        # Get columns
        rows = await conn.fetch("""
            SELECT 
                column_name,
                data_type,
                udt_name,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """, schema, table_name)
        
        for row in rows:
            col_name = row['column_name']
            data_type = row['data_type'].upper()
            udt_name = row['udt_name']
            max_len = row['character_maximum_length']
            precision = row['numeric_precision']
            scale = row['numeric_scale']
            is_nullable = row['is_nullable'] == 'YES'
            default_value = row['column_default']
            
            # Normalize type name
            type_str = self._normalize_type(data_type, udt_name, max_len, precision, scale)
            
            table_info["columns"][col_name] = {
                "name": col_name,
                "type": type_str,
                "nullable": is_nullable,
                "default": default_value,
            }
        
        # Get primary keys
        rows = await conn.fetch("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_schema = $1 AND tc.table_name = $2
        """, schema, table_name)
        
        pk_columns = {row['column_name'] for row in rows}
        for col_name in pk_columns:
            if col_name in table_info["columns"]:
                table_info["columns"][col_name]["primary_key"] = True
        
        # Get unique constraints - only mark columns that are the ONLY column in a constraint
        # (multi-column unique constraints should be handled as unique_together, not individual uniques)
        rows = await conn.fetch("""
            SELECT kcu.column_name, tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'UNIQUE'
            AND tc.table_schema = $1 AND tc.table_name = $2
        """, schema, table_name)
        
        # Group columns by constraint name
        constraint_columns = {}
        for row in rows:
            col_name, constraint_name = row['column_name'], row['constraint_name']
            if constraint_name not in constraint_columns:
                constraint_columns[constraint_name] = []
            constraint_columns[constraint_name].append(col_name)
        
        # Only mark as unique if it's a single-column constraint
        # Store multi-column constraints separately in unique_together (with real names for DROP)
        for constraint_name, columns in constraint_columns.items():
            if len(columns) == 1:
                col_name = columns[0]
                if col_name in table_info["columns"]:
                    table_info["columns"][col_name]["unique"] = True
            else:
                # Multi-column unique constraint - store as dict with name and columns
                table_info["unique_together"].append({
                    "name": constraint_name,
                    "columns": tuple(sorted(columns))
                })
        
        # Get foreign keys
        rows = await conn.fetch("""
            SELECT 
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints rc
                ON tc.constraint_name = rc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = $1 AND tc.table_name = $2
        """, schema, table_name)
        
        for row in rows:
            col_name = row['column_name']
            fk_schema = row['foreign_table_schema']
            fk_table = row['foreign_table_name']
            fk_col = row['foreign_column_name']
            on_delete = row['delete_rule']
            
            if col_name in table_info["columns"]:
                table_info["columns"][col_name]["foreign_key"] = f"{fk_schema}.{fk_table}.{fk_col}"
                table_info["columns"][col_name]["on_delete"] = on_delete
        
        # Get indexes and mark indexed columns
        # First, get index names that back constraints (PK, UNIQUE) - we should ignore these
        constraint_rows = await conn.fetch("""
            SELECT c.conname, i.indexrelid::regclass::text as indexname
            FROM pg_constraint c
            JOIN pg_index i ON i.indexrelid = c.conindid
            WHERE c.conrelid = (
                SELECT oid FROM pg_class 
                WHERE relname = $1 
                AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = $2)
            )
            AND c.contype IN ('p', 'u')
        """, table_name, schema)
        constraint_indexes = {row['indexname'].split('.')[-1] for row in constraint_rows}
        
        rows = await conn.fetch("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = $1 AND tablename = $2
        """, schema, table_name)
        
        import re
        for row in rows:
            index_name = row['indexname']
            index_def = row['indexdef']
            
            # Extract column name from index definition 
            # Format: CREATE INDEX idx_xxx ON schema.table (column)
            # or: CREATE INDEX idx_xxx ON schema.table USING btree (column)
            match = re.search(r'\(([^)]+)\)$', index_def)
            if match:
                indexed_cols = [c.strip() for c in match.group(1).split(',')]
                # Only consider it a "column index" if it's a single column
                # Composite indexes don't satisfy simple column index=True requirements
                if len(indexed_cols) == 1:
                    col_name = indexed_cols[0].split()[0].strip('"')
                    if col_name in table_info["columns"]:
                        table_info["columns"][col_name]["index"] = True

            # Skip primary key indexes
            if '_pkey' in index_name:
                continue
            
            # Skip indexes that back unique constraints
            if index_name in constraint_indexes:
                continue
            
            table_info["indexes"].append({
                "name": index_name,
                "definition": index_def,
            })
        
        return table_info
    
    def _normalize_type(self, data_type: str, udt_name: str, max_len: Optional[int], 
                       precision: Optional[int], scale: Optional[int]) -> str:
        """Normalize PostgreSQL type names to match model DDL."""
        # Map common types
        type_map = {
            'CHARACTER VARYING': 'VARCHAR',
            'CHARACTER': 'CHAR',
            'INTEGER': 'INTEGER',
            'BIGINT': 'BIGINT',
            'SMALLINT': 'SMALLINT',
            'REAL': 'REAL',
            'DOUBLE PRECISION': 'DOUBLE PRECISION',
            'NUMERIC': 'NUMERIC',
            'BOOLEAN': 'BOOLEAN',
            'TEXT': 'TEXT',
            'BYTEA': 'BYTEA',
            'DATE': 'DATE',
            'TIMESTAMP WITHOUT TIME ZONE': 'TIMESTAMP',
            'TIMESTAMP WITH TIME ZONE': 'TIMESTAMP WITH TIME ZONE',
            'TIME WITHOUT TIME ZONE': 'TIME',
            'TIME WITH TIME ZONE': 'TIME WITH TIME ZONE',
            'INTERVAL': 'INTERVAL',
            'JSON': 'JSON',
            'JSONB': 'JSONB',
            'USER-DEFINED': udt_name.upper() if udt_name else 'TEXT',
            'ARRAY': 'ARRAY',
        }
        
        normalized = type_map.get(data_type, data_type)
        
        # Add length for VARCHAR/CHAR
        if normalized in ('VARCHAR', 'CHAR') and max_len:
            normalized = f"{normalized}({max_len})"
        
        # Add precision for NUMERIC
        if normalized == 'NUMERIC' and precision:
            if scale:
                normalized = f"{normalized}({precision},{scale})"
            else:
                normalized = f"{normalized}({precision})"
        
        return normalized
    
    def _get_model_tables(self, models: List[Type["PSQLModel"]]) -> Dict[str, Dict[str, Any]]:
        """Extract table definitions from model classes."""
        tables = {}
        
        for model in models:
            schema = getattr(model, '__schema__', 'public') or 'public'
            table_name = getattr(model, '__tablename__', model.__name__.lower())
            key = f"{schema}.{table_name}"
            
            columns = {}
            for col_name, col in getattr(model, '__columns__', {}).items():
                columns[col_name] = self.hasher.get_column_details(col)
            
            # Extract unique_together from __constraints__ (UniqueConstraint objects)
            # The @table decorator stores unique_together as UniqueConstraint in __constraints__
            from ..orm.table import UniqueConstraint
            unique_together = []
            for constraint in getattr(model, '__constraints__', []):
                if isinstance(constraint, UniqueConstraint):
                    # Get column names from constraint
                    col_names = []
                    for col in constraint.columns:
                        if isinstance(col, str):
                            col_names.append(col)
                        elif hasattr(col, 'name'):
                            col_names.append(col.name)
                    if len(col_names) > 1:  # Only multi-column constraints count as unique_together
                        # For model constraints, name is None (will be generated on ADD)
                        unique_together.append({
                            "name": constraint.name,  # Could be None or explicit name
                            "columns": tuple(sorted(col_names))
                        })
            
            tables[key] = {
                "schema": schema,
                "name": table_name,
                "columns": columns,
                "unique_together": unique_together,
                "model": model,
            }
        
        return tables
    
    def _compare_columns(self, model_col: Dict[str, Any], db_col: Dict[str, Any], 
                         col_name: str) -> List[Dict[str, Any]]:
        """Compare two column definitions and return changes.
        
        Returns format compatible with engine.py check_schema_drift():
        [{"change": "type_changed", "column": "email", "from": "VARCHAR(100)", "to": "VARCHAR(255)"}]
        """
        changes = []
        
        # Compare type
        model_type = model_col.get("type")
        db_type = db_col.get("type")
        if model_type and db_type and model_type != db_type:
            changes.append({
                "change": "type_changed",
                "column": col_name,
                "from": db_type,
                "to": model_type,
            })
        
        # Compare nullable
        model_nullable = model_col.get("nullable", True)
        db_nullable = db_col.get("nullable", True)
        if model_nullable != db_nullable:
            changes.append({
                "change": "nullable_changed",
                "column": col_name,
                "from": db_nullable,
                "to": model_nullable,
            })
        
        # Compare primary_key
        model_pk = model_col.get("primary_key", False)
        db_pk = db_col.get("primary_key", False)
        if model_pk != db_pk:
            changes.append({
                "change": "pk_changed",
                "column": col_name,
                "from": db_pk,
                "to": model_pk,
            })
        
        # Compare unique
        model_unique = model_col.get("unique", False)
        db_unique = db_col.get("unique", False)
        if model_unique != db_unique:
            changes.append({
                "change": "unique_changed",
                "column": col_name,
                "from": db_unique,
                "to": model_unique,
            })
        
        # Compare default
        model_default = model_col.get("default")
        db_default = db_col.get("default")
        # Normalize defaults for comparison
        norm_model = self._normalize_default(model_default)
        norm_db = self._normalize_default(db_default)
        if norm_model != norm_db:
            print(f"DEBUG: Default mismatch on {col_name}: Model='{norm_model}' vs DB='{norm_db}'")
            changes.append({
                "change": "default_changed",
                "column": col_name,
                "from": db_default,
                "to": model_default,
            })
        
        # Compare foreign_key
        model_fk = model_col.get("foreign_key")
        db_fk = db_col.get("foreign_key")
        
        # Normalize FKs to ensure consistent schema prefix
        def normalize_fk(fk):
            if not fk:
                return None
            fk_str = str(fk)
            parts = fk_str.split('.')
            if len(parts) == 2:
                # Missing schema, add 'public.' prefix
                return f"public.{fk_str}"
            return fk_str.lower() # Case insensitive since table names are lower
        
        norm_model_fk = normalize_fk(model_fk)
        norm_db_fk = normalize_fk(db_fk)
        
        if norm_model_fk != norm_db_fk:
            print(f"DEBUG: FK mismatch on {col_name}: Model='{norm_model_fk}' vs DB='{norm_db_fk}'")
            changes.append({
                "change": "fk_changed",
                "column": col_name,
                "from": db_fk,
                "to": model_fk,
            })
        
        # Compare on_delete
        model_on_delete = model_col.get("on_delete")
        db_on_delete = db_col.get("on_delete")
        if model_on_delete and db_on_delete and model_on_delete.upper() != db_on_delete.upper():
            # print(f"DEBUG: OnDelete mismatch on {col_name}: Model='{model_on_delete}' vs DB='{db_on_delete}'")
            changes.append({
                "change": "on_delete_changed",
                "column": col_name,
                "from": db_on_delete,
                "to": model_on_delete,
                "foreign_key": model_col.get("foreign_key"),  # Required to recreate the FK
            })
        
        # Compare index
        model_index = model_col.get("index", False)
        db_index = db_col.get("index", False)
        
        # If model defines unique=True, an index exists in DB backing it.
        # We shouldn't flag this as "index exists but model says no" drift (Drop Index).
        model_pk = model_col.get("primary_key", False)
        ignore_index_diff = (model_unique or model_pk) and db_index

        if model_index != db_index and not ignore_index_diff:
            changes.append({
                "change": "index_changed",
                "column": col_name,
                "from": db_index,
                "to": model_index,
            })
        
        return changes
    
    def _normalize_default(self, value: Any) -> Optional[str]:
        """Normalize default values for comparison."""
        if value is None:
            return None
        if callable(value):
            return "<callable>"
        
        # Handle boolean normalization (Python True -> 'true')
        if isinstance(value, bool):
            return str(value).lower()
        
        # PostgreSQL often wraps defaults in casting expressions
        str_val = str(value)
        # Remove type casts like ::integer, ::varchar
        if '::' in str_val:
            str_val = str_val.split('::')[0]
        # Remove quotes
        str_val = str_val.strip("'\"")
        
        # Normalize specific SQL function artifacts from Python objects or strings
        if 'gen_default_uuid' in str_val or 'gen_random_uuid' in str_val:
            return 'gen_random_uuid()'
        
        # Normalize all timestamp defaults to 'now()'
        # DB: CURRENT_TIMESTAMP, now(), '2025-...'::timestamp
        # Model: <function now>, now(), CURRENT_TIMESTAMP
        str_val_lower = str_val.lower()
        if any(x in str_val_lower for x in ['now', 'current_timestamp', '<function']):
            return 'now()'
        
        return str_val if str_val else None
    
    async def compare_async(self, models: List[Type["PSQLModel"]]) -> DiffResult:
        """Compare models against database (Async)."""
        db_tables = await self._get_db_tables_async()
        return self._compare_with_tables(models, db_tables)

    def compare(self, models: List[Type["PSQLModel"]]) -> DiffResult:
        """Compare models against database and return detailed diff.
        
        This is the main entry point, called by MigrationManager._compute_diff().
        """
        db_tables = self._get_db_tables()
        return self._compare_with_tables(models, db_tables)

    def _compare_with_tables(self, models: List[Type["PSQLModel"]], db_tables: Dict[str, Dict[str, Any]]) -> DiffResult:
        """Shared comparison logic."""
        result = DiffResult()
        
        model_tables = self._get_model_tables(models)
        
        # Find new tables (in models but not in DB)
        for key, model_data in model_tables.items():
            if key not in db_tables:
                result.new_tables.append(DiffItem(
                    object_name=key,
                    object_type="table",
                    details={
                        "columns": model_data["columns"],
                        "unique_together": model_data.get("unique_together", [])
                    }
                ))
        
        # Find removed tables (in DB but not in models)
        for key, db_data in db_tables.items():
            if key not in model_tables:
                result.removed_tables.append(DiffItem(
                    object_name=key,
                    object_type="table",
                    details={"columns": db_data["columns"]}
                ))
        
        # Find modified tables
        for key in model_tables:
            if key in db_tables:
                model_data = model_tables[key]
                db_data = db_tables[key]
                
                column_changes = []
                
                # Find added columns
                for col_name in model_data["columns"]:
                    if col_name not in db_data["columns"]:
                        column_changes.append({
                            "change": "added",
                            "column": col_name,
                        })
                
                # Find removed columns
                for col_name in db_data["columns"]:
                    if col_name not in model_data["columns"]:
                        column_changes.append({
                            "change": "removed",
                            "column": col_name,
                        })
                
                # Find modified columns
                for col_name in model_data["columns"]:
                    if col_name in db_data["columns"]:
                        changes = self._compare_columns(
                            model_data["columns"][col_name],
                            db_data["columns"][col_name],
                            col_name
                        )
                        column_changes.extend(changes)
                
                if column_changes:
                    result.modified_tables.append(DiffItem(
                        object_name=key,
                        object_type="table",
                        details={"column_changes": column_changes}
                    ))
                
                # Compare unique_together
                # Build lookup dictionaries: columns -> constraint info
                model_ut_list = model_data.get("unique_together", [])
                db_ut_list = db_data.get("unique_together", [])
                
                # Create column-based lookup
                model_cols_set = {ut["columns"] for ut in model_ut_list}
                db_cols_to_name = {ut["columns"]: ut["name"] for ut in db_ut_list}
                db_cols_set = set(db_cols_to_name.keys())
                
                # Find added unique_together (in model but not in DB)
                for ut in model_ut_list:
                    if ut["columns"] not in db_cols_set:
                        result.modified_tables.append(DiffItem(
                            object_name=key,
                            object_type="unique_together",
                            details={"change": "added", "columns": list(ut["columns"]), "name": ut.get("name")}
                        ))
                
                # Find removed unique_together (in DB but not in model)
                for ut in db_ut_list:
                    if ut["columns"] not in model_cols_set:
                        # Use the ACTUAL DB constraint name for DROP
                        result.modified_tables.append(DiffItem(
                            object_name=key,
                            object_type="unique_together",
                            details={"change": "removed", "columns": list(ut["columns"]), "name": ut["name"]}
                        ))
        
        return result
    
    def _get_db_triggers(self) -> Dict[str, Dict[str, Any]]:
        """Introspect database to get trigger definitions."""
        dsn = self.engine._build_sync_dsn()
        triggers = {}
        
        try:
            conn = psycopg.connect(dsn)
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT 
                        trigger_name,
                        event_object_schema,
                        event_object_table,
                        action_timing,
                        event_manipulation,
                        action_statement
                    FROM information_schema.triggers
                    WHERE trigger_schema NOT IN ('pg_catalog', 'information_schema')
                """)
                
                for row in cur.fetchall():
                    name = row[0]
                    triggers[name] = {
                        "name": name,
                        "schema": row[1],
                        "table": row[2],
                        "timing": row[3],
                        "event": row[4],
                        "statement": row[5],
                    }
                
                cur.close()
            finally:
                conn.close()
        except Exception:
            pass
        
        return triggers

    async def _get_db_triggers_async(self) -> Dict[str, Dict[str, Any]]:
        """Introspect database to get trigger definitions (Async)."""
        dsn = self.engine._build_async_dsn()
        triggers = {}
        
        try:
            conn = await asyncpg.connect(dsn)
            try:
                rows = await conn.fetch("""
                    SELECT 
                        trigger_name,
                        event_object_schema,
                        event_object_table,
                        action_timing,
                        event_manipulation,
                        action_statement
                    FROM information_schema.triggers
                    WHERE trigger_schema NOT IN ('pg_catalog', 'information_schema')
                """)
                
                for row in rows:
                    name = row['trigger_name']
                    triggers[name] = {
                        "name": name,
                        "schema": row['event_object_schema'],
                        "table": row['event_object_table'],
                        "timing": row['action_timing'],
                        "event": row['event_manipulation'],
                        "statement": row['action_statement'],
                    }
                
            finally:
                await conn.close()
        except Exception:
            pass
        
        return triggers
