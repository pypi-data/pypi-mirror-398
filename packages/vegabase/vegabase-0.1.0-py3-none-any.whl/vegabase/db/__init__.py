"""
SQLAlchemy Core + Pydantic

Type-safe database queries with runtime validation.

Example:
    ```python
    from sqlalchemy import MetaData, Table, Column, Integer, String, select
    from pydantic import BaseModel
    from vegabase.db import Database, query

    # Define table (SQLAlchemy Core)
    metadata = MetaData()
    users = Table('users', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
    )

    # Define result model (Pydantic)
    class User(BaseModel):
        id: int
        name: str

    # Create typed query function
    def get_user(user_id: int) -> TypedQuery[User]:
        return query(User, select(users).where(users.c.id == user_id))

    # Execute with full type safety
    db = Database("sqlite:///app.db")
    with db.connection() as conn:
        user = conn.one(get_user(42))  # user is User, not Any
        print(user.name)  # IDE autocomplete works!
    ```
"""

from .async_database import AsyncDatabase, AsyncTypedConnection
from .database import Database, TypedConnection
from .errors import (
    DatabaseError,
    NotFoundError,
    TooManyRowsError,
    ValidationError,
)
from .hooks import (
    CamelCaseHook,
    Hook,
    HookChain,
    LoggingHook,
    QueryContext,
    SlowQueryHook,
)
from .schema import SchemaChange, apply, create_all, drop_all, plan
from .types import T, TypedQuery, query

__version__ = "0.1.0"

__all__ = [
    # Core types
    "TypedQuery",
    "query",
    "T",
    # Sync database
    "Database",
    "TypedConnection",
    # Async database
    "AsyncDatabase",
    "AsyncTypedConnection",
    # Errors
    "DatabaseError",
    "NotFoundError",
    "TooManyRowsError",
    "ValidationError",
    # Hooks
    "Hook",
    "HookChain",
    "QueryContext",
    "LoggingHook",
    "CamelCaseHook",
    "SlowQueryHook",
    # Schema management
    "plan",
    "apply",
    "create_all",
    "drop_all",
    "SchemaChange",
]
