"""
PSQLModel Migration System - Diff Types

DiffItem and DiffResult classes for schema comparison.
Compatible with engine.py check_schema_drift() format.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class DiffItem:
    """Represents a single change in the schema.
    
    Attributes:
        object_name: Fully qualified name (e.g., "schema.table" or "trigger_name")
        object_type: Type of object ("table", "trigger", "index", "constraint")
        details: Additional metadata about the change
        
    For modified_tables, details should contain:
        {
            "column_changes": [
                {"change": "type_changed", "column": "email", "from": "VARCHAR(100)", "to": "VARCHAR(255)"},
                {"change": "added", "column": "bio"},
                {"change": "removed", "column": "temp_field"},
                {"change": "nullable_changed", "column": "age", "from": True, "to": False},
                {"change": "default_changed", "column": "role", "from": None, "to": "'user'"},
                {"change": "pk_changed", "column": "id", "from": False, "to": True},
                {"change": "fk_changed", "column": "user_id", "from": None, "to": "users.id"},
                {"change": "unique_changed", "column": "email", "from": False, "to": True},
                {"change": "index_changed", "column": "name", "from": None, "to": "btree"},
            ]
        }
    """
    
    object_name: str
    object_type: str = "table"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiffResult:
    """Complete result of a schema comparison.
    
    This class format is compatible with engine.py check_schema_drift().
    
    Attributes:
        new_tables: Tables present in models but not in database
        removed_tables: Tables present in database but not in models
        modified_tables: Tables with changed columns/constraints
        renamed_tables: Tables detected as renames (old_name -> new_name)
        new_triggers: New triggers to be created
        removed_triggers: Triggers to be removed
        modified_triggers: Triggers with changed definitions
        new_indexes: New indexes to be created
        removed_indexes: Indexes to be removed
        modified_indexes: Indexes with changed definitions
    """
    
    new_tables: List[DiffItem] = field(default_factory=list)
    removed_tables: List[DiffItem] = field(default_factory=list)
    modified_tables: List[DiffItem] = field(default_factory=list)
    renamed_tables: List[DiffItem] = field(default_factory=list)  # {old_name, new_name}
    new_triggers: List[DiffItem] = field(default_factory=list)
    removed_triggers: List[DiffItem] = field(default_factory=list)
    modified_triggers: List[DiffItem] = field(default_factory=list)
    new_indexes: List[DiffItem] = field(default_factory=list)
    removed_indexes: List[DiffItem] = field(default_factory=list)
    modified_indexes: List[DiffItem] = field(default_factory=list)
    
    @property
    def has_changes(self) -> bool:
        """Check if any changes were detected."""
        return bool(
            self.new_tables or self.removed_tables or self.modified_tables or
            self.new_triggers or self.removed_triggers or self.modified_triggers or
            self.new_indexes or self.removed_indexes or self.modified_indexes
        )
    
    @property
    def has_actionable_changes(self) -> bool:
        """Check if there are changes that generate real DDL (not just comments).
        
        Excludes removed_tables because they only generate warning comments
        unless --drop-orphans is used.
        """
        return bool(
            self.new_tables or self.modified_tables or
            self.new_triggers or self.removed_triggers or self.modified_triggers or
            self.new_indexes or self.removed_indexes or self.modified_indexes
        )
    
    @property
    def total_changes(self) -> int:
        """Count total number of changes."""
        return (
            len(self.new_tables) + len(self.removed_tables) + len(self.modified_tables) +
            len(self.new_triggers) + len(self.removed_triggers) + len(self.modified_triggers) +
            len(self.new_indexes) + len(self.removed_indexes) + len(self.modified_indexes)
        )
    
    def format_summary(self) -> str:
        """Generate a brief summary of changes."""
        parts = []
        if self.new_tables:
            parts.append(f"+{len(self.new_tables)} tables")
        if self.removed_tables:
            parts.append(f"-{len(self.removed_tables)} tables")
        if self.modified_tables:
            parts.append(f"~{len(self.modified_tables)} tables")
        if self.new_triggers:
            parts.append(f"+{len(self.new_triggers)} triggers")
        if self.new_indexes:
            parts.append(f"+{len(self.new_indexes)} indexes")
        return ", ".join(parts) if parts else "No changes"
