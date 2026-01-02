"""
PSQLModel Migration System - State Manager

Manages migration state in both local files and database tables.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime
import hashlib

import hashlib
import asyncio

import psycopg
import asyncpg

from .config import MigrationConfig

if TYPE_CHECKING:
    from ..core.engine import Engine


class StateManager:
    """Manages migration state across local file and database.
    
    State is stored in:
    - Local file (.schema_state.json) for quick access
    - Database table (_psqlmodel_schema_state) for distributed systems
    - History table (_psqlmodel_migrations) for audit log
    """
    
    def __init__(self, engine: "Engine", config: MigrationConfig):
        self.engine = engine
        self.config = config
        self._lock_id = self._compute_lock_id()
    
    def _compute_lock_id(self) -> int:
        """Compute advisory lock ID from database name."""
        db_name = self.engine.config.database or "psqlmodel"
        return int(hashlib.md5(f"psqlmodel_migrations_{db_name}".encode()).hexdigest()[:15], 16)
    
    async def _get_connection_async(self):
        """Get an async database connection."""
        dsn = self.engine._build_async_dsn()
        return await asyncpg.connect(dsn)

    def _get_connection(self):
        """Get a database connection."""
        dsn = self.engine._build_sync_dsn()
        return psycopg.connect(dsn)
    
    async def ensure_tables_async(self) -> None:
        """Create state and history tables if they don't exist (Async)."""
        conn = await self._get_connection_async()
        try:
            # Ensure migrations schema exists
            await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.config.migrations_schema}")

            # Schema state table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.config.state_table_name} (
                    object_type VARCHAR(50) NOT NULL,
                    object_name VARCHAR(255) NOT NULL,
                    schema_hash VARCHAR(64) NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    PRIMARY KEY (object_type, object_name)
                );
            """)
            
            # Migration history table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.config.history_table_name} (
                    version VARCHAR(50) PRIMARY KEY,
                    message TEXT,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    checksum VARCHAR(64),
                    execution_time_ms INTEGER,
                    rolled_back_at TIMESTAMP WITH TIME ZONE
                );
            """)
            
            # Migration failures table (for tracking failed migrations)
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.config.history_table_name}_failures (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) NOT NULL,
                    message TEXT,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    failed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
        finally:
            await conn.close()

    def ensure_tables(self) -> None:
        """Create state and history tables if they don't exist."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            # Ensure migrations schema exists
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {self.config.migrations_schema}")
            
            # Schema state table
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.config.state_table_name} (
                    object_type VARCHAR(50) NOT NULL,
                    object_name VARCHAR(255) NOT NULL,
                    schema_hash VARCHAR(64) NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    PRIMARY KEY (object_type, object_name)
                );
            """)
            
            # Migration history table
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.config.history_table_name} (
                    version VARCHAR(50) PRIMARY KEY,
                    message TEXT,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    checksum VARCHAR(64),
                    execution_time_ms INTEGER,
                    rolled_back_at TIMESTAMP WITH TIME ZONE
                );
            """)
            
            # Migration failures table (for tracking failed migrations)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.config.history_table_name}_failures (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) NOT NULL,
                    message TEXT,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    failed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            conn.commit()
            cur.close()
        finally:
            conn.close()
    
    async def get_current_state_async(self) -> Dict[str, str]:
        """Get current schema hashes from database (Async)."""
        state = {}
        try:
            conn = await self._get_connection_async()
            try:
                rows = await conn.fetch(f"""
                    SELECT object_type, object_name, schema_hash 
                    FROM {self.config.state_table_name}
                """)
                for row in rows:
                    key = f"{row['object_type']}:{row['object_name']}"
                    state[key] = row['schema_hash']
            finally:
                await conn.close()
        except Exception:
            pass
        return state

    def get_current_state(self) -> Dict[str, str]:
        """Get current schema hashes from database."""
        state = {}
        try:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute(f"""
                    SELECT object_type, object_name, schema_hash 
                    FROM {self.config.state_table_name}
                """)
                for row in cur.fetchall():
                    key = f"{row[0]}:{row[1]}"
                    state[key] = row[2]
                cur.close()
            finally:
                conn.close()
        except Exception:
            pass
        return state
    
    def save_state(self, state: Dict[str, str]) -> None:
        """Save schema state to both database and local file."""
        # Save to database
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            for key, hash_value in state.items():
                object_type, object_name = key.split(":", 1)
                cur.execute(f"""
                    INSERT INTO {self.config.state_table_name} 
                    (object_type, object_name, schema_hash, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (object_type, object_name) 
                    DO UPDATE SET schema_hash = EXCLUDED.schema_hash, updated_at = NOW()
                """, (object_type, object_name, hash_value))
            conn.commit()
            cur.close()
        finally:
            conn.close()
        
        # Save to local file
        self._save_local_state(state)

    async def save_state_async(self, state: Dict[str, str]) -> None:
        """Save schema state to both database and local file (Async)."""
        conn = await self._get_connection_async()
        try:
            for key, hash_value in state.items():
                object_type, object_name = key.split(":", 1)
                await conn.execute(f"""
                    INSERT INTO {self.config.state_table_name} 
                    (object_type, object_name, schema_hash, updated_at)
                    VALUES ($1, $2, $3, NOW())
                    ON CONFLICT (object_type, object_name) 
                    DO UPDATE SET schema_hash = EXCLUDED.schema_hash, updated_at = NOW()
                """, object_type, object_name, hash_value)
        finally:
            await conn.close()
        
        # Save to local file (sync operation, acceptable)
        self._save_local_state(state)
    
    def _save_local_state(self, state: Dict[str, str]) -> None:
        """Save state to local JSON file."""
        migrations_path = self.config.get_migrations_path()
        state_file = migrations_path / self.config.state_file_name
        
        try:
            state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, 'w') as f:
                json.dump({
                    "version": "1.0",
                    "updated_at": datetime.utcnow().isoformat(),
                    "state": state,
                }, f, indent=2)
        except Exception:
            pass
    
    def _load_local_state(self) -> Dict[str, str]:
        """Load state from local JSON file."""
        migrations_path = self.config.get_migrations_path()
        state_file = migrations_path / self.config.state_file_name
        
        try:
            if state_file.exists():
                with open(state_file, 'r') as f:
                    data = json.load(f)
                    return data.get("state", {})
        except Exception:
            pass
        return {}
    
    async def get_applied_migrations_async(self) -> List[Dict[str, Any]]:
        """Get list of applied migrations from database (Async)."""
        migrations = []
        try:
            conn = await self._get_connection_async()
            try:
                rows = await conn.fetch(f"""
                    SELECT version, message, applied_at, checksum, 
                           execution_time_ms, rolled_back_at
                    FROM {self.config.history_table_name}
                    WHERE rolled_back_at IS NULL
                    ORDER BY version ASC
                """)
                for row in rows:
                    migrations.append({
                        "version": row['version'],
                        "message": row['message'],
                        "applied_at": row['applied_at'].isoformat() if row['applied_at'] else None,
                        "checksum": row['checksum'],
                        "execution_time_ms": row['execution_time_ms'],
                    })
            finally:
                await conn.close()
        except Exception:
            pass
        return migrations

    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """Get list of applied migrations from database."""
        migrations = []
        try:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute(f"""
                    SELECT version, message, applied_at, checksum, 
                           execution_time_ms, rolled_back_at
                    FROM {self.config.history_table_name}
                    WHERE rolled_back_at IS NULL
                    ORDER BY version ASC
                """)
                for row in cur.fetchall():
                    migrations.append({
                        "version": row[0],
                        "message": row[1],
                        "applied_at": row[2].isoformat() if row[2] else None,
                        "checksum": row[3],
                        "execution_time_ms": row[4],
                    })
                cur.close()
            finally:
                conn.close()
        except Exception:
            pass
        return migrations
    
    async def mark_applied_async(self, version: str, message: str, checksum: str, 
                                 execution_time_ms: int) -> None:
        """Record a migration as applied (Async)."""
        conn = await self._get_connection_async()
        try:
            await conn.execute(f"""
                INSERT INTO {self.config.history_table_name}
                (version, message, applied_at, checksum, execution_time_ms)
                VALUES ($1, $2, NOW(), $3, $4)
                ON CONFLICT (version) DO UPDATE SET
                    message = EXCLUDED.message,
                    applied_at = NOW(),
                    checksum = EXCLUDED.checksum,
                    execution_time_ms = EXCLUDED.execution_time_ms,
                    rolled_back_at = NULL
            """, version, message, checksum, execution_time_ms)
        finally:
            await conn.close()

    def mark_applied(self, version: str, message: str, checksum: str, 
                     execution_time_ms: int) -> None:
        """Record a migration as applied."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"""
                INSERT INTO {self.config.history_table_name}
                (version, message, applied_at, checksum, execution_time_ms)
                VALUES (%s, %s, NOW(), %s, %s)
                ON CONFLICT (version) DO UPDATE SET
                    message = EXCLUDED.message,
                    applied_at = NOW(),
                    checksum = EXCLUDED.checksum,
                    execution_time_ms = EXCLUDED.execution_time_ms,
                    rolled_back_at = NULL
            """, (version, message, checksum, execution_time_ms))
            conn.commit()
            cur.close()
        finally:
            conn.close()
    
    async def mark_rolled_back_async(self, version: str) -> None:
        """Mark a migration as rolled back (Async)."""
        conn = await self._get_connection_async()
        try:
            await conn.execute(f"""
                UPDATE {self.config.history_table_name}
                SET rolled_back_at = NOW()
                WHERE version = $1
            """, version)
        finally:
            await conn.close()

    def mark_rolled_back(self, version: str) -> None:
        """Mark a migration as rolled back."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"""
                UPDATE {self.config.history_table_name}
                SET rolled_back_at = NOW()
                WHERE version = %s
            """, (version,))
            conn.commit()
            cur.close()
        finally:
            conn.close()
    
    async def get_current_version_async(self) -> Optional[str]:
        """Get the latest applied migration version (Async)."""
        try:
            conn = await self._get_connection_async()
            try:
                val = await conn.fetchval(f"""
                    SELECT version 
                    FROM {self.config.history_table_name}
                    WHERE rolled_back_at IS NULL
                    ORDER BY version DESC
                    LIMIT 1
                """)
                return val
            finally:
                await conn.close()
        except Exception:
            return None

    def get_current_version(self) -> Optional[str]:
        """Get the latest applied migration version."""
        try:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute(f"""
                    SELECT version 
                    FROM {self.config.history_table_name}
                    WHERE rolled_back_at IS NULL
                    ORDER BY version DESC
                    LIMIT 1
                """)
                row = cur.fetchone()
                cur.close()
                return row[0] if row else None
            finally:
                conn.close()
        except Exception:
            return None
    
    async def acquire_lock_async(self, timeout: int = 30) -> bool:
        """Acquire PostgreSQL advisory lock (Async)."""
        try:
            conn = await self._get_connection_async()
            try:
                # pg_try_advisory_lock retrieves a boolean
                result = await conn.fetchval(f"SELECT pg_try_advisory_lock({self._lock_id})")
                return bool(result)
            finally:
                await conn.close()
        except Exception:
            return False

    async def release_lock_async(self) -> None:
        """Release the advisory lock (Async)."""
        try:
            conn = await self._get_connection_async()
            try:
                await conn.execute(f"SELECT pg_advisory_unlock({self._lock_id})")
            finally:
                await conn.close()
        except Exception:
            pass

    def acquire_lock(self, timeout: int = 30) -> bool:
        """Acquire PostgreSQL advisory lock for migration safety.
        
        Returns True if lock was acquired, False otherwise.
        """
        try:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute(f"SELECT pg_try_advisory_lock({self._lock_id})")
                result = cur.fetchone()
                cur.close()
                return bool(result and result[0])
            finally:
                conn.close()
        except Exception:
            return False
    
    def release_lock(self) -> None:
        """Release the advisory lock."""
        try:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute(f"SELECT pg_advisory_unlock({self._lock_id})")
                cur.close()
            finally:
                conn.close()
        except Exception:
            pass
    
    # ============================================================
    # FAILURE TRACKING METHODS
    # ============================================================
    
    def mark_failed(self, version: str, message: str, error: str, stack_trace: str = None) -> None:
        """Record a failed migration attempt.
        
        Args:
            version: Migration version that failed
            message: Migration message/description
            error: Error message
            stack_trace: Optional full stack trace
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"""
                INSERT INTO {self.config.history_table_name}_failures 
                (version, message, error_message, stack_trace)
                VALUES (%s, %s, %s, %s)
            """, (version, message, error, stack_trace))
            conn.commit()
            cur.close()
        finally:
            conn.close()
    
    async def mark_failed_async(self, version: str, message: str, error: str, stack_trace: str = None) -> None:
        """Record a failed migration attempt (Async).
        
        Args:
            version: Migration version that failed
            message: Migration message/description
            error: Error message
            stack_trace: Optional full stack trace
        """
        conn = await self._get_connection_async()
        try:
            await conn.execute(f"""
                INSERT INTO {self.config.history_table_name}_failures 
                (version, message, error_message, stack_trace)
                VALUES ($1, $2, $3, $4)
            """, version, message, error, stack_trace)
        finally:
            await conn.close()
    
    def get_failures(self, limit: int = 20, skip: int = 0) -> List[Dict[str, Any]]:
        """Get list of migration failures.
        
        Args:
            limit: Maximum number of failures to return
            skip: Number of failures to skip (for pagination)
            
        Returns:
            List of failure records
        """
        failures = []
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            try:
                cur.execute(f"""
                    SELECT id, version, message, error_message, stack_trace, failed_at
                    FROM {self.config.history_table_name}_failures
                    ORDER BY failed_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, skip))
                rows = cur.fetchall()
                columns = ['id', 'version', 'message', 'error_message', 'stack_trace', 'failed_at']
                for row in rows:
                    failures.append(dict(zip(columns, row)))
                cur.close()
            except self.psycopg.errors.UndefinedTable:
                pass
        finally:
            conn.close()
        return failures
    
    async def get_failures_async(self, limit: int = 20, skip: int = 0) -> List[Dict[str, Any]]:
        """Get list of migration failures (Async).
        
        Args:
            limit: Maximum number of failures to return
            skip: Number of failures to skip (for pagination)
            
        Returns:
            List of failure records
        """
        failures = []
        conn = await self._get_connection_async()
        try:
            try:
                rows = await conn.fetch(f"""
                    SELECT id, version, message, error_message, stack_trace, failed_at
                    FROM {self.config.history_table_name}_failures
                    ORDER BY failed_at DESC
                    LIMIT $1 OFFSET $2
                """, limit, skip)
                for row in rows:
                    failures.append(dict(row))
            except asyncpg.UndefinedTableError:
                pass
        finally:
            await conn.close()
        return failures
