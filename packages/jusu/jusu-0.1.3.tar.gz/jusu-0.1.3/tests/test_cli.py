from JUSU import cli
import sys


def test_cli_bundle_unscoped(tmp_path):
    # create a tiny module file to import
    mod_path = tmp_path / "mymod.py"
    mod_path.write_text(
        "from JUSU.core import Div, P\ncomp = Div(P('hello'), cls='c', css={'c': {'color': 'red'}})\n",
        encoding="utf-8",
    )
    sys.path.insert(0, str(tmp_path))
    try:
        obj = cli._import_target("mymod:comp")
        component = obj() if callable(obj) else obj
        html_path, css_path = component.bundle(str(tmp_path), name="comp", scoped=False)
        assert (tmp_path / "comp.css").exists()
    finally:
        sys.path.pop(0)


def test_cli_bundle_zip(tmp_path):
    mod_path = tmp_path / "mymod2.py"
    mod_path.write_text(
        "from JUSU.core import Div, P\ncomp = Div(P('x'), cls='c', css={'c': {'color': 'blue'}})\n",
        encoding="utf-8",
    )
    sys.path.insert(0, str(tmp_path))
    try:
        obj = cli._import_target("mymod2:comp")
        component = obj() if callable(obj) else obj
        component.bundle_export(str(tmp_path), name="compzip", scoped=False)
        assert (tmp_path / "compzip.zip").exists()
    finally:
        sys.path.pop(0)
