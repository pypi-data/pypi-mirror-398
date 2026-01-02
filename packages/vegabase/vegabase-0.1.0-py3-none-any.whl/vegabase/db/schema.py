"""
Schema management with plan/apply pattern.

No migration files - just compare your code to the live database
and apply the diff directly.

Example:
    ```python
    from vegabase.db import Database, plan, apply
    from sqlalchemy import MetaData, Table, Column, Integer, String

    metadata = MetaData()
    users = Table('users', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(100)),
        Column('email', String(255)),  # ← Just add new columns
    )

    db = Database("postgresql://localhost/myapp")

    # Preview changes (dry run)
    changes = plan(db, metadata)
    for change in changes:
        print(change)
    # → CreateTable(users)
    # → AddColumn(users.email)

    # Apply changes to database
    apply(db, metadata)
    ```
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from sqlalchemy import Column, MetaData, inspect
from sqlalchemy.engine import Engine


class ChangeType(Enum):
    """Type of schema change."""

    CREATE_TABLE = "create_table"
    DROP_TABLE = "drop_table"
    ADD_COLUMN = "add_column"
    DROP_COLUMN = "drop_column"
    MODIFY_COLUMN = "modify_column"
    ADD_INDEX = "add_index"
    DROP_INDEX = "drop_index"
    ADD_CONSTRAINT = "add_constraint"
    DROP_CONSTRAINT = "drop_constraint"


@dataclass
class SchemaChange:
    """
    Represents a single schema change.

    Attributes:
        change_type: The type of change
        table_name: Name of the affected table
        detail: Additional detail (column name, index name, etc.)
        sql: The SQL statement to execute this change
    """

    change_type: ChangeType
    table_name: str
    detail: str | None = None
    sql: str | None = None

    def __str__(self) -> str:
        if self.detail:
            return f"{self.change_type.value}: {self.table_name}.{self.detail}"
        return f"{self.change_type.value}: {self.table_name}"

    def __repr__(self) -> str:
        return f"SchemaChange({self.change_type.name}, {self.table_name!r}, {self.detail!r})"


def _get_column_type_string(column: Any) -> str:
    """Get a comparable string representation of a column type."""
    try:
        return str(column.type)
    except Exception:
        return str(type(column.type).__name__)


def _compare_columns(target_col: Column[Any], existing_col: Any) -> list[str]:
    """Compare a target column definition to an existing column."""
    differences = []

    # Check nullability
    target_nullable = target_col.nullable if target_col.nullable is not None else True
    existing_nullable = (
        existing_col.get("nullable", True) if hasattr(existing_col, "get") else True
    )
    if target_nullable != existing_nullable:
        differences.append(f"nullable: {existing_nullable} → {target_nullable}")

    return differences


def plan(engine: Engine, metadata: MetaData) -> list[SchemaChange]:
    """
    Compare your MetaData to the live database and return planned changes.

    This is the "dry run" - it shows what would change without modifying anything.

    Args:
        engine: SQLAlchemy Engine (or Database.engine)
        metadata: Your MetaData with table definitions

    Returns:
        List of SchemaChange objects describing what would be modified

    Example:
        ```python
        db = Database("postgresql://...")
        changes = plan(db.engine, metadata)
        for change in changes:
            print(change)
        ```
    """
    changes: list[SchemaChange] = []
    inspector = inspect(engine)

    # Get existing tables in the database
    existing_tables = set(inspector.get_table_names())

    # Check each table in the target metadata
    for table_name, table in metadata.tables.items():
        if table_name not in existing_tables:
            # Table doesn't exist - needs to be created
            # Generate CREATE TABLE SQL
            sql = str(
                table.compile(engine).string
                if hasattr(table, "compile")
                else f"CREATE TABLE {table_name} (...)"
            )
            changes.append(
                SchemaChange(
                    change_type=ChangeType.CREATE_TABLE,
                    table_name=table_name,
                    sql=sql,
                )
            )
        else:
            # Table exists - check columns
            existing_columns = {
                col["name"]: col for col in inspector.get_columns(table_name)
            }

            for column in table.columns:
                col_name = column.name
                if col_name not in existing_columns:
                    # Column doesn't exist - needs to be added
                    col_type = _get_column_type_string(column)
                    nullable = "NULL" if column.nullable else "NOT NULL"
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} {nullable}"
                    changes.append(
                        SchemaChange(
                            change_type=ChangeType.ADD_COLUMN,
                            table_name=table_name,
                            detail=col_name,
                            sql=sql,
                        )
                    )
                else:
                    # Column exists - check for modifications
                    differences = _compare_columns(column, existing_columns[col_name])
                    if differences:
                        changes.append(
                            SchemaChange(
                                change_type=ChangeType.MODIFY_COLUMN,
                                table_name=table_name,
                                detail=f"{col_name} ({', '.join(differences)})",
                            )
                        )

            # Check for columns that exist in DB but not in metadata (optional drop)
            # By default, we don't auto-drop columns to prevent data loss
            # for col_name in existing_columns:
            #     if col_name not in {c.name for c in table.columns}:
            #         changes.append(SchemaChange(
            #             change_type=ChangeType.DROP_COLUMN,
            #             table_name=table_name,
            #             detail=col_name,
            #         ))

    return changes


def apply(
    engine: Engine,
    metadata: MetaData,
    *,
    create_tables: bool = True,
    add_columns: bool = True,
    modify_columns: bool = False,
    drop_columns: bool = False,
    drop_tables: bool = False,
) -> list[SchemaChange]:
    """
    Apply schema changes to the database.

    Compares your MetaData to the live database and executes the necessary
    ALTER TABLE statements to bring them in sync.

    Args:
        engine: SQLAlchemy Engine (or Database.engine)
        metadata: Your MetaData with table definitions
        create_tables: Whether to create new tables (default: True)
        add_columns: Whether to add new columns (default: True)
        modify_columns: Whether to modify existing columns (default: False)
        drop_columns: Whether to drop removed columns (default: False, DANGEROUS)
        drop_tables: Whether to drop removed tables (default: False, DANGEROUS)

    Returns:
        List of SchemaChange objects that were applied

    Example:
        ```python
        db = Database("postgresql://...")
        applied = apply(db.engine, metadata)
        print(f"Applied {len(applied)} changes")
        ```
    """
    changes = plan(engine, metadata)
    applied: list[SchemaChange] = []

    with engine.begin() as conn:
        for change in changes:
            should_apply = False

            if change.change_type == ChangeType.CREATE_TABLE and create_tables:
                should_apply = True
                # Use SQLAlchemy's built-in method for better compatibility
                table = metadata.tables[change.table_name]
                table.create(conn, checkfirst=True)
                applied.append(change)
            elif (
                change.change_type == ChangeType.ADD_COLUMN
                and add_columns
                or change.change_type == ChangeType.MODIFY_COLUMN
                and modify_columns
                or change.change_type == ChangeType.DROP_COLUMN
                and drop_columns
                or change.change_type == ChangeType.DROP_TABLE
                and drop_tables
            ):
                should_apply = True

            # Execute SQL for non-CREATE_TABLE changes
            if (
                should_apply
                and change.sql
                and change.change_type != ChangeType.CREATE_TABLE
            ):
                from sqlalchemy import text

                conn.execute(text(change.sql))
                applied.append(change)

    return applied


def create_all(engine: Engine, metadata: MetaData) -> None:
    """
    Create all tables that don't exist yet.

    This is a simpler alternative to apply() when you just want to ensure
    tables exist without comparing columns.

    Equivalent to SQLAlchemy's metadata.create_all(engine).

    Example:
        ```python
        db = Database("postgresql://...")
        create_all(db.engine, metadata)
        ```
    """
    metadata.create_all(engine)


def drop_all(engine: Engine, metadata: MetaData) -> None:
    """
    Drop all tables defined in the metadata.

    ⚠️ DANGEROUS: This will delete all data!

    Example:
        ```python
        db = Database("postgresql://...")
        drop_all(db.engine, metadata)  # Deletes everything!
        ```
    """
    metadata.drop_all(engine)
