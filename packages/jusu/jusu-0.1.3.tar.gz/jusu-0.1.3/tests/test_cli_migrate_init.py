from typer.testing import CliRunner

from JUSU.cli import app


def test_migrate_init_runs_alembic(monkeypatch):
    runner = CliRunner()
    fake = {}

    def fake_which(name):
        return "/usr/bin/alembic"

    def fake_run(cmd, check):
        fake['cmd'] = cmd

    monkeypatch.setattr("shutil.which", fake_which)
    monkeypatch.setattr("subprocess.run", fake_run)

    result = runner.invoke(app, ["migrate", "--init"])
    assert result.exit_code == 0
    assert fake['cmd'][0].endswith('alembic')
    assert fake['cmd'][1] == 'init'
    assert fake['cmd'][2] == 'alembic'
