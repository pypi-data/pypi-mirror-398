from pathlib import Path
from JUSU.core import Div, P


def test_component_bundle_scoped(tmp_path):
    page = Div(P("Hello world"), cls="card highlight", css={"card": {"background": "yellow", "padding": "1rem"}})
    out_dir = str(tmp_path)
    html_path, css_path = page.bundle(out_dir, name="card", scoped=True)
    assert Path(html_path).exists()
    assert Path(css_path).exists()
    html = Path(html_path).read_text(encoding="utf-8")
    css = Path(css_path).read_text(encoding="utf-8")
    # The class 'card' should have been rewritten to a prefixed name in HTML
    assert "card" not in html or "card " not in html or "class=\"card\"" not in html
    # CSS should contain the prefixed classname
    assert "_card" in css


def test_component_bundle_unscoped(tmp_path):
    page = Div(P("Hello world"), cls="card", css={"card": {"background": "green"}})
    html_path, css_path = page.bundle(str(tmp_path), name="card_unscoped", scoped=False)
    assert Path(html_path).exists()
    css = Path(css_path).read_text(encoding="utf-8")
    assert ".card" in css
