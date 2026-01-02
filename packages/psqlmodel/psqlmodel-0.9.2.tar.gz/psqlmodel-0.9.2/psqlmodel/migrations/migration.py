"""
PSQLModel Migration System - Migration Classes

Migration base class, generator, and loader.
"""

import hashlib
import importlib.util
import re
import textwrap
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Type, TYPE_CHECKING, Union, Any
import uuid

from .config import MigrationConfig
from .diff import DiffResult
from .ddl_generator import DDLGenerator

if TYPE_CHECKING:
    from ..core.engine import Engine


class Migration(ABC):
    """Abstract base class for migration files.
    
    Subclasses must implement up() and down() methods.
    
    Attributes:
        version: Unique version identifier (timestamp-based)
        message: Human-readable description
        depends_on: Optional dependency on another migration
    """
    
    version: str = ""
    message: str = ""
    depends_on: Union[Optional[str], List[str]] = None
    head_id: str = ""
    is_data_migration: bool = False
    _file_path: Optional[str] = None  # Set by loader
    _checksum_cache: Optional[str] = None  # Cached checksum
    
    @abstractmethod
    def up(self, engine: "Engine") -> None:
        """Apply the migration."""
        pass
    
    @abstractmethod
    def down(self, engine: "Engine") -> None:
        """Revert the migration."""
        pass

    async def up_async(self, engine: "Engine") -> None:
        """Apply the migration asynchronously (optional)."""
        pass
        
    async def down_async(self, engine: "Engine") -> None:
        """Revert the migration asynchronously (optional)."""
        pass
    
    @property
    def checksum(self) -> str:
        """Compute normalized SHA256 checksum of migration logic (cached, short format).
        
        Features:
        - Cached: avoids recomputation on repeated access
        - Semantic: hashes only up/down method bodies, not imports/comments
        - Normalized: collapses whitespace to prevent false-positive changes
        - Short: returns first 16 chars (64 bits, sufficient uniqueness)
        """
        if self._checksum_cache:
            return self._checksum_cache
        
        try:
            import inspect
            import re
            
            # Semantic: hash only up/down methods
            up_source = inspect.getsource(self.up)
            down_source = inspect.getsource(self.down)
            content = up_source + down_source
            
            # Normalize: collapse whitespace
            content = re.sub(r'\s+', ' ', content.strip())
            
            # Short hash: first 16 chars
            self._checksum_cache = hashlib.sha256(content.encode()).hexdigest()[:16]
            return self._checksum_cache
            
        except Exception:
            pass
        
        # Fallback: hash version + message
        fallback = f"{self.version}:{self.message}"
        self._checksum_cache = hashlib.sha256(fallback.encode()).hexdigest()[:16]
        return self._checksum_cache


class DataMigration(Migration):
    """Base class for data migrations.
    
    Data migrations involve moving or transforming data, not just schema changes.
    They may require longer timeouts or batching.
    """
    
    is_data_migration: bool = True
    timeout_seconds: Optional[int] = None  # None uses default timeout
    batch_size: int = 1000  # Default batch size for iterative operations

    async def up_async(self, engine: "Engine") -> None:
        """Apply the migration asynchronously (optional)."""
        pass
        
    async def iter_batches(self, context: Any, table: str, order_by: str = "id", batch_size: int = None):
        """Async generator to iterate over table rows in batches.
        
        Args:
            context: The execution context (provides fetch_all)
            table: Table name to read from
            order_by: Column to sort by (pagination stability)
            batch_size: Override default batch size
            
        Yields:
            List of row dictionaries
        """
        limit = batch_size or self.batch_size
        offset = 0
        while True:
            # Note: This is a basic offset pagination. For huge datasets, cursor-based (keyset) might be better
            # but requires knowing last seen ID.
            sql = f"SELECT * FROM {table} ORDER BY {order_by} LIMIT {limit} OFFSET {offset}"
            rows = await context.fetch_all(sql)
            
            if not rows:
                break
                
            yield rows
            
            if len(rows) < limit:
                break
                
            offset += limit

    async def down_async(self, engine: "Engine") -> None:
        """Revert the migration asynchronously (optional)."""
        pass


class MigrationGenerator:
    """Generates migration files from diffs."""
    
    TEMPLATE = textwrap.dedent('''
        """
        Migration: {message}
        
        Generated: {timestamp}
        """
        
        from psqlmodel.migrations import Migration
        
        
        class {class_name}(Migration):
            """
            {message}
            """
            
            version = "{version}"
            message = "{message}"
            depends_on = {depends_on}
            head_id = "{head_id}"
            
            def up(self, engine):
                """Apply migration (sync)."""
        {up_statements}
            
            def down(self, engine):
                """Revert migration (sync)."""
        {down_statements}
    ''').strip()
    
    @staticmethod
    def generate_version(config: MigrationConfig = None) -> str:
        """Generate a version string based on current timestamp."""
        format_str = config.version_format if config else "%Y%m%d_%H%M%S"
        return datetime.utcnow().strftime(format_str)
    
    @staticmethod
    def sanitize_message(message: str) -> str:
        """Convert message to valid Python identifier parts."""
        # Replace non-alphanumeric with underscore
        clean = re.sub(r'[^a-zA-Z0-9]', '_', message.lower())
        # Remove consecutive underscores
        clean = re.sub(r'_+', '_', clean)
        # Limit length and remove trailing underscore
        return clean[:50].strip('_')
    
    @classmethod
    def generate(cls, message: str, diff: DiffResult,
                 config: MigrationConfig = None,
                 depends_on: Union[Optional[str], List[str]] = None,
                 drop_orphans: bool = False,
                 head_id: Optional[str] = None) -> Tuple[str, str, str]:
        """Generate a migration from a diff.
        
        Args:
            message: Migration description
            diff: The schema diff result
            config: Migration configuration
            depends_on: Optional dependency on previous migration
            drop_orphans: If True, generate DROP TABLE for orphan tables
        
        Returns:
            Tuple of (version, filename, file_content)
        """
        version = cls.generate_version(config)
        clean_msg = cls.sanitize_message(message)
        filename = f"{version}_{clean_msg}.py"
        class_name = f"Migration_{version}"
        
        # Generate DDL statements
        ddl_gen = DDLGenerator()
        up_stmts, down_stmts = ddl_gen.generate_from_diff(diff, drop_orphans=drop_orphans)
        
        # Format statements for template
        up_code = cls._format_statements(up_stmts)
        down_code = cls._format_statements(down_stmts)
        
        if isinstance(depends_on, list):
            depends_str = "[" + ", ".join(f'"{d}"' for d in depends_on) + "]"
        else:
            depends_str = f'"{depends_on}"' if depends_on else "None"
        
        # Generate head_id if not provided
        if not head_id:
            head_id = str(uuid.uuid4())
        
        content = cls.TEMPLATE.format(
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            class_name=class_name,
            version=version,
            depends_on=depends_str,
            head_id=head_id,
            up_statements=up_code,
            down_statements=down_code,
        )
        
        return version, filename, content
    
    @staticmethod
    def _format_statements(statements: List[str]) -> str:
        """Format SQL statements as Python code."""
        if not statements:
            return "        pass"
        
        lines = []
        for stmt in statements:
            # Handle comments
            if stmt.strip().startswith("--"):
                lines.append(f"        # {stmt.strip()[2:].strip()}")
            else:
                # Use triple quotes for multiline SQL
                if "\n" in stmt:
                    # Escape triple quotes if present (rare)
                    cleaned = stmt.replace('"""', '\\"\\"\\"')
                    lines.append(f'        engine.execute_sql("""{cleaned}""")')
                else:
                    # Escape quotes in SQL
                    escaped = stmt.replace('"', '\\"').replace("'", "\\'")
                    lines.append(f'        engine.execute_sql("{escaped}")')
        
        return "\n".join(lines)
    
    @classmethod
    def generate_empty(cls, message: str, 
                       config: MigrationConfig = None,
                       depends_on: Union[Optional[str], List[str]] = None,
                       head_id: Optional[str] = None) -> Tuple[str, str, str]:
        """Generate an empty migration for manual editing."""
        version = cls.generate_version(config)
        clean_msg = cls.sanitize_message(message)
        filename = f"{version}_{clean_msg}.py"
        class_name = f"Migration_{version}"
        
        if isinstance(depends_on, list):
            depends_str = "[" + ", ".join(f'"{d}"' for d in depends_on) + "]"
        else:
            depends_str = f'"{depends_on}"' if depends_on else "None"
        
        if not head_id:
            head_id = str(uuid.uuid4())
        
        content = cls.TEMPLATE.format(
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            class_name=class_name,
            version=version,
            depends_on=depends_str,
            head_id=head_id,
            up_statements="        # TODO: Add migration SQL\n        pass",
            down_statements="        # TODO: Add rollback SQL\n        pass",
        )
        
        return version, filename, content


class MigrationLoader:
    """Loads migration files from disk."""
    
    @staticmethod
    def load_from_file(path: Path) -> Optional[Migration]:
        """Load a Migration class from a Python file."""
        if not path.exists() or not path.suffix == '.py':
            return None
        
        try:
            spec = importlib.util.spec_from_file_location(
                f"migration_{path.stem}", path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find the Migration subclass
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, Migration) and 
                        attr is not Migration and
                        attr is not DataMigration):
                        instance = attr()
                        instance._file_path = str(path)  # Store path for checksum
                        return instance
        except Exception:
            pass
        
        return None
    
    @classmethod
    def load_all_from_directory(cls, path: Path) -> List[Migration]:
        """Load all migrations from a directory, sorted by version."""
        migrations = []
        
        if not path.exists() or not path.is_dir():
            return migrations
        
        for file_path in sorted(path.glob("*.py")):
            # Skip __init__.py and similar
            if file_path.name.startswith("_"):
                continue
            
            migration = cls.load_from_file(file_path)
            if migration:
                migrations.append(migration)
        
        # Sort by version
        migrations.sort(key=lambda m: m.version)
        
        return migrations
