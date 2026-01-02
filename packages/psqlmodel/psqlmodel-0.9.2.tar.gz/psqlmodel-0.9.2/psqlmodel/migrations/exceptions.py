"""
PSQLModel Migration System - Exceptions

Custom exception hierarchy for migration errors.
"""

from typing import Dict, Any, Optional


class MigrationError(Exception):
    """Base exception for all migration-related errors."""
    pass


class SchemaDriftError(MigrationError):
    """Raised when schema mismatch is detected between models and database.
    
    Attributes:
        drift_details: Dictionary containing detailed diff information
    """
    
    def __init__(self, message: str, drift_details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.drift_details = drift_details or {}


class MigrationNotFoundError(MigrationError):
    """Raised when a migration file cannot be found.
    
    Attributes:
        version: The migration version that was not found
        file_path: Expected path to the migration file
    """
    
    def __init__(self, version: str, file_path: Optional[str] = None):
        self.version = version
        self.file_path = file_path
        message = f"Migration '{version}' not found"
        if file_path:
            message += f" at {file_path}"
        super().__init__(message)


class MigrationAlreadyAppliedError(MigrationError):
    """Raised when attempting to apply a migration that has already been applied.
    
    Attributes:
        version: The migration version that was already applied
    """
    
    def __init__(self, version: str):
        self.version = version
        super().__init__(f"Migration '{version}' has already been applied")


class MigrationDependencyError(MigrationError):
    """Raised when a migration's dependency has not been applied.
    
    Attributes:
        version: The migration that has unmet dependencies
        depends_on: The required dependency version
    """
    
    def __init__(self, version: str, depends_on: str):
        self.version = version
        self.depends_on = depends_on
        super().__init__(
            f"Migration '{version}' depends on '{depends_on}' which has not been applied"
        )


class RollbackError(MigrationError):
    """Raised when a migration rollback fails.
    
    Attributes:
        version: The migration version that failed to rollback
        original_error: The underlying exception
    """
    
    def __init__(self, version: str, original_error: Optional[Exception] = None):
        self.version = version
        self.original_error = original_error
        message = f"Failed to rollback migration '{version}'"
        if original_error:
            message += f": {original_error}"
        super().__init__(message)


class StateCorruptionError(MigrationError):
    """Raised when local and database state are inconsistent.
    
    Attributes:
        details: Description of the inconsistency
    """
    
    def __init__(self, details: str):
        self.details = details
        super().__init__(f"State corruption detected: {details}")
