"""
PSQLModel Migration System - DDL Generator

Generates SQL DDL statements from schema diffs.
"""

from typing import List, Tuple, Dict, Any, Optional, TYPE_CHECKING

from .diff import DiffResult, DiffItem

if TYPE_CHECKING:
    from ..orm.column import Column
    from ..orm.table import Constraint, Index


class DDLGenerator:
    """Generates SQL DDL statements from diff results."""
    
    # =========================================================================
    # SAFE TYPE CONVERSIONS MAP
    # =========================================================================
    # Maps (from_type, to_type) -> conversion strategy
    # True = Safe, no USING needed (PostgreSQL auto-converts)
    # "USING" = Requires explicit USING clause with cast
    # "USING_FUNC" = Requires USING with specific function
    # str = Custom USING expression
    # =========================================================================
    
    SAFE_TYPE_CONVERSIONS: dict = {
        # =====================================================================
        # NUMERIC TYPES
        # =====================================================================
        # Widening (safe - no data loss)
        ("SMALLINT", "INTEGER"): True,
        ("SMALLINT", "BIGINT"): True,
        ("INTEGER", "BIGINT"): True,
        ("REAL", "DOUBLE PRECISION"): True,
        ("REAL", "NUMERIC"): True,
        ("DOUBLE PRECISION", "NUMERIC"): True,
        
        # Narrowing (requires USING, may lose precision/overflow)
        ("BIGINT", "INTEGER"): "USING",
        ("BIGINT", "SMALLINT"): "USING",
        ("INTEGER", "SMALLINT"): "USING",
        ("DOUBLE PRECISION", "REAL"): "USING",
        ("NUMERIC", "REAL"): "USING",
        ("NUMERIC", "DOUBLE PRECISION"): "USING",
        ("NUMERIC", "INTEGER"): "USING",
        ("NUMERIC", "BIGINT"): "USING",
        ("NUMERIC", "SMALLINT"): "USING",
        
        # Numeric <-> Decimal (aliases in PostgreSQL)
        ("NUMERIC", "DECIMAL"): True,
        ("DECIMAL", "NUMERIC"): True,
        
        # Money conversions
        ("MONEY", "NUMERIC"): "USING",
        ("NUMERIC", "MONEY"): True,
        ("MONEY", "TEXT"): "USING",
        
        # Serial types (internal representation is INTEGER/BIGINT)
        ("SERIAL", "INTEGER"): True,
        ("INTEGER", "SERIAL"): True,
        ("BIGSERIAL", "BIGINT"): True,
        ("BIGINT", "BIGSERIAL"): True,
        ("SMALLSERIAL", "SMALLINT"): True,
        ("SMALLINT", "SMALLSERIAL"): True,
        ("SERIAL", "BIGSERIAL"): True,
        ("BIGSERIAL", "SERIAL"): "USING",
        
        # =====================================================================
        # TEXT TYPES
        # =====================================================================
        # VARCHAR/TEXT/CHAR conversions (generally safe)
        ("VARCHAR", "TEXT"): True,
        ("TEXT", "VARCHAR"): True,  # May truncate if too long
        ("CHAR", "TEXT"): True,
        ("TEXT", "CHAR"): True,  # May truncate
        ("CHAR", "VARCHAR"): True,
        ("VARCHAR", "CHAR"): True,
        
        # Any type to TEXT (stringify)
        ("INTEGER", "TEXT"): "USING",
        ("BIGINT", "TEXT"): "USING",
        ("SMALLINT", "TEXT"): "USING",
        ("BOOLEAN", "TEXT"): "USING",
        ("REAL", "TEXT"): "USING",
        ("DOUBLE PRECISION", "TEXT"): "USING",
        ("NUMERIC", "TEXT"): "USING",
        ("UUID", "TEXT"): "USING",
        ("JSON", "TEXT"): "USING",
        ("JSONB", "TEXT"): "USING",
        ("XML", "TEXT"): "USING",
        ("INET", "TEXT"): "USING",
        ("CIDR", "TEXT"): "USING",
        ("MACADDR", "TEXT"): "USING",
        ("MACADDR8", "TEXT"): "USING",
        
        # TEXT to numeric (requires parsing)
        ("TEXT", "INTEGER"): "USING",
        ("TEXT", "BIGINT"): "USING",
        ("TEXT", "SMALLINT"): "USING",
        ("TEXT", "NUMERIC"): "USING",
        ("TEXT", "REAL"): "USING",
        ("TEXT", "DOUBLE PRECISION"): "USING",
        ("TEXT", "UUID"): "USING",
        ("TEXT", "BOOLEAN"): "{col}::boolean",  # Custom expression
        ("VARCHAR", "INTEGER"): "USING",
        ("VARCHAR", "BIGINT"): "USING",
        ("VARCHAR", "UUID"): "USING",
        
        # BIT types
        ("BIT", "VARBIT"): True,
        ("VARBIT", "BIT"): True,
        ("BIT", "TEXT"): "USING",
        ("VARBIT", "TEXT"): "USING",
        
        # =====================================================================
        # DATE/TIME TYPES
        # =====================================================================
        # Timestamp conversions
        ("TIMESTAMP", "TIMESTAMPTZ"): True,  # Assumes UTC/local
        ("TIMESTAMPTZ", "TIMESTAMP"): True,  # Loses timezone
        ("TIMESTAMP", "DATE"): "USING",  # Truncates time
        ("DATE", "TIMESTAMP"): True,  # Adds 00:00:00
        ("TIMESTAMP", "TIME"): "USING",  # Extracts time
        ("TIMESTAMPTZ", "DATE"): "USING",
        ("DATE", "TIMESTAMPTZ"): True,
        
        # Time conversions
        ("TIME", "TIMETZ"): True,
        ("TIMETZ", "TIME"): True,
        ("TIME", "INTERVAL"): True,
        ("TIME", "TEXT"): "USING",
        ("TIMETZ", "TEXT"): "USING",
        
        # Date/Timestamp to text
        ("DATE", "TEXT"): "USING",
        ("TIMESTAMP", "TEXT"): "USING",
        ("TIMESTAMPTZ", "TEXT"): "USING",
        ("INTERVAL", "TEXT"): "USING",
        
        # Text to date/time
        ("TEXT", "DATE"): "USING",
        ("TEXT", "TIMESTAMP"): "USING",
        ("TEXT", "TIMESTAMPTZ"): "USING",
        ("TEXT", "TIME"): "USING",
        ("TEXT", "INTERVAL"): "USING",
        
        # =====================================================================
        # JSON TYPES
        # =====================================================================
        ("JSON", "JSONB"): "USING",
        ("JSONB", "JSON"): "USING",
        ("TEXT", "JSON"): "USING",
        ("TEXT", "JSONB"): "USING",
        
        # =====================================================================
        # UUID TYPES
        # =====================================================================
        ("UUID", "VARCHAR"): "USING",
        ("VARCHAR", "UUID"): "USING",
        ("TEXT", "UUID"): "USING",
        ("UUID", "TEXT"): "USING",
        
        # =====================================================================
        # BOOLEAN TYPES
        # =====================================================================
        ("BOOLEAN", "INTEGER"): "{col}::integer",
        ("INTEGER", "BOOLEAN"): "{col} <> 0",
        ("SMALLINT", "BOOLEAN"): "{col} <> 0",
        ("TEXT", "BOOLEAN"): "CASE WHEN {col} IN ('true', 't', '1', 'yes', 'on') THEN true ELSE false END",
        ("BOOLEAN", "TEXT"): "USING",
        
        # =====================================================================
        # NETWORK TYPES
        # =====================================================================
        ("INET", "CIDR"): "USING",
        ("CIDR", "INET"): True,
        ("INET", "TEXT"): "USING",
        ("CIDR", "TEXT"): "USING",
        ("TEXT", "INET"): "USING",
        ("TEXT", "CIDR"): "USING",
        ("MACADDR", "MACADDR8"): True,
        ("MACADDR8", "MACADDR"): "USING",
        ("TEXT", "MACADDR"): "USING",
        ("TEXT", "MACADDR8"): "USING",
        
        # =====================================================================
        # GEOMETRIC TYPES
        # =====================================================================
        ("POINT", "TEXT"): "USING",
        ("LINE", "TEXT"): "USING",
        ("LSEG", "TEXT"): "USING",
        ("BOX", "TEXT"): "USING",
        ("PATH", "TEXT"): "USING",
        ("POLYGON", "TEXT"): "USING",
        ("CIRCLE", "TEXT"): "USING",
        ("TEXT", "POINT"): "USING",
        ("TEXT", "LINE"): "USING",
        ("TEXT", "LSEG"): "USING",
        ("TEXT", "BOX"): "USING",
        ("TEXT", "PATH"): "USING",
        ("TEXT", "POLYGON"): "USING",
        ("TEXT", "CIRCLE"): "USING",
        
        # =====================================================================
        # RANGE TYPES
        # =====================================================================
        ("INT4RANGE", "INT8RANGE"): "USING",
        ("INT8RANGE", "INT4RANGE"): "USING",
        ("TSRANGE", "TSTZRANGE"): "USING",
        ("TSTZRANGE", "TSRANGE"): "USING",
        ("NUMRANGE", "TEXT"): "USING",
        ("DATERANGE", "TEXT"): "USING",
        ("INT4RANGE", "TEXT"): "USING",
        ("INT8RANGE", "TEXT"): "USING",
        
        # =====================================================================
        # SPECIAL TYPES
        # =====================================================================
        ("XML", "TEXT"): "USING",
        ("TEXT", "XML"): "USING",
        ("TSVECTOR", "TEXT"): "USING",
        ("TEXT", "TSVECTOR"): "to_tsvector('english', {col})",
        ("TSQUERY", "TEXT"): "USING",
        ("TEXT", "TSQUERY"): "to_tsquery('english', {col})",
        
        # BYTEA
        ("BYTEA", "TEXT"): "encode({col}, 'hex')",
        ("TEXT", "BYTEA"): "decode({col}, 'hex')",
    }
    
    def generate_add_column(self, table: str, schema: str, 
                           col_name: str, col_def: str) -> str:
        """Generate ALTER TABLE ADD COLUMN statement."""
        return f"ALTER TABLE {schema}.{table} ADD COLUMN {col_name} {col_def};"
    
    def generate_drop_column(self, table: str, schema: str, col_name: str) -> str:
        """Generate ALTER TABLE DROP COLUMN statement."""
        return f"ALTER TABLE {schema}.{table} DROP COLUMN {col_name};"
    
    def generate_alter_column_type(self, table: str, schema: str, 
                                   col_name: str, new_type: str,
                                   old_type: str = None) -> str:
        """Generate ALTER COLUMN TYPE statement with safe conversion handling.
        
        Args:
            table: Table name
            schema: Schema name
            col_name: Column name
            new_type: Target type
            old_type: Source type (optional, for intelligent USING clause)
            
        Returns:
            ALTER TABLE statement with appropriate USING clause if needed
        """
        # Normalize type names for lookup
        old_upper = old_type.upper().split("(")[0].strip() if old_type else None
        new_upper = new_type.upper().split("(")[0].strip()
        
        base_sql = f"ALTER TABLE {schema}.{table} ALTER COLUMN {col_name} TYPE {new_type}"
        
        # Check for array types (simple [] notation)
        if old_upper and old_upper.endswith("[]") and new_upper.endswith("[]"):
            base_old = old_upper[:-2]
            base_new = new_upper[:-2]
            # Check if base types have a known conversion
            array_key = (base_old, base_new)
            base_conversion = self.SAFE_TYPE_CONVERSIONS.get(array_key)
            
            if base_conversion is True or base_conversion == "USING":
                # If base conversion is standard, array cast usually works
                return f"{base_sql} USING {col_name}::{new_type};"

        # Check if we have a known conversion
        if old_upper:
            key = (old_upper, new_upper)
            conversion = self.SAFE_TYPE_CONVERSIONS.get(key)
            
            if conversion is True:
                # Safe conversion, no USING needed
                return f"{base_sql};"
            elif conversion == "USING":
                # Standard USING with cast
                return f"{base_sql} USING {col_name}::{new_type};"
            elif isinstance(conversion, str):
                # Custom USING expression
                using_expr = conversion.replace("{col}", col_name)
                return f"{base_sql} USING {using_expr};"
            
            # Warning for unknown conversions
            import sys
            print(f"[WARNING] Unknown type conversion: {old_type} -> {new_type} on {table}.{col_name}. "
                  f"Generating explicit cast, but verify data safety.", file=sys.stderr)
        
        # Default: use USING with cast for safety
        return f"{base_sql} USING {col_name}::{new_type};"
    
    def generate_alter_column_nullable(self, table: str, schema: str, 
                                       col_name: str, nullable: bool) -> str:
        """Generate SET/DROP NOT NULL statement."""
        action = "DROP NOT NULL" if nullable else "SET NOT NULL"
        return f"ALTER TABLE {schema}.{table} ALTER COLUMN {col_name} {action};"
    
    def generate_alter_column_default(self, table: str, schema: str, 
                                      col_name: str, default: Optional[str]) -> str:
        """Generate SET/DROP DEFAULT statement."""
        if default is None:
            return f"ALTER TABLE {schema}.{table} ALTER COLUMN {col_name} DROP DEFAULT;"
        
        # Handle callables/objects by converting to SQL
        default_str = str(default)
        if 'gen_default_uuid' in default_str or 'gen_random_uuid' in default_str:
            return f"ALTER TABLE {schema}.{table} ALTER COLUMN {col_name} SET DEFAULT gen_random_uuid();"
        if 'now' in default_str or 'current_timestamp' in default_str:
            return f"ALTER TABLE {schema}.{table} ALTER COLUMN {col_name} SET DEFAULT CURRENT_TIMESTAMP;"
            
        return f"ALTER TABLE {schema}.{table} ALTER COLUMN {col_name} SET DEFAULT {default};"
    
    def generate_add_unique(self, table: str, schema: str, col_name: str) -> str:
        """Generate ADD UNIQUE CONSTRAINT statement (idempotent)."""
        constraint_name = f"uq_{table}_{col_name}"
        # Drop first to make idempotent
        drop_sql = f"ALTER TABLE {schema}.{table} DROP CONSTRAINT IF EXISTS {constraint_name};"
        add_sql = f"ALTER TABLE {schema}.{table} ADD CONSTRAINT {constraint_name} UNIQUE ({col_name});"
        return f"{drop_sql}\n{add_sql}"
    
    def generate_drop_unique(self, table: str, schema: str, col_name: str) -> str:
        """Generate DROP UNIQUE CONSTRAINT statement."""
        constraint_name = f"uq_{table}_{col_name}"
        return f"ALTER TABLE {schema}.{table} DROP CONSTRAINT IF EXISTS {constraint_name};"
    
    def generate_add_foreign_key(self, table: str, schema: str, col_name: str,
                                 ref_table: str, ref_col: str, 
                                 on_delete: Optional[str] = None) -> str:
        """Generate ADD FOREIGN KEY CONSTRAINT statement (idempotent).
        
        Ensures schema is included in reference if not already present.
        """
        constraint_name = f"fk_{table}_{col_name}"
        
        # Ensure ref_table has schema prefix
        if "." not in ref_table:
            ref_table = f"public.{ref_table}"
        
        # Drop first to make idempotent
        drop_sql = f"ALTER TABLE {schema}.{table} DROP CONSTRAINT IF EXISTS {constraint_name};"
        add_sql = f"ALTER TABLE {schema}.{table} ADD CONSTRAINT {constraint_name} " \
                  f"FOREIGN KEY ({col_name}) REFERENCES {ref_table}({ref_col})"
        if on_delete:
            add_sql += f" ON DELETE {on_delete}"
        add_sql += ";"
        return f"{drop_sql}\n{add_sql}"
    
    def generate_drop_foreign_key(self, table: str, schema: str, col_name: str) -> str:
        """Generate DROP FOREIGN KEY CONSTRAINT statement."""
        constraint_name = f"fk_{table}_{col_name}"
        return f"ALTER TABLE {schema}.{table} DROP CONSTRAINT IF EXISTS {constraint_name};"
    
    def generate_add_unique_together(self, table: str, schema: str, columns: List[str]) -> str:
        """Generate ADD UNIQUE CONSTRAINT statement for multi-column (idempotent).
        
        Generates constraint name based on first 3 columns to avoid exceeding identifier limits.
        """
        # Truncate to avoid long constraint names (PostgreSQL limit ~63 chars)
        constraint_suffix = "_".join(columns[:3])
        constraint_name = f"uq_{table}_{constraint_suffix}"[:63]
        cols = ", ".join(columns)
        # Drop first to make idempotent
        drop_sql = f"ALTER TABLE {schema}.{table} DROP CONSTRAINT IF EXISTS {constraint_name};"
        add_sql = f"ALTER TABLE {schema}.{table} ADD CONSTRAINT {constraint_name} UNIQUE ({cols});"
        return f"{drop_sql}\n{add_sql}"
    
    def generate_drop_unique_together(self, table: str, schema: str, columns: List[str]) -> str:
        """Generate DROP UNIQUE CONSTRAINT statement for multi-column."""
        constraint_suffix = "_".join(columns[:3])
        constraint_name = f"uq_{table}_{constraint_suffix}"[:63]
        return f"ALTER TABLE {schema}.{table} DROP CONSTRAINT IF EXISTS {constraint_name};"
    
    def generate_create_index(self, table: str, schema: str, col_name: str,
                             method: Optional[str] = None, unique: bool = False) -> str:
        """Generate CREATE INDEX statement."""
        index_name = f"idx_{table}_{col_name}"
        unique_sql = "UNIQUE " if unique else ""
        method_sql = f"USING {method} " if method else ""
        return f"CREATE {unique_sql}INDEX IF NOT EXISTS {index_name} "\
               f"ON {schema}.{table} {method_sql}({col_name});"
    
    def generate_drop_index(self, schema: str, index_name: str) -> str:
        """Generate DROP INDEX statement."""
        return f"DROP INDEX IF EXISTS {schema}.{index_name};"
    
    def generate_create_table(self, table: str, schema: str, 
                             columns: Dict[str, Dict[str, Any]]) -> str:
        """Generate CREATE TABLE statement."""
        col_defs = []
        for col_name, col_data in columns.items():
            col_def = f"{col_name} {col_data.get('type', 'TEXT')}"
            if col_data.get('primary_key'):
                col_def += " PRIMARY KEY"
            if not col_data.get('nullable', True):
                col_def += " NOT NULL"
            if col_data.get('unique'):
                col_def += " UNIQUE"
            if col_data.get('default') is not None:
                def_val = col_data['default']
                if isinstance(def_val, str):
                    # Quote strings and escape single quotes
                    safe_val = def_val.replace("'", "''")
                    col_def += f" DEFAULT '{safe_val}'"
                elif isinstance(def_val, bool):
                    # Lowercase boolean
                    col_def += f" DEFAULT {str(def_val).lower()}"
                else:
                    col_def += f" DEFAULT {def_val}"
            col_defs.append(col_def)
        
        return f"CREATE TABLE IF NOT EXISTS {schema}.{table} (\n    " + \
               ",\n    ".join(col_defs) + "\n);"
    
    def generate_drop_table(self, table: str, schema: str) -> str:
        """Generate DROP TABLE statement."""
        return f"DROP TABLE IF EXISTS {schema}.{table};"
    
    def generate_from_diff(self, diff: DiffResult, drop_orphans: bool = False) -> Tuple[List[str], List[str]]:
        """Generate SQL statements from diff result.
        
        Args:
            diff: The computed schema difference
            drop_orphans: If True, generate DROP TABLE for removed tables
            
        Returns:
            Tuple of (up_statements, down_statements)
        """
        up_statements = []
        down_statements = []
        
        # New tables
        for item in diff.new_tables:
            schema, table = self._parse_object_name(item.object_name)
            columns = item.details.get("columns", {})
            
            up_statements.append(f"-- Create table {item.object_name}")
            if columns:
                up_statements.append(self.generate_create_table(table, schema, columns))
                
                # Create Foreign Keys for new table
                for col_name, col_data in columns.items():
                    fk = col_data.get("foreign_key")
                    if fk:
                        # Handle string FKs like "schema.table.col"
                        parts = str(fk).split(".")
                        if len(parts) >= 2:
                            ref_table = ".".join(parts[:-1])
                            ref_col = parts[-1]
                            on_delete = col_data.get("on_delete")
                            
                            up_statements.append(
                                self.generate_add_foreign_key(table, schema, col_name,
                                                            ref_table, ref_col, 
                                                            on_delete=on_delete)
                            )
                
                # Create Indexes for new table
                for col_name, col_data in columns.items():
                    if col_data.get("index"):
                        method = col_data.get("index_method")
                        up_statements.append(
                            self.generate_create_index(table, schema, col_name, method=method)
                        )
                
                # Create Unique Constraints (unique_together) for new table
                unique_together = item.details.get("unique_together", [])
                for ut in unique_together:
                    # ut is a dict {name: ..., columns: ...}
                    columns_ut = ut.get("columns", [])
                    if columns_ut:
                        # Convert to list of strings if it's a tuple
                        columns_list = list(columns_ut)
                        up_statements.append(
                            self.generate_add_unique_together(table, schema, columns_list)
                        )
            else:
                # Fallback for empty table
                up_statements.append(f"CREATE TABLE IF NOT EXISTS {schema}.{table} ();")
            
            down_statements.append(self.generate_drop_table(table, schema))
        
        # Removed tables
        # Removed tables (orphan tables in DB not in models)
        for item in diff.removed_tables:
            schema, table = self._parse_object_name(item.object_name)
            if drop_orphans:
                # Generate actual DROP TABLE statements
                up_statements.append(f"DROP TABLE IF EXISTS {schema}.{table} CASCADE;")
                # For down, we can't recreate the table without knowing the full schema
                down_statements.append(f"-- Cannot recreate {schema}.{table} - backup table structure before dropping")
            else:
                # Just add warning comments
                up_statements.append(f"-- WARNING: Table {schema}.{table} exists in DB but not in models (orphan)")
                up_statements.append(f"-- To drop: DROP TABLE IF EXISTS {schema}.{table};")
        
        # Modified tables
        for item in diff.modified_tables:
            schema, table = self._parse_object_name(item.object_name)
            
            # Handle unique_together changes
            if item.object_type == "unique_together":
                change_type = item.details.get("change")
                columns = item.details.get("columns", [])
                
                if change_type == "added":
                    up_statements.append(
                        self.generate_add_unique_together(table, schema, columns)
                    )
                    down_statements.append(
                        self.generate_drop_unique_together(table, schema, columns)
                    )
                elif change_type == "removed":
                    # Use actual DB constraint name for DROP
                    constraint_name = item.details.get("name")
                    if constraint_name:
                        up_statements.append(
                            f"ALTER TABLE {schema}.{table} DROP CONSTRAINT IF EXISTS \"{constraint_name}\";"
                        )
                    else:
                        up_statements.append(
                            self.generate_drop_unique_together(table, schema, columns)
                        )
                    down_statements.append(
                        self.generate_add_unique_together(table, schema, columns)
                    )
                continue  # Skip column processing for unique_together items
            
            column_changes = item.details.get("column_changes", [])
            
            for change in column_changes:
                change_type = change.get("change")
                col_name = change.get("column")
                from_val = change.get("from")
                to_val = change.get("to")
                
                if change_type == "added":
                    up_statements.append(
                        f"ALTER TABLE {schema}.{table} ADD COLUMN {col_name} TEXT;"
                    )
                    down_statements.append(
                        self.generate_drop_column(table, schema, col_name)
                    )
                
                elif change_type == "removed":
                    up_statements.append(
                        self.generate_drop_column(table, schema, col_name)
                    )
                    down_statements.append(
                        f"ALTER TABLE {schema}.{table} ADD COLUMN {col_name} TEXT;"
                    )
                
                elif change_type == "type_changed":
                    up_statements.append(
                        self.generate_alter_column_type(table, schema, col_name, to_val, old_type=from_val)
                    )
                    down_statements.append(
                        self.generate_alter_column_type(table, schema, col_name, from_val, old_type=to_val)
                    )
                
                elif change_type == "nullable_changed":
                    up_statements.append(
                        self.generate_alter_column_nullable(table, schema, col_name, to_val)
                    )
                    down_statements.append(
                        self.generate_alter_column_nullable(table, schema, col_name, from_val)
                    )
                
                elif change_type == "default_changed":
                    up_statements.append(
                        self.generate_alter_column_default(table, schema, col_name, to_val)
                    )
                    down_statements.append(
                        self.generate_alter_column_default(table, schema, col_name, from_val)
                    )
                
                elif change_type == "unique_changed":
                    if to_val:
                        up_statements.append(self.generate_add_unique(table, schema, col_name))
                        down_statements.append(self.generate_drop_unique(table, schema, col_name))
                    else:
                        up_statements.append(self.generate_drop_unique(table, schema, col_name))
                        down_statements.append(self.generate_add_unique(table, schema, col_name))
                
                elif change_type == "fk_changed":
                    if to_val:
                        # Parse ref table and column
                        parts = to_val.split(".")
                        if len(parts) >= 2:
                            ref_table = ".".join(parts[:-1])
                            ref_col = parts[-1]
                            up_statements.append(
                                self.generate_add_foreign_key(table, schema, col_name, 
                                                            ref_table, ref_col)
                            )
                            down_statements.append(
                                self.generate_drop_foreign_key(table, schema, col_name)
                            )
                    else:
                        up_statements.append(
                            self.generate_drop_foreign_key(table, schema, col_name)
                        )
                        if from_val:
                            parts = from_val.split(".")
                            if len(parts) >= 2:
                                ref_table = ".".join(parts[:-1])
                                ref_col = parts[-1]
                                down_statements.append(
                                    self.generate_add_foreign_key(table, schema, col_name, 
                                                                ref_table, ref_col)
                                )
                
                elif change_type == "on_delete_changed":
                    fk_val = change.get("foreign_key")
                    if fk_val:
                        parts = fk_val.split(".")
                        if len(parts) >= 2:
                            ref_table = ".".join(parts[:-1])
                            ref_col = parts[-1]
                            on_delete = to_val
                            
                            up_statements.append(
                                self.generate_drop_foreign_key(table, schema, col_name)
                            )
                            up_statements.append(
                                self.generate_add_foreign_key(table, schema, col_name,
                                                            ref_table, ref_col,
                                                            on_delete=on_delete)
                            )
                            
                            down_statements.append(
                                self.generate_drop_foreign_key(table, schema, col_name)
                            )
                            down_statements.append(
                                self.generate_add_foreign_key(table, schema, col_name,
                                                            ref_table, ref_col,
                                                            on_delete=from_val)
                            )

                elif change_type == "index_changed":
                    if to_val:
                        method = to_val if isinstance(to_val, str) else None
                        up_statements.append(
                            self.generate_create_index(table, schema, col_name, method)
                        )
                        down_statements.append(
                            self.generate_drop_index(schema, f"idx_{table}_{col_name}")
                        )
                    else:
                        up_statements.append(
                            self.generate_drop_index(schema, f"idx_{table}_{col_name}")
                        )
                        if from_val:
                            method = from_val if isinstance(from_val, str) else None
                            down_statements.append(
                                self.generate_create_index(table, schema, col_name, method)
                            )
        
        return up_statements, down_statements
    
    def _parse_object_name(self, name: str) -> Tuple[str, str]:
        """Parse 'schema.table' into (schema, table)."""
        parts = name.split(".", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return "public", parts[0]
