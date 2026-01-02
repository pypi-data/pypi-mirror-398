from __future__ import annotations

"""Session and AsyncSession wrappers around Transaction.

Integran Engine + Transaction + PSQLModel con:
- Context managers sync/async para FastAPI / frameworks.
- Identity map (cache por PK).
- Carga diferida y eager (Include).
- API tipo ORM: add, get, exec, exec_one, exec_scalar, refresh, delete, bulk_*.
- SessionManager con contextvars para que el QueryBuilder use siempre
  la sesión/transacción actual sin pasarla a mano.
"""

from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Optional,
    TypeVar,
    Generic,
    Awaitable,
    Sequence,
)
from contextvars import ContextVar, Token

from .transactions import Transaction

if TYPE_CHECKING:  # avoid circular imports at runtime
    from ..orm.model import PSQLModel
    from .engine import Engine

T = TypeVar("T")


# ============================================================
# Shared Mixin for Session and AsyncSession
# ============================================================

class _SessionMixin:
    """Shared methods between Session and AsyncSession.
    
    Contains identity map operations and relationship detection logic
    that is identical in both sync and async contexts.
    """
    
    # These will be defined in subclasses
    _identity_map: dict
    _expired: set
    
    def _add_to_cache(self, model: "PSQLModel") -> None:
        """Add model to identity map if it has a PK."""
        try:
            pk_name = None
            for name, col in getattr(model.__class__, "__columns__", {}).items():
                if getattr(col, "primary_key", False):
                    pk_name = name
                    break
            if pk_name:
                pk_value = getattr(model, pk_name, None)
                if pk_value is not None:
                    key = (model.__class__, pk_value)
                    self._identity_map[key] = model
        except Exception:
            pass

    def _evict_from_cache(self, model: "PSQLModel") -> None:
        """Remove model from identity map if present."""
        try:
            pk_name = None
            for name, col in getattr(model.__class__, "__columns__", {}).items():
                if getattr(col, "primary_key", False):
                    pk_name = name
                    break
            if pk_name:
                pk_value = getattr(model, pk_name, None)
                if pk_value is not None:
                    self._identity_map.pop((model.__class__, pk_value), None)
        except Exception:
            pass

    def _normalize_fk_ref(self, fk_ref) -> Optional[str]:
        """Normalize FK reference to 'table.column' or 'schema.table.column' format."""
        if fk_ref is None:
            return None
        
        # FK is a Column object (e.g., User.id)
        if hasattr(fk_ref, "model") and hasattr(fk_ref, "name"):
            table = getattr(fk_ref.model, "__tablename__", "")
            schema = getattr(fk_ref.model, "__schema__", "public") or "public"
            return f"{schema}.{table}.{fk_ref.name}"
        
        # FK is a string like "users.id" or "public.users.id"
        if isinstance(fk_ref, str):
            return fk_ref
        
        return None

    def _detect_relationship(self, owner_model, target_model):
        """Auto-detect relationship type between two models using metadata, FK metadata and heuristics."""
        try:
            relations = getattr(owner_model, "__relations__", {})
        except Exception:
            relations = {}

        for attr_name, rel in relations.items():
            try:
                target = rel._resolve_target()
            except Exception:
                target = None
            if target is not target_model:
                continue

            try:
                rel._detect_relationship_type()
            except Exception:
                pass

            rel_type = getattr(rel, "_relationship_type", None)
            fk_name = getattr(rel, "_foreign_key", None)

            owner_table = getattr(owner_model, "__tablename__", owner_model.__name__.lower())
            target_table = getattr(target_model, "__tablename__", target_model.__name__.lower())

            def to_singular(name: str) -> str:
                return name[:-1] if name.endswith("s") else name

            if not fk_name:
                if rel_type in ("many_to_one", "one_to_one"):
                    fk_name = f"{to_singular(target_table)}_id"
                elif rel_type == "one_to_many":
                    fk_name = f"{to_singular(owner_table)}_id"

            # VALIDATION: Only return if the FK actually exists in the appropriate model
            fk_exists = False
            if rel_type == "one_to_many":
                fk_exists = fk_name in getattr(target_model, "__columns__", {})
            elif rel_type in ("many_to_one", "one_to_one"):
                fk_exists = (fk_name in getattr(owner_model, "__columns__", {}) or
                            fk_name in getattr(target_model, "__columns__", {}))
            elif rel_type == "many_to_many":
                fk_exists = True

            if fk_exists:
                return {
                    "type": rel_type or "many_to_one",
                    "fk_name": fk_name,
                    "attr_name": attr_name,
                    "rel_obj": rel,
                }

        # Check FK metadata on columns
        owner_table = getattr(owner_model, "__tablename__", owner_model.__name__.lower())
        target_table = getattr(target_model, "__tablename__", target_model.__name__.lower())
        target_schema = getattr(target_model, "__schema__", "public") or "public"
        owner_schema = getattr(owner_model, "__schema__", "public") or "public"

        def to_singular(name: str) -> str:
            return name[:-1] if name.endswith("s") else name

        # Find target's primary key
        target_pk = None
        for name, col in getattr(target_model, "__columns__", {}).items():
            if getattr(col, "primary_key", False):
                target_pk = name
                break

        # Check owner columns for FK pointing to target (many_to_one / one_to_one)
        if target_pk:
            for col_name, col in getattr(owner_model, "__columns__", {}).items():
                fk_ref = getattr(col, "foreign_key", None)
                if fk_ref:
                    fk_target = self._normalize_fk_ref(fk_ref)
                    expected_refs = [
                        f"{target_table}.{target_pk}",
                        f"{target_schema}.{target_table}.{target_pk}",
                    ]
                    if fk_target in expected_refs:
                        is_unique = bool(getattr(col, "unique", False))
                        return {
                            "type": "one_to_one" if is_unique else "many_to_one",
                            "fk_name": col_name,
                            "attr_name": col_name.replace("_id", "") if col_name.endswith("_id") else col_name,
                        }

        # Find owner's primary key
        owner_pk = None
        for name, col in getattr(owner_model, "__columns__", {}).items():
            if getattr(col, "primary_key", False):
                owner_pk = name
                break

        # Check target columns for FK pointing to owner (one_to_many)
        if owner_pk:
            for col_name, col in getattr(target_model, "__columns__", {}).items():
                fk_ref = getattr(col, "foreign_key", None)
                if fk_ref:
                    fk_target = self._normalize_fk_ref(fk_ref)
                    expected_refs = [
                        f"{owner_table}.{owner_pk}",
                        f"{owner_schema}.{owner_table}.{owner_pk}",
                    ]
                    if fk_target in expected_refs:
                        attr_name = target_table
                        for rel_name, rel in getattr(owner_model, "__relations__", {}).items():
                            try:
                                if rel._resolve_target() is target_model:
                                    attr_name = rel_name
                                    break
                            except Exception:
                                pass
                        
                        is_unique = bool(getattr(col, "unique", False))
                        rel_type = "one_to_one" if is_unique else "one_to_many"
                        
                        return {
                            "type": rel_type,
                            "fk_name": col_name,
                            "attr_name": attr_name,
                        }

        # Fallback: Heuristica basada en nombres (legacy)
        owner_fk_name = f"{to_singular(target_table)}_id"
        if owner_fk_name in getattr(owner_model, "__columns__", {}):
            col = owner_model.__columns__[owner_fk_name]
            is_unique = bool(getattr(col, "unique", False))
            return {
                "type": "one_to_one" if is_unique else "many_to_one",
                "fk_name": owner_fk_name,
                "attr_name": to_singular(target_table),
            }

        target_fk_name = f"{to_singular(owner_table)}_id"
        if target_fk_name in getattr(target_model, "__columns__", {}):
            return {
                "type": "one_to_many",
                "fk_name": target_fk_name,
                "attr_name": target_table,
            }

        return None

    def expire(self, model: "PSQLModel", attribute_names: list = None) -> None:
        """Mark model (or specific attributes) as expired.
        
        Next access to expired attributes will reload from DB.
        
        Examples:
            session.expire(user)  # Expire all attributes
            session.expire(user, ["email", "name"])  # Expire specific attrs
        """
        pk_name = None
        for name, col in getattr(model.__class__, "__columns__", {}).items():
            if getattr(col, "primary_key", False):
                pk_name = name
                break
        
        if pk_name:
            pk_val = getattr(model, pk_name, None)
            if pk_val is not None:
                if attribute_names:
                    # Track specific expired attributes on model
                    if not hasattr(model, "_expired_attrs"):
                        model._expired_attrs = set()
                    model._expired_attrs.update(attribute_names)
                else:
                    # Mark entire model as expired
                    self._expired.add((type(model), pk_val))

    def expire_all(self) -> None:
        """Expire all models in the identity map."""
        for key in self._identity_map:
            self._expired.add(key)

    def expunge(self, model: "PSQLModel") -> None:
        """Detach model from session (remove from identity map).
        
        The model will no longer be tracked by this session.
        """
        pk_name = None
        for name, col in getattr(model.__class__, "__columns__", {}).items():
            if getattr(col, "primary_key", False):
                pk_name = name
                break
        
        if pk_name:
            pk_val = getattr(model, pk_name, None)
            if pk_val is not None:
                key = (type(model), pk_val)
                self._identity_map.pop(key, None)
                self._expired.discard(key)
        
        # Remove session binding
        if hasattr(model, "__session__"):
            try:
                model.__session__ = None
            except Exception:
                pass

    def expunge_all(self) -> None:
        """Detach all models from session."""
        for key, model in list(self._identity_map.items()):
            if hasattr(model, "__session__"):
                try:
                    model.__session__ = None
                except Exception:
                    pass
        self._identity_map.clear()
        self._expired.clear()

    def no_autoflush(self):
        """Context manager to temporarily disable autoflush.
        
        Usage:
            with session.no_autoflush():
                # Operations here won't trigger autoflush
                user.name = "new name"
        """
        from contextlib import contextmanager
        
        @contextmanager
        def _no_autoflush():
            old_value = self._autoflush
            self._autoflush = False
            try:
                yield
            finally:
                self._autoflush = old_value
        
        return _no_autoflush()

    def on_before_flush(self, callback) -> None:
        """Register callback to run before flush.
        
        Callback receives the session as argument.
        """
        self._before_flush_hooks.append(callback)

    def on_after_commit(self, callback) -> None:
        """Register callback to run after successful commit."""
        self._after_commit_hooks.append(callback)

    def on_after_rollback(self, callback) -> None:
        """Register callback to run after rollback."""
        self._after_rollback_hooks.append(callback)

    def _run_hooks(self, hook_name: str) -> None:
        """Run all registered hooks for the given event."""
        hooks = {
            "before_flush": self._before_flush_hooks,
            "after_commit": self._after_commit_hooks,
            "after_rollback": self._after_rollback_hooks,
        }.get(hook_name, [])
        
        for hook in hooks:
            try:
                hook(self)
            except Exception:
                pass  # Don't let hook errors break the session


# ============================================================
# SessionManager basado en contextvars
# ============================================================

_current_session: ContextVar["Session | None"] = ContextVar(
    "psqlmodel_current_session", default=None
)
_current_async_session: ContextVar["AsyncSession | None"] = ContextVar(
    "psqlmodel_current_async_session", default=None
)


class SessionManager:
    """Punto central para obtener la Session/AsyncSession actual.

    Uso típico dentro del QueryBuilder:

        from psqlmodel.session import SessionManager

        def all(self):
            session = SessionManager.require_current()
            return session.exec(self).all()
    """

    # ---- Sync ----
    @staticmethod
    def current() -> "Session | None":
        return _current_session.get()

    @staticmethod
    def require_current() -> "Session":
        session = _current_session.get()
        if session is None:
            raise RuntimeError(
                "No hay Session activa. Usa 'with Session(engine) as session:' "
                "o una dependencia de FastAPI que cree la sesión."
            )
        return session

    # ---- Async ----
    @staticmethod
    def current_async() -> "AsyncSession | None":
        return _current_async_session.get()

    @staticmethod
    def require_current_async() -> "AsyncSession":
        session = _current_async_session.get()
        if session is None:
            raise RuntimeError(
                "No hay AsyncSession activa. Usa 'async with AsyncSession(engine) as session:' "
                "o una dependencia async que cree la sesión."
            )
        return session


# ============================================================
# Result wrappers
# ============================================================

# ============================================================
# Row Object (for mixed results)
# ============================================================

class Row(tuple):
    """
    Representa una fila de resultados híbridos (Modelos + Escalares).
    Se comporta como una tupla, pero permite acceso por nombre (si existe).
    """
    __slots__ = ()

    # Mapping is stored on the instance by a factory or wrapper?
    # Tuple instances cannot have attributes unless we preserve them in a subclass that has slots or dict.
    # But for a simple effective implementation that mimics namedtuple but allows "model" objects...
    
    # Let's use a dynamic approach where we set attributes on a subclass creation? No, too slow.
    # We can assume Row is just a customized tuple that has a separate mapping attached to the CLASS or INSTANCE?
    # Since tuple is immutable, we can't easily attach data to an instance unless we use __new__.
    pass

class RowResult:
    """
    Wrapper para resultados mixtos.
    Soporta acceso por índice: row[0]
    Soporta acceso por clave: row.field_name (si existe)
    """
    __slots__ = ("_data", "_key_map")

    def __init__(self, data: tuple, key_map: dict[str, int]):
        self._data = data
        self._key_map = key_map

    def __getitem__(self, index: int | str):
        if isinstance(index, str):
            if index not in self._key_map:
                raise KeyError(f"Key '{index}' not found in Row")
            return self._data[self._key_map[index]]
        return self._data[index]

    def __getattr__(self, name: str):
        if name in self._key_map:
            return self._data[self._key_map[name]]
        raise AttributeError(f"Row has no attribute '{name}'")
    
    def __iter__(self):
        return iter(self._data)
    
    def __repr__(self):
        return repr(self._data)

    def __len__(self):
        return len(self._data)

    def _asdict(self) -> dict:
        """Return a dictionary representation of the row logic."""
        d = {}
        
        # Build reverse map for valid keys
        idx_to_key = {v: k for k, v in self._key_map.items()}
        
        for i, val in enumerate(self._data):
            key = idx_to_key.get(i)
            
            if key:
                # Named item (Scalar alias or Model alias)
                if hasattr(val, "model_dump"):
                    d[key] = val.model_dump(mode='json')
                elif hasattr(val, "_asdict"):
                    d[key] = val._asdict()
                else:
                    d[key] = val
            else:
                # Unnamed item
                if hasattr(val, "model_dump"):
                    # Flatten Model into root dict
                    d.update(val.model_dump(mode='json'))
                else:
                    # Unnamed scalar - cannot represent in dict without key
                    pass
                    
        return d

class QueryResult(Generic[T]):
    """Result wrapper that behaves like a read-only list + helpers."""

    def __init__(self, data: List[T], model_cls: Optional[type] = None):
        self._data = data
        self._model_cls = model_cls

    # List-like behaviour
    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, item):
        return self._data[item]

    def __repr__(self) -> str:
        return (
            f"QueryResult(len={len(self._data)}, "
            f"model={getattr(self._model_cls, '__name__', None)})"
        )

    # Helpers
    def all(self) -> List[T]:
        """Return all results as a list."""
        return self._data

    def first(self) -> Optional[T]:
        """Return the first result or None if empty."""
        return self._data[0] if self._data else None

    def one(self) -> T:
        """Return exactly one result or raise an error."""
        if not self._data:
            raise ValueError("No results found")
        if len(self._data) > 1:
            raise ValueError(f"Expected 1 result, got {len(self._data)}")
        return self._data[0]

    def one_or_none(self) -> Optional[T]:
        """Return exactly one result, None if empty, or raise if multiple."""
        if not self._data:
            return None
        if len(self._data) > 1:
            raise ValueError(f"Expected 1 result, got {len(self._data)}")
        return self._data[0]

    def to_dicts(self) -> List[dict]:
        """Convert all results to dictionaries.
        
        Useful for API responses with FastAPI/Pydantic.
        
        Examples:
            trips = session.exec(Select(Trip)).to_dicts()
            return {"trips": trips}  # Already serializable
        """
        import json as json_stdlib
        from ..orm.types import jsonb as jsonb_type, json as json_type
        
        result = []
        for item in self._data:
            # Get column names from __columns__ if available
            cols = getattr(item.__class__, "__columns__", None)
            if cols:
                d = {}
                instance_dict = getattr(item, "__dict__", {})
                # Use model_dump used for Pydantic compatibility
                # mode='json' ensures UUID/Date -> str conversion
                if hasattr(item, "model_dump"):
                    d = item.model_dump(mode='json')
                result.append(d)
                continue
            
            # Explicit RowResult support
            if hasattr(item, "_asdict"):
                result.append(item._asdict())
                continue

            else:
                # Fallback: filter __dict__ manually
                d = {}
                for k, v in getattr(item, "__dict__", {}).items():
                    if not k.startswith("_") and not hasattr(v, "primary_key"):
                        d[k] = v
                result.append(d)
        return result


class AsyncQueryResult(Generic[T]):
    """Async result wrapper that provides .all() / .first() / .one() / .one_or_none()."""

    def __init__(self, coro: Awaitable[List[T]]):
        self._coro = coro
        self._data: Optional[List[T]] = None

    async def _ensure_data(self) -> List[T]:
        """Await the coroutine if not already done."""
        if self._data is None:
            self._data = await self._coro
        return self._data

    async def all(self) -> List[T]:
        """Return all results as a list."""
        return await self._ensure_data()

    async def first(self) -> Optional[T]:
        """Return the first result or None if empty."""
        data = await self._ensure_data()
        return data[0] if data else None

    async def one(self) -> T:
        """Return exactly one result or raise an error."""
        data = await self._ensure_data()
        if not data:
            raise ValueError("No results found")
        if len(data) > 1:
            raise ValueError(f"Expected 1 result, got {len(data)}")
        return data[0]

    async def one_or_none(self) -> Optional[T]:
        """Return exactly one result, None if empty, or raise if multiple."""
        data = await self._ensure_data()
        if not data:
            return None
        if len(data) > 1:
            raise ValueError(f"Expected 1 result, got {len(data)}")
        return data[0]

    async def to_dicts(self) -> List[dict]:
        """Convert all results to dictionaries.
        
        Useful for API responses with FastAPI/Pydantic.
        
        Examples:
            trips = await session.exec(Select(Trip)).to_dicts()
            return {"trips": trips}  # Already serializable
        """
        import json as json_stdlib
        from ..orm.types import jsonb as jsonb_type, json as json_type
        
        data = await self._ensure_data()
        result = []
        for item in data:
            # Get column names from __columns__ if available
            cols = getattr(item.__class__, "__columns__", None)
            if cols:
                d = {}
                instance_dict = getattr(item, "__dict__", {})
                # Use model_dump used for Pydantic compatibility
                # mode='json' ensures UUID/Date -> str conversion
                if hasattr(item, "model_dump"):
                    d = item.model_dump(mode='json')
                result.append(d)
                continue

            # Explicit RowResult support
            if hasattr(item, "_asdict"):
                result.append(item._asdict())
                continue

            else:
                # Fallback: filter __dict__ manually
                d = {}
                for k, v in getattr(item, "__dict__", {}).items():
                    if not k.startswith("_") and not hasattr(v, "primary_key"):
                        d[k] = v
                result.append(d)
        return result

    def __await__(self):
        """Allow awaiting the result directly (equivalent to .all())."""
        return self._ensure_data().__await__()


# ============================================================
# Synchronous Session
# ============================================================

class Session(_SessionMixin):
    """Synchronous session wrapper around Transaction.

    - Usa el pool del Engine y una Transaction interna.
    - Soporta identity map.
    - Se publica en un ContextVar vía SessionManager.

    auto_commit / auto_rollback:
    - auto_commit=True: si sales del 'with' sin excepción y no hiciste commit
      manual, hace COMMIT automático.
    - auto_rollback=True: si sales del 'with' con excepción o con auto_commit=False
      y hay TX pendiente, hace ROLLBACK automático.
    - atomic: bool = False.
      Si True, commit() cierra la sesión.
      Si False (default), commit() cierra la transacción pero mantiene la sesión abierta
      para nuevas operaciones (que abrirán una nueva transacción automáticamente).
    """

    # ----------------------------------
    # Métodos de alto nivel (flush/tx)
    # ----------------------------------
    def _ensure_transaction(self) -> None:
        """Asegura que haya una transacción activa. Si no, arranca una nueva."""
        if self._closed:
            raise RuntimeError("Session is closed.")

        if self._tx is None:
            if self._atomic:
                # En modo atomic, si no hay tx es porque se cerró (commit/rollback)
                raise RuntimeError("Session is not active (atomic mode).")

            # Modo no-atomic: abrir nueva transacción
            self._tx = Transaction(self.engine)
            self._tx.__enter__()  # BEGIN

    def flush(self) -> None:
        """Flush explícito de modelos registrados en la Transaction actual.

        No hace COMMIT ni ROLLBACK, solo sincroniza los cambios pendientes
        con la base de datos dentro de la misma transacción.
        """
        self._ensure_transaction()
        if self._tx is None or self._tx._conn is None:
            raise RuntimeError("Session is not active. Use it inside a 'with' block.")

        # Respetar el orden: inserts, updates, deletes.
        self._tx._run_hooks("before_flush")  # type: ignore[attr-defined]
        for model in list(getattr(self._tx, "_inserts", [])):
            self._tx._flush_model(None, model, op="insert")
        for model in list(getattr(self._tx, "_updates", [])):
            self._tx._flush_model(None, model, op="update")
        for model in list(getattr(self._tx, "_deletes", [])):
            self._tx._flush_model(None, model, op="delete")
        self._tx._run_hooks("after_flush")  # type: ignore[attr-defined]

        # Limpiamos colas de la TX para evitar re-flush duplicado
        self._tx._inserts.clear()
        self._tx._updates.clear()
        self._tx._deletes.clear()

    def commit(self) -> None:
        """Commit explícito de la transacción actual.

        - Usa Transaction.__exit__ internamente.
        - Si atomic=True: Cierra la sesión (comportamiento legacy).
        - Si atomic=False (default): Cierra sólo la transacción; la sesión sigue abierta.
        - Si expire_on_commit=True: Marca todos los objetos en identity map como expired.
        
        Autobegin: If there are pending inserts and no active transaction,
        a new transaction is started automatically (non-atomic mode only).
        """
        # Autobegin: start a new transaction if there are pending operations
        has_pending = hasattr(self, "_pending_inserts") and self._pending_inserts
        
        if self._tx is None and has_pending:
            # Start a new transaction to handle the pending inserts
            self._ensure_transaction()
        
        if self._tx is None:
            # No transaction and no pending operations - nothing to commit
            return

        # Flush pending inserts before commit (sync Session may also use this pattern)
        if hasattr(self, "_pending_inserts") and self._pending_inserts:
            for model in self._pending_inserts:
                self._tx.register(model)
            self._pending_inserts.clear()

        self._tx.__exit__(None, None, None)  # COMMIT
        self._tx = None

        # Mark all objects as expired if expire_on_commit=True
        if self._expire_on_commit:
            for key in self._identity_map:
                self._expired.add(key)

        if self._atomic:
            self._closed = True

    def rollback(self) -> None:
        """Rollback explícito de la transacción actual.

        - Si atomic=True: Cierra la sesión.
        - Si atomic=False (default): Cierra sólo la transacción; la sesión sigue abierta.
        """
        if self._tx is None:
            raise RuntimeError("Session is not active. Use it inside a 'with' block.")

        class _SessionRollback(Exception):
            pass

        self._tx.__exit__(_SessionRollback, _SessionRollback("manual rollback"), None)
        self._tx = None

        if self._atomic:
            self._closed = True

    def refresh(self, model: "PSQLModel") -> None:
        """Vuelve a cargar un modelo desde la BD por su PK, dentro de la misma TX."""
        self._ensure_transaction()
        if self._tx is None or self._tx._conn is None:
            raise RuntimeError("Session is not active. Use it inside a 'with' block.")

        pk_name = None
        cols = getattr(model.__class__, "__columns__", {})
        for name, col in cols.items():
            if getattr(col, "primary_key", False):
                pk_name = name
                break
        if pk_name is None:
            raise ValueError("No primary key defined")

        pk_value = getattr(model, pk_name, None)
        if pk_value is None:
            raise ValueError("Primary key value is None; cannot refresh")

        table = getattr(model, "__tablename__")
        schema = getattr(model, "__schema__", "public") or "public"

        # IMPORTANTE: seleccionar columnas en el orden de __columns__ para mapear correctamente.
        col_names = list(cols.keys())
        select_list = ", ".join(col_names) if col_names else "*"
        sql = f"SELECT {select_list} FROM {schema}.{table} WHERE {pk_name} = %s"

        rows = self._tx._execute_sql_in_tx_sync(sql, [pk_value])  # type: ignore[attr-defined]
        if rows:
            row = rows[0]
            for idx, name in enumerate(col_names):
                try:
                    setattr(model, name, row[idx])
                except Exception:
                    pass

        self._add_to_cache(model)

    def delete(self, model: "PSQLModel") -> None:
        """Marca un modelo para DELETE (y lo ejecuta inmediato para compatibilidad).
        
        If related objects have cascade=True, they are deleted first.
        If passive_deletes=True, relies on database ON DELETE CASCADE.
        """
        self._ensure_transaction()
        if self._tx is None:
            raise RuntimeError("Session is not active. Use it inside a 'with' block.")

        # Handle cascade deletes for relationships
        self._cascade_delete(model)

        self._tx.register(model, op="delete")
        self._tx._flush_model(None, model, op="delete")

        # Evitar doble DELETE al hacer commit/exit (si quedó en la cola)
        try:
            if model in self._tx._deletes:
                self._tx._deletes.remove(model)
        except Exception:
            pass

        # Sacar del identity map
        self._evict_from_cache(model)

    def bulk_insert(self, models: list) -> None:
        self._ensure_transaction()
        if self._tx is None:
            raise RuntimeError("Session is not active. Use it inside a 'with' block.")
        self._tx.bulk_insert(models)

    def bulk_update(self, models: list) -> None:
        self._ensure_transaction()
        if self._tx is None:
            raise RuntimeError("Session is not active. Use it inside a 'with' block.")
        self._tx.bulk_update(models)

    # Expire / Expunge / Autoflush
    # ----------------------------------
    # NOTE: expire, expire_all, expunge, expunge_all, no_autoflush inherited from _SessionMixin
    # NOTE: on_before_flush, on_after_commit, on_after_rollback, _run_hooks inherited from _SessionMixin

    # ----------------------------------
    # Constructor / context manager
    # ----------------------------------
    def __init__(
        self,
        engine: "Engine",
        auto_commit: bool = False,
        auto_rollback: bool = True,
        atomic: bool = False,
        expire_on_commit: bool = False,
    ):
        self.engine = engine
        self._auto_commit = auto_commit
        self._auto_rollback = auto_rollback
        self._atomic = atomic
        self._expire_on_commit = expire_on_commit

        self._tx: Optional[Transaction] = None
        self._closed = False

        # Identity Map: (modelo_cls, pk_value) -> instancia
        self._identity_map: dict[tuple[type, Any], Any] = {}

        # Token para contextvar
        self._ctx_token: Optional[Token] = None

        # Expire tracking
        self._expired: set[tuple[type, Any]] = set()  # (model_cls, pk) that need refresh

        # Autoflush control
        self._autoflush = True

        # Event hooks
        self._before_flush_hooks: list = []
        self._after_commit_hooks: list = []
        self._after_rollback_hooks: list = []

    def __enter__(self) -> "Session":
        if self.engine.config.async_:
            raise RuntimeError("Engine async; use AsyncSession(engine) en su lugar.")
        if self._closed:
            raise RuntimeError("Session is already closed.")
        if self._tx is not None:
            raise RuntimeError("Session is already active.")

        self._tx = Transaction(self.engine)
        self._tx.__enter__()  # Acquire conn + BEGIN

        # Publicar en contextvar
        self._ctx_token = _current_session.set(self)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        # Siempre limpiar el contextvar
        if self._ctx_token is not None:
            _current_session.reset(self._ctx_token)
            self._ctx_token = None

        if self._tx is None:
            self._closed = True
            return

        # Si ya hicimos commit/rollback manual, _tx debería ser None.
        # Por seguridad, comprobamos:
        if self._closed:
            self._tx = None
            return

        # Lógica de auto_commit / auto_rollback
        if exc_type is not None:
            # Hay excepción dentro del bloque
            if self._auto_rollback:
                self._tx.__exit__(exc_type, exc, tb)
            else:
                # Seguridad: aunque auto_rollback=False, es peligroso no hacer rollback.
                self._tx.__exit__(exc_type, exc, tb)
        else:
            # No hay excepción
            if self._auto_commit:
                self._tx.__exit__(None, None, None)
            elif self._auto_rollback:
                class _AutoRollback(Exception):
                    pass

                self._tx.__exit__(
                    _AutoRollback,
                    _AutoRollback("auto rollback end-of-context"),
                    None,
                )
            else:
                class _SafeRollback(Exception):
                    pass

                self._tx.__exit__(
                    _SafeRollback,
                    _SafeRollback("safe rollback (auto_commit=False, auto_rollback=False)"),
                    None,
                )

        self._tx = None
        self._closed = True

    # ----------------------------------
    # API de trabajo con modelos
    # ----------------------------------
    def add(self, model: "PSQLModel") -> None:
        """Registra un modelo en la UoW de la transacción."""
        self._ensure_transaction()
        if self._tx is None:
            raise RuntimeError("Session is not active. Use it inside a 'with' block.")

        self._tx.register(model)
        try:
            setattr(model, "__session__", self)
        except Exception:
            pass

        self._add_to_cache(model)

    def get(self, model_cls: type, pk_value: Any):
        """Carga por primary key con caché (similar a SQLAlchemy Session.get)."""
        if pk_value is None:
            return None

        key = (model_cls, pk_value)
        if key in self._identity_map:
            return self._identity_map[key]

        # Resolver PK
        pk_name = None
        for name, col in getattr(model_cls, "__columns__", {}).items():
            if getattr(col, "primary_key", False):
                pk_name = name
                break
        if pk_name is None:
            raise ValueError(f"Modelo {model_cls.__name__} no tiene primary key definida.")

        try:
            from ..query.builder import Select
        except Exception:
            from psqlmodel.query.builder import Select  # type: ignore

        pk_col = getattr(model_cls, pk_name)
        res = self.exec(Select(model_cls).Where(pk_col == pk_value)).first()
        if res:
            # Ensure model is marked as existing in DB (safety, exec should do this)
            try:
                if not getattr(res, "_psqlmodel_flushed_", False):
                    setattr(res, "_psqlmodel_flushed_", True)
                    cols = getattr(model_cls, "__columns__", {})
                    original = {name: getattr(res, name, None) for name in cols}
                    setattr(res, "_psqlmodel_original_", original)
            except Exception:
                pass
            self._add_to_cache(res)
        return res

    # ----------------------------------
    # Exec de queries (sync)
    # ----------------------------------
    def exec(self, query: Any, *, params: Sequence[Any] | None = None) -> QueryResult:
        """Execute a query builder (Select, Insert, Update, Delete, etc.) or raw SQL."""
        self._ensure_transaction()
        if self._tx is None or self._tx._conn is None:
            raise RuntimeError("Session is not active. Use it inside a 'with' block.")

        sql: str
        query_params: Sequence[Any]

        # Get SQL and params from query
        if isinstance(query, str):
            sql = query
            query_params = params or []
        elif hasattr(query, "to_sql_params"):
            sql, query_params = query.to_sql_params()
        elif hasattr(query, "to_sql"):
            sql = query.to_sql()
            query_params = []
        else:
            raise ValueError("Query must be a string or have to_sql_params() or to_sql() method")

        # Try to import SelectQuery robustly (relative + fallback)
        SelectQuery = None
        try:
            from ..query.builder import SelectQuery as _SelectQuery  # type: ignore
            SelectQuery = _SelectQuery
        except Exception:
            try:
                from psqlmodel.query.builder import SelectQuery as _SelectQuery  # type: ignore
                SelectQuery = _SelectQuery
            except Exception:
                SelectQuery = None

        # Caso: SELECT * FROM Modelo → materializar modelos + identity map + includes

        # Caso: SELECT * FROM Modelo -> materializar modelos + identity map + includes
        if (
            SelectQuery is not None
            and isinstance(query, SelectQuery)
            and bool(getattr(query, "select_all", False))
        ):
            # 1. Standard "Select(Model)" logic (Backwards Compatibility)
            rows = self._tx._execute_sql_in_tx_sync(sql, list(query_params))  # type: ignore[attr-defined]
            rows = rows or []

            result_list: List[Any] = []
            base_model = query.base_model
            col_names = list(getattr(base_model, "__columns__", {}).keys())

            pk_name = None
            for name, col in getattr(base_model, "__columns__", {}).items():
                if getattr(col, "primary_key", False):
                    pk_name = name
                    break

            for row in rows:
                row_dict = dict(zip(col_names, row))
                if pk_name and pk_name in row_dict:
                    k = (base_model, row_dict[pk_name])
                    if k in self._identity_map:
                        result_list.append(self._identity_map[k])
                        continue

                instance = base_model(**row_dict)
                try:
                    setattr(instance, "__session__", self)
                    # Mark as already in DB so add() will UPDATE, not INSERT
                    setattr(instance, "_psqlmodel_flushed_", True)
                    # Save original state for dirty tracking
                    cols = getattr(base_model, "__columns__", {})
                    original = {name: getattr(instance, name, None) for name in cols}
                    setattr(instance, "_psqlmodel_original_", original)
                except Exception:
                    pass
                self._add_to_cache(instance)
                result_list.append(instance)

            if getattr(query, "includes", None):
                self._load_includes_sync(result_list, query.includes)

            return QueryResult(result_list, model_cls=base_model)
        
        # 2. Mixed / Partial Selection Logic (Layout based) - Applied to ANY query with layout
        if getattr(query, "_layout", None):
            rows = self._tx._execute_sql_in_tx_sync(sql, list(query_params))
            rows = rows or []
            
            result_list = []
            layout = query._layout
            
            # Pre-calculate model column maps to avoid re-doing it per row
            layout_metadata = []
            for item in layout:
                if item["type"] == "model":
                    model_cls = item["model"]
                    col_names = list(getattr(model_cls, "__columns__", {}).keys())
                    pk_name = None
                    for name, col in getattr(model_cls, "__columns__", {}).items():
                        if getattr(col, "primary_key", False):
                            pk_name = name
                            break
                    layout_metadata.append({
                        "col_names": col_names,
                        "pk_name": pk_name
                    })
                else:
                    layout_metadata.append(None)

            import json

            for row in rows:
                row_values = []
                key_map = {}
                
                for i, item in enumerate(layout):
                    item_type = item["type"]
                    
                    if item_type == "model":
                        # Hydrate Model
                        start, end = item["start"], item["end"]
                        model_cls = item["model"]
                        meta = layout_metadata[i]
                        
                        # Slice row
                        model_data = row[start:end]
                        row_dict = dict(zip(meta["col_names"], model_data))
                        
                        # Identity Map Check
                        instance = None
                        if meta["pk_name"] and meta["pk_name"] in row_dict:
                            k = (model_cls, row_dict[meta["pk_name"]])
                            if k in self._identity_map:
                                instance = self._identity_map[k]
                        
                        if instance is None:
                            instance = model_cls(**row_dict) # This handles JSON parsing inside __init__
                            try:
                                setattr(instance, "__session__", self)
                                setattr(instance, "_psqlmodel_flushed_", True)
                                cols = getattr(model_cls, "__columns__", {})
                                original = {name: getattr(instance, name, None) for name in cols}
                                setattr(instance, "_psqlmodel_original_", original)
                            except Exception:
                                pass
                            self._add_to_cache(instance)
                        
                        row_values.append(instance)
                        
                    elif item_type == "scalar":
                        # Extract Value
                        val = row[item["index"]]
                        key = item["key"]
                        
                        # Handle JSON parsing for scalars
                        col_def = item.get("column")
                        if col_def and val is not None and isinstance(val, str):
                            type_hint = getattr(col_def, "type_hint", None)
                            if type_hint:
                                type_name = getattr(type_hint, "__name__", "")
                                if not type_name and hasattr(type_hint, "__class__"):
                                    type_name = type_hint.__class__.__name__
                                if type_name in ("json", "jsonb"):
                                    try:
                                        val = json.loads(val)
                                    except:
                                        pass

                        row_values.append(val)
                        if key:
                            key_map[key] = i
                
                # Store as RowResult (wrapper around tuple + keys)
                result_list.append(RowResult(tuple(row_values), key_map))
            
            return QueryResult(result_list, model_cls=None)
        self.engine._debug("[ENGINE] SQL: {} {}", sql, list(query_params) if query_params else [])

        cur = self._tx._conn.cursor()
        try:
            cur.execute(sql, list(query_params) if query_params else None)
            if not cur.description:
                result: List[Any] = []
            else:
                rows = cur.fetchall()
                col_names = [desc[0] for desc in cur.description]
                result = [dict(zip(col_names, row)) for row in rows]
        finally:
            cur.close()

        return QueryResult(result, model_cls=None)

    # ----------------------------------
    # Helpers de relaciones (sync)
    # ----------------------------------
    def _load_includes_sync(self, instances, includes):
        """Carga relaciones declaradas vía Include() para consultas sync."""
        if not instances or not includes:
            return

        try:
            from ..query.builder import Select, SelectQuery, IncludeSpec
        except Exception:
            from psqlmodel.query.builder import Select, SelectQuery, IncludeSpec  # type: ignore

        try:
            from ..orm.column import Column
        except Exception:
            from psqlmodel.orm.column import Column  # type: ignore

        owner_model = type(instances[0])

        for include_item in includes:
            # Unwrap IncludeSpec if present
            if isinstance(include_item, IncludeSpec):
                include_target = include_item.target
                children = include_item.children
            else:
                # Backwards compatibility: raw target without IncludeSpec wrapper
                include_target = include_item
                children = []
            
            target_model = None
            custom_query = None
            select_columns = None

            if isinstance(include_target, SelectQuery):
                custom_query = include_target
                if include_target.select_all and hasattr(include_target, "_from_model"):
                    target_model = include_target._from_model
                elif getattr(include_target, "columns", None):
                    first_col = include_target.columns[0]
                    expr = first_col.expr if hasattr(first_col, "expr") else first_col
                    if hasattr(expr, "model"):
                        target_model = expr.model
            elif isinstance(include_target, type):
                target_model = include_target
            elif isinstance(include_target, Column):
                target_model = include_target.model
                select_columns = [include_target]
            # Handle Relation/Relationship objects like Post.author
            elif hasattr(include_target, "_resolve_target") and hasattr(include_target, "attr_name"):
                # This is a Relation descriptor
                try:
                    target_model = include_target._resolve_target()
                except Exception:
                    pass
            else:
                continue

            if not target_model:
                continue

            rel_info = self._detect_relationship(owner_model, target_model)
            if not rel_info:
                continue

            rel_type = rel_info["type"]
            fk_name = rel_info["fk_name"]
            attr_name = rel_info["attr_name"]

            # ONE-TO-MANY
            if rel_type == "one_to_many":
                owner_pk = None
                for name, col in getattr(owner_model, "__columns__", {}).items():
                    if getattr(col, "primary_key", False):
                        owner_pk = name
                        break
                if owner_pk is None:
                    continue

                owner_ids = [getattr(inst, owner_pk) for inst in instances]
                fk_col = getattr(target_model, fk_name, None)
                if fk_col is None:
                    continue

                if custom_query:
                    # For partial column selections, ensure FK is included
                    if not custom_query.select_all:
                        # Check if FK is already in the selected columns
                        fk_sql = fk_col.to_sql()
                        cols = getattr(custom_query, "columns", [])
                        has_fk = any(
                            getattr(c, "to_sql", lambda: "")() == fk_sql
                            if hasattr(c, "to_sql")
                            else (hasattr(c, "expr") and getattr(c.expr, "to_sql", lambda: "")() == fk_sql)
                            for c in cols
                        )
                        if not has_fk:
                            # Add FK to the columns - need to rebuild the query
                            new_cols = list(cols) + [fk_col]
                            from ..query.builder import Select as _Select
                            query2 = _Select(*new_cols)
                            # Copy over the custom query's conditions
                            if hasattr(custom_query, "where_clause") and custom_query.where_clause:
                                query2.where_clause = custom_query.where_clause
                            if hasattr(custom_query, "order_by_list") and custom_query.order_by_list:
                                query2.order_by_list = custom_query.order_by_list
                            if hasattr(custom_query, "limit_value") and custom_query.limit_value:
                                query2.limit_value = custom_query.limit_value
                            if hasattr(custom_query, "offset_value") and custom_query.offset_value:
                                query2.offset_value = custom_query.offset_value
                            query2 = query2.Where(fk_col).In(owner_ids)
                        else:
                            query2 = custom_query.Where(fk_col).In(owner_ids)
                    else:
                        query2 = custom_query.Where(fk_col).In(owner_ids)
                else:
                    if select_columns:
                        cols_to_select = list(select_columns)
                        fk_sql = fk_col.to_sql()
                        has_fk = any(getattr(c, "to_sql", lambda: "")() == fk_sql for c in cols_to_select)
                        if not has_fk:
                            cols_to_select.append(fk_col)
                        query2 = Select(*cols_to_select).Where(fk_col).In(owner_ids)
                    else:
                        query2 = Select(target_model).Where(fk_col).In(owner_ids)

                related_items = self.exec(query2).all()

                grouped: dict[Any, list[Any]] = {}
                for item in related_items:
                    fk_value = None
                    extracted_value = item
                    if isinstance(item, dict):
                        fk_value = item.get(fk_name)
                        # For partial selections, create a clean dict without the FK
                        if len(item) > 1:
                            extracted_value = {k: v for k, v in item.items() if k != fk_name}
                        else:
                            # Single non-FK column, extract the value
                            for k, v in item.items():
                                if k != fk_name:
                                    extracted_value = v
                                    break
                    else:
                        fk_value = getattr(item, fk_name, None)

                    if fk_value is not None:
                        grouped.setdefault(fk_value, []).append(extracted_value)

                for inst in instances:
                    pk_value = getattr(inst, owner_pk, None)
                    try:
                        setattr(inst, attr_name, grouped.get(pk_value, []))
                    except Exception:
                        pass
                
                # Recursively process nested includes on loaded items
                if children and related_items:
                    # Filter to only model instances (not dicts from partial selects)
                    nested_instances = [item for item in related_items if hasattr(item, '__class__') and hasattr(item.__class__, '__tablename__')]
                    if nested_instances:
                        self._load_includes_sync(nested_instances, children)

            # MANY-TO-ONE / ONE-TO-ONE
            elif rel_type in ("many_to_one", "one_to_one"):
                # Determine if FK is in owner or target model
                fk_in_owner = fk_name in getattr(owner_model, "__columns__", {})
                fk_in_target = fk_name in getattr(target_model, "__columns__", {})
                
                if fk_in_owner:
                    # Standard many_to_one/one_to_one: FK is in owner, query target by PK
                    fk_values = [getattr(inst, fk_name, None) for inst in instances if hasattr(inst, fk_name)]
                    fk_values = [v for v in fk_values if v is not None]
                    if not fk_values:
                        continue

                    target_pk = None
                    for name, col in getattr(target_model, "__columns__", {}).items():
                        if getattr(col, "primary_key", False):
                            target_pk = name
                            break
                    if target_pk is None:
                        continue

                    pk_col = getattr(target_model, target_pk, None)
                    if pk_col is None:
                        continue

                    if custom_query:
                        query2 = custom_query.Where(pk_col).In(fk_values)
                    else:
                        if select_columns:
                            query2 = Select(*select_columns).Where(pk_col).In(fk_values)
                        else:
                            query2 = Select(target_model).Where(pk_col).In(fk_values)

                    related_items = self.exec(query2).all()

                    items_map: dict[Any, Any] = {}
                    for item in related_items:
                        pk_value = item.get(target_pk) if isinstance(item, dict) else getattr(item, target_pk, None)
                        if pk_value is not None:
                            items_map[pk_value] = item

                    for inst in instances:
                        if hasattr(inst, fk_name):
                            fk_value = getattr(inst, fk_name, None)
                            try:
                                setattr(inst, attr_name, items_map.get(fk_value))
                            except Exception:
                                pass
                    
                elif fk_in_target:
                    # INVERSE one_to_one: FK is in target, query target by FK = owner's PK
                    owner_pk = None
                    for name, col in getattr(owner_model, "__columns__", {}).items():
                        if getattr(col, "primary_key", False):
                            owner_pk = name
                            break
                    if owner_pk is None:
                        continue

                    owner_ids = [getattr(inst, owner_pk) for inst in instances]
                    fk_col = getattr(target_model, fk_name, None)
                    if fk_col is None:
                        continue

                    if custom_query:
                        query2 = custom_query.Where(fk_col).In(owner_ids)
                    else:
                        if select_columns:
                            query2 = Select(*select_columns).Where(fk_col).In(owner_ids)
                        else:
                            query2 = Select(target_model).Where(fk_col).In(owner_ids)

                    related_items = self.exec(query2).all()

                    # Map by FK value (which corresponds to owner's PK)
                    items_map: dict[Any, Any] = {}
                    for item in related_items:
                        fk_value = item.get(fk_name) if isinstance(item, dict) else getattr(item, fk_name, None)
                        if fk_value is not None:
                            items_map[fk_value] = item

                    for inst in instances:
                        pk_value = getattr(inst, owner_pk, None)
                        try:
                            setattr(inst, attr_name, items_map.get(pk_value))
                        except Exception:
                            pass
                else:
                    continue
                
                # Recursively process nested includes on loaded items
                if children and related_items:
                    nested_instances = [item for item in related_items if hasattr(item, '__class__') and hasattr(item.__class__, '__tablename__')]
                    if nested_instances:
                        self._load_includes_sync(nested_instances, children)

            # MANY-TO-MANY
            elif rel_type == "many_to_many":
                owner_pk = None
                for name, col in getattr(owner_model, "__columns__", {}).items():
                    if getattr(col, "primary_key", False):
                        owner_pk = name
                        break
                if owner_pk is None:
                    continue

                owner_ids = [getattr(inst, owner_pk, None) for inst in instances]
                owner_ids = [v for v in owner_ids if v is not None]
                if not owner_ids:
                    continue

                relations = getattr(owner_model, "__relations__", {})
                rel_obj = None
                for _attr_name2, rel_candidate in relations.items():
                    try:
                        target = rel_candidate._resolve_target()
                    except Exception:
                        target = None
                    if target is target_model:
                        rel_obj = rel_candidate
                        break

                junction = getattr(rel_obj, "secondary", None) if rel_obj else None
                if not junction:
                    continue

                def singular(name: str) -> str:
                    return name[:-1] if name.endswith("s") else name

                owner_table = getattr(owner_model, "__tablename__", owner_model.__name__.lower())
                target_table = getattr(target_model, "__tablename__", target_model.__name__.lower())
                owner_fk = f"{singular(owner_table)}_id"
                target_fk = f"{singular(target_table)}_id"

                schema = getattr(owner_model, "__schema__", "public") or "public"
                junction_full = junction if "." in junction else f"{schema}.{junction}"

                cur = self._tx._conn.cursor()
                try:
                    cur.execute(
                        f"SELECT {owner_fk}, {target_fk} FROM {junction_full} WHERE {owner_fk} = ANY(%s)",
                        (owner_ids,),
                    )
                    rows = cur.fetchall()
                finally:
                    cur.close()

                by_owner: dict[Any, list[Any]] = {}
                target_ids: set[Any] = set()
                for row_owner, row_target in rows:
                    by_owner.setdefault(row_owner, []).append(row_target)
                    if row_target is not None:
                        target_ids.add(row_target)

                if not target_ids:
                    for inst in instances:
                        try:
                            setattr(inst, attr_name, [])
                        except Exception:
                            pass
                    continue

                target_pk = None
                for name, col in getattr(target_model, "__columns__", {}).items():
                    if getattr(col, "primary_key", False):
                        target_pk = name
                        break
                if target_pk is None:
                    continue

                pk_col = getattr(target_model, target_pk, None)
                if pk_col is None:
                    continue

                if select_columns:
                    cols_to_select = list(select_columns)
                    pk_sql = pk_col.to_sql()
                    has_pk = any(getattr(c, "to_sql", lambda: "")() == pk_sql for c in cols_to_select)
                    if not has_pk:
                        cols_to_select.append(pk_col)
                    query2 = Select(*cols_to_select).Where(pk_col).In(list(target_ids))
                else:
                    query2 = Select(target_model).Where(pk_col).In(list(target_ids))

                related_items = self.exec(query2).all()

                items_map: dict[Any, Any] = {}
                for item in related_items:
                    pk_value = item.get(target_pk) if isinstance(item, dict) else getattr(item, target_pk, None)
                    if pk_value is not None:
                        items_map[pk_value] = item

                for inst in instances:
                    pk_value = getattr(inst, owner_pk, None)
                    ids_for_owner = by_owner.get(pk_value, [])
                    try:
                        setattr(inst, attr_name, [items_map[i] for i in ids_for_owner if i in items_map])
                    except Exception:
                        pass
                
                # Recursively process nested includes on loaded items
                if children and related_items:
                    nested_instances = [item for item in related_items if hasattr(item, '__class__') and hasattr(item.__class__, '__tablename__')]
                    if nested_instances:
                        self._load_includes_sync(nested_instances, children)
    
    # NOTE: _detect_relationship, _normalize_fk_ref, _add_to_cache, _evict_from_cache inherited from _SessionMixin

    def _cascade_delete(self, model: "PSQLModel") -> None:
        """Handle ORM-level cascade deletes for relationships.
        
        Iterates through model's relations and deletes children that have:
        - cascade=True (or "delete" in cascade set)
        - passive_deletes=False (if True, relies on DB-level ON DELETE CASCADE)
        """
        relations = getattr(model.__class__, "__relations__", {})
        
        for rel_name, relation in relations.items():
            # Check if this relationship has cascade delete
            cascade_ops = getattr(relation, "cascade", set())
            passive = getattr(relation, "passive_deletes", False)
            
            # Skip if no delete cascade or using passive deletes (DB handles it)
            if "delete" not in cascade_ops or passive:
                continue
            
            # Get the related objects
            try:
                related = getattr(model, rel_name, None)
            except Exception:
                continue
            
            if related is None:
                continue
            
            # Handle both single objects and collections
            if isinstance(related, list):
                for child in list(related):  # Copy to avoid mutation during iteration
                    self.delete(child)  # Recursive cascade
            elif hasattr(related, "__tablename__"):  # It's a model
                self.delete(related)

    # ----------------------------------
    # Atajos exec_* y paralelismo
    # ----------------------------------
    def exec_one(self, query: Any) -> Any:
        """Execute a query and return only the first result (or None)."""
        result = self.exec(query)
        return result.first()

    def exec_scalar(self, query: Any) -> Any:
        """Execute a query and return the first column of the first row."""
        first_row = self.exec(query).first()
        if first_row is None:
            return None
        if isinstance(first_row, dict):
            return next(iter(first_row.values())) if first_row else None
        cols = getattr(first_row.__class__, "__columns__", {})
        if cols:
            first_name = next(iter(cols.keys()))
            return getattr(first_row, first_name, None)
        return first_row

    def parallel_exec(self, tasks: list[Any], *, max_workers: int | None = None) -> list[Any]:
        """Ejecuta múltiples consultas en paralelo usando el Engine (sync).

        IMPORTANTE:
        - Usa el pool del Engine, no la conexión de esta Session.
        - Por tanto, NO forma parte de la misma transacción que la Session.
        - Útil para lecturas en paralelo (reporting, dashboards, etc.).
        """
        return self.engine.parallel_execute(tasks, max_workers=max_workers)


# ============================================================
# Asynchronous Session
# ============================================================

class AsyncSession(_SessionMixin):
    """Asynchronous session wrapper around Transaction.

    Pensada para usar con Engine async:

        async def get_async_session():
            async with AsyncSession(engine) as session:
                yield session
    """

    # ----------------------------------
    # Métodos de alto nivel (flush/tx)
    # ----------------------------------
    async def flush(self) -> None:
        """Flush explícito en modo async."""
        await self._ensure_transaction()
        if self._tx is None or self._tx._conn is None:
            raise RuntimeError("AsyncSession is not active. Use it inside an 'async with' block.")

        # Register any pending inserts added before transaction was created
        if hasattr(self, "_pending_inserts"):
            for model in self._pending_inserts:
                self._tx.register(model)
            self._pending_inserts.clear()

        await self._tx._run_hooks_async("before_flush")  # type: ignore[attr-defined]
        for model in list(getattr(self._tx, "_inserts", [])):
            await self._tx._flush_model_async(self._tx._conn, model, op="insert")
        for model in list(getattr(self._tx, "_updates", [])):
            await self._tx._flush_model_async(self._tx._conn, model, op="update")
        for model in list(getattr(self._tx, "_deletes", [])):
            await self._tx._flush_model_async(self._tx._conn, model, op="delete")
        await self._tx._run_hooks_async("after_flush")  # type: ignore[attr-defined]

        self._tx._inserts.clear()
        self._tx._updates.clear()
        self._tx._deletes.clear()

    async def commit(self) -> None:
        """Commit explicito (async).

        - Si atomic=True: Cierra la sesión.
        - Si atomic=False (default): Cierra sólo la transacción; la sesión sigue abierta.
        - Si expire_on_commit=True: Marca todos los objetos en identity map como expired.
        
        Autobegin: If there are pending inserts and no active transaction,
        a new transaction is started automatically (non-atomic mode only).
        """
        # Autobegin: start a new transaction if there are pending operations
        has_pending = hasattr(self, "_pending_inserts") and self._pending_inserts
        
        if self._tx is None and has_pending:
            # Start a new transaction to handle the pending inserts
            await self._ensure_transaction()
        
        if self._tx is None:
            # No transaction and no pending operations - nothing to commit
            return

        # Flush pending inserts before commit
        if hasattr(self, "_pending_inserts") and self._pending_inserts:
            for model in self._pending_inserts:
                self._tx.register(model)
            self._pending_inserts.clear()

        await self._tx.__aexit__(None, None, None)
        self._tx = None

        # Mark all objects as expired if expire_on_commit=True
        if self._expire_on_commit:
            for key in self._identity_map:
                self._expired.add(key)

        if self._atomic:
            self._closed = True

    async def rollback(self) -> None:
        """Rollback explicito (async).

        - Si atomic=True: Cierra la sesión.
        - Si atomic=False (default): Cierra sólo la transacción; la sesión sigue abierta.
        """
        if self._tx is None:
            raise RuntimeError("AsyncSession is not active. Use it inside an 'async with' block.")

        class _AsyncSessionRollback(Exception):
            pass

        await self._tx.__aexit__(_AsyncSessionRollback, _AsyncSessionRollback("manual rollback"), None)
        self._tx = None

        if self._atomic:
            self._closed = True

    async def refresh(self, model: "PSQLModel") -> None:
        """Reload model from DB in same TX (async)."""
        await self._ensure_transaction()
        if self._tx is None or self._tx._conn is None:
            raise RuntimeError("AsyncSession is not active.")

        pk_name = None
        cols = getattr(model.__class__, "__columns__", {})
        for name, col in cols.items():
            if getattr(col, "primary_key", False):
                pk_name = name
                break
        if pk_name is None:
            raise ValueError("No primary key defined")

        pk_value = getattr(model, pk_name, None)
        if pk_value is None:
            raise ValueError("Primary key value is None; cannot refresh")

        table = getattr(model, "__tablename__")
        schema = getattr(model, "__schema__", "public") or "public"

        col_names = list(cols.keys())
        select_list = ", ".join(col_names) if col_names else "*"
        sql = f"SELECT {select_list} FROM {schema}.{table} WHERE {pk_name} = $1"

        rows = await self._tx._execute_sql_in_tx_async(sql, [pk_value])  # type: ignore[attr-defined]
        if rows:
            row0 = rows[0]
            row_dict = dict(row0)
            for name in col_names:
                if name in row_dict:
                    try:
                        setattr(model, name, row_dict[name])
                    except Exception:
                        pass

        self._add_to_cache(model)

    async def delete(self, model: "PSQLModel") -> None:
        """Delete a model with cascade support for relationships.
        
        If related objects have cascade=True, they are deleted first.
        If passive_deletes=True, relies on database ON DELETE CASCADE.
        """
        await self._ensure_transaction()
        if self._tx is None or self._tx._conn is None:
            raise RuntimeError("AsyncSession is not active. Use it inside an 'async with' block.")

        # Handle cascade deletes for relationships
        await self._cascade_delete(model)

        self._tx.register(model, op="delete")
        await self._tx._flush_model_async(self._tx._conn, model, op="delete")

        # Evitar doble DELETE al hacer commit/exit (si quedó en la cola)
        try:
            if model in self._tx._deletes:
                self._tx._deletes.remove(model)
        except Exception:
            pass

        self._evict_from_cache(model)

    async def bulk_insert(self, models: list) -> None:
        await self._ensure_transaction()
        if self._tx is None:
            raise RuntimeError("AsyncSession is not active. Use it inside an 'async with' block.")
        await self._tx.bulk_insert_async(models)

    async def bulk_update(self, models: list) -> None:
        await self._ensure_transaction()
        if self._tx is None:
            raise RuntimeError("AsyncSession is not active. Use it inside an 'async with' block.")
        await self._tx.bulk_update_async(models)

    # ----------------------------------
    # Constructor / context manager
    # ----------------------------------
    def __init__(
        self,
        engine: "Engine",
        auto_commit: bool = False,
        auto_rollback: bool = True,
        atomic: bool = False,
        expire_on_commit: bool = False,
    ):
        self.engine = engine
        self._tx: Optional[Transaction] = None
        self._closed: bool = False

        self._auto_commit = auto_commit
        self._auto_rollback = auto_rollback
        self._atomic = atomic
        self._expire_on_commit = expire_on_commit

        self._identity_map: dict[tuple[type, Any], Any] = {}
        self._expired: set[tuple[type, Any]] = set()
        self._ctx_token: Optional[Token] = None
        
        # Autoflush control
        self._autoflush = True
        
        # Event hooks
        self._before_flush_hooks: list = []
        self._after_commit_hooks: list = []
        self._after_rollback_hooks: list = []

    async def __aenter__(self) -> "AsyncSession":
        if not self.engine.config.async_:
            raise RuntimeError("Engine sync; use Session(engine) en su lugar.")
        if self._closed:
            raise RuntimeError("AsyncSession is already closed.")
        if self._tx is not None:
            raise RuntimeError("AsyncSession is already active.")

        self._tx = Transaction(self.engine)
        await self._tx.__aenter__()

        self._ctx_token = _current_async_session.set(self)
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        # Siempre limpiar el contextvar
        if self._ctx_token is not None:
            _current_async_session.reset(self._ctx_token)
            self._ctx_token = None

        if self._tx is None:
            self._closed = True
            return

        if self._closed:
            self._tx = None
            return

        # Lógica auto_commit / auto_rollback
        if exc_type is not None:
            if self._auto_rollback:
                await self._tx.__aexit__(exc_type, exc, tb)
            else:
                await self._tx.__aexit__(exc_type, exc, tb)
        else:
            if self._auto_commit:
                # Flush pending inserts before auto commit
                if hasattr(self, "_pending_inserts") and self._pending_inserts:
                    for model in self._pending_inserts:
                        self._tx.register(model)
                    self._pending_inserts.clear()
                await self._tx.__aexit__(None, None, None)
            elif self._auto_rollback:
                class _AutoRollback(Exception):
                    pass

                await self._tx.__aexit__(
                    _AutoRollback,
                    _AutoRollback("auto rollback end-of-context"),
                    None,
                )
            else:
                class _SafeRollback(Exception):
                    pass

                await self._tx.__aexit__(
                    _SafeRollback,
                    _SafeRollback("safe rollback (auto_commit=False, auto_rollback=False)"),
                    None,
                )

        self._tx = None
        # Igual que Session(sync): salir del context manager siempre cierra la sesión
        self._closed = True

    async def _ensure_transaction(self) -> None:
        """Asegura que haya una transacción activa (async)."""
        if self._closed:
            raise RuntimeError("AsyncSession is closed.")

        if self._tx is None:
            if self._atomic:
                raise RuntimeError("AsyncSession is not active (atomic mode).")

            self._tx = Transaction(self.engine)
            await self._tx.__aenter__()

    # ----------------------------------
    # API de modelos (async)
    # ----------------------------------
    def add(self, model: "PSQLModel") -> None:
        """Register model for insertion (sync).
        
        The transaction is created lazily on flush/commit, not here.
        This just registers the model in memory.
        """
        # Lazy init of pending inserts if no transaction yet
        if not hasattr(self, "_pending_inserts"):
            self._pending_inserts: list = []
        
        if self._tx is not None:
            self._tx.register(model)
        else:
            # Store for later when transaction is created
            self._pending_inserts.append(model)
        
        try:
            setattr(model, "__session__", self)
        except Exception:
            pass
        self._add_to_cache(model)

    async def get(self, model_cls: type, pk_value: Any):
        """Get model by primary key with identity map caching (async)."""
        if pk_value is None:
            return None

        key = (model_cls, pk_value)
        if key in self._identity_map:
            return self._identity_map[key]

        pk_name = None
        for name, col in getattr(model_cls, "__columns__", {}).items():
            if getattr(col, "primary_key", False):
                pk_name = name
                break
        if pk_name is None:
            raise ValueError(f"Modelo {model_cls.__name__} no tiene primary key definida.")

        try:
            from ..query.builder import Select
        except Exception:
            from psqlmodel.query.builder import Select  # type: ignore

        pk_col = getattr(model_cls, pk_name)
        res = await self.exec(Select(model_cls).Where(pk_col == pk_value)).first()
        if res:
            # Ensure model is marked as existing in DB (safety, exec should do this)
            try:
                if not getattr(res, "_psqlmodel_flushed_", False):
                    setattr(res, "_psqlmodel_flushed_", True)
                    cols = getattr(model_cls, "__columns__", {})
                    original = {name: getattr(res, name, None) for name in cols}
                    setattr(res, "_psqlmodel_original_", original)
            except Exception:
                pass
            self._add_to_cache(res)
        return res

    # ----------------------------------
    # Helper methods
    # ----------------------------------
    # NOTE: _add_to_cache, _evict_from_cache, _normalize_fk_ref are inherited from _SessionMixin

    async def _cascade_delete(self, model: "PSQLModel") -> None:
        """Handle ORM-level cascade deletes for relationships (async).
        
        Iterates through model's relations and deletes children that have:
        - cascade=True (or "delete" in cascade set)
        - passive_deletes=False (if True, relies on DB-level ON DELETE CASCADE)
        """
        relations = getattr(model.__class__, "__relations__", {})
        
        for rel_name, relation in relations.items():
            # Check if this relationship has cascade delete
            cascade_ops = getattr(relation, "cascade", set())
            passive = getattr(relation, "passive_deletes", False)
            
            # Skip if no delete cascade or using passive deletes (DB handles it)
            if "delete" not in cascade_ops or passive:
                continue
            
            # Get the related objects
            try:
                related = getattr(model, rel_name, None)
            except Exception:
                continue
            
            if related is None:
                continue
            
            # Handle both single objects and collections
            if isinstance(related, list):
                for child in list(related):  # Copy to avoid mutation during iteration
                    await self.delete(child)  # Recursive cascade
            elif hasattr(related, "__tablename__"):  # It's a model
                await self.delete(related)

    # ----------------------------------
    # Exec de queries (async)
    # ----------------------------------
    def exec(self, query: Any, *, params: Sequence[Any] | None = None) -> AsyncQueryResult:
        """Execute a query builder (Select, Insert, Update, Delete, etc.) or raw SQL asynchronously."""

        async def _execute() -> List[Any]:
            await self._ensure_transaction()
            if self._tx is None or self._tx._conn is None:
                raise RuntimeError("AsyncSession is not active. Use it inside an 'async with' block.")

            sql: str
            query_params: Sequence[Any]

            if isinstance(query, str):
                sql = query
                query_params = params or []
            elif hasattr(query, "to_sql_params"):
                sql, query_params = query.to_sql_params()
            elif hasattr(query, "to_sql"):
                sql = query.to_sql()
                query_params = []
            else:
                raise ValueError("Query must be a string or have to_sql_params() or to_sql() method")

            rows = await self._tx._execute_sql_in_tx_async(sql, list(query_params))  # type: ignore[attr-defined]
            rows = rows or []

            # Try import SelectQuery robustly
            SelectQuery = None
            try:
                from ..query.builder import SelectQuery as _SelectQuery  # type: ignore
                SelectQuery = _SelectQuery
            except Exception:
                try:
                    from psqlmodel.query.builder import SelectQuery as _SelectQuery  # type: ignore
                    SelectQuery = _SelectQuery
                except Exception:
                    SelectQuery = None

            if (
                SelectQuery is not None
                and isinstance(query, SelectQuery)
                and bool(getattr(query, "select_all", False))
            ):
                # 1. Standard "Select(Model)" logic (Backwards Compatibility)
                result: List[Any] = []

                pk_name = None
                for name, col in getattr(query.base_model, "__columns__", {}).items():
                    if getattr(col, "primary_key", False):
                        pk_name = name
                        break

                for row in rows:
                    row_dict = dict(row)
                    if pk_name and pk_name in row_dict:
                        k = (query.base_model, row_dict[pk_name])
                        if k in self._identity_map:
                            result.append(self._identity_map[k])
                            continue

                    instance = query.base_model(**row_dict)
                    try:
                        setattr(instance, "__session__", self)
                        # Mark as already in DB so add() will UPDATE, not INSERT
                        setattr(instance, "_psqlmodel_flushed_", True)
                        # Save original state for dirty tracking
                        cols = getattr(query.base_model, "__columns__", {})
                        original = {name: getattr(instance, name, None) for name in cols}
                        setattr(instance, "_psqlmodel_original_", original)
                    except Exception:
                        pass
                    self._add_to_cache(instance)
                    result.append(instance)

                if getattr(query, "includes", None) and result:
                    await self._load_includes_async(result, query.includes)

                return result
            
            # 2. Mixed / Partial Selection Logic (Layout based) - Applied to ANY query with layout
            if getattr(query, "_layout", None):
                result_list = []
                layout = query._layout
                
                # Pre-calculate model column maps to avoid re-doing it per row
                layout_metadata = []
                for item in layout:
                    if item["type"] == "model":
                        model_cls = item["model"]
                        col_names = list(getattr(model_cls, "__columns__", {}).keys())
                        pk_name = None
                        for name, col in getattr(model_cls, "__columns__", {}).items():
                            if getattr(col, "primary_key", False):
                                pk_name = name
                                break
                        layout_metadata.append({
                            "col_names": col_names,
                            "pk_name": pk_name
                        })
                    else:
                        layout_metadata.append(None)

                import json

                for row in rows:
                    row_values = []
                    key_map = {}
                    
                    for i, item in enumerate(layout):
                        item_type = item["type"]
                        
                        if item_type == "model":
                            # Hydrate Model
                            start, end = item["start"], item["end"]
                            model_cls = item["model"]
                            meta = layout_metadata[i]
                            
                            # Slice row
                            model_data = row[start:end]
                            row_dict = dict(zip(meta["col_names"], model_data))
                            
                            # Identity Map Check
                            instance = None
                            if meta["pk_name"] and meta["pk_name"] in row_dict:
                                k = (model_cls, row_dict[meta["pk_name"]])
                                if k in self._identity_map:
                                    instance = self._identity_map[k]
                            
                            if instance is None:
                                instance = model_cls(**row_dict) # This handles JSON parsing inside __init__
                                try:
                                    setattr(instance, "__session__", self)
                                    setattr(instance, "_psqlmodel_flushed_", True)
                                    cols = getattr(model_cls, "__columns__", {})
                                    original = {name: getattr(instance, name, None) for name in cols}
                                    setattr(instance, "_psqlmodel_original_", original)
                                except Exception:
                                    pass
                                self._add_to_cache(instance)
                            
                            row_values.append(instance)
                            
                        elif item_type == "scalar":
                            # Extract Value
                            val = row[item["index"]]
                            key = item["key"]
                            
                            # Handle JSON parsing for scalars
                            col_def = item.get("column")
                            if col_def and val is not None and isinstance(val, str):
                                type_hint = getattr(col_def, "type_hint", None)
                                if type_hint:
                                    type_name = getattr(type_hint, "__name__", "")
                                    if not type_name and hasattr(type_hint, "__class__"):
                                        type_name = type_hint.__class__.__name__
                                    if type_name in ("json", "jsonb"):
                                        try:
                                            val = json.loads(val)
                                        except:
                                            pass

                            row_values.append(val)
                            if key:
                                key_map[key] = i
                    
                    # Store as RowResult (wrapper around tuple + keys)
                    result_list.append(RowResult(tuple(row_values), key_map))
                
                return result_list

            # Non-model results
            return [dict(r) for r in rows] if rows else []

        return AsyncQueryResult(_execute())

    async def _load_includes_async(self, instances, includes):
        """Load related objects for Include() - auto-detects relationships."""
        if not instances or not includes:
            return

        try:
            from ..query.builder import Select, SelectQuery, IncludeSpec
        except Exception:
            from psqlmodel.query.builder import Select, SelectQuery, IncludeSpec  # type: ignore

        try:
            from ..orm.column import Column
        except Exception:
            from psqlmodel.orm.column import Column  # type: ignore

        owner_model = type(instances[0])

        for include_item in includes:
            # Unwrap IncludeSpec if present
            if isinstance(include_item, IncludeSpec):
                include_target = include_item.target
                children = include_item.children
            else:
                # Backwards compatibility: raw target without IncludeSpec wrapper
                include_target = include_item
                children = []
            
            target_model = None
            custom_query = None
            select_columns = None

            if isinstance(include_target, SelectQuery):
                custom_query = include_target
                if include_target.select_all and hasattr(include_target, "_from_model"):
                    target_model = include_target._from_model
                elif getattr(include_target, "columns", None):
                    first_col = include_target.columns[0]
                    expr = first_col.expr if hasattr(first_col, "expr") else first_col
                    if hasattr(expr, "model"):
                        target_model = expr.model
            elif isinstance(include_target, type):
                target_model = include_target
            elif isinstance(include_target, Column):
                target_model = include_target.model
                select_columns = [include_target]
            # Handle Relation/Relationship objects like Post.author
            elif hasattr(include_target, "_resolve_target") and hasattr(include_target, "attr_name"):
                # This is a Relation descriptor
                try:
                    target_model = include_target._resolve_target()
                except Exception:
                    pass
            else:
                continue

            if not target_model:
                continue

            rel_info = self._detect_relationship(owner_model, target_model)
            if not rel_info:
                continue

            rel_type = rel_info["type"]
            fk_name = rel_info["fk_name"]
            attr_name = rel_info["attr_name"]

            # ONE-TO-MANY
            if rel_type == "one_to_many":
                owner_pk = None
                for name, col in getattr(owner_model, "__columns__", {}).items():
                    if getattr(col, "primary_key", False):
                        owner_pk = name
                        break
                if owner_pk is None:
                    continue

                owner_ids = [getattr(inst, owner_pk, None) for inst in instances]
                owner_ids = [v for v in owner_ids if v is not None]
                if not owner_ids:
                    continue

                fk_col = getattr(target_model, fk_name, None)
                if fk_col is None:
                    continue

                if custom_query:
                    # For partial column selections, ensure FK is included
                    if not custom_query.select_all:
                        # Check if FK is already in the selected columns
                        fk_sql = fk_col.to_sql()
                        cols = getattr(custom_query, "columns", [])
                        has_fk = any(
                            getattr(c, "to_sql", lambda: "")() == fk_sql
                            if hasattr(c, "to_sql")
                            else (hasattr(c, "expr") and getattr(c.expr, "to_sql", lambda: "")() == fk_sql)
                            for c in cols
                        )
                        if not has_fk:
                            # Add FK to the columns - need to rebuild the query
                            new_cols = list(cols) + [fk_col]
                            from ..query.builder import Select as _Select
                            query2 = _Select(*new_cols)
                            # Copy over the custom query's conditions
                            if hasattr(custom_query, "where_clause") and custom_query.where_clause:
                                query2.where_clause = custom_query.where_clause
                            if hasattr(custom_query, "order_by_list") and custom_query.order_by_list:
                                query2.order_by_list = custom_query.order_by_list
                            if hasattr(custom_query, "limit_value") and custom_query.limit_value:
                                query2.limit_value = custom_query.limit_value
                            if hasattr(custom_query, "offset_value") and custom_query.offset_value:
                                query2.offset_value = custom_query.offset_value
                            query2 = query2.Where(fk_col).In(owner_ids)
                        else:
                            query2 = custom_query.Where(fk_col).In(owner_ids)
                    else:
                        query2 = custom_query.Where(fk_col).In(owner_ids)
                else:
                    if select_columns:
                        cols_to_select = list(select_columns)
                        fk_sql = fk_col.to_sql()
                        has_fk = any(getattr(c, "to_sql", lambda: "")() == fk_sql for c in cols_to_select)
                        if not has_fk:
                            cols_to_select.append(fk_col)
                        query2 = Select(*cols_to_select).Where(fk_col).In(owner_ids)
                    else:
                        query2 = Select(target_model).Where(fk_col).In(owner_ids)

                related_items = await self.exec(query2).all()

                grouped: dict[Any, list[Any]] = {}
                for item in related_items:
                    fk_value = None
                    extracted_value = item

                    if isinstance(item, dict):
                        fk_value = item.get(fk_name)
                        # For partial selections, create a clean dict without the FK
                        if len(item) > 1:
                            extracted_value = {k: v for k, v in item.items() if k != fk_name}
                        else:
                            # Single non-FK column, extract the value
                            for k, v in item.items():
                                if k != fk_name:
                                    extracted_value = v
                                    break
                    else:
                        fk_value = getattr(item, fk_name, None)

                    if fk_value is not None:
                        grouped.setdefault(fk_value, []).append(extracted_value)

                for inst in instances:
                    pk_value = getattr(inst, owner_pk, None)
                    try:
                        setattr(inst, attr_name, grouped.get(pk_value, []))
                    except Exception:
                        pass
                
                # Recursively process nested includes on loaded items
                if children and related_items:
                    nested_instances = [item for item in related_items if hasattr(item, '__class__') and hasattr(item.__class__, '__tablename__')]
                    if nested_instances:
                        await self._load_includes_async(nested_instances, children)

            # MANY-TO-ONE / ONE-TO-ONE
            elif rel_type in ("many_to_one", "one_to_one"):
                # Determine if FK is in owner or target model
                fk_in_owner = fk_name in getattr(owner_model, "__columns__", {})
                fk_in_target = fk_name in getattr(target_model, "__columns__", {})
                
                if fk_in_owner:
                    # Standard many_to_one/one_to_one: FK is in owner, query target by PK
                    fk_values = [getattr(inst, fk_name, None) for inst in instances if hasattr(inst, fk_name)]
                    fk_values = [v for v in fk_values if v is not None]
                    if not fk_values:
                        continue

                    target_pk = None
                    for name, col in getattr(target_model, "__columns__", {}).items():
                        if getattr(col, "primary_key", False):
                            target_pk = name
                            break
                    if target_pk is None:
                        continue

                    pk_col = getattr(target_model, target_pk, None)
                    if pk_col is None:
                        continue

                    if custom_query:
                        query2 = custom_query.Where(pk_col).In(fk_values)
                    else:
                        if select_columns:
                            query2 = Select(*select_columns).Where(pk_col).In(fk_values)
                        else:
                            query2 = Select(target_model).Where(pk_col).In(fk_values)

                    related_items = await self.exec(query2).all()

                    items_map: dict[Any, Any] = {}
                    for item in related_items:
                        pk_value = item.get(target_pk) if isinstance(item, dict) else getattr(item, target_pk, None)
                        if pk_value is not None:
                            items_map[pk_value] = item

                    for inst in instances:
                        if hasattr(inst, fk_name):
                            fk_value = getattr(inst, fk_name, None)
                            try:
                                setattr(inst, attr_name, items_map.get(fk_value))
                            except Exception:
                                pass
                    
                elif fk_in_target:
                    # INVERSE one_to_one: FK is in target, query target by FK = owner's PK
                    owner_pk = None
                    for name, col in getattr(owner_model, "__columns__", {}).items():
                        if getattr(col, "primary_key", False):
                            owner_pk = name
                            break
                    if owner_pk is None:
                        continue

                    owner_ids = [getattr(inst, owner_pk) for inst in instances]
                    fk_col = getattr(target_model, fk_name, None)
                    if fk_col is None:
                        continue

                    if custom_query:
                        query2 = custom_query.Where(fk_col).In(owner_ids)
                    else:
                        if select_columns:
                            query2 = Select(*select_columns).Where(fk_col).In(owner_ids)
                        else:
                            query2 = Select(target_model).Where(fk_col).In(owner_ids)

                    related_items = await self.exec(query2).all()

                    # Map by FK value (which corresponds to owner's PK)
                    items_map: dict[Any, Any] = {}
                    for item in related_items:
                        fk_value = item.get(fk_name) if isinstance(item, dict) else getattr(item, fk_name, None)
                        if fk_value is not None:
                            items_map[fk_value] = item

                    for inst in instances:
                        pk_value = getattr(inst, owner_pk, None)
                        try:
                            setattr(inst, attr_name, items_map.get(pk_value))
                        except Exception:
                            pass
                else:
                    continue
                
                # Recursively process nested includes on loaded items
                if children and related_items:
                    nested_instances = [item for item in related_items if hasattr(item, '__class__') and hasattr(item.__class__, '__tablename__')]
                    if nested_instances:
                        await self._load_includes_async(nested_instances, children)

            # MANY-TO-MANY
            elif rel_type == "many_to_many":
                owner_pk = None
                for name, col in getattr(owner_model, "__columns__", {}).items():
                    if getattr(col, "primary_key", False):
                        owner_pk = name
                        break
                if owner_pk is None:
                    continue

                owner_ids = [getattr(inst, owner_pk, None) for inst in instances]
                owner_ids = [v for v in owner_ids if v is not None]
                if not owner_ids:
                    continue

                relations = getattr(owner_model, "__relations__", {})
                rel_obj = None
                for _attr_name2, rel_candidate in relations.items():
                    try:
                        target = rel_candidate._resolve_target()
                    except Exception:
                        target = None
                    if target is target_model:
                        rel_obj = rel_candidate
                        break

                junction = getattr(rel_obj, "secondary", None) if rel_obj else None
                if not junction:
                    continue

                def singular(name: str) -> str:
                    return name[:-1] if name.endswith("s") else name

                owner_table = getattr(owner_model, "__tablename__", owner_model.__name__.lower())
                target_table = getattr(target_model, "__tablename__", target_model.__name__.lower())
                owner_fk = f"{singular(owner_table)}_id"
                target_fk = f"{singular(target_table)}_id"

                schema = getattr(owner_model, "__schema__", "public") or "public"
                junction_full = junction if "." in junction else f"{schema}.{junction}"

                rows = await self._tx._conn.fetch(  # type: ignore[union-attr]
                    f"SELECT {owner_fk}, {target_fk} FROM {junction_full} WHERE {owner_fk} = ANY($1)",
                    owner_ids,
                )

                by_owner: dict[Any, list[Any]] = {}
                target_ids: set[Any] = set()
                for row in rows:
                    row_owner = row[owner_fk]
                    row_target = row[target_fk]
                    by_owner.setdefault(row_owner, []).append(row_target)
                    if row_target is not None:
                        target_ids.add(row_target)

                if not target_ids:
                    for inst in instances:
                        try:
                            setattr(inst, attr_name, [])
                        except Exception:
                            pass
                    continue

                target_pk = None
                for name, col in getattr(target_model, "__columns__", {}).items():
                    if getattr(col, "primary_key", False):
                        target_pk = name
                        break
                if target_pk is None:
                    continue

                pk_col = getattr(target_model, target_pk, None)
                if pk_col is None:
                    continue

                if select_columns:
                    cols_to_select = list(select_columns)
                    pk_sql = pk_col.to_sql()
                    has_pk = any(getattr(c, "to_sql", lambda: "")() == pk_sql for c in cols_to_select)
                    if not has_pk:
                        cols_to_select.append(pk_col)
                    query2 = Select(*cols_to_select).Where(pk_col).In(list(target_ids))
                else:
                    query2 = Select(target_model).Where(pk_col).In(list(target_ids))

                related_items = await self.exec(query2).all()

                items_map: dict[Any, Any] = {}
                for item in related_items:
                    pk_value = item.get(target_pk) if isinstance(item, dict) else getattr(item, target_pk, None)
                    if pk_value is not None:
                        items_map[pk_value] = item

                for inst in instances:
                    pk_value = getattr(inst, owner_pk, None)
                    ids_for_owner = by_owner.get(pk_value, [])
                    try:
                        setattr(inst, attr_name, [items_map[i] for i in ids_for_owner if i in items_map])
                    except Exception:
                        pass
                
                # Recursively process nested includes on loaded items
                if children and related_items:
                    nested_instances = [item for item in related_items if hasattr(item, '__class__') and hasattr(item.__class__, '__tablename__')]
                    if nested_instances:
                        await self._load_includes_async(nested_instances, children)

    # NOTE: _detect_relationship, _normalize_fk_ref, _add_to_cache, _evict_from_cache inherited from _SessionMixin

    # ----------------------------------
    # Atajos exec_* y paralelismo
    # ----------------------------------
    async def exec_one(self, query: Any) -> Any:
        """Execute a query and return only the first result (or None)."""
        return await self.exec(query).first()

    async def exec_scalar(self, query: Any) -> Any:
        """Execute a query and return the first column of the first row."""
        first_row = await self.exec(query).first()
        if first_row is None:
            return None
        if isinstance(first_row, dict):
            return next(iter(first_row.values())) if first_row else None
        cols = getattr(first_row.__class__, "__columns__", {})
        if cols:
            first_name = next(iter(cols.keys()))
            return getattr(first_row, first_name, None)
        return first_row

    async def parallel_exec(self, tasks: list[Any], *, max_concurrency: int | None = None) -> list[Any]:
        """Ejecuta múltiples consultas en paralelo usando el Engine (async).

        Igual que en Session.parallel_exec:
        - Usa el pool del Engine, no la conexión de esta AsyncSession.
        - No forma parte de la misma transacción.
        """
        return await self.engine.parallel_execute_async(tasks, max_concurrency=max_concurrency)