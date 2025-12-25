"""Convenience session helpers for JUSU (login/logout utilities)

These helpers are small, opinionated helpers intended for convenience in
examples and prototyping. They assume SessionMiddleware is installed (cookie
sessions). For production, favor a robust auth library and secure storage.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Request, Response


def login_user(request: Request, user: dict) -> None:
    """Attach `user` to the current session.

    - If SessionMiddleware is not present this will set a session dict in
      `request.scope['session']` for compatibility with tests.
    """
    try:
        request.session["user"] = user
    except AssertionError:
        # SessionMiddleware not installed; fall back to storing in scope for tests or simple setups
        request.scope.setdefault("session", {})
        request.scope["session"]["user"] = user
    except Exception:
        # Be resilient for other unexpected request implementations
        request.scope.setdefault("session", {})
        request.scope["session"]["user"] = user


def logout_user(request: Request, response: Optional[Response] = None, cookie_name: str = "jusu_session") -> None:
    """Clear user session and optionally remove session cookie on response."""
    try:
        request.session.pop("user", None)
    except AssertionError:
        if "session" in request.scope:
            request.scope["session"].pop("user", None)
    except Exception:
        if "session" in request.scope:
            request.scope["session"].pop("user", None)
    if response is not None:
        # Instruct browser to delete cookie
        response.delete_cookie(cookie_name)
