"""
Transaction manager y context manager para el ORM.

Funciones principales:
- Manejo de transacciones sync/async (BEGIN, COMMIT, ROLLBACK)
- Savepoints y transacciones anidadas
- Bulk operations (insert/update/delete masivo)
- Unit of Work y dirty tracking
- Hooks y eventos (before_commit, after_commit, etc.)
- Validación y serialización de modelos
- Gestión de errores y retry

Ejemplo de uso (sync):

from psqlmodel.engine import create_engine
from psqlmodel.model import PSQLModel
from psqlmodel.transactions import Transaction

engine = create_engine(...)

class User(PSQLModel):
    ...

with Transaction(engine) as tx:
    user = User(name="Alice", age=30)
    tx.register(user, op="insert")
    tx.savepoint("sp1")
    # ...
    tx.bulk_insert([user1, user2])

Ejemplo de uso (async, estilo clásico):

from psqlmodel.engine import create_engine
from psqlmodel.model import PSQLModel
from psqlmodel.transactions import Transaction, AsyncTransaction

engine = create_engine(..., async_=True)

class User(PSQLModel):
    ...

# Opción 1 (compatible con versiones anteriores)
async def main():
    async with Transaction(engine) as tx:
        user = User(name="Bob", age=25)
        tx.register(user, op="insert")
        await tx.savepoint_async("sp1")
        await tx.bulk_insert_async([user1, user2])

# Opción 2 (recomendada, API limpia)
async def main():
    async with AsyncTransaction(engine) as tx:
        user = User(name="Bob", age=25)
        tx.register(user, op="insert")
        await tx.savepoint("sp1")
        await tx.bulk_insert([user1, user2])
"""

from __future__ import annotations

from typing import Any, Optional, List, Dict, Tuple

import asyncio
import time
import re
import threading

import psycopg

from .engine import Engine
from ..query.crud import build_insert_sql, build_update_sql
from ..orm.model import PSQLModel


# ============================================================
# Internals: nested TX support (savepoints) without breaking API
# ============================================================

# Sync: thread-local stack per Engine (id(engine) -> list of frames)
# frame = {"conn": <psycopg conn>, "savepoint": Optional[str]}
_SYNC_LOCAL = threading.local()

# Async: context-var-like behavior (per task). We'll keep it simple with a dict stored on the task.
# We avoid importing contextvars to reduce surface; asyncio tasks already isolate attributes.


def _get_sync_stack() -> Dict[int, List[Dict[str, Any]]]:
    stk = getattr(_SYNC_LOCAL, "stack", None)
    if stk is None:
        stk = {}
        setattr(_SYNC_LOCAL, "stack", stk)
    return stk


def _get_async_stack() -> Dict[int, List[Dict[str, Any]]]:
    task = asyncio.current_task()
    if task is None:
        # Fallback: global-ish, but async without a task is rare; keep isolated in module attribute
        stk = getattr(_SYNC_LOCAL, "_async_fallback_stack", None)
        if stk is None:
            stk = {}
            setattr(_SYNC_LOCAL, "_async_fallback_stack", stk)
        return stk

    stk = getattr(task, "_psqlmodel_tx_stack", None)
    if stk is None:
        stk = {}
        setattr(task, "_psqlmodel_tx_stack", stk)
    return stk


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(name: str, *, kind: str = "identifier") -> str:
    if not name or not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid {kind}: {name!r}. Use [A-Za-z_][A-Za-z0-9_]*")
    return name


def _qualify_table(default_schema: str, table: str) -> str:
    # If already qualified (schema.table), respect it.
    if "." in (table or ""):
        return table
    return f"{default_schema}.{table}"


class Transaction:
    # --- Hooks y eventos transacción ---
    def add_hook(self, event: str, func):
        """Registrar un hook para un evento ('before_commit', 'after_commit', etc.)."""
        if not hasattr(self, "_hooks"):
            self._hooks = {}
        self._hooks.setdefault(event, []).append(func)

    def _run_hooks(self, event: str):
        for func in getattr(self, "_hooks", {}).get(event, []):
            func(self)

    async def _run_hooks_async(self, event: str):
        for func in getattr(self, "_hooks", {}).get(event, []):
            res = func(self)
            if asyncio.iscoroutine(res):
                await res

    # --- Gestión de errores y retry genérico (no SQL) ---
    def _retry_operation(
        self,
        func,
        *args,
        retries: int = 3,
        retry_exceptions: tuple = (Exception,),
        **kwargs,
    ):
        """Ejecuta una operación con reintentos automáticos en caso de error (no SQL)."""
        last_exc: Optional[BaseException] = None
        attempts = max(1, int(retries or 1))
        for attempt in range(attempts):
            try:
                return func(*args, **kwargs)
            except retry_exceptions as exc:
                last_exc = exc
                time.sleep(0.1 * (attempt + 1))  # backoff simple
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Retry operation failed without exception (unexpected)")

    async def _retry_operation_async(
        self,
        func,
        *args,
        retries: int = 3,
        retry_exceptions: tuple = (Exception,),
        **kwargs,
    ):
        """Ejecuta una operación async con reintentos automáticos en caso de error (no SQL)."""
        last_exc: Optional[BaseException] = None
        attempts = max(1, int(retries or 1))
        for attempt in range(attempts):
            try:
                return await func(*args, **kwargs)
            except retry_exceptions as exc:
                last_exc = exc
                await asyncio.sleep(0.1 * (attempt + 1))
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Async retry operation failed without exception (unexpected)")

    # ============================================================
    # Helpers internos: ejecutar SQL dentro de la TX usando
    # middlewares, hooks, metrics y tracer del Engine.
    # ============================================================
    def _execute_sql_in_tx_sync(
        self,
        sql: str,
        params: Optional[List[Any]] = None,
        *,
        retries: Optional[int] = None,
    ):
        """Ejecutar un SQL dentro de la transacción (sync) usando el pipeline del Engine."""
        if self._conn is None:
            raise RuntimeError("No active transaction")

        engine: Engine = self.engine

        def final(s: str, p: Any):
            # Copia de _execute_core_sync pero usando self._conn
            engine._debug("[ENGINE] SQL: {} {}", s, p)

            # Hooks before_execute
            for h in list(getattr(engine, "_hooks", {}).get("before_execute", [])):  # type: ignore[attr-defined]
                try:
                    h(s, p)
                except Exception:
                    engine._debug("[ENGINE] before_execute hook error")

            cur = self._conn.cursor()
            try:
                cur.execute(s, p or None)
                try:
                    rows = cur.fetchall()
                except psycopg.ProgrammingError:
                    rows = None
            finally:
                cur.close()

            # Hooks after_execute
            for h in list(getattr(engine, "_hooks", {}).get("after_execute", [])):  # type: ignore[attr-defined]
                try:
                    h(s, rows)
                except Exception:
                    engine._debug("[ENGINE] after_execute hook error")
            return rows

        # Construir cadena de middlewares igual que Engine._run_sync_pipeline
        import signal

        chain = final

        # IMPORTANT: igual que Engine -> sort asc; higher priority wraps outermost
        middlewares = sorted(
            getattr(engine, "_middlewares_sync", []),  # type: ignore[attr-defined]
            key=lambda x: x[0],
        )

        for _priority, mw_func, timeout in middlewares:
            prev = chain

            def make_mw(mw, prev_func, mw_timeout):
                def _wrapped(s, p):
                    # Igual que Engine: evitar señales en hilos secundarios o plataformas sin setitimer.
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

        # Retry: si retries es None, usamos config.max_retries como en Engine.
        if retries is None:
            attempts = max(0, int(getattr(engine.config, "max_retries", 0) or 0))
        else:
            # Compat con versión anterior: retries = número TOTAL de intentos.
            attempts = max(0, int(retries) - 1)

        delay = float(getattr(engine.config, "retry_delay", 0.0) or 0.0)

        last_exc: Optional[BaseException] = None
        for i in range(attempts + 1):
            try:
                return chain(sql, params)
            except Exception as e:
                last_exc = e
                if i < attempts and delay > 0:
                    time.sleep(delay)
                    continue
                raise last_exc

    async def _execute_sql_in_tx_async(
        self,
        sql: str,
        params: Optional[List[Any]] = None,
        *,
        retries: Optional[int] = None,
    ):
        """Ejecutar un SQL dentro de la transacción (async) usando el pipeline del Engine."""
        if self._conn is None:
            raise RuntimeError("No active transaction")

        engine: Engine = self.engine

        async def final(s: str, p: Any):
            # Copia de _execute_core_async pero usando self._conn
            # Hooks before_execute
            for h in list(getattr(engine, "_hooks", {}).get("before_execute", [])):  # type: ignore[attr-defined]
                try:
                    res = h(s, p)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception:
                    engine._debug("[ENGINE] before_execute hook error")

            # Convert psycopg-style %s placeholders to asyncpg-style $1, $2, $3
            if "%s" in s:
                idx = 1
                while "%s" in s:
                    s = s.replace("%s", f"${idx}", 1)
                    idx += 1

            # asyncpg requires jsonb as JSON string, convert dict/list params
            if p:
                from decimal import Decimal
                from uuid import UUID
                from datetime import datetime, date
                import json as json_stdlib
                
                def convert_special_types(obj):
                    if isinstance(obj, dict):
                        return {k: convert_special_types(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_special_types(v) for v in obj]
                    elif isinstance(obj, Decimal):
                        return float(obj)
                    elif isinstance(obj, UUID):
                        return str(obj)
                    elif isinstance(obj, (datetime, date)):
                        return obj.isoformat()
                    return obj
                
                processed_params = []
                for val in p:
                    if isinstance(val, (dict, list)):
                        # Convert special types then serialize to JSON string
                        val = convert_special_types(val)
                        processed_params.append(json_stdlib.dumps(val))
                    else:
                        processed_params.append(val)
                p = processed_params

            conn = self._conn

            # Compat: intenta fetch (como Engine) pero cae a execute si no devuelve filas.
            # Esto evita crashes en INSERT/UPDATE sin RETURNING.
            stmt_type = (s.strip().split(None, 1)[0].upper() if s and s.strip() else "UNKNOWN")
            expects_rows = ("RETURNING" in s.upper()) or (stmt_type in {"SELECT", "SHOW", "WITH"})

            rows = None
            if expects_rows:
                stmt = await conn.prepare(s)
                rows = await stmt.fetch(*p) if p else await stmt.fetch()
            else:
                # para DDL/DML sin RETURNING
                await conn.execute(s, *(p or []))
                rows = None

            # Hooks after_execute
            for h in list(getattr(engine, "_hooks", {}).get("after_execute", [])):  # type: ignore[attr-defined]
                try:
                    res = h(s, rows)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception:
                    engine._debug("[ENGINE] after_execute hook error")
            return rows

        # Cadena de middlewares igual que Engine._run_async_pipeline
        chain = final

        # IMPORTANT: igual que Engine -> sort asc; higher priority wraps outermost
        middlewares = sorted(
            getattr(engine, "_middlewares_async", []),  # type: ignore[attr-defined]
            key=lambda x: x[0],
        )

        for _priority, mw_func, timeout in middlewares:
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

        if retries is None:
            attempts = max(0, int(getattr(engine.config, "max_retries", 0) or 0))
        else:
            # Compat con versión anterior: retries = número TOTAL de intentos.
            attempts = max(0, int(retries) - 1)

        delay = float(getattr(engine.config, "retry_delay", 0.0) or 0.0)

        last_exc: Optional[BaseException] = None
        for i in range(attempts + 1):
            try:
                return await chain(sql, params)
            except Exception as e:
                last_exc = e
                if i < attempts and delay > 0:
                    await asyncio.sleep(delay)
                    continue
                raise last_exc

    # --- Ejecutar SQL con retry explícito (compat) ---
    def execute_with_retry(
        self,
        sql: str,
        params: Optional[List[Any]] = None,
        retries: int = 3,
    ) -> None:
        """Ejecuta una sentencia SQL con reintentos automáticos (sync).

        Compatibilidad:
        - La firma se mantiene igual.
        - `retries` sigue siendo el número TOTAL de intentos (3 => hasta 3 intentos).
        """
        if self._conn is None:
            raise RuntimeError("No active transaction")
        self._execute_sql_in_tx_sync(sql, params or None, retries=retries)

    async def execute_with_retry_async(
        self,
        sql: str,
        params: Optional[List[Any]] = None,
        retries: int = 3,
    ) -> None:
        """Ejecuta una sentencia SQL con reintentos automáticos (async)."""
        if self._conn is None:
            raise RuntimeError("No active transaction")
        await self._execute_sql_in_tx_async(sql, params or None, retries=retries)

    # --- Bulk operations ---
    def bulk_insert(self, models: list) -> None:
        """Insertar múltiples modelos en una sola operación (sync)."""
        if self._conn is None:
            raise RuntimeError("No active transaction")
        if not models:
            return
        for model in models:
            sql, values, returning_pk = build_insert_sql(model)
            result = self._execute_sql_in_tx_sync(sql, list(values))
            # Populate returned serial ID if available
            if returning_pk and result:
                try:
                    if hasattr(result, '__iter__') and len(result) > 0:
                        row = result[0]
                        if isinstance(row, dict):
                            setattr(model, returning_pk, row.get(returning_pk))
                        elif hasattr(row, returning_pk):
                            setattr(model, returning_pk, getattr(row, returning_pk))
                        elif hasattr(row, '__getitem__'):
                            setattr(model, returning_pk, row[0])
                except Exception:
                    pass

    def bulk_update(self, models: list) -> None:
        """Actualizar múltiples modelos en una sola operación (sync)."""
        if self._conn is None:
            raise RuntimeError("No active transaction")
        if not models:
            return
        for model in models:
            dirty = getattr(model, "dirty_fields", getattr(model, "_dirty_fields", {}))
            sql, values = build_update_sql(model, dirty)
            if sql:
                self._execute_sql_in_tx_sync(sql, list(values))

    async def bulk_insert_async(self, models: list) -> None:
        """Insertar múltiples modelos en una sola operación (async)."""
        if self._conn is None:
            raise RuntimeError("No active transaction")
        if not models:
            return
        for model in models:
            sql, values, returning_pk = build_insert_sql(model, style="asyncpg")
            result = await self._execute_sql_in_tx_async(sql, list(values))
            # Populate returned serial ID if available
            if returning_pk and result:
                try:
                    if hasattr(result, '__iter__') and len(result) > 0:
                        row = result[0]
                        if isinstance(row, dict):
                            setattr(model, returning_pk, row.get(returning_pk))
                        elif hasattr(row, returning_pk):
                            setattr(model, returning_pk, getattr(row, returning_pk))
                        elif hasattr(row, '__getitem__'):
                            setattr(model, returning_pk, row[0])
                except Exception:
                    pass

    async def bulk_update_async(self, models: list) -> None:
        """Actualizar múltiples modelos en una sola operación (async)."""
        if self._conn is None:
            raise RuntimeError("No active transaction")
        if not models:
            return
        for model in models:
            dirty = getattr(model, "dirty_fields", getattr(model, "_dirty_fields", {}))
            sql, values = build_update_sql(model, dirty, style="asyncpg")
            if sql:
                await self._execute_sql_in_tx_async(sql, list(values))

    # --- Savepoints y transacciones anidadas ---
    def savepoint(self, name: Optional[str] = None) -> str:
        """Crear un savepoint con nombre único o dado (sync)."""
        if self._conn is None:
            raise RuntimeError("No active transaction")
        if name is None:
            import uuid
            name = f"sp_{uuid.uuid4().hex[:8]}"
        _validate_identifier(name, kind="savepoint name")
        cur = self._conn.cursor()
        try:
            cur.execute(f"SAVEPOINT {name}")
        finally:
            cur.close()
        self.engine._debug("[TX] SAVEPOINT {}", name)
        return name

    def rollback_to_savepoint(self, name: str) -> None:
        """Hacer rollback parcial a un savepoint (sync)."""
        if self._conn is None:
            raise RuntimeError("No active transaction")
        _validate_identifier(name, kind="savepoint name")
        cur = self._conn.cursor()
        try:
            cur.execute(f"ROLLBACK TO SAVEPOINT {name}")
        finally:
            cur.close()
        self.engine._debug("[TX] ROLLBACK TO SAVEPOINT {}", name)

    def _release_savepoint(self, name: str) -> None:
        """Release savepoint (sync). Internal helper for nested TX."""
        if self._conn is None:
            raise RuntimeError("No active transaction")
        _validate_identifier(name, kind="savepoint name")
        cur = self._conn.cursor()
        try:
            cur.execute(f"RELEASE SAVEPOINT {name}")
        finally:
            cur.close()
        self.engine._debug("[TX] RELEASE SAVEPOINT {}", name)

    async def savepoint_async(self, name: Optional[str] = None) -> str:
        """Crear un savepoint en modo async."""
        if self._conn is None:
            raise RuntimeError("No active transaction")
        if name is None:
            import uuid
            name = f"sp_{uuid.uuid4().hex[:8]}"
        _validate_identifier(name, kind="savepoint name")
        await self._conn.execute(f"SAVEPOINT {name}")
        self.engine._debug("[TX] SAVEPOINT (async) {}", name)
        return name

    async def rollback_to_savepoint_async(self, name: str) -> None:
        """Hacer rollback parcial a un savepoint en modo async."""
        if self._conn is None:
            raise RuntimeError("No active transaction")
        _validate_identifier(name, kind="savepoint name")
        await self._conn.execute(f"ROLLBACK TO SAVEPOINT {name}")
        self.engine._debug("[TX] ROLLBACK TO SAVEPOINT (async) {}", name)

    async def _release_savepoint_async(self, name: str) -> None:
        """Release savepoint (async). Internal helper for nested TX."""
        if self._conn is None:
            raise RuntimeError("No active transaction")
        _validate_identifier(name, kind="savepoint name")
        await self._conn.execute(f"RELEASE SAVEPOINT {name}")
        self.engine._debug("[TX] RELEASE SAVEPOINT (async) {}", name)

    # --- Paralelismo delegando al Engine (lecturas fuera de la TX) ---
    def parallel_execute(self, tasks: list[Any], *, max_workers: Optional[int] = None) -> list[Any]:
        """
        Ejecutar múltiples tareas en paralelo usando el Engine (modo sync).

        IMPORTANTE:
        - Usa el pool del Engine, no la conexión de esta transacción.
        - Las consultas NO forman parte de esta transacción actual.
        - Úsalo para operaciones de solo lectura o independientes.
        """
        return self.engine.parallel_execute(tasks, max_workers=max_workers)

    async def parallel_execute_async(
        self,
        tasks: list[Any],
        *,
        max_concurrency: Optional[int] = None,
    ) -> list[Any]:
        """
        Versión async que delega al Engine.parallel_execute_async.

        Igual que parallel_execute(): las operaciones NO forman parte de la TX.
        """
        return await self.engine.parallel_execute_async(tasks, max_concurrency=max_concurrency)

    """Context manager de transacción de alto nivel.

    Uso sync:
        with Transaction(engine) as tx:
            # mutar modelos, ejecutar queries, etc.

    Uso async (modo compat):
        async with Transaction(engine) as tx:
            ...
    """

    def __init__(self, engine: Engine):
        self.engine = engine
        self._conn = None
        self._models: List[PSQLModel] = []
        self._inserts: List[PSQLModel] = []
        self._updates: List[PSQLModel] = []
        self._deletes: List[PSQLModel] = []

        # Internals for nested/savepoint mode
        self._own_conn: bool = True
        self._nested_savepoint: Optional[str] = None

        # Optional tokens if Engine supports binding/unbinding tx conn (forward-compatible)
        self._bind_token: Any = None

    # Registro de modelos afectados en esta transacción
    def register(self, model: PSQLModel, op: str = "auto") -> None:
        """Registrar modelo y operación: 'insert', 'update', 'delete', o 'auto'."""
        if op == "insert":
            if model not in self._inserts:
                self._inserts.append(model)
            return
        if op == "update":
            if model not in self._updates:
                self._updates.append(model)
            return
        if op == "delete":
            if model not in self._deletes:
                self._deletes.append(model)
            return

        # auto: decide por PK y dirty
        pk_name = None
        cols = getattr(model.__class__, "__columns__", {})
        for name, col in cols.items():
            if getattr(col, "primary_key", False):
                pk_name = name
                break

        dirty = getattr(model, "dirty_fields", getattr(model, "_dirty_fields", {}))
        is_tracked = hasattr(model, "_original_values")
        
        # Check if model was already flushed (SQLAlchemy-like behavior)
        # If it was flushed before, it's already in the DB -> should be UPDATE
        was_flushed = getattr(model, "_psqlmodel_flushed_", False)

        # Lógica mejorada:
        # - Si ya fue flusheado y tiene PK -> UPDATE (no INSERT de nuevo)
        # - Si no está tracked y no hay PK o PK es None -> INSERT
        # - Si hay dirty -> UPDATE
        if was_flushed and pk_name and getattr(model, pk_name, None) is not None:
            # Ya existe en DB, registrar como UPDATE si no está ya registrado
            if model not in self._updates and model not in self._inserts:
                self._updates.append(model)
            # Remove from inserts if it was there (shouldn't happen but safety)
            if model in self._inserts:
                self._inserts.remove(model)
        elif not is_tracked or pk_name is None or getattr(model, pk_name, None) is None:
            if model not in self._inserts:
                self._inserts.append(model)
        elif dirty:
            if model not in self._updates:
                self._updates.append(model)

    # --- sync ---
    def __enter__(self) -> "Transaction":
        if self.engine.config.async_:
            raise RuntimeError(
                "Engine configurado en modo async; usa 'async with Transaction(engine)' "
                "o 'async with AsyncTransaction(engine)'"
            )

        eng_id = id(self.engine)
        stack = _get_sync_stack().get(eng_id, [])

        # Nested TX => use savepoint on same connection
        if stack:
            self._conn = stack[-1]["conn"]
            self._own_conn = False
            sp = self.savepoint()  # validated
            self._nested_savepoint = sp
            stack.append({"conn": self._conn, "savepoint": sp})
            _get_sync_stack()[eng_id] = stack
            return self

        # Outermost TX => acquire and BEGIN
        self._own_conn = True
        self._conn = self.engine.acquire_sync()
        cur = self._conn.cursor()
        try:
            cur.execute("BEGIN")
        finally:
            cur.close()
        self.engine._debug("[TX] BEGIN")

        # Forward-compatible: bind tx conn into Engine if supported
        if hasattr(self.engine, "_bind_tx_conn_sync"):
            try:
                self._bind_token = self.engine._bind_tx_conn_sync(self._conn)  # type: ignore[attr-defined]
            except Exception:
                self._bind_token = None

        _get_sync_stack()[eng_id] = [{"conn": self._conn, "savepoint": None}]
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._conn is None:
            return

        eng_id = id(self.engine)
        stack = _get_sync_stack().get(eng_id, [])

        # Nested: rollback/release savepoint only; never release conn to pool
        if not self._own_conn:
            sp = self._nested_savepoint
            try:
                if sp:
                    if exc_type is None:
                        # Flush inside nested scope (keeps old behavior)
                        self._run_hooks("before_flush")
                        for model in self._inserts:
                            self._flush_model(None, model, op="insert")
                        for model in self._updates:
                            self._flush_model(None, model, op="update")
                        for model in self._deletes:
                            self._flush_model(None, model, op="delete")
                        self._run_hooks("after_flush")

                        self._run_hooks("before_commit")
                        self._release_savepoint(sp)
                        self._run_hooks("after_commit")
                    else:
                        self._run_hooks("before_rollback")
                        self.rollback_to_savepoint(sp)
                        self._run_hooks("after_rollback")
            finally:
                # pop this frame
                if stack:
                    stack.pop()
                    if stack:
                        _get_sync_stack()[eng_id] = stack
                    else:
                        _get_sync_stack().pop(eng_id, None)
                self._nested_savepoint = None
            # propagate exception (default __exit__ behavior) by returning None
            return

        # Outermost: commit/rollback + release conn
        try:
            if exc_type is None:
                try:
                    # Flush models
                    self._run_hooks("before_flush")
                    for model in self._inserts:
                        self._flush_model(None, model, op="insert")
                    for model in self._updates:
                        self._flush_model(None, model, op="update")
                    for model in self._deletes:
                        self._flush_model(None, model, op="delete")
                    self._run_hooks("after_flush")

                    # Commit
                    self._run_hooks("before_commit")
                    cur = self._conn.cursor()
                    try:
                        cur.execute("COMMIT")
                    finally:
                        cur.close()
                    self.engine._debug("[TX] COMMIT")
                    self._run_hooks("after_commit")
                except Exception:
                    # If flush/commit fails, rollback to keep DB consistent
                    try:
                        self._run_hooks("before_rollback")
                        cur = self._conn.cursor()
                        try:
                            cur.execute("ROLLBACK")
                        finally:
                            cur.close()
                        self.engine._debug("[TX] ROLLBACK (commit failed)")
                        self._run_hooks("after_rollback")
                    finally:
                        raise
            else:
                # Rollback
                self._run_hooks("before_rollback")
                cur = self._conn.cursor()
                try:
                    cur.execute("ROLLBACK")
                finally:
                    cur.close()
                self.engine._debug("[TX] ROLLBACK")
                self._run_hooks("after_rollback")
        finally:
            # unbind if supported
            if self._bind_token is not None and hasattr(self.engine, "_unbind_tx_conn_sync"):
                try:
                    self.engine._unbind_tx_conn_sync(self._bind_token)  # type: ignore[attr-defined]
                except Exception:
                    pass
                self._bind_token = None

            # pop stack for this engine
            if stack:
                stack.pop()
            _get_sync_stack().pop(eng_id, None)

            self.engine.release_sync(self._conn)
            self._conn = None

    # --- async ---
    async def __aenter__(self) -> "Transaction":
        if not self.engine.config.async_:
            raise RuntimeError(
                "Engine configurado en modo sync; usa 'with Transaction(engine)' "
                "o 'async with AsyncTransaction(engine)' con un Engine async"
            )

        eng_id = id(self.engine)
        stack = _get_async_stack().get(eng_id, [])

        # Nested TX => savepoint on same connection
        if stack:
            self._conn = stack[-1]["conn"]
            self._own_conn = False
            sp = await self.savepoint_async()
            self._nested_savepoint = sp
            stack.append({"conn": self._conn, "savepoint": sp})
            _get_async_stack()[eng_id] = stack
            return self

        # Outermost
        self._own_conn = True
        self._conn = await self.engine.acquire()
        await self._conn.execute("BEGIN")
        self.engine._debug("[TX] BEGIN (async)")

        # Forward-compatible: bind tx conn into Engine if supported
        if hasattr(self.engine, "_bind_tx_conn_async"):
            try:
                self._bind_token = self.engine._bind_tx_conn_async(self._conn)  # type: ignore[attr-defined]
            except Exception:
                self._bind_token = None

        _get_async_stack()[eng_id] = [{"conn": self._conn, "savepoint": None}]
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._conn is None:
            return

        eng_id = id(self.engine)
        stack = _get_async_stack().get(eng_id, [])

        # Nested: rollback/release savepoint only
        if not self._own_conn:
            sp = self._nested_savepoint
            try:
                if sp:
                    if exc_type is None:
                        try:
                            await self._run_hooks_async("before_flush")
                            for model in self._inserts:
                                await self._flush_model_async(self._conn, model, op="insert")
                            for model in self._updates:
                                await self._flush_model_async(self._conn, model, op="update")
                            for model in self._deletes:
                                await self._flush_model_async(self._conn, model, op="delete")
                            await self._run_hooks_async("after_flush")

                            await self._run_hooks_async("before_commit")
                            await self._release_savepoint_async(sp)
                            await self._run_hooks_async("after_commit")
                        except Exception:
                            await self._run_hooks_async("before_rollback")
                            await self.rollback_to_savepoint_async(sp)
                            await self._run_hooks_async("after_rollback")
                            raise
                    else:
                        await self._run_hooks_async("before_rollback")
                        await self.rollback_to_savepoint_async(sp)
                        await self._run_hooks_async("after_rollback")
            finally:
                if stack:
                    stack.pop()
                    if stack:
                        _get_async_stack()[eng_id] = stack
                    else:
                        _get_async_stack().pop(eng_id, None)
                self._nested_savepoint = None
            return

        # Outermost
        try:
            if exc_type is None:
                try:
                    await self._run_hooks_async("before_flush")
                    for model in self._inserts:
                        await self._flush_model_async(self._conn, model, op="insert")
                    for model in self._updates:
                        await self._flush_model_async(self._conn, model, op="update")
                    for model in self._deletes:
                        await self._flush_model_async(self._conn, model, op="delete")
                    await self._run_hooks_async("after_flush")

                    await self._run_hooks_async("before_commit")
                    await self._conn.execute("COMMIT")
                    self.engine._debug("[TX] COMMIT (async)")
                    await self._run_hooks_async("after_commit")
                except Exception:
                    try:
                        await self._run_hooks_async("before_rollback")
                        await self._conn.execute("ROLLBACK")
                        self.engine._debug("[TX] ROLLBACK (async, commit failed)")
                        await self._run_hooks_async("after_rollback")
                    finally:
                        raise
            else:
                await self._run_hooks_async("before_rollback")
                await self._conn.execute("ROLLBACK")
                self.engine._debug("[TX] ROLLBACK (async)")
                await self._run_hooks_async("after_rollback")
        finally:
            # unbind if supported
            if self._bind_token is not None and hasattr(self.engine, "_unbind_tx_conn_async"):
                try:
                    self.engine._unbind_tx_conn_async(self._bind_token)  # type: ignore[attr-defined]
                except Exception:
                    pass
                self._bind_token = None

            if stack:
                stack.pop()
            _get_async_stack().pop(eng_id, None)

            await self.engine.release(self._conn)
            self._conn = None

    # -----------------------------
    # Flush de modelos (sync/async)
    # -----------------------------
    def _flush_model(self, cur, model: PSQLModel, op: str = "auto") -> None:
        """Flush de un modelo a la DB (sync). El parámetro `cur` se mantiene por compatibilidad."""
        table_name = getattr(model, "__tablename__", "unknown")
        self.engine._debug(f"[TX] FLUSH op={op} table={table_name}")

        from ..query.crud import DirtyTrackingMixin  # evitar ciclos fuertes

        if hasattr(model, "validate"):
            model.validate()
        if hasattr(model, "to_dict"):
            _ = model.to_dict()

        cols = getattr(model.__class__, "__columns__", {})
        pk_name = None
        for name, col in cols.items():
            if getattr(col, "primary_key", False):
                pk_name = name
                break

        dirty = getattr(model, "dirty_fields", getattr(model, "_dirty_fields", {}))
        
        # Auto-compute dirty if model was flushed and has original state saved
        if not dirty and hasattr(model, "_psqlmodel_original_"):
            original = getattr(model, "_psqlmodel_original_", {})
            for name in cols:
                old_val = original.get(name)
                new_val = getattr(model, name, None)
                if old_val != new_val:
                    dirty[name] = (old_val, new_val)

        sql: Optional[str] = None
        values: List[Any] = []
        returning_pk = None  # Will be set for serial PK inserts

        if op == "insert" or (op == "auto" and (pk_name is None or getattr(model, pk_name) is None)):
            sql, vals, returning_pk = build_insert_sql(model)
            values = list(vals)
        elif op == "update" or (op == "auto" and dirty):
            sql, vals = build_update_sql(model, dirty)
            if not sql:
                return
            values = list(vals)
        elif op == "delete":
            if pk_name is None:
                return
            pk_value = getattr(model, pk_name)
            table = getattr(model, "__tablename__")
            schema = getattr(model, "__schema__", "public") or "public"
            sql = f"DELETE FROM {schema}.{table} WHERE {pk_name} = %s"
            values = [pk_value]

            # ORM-level cascade: delete junction rows and one-to-many dependents
            for rel in getattr(model.__class__, "__relations__", {}).values():
                try:
                    rel._detect_relationship_type()
                except Exception:
                    continue

                if getattr(rel, "_relationship_type", None) == "many_to_many" and rel.secondary:
                    owner_table = getattr(model.__class__, "__tablename__")
                    owner_fk = (owner_table[:-1] if owner_table.endswith("s") else owner_table) + "_id"
                    junction = _qualify_table(schema, rel.secondary)
                    self._execute_sql_in_tx_sync(
                        f"DELETE FROM {junction} WHERE {owner_fk} = %s",
                        [pk_value],
                    )

                if getattr(rel, "_relationship_type", None) == "one_to_many":
                    target_model = rel._resolve_target()
                    if target_model is not None:
                        target_schema = getattr(target_model, "__schema__", "public") or "public"
                        target_table = getattr(target_model, "__tablename__")
                        owner_table = getattr(model.__class__, "__tablename__")
                        fk_name = rel._foreign_key or (
                            (owner_table[:-1] if owner_table.endswith("s") else owner_table) + "_id"
                        )
                        target_cols = getattr(target_model, "__columns__", {})
                        fk_col = target_cols.get(fk_name)
                        on_delete = getattr(fk_col, "on_delete", None) if fk_col else None

                        if on_delete in {"RESTRICT", "NO ACTION"}:
                            rows = self._execute_sql_in_tx_sync(
                                f"SELECT 1 FROM {target_schema}.{target_table} "
                                f"WHERE {fk_name} = %s LIMIT 1",
                                [pk_value],
                            )
                            if rows:
                                raise RuntimeError(f"Delete restricted: related rows exist in {target_table}")
                        elif on_delete == "SET NULL":
                            self._execute_sql_in_tx_sync(
                                f"UPDATE {target_schema}.{target_table} "
                                f"SET {fk_name} = NULL WHERE {fk_name} = %s",
                                [pk_value],
                            )
                        elif on_delete == "SET DEFAULT" and getattr(fk_col, "default", None) is not None:
                            default_val = fk_col.default() if callable(fk_col.default) else fk_col.default
                            self._execute_sql_in_tx_sync(
                                f"UPDATE {target_schema}.{target_table} "
                                f"SET {fk_name} = %s WHERE {fk_name} = %s",
                                [default_val, pk_value],
                            )
                        else:
                            self._execute_sql_in_tx_sync(
                                f"DELETE FROM {target_schema}.{target_table} "
                                f"WHERE {fk_name} = %s",
                                [pk_value],
                            )
        else:
            return

        if sql:
            result = self._execute_sql_in_tx_sync(sql, values)
            # Populate returned serial ID for inserts
            if op == "insert" and returning_pk and result:
                try:
                    if hasattr(result, '__iter__') and len(result) > 0:
                        row = result[0]
                        if isinstance(row, dict):
                            setattr(model, returning_pk, row.get(returning_pk))
                        elif hasattr(row, returning_pk):
                            setattr(model, returning_pk, getattr(row, returning_pk))
                        elif hasattr(row, '__getitem__'):
                            setattr(model, returning_pk, row[0])
                except Exception:
                    pass
            # Mark as flushed so subsequent add() calls will UPDATE, not INSERT
            if op == "insert":
                try:
                    setattr(model, "_psqlmodel_flushed_", True)
                    # Save original state for dirty tracking comparison on future updates
                    cols = getattr(model.__class__, "__columns__", {})
                    original = {name: getattr(model, name, None) for name in cols}
                    setattr(model, "_psqlmodel_original_", original)
                except Exception:
                    pass
            if isinstance(model, DirtyTrackingMixin):
                model.clear_dirty()

    async def _flush_model_async(self, conn, model: PSQLModel, op: str = "auto") -> None:
        """Flush de un modelo (async). El parámetro `conn` se mantiene por compatibilidad."""
        table_name = getattr(model, "__tablename__", "unknown")
        self.engine._debug(f"[TX] FLUSH op={op} table={table_name}")

        from ..query.crud import DirtyTrackingMixin

        if hasattr(model, "validate"):
            model.validate()
        if hasattr(model, "to_dict"):
            _ = model.to_dict()

        cols = getattr(model.__class__, "__columns__", {})
        pk_name = None
        for name, col in cols.items():
            if getattr(col, "primary_key", False):
                pk_name = name
                break

        dirty = getattr(model, "dirty_fields", getattr(model, "_dirty_fields", {}))
        
        # Auto-compute dirty if model was flushed and has original state saved
        if not dirty and hasattr(model, "_psqlmodel_original_"):
            original = getattr(model, "_psqlmodel_original_", {})
            for name in cols:
                old_val = original.get(name)
                new_val = getattr(model, name, None)
                if old_val != new_val:
                    dirty[name] = (old_val, new_val)

        sql: Optional[str] = None
        values: List[Any] = []
        returning_pk = None  # Will be set for serial PK inserts

        if op == "insert" or (op == "auto" and (pk_name is None or getattr(model, pk_name) is None)):
            sql, vals, returning_pk = build_insert_sql(model, style="asyncpg")
            values = list(vals)
        elif op == "update" or (op == "auto" and dirty):
            sql, vals = build_update_sql(model, dirty, style="asyncpg")
            if not sql:
                return
            values = list(vals)
        elif op == "delete":
            if pk_name is None:
                return
            pk_value = getattr(model, pk_name)
            table = getattr(model, "__tablename__")
            schema = getattr(model, "__schema__", "public") or "public"
            sql = f"DELETE FROM {schema}.{table} WHERE {pk_name} = $1"
            values = [pk_value]

            for rel in getattr(model.__class__, "__relations__", {}).values():
                try:
                    rel._detect_relationship_type()
                except Exception:
                    continue

                if getattr(rel, "_relationship_type", None) == "many_to_many" and rel.secondary:
                    owner_table = getattr(model.__class__, "__tablename__")
                    owner_fk = (owner_table[:-1] if owner_table.endswith("s") else owner_table) + "_id"
                    junction = _qualify_table(schema, rel.secondary)
                    await self._execute_sql_in_tx_async(
                        f"DELETE FROM {junction} WHERE {owner_fk} = $1",
                        [pk_value],
                    )

                if getattr(rel, "_relationship_type", None) == "one_to_many":
                    target_model = rel._resolve_target()
                    if target_model is not None:
                        target_schema = getattr(target_model, "__schema__", "public") or "public"
                        target_table = getattr(target_model, "__tablename__")
                        owner_table = getattr(model.__class__, "__tablename__")
                        fk_name = rel._foreign_key or (
                            (owner_table[:-1] if owner_table.endswith("s") else owner_table) + "_id"
                        )
                        target_cols = getattr(target_model, "__columns__", {})
                        fk_col = target_cols.get(fk_name)
                        on_delete = getattr(fk_col, "on_delete", None) if fk_col else None

                        if on_delete in {"RESTRICT", "NO ACTION"}:
                            rows = await self._execute_sql_in_tx_async(
                                f"SELECT 1 FROM {target_schema}.{target_table} "
                                f"WHERE {fk_name} = $1 LIMIT 1",
                                [pk_value],
                            )
                            if rows:
                                raise RuntimeError(f"Delete restricted: related rows exist in {target_table}")
                        elif on_delete == "SET NULL":
                            await self._execute_sql_in_tx_async(
                                f"UPDATE {target_schema}.{target_table} "
                                f"SET {fk_name} = NULL WHERE {fk_name} = $1",
                                [pk_value],
                            )
                        elif on_delete == "SET DEFAULT" and getattr(fk_col, "default", None) is not None:
                            default_val = fk_col.default() if callable(fk_col.default) else fk_col.default
                            await self._execute_sql_in_tx_async(
                                f"UPDATE {target_schema}.{target_table} "
                                f"SET {fk_name} = $1 WHERE {fk_name} = $2",
                                [default_val, pk_value],
                            )
                        else:
                            await self._execute_sql_in_tx_async(
                                f"DELETE FROM {target_schema}.{target_table} "
                                f"WHERE {fk_name} = $1",
                                [pk_value],
                            )
        else:
            return

        if sql:
            result = await self._execute_sql_in_tx_async(sql, values)
            # Populate returned serial ID for inserts
            if op == "insert" and returning_pk and result:
                try:
                    if hasattr(result, '__iter__') and len(result) > 0:
                        row = result[0]
                        if isinstance(row, dict):
                            setattr(model, returning_pk, row.get(returning_pk))
                        elif hasattr(row, returning_pk):
                            setattr(model, returning_pk, getattr(row, returning_pk))
                        elif hasattr(row, '__getitem__'):
                            setattr(model, returning_pk, row[0])
                except Exception:
                    pass
            # Mark as flushed so subsequent add() calls will UPDATE, not INSERT
            if op == "insert":
                try:
                    setattr(model, "_psqlmodel_flushed_", True)
                    # Save original state for dirty tracking comparison on future updates
                    cols = getattr(model.__class__, "__columns__", {})
                    original = {name: getattr(model, name, None) for name in cols}
                    setattr(model, "_psqlmodel_original_", original)
                except Exception:
                    pass
            if isinstance(model, DirtyTrackingMixin):
                model.clear_dirty()


# ============================================================
# AsyncTransaction – API async “bonita” sin sufijos *_async
# ============================================================

class AsyncTransaction(Transaction):
    """
    Versión asíncrona de Transaction con métodos sin sufijo *_async.

    Uso:
        async with AsyncTransaction(engine) as tx:
            tx.register(model)
            await tx.bulk_insert([model1, model2])
            sp = await tx.savepoint()
            ...
    """

    def __init__(self, engine: Engine):
        if not engine.config.async_:
            raise RuntimeError("AsyncTransaction requiere un Engine configurado con async_=True")
        super().__init__(engine)

    def __enter__(self):
        raise RuntimeError("AsyncTransaction solo puede usarse con 'async with AsyncTransaction(engine)'")

    async def __aenter__(self) -> "AsyncTransaction":
        await super().__aenter__()
        return self

    async def savepoint(self, name: Optional[str] = None) -> str:
        return await super().savepoint_async(name)

    async def rollback_to_savepoint(self, name: str) -> None:
        await super().rollback_to_savepoint_async(name)

    async def bulk_insert(self, models: list) -> None:
        await super().bulk_insert_async(models)

    async def bulk_update(self, models: list) -> None:
        await super().bulk_update_async(models)

    async def execute_with_retry(
        self,
        sql: str,
        params: Optional[List[Any]] = None,
        retries: int = 3,
    ) -> None:
        await super().execute_with_retry_async(sql, params, retries)

    async def parallel_execute(
        self,
        tasks: list[Any],
        *,
        max_concurrency: Optional[int] = None,
    ) -> list[Any]:
        """Ejecuta múltiples consultas en paralelo usando el Engine (fuera de esta TX)."""
        return await self.engine.parallel_execute_async(tasks, max_concurrency=max_concurrency)
