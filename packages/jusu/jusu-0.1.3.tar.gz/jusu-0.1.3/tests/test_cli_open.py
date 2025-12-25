from typer.testing import CliRunner
from JUSU import cli

runner = CliRunner()


def test_open_url_helper(monkeypatch):
    called = {"url": None}

    def fake_open(u):
        called["url"] = u
        return True

    monkeypatch.setattr("webbrowser.open", fake_open)
    cli.open_url("http://127.0.0.1:1234")
    assert called["url"] == "http://127.0.0.1:1234"


def test_serve_open_no_block(monkeypatch, tmp_path):
    # ensure browser open is called when --open and --no-block used
    called = {"url": None}

    def fake_open(u):
        called["url"] = u
        return True

    monkeypatch.setattr("webbrowser.open", fake_open)

    res = runner.invoke(cli.app, ["serve", "--out-dir", str(tmp_path), "--no-block", "--open"]) 
    assert res.exit_code == 0
    assert called["url"] is not None
    assert "127.0.0.1" in called["url"]
