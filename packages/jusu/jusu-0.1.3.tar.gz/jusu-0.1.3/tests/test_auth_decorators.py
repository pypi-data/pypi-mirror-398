from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, Request
from JUSU.auth import create_jwt, SessionManager, login_required


def test_jwt_and_login_required_cookie_session():
    app = FastAPI()
    mgr = SessionManager(secret_key="testsess")
    mgr.init_app(app)

    @app.get("/set")
    def set_route(request: Request):
        request.session["user"] = {"sub": "alice"}
        return {"ok": True}

    @app.get("/who")
    def who(user=Depends(login_required(jwt_secret="jwtsecret"))):
        return {"user": user}

    client = TestClient(app)
    r = client.get("/set")
    assert r.status_code == 200
    r2 = client.get("/who")
    assert r2.status_code == 200
    assert r2.json()["user"]["sub"] == "alice"


def test_jwt_bearer_access():
    app = FastAPI()

    @app.get("/who")
    def who(user=Depends(login_required(jwt_secret="jwtsecret"))):
        return {"user": user}

    client = TestClient(app)
    token = create_jwt({"sub":"bob"}, secret="jwtsecret", expires_in=60)
    r = client.get("/who", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["user"]["sub"] == "bob"
