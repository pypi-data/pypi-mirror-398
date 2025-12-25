"""Pluggable auth backend registry and built-in backends for JUSU.

Backends should implement a small surface (class or callable) with methods:
- `get_user(request) -> Optional[dict]` - inspect request and return a user dict or None
- Optionally `login(request, response, user)` and `logout(request, response)` for session-style backends

Register backends via `register_backend(name, backend)` and select them by name.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Protocol


class AuthBackend(Protocol):
    def get_user(self, request: Any) -> Optional[dict]:
        ...

    def login(self, request: Any, response: Any, user: dict) -> None:  # pragma: no cover - optional
        ...

    def logout(self, request: Any, response: Any) -> None:  # pragma: no cover - optional
        ...


_BACKENDS: Dict[str, AuthBackend] = {}


def register_backend(name: str, backend: AuthBackend) -> None:
    """Register an auth backend by name. Overwrites existing name."""
    _BACKENDS[name] = backend


def get_backend(name: str) -> Optional[AuthBackend]:
    return _BACKENDS.get(name)


# Built-in Session backend
class SessionBackend:
    def __init__(self, cookie_name: str = "jusu_session"):
        self.cookie_name = cookie_name

    def get_user(self, request: Any) -> Optional[dict]:
        # Use request.scope session if available to avoid raising AssertionError
        try:
            sess = request.scope.get("session") if hasattr(request, "scope") else None
            if isinstance(sess, dict) and sess.get("user"):
                return sess.get("user")
        except Exception:
            pass
        # fallback: try request.session (may raise AssertionError when SessionMiddleware absent)
        try:
            s = getattr(request, "session", None)
            if s and s.get("user"):
                return s.get("user")
        except Exception:
            pass
        return None

    def login(self, request: Any, response: Any, user: dict) -> None:
        try:
            request.session["user"] = user
        except Exception:
            request.scope.setdefault("session", {})
            request.scope["session"]["user"] = user
        if response is not None:
            # For simple convenience also set a cookie (not secure by default)
            try:
                response.set_cookie(self.cookie_name, str(user.get("sub") or ""), httponly=True)
            except Exception:
                pass

    def logout(self, request: Any, response: Any) -> None:
        try:
            request.session.pop("user", None)
        except Exception:
            if "session" in request.scope:
                request.scope["session"].pop("user", None)
        if response is not None:
            try:
                response.delete_cookie(self.cookie_name)
            except Exception:
                pass


# Built-in Firebase backend (uses firebase.verify_id_token under the hood)
class FirebaseBackend:
    def __init__(self, jwt_header: str = "Authorization"):
        try:
            from .firebase import verify_id_token
        except Exception as exc:  # pragma: no cover - optional dep
            raise RuntimeError("firebase-admin not installed or firebase wrapper failing") from exc
        self._verify = verify_id_token
        self.jwt_header = jwt_header

    def get_user(self, request: Any) -> Optional[dict]:
        # Expect Authorization: Bearer <idToken>
        h = request.headers.get(self.jwt_header, "")
        if not h.lower().startswith("bearer "):
            return None
        token = h.split(None, 1)[1]
        try:
            payload = self._verify(token)
            return payload
        except Exception:
            return None


# Register defaults
register_backend("session", SessionBackend())
try:
    register_backend("firebase", FirebaseBackend())
except Exception:
    # If firebase admin not installed or not configured, skip registering
    pass

__all__ = ["register_backend", "get_backend", "AuthBackend", "SessionBackend", "FirebaseBackend"]