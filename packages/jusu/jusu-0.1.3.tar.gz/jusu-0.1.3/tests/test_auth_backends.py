import pytest

from JUSU.auth_backends import register_backend, get_backend, SessionBackend
from JUSU.app import JusuApp
from fastapi import HTTPException


class DummyBackend:
    def __init__(self):
        self.calls = 0

    def get_user(self, request):
        self.calls += 1
        # simple header-based check
        if getattr(request, "headers", {}).get("x-user") == "dummy":
            return {"sub": "dummy"}
        return None


def test_register_and_get_backend():
    b = DummyBackend()
    register_backend("dummy-test", b)
    assert get_backend("dummy-test") is b


def make_request_with_scope(scope=None, headers=None):
    class Req:
        pass

    r = Req()
    r.scope = scope or {}
    r.headers = headers or {}
    return r


def test_jusuapp_session_backend_get_user():
    app = JusuApp()
    app.set_auth_backend("session")  # registered by default

    req = make_request_with_scope({"session": {"user": {"sub": "alice"}}})
    user = app.get_current_user(req)
    assert user == {"sub": "alice"}


def test_jusuapp_missing_user_raises():
    app = JusuApp()
    app.set_auth_backend(SessionBackend())

    req = make_request_with_scope({})
    with pytest.raises(HTTPException):
        app.get_current_user(req, raise_on_missing=True)


def test_dummy_backend_registered_and_used():
    b = DummyBackend()
    register_backend("dummy2", b)
    app = JusuApp(auth_backend="dummy2")

    req = make_request_with_scope(headers={"x-user": "dummy"})
    user = app.get_current_user(req)
    assert user == {"sub": "dummy"}
    assert b.calls == 1
