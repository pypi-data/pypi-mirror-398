from JUSU.core import Div, H1, P, Header, Nav, Main, Section, Article, Footer, Button, Img, Ul, Input, Comment, JusuError, UnknownAttributeError, EmptyTagError
from JUSU import StyleSheet


def test_basic_rendering(tmp_path):
	header = H1("Hello")
	para = P("This is a paragraph.")
	btn = Button("Click", onclick="alert('ok')", cls="btn")
	img = Img(src="https://example.com/image.png", alt="an image")
	page = Div(header, para, btn, img, cls="main")
	html = page.render(pretty=False)
	assert "<h1" in html
	assert "<p>" in html
	assert "onclick='alert'" or "onclick=" in html or "onclick" in html


def test_self_closing_and_wrapping():
	u = Ul("Item 1", "Item 2")
	out = u.render(pretty=False)
	assert "<li>" in out
	# Img must be self closing and not accept children
	try:
		Img("child")
		assert False, "Img should not accept children"
	except JusuError:
		pass
	# Input must be self-closing and not accept children
	try:
		Input("child")
		assert False, "Input should not accept children"
	except JusuError:
		pass


def test_attribute_validation_and_empty_errors():
	# Invalid attribute name passed via expansion
	try:
		Div("X", **{"bad$name": "x"})
		assert False, "Invalid attribute name should raise"
	except UnknownAttributeError:
		pass

	# Empty div should raise
	try:
		Div()
		assert False, "EmptyTagError expected"
	except EmptyTagError:
		pass


def test_render_to_file(tmp_path):
	header = H1("File test")
	page = Div(header, cls="wrap")
	out = tmp_path / "out.html"
	page.render_to_file(str(out))
	assert out.exists()
	content = out.read_text(encoding="utf-8")
	assert "<!DOCTYPE html>" in content


def test_render_to_file_with_stylesheet(tmp_path):
	header = H1("File test")
	page = Div(header, cls="wrap")
	css = StyleSheet()
	css.add_class("wrap", {"max-width": "800px"})
	out = tmp_path / "out2.html"
	cssfile = tmp_path / "out2.css"
	page.render_to_file(str(out), styles=css, css_filename=str(cssfile), css_minify=False)
	# Files should be created
	assert out.exists()
	assert cssfile.exists()
	content = out.read_text(encoding="utf-8")
	assert '<link rel="stylesheet" href="out2.css">' in content
	assert "max-width" in cssfile.read_text(encoding="utf-8")


def test_style_dict_and_cls_mapping():
	# Support passing style as dict and mapping 'cls' to class attribute
	p = P("Styled paragraph", cls="lead", style={"color": "red", "font-weight": "bold"})
	html = p.render(pretty=False)
	assert 'class="lead"' in html
	assert 'style="color: red; font-weight: bold"' in html

def test_boolean_and_data_aria_attributes():
	inp = Input(type="checkbox", checked=True, data_id="42", aria_label="Close")
	out = inp.render(pretty=False)
	assert "checked" in out
	assert 'data-id="42"' in out
	assert 'aria-label="Close"' in out


def test_comment_and_minified_output():
	c = Comment("This is a comment")
	html = c.render(pretty=False)
	assert html.strip() == "<!-- This is a comment -->"
	# Test minified rendering for text escaping
	p = P("A & B <tag>")
	html2 = p.render(pretty=False)
	assert "&amp;" in html2
	assert "\n" not in html2


def test_semantic_tags_and_aria():
	h = Header(Nav(Button("Home", role="link", aria_label="Home")), cls="site-header")
	assert "<header" in h.render(pretty=False)
	# role and aria mapping
	btn = Button("Close", role="button", aria_pressed=False, aria_label="Close")
	html = btn.render(pretty=False)
	assert 'role="button"' in html
	assert 'aria-pressed' not in html or 'aria-pressed="False"' not in html
	# adding main/section/article/footer
	m = Main(Section(Article(H1("Title"), P("Content"))), Footer(P("© 2025")))
	out = m.render(pretty=False)
	assert "<main" in out
	assert "<section" in out
	assert "<article" in out
	assert "<footer" in out