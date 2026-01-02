import json
import os
import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

import httpx
from fastapi import Request, Response

# Render mode type
RenderMode = Literal["ssr", "client", "cached", "static"]


class InertiaJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Pydantic models and common Python types."""

    def default(self, obj: Any) -> Any:  # type: ignore[override]
        # Handle Pydantic models (v2)
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        # Handle Pydantic models (v1 fallback)
        if hasattr(obj, "dict") and hasattr(obj, "__fields__"):
            return obj.dict()
        # Handle dataclasses
        if hasattr(obj, "__dataclass_fields__"):
            from dataclasses import asdict

            return asdict(obj)
        # Handle datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Handle date
        if isinstance(obj, date):
            return obj.isoformat()
        # Handle UUID
        if isinstance(obj, UUID):
            return str(obj)
        # Handle Decimal
        if isinstance(obj, Decimal):
            return float(obj)
        # Handle bytes
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        # Handle sets
        if isinstance(obj, set):
            return list(obj)

        # Provide helpful error messages for common problematic types
        type_name = type(obj).__name__
        module = type(obj).__module__

        hints = {
            "function": "Functions cannot be serialized. Remove it from props.",
            "method": "Methods cannot be serialized. Remove it from props.",
            "generator": "Convert generator to list() before passing to render().",
            "coroutine": "Await the coroutine before passing to render().",
            "Connection": "Pass data, not database connections.",
            "Session": "Pass data, not database sessions.",
            "Engine": "Pass data, not database engines.",
        }

        hint = hints.get(type_name, "")
        if not hint and "sqlalchemy" in module.lower():
            hint = "SQLAlchemy objects must be converted to Pydantic models or dicts."

        error_msg = f"Object of type '{type_name}' is not JSON serializable."
        if hint:
            error_msg += f" Hint: {hint}"

        raise TypeError(error_msg)


def _serialize(data: Any) -> str:
    """Serialize data to JSON using custom encoder."""
    return json.dumps(data, cls=InertiaJSONEncoder)


class LRUCache:
    """Simple LRU cache with max size limit."""

    def __init__(self, maxsize: int = 100):
        self.maxsize = maxsize
        self._cache: dict[str, tuple[list, str, float]] = {}
        self._order: list[str] = []  # Track access order

    def get(self, key: str) -> tuple[list, str, float] | None:
        if key in self._cache:
            # Move to end (most recently used)
            self._order.remove(key)
            self._order.append(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: tuple[list, str, float]) -> None:
        if key in self._cache:
            self._order.remove(key)
        elif len(self._cache) >= self.maxsize:
            # Evict least recently used
            oldest = self._order.pop(0)
            del self._cache[oldest]
        self._cache[key] = value
        self._order.append(key)

    def pop(self, key: str) -> tuple[list, str, float] | None:
        if key in self._cache:
            self._order.remove(key)
            return self._cache.pop(key)
        return None

    def clear(self) -> None:
        self._cache.clear()
        self._order.clear()

    def __contains__(self, key: str) -> bool:
        return key in self._cache


class Inertia:
    FLASH_SESSION_KEY = "_inertia_flash"

    def __init__(self, app, ssr_url: str | None = None, cache_maxsize: int = 100):
        self.app = app
        self.is_dev = os.getenv("APP_ENV") == "development"

        # Configure SSR URL
        if ssr_url:
            self.ssr_url = ssr_url
        elif self.is_dev:
            self.ssr_url = "http://localhost:3001/render"
        else:
            self.ssr_url = "http://localhost:13714/render"

        # Configure asset paths based on environment
        self.assets_url = "http://localhost:3001" if self.is_dev else "/static/dist"

        # ISR cache with LRU eviction
        self._isr_cache = LRUCache(maxsize=cache_maxsize)

    def flash(self, request: Request, message: str, type: str = "success") -> None:
        """
        Set a flash message to be displayed on the next page render.

        Args:
            request: The FastAPI request object (must have session middleware)
            message: The flash message text
            type: The message type (success, error, warning, info)
        """
        if not hasattr(request, "session"):
            raise RuntimeError(
                "Flash messages require session middleware. "
                "Add SessionMiddleware to your app:\n\n"
                "  from starlette.middleware.sessions import SessionMiddleware\n"
                "  app.add_middleware(SessionMiddleware, secret_key='your-secret')"
            )
        request.session[self.FLASH_SESSION_KEY] = {"type": type, "message": message}

    def _get_and_clear_flash(self, request: Request) -> dict | None:
        """Get flash message from session and clear it."""
        if not hasattr(request, "session"):
            return None
        return request.session.pop(self.FLASH_SESSION_KEY, None)

    def invalidate_cache(self, cache_key: str | None = None) -> None:
        """
        Invalidate ISR cache.

        Args:
            cache_key: Specific key to invalidate, or None to clear all cache
        """
        if cache_key:
            self._isr_cache.pop(cache_key)
        else:
            self._isr_cache.clear()

    async def render(
        self,
        component: str,
        props: dict,
        request: Request,
        mode: RenderMode = "ssr",
        revalidate: int | None = None,
        cache_key: str | None = None,
    ):
        """
        Render an Inertia page.

        Args:
            component: The React component name (e.g., "Dashboard", "Posts/Index")
            props: Props to pass to the component
            request: FastAPI request object
            mode: Rendering mode - "ssr" (default), "client", "cached", or "static"
            revalidate: For cached mode, cache TTL in seconds (0 = forever)
            cache_key: Custom cache key for cached mode (default: component name)
        """
        # Automatically inject flash message if present
        flash = self._get_and_clear_flash(request)
        if flash:
            props = {**props, "flash": flash}

        # Determine if client should hydrate
        should_hydrate = mode != "static"

        page_data = {
            "component": component,
            "props": props,
            "url": str(request.url.path),
            "version": "1.0",  # TODO: Implement asset hashing
            "mode": mode,  # Include mode for client to know how to render
        }

        # CASE A: Client is navigating (AJAX)
        if "X-Inertia" in request.headers:
            return Response(
                content=_serialize(page_data),
                media_type="application/json",
                headers={"X-Inertia": "true", "Vary": "X-Inertia"},
            )

        # CASE B: First Load (Browser Refresh)
        head: list = []
        body = ""

        if mode == "client":
            # Client-side only rendering - no SSR call
            body = f"<div id='app' data-page='{_serialize(page_data)}'></div>"

        elif mode == "cached":
            # Incremental Static Regeneration - check cache first
            key = cache_key or component
            now = time.time()

            cached = self._isr_cache.get(key)
            if cached:
                cached_head, cached_body, cached_time = cached
                is_stale = revalidate is not None and (now - cached_time) > revalidate

                if not is_stale or revalidate == 0:
                    # Cache is fresh or revalidate=0 (cache forever)
                    head, body = cached_head, cached_body
                else:
                    # Cache is stale - serve stale and regenerate
                    head, body = cached_head, cached_body
                    # In a real implementation, this would be a background task
                    # For now, we'll just update synchronously
                    new_head, new_body = await self._ssr_render(page_data)
                    self._isr_cache.set(key, (new_head, new_body, now))
            else:
                # Cache miss - render and cache
                head, body = await self._ssr_render(page_data)
                self._isr_cache.set(key, (head, body, now))

        elif mode == "ssr" or mode == "static":
            # Standard SSR - call SSR server every time
            head, body = await self._ssr_render(page_data)

        # Construct HTML
        head_html = "\n".join(head) if isinstance(head, list) else str(head)

        # Determine asset URLs
        script_src = f"{self.assets_url}/client.js"
        css_src = f"{self.assets_url}/client.css"

        # For html mode, don't include the script tag
        script_tag = (
            f'<script type="module" src="{script_src}"></script>'
            if should_hydrate
            else ""
        )

        html = f"""
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0" />
            {head_html}
            <title>PyReact App</title>
            <link rel="stylesheet" href="{css_src}" />
          </head>
          <body>
            {body}
            {script_tag}
          </body>
        </html>
        """

        # Build response headers
        # Vary by X-Inertia so CDNs cache JSON/HTML responses separately
        headers: dict[str, str] = {"Vary": "X-Inertia"}

        # Add Cache-Control headers for ISR mode (CDN + browser caching)
        if mode == "cached" and revalidate is not None and revalidate > 0:
            # stale-while-revalidate allows serving stale while refreshing
            swr = revalidate * 10  # Allow stale for 10x the revalidate time
            headers["Cache-Control"] = (
                f"public, max-age={revalidate}, s-maxage={revalidate}, "
                f"stale-while-revalidate={swr}"
            )
        elif mode == "static":
            # Static HTML can be cached longer
            headers["Cache-Control"] = "public, max-age=3600"
        else:
            # SSR/CSR - don't cache at CDN level
            headers["Cache-Control"] = "private, no-cache"

        return Response(content=html, media_type="text/html", headers=headers)

    async def _ssr_render(self, page_data: dict) -> tuple[list, str]:
        """Call SSR server and return (head, body)."""
        head: list = []
        body = ""

        try:
            async with httpx.AsyncClient() as client:
                page_json = json.loads(_serialize(page_data))
                resp = await client.post(self.ssr_url, json=page_json)
                try:
                    ssr_response = resp.json()
                    head = ssr_response.get("head", [])
                    body = ssr_response.get("body", "")
                except json.JSONDecodeError:
                    print(f"SSR JSON Error: {resp.text}")
        except Exception as e:
            print(f"SSR Connection Error: {e}")
            body = f"<div id='app' data-page='{_serialize(page_data)}'></div>"

        return head, body
