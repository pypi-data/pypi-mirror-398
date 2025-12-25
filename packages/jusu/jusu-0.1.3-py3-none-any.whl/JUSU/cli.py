"""CLI utilities for JUSU - minimal Typer-based CLI to perform common tasks."""
from __future__ import annotations

import importlib
import sys
import os
from pathlib import Path
from typing import Optional, Callable
import threading
import http.server
import socketserver
import time
import socket
import webbrowser
import subprocess
import shutil

import typer

app = typer.Typer(help="JUSU CLI - bundle components and export assets")

# Register auth subcommands
from .auth_cli import auth_app  # noqa: E402
app.add_typer(auth_app, name="auth")


def _import_target(target: str):
    """Import a python target specified as module:attr or module.attr

    Examples:
      mypkg.mymodule:page
      mypkg.mymodule.page
      mypkg.mymodule:app.instance
    Returns the object (callable or Tag instance) or raises an exception.
    """
    if ":" in target:
        module_name, attr = target.split(":", 1)
    elif "." in target:
        module_name, attr = target.rsplit(".", 1)
    else:
        raise typer.BadParameter("Target must be module:attr or module.attr")

    mod = importlib.import_module(module_name)
    # Support nested attribute access like 'app.instance' by walking the attribute chain
    obj = mod
    for part in attr.split("."):
        if not hasattr(obj, part):
            raise typer.BadParameter(f"Module '{module_name}' has no attribute '{attr}'")
        obj = getattr(obj, part)
    return obj


@app.command()
def bundle(
    target: str = typer.Argument(..., help="Module:attr path to component (e.g. mypkg.page:main)"),
    out_dir: Path = typer.Option(Path("./dist"), help="Output directory where bundle will be written"),
    name: Optional[str] = typer.Option(None, help="Base name for output files (defaults to target attr name)"),
    scoped: bool = typer.Option(True, help="Scope CSS classnames for isolation"),
    scoped_unique: bool = typer.Option(False, help="Append timestamp/uuid for unique scope names"),
    zip: bool = typer.Option(False, help="Produce a zip archive of the bundle"),
    open_browser: bool = typer.Option(False, "--open", help="Open the resulting HTML in the default browser"),
    run_cmd: Optional[str] = typer.Option(None, "--run", help="Shell command to run after bundling (best-effort; potentially unsafe)"),
    engine: Optional[str] = typer.Option(None, help="Optional bundling engine to run after bundling (e.g. 'esbuild')"),
    engine_args: Optional[str] = typer.Option(None, help="Arguments to pass to the engine command"),
):
    """Bundle a component specified by its import path and write files to disk."""
    out_dir = Path(out_dir)
    try:
        obj = _import_target(target)
    except Exception as exc:
        typer.echo(f"Error importing target: {exc}")
        raise typer.Exit(code=2)

    # If obj is a callable, call it to get the Tag; otherwise assume it's already a Tag
    component = obj() if callable(obj) else obj

    if name is None:
        name = getattr(component, "name", None) or getattr(component, "__name__", "component")

    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        if zip:
            path = component.bundle_export(str(out_dir), name=name, scoped=scoped, scoped_unique=scoped_unique)
            typer.echo(f"Wrote bundle ZIP: {path}")
            html_path = None
        else:
            html_path, css_path = component.bundle(str(out_dir), name=name, scoped=scoped, scoped_unique=scoped_unique)
            typer.echo(f"Wrote HTML: {html_path}")
            typer.echo(f"Wrote CSS: {css_path}")
    except Exception as exc:
        typer.echo(f"Error bundling component: {exc}")
        raise typer.Exit(code=3)

    # Post-build: run engine, shell command, and optionally open
    if engine:
        try:
            run_engine(engine, engine_args or "", out_dir=str(out_dir), name=name)
            typer.echo(f"Ran engine: {engine}")
        except Exception as exc:
            typer.echo(f"Engine '{engine}' failed: {exc}")
    if run_cmd:
        try:
            run_shell_command(run_cmd)
            typer.echo("Ran post-build command")
        except Exception as exc:
            typer.echo(f"Post-build command failed: {exc}")
    if open_browser and html_path:
        open_url(f"http://127.0.0.1:{8000}/{os.path.basename(html_path)}")




# -- Serve/helpers & utilities -------------------------------------------

# Engine registry
_ENGINES: dict = {}

def register_engine(name: str, fn: Callable):
    _ENGINES[name] = fn


def run_engine(name: str, args: str, out_dir: str, name_arg: str) -> None:
    """Run a registered engine, or try to call a system command with the same name."""
    if name in _ENGINES:
        _ENGINES[name](args, out_dir, name_arg)
        return
    # Fallback: attempt to find system binary
    exe = shutil.which(name)
    if not exe:
        raise RuntimeError(f"Engine '{name}' not found on PATH and not registered.")
    cmd = [exe]
    if args:
        cmd.extend(args.split())
    # Best-effort run
    subprocess.run(cmd, check=True)


def run_shell_command(cmd: str) -> None:
    """Run a shell command as a best-effort post-build hook.

    Warning: running arbitrary shell commands can be unsafe and is executed
    with the user's privileges; this is provided as a convenience for local
    development only.
    """
    # On Windows, unquoted executable paths with spaces (e.g., a python.exe
    # inside "C:\Program Files ...") can cause the shell to split the
    # command incorrectly. Try to be helpful by quoting sys.executable when
    # it appears unquoted in the command string, and retry with a quoted
    # first token on failure.
    if isinstance(cmd, str):
        try:
            exe = sys.executable
        except Exception:
            exe = None
        if exe and exe in cmd and f'"{exe}"' not in cmd and f"'{exe}'" not in cmd:
            cmd = cmd.replace(exe, f'"{exe}"')
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        # As a second attempt (best-effort), on Windows try quoting the
        # first token if it contains spaces and is not already quoted.
        if os.name == "nt" and isinstance(cmd, str):
            parts = cmd.split()
            if parts:
                first = parts[0]
                if " " in first and not (first.startswith('"') or first.startswith("'")):
                    new_cmd = cmd.replace(first, f'"{first}"', 1)
                    subprocess.run(new_cmd, shell=True, check=True)
                    return
        raise


def start_static_server(directory: Path, port: int = 8000):
    """Start a simple HTTP server serving `directory`. Returns (server, thread, stop_callable)."""
    directory = Path(directory)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

    server = socketserver.ThreadingTCPServer(("", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def stop():
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            server.server_close()
        except Exception:
            pass
        if thread.is_alive():
            thread.join(timeout=1.0)

    return server, thread, stop


def open_url(url: str) -> None:
    """Open a URL in the default browser (wrapper for testability)."""
    try:
        webbrowser.open(str(url))
    except Exception:
        # Do not raise; best-effort only
        pass


def _is_port_open(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.2)
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        try:
            s.close()
        except Exception:
            pass
        return False


def watch_module_file(module_path: str, on_change: Callable, interval: float = 0.5, timeout: float = 5.0) -> bool:
    """Watch a file path for changes; call `on_change` once and return True when change detected.

    This helper is synchronous and intended for simple CLI behavior and tests.
    """
    try:
        last = os.path.getmtime(module_path)
    except OSError:
        last = None

    start = time.time()
    while True:
        if time.time() - start > timeout:
            return False
        try:
            cur = os.path.getmtime(module_path)
        except OSError:
            cur = None
        if last is not None and cur is not None and cur != last:
            try:
                on_change()
            except Exception:
                pass
            return True
        last = cur
        time.sleep(interval)


@app.command()
def serve(
    target: Optional[str] = typer.Argument(None, help="Optional module:attr path to component to build and watch"),
    out_dir: Path = typer.Option(Path("./dist"), help="Directory to serve and where bundles will be written"),
    port: int = typer.Option(8000, help="Port to serve on"),
    watch: bool = typer.Option(True, help="If True and a target is provided, rebuild on file changes"),
    interval: float = typer.Option(0.5, help="Polling interval for watcher in seconds"),
    open_browser: bool = typer.Option(False, "--open", help="Open the served URL in the default browser"),
    no_block: bool = typer.Option(False, help="Start server and return (useful for scripts/tests)"),
):
    """Serve a directory over HTTP and optionally watch a component to rebuild on changes."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    component = None
    module_file = None
    if target:
        try:
            obj = _import_target(target)
            component = obj() if callable(obj) else obj
            # try to locate module file for watching
            mod_name = target.split(":")[0] if ":" in target else target.rsplit('.', 1)[0]
            mod = __import__(mod_name, fromlist=[None])
            module_file = getattr(mod, "__file__", None)
        except Exception as exc:
            typer.echo(f"Error importing target: {exc}")
            raise typer.Exit(code=2)

    # initial build
    if component:
        try:
            component.bundle(str(out_dir), name=getattr(component, "name", "component"), scoped=True)
        except Exception as exc:
            typer.echo(f"Initial bundle failed: {exc}")

    # start server
    server, thread, stop_server = start_static_server(out_dir, port=port)
    # Update port in case 0 (ephemeral) was used
    actual_port = server.server_address[1]
    typer.echo(f"Serving {out_dir} at http://127.0.0.1:{actual_port}")

    # Optionally open browser
    if open_browser:
        open_url(f"http://127.0.0.1:{actual_port}")

    try:
        if no_block:
            # For no_block we briefly run the server and then stop so CLI returns (useful for tests/scripts)
            time.sleep(0.2)
            return
        if watch and component and module_file:
            typer.echo(f"Watching {module_file} for changes...")
            while True:
                changed = watch_module_file(module_file, lambda: component.bundle(str(out_dir), name=getattr(component, "name", "component")), interval=interval, timeout=3600.0)
                if not changed:
                    # timeout reached or watcher stopped; loop continues until interrupted
                    continue
        else:
            # block until Ctrl+C
            while True:
                time.sleep(1.0)
    except KeyboardInterrupt:
        typer.echo("Stopping server...")
    finally:
        stop_server()


@app.command()
def run(
    target: str = typer.Argument("examples.fastapi_app:app.app", help="ASGI app target (module:attr or nested attr)"),
    host: str = typer.Option("127.0.0.1", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind"),
    reload: bool = typer.Option(False, help="Enable auto-reload (uses uvicorn)"),
    no_block: bool = typer.Option(False, help="Run in background and return immediately"),
):
    """Run an ASGI app using Uvicorn. The `target` can be nested (e.g. module:app.instance)."""
    try:
        obj = _import_target(target)
    except Exception as exc:
        typer.echo(f"Error importing target: {exc}")
        raise typer.Exit(code=2)

    # If the object is a JusuApp wrapper, try to access `.app` attribute to get FastAPI
    if hasattr(obj, "app") and not callable(obj):
        asgi_app = getattr(obj, "app")
    else:
        asgi_app = obj

    try:
        import uvicorn
    except Exception:
        typer.echo("uvicorn is required to run an ASGI app; install with `pip install jusu[web]`")
        raise typer.Exit(code=3)

    if no_block:
        # Start uvicorn in a background thread and return
        import threading

        def _target():
            uvicorn.run(asgi_app, host=host, port=port, reload=reload)

        t = threading.Thread(target=_target, daemon=True)
        t.start()
        typer.echo(f"Started ASGI app at http://{host}:{port} (background)")
        return

    # Blocking run
    uvicorn.run(asgi_app, host=host, port=port, reload=reload)


@app.command()
def migrate(
    revision: str = typer.Option("head", help="Target revision (head by default)"),
    alembic_ini: str = typer.Option("alembic.ini", help="Path to alembic.ini"),
    init: bool = typer.Option(False, help="Initialize an Alembic environment (creates ./alembic)"),
    create: bool = typer.Option(False, help="Create a new revision (runs alembic revision)") ,
    message: str = typer.Option("", "-m", help="Message for new revision when using --create"),
):
    """Run Alembic migrations (requires alembic installed and a configured alembic.ini).

    Set `--init` to bootstrap an Alembic environment via `alembic init alembic`.
    Use `--create -m "msg"` to create a new revision (autogenerate if possible).
    """
    import subprocess
    exe = shutil.which("alembic")
    if not exe:
        typer.echo("Alembic not found on PATH. Install with `pip install alembic` and configure an alembic.ini.")
        raise typer.Exit(code=2)
    if init:
        cmd = [exe, "init", "alembic"]
        subprocess.run(cmd, check=True)
        typer.echo("Alembic environment initialized (./alembic)")
        return
    if create:
        cmd = [exe, "-c", alembic_ini, "revision", "-m", message or "autogenerated", "--autogenerate"]
        subprocess.run(cmd, check=True)
        typer.echo("Alembic revision created")
        return
    cmd = [exe, "-c", alembic_ini, "upgrade", revision]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    app()
