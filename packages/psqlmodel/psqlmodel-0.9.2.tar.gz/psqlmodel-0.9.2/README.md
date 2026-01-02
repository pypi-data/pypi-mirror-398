# PSQLModel

[![PyPI version](https://badge.fury.io/py/psqlmodel.svg)](https://badge.fury.io/py/psqlmodel)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**PSQLModel** is a modern, lightweight asynchronous ORM/Framework for PostgreSQL. It combines the speed of `asyncpg` with a Pythonic API for generic relationship handling, complex query generation, and robust schema migrations.

> [!WARNING]
> **Project in Active Development (Beta)**
>
> This package is currently in **BETA**. APIs may change slightly between versions as we refine the architecture.
>
> We strongly encourage the community to **contribute**! If you find bugs, see opportunities for optimization, or want to help structure the code better, please submit a PR or open an issue. Let's build the best Python async ORM/Framework together.

---

## 🏗️ Core Modules

The framework is structured into several key modules:

*   **`psqlmodel.orm`**: Core Object-Relational Mapping logic. Defines `PSQLModel`, `Column`, `Table`, and relationship descriptors.
*   **`psqlmodel.core`**: Engine and Session management (`create_engine`, `Session`, `AsyncSession`). Handles connection pooling and transaction lifecycles.
*   **`psqlmodel.migrations`**: A complete migration system (Alembic-style) supporting auto-generation, DAG dependency validation, and atomic rollbacks.
*   **`psqlmodel.query_builder`**: A fluent API for constructing complex SQL queries (SELECT, INSERT, CTEs) programmatically.
*   **`psqlmodel.db.triggers`**: A DSL for defining reactive database triggers in pure Python.

---

## 🚀 Quick Start

### 1. Define Models
Use Python type hints and the `Column` descriptor to define your schema.

```python
from psqlmodel import PSQLModel, Column, table, Relationship, Relation
from psqlmodel.types import serial, varchar, timestamp
from datetime import datetime

@table("users")
class User(PSQLModel):
    id: serial = Column(primary_key=True)
    username: str = Column(max_len=50, unique=True, nullable=False)
    created_at: timestamp = Column(default=datetime.now)
    
    # Relationships
    posts: Relation[list["Post"]] = Relationship("Post")

@table("posts")
class Post(PSQLModel):
    id: serial = Column(primary_key=True)
    title: str = Column(max_len=200)
    user_id: int = Column(foreign_key="users.id")
    
    # Inverse relationship
    author: Relation["User"] = Relationship("User")
```

### 2. Async Usage
Perform operations using `AsyncSession`.

```python
from psqlmodel import create_engine, Select, Session

async def main():
    engine = create_engine("postgresql://user:pass@localhost/db", async_=True)
    
    async with Session(engine) as session:
        # Create
        new_user = User(username="hashdown")
        await session.add(new_user)
        
        # Query with Eager Loading (JOIN)
        stmt = Select(User).Where(User.username == "hashdown").Include(Posts) #<- Use the Model name instead of the table name or User.posts
        user = await session.exec(stmt).first()
```

---

## 🔍 Query Structure

PSQLModel provides a powerful Query Builder for complex SQL generation.

### Select & Join
```python
# SELECT * FROM users 
# JOIN posts ON posts.user_id = users.id 
# WHERE users.age > 18
stmt = (
    Select(User)
    .Where(User.age > 18)
    .Include(Post) #<- Use the Model name instead of the table name or User.posts
)
```

### CTEs and Chained Inserts
Build Common Table Expressions (WITH clauses) easily.

```python
from psqlmodel import With, Insert

# WITH new_org AS (INSERT ...) 
# INSERT INTO users ... FROM new_org
stmt_org = Insert(Organization).Values(name="MyCorp").Returning(Organization.id)

stmt_user = (
    Insert(User)
    .Select("email", "org_id")
    .From("new_org")
)

query = With("new_org", stmt_org).Then(stmt_user)
```

### UPSERT (On Conflict)
```python
Insert(User).Values(...).OnConflict(
    User.email,
    do_update={"last_login": Now()}
)
```

---

## 📦 Migration System

PSQLModel includes a CLI for managing schema changes.

| Command | Description |
|:---|:---|
| `migrate init` | Initialize migrations directory. |
| `migrate generate -m "msg"` | Auto-generate migration from model changes. |
| `migrate upgrade head` | Apply pending migrations. |
| `migrate downgrade -1` | Revert the last migration. |
| `migrate history` | Show migration history (DDL & Data). |
| `migrate failures` | View failed migration attempts. |

### Data Migrations
For complex data transformations, inherit from `DataMigration` and use `iter_batches`.

```python
from psqlmodel.migrations import DataMigration

class Migration_Backfill(DataMigration):
    timeout_seconds = 600
    
    async def up_async(self, ctx):
        async for batch in self.iter_batches(ctx, "users"):
            # Transform batch...
            pass
```

---

## ⚡ Types & Triggers

### Types
Import types from `psqlmodel.types` for clarity in definitions:
*   `serial`, `bigserial`, `uuid`
*   `varchar`, `text`, `jsonb`
*   `timestamp`, `date`, `boolean`

### Trigger DSL
Define reactive database logic purely in Python:

```python
from psqlmodel import trigger, Trigger, Old, New

def log_change(old, new):
    print(f"User changed from {old.email} to {new.email}")

@trigger(Trigger().BeforeUpdate().Exec(log_change))
@table("users")
class User(PSQLModel):
    ...
```

---

## 🔌 Integrations & Middlewares

PSQLModel is designed to be extensible. We provide built-in integrations for common patterns:

### Middlewares
Plug these into your engine to enhance query execution:
*   **ValidationMiddleware**: Enforces schema constraints (max_len, min_value) at runtime.
*   **AuditMiddleware**: Records detailed logs of executed queries.
*   **MetricsMiddleware**: Collects performance stats (latency, query counts).
*   **RetryMiddleware**: Automatically retries failed queries (e.g., deadlocks, connection loss).

### External Integrations
Triggers can interact with external systems (requires `plpython3u`):
*   **Kafka**: Produce events directly from database triggers.
*   **Redis**: Publish messages or cache invalidations from triggers.

```python
from psqlmodel.integrations.middlewares import ValidationMiddleware
engine.add_middleware_sync(ValidationMiddleware(model=User).sync)
```

---

## 📚 Documentation & Contributing

**This documentation is a living document.** As the framework evolves, we will continue adding more guides, API references, and best practices.

We strongly encourage the community to **contribute**! 
*   **Documentation**: Help us improve this README, write tutorials, or add docstrings.
*   **Examples**: Have a cool use case? Add it to `examples/`.
*   **Code**: Fix bugs, add features, or optimize performance.

Please check the `examples/` directory for advanced usage patterns (replication, middlewares, complex queries).

**Repo Structure:**
*   `/psqlmodel`: Source code.
*   `/examples`: Comprehensive usage examples.
*   `/tests`: Pytest suite.

License: MIT
