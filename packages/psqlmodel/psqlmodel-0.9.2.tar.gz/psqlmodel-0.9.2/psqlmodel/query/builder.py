
# ============================================================
# query_builder.py – Select, Join, Query (compatible con column.py + PSQLModel)
# ============================================================

from ..orm.column import (
    SQLExpression,
    Column,
    Alias,
    RawExpression,
)
from ..orm.column import (
    Column,
    RawExpression,
    # BinaryExpression, # Not used directly here, but might be in column.py
    # LogicalExpression, # Not used directly here, but might be in column.py
    # Ordering, # Not used directly here, but might be in column.py
)
from .layout import calculate_layout


# ============================================================
# QUERY BASE
# ============================================================

# Track which extensions have been installed per-engine to avoid repeated checks
_installed_extensions: dict = {}

class Query(SQLExpression):
    """
    Base de todas las consultas (Select, Insert, Update, Delete, etc.)
    """

    def to_sql_params(self):
        raise NotImplementedError()

    def _collect_required_extensions(self, obj=None, visited=None) -> set:
        """Recursively collect all required_extension values from query components."""
        if visited is None:
            visited = set()
        
        extensions = set()
        
        if obj is None:
            obj = self
        
        # Avoid infinite recursion
        obj_id = id(obj)
        if obj_id in visited:
            return extensions
        visited.add(obj_id)
        
        # Check if object has required_extension
        if hasattr(obj, "required_extension") and obj.required_extension:
            extensions.add(obj.required_extension)
        
        # Recurse into common query attributes
        for attr in ("columns", "where", "where_clauses", "set_clauses", 
                     "select_query", "values_dict", "_returning", "joins",
                     "group_by", "having", "order_by", "ctes"):
            if hasattr(obj, attr):
                val = getattr(obj, attr)
                if val is not None:
                    if isinstance(val, (list, tuple)):
                        for item in val:
                            if isinstance(item, tuple):
                                for sub in item:
                                    extensions |= self._collect_required_extensions(sub, visited)
                            else:
                                extensions |= self._collect_required_extensions(item, visited)
                    elif isinstance(val, dict):
                        for v in val.values():
                            extensions |= self._collect_required_extensions(v, visited)
                    elif hasattr(val, "required_extension") or hasattr(val, "to_sql"):
                        extensions |= self._collect_required_extensions(val, visited)
        
        return extensions

    def _ensure_extensions(self, engine, extensions: set):
        """Install required extensions if not already installed."""
        engine_id = id(engine)
        if engine_id not in _installed_extensions:
            _installed_extensions[engine_id] = set()
        
        for ext in extensions:
            if ext not in _installed_extensions[engine_id]:
                try:
                    engine.execute_raw(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')
                    _installed_extensions[engine_id].add(ext)
                except Exception as e:
                    # Log but don't fail - extension might already exist
                    if engine._config.debug:
                        print(f"[psqlmodel] Extension '{ext}': {e}")

    async def _ensure_extensions_async(self, engine, extensions: set):
        """Install required extensions asynchronously if not already installed."""
        engine_id = id(engine)
        if engine_id not in _installed_extensions:
            _installed_extensions[engine_id] = set()
        
        for ext in extensions:
            if ext not in _installed_extensions[engine_id]:
                try:
                    await engine.execute_raw_async(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')
                    _installed_extensions[engine_id].add(ext)
                except Exception as e:
                    if engine._config.debug:
                        print(f"[psqlmodel] Extension '{ext}': {e}")

    # Helpers de conveniencia para ejecutar una query con un Engine.
    def execute(self, engine, *params):
        """Ejecutar esta query en modo síncrono usando un Engine."""
        # Auto-install required extensions before execution
        extensions = self._collect_required_extensions()
        if extensions:
            self._ensure_extensions(engine, extensions)
        return engine.execute(self, *params)

    async def execute_async(self, engine, *params):
        """Ejecutar esta query en modo asíncrono usando un Engine."""
        # Auto-install required extensions before execution
        extensions = self._collect_required_extensions()
        if extensions:
            await self._ensure_extensions_async(engine, extensions)
        return await engine.execute_async(self, *params)



# ============================================================
# JOIN OBJECT
# ============================================================

class Join:
    def __init__(self, parent_query, model):
        self.parent_query = parent_query
        self.model = model
        self.condition = None
        self.kind = "INNER"  # INNER, LEFT, RIGHT, FULL, CROSS, LATERAL, CROSS LATERAL
        self.alias = None    # Para subqueries/LATERAL

    def On(self, cond):
        # Guardamos la condición en el propio Join y devolvemos
        # el SelectQuery padre para permitir cadenas fluidas como
        # Select(...).Join(Model).On(cond).DistinctOn(...)
        self.condition = cond
        return self.parent_query

    # Variantes de JOIN
    def Left(self):
        self.kind = "LEFT"
        return self

    def Right(self):
        self.kind = "RIGHT"
        return self

    def Inner(self):
        self.kind = "INNER"
        return self

    def Full(self):
        self.kind = "FULL"
        return self

    def Cross(self):
        self.kind = "CROSS"
        return self

    def Lateral(self):
        """Make this a LATERAL join (requires subquery)."""
        self.kind = "LATERAL"
        return self


# ============================================================
# INCLUDE SPEC - For nested eager loading
# ============================================================

class IncludeSpec:
    """Specification for a single include with optional nested children.
    
    Used by Include/ThenInclude for nested eager loading:
        .Include(Post.author)        -> IncludeSpec(target=Post.author, children=[])
            .ThenInclude(User.profile) -> IncludeSpec.children.append(IncludeSpec(target=User.profile))
    """
    __slots__ = ("target", "children")
    
    def __init__(self, target, children=None):
        self.target = target
        self.children = children if children is not None else []
    
    def __repr__(self):
        return f"IncludeSpec({self.target!r}, children={len(self.children)})"


def _detect_relationship(owner_model, target_model):
    """Helper to detect relationship between two models.
    
    Delegates to _SessionMixin._detect_relationship for the full implementation.
    This is a module-level wrapper for backward compatibility.
    """
    # Import lazily to avoid circular imports
    try:
        from .core.session import _SessionMixin
    except ImportError:
        from psqlmodel.core.session import _SessionMixin
    
    # Create a temporary mixin instance to use its method
    mixin = _SessionMixin()
    mixin._identity_map = {}
    mixin._expired = set()
    return mixin._detect_relationship(owner_model, target_model)


# ============================================================
# SELECT
# ============================================================

class SelectQuery(Query):
    def __init__(self, *columns):
        if not columns:
            raise ValueError("Select requiere al menos una columna, modelo o expresión")

        # Flags / metadata
        self.select_all = False
        self.base_model = None
        self._from_model = None  # Para Include/relaciones
        self._from = None        # Fuente explícita de FROM (modelo, str, subquery)

        # WHERE / JOIN / GROUP / ORDER / etc.
        self.where = []
        self.joins = []
        self.group_by = []
        self.having = None
        self.order_by = []
        self.limit = None
        self.offset = None
        self.distinct = False
        self.distinct_on = None
        self.includes = []      # Para eager loading de relaciones (list of IncludeSpec)
        self._last_include = None  # Track last include for ThenInclude chaining
        self._last_column = None  # Para Like/ILike/NotLike/In/NotIn
        
        # Row locking
        self._for_update = False
        self._for_share = False
        self._of_tables = []
        self._nowait = False
        self._skip_locked = False

        # -------------------------------
        # 1) Determinar base_model
        # -------------------------------
        candidates = []
        for c in columns:
            expr = c.expr if isinstance(c, Alias) else c
            if isinstance(expr, Column) and getattr(expr, "model", None) is not None:
                candidates.append(expr.model)
            elif hasattr(expr, "__tablename__"):
                candidates.append(expr)

        if candidates:
            self.base_model = candidates[0]
            self._from_model = self.base_model

        # -------------------------------
        # 2) Modo SELECT * FROM model
        # -------------------------------
        if len(columns) == 1 and hasattr(columns[0], "__tablename__"):
            # Select(User) → SELECT * FROM users
            self.select_all = True
            self.columns = []
            if self.base_model is None:
                self.base_model = columns[0]
                self._from_model = self.base_model
            return

        # -------------------------------
        # 3) Normalizar columnas
        #     - str  → RawExpression
        #     - int/float/bool → RawExpression
        #     - Model → se expande a todas sus columnas
        # -------------------------------
        normalized = []
        for c in columns:
            expr = c.expr if isinstance(c, Alias) else c
            if isinstance(expr, str):
                # str como columna cruda
                normalized.append(RawExpression(expr))
            elif isinstance(expr, (int, float, bool)):
                # Números y booleanos → RawExpression
                normalized.append(RawExpression(str(expr)))
            else:
                normalized.append(c)

        expanded = []
        for c in normalized:
            expr = c.expr if isinstance(c, Alias) else c
            if hasattr(expr, "__tablename__") and hasattr(expr, "__columns__"):
                # Modelo dentro del SELECT → expandir a todas sus columnas
                model = expr
                cols_map = getattr(model, "__columns__", {})
                for name, col in cols_map.items():
                    bound_col = getattr(model, name, col)
                    expanded.append(bound_col)
                # Asegurar base_model si aún no estaba
                if self.base_model is None:
                    self.base_model = model
                    self._from_model = model
        


            else:
                expanded.append(c)

        self.columns = tuple(expanded)

        # -------------------------------
        # 4) Calculate Layout (for mixed hydration)
        # -------------------------------
        # Use extracted helper
        self._layout = calculate_layout(normalized)

    # ------------------------
    # FROM
    # ------------------------
    def From(self, source):
        """Setea la fuente explícita de FROM: modelo, nombre de tabla/CTE (str) o subquery."""
        self._from = source
        if self.base_model is None and hasattr(source, "__tablename__"):
            self.base_model = source
            self._from_model = source
        return self

    # ------------------------
    # DISTINCT
    # ------------------------
    def Distinct(self):
        self.distinct = True
        return self

    def DistinctOn(self, *cols):
        self.distinct_on = cols
        return self

    # ------------------------
    # WHERE SYSTEM
    # ------------------------
    def Where(self, cond):
        # Primera condición usa WHERE; las siguientes WHERE se consideran AND
        # Si cond es una columna, se guarda para usar con Like/ILike/NotLike
        if not self.where:
            self.where.append(("WHERE", cond))
        else:
            self.where.append(("AND", cond))
        self._last_column = cond if hasattr(cond, "to_sql") else None
        return self

    def And(self, cond):
        self.where.append(("AND", cond))
        self._last_column = cond if hasattr(cond, "to_sql") else None
        return self

    def Or(self, cond):
        self.where.append(("OR", cond))
        self._last_column = cond if hasattr(cond, "to_sql") else None
        return self

    def Like(self, pattern: str):
        """SQL LIKE pattern matching después de Where.

        Usage:
            Select(User).Where(User.email).Like("user@%")
        """
        if not self._last_column:
            raise ValueError("Like() debe usarse después de Where(columna)")
        from ..orm.column import RawExpression
        # Reemplazar la última condición con LIKE parameterizado
        if self.where and self.where[-1][0] in ("WHERE", "AND", "OR"):
            op, _ = self.where[-1]
            # Use _bin to create a BinaryExpression which now supports parameterization
            like_expr = self._last_column._bin(pattern, "LIKE")
            self.where[-1] = (op, like_expr)
        return self

    def ILike(self, pattern: str):
        """Case-insensitive LIKE (PostgreSQL) después de Where.

        Usage:
            Select(User).Where(User.email).ILike("user@%")
        """
        if not self._last_column:
            raise ValueError("ILike() debe usarse después de Where(columna)")
        from ..orm.column import RawExpression
        if self.where and self.where[-1][0] in ("WHERE", "AND", "OR"):
            op, _ = self.where[-1]
            ilike_expr = self._last_column._bin(pattern, "ILIKE")
            self.where[-1] = (op, ilike_expr)
        return self

    def NotLike(self, pattern: str):
        """SQL NOT LIKE pattern matching después de Where.

        Usage:
            Select(User).Where(User.email).NotLike("test%")
        """
        if not self._last_column:
            raise ValueError("NotLike() debe usarse después de Where(columna)")
        from ..orm.column import RawExpression
        if self.where and self.where[-1][0] in ("WHERE", "AND", "OR"):
            op, _ = self.where[-1]
            notlike_expr = self._last_column._bin(pattern, "NOT LIKE")
            self.where[-1] = (op, notlike_expr)
        return self

    def In(self, values):
        """SQL IN después de Where.

        Usage:
            Select(User).Where(User.id).In([1, 2, 3])
            Select(User).Where(User.role).In(Select(Role.name))
        """
        if not self._last_column:
            raise ValueError("In() debe usarse después de Where(columna)")
        from ..orm.column import RawExpression

        if hasattr(values, "to_sql") or hasattr(values, "to_sql_params"):
             # Handle Subquery directly or via InExpression if needed
             # But Column.In supports subqueries too.
             in_expr = self._last_column.In(values)
        else:
             # Assume values is iterable. Column.In handles list/tuple
             in_expr = self._last_column.In(values)
        
        if self.where and self.where[-1][0] in ("WHERE", "AND", "OR"):
            op, _ = self.where[-1]
            self.where[-1] = (op, in_expr)
        return self

    def NotIn(self, values):
        """SQL NOT IN después de Where.

        Usage:
            Select(User).Where(User.id).NotIn([1, 2, 3])
            Select(User).Where(User.role).NotIn(Select(Role.name))
        """
        if not self._last_column:
            raise ValueError("NotIn() debe usarse después de Where(columna)")
        from ..orm.column import RawExpression

        if hasattr(values, "to_sql") or hasattr(values, "to_sql_params"):
            notin_expr = self._last_column.NotIn(values)
        else:
            notin_expr = self._last_column.NotIn(values)

        if self.where and self.where[-1][0] in ("WHERE", "AND", "OR"):
            op, _ = self.where[-1]
            self.where[-1] = (op, notin_expr)
        return self

    # ------------------------
    # JOIN SYSTEM
    # ------------------------
    def Join(self, model):
        j = Join(self, model)
        self.joins.append(j)
        return j

    def LeftJoin(self, model):
        j = Join(self, model)
        j.kind = "LEFT"
        self.joins.append(j)
        return j

    def RightJoin(self, model):
        j = Join(self, model)
        j.kind = "RIGHT"
        self.joins.append(j)
        return j

    def InnerJoin(self, model):
        j = Join(self, model)
        j.kind = "INNER"
        self.joins.append(j)
        return j

    def FullJoin(self, model):
        j = Join(self, model)
        j.kind = "FULL"
        self.joins.append(j)
        return j

    def CrossJoin(self, model):
        j = Join(self, model)
        j.kind = "CROSS"
        self.joins.append(j)
        # CROSS JOIN no requiere .On(), devolver el SelectQuery para seguir encadenando
        return self

    def LateralJoin(self, subquery, alias: str = None):
        """LEFT JOIN LATERAL for correlated subqueries.
        
        Usage:
            Select(User).LateralJoin(
                Select(Order).Where(Order.user_id == User.id).Limit(5),
                alias="recent_orders"
            ).On(True)
        """
        j = Join(self, subquery)
        j.kind = "LATERAL"
        j.alias = alias or f"lat{len(self.joins)}"
        self.joins.append(j)
        return j

    def CrossJoinLateral(self, subquery, alias: str = None):
        """CROSS JOIN LATERAL for correlated subqueries.
        
        Usage:
            Select(User).CrossJoinLateral(
                Select(generate_series(1, 5)),
                alias="nums"
            )
        """
        j = Join(self, subquery)
        j.kind = "CROSS LATERAL"
        j.alias = alias or f"lat{len(self.joins)}"
        self.joins.append(j)
        # CROSS JOIN LATERAL no requiere .On()
        return self

    # ------------------------
    # EAGER VIA JOIN RELACIONADO
    # ------------------------
    def JoinRelated(self, target_model, kind: str = "INNER"):
        """Agrega un JOIN automático usando metadata de relaciones entre base_model y target_model.

        Útil para eager loading basado en JOIN sin escribir condiciones a mano.
        Soporta many-to-one, one-to-one y one-to-many. Para many-to-many requiere secondary.
        """
        if self.base_model is None:
            raise ValueError("JoinRelated requiere un base_model en el SELECT")

        rel_info = _detect_relationship(self.base_model, target_model)
        if not rel_info:
            raise ValueError(f"No se detectó relación entre {self.base_model} y {target_model}")

        rel_type = rel_info["type"]
        fk_name = rel_info["fk_name"]
        rel = rel_info["rel"]

        # Resolver primary keys
        def _pk(model_cls):
            for name, col in getattr(model_cls, "__columns__", {}).items():
                if getattr(col, "primary_key", False):
                    return name
            return None

        if rel_type in ("many_to_one", "one_to_one"):
            fk_col = getattr(self.base_model, fk_name)
            target_pk_name = _pk(target_model)
            if target_pk_name is None:
                raise ValueError(f"No PK en {target_model}")
            target_pk_col = getattr(target_model, target_pk_name)
            cond = fk_col == target_pk_col
            j = Join(self, target_model)
            j.kind = kind.upper()
            j.condition = cond
            self.joins.append(j)
            return j

        if rel_type == "one_to_many":
            base_pk_name = _pk(self.base_model)
            if base_pk_name is None:
                raise ValueError(f"No PK en {self.base_model}")
            base_pk_col = getattr(self.base_model, base_pk_name)
            fk_col = getattr(target_model, fk_name)
            cond = fk_col == base_pk_col
            j = Join(self, target_model)
            j.kind = kind.upper()
            j.condition = cond
            self.joins.append(j)
            return j

        if rel_type == "many_to_many" and rel and rel.secondary:
            # JOIN con tabla intermedia y luego con target
            owner_table = getattr(self.base_model, "__tablename__", None)
            target_pk_name = _pk(target_model)
            base_pk_name = _pk(self.base_model)
            if not target_pk_name or not base_pk_name:
                raise ValueError("PK no encontrada para many_to_many")

            # nombres de columnas FK en junction
            owner_fk = f"{owner_table[:-1] if owner_table.endswith('s') else owner_table}_id"
            target_table = getattr(target_model, "__tablename__", target_model.__name__.lower())
            target_fk = f"{target_table[:-1] if target_table.endswith('s') else target_table}_id"

            # JOIN junction
            junction_table = rel.secondary
            from ..orm.column import RawExpression
            cond_junction = RawExpression(
                f"{junction_table}.{owner_fk} = {self.base_model.__tablename__}.{base_pk_name}"
            )
            j1 = Join(self, junction_table)
            j1.kind = kind.upper()
            j1.condition = cond_junction
            self.joins.append(j1)

            # JOIN target on junction.target_fk = target.pk
            cond_target = RawExpression(
                f"{junction_table}.{target_fk} = {target_model.__tablename__}.{target_pk_name}"
            )
            j2 = Join(self, target_model)
            j2.kind = kind.upper()
            j2.condition = cond_target
            self.joins.append(j2)
            return j2

        raise ValueError(f"Tipo de relación '{rel_type}' no soportado para JoinRelated")

    # ------------------------
    # EAGER LOADING - INCLUDE
    # ------------------------
    def Include(self, *targets):
        """Eager load de relaciones automáticas.

        El sistema detecta automáticamente la relación entre el modelo principal
        y el modelo/columna/subconsulta proporcionada.
        
        Usage:
            .Include(Post)                    # Full model
            .Include(Post.id, Post.title)     # Specific columns
            .Include(Select(Post).Limit(5))   # Subquery
            .Include(Post.author)             # Relation descriptor
        """
        for target in targets:
            spec = IncludeSpec(target=target, children=[])
            self.includes.append(spec)
            self._last_include = spec
        return self

    def ThenInclude(self, target):
        """Nested eager loading for the last Include.
        
        Usage:
            .Include(Post.author)          # Loads User into post.author
                .ThenInclude(User.profile) # Loads Profile into user.profile
                .ThenInclude(User.settings)# Loads Settings into user.settings
        """
        if self._last_include is None:
            raise ValueError("ThenInclude must be called after Include")
        
        child = IncludeSpec(target=target, children=[])
        self._last_include.children.append(child)
        self._last_include = child  # Allow deeper chaining
        return self

    # ------------------------
    # GROUP BY / HAVING
    # ------------------------
    def GroupBy(self, *cols):
        self.group_by.extend(cols)
        return self

    def Having(self, cond):
        # Permite pasar una sola condición o una LogicalExpression
        # construida con & / |, igual que en Where.
        self.having = cond
        return self

    # ------------------------
    # ORDER BY
    # ------------------------
    def OrderBy(self, *cols):
        # Guardamos solo las columnas; la dirección se aplicará luego
        # con Asc()/Desc() sobre el último grupo añadido.
        if not cols:
            return self
        self.order_by.append({"cols": list(cols), "direction": None})
        return self

    def Asc(self):
        if not self.order_by:
            return self
        self.order_by[-1]["direction"] = "ASC"
        return self

    def Desc(self):
        if not self.order_by:
            return self
        self.order_by[-1]["direction"] = "DESC"
        return self

    # ------------------------
    # LIMIT / OFFSET
    # ------------------------
    def Limit(self, n):
        self.limit = n
        return self

    def Offset(self, n):
        self.offset = n
        return self

    # ------------------------
    # EXEC HELPERS (SessionManager)
    # ------------------------
    def Exec(self):
        """
        Ejecuta este SELECT usando la Session síncrona actual
        registrada en el SessionManager.

        Uso:
            Select(User).Where(User.id == 1).Exec().first()
            Select(User).Where(...).all()   # alias directo
        """
        from ..core.session import SessionManager  # import local → evita ciclos
        session = SessionManager.require_current()
        return session.exec(self)

    def all(self):
        """
        Ejecuta este SELECT en la Session actual y devuelve .all().

        Uso:
            users = Select(User).Where(User.is_active == True).all()
        """
        return self.Exec().all()

    def first(self):
        """
        Ejecuta este SELECT en la Session actual y devuelve .first().

        Uso:
            user = Select(User).Where(User.id == 1).first()
        """
        return self.Exec().first()

    def one(self):
        """
        Ejecuta este SELECT en la Session actual y devuelve .one().

        Lanza ValueError si no hay resultados o hay más de uno.
        """
        return self.Exec().one()

    def one_or_none(self):
        """
        Ejecuta este SELECT en la Session actual y devuelve .one_or_none().

        Devuelve None si no hay resultados y lanza si hay más de uno.
        """
        return self.Exec().one_or_none()

    async def all_async(self):
        """
        Versión asíncrona usando AsyncSession actual via SessionManager.

        Uso:
            async with AsyncSession(engine) as s:
                users = await Select(User).Where(...).all_async()
        """
        from ..core.session import SessionManager  # import local → evita ciclos
        session = SessionManager.require_current_async()
        return await session.exec(self).all()

    async def first_async(self):
        """
        Versión asíncrona: devuelve el primer resultado o None.
        """
        from ..core.session import SessionManager
        session = SessionManager.require_current_async()
        return await session.exec(self).first()

    async def one_async(self):
        """
        Versión asíncrona: devuelve exactamente un resultado o lanza error.
        """
        from ..core.session import SessionManager
        session = SessionManager.require_current_async()
        return await session.exec(self).one()

    async def one_or_none_async(self):
        """
        Versión asíncrona: devuelve uno, None o lanza si hay más de uno.
        """
        from ..core.session import SessionManager
        session = SessionManager.require_current_async()
        return await session.exec(self).one_or_none()

    # ============================================================
    # SQL GENERATION
    # ============================================================

    def to_sql_params(self):
        sql = ["SELECT"]
        params = []

        # DISTINCT
        if self.distinct_on:
            dist_fragments = []
            for c in self.distinct_on:
                if hasattr(c, "to_sql_params"):
                    c_sql, c_params = c.to_sql_params()
                    dist_fragments.append(c_sql)
                    params.extend(c_params)
                elif hasattr(c, "to_sql"):
                    dist_fragments.append(c.to_sql())
                else:
                    dist_fragments.append(str(c))
                    
            sql.append(
                "DISTINCT ON (" +
                ", ".join(dist_fragments) +
                ")"
            )
        elif self.distinct:
            sql.append("DISTINCT")

        # COLUMNS
        if self.select_all:
            # SELECT * FROM table
            sql.append("*")
        else:
            if not self.columns:
                raise ValueError("SELECT requiere al menos una columna cuando no se usa Select(Model) directo")
            
            col_sqls = []
            for c in self.columns:
                if hasattr(c, "to_sql_params"):
                    c_sql, c_params = c.to_sql_params()
                    # Determine if it needs parens (e.g. it is a SelectQuery acting as a column)
                    # We check if it looks like a SELECT statement strings start with SELECT
                    if c_sql.strip().upper().startswith("SELECT"):
                        c_sql = f"({c_sql})"
                    col_sqls.append(c_sql)
                    params.extend(c_params)
                elif hasattr(c, "to_sql"):
                    c_sql = c.to_sql()
                    if c_sql.strip().upper().startswith("SELECT"):
                        c_sql = f"({c_sql})"
                    col_sqls.append(c_sql)
                else:
                    col_sqls.append(str(c))
            
            sql.append(", ".join(col_sqls))

        # FROM
        if self._from is not None:
            src = self._from
            # Subquery
            if hasattr(src, "to_sql_params"):
                from_sql, from_params = src.to_sql_params()
                sql.append(f"FROM ({from_sql})")
                params.extend(from_params)
            # Modelo
            elif hasattr(src, "__tablename__"):
                schema = getattr(src, "__schema__", None)
                table = src.__tablename__
                if schema and schema != "public":
                    full_table = f"{schema}.{table}"
                else:
                    full_table = table
                sql.append(f"FROM {full_table}")
            # Nombre crudo (tabla/CTE)
            else:
                sql.append(f"FROM {src}")
        else:
            # FROM por base_model
            if self.base_model is None:
                raise ValueError(
                    "No se pudo determinar la tabla base para SELECT; "
                    "usa Select(Model) o Select(...).From('tabla')"
                )
            schema = getattr(self.base_model, "__schema__", None)
            table = self.base_model.__tablename__
            if schema and schema != "public":
                full_table = f"{schema}.{table}"
            else:
                full_table = table
            sql.append(f"FROM {full_table}")

        # JOINS
        for j in self.joins:
            join_sql, join_params = j.condition.to_sql_params() if j.condition else ("", [])
            
            # Handle subqueries (have to_sql_params) vs normal models
            if hasattr(j.model, "to_sql_params"):
                # Subquery - render with alias
                sub_sql, sub_params = j.model.to_sql_params()
                j_full_table = f"({sub_sql}) AS {j.alias or 'subq'}"
                params.extend(sub_params)
            else:
                # Regular model
                j_schema = getattr(j.model, "__schema__", None)
                j_table = getattr(j.model, "__tablename__", None) if hasattr(j.model, "__tablename__") else None
    
                if j_table is None:
                    j_full_table = str(j.model)
                else:
                    j_full_table = f"{j_schema}.{j_table}" if j_schema and j_schema != "public" else j_table
                    if j.alias:
                        j_full_table += f" AS {j.alias}"

            # Determine JOIN keyword
            join_kw = {
                "INNER": "JOIN",
                "LEFT": "LEFT JOIN",
                "RIGHT": "RIGHT JOIN",
                "FULL": "FULL JOIN",
                "CROSS": "CROSS JOIN",
                "LATERAL": "LEFT JOIN LATERAL",
                "CROSS LATERAL": "CROSS JOIN LATERAL",
            }.get(j.kind, "JOIN")
            
            if j.kind in ("CROSS", "CROSS LATERAL"):
                sql.append(f"{join_kw} {j_full_table}")
            elif join_sql:
                sql.append(f"{join_kw} {j_full_table} ON {join_sql}")
            else:
                sql.append(f"{join_kw} {j_full_table}")
            params.extend(join_params)

        # WHERE
        if self.where:
            where_fragments = []
            for op, cond in self.where:
                if hasattr(cond, "to_sql_params"):
                    cond_sql, cond_params = cond.to_sql_params()
                else:
                    cond_sql, cond_params = str(cond), []
                where_fragments.append(f"{op} {cond_sql}")
                params.extend(cond_params)
            sql.append(" ".join(where_fragments))

        # GROUP BY
        if self.group_by:
            group_fragments = []
            for c in self.group_by:
                if hasattr(c, "to_sql_params"):
                    c_sql, c_params = c.to_sql_params()
                    group_fragments.append(c_sql)
                    params.extend(c_params)
                elif hasattr(c, "to_sql"):
                    group_fragments.append(c.to_sql())
                else:
                    group_fragments.append(str(c))
            sql.append("GROUP BY " + ", ".join(group_fragments))

        # HAVING
        if self.having:
            if hasattr(self.having, "to_sql_params"):
                having_sql, having_params = self.having.to_sql_params()
            else:
                having_sql, having_params = str(self.having), []
            sql.append("HAVING " + having_sql)
            params.extend(having_params)

        # ORDER BY
        if self.order_by:
            from ..orm.column import OrderExpression
            order_fragments = []
            for entry in self.order_by:
                cols = entry["cols"]
                direction = entry["direction"] or "ASC"
                for col in cols:
                    # Check if col is an OrderExpression (has its own direction)
                    if isinstance(col, OrderExpression):
                        # OrderExpression.to_sql() includes direction
                        order_fragments.append(col.to_sql())
                    elif hasattr(col, "to_sql_params"):
                         col_sql, col_params = col.to_sql_params()
                         order_fragments.append(f"{col_sql} {direction}")
                         params.extend(col_params)
                    elif hasattr(col, "to_sql"):
                        order_fragments.append(f"{col.to_sql()} {direction}")
                    else:
                        order_fragments.append(f"{str(col)} {direction}")
            sql.append("ORDER BY " + ", ".join(order_fragments))

        # LIMIT
        if self.limit is not None:
            sql.append("LIMIT %s")
            params.append(self.limit)

        # OFFSET
        if self.offset is not None:
            sql.append("OFFSET %s")
            params.append(self.offset)

        # ROW LOCKING (must be after LIMIT/OFFSET)
        if self._for_update or self._for_share:
            lock_clause = "FOR UPDATE" if self._for_update else "FOR SHARE"
            if self._of_tables:
                table_names = ", ".join(
                    t.__tablename__ if hasattr(t, "__tablename__") else str(t)
                    for t in self._of_tables
                )
                lock_clause += f" OF {table_names}"
            if self._nowait:
                lock_clause += " NOWAIT"
            elif self._skip_locked:
                lock_clause += " SKIP LOCKED"
            sql.append(lock_clause)

        return "\n".join(sql), params

    # ------------------------
    # ROW LOCKING
    # ------------------------
    def ForUpdate(self, *tables, nowait: bool = False, skip_locked: bool = False):
        """Lock selected rows for update.
        
        Usage:
            Select(User).ForUpdate()                          # Lock all
            Select(User).ForUpdate(nowait=True)               # Fail if locked
            Select(Job).ForUpdate(skip_locked=True)           # Skip locked rows
            Select(User, Order).Join(Order).ForUpdate(Order)  # Lock only Order
            Select(User, Order).ForUpdate(Order, skip_locked=True)
        """
        self._for_update = True
        self._for_share = False
        self._of_tables = list(tables)
        self._nowait = nowait
        self._skip_locked = skip_locked
        return self

    def ForShare(self, *tables, nowait: bool = False, skip_locked: bool = False):
        """Lock selected rows for share (concurrent reads allowed).
        
        Usage:
            Select(User).ForShare()
            Select(User).ForShare(nowait=True)
        """
        self._for_share = True
        self._for_update = False
        self._of_tables = list(tables)
        self._nowait = nowait
        self._skip_locked = skip_locked
        return self

    # ------------------------
    # SET OPERATIONS
    # ------------------------
    def Union(self, other, all: bool = False):
        """Combine with UNION [ALL].
        
        Usage:
            Select(User).Where(User.active == True).Union(Select(Admin))
            Select(User).Union(Select(Admin), all=True)
        """
        return SetOperationQuery(self, "UNION", other, all=all)

    def Intersect(self, other, all: bool = False):
        """Combine with INTERSECT [ALL]."""
        return SetOperationQuery(self, "INTERSECT", other, all=all)

    def Except(self, other, all: bool = False):
        """Combine with EXCEPT [ALL]."""
        return SetOperationQuery(self, "EXCEPT", other, all=all)


def Select(*columns):
    """Convenience function that returns a SelectQuery instance so callers
    can use `Select(...)` as a function and chain `.From()`, `.Where()`, etc.

    Ejemplos:
        Select(User)                          # SELECT * FROM users
        Select(User.id, User.email)           # columnas de un modelo
        Select(User, Driver, Order.id)        # todas las columnas de User y Driver + Order.id
        Select("id", "email").From("auth.users")
        Select(RawExpression("*")).From("active_users")  # CTE
    """
    return SelectQuery(*columns)


# ============================================================
# SET OPERATIONS (UNION / INTERSECT / EXCEPT)
# ============================================================

class SetOperationQuery(Query):
    """UNION / INTERSECT / EXCEPT entre SelectQueries.
    
    Permite encadenar múltiples set operations y agregar ORDER BY / LIMIT / OFFSET
    sobre el resultado final.
    
    Usage:
        Select(User).Union(Select(Admin)).OrderBy(User.name).Limit(10)
        Select(A).Union(Select(B)).Intersect(Select(C))
        Select(A).Except(Select(B), all=True)
    """

    def __init__(self, left, op: str, right, all: bool = False):
        self.left = left
        self.op = op
        self.right = right
        self.all = all
        self._order_by = []
        self._limit = None
        self._offset = None

    def Union(self, other, all: bool = False):
        """Chain another UNION."""
        return SetOperationQuery(self, "UNION", other, all=all)

    def Intersect(self, other, all: bool = False):
        """Chain another INTERSECT."""
        return SetOperationQuery(self, "INTERSECT", other, all=all)

    def Except(self, other, all: bool = False):
        """Chain another EXCEPT."""
        return SetOperationQuery(self, "EXCEPT", other, all=all)

    def OrderBy(self, *cols):
        """ORDER BY applied to the combined result."""
        if cols:
            self._order_by.append({"cols": list(cols), "direction": None})
        return self

    def Asc(self):
        """Set ASC direction for last OrderBy."""
        if self._order_by:
            self._order_by[-1]["direction"] = "ASC"
        return self

    def Desc(self):
        """Set DESC direction for last OrderBy."""
        if self._order_by:
            self._order_by[-1]["direction"] = "DESC"
        return self

    def Limit(self, n: int):
        """LIMIT applied to the combined result."""
        self._limit = n
        return self

    def Offset(self, n: int):
        """OFFSET applied to the combined result."""
        self._offset = n
        return self

    def to_sql_params(self):
        left_sql, left_params = self.left.to_sql_params()
        right_sql, right_params = self.right.to_sql_params()

        op_str = f"{self.op} ALL" if self.all else self.op
        sql = f"({left_sql}) {op_str} ({right_sql})"
        params = left_params + right_params

        # ORDER BY
        if self._order_by:
            from ..orm.column import OrderExpression
            order_fragments = []
            for entry in self._order_by:
                cols = entry["cols"]
                direction = entry["direction"] or "ASC"
                for col in cols:
                    # Check if col is an OrderExpression (has its own direction)
                    if isinstance(col, OrderExpression):
                        order_fragments.append(col.to_sql())
                    elif hasattr(col, "to_sql_params"):
                        col_sql, col_params = col.to_sql_params()
                        order_fragments.append(f"{col_sql} {direction}")
                        params.extend(col_params)
                    elif hasattr(col, "to_sql"):
                        order_fragments.append(f"{col.to_sql()} {direction}")
                    else:
                        order_fragments.append(f"{str(col)} {direction}")
            sql += " ORDER BY " + ", ".join(order_fragments)

        # LIMIT
        if self._limit is not None:
            sql += " LIMIT %s"
            params.append(self._limit)

        # OFFSET
        if self._offset is not None:
            sql += " OFFSET %s"
            params.append(self._offset)

        return sql, params

    # Exec helpers (same as SelectQuery)
    def Exec(self):
        """Execute using current sync Session."""
        from ..core.session import SessionManager
        session = SessionManager.require_current()
        return session.exec(self)

    def all(self):
        """Execute and return all results."""
        return self.Exec().all()

    def first(self):
        """Execute and return first result."""
        return self.Exec().first()

    async def all_async(self):
        """Execute async and return all results."""
        from ..core.session import SessionManager
        session = SessionManager.require_current_async()
        return await session.exec(self).all()


# ============================================================
# DELETE
# ============================================================

class DeleteQuery(Query):
    """DELETE query builder with WHERE support.

    Usage:
        Delete(User).Where(User.id == 5).execute(engine)
        Delete(User).Where(User.is_active == False)
    """

    def __init__(self, model):
        self.model = model
        self.where_clauses = []
        self._returning = None
        self._last_column = None  # Para In/NotIn

    def Where(self, cond):
        if not self.where_clauses:
            self.where_clauses.append(("WHERE", cond))
        else:
            self.where_clauses.append(("AND", cond))
        self._last_column = cond if hasattr(cond, "to_sql") else None
        return self

    def And(self, cond):
        self.where_clauses.append(("AND", cond))
        self._last_column = cond if hasattr(cond, "to_sql") else None
        return self

    def Or(self, cond):
        self.where_clauses.append(("OR", cond))
        self._last_column = cond if hasattr(cond, "to_sql") else None
        return self

    def In(self, *values):
        """SQL IN después de Where. Soporta .In([1, 2]) y .In(1, 2)."""
        if not self._last_column:
            raise ValueError("In() debe usarse después de Where(columna)")
        from psqlmodel.orm.column import RawExpression

        # Aplanar valores si se pasa una lista única
        if len(values) == 1 and isinstance(values[0], (list, tuple, set)) and not isinstance(values[0], (str, bytes)):
            actual_values = values[0]
        else:
            actual_values = values

        # Si values es una Query (subconsulta)
        if hasattr(actual_values, "to_sql") or hasattr(actual_values, "to_sql_params"):
             in_expr = self._last_column.In(actual_values)
        else:
             in_expr = self._last_column.In(actual_values)
        
        if self.where_clauses and self.where_clauses[-1][0] in ("WHERE", "AND", "OR"):
            op, _ = self.where_clauses[-1]
            self.where_clauses[-1] = (op, in_expr)
        return self

    def NotIn(self, *values):
        """SQL NOT IN después de Where. Soporta .NotIn([1, 2]) y .NotIn(1, 2)."""
        if not self._last_column:
            raise ValueError("NotIn() debe usarse después de Where(columna)")
        from psqlmodel.column import RawExpression

        # Aplanar valores si se pasa una lista única
        if len(values) == 1 and isinstance(values[0], (list, tuple, set)) and not isinstance(values[0], (str, bytes)):
            actual_values = values[0]
        else:
            actual_values = values

        # Si values es una Query (subconsulta)
        if hasattr(actual_values, "to_sql") or hasattr(actual_values, "to_sql_params"):
            notin_expr = self._last_column.NotIn(actual_values)
        else:
            notin_expr = self._last_column.NotIn(actual_values)

        if self.where_clauses and self.where_clauses[-1][0] in ("WHERE", "AND", "OR"):
            op, _ = self.where_clauses[-1]
            self.where_clauses[-1] = (op, notin_expr)
        return self


    def Or(self, cond):
        self.where_clauses.append(("OR", cond))
        return self

    def Returning(self, *cols):
        """Add RETURNING clause to get deleted rows back."""
        self._returning = cols if cols else None
        
        # Calculate Layout
        if self._returning:
            normalized = []
            for c in self._returning:
                 normalized.append(c)
            self._layout = calculate_layout(normalized)
        else:
            self._layout = None
            
        return self

    def As(self, *aliases):
        """
        Assign aliases to the columns defined in Returning().
        Usage: .Returning(User.id, User.name).As("uid", "uname")
        """
        if not self._returning:
            raise ValueError("As() requires a preceding Returning() clause")
        
        if len(aliases) != len(self._returning):
            raise ValueError(
                f"As() received {len(aliases)} aliases but Returning() has {len(self._returning)} columns"
            )
        
        normalized = []
        for c, alias in zip(self._returning, aliases):
            if isinstance(c, Alias):
                 c = c.expr
            normalized.append(Alias(c, alias))
            
        self._returning = tuple(normalized)
        self._layout = calculate_layout(normalized)
        return self

    def to_sql_params(self):
        schema = getattr(self.model, "__schema__", "public") or "public"
        table = getattr(self.model, "__tablename__")

        sql = [f"DELETE FROM {schema}.{table}"]
        params = []

        # WHERE
        if self.where_clauses:
            where_parts = []
            for op, cond in self.where_clauses:
                if hasattr(cond, "to_sql_params"):
                    cond_sql, cond_params = cond.to_sql_params()
                else:
                    cond_sql, cond_params = str(cond), []
                where_parts.append(f"{op} {cond_sql}")
                params.extend(cond_params)
            sql.append(" ".join(where_parts))

        # RETURNING
        if self._returning:
            returning_parts = []
            for c in self._returning:
                if hasattr(c, "to_sql_params"):
                    c_sql, c_params = c.to_sql_params()
                    returning_parts.append(c_sql)
                    params.extend(c_params)
                elif hasattr(c, "to_sql"):
                    returning_parts.append(c.to_sql())
                else:
                    returning_parts.append(str(c))
                    
            sql.append(f"RETURNING {', '.join(returning_parts)}")

        return "\n".join(sql), params


def Delete(model):
    """Create a DELETE query for the given model."""
    return DeleteQuery(model)


# ============================================================
# UPDATE (Bulk/WHERE-based)
# ============================================================

class UpdateQuery(Query):
    """UPDATE query builder with SET and WHERE support.

    Usage:
        Update(User).Set(name="NewName").Where(User.id == 5).execute(engine)
        Update(User).Set(is_active=False).Where(User.last_login < cutoff).execute(engine)
    """

    def __init__(self, model):
        self.model = model
        self.set_clauses = []  # list of (column, value)
        self.where_clauses = []
        self._returning = None

    def Set(self, **kwargs):
        """
        Set columns to values using keyword arguments only.
        Example: .Set(email="foo", name="bar")
        This enables auto-completion of model attributes in most editors.
        """
        columns = getattr(self.model, "__columns__", {})
        for col_name, value in kwargs.items():
            if col_name in columns:
                col = columns[col_name]
                self.set_clauses.append((col, value))
            else:
                raise ValueError(f"Column '{col_name}' not found in model {self.model}")
        return self

    def SetMany(self, **kwargs):
        """Set multiple columns at once using keyword arguments.

        Usage: Update(User).SetMany(name="Alice", age=30).Where(...)
        """
        columns = getattr(self.model, "__columns__", {})
        for col_name, value in kwargs.items():
            if col_name in columns:
                col = columns[col_name]
                self.set_clauses.append((col, value))
        return self

    def Where(self, cond):
        if not self.where_clauses:
            self.where_clauses.append(("WHERE", cond))
        else:
            self.where_clauses.append(("AND", cond))
        return self

    def And(self, cond):
        self.where_clauses.append(("AND", cond))
        return self

    def Or(self, cond):
        self.where_clauses.append(("OR", cond))
        return self

    def Returning(self, *cols):
        """Add RETURNING clause to get updated rows back."""
        self._returning = cols if cols else None
        
        # Calculate Layout
        if self._returning:
            normalized = []
            for c in self._returning:
                 normalized.append(c)
            self._layout = calculate_layout(normalized)
        else:
            self._layout = None
            
        return self

    def As(self, *aliases):
        """
        Assign aliases to the columns defined in Returning().
        Usage: .Returning(User.id, User.name).As("uid", "uname")
        """
        if not self._returning:
            raise ValueError("As() requires a preceding Returning() clause")
        
        if len(aliases) != len(self._returning):
            raise ValueError(
                f"As() received {len(aliases)} aliases but Returning() has {len(self._returning)} columns"
            )
        
        normalized = []
        for c, alias in zip(self._returning, aliases):
            if isinstance(c, Alias):
                 c = c.expr
            normalized.append(Alias(c, alias))
            
        self._returning = tuple(normalized)
        self._layout = calculate_layout(normalized)
        return self

    def to_sql_params(self):
        if not self.set_clauses:
            raise ValueError("UPDATE query requires at least one SET clause")

        schema = getattr(self.model, "__schema__", "public") or "public"
        table = getattr(self.model, "__tablename__")

        sql = [f"UPDATE {schema}.{table}"]
        params = []

        # SET - support expressions (functions, subqueries, arithmetic, etc.)
        set_parts = []
        for col, value in self.set_clauses:
            col_name = col.name if hasattr(col, "name") else str(col)
            if hasattr(value, "to_sql_params"):
                val_sql, val_params = value.to_sql_params()
                if val_sql.strip().upper().startswith("SELECT"):
                    val_sql = f"({val_sql})"
                set_parts.append(f"{col_name} = {val_sql}")
                params.extend(val_params)
            elif hasattr(value, "to_sql"):
                val_sql = value.to_sql()
                if val_sql.strip().upper().startswith("SELECT"):
                    val_sql = f"({val_sql})"
                set_parts.append(f"{col_name} = {val_sql}")
            else:
                set_parts.append(f"{col_name} = %s")
                params.append(value)
        sql.append("SET " + ", ".join(set_parts))

        # WHERE
        if self.where_clauses:
            where_parts = []
            for op, cond in self.where_clauses:
                if hasattr(cond, "to_sql_params"):
                    cond_sql, cond_params = cond.to_sql_params()
                else:
                    cond_sql, cond_params = str(cond), []
                where_parts.append(f"{op} {cond_sql}")
                params.extend(cond_params)
            sql.append(" ".join(where_parts))

        # RETURNING
        if self._returning:
            returning_parts = []
            for c in self._returning:
                if hasattr(c, "to_sql_params"):
                    c_sql, c_params = c.to_sql_params()
                    returning_parts.append(c_sql)
                    params.extend(c_params)
                elif hasattr(c, "to_sql"):
                    returning_parts.append(c.to_sql())
                else:
                    returning_parts.append(str(c))
                    
            sql.append(f"RETURNING {', '.join(returning_parts)}")

        return "\n".join(sql), params


def Update(model):
    """Create an UPDATE query for the given model."""
    return UpdateQuery(model)


# ============================================================
# INSERT SELECT PROXY (fluent API helper)
# ============================================================

class InsertSelectProxy:
    """Proxy that allows chaining SelectQuery methods while maintaining InsertQuery context.
    
    Example:
        Insert(Archive)
            .Select(User.id, User.name)
            .Where(User.active == False)
            .And(NotExists(...))
            .Returning(Archive.id)
    """
    def __init__(self, insert_query, select_query):
        self.insert_query = insert_query
        self.select_query = select_query
    
    # Proxy SelectQuery methods
    def From(self, source):
        self.select_query.From(source)
        return self
    
    def Where(self, cond):
        self.select_query.Where(cond)
        return self
    
    def And(self, cond):
        self.select_query.And(cond)
        return self
    
    def Or(self, cond):
        self.select_query.Or(cond)
        return self
    
    def OrderBy(self, *cols):
        self.select_query.OrderBy(*cols)
        return self
    
    def Limit(self, n):
        self.select_query.Limit(n)
        return self
    
    def Offset(self, n):
        self.select_query.Offset(n)
        return self
    
    def In(self, values):
        self.select_query.In(values)
        return self
    
    def NotIn(self, values):
        self.select_query.NotIn(values)
        return self
    
    # InsertQuery methods remain available
    def Returning(self, *cols):
        self.insert_query.Returning(*cols)
        return self

    def As(self, *aliases):
        """Proxy .As() to the underlying insert query."""
        self.insert_query.As(*aliases)
        return self
    
    def OnConflict(self, conflict_column, *, do_update=None, do_nothing=False):
        self.insert_query.OnConflict(conflict_column, do_update=do_update, do_nothing=do_nothing)
        return self
    
    # Execution methods
    def to_sql_params(self):
        return self.insert_query.to_sql_params()
    
    def execute(self, engine, *params):
        return self.insert_query.execute(engine, *params)
    
    async def execute_async(self, engine, *params):
        return await self.insert_query.execute_async(engine, *params)


# ============================================================
# INSERT (with RETURNING and ON CONFLICT / UPSERT)
# ============================================================

class InsertQuery(Query):
    """INSERT query builder with RETURNING and ON CONFLICT (UPSERT) support.

    Usage:
        # Simple insert
        Insert(User).Values(name="Alice", age=30).execute(engine)

        # Insert with RETURNING
        Insert(User).Values(name="Alice", age=30).Returning(User.id).execute(engine)

        # UPSERT (insert or update on conflict)
        Insert(User).Values(email="a@b.com", name="Alice").OnConflict(
            User.email,
            do_update={"name": "Alice Updated"}
        ).execute(engine)
    """

    def __init__(self, *args):
        # Detect if first arg is a model or if all are columns
        if len(args) == 1 and hasattr(args[0], "__tablename__"):
            # Single model passed: Insert(User)
            self.model = args[0]
            self.target_columns = None  # Use all columns from model
        elif len(args) >= 1 and all(hasattr(a, "model") for a in args):
            # Columns passed: Insert(User.id, User.name)
            # Extract model from first column
            self.model = args[0].model
            self.target_columns = list(args)  # Store specific columns
        else:
            raise ValueError(
                "Insert() requires a model class or Column objects. "
                f"Got: {[type(a).__name__ for a in args]}"
            )
        self.values_dict = {}
        self.select_query = None  # For INSERT...SELECT
        self._returning = None
        self._on_conflict_column = None
        self._on_conflict_do_update = None
        self._on_conflict_do_nothing = False

    def Values(self, **kwargs):
        """
        Set column values for the insert, validating against model columns.
        Example: Insert(User).Values(name="Alice", email="a@b.com")
        Only model attributes are allowed (auto-completion in IDEs).
        """
        if self.select_query:
            raise ValueError("Cannot use .Values() with .Select() - choose one")
        columns = getattr(self.model, "__columns__", {})
        for col_name, value in kwargs.items():
            if col_name in columns:
                self.values_dict[col_name] = value
            else:
                raise ValueError(f"Column '{col_name}' not found in model {self.model}")
        return self

    def Select(self, *cols):
        """Configure INSERT ... SELECT.
        
        Can pass column list (which creates a new SelectQuery) or an existing SelectQuery object.
        """
        from .insert_select_proxy import InsertSelectProxy
        # SelectQuery is available in global scope
        
        if len(cols) == 1 and hasattr(cols[0], "to_sql_params") and hasattr(cols[0], "From") and not isinstance(cols[0], (str, int, float, bool)):
             # Assume it's a Query object
             self.select_query = cols[0]
        else:
             self.select_query = SelectQuery(*cols)
        return InsertSelectProxy(self, self.select_query)


    def Returning(self, *cols):
        """Add RETURNING clause to get inserted rows back."""
        self._returning = cols if cols else None
        
        # Calculate Layout
        if self._returning:
            normalized = []
            for c in self._returning:
                 normalized.append(c)
            self._layout = calculate_layout(normalized)
        else:
            self._layout = None

        return self

    def As(self, *aliases):
        """
        Assign aliases to the columns defined in Returning().
        Usage: .Returning(User.id, User.name).As("uid", "uname")
        """
        if not self._returning:
            raise ValueError("As() requires a preceding Returning() clause")
        
        if len(aliases) != len(self._returning):
            raise ValueError(
                f"As() received {len(aliases)} aliases but Returning() has {len(self._returning)} columns"
            )
        
        normalized = []
        for c, alias in zip(self._returning, aliases):
            if isinstance(c, Alias):
                 c = c.expr
            normalized.append(Alias(c, alias))
            
        self._returning = tuple(normalized)
        self._layout = calculate_layout(normalized)
        return self

    def OnConflict(self, conflict_column, *, do_update=None, do_nothing=False):
        """Handle conflicts (UPSERT).

        Args:
            conflict_column: The column that defines the conflict (usually unique/pk)
            do_update: Dict of {column_name: new_value} to update on conflict
            do_nothing: If True, do nothing on conflict (ignore)
        """
        self._on_conflict_column = conflict_column
        self._on_conflict_do_update = do_update
        self._on_conflict_do_nothing = do_nothing
        return self

    def to_sql_params(self):
        schema = getattr(self.model, "__schema__", "public") or "public"
        table = getattr(self.model, "__tablename__")

        # INSERT...SELECT path
        if self.select_query:
            # Use explicitly specified target_columns if provided, else infer from SELECT
            if self.target_columns:
                col_names = [c.name for c in self.target_columns]
            else:
                # Extract column names from SelectQuery columns
                col_names = []
                for c in self.select_query.columns:
                    if hasattr(c, "name"):
                        col_names.append(c.name)
                    elif hasattr(c, "expr") and hasattr(c.expr, "name"):  # Alias
                        col_names.append(c.expr.name)
                    else:
                        # For RawExpression or unknown, skip or use a generic name
                        pass
            
            # Get SELECT SQL
            select_sql, params = self.select_query.to_sql_params()
            
            sql = [f"INSERT INTO {schema}.{table}"]
            if col_names:
                sql.append(f"({', '.join(col_names)})")
            sql.append(select_sql)
            
            # ON CONFLICT (same logic as VALUES)
            if self._on_conflict_column is not None:
                conflict_col_name = (
                    self._on_conflict_column.name
                    if hasattr(self._on_conflict_column, "name")
                    else str(self._on_conflict_column)
                )
                if self._on_conflict_do_nothing:
                    sql.append(f"ON CONFLICT ({conflict_col_name}) DO NOTHING")
                elif self._on_conflict_do_update:
                    update_parts = []
                    for col_name, value in self._on_conflict_do_update.items():
                        if hasattr(value, "to_sql"):
                            update_parts.append(f"{col_name} = {value.to_sql()}")
                        else:
                            update_parts.append(f"{col_name} = %s")
                            params.append(value)
                    sql.append(
                        f"ON CONFLICT ({conflict_col_name}) DO UPDATE SET "
                        + ", ".join(update_parts)
                    )
            
            # RETURNING
            if self._returning:
                returning_parts = []
                for c in self._returning:
                    if hasattr(c, "to_sql_params"):
                        c_sql, c_params = c.to_sql_params()
                        returning_parts.append(c_sql)
                        params.extend(c_params)
                    elif hasattr(c, "to_sql"):
                        returning_parts.append(c.to_sql())
                    else:
                        returning_parts.append(str(c))
                
                sql.append(f"RETURNING {', '.join(returning_parts)}")
            
            return "\n".join(sql), params
        
        # INSERT...VALUES path (original logic)
        if not self.values_dict:
            raise ValueError("INSERT query requires at least one value or SELECT")

        col_names = list(self.values_dict.keys())
        placeholders = []
        params = []

        for col_name in col_names:
            value = self.values_dict[col_name]
            # Handle expressions (functions, subqueries, etc.)
            if hasattr(value, "to_sql_params"):
                val_sql, val_params = value.to_sql_params()
                placeholders.append(val_sql)
                params.extend(val_params)
            elif hasattr(value, "to_sql"):
                placeholders.append(value.to_sql())
            else:
                # Note: dict/list values for jsonb columns are passed as-is
                # The execution layer (session/transaction) handles serialization
                # appropriately for asyncpg (json.dumps) vs psycopg (Jsonb wrapper)
                placeholders.append("%s")
                params.append(value)

        sql = [f"INSERT INTO {schema}.{table} ({', '.join(col_names)})"]
        sql.append(f"VALUES ({', '.join(placeholders)})")

        # ON CONFLICT
        if self._on_conflict_column is not None:
            conflict_col_name = (
                self._on_conflict_column.name
                if hasattr(self._on_conflict_column, "name")
                else str(self._on_conflict_column)
            )

            if self._on_conflict_do_nothing:
                sql.append(f"ON CONFLICT ({conflict_col_name}) DO NOTHING")
            elif self._on_conflict_do_update:
                update_parts = []
                for col_name, value in self._on_conflict_do_update.items():
                    # Support EXCLUDED references and expressions
                    if hasattr(value, "to_sql_params"):
                        val_sql, val_params = value.to_sql_params()
                        update_parts.append(f"{col_name} = {val_sql}")
                        params.extend(val_params)
                    elif hasattr(value, "to_sql"):
                        update_parts.append(f"{col_name} = {value.to_sql()}")
                    else:
                        update_parts.append(f"{col_name} = %s")
                        params.append(value)
                sql.append(
                    f"ON CONFLICT ({conflict_col_name}) DO UPDATE SET "
                    + ", ".join(update_parts)
                )

        # RETURNING
        if self._returning:
            returning_parts = []
            for c in self._returning:
                if hasattr(c, "to_sql_params"):
                    c_sql, c_params = c.to_sql_params()
                    returning_parts.append(c_sql)
                    params.extend(c_params)
                elif hasattr(c, "to_sql"):
                    returning_parts.append(c.to_sql())
                else:
                    returning_parts.append(str(c))
            
            sql.append(f"RETURNING {', '.join(returning_parts)}")

        return "\n".join(sql), params


def Insert(*args):
    """Create an INSERT query for the given model or columns.
    
    Usage:
        Insert(User)                           # All columns
        Insert(User.id, User.name).Select(...) # Specific columns
    """
    return InsertQuery(*args)


# ============================================================
# BULK OPERATIONS
# ============================================================

class BulkInsertQuery(Query):
    """Bulk INSERT query for inserting multiple rows at once.

    Usage:
        BulkInsert(User, [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]).execute(engine)
    """

    def __init__(self, model, rows: list):
        self.model = model
        self.rows = rows
        self._returning = None
        self._on_conflict_column = None
        self._on_conflict_do_update = None
        self._on_conflict_do_nothing = False

    def Returning(self, *cols):
        self._returning = cols if cols else None
        return self

    def As(self, *aliases):
        """
        Assign aliases to the columns defined in Returning().
        Usage: .Returning(User.id, User.name).As("uid", "uname")
        """
        if not self._returning:
            raise ValueError("As() requires a preceding Returning() clause")
        
        if len(aliases) != len(self._returning):
            raise ValueError(
                f"As() received {len(aliases)} aliases but Returning() has {len(self._returning)} columns"
            )
        
        normalized = []
        from ..orm.column import Alias
        for c, alias in zip(self._returning, aliases):
            if isinstance(c, Alias):
                 c = c.expr
            normalized.append(Alias(c, alias))
            
        self._returning = tuple(normalized)
        return self

    def OnConflict(self, conflict_column, *, do_update=None, do_nothing=False):
        self._on_conflict_column = conflict_column
        self._on_conflict_do_update = do_update
        self._on_conflict_do_nothing = do_nothing
        return self

    def to_sql_params(self):
        if not self.rows:
            raise ValueError("BulkInsert requires at least one row")

        schema = getattr(self.model, "__schema__", "public") or "public"
        table = getattr(self.model, "__tablename__")

        # Get column names from first row
        col_names = list(self.rows[0].keys())

        # Build VALUES clause for all rows
        values_clauses = []
        params = []
        columns = getattr(self.model, "__columns__", {})
    
        for row in self.rows:
            placeholders = ["%s"] * len(col_names)
            values_clauses.append(f"({', '.join(placeholders)})")
            for col_name in col_names:
                value = row.get(col_name)
                # Note: dict/list values for jsonb columns are passed as-is
                # The execution layer handles serialization appropriately
                params.append(value)

        sql = [f"INSERT INTO {schema}.{table} ({', '.join(col_names)})"]
        sql.append("VALUES " + ", ".join(values_clauses))

        # ON CONFLICT
        if self._on_conflict_column is not None:
            conflict_col_name = (
                self._on_conflict_column.name
                if hasattr(self._on_conflict_column, "name")
                else str(self._on_conflict_column)
            )

            if self._on_conflict_do_nothing:
                sql.append(f"ON CONFLICT ({conflict_col_name}) DO NOTHING")
            elif self._on_conflict_do_update:
                update_parts = []
                for col_name, value in self._on_conflict_do_update.items():
                    update_parts.append(f"{col_name} = %s")
                    params.append(value)
                sql.append(
                    f"ON CONFLICT ({conflict_col_name}) DO UPDATE SET "
                    + ", ".join(update_parts)
                )

        # RETURNING
        if self._returning:
            returning_parts = []
            for c in self._returning:
                if hasattr(c, "to_sql_params"):
                    c_sql, c_params = c.to_sql_params()
                    returning_parts.append(c_sql)
                    params.extend(c_params)
                elif hasattr(c, "to_sql"):
                    returning_parts.append(c.to_sql())
                else:
                    returning_parts.append(str(c))
            
            sql.append(f"RETURNING {', '.join(returning_parts)}")

        return "\n".join(sql), params


def BulkInsert(model, rows: list):
    """Create a bulk INSERT query for the given model and rows."""
    return BulkInsertQuery(model, rows)


class BulkUpdateQuery(Query):
    """Bulk UPDATE query using CASE WHEN for updating multiple rows efficiently.

    Usage:
        # Update specific rows by primary key
        BulkUpdate(User, User.id, [
            {"id": 1, "name": "Alice Updated"},
            {"id": 2, "name": "Bob Updated"},
        ]).execute(engine)
    """

    def __init__(self, model, pk_column, rows: list):
        self.model = model
        self.pk_column = pk_column
        self.rows = rows
        self._returning = None

    def Returning(self, *cols):
        self._returning = cols if cols else None
        return self

    def As(self, *aliases):
        """
        Assign aliases to the columns defined in Returning().
        Usage: .Returning(User.id, User.name).As("uid", "uname")
        """
        if not self._returning:
            raise ValueError("As() requires a preceding Returning() clause")
        
        if len(aliases) != len(self._returning):
            raise ValueError(
                f"As() received {len(aliases)} aliases but Returning() has {len(self._returning)} columns"
            )
        
        normalized = []
        from ..orm.column import Alias
        for c, alias in zip(self._returning, aliases):
            if isinstance(c, Alias):
                 c = c.expr
            normalized.append(Alias(c, alias))
            
        self._returning = tuple(normalized)
        return self

    def to_sql_params(self):
        if not self.rows:
            raise ValueError("BulkUpdate requires at least one row")

        schema = getattr(self.model, "__schema__", "public") or "public"
        table = getattr(self.model, "__tablename__")
        pk_name = (
            self.pk_column.name if hasattr(self.pk_column, "name") else str(self.pk_column)
        )

        # Get all column names to update (excluding PK)
        update_cols = set()
        pk_values = []
        for row in self.rows:
            pk_values.append(row.get(pk_name))
            for key in row.keys():
                if key != pk_name:
                    update_cols.add(key)

        # Build CASE WHEN statements for each column
        set_parts = []
        params = []

        for col_name in update_cols:
            case_parts = []
            for row in self.rows:
                if col_name in row:
                    case_parts.append(f"WHEN {pk_name} = %s THEN %s")
                    params.append(row.get(pk_name))
                    params.append(row.get(col_name))
            if case_parts:
                set_parts.append(
                    f"{col_name} = CASE {' '.join(case_parts)} ELSE {col_name} END"
                )

        if not set_parts:
            raise ValueError(
                "BulkUpdate requires at least one column to update (besides PK)"
            )

        sql = [f"UPDATE {schema}.{table}"]
        sql.append("SET " + ", ".join(set_parts))

        # WHERE pk IN (...)
        in_placeholders = ", ".join(["%s"] * len(pk_values))
        sql.append(f"WHERE {pk_name} IN ({in_placeholders})")
        params.extend(pk_values)

        # RETURNING
        if self._returning:
            returning_parts = []
            for c in self._returning:
                if hasattr(c, "to_sql_params"):
                    c_sql, c_params = c.to_sql_params()
                    returning_parts.append(c_sql)
                    params.extend(c_params)
                elif hasattr(c, "to_sql"):
                    returning_parts.append(c.to_sql())
                else:
                    returning_parts.append(str(c))
            
            sql.append(f"RETURNING {', '.join(returning_parts)}")

        return "\n".join(sql), params


def BulkUpdate(model, pk_column, rows: list):
    """Create a bulk UPDATE query for the given model using CASE WHEN."""
    return BulkUpdateQuery(model, pk_column, rows)


class BulkDeleteQuery(Query):
    """Bulk DELETE query for deleting multiple rows by primary key.

    Usage:
        BulkDelete(User, User.id, [1, 2, 3]).execute(engine)
    """

    def __init__(self, model, pk_column, pk_values: list):
        self.model = model
        self.pk_column = pk_column
        self.pk_values = pk_values
        self._returning = None

    def Returning(self, *cols):
        self._returning = cols if cols else None
        return self

    def As(self, *aliases):
        """
        Assign aliases to the columns defined in Returning().
        Usage: .Returning(User.id, User.name).As("uid", "uname")
        """
        if not self._returning:
            raise ValueError("As() requires a preceding Returning() clause")
        
        if len(aliases) != len(self._returning):
            raise ValueError(
                f"As() received {len(aliases)} aliases but Returning() has {len(self._returning)} columns"
            )
        
        normalized = []
        from ..orm.column import Alias
        for c, alias in zip(self._returning, aliases):
            if isinstance(c, Alias):
                 c = c.expr
            normalized.append(Alias(c, alias))
            
        self._returning = tuple(normalized)
        return self

    def to_sql_params(self):
        if not self.pk_values:
            raise ValueError("BulkDelete requires at least one primary key value")

        schema = getattr(self.model, "__schema__", "public") or "public"
        table = getattr(self.model, "__tablename__")
        pk_name = (
            self.pk_column.name if hasattr(self.pk_column, "name") else str(self.pk_column)
        )

        in_placeholders = ", ".join(["%s"] * len(self.pk_values))
        sql = [f"DELETE FROM {schema}.{table}"]
        sql.append(f"WHERE {pk_name} IN ({in_placeholders})")
        params = list(self.pk_values)

        # RETURNING
        if self._returning:
            returning_parts = []
            for c in self._returning:
                if hasattr(c, "to_sql_params"):
                    c_sql, c_params = c.to_sql_params()
                    returning_parts.append(c_sql)
                    params.extend(c_params)
                elif hasattr(c, "to_sql"):
                    returning_parts.append(c.to_sql())
                else:
                    returning_parts.append(str(c))
            
            sql.append(f"RETURNING {', '.join(returning_parts)}")

        return "\n".join(sql), params


def BulkDelete(model, pk_column, pk_values: list):
    """Create a bulk DELETE query for the given model by primary key values."""
    return BulkDeleteQuery(model, pk_column, pk_values)


# ============================================================
# BULK OPERATIONS
# ============================================================

class CTEQuery(Query):
    """CTE (WITH clause) query builder.

    Usage:
        # Simple CTE
        With("active_users", Select(User.id, User.name).Where(User.active == True)) \
            .Then(Select(RawExpression("*")).From("active_users")) \
            .execute(engine)

        # Multiple CTEs
        With("rich_users", Select(User.id).Where(User.balance > 1000)) \
            .With("active_users", Select(User.id).Where(User.active == True)) \
            .Then(
                InsertFromSelect(
                    Transactions, ["user_id", "type"],
                    Select(RawExpression("id"), RawExpression("'bonus'")).From("rich_users")
                )
            ).execute(engine)
    """

    def __init__(self, name: str, query):
        """
        Args:
            name: CTE alias name
            query: The query for this CTE
        """
        self.ctes = [(name, query)]
        self.final_query = None

    def With(self, name: str, query):
        """Add another CTE to the WITH clause."""
        self.ctes.append((name, query))
        return self

    def Then(self, query):
        """Set the final query that uses the CTEs.
        
        Smart FROM inference: If the final query is a SelectQuery with exactly
        one CTE and no explicit .From(), automatically set FROM to the CTE name.
        """
        self.final_query = query
        
        # Smart FROM inference for SelectQuery
        if isinstance(query, SelectQuery):
            # Auto-infer FROM only if:
            # 1. Exactly one CTE registered
            # 2. No explicit FROM clause set
            if len(self.ctes) == 1 and query._from is None:
                query._from = self.ctes[0][0]  # Set FROM to CTE name
        
        return self

    def to_sql_params(self):
        if not self.final_query:
            raise ValueError("CTE requires a final query via .Then()")

        params = []
        cte_parts = []

        for name, cte_query in self.ctes:
            cte_sql, cte_params = cte_query.to_sql_params()
            cte_parts.append(f"{name} AS (\n{cte_sql}\n)")
            params.extend(cte_params)

        final_sql, final_params = self.final_query.to_sql_params()
        params.extend(final_params)

        sql = "WITH " + ",\n".join(cte_parts) + "\n" + final_sql
        return sql, params


def With(name: str, query):
    """Create a CTE (WITH clause) query."""
    return CTEQuery(name, query)
