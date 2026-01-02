"""
PSQLModel Migration System

Intelligent schema migration system for PSQLModel ORM.

Usage:
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    config = MigrationConfig(migrations_path="./migrations/")
    manager = MigrationManager(engine, config)
    
    # Check status
    status = manager.status()
    
    # Auto-generate migration
    migration = manager.autogenerate("Add user profile")
    
    # Apply pending migrations
    count = manager.upgrade()
"""

from .exceptions import (
    MigrationError,
    SchemaDriftError,
    MigrationNotFoundError,
    MigrationAlreadyAppliedError,
    MigrationDependencyError,
    RollbackError,
    StateCorruptionError,
)

from .config import MigrationConfig
from .status import MigrationStatus
from .diff import DiffItem, DiffResult
from .hasher import SchemaHasher
from .differ import SchemaDiffer
from .state import StateManager
from .ddl_generator import DDLGenerator
from .migration import Migration, MigrationGenerator, MigrationLoader
from .manager import MigrationManager


__all__ = [
    # Core classes
    "MigrationManager",
    "MigrationConfig",
    "MigrationStatus",
    "Migration",
    
    # Diff types
    "DiffItem",
    "DiffResult",
    
    # Components
    "SchemaHasher",
    "SchemaDiffer",
    "StateManager",
    "DDLGenerator",
    "MigrationGenerator",
    "MigrationLoader",
    
    # Exceptions
    "MigrationError",
    "SchemaDriftError",
    "MigrationNotFoundError",
    "MigrationAlreadyAppliedError",
    "MigrationDependencyError",
    "RollbackError",
    "StateCorruptionError",
]
