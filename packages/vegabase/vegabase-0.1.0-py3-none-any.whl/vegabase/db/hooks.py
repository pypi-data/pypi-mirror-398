"""
Hook system for the library.

Allows hooking into the query lifecycle for:
- Logging and timing
- Row transformation (e.g., snake_case → camelCase)
- Query modification (e.g., soft delete filters)
- Error handling
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .types import ReturningStatement


@dataclass
class QueryContext:
    """
    Context passed to hooks containing query information.

    Hooks can read/modify this context to affect query execution.
    """

    # The SQLAlchemy statement being executed (SELECT or mutation with RETURNING)
    statement: ReturningStatement

    # The Pydantic model type for validation
    model_name: str

    # Optional params for the query
    params: dict[str, Any] | None = None

    # Whether validation is being skipped
    skip_validation: bool = False

    # Custom data that hooks can attach
    extra: dict[str, Any] = field(default_factory=dict)


class Hook:
    """
    Base class for hooks.

    Implement any of the hook methods to intercept query execution.
    All methods have default no-op implementations, so you only need
    to override the ones you care about.

    Example:
        ```python
        class LoggingHook(Hook):
            def before_execute(self, ctx: QueryContext) -> None:
                ctx.extra['start'] = time.time()
                print(f"[SQL] Executing query for {ctx.model_name}")

            def after_execute(self, ctx: QueryContext, rows: list[dict]) -> list[dict]:
                elapsed = time.time() - ctx.extra['start']
                print(f"[SQL] {len(rows)} rows in {elapsed*1000:.2f}ms")
                return rows
        ```
    """

    def before_execute(self, ctx: QueryContext) -> None:
        """
        Called before the query is executed.

        Use this for:
        - Logging the query
        - Starting timers
        - Modifying the query (via ctx.statement)
        """
        pass

    def after_execute(
        self, ctx: QueryContext, rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Called after execution, before Pydantic validation.

        Args:
            ctx: The query context
            rows: Raw row data as list of dicts

        Returns:
            Transformed rows (or original if unchanged)

        Use this for:
        - Logging timing/row count
        - Transforming field names (snake_case → camelCase)
        - Filtering rows
        """
        return rows

    def on_error(self, ctx: QueryContext, error: Exception) -> Exception:
        """
        Called when an error occurs during execution or validation.

        Args:
            ctx: The query context
            error: The exception that was raised

        Returns:
            The exception to raise (can return a different one)

        Use this for:
        - Error logging/alerting
        - Translating error types
        """
        return error


class HookChain:
    """
    Manages a chain of hooks and runs them in order.
    """

    def __init__(self, hooks: list[Hook] | None = None):
        self._hooks = hooks or []

    def add(self, hook: Hook) -> None:
        """Add an hook to the chain."""
        self._hooks.append(hook)

    def run_before(self, ctx: QueryContext) -> None:
        """Run all before_execute hooks."""
        for hook in self._hooks:
            hook.before_execute(ctx)

    def run_after(
        self, ctx: QueryContext, rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Run all after_execute hooks, passing rows through each."""
        for hook in self._hooks:
            rows = hook.after_execute(ctx, rows)
        return rows

    def run_on_error(self, ctx: QueryContext, error: Exception) -> Exception:
        """Run all on_error hooks."""
        for hook in self._hooks:
            error = hook.on_error(ctx, error)
        return error


# =============================================================================
# Built-in Hooks
# =============================================================================


class LoggingHook(Hook):
    """
    Logs query execution with timing.

    Example output:
        [SQL] User: 3 rows in 1.23ms

    Usage:
        db = Database("...", hooks=[LoggingHook()])
    """

    def __init__(
        self, prefix: str = "[SQL]", log_fn: Callable[[str], None] | None = None
    ):
        self.prefix = prefix
        self.log_fn = log_fn or print

    def before_execute(self, ctx: QueryContext) -> None:
        import time

        ctx.extra["_log_start"] = time.perf_counter()

    def after_execute(
        self, ctx: QueryContext, rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        import time

        start = ctx.extra.get("_log_start", 0)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.log_fn(
            f"{self.prefix} {ctx.model_name}: {len(rows)} rows in {elapsed_ms:.2f}ms"
        )
        return rows


def _to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class CamelCaseHook(Hook):
    """
    Transforms row field names from snake_case to camelCase.

    Useful when your DB uses snake_case but your API expects camelCase.

    Example:
        {"user_name": "Alice"} → {"userName": "Alice"}

    Usage:
        db = Database("...", hooks=[CamelCaseHook()])
    """

    def after_execute(
        self, ctx: QueryContext, rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        return [{_to_camel_case(k): v for k, v in row.items()} for row in rows]


class SlowQueryHook(Hook):
    """
    Logs a warning for queries that exceed a threshold.

    Usage:
        db = Database("...", hooks=[SlowQueryHook(threshold_ms=100)])
    """

    def __init__(
        self, threshold_ms: float = 100, log_fn: Callable[[str], None] | None = None
    ):
        self.threshold_ms = threshold_ms
        self.log_fn = log_fn or print

    def before_execute(self, ctx: QueryContext) -> None:
        import time

        ctx.extra["_slow_start"] = time.perf_counter()

    def after_execute(
        self, ctx: QueryContext, rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        import time

        start = ctx.extra.get("_slow_start", 0)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > self.threshold_ms:
            self.log_fn(
                f"[SLOW QUERY] {ctx.model_name}: {elapsed_ms:.2f}ms (threshold: {self.threshold_ms}ms)"
            )
        return rows
