import sys
from JUSU import cli


def test_run_shell_command_creates_file(tmp_path):
    out = tmp_path / "flag.txt"
    cmd = f"{sys.executable} -c \"open(r'{out}', 'w').write('ok')\""
    cli.run_shell_command(cmd)
    assert out.exists()
    assert out.read_text() == "ok"


def test_register_engine_and_run(tmp_path):
    called = {"args": None}

    def fake_engine(args, out_dir, name_arg):
        called["args"] = (args, out_dir, name_arg)

    cli.register_engine("fake", fake_engine)
    cli.run_engine("fake", "--foo", out_dir=str(tmp_path), name_arg="comp")
    assert called["args"][0] == "--foo"
    assert called["args"][1] == str(tmp_path)
    assert called["args"][2] == "comp"


def test_run_engine_missing():
    import pytest

    with pytest.raises(RuntimeError):
        cli.run_engine("nope-engine", "", out_dir=".", name_arg="comp")
