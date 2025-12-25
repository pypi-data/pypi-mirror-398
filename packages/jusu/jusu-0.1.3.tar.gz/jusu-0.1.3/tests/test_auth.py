from JUSU.auth import create_jwt, verify_jwt, SessionManager
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


def test_jwt_create_verify():
    token = create_jwt({"sub": "user1"}, secret="s3cr3t", expires_in=60)
    payload = verify_jwt(token, secret="s3cr3t")
    assert payload["sub"] == "user1"


def test_session_manager_basic():
    app = FastAPI()
    mgr = SessionManager(secret_key="sessionsecret", cookie_name="jusu_session", max_age=3600)
    mgr.init_app(app)

    @app.get("/set")
    def set_route(request: Request):
        request.session["x"] = "y"
        return {"ok": True}

    @app.get("/get")
    def get_route(request: Request):
        return {"x": request.session.get("x")}

    client = TestClient(app)
    r = client.get("/set")
    assert r.status_code == 200

    r2 = client.get("/get")
    assert r2.json()["x"] == "y"
