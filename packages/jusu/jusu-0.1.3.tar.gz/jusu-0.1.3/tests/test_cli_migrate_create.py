from typer.testing import CliRunner
from JUSU.cli import app


def test_migrate_create(monkeypatch):
    runner = CliRunner()
    fake = {}

    def fake_which(name):
        return "/usr/bin/alembic"

    def fake_run(cmd, check):
        fake['cmd'] = cmd

    monkeypatch.setattr("shutil.which", fake_which)
    monkeypatch.setattr("subprocess.run", fake_run)

    result = runner.invoke(app, ["migrate", "--create", "-m", "add users"])
    assert result.exit_code == 0
    assert fake['cmd'][0].endswith('alembic')
    assert fake['cmd'][1] == '-c'
    assert 'revision' in fake['cmd']
    assert '-m' in fake['cmd']
