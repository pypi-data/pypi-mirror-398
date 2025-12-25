from JUSU import StyleSheet
from JUSU.core import Div, P


def test_tag_css_registration(tmp_path):
    css = StyleSheet()
    page = Div(P("Hello"), cls="box", css={"box": {"color": "red", "padding": "1rem"}})
    out = tmp_path / "page.html"
    cssfile = tmp_path / "page.css"
    page.render_to_file(str(out), styles=css, css_filename=str(cssfile))
    assert cssfile.exists()
    content = cssfile.read_text(encoding="utf-8")
    assert "color: red" in content


def test_autoprefixer_pluggable():
    css = StyleSheet()

    def my_prefixer(props):
        # simple example: if transform in props, return a custom prefixed prop
        if "transform" in props:
            return [("-my-transform", props["transform"]) ]
        return []

    css.add_class("t", {"transform": "rotate(10deg)"})
    css.add_autoprefixer(my_prefixer)
    s = css.render(pretty=False, autoprefix=True)
    assert "-my-transform" in s

