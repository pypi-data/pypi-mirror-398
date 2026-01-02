"""
PSQLModel Migration System - Configuration

MigrationConfig dataclass for configuring the migration system.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


@dataclass
class MigrationConfig:
    """Configuration for the migration system.
    
    Attributes:
        migrations_path: Directory for migration files
        state_table_name: Database table for current schema hashes
        history_table_name: Database table for migration history
        state_file_name: Local file for schema state cache
        auto_detect_changes: Check for drift on initialization
        fail_on_drift: Raise error instead of warning on drift
        debug: Enable verbose output
        logger: External logger function
        version_format: Timestamp format for migration versions
    """
    
    migrations_path: str = "./migrations/"
    migrations_schema: str = "migrations"
    state_table_name: str = "migrations._psqlmodel_schema_state"
    history_table_name: str = "migrations._psqlmodel_migrations"
    state_file_name: str = ".schema_state.json"
    head_lock_file: str = "head.lock"
    auto_detect_changes: bool = True
    fail_on_drift: bool = False
    debug: bool = False
    logger: Optional[Callable[[str], None]] = None
    version_format: str = "%Y%m%d_%H%M%S"
    
    def get_migrations_path(self) -> Path:
        """Get the migrations path as a Path object."""
        return Path(self.migrations_path).resolve()
    
    def _log(self, message: str) -> None:
        """Internal logging helper."""
        if not self.debug:
            return
        if self.logger:
            try:
                self.logger(message)
            except Exception:
                print(message)
        else:
            print(message)
