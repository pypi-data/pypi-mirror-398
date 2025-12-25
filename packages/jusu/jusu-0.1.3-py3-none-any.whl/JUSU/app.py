"""JUSU ASGI integration helpers (FastAPI wrapper)

This module provides a small convenience wrapper around FastAPI so you can
use JUSU's Tag rendering directly as view handlers. FastAPI is an optional
dependency — importing this module will raise a helpful error if FastAPI is
not installed.

Example:
    from JUSU import Div, H1, P
    from JUSU.app import JusuApp

    app = JusuApp(title="JUSU Example")

    @app.get("/")
    async def index():
        return Div(H1("Hello from JUSU"), P("Rendered with JUSU + FastAPI"))

    # run with: uvicorn examples.fastapi_app:app.app --reload
"""
from __future__ import annotations

from typing import Any, Callable

from .core import Tag, Main, Div

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
except Exception:  # pragma: no cover - optional dependency
    FastAPI = None  # type: ignore


class JusuApp:
    """Small wrapper exposing a FastAPI app that understands JUSU Tags.

    Usage:
        app = JusuApp()

        @app.get("/")
        def index():
            return Div(H1("Hello"))

    The wrapper converts returned `Tag` instances to HTML responses.
    """

    def __init__(self, title: str = "JUSU Application", fastapi_app: Any | None = None, auth_backend: Any | None = None):
        if fastapi_app is None:
            if FastAPI is None:
                raise RuntimeError(
                    "FastAPI is not installed. Install with `pip install jusu[web]` or `pip install fastapi uvicorn`"
                )
            fastapi_app = FastAPI(title=title)
        self.app: Any = fastapi_app

        # Auth backend can be provided as a name (registered via auth_backends.register_backend)
        # or as an object implementing the AuthBackend protocol. Resolve names lazily.
        self._auth_backend = None
        if auth_backend is not None:
            self.set_auth_backend(auth_backend)

    def render_to_response(self, value: Any, status_code: int = 200):
        """Convert a returned value to an appropriate FastAPI response.

        - `Tag` -> HTMLResponse
        - `str` -> HTMLResponse
        - other -> returned as-is (allow FastAPI to handle JSON/Response types)
        """
        if isinstance(value, Tag):
            return HTMLResponse(content=value.render(pretty=False), status_code=status_code)
        if isinstance(value, str):
            return HTMLResponse(content=value, status_code=status_code)
        return value

    def route(self, path: str, **kwargs) -> Callable:
        """General route decorator that registers handlers on the underlying FastAPI app.

        The returned decorator wraps the handler to convert JUSU `Tag` values to HTML.
        """
        def decorator(fn: Callable) -> Callable:
            # Wrap async and sync functions transparently
            import inspect

            if inspect.iscoroutinefunction(fn):
                async def wrapper(*args: Any, **kw: Any):
                    result = await fn(*args, **kw)
                    return self.render_to_response(result)
            else:
                def wrapper(*args: Any, **kw: Any):
                    result = fn(*args, **kw)
                    return self.render_to_response(result)

            # Preserve the original function signature so FastAPI can correctly
            # introspect parameters (avoid generic *args/**kw being interpreted
            # as query parameters called 'args' and 'kw').
            try:
                wrapper.__signature__ = inspect.signature(fn)
            except Exception:
                # If setting the signature fails, that's okay; FastAPI will
                # still try to introspect the wrapper.
                pass

            # Register the wrapper. Using add_api_route keeps compatibility with all methods
            self.app.add_api_route(path, wrapper, **kwargs)
            return wrapper

        return decorator

    # Convenience shortcuts for common methods
    def get(self, path: str, **kwargs) -> Callable:
        return self.route(path, methods=["GET"], **kwargs)

    def post(self, path: str, **kwargs) -> Callable:
        return self.route(path, methods=["POST"], **kwargs)

    def mount_static(self, path: str = "/static", directory: str = "static", name: str = "static", cache_control: str | None = None) -> None:
        """Mount a StaticFiles instance to serve static assets.

        If `cache_control` is provided, a small middleware is added which sets
        the `Cache-Control` response header for responses whose path starts
        with the mounted `path`.
        """
        if FastAPI is None:
            raise RuntimeError("FastAPI is not installed; cannot mount static files.")
        # Mount the actual fileserver
        self.app.mount(path, StaticFiles(directory=directory), name=name)

        # Optionally add a middleware that sets cache headers for the mount
        if cache_control:
            from starlette.middleware.base import BaseHTTPMiddleware
            from starlette.requests import Request
            from starlette.responses import Response

            class _CacheControlMiddleware(BaseHTTPMiddleware):
                def __init__(self, app, prefix: str, header: str):
                    super().__init__(app)
                    self.prefix = prefix.rstrip("/")
                    self.header = header

                async def dispatch(self, request: Request, call_next):
                    resp: Response = await call_next(request)
                    if request.url.path.startswith(self.prefix):
                        resp.headers["Cache-Control"] = self.header
                    return resp

            self.app.add_middleware(_CacheControlMiddleware, prefix=path, header=cache_control)

    def add_middleware(self, middleware_class: type, **options) -> None:
        """Add middleware to the underlying FastAPI app.

        Example:
            app.add_middleware(SomeMiddleware, option=value)
        """
        if FastAPI is None:
            raise RuntimeError("FastAPI is not installed; cannot add middleware.")
        self.app.add_middleware(middleware_class, **options)

    def static_url(self, filename: str, path: str = "/static") -> str:
        """Return a mounted static URL for a given filename.

        This is a tiny helper for building links to static assets in templates.
        """
        return f"{path.rstrip('/')}/{filename.lstrip('/')}"

    def render_template(self, value: Any, layout: Tag | None = None, status_code: int = 200):
        """Render a `Tag` or string into an HTMLResponse using an optional layout.

        If `layout` is provided, the rendered content is inserted inside
        a `main` tag as a simple composition pattern.
        """
        if isinstance(value, Tag):
            body = value
        else:
            # allow raw strings or other responses
            return self.render_to_response(value, status_code=status_code)

        if layout is not None:
            # wrap body in a main element to avoid missing-body situations
            try:
                layout.add(Main(body))
            except Exception:
                # if layout doesn't support `.add`, fall back to a simple Div
                layout = Div(body)
            return self.render_to_response(layout, status_code=status_code)

        return self.render_to_response(body, status_code=status_code)

    # --- Auth backend helpers -------------------------------------------------
    def set_auth_backend(self, backend: Any) -> None:
        """Set the auth backend for the application.

        Accepts either a registered backend name (str) or an object that
        implements the `AuthBackend` protocol.
        """
        # Import locally to keep optional imports lazy
        from .auth_backends import get_backend

        if isinstance(backend, str):
            resolved = get_backend(backend)
            if resolved is None:
                raise RuntimeError(f"auth backend '{backend}' is not registered")
            self._auth_backend = resolved
        else:
            self._auth_backend = backend

    def get_current_user(self, request: Any, raise_on_missing: bool = False):
        """Return the current user as provided by the configured auth backend.

        If `raise_on_missing` is True and no user is found, raises
        `fastapi.HTTPException(status_code=401)`.
        """
        if self._auth_backend is None:
            if raise_on_missing:
                try:
                    from fastapi import HTTPException
                except Exception:
                    raise RuntimeError("auth backend is not configured")
                raise HTTPException(status_code=401, detail="Authentication required")
            return None

        try:
            user = self._auth_backend.get_user(request)
        except Exception:
            user = None

        if not user and raise_on_missing:
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Authentication required")
        return user

    def require_user(self):
        """Return a FastAPI dependency that resolves the current user or raises 401.

        Example:
            @app.get("/secret", dependencies=[Depends(app.require_user())])
            def secret_route(user=Depends(app.require_user())):
                return Div(P(f"hello {user['sub']}"))
        """
        from fastapi import Depends

        def _dep(request: Any = None):
            # Request will be provided by FastAPI; we accept None to make the
            # function call-friendly in tests where we may call it directly.
            user = self.get_current_user(request, raise_on_missing=True)
            return user

        return Depends(_dep)


__all__ = ["JusuApp"]
