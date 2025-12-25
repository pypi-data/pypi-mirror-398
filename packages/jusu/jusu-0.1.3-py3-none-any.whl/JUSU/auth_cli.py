"""CLI helpers for auth-related commands (hash, create-user)."""
from __future__ import annotations

import typer
from sqlmodel import SQLModel, Field, Session, create_engine, select

from .auth import hash_password

auth_app = typer.Typer(help="Auth helpers: password hashing and simple user creation")


class _User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    salt: str
    hashed: str


@auth_app.command()
def hash(password: str = typer.Argument(..., help="Password to hash")):
    """Hash a password and print salt,hash (salt empty when bcrypt used)."""
    salt, hashed = hash_password(password)
    typer.echo(salt)
    typer.echo(hashed)


@auth_app.command()
def create_user(
    db_url: str = typer.Option("sqlite:///./jusu_users.db", help="Database URL to store the user"),
    username: str = typer.Option(..., help="Username for the user"),
    password: str = typer.Option(..., help="Password for the user"),
):
    """Create a simple user record in the given DB (creates table if needed)."""
    engine = create_engine(db_url, echo=False)
    SQLModel.metadata.create_all(engine)
    salt, hashed = hash_password(password)
    user = _User(username=username, salt=salt, hashed=hashed)
    with Session(engine) as sess:
        existing = sess.exec(select(_User).where(_User.username == username)).first()
        if existing:
            typer.echo(f"User '{username}' already exists")
            raise typer.Exit(code=2)
        sess.add(user)
        sess.commit()
    typer.echo(f"Created user '{username}'")


__all__ = ["auth_app"]
