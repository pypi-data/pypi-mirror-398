from pathlib import Path
from JUSU.core import Div, P


def test_scoped_unique_prefix_change(tmp_path):
    page = Div(P("Hi"), cls="card", css={"card": {"color": "red"}})
    out = str(tmp_path)
    # create two zip exports with unique scoping
    zip1 = page.bundle_export(out, name="comp1", scoped=True, scoped_unique=True)
    zip2 = page.bundle_export(out, name="comp2", scoped=True, scoped_unique=True)
    assert Path(zip1).exists()
    assert Path(zip2).exists()
    # extract CSS from both zip files and ensure the prefixes differ
    import zipfile

    def read_css_from_zip(zippath):
        with zipfile.ZipFile(zippath, "r") as zf:
            for name in zf.namelist():
                if name.endswith('.css'):
                    return zf.read(name).decode('utf-8')
        return ""

    css1 = read_css_from_zip(zip1)
    css2 = read_css_from_zip(zip2)
    assert css1 != css2


def test_bundle_zip_contains_files(tmp_path):
    page = Div(P("Hello"), cls="card", css={"card": {"background": "green"}})
    out = str(tmp_path)
    zippath = page.bundle_export(out, name="compzip", scoped=False)
    assert Path(zippath).exists()
    import zipfile
    with zipfile.ZipFile(zippath, 'r') as zf:
        names = zf.namelist()
        assert 'compzip.html' in names
        assert 'compzip.css' in names
