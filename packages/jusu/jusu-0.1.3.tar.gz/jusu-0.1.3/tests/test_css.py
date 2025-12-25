from JUSU import StyleSheet


def test_stylesheet_basic(tmp_path):
	css = StyleSheet()
	css.add_class("btn", {"background": "blue", "color": "white", "padding": "0.5rem 1rem"})
	s = css.render(pretty=False)
	assert ".btn{" in s or ".btn" in s
	# write to file
	f = tmp_path / "site.css"
	css.write(str(f), pretty=True)
	assert f.exists()
	content = f.read_text(encoding="utf-8")
	assert "background" in content


def test_media_query():
	css = StyleSheet()
	css.add_class("container", {"max-width": "1200px"})
	css.add_media_query("(max-width: 640px)", {"container": {"padding": "0 1rem"}})
	s = css.render(pretty=False)
	assert "@media (max-width: 640px)" in s
	assert "padding" in s


def test_variables_minify_and_autoprefix():
	css = StyleSheet()
	css.add_variable("brand-color", "#123456")
	css.add_class("btn", {"background": "var(--brand-color)", "user_select": "none", "display": "flex"})
	# autoprefix off
	s1 = css.render(pretty=True, autoprefix=False)
	assert "--brand-color" in s1
	# autoprefix on and minify
	s2 = css.render(pretty=False, minify=True, autoprefix=True)
	assert "-webkit-user-select" in s2
	assert "-ms-flexbox" in s2 or "-webkit-box" in s2