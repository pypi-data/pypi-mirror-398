from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from JUSU.session_helpers import login_user, logout_user


def test_login_logout_helpers():
    app = FastAPI()

    @app.get("/login")
    def login(request: Request):
        login_user(request, {"sub": "alice"})
        return {"ok": True}

    @app.get("/who")
    def who(request: Request):
        # Access session safely (SessionMiddleware property raises AssertionError when absent)
        try:
            u = request.session.get("user")
        except AssertionError:
            u = request.scope.get("session", {}).get("user")
        return {"user": u}

    # Install a SessionMiddleware so the session persists across requests
    from JUSU.auth import SessionManager
    mgr = SessionManager(secret_key="testsess")
    mgr.init_app(app)

    client = TestClient(app)
    r = client.get("/login")
    assert r.status_code == 200
    r2 = client.get("/who")
    assert r2.json()["user"]["sub"] == "alice"

    @app.get("/logout")
    def do_logout(request: Request, response: Response):
        logout_user(request, response)
        return {"ok": True}

    r3 = client.get("/logout")
    assert r3.status_code == 200
    r4 = client.get("/who")
    assert r4.json()["user"] is None
