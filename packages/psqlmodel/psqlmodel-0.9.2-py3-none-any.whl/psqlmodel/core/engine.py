from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, ContextManager, AsyncContextManager, Callable, List, Union
import threading
import queue
import os
import importlib.util
import asyncio
import concurrent.futures
from collections import deque, defaultdict
import datetime
import contextvars

import psycopg
import asyncpg

from ..orm.model import PSQLModel
from ..orm.column import Column  # puede ser útil para typings internos


# ============================================================
# Custom Exceptions
# ============================================================

class PSQLModelError(Exception):
    """
    Base exception for all PSQLModel errors.
    
    All custom exceptions raised by the ORM inherit from this class,
    allowing users to catch all ORM-related errors with a single except block.
    
    Usage:
        try:
            db.connect()
        except PSQLModelError as e:
            print(f"ORM Error: {e}")
    """
    pass


class DatabaseNotFoundError(PSQLModelError):
    """
    Raised when attempting to connect to a non-existent database.
    
    This exception includes a helpful message suggesting how to create the database
    automatically using `ensure_database=True`.
    """

    def __init__(self, database_name: str, original_error: Exception):
        self.database_name = database_name
        self.original_error = original_error

        message = (
            f"\n\n{'=' * 70}\n"
            f"❌ DATABASE NOT FOUND: '{database_name}'\n"
            f"{'=' * 70}\n\n"
            f"The database '{database_name}' does not exist on the server.\n\n"
            f"💡 SOLUTION:\n"
            f"   Enable automatic database creation by setting:\n\n"
            f"   PSQLModel.init(\n"
            f"       'your_connection_string',\n"
            f"       ensure_database=True  # ← Set this to True\n"
            f"   )\n\n"
            f"   Or create the database manually:\n"
            f"   CREATE DATABASE {database_name};\n\n"
            f"{'=' * 70}\n"
        )
        super().__init__(message)


class ConnectionError(PSQLModelError):
    """
    Raised when connection to database fails.
    
    This can happen due to network issues, invalid credentials, or server downtime.
    """
    pass


# ============================================================
# Identifier validation helpers (prevents SQL injection in DDL)
# ============================================================

_IDENT_RE = None

def _is_valid_identifier(name: str) -> bool:
    """
    Validate an SQL identifier to prevent SQL injection in DDL operations.
    
    Ensures the name contains only alphanumeric characters and underscores,
    and starts with a letter or underscore.
    
    Args:
        name (str): The identifier name to validate (e.g., table name, column name).
        
    Returns:
        bool: True if valid, False otherwise.
    """
    global _IDENT_RE
    if _IDENT_RE is None:
        import re
        _IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    if not isinstance(name, str) or not name:
        return False
    return bool(_IDENT_RE.match(name))


def _validate_qualified_name(name: str, *, kind: str = "identifier") -> None:
    """Validate 'schema.table' or 'table' form."""
    if not isinstance(name, str) or not name:
        raise ValueError(f"Invalid {kind}: empty")
    parts = name.split(".")
    if len(parts) > 2:
        raise ValueError(f"Invalid {kind}: '{name}' (too many parts)")
    for p in parts:
        if not _is_valid_identifier(p):
            raise ValueError(f"Invalid {kind}: '{name}' (bad token: '{p}')")


@dataclass
class EngineConfig:
    """
    Configuration options for the Database Engine.
    
    This dataclass holds all settings related to database connection, pooling,
    lifecycle management, and observability.
    
    Attributes:
        dsn (Optional[str]): Full connection string (e.g. 'postgresql://user:pass@host:5432/db').
                             If provided, it overrides individual connection fields.
        username (Optional[str]): Database username.
        password (Optional[str]): Database password.
        host (str): Database host address (default: "localhost").
        port (int): Database port (default: 5432).
        database (Optional[str]): Target database name.
        async_ (bool): If True, uses asyncpg for asynchronous I/O. 
                       If False, uses psycopg for synchronous I/O.
        pool_size (int): Size of the connection pool (default: 20).
        auto_adjust_pool_size (bool): Not yet implemented.
        max_pool_size (Optional[int]): Hard limit for pool expansion.
        connection_timeout (Optional[float]): Timeout for establishing new connections.
        ensure_database (bool): If True, attempts to create the database if it doesn't exist.
        ensure_tables (bool): If True, creates tables for registered models on startup.
        ensure_migrations (bool): If True, runs pending migrations on startup (default: False).
        check_schema_drift (bool): If True, warns if model definitions differ from DB schema.
        migrations_path (Optional[str]): Custom path for migration files.
        models_path (Optional[Union[str, List[str]]]): Path(s) to load models from. Can be a single path or list of paths.
        debug (bool): If True, prints detailed SQL execution logs to stdout.
        logger (Optional[Callable]): Custom logger function (e.g., logging.info).
        health_check_enabled (bool): Enable periodic pool health checks.
        health_check_interval (float): Seconds between health checks.
        enable_metrics (bool): Enable collection of performance metrics.
        enable_query_tracer (bool): Enable tracing of recent queries for debugging.
        enable_structured_logging (bool): Enable JSON-structured logs.
    """
    dsn: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    host: str = "localhost"
    port: int = 5432
    database: Optional[str] = None
    async_: bool = False
    pool_size: int = 20
    auto_adjust_pool_size: bool = False
    max_pool_size: Optional[int] = None
    connection_timeout: Optional[float] = None
    ensure_database: bool = True
    ensure_tables: bool = True
    auto_startup: bool = True  # If False, Session/AsyncSession won't auto-call startup
    ensure_migrations: bool = False  # Auto-run migrations on startup
    check_schema_drift: bool = True  # Warn if models differ from DB
    migrations_path: Optional[str] = None  # Path for migrations directory
    models_path: Optional[Union[str, List[str]]] = None  # Optional path(s) to model files/directories
    debug: bool = False  # si True, imprime todas las sentencias SQL ejecutadas
    logger: Optional[Callable[[str], None]] = None  # logger opcional para debug
    # Health-check / pool repair
    health_check_enabled: bool = False
    health_check_interval: float = 30.0
    health_check_retries: int = 1
    health_check_timeout: float = 5.0
    # Connection lifecycle
    pool_pre_ping: bool = False
    pool_recycle: Optional[float] = None  # seconds
    max_retries: int = 0
    retry_delay: float = 0.0
    # --- NUEVO: métricas / tracer / logging estructurado ---
    enable_metrics: bool = True
    enable_query_tracer: bool = True
    query_trace_size: int = 200
    enable_structured_logging: bool = True
    # Model discovery options
    ignore_duplicates: bool = False  # If True, use first table reference and ignore subsequent duplicates
    # Pool shutdown options
    pool_close_timeout: float = 5.0  # Seconds to wait for pool.close() before forcing terminate()

    def __post_init__(self):
        """Parse DSN if provided and populate connection fields."""
        if self.dsn:
            from urllib.parse import urlparse, unquote

            try:
                parsed = urlparse(self.dsn)

                if parsed.username and not self.username:
                    self.username = unquote(parsed.username)

                if parsed.password and not self.password:
                    self.password = unquote(parsed.password)

                if parsed.hostname and self.host == "localhost":
                    self.host = parsed.hostname

                if parsed.port and self.port == 5432:
                    self.port = parsed.port

                if parsed.path and len(parsed.path) > 1 and not self.database:
                    self.database = parsed.path.lstrip("/")

            except Exception:
                pass


class Engine:
    """
    Core database engine for psqlmodel.

    The Engine serves as the central point for all database interactions. It manages:
    1. Connection Pooling: Efficiently reuses connections for both sync (psycopg) and async (asyncpg).
    2. Query Execution: Provides methods to execute SQL statements (exec, fetch, etc.).
    3. Transaction Management: Handles transaction lifecycle and context propagation.
    4. DDL Generation: Automatically creates tables and schemas based on models (`ensure_tables`).
    5. Schema Drift Detection: Warns if the database schema deviates from model definitions.
    6. Observability: Integrated metrics, query tracing, and structured logging.

    The Engine is designed to be thread-safe in synchronous contexts and task-safe in asynchronous contexts.
    """

    def __init__(self, config: EngineConfig):
        """
        Initialize the Engine with the given configuration.
        
        This sets up internal state for connection pools, metrics, and transaction contexts
        but DOES NOT establish connections immediately. Connections are created lazily
        or during explicit startup calls (`startup_sync` or `startup_async`).
        
        Args:
           config (EngineConfig): Complete configuration for the engine.
        """
        self.config = config
        # Pooles separados para sync / async.
        self._pool: Optional[queue.Queue] = None  # sync (psycopg)
        self._async_pool: Optional[asyncpg.pool.Pool] = None  # async (asyncpg)
        self._pool_lock = threading.Lock()
        self._pool_size = 0
        # Hooks for execution pipeline
        self._hooks: dict[str, list] = {
            "before_execute": [],
            "after_execute": [],
        }
        # Middlewares: list of (priority, func, timeout)
        self._middlewares_sync: list[tuple[int, Any, Optional[float]]] = []
        self._middlewares_async: list[tuple[int, Any, Optional[float]]] = []
        # Health monitor handles
        self._health_thread: Optional[threading.Thread] = None
        self._health_thread_stop: threading.Event = threading.Event()
        self._health_task: Optional[asyncio.Task] = None
        # Track async pool sizing for auto-adjust logic
        self._async_pool_max_size: Optional[int] = None
        # Lifecycle tracking
        self._conn_last_used_sync: dict[Any, float] = {}
        self._async_pool_last_recreate: float = 0.0

        # ====================================================
        # NUEVO: estado interno para métricas + tracer
        # ====================================================
        self._metrics_lock = threading.Lock()
        self._metrics_enabled = bool(self.config.enable_metrics)
        self._query_tracer_enabled = bool(self.config.enable_query_tracer)
        self._structured_logging_enabled = bool(self.config.enable_structured_logging)

        self._metrics = {
            "total_queries": 0,
            "total_errors": 0,
            "by_statement": defaultdict(
                lambda: {
                    "count": 0,
                    "errors": 0,
                    "total_duration_ms": 0.0,
                    "total_rows": 0,
                }
            ),
            "by_table": defaultdict(
                lambda: {
                    "count": 0,
                    "errors": 0,
                    "total_duration_ms": 0.0,
                    "total_rows": 0,
                }
            ),
        }

        # Query tracer circular
        self._query_trace_size = int(self.config.query_trace_size or 0)
        if self._query_tracer_enabled and self._query_trace_size > 0:
            self._query_trace: Optional[deque] = deque(maxlen=self._query_trace_size)
        else:
            self._query_trace = None

        # Flag para no registrar dos veces el middleware interno
        self._logging_middlewares_installed: bool = False
        if (
            self._structured_logging_enabled
            or self._metrics_enabled
            or self._query_tracer_enabled
        ):
            self._install_internal_logging_middlewares()

        # ====================================================
        # NUEVO: Transaction context (sync + async)
        # ====================================================
        self._tx_conn_sync: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar(
            "psqlmodel_tx_conn_sync", default=None
        )
        self._tx_conn_async: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar(
            "psqlmodel_tx_conn_async", default=None
        )

        # ====================================================
        # Startup (sync + async) guards
        # ====================================================
        self._startup_lock_sync = threading.Lock()
        self._startup_done_sync: bool = False

        self._startup_lock_async: Optional[asyncio.Lock] = None
        self._startup_done_async: bool = False
        # In async mode, we do lazy startup inside the running event loop
        self._pending_async_setup: bool = bool(self.config.async_) and (
            bool(self.config.ensure_database)
            or bool(self.config.ensure_tables)
            or bool(self.config.health_check_enabled)
        )

    # ============================================================
    # Debug helper
    # ============================================================
    def _debug(self, msg: str, *args: Any) -> None:
        """Internal debug printing respecting config.debug and optional logger."""
        if not self.config.debug:
            return
        if args:
            msg = msg.format(*args)
            
        # Colorize warnings (Yellow)
        YELLOW = "\033[33m"
        RESET = "\033[0m"
        lower_msg = msg.lower()
        if "warning" in lower_msg or "not available" in lower_msg or "drift" in lower_msg or "to enable" in lower_msg:
             msg = f"{YELLOW}{msg}{RESET}"

        if self.config.logger:
            try:
                self.config.logger(msg)
            except Exception:
                print(msg)
        else:
            print(msg)

    # ============================================================
    # Transaction context helpers (optional use by Transaction module)
    # ============================================================
    def _get_tx_conn_sync(self) -> Optional[Any]:
        return self._tx_conn_sync.get()

    def _get_tx_conn_async(self) -> Optional[Any]:
        return self._tx_conn_async.get()

    def _bind_tx_conn_sync(self, conn: Any):
        """Bind a sync connection to the current context (Transaction helper)."""
        return self._tx_conn_sync.set(conn)

    def _unbind_tx_conn_sync(self, token):
        return self._tx_conn_sync.reset(token)

    def _bind_tx_conn_async(self, conn: Any):
        """Bind an async connection to the current context (Transaction helper)."""
        return self._tx_conn_async.set(conn)

    def _unbind_tx_conn_async(self, token):
        return self._tx_conn_async.reset(token)

    # ============================================================
    # Helpers privados para logging/metrics/tracer
    # ============================================================
    def _mask_dsn(self, dsn: str) -> str:
        """Mask password in DSN string for secure logging."""
        if not dsn:
            return dsn
        import re
        # Mask password=xxx patterns
        masked = re.sub(r'password=[^\s]+', 'password=***', dsn, flags=re.IGNORECASE)
        # Also mask URI style: postgresql://user:password@host
        masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', masked)
        return masked
    
    def _extract_statement_type(self, sql: str) -> str:
        if not sql:
            return "UNKNOWN"
        first = sql.strip().split(None, 1)[0].upper()
        if first in {"SELECT", "INSERT", "UPDATE", "DELETE"}:
            return first
        if first in {"CREATE", "ALTER", "DROP"}:
            return "DDL"
        if first in {"BEGIN", "COMMIT", "ROLLBACK"}:
            return "TX"
        return first or "UNKNOWN"

    def _extract_table_name(self, sql: str) -> Optional[str]:
        if not sql:
            return None
        s = sql.upper()
        import re
        patterns = [
            r"\bFROM\s+([^\s;,]+)",
            r"\bINTO\s+([^\s;,]+)",
            r"\bUPDATE\s+([^\s;,]+)",
            r"\bJOIN\s+([^\s;,]+)",
        ]
        candidates = []
        for pat in patterns:
            m = re.search(pat, s)
            if m:
                raw = m.group(1)
                raw = raw.split("AS", 1)[0].strip()
                start = s.find(raw)
                if start != -1:
                    candidates.append(sql[start:start + len(raw)])
                else:
                    candidates.append(raw)
        return candidates[0] if candidates else None

    def _update_metrics_internal(
        self,
        statement: Optional[str],
        table: Optional[str],
        duration_ms: Optional[float],
        rows_count: Optional[int],
        error: bool,
    ) -> None:
        if not self._metrics_enabled:
            return
        with self._metrics_lock:
            self._metrics["total_queries"] += 1
            if error:
                self._metrics["total_errors"] += 1

            if statement:
                st = self._metrics["by_statement"][statement]
                st["count"] += 1
                if error:
                    st["errors"] += 1
                if duration_ms is not None:
                    st["total_duration_ms"] += float(duration_ms)
                if rows_count is not None:
                    st["total_rows"] += int(rows_count or 0)

            if table:
                tb = self._metrics["by_table"][table]
                tb["count"] += 1
                if error:
                    tb["errors"] += 1
                if duration_ms is not None:
                    tb["total_duration_ms"] += float(duration_ms)
                if rows_count is not None:
                    tb["total_rows"] += int(rows_count or 0)

    def _append_query_trace_internal(
        self,
        sql: str,
        params: Any,
        duration_ms: Optional[float],
        rows_count: Optional[int],
        statement: Optional[str],
        table: Optional[str],
        error: Optional[BaseException],
        started_at: datetime.datetime,
        finished_at: datetime.datetime,
    ) -> None:
        if not (self._query_tracer_enabled and self._query_trace is not None):
            return
        entry = {
            "sql": sql,
            "params": params,
            "statement": statement,
            "table": table,
            "duration_ms": duration_ms,
            "rows": rows_count,
            "error": repr(error) if error else None,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
        }
        with self._metrics_lock:
            self._query_trace.append(entry)

    def _install_internal_logging_middlewares(self) -> None:
        if self._logging_middlewares_installed:
            return
        self._logging_middlewares_installed = True

        high_priority = 10_000

        def _logging_middleware_sync(sql, params, call_next):
            import time
            start_ts = datetime.datetime.now(datetime.timezone.utc)
            t0 = time.perf_counter()
            err: Optional[BaseException] = None
            rows = None
            try:
                rows = call_next(sql, params)
                return rows
            except Exception as e:
                err = e
                raise
            finally:
                t1 = time.perf_counter()
                duration_ms = (t1 - t0) * 1000.0
                rows_count: Optional[int] = None
                try:
                    if rows is not None and hasattr(rows, "__len__"):
                        rows_count = len(rows)  # type: ignore[arg-type]
                except Exception:
                    rows_count = None

                statement = self._extract_statement_type(sql)
                table = self._extract_table_name(sql)
                finished_ts = datetime.datetime.now(datetime.timezone.utc)

                self._update_metrics_internal(
                    statement=statement,
                    table=table,
                    duration_ms=duration_ms,
                    rows_count=rows_count,
                    error=err is not None,
                )
                self._append_query_trace_internal(
                    sql=sql,
                    params=params,
                    duration_ms=duration_ms,
                    rows_count=rows_count,
                    statement=statement,
                    table=table,
                    error=err,
                    started_at=start_ts,
                    finished_at=finished_ts,
                )

                if self._structured_logging_enabled:
                    if self.config.debug:
                        self._debug("[ENGINE] SQL: {} {}", sql, params or [])

                    self._debug(
                        "[ENGINE|QUERY] stmt={} table={} duration_ms={:.2f} rows={} error={}",
                        statement,
                        table,
                        duration_ms,
                        rows_count,
                        bool(err),
                    )

        async def _logging_middleware_async(sql, params, call_next):
            import time
            start_ts = datetime.datetime.now(datetime.timezone.utc)
            t0 = time.perf_counter()
            err: Optional[BaseException] = None
            rows = None
            try:
                rows = await call_next(sql, params)
                return rows
            except Exception as e:
                err = e
                raise
            finally:
                t1 = time.perf_counter()
                duration_ms = (t1 - t0) * 1000.0
                rows_count: Optional[int] = None
                try:
                    if rows is not None and hasattr(rows, "__len__"):
                        rows_count = len(rows)  # type: ignore[arg-type]
                except Exception:
                    rows_count = None

                statement = self._extract_statement_type(sql)
                table = self._extract_table_name(sql)
                finished_ts = datetime.datetime.now(datetime.timezone.utc)

                self._update_metrics_internal(
                    statement=statement,
                    table=table,
                    duration_ms=duration_ms,
                    rows_count=rows_count,
                    error=err is not None,
                )
                self._append_query_trace_internal(
                    sql=sql,
                    params=params,
                    duration_ms=duration_ms,
                    rows_count=rows_count,
                    statement=statement,
                    table=table,
                    error=err,
                    started_at=start_ts,
                    finished_at=finished_ts,
                )

                if self._structured_logging_enabled:
                    if self.config.debug:
                        self._debug("[ENGINE] SQL: {} {}", sql, params or [])

                    self._debug(
                        "[ENGINE|QUERY] stmt={} table={} duration_ms={:.2f} rows={} error={}",
                        statement,
                        table,
                        duration_ms,
                        rows_count,
                        bool(err),
                    )

        self.add_middleware_sync(_logging_middleware_sync, priority=high_priority)
        self.add_middleware_async(_logging_middleware_async, priority=high_priority)

    # ============================================================
    # API pública de métricas y tracer
    # ============================================================
    def get_query_metrics(self) -> dict[str, Any]:
        if not self._metrics_enabled:
            return {
                "enabled": False,
                "total_queries": 0,
                "total_errors": 0,
                "by_statement": {},
                "by_table": {},
            }
        with self._metrics_lock:
            by_stmt = {k: dict(v) for k, v in self._metrics["by_statement"].items()}
            by_table = {k: dict(v) for k, v in self._metrics["by_table"].items()}
            return {
                "enabled": True,
                "total_queries": self._metrics["total_queries"],
                "total_errors": self._metrics["total_errors"],
                "by_statement": by_stmt,
                "by_table": by_table,
            }

    def reset_query_metrics(self) -> None:
        with self._metrics_lock:
            self._metrics["total_queries"] = 0
            self._metrics["total_errors"] = 0
            self._metrics["by_statement"].clear()
            self._metrics["by_table"].clear()

    def get_query_trace(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        if not (self._query_tracer_enabled and self._query_trace is not None):
            return []
        with self._metrics_lock:
            data = list(self._query_trace)
        if limit is not None and limit >= 0:
            return data[-limit:]
        return data

    # ============================================================
    # DSN helpers (eliminan duplicación)
    # ============================================================
    def _build_sync_dsn(self, *, database_override: Optional[str] = None, admin: bool = False) -> str:
        if self.config.dsn and not admin:
            return self.config.dsn
        dbname = "postgres" if admin else (database_override or self.config.database or "postgres")
        return (
            f"dbname={dbname} user={self.config.username or ''} "
            f"password={self.config.password or ''} host={self.config.host} port={self.config.port}"
        )

    def _build_async_dsn(self, *, database_override: Optional[str] = None) -> str:
        # BUGFIX: respetar database_override incluso cuando se pasa un DSN completo.
        if self.config.dsn:
            if database_override:
                from urllib.parse import urlparse, urlunparse
                try:
                    parsed = urlparse(self.config.dsn)
                    new_path = f"/{database_override}"
                    parsed = parsed._replace(path=new_path)
                    return urlunparse(parsed)
                except Exception:
                    return self.config.dsn
            return self.config.dsn
        dbname = database_override or self.config.database or "postgres"
        return (
            f"postgresql://{self.config.username or ''}:{self.config.password or ''}"
            f"@{self.config.host}:{self.config.port}/{dbname}"
        )

    # ============================================================
    # Startup (sync/async)
    # ============================================================
    def startup_sync(self) -> None:
        """
        Run startup sequence for synchronous mode.

        Perform initialization steps:
        1. Ensure target database exists (`ensure_database`).
        2. Initialize connection pool.
        3. Create missing tables based on registered models (`ensure_tables`).
        4. Run migrations if configured (`ensure_migrations`).
        5. Check for schema drift (`check_schema_drift`).
        6. Start health monitor thread if enabled.

        This method is idempotent; calling it multiple times has no effect.

        Raises:
            RuntimeError: If called on an async-configured engine.
            DatabaseNotFoundError: If database creation fails or connection implies missing DB.
        """
        if self.config.async_:
            raise RuntimeError("startup_sync() called on async engine; use await startup_async()")

        if self._startup_done_sync:
            return

        with self._startup_lock_sync:
            if self._startup_done_sync:
                return

            if self.config.ensure_database:
                self.ensure_database()

            self._init_sync_pool()

            if self.config.ensure_tables:
                self.ensure_tables()

            if self.config.ensure_migrations:
                self.ensure_migrations()

            if self.config.check_schema_drift:
                self.check_schema_drift()

            if self.config.health_check_enabled:
                try:
                    self.start_health_monitor()
                except Exception:
                    self._debug("[ENGINE] failed to start sync health monitor")

            self._startup_done_sync = True

    async def startup_async(self) -> None:
        """
        Run startup sequence for asynchronous mode within the running event loop.
        
        Performs similar steps to `startup_sync` but adapted for async execution:
        1. Ensures database exists (`ensure_database_async`).
        2. Creates tables (`ensure_tables_async`).
        3. Initializes async connection pool (`asyncpg`).
        4. Starts health monitor task.
        
        Note: Migrations and schema drift checks are currently sync-only and skipped here.
        
        Raises:
            RuntimeError: If called on a sync-configured engine.
        """
        if not self.config.async_:
            raise RuntimeError("startup_async() called on sync engine; use startup_sync()")

        if self._startup_done_async:
            return

        if self._startup_lock_async is None:
            self._startup_lock_async = asyncio.Lock()

        async with self._startup_lock_async:
            if self._startup_done_async:
                return

            # Ensure DB exists before any pool operations
            if self.config.ensure_database:
                await self.ensure_database_async()

            # Ensure tables before pool (DDL ops use direct connections; pool still lazy)
            if self.config.ensure_tables:
                await self.ensure_tables_async()

            # Auto-run migrations if enabled
            if self.config.ensure_migrations:
                await self.ensure_migrations_async()

            if self.config.check_schema_drift:
                await self.check_schema_drift_async()

            if self.config.health_check_enabled:
                try:
                    await self.start_health_monitor_async()
                except Exception:
                    self._debug("[ENGINE] failed to start async health monitor")

            # Initialize the async pool so it's ready for use
            await self._init_async_pool()

            self._startup_done_async = True
            self._pending_async_setup = False

    async def _ensure_startup_async_if_needed(self) -> None:
        """Ensure startup_async() has been called, but skip if auto_startup=False or already done."""
        if not self.config.auto_startup:
            return  # User wants manual control
        if self.config.async_ and (self._pending_async_setup or not self._startup_done_async):
            await self.startup_async()

    def _ensure_startup_sync_if_needed(self) -> None:
        """Ensure startup_sync() has been called, but skip if auto_startup=False or already done."""
        if not self.config.auto_startup:
            return  # User wants manual control
        if not self.config.async_ and not self._startup_done_sync:
            self.startup_sync()

    # ============================================================
    # Gestión de conexiones sync
    # ============================================================
    def _init_sync_pool(self) -> None:
        if self._pool is not None:
            return
        self._pool = queue.Queue()
        for _ in range(self.config.pool_size):
            conn = self._create_sync_connection()
            self._pool.put(conn)
            self._pool_size += 1
        self._debug("[ENGINE] sync pool initialized with size={}", self._pool_size)

    def _repair_sync_pool(self) -> None:
        if self._pool is None:
            return
        with self._pool_lock:
            conns = []
            while not self._pool.empty():
                try:
                    conns.append(self._pool.get_nowait())
                except queue.Empty:
                    break
            repaired = 0
            for i, conn in enumerate(conns):
                try:
                    closed = getattr(conn, "closed", 1)
                except Exception:
                    closed = 1
                if closed:
                    try:
                        conns[i] = self._create_sync_connection()
                        repaired += 1
                    except Exception:
                        conns[i] = conn
            for conn in conns:
                self._pool.put(conn)
            if repaired and self.config.debug:
                self._debug("[ENGINE] sync pool repaired: {} connections recreated", repaired)

    def _create_sync_connection(self):
        dsn = self._build_sync_dsn()
        self._debug("[ENGINE] CONNECT (pool sync) DSN={}", self._mask_dsn(dsn))
        try:
            return psycopg.connect(dsn)
        except psycopg.OperationalError as e:
            error_msg = str(e).lower()
            if "database" in error_msg and "does not exist" in error_msg:
                db_name = self.config.database or "unknown"
                raise DatabaseNotFoundError(db_name, e) from e
            raise ConnectionError(f"Failed to connect to database: {e}") from e

    def acquire_sync(self):
        """
        Acquire a connection from the synchronous pool.

        Blocks until a connection is available or timeout occurs.
        Features:
        - Auto-resizing if enabled.
        - Recycle check (closes old connections).
        - Pre-ping (validates connection aliveness).

        Returns:
            psycopg.Connection: A ready-to-use database connection.

        Raises:
            TimeoutError: If no connection is acquired within `config.connection_timeout`.
            RuntimeError: If called on Async engine.
        """
        if self.config.async_:
            raise RuntimeError("Engine configurado en modo async; use acquire()")
        
        # Ensure startup has been run (will skip if already done)
        self._ensure_startup_sync_if_needed()
        
        if self._pool is None:
            self._init_sync_pool()

        timeout = self.config.connection_timeout
        try:
            conn = self._pool.get(timeout=timeout)
        except queue.Empty:
            if self.config.auto_adjust_pool_size:
                with self._pool_lock:
                    max_pool = self.config.max_pool_size or (self.config.pool_size * 4)
                    if self._pool_size < max_pool:
                        conn = self._create_sync_connection()
                        self._pool_size += 1
                        self._debug(
                            "[ENGINE] sync pool resize: new_size={} max={}",
                            self._pool_size,
                            max_pool,
                        )
                        return conn
            raise TimeoutError("Timeout acquiring connection from pool")

        import time
        now = time.time()

        # Recycle
        if self.config.pool_recycle and self.config.pool_recycle > 0:
            last = self._conn_last_used_sync.get(conn, 0.0)
            if (now - last) >= float(self.config.pool_recycle):
                try:
                    conn.close()
                except Exception:
                    pass
                conn = self._create_sync_connection()

        # Pre-ping
        if self.config.pool_pre_ping:
            try:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.close()
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
                conn = self._create_sync_connection()

        return conn

    def release_sync(self, conn) -> None:
        """
        Return a connection to the synchronous pool.
        
        Args:
            conn: The psycopg connection to return.
        """
        if self.config.async_:
            raise RuntimeError("Engine configurado en modo async; use release()")
        if self._pool is None:
            return
        import time
        self._conn_last_used_sync[conn] = time.time()
        self._pool.put(conn)

    # ============================================================
    # Gestión de conexiones async
    # ============================================================
    async def acquire(self):
        if not self.config.async_:
            raise RuntimeError("Engine configurado en modo sync; use acquire_sync()")

        await self._ensure_startup_async_if_needed()

        if self._async_pool is None:
            await self._init_async_pool()

        assert self._async_pool is not None

        if self.config.pool_recycle and self.config.pool_recycle > 0:
            import time
            if (time.time() - self._async_pool_last_recreate) >= float(self.config.pool_recycle):
                await self._recreate_async_pool(
                    self._async_pool_max_size or (self.config.max_pool_size or self.config.pool_size)
                )

        timeout = self.config.connection_timeout
        try:
            if timeout and timeout > 0:
                conn = await asyncio.wait_for(self._async_pool.acquire(), timeout=timeout)
            else:
                conn = await self._async_pool.acquire()

            if self.config.pool_pre_ping:
                try:
                    await asyncio.wait_for(
                        conn.fetchrow("SELECT 1"),
                        timeout=self.config.health_check_timeout or 5.0,
                    )
                except Exception:
                    try:
                        await self._async_pool.release(conn)
                    except Exception:
                        try:
                            await conn.close()
                        except Exception:
                            pass
                    if timeout and timeout > 0:
                        conn = await asyncio.wait_for(self._async_pool.acquire(), timeout=timeout)
                    else:
                        conn = await self._async_pool.acquire()

            return conn

        except asyncio.TimeoutError:
            if self.config.auto_adjust_pool_size:
                return await self._async_auto_adjust_and_retry_acquire()
            raise TimeoutError("Timeout acquiring connection from async pool")

    async def release(self, conn) -> None:
        if not self.config.async_:
            raise RuntimeError("Engine configurado en modo sync; use release_sync()")
        if self._async_pool is None:
            try:
                await conn.close()
            except Exception:
                pass
            return
        try:
            await self._async_pool.release(conn)
        except Exception:
            try:
                await conn.close()
            except Exception:
                pass

    async def _init_async_pool(self) -> None:
        if self._async_pool is not None:
            return

        dsn = self._build_async_dsn()
        self._debug("[ENGINE] ASYNC POOL CREATE DSN={}", self._mask_dsn(dsn))
        try:
            max_size = self.config.max_pool_size or self.config.pool_size
            self._async_pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=1,
                max_size=max_size,
                timeout=self.config.connection_timeout,
            )
            self._async_pool_max_size = max_size
            import time
            self._async_pool_last_recreate = time.time()
        except asyncpg.InvalidCatalogNameError as e:
            db_name = self.config.database or "unknown"
            raise DatabaseNotFoundError(db_name, e) from e
        except Exception as e:
            raise ConnectionError(f"Failed to create async pool: {e}") from e

    async def _async_auto_adjust_and_retry_acquire(self):
        current_max = self._async_pool_max_size or (self.config.max_pool_size or self.config.pool_size)
        hard_max = self.config.max_pool_size or (self.config.pool_size * 4)
        if current_max >= hard_max:
            raise TimeoutError("Timeout acquiring connection from async pool (max size reached)")

        new_max = min(current_max + 1, hard_max)
        try:
            await self._recreate_async_pool(new_max)
        except Exception:
            raise TimeoutError("Timeout acquiring connection from async pool (resize failed)")

        assert self._async_pool is not None
        timeout = self.config.connection_timeout
        try:
            if timeout and timeout > 0:
                return await asyncio.wait_for(self._async_pool.acquire(), timeout=timeout)
            else:
                return await self._async_pool.acquire()
        except asyncio.TimeoutError:
            raise TimeoutError("Timeout acquiring connection from async pool")

    async def _recreate_async_pool(self, new_max_size: int) -> None:
        if self._async_pool is not None:
            try:
                close_timeout = getattr(self.config, 'pool_close_timeout', 5.0) or 5.0
                await asyncio.wait_for(self._async_pool.close(), timeout=close_timeout)
            except asyncio.TimeoutError:
                try:
                    self._async_pool.terminate()
                except Exception:
                    pass
            except Exception:
                pass
            self._async_pool = None

        dsn = self._build_async_dsn()
        self._async_pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=new_max_size,
            timeout=self.config.connection_timeout,
        )
        self._async_pool_max_size = new_max_size
        self._debug("[ENGINE] async pool resize: new_max_size={}", new_max_size)
        import time
        self._async_pool_last_recreate = time.time()

    # ============================================================
    # Context managers
    # ============================================================
    def connection(self) -> ContextManager[Any]:
        """
        Synchronous context manager for acquiring and releasing a connection.

        Features:
        - Transaction aware: If an active transaction exists, reuses its connection.
        - Pool management: Acquires from pool on entry, releases on exit (if not tx bound).
        
        Yields:
             psycopg.Connection: The active database connection.
        """
        from contextlib import contextmanager

        @contextmanager
        def _cm():
            tx_conn = self._get_tx_conn_sync()
            if tx_conn is not None:
                yield tx_conn
                return

            conn = self.acquire_sync()
            try:
                yield conn
            finally:
                self.release_sync(conn)

        return _cm()

    def connection_async(self) -> AsyncContextManager[Any]:
        """
        Asynchronous context manager for acquiring and releasing a connection.

        Features:
        - Transaction aware: If an active transaction exists, reuses its connection.
        - Pool management: Acquires from pool on entry, releases on exit (if not tx bound).
        
        Yields:
             asyncpg.Connection: The active database connection.
        """
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _acm():
            tx_conn = self._get_tx_conn_async()
            if tx_conn is not None:
                yield tx_conn
                return

            conn = await self.acquire()
            try:
                yield conn
            finally:
                await self.release(conn)

        return _acm()

    # ============================================================
    # Health monitor helpers
    # ============================================================
    def _health_monitor_thread(self) -> None:
        interval = max(0.1, float(self.config.health_check_interval or 0.0))
        stop_evt = self._health_thread_stop
        while not stop_evt.wait(interval):
            try:
                self._repair_sync_pool()
            except Exception:
                self._debug("[ENGINE] health monitor error (sync)")

    def start_health_monitor(self) -> None:
        if not self.config.health_check_enabled or self.config.async_:
            return
        if self._health_thread and self._health_thread.is_alive():
            return
        self._health_thread_stop.clear()
        t = threading.Thread(target=self._health_monitor_thread, daemon=True)
        self._health_thread = t
        t.start()

    async def start_health_monitor_async(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        if not self.config.health_check_enabled or not self.config.async_:
            return
        if self._health_task and not self._health_task.done():
            return
        loop = loop or asyncio.get_running_loop()

        async def _task():
            interval = max(0.1, float(self.config.health_check_interval or 0.0))
            while True:
                try:
                    await self._repair_async_pool()
                except Exception:
                    self._debug("[ENGINE] health monitor error (async)")
                await asyncio.sleep(interval)

        self._health_task = loop.create_task(_task())

    async def _repair_async_pool(self) -> None:
        if self._async_pool is None:
            return
        try:
            async with self._async_pool.acquire() as conn:
                try:
                    await asyncio.wait_for(
                        conn.fetchrow("SELECT 1"),
                        timeout=self.config.health_check_timeout,
                    )
                except asyncio.TimeoutError:
                    raise
        except Exception:
            try:
                close_timeout = getattr(self.config, 'pool_close_timeout', 5.0) or 5.0
                await asyncio.wait_for(self._async_pool.close(), timeout=close_timeout)
            except asyncio.TimeoutError:
                try:
                    self._async_pool.terminate()
                except Exception:
                    pass
            except Exception:
                pass
            self._async_pool = None
            try:
                await self._init_async_pool()
            except Exception:
                self._debug("[ENGINE] async pool repair failed")

    def stop_health_monitor(self) -> None:
        if self._health_thread:
            self._health_thread_stop.set()
            try:
                self._health_thread.join(timeout=1.0)
            except Exception:
                pass
            self._health_thread = None

    def dispose(self) -> None:
        self.stop_health_monitor()
        if self._pool is not None:
            conns = []
            try:
                while not self._pool.empty():
                    conns.append(self._pool.get_nowait())
            except Exception:
                pass
            for c in conns:
                try:
                    c.close()
                except Exception:
                    pass
            self._pool = None
            self._pool_size = 0
            self._debug("[ENGINE] sync pool disposed")

    async def stop_health_monitor_async(self) -> None:
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except Exception:
                pass
            self._health_task = None
        if self._async_pool is not None:
            try:
                # Graceful close with timeout (default 5s)
                # pool.close() waits for all connections to be released
                close_timeout = getattr(self.config, 'pool_close_timeout', 5.0) or 5.0
                await asyncio.wait_for(self._async_pool.close(), timeout=close_timeout)
            except asyncio.TimeoutError:
                # Force terminate unreleased connections
                self._debug("[ENGINE] pool.close() timeout, forcing terminate()")
                try:
                    self._async_pool.terminate()
                except Exception:
                    pass
            except Exception:
                pass
            self._async_pool = None
            self._debug("[ENGINE] async pool disposed")

    async def dispose_async(self) -> None:
        await self.stop_health_monitor_async()

    # ============================================================
    # Health metrics
    # ============================================================
    def health_check(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "mode": "async" if self.config.async_ else "sync",
            "database": self.config.database,
        }
        if not self.config.async_:
            current_size = self._pool_size
            max_size = self.config.max_pool_size or (self.config.pool_size * 4)
            if self._pool is not None:
                try:
                    idle = self._pool.qsize()
                except Exception:
                    idle = None
                active = current_size - (idle or 0)
            else:
                idle = 0
                active = 0
            data.update(
                {
                    "pool_size": current_size,
                    "max_pool_size": max_size,
                    "idle": idle,
                    "active": active,
                }
            )
        else:
            data.update(
                {
                    "max_pool_size": self._async_pool_max_size
                    or (self.config.max_pool_size or self.config.pool_size),
                    "details": "use health_check_async() for async pool metrics",
                }
            )
        return data

    async def health_check_async(self) -> dict[str, Any]:
        if not self.config.async_:
            raise RuntimeError("Engine configurado en modo sync; use health_check()")

        await self._ensure_startup_async_if_needed()

        if self._async_pool is None:
            await self._init_async_pool()
        assert self._async_pool is not None
        data: dict[str, Any] = {
            "mode": "async",
            "database": self.config.database,
        }
        try:
            size = self._async_pool.get_size()  # type: ignore[attr-defined]
            max_size = self._async_pool.get_max_size()  # type: ignore[attr-defined]
            idle = self._async_pool.get_idle_count()  # type: ignore[attr-defined]
        except Exception:
            size = None
            max_size = self._async_pool_max_size or (
                self.config.max_pool_size or self.config.pool_size
            )
            idle = None
        data.update({"pool_size": size, "max_pool_size": max_size, "idle": idle})
        if isinstance(size, int) and isinstance(idle, int):
            data["active"] = max(0, size - idle)
        return data

    # Metrics alias + logger
    def metrics(self) -> dict[str, Any]:
        return self.health_check()

    async def metrics_async(self) -> dict[str, Any]:
        return await self.health_check_async()

    def start_metrics_logger(self, interval: float = 30.0) -> None:
        """Start a background thread that prints health metrics periodically (debug-style)."""
        stop_evt = getattr(self, "_metrics_thread_stop", None)
        if stop_evt is None:
            stop_evt = threading.Event()
            self._metrics_thread_stop = stop_evt  # type: ignore[attr-defined]

        def _worker():
            import time
            while not stop_evt.wait(max(0.1, float(interval or 0.0))):
                try:
                    m = self.health_check()
                    print(f"[ENGINE] metrics: {m}")
                except Exception:
                    pass

        if getattr(self, "_metrics_thread", None) and getattr(
            self._metrics_thread, "is_alive", lambda: False
        )():
            return
        t = threading.Thread(target=_worker, daemon=True)
        self._metrics_thread = t  # type: ignore[attr-defined]
        t.start()

    def stop_metrics_logger(self) -> None:
        """Stop sync metrics logger thread if running."""
        evt = getattr(self, "_metrics_thread_stop", None)
        if evt is not None:
            evt.set()

    async def start_metrics_logger_async(self, interval: float = 30.0) -> None:
        """Start a background asyncio task that prints health metrics periodically (async)."""
        if getattr(self, "_metrics_task", None) and not self._metrics_task.done():  # type: ignore
            return

        stop_evt = getattr(self, "_metrics_task_stop", None)
        if stop_evt is None:
            stop_evt = asyncio.Event()
            self._metrics_task_stop = stop_evt  # type: ignore[attr-defined]

        async def _worker():
            while True:
                if stop_evt.is_set():
                    return
                try:
                    m = await self.health_check_async()
                    print(f"[ENGINE] metrics (async): {m}")
                except Exception:
                    pass
                await asyncio.sleep(max(0.1, float(interval or 0.0)))

        loop = asyncio.get_running_loop()
        self._metrics_task = loop.create_task(_worker())  # type: ignore

    async def stop_metrics_logger_async(self) -> None:
        evt = getattr(self, "_metrics_task_stop", None)
        if evt is not None:
            evt.set()
        task = getattr(self, "_metrics_task", None)
        if task is not None:
            try:
                task.cancel()
            except Exception:
                pass

    # ============================================================
    # Ejecución sync
    # ============================================================
    def execute(self, query_or_sql: Any, *params: Any, **kwargs: Any) -> Any:
        """
        Execute a SQL statement or Query object synchronously.
        
        Args:
            query_or_sql: SQL string or a Query object with `to_sql_params()`.
            *params: Parameters to substitute into the SQL query (if passing raw SQL).
            **kwargs: Additional options (currently unused).
            
        Returns:
             The result of the query execution (usually a list of rows or None for DML).
            
        Raises:
            RuntimeError: If called on an async-configured engine.
        """
        if self.config.async_:
            raise RuntimeError("Engine configurado en modo async; use execute_async()")
        if hasattr(query_or_sql, "to_sql_params"):
            sql, query_params = query_or_sql.to_sql_params()
        elif hasattr(query_or_sql, "to_sql"):
            sql = query_or_sql.to_sql()
            query_params = params
        else:
            sql = str(query_or_sql)
            query_params = params
        return self._run_sync_pipeline(sql, query_params)

    def _execute_core_sync(self, sql: str, query_params: Any):
        """Core synchronous executor with correct commit/rollback semantics.

        - If running inside a transaction context (tx connection bound), it will NOT auto-commit/rollback.
        - Otherwise, it commits on success and rolls back on error to keep pooled connections clean.
        """
        self._debug("[ENGINE] SQL: {} {}", sql, query_params)

        for h in list(self._hooks.get("before_execute", [])):
            try:
                h(sql, query_params)
            except Exception:
                self._debug("[ENGINE] before_execute hook error")

        tx_conn = self._get_tx_conn_sync()
        if tx_conn is not None:
            conn = tx_conn
            cur = conn.cursor()
            try:
                cur.execute(sql, query_params or None)
                try:
                    rows = cur.fetchall()
                except psycopg.ProgrammingError:
                    rows = None
            finally:
                try:
                    cur.close()
                except Exception:
                    pass

            for h in list(self._hooks.get("after_execute", [])):
                try:
                    h(sql, rows)
                except Exception:
                    self._debug("[ENGINE] after_execute hook error")
            return rows

        # No active transaction -> managed lifecycle
        with self.connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(sql, query_params or None)
                try:
                    rows = cur.fetchall()
                except psycopg.ProgrammingError:
                    rows = None
                # Always commit to avoid leaving implicit transactions open in pooled conns
                try:
                    conn.commit()
                except Exception:
                    pass
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
                raise
            finally:
                try:
                    cur.close()
                except Exception:
                    pass

            for h in list(self._hooks.get("after_execute", [])):
                try:
                    h(sql, rows)
                except Exception:
                    self._debug("[ENGINE] after_execute hook error")
            return rows

    # ============================================================
    # NUEVO: helper raw para Relation (sync only)
    # ============================================================
    def execute_raw(self, sql: str, params: Optional[list[Any]] = None) -> list[tuple]:
        """
        Execute raw SQL and return a list of rows (tuples).
        
        Designed for internal use (relationships) or when skipping the ORM layer is desired.
        Supports only synchronous mode.
        
        Args:
            sql (str): Raw SQL query.
            params (list, optional): List of parameters for the query.
            
        Returns:
            list[tuple]: List of result rows found. Returns empty list if no rows.
        """
        if self.config.async_:
            raise RuntimeError("execute_raw solo está disponible en Engine síncrono")

        self._debug("[ENGINE] RAW SQL: {} {}", sql, params)

        tx_conn = self._get_tx_conn_sync()
        if tx_conn is not None:
            conn = tx_conn
            cur = conn.cursor()
            try:
                cur.execute(sql, params or None)
                try:
                    rows = cur.fetchall()
                except psycopg.ProgrammingError:
                    rows = []
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
            return rows

        with self.connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(sql, params or None)
                try:
                    rows = cur.fetchall()
                except psycopg.ProgrammingError:
                    rows = []
                try:
                    conn.commit()
                except Exception:
                    pass
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
                raise
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
            return rows

    async def execute_raw_async(self, sql: str, params: Optional[list[Any]] = None) -> list[tuple]:
        """
        Execute raw SQL asynchronously and return a list of rows (tuples).
        
        Designed for internal use (relationships) or when skipping the ORM layer is desired.
        Supports only asynchronous mode.
        
        Args:
            sql (str): Raw SQL query.
            params (list, optional): List of parameters for the query.
            
        Returns:
            list[tuple]: List of result rows found. Returns empty list if no rows.
        """
        if not self.config.async_:
            raise RuntimeError("execute_raw_async solo está disponible en Engine asíncrono")

        await self._ensure_startup_async_if_needed()

        self._debug("[ENGINE] RAW SQL (async): {} {}", sql, params)

        # Convert placeholders %s -> $n (only if needed)
        if params and "%s" in sql:
            idx = 1
            while "%s" in sql:
                sql = sql.replace("%s", f"${idx}", 1)
                idx += 1

        tx_conn = self._get_tx_conn_async()
        if tx_conn is not None:
            records = await tx_conn.fetch(sql, *params) if params else await tx_conn.fetch(sql)
            return [tuple(r.values()) for r in records]

        if self._async_pool is None:
            await self._init_async_pool()

        assert self._async_pool is not None
        async with self._async_pool.acquire() as conn:
            records = await conn.fetch(sql, *params) if params else await conn.fetch(sql)
            return [tuple(r.values()) for r in records]

    def _run_sync_pipeline(self, sql: str, query_params: Any):
        import signal

        def final(s, p):
            return self._execute_core_sync(s, p)

        chain = final
        # BUGFIX: prioridad más alta envuelve a las demás (se ejecuta primero).
        sorted_mws = sorted(self._middlewares_sync, key=lambda x: x[0])
        for priority, mw_func, timeout in sorted_mws:
            prev = chain

            def make_mw(mw, prev_func, mw_timeout):
                def _wrapped(s, p):
                    use_alarm = (
                        mw_timeout is not None
                        and mw_timeout > 0
                        and hasattr(signal, "setitimer")
                        and threading.current_thread() is threading.main_thread()
                    )
                    if use_alarm:
                        def _timeout_handler(signum, frame):
                            raise TimeoutError(f"Middleware timed out after {mw_timeout}s")
                        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                        try:
                            signal.setitimer(signal.ITIMER_REAL, mw_timeout)
                            return mw(s, p, prev_func)
                        finally:
                            signal.setitimer(signal.ITIMER_REAL, 0)
                            signal.signal(signal.SIGALRM, old_handler)
                    else:
                        return mw(s, p, prev_func)

                return _wrapped

            chain = make_mw(mw_func, prev, timeout)

        def _retry_run():
            attempts = max(0, int(self.config.max_retries or 0))
            delay = float(self.config.retry_delay or 0.0)
            last_exc = None
            for i in range(attempts + 1):
                try:
                    return chain(sql, query_params)
                except Exception as e:
                    last_exc = e
                    if i < attempts and delay > 0:
                        import time
                        time.sleep(delay)
                        continue
                    raise last_exc

        return _retry_run()

    def parallel_execute(self, tasks: list[Any], *, max_workers: Optional[int] = None) -> list[Any]:
        """
        Execute multiple queries in parallel using a thread pool.
        
        Each task is executed in a separate thread, acquiring its own connection from the pool.
        
        Args:
            tasks (list[Any]): List of queries or (query, params) tuples.
            max_workers (Optional[int]): Max threads to use. Defaults to pool size or task count.
            
        Returns:
            list[Any]: List of results in the same order as tasks.
            
        Raises:
            RuntimeError: If called on async engine.
        """
        if self.config.async_:
            raise RuntimeError("Engine async; use parallel_execute_async()")
        if not tasks:
            return []

        def _unpack(task):
            if isinstance(task, tuple):
                return task[0], task[1:]
            return task, ()

        def _run(task):
            q, params = _unpack(task)
            return self.execute(q, *params)

        workers = max_workers or min(len(tasks), self.config.pool_size or len(tasks))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(_run, t) for t in tasks]
            return [f.result() for f in futures]

    # ============================================================
    # Ejecución async
    # ============================================================
    async def execute_async(self, query_or_sql: Any, *params: Any, **kwargs: Any) -> Any:
        """
        Execute a SQL statement or Query object asynchronously.
        
        Ensures the engine is started (lazy startup) and handles parameter style conversion
        (psycopg `%s` -> asyncpg `$n`).
        
        Args:
            query_or_sql: SQL string or Query object.
            *params: Parameters for the query.
            **kwargs: Unused.
            
        Returns:
            list[asyncpg.Record]: Result records.
            
        Raises:
            RuntimeError: If called on sync engine.
        """
        if not self.config.async_:
            raise RuntimeError("Engine configurado en modo sync; use execute()")

        await self._ensure_startup_async_if_needed()

        if hasattr(query_or_sql, "to_sql_params"):
            sql, query_params = query_or_sql.to_sql_params()
        elif hasattr(query_or_sql, "to_sql"):
            sql = query_or_sql.to_sql()
            query_params = params
        else:
            sql = str(query_or_sql)
            query_params = params

        self._debug("[ENGINE] SQL (async): {} {}", sql, query_params)
        return await self._run_async_pipeline(sql, query_params)

    async def _execute_core_async(self, sql: str, query_params: Any):
        for h in list(self._hooks.get("before_execute", [])):
            try:
                res = h(sql, query_params)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                self._debug("[ENGINE] before_execute hook error")

        tx_conn = self._get_tx_conn_async()
        if tx_conn is not None:
            # Convert psycopg-style %s placeholders to asyncpg-style $1, $2...
            if query_params and "%s" in sql:
                idx = 1
                while "%s" in sql:
                    sql = sql.replace("%s", f"${idx}", 1)
                    idx += 1

            rows = await tx_conn.fetch(sql, *query_params) if query_params else await tx_conn.fetch(sql)
            for h in list(self._hooks.get("after_execute", [])):
                try:
                    res = h(sql, rows)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception:
                    self._debug("[ENGINE] after_execute hook error")
            return rows

        if self._async_pool is None:
            await self._init_async_pool()

        # Convert placeholders if needed
        if query_params and "%s" in sql:
            idx = 1
            while "%s" in sql:
                sql = sql.replace("%s", f"${idx}", 1)
                idx += 1

        assert self._async_pool is not None
        async with self._async_pool.acquire() as conn:
            # Avoid prepare() overhead by default; asyncpg handles statement cache internally.
            rows = await conn.fetch(sql, *query_params) if query_params else await conn.fetch(sql)

            for h in list(self._hooks.get("after_execute", [])):
                try:
                    res = h(sql, rows)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception:
                    self._debug("[ENGINE] after_execute hook error")
            return rows

    async def _run_async_pipeline(self, sql: str, query_params: Any):
        async def final(s, p):
            return await self._execute_core_async(s, p)

        chain = final
        sorted_mws = sorted(self._middlewares_async, key=lambda x: x[0])
        for priority, mw_func, timeout in sorted_mws:
            prev = chain

            def make_mw(mw, prev_func, mw_timeout):
                async def _wrapped(s, p):
                    if mw_timeout is not None and mw_timeout > 0:
                        try:
                            return await asyncio.wait_for(mw(s, p, prev_func), timeout=mw_timeout)
                        except asyncio.TimeoutError:
                            raise TimeoutError(f"Async middleware timed out after {mw_timeout}s")
                    else:
                        return await mw(s, p, prev_func)
                return _wrapped

            chain = make_mw(mw_func, prev, timeout)

        attempts = max(0, int(self.config.max_retries or 0))
        delay = float(self.config.retry_delay or 0.0)
        last_exc = None
        for i in range(attempts + 1):
            try:
                return await chain(sql, query_params)
            except Exception as e:
                last_exc = e
                if i < attempts and delay > 0:
                    await asyncio.sleep(delay)
                    continue
                raise last_exc

    async def parallel_execute_async(self, tasks: list[Any], *, max_concurrency: Optional[int] = None) -> list[Any]:
        if not self.config.async_:
            raise RuntimeError("Engine sync; use parallel_execute()")
        if not tasks:
            return []

        await self._ensure_startup_async_if_needed()

        semaphore = asyncio.Semaphore(max_concurrency) if max_concurrency else None

        async def _run(task):
            q, params = (task[0], task[1:]) if isinstance(task, tuple) else (task, ())
            if semaphore:
                async with semaphore:
                    return await self.execute_async(q, *params)
            return await self.execute_async(q, *params)

        return await asyncio.gather(*[_run(t) for t in tasks])

    # ============================================================
    # Middleware registration
    # ============================================================
    def add_middleware_sync(self, func, *, priority: int = 100, timeout: Optional[float] = None) -> None:
        self._middlewares_sync.append((priority, func, timeout))

    def add_middleware_async(self, func, *, priority: int = 100, timeout: Optional[float] = None) -> None:
        self._middlewares_async.append((priority, func, timeout))

    def remove_middleware_sync(self, func) -> None:
        self._middlewares_sync = [(p, f, t) for p, f, t in self._middlewares_sync if f is not func]

    def remove_middleware_async(self, func) -> None:
        self._middlewares_async = [(p, f, t) for p, f, t in self._middlewares_async if f is not func]

    def clear_middlewares_sync(self) -> None:
        self._middlewares_sync.clear()

    def clear_middlewares_async(self) -> None:
        self._middlewares_async.clear()

    # ============================================================
    # Hooks management
    # ============================================================
    def add_hook(self, name: str, func) -> None:
        if name not in self._hooks:
            raise ValueError(f"Unknown hook '{name}'")
        self._hooks[name].append(func)

    def remove_hook(self, name: str, func) -> None:
        if name not in self._hooks:
            return
        try:
            self._hooks[name].remove(func)
        except ValueError:
            pass

    # ============================================================
    # Transactions
    # ============================================================
    def transaction(self):
        from .transactions import Transaction
        return Transaction(self)

    async def transaction_async(self):
        # Kept for backwards compatibility: returns Transaction(self)
        from .transactions import Transaction
        return Transaction(self)

    # ============================================================
    # Auto-setup: database, tables, triggers
    # ============================================================
    def ensure_database(self) -> None:
        """
        Create the target database if it does not exist.
        
        Connects to the 'postgres' default database to check for existence
        and issues the CREATE DATABASE command if needed.
        
        Raises:
            ConnectionError: If connection to 'postgres' fails.
        """
        dbname = self.config.database
        if not dbname:
            return

        admin_dsn = self._build_sync_dsn(admin=True)
        self._debug("[ENGINE] CONNECT (admin) DSN={}", self._mask_dsn(admin_dsn))

        try:
            conn = psycopg.connect(admin_dsn, autocommit=True)
        except Exception as e:
            raise ConnectionError(f"Failed to connect (admin) to create database: {e}") from e

        try:
            cur = conn.cursor()
            self._debug("[ENGINE] SQL: {} {}", "SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            exists = cur.fetchone() is not None
            if not exists:
                # Use safe identifier formatting
                from psycopg import sql as pgsql
                sql_stmt = pgsql.SQL("CREATE DATABASE {}").format(pgsql.Identifier(dbname))
                self._debug("[ENGINE] SQL: {}", str(sql_stmt))
                cur.execute(sql_stmt)
            cur.close()
        finally:
            try:
                conn.close()
            except Exception:
                pass

    async def ensure_database_async(self) -> None:
        """
        Create the target database if it does not exist (async).
        
        Connects to the 'postgres' default database using asyncpg to check for existence
        and issues the CREATE DATABASE command if needed.
        
        Raises:
            DatabaseNotFoundError: If 'postgres' db is missing.
            ConnectionError: If connection fails.
        """
        dbname = self.config.database
        if not dbname:
            return

        admin_dsn = self._build_async_dsn(database_override="postgres")
        self._debug("[ENGINE] CONNECT (admin async) DSN={}", self._mask_dsn(admin_dsn))

        try:
            conn = await asyncpg.connect(admin_dsn)
            try:
                exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", dbname)
                if not exists:
                    if not _is_valid_identifier(dbname) and '"' in dbname:
                        # database names can be quoted; we avoid supporting weird names via raw f-strings
                        raise ValueError(f"Invalid database name '{dbname}'")
                    # CREATE DATABASE cannot be parameterized; validate + execute
                    if not _is_valid_identifier(dbname) and not dbname.isidentifier():
                        # fallback strict validation
                        raise ValueError(f"Invalid database name '{dbname}'")
                    sql = f"CREATE DATABASE {dbname}"
                    self._debug("[ENGINE] SQL (async): {}", sql)
                    await conn.execute(sql)
            finally:
                await conn.close()
        except asyncpg.InvalidCatalogNameError as e:
            raise DatabaseNotFoundError(dbname, e) from e
        except Exception as e:
            raise ConnectionError(f"ensure_database_async failed: {e}") from e

    def ensure_tables(self) -> None:
        """
        Generate and execute DDL for all registered models (Sync).
        
        Steps:
        1. Discover models (via EnsureDatabaseTables helper).
        2. Generate CREATE TABLE / CREATE INDEX sql.
        3. Execute DDL steps in valid dependency order.
        4. Re-create Triggers and Functions.
        
        Note: This is non-destructive (uses IF NOT EXISTS).
        """
        EnsureDatabaseTables(self)
        self.apply_ddl_plan()
        self._ensure_triggers_sync()

    async def ensure_tables_async(self) -> None:
        """
        Generate and execute DDL for all registered models (Async).
        
        Steps:
        1. Discover models (via EnsureDatabaseTables helper).
        2. Generate CREATE TABLE / CREATE INDEX sql.
        3. Execute DDL steps asynchronously.
        4. Re-create Triggers and Functions asynchronously.
        
        Note: This is non-destructive (uses IF NOT EXISTS).
        """
        EnsureDatabaseTables(self)
        await self.apply_ddl_plan_async()
        await self._ensure_triggers_async()

    def ensure_migrations(self) -> None:
        """
        Auto-run migrations on startup.

        Process:
        1. Initialize migrations system at `migrations_path` if missing.
        2. Check for schema drift compared to last migration.
        3. Auto-generate a new migration file if drift is detected.
        4. Apply all pending migrations (`upgrade head`).
        
        Useful for development environments to keep DB in sync with code automatically.
        """
        from ..migrations import MigrationManager, MigrationConfig

        migrations_path = self.config.migrations_path or "./migrations"

        config = MigrationConfig(
            migrations_path=migrations_path,
            debug=self.config.debug,
            logger=self.config.logger,
        )
        manager = MigrationManager(self, config)

        status = manager.status()
        if not status.initialized:
            manager.init()
            self._debug("[ENGINE] Migrations initialized at {}", migrations_path)

        try:
            diff = manager._compute_diff(context="Startup")
            if diff.has_changes:
                migration = manager.autogenerate("Auto-generated migration")
                if migration:
                    self._debug("[ENGINE] Auto-generated migration: {}", migration.version)
        except Exception as e:
            self._debug("[ENGINE] Autogenerate skipped: {}", e)

        count = manager.upgrade()
        if count > 0:
            self._debug("[ENGINE] Applied {} migration(s)", count)

    async def ensure_migrations_async(self) -> None:
        """
        Auto-run migrations on startup (Async).

        Process:
        1. Initialize migrations system at `migrations_path` if missing.
        2. Check for schema drift compared to last migration.
        3. Auto-generate a new migration file if drift is detected.
        4. Apply all pending migrations (`upgrade head`).
        
        Useful for development environments to keep DB in sync with code automatically.
        """
        from ..migrations import MigrationManager, MigrationConfig

        migrations_path = self.config.migrations_path or "./migrations"

        config = MigrationConfig(
            migrations_path=migrations_path,
            debug=self.config.debug,
            logger=self.config.logger,
        )
        manager = MigrationManager(self, config)

        status = await manager.status_async()
        if not status.initialized:
            await manager.init_async()
            self._debug("[ENGINE] Migrations initialized at {}", migrations_path)

        try:
            diff = await manager._compute_diff_async(context="Startup")
            if diff.has_changes:
                migration = await manager.autogenerate_async("Auto-generated migration")
                if migration:
                    self._debug("[ENGINE] Auto-generated migration: {}", migration.version)
        except Exception as e:
            self._debug("[ENGINE] Autogenerate skipped: {}", e)

        count = await manager.upgrade_async()
        if count > 0:
            self._debug("[ENGINE] Applied {} migration(s)", count)

    def check_schema_drift(self) -> None:
        """
        Check for differences between models and database schema (Sync).

        If differences are found, emits a colored warning to the console/log.
        For async engines, use check_schema_drift_async() instead.
        """
        if self.config.async_:
            self._debug("[ENGINE] Schema drift check skipped for async engine - use check_schema_drift_async()")
            return

        import warnings
        from ..migrations import MigrationManager, MigrationConfig

        migrations_path = self.config.migrations_path or "./migrations"

        config = MigrationConfig(
            migrations_path=migrations_path,
            debug=False,
            auto_detect_changes=True,
        )

        try:
            manager = MigrationManager(self, config)
            diff = manager._compute_diff(context="Drift Check")

            if diff.has_changes:
                changes = []
                for d in diff.new_tables:
                    changes.append(f"+{d.object_name}")
                for d in diff.removed_tables:
                    changes.append(f"-{d.object_name}")
                for d in diff.modified_tables:
                    col_changes = d.details.get("column_changes", [])
                    if col_changes:
                        col_details = []
                        for c in col_changes[:3]:
                            if c["change"] == "type_changed":
                                col_details.append(f"{c['column']}:{c['from']}->{c['to']}")
                            elif c["change"] == "added":
                                col_details.append(f"+{c['column']}")
                            elif c["change"] == "removed":
                                col_details.append(f"-{c['column']}")
                            else:
                                col_details.append(c["column"])
                        changes.append(f"~{d.object_name}({', '.join(col_details)})")
                    else:
                        changes.append(f"~{d.object_name}")

                if len(changes) > 5:
                    changes_str = ", ".join(changes[:5]) + f" (+{len(changes)-5} more)"
                else:
                    changes_str = ", ".join(changes)

                YELLOW = "\033[33m"
                RESET = "\033[0m"
                warnings.warn(
                    f"{YELLOW}[PSQLMODEL] Schema drift detected: {changes_str}. "
                    f"Run 'python -m psqlmodel migrate autogenerate \"msg\"' to create migration.{RESET}",
                    UserWarning,
                    stacklevel=3,
                )
                self._debug("[ENGINE] Schema drift: {}", changes_str)
        except Exception as e:
            self._debug("[ENGINE] Schema drift check skipped: {}", e)

    async def check_schema_drift_async(self) -> None:
        """
        Check for differences between models and database schema (Async).

        If differences are found, emits a colored warning to the console/log.
        """
        import warnings
        from ..migrations import MigrationManager, MigrationConfig

        migrations_path = self.config.migrations_path or "./migrations"

        config = MigrationConfig(
            migrations_path=migrations_path,
            debug=False,
            auto_detect_changes=True,
        )

        try:
            manager = MigrationManager(self, config)
            diff = await manager._compute_diff_async(context="Drift Check")

            if diff.has_changes:
                changes = []
                for d in diff.new_tables:
                    changes.append(f"+{d.object_name}")
                for d in diff.removed_tables:
                    changes.append(f"-{d.object_name}")
                for d in diff.modified_tables:
                    col_changes = d.details.get("column_changes", [])
                    if col_changes:
                        col_details = []
                        for c in col_changes[:3]:
                            if c["change"] == "type_changed":
                                col_details.append(f"{c['column']}:{c['from']}->{c['to']}")
                            elif c["change"] == "added":
                                col_details.append(f"+{c['column']}")
                            elif c["change"] == "removed":
                                col_details.append(f"-{c['column']}")
                            else:
                                col_details.append(c["column"])
                        changes.append(f"~{d.object_name}({', '.join(col_details)})")
                    else:
                        changes.append(f"~{d.object_name}")

                if len(changes) > 5:
                    changes_str = ", ".join(changes[:5]) + f" (+{len(changes)-5} more)"
                else:
                    changes_str = ", ".join(changes)

                YELLOW = "\033[33m"
                RESET = "\033[0m"
                warnings.warn(
                    f"{YELLOW}[PSQLMODEL] Schema drift detected: {changes_str}. "
                    f"Run 'python -m psqlmodel migrate autogenerate \"msg\"' to create migration.{RESET}",
                    UserWarning,
                    stacklevel=3,
                )
                self._debug("[ENGINE] Schema drift: {}", changes_str)
        except Exception as e:
            self._debug("[ENGINE] Schema drift check skipped: {}", e)

    def _ensure_triggers_sync(self) -> None:
        discovered_models = getattr(self, "_discovered_models", [])
        plpython_available = self._check_plpython_available_sync()

        if not plpython_available:
            self._debug("[ENGINE] plpython3u not available, using PL/pgSQL fallback for triggers")
            self._debug("[ENGINE] To enable Python execution in triggers, install: sudo apt-get install postgresql-plpython3-16")

        for model_cls, _ in discovered_models:
            if not hasattr(model_cls, "__triggers__"):
                continue
            for trigger in model_cls.__triggers__:
                try:
                    trigger._use_plpython = plpython_available
                    func_sql, trigger_sql = trigger.to_sql()
                    self._execute_ddl_sync(func_sql)
                    for cmd in trigger_sql.split(";"):
                        cmd = cmd.strip()
                        if cmd:
                            self._execute_ddl_sync(cmd + ";")
                    lang = "plpython3u" if plpython_available else "plpgsql"
                    self._debug("[ENGINE] Created trigger: {} ({})", trigger.trigger_name, lang)
                except Exception as e:
                    self._debug(
                        "[ENGINE] Warning: Failed to create trigger {}: {}",
                        getattr(trigger, "trigger_name", "?"),
                        e,
                    )

    def _check_plpython_available_sync(self) -> bool:
        try:
            dsn = self._build_sync_dsn()
            conn = psycopg.connect(dsn)
            try:
                cur = conn.cursor()
                cur.execute("CREATE EXTENSION IF NOT EXISTS plpython3u;")
                conn.commit()
                cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'plpython3u';")
                result = cur.fetchone()
                cur.close()
                return result is not None
            finally:
                conn.close()
        except Exception:
            return False

    def _execute_ddl_sync(self, sql: str) -> None:
        dsn = self._build_sync_dsn()
        conn = psycopg.connect(dsn)
        try:
            cur = conn.cursor()
            self._debug("[ENGINE] SQL DDL: {}...", sql[:100])
            cur.execute(sql)
            conn.commit()
            cur.close()
        finally:
            conn.close()

    async def _ensure_triggers_async(self) -> None:
        discovered_models = getattr(self, "_discovered_models", [])
        plpython_available = await self._check_plpython_available_async()

        if not plpython_available:
            self._debug("[ENGINE] plpython3u not available, using PL/pgSQL fallback for triggers")
            self._debug("[ENGINE] To enable Python execution in triggers, install: sudo apt-get install postgresql-plpython3-16")

        for model_cls, _ in discovered_models:
            if not hasattr(model_cls, "__triggers__"):
                continue
            for trigger in model_cls.__triggers__:
                try:
                    trigger._use_plpython = plpython_available
                    func_sql, trigger_sql = trigger.to_sql()
                    await self._execute_ddl_async(func_sql)
                    for cmd in trigger_sql.split(";"):
                        cmd = cmd.strip()
                        if cmd:
                            await self._execute_ddl_async(cmd + ";")
                    lang = "plpython3u" if plpython_available else "plpgsql"
                    self._debug("[ENGINE] Created trigger: {} ({})", trigger.trigger_name, lang)
                except Exception as e:
                    self._debug(
                        "[ENGINE] Warning: Failed to create trigger {}: {}",
                        getattr(trigger, "trigger_name", "?"),
                        e,
                    )

    async def _check_plpython_available_async(self) -> bool:
        try:
            conn = await self._get_async_connection()
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS plpython3u;")
                result = await conn.fetchval("SELECT 1 FROM pg_extension WHERE extname = 'plpython3u';")
                return result is not None
            finally:
                await conn.close()
        except Exception:
            return False

    async def _execute_ddl_async(self, sql: str) -> None:
        conn = await self._get_async_connection()
        try:
            self._debug("[ENGINE] SQL DDL (async): {}...", sql[:100])
            await conn.execute(sql)
        finally:
            await conn.close()

    async def _get_async_connection(self):
        dsn = self._build_async_dsn()
        return await asyncpg.connect(dsn)

    # ============================================================
    # Aplicar plan DDL
    # ============================================================
    def apply_ddl_plan(self) -> None:
        """
        Execute the DDL statements prepared by `EnsureDatabaseTables`.
        
        This method connects to the database (sync) and runs the CREATE TABLE/INDEX statements
        in the correct dependency order. It commits the transaction upon success.
        """
        ddl_plan = getattr(self, "_last_ddl_plan", None)
        if not ddl_plan:
            return

        dsn = self._build_sync_dsn()
        self._debug("[ENGINE] CONNECT (DDL) DSN={}", self._mask_dsn(dsn))
        conn = psycopg.connect(dsn)
        try:
            cur = conn.cursor()
            for sql_statement in ddl_plan:
                self._debug("[ENGINE] SQL DDL PLAN: {}", sql_statement)
                cur.execute(sql_statement)
            conn.commit()
            cur.close()
        finally:
            conn.close()

    async def apply_ddl_plan_async(self) -> None:
        """
        Execute the DDL statements prepared by `EnsureDatabaseTables` (Async).
        
        This method connects to the database (async) and runs the CREATE TABLE/INDEX statements
        sequentially.
        """
        ddl_plan = getattr(self, "_last_ddl_plan", None)
        if not ddl_plan:
            return

        conn = await self._get_async_connection()
        try:
            for sql_statement in ddl_plan:
                self._debug("[ENGINE] SQL DDL PLAN (async): {}", sql_statement)
                await conn.execute(sql_statement)
        finally:
            await conn.close()


# ============================================================
# EnsureDatabaseTables – detección de modelos @table y DDL
# ============================================================

def _iter_python_files(root_dir: str):
    IGNORE_DIRS = {
        "__pycache__",
        ".venv",
        "venv",
        ".env",
        "env",
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        ".tox",
        ".nox",
        ".pytest_cache",
        ".mypy_cache",
        "dist",
        "build",
        "*.egg-info",
        "site-packages",
    }

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [
            d for d in dirnames if d not in IGNORE_DIRS and not d.endswith(".egg-info")
        ]
        for name in filenames:
            if name.endswith(".py") and not name.startswith("."):
                yield os.path.join(dirpath, name)


def _import_module_from_path(path: str):
    import sys
    main_file = os.path.abspath(sys.argv[0]) if sys.argv else None
    if main_file and os.path.abspath(path) == main_file:
        return sys.modules.get("__main__")

    abs_path = os.path.abspath(path)
    for mod_name, mod in sys.modules.items():
        if hasattr(mod, "__file__") and mod.__file__:
            if os.path.abspath(mod.__file__) == abs_path:
                return mod

    unique_name = f"_psqlmodel_import_{abs(hash(abs_path))}"

    spec = importlib.util.spec_from_file_location(unique_name, path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)  # type: ignore
        except Exception:
            return None
        return module
    return None


def _iter_models_in_module(module):
    for attr_name in dir(module):
        obj = getattr(module, attr_name, None)
        if isinstance(obj, type) and issubclass(obj, PSQLModel):
            if obj is PSQLModel:
                continue
            if hasattr(obj, "__tablename__") and hasattr(obj, "__columns__"):
                table_name = getattr(obj, "__tablename__", None)
                if not table_name:
                    continue
                yield obj


def EnsureDatabaseTables(engine: Engine) -> None:
    """
    Discover all PSQLModel subclasses and prepare the DDL plan.
    
    This function performs auto-discovery of models by:
    1. Walking the project directory (or `models_path` if configured).
    2. Importing Python files to trigger model registration.
    3. Collecting all subclasses of PSQLModel that have a `__tablename__`.
    4. Checking for duplicate table names across different files.
    5. Sorting tables based on foreign key dependencies to ensure correct creation order.
    6. Generating DDL (Create Schema, Create Table) using `generate_table_ddl`.
    7. Generating junction tables for Many-to-Many relationships automatically.
    
    The resulting SQL statements are stored in `engine._last_ddl_plan` for execution via `apply_ddl_plan`.
    
    Args:
        engine (Engine): The engine instance to configure.
        
    Raises:
        ValueError: If multiple models define the same table name.
    """
    from ..orm.table import generate_table_ddl
    import sys
    import re

    main_file = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else None
    models: list[tuple[Any, str]] = []
    table_registry: dict = {}

    if engine.config.models_path:
        # Normalize to list
        paths = engine.config.models_path
        if isinstance(paths, str):
            paths = [paths]
        
        for path in paths:
            if path in ("__main__", ".", "__file__"):
                if main_file and os.path.isfile(main_file):
                    module = _import_module_from_path(main_file)
                    if module:
                        for model_cls in _iter_models_in_module(module):
                            models.append((model_cls, main_file))
            elif os.path.isdir(path):
                for fpath in _iter_python_files(path):
                    module = _import_module_from_path(fpath)
                    if not module:
                        continue
                    for model_cls in _iter_models_in_module(module):
                        models.append((model_cls, fpath))
            else:
                module = _import_module_from_path(path)
                if module:
                    for model_cls in _iter_models_in_module(module):
                        models.append((model_cls, path))
    else:
        project_root = os.getcwd()
        for fpath in _iter_python_files(project_root):
            module = _import_module_from_path(fpath)
            if not module:
                continue
            for model_cls in _iter_models_in_module(module):
                models.append((model_cls, fpath))

    # Conflictos
    for model_cls, fpath in models:
        schema = getattr(model_cls, "__schema__", "public") or "public"
        table_name = getattr(model_cls, "__tablename__", None)
        if not table_name:
            continue
        key = (schema, table_name)
        table_registry.setdefault(key, []).append((model_cls, fpath))

    conflicts = {k: v for k, v in table_registry.items() if len(v) > 1}
    if conflicts:
        if engine.config.ignore_duplicates:
            # Keep only first reference for each table
            for key in conflicts:
                first_model, first_path = table_registry[key][0]
                table_registry[key] = [(first_model, first_path)]
            # Rebuild models list with only first references
            seen_tables = set()
            filtered_models = []
            for model_cls, fpath in models:
                schema = getattr(model_cls, "__schema__", "public") or "public"
                table_name = getattr(model_cls, "__tablename__", None)
                if not table_name:
                    continue
                key = (schema, table_name)
                if key not in seen_tables:
                    seen_tables.add(key)
                    filtered_models.append((model_cls, fpath))
            models = filtered_models
        else:
            error_lines = [
                "ERROR: Multiple models with the same table name detected.",
                "This can cause unexpected behavior when creating tables.",
                "",
            ]
            for (schema, table_name), model_list in conflicts.items():
                error_lines.append(f"  Table '{schema}.{table_name}' defined in:")
                for model_cls, fpath in model_list:
                    error_lines.append(f"    - {model_cls.__name__} in {fpath}")
            error_lines.append("")
            error_lines.append("SOLUTION: Use 'ignore_duplicates=True' in create_engine() to use first reference,")
            error_lines.append("          or use 'models_path' to specify specific model files.")
            raise ValueError("\n".join(error_lines))

    # Schemas
    schemas = set()
    for model_cls, _ in models:
        schema = getattr(model_cls, "__schema__", "public") or "public"
        if schema:
            if not _is_valid_identifier(schema):
                raise ValueError(f"Invalid schema name '{schema}' (must be a valid SQL identifier)")
            schemas.add(schema)

    ddl_statements = [f"CREATE SCHEMA IF NOT EXISTS {schema};" for schema in schemas]

    # Dependencias
    table_keys = []
    table_ddls: dict[tuple[str, str], list[str]] = {}
    table_deps: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for model_cls, fpath in models:
        schema = getattr(model_cls, "__schema__", "public") or "public"
        table_name = getattr(model_cls, "__tablename__", None)
        if not table_name:
            continue
        key = (schema, table_name)
        table_keys.append(key)
        try:
            statements = generate_table_ddl(model_cls)
            statements = [s for s in statements if not s.startswith("CREATE SCHEMA")]
            deps = set()
            for stmt in statements:
                if stmt.startswith("CREATE TABLE"):
                    # Match REFERENCES schema.table(col) or REFERENCES table(col)
                    # Pattern 1: REFERENCES schema.table(col)
                    for m in re.finditer(r"REFERENCES ([\w]+)\.([\w]+)\(", stmt):
                        dep_schema, dep_table = m.groups()
                        deps.add((dep_schema, dep_table))
                    # Pattern 2: REFERENCES table(col) - assume public schema
                    for m in re.finditer(r"REFERENCES (\w+)\((?!\w+\.)", stmt):
                        dep_table = m.group(1)
                        # Only add if not already matched with schema
                        if not any(d[1] == dep_table for d in deps):
                            deps.add(("public", dep_table))
            table_ddls[key] = statements
            table_deps[key] = deps
        except Exception:
            table_ddls[key] = []
            table_deps[key] = set()

    sorted_keys: list[tuple[str, str]] = []
    visited: set[tuple[str, str]] = set()
    in_progress: set[tuple[str, str]] = set()  # Track nodes being visited (cycle detection)

    def visit(key):
        if key in visited:
            return
        if key in in_progress:
            # Circular dependency detected - skip to avoid infinite recursion
            return
        in_progress.add(key)
        for dep in table_deps.get(key, set()):
            if dep in table_ddls:
                visit(dep)
        in_progress.discard(key)
        visited.add(key)
        sorted_keys.append(key)

    for key in table_keys:
        visit(key)

    # Separate CREATE TABLE statements from FK constraint statements
    # This ensures all tables exist before FK constraints are added
    # FK statements can be: 
    #   - "ALTER TABLE ... FOREIGN KEY" 
    #   - "DO $$ ... ALTER TABLE ... FOREIGN KEY ..."
    create_statements = []
    fk_statements = []
    
    for key in sorted_keys:
        for stmt in table_ddls.get(key, []):
            is_fk_stmt = (
                (stmt.startswith("ALTER TABLE") and "FOREIGN KEY" in stmt) or
                (stmt.startswith("DO $$") and "FOREIGN KEY" in stmt)
            )
            if is_fk_stmt:
                fk_statements.append(stmt)
            else:
                create_statements.append(stmt)
    
    ddl_statements.extend(create_statements)

    # Junction tables (many-to-many)
    junction_tables = _generate_junction_tables(models)
    ddl_statements.extend(junction_tables)
    
    # Add FK constraints LAST after all tables exist
    ddl_statements.extend(fk_statements)

    engine._last_ddl_plan = ddl_statements  # type: ignore[attr-defined]
    engine._discovered_models = models  # type: ignore[attr-defined]


def _generate_junction_tables(models: list) -> list[str]:
    junction_ddl = []
    seen_junctions = set()

    for model_cls, _ in models:
        if not hasattr(model_cls, "__relations__"):
            continue

        for rel_name, relationship in model_cls.__relations__.items():
            if not hasattr(relationship, "secondary") or not relationship.secondary:
                continue

            junction_table = relationship.secondary
            if junction_table in seen_junctions:
                continue
            seen_junctions.add(junction_table)

            _validate_qualified_name(junction_table, kind="junction table")

            relationship._detect_relationship_type()
            if relationship._relationship_type != "many_to_many":
                continue

            owner_table = getattr(model_cls, "__tablename__", None)
            if not owner_table:
                continue

            target_model = relationship._resolve_target()
            if not target_model:
                continue

            target_table = getattr(target_model, "__tablename__", None)
            if not target_table:
                continue

            owner_schema = getattr(model_cls, "__schema__", "public") or "public"
            target_schema = getattr(target_model, "__schema__", "public") or "public"
            if not _is_valid_identifier(owner_schema):
                raise ValueError(f"Invalid schema name '{owner_schema}' in model {model_cls.__name__}")
            if not _is_valid_identifier(target_schema):
                raise ValueError(f"Invalid schema name '{target_schema}' in model {target_model.__name__}")

            owner_full_table = f"{owner_schema}.{owner_table}"
            target_full_table = f"{target_schema}.{target_table}"

            owner_pk_col = list(model_cls.__columns__.keys())[0]
            target_pk_col = list(target_model.__columns__.keys())[0]

            owner_pk_type = model_cls.__columns__[owner_pk_col].type_hint
            target_pk_type = target_model.__columns__[target_pk_col].type_hint

            owner_sql_type = _python_type_to_sql(owner_pk_type)
            target_sql_type = _python_type_to_sql(target_pk_type)

            owner_fk = f"{_to_singular(owner_table)}_id"
            target_fk = f"{_to_singular(target_table)}_id"

            if not _is_valid_identifier(owner_fk) or not _is_valid_identifier(target_fk):
                raise ValueError(f"Invalid junction FK column names: {owner_fk}, {target_fk}")

            ddl = f"""CREATE TABLE IF NOT EXISTS {junction_table} (
    {owner_fk} {owner_sql_type} NOT NULL,
    {target_fk} {target_sql_type} NOT NULL,
    PRIMARY KEY ({owner_fk}, {target_fk}),
    FOREIGN KEY ({owner_fk}) REFERENCES {owner_full_table}({owner_pk_col}) ON DELETE CASCADE,
    FOREIGN KEY ({target_fk}) REFERENCES {target_full_table}({target_pk_col}) ON DELETE CASCADE
);"""
            junction_ddl.append(ddl)

    return junction_ddl


def _python_type_to_sql(python_type) -> str:
    """Best-effort mapping for junction tables (PK types)."""
    if python_type is None:
        return "INTEGER"

    # Unwrap Optional/Union
    try:
        from typing import get_origin, get_args, Union
        origin = get_origin(python_type)
        if origin is Union:
            args = [a for a in get_args(python_type) if a is not type(None)]  # noqa
            python_type = args[0] if args else python_type
    except Exception:
        pass

    if hasattr(python_type, "__name__"):
        type_name = python_type.__name__
    elif hasattr(python_type, "__class__"):
        type_name = python_type.__class__.__name__
    else:
        type_name = str(python_type)

    type_name = type_name.lower()

    type_map = {
        "uuid": "UUID",
        "int": "INTEGER",
        "integer": "INTEGER",
        "bigint": "BIGINT",
        "smallint": "SMALLINT",
        "serial": "SERIAL",
        "bigserial": "BIGSERIAL",
        "str": "TEXT",
        "string": "TEXT",
        "varchar": "VARCHAR",
        "text": "TEXT",
        "bool": "BOOLEAN",
        "boolean": "BOOLEAN",
        "datetime": "TIMESTAMPTZ",
        "timestamptz": "TIMESTAMP WITH TIME ZONE",
    }

    return type_map.get(type_name, "INTEGER")


def _to_singular(table_name: str) -> str:
    if table_name.endswith("s"):
        return table_name[:-1]
    return table_name


# ============================================================
# create_engine – punto de entrada unificado
# ============================================================

def create_engine(
    dsn: Optional[str] = None,
    *,
    username: Optional[str] = None,
    password: Optional[str] = None,
    host: str = "localhost",
    port: int = 5432,
    database: Optional[str] = None,
    pool_size: int = 20,
    auto_adjust_pool_size: bool = False,
    max_pool_size: Optional[int] = None,
    connection_timeout: Optional[float] = None,
    ensure_database: bool = True,
    ensure_tables: bool = True,
    auto_startup: bool = True,
    ensure_migrations: bool = False,
    check_schema_drift: bool = True,
    migrations_path: Optional[str] = None,
    models_path: Optional[Union[str, List[str]]] = None,
    debug: bool = False,
    # Health-check options
    health_check_enabled: bool = False,
    health_check_interval: float = 30.0,
    health_check_retries: int = 1,
    health_check_timeout: float = 5.0,
    # Lifecycle options
    pool_pre_ping: bool = False,
    pool_recycle: Optional[float] = None,
    max_retries: int = 0,
    retry_delay: float = 0.0,
    # Logger opcional
    logger: Optional[Callable[[str], None]] = None,
    # Toggles de métricas / tracer / logging estructurado
    enable_metrics: bool = True,
    enable_query_tracer: bool = True,
    query_trace_size: int = 200,
    enable_structured_logging: bool = True,
    # Model discovery options
    ignore_duplicates: bool = False,
    # Pool shutdown options
    pool_close_timeout: float = 5.0,
) -> Engine:
    """Create a synchronous database Engine.
    
    If auto_startup=True (default), runs startup_sync() immediately.
    If auto_startup=False, startup must be called manually or will happen
    lazily on first Session use.
    
    For async engines, use create_async_engine() instead.
    """
    config = EngineConfig(
        dsn=dsn,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
        async_=False,  # Sync engine
        pool_size=pool_size,
        auto_adjust_pool_size=auto_adjust_pool_size,
        max_pool_size=max_pool_size,
        connection_timeout=connection_timeout,
        ensure_database=ensure_database,
        ensure_tables=ensure_tables,
        auto_startup=auto_startup,
        ensure_migrations=ensure_migrations,
        check_schema_drift=check_schema_drift,
        migrations_path=migrations_path,
        models_path=models_path,
        debug=debug,
        logger=logger,
        health_check_enabled=health_check_enabled,
        health_check_interval=health_check_interval,
        health_check_retries=health_check_retries,
        health_check_timeout=health_check_timeout,
        pool_pre_ping=pool_pre_ping,
        pool_recycle=pool_recycle,
        max_retries=max_retries,
        retry_delay=retry_delay,
        enable_metrics=enable_metrics,
        enable_query_tracer=enable_query_tracer,
        query_trace_size=query_trace_size,
        enable_structured_logging=enable_structured_logging,
        ignore_duplicates=ignore_duplicates,
        pool_close_timeout=pool_close_timeout,
    )

    engine = Engine(config=config)

    if auto_startup:
        engine.startup_sync()

    return engine


def create_async_engine(
    dsn: Optional[str] = None,
    *,
    username: Optional[str] = None,
    password: Optional[str] = None,
    host: str = "localhost",
    port: int = 5432,
    database: Optional[str] = None,
    pool_size: int = 20,
    auto_adjust_pool_size: bool = False,
    max_pool_size: Optional[int] = None,
    connection_timeout: Optional[float] = None,
    ensure_database: bool = True,
    ensure_tables: bool = True,
    auto_startup: bool = True,
    ensure_migrations: bool = False,
    check_schema_drift: bool = True,
    migrations_path: Optional[str] = None,
    models_path: Optional[Union[str, List[str]]] = None,
    debug: bool = False,
    # Health-check options
    health_check_enabled: bool = False,
    health_check_interval: float = 30.0,
    health_check_retries: int = 1,
    health_check_timeout: float = 5.0,
    # Lifecycle options
    pool_pre_ping: bool = False,
    pool_recycle: Optional[float] = None,
    max_retries: int = 0,
    retry_delay: float = 0.0,
    # Logger opcional
    logger: Optional[Callable[[str], None]] = None,
    # Toggles de métricas / tracer / logging estructurado
    enable_metrics: bool = True,
    enable_query_tracer: bool = True,
    query_trace_size: int = 200,
    enable_structured_logging: bool = True,
    # Model discovery options
    ignore_duplicates: bool = False,
    # Pool shutdown options
    pool_close_timeout: float = 5.0,
) -> Engine:
    """Create an asynchronous database Engine.
    
    This is a synchronous function that creates an async-configured engine.
    
    If auto_startup=True (default), startup will happen lazily on first
    AsyncSession use, or you can call await engine.startup_async() explicitly.
    
    If auto_startup=False, you must call await engine.startup_async() manually
    before using the engine, or ensure database/tables won't be checked.
    
    For sync engines, use create_engine() instead.
    """
    config = EngineConfig(
        dsn=dsn,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
        async_=True,  # Async engine
        pool_size=pool_size,
        auto_adjust_pool_size=auto_adjust_pool_size,
        max_pool_size=max_pool_size,
        connection_timeout=connection_timeout,
        ensure_database=ensure_database,
        ensure_tables=ensure_tables,
        auto_startup=auto_startup,
        ensure_migrations=ensure_migrations,
        check_schema_drift=check_schema_drift,
        migrations_path=migrations_path,
        models_path=models_path,
        debug=debug,
        logger=logger,
        health_check_enabled=health_check_enabled,
        health_check_interval=health_check_interval,
        health_check_retries=health_check_retries,
        health_check_timeout=health_check_timeout,
        pool_pre_ping=pool_pre_ping,
        pool_recycle=pool_recycle,
        max_retries=max_retries,
        retry_delay=retry_delay,
        enable_metrics=enable_metrics,
        enable_query_tracer=enable_query_tracer,
        query_trace_size=query_trace_size,
        enable_structured_logging=enable_structured_logging,
        ignore_duplicates=ignore_duplicates,
        pool_close_timeout=pool_close_timeout,
    )

    return Engine(config=config)
