from typer.testing import CliRunner
from sqlmodel import create_engine, Session, select

from JUSU.cli import app


def test_auth_hash_outputs_hash():
    runner = CliRunner()
    result = runner.invoke(app, ["auth", "hash", "secretpw"])
    assert result.exit_code == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 2


def test_create_user_creates_db(tmp_path):
    runner = CliRunner()
    dbfile = tmp_path / "test_users.db"
    db_url = f"sqlite:///{dbfile}"
    username = "alice"
    res = runner.invoke(app, ["auth", "create-user", "--db-url", db_url, "--username", username, "--password", "pw"])
    # Typer uses exit_code 0 on success
    assert res.exit_code == 0
    # verify record exists
    from JUSU.auth_cli import _User
    engine = create_engine(db_url, echo=False)
    SQLModel = None
    try:
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(engine)
    except Exception:
        pass
    with Session(engine) as s:
        u = s.exec(select(_User).where(_User.username == username)).first()
        assert u is not None
        assert u.username == username
