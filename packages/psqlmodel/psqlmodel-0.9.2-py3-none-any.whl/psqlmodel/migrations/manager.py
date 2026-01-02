"""
PSQLModel Migration System - Migration Manager

Main orchestrator for the migration system.
Compatible with engine.py ensure_migrations() and check_schema_drift() methods.
"""

import os
import re
import uuid
import json
import time
import sys
import importlib.util
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Type, Dict, Any, Set, TYPE_CHECKING, Union, Tuple
import graphlib

import psycopg

from .config import MigrationConfig
from .status import MigrationStatus
from .diff import DiffResult, DiffItem
from .hasher import SchemaHasher
from .differ import SchemaDiffer
from .state import StateManager
from .ddl_generator import DDLGenerator
from .migration import Migration, MigrationGenerator, MigrationLoader
from .exceptions import (
    MigrationError, MigrationNotFoundError, MigrationAlreadyAppliedError,
    MigrationDependencyError, RollbackError
)

if TYPE_CHECKING:
    from ..core.engine import Engine
    from ..orm.model import PSQLModel


class MigrationManager:
    """Main orchestrator for the migration system.
    
    This class provides all methods used by engine.py and CLI.
    
    Engine.py integration:
        - __init__(engine, config) - constructor
        - status() → MigrationStatus - get current state
        - init() → Path - initialize migrations
        - _compute_diff() → DiffResult - compare models vs DB (internal)
        - autogenerate(message) → Migration - create migration from diff
        - upgrade(target) → int - apply pending migrations
        
    CLI integration:
        - downgrade(target) - rollback migrations
        - history(limit) - show migration history
        - check() - verify no pending migrations
        - current() - get current version
        - stamp(version) - mark version without running
        - generate_sql(direction, target) - preview SQL
        - verify() - validate checksums
    """
    
    def __init__(self, engine: "Engine", config: Optional[MigrationConfig] = None):
        """Initialize the migration manager.
        
        Args:
            engine: PSQLModel engine instance
            config: Migration configuration (uses defaults if None)
        """
        self.engine = engine
        self.config = config or MigrationConfig()
        self.state = StateManager(engine, self.config)
        self.hasher = SchemaHasher()
        self.differ = SchemaDiffer(engine)
        self.ddl_gen = DDLGenerator()
        self.generator = MigrationGenerator()
        self.loader = MigrationLoader()
    
    def _log(self, message: str) -> None:
        """Internal logging helper."""
        self.config._log(message)
    
    def _get_models(self, context: str = None) -> List[Type["PSQLModel"]]:
        """Get models from engine or by scanning loaded modules.
        
        First tries engine._discovered_models (populated during startup).
        If empty, scans sys.modules for PSQLModel subclasses.
        """
        from ..orm.model import PSQLModel
        import sys
        
        # First try engine's discovered models
        discovered = getattr(self.engine, '_discovered_models', [])
        if discovered:
            return [model for model, _ in discovered]
            
        # If no models found and models_path is set in engine config, try to load them
        models_path = getattr(self.engine.config, 'models_path', None)
        if models_path:
            from pathlib import Path
            import importlib.util
            import os
            
            # Normalize to list
            paths = models_path if isinstance(models_path, list) else [models_path]
            loaded_files = []
            
            # Helper to import file
            def import_file(fpath: Path):
                try:
                    module_name = fpath.stem
                    spec = importlib.util.spec_from_file_location(module_name, fpath)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        loaded_files.append(fpath.name)
                except Exception:
                    pass

            for path in paths:
                path_obj = Path(path)
                if path_obj.is_file():
                    import_file(path_obj)
                elif path_obj.is_dir():
                    for f in path_obj.glob("*.py"):
                        if not f.name.startswith("_"):
                            import_file(f)
                elif not path_obj.exists() and (Path.cwd() / path).exists():
                    # Try current directory if path is relative
                    import_file(Path.cwd() / path)
            
            if loaded_files:
                prefix = f"[{context}] " if context else ""
                print(f"📦 {prefix}Loaded {len(loaded_files)} model file(s) from: {', '.join(loaded_files)}")
        
        # Fallback: scan loaded modules for PSQLModel subclasses
        
        # Fallback: scan loaded modules for PSQLModel subclasses
        models = []
        seen = set()
        
        for module_name, module in list(sys.modules.items()):
            # Skip internal modules
            if module_name.startswith('_') or module is None:
                continue
            if module_name.startswith(('psqlmodel.', 'psycopg', 'typing')):
                continue
                
            try:
                for attr_name in dir(module):
                    if attr_name.startswith('_'):
                        continue
                    try:
                        obj = getattr(module, attr_name)
                        if (isinstance(obj, type) and 
                            issubclass(obj, PSQLModel) and 
                            obj is not PSQLModel and
                            hasattr(obj, '__tablename__') and
                            id(obj) not in seen):
                            models.append(obj)
                            seen.add(id(obj))
                    except (TypeError, AttributeError):
                        pass
            except Exception:
                pass
        
        return models
    
    # =========================================================================
    # Engine.py compatible methods
    # =========================================================================
    
    async def _ensure_async_setup(self):
        """Ensure setup for async commands."""
        await self.state.ensure_tables_async()

    async def _compute_diff_async(self, context: str = "") -> DiffResult:
        """Compute diff asynchronously."""
        models = self._get_models(context)
        return await self.differ.compare_async(models)

    def status(self) -> MigrationStatus:
        """Get current migration status.
        
        Returns:
            MigrationStatus with current state information
        """
        migrations_path = self.config.get_migrations_path()
        initialized = migrations_path.exists() and (migrations_path / "__init__.py").exists()
        
        if not initialized:
            return MigrationStatus(
                initialized=False,
                migrations_path=str(migrations_path),
                current_version=None,
                applied_count=0,
                pending_count=0,
                has_drift=False,
            )
        
        # Get applied migrations
        applied = self.state.get_applied_migrations()
        current_version = self.state.get_current_version()
        
        # Get pending migrations
        all_migrations = self.loader.load_all_from_directory(migrations_path)
        applied_versions = {m["version"] for m in applied}
        pending = [m for m in all_migrations if m.version not in applied_versions]
        
        # Check for drift
        has_drift = False
        drift_summary = None
        try:
            diff = self._compute_diff(context="Status")
            if diff.has_changes:
                has_drift = True
                drift_summary = diff.format_summary()
        except Exception:
            pass
        
        return MigrationStatus(
            initialized=True,
            migrations_path=str(migrations_path),
            current_version=current_version,
            applied_count=len(applied),
            pending_count=len(pending),
            has_drift=has_drift,
            drift_summary=drift_summary,
        )
    
    async def status_async(self) -> MigrationStatus:
        """Get current migration status (Async)."""
        migrations_path = self.config.get_migrations_path()
        initialized = migrations_path.exists() and (migrations_path / "__init__.py").exists()

        if not initialized:
            return MigrationStatus(
                initialized=False,
                migrations_path=str(migrations_path),
                current_version=None,
                applied_count=0,
                pending_count=0,
                has_drift=False,
            )

        await self._ensure_async_setup()
        
        applied = await self.state.get_applied_migrations_async()
        available = self.loader.load_all_from_directory(migrations_path)
        
        applied_versions = {m["version"] for m in applied}
        pending_count = sum(1 for m in available if m.version not in applied_versions)
        
        # Drift check
        drift = False
        if self.config.auto_detect_changes:
             diff = await self._compute_diff_async(context="Status")
             drift = diff.has_changes
             
        return MigrationStatus(
            initialized=True,
            migrations_path=str(migrations_path),
            current_version=applied[-1]["version"] if applied else None,
            applied_count=len(applied),
            pending_count=pending_count,
            has_drift=drift,
        )

    def init(self) -> Path:
        """Initialize migrations directory and database tables.
        
        Returns:
            Path to the migrations directory
        """
        migrations_path = self.config.get_migrations_path()
        
        # Create directory
        migrations_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py
        init_file = migrations_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""PSQLModel migrations directory."""\n')
        
        # Create database tables
        try:
            self.state.ensure_tables()
        except Exception as e:
            self._log(f"Warning: Could not create state tables: {e}")
        
        self._log(f"Initialized migrations at {migrations_path}")
        
        return migrations_path

    async def init_async(self) -> Path:
        """Initialize migrations directory and database tables (Async).
        
        Returns:
            Path to the migrations directory
        """
        migrations_path = self.config.get_migrations_path()
        
        # Create directory
        migrations_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py
        init_file = migrations_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""PSQLModel migrations directory."""\n')
        
        # Create database tables (async)
        try:
            await self.state.ensure_tables_async()
        except Exception as e:
            self._log(f"Warning: Could not create state tables: {e}")
        
        self._log(f"Initialized migrations at {migrations_path}")
        
        return migrations_path
    
    def _compute_diff(self, context: str = None) -> "DiffResult":
        """Compare models against database state.
        
        This is the internal method used by both ensure_migrations() and 
        check_schema_drift() in engine.py.
        
        Returns:
            DiffResult with changes in engine-compatible format
        """
        models = self._get_models(context=context)
        # Note: If no models are found, _compute_diff returns empty, 
        # but what if there are tables in DB? They appear as orphans (removed_tables).
        # DiffResult handles this logic in differ.compare().
        if not models:
            # We still need to check for removed_tables if DB has tables but we have no models.
            # But normally _get_models loads models. If 0 models, comparing 0 models vs DB.
            pass
        
        return self.differ.compare(models)

    def check_stale_migrations(self) -> List[Migration]:
        """Check for pending migrations that cover changes already present in the DB.
        
        Useful when the DB schema matches the models (no drift), but there are still 
        migrations marked as pending. This suggests the migrations are 'stale' or 
        created redundantly.
        """
        # 1. Check if there is actual schema drift
        diff = self._compute_diff(context="Stale Check")
        if diff.has_actionable_changes:
            return []
            
        # 2. If no drift, any pending migration is potentially stale
        all_migrations = self.loader.load_all_from_directory(self.config.get_migrations_path())
        applied = self.state.get_applied_migrations()
        applied_versions = {m["version"] for m in applied}
        pending = [m for m in all_migrations if m.version not in applied_versions]
        
        return pending

    def get_orphan_tables(self) -> List["DiffItem"]:
        """Get list of tables present in DB but missing from models."""
        diff = self._compute_diff(context="Orphan Check")
        return diff.removed_tables

    async def check_stale_migrations_async(self) -> List[Migration]:
        """Check for pending migrations that cover changes already present in the DB (Async)."""
        await self._ensure_async_setup()
        
        diff = await self._compute_diff_async(context="Stale Check")
        if diff.has_actionable_changes:
            return []
            
        all_migrations = self.loader.load_all_from_directory(self.config.get_migrations_path())
        applied = await self.state.get_applied_migrations_async()
        applied_versions = {m["version"] for m in applied}
        pending = [m for m in all_migrations if m.version not in applied_versions]
        
        return pending

    async def get_orphan_tables_async(self) -> List["DiffItem"]:
        """Get list of tables present in DB but missing from models (Async)."""
        await self._ensure_async_setup()
        diff = await self._compute_diff_async(context="Orphan Check")
        return diff.removed_tables
    
    async def autogenerate_async(self, message: str) -> Optional[Migration]:
        """Auto-generate a migration based on model changes (Async)."""
        await self._ensure_async_setup()
        
        diff = await self._compute_diff_async(context="Autogenerate")
        
        if not diff.has_changes:
            self._log("No changes detected.")
            return None
            
        current_version = await self.state.get_current_version_async()
        
        if not current_version:
             # Check if we have manually created migrations that are applied?
             # For simplicty, just pass None if no version found in DB.
             # But if there are files but DB is empty, it means we are behind.
             # autogenerate typically assumes we are generating ON TOP of current DB state.
             pass
        
        migration = self.generator.generate(
            message=message,
            diff=diff,
            depends_on=current_version
        )
        
        self.generator.save_to_file(migration, self.config.get_migrations_path())
        
        self._log(f"Generated migration: {migration.version}")
             
        return migration

    def autogenerate(self, message: str) -> Optional[Migration]:
        """Auto-generate a migration from detected changes.
        
        Args:
            message: Description for the migration
            
        Returns:
            Generated Migration object, or None if no changes detected
        """
        # Generate head_id first
        head_id = str(uuid.uuid4())
        
        diff = self._compute_diff(context="Autogenerate")
        
        if not diff.has_changes:
            self._log("No changes detected")
            return None
            
        # Get latest migration for dependency
        migrations = self.loader.load_all_from_directory(
            self.config.get_migrations_path()
        )
        depends_on = migrations[-1].version if migrations else None
        
        # Check if we should drop orphans
        _drop_orphans = getattr(self, '_drop_orphans', False)
        
        version, filename, content = self.generator.generate(
            message=message,
            diff=diff,
            config=self.config,
            depends_on=depends_on,
            drop_orphans=_drop_orphans,
            head_id=head_id
        )
        
        path = self.config.get_migrations_path() / filename
        # Ensure migrations directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
            
        self._log(f"Generated migration: {filename}")
        
        # Update Head Lock
        self._write_head_lock(version, head_id)
        
        # Return incomplete migration object (just for info)
        m = self.loader.load_from_file(path)
        return m

    async def check_async(self) -> bool:
        """Check for schema drift (Async) - returns True if changes detected."""
        await self._ensure_async_setup()
        diff = await self._compute_diff_async(context="Check")
        return diff.has_changes

    async def current_async(self) -> Optional[str]:
        """Get current version (Async)."""
        await self._ensure_async_setup()
        return await self.state.get_current_version_async()

    async def stamp_async(self, version: str) -> None:
        """Stamp database with version without executing (Async)."""
        await self._ensure_async_setup()
        # Mock checksum/message since we skip execution
        await self.state.mark_applied_async(
            version=version,
            message=f"Stamped via CLI",
            checksum="stamped",
            execution_time_ms=0
        )
    
    def upgrade(self, target: str = "head", transactional: bool = True,
                lock: bool = True) -> int:
        """Apply pending migrations.
        
        Args:
            target: Target version ("head" for all, or specific version)
            transactional: Wrap each migration in a transaction
            lock: Acquire advisory lock during upgrade
            
        Returns:
            Number of migrations applied
        """
        # Ensure state tables exist
        self.state.ensure_tables()
        
        migrations_path = self.config.get_migrations_path()
        
        # Load all migrations
        all_migrations = self.loader.load_all_from_directory(migrations_path)
        if not all_migrations:
            self._log("No migrations found in the migrations directory.")
            return 0
        
        applied = self.state.get_applied_migrations()
        applied_versions = {m["version"] for m in applied}
        
        # Validate Head Integrity
        # ... (Existing head lock logic omitted/unaltered for now)
        # Note: We need to adapt head lock to multi-head? 
        # Actually, merge creates a single head, so "Head Lock" logic remains "Lock Single Head".
        # But if we are IN the process of merging (before applying), we might have multiple heads.
        # Strict Head Lock probably fails if we have unmerged heads? 
        # Yes, that's the point. You must merge them.
        
        # 1. Topological Sort (DAG Support)
        try:
            sorted_migrations = self._topo_sort(all_migrations)
        except Exception as e:
            raise MigrationError(f"Dependency cycle detected or invalid graph: {e}")
            
        # 2. Filter Pending
        pending = []
        for m in sorted_migrations:
            if m.version not in applied_versions:
                pending.append(m)
                
        if not pending:
             self._log("No pending migrations to apply.")
             return 0

        # 3. Target Filtering
        if target != "head":
             # Find target and its ancestors only?
             # For a DAG, "target" implies we want to reach state X.
             # We should only apply ancestors of X.
             target_mig = next((m for m in all_migrations if m.version == target), None)
             if not target_mig:
                 self._log(f"Target {target} not found.")
                 return 0
             
             ancestors = self._get_ancestors(target_mig, all_migrations)
             ancestors.add(target_mig.version)
             pending = [m for m in pending if m.version in ancestors]

        if not pending:
            self._log("No pending migrations after filtering.")
            return 0
            
        # 4. Head Lock Validation
        # If lock exists, ensure the FINAL migration in 'pending' (or current state + pending)
        # matches the lock? Or that the path leads there?
        valid_head_version = None
        try:
            head_lock = self._read_head_lock()
            if head_lock:
                 # Check if the target leads to the locked head
                 # If target="head" (default), logic ensures we go to tips.
                 # If head lock exists, it implies there SHOULD be only one valid tip.
                 # If we are merging, we might be creating that tip.
                 pass
        except:
             pass

        # Acquire lock
        if lock:
            if not self.state.acquire_lock():
                raise MigrationError("Could not acquire migration lock")
        
        try:
            count = 0
            for migration in pending:
                self._apply_migration(migration, transactional)
                count += 1
            return count
        finally:
            if lock:
                self.state.release_lock()

    async def upgrade_async(self, target: str = "head", transactional: bool = True,
                          lock: bool = True) -> int:
        """Apply pending migrations (Async)."""
        # Ensure state tables exist (Async)
        await self.state.ensure_tables_async()
        
        migrations_path = self.config.get_migrations_path()
        all_migrations = self.loader.load_all_from_directory(migrations_path)
        
        if not all_migrations:
            self._log("No migrations found.")
            return 0
            
        # Use async state manager
        applied = await self.state.get_applied_migrations_async()
        applied_versions = {m["version"] for m in applied}
        
        try:
            sorted_migrations = self._topo_sort(all_migrations)
        except Exception as e:
            raise MigrationError(f"Dependency cycle detected or invalid graph: {e}")
            
        pending = []
        for m in sorted_migrations:
            if m.version not in applied_versions:
                pending.append(m)
                
        if not pending:
             self._log("No pending migrations to apply.")
             return 0

        # Target filtering logic (same as sync)
        if target != "head":
             target_mig = next((m for m in all_migrations if m.version == target), None)
             if not target_mig:
                 self._log(f"Target {target} not found.")
                 return 0
             ancestors = self._get_ancestors(target_mig, all_migrations)
             ancestors.add(target_mig.version)
             pending = [m for m in pending if m.version in ancestors]

        if not pending:
            self._log("No pending migrations after filtering.")
            return 0
            
        if lock:
            acquired = await self.state.acquire_lock_async()
            if not acquired:
                raise MigrationError("Could not acquire migration lock")
        
        try:
            count = 0
            for migration in pending:
                await self._apply_migration_async(migration, transactional)
                count += 1
            return count
        finally:
            if lock:
                 await self.state.release_lock_async()

    async def _apply_migration_async(self, migration: Migration, transactional: bool = True) -> None:
        """Apply a single migration asynchronously.
        
        Uses savepoints for clean rollback on failure and records failures
        in the migration_failures table for debugging.
        """
        import traceback
        
        self._log(f"Applying migration (async): {migration.version}")
        start_time = time.time()
        
        # Acquire async connection from engine
        conn = await self.engine.acquire()
        try:
            # Transaction handling
            if transactional:
                # asyncpg transaction
                txn = conn.transaction()
                await txn.start()
                # Create savepoint for clean rollback
                await conn.execute("SAVEPOINT migration_checkpoint")
            
            try:
                # Context object for user migration code
                class AsyncExecuteContext:
                    def __init__(self, connection):
                        self._conn = connection
                    
                    async def execute_sql(self, sql: str, *args) -> None:
                        await self._conn.execute(sql, *args)
                        
                    async def fetch_all(self, sql: str, *args) -> List[dict]:
                        rows = await self._conn.fetch(sql, *args)
                        return [dict(row) for row in rows]
                        
                    async def fetch_one(self, sql: str, *args) -> Optional[dict]:
                        row = await self._conn.fetchrow(sql, *args)
                        return dict(row) if row else None
                
                ctx = AsyncExecuteContext(conn)
                
                # Check for timeout setting
                timeout = getattr(migration, 'timeout_seconds', None)
                if timeout:
                    self._log(f"Applying with timeout: {timeout}s")
                
                async def _run_migration_action():
                    # Check if up_async is custom
                    is_async_custom = migration.up_async.__code__ is not Migration.up_async.__code__
                    
                    if is_async_custom:
                        await migration.up_async(ctx)
                    else:
                        # Fallback to sync execution in thread
                        # Only log if not already logged (to avoid noise)
                        if getattr(migration, 'is_data_migration', False):
                            self._log(f"Running data migration {migration.version}...")
                        
                        await self._run_sync_migration_in_thread(migration, "up")
                
                if timeout:
                    try:
                        await asyncio.wait_for(_run_migration_action(), timeout=timeout)
                    except asyncio.TimeoutError as e:
                        raise MigrationError(f"Migration timed out after {timeout} seconds") from e
                else:
                    await _run_migration_action()

                if transactional:
                    await txn.commit()
                
            except Exception as e:
                # Get full stack trace for debugging
                stack_trace = traceback.format_exc()
                error_msg = str(e)
                
                if transactional:
                    # Rollback to savepoint first, then full rollback
                    try:
                        await conn.execute("ROLLBACK TO SAVEPOINT migration_checkpoint")
                    except Exception:
                        pass
                    await txn.rollback()
                
                # Record failure in database for later analysis
                try:
                    await self.state.mark_failed_async(
                        migration.version,
                        migration.message,
                        error_msg,
                        stack_trace
                    )
                except Exception as record_err:
                    self._log(f"Warning: Could not record failure: {record_err}")
                
                raise MigrationError(f"Migration {migration.version} failed: {e}") from e
        finally:
            await self.engine.release(conn)
        
        # Record history
        execution_time = int((time.time() - start_time) * 1000)
        await self.state.mark_applied_async(
            migration.version,
            migration.message,
            migration.checksum,
            execution_time
        )
        self._log(f"Applied migration: {migration.version} ({execution_time}ms)")

    async def _run_sync_migration_in_thread(self, migration: Migration, direction: str) -> None:
        """Run a sync migration using a temporary sync connection in a thread."""
        loop = asyncio.get_running_loop()
        
        def _target():
            # Build SYNC DSN from async engine config
            # We assume engine has this method or we reconstruct it
            if hasattr(self.engine, '_build_sync_dsn'):
                dsn = self.engine._build_sync_dsn()
            else:
                # Hand-craft DSN from config
                c = self.engine.config
                dsn = f"postgresql://{c.username}:{c.password}@{c.host}:{c.port}/{c.database}"
            
            # Direct psycopg connection
            with psycopg.connect(dsn) as conn:
                try:
                    # Sync Context
                    class SyncContext:
                        def __init__(self, c): self._c = c
                        def execute_sql(self, sql):
                            cur = self._c.cursor()
                            cur.execute(sql)
                            cur.close()
                    
                    ctx = SyncContext(conn)
                    
                    if direction == "up":
                        migration.up(ctx)
                    else:
                        migration.down(ctx)
                        
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
                
        await loop.run_in_executor(None, _target)

    async def downgrade_async(self, target: str = "-1") -> int:
        """Revert migrations (Async)."""
        applied = await self.state.get_applied_migrations_async()
        if not applied:
            return 0
        
        # Determine how many to rollback
        if target == "-1":
            to_rollback = [applied[-1]]
        elif target.startswith("-"):
            try:
                count = int(target)
                to_rollback = applied[count:]
            except ValueError:
                to_rollback = []
        else:
            # Rollback to specific version
            to_rollback = [m for m in reversed(applied) if m["version"] > target]
        
        if not to_rollback:
            return 0
        
        # Load migration files
        migrations_path = self.config.get_migrations_path()
        all_migrations = self.loader.load_all_from_directory(migrations_path)
        migration_map = {m.version: m for m in all_migrations}
        
        count = 0
        for record in reversed(to_rollback):
            version = record["version"]
            migration = migration_map.get(version)
            
            if migration:
                await self._rollback_migration_async(migration)
            
            await self.state.mark_rolled_back_async(version)
            count += 1
        
        return count

    async def _rollback_migration_async(self, migration: Migration) -> None:
        """Rollback a single migration (Async)."""
        self._log(f"Rolling back migration (async): {migration.version}")
        
        # Acquire async connection from engine
        conn = await self.engine.acquire()
        try:
            # asyncpg transaction
            txn = conn.transaction()
            await txn.start()
            
            try:
                # Context object for user migration code
                class AsyncExecuteContext:
                    def __init__(self, connection):
                        self._conn = connection
                    
                    async def execute_sql(self, sql: str) -> None:
                        await self._conn.execute(sql)
                
                ctx = AsyncExecuteContext(conn)
                
                # Check if down_async is custom
                is_async_custom = migration.down_async.__code__ is not Migration.down_async.__code__
                
                if is_async_custom:
                    await migration.down_async(ctx)
                else:
                    # Fallback to sync execution in thread
                    self._log(f"Migration {migration.version} down() is sync-only. Running via sync fallback.")
                    await self._run_sync_migration_in_thread(migration, "down")

                await txn.commit()
                
            except Exception as e:
                await txn.rollback()
                raise RollbackError(migration.version, e) from e
        finally:
            await self.engine.release(conn)

    def _topo_sort(self, migrations: List[Migration]) -> List[Migration]:
        """Topologically sort migrations and validate DAG."""
        map_ = {m.version: m for m in migrations}
        ts = graphlib.TopologicalSorter()
        
        # Check for missing dependencies first
        for m in migrations:
            deps = m.depends_on
            if deps:
                if isinstance(deps, str):
                    dep_list = [deps]
                else:
                    dep_list = deps
                
                for d in dep_list:
                    if d not in map_:
                        raise MigrationError(f"Migration {m.version} depends on missing migration {d}")
        
        for m in migrations:
            deps = m.depends_on
            if deps:
                if isinstance(deps, str):
                    ts.add(m.version, deps)
                elif isinstance(deps, list):
                    for d in deps:
                        ts.add(m.version, d)
            else:
                ts.add(m.version)
                
        try:
            order = list(ts.static_order())
        except graphlib.CycleError as e:
            # Provide more details about the cycle
            cycle = " -> ".join(e.args[1]) if e.args and isinstance(e.args[1], (list, tuple)) else str(e)
            raise MigrationError(f"Dependency cycle detected or invalid graph: {cycle}") from e
            
        # Convert versions back to objects
        return [map_[v] for v in order if v in map_]

    def _get_ancestors(self, migration: Migration, all_migrations: List[Migration]) -> Set[str]:
        """Get all ancestor versions for a migration."""
        map_ = {m.version: m for m in all_migrations}
        ancestors = set()
        queue = [migration]
        
        while queue:
            curr = queue.pop(0)
            deps = curr.depends_on
            if deps:
                if isinstance(deps, str):
                    dep_list = [deps]
                else:
                    dep_list = deps
                
                for d in dep_list:
                    if d not in ancestors and d in map_:
                        ancestors.add(d)
                        queue.append(map_[d])
        return ancestors

    def merge(self, message: str, revisions: Optional[List[str]] = None) -> Optional[Migration]:
        """Merge multiple heads into a new migration."""
        migrations_path = self.config.get_migrations_path()
        all_migrations = self.loader.load_all_from_directory(migrations_path)
        
        if revisions:
            heads_to_merge = revisions
        else:
            heads_to_merge = self.heads()
            
        if len(heads_to_merge) < 2:
            self._log("Need at least 2 heads to merge.")
            return None
            
        # Verify heads exist
        map_ = {m.version: m for m in all_migrations}
        for h in heads_to_merge:
            if h not in map_:
                raise MigrationError(f"Revision {h} not found.")

        # Generate empty migration with multiple dependencies
        head_id = str(uuid.uuid4())
        
        version, filename, content = self.generator.generate_empty(
            message=message,
            config=self.config,
            depends_on=heads_to_merge,
            head_id=head_id
        )
        
        path = migrations_path / filename
        with open(path, "w") as f:
            f.write(content)
            
        self._log(f"Generated merge migration: {filename}")
        self._log(f"  Merges: {', '.join(heads_to_merge)}")
        
        # Update lock to this new merge
        self._write_head_lock(version, head_id)
        
        return self.loader.load_from_file(path)
    
    def _apply_migration(self, migration: Migration, transactional: bool = True) -> None:
        """Apply a single migration.
        
        Uses savepoints for clean rollback on failure and records failures
        in the migration_failures table for debugging.
        """
        import traceback
        
        self._log(f"Applying migration: {migration.version}")
        
        start_time = time.time()
        dsn = self.engine._build_sync_dsn()
        
        conn = psycopg.connect(dsn)
        try:
            if transactional:
                conn.autocommit = False
                # Create savepoint for clean rollback
                cur = conn.cursor()
                cur.execute("SAVEPOINT migration_checkpoint")
                cur.close()
            else:
                conn.autocommit = True
            
            # Create a simple engine-like wrapper for execute_sql
            class ExecuteContext:
                def __init__(self, connection):
                    self._conn = connection
                
                def execute_sql(self, sql: str) -> None:
                    cur = self._conn.cursor()
                    cur.execute(sql)
                    cur.close()
            
            ctx = ExecuteContext(conn)
            
            try:
                migration.up(ctx)
                
                if transactional:
                    conn.commit()
                
            except Exception as e:
                # Get full stack trace for debugging
                stack_trace = traceback.format_exc()
                error_msg = str(e)
                
                if transactional:
                    # Rollback to savepoint first, then full rollback
                    try:
                        cur = conn.cursor()
                        cur.execute("ROLLBACK TO SAVEPOINT migration_checkpoint")
                        cur.close()
                    except Exception:
                        pass
                    conn.rollback()
                
                # Record failure in database for later analysis
                try:
                    self.state.mark_failed(
                        migration.version,
                        migration.message,
                        error_msg,
                        stack_trace
                    )
                except Exception as record_err:
                    self._log(f"Warning: Could not record failure: {record_err}")
                
                raise MigrationError(f"Migration {migration.version} failed: {e}") from e
        
        finally:
            conn.close()
        
        # Record in history
        execution_time = int((time.time() - start_time) * 1000)
        self.state.mark_applied(
            migration.version,
            migration.message,
            migration.checksum,
            execution_time
        )
        
        self._log(f"Applied migration: {migration.version} ({execution_time}ms)")
    
    # =========================================================================
    # CLI methods
    # =========================================================================
    
    def downgrade(self, target: str = "-1") -> int:
        """Rollback migrations.
        
        Args:
            target: Target version ("-1" for one step back, or specific version)
            
        Returns:
            Number of migrations rolled back
        """
        applied = self.state.get_applied_migrations()
        if not applied:
            return 0
        
        # Determine how many to rollback
        if target == "-1":
            to_rollback = [applied[-1]]
        elif target.startswith("-"):
            try:
                count = int(target)
                to_rollback = applied[count:]
            except ValueError:
                to_rollback = []
        else:
            # Rollback to specific version
            to_rollback = [m for m in reversed(applied) if m["version"] > target]
        
        if not to_rollback:
            return 0
        
        # Load migration files
        migrations_path = self.config.get_migrations_path()
        all_migrations = self.loader.load_all_from_directory(migrations_path)
        migration_map = {m.version: m for m in all_migrations}
        
        count = 0
        for record in reversed(to_rollback):
            version = record["version"]
            migration = migration_map.get(version)
            
            if migration:
                self._rollback_migration(migration)
            
            self.state.mark_rolled_back(version)
            count += 1
        
        return count
    
    def _rollback_migration(self, migration: Migration) -> None:
        """Rollback a single migration."""
        self._log(f"Rolling back migration: {migration.version}")
        
        dsn = self.engine._build_sync_dsn()
        conn = psycopg.connect(dsn)
        
        try:
            class ExecuteContext:
                def __init__(self, connection):
                    self._conn = connection
                
                def execute_sql(self, sql: str) -> None:
                    cur = self._conn.cursor()
                    cur.execute(sql)
                    cur.close()
            
            ctx = ExecuteContext(conn)
            
            try:
                migration.down(ctx)
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise RollbackError(migration.version, e) from e
        finally:
            conn.close()
    
    def history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get migration history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of migration history entries
        """
        applied = self.state.get_applied_migrations()
        return applied[-limit:] if limit else applied

    async def history_async(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get migration history (Async).
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of migration history entries
        """
        await self._ensure_async_setup()
        applied = await self.state.get_applied_migrations_async()
        return applied[-limit:] if limit else applied
    
    def check(self) -> bool:
        """Check if there are pending migrations or drift.
        
        Returns:
            True if there ARE pending migrations or drift (changes detected)
        """
        status = self.status()
        return status.pending_count > 0 or status.has_drift
    
    def current(self) -> Optional[str]:
        """Get the current migration version.
        
        Returns:
            Current version string or None
        """
        return self.state.get_current_version()
    
    def stamp(self, version: str) -> None:
        """Mark a version as applied without running it.
        
        Args:
            version: Version to stamp
        """
        self.state.mark_applied(version, "Stamped", "", 0)
        self._log(f"Stamped version: {version}")
    
    def generate_sql(self, direction: str = "up", target: str = "head") -> List[str]:
        """Preview SQL for migrations (dry run).
        
        Args:
            direction: "up" or "down"
            target: Target version
            
        Returns:
            List of SQL statements
        """
        diff = self._compute_diff(context="SQL Dry Run")
        up_stmts, down_stmts = self.ddl_gen.generate_from_diff(diff)
        
        return up_stmts if direction == "up" else down_stmts

    async def generate_sql_async(self, direction: str = "up", target: str = "head") -> List[str]:
        """Preview SQL for migrations (dry run) (Async).
        
        Args:
            direction: "up" or "down"
            target: Target version
            
        Returns:
            List of SQL statements
        """
        await self._ensure_async_setup()
        diff = await self._compute_diff_async(context="SQL Dry Run")
        up_stmts, down_stmts = self.ddl_gen.generate_from_diff(diff)
        
        return up_stmts if direction == "up" else down_stmts

    def _read_head_lock(self) -> Optional[Dict[str, str]]:
        """Read the head.lock file."""
        path = self.config.get_migrations_path() / self.config.head_lock_file
        if not path.exists():
            return None
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return None

    def _write_head_lock(self, version: str, head_id: str) -> None:
        """Write the head.lock file."""
        path = self.config.get_migrations_path() / self.config.head_lock_file
        with open(path, "w") as f:
            json.dump({"version": version, "head_id": head_id}, f, indent=2)
    
    def heads(self) -> List[str]:
        """Get all migration head versions.
        
        Returns:
            List of head version strings
        """
        migrations_path = self.config.get_migrations_path()
        all_migrations = self.loader.load_all_from_directory(migrations_path)
        
        if not all_migrations:
            return []
        
        # Find migrations that are not dependencies of any other
        all_versions = {m.version for m in all_migrations}
        dependencies = {m.depends_on for m in all_migrations if m.depends_on}
        
        heads = all_versions - dependencies
        return sorted(heads)

    def branch(self, message: str, from_revision: str = None, 
               branch_label: str = None) -> Optional[Migration]:
        """Create a new migration branch from a specific revision.
        
        This enables parallel development workflows where multiple
        developers can work on different features independently.
        
        Args:
            message: Message for the branch migration
            from_revision: Revision to branch from (default: current head)
            branch_label: Optional label to identify this branch
            
        Returns:
            New branch migration, or None on failure
            
        Usage:
            # Create branch from current head
            manager.branch("feature-auth", branch_label="auth")
            
            # Create branch from specific revision
            manager.branch("feature-payments", from_revision="v0001_initial")
            
            # Later, merge branches
            manager.merge("merge-features")
        """
        migrations_path = self.config.get_migrations_path()
        all_migrations = self.loader.load_all_from_directory(migrations_path)
        
        # Determine branch point
        if from_revision:
            # Verify revision exists
            found = any(m.version == from_revision for m in all_migrations)
            if not found:
                self._log(f"Revision {from_revision} not found")
                return None
            branch_from = from_revision
        else:
            # Branch from current head(s)
            current_heads = self.heads()
            if not current_heads:
                self._log("No existing migrations to branch from")
                branch_from = None
            elif len(current_heads) == 1:
                branch_from = current_heads[0]
            else:
                # Multiple heads exist - user should merge first or specify
                self._log(f"Multiple heads detected: {current_heads}")
                self._log("Please specify from_revision or merge heads first")
                return None
        
        # Generate branch migration
        head_id = str(uuid.uuid4())
        
        # Include branch label in message if provided
        if branch_label:
            full_message = f"[{branch_label}] {message}"
        else:
            full_message = message
        
        version, filename, content = self.generator.generate_empty(
            message=full_message,
            config=self.config,
            depends_on=branch_from,
            head_id=head_id
        )
        
        path = migrations_path / filename
        with open(path, "w") as f:
            f.write(content)
            
        self._log(f"Created branch migration: {filename}")
        if branch_from:
            self._log(f"  Branches from: {branch_from}")
        if branch_label:
            self._log(f"  Label: {branch_label}")
        
        return self.loader.load_from_file(path)

    def show_branches(self) -> Dict[str, List[str]]:
        """Show all migration branches.
        
        Returns:
            Dict mapping branch labels to their revision chains
        """
        migrations_path = self.config.get_migrations_path()
        all_migrations = self.loader.load_all_from_directory(migrations_path)
        
        if not all_migrations:
            return {}
        
        # Build dependency graph
        children: Dict[str, List[str]] = {}  # parent -> [children]
        for m in all_migrations:
            deps = m.depends_on if isinstance(m.depends_on, list) else [m.depends_on] if m.depends_on else []
            for d in deps:
                if d not in children:
                    children[d] = []
                children[d].append(m.version)
        
        # Find branch points (revisions with multiple children)
        branch_points = {v: c for v, c in children.items() if len(c) > 1}
        
        # For each branch point, trace paths to heads
        heads = set(self.heads())
        branches = {}
        
        for bp, kids in branch_points.items():
            for kid in kids:
                # Trace from kid to head
                path = [kid]
                current = kid
                while current not in heads:
                    next_children = children.get(current, [])
                    if not next_children:
                        break
                    current = next_children[0]  # Follow first child
                    path.append(current)
                
                # Use first migration message for branch label
                first_mig = next((m for m in all_migrations if m.version == kid), None)
                label = first_mig.message if first_mig else kid
                branches[f"{bp} -> {label}"] = path
        
        return branches
    
    async def dry_run_async(self, target: str = "head") -> List[Dict[str, Any]]:
        """Preview migrations that would be applied (Async)."""
        await self._ensure_async_setup()
        
        migrations_path = self.config.get_migrations_path()
        all_migrations = self.loader.load_all_from_directory(migrations_path)
        
        applied = await self.state.get_applied_migrations_async()
        applied_versions = {m["version"] for m in applied}
        
        pending = [m for m in all_migrations if m.version not in applied_versions]
        
        if target != "head":
            pending = [m for m in pending if m.version <= target]
        
        return [
            {
                "version": m.version,
                "message": m.message,
                "depends_on": m.depends_on,
            }
            for m in pending
        ]

    def dry_run(self, target: str = "head") -> List[Dict[str, Any]]:
        """Preview migrations that would be applied.
        
        Args:
            target: Target version
            
        Returns:
            List of migration info dicts
        """
        migrations_path = self.config.get_migrations_path()
        all_migrations = self.loader.load_all_from_directory(migrations_path)
        
        applied = self.state.get_applied_migrations()
        applied_versions = {m["version"] for m in applied}
        
        pending = [m for m in all_migrations if m.version not in applied_versions]
        
        if target != "head":
            pending = [m for m in pending if m.version <= target]
        
        return [
            {
                "version": m.version,
                "message": m.message,
                "depends_on": m.depends_on,
            }
            for m in pending
        ]
    
    async def verify_async(self) -> List[Dict[str, Any]]:
        """Verify checksums of applied migrations (Async)."""
        await self._ensure_async_setup()
        
        migrations_path = self.config.get_migrations_path()
        all_migrations = self.loader.load_all_from_directory(migrations_path)
        migration_map = {m.version: m for m in all_migrations}
        
        applied = await self.state.get_applied_migrations_async()
        
        results = []
        for record in applied:
            version = record["version"]
            stored_checksum = record.get("checksum", "")
            
            migration = migration_map.get(version)
            if migration:
                current_checksum = migration.checksum
                valid = stored_checksum == current_checksum or not stored_checksum
            else:
                current_checksum = None
                valid = False
            
            results.append({
                "version": version,
                "message": record.get("message", ""),
                "stored_checksum": stored_checksum,
                "current_checksum": current_checksum,
                "valid": valid,
            })
        
        return results

    def verify(self) -> List[Dict[str, Any]]:
        """Verify checksums of applied migrations.
        
        Returns:
            List of verification results
        """
        migrations_path = self.config.get_migrations_path()
        all_migrations = MigrationLoader.load_all_from_directory(migrations_path)
        migration_map = {m.version: m for m in all_migrations}
        
        applied = self.state.get_applied_migrations()
        
        results = []
        for record in applied:
            version = record["version"]
            stored_checksum = record.get("checksum", "")
            
            migration = migration_map.get(version)
            if migration:
                current_checksum = migration.checksum
                valid = stored_checksum == current_checksum or not stored_checksum
            else:
                current_checksum = None
                valid = False
            
            results.append({
                "version": version,
                "message": record.get("message", ""),
                "stored_checksum": stored_checksum,
                "current_checksum": current_checksum,
                "valid": valid,
            })
        
        return results
    
    def squash(self, message: str, start: str, end: str) -> Optional[Migration]:
        """Squash multiple migrations into one.
        
        Args:
            message: Message for the squashed migration
            start: Starting version (exclusive)
            end: Ending version (inclusive)
            
        Returns:
            New squashed migration, or None
        """
        """Squash a range of migrations into a single file.
        
        Args:
            message: Message for the new squash migration
            start: Start version (inclusive)
            end: End version (inclusive)
            
        Returns:
            The new squash Migration object, or None on failure
        """
        import inspect
        
        # 1. Load all migrations
        migrations = self.loader.load_all_from_directory(self.config.get_migrations_path())
        
        # 2. Find range indices
        start_idx = -1
        end_idx = -1
        
        for i, m in enumerate(migrations):
            if m.version == start:
                start_idx = i
            if m.version == end:
                end_idx = i
                
        if start_idx == -1 or end_idx == -1:
            self._log(f"Could not find start ({start}) or end ({end}) version")
            return None
            
        if start_idx > end_idx:
            self._log(f"Start version {start} is after end version {end}")
            return None
            
        subset = migrations[start_idx : end_idx + 1]
        self._log(f"Squashing {len(subset)} migrations: {start} -> {end}")
        
        # 3. Concatenate UP and DOWN bodies
        combined_up = []
        combined_down = [] # Should be reversed
        
        for m in subset:
            # UP
            try:
                lines, _ = inspect.getsourcelines(m.up)
                # Skip 'def up...' and docstring?
                # A heuristic: take everything after the first docstring closure?
                # Or simplistic: take everything non-docstring.
                # Let's rely on source lines skipping the def signature logic manually.
                
                body = []
                in_def = True
                for line in lines:
                    if in_def:
                        if line.strip().startswith("def up"):
                            in_def = False
                        continue
                    body.append(line)
                    
                # Dedent
                if body:
                    # simplistic dedent based on first line
                    first_line = next((x for x in body if x.strip()), "")
                    indent = len(first_line) - len(first_line.lstrip())
                    dedented = [L[indent:] if len(L) > indent else L.lstrip() for L in body]
                    
                    combined_up.append(f"        # --- {m.version}: {m.message} ---")
                    combined_up.extend(["        " + L for L in dedented]) # Re-indent for new file
            except Exception as e:
                self._log(f"Error reading source for {m.version}: {e}")
                
        for m in reversed(subset):
            # DOWN
            try:
                lines, _ = inspect.getsourcelines(m.down)
                body = []
                in_def = True
                for line in lines:
                    if in_def:
                        if line.strip().startswith("def down"):
                            in_def = False
                        continue
                    body.append(line)
                    
                if body:
                    first_line = next((x for x in body if x.strip()), "")
                    indent = len(first_line) - len(first_line.lstrip())
                    dedented = [L[indent:] if len(L) > indent else L.lstrip() for L in body]
                    
                    combined_down.append(f"        # --- {m.version}: {m.message} ---")
                    combined_down.extend(["        " + L for L in dedented])
            except Exception:
                pass

        # 4. Generate new migration
        depends_on = subset[0].depends_on
        
        # We manually construct content using the Generator's template but bypassing raw statements
        # Or better: make a temporary helper or just format it here.
        
        # Using Generator internals (a bit hacky but Generator is in our control)
        from .migration import MigrationGenerator
        
        version = MigrationGenerator.generate_version(self.config)
        clean_msg = MigrationGenerator.sanitize_message(message)
        filename = f"{version}_{clean_msg}.py"
        class_name = f"Migration_{version}"
        head_id = str(uuid.uuid4())
        
        if isinstance(depends_on, list):
            depends_str = "[" + ", ".join(f'"{d}"' for d in depends_on) + "]"
        else:
            depends_str = f'"{depends_on}"' if depends_on else "None"

        # Join lines
        up_code = "".join(combined_up).strip()
        down_code = "".join(combined_down).strip()
        
        if not up_code: up_code = "        pass"
        if not down_code: down_code = "        pass"
        
        content = MigrationGenerator.TEMPLATE.format(
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            class_name=class_name,
            version=version,
            depends_on=depends_str,
            head_id=head_id,
            up_statements=up_code,
            down_statements=down_code,
        )
        
        # 5. Write new file
        path = self.config.get_migrations_path() / filename
        with open(path, "w") as f:
            f.write(content)
            
        self._log(f"Created squash migration: {filename}")
        
        # 6. Delete old files
        for m in subset:
            # Try to find file path
            # The loader should have attached it, or we infer it?
            # State/Migration object doesn't have file_path by default in base class, 
            # but loader might have set it? Let's check loader or just glob.
            # Assuming standard naming: version_*.py
            
            # Robust way: glob
            found = list(self.config.get_migrations_path().glob(f"{m.version}_*.py"))
            for p in found:
                p.unlink()
                self._log(f"Deleted old migration: {p.name}")

        m_obj = self.loader.load_from_file(path)
        return m_obj
    
    async def seed_async(self, file_path: str, env: str = "default") -> int:
        """Load seed data from file (Async)."""
        import json
        
        path = Path(file_path)
        if not path.exists():
            raise MigrationError(f"Seed file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Filter by environment if specified
        if isinstance(data, dict) and env in data:
            data = data[env]
        
        # Process seed data
        count = 0
        conn = await self.engine.acquire()
        try:
             # Transaction
             txn = conn.transaction()
             await txn.start()
             try:
                 for table_name, records in data.items():
                     for record in records:
                         columns = list(record.keys())
                         values = list(record.values())
                         
                         # Asyncpg uses $1, $2, etc.
                         placeholders = ", ".join([f"${i+1}" for i in range(len(values))])
                         cols_sql = ", ".join(columns)
                         
                         sql = f"INSERT INTO {table_name} ({cols_sql}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                         await conn.execute(sql, *values)
                         count += 1
                 await txn.commit()
             except Exception:
                 await txn.rollback()
                 raise
        finally:
            await self.engine.release(conn)
        
        self._log(f"Seeded {count} records from {file_path} (Async)")
        return count

    def seed(self, file_path: str, env: str = "default") -> int:
        """Load seed data from file.
        
        Args:
            file_path: Path to JSON/YAML seed file
            env: Environment name for filtering
            
        Returns:
            Number of records seeded
        """
        import json
        
        path = Path(file_path)
        if not path.exists():
            raise MigrationError(f"Seed file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Filter by environment if specified
        if isinstance(data, dict) and env in data:
            data = data[env]
        
        # Process seed data
        count = 0
        dsn = self.engine._build_sync_dsn()
        conn = psycopg.connect(dsn)
        
        try:
            cur = conn.cursor()
            
            for table_name, records in data.items():
                for record in records:
                    columns = list(record.keys())
                    values = list(record.values())
                    placeholders = ", ".join(["%s"] * len(values))
                    cols_sql = ", ".join(columns)
                    
                    sql = f"INSERT INTO {table_name} ({cols_sql}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                    cur.execute(sql, values)
                    count += 1
            
            conn.commit()
            cur.close()
        finally:
            conn.close()
        
        self._log(f"Seeded {count} records from {file_path}")
        return count
    
    # =========================================================================
    # Multi-database support
    # =========================================================================
    
    @staticmethod
    def upgrade_multi(databases: List[Dict[str, Any]], target: str = "head",
                      parallel: bool = True) -> Dict[str, int]:
        """Upgrade multiple databases.
        
        Args:
            databases: List of database configs with 'name' and 'dsn'
            target: Target version
            parallel: Run in parallel (up to 10 workers)
            
        Returns:
            Dict of {database_name: migrations_applied}
        """
        import concurrent.futures
        results = {}
        
        def _upgrade_single(db_config):
            db_name = db_config.get("name", "unknown")
            try:
                # Create engine for this database
                from ..core.engine import create_engine
                engine = create_engine(
                    dsn=db_config.get("dsn"),
                    ensure_database=False,
                    ensure_tables=False,
                    check_schema_drift=False,
                )
                
                manager = MigrationManager(engine)
                count = manager.upgrade(target)
                engine.dispose()
                return db_name, count
            except Exception as e:
                # Log error?
                return db_name, -1

        if parallel:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(databases), 10)) as executor:
                future_to_db = {executor.submit(_upgrade_single, db): db for db in databases}
                for future in concurrent.futures.as_completed(future_to_db):
                    db_name, count = future.result()
                    results[db_name] = count
        else:
            for db in databases:
                db_name, count = _upgrade_single(db)
                results[db_name] = count
        
        return results
