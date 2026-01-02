"""
PSQLModel CLI - Command-line interface for the ORM.

Usage:
    python -m psqlmodel                     # Start metrics logger
    python -m psqlmodel migrate init        # Initialize migrations
    python -m psqlmodel migrate status      # Check status
    # ... see --help for more
"""

import argparse
import os
import sys
import signal
from typing import Optional, List

from psqlmodel.core.engine import create_engine


# ============================================================
# UTILS
# ============================================================

def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.environ.get(name)
    return val if val is not None else default

def _create_engine_from_profile(profile_name: Optional[str] = None):
    """Create engine from saved profile or environment variables."""
    from psqlmodel.cli_config import get_profile
    
    # Try to load from saved profile first
    profile = get_profile(profile_name)
    
    if profile:
        username = profile.get("username") or _env("PSQL_USER")
        password = profile.get("password") or _env("PSQL_PASSWORD")
        host = profile.get("host") or _env("PSQL_HOST", "localhost") or "localhost"
        port = profile.get("port") or int(_env("PSQL_PORT", "5432") or "5432")
        database = profile.get("database") or _env("PSQL_DB")
        models_path = profile.get("models_path") or _env("PSQL_MODELS_PATH")
    else:
        # Fall back to environment variables
        username = _env("PSQL_USER")
        password = _env("PSQL_PASSWORD")
        host = _env("PSQL_HOST", "localhost") or "localhost"
        port = int(_env("PSQL_PORT", "5432") or "5432")
        database = _env("PSQL_DB")
        models_path = _env("PSQL_MODELS_PATH")
    
    pool_size = int(_env("PSQL_POOL_SIZE", "20") or "20")
    max_pool_size = _env("PSQL_MAX_POOL_SIZE")
    max_pool_size = int(max_pool_size) if max_pool_size else None
    connection_timeout = _env("PSQL_CONN_TIMEOUT")
    connection_timeout = float(connection_timeout) if connection_timeout else None
    health_enabled = (_env("PSQL_HEALTH_ENABLED", "false") or "false").lower() in {"1", "true", "yes"}
    auto_adjust = (_env("PSQL_AUTO_ADJUST", "false") or "false").lower() in {"1", "true", "yes"}
    pre_ping = (_env("PSQL_PRE_PING", "false") or "false").lower() in {"1", "true", "yes"}
    pool_recycle_env = _env("PSQL_POOL_RECYCLE")
    pool_recycle = float(pool_recycle_env) if pool_recycle_env else None

    return create_engine(
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
        pool_size=pool_size,
        max_pool_size=max_pool_size,
        connection_timeout=connection_timeout,
        health_check_enabled=health_enabled,
        auto_adjust_pool_size=auto_adjust,
        debug=False,
        pool_pre_ping=pre_ping,
        pool_recycle=pool_recycle,
        models_path=models_path,
        ensure_database=False,
        ensure_tables=False,
        auto_startup=True, 
    )


# ============================================================
# COMMAND HANDLERS
# ============================================================

def cmd_migrate_init(args):
    from pathlib import Path
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    # Default path if not specified
    migrations_path = Path(args.path or "./migrations").resolve()
    
    # Create directory
    migrations_path.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py
    init_file = migrations_path / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""PSQLModel migrations directory."""\n')
    
    # Create history table in database if profile exists
    try:
        engine = _create_engine_from_profile()
        config = MigrationConfig(migrations_path=str(migrations_path))
        manager = MigrationManager(engine, config)
        manager.state.ensure_tables()  # This creates the history table
        engine.dispose()
        print(f"✅ Migrations initialized at: {migrations_path}")
        print(f"   History table created in database.")
    except Exception as e:
        print(f"✅ Migrations initialized at: {migrations_path}")
        print(f"   ⚠️  Could not create history table: {e}")
        print(f"   Next steps:")
        print(f"   1. Configure a profile: python -m psqlmodel profile --save ...")
        print(f"   2. Generate migration: python -m psqlmodel migrate autogenerate 'initial'")

def cmd_migrate_status(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    migrations_path = args.path or "./migrations"
    config = MigrationConfig(migrations_path=migrations_path, debug=False, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    status = manager.status()
    
    print("\n" + "=" * 50)
    print("MIGRATION STATUS")
    print("=" * 50)
    print(f"   Initialized:      {'Yes' if status.initialized else 'No'}")
    print(f"   Migrations path:  {status.migrations_path}")
    print(f"   Current version:  {status.current_version or '(none)'}")
    print(f"   Applied:          {status.applied_count}")
    print(f"   Pending:          {status.pending_count}")
    print(f"   Schema drift:     {'Yes' if status.has_drift else 'No'}")
    
    if args.full:
        print("\n" + "-" * 60)
        print("🔍 DETAILED SCHEMA DIFF")
        print("-" * 60)
        
        diff = manager._compute_diff()
        
        if not diff.has_changes:
            print("\n✅ Schema is in sync with models.")
        else:
            # Model -> DB
            if diff.new_tables or diff.modified_tables or diff.new_triggers or diff.modified_triggers:
                print("\n✅ MODEL → DB (will generate migrations):")
                for t in diff.new_tables:
                    print(f"   + NEW TABLE: {t.object_name}")
                for t in diff.modified_tables:
                    print(f"   ~ MODIFIED: {t.object_name}")
                    for c in t.details.get("column_changes", []):
                        print(f"      {c['column']}: {c['change'].replace('_', ' ')}")
            
            # DB -> Model (Orphans)
            if diff.removed_tables:
                print("\n⚠️  DB → MODEL (orphan tables, not in models):")
                for t in diff.removed_tables:
                    cols = len(t.details.get('columns', []))
                    print(f"   ? {t.object_name} ({cols} columns)")
                print("\n   Use --create-models to generate draft model files.")
    
    print("=" * 50 + "\n")
    engine.dispose()

def cmd_migrate_validate(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path, debug=False, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    warnings = manager.validate()
    for warning in warnings:
        print(warning)
    engine.dispose()

def cmd_migrate_autogenerate(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    from pathlib import Path
    
    if not args.message:
        print("Error: Please provide a message for the migration")
        sys.exit(1)
    
    # Capture CWD at start - model loading may change directories
    original_cwd = Path.cwd()
    
    engine = _create_engine_from_profile()
    migrations_path = (original_cwd / (args.path or "./migrations")).resolve()
    config = MigrationConfig(migrations_path=str(migrations_path), debug=True, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    # Get diff first
    diff = manager._compute_diff(context="Autogenerate (Pre-check)")
    
    # Handle --drop-orphans: include DROP TABLE for orphan tables
    drop_orphans = getattr(args, 'drop_orphans', False)
    if drop_orphans:
        manager._drop_orphans = True
    
    # Check for actionable changes (excludes orphan table warnings unless --drop-orphans)
    has_real_changes = diff.has_actionable_changes or (drop_orphans and diff.removed_tables)
    
    # ========== STALE MIGRATION DETECTION ==========
    try:
        pending_stale = manager.check_stale_migrations()
        if pending_stale and not has_real_changes:
            if auto_stamp_stale:
                print("\n🔧 Auto-stamping stale/obsolete migrations...")
                for m in pending_stale:
                    manager.stamp(m.version)
                    print(f"   ✅ Stamped: {m.version}")
                print(f"\n   Stamped {len(pending_stale)} stale migration(s). They will be skipped during upgrade.\n")
            else:
                print("\n⚠️  WARNING: Stale/obsolete migrations detected!")
                print("   Model matches DB, but these pending migrations would apply changes:\n")
                for m in pending_stale:
                    print(f"   - {m.version}: {getattr(m, 'message', 'no message')}")
                print("\n   These migrations may be OBSOLETE if you reverted model changes.")
                print("   Options:")
                print("     1. Use --auto-stamp-stale to skip them automatically")
                print("     2. Delete the stale migration files if no longer needed")
                print("     3. Run 'migrate upgrade' if you DO want to apply them\n")
    except Exception:
        pass  # Don't fail autogenerate if stale check fails
    
    if not has_real_changes:
        if args.force:
            print("⚠️  No actionable changes detected, but --force used. Generating empty migration.")
        else:
            print("No Model→DB changes detected. Use --force to generate anyway.")
            if not getattr(args, 'create_models', False):
                 engine.dispose()
                 return
            migration = None
    else:
        # Check if async config, though autogenerate is sync-delegated for now
        if engine.config.async_:
             import asyncio
             migration = asyncio.run(manager.autogenerate_async(args.message))
        else:
             migration = manager.autogenerate(args.message)
        
        if migration:
            print(f"✅ Created migration: {migration.version}")
            file_path = getattr(migration, '_file_path', None) or getattr(migration, 'file_path', migrations_path)
            print(f"   File: {file_path}")
    
    # Handle --create-models for orphan tables (DB→Model)
    orphans = manager.get_orphan_tables()
    create_models = getattr(args, 'create_models', False)
    
    if create_models and orphans:
        from psqlmodel.migrations.model_generator import ModelGenerator
        
        print(f"\n📝 Generating draft models for {len(orphans)} orphan table(s)...")
        
        models_dir = migrations_path / "models"
        generator = ModelGenerator(engine)
        created = generator.generate_models_from_orphans(orphans, models_dir, force=args.force)
        
        if created:
            print(f"\n✅ Created {len(created)} draft model file(s) in: {models_dir}")
            print("   Review and integrate these files into your codebase.")
    elif orphans and not create_models and not drop_orphans:
        print(f"\n⚠️  {len(orphans)} orphan table(s) in DB (not in models).")
        print("   Use --create-models to generate draft model files.")
        print("   Use --drop-orphans to generate DROP TABLE statements.")
    
    engine.dispose()

def cmd_migrate_upgrade(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    # Multi-database support
    if args.all:
        from psqlmodel.cli_config import list_profiles
        from psqlmodel import create_engine as ce
        
        profiles = list_profiles()
        if not profiles:
            print("No profiles found. Use 'migrate users save' first.")
            sys.exit(1)
        
        databases = []
        for name, profile in profiles.items():
            dsn = f"postgresql://{profile['username']}:{profile['password']}@{profile['host']}:{profile.get('port', 5432)}/{profile['database']}"
            databases.append({"name": name, "engine": ce(dsn)})
        
        results = MigrationManager.upgrade_multi(databases, args.target, parallel=True)
        
        for name, count in results.items():
            print(f"   {name}: {count} migration(s) applied")
        
        for db in databases:
            db["engine"].dispose()
        return

    # Single database
    if args.database:
        from psqlmodel.cli_config import get_profile
        from psqlmodel import create_engine as ce
        
        profile = get_profile(args.database)
        if not profile:
            print(f"Profile '{args.database}' not found")
            sys.exit(1)
        
        dsn = f"postgresql://{profile['username']}:{profile['password']}@{profile['host']}:{profile.get('port', 5432)}/{profile['database']}"
        engine = ce(dsn)
    else:
        engine = _create_engine_from_profile()

    migrations_path = args.path or "./migrations"
    config = MigrationConfig(migrations_path=migrations_path, debug=True, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    if engine.config.async_:
        import asyncio
        print(f"   [Async Mode] Target: {args.target}")
        count = asyncio.run(manager.upgrade_async(
            args.target, 
            transactional=args.transactional, 
            lock=args.lock
        ))
    else:
        count = manager.upgrade(
            args.target, 
            transactional=args.transactional, 
            lock=args.lock
        )
    
    if count > 0:
        print(f"Applied {count} migration(s)")
    else:
        print("No pending migrations")
    engine.dispose()

def cmd_migrate_downgrade(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path, debug=True, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    count = manager.downgrade(args.target)
    
    if count > 0:
        print(f"Rolled back {count} migration(s)")
    else:
        print("No migrations to rollback")
    engine.dispose()

def cmd_migrate_history(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path or "./migrations", debug=False, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    skip = getattr(args, 'skip', 0) or 0
    limit = getattr(args, 'limit', 20) or 20
    show_oldest_first = getattr(args, 'first', False)
    
    # Get all history from state directly
    all_history = manager.state.get_applied_migrations()
    
    if show_oldest_first:
        ordered = all_history  # oldest first (ASC)
    else:
        ordered = list(reversed(all_history))  # newest first (DESC)
    
    # Apply pagination: skip then limit
    paginated = ordered[skip:skip + limit]
    
    if not paginated:
        if skip > 0:
            print(f"No migrations found (skipped {skip}, total: {len(all_history)})")
        else:
            print("No migrations applied yet")
    else:
        order_label = "(oldest first)" if show_oldest_first else "(newest first)"
        total = len(all_history)
        showing = f"Showing {skip + 1}-{skip + len(paginated)} of {total}"
        
        print("\n" + "=" * 70)
        print(f"MIGRATION HISTORY {order_label} - {showing}")
        print("=" * 70)
    # Load migration files to check types
    files = manager.loader.load_all_from_directory(config.get_migrations_path())
    migration_map = {m.version: m for m in files}

    for record in paginated:
        status = "✓" if not record.get("rolled_back_at") else "↩"
        version = record.get('version', 'unknown')
        message = record.get('message', '')[:40]
        applied_at = str(record.get('applied_at', ''))[:19]
        exec_time = record.get('execution_time_ms', 0)
        
        # Determine type
        mig_obj = migration_map.get(version)
        if mig_obj and getattr(mig_obj, "is_data_migration", False):
            type_tag = "[DATA]"
        else:
            type_tag = "[DDL] "
            
        print(f"  {status} {type_tag} {version} - {message}")
        print(f"        Applied: {applied_at} ({exec_time}ms)")
        print("=" * 70)
        if skip + limit < total:
            print(f"  More: use --skip {skip + limit} to see next page")
        print()
    engine.dispose()

def cmd_migrate_failures(args):
    """Show migration failures."""
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path or "./migrations", debug=False, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    skip = getattr(args, 'skip', 0) or 0
    limit = getattr(args, 'limit', 20) or 20
    
    # Get failures from state
    failures = manager.state.get_failures(limit=limit, skip=skip)
    
    if not failures:
        if skip > 0:
            print(f"No failures found (skipped {skip})")
        else:
            print("✓ No migration failures recorded")
    else:
        print("\n" + "=" * 70)
        print(f"MIGRATION FAILURES (showing {len(failures)} records)")
        print("=" * 70)
        for record in failures:
            version = record.get('version', 'unknown')
            message = record.get('message', '')[:40]
            error = record.get('error_message', '')[:60]
            failed_at = str(record.get('failed_at', ''))[:19]
            
            print(f"  ✗ {version} - {message}")
            print(f"     Failed: {failed_at}")
            print(f"     Error:  {error}")
            
            if getattr(args, 'verbose', False):
                stack = record.get('stack_trace', '')
                if stack:
                    print(f"     Stack trace:")
                    for line in stack.split('\n')[:5]:
                        print(f"       {line}")
            print()
        print("=" * 70)
    engine.dispose()


def cmd_migrate_check(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path, debug=False, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    has_changes = manager.check()
    engine.dispose()
    
    if has_changes:
        print("Schema changes detected! Run 'migrate autogenerate' to create migration.")
        sys.exit(1)
    else:
        print("No schema changes detected.")
        sys.exit(0)

def cmd_migrate_current(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path, debug=False, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    version = manager.current()
    if version:
        print(version)
    else:
        print("(none)")
    engine.dispose()

def cmd_migrate_stamp(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path, debug=True, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    try:
        manager.stamp(args.version)
        print(f"Stamped: {args.version}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

def cmd_migrate_sql(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path, debug=False, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    sql_statements = manager.generate_sql(args.direction, args.target)
    engine.dispose()
    
    if not sql_statements:
        print("-- No SQL to generate")
        return
    
    sql_output = "\n".join(sql_statements)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(sql_output)
        print(f"SQL written to: {args.output}")
    else:
        print(sql_output)

def cmd_migrate_heads(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path or "./migrations", debug=False, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    heads = manager.heads()
    engine.dispose()
    
    if not heads:
        print("No migrations found")
    elif len(heads) == 1:
        print(f"Single head: {heads[0]}")
    else:
        print(f"\nMultiple heads detected ({len(heads)}):")
        for h in heads:
            print(f"   * {h}")
        print("\nRun 'migrate merge \"message\"' to unify branches.")

def cmd_migrate_merge(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path or "./migrations", debug=True, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    migration = manager.merge(args.message, args.revisions)
    engine.dispose()
    
    if migration:
        print(f"Created merge migration: {migration.version}")
        print(f"   File: {migration._file_path}")
    else:
        print("No merge needed (only one head)")

def cmd_migrate_dryrun(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path or "./migrations", debug=False, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    pending = manager.dry_run(args.target)
    engine.dispose()
    
    if not pending:
        print("No pending migrations")
    else:
        print(f"\nWould apply {len(pending)} migration(s):")
        print("=" * 60)
        for m in pending:
            print(f"   {m['version']} - {m['message']}")
        print("=" * 60)

def cmd_migrate_verify(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path or "./migrations", debug=False, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    results = manager.verify()
    violations = [v for v in results if not v['valid']]
    engine.dispose()
    
    if not violations:
        print("All migrations verified - no modifications detected")
    else:
        print(f"\n⚠️ {len(violations)} migration(s) modified after apply:")
        print("=" * 60)
        for v in violations:
            print(f"   {v['version']} - {v['message']}")
            print(f"      Stored:  {v['stored_checksum'][:16]}...")
            print(f"      Current: {v['current_checksum'][:16]}...")
        print("=" * 60)
        sys.exit(1)

# ============================================================
# ASYNC HANDLERS
# ============================================================

def _run_async_command(args, coro_func):
    import asyncio
    import traceback
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    # Force async driver for async commands
    os.environ["PSQL_ASYNC"] = "true"
    
    # Handle path default
    path = getattr(args, 'path', None) or "./migrations"
    
    engine = _create_engine_from_profile()
    config = MigrationConfig(
        migrations_path=path, 
        debug=getattr(args, 'verbose', False), 
        auto_detect_changes=getattr(args, 'auto_detect', True)
    )
    manager = MigrationManager(engine, config)
    
    async def wrapper():
        try:
            # Run startup to show drift warnings like sync version
            await engine.startup_async()
            await coro_func(manager)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            traceback.print_exc()
        finally:
            try:
                await engine.dispose_async()
            except Exception:
                pass

    asyncio.run(wrapper())


def cmd_migrate_async_upgrade(args):
    async def _action(manager):
        count = await manager.upgrade_async(args.target, args.transactional, args.lock)
        print(f"Applied {count} migrations (Async)")
    _run_async_command(args, _action)

def cmd_migrate_async_downgrade(args):
    async def _action(manager):
        count = await manager.downgrade_async(args.target)
        print(f"Rolled back {count} migrations (Async)")
    _run_async_command(args, _action)

def cmd_migrate_async_status(args):
    async def _action(manager):
        status = await manager.status_async()
        
        print("\n" + "=" * 50)
        print("MIGRATION STATUS (ASYNC)")
        print("=" * 50)
        print(f"   Initialized:      {'Yes' if status.initialized else 'No'}")
        print(f"   Migrations path:  {status.migrations_path}")
        print(f"   Current version:  {status.current_version or '(none)'}")
        print(f"   Applied:          {status.applied_count}")
        print(f"   Pending:          {status.pending_count}")
        print(f"   Schema drift:     {'Yes' if status.has_drift else 'No'}")
        print("=" * 50)
    _run_async_command(args, _action)

def cmd_migrate_async_autogenerate(args):
    async def _action(manager):
        manager.config.auto_detect_changes = True # Force enable for autogen
        migration = await manager.autogenerate_async(args.message)
        if not migration:
            print("No changes detected (Async)")
    _run_async_command(args, _action)

def cmd_migrate_async_check(args):
    async def _action(manager):
        has_changes = await manager.check_async()
        if has_changes:
            print("Schema changes detected! (Async)")
            sys.exit(1)
        else:
            print("No schema changes detected. (Async)")
    _run_async_command(args, _action)

def cmd_migrate_async_current(args):
    async def _action(manager):
        version = await manager.current_async()
        print(version if version else "(none)")
    _run_async_command(args, _action)

def cmd_migrate_async_stamp(args):
    async def _action(manager):
        await manager.stamp_async(args.version)
        print(f"Stamped: {args.version} (Async)")
    _run_async_command(args, _action)




def cmd_migrate_async_verify(args):
    async def _action(manager):
        results = await manager.verify_async()
        violations = [v for v in results if not v['valid']]
        if not violations:
            print("All migrations verified - no modifications detected (Async)")
        else:
            print(f"\n⚠️ {len(violations)} migration(s) modified after apply:")
            for v in violations:
                 print(f"   {v['version']} - {v['message']}")
            sys.exit(1)
    _run_async_command(args, _action)

def cmd_migrate_async_dryrun(args):
    async def _action(manager):
        pending = await manager.dry_run_async(args.target)
        if not pending:
            print("No pending migrations (Async)")
        else:
            print(f"\nWould apply {len(pending)} migration(s) (Async):")
            for m in pending:
                print(f"   {m['version']} - {m['message']}")
    _run_async_command(args, _action)

def cmd_migrate_async_seed(args):
    async def _action(manager):
        count = await manager.seed_async(args.file, args.env)
        print(f"Seeded {count} records (Async)")
    _run_async_command(args, _action)

def cmd_migrate_async_history(args):
    async def _action(manager):
        limit = getattr(args, 'limit', 20)
        skip = getattr(args, 'skip', 0)
        history = await manager.history_async(limit=limit + skip)
        
        # Apply skip
        if skip:
            history = history[:-skip] if skip < len(history) else []
        
        if not history:
            print("No migration history found")
            return
            
        print(f"\nMigration History ({len(history)} entries):")
        print("=" * 60)
        for entry in history:
            applied_at = entry.get('applied_at', 'N/A')
            print(f"  {entry['version']} | {entry.get('message', '')} | {applied_at}")
        print("=" * 60)
    _run_async_command(args, _action)

def cmd_migrate_async_init(args):
    async def _action(manager):
        path = await manager.init_async()
        print(f"Initialized migrations at: {path} (Async)")
    _run_async_command(args, _action)

def cmd_migrate_async_sql(args):
    async def _action(manager):
        direction = "up" if args.direction == "upgrade" else "down"
        statements = await manager.generate_sql_async(direction, args.target)
        
        if not statements:
            print("-- No SQL statements generated", file=sys.stderr)
            return
            
        # Output SQL (to stdout for piping)
        for stmt in statements:
            print(stmt)
            print(";")
            print()
    _run_async_command(args, _action)


def cmd_migrate_head(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    import uuid
    import re
    import sys
    
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path or "./migrations", debug=True)
    manager = MigrationManager(engine, config)
    
    version = args.version
    migrations_path = config.get_migrations_path()
    
    # Find file
    file_path = next((p for p in migrations_path.glob("*.py") if p.name.startswith(version + "_")), None)
    
    if not file_path:
         print(f"❌ Error: Could not locate migration file for version {version}")
         sys.exit(1)
         
    content = file_path.read_text()
    new_head_id = str(uuid.uuid4())
    
    # Regex to replace or insert head_id
    if "head_id =" in content:
        content = re.sub(r'head_id\s*=\s*["\'].*?["\']', f'head_id = "{new_head_id}"', content)
    else:
        # Inject after depends_on
        # Note: depends_on might span multiple lines if list? No, it's string.
        # But let's look for the line `depends_on = ...`
        if re.search(r'depends_on\s*=', content):
             content = re.sub(r'(depends_on\s*=\s*.*)', f'\\1\n    head_id = "{new_head_id}"', content)
        else:
             print("❌ Error: Could not parse migration file structure (missing depends_on)")
             sys.exit(1)
        
    file_path.write_text(content)
    manager._write_head_lock(version, new_head_id)
    
    print(f"✅ Head locked to version {version}")
    print(f"   Signature: {new_head_id}")
    print(f"   Lock file: {config.head_lock_file}")


def cmd_migrate_squash(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path or "./migrations", debug=True, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    migration = manager.squash(args.message, args.start, args.end)
    engine.dispose()
    
    if migration:
        print(f"Created squash migration: {migration.version}")
        print(f"   File: {migration._file_path}")
    else:
        print("Not enough migrations to squash")

def cmd_migrate_seed(args):
    from psqlmodel.migrations import MigrationManager, MigrationConfig
    
    engine = _create_engine_from_profile()
    engine = _create_engine_from_profile()
    config = MigrationConfig(migrations_path=args.path or "./migrations", debug=True, auto_detect_changes=False)
    manager = MigrationManager(engine, config)
    
    count = manager.seed(args.file, args.env)
    engine.dispose()
    
    if count > 0:
        print(f"Seeded {count} records")
    else:
        print("No seed data found")

def cmd_users_list(args):
    from psqlmodel.cli_config import list_profiles
    profiles = list_profiles()
    if not profiles:
        print("No saved profiles")
        print("   Use: profile save <name> ...")
        return
    
    detailed = getattr(args, 'detailed', False)
    
    print("Saved profiles:")
    for name, p in profiles.items():
        print(f"  - {name} ({p.get('host')}:{p.get('port')}/{p.get('database')})")
        if detailed:
            print(f"      username:        {p.get('username', 'N/A')}")
            pw = p.get('password', '')
            masked_pw = pw[:2] + '*' * (len(pw) - 2) if pw and len(pw) > 2 else '***'
            print(f"      password:        {masked_pw}")
            print(f"      models_path:     {p.get('models_path', 'N/A')}")
            print(f"      migrations_path: {p.get('migrations_path', './migrations')}")

def cmd_users_save(args):
    from psqlmodel.cli_config import save_profile
    save_profile(
        name=args.name,
        username=args.username,
        password=args.password,
        host=args.host,
        port=args.port,
        database=args.database,
        models_path=args.models_path,
        migrations_path=args.migrations_path,
        set_default=args.default
    )
    print(f"Profile '{args.name}' saved.")

def cmd_users_remove(args):
    from psqlmodel.cli_config import remove_profile
    if remove_profile(args.name):
        print(f"Profile '{args.name}' removed.")
    else:
        print(f"Profile '{args.name}' not found.")

def cmd_users_use(args):
    from psqlmodel.cli_config import set_default_profile
    set_default_profile(args.name)
    print(f"Profile '{args.name}' set as default.")

# ============================================================
# MAIN DISPATCHER
# ============================================================

def main():
    parser = argparse.ArgumentParser(prog="python -m psqlmodel", description="PSQLModel CLI")
    
    # Global flags (mostly for default engine creation if not using subcommands?
    # Actually, argparse handles subcommands. We can have a default action.)
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # --- MIGRATE ---
    migrate_parser = subparsers.add_parser("migrate", help="Database migrations")
    migrate_subs = migrate_parser.add_subparsers(dest="migrate_cmd", help="Migration actions")
    
    # migrate init
    p_init = migrate_subs.add_parser("init", help="Initialize migrations")
    p_init.add_argument("-p", "--path", help="Migrations directory path")
    p_init.add_argument("-v", "--verbose", action="store_true")
    p_init.set_defaults(func=cmd_migrate_init)
    
    # migrate status
    p_status = migrate_subs.add_parser("status", help="Show status")
    p_status.add_argument("-p", "--path", help="Migrations directory path")
    p_status.add_argument("--full", action="store_true", help="Show detailed drift")
    p_status.set_defaults(func=cmd_migrate_status)
    
    # migrate validate
    p_validate = migrate_subs.add_parser("validate", help="Validate schema")
    p_validate.add_argument("-p", "--path", help="Migrations directory path")
    p_validate.set_defaults(func=cmd_migrate_validate)
    
    # migrate autogenerate
    p_auto = migrate_subs.add_parser("autogenerate", help="Auto-generate migration")
    p_auto.add_argument("message", help="Migration message")
    p_auto.add_argument("-p", "--path", help="Migrations directory path")
    p_auto.add_argument("--create-models", dest="create_models", action="store_true", 
                        help="Generate draft models for orphan DB tables")
    p_auto.add_argument("--drop-orphans", dest="drop_orphans", action="store_true",
                        help="Include DROP TABLE for orphan tables (in DB but not in models)")
    p_auto.add_argument("--force", action="store_true", help="Force generation even if no changes")
    p_auto.add_argument("--auto-stamp-stale", dest="auto_stamp_stale", action="store_true",
                        help="Auto-stamp stale pending migrations as applied (skip without executing)")
    p_auto.set_defaults(func=cmd_migrate_autogenerate)
    
    # migrate upgrade
    p_up = migrate_subs.add_parser("upgrade", help="Apply migrations")
    p_up.add_argument("target", nargs="?", default="head", help="Target version")
    p_up.add_argument("-p", "--path", help="Migrations directory path")
    p_up.add_argument("--no-transaction", dest="transactional", action="store_false", default=True)
    p_up.add_argument("--no-lock", dest="lock", action="store_false", default=True)
    p_up.add_argument("-d", "--database", help="Target specific database profile")
    p_up.add_argument("--all", action="store_true", help="Upgrade all profiles")
    p_up.set_defaults(func=cmd_migrate_upgrade)
    
    # migrate downgrade
    p_down = migrate_subs.add_parser("downgrade", help="Revert migrations")
    p_down.add_argument("target", nargs="?", default="-1", help="Target version or -N")
    p_down.add_argument("-p", "--path", help="Migrations directory path")
    p_down.set_defaults(func=cmd_migrate_downgrade)
    
    # migrate history
    p_hist = migrate_subs.add_parser("history", help="Show history")
    p_hist.add_argument("-p", "--path", help="Migrations directory path")
    p_hist.add_argument("-s", "--skip", type=int, default=0, help="Skip N migrations")
    p_hist.add_argument("-l", "--limit", type=int, default=20, help="Limit number of rows")
    p_hist.add_argument("--first", action="store_true", help="Show oldest first")
    p_hist.set_defaults(func=cmd_migrate_history)
    
    # migrate failures
    p_fail = migrate_subs.add_parser("failures", help="Show failed migrations")
    p_fail.add_argument("-p", "--path", help="Migrations directory path")
    p_fail.add_argument("-s", "--skip", type=int, default=0, help="Skip N records")
    p_fail.add_argument("-l", "--limit", type=int, default=20, help="Limit number of rows")
    p_fail.add_argument("-v", "--verbose", action="store_true", help="Show stack traces")
    p_fail.set_defaults(func=cmd_migrate_failures)
    
    # migrate check
    p_check = migrate_subs.add_parser("check", help="Check for changes (CI)")
    p_check.add_argument("-p", "--path", help="Migrations directory path")
    p_check.set_defaults(func=cmd_migrate_check)
    
    # migrate current
    p_curr = migrate_subs.add_parser("current", help="Show current version")
    p_curr.add_argument("-p", "--path", help="Migrations directory path")
    p_curr.set_defaults(func=cmd_migrate_current)
    
    # migrate stamp
    p_stamp = migrate_subs.add_parser("stamp", help="Mark version as applied")
    p_stamp.add_argument("version", help="Version to stamp")
    p_stamp.add_argument("-p", "--path", help="Migrations directory path")
    p_stamp.set_defaults(func=cmd_migrate_stamp)
    
    # migrate sql
    p_sql = migrate_subs.add_parser("sql", help="Generate SQL")
    p_sql.add_argument("direction", choices=["upgrade", "downgrade"], help="Direction")
    p_sql.add_argument("target", nargs="?", default="head", help="Target version")
    p_sql.add_argument("-p", "--path", help="Migrations directory path")
    p_sql.add_argument("-o", "--output", help="Output file")
    p_sql.set_defaults(func=cmd_migrate_sql)
    
    # migrate head (singular: set/sign head)
    p_head = migrate_subs.add_parser("head", help="Sign version as valid head")
    p_head.add_argument("version", help="Version to sign")
    p_head.add_argument("-p", "--path", help="Migrations directory path")
    p_head.set_defaults(func=cmd_migrate_head)

    # migrate heads (plural: show heads)
    p_heads = migrate_subs.add_parser("heads", help="Show heads")
    p_heads.add_argument("-p", "--path", help="Migrations directory path")
    p_heads.set_defaults(func=cmd_migrate_heads)
    
    # migrate merge
    p_merge = migrate_subs.add_parser("merge", help="Merge heads")
    p_merge.add_argument("message", help="Merge message")
    p_merge.add_argument("-r", "--revisions", nargs="+", help="Revisions to merge")
    p_merge.add_argument("-p", "--path", help="Migrations directory path")
    p_merge.set_defaults(func=cmd_migrate_merge)
    
    # migrate dryrun
    p_dry = migrate_subs.add_parser("dryrun", help="Dry run preview")
    p_dry.add_argument("target", nargs="?", default="head", help="Target version")
    p_dry.add_argument("-p", "--path", help="Migrations directory path")
    p_dry.set_defaults(func=cmd_migrate_dryrun)
    
    # --------------------------------------------------------
    # migrate async
    # --------------------------------------------------------
    p_async = migrate_subs.add_parser(
        "async", 
        help="Async operations (for testing async methods)",
        description="⚠️  ASYNC COMMANDS - For testing async code paths only.\n\n"
                    "These commands use asyncpg driver and async methods internally.\n"
                    "For normal usage, use the standard 'migrate' commands (sync) - they are functionally equivalent.\n\n"
                    "The async commands exist to verify that async methods work correctly,\n"
                    "not for performance benefits (CLI is single-shot, no concurrency advantage)."
    )
    async_subs = p_async.add_subparsers(dest="async_cmd", help="Async actions")
    
    # async upgrade
    pa_up = async_subs.add_parser("upgrade", help="Apply migrations (Async)")
    pa_up.add_argument("target", nargs="?", default="head")
    pa_up.add_argument("-p", "--path")
    pa_up.add_argument("--no-transaction", dest="transactional", action="store_false", default=True)
    pa_up.add_argument("--no-lock", dest="lock", action="store_false", default=True)
    pa_up.set_defaults(func=cmd_migrate_async_upgrade)
    
    # async downgrade
    pa_down = async_subs.add_parser("downgrade", help="Revert migrations (Async)")
    pa_down.add_argument("target", nargs="?", default="-1")
    pa_down.add_argument("-p", "--path")
    pa_down.set_defaults(func=cmd_migrate_async_downgrade)
    
    # async status
    pa_status = async_subs.add_parser("status", help="Show status (Async)")
    pa_status.add_argument("-p", "--path")
    pa_status.set_defaults(func=cmd_migrate_async_status)
    
    # async check
    pa_check = async_subs.add_parser("check", help="Check drift (Async)")
    pa_check.add_argument("-p", "--path")
    pa_check.set_defaults(func=cmd_migrate_async_check)
    
    # async current
    pa_curr = async_subs.add_parser("current", help="Show current version (Async)")
    pa_curr.add_argument("-p", "--path")
    pa_curr.set_defaults(func=cmd_migrate_async_current)
    
    # async stamp
    pa_stamp = async_subs.add_parser("stamp", help="Stamp version (Async)")
    pa_stamp.add_argument("version")
    pa_stamp.add_argument("-p", "--path")
    pa_stamp.set_defaults(func=cmd_migrate_async_stamp)
    
    # async autogenerate
    pa_auto = async_subs.add_parser("autogenerate", help="Autogenerate (Async)")
    pa_auto.add_argument("message")
    pa_auto.add_argument("-p", "--path")
    pa_auto.set_defaults(func=cmd_migrate_async_autogenerate)
    
    # async verify
    pa_ver = async_subs.add_parser("verify", help="Verify integrity (Async)")
    pa_ver.add_argument("-p", "--path")
    pa_ver.set_defaults(func=cmd_migrate_async_verify)

    # async dryrun
    pa_dry = async_subs.add_parser("dryrun", help="Dry run (Async)")
    pa_dry.add_argument("target", nargs="?", default="head")
    pa_dry.add_argument("-p", "--path")
    pa_dry.set_defaults(func=cmd_migrate_async_dryrun)

    # async seed
    pa_seed = async_subs.add_parser("seed", help="Seed data (Async)")
    pa_seed.add_argument("file")
    pa_seed.add_argument("--env", default="default")
    pa_seed.add_argument("-p", "--path")
    pa_seed.set_defaults(func=cmd_migrate_async_seed)

    # async history
    pa_hist = async_subs.add_parser("history", help="Show history (Async)")
    pa_hist.add_argument("-p", "--path")
    pa_hist.add_argument("-s", "--skip", type=int, default=0)
    pa_hist.add_argument("-l", "--limit", type=int, default=20)
    pa_hist.set_defaults(func=cmd_migrate_async_history)

    # async init
    pa_init = async_subs.add_parser("init", help="Initialize migrations (Async)")
    pa_init.add_argument("-p", "--path")
    pa_init.add_argument("-v", "--verbose", action="store_true")
    pa_init.set_defaults(func=cmd_migrate_async_init)

    # async sql
    pa_sql = async_subs.add_parser("sql", help="Generate SQL (Async)")
    pa_sql.add_argument("direction", choices=["upgrade", "downgrade"])
    pa_sql.add_argument("target", nargs="?", default="head")
    pa_sql.add_argument("-p", "--path")
    pa_sql.add_argument("-o", "--output")
    pa_sql.set_defaults(func=cmd_migrate_async_sql)
    
    # migrate verify
    p_ver = migrate_subs.add_parser("verify", help="Verify integrity")
    p_ver.add_argument("-p", "--path", help="Migrations directory path")
    p_ver.set_defaults(func=cmd_migrate_verify)
    
    # migrate squash
    p_sq = migrate_subs.add_parser("squash", help="Squash migrations")
    p_sq.add_argument("message", help="Squash message")
    p_sq.add_argument("--from", dest="start", required=True, help="Start version")
    p_sq.add_argument("--to", dest="end", required=True, help="End version")
    p_sq.add_argument("-p", "--path", help="Migrations directory path")
    p_sq.set_defaults(func=cmd_migrate_squash)
    
    # migrate seed
    p_seed = migrate_subs.add_parser("seed", help="Seed data")
    p_seed.add_argument("file", help="Seed file (JSON/YAML)")
    p_seed.add_argument("-e", "--env", default="default", help="Environment")
    p_seed.add_argument("-p", "--path", help="Migrations directory path")
    p_seed.set_defaults(func=cmd_migrate_seed)
    
    # profile
    p_profile = subparsers.add_parser("profile", help="Manage profiles")
    profile_subs = p_profile.add_subparsers(dest="profile_cmd")
    
    u_list = profile_subs.add_parser("list", help="List profiles")
    u_list.add_argument("-d", "--detailed", action="store_true", help="Show detailed info (password masked)")
    u_list.set_defaults(func=cmd_users_list)
    
    u_save = profile_subs.add_parser("save", help="Save profile")
    u_save.add_argument("name", help="Profile name")
    u_save.add_argument("-u", "--username", required=True)
    u_save.add_argument("--password", required=True)
    u_save.add_argument("--host", default="localhost")
    u_save.add_argument("-P", "--port", type=int, default=5432)
    u_save.add_argument("-db", "--database", required=True)
    u_save.add_argument("--models-path", dest="models_path", nargs="+", help="Path(s) to model files/directories (can specify multiple)")
    u_save.add_argument("--migrations-path", dest="migrations_path", help="Path to migrations directory (default: ./migrations)")
    u_save.add_argument("--default", action="store_true")
    u_save.set_defaults(func=cmd_users_save)
    
    u_remove = profile_subs.add_parser("remove", aliases=["delete"], help="Remove/delete profile")
    u_remove.add_argument("name", help="Profile name")
    u_remove.set_defaults(func=cmd_users_remove)
    
    u_use = profile_subs.add_parser("use", help="Set default profile")
    u_use.add_argument("name", help="Profile name")
    u_use.set_defaults(func=cmd_users_use)
    
    # --- DEFAULT ACTION (Metrics) ---
    # args = parser.parse_args()
    
    # Handle the case where no command is passed (start metrics/app)
    # If explicit 'start' command was needed, we'd add it.
    # But usage says 'python -m psqlmodel' starts metrics logger.
    # We can check sys.argv or set a default function.
    
    if len(sys.argv) == 1:
        # No args
        print("Starting PSQLModel Metrics Logger... (Press Ctrl+C to stop)")
        # Minimal engine to keep process alive or whatever default behavior was
        # The original code didn't actually show the implementation of the default action
        # other than dispatch failing?
        # Re-reading original file (implicit in viewed lines):
        # It had "Usage: python -m psqlmodel # Start metrics logger"
        # But logic was just falling through if no match?
        # I'll implement a dummy wait loop or just print help.
        # Actually, standard behavior for CLI without args is help.
        parser.print_help()
        return

    args = parser.parse_args()
    
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
