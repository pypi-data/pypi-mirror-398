"""Authentication & session helpers for JUSU

This module provides:
- JWT helpers (create/verify tokens using PyJWT)
- SessionManager: small helper to add a cookie-based SessionMiddleware and
  a FastAPI dependency for accessing the session dict.

Use as optional features — importing raises a clear error if dependencies
are missing.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import hashlib
import secrets

try:
    import jwt
except Exception:  # pragma: no cover - optional dependency
    jwt = None  # type: ignore


class AuthError(Exception):
    """Raised for auth-related errors."""


def create_jwt(payload: Dict[str, Any], secret: str, algorithm: str = "HS256", expires_in: Optional[int] = None) -> str:
    """Create a JWT token from `payload`.

    - `expires_in` is seconds from now to set the `exp` claim.
    """
    if jwt is None:
        raise AuthError("PyJWT is not installed. Install with `pip install PyJWT`")

    data = payload.copy()
    if expires_in is not None:
        # Use timezone-aware UTC to avoid deprecation warnings and future issues
        data["exp"] = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)
    token = jwt.encode(data, secret, algorithm=algorithm)
    # PyJWT >= 2 returns str, older versions may return bytes
    if isinstance(token, bytes):
        token = token.decode("ascii")
    return token


def verify_jwt(token: str, secret: str, algorithms: Optional[list] = None) -> Dict[str, Any]:
    """Verify and decode a JWT token, returning the payload or raising AuthError."""
    if jwt is None:
        raise AuthError("PyJWT is not installed. Install with `pip install PyJWT`")
    try:
        payload = jwt.decode(token, secret, algorithms=algorithms or ["HS256"])
        return payload
    except Exception as exc:
        raise AuthError(f"Invalid token: {exc}") from exc


# Session helpers (wrappers around Starlette's SessionMiddleware)
try:
    from starlette.middleware.sessions import SessionMiddleware
    from starlette.requests import Request
except Exception:  # pragma: no cover
    SessionMiddleware = None  # type: ignore
    Request = None  # type: ignore

# FastAPI / HTTP helpers (optional dependency)
try:
    from fastapi import HTTPException, Request
    from starlette.status import HTTP_401_UNAUTHORIZED
except Exception:  # pragma: no cover
    HTTPException = None  # type: ignore
    Request = None  # type: ignore
    HTTP_401_UNAUTHORIZED = None  # type: ignore


class SessionManager:
    """Simple helper to install SessionMiddleware and provide a FastAPI
    dependency to access the session dict.

    Example:
        mgr = SessionManager(secret_key="...")
        mgr.init_app(app)

        @app.get("/set")
        def set(req: Request):
            req.session["k"] = "v"
            return {"ok": True}

    The dependency `mgr.get_session` can be used in FastAPI endpoints:
        def handler(session=Depends(mgr.get_session)):
            session["k"] = 1
    """

    def __init__(self, secret_key: Optional[str] = None, cookie_name: str = "jusu_session", max_age: Optional[int] = None):
        if SessionMiddleware is None:  # pragma: no cover - optional dep
            raise RuntimeError("starlette is required for SessionManager (install fastapi)")
        self.secret_key = secret_key
        self.cookie_name = cookie_name
        self.max_age = max_age

    def init_app(self, app: Any, secret_key: Optional[str] = None) -> None:
        """Add the SessionMiddleware to a FastAPI/Starlette `app`."""
        if secret_key is None:
            secret_key = self.secret_key
        if not secret_key:
            raise RuntimeError("A `secret_key` must be provided to init sessions.")
        app.add_middleware(SessionMiddleware, secret_key=secret_key, session_cookie=self.cookie_name, max_age=self.max_age)

    # FastAPI dependency
    def get_session(self, request: Request) -> Dict[str, Any]:
        """Return the session dict from the request (dependency-friendly)."""
        return request.session


# Password hashing utilities: use passlib[bcrypt] if available, otherwise fall back to SHA256 salt

try:
    from passlib.context import CryptContext
except Exception:  # pragma: no cover - optional dep
    CryptContext = None  # type: ignore

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto") if CryptContext is not None else None


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Return (salt, hashed).

    - When `salt` is provided (non-empty), we always use the legacy SHA256 path
      to maintain compatibility with existing stored hashes.
    - When passlib is available and `salt` is None/empty, use bcrypt and return
      an empty `salt` with the bcrypt hash. If bcrypt fails for any reason we
      gracefully fall back to legacy SHA256+salt.
    """
    # If a salt is explicitly provided, use legacy SHA256 behavior for
    # compatibility with existing stored values.
    if salt is not None and salt != "":
        hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return salt, hashed

    if _pwd_ctx is not None:
        try:
            hashed = _pwd_ctx.hash(password)
            return "", hashed
        except Exception:
            # If passlib/bcrypt backend fails (environment issue), fall back
            # to the legacy SHA256+salt approach to remain robust.
            pass

    # Fallback (legacy)
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, hashed


def verify_password(password: str, salt: str, hashed: str) -> bool:
    """Verify a password against the stored values.

    - If `salt` is empty and passlib is available, use bcrypt verification.
    - Otherwise use the SHA256(salt + password) check for legacy hashes.
    """
    if _pwd_ctx is not None and (salt is None or salt == ""):
        try:
            return _pwd_ctx.verify(password, hashed)
        except Exception:
            return False
    # Legacy fallback
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest() == hashed

# FastAPI / convenience dependencies
# (imports moved to top-level optional try/except for lint/safety)


def get_current_user_from_jwt(token: str, secret: str):
    try:
        payload = verify_jwt(token, secret)
        return payload
    except AuthError as exc:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(exc))


def get_current_user(request: Request, jwt_secret: Optional[str] = None) -> Optional[dict]:
    """Attempt to retrieve current user from session or Authorization header (Bearer JWT).

    If a session exists and contains 'user', it is returned. Otherwise, an
    Authorization header with Bearer token is checked and decoded using
    `jwt_secret` if provided.
    """
    # Session-first (use request.scope to avoid SessionMiddleware assertion when absent)
    sess = request.scope.get("session") if hasattr(request, "scope") else None
    if isinstance(sess, dict) and sess.get("user"):
        return sess["user"]

    # Authorization header
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer ") and jwt_secret:
        token = auth.split(None, 1)[1]
        return get_current_user_from_jwt(token, jwt_secret)

    return None


def login_required(jwt_secret: Optional[str] = None):
    """Dependency factory that raises 401 if no current user found (session or JWT).

    Returns a callable suitable to be used in `Depends(...)`.
    """
    def _dep(request: Request):
        user = get_current_user(request, jwt_secret=jwt_secret)
        if not user:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Authentication required")
        return user

    return _dep


__all__ = [
    "create_jwt",
    "verify_jwt",
    "SessionManager",
    "AuthError",
    "hash_password",
    "verify_password",
    "get_current_user",
    "login_required",
]

# Expose session helper conveniences
__all__.extend(["login_user", "logout_user"])
