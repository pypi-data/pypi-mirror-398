"""
PSQLModel Migration System - Schema Hasher

Generates deterministic SHA256 hashes for schema objects.
"""

import hashlib
import json
from typing import Type, Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..orm.model import PSQLModel
    from ..orm.column import Column


class SchemaHasher:
    """Generates deterministic SHA256 hashes for schema comparison.
    
    Hashes include all relevant attributes of tables, columns,
    constraints, indexes, and triggers.
    """
    
    def _compute_hash(self, data: Any) -> str:
        """Compute SHA256 hash of data structure."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _serialize_column(self, col: "Column") -> Dict[str, Any]:
        """Extract all hashable attributes from a Column."""
        # Handle foreign_key serialization
        fk_value = None
        if col.foreign_key:
            if hasattr(col.foreign_key, 'model'):
                # It's a Column reference
                fk_model = col.foreign_key.model
                fk_schema = getattr(fk_model, '__schema__', 'public') or 'public'
                fk_table = getattr(fk_model, '__tablename__', '')
                fk_col = col.foreign_key.name
                fk_value = f"{fk_schema}.{fk_table}.{fk_col}"
            else:
                # It's a string like "locations.id" or "public.locations.id"
                fk_str = str(col.foreign_key)
                parts = fk_str.split('.')
                if len(parts) == 2:
                    # Missing schema, add 'public.' prefix
                    fk_value = f"public.{fk_str}"
                else:
                    fk_value = fk_str
        
        # Handle type hint serialization
        type_str = None
        if col.type_hint:
            if hasattr(col.type_hint, 'ddl'):
                try:
                    type_str = col.type_hint.ddl()
                except Exception:
                    type_str = str(col.type_hint)
            else:
                type_str = str(col.type_hint)
        
        # Add length to VARCHAR/CHAR types
        if type_str in ('VARCHAR', 'CHAR') and col.max_len:
            type_str = f"{type_str}({col.max_len})"
        
        return {
            "name": col.name,
            "type": type_str,
            "primary_key": getattr(col, 'primary_key', False),
            "nullable": getattr(col, 'nullable', True),
            "unique": getattr(col, 'unique', False),
            "default": col.default if isinstance(col.default, (bool, int, float, str, type(None))) else str(col.default),
            "foreign_key": fk_value,
            "on_delete": getattr(col, 'on_delete', None),
            "index": getattr(col, 'index', False),
            "index_method": getattr(col, 'index_method', None),
            "max_len": getattr(col, 'max_len', None),
            "timez": getattr(col, 'timez', False),
        }
    
    def hash_column(self, col: "Column") -> str:
        """Hash a single column definition."""
        data = self._serialize_column(col)
        return self._compute_hash(data)
    
    def _serialize_constraint(self, constraint, table_name: str, schema: str) -> str:
        """Serialize a constraint to its DDL string."""
        try:
            return constraint.ddl(table_name, schema)
        except Exception:
            return str(constraint)
    
    def _serialize_index(self, index, table_name: str, schema: str) -> str:
        """Serialize an index to its DDL string."""
        try:
            return index.ddl(table_name, schema)
        except Exception:
            return str(index)
    
    def hash_table(self, model: Type["PSQLModel"]) -> str:
        """Hash an entire table including columns, constraints, and indexes."""
        schema = getattr(model, '__schema__', 'public') or 'public'
        table_name = getattr(model, '__tablename__', model.__name__.lower())
        columns = getattr(model, '__columns__', {})
        constraints = getattr(model, '__constraints__', [])
        indexes = getattr(model, '__indexes__', [])
        
        data = {
            "name": table_name,
            "schema": schema,
            "columns": {
                name: self._serialize_column(col) 
                for name, col in columns.items()
            },
            "constraints": [
                self._serialize_constraint(c, table_name, schema) 
                for c in constraints
            ],
            "indexes": [
                self._serialize_index(i, table_name, schema) 
                for i in indexes
            ],
        }
        
        return self._compute_hash(data)
    
    def hash_trigger(self, trigger) -> str:
        """Hash a trigger definition."""
        data = {
            "name": getattr(trigger, 'trigger_name', None),
            "timing": getattr(trigger, 'timing', None),
            "events": getattr(trigger, 'events', []),
            "for_each": getattr(trigger, 'for_each', None),
            "when": trigger.when_condition.to_sql() if getattr(trigger, 'when_condition', None) else None,
            "function": trigger.function.__name__ if getattr(trigger, 'function', None) else None,
        }
        return self._compute_hash(data)
    
    def hash_models(self, models: List[Type["PSQLModel"]]) -> Dict[str, str]:
        """Hash all models and return a dict of {schema.table: hash}."""
        result = {}
        for model in models:
            schema = getattr(model, '__schema__', 'public') or 'public'
            table_name = getattr(model, '__tablename__', model.__name__.lower())
            key = f"{schema}.{table_name}"
            result[key] = self.hash_table(model)
        return result
    
    def get_column_details(self, col: "Column") -> Dict[str, Any]:
        """Get detailed column attributes for comparison."""
        return self._serialize_column(col)
