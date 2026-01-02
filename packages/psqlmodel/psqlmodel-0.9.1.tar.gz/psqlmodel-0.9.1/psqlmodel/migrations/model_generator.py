"""
PSQLModel Migration System - Model Generator

Generates PSQLModel class files from database introspection.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.engine import Engine


class ModelGenerator:
    """Generate PSQLModel class files from database tables.
    
    Used to create draft model files for orphan tables (tables in DB but not in models).
    """
    
    # Type mapping from PostgreSQL to psqlmodel types
    TYPE_MAP = {
        'INTEGER': 'integer',
        'BIGINT': 'bigint',
        'SMALLINT': 'smallint',
        'SERIAL': 'serial',
        'BIGSERIAL': 'bigserial',
        'REAL': 'real',
        'DOUBLE PRECISION': 'double',
        'NUMERIC': 'numeric',
        'BOOLEAN': 'boolean',
        'TEXT': 'text',
        'VARCHAR': 'varchar',
        'CHARACTER VARYING': 'varchar',
        'CHAR': 'char',
        'UUID': 'uuid',
        'DATE': 'date',
        'TIMESTAMP': 'timestamp',
        'TIMESTAMP WITHOUT TIME ZONE': 'timestamp',
        'TIMESTAMP WITH TIME ZONE': 'timestamptz',
        'TIME': 'time',
        'INTERVAL': 'interval',
        'JSONB': 'jsonb',
        'JSON': 'json',
        'BYTEA': 'bytea',
        'INET': 'inet',
        'CIDR': 'cidr',
        'MACADDR': 'macaddr',
        'ARRAY': 'array',
        'POINT': 'point',
        'XML': 'xml',
        'TSVECTOR': 'tsvector',
    }
    
    # Defaults that need imports from utils
    DEFAULT_FUNCS = {
        'gen_random_uuid()': 'gen_default_uuid',
        'now()': 'now',
        'current_timestamp': 'now',
    }
    
    def __init__(self, engine: "Engine"):
        self.engine = engine
    
    def generate_model_for_table(self, schema: str, table_name: str, 
                                  table_info: Dict[str, Any]) -> str:
        """Generate Python model code for a table."""
        class_name = self._to_pascal_case(table_name)
        
        # Collect which types and utils are needed
        types_needed = set()
        utils_needed = set()
        
        columns = table_info.get('columns', {})
        for col_data in columns.values():
            # Type
            db_type = col_data.get('type', 'TEXT')
            base_type = db_type.split('(')[0].upper()
            psql_type = self.TYPE_MAP.get(base_type, 'text')
            types_needed.add(psql_type)
            
            # Default
            default = col_data.get('default', '')
            if default:
                default_lower = str(default).lower()
                if 'gen_random_uuid()' in default_lower:
                    utils_needed.add('gen_default_uuid')
                elif 'now()' in default_lower or 'current_timestamp' in default_lower:
                    utils_needed.add('now')
        
        # Build imports
        lines = [
            '"""',
            f'Draft model for table: {schema}.{table_name}',
            f'Generated: {datetime.now().isoformat()}',
            '',
            'REVIEW THIS FILE before integrating into your codebase.',
            'Pay special attention to auto-generated relationships - verify they match your intended schema.',
            '"""',
            '',
            'from psqlmodel import PSQLModel, Column, table',
        ]
        
        # Check for CHECK constraints
        check_constraints = table_info.get('check_constraints', [])
        needs_check_import = bool(check_constraints)
        
        # Check for foreign keys (for Relation/Relationship import)
        has_foreign_keys = any(col.get('foreign_key') for col in columns.values())
        has_reverse_fks = bool(table_info.get('reverse_fks'))
        
        # Add type imports
        if types_needed:
            types_list = ', '.join(sorted(types_needed))
            lines.append(f'from psqlmodel.types import {types_list}')
        
        # Add utils imports
        if utils_needed:
            utils_list = ', '.join(sorted(utils_needed))
            lines.append(f'from psqlmodel.utils import {utils_list}')
        
        # Add Relation/Relationship import if there are any relationships
        if has_foreign_keys or has_reverse_fks:
            lines.append('from psqlmodel import Relation, Relationship')
        
        # Add CheckConstraint import if needed
        if needs_check_import:
            lines.append('from psqlmodel.orm.table import CheckConstraint')
        
        # Add Index import if needed
        indexes = table_info.get('indexes', [])
        if any(not idx.get('is_constraint') for idx in indexes):
             lines.append('from psqlmodel.orm.table import Index')
        
        lines.extend(['', ''])
        
        # Table decorator arguments
        decorator_args = []
        if check_constraints:
            constraints_list = []
            for ck in check_constraints:
                name = ck.get('name', '')
                expr = ck.get('expression', '').replace('"', '\\"')
                constraints_list.append(f'CheckConstraint("{expr}", name="{name}")')
            
            constraints_str = ', '.join(constraints_list)
            decorator_args.append(f'constraints=[{constraints_str}]')
        
        # unique_together
        unique_together = table_info.get('unique_together', [])
        if unique_together:
            ut_list = []
            for cols in unique_together:
                # ["col1", "col2"] -> '["col1", "col2"]'
                # repr() works well for list of strings
                ut_list.append(repr(cols).replace("'", '"'))
            
            ut_str = ', '.join(ut_list)
            decorator_args.append(f'unique_together=[{ut_str}]')
            
        # indexes
        indexes = table_info.get('indexes', [])
        index_list = []
        if indexes:
             for idx in indexes:
                 idx_name = idx.get('name')
                 idx_cols = idx.get('columns', [])
                 unique = idx.get('unique', False)
                 # Only generate if not PK/Unique constraint/Primary
                 if not idx.get('is_constraint') and not idx.get('is_primary'):
                      cols_str = ', '.join([f'"{c}"' for c in idx_cols])
                      index_list.append(f'Index({cols_str}, name="{idx_name}", unique={unique})')
        
        if index_list:
            indexes_str = ', '.join(index_list)
            decorator_args.append(f'indexes=[{indexes_str}]')

        # Build decorator
        if schema != 'public':
            decorator_args.insert(0, f'schema="{schema}"')
        
        args_str = ', '.join(decorator_args)
        lines.append(f'@table("{table_name}", {args_str})')
        
        lines.append(f'class {class_name}(PSQLModel):')
        lines.append(f'    """Model for {schema}.{table_name}."""')
        lines.append('')
        
        # Columns
        columns = table_info.get('columns', {})
        for col_name, col_data in columns.items():
            col_line = self._generate_column_line(col_name, col_data)
            lines.append(f'    {col_line}')
        
        # Generate relationships from foreign keys
        relationships = []
        for col_name, col_data in columns.items():
            fk = col_data.get('foreign_key')
            if fk:
                # Parse FK: "schema.table.column" or "table.column"
                parts = fk.split('.')
                if len(parts) >= 2:
                    # Get the referenced table name
                    ref_table = parts[-2]  # Second to last is table name
                    ref_class = self._to_pascal_case(ref_table)
                    
                    # Relationship name: usually the FK column without "_id" suffix
                    rel_name = col_name
                    if rel_name.endswith('_id'):
                        rel_name = rel_name[:-3]
                    
                    # Column with FK -> many_to_one (FK in current table)
                    # Type: Relation["ClassName"]
                    # Value: Relationship("ClassName")
                    relationships.append({
                        'name': rel_name,
                        'class': ref_class,
                        'type': 'many_to_one',  # FK in this table = many-to-one
                    })
        
        # Generate one-to-many relationships from reverse FKs (other tables pointing here)
        reverse_fks = table_info.get('reverse_fks', [])
        seen_reverse_tables = set()  # Deduplicate: same table may have multiple FK columns
        for rfk in reverse_fks:
            ref_table = rfk['table']
            
            # Skip if we already added a relationship from this table
            if ref_table in seen_reverse_tables:
                continue
            seen_reverse_tables.add(ref_table)
            
            ref_class = self._to_pascal_case(ref_table)
            
            # Relationship name: plural of the referenced table
            # Simple pluralization: add 's' if not already ending in 's'
            rel_name = ref_table if ref_table.endswith('s') else ref_table + 's'
            
            # one-to-many: Relation[list["ClassName"]] = Relationship("ClassName")
            relationships.append({
                'name': rel_name,
                'class': ref_class,
                'type': 'one_to_many',
            })
        
        # Add relationships section if any FKs were found
        if relationships:
            lines.append('')
            lines.append('    # Relationships (auto-generated from foreign keys)')
            for rel in relationships:
                if rel['type'] == 'one_to_many':
                    # one-to-many: Relation[list["ClassName"]] = Relationship("ClassName")
                    lines.append(f'    {rel["name"]}: Relation[list["{rel["class"]}"]] = Relationship("{rel["class"]}")')
                else:
                    # many-to-one: Relation["ClassName"] = Relationship("ClassName")
                    lines.append(f'    {rel["name"]}: Relation["{rel["class"]}"] = Relationship("{rel["class"]}")')
        
        return '\n'.join(lines)
    
    def _generate_column_line(self, col_name: str, col_data: Dict[str, Any]) -> str:
        """Generate a single column definition line."""
        # Get psqlmodel type and extract max_len if present
        db_type = col_data.get('type', 'TEXT')
        udt_name = col_data.get('udt_name')
        
        # Use udt_name if available and db_type is generic or USER-DEFINED
        if udt_name and (db_type == 'USER-DEFINED' or db_type == 'ARRAY'):
             base_type = udt_name.upper()
        else:
             base_type = db_type.split('(')[0].upper()
             
        psql_type = self.TYPE_MAP.get(base_type, 'text')
        
        # Special case for known custom types or improved mapping
        if base_type == 'BPCHAR':
            psql_type = 'char'
        elif base_type == 'TIMESTAMPTZ':
            psql_type = 'timestamptz'
        
        # Extract max_len from types like VARCHAR(100), CHAR(10), BIT(8)
        max_len = None
        if '(' in db_type and ')' in db_type:
            try:
                len_str = db_type.split('(')[1].split(')')[0]
                max_len = int(len_str)
            except (ValueError, IndexError):
                pass
        
        # Build Column arguments
        col_args = []
        is_pk = col_data.get('primary_key', False)
        
        # Primary key
        if is_pk:
            col_args.append('primary_key=True')
        
        # Nullable - skip for PKs (implicit)
        nullable = col_data.get('nullable', True)
        if not nullable and not is_pk:
            col_args.append('nullable=False')
        
        # Unique - skip for PKs (implicit)
        if col_data.get('unique') and not is_pk:
            col_args.append('unique=True')
        
        # Index - skip for PK/Unique/FK (often implicit or handled elsewhere, but explicit index=True is fine)
        if col_data.get('index') and not is_pk and not col_data.get('unique'):
            col_args.append('index=True')
        
        # max_len for VARCHAR, CHAR, BIT
        if max_len and base_type in ('VARCHAR', 'CHARACTER VARYING', 'CHAR', 'BIT', 'VARBIT'):
            col_args.append(f'max_len={max_len}')
        
        # Foreign key (check first - affects default handling)
        fk = col_data.get('foreign_key')
        is_fk = bool(fk)
        if fk:
            parts = fk.split('.')
            if len(parts) >= 2:
                ref_col = parts[-1]
                ref_table = '.'.join(parts[:-1])
                col_args.append(f'foreign_key="{ref_table}.{ref_col}"')
                on_delete = col_data.get('on_delete')
                if on_delete:
                    col_args.append(f'on_delete="{on_delete}"')
        
        # Default
        default = col_data.get('default')
        # Allow defaults for PKs (e.g. gen_random_uuid) but skip for FKs usually (unless explicit)
        if default and not is_fk:
            default_str = str(default).strip()
            
            # Remove type casts like 'value'::type
            if '::' in default_str:
                import re
                # Capture everything before the :: (keep quotes if present)
                m = re.match(r"^(.*?)::[\w\s]+", default_str)
                if m:
                    default_str = m.group(1)
            
            default_lower = default_str.lower()
            
            if 'gen_random_uuid()' in default_lower:
                col_args.append('default=gen_default_uuid')
            elif 'now()' in default_lower or 'current_timestamp' in default_lower:
                col_args.append('default=now')
            elif default_str.startswith("'") and default_str.endswith("'"):
                 # String literal - keep as is (quotes already included)
                 col_args.append(f'default={default_str}')
            elif default_str.replace('.', '', 1).isdigit():
                 # Number
                 col_args.append(f'default={default_str}')
            elif default_lower in ('true', 'false'):
                 # Boolean
                 col_args.append(f'default={default_lower.capitalize()}')
            else:
                 # Fallback: if it looks like a string but no quotes, and type is text-like, query?
                 # For now, if we stripped the cast and it's not one of above, careful.
                 # But for '2025-...' it should have quotes from DB if it's a string literal.
                 pass
        
        # Build the line - use psqlmodel type directly (no Optional wrapper)
        args_str = ', '.join(col_args) if col_args else ''
        
        if args_str:
            return f'{col_name}: {psql_type} = Column({args_str})'
        else:
            return f'{col_name}: {psql_type} = Column()'
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert table_name to PascalCase."""
        return ''.join(word.capitalize() for word in name.split('_'))
    
    def generate_models_from_orphans(self, orphan_tables: List[Dict[str, Any]], 
                                      output_dir: Path, force: bool = False) -> List[Path]:
        """Generate model files for orphan tables.
        
        Args:
            orphan_tables: List of DiffItem for removed_tables
            output_dir: Directory to write files (e.g., migrations/models/)
            
        Returns:
            List of created file paths
        """
        import psycopg
        
        output_dir.mkdir(parents=True, exist_ok=True)
        created_files = []
        
        # Get detailed table info
        dsn = self.engine._build_sync_dsn()
        conn = psycopg.connect(dsn)
        
        try:
            cur = conn.cursor()
            
            for item in orphan_tables:
                # Parse schema.table
                parts = item.object_name.split('.', 1)
                if len(parts) == 2:
                    schema, table_name = parts
                else:
                    schema, table_name = 'public', parts[0]
                
                # Check if model file already exists for this table
                if not force:
                    existing = list(output_dir.glob(f"*_{table_name}.py"))
                    if existing:
                        # Also check if it's not a migration file (starts with digit?)
                        # But models usually start with draft_ or are just names.
                        # Assuming draft_timestamp_tablename.py format.
                        model_files = [f for f in existing if "draft_" in f.name or f.name == f"{table_name}.py"]
                        if model_files:
                             print(f"   ⚠️  Skipping {table_name}: Model file exists ({model_files[0].name}). Use --force to overwrite.")
                             continue

                # Get table info
                table_info = self._introspect_table(cur, schema, table_name)
                
                # Generate code
                code = self.generate_model_for_table(schema, table_name, table_info)
                
                # Write file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"draft_{timestamp}_{table_name}.py"
                file_path = output_dir / filename
                file_path.write_text(code)
                
                created_files.append(file_path)
                created_files.append(file_path)
                print(f"   ✅ Created: {file_path.absolute()}")
            
            cur.close()
        finally:
            conn.close()
        
        return created_files
    
    def _introspect_table(self, cur, schema: str, table_name: str) -> Dict[str, Any]:
        """Get detailed table information from database."""
        table_info = {
            "schema": schema,
            "name": table_name,
            "columns": {},
        }
        
        # Get columns
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                udt_name,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, table_name))
        
        for row in cur.fetchall():
            col_name = row[0]
            data_type = row[1].upper()
            max_len = row[3]
            is_nullable = row[4] == 'YES'
            default_value = row[5]
            
            type_str = data_type
            if data_type in ('CHARACTER VARYING', 'VARCHAR') and max_len:
                type_str = f'VARCHAR({max_len})'
            
            table_info["columns"][col_name] = {
                "name": col_name,
                "type": type_str,
                "udt_name": row[2],  # udt_name
                "nullable": is_nullable,
                "default": default_value,
            }
        
        # Get primary keys
        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_schema = %s AND tc.table_name = %s
        """, (schema, table_name))
        
        for row in cur.fetchall():
            col_name = row[0]
            if col_name in table_info["columns"]:
                table_info["columns"][col_name]["primary_key"] = True
        
        # Get unique constraints
        cur.execute("""
            SELECT 
                tc.constraint_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'UNIQUE'
            AND tc.table_schema = %s AND tc.table_name = %s
            ORDER BY tc.constraint_name, kcu.ordinal_position
        """, (schema, table_name))
        
        unique_constraints = {}
        for row in cur.fetchall():
            c_name = row[0]
            col_name = row[1]
            if c_name not in unique_constraints:
                unique_constraints[c_name] = []
            unique_constraints[c_name].append(col_name)
        
        table_info["unique_together"] = []
        for c_name, cols in unique_constraints.items():
            if len(cols) == 1:
                # Single column unique -> attribute
                col = cols[0]
                if col in table_info["columns"]:
                    table_info["columns"][col]["unique"] = True
            else:
                # Multi column unique -> unique_together
                table_info["unique_together"].append(cols)
        
        # Get foreign keys
        cur.execute("""
            SELECT 
                kcu.column_name,
                ccu.table_schema,
                ccu.table_name,
                ccu.column_name,
                rc.delete_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
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
        
        # Get REVERSE foreign keys (other tables pointing TO this table) for one-to-many
        cur.execute("""
            SELECT 
                kcu.table_schema,
                kcu.table_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND ccu.table_schema = %s AND ccu.table_name = %s
        """, (schema, table_name))
        
        reverse_fks = []
        for row in cur.fetchall():
            reverse_fks.append({
                "schema": row[0],
                "table": row[1],
                "column": row[2],
            })
        
        if reverse_fks:
            table_info["reverse_fks"] = reverse_fks
        
        # Get CHECK constraints
        cur.execute("""
            SELECT 
                c.conname AS constraint_name,
                pg_get_constraintdef(c.oid) AS constraint_def
            FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            JOIN pg_class t ON t.oid = c.conrelid
            WHERE c.contype = 'c'
            AND n.nspname = %s
            AND t.relname = %s
        """, (schema, table_name))
        
        check_constraints = []
        for row in cur.fetchall():
            constraint_name = row[0]
            constraint_def = row[1]
            # Extract expression from "CHECK (expression)"
            if constraint_def.upper().startswith('CHECK'):
                expr = constraint_def[5:].strip()
                if expr.startswith('(') and expr.endswith(')'):
                    expr = expr[1:-1]
                # Clean up NOT VALID suffix (PostgreSQL adds this for unvalidated constraints)
                if expr.upper().endswith('NOT VALID'):
                    expr = expr[:-9].strip()
                    if expr.endswith(')'):
                        # Remove trailing ) that was before NOT VALID
                        pass
                check_constraints.append({
                    "name": constraint_name,
                    "expression": expr,
                })
        
        if check_constraints:
            table_info["check_constraints"] = check_constraints
            
        # Get Indexes
        cur.execute("""
            SELECT
                i.relname as index_name,
                ARRAY(
                    SELECT pg_get_indexdef(idx.indexrelid, k + 1, true)
                    FROM generate_subscripts(idx.indkey, 1) as k
                    ORDER BY k
                ) as index_keys,
                idx.indisunique as is_unique,
                idx.indisprimary as is_primary,
                c.conname IS NOT NULL as is_constraint
            FROM pg_index idx
            JOIN pg_class i ON i.oid = idx.indexrelid
            JOIN pg_class t ON t.oid = idx.indrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            LEFT JOIN pg_constraint c ON c.conindid = idx.indexrelid
            WHERE n.nspname = %s AND t.relname = %s
        """, (schema, table_name))
        
        indexes = []
        for row in cur.fetchall():
            indexes.append({
                "name": row[0],
                "columns": row[1],
                "unique": row[2],
                'primary': row[3],
                'is_constraint': row[4]
            })
        
        if indexes:
            # Filter indexes: if single column -> promote to column attribute
            table_indexes = []
            for idx in indexes:
                cols = idx.get('columns', [])
                if len(cols) == 1:
                     col_name = cols[0]
                     if col_name in table_info["columns"]:
                         # Check if it's unique
                         if idx.get('unique'):
                             table_info["columns"][col_name]["unique"] = True
                         elif not idx.get('is_primary') and not idx.get('is_constraint'):
                             # Regular index
                             table_info["columns"][col_name]["index"] = True
                     else:
                         # Column not found (maybe expression index?), keep as table index
                         table_indexes.append(idx)
                else:
                     table_indexes.append(idx)
            
            if table_indexes:
                 table_info["indexes"] = table_indexes
        
        return table_info
