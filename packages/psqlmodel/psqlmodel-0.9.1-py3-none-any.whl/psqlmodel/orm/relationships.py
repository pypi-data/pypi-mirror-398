"""
Sistema de relaciones para PSQLModel ORM - SIMPLE Y POTENTE.

Solo hay una forma de hacer las cosas, la correcta:
    
    # Definir relación
    class User(PSQLModel):
        driver: Relation["Driver"] = Relation("Driver")  # String para forward ref
    
    class Driver(PSQLModel):
        user_id: uuid
        user: Relation["User"] = Relation(User)  # Clase directa
    
    # Usar - Lazy load
    user = session.exec(Select(User).Where(User.id == id)).first()
    user.driver.id  # Lazy load automático cuando accedes
    
    # Usar - Eager load
    user = session.exec(Select(User).Where(User.id == id).Include(Driver))
    user.driver.id  # Ya está cargado, no hace query extra

Sin append, sin Save especial, sin complicaciones.
"""

from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

if TYPE_CHECKING:
    from .model import PSQLModel
    from ..core.session import Session as _SyncSession  # solo para hints
    from ..core.session import AsyncSession as _AsyncSession

T = TypeVar("T")


# ============================================================
# Helpers internos
# ============================================================

def _singular(name: str) -> str:
    """Heurística simple para singular: cars -> car, users -> user."""
    return name[:-1] if name.endswith("s") else name


def _iter_model_subclasses(base: type) -> List[type]:
    """Recorre recursivamente todas las subclases de un modelo base."""
    out: List[type] = []
    stack = list(base.__subclasses__())
    while stack:
        cls = stack.pop()
        out.append(cls)
        stack.extend(cls.__subclasses__())
    return out


# ============================================================
# RELACIÓN UNIVERSAL - UNA SOLA CLASE
# ============================================================

class Relation(Generic[T]):
    """Type annotation and descriptor for defining model relationships.
    
    Relation is the core class used for type hints and relationship definitions.
    Relationship is an alias for this class for more semantic clarity.
    
    Auto-detects:
    - Relationship type (many_to_one / one_to_many / one_to_one / many_to_many)
    - Backref automatically using __relations__
    - Related table from argument (class or str)
    
    Usage:
        class User(PSQLModel):
            # Use Relation[T] as type hint, Relationship() or Relation() as descriptor
            driver: Relation["Driver"] = Relationship("Driver")
        
        class Driver(PSQLModel):
            user_id: uuid = Column()
            user: Relation["User"] = Relationship(User)
        
        # Access related objects:
        user.driver.name
        driver.user.email
    
    Note: Relationship = Relation (alias for semantic clarity)
    """

    # NOTA importante para autocompletado:
    # - Declara en el modelo:   driver: Relation["Driver"] = Relation("Driver")
    # - El type checker entiende que al acceder a .driver, __get__ devuelve Driver|None.

    def __init__(
        self,
        table_name: Union[str, type, None] = None,
        secondary: Optional[str] = None,
        *,
        # Explicit foreign key column name (when multiple FKs to same model)
        foreign_keys: Optional[str] = None,
        # Python-side cascade behavior (distinct from DB-level on_delete)
        # True = "all, delete-orphan", False/None = no cascade, str = specific cascade
        cascade: Union[bool, str, None] = None,
        # If True, rely on DB-level ON DELETE CASCADE instead of ORM cascade
        passive_deletes: bool = False,
        # Force uselist behavior (True=list, False=single, None=auto-detect)
        uselist: bool = None,
        # Default ordering for collections
        order_by: Any = None,
        # For circular FK (UPDATE after INSERT)
        post_update: bool = False,
        # Loading strategy
        lazy: str = "select",
    ) -> None:
        """
        Args:
            table_name:
                - Nombre de la tabla relacionada (str or class)
                - If None, extracted from type hint: Relation["Message"] -> "Message"
            secondary:
                - Nombre de tabla intermedia para ManyToMany
                - Si es "auto" -> genera "<owner>_<target>_junction"
            foreign_keys:
                - Column name to use as FK (when multiple FKs point to same model)
                - Example: foreign_keys="recipient_id" in received_messages relationship
            cascade:
                - True: "all, delete-orphan" (save-update, merge, delete, delete-orphan)
                - False/None: no cascade
                - str: specific cascade options ("save-update", "delete", etc.)
            passive_deletes:
                - If True: rely on database-level ON DELETE CASCADE
                - If False: ORM handles cascade (emits DELETE statements)
            uselist:
                - True: always return list, False: always return single item
                - None (default): auto-detect from relationship type
            order_by:
                - Column or list of Columns for default ordering of collections
            post_update:
                - If True, related objects are updated after parent INSERT
                - Useful for circular foreign keys
            lazy:
                - Loading strategy: "select" (default), "joined", "subquery", "noload"
        """
        # table_name can be None - will be extracted from type hint in __set_name__
        if isinstance(table_name, type):
            self.target_model: Optional[type] = table_name
            self.table_name: Optional[str] = getattr(table_name, "__tablename__", table_name.__name__.lower())
        elif table_name is not None:
            self.table_name = table_name
            self.target_model = None
        else:
            # Will be set from type hint in __set_name__
            self.table_name = None
            self.target_model = None

        # secondary="auto" -> se resuelve en __set_name__
        self._secondary_auto: bool = True if secondary == "auto" else False
        self.secondary: Optional[str] = None if secondary == "auto" else secondary

        self.attr_name: Optional[str] = None
        self.owner_model: Optional[type] = None

        # Cache por instancia (id(instance) -> valor o RelationProxy)
        self._cache: dict[int, Any] = {}

        # Meta detectada
        self._relationship_type: Optional[str] = None  # 'many_to_one', 'one_to_many', 'one_to_one', 'many_to_many'
        self._foreign_key: Optional[str] = foreign_keys  # Explicit FK or auto-detected

        # Cascade options
        self.cascade = self._parse_cascade(cascade)
        self.passive_deletes = passive_deletes
        self._uselist = uselist
        self._order_by = [order_by] if order_by and not isinstance(order_by, (list, tuple)) else (order_by or [])
        self.post_update = post_update
        self.lazy = lazy

    def _parse_cascade(self, cascade: Union[bool, str, None]) -> set:
        """Parse cascade value into set of operations.
        
        Args:
            cascade: True (all, delete-orphan), False/None (no cascade), or str
        """
        if cascade is None or cascade is False:
            return set()
        
        if cascade is True:
            # cascade=True means "all, delete-orphan"
            return {"save-update", "merge", "refresh-expire", "expunge", "delete", "delete-orphan"}
        
        # String cascade
        ops = set()
        for part in cascade.split(","):
            part = part.strip().lower()
            if part == "all":
                ops.update({"save-update", "merge", "refresh-expire", "expunge", "delete"})
            elif part == "all, delete-orphan":
                ops.update({"save-update", "merge", "refresh-expire", "expunge", "delete", "delete-orphan"})
            else:
                ops.add(part)
        return ops

    @property
    def uselist(self) -> bool:
        """Determine if relationship returns a list or single item."""
        if self._uselist is not None:
            return self._uselist
        
        # Auto-detect based on relationship type
        if self._relationship_type is None and self.owner_model:
            self._detect_relationship_type()
        return self._relationship_type in ("one_to_many", "many_to_many")

    # ------------------------------------------------------------------
    # Registro en el modelo
    # ------------------------------------------------------------------
    def __set_name__(self, owner: type, name: str) -> None:
        """Auto-registro cuando se asigna al modelo."""
        self.attr_name = name
        self.owner_model = owner

        # Extract target model from type hint if not provided
        if self.table_name is None:
            self._extract_target_from_type_hint(owner, name)

        # Asignar nombre de tabla intermedia automático para ManyToMany si se pidió "auto"
        if self._secondary_auto and self.secondary is None and self.table_name:
            owner_table = getattr(owner, "__tablename__", owner.__name__.lower())
            target_name: Optional[str]
            if isinstance(self.table_name, str):
                target_name = self.table_name
            elif isinstance(self.table_name, type):
                target_name = getattr(self.table_name, "__tablename__", self.table_name.__name__.lower())
            else:
                target_name = str(self.table_name)

            if target_name:
                pair = sorted([owner_table, str(target_name)])
                self.secondary = f"{pair[0]}_{pair[1]}_junction"

        # Registrar en __relations__ para que otros componentes (Session / QueryBuilder)
        # puedan detectar relaciones de forma unificada.
        if not hasattr(owner, "__relations__"):
            owner.__relations__ = {}
        owner.__relations__[name] = self

    def _extract_target_from_type_hint(self, owner: type, name: str) -> None:
        """Extract target model name from type hint annotation.
        
        Handles: Relation["Message"], Relation[Message], Relation[list["Message"]], etc.
        """
        import typing
        import re
        
        # Get type hints for the class
        hints = getattr(owner, "__annotations__", {})
        hint = hints.get(name)
        
        if hint is None:
            return
        
        # Handle string annotation (forward reference)
        if isinstance(hint, str):
            # Parse "Relation[list['Message']]" or "Relation['Message']"
            match = re.search(r"Relation\[(?:list\[)?['\"]?(\w+)['\"]?\]?\]", hint)
            if match:
                self.table_name = match.group(1).lower()
            return
        
        # Handle actual type
        origin = getattr(hint, "__origin__", None)
        args = getattr(hint, "__args__", ())
        
        if not args:
            return
        
        target_type = args[0]
        
        # If it's list[Model], get the inner type
        if getattr(target_type, "__origin__", None) is list and hasattr(target_type, "__args__"):
            target_type = target_type.__args__[0]
        
        # Handle ForwardRef (string reference like "Message")
        if isinstance(target_type, type):
            self.target_model = target_type
            self.table_name = getattr(target_type, "__tablename__", target_type.__name__.lower())
        elif hasattr(target_type, "__forward_arg__"):
            # ForwardRef in older Python
            self.table_name = target_type.__forward_arg__.lower()
        elif isinstance(target_type, str):
            self.table_name = target_type.lower()
        elif hasattr(typing, "ForwardRef") and isinstance(target_type, typing.ForwardRef):
            # ForwardRef in Python 3.7+
            self.table_name = target_type.__forward_arg__.lower()

    # ------------------------------------------------------------------
    # Detección automática del tipo de relación
    # ------------------------------------------------------------------
    def _detect_relationship_type(self) -> None:
        """Detecta automáticamente el tipo de relación si aún no fue detectado."""
        if self._relationship_type is not None:
            return

        # 1) Many-to-many si hay secondary
        if self.secondary:
            self._relationship_type = "many_to_many"
            return

        # 2) Resolver modelo target
        target = self._resolve_target()
        if target is None or self.owner_model is None:
            return

        owner_model = self.owner_model

        owner_table = getattr(owner_model, "__tablename__", owner_model.__name__.lower())
        target_table = getattr(target, "__tablename__", target.__name__.lower())
        target_singular = _singular(target_table)
        owner_singular = _singular(owner_table)

        owner_cols = getattr(owner_model, "__columns__", {}) or {}
        target_cols = getattr(target, "__columns__", {}) or {}

        # 3) PRIORITY: Check explicit foreign_key attribute on columns
        # This takes precedence over naming conventions
        
        # Find owner's primary key
        owner_pk = None
        for name, col in owner_cols.items():
            if getattr(col, "primary_key", False):
                owner_pk = name
                break

        # Find target's primary key
        target_pk = None
        for name, col in target_cols.items():
            if getattr(col, "primary_key", False):
                target_pk = name
                break

        # Check target columns for FK pointing to owner (one_to_many or one_to_one inverse)
        if owner_pk:
            for col_name, col in target_cols.items():
                fk_ref = getattr(col, "foreign_key", None)
                if fk_ref:
                    # Normalize FK reference - handle both Column objects and strings
                    fk_str = self._normalize_fk_reference(fk_ref)
                    # Match against owner table and PK
                    owner_schema = getattr(owner_model, "__schema__", "public") or "public"
                    expected_refs = [
                        f"{owner_table}.{owner_pk}",
                        f"{owner_schema}.{owner_table}.{owner_pk}",
                    ]
                    if fk_str in expected_refs:
                        # Check if FK has unique constraint → one_to_one inverse
                        # Also check if it's a PK (like Manager.id = User.id)
                        is_unique = bool(getattr(col, "unique", False)) or bool(getattr(col, "primary_key", False))
                        self._relationship_type = "one_to_one_inverse" if is_unique else "one_to_many"
                        self._foreign_key = col_name
                        return

        # Check owner columns for FK pointing to target (many_to_one / one_to_one)
        if target_pk:
            for col_name, col in owner_cols.items():
                fk_ref = getattr(col, "foreign_key", None)
                if fk_ref:
                    fk_str = self._normalize_fk_reference(fk_ref)
                    target_schema = getattr(target, "__schema__", "public") or "public"
                    expected_refs = [
                        f"{target_table}.{target_pk}",
                        f"{target_schema}.{target_table}.{target_pk}",
                    ]
                    if fk_str in expected_refs:
                        is_unique = self._has_unique_constraint(col_name)
                        self._relationship_type = "one_to_one" if is_unique else "many_to_one"
                        self._foreign_key = col_name
                        return

        # 4) FALLBACK: Check by naming conventions if no explicit FK found
        # Helper para FK en un model (por nombre)
        def _find_fk(model_cols: dict, candidates: List[str]) -> Optional[str]:
            for name in candidates:
                if name in model_cols:
                    return name
            return None

        # FK en owner -> many_to_one / one_to_one (por nombre convencional)
        owner_fk_candidates = [f"{target_table}_id", f"{target_singular}_id"]
        fk_in_owner = _find_fk(owner_cols, owner_fk_candidates)
        if fk_in_owner:
            self._foreign_key = fk_in_owner
            is_unique = self._has_unique_constraint(fk_in_owner)
            self._relationship_type = "one_to_one" if is_unique else "many_to_one"
            return

        # FK en target → one_to_many o one_to_one inverse (por nombre convencional)
        target_fk_candidates = [f"{owner_table}_id", f"{owner_singular}_id"]
        fk_in_target = _find_fk(target_cols, target_fk_candidates)
        if fk_in_target:
            # Check if FK has unique constraint → one_to_one inverse (not one_to_many)
            fk_col = target_cols.get(fk_in_target)
            is_unique = bool(getattr(fk_col, "unique", False)) if fk_col else False
            self._relationship_type = "one_to_one_inverse" if is_unique else "one_to_many"
            self._foreign_key = fk_in_target
            return

        # 5) Fallback: asumimos many_to_one owner -> target
        self._relationship_type = "many_to_one"
        self._foreign_key = f"{target_singular}_id"

    def _normalize_fk_reference(self, fk_ref) -> str:
        """Normalize FK reference to 'table.column' format.
        
        Handles both Column objects and string references like 'table.column'.
        """
        if fk_ref is None:
            return ""
        
        # If it's a Column object, extract model and column name
        from .column import Column
        if isinstance(fk_ref, Column):
            fk_model = getattr(fk_ref, "model", None)
            if fk_model:
                fk_table = getattr(fk_model, "__tablename__", fk_model.__name__.lower())
                fk_col_name = getattr(fk_ref, "name", None)
                if fk_table and fk_col_name:
                    return f"{fk_table}.{fk_col_name}"
            return ""
        
        # Already a string - return as is
        return str(fk_ref)

    def _has_unique_constraint(self, column_name: str) -> bool:
        """Verifica si una columna tiene unique constraint (OneToOne)."""
        owner = self.owner_model
        if owner is None:
            return False

        # 1) UniqueConstraint en __constraints__ (si existe)
        constraints = getattr(owner, "__constraints__", []) or []
        for constraint in constraints:
            try:
                from .table import UniqueConstraint  # import tardío para evitar ciclos
            except Exception:
                UniqueConstraint = ()  # type: ignore

            if isinstance(constraint, UniqueConstraint):
                try:
                    col_names = constraint._resolve_columns(owner)
                except Exception:
                    continue
                if len(col_names) == 1 and col_names[0] == column_name:
                    return True

        # 2) Flag unique=True en Column
        cols = getattr(owner, "__columns__", {}) or {}
        col = cols.get(column_name)
        if col is not None and getattr(col, "unique", False):
            return True

        return False

    def _resolve_target(self) -> Optional[type]:
        """Resuelve el modelo objetivo por nombre de tabla o nombre de clase."""
        if self.target_model is not None:
            return self.target_model

        # Import aquí para evitar ciclos
        from .model import PSQLModel

        target_name_lower = str(self.table_name).lower()

        # Buscar en subclases recursivas de PSQLModel
        for subclass in _iter_model_subclasses(PSQLModel):
            tab = getattr(subclass, "__tablename__", None)
            if tab and str(tab).lower() == target_name_lower:
                self.target_model = subclass
                return subclass
            if subclass.__name__.lower() == target_name_lower:
                self.target_model = subclass
                return subclass

        return None

    # ------------------------------------------------------------------
    # Descriptor: acceso y asignación
    # ------------------------------------------------------------------
    @overload
    def __get__(self: "Relation[T]", instance: None, owner: Type[Any]) -> "Relation[T]":
        ...

    @overload
    def __get__(
        self, instance: Any, owner: Type[Any]
    ) -> Union[T, "RelationProxy[T]", List[T], None]:
        ...

    def __get__(self, instance: Any, owner: Type[Any]) -> Any:
        """Lazy load automático con detección de tipo."""
        if instance is None:
            # Acceso desde la clase → devolvemos el descriptor
            return self

        # Asegurar tipo detectado
        self._detect_relationship_type()

        cache_key = id(instance)
        cached_value = self._cache.get(cache_key)

        # ONE-TO-ONE-INVERSE: Returns single instance (FK is on target with unique)
        # But Include may have cached a list - extract first element
        if self._relationship_type == "one_to_one_inverse":
            if cached_value is not None:
                if isinstance(cached_value, list):
                    # Extract first element from list (from Include)
                    result = cached_value[0] if cached_value else None
                    self._cache[cache_key] = result  # Replace with singleton
                    return result
                return cached_value  # Already singleton
            # Not cached, lazy load
            result = self._load(instance)
            self._cache[cache_key] = result
            return result

        # Relaciones que devuelven colección → RelationProxy
        if self._relationship_type in ("one_to_many", "many_to_many"):
            # BUGFIX: Check if eager-loaded data (list) was set via __set__ first
            
            # If a list was set directly (e.g., from Include/eager loading), use it
            if isinstance(cached_value, list):
                # Create proxy with pre-loaded data
                proxy = RelationProxy(self, instance)
                proxy._data = cached_value  # Set the pre-loaded data
                self._cache[cache_key] = proxy  # Cache the proxy
                return proxy
            
            # If proxy already exists, return it
            if isinstance(cached_value, RelationProxy):
                return cached_value
            
            # Otherwise create new empty proxy
            proxy = RelationProxy(self, instance)
            self._cache[cache_key] = proxy
            return proxy

        # Singleton (many_to_one / one_to_one) → usar cache directo
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = self._load(instance)
        self._cache[cache_key] = result
        return result

    def __set__(self, instance: Any, value: Any) -> None:
        """Asignación directa manual al atributo relación."""
        self._cache[id(instance)] = value

    # ------------------------------------------------------------------
    # Carga perezosa
    # ------------------------------------------------------------------
    def _load(self, instance: Any) -> Union[T, List[T], None]:
        """Carga inteligente basada en el tipo detectado usando la Session adjunta."""
        # Requiere que la instancia tenga __session__ adjunto por Session/AsyncSession
        sess = getattr(instance, "__session__", None)

        # Soportamos solo Session síncrona para lazy-load automático.
        # Para AsyncSession, se recomienda usar Include() en las queries.
        is_async = getattr(sess, "__class__", None).__name__ == "AsyncSession"

        if sess is None or is_async:
            # Sin sesión o async: no podemos lazy-load correctamente en este contexto.
            try:
                kind = "async" if is_async else "no-session"
                print(
                    f"[psqlmodel] WARNING: lazy-load of '{self.attr_name}' "
                    f"on '{type(instance).__name__}' skipped ({kind}). "
                    f"Use Select(...).Include(...) o adjunta una Session sync."
                )
            except Exception:
                pass
            if self._relationship_type in ("one_to_many", "many_to_many"):
                return []
            return None

        from ..query.builder import Select

        target = self._resolve_target()
        if target is None or self.owner_model is None:
            if self._relationship_type in ("one_to_many", "many_to_many"):
                return []
            return None

        owner_model = self.owner_model
        owner_table = getattr(owner_model, "__tablename__", owner_model.__name__.lower())
        owner_cols = getattr(owner_model, "__columns__", {}) or {}
        target_cols = getattr(target, "__columns__", {}) or {}

        # Obtener PK del owner
        owner_pk_name: Optional[str] = None
        for name, col in owner_cols.items():
            if getattr(col, "primary_key", False):
                owner_pk_name = name
                break

        # Owner sin PK → sin relación
        if owner_pk_name is None:
            if self._relationship_type in ("one_to_many", "many_to_many"):
                return []
            return None

        owner_pk_value = getattr(instance, owner_pk_name, None)

        # -------------------------------------------------------
        # ONE-TO-MANY: owner -> [target]
        # target tiene FK hacia owner
        # -------------------------------------------------------
        if self._relationship_type in ("one_to_many", "one_to_one_inverse"):
            fk_name = self._foreign_key or f"{_singular(owner_table)}_id"
            fk_col = getattr(target, fk_name, None)
            if fk_col is None or owner_pk_value is None:
                if self._relationship_type == "one_to_one_inverse":
                    return None
                return []

            query = Select(target).Where(fk_col == owner_pk_value)
            
            if self._relationship_type == "one_to_one_inverse":
                # Return single instance
                res = sess.exec(query).first()
                if res is not None:
                    try:
                        setattr(res, "__session__", sess)
                    except Exception:
                        pass
                return res
            else:
                # Return list
                res = sess.exec(query).all()  # type: ignore[attr-defined]

                # Adjuntar session a cada item para posteriores lazy loads
                for item in res:
                    try:
                        setattr(item, "__session__", sess)
                    except Exception:
                        pass
                return res

        # -------------------------------------------------------
        # MANY-TO-ONE / ONE-TO-ONE: owner -> target
        # owner tiene FK hacia target
        # -------------------------------------------------------
        if self._relationship_type in ("many_to_one", "one_to_one"):
            target_table = getattr(target, "__tablename__", target.__name__.lower())
            fk_name = self._foreign_key or f"{_singular(target_table)}_id"
            fk_value = getattr(instance, fk_name, None)
            if fk_value is None:
                return None

            target_pk_name: Optional[str] = None
            for name, col in target_cols.items():
                if getattr(col, "primary_key", False):
                    target_pk_name = name
                    break
            if target_pk_name is None:
                return None

            pk_col = getattr(target, target_pk_name)
            query = Select(target).Where(pk_col == fk_value)
            res = sess.exec(query).first()  # type: ignore[attr-defined]

            if res is not None:
                try:
                    setattr(res, "__session__", sess)
                except Exception:
                    pass
            return res

        # -------------------------------------------------------
        # MANY-TO-MANY: owner <-> target vía tabla secundaria
        # -------------------------------------------------------
        if self._relationship_type == "many_to_many":
            junction = self.secondary
            if not junction or owner_pk_value is None:
                return []

            target_table = getattr(target, "__tablename__", target.__name__.lower())
            owner_fk = f"{_singular(owner_table)}_id"
            target_fk = f"{_singular(target_table)}_id"

            # Paso 1: obtener IDs de target desde la tabla secundaria
            # Usamos RAW SQL a través del Engine del Session para no complicar QueryBuilder.
            try:
                # El Session tiene engine
                engine = getattr(sess, "engine", None)
                if engine is None:
                    raise RuntimeError("Session has no engine attached")

                #  SELECT target_fk FROM junction WHERE owner_fk = %s
                sql = f"SELECT {target_fk} FROM {junction} WHERE {owner_fk} = %s"
                rows = engine.execute_raw(sql, [owner_pk_value])  # type: ignore[attr-defined]
                target_ids = [r[0] for r in rows] if rows else []
            except Exception:
                target_ids = []

            if not target_ids:
                return []

            # Paso 2: obtener targets por PK IN (...)
            target_pk_name: Optional[str] = None
            for name, col in target_cols.items():
                if getattr(col, "primary_key", False):
                    target_pk_name = name
                    break
            if target_pk_name is None:
                return []

            pk_col = getattr(target, target_pk_name)
            from ..query.builder import Select as _Select
            # Usamos IN([...]) – QueryBuilder ya sabe convertir lista en IN (val1, val2, ...)
            query = _Select(target).Where(pk_col).In(target_ids)
            res = sess.exec(query).all()  # type: ignore[attr-defined]

            for item in res:
                try:
                    setattr(item, "__session__", sess)
                except Exception:
                    pass
            return res

        # Fallback
        if self._relationship_type in ("one_to_many", "many_to_many"):
            return []
        return None


# ============================================================
# PROXY PARA COLECCIONES (one-to-many / many-to-many)
# ============================================================

class FilterResult(List[T]):
    """Wrapper para resultados de filtrado que añade .first() y .all()."""

    def first(self) -> Optional[T]:
        """Devuelve el primer elemento o None."""
        return self[0] if self else None

    def all(self) -> List[T]:
        """Devuelve todos los elementos como lista."""
        return list(self)

    def limit(self, n: int) -> "FilterResult[T]":
        """Devuelve los primeros n elementos."""
        return FilterResult(self[:n])

    def skip(self, n: int) -> "FilterResult[T]":
        """Salta los primeros n elementos."""
        return FilterResult(self[n:])

    def order_by(self, *args) -> "FilterResult[T]":
        """Ordena los resultados en memoria."""
        data = list(self)
        # Sort is stable, so we iterate in reverse order of arguments
        for arg in reversed(args):
            direction = "ASC"
            expr = arg
            
            # Detect SortExpression (duck typing to avoid circular import)
            if hasattr(arg, "direction") and hasattr(arg, "expr"):
                direction = arg.direction
                expr = arg.expr
            
            # Extract column name
            attr_name = None
            if hasattr(expr, "name"):
                attr_name = expr.name
            elif hasattr(expr, "attr_name"):
                attr_name = expr.attr_name
            
            if attr_name:
                reverse = (direction == "DESC")
                # Handle None values safely (put them last or first depending on preference, here standard python sort)
                # To make it robust: (x is None, x)
                def key_func(item):
                    val = getattr(item, attr_name, None)
                    # Sort None values: usually None comes first in Python sort if comparable, 
                    # but we can't compare None with int/str directly in Python 3.
                    # So we use a tuple (is_none, value)
                    return (val is None, val)
                
                data.sort(key=key_func, reverse=reverse)
        
        return FilterResult(data)


class RelationProxy(List[T]):
    """Proxy de relación one-to-many/many-to-many.
    
    - Se comporta como una lista lazy.
    - Soporta filter() con:
        - callable → filtrado en memoria
        - SQLExpression → ejecuta SELECT con condición extra
    """

    def __init__(self, relation: Relation[T], instance: Any) -> None:
        super().__init__()  # la lista base no se usa directamente, pero mantiene compat
        self._relation: Relation[T] = relation
        self._instance: Any = instance
        self._data: Optional[List[T]] = None

    # ------------------------------
    # Carga interna
    # ------------------------------
    def _load(self) -> List[T]:
        if self._data is None:
            res = self._relation._load(self._instance)
            if res is None:
                self._data = []
            elif isinstance(res, list):
                self._data = res
            else:
                # Si por error devolviera un singleton, lo envolvemos
                self._data = [res]  # type: ignore[list-item]
        return self._data

    # ------------------------------
    # Implementación tipo lista
    # ------------------------------
    def __iter__(self):
        return iter(self._load())

    def __len__(self) -> int:  # type: ignore[override]
        return len(self._load())

    def __getitem__(self, item):  # type: ignore[override]
        return self._load()[item]

    def __repr__(self) -> str:
        # Show as a normal list for intuitive debugging
        return repr(self._load())

    def __str__(self) -> str:
        return str(self._load())

    # ------------------------------
    # Autocompletado: columnas del modelo
    # ------------------------------
    def __getattr__(self, name: str) -> Any:
        """
        Exponer columnas del modelo target para construir condiciones:

            driver.orders.filter(Order.priority >= 1)
        """
        target = self._relation._resolve_target()
        if target and hasattr(target, name):
            return getattr(target, name)
        raise AttributeError(name)

    # ------------------------------
    # API de filtrado
    # ------------------------------
    def filter(self, condition: Any = None) -> "FilterResult[T]":
        """
        Filtra la relación.

        - Si `condition` es callable → filtra en memoria:
              driver.orders.filter(lambda o: o.priority >= 1)

        - Si `condition` es una SQLExpression / ColumnExpression → 
          ejecuta SELECT en la tabla target con:
              - one_to_many: WHERE fk = owner_pk AND <condition>
              - many_to_many: WHERE target.pk IN (subquery/junction) AND <condition>
        """
        # 1) Filtrado en memoria
        if condition is None:
            return FilterResult(self._load())

        if callable(condition):
            return FilterResult([item for item in self._load() if condition(item)])

        # 2) Filtrado vía query SQL (one_to_many y many_to_many)
        sess = getattr(self._instance, "__session__", None)
        if sess is None:
            return FilterResult([])

        rel_type = self._relation._relationship_type
        if rel_type not in ("one_to_many", "many_to_many"):
            return FilterResult([])

        target = self._relation._resolve_target()
        owner_model = self._relation.owner_model
        if target is None or owner_model is None:
            return FilterResult([])

        from ..query.builder import Select

        # owner PK
        owner_pk_name: Optional[str] = None
        for name, col in getattr(owner_model, "__columns__", {}).items():
            if getattr(col, "primary_key", False):
                owner_pk_name = name
                break
        if owner_pk_name is None:
            return FilterResult([])

        owner_pk_value = getattr(self._instance, owner_pk_name, None)
        if owner_pk_value is None:
            return FilterResult([])

        # -------------------------------------------------------
        # ONE-TO-MANY
        # -------------------------------------------------------
        if rel_type == "one_to_many":
            owner_table = getattr(owner_model, "__tablename__", owner_model.__name__.lower())
            fk_name = self._relation._foreign_key or f"{_singular(owner_table)}_id"
            fk_col = getattr(target, fk_name, None)
            if fk_col is None:
                return FilterResult([])

            # WHERE fk = owner_pk AND <condition>
            query = Select(target).Where(fk_col == owner_pk_value).And(condition)
            try:
                res = sess.exec(query).all()  # type: ignore[attr-defined]
            except Exception:
                return FilterResult([])

            # Adjuntar session a cada item
            for item in res:
                try:
                    setattr(item, "__session__", sess)
                except Exception:
                    pass
            return FilterResult(res)

        # -------------------------------------------------------
        # MANY-TO-MANY
        # -------------------------------------------------------
        junction = self._relation.secondary
        if not junction:
            return FilterResult([])

        owner_table = getattr(owner_model, "__tablename__", owner_model.__name__.lower())
        target_table = getattr(target, "__tablename__", target.__name__.lower())
        owner_fk = f"{_singular(owner_table)}_id"
        target_fk = f"{_singular(target_table)}_id"

        # Paso 1: obtener IDs de target desde la tabla secundaria
        try:
            engine = getattr(sess, "engine", None)
            if engine is None:
                raise RuntimeError("Session has no engine attached")

            sql = f"SELECT {target_fk} FROM {junction} WHERE {owner_fk} = %s"
            rows = engine.execute_raw(sql, [owner_pk_value])  # type: ignore[attr-defined]
            target_ids = [r[0] for r in rows] if rows else []
        except Exception:
            target_ids = []

        if not target_ids:
            return FilterResult([])

        # Paso 2: obtener PK del target
        target_pk_name: Optional[str] = None
        for name, col in getattr(target, "__columns__", {}).items():
            if getattr(col, "primary_key", False):
                target_pk_name = name
                break
        if target_pk_name is None:
            return FilterResult([])

        pk_col = getattr(target, target_pk_name)

        # WHERE target.pk IN (...) AND <condition>
        query = Select(target).Where(pk_col).In(target_ids).And(condition)
        try:
            res = sess.exec(query).all()  # type: ignore[attr-defined]
        except Exception:
            return FilterResult([])

        # Adjuntar session a cada item
        for item in res:
            try:
                setattr(item, "__session__", sess)
            except Exception:
                pass
        return FilterResult(res)


# ============================================================
# ALIASES PARA COMPATIBILIDAD
# ============================================================

# ============================================================
# ALIASES
# ============================================================

# Relationship: Alias for Relation - use for semantic clarity when defining descriptors
# Pattern: field: Relation["Model"] = Relationship("Model")
# - Relation[T]: Used as type hint for type checking and autocompletion  
# - Relationship(): Used as descriptor/instance for relationship configuration
Relationship = Relation

# Legacy aliases (kept for backwards compatibility)
OneToMany = Relation
ManyToOne = Relation
OneToOne = Relation
ManyToMany = Relation
