"""
PSQLModel - A PostgreSQL ORM with QueryBuilder support.
"""

__version__ = "0.9.2"

# Core
from psqlmodel.orm.model import PSQLModel
from psqlmodel.orm.column import Column, Identifier
from psqlmodel.orm.table import table

# Exceptions
from psqlmodel.core.engine import (
    PSQLModelError,
    DatabaseNotFoundError,
    ConnectionError,
)

# Types
from psqlmodel.orm.types import (
    integer, bigint, smallint, serial, bigserial, smallserial,
    varchar, char, text, bytea,
    boolean,
    real, double, numeric, money,
    date, time, timestamp, interval,
    jsonb, json, uuid,
    bit, varbit, point, line, circle, polygon,
)

# Query Builder
from psqlmodel.query.builder import (
    Select, Insert, Update, Delete,
    With,
    BulkInsert, BulkUpdate, BulkDelete,
    SetOperationQuery,
)

# Expressions
from psqlmodel.orm.column import (
    RawExpression,
    BinaryExpression,
    LogicalExpression,
    Alias,
    # CASE
    Case, CaseExpression,
    # Functions
    Now, Coalesce, Nullif, Greatest, Least,
    Lower, Upper, Length, Concat, Func, FuncExpression,
    # JSON
    JsonbBuildObject, JsonbAgg, ToJsonb, JsonbExtract, JsonbExtractText,
    # Arithmetic
    ArithmeticExpression,
    # Subquery
    SubqueryValue, Scalar,
    # EXCLUDED (for UPSERT)
    Excluded, ExcludedColumn,
    # VALUES
    Values, ValuesExpression,
    # Aggregates
    Sum, Avg, Count, RowNumber,
    AggregateOrWindow,
    # EXISTS
    Exists, NotExists, ExistsExpression,
    # BETWEEN / ANY-ALL (new)
    BetweenExpression, AnyAllExpression,
    # Full-text search (new)
    ToTsVector, ToTsQuery, PlainToTsQuery, PhraseToTsQuery, WebsearchToTsQuery,
    TsRank, TsHeadline,
)

# Engine & Sessions
from psqlmodel.core.engine import create_engine, create_async_engine
from psqlmodel.core.session import Session, AsyncSession
from psqlmodel.core.transactions import Transaction, AsyncTransaction

# Middlewares
from psqlmodel.integrations.middlewares import (
    ValidationMiddleware,
    MetricsMiddleware,
    AuditMiddleware,
    LoggingMiddleware,
    RetryMiddleware,
)

# PSQLModel
from psqlmodel.orm.model import PSQLModel

# Table Constraints
from psqlmodel.orm.table import (
    Constraint,
    UniqueConstraint,
    PrimaryKeyConstraint,
    ForeignKeyConstraint,
    CheckConstraint,
    Index,
)

# Triggers
from psqlmodel.db.triggers import (
    Trigger,
    Old,
    New,
    trigger,
    TriggerColumnReference,
    TriggerCondition,
)

# Relationships
from psqlmodel.orm.relationships import (
    Relationship,
    Relation,
    OneToMany, ManyToOne, OneToOne, ManyToMany
)

# Subscriber
from psqlmodel.db.subscriber import Subscribe

# Migrations
from psqlmodel.migrations import (
    MigrationManager,
    MigrationConfig,
    Migration,
    MigrationError,
    SchemaDriftError,
)

# Utils (date/time functions)
from psqlmodel.utils import (
    gen_default_uuid,
    now, current_date,
    Interval,
    gen_salt, crypt,
)


__all__ = [
    # Core
    "PSQLModel", "Column", "table",
    # Query Builder
    "Select", "Insert", "Update", "Delete",
    "With",
    "BulkInsert", "BulkUpdate", "BulkDelete",
    # Expressions
    "RawExpression", "BinaryExpression", "LogicalExpression", "Alias",
    "Case", "CaseExpression",
    "Now", "Coalesce", "Nullif", "Greatest", "Least",
    "Lower", "Upper", "Length", "Concat", "Func", "FuncExpression",
    "JsonbBuildObject", "JsonbAgg", "ToJsonb", "JsonbExtract", "JsonbExtractText",
    "ArithmeticExpression",
    "SubqueryValue", "Scalar",
    "Excluded", "ExcludedColumn",
    "Values", "ValuesExpression",
    "Sum", "Avg", "Count", "RowNumber", "AggregateOrWindow",
    "Exists", "NotExists", "ExistsExpression",
    # Engine
    "create_engine", "create_async_engine", "Session", "AsyncSession",
    "Transaction", "AsyncTransaction",
    # Exceptions
    "PSQLModelError", "DatabaseNotFoundError", "ConnectionError",
    # Middlewares
    "ValidationMiddleware", "MetricsMiddleware",
    "AuditMiddleware", "LoggingMiddleware", "RetryMiddleware",
    # Constraints
    "Constraint", "UniqueConstraint", "PrimaryKeyConstraint",
    "ForeignKeyConstraint", "CheckConstraint", "Index",
    # Triggers
    "Trigger", "Old", "New", "trigger",
    "TriggerColumnReference", "TriggerCondition",
    # Relaciones
    "Relationship",
    "Relation",
    # Aliases por compatibilidad
    "OneToMany", "ManyToOne", "OneToOne", "ManyToMany",
    "Subscribe",
    # Migrations
    "MigrationManager", "MigrationConfig", "Migration",
    "MigrationError", "SchemaDriftError",
    # PSQLModel
    "PSQLModel"
]

