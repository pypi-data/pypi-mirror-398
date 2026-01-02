# vegabase.db

**Strict SQL** — A type-safe database client for Python

A DB adapter which uses SQLAlchemy Core for query composition and Pydantic for runtime validation. 

- **Static type safety** — IDE knows query return types (`List[User]`, not `List[Any]`)
- **Runtime validation** — Pydantic validates every row from the database
- **Cross-database** — Works with PostgreSQL, SQLite, MySQL via SQLAlchemy
- **No ORM magic** — Decoupled tables and models, explicit queries only

## Installation

```bash
pip install vegabase

# With database drivers
pip install vegabase[postgres]  # PostgreSQL with psycopg3
pip install vegabase[async]     # Async support with aiosqlite/asyncpg
```

## Quick Start

```python
from sqlalchemy import MetaData, Table, Column, Integer, String, select
from pydantic import BaseModel
from vegabase.db import Database, query, TypedQuery

# 1. Define table (SQLAlchemy Core)
metadata = MetaData()
users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('email', String),
)

# 2. Define result model (Pydantic)
class User(BaseModel):
    id: int
    name: str
    email: str

# 3. Create typed query function (Option A - recommended)
def get_user(user_id: int) -> TypedQuery[User]:
    return query(User, select(users).where(users.c.id == user_id))

# 4. Execute with full type safety
db = Database("sqlite:///app.db")

with db.connection() as conn:
    user = conn.one(get_user(42))  # IDE knows: user is User
    print(user.name)               # Autocomplete works!
```

## Query Methods

vegabase.db provides explicit query methods:

| Method | Returns | Raises |
|--------|---------|--------|
| `one(query)` | Single `T` | `NotFoundError` (0 rows), `TooManyRowsError` (>1) |
| `maybe_one(query)` | `T \| None` | `TooManyRowsError` (>1) |
| `many(query)` | `List[T]` (1+) | `NotFoundError` (0 rows) |
| `all(query)` | `List[T]` (0+) | Never (for count) |

## Mutations

### Execute (INSERT/UPDATE/DELETE)

```python
from sqlalchemy import insert, update, delete

with db.transaction() as conn:
    # INSERT/UPDATE/DELETE without RETURNING - returns row count
    count = conn.execute(insert(users).values(name="Alice", email="alice@example.com"))
    count = conn.execute(update(users).where(users.c.id == 1).values(name="Alice Updated"))
    count = conn.execute(delete(users).where(users.c.id == 1))
```

### RETURNING Clause

```python
# INSERT/UPDATE/DELETE with RETURNING - returns typed model
new_user = conn.returning_one(
    query(User, insert(users).values(name="Alice").returning(users))
)

deleted_users = conn.returning_many(
    query(User, delete(users).where(users.c.active == False).returning(users))
)
```

### Scalar Queries

```python
from sqlalchemy import func

# Aggregate queries returning single values
count = conn.scalar(select(func.count()).select_from(users))
max_id = conn.scalar(select(func.max(users.c.id)))
```

### Bulk Insert

```python
conn.execute_many(
    insert(users),
    [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]
)
```

## Async Support

```python
from vegabase.db import AsyncDatabase, query

db = AsyncDatabase("sqlite+aiosqlite:///app.db")

async with db.connection() as conn:
    user = await conn.one(get_user(42))
    users = await conn.all(query(User, select(users)))
    
    # All mutation methods are also available with await
    await conn.execute(insert(users).values(name="Alice"))
    new_user = await conn.returning_one(query(User, insert(...).returning(users)))
```

## Transactions

```python
# Auto-commits on success, rolls back on exception
with db.transaction() as conn:
    conn.returning_one(query(User, insert(users).values(name="Alice").returning(users)))
    conn.returning_one(query(User, insert(users).values(name="Bob").returning(users)))
    # Both committed together
```

## Performance: Skip Validation

For bulk operations where you trust the data:

```python
# Bypass Pydantic validation (constructs without checking)
users = conn.all(get_all_users(), skip_validation=True)
```

## Schema Management (No Migration Files!)

vegabase.db uses a **plan/apply** pattern instead of migration files:

### CLI Usage

```bash
# Create db/schema.py with your schema
# Then preview changes:
vegabase db plan

# Apply changes to database:
vegabase db apply

# Skip confirmation (for CI/CD):
vegabase db apply --yes
```

**Convention:** The CLI looks for `backend/db/schema.py` with:
```python
# backend/db/schema.py
from sqlalchemy import MetaData, Table, Column, Integer, String

DATABASE_URL = "sqlite:///app.db"  # or os.environ["DATABASE_URL"]
metadata = MetaData()
users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100)),
)
```

### Python API

```python
from vegabase.db import Database, plan, apply

db = Database("postgresql://localhost/myapp")

# Preview changes (dry run)
changes = plan(db.engine, metadata)
for change in changes:
    print(change)
# → create_table: users

# Apply changes to database
applied = apply(db.engine, metadata)
print(f"Applied {len(applied)} changes")
```

### Why No Migration Files?

| Aspect | Migration Files | plan/apply |
|--------|-----------------|------------|
| Merge conflicts | 💀 Constant pain | ✅ None |
| Rollback | ⚠️ Rarely works | ❌ Use backups |
| Simplicity | ❌ Complex | ✅ Simple |
| Audit trail | ✅ Git history | ⚠️ DB logs only |

### Safety Options

```python
# Default: only safe operations
apply(db.engine, metadata)  # Creates tables, adds columns

# Opt-in to dangerous operations
apply(db.engine, metadata,
    drop_columns=True,   # ⚠️ Data loss possible
    drop_tables=True,    # ⚠️ Data loss possible
    modify_columns=True, # ⚠️ May fail with data
)
```

## Philosophy

This DB adapter differs from SQLModel/ORMs:

| Aspect | SQLModel | vegabase.db |
|--------|----------|--------|
| Philosophy | One class = table + model | Tables and models are separate |
| State | Connected objects tracked by Session | Disconnected data (just Pydantic) |
| N+1 Problem | Possible (lazy loading) | Impossible (no magic) |
| Migrations | Files or Alembic | plan/apply (no files) |

## License

MIT
