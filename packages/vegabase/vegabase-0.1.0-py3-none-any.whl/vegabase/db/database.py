"""
Synchronous database connection and query execution.

Provides Database and TypedConnection with query methods.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, TypeVar

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import Connection, Engine, create_engine

from .errors import NotFoundError, TooManyRowsError, ValidationError
from .hooks import Hook, HookChain, QueryContext
from .types import TypedQuery

# Define T locally for proper type inference by type checkers
T = TypeVar("T", bound=BaseModel)


class TypedConnection:
    """
    Wrapper around SQLAlchemy Connection providing type-safe query methods.

    Provides these methods:
    - `one()`: Exactly one row (raises if 0 or >1)
    - `maybe_one()`: Zero or one row (raises if >1)
    - `many()`: One or more rows (raises if 0)
    - `all()`: Zero or more rows (never raises for count)

    All methods support:
    - `params`: Optional dict for bindparam queries
    - `skip_validation`: Bypass Pydantic validation for performance
    """

    __slots__ = ("_conn", "_hooks")

    def __init__(self, conn: Connection, hooks: HookChain | None = None):
        self._conn = conn
        self._hooks = hooks or HookChain()

    def one(
        self,
        query: TypedQuery[T],
        params: dict[str, Any] | None = None,
        skip_validation: bool = False,
    ) -> T:
        """
        Execute query and return exactly one row.

        Raises:
            NotFoundError: If zero rows returned
            TooManyRowsError: If more than one row returned
            ValidationError: If row fails Pydantic validation
        """
        rows = self._execute(query, params, skip_validation)
        if len(rows) == 0:
            raise NotFoundError("Expected exactly 1 row, got 0")
        if len(rows) > 1:
            raise TooManyRowsError(f"Expected exactly 1 row, got {len(rows)}")
        return rows[0]

    def maybe_one(
        self,
        query: TypedQuery[T],
        params: dict[str, Any] | None = None,
        skip_validation: bool = False,
    ) -> T | None:
        """
        Execute query and return zero or one row.

        Raises:
            TooManyRowsError: If more than one row returned
            ValidationError: If row fails Pydantic validation
        """
        rows = self._execute(query, params, skip_validation)
        if len(rows) > 1:
            raise TooManyRowsError(f"Expected 0 or 1 row, got {len(rows)}")
        return rows[0] if rows else None

    def many(
        self,
        query: TypedQuery[T],
        params: dict[str, Any] | None = None,
        skip_validation: bool = False,
    ) -> list[T]:
        """
        Execute query and return one or more rows.

        Raises:
            NotFoundError: If zero rows returned
            ValidationError: If any row fails Pydantic validation
        """
        rows = self._execute(query, params, skip_validation)
        if len(rows) == 0:
            raise NotFoundError("Expected at least 1 row, got 0")
        return rows

    def all(
        self,
        query: TypedQuery[T],
        params: dict[str, Any] | None = None,
        skip_validation: bool = False,
    ) -> list[T]:
        """
        Execute query and return zero or more rows.

        Never raises for row count. Use this when empty results are valid.

        Raises:
            ValidationError: If any row fails Pydantic validation
        """
        return self._execute(query, params, skip_validation)

    def execute(
        self,
        statement: Any,
        params: dict[str, Any] | None = None,
    ) -> int:
        """
        Execute a mutation statement (INSERT/UPDATE/DELETE) and return row count.

        Use this for statements that don't return rows, or when you don't need
        the returned data typed.

        Returns:
            Number of rows affected

        Example:
            ```python
            count = conn.execute(delete(users).where(users.c.id == 42))
            count = conn.execute(update(users).values(active=False))
            ```
        """
        result = self._conn.execute(statement, params or {})
        return result.rowcount

    def scalar(
        self,
        statement: Any,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """
        Execute a query and return a single scalar value.

        Use for COUNT, SUM, MAX, or any query returning one value.

        Returns:
            The scalar value (int, str, etc.)

        Raises:
            NotFoundError: If no rows returned

        Example:
            ```python
            count = conn.scalar(select(func.count()).select_from(users))
            max_id = conn.scalar(select(func.max(users.c.id)))
            ```
        """
        result = self._conn.execute(statement, params or {})
        row = result.fetchone()
        if row is None:
            raise NotFoundError("Expected a scalar value, got no rows")
        return row[0]

    def returning_one(
        self,
        query: TypedQuery[T],
        params: dict[str, Any] | None = None,
        skip_validation: bool = False,
    ) -> T:
        """
        Execute INSERT/UPDATE/DELETE with RETURNING clause and return one typed row.

        Use for mutations that return the affected row(s) via RETURNING.
        Requires database support (PostgreSQL, SQLite 3.35+).

        Raises:
            NotFoundError: If no rows returned
            TooManyRowsError: If more than one row returned
            ValidationError: If row fails Pydantic validation

        Example:
            ```python
            new_user = conn.returning_one(
                query(User, insert(users).values(name="Alice").returning(users))
            )
            ```
        """
        return self.one(query, params, skip_validation)

    def returning_many(
        self,
        query: TypedQuery[T],
        params: dict[str, Any] | None = None,
        skip_validation: bool = False,
    ) -> list[T]:
        """
        Execute INSERT/UPDATE/DELETE with RETURNING clause and return typed rows.

        Use for bulk mutations that return affected rows via RETURNING.
        Requires database support (PostgreSQL, SQLite 3.35+).

        Example:
            ```python
            deleted_users = conn.returning_many(
                query(User, delete(users).where(users.c.active == False).returning(users))
            )
            ```
        """
        return self.all(query, params, skip_validation)

    def execute_many(
        self,
        statement: Any,
        params_list: list[dict[str, Any]],
    ) -> int:
        """
        Execute a statement multiple times with different parameters (bulk insert).

        Efficient for inserting many rows at once.

        Returns:
            Total number of rows affected

        Example:
            ```python
            conn.execute_many(
                insert(users),
                [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]
            )
            ```
        """
        result = self._conn.execute(statement, params_list)
        return result.rowcount

    def _execute(
        self, query: TypedQuery[T], params: dict[str, Any] | None, skip_validation: bool
    ) -> list[T]:
        """Internal: execute query with hooks and validate results."""
        # Create context for hooks
        ctx = QueryContext(
            statement=query.statement,
            model_name=query.model.__name__,
            params=params,
            skip_validation=skip_validation,
        )

        try:
            # Run before hooks
            self._hooks.run_before(ctx)

            # Execute query
            result = self._conn.execute(ctx.statement, ctx.params)

            # Convert to list of dicts
            rows: list[dict[str, Any]] = [dict(row._mapping) for row in result]

            # Run after hooks (can transform rows)
            rows = self._hooks.run_after(ctx, rows)

            # Validate with Pydantic
            validated: list[T] = []
            for row_dict in rows:
                if skip_validation:
                    # Performance bypass: construct without validation
                    validated.append(query.model.model_construct(**row_dict))
                else:
                    # Full runtime validation
                    try:
                        validated.append(query.model.model_validate(row_dict))
                    except PydanticValidationError as e:
                        raise ValidationError(
                            f"Row validation failed for {query.model.__name__}: {e}",
                            e.errors(),
                        ) from e

            return validated

        except Exception as e:
            # Run error hooks
            error = self._hooks.run_on_error(ctx, e)
            raise error from None


class Database:
    """
    Synchronous database connection manager.

    Wraps a SQLAlchemy Engine and provides context managers for
    connections and transactions with type-safe query execution.

    Example:
        ```python
        from vegabase.db import Database, LoggingHook

        db = Database(
            "sqlite:///app.db",
            hooks=[LoggingHook()]
        )

        with db.connection() as conn:
            user = conn.one(get_user(42))
            # Console: [SQL] User: 1 rows in 0.52ms

        with db.transaction() as conn:
            conn.one(create_user("Alice"))
            # Auto-commits on success, rollback on exception
        ```
    """

    def __init__(
        self,
        url: str,
        hooks: list[Hook] | None = None,
        **engine_kwargs: Any,
    ):
        """
        Create a Database instance.

        Args:
            url: SQLAlchemy database URL (e.g., "sqlite:///app.db", "postgresql://...")
            hooks: Optional list of Hook instances
            **engine_kwargs: Additional arguments passed to create_engine
        """
        self.engine: Engine = create_engine(url, **engine_kwargs)
        self._hooks = HookChain(hooks)

    def add_hook(self, hook: Hook) -> None:
        """Add an hook to the chain."""
        self._hooks.add(hook)

    @contextmanager
    def connection(self) -> Generator[TypedConnection, None, None]:
        """
        Get a connection context manager.

        Connection is automatically closed when context exits.
        Does NOT auto-commit - use transaction() for that.
        """
        with self.engine.connect() as conn:
            yield TypedConnection(conn, self._hooks)

    @contextmanager
    def transaction(self) -> Generator[TypedConnection, None, None]:
        """
        Get a transaction context manager.

        - Auto-commits when context exits normally
        - Auto-rolls back when an exception is raised
        """
        with self.engine.begin() as conn:
            yield TypedConnection(conn, self._hooks)

    def dispose(self) -> None:
        """Dispose of the connection pool."""
        self.engine.dispose()
