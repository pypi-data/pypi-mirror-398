"""
Core type definitions for the library.

Provides TypedQuery[T] - the key abstraction binding SQL statements to Pydantic models.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.sql.dml import ReturningDelete, ReturningInsert, ReturningUpdate

# TypeVar bound to BaseModel for result type safety
T = TypeVar("T", bound=BaseModel)

# Statement types that return rows (SELECT or mutations with RETURNING)
ReturningStatement = (
    Select[Any] | ReturningInsert[Any] | ReturningUpdate[Any] | ReturningDelete[Any]
)


class TypedQuery(Generic[T]):
    """
    Binds a SQLAlchemy statement to a Pydantic model type.

    This is the core abstraction that enables type-safe queries:
    - Static typing: IDE knows the return type
    - Runtime validation: Pydantic validates each row

    Works with:
    - SELECT statements
    - INSERT/UPDATE/DELETE with RETURNING clause

    Example:
        ```python
        class User(BaseModel):
            id: int
            name: str

        # SELECT query
        query = query(User, select(users))

        # INSERT with RETURNING
        query = query(User, insert(users).values(...).returning(users))
        ```
    """

    __slots__ = ("model", "statement")

    def __init__(self, model: type[T], statement: ReturningStatement):
        self.model = model
        self.statement = statement

    def __repr__(self) -> str:
        return f"TypedQuery[{self.model.__name__}]({self.statement})"


def query(model: type[T], statement: ReturningStatement) -> TypedQuery[T]:
    """
    Create a TypedQuery binding a Pydantic model to a SQL statement.

    Primary pattern: Use with query functions for type-safe parameters.

    Example:
        ```python
        # SELECT query
        def get_user(user_id: int) -> TypedQuery[User]:
            return query(User, select(users).where(users.c.id == user_id))

        # INSERT with RETURNING
        def create_user(name: str) -> TypedQuery[User]:
            return query(User, insert(users).values(name=name).returning(users))

        user = conn.one(get_user(42))        # IDE knows: user is User
        new_user = conn.one(create_user("Alice"))  # Also typed!
        ```

    Args:
        model: A Pydantic BaseModel subclass defining the row shape
        statement: A SQLAlchemy SELECT or mutation with RETURNING

    Returns:
        TypedQuery[T] that can be executed via Database connection methods
    """
    return TypedQuery(model, statement)
