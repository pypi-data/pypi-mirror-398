from fastapi.testclient import TestClient

from JUSU.app import JusuApp
from JUSU import Div, P


def test_add_middleware_and_route():
    app = JusuApp("mwtest")

    class HeaderMW:
        def __init__(self, app, header_name="X-Test-Header"):
            self.app = app
            self.header_name = header_name

        async def __call__(self, scope, receive, send):
            async def send_wrapper(message):
                if message.get("type") == "http.response.start":
                    headers = list(message.setdefault("headers", []))
                    headers.append((self.header_name.encode(), b"1"))
                    message["headers"] = headers
                await send(message)

            await self.app(scope, receive, send_wrapper)

    app.add_middleware(HeaderMW, header_name="X-Test-Header")

    @app.get("/mw")
    def mw_index():
        return Div(P("ok"))

    client = TestClient(app.app)
    r = client.get("/mw")
    assert r.status_code == 200
    assert r.headers.get("X-Test-Header") == "1"


def test_mount_static_with_cache(tmp_path):
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    f = static_dir / "hello.txt"
    f.write_text("hello")

    app = JusuApp("static")
    app.mount_static("/static", directory=str(static_dir), cache_control="public, max-age=3600")

    client = TestClient(app.app)
    r = client.get("/static/hello.txt")
    assert r.status_code == 200
    assert r.text == "hello"
    assert r.headers.get("Cache-Control") == "public, max-age=3600"
