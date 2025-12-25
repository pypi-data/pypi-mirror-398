import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from JUSU.app import JusuApp  # noqa: E402
from JUSU import Div, H1, P  # noqa: E402


def test_index_returns_html():
    app = JusuApp("test")

    @app.get("/")
    def index():
        return Div(H1("Hello JUSU"), P("works"))

    client = TestClient(app.app)
    r = client.get("/")
    assert r.status_code == 200
    assert "Hello JUSU" in r.text
    assert "works" in r.text
