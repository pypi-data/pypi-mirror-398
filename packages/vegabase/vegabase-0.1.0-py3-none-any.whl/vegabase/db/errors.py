"""
Semantic error types for the library.

These provide meaningful exceptions instead of generic database errors.
"""

from typing import Any


class DatabaseError(Exception):
    """Base exception for all errors."""

    pass


class NotFoundError(DatabaseError):
    """
    Expected at least one row, but got zero.

    Raised by `one()` and `many()` when no rows are returned.
    """

    def __init__(self, message: str = "Expected at least one row, got 0"):
        super().__init__(message)


class TooManyRowsError(DatabaseError):
    """
    Expected at most one row, but got multiple.

    Raised by `one()` and `maybe_one()` when more than one row is returned.
    """

    def __init__(self, message: str = "Expected at most 1 row, got multiple"):
        super().__init__(message)


class ValidationError(DatabaseError):
    """
    Runtime validation of row data against Pydantic model failed.

    Contains the original Pydantic validation errors for inspection.
    """

    def __init__(self, message: str, pydantic_errors: Any = None):
        super().__init__(message)
        self.pydantic_errors = pydantic_errors or []
