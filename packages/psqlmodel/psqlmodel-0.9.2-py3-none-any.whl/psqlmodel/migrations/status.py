"""
PSQLModel Migration System - Status

MigrationStatus dataclass for reporting migration state.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MigrationStatus:
    """Status report for the migration system.
    
    Attributes:
        initialized: Whether migrations have been initialized
        migrations_path: Path to migration files
        current_version: The latest applied migration version
        applied_count: Number of applied migrations
        pending_count: Number of pending migrations
        has_drift: Whether schema drift was detected
        drift_summary: Brief description of detected drift
    """
    
    initialized: bool
    migrations_path: str
    current_version: Optional[str]
    applied_count: int
    pending_count: int
    has_drift: bool
    drift_summary: Optional[str] = None
