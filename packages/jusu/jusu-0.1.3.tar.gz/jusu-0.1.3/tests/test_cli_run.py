from typer.testing import CliRunner
from unittest.mock import patch

from JUSU.cli import _import_target, app


def test_import_nested_attribute():
    # examples.fastapi_app provides `app` (JusuApp) and `.app` (FastAPI) nested
    obj = _import_target("examples.fastapi_app:app.app")
    # FastAPI apps have an `openapi` attribute
    assert hasattr(obj, "openapi")


def test_run_no_block_monkeypatch(monkeypatch):
    runner = CliRunner()

    # Monkeypatch uvicorn.run to avoid actually starting a server
    called = {}

    def fake_run(asgi_app, host, port, reload):
        called['host'] = host
        called['port'] = port
        called['reload'] = reload

    with patch("uvicorn.run", fake_run):
        result = runner.invoke(app, ["run", "examples.fastapi_app:app.app", "--host", "127.0.0.1", "--port", "12345", "--no-block"])
        assert result.exit_code == 0
        assert called['host'] == "127.0.0.1"
        assert called['port'] == 12345
