"""
JUSU - A tiny beginner-friendly HTML builder library

This module provides simple Tag classes to build HTML using plain-English
style Python syntax. The API is intentionally forgiving for beginners:
- strings passed as children are auto-wrapped into paragraphs where sensible
- `cls` maps to the HTML `class` attribute
- `render()` returns HTML string
- `render_to_file()` writes an HTML string to a file

Supported tags: Div, H1, P, Button, Img, Span, Ul, Li, Br, Hr, Input

Usage (demo at bottom):
	page = Div(H1("Hello"), P("Welcome."), Button("Click me", onclick="alert('Hi')"))
	print(page.render())
"""
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from typing import Any, List, MutableMapping, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from .css import StyleSheet
import os


class JusuError(Exception):
	"""Base class for JUSU errors."""


class UnknownAttributeError(JusuError):
	"""Raised when an attribute is invalid or intentionally forbidden."""


class EmptyTagError(JusuError):
	"""Raised when a non-self-closing tag is created without children."""


def _is_string_like(value: Any) -> bool:
	return isinstance(value, (str,))


def _debug(msg: str) -> None:
	# Lightweight debug helper; keep no-op by default to avoid noisy output.
	# Developers can monkeypatch or override during debugging if needed.
	return


@dataclass
class Tag:
	"""Generic HTML tag builder.

	Parameters:
	- name: tag name (e.g. 'div')
	- children: nested string or Tag objects
	- attrs: keyword arguments for attributes (uses 'cls' for class)
	"""

	name: str
	_children: List[Any] = field(default_factory=list)
	_attrs: MutableMapping[str, Any] = field(default_factory=dict)
	self_closing: bool = False
	allow_empty: bool = False

	# A small set of attribute names we specially support mapping for.
	_attr_aliases = {
		"cls": "class",
		"classname": "class",
		# leave 'id', 'style', 'onclick' as-is
	}

	def __init__(self, *children: Any, **attrs: Any) -> None:
		# initialize dataclass fields
		object.__setattr__(self, "name", getattr(self, "name", self.__class__.__name__.lower()))
		object.__setattr__(self, "_children", [])
		object.__setattr__(self, "_attrs", {})

		# Special attribute mapping: accept 'cls' and 'class' (for flexibility)
		for key, value in attrs.items():
			key_str = str(key)
			# Map aliases like 'cls' -> 'class'
			if key_str in self._attr_aliases:
				key_str = self._attr_aliases[key_str]
			# Allow python-friendly attribute names like data_id -> data-id and aria_label -> aria-label
			key_str = key_str.replace("_", "-")
			# Special: collect css rules (do not render as an HTML attribute)
			if key_str == "css":
				object.__setattr__(self, "_css_rules", value)
				continue
			if key_str == "class":
				self._attrs["class"] = value
			else:
				# Allow only alphanumeric and hyphens in attribute names
				if not key_str.replace("-", "").isalnum():
					raise UnknownAttributeError(f"Invalid attribute name: '{key}'.")
				self._attrs[key_str] = value

		# Add children (strings or Tag objects). Auto-wrap strings where sensible.
		for child in children:
			self.add(child)

		# Validation at construction time: non-self-closing tags must not be empty
		if not getattr(self, "self_closing", False) and not getattr(self, "allow_empty", False):
			if len(self._children) == 0:
				raise EmptyTagError(f"Tag <{self.name}> is empty. Add children or use allow_empty=True.")

	def add(self, child: Any) -> Tag:
		"""Add a child (string or Tag) to this tag in a forgiving way.

		- Strings are wrapped in `P` unless this tag expects inline content.
		- Strings under `ul` become `Li` elements.
		- Tag children are added as-is.
		"""
		# Handle None silently
		if child is None:
			return self

		# Allow lists/iterables to be flattened
		if isinstance(child, (list, tuple)):
			for c in child:
				self.add(c)
			return self

		# If child is a string, decide a sensible wrapper
		if _is_string_like(child):
			text = str(child)
			# In a UL, text should be wrapped into LI. For inline tags and
			# text-holding tags like P/H1/Li/Span/Button we insert text directly
			if self.name == "ul":
				self._children.append(Li(text))
			elif self.name in {"span", "button", "p", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
				self._children.append(text)
			else:
				# For block containers like div, wrap plain text into paragraphs
				self._children.append(P(text))
			return self

		# If child is already a Tag, append
		if isinstance(child, Tag):
			self._children.append(child)
			return self

		# Finally, try converting to str and add
		self._children.append(str(child))
		return self

	def collect_css_rules(self) -> dict:
		"""Recursively collect css rule dicts from this tag and children.

		Each tag may supply a `css` kwarg (a dict mapping classnames to props).
		This method merges them and returns a dict suitable for StyleSheet.add_class.
		"""
		rules: dict = {}
		# own rules
		own = getattr(self, "_css_rules", None)
		if isinstance(own, dict):
			for k, v in own.items():
				rules[k] = v
		# children
		for child in self._children:
			if isinstance(child, Tag):
				rules.update(child.collect_css_rules())
		return rules

	def register_css(self, stylesheet: "StyleSheet") -> None:
		"""Register collected rules into the provided StyleSheet."""
		rules = self.collect_css_rules()
		for k, v in rules.items():
			stylesheet.add_class(k, v)

	def _render_attrs(self) -> str:
		"""Render attributes mapping, escaping values appropriately."""
		pieces: List[str] = []
		for k, v in self._attrs.items():
			if v is True:
				pieces.append(f"{k}")
			elif v is False or v is None:
				continue
			else:
				# Accept style as dict for beginner-friendliness
				if k == "style" and isinstance(v, dict):
					style_str = "; ".join(f"{prop}: {val}" for prop, val in v.items())
					pieces.append(f'{k}="{escape(style_str, quote=True)}"')
				else:
					pieces.append(f'{k}="{escape(str(v), quote=True)}"')
		return " " + " ".join(pieces) if pieces else ""

	def render(self, indent: Optional[int] = 0, pretty: bool = True) -> str:
		"""Return the HTML string for this tag, optionally pretty-printed.

		- `indent` indicates number of spaces to indent the current tag.
		- `pretty` when True inserts newlines and indentation for readability.
		"""
		space = " " * (indent or 0)
		nl = "\n" if pretty else ""
		attrs = self._render_attrs()

		if getattr(self, "self_closing", False):
			return f"{space}<{self.name}{attrs} />{nl}"

		if not self._children and not getattr(self, "allow_empty", False):
			# defensive check: if children are absent, we raise the informative error
			raise EmptyTagError(f"Tag <{self.name}> is empty and may be accidental.")

		# render children
		rendered_children: List[str] = []
		for child in self._children:
			if isinstance(child, Tag):
				rendered_children.append(child.render(indent=(indent or 0) + 2, pretty=pretty))
			else:
				# text node - escape HTML
				text = escape(str(child))
				if pretty:
					rendered_children.append(f"{' ' * ((indent or 0) + 2)}{text}{nl}")
				else:
					rendered_children.append(text)

		content = "".join(rendered_children)
		if pretty:
			return f"{space}<{self.name}{attrs}>{nl}{content}{space}</{self.name}>{nl}"
		else:
			return f"<{self.name}{attrs}>{content}</{self.name}>"

	def render_to_file(
		self,
		filename: str,
		pretty: bool = True,
		doctype: bool = True,
		styles: Optional["StyleSheet"] = None,
		css_filename: Optional[str] = None,
		css_minify: bool = False,
		css_autoprefix: bool = False,
	) -> None:
		"""Write the HTML for this tag to a file.

		Optionally write a linked CSS file when a StyleSheet is provided.
		- `styles`: a `StyleSheet` instance to write
		- `css_filename`: optional path for the stylesheet; defaults to the HTML name with .css
		- `css_minify`/`css_autoprefix`: styling render options
		"""
		body = self.render(pretty=pretty)
		# Small friendly document wrapper for beginners; insert stylesheet link when provided
		head_parts = ["<head>\n<meta charset=\"utf-8\">\n"]
		if styles is not None:
			# If the tag tree contains css rules, register them first
			try:
				self.register_css(styles)
			except Exception:
				# keep render resilient
				pass
			# Determine default css filename if not given
			if css_filename is None:
				base, _ = os.path.splitext(filename)
				css_filename = base + ".css"
			# Write CSS to file
			styles.write(css_filename, pretty=pretty, minify=css_minify, autoprefix=css_autoprefix)
			head_parts.append(f'<link rel="stylesheet" href="{os.path.basename(css_filename)}">\n')
		head_parts.append("</head>\n")
		head = "".join(head_parts)
		html_doc = f"<html>\n{head}<body>\n{body}\n</body>\n</html>\n"
		if doctype:
			full = "<!DOCTYPE html>\n" + html_doc
		else:
			full = html_doc

		with open(filename, "w", encoding="utf-8") as fh:
			fh.write(full)

# Tag subclasses (small, readable wrappers)
class Div(Tag):
	name = "div"


class H1(Tag):
	name = "h1"


class P(Tag):
	name = "p"


class Button(Tag):
	name = "button"


class Img(Tag):
	name = "img"
	self_closing = True

	def __init__(self, *children: Any, **attrs: Any) -> None:
		# Img is self-closing; children are not allowed
		if children:
			raise JusuError("Img is a self-closing tag and cannot contain children.")
		super().__init__(**attrs)


class Span(Tag):
	name = "span"
	allow_empty = True


class Ul(Tag):
	name = "ul"


class Li(Tag):
	name = "li"


class Input(Tag):
	name = "input"
	self_closing = True

	def __init__(self, *children: Any, **attrs: Any) -> None:
		if children:
			raise JusuError("Input is a self-closing tag and cannot contain children.")
		super().__init__(**attrs)


class Br(Tag):
	name = "br"
	self_closing = True


class Hr(Tag):
	name = "hr"
	self_closing = True


# Semantic helpers: header, nav, main, section, article, footer
class Header(Tag):
	name = "header"


class Nav(Tag):
	name = "nav"


class Main(Tag):
	name = "main"


class Section(Tag):
	name = "section"


class Article(Tag):
	name = "article"


class Footer(Tag):
	name = "footer"


# Heading levels
class H2(Tag):
	name = "h2"


class H3(Tag):
	name = "h3"


class H4(Tag):
	name = "h4"


class H5(Tag):
	name = "h5"


class H6(Tag):
	name = "h6"


class Comment:
	"""Render an HTML comment node."""
	def __init__(self, text: Any) -> None:
		self.text = text

	def render(self, indent: Optional[int] = 0, pretty: bool = True) -> str:
		space = " " * (indent or 0)
		nl = "\n" if pretty else ""
		# Comments must not contain '--'; escape sequences safely
		safe_text = str(self.text).replace("--", "&#45;&#45;")
		return f"{space}<!-- {safe_text} -->{nl}"

	# Utilities for scoping and bundling
	def _traverse_tags(self):
		# generator for traversing Tag trees -- implemented on Tag below
		raise NotImplementedError


# Add Tag traversal, scoping and bundling methods
def _tag_traverse(self):
	yield self
	for c in self._children:
		if isinstance(c, Tag):
			yield from c._traverse_tags()


def _generate_scope_prefix(self, unique: bool = False) -> str:
	"""Generate a short prefix based on the tag and its collected rules.

	If `unique` is True, include a timestamp + random UUID suffix for stronger uniqueness.
	"""
	import hashlib
	import time
	import uuid
	rules = sorted(list(self.collect_css_rules().keys()))
	base = self.name + "::" + ",".join(rules)
	h = hashlib.sha1(base.encode("utf-8")).hexdigest()
	prefix = h[:8]
	if unique:
		suffix = f"{int(time.time()):x}{uuid.uuid4().hex[:6]}"
		return f"{prefix}{suffix}"
	return prefix


def _apply_scoped_mapping(self, mapping: dict):
	"""Mutate class attributes in-place replacing classnames according to `mapping`.

	Returns a dict of original values so caller can restore later.
	"""
	originals = {}
	for node in self._traverse_tags():
		cls_val = node._attrs.get("class")
		if not cls_val:
			continue
		orig = cls_val
		parts = str(cls_val).split()
		new_parts = [mapping.get(p, p) for p in parts]
		new = " ".join(new_parts)
		if new != orig:
			originals[id(node)] = orig
			node._attrs["class"] = new
	return originals


def _restore_scoped_mapping(self, originals: dict):
	for node in self._traverse_tags():
		if id(node) in originals:
			node._attrs["class"] = originals[id(node)]


def _collect_rules_for_bundle(self) -> dict:
	"""Collect a fresh copy of the css rules for bundling."""
	return dict(self.collect_css_rules())


def bundle(self, out_dir: str, name: str = "component", pretty: bool = True, minify_css: bool = False, autoprefix_css: bool = False, scoped: bool = True, scoped_unique: bool = False) -> tuple[str, str]:
	"""Bundle this tag as an HTML file + CSS file.

	- `out_dir`: directory path (string or Path)
	- `name`: base filename (without extension)
	- returns (html_path, css_path)
	"""
	import os
	from .css import StyleSheet

	os.makedirs(out_dir, exist_ok=True)
	rules = self._collect_rules_for_bundle()
	ss = StyleSheet()
	mapping = {}
	originals = {}
	# If scoped, create prefixed classnames
	if scoped and rules:
		prefix = self._generate_scope_prefix(unique=scoped_unique)
		for k in list(rules.keys()):
			mapping[k] = f"{prefix}_{k}"
		scoped_rules = {mapping[k]: v for k, v in rules.items()}
		for k, v in scoped_rules.items():
			ss.add_class(k, v)
		# apply mapping to this tag tree (mutates temporarily)
		originals = self._apply_scoped_mapping(mapping)
	else:
		for k, v in rules.items():
			ss.add_class(k, v)

	html_file = os.path.join(out_dir, f"{name}.html")
	css_file = os.path.join(out_dir, f"{name}.css")
	# Use existing render_to_file which writes css when given a StyleSheet
	try:
		self.render_to_file(html_file, pretty=pretty, styles=ss, css_filename=css_file, css_minify=minify_css, css_autoprefix=autoprefix_css)
	finally:
		# restore original classes if we mutated them
		if originals:
			self._restore_scoped_mapping(originals)

	return (html_file, css_file)


def bundle_export(self, out_dir: str, name: str = "component", pretty: bool = True, minify_css: bool = False, autoprefix_css: bool = False, scoped: bool = True, scoped_unique: bool = False, zip_name: str | None = None) -> str:
	"""Bundle and export as a ZIP archive containing the HTML and CSS.

	Returns the path to the created ZIP file.
	"""
	# create files
	html_path, css_path = self.bundle(out_dir, name=name, pretty=pretty, minify_css=minify_css, autoprefix_css=autoprefix_css, scoped=scoped, scoped_unique=scoped_unique)
	# archive
	from .bundle import export_zip
	if zip_name is None:
		zip_name = f"{name}.zip"
	zip_path = os.path.join(out_dir, zip_name)
	export_zip(html_path, css_path, zip_path)
	return zip_path


# Attach bundle_export to Tag
Tag.bundle_export = bundle_export


# Attach helper functions as methods on Tag for convenience
Tag._traverse_tags = _tag_traverse
Tag._generate_scope_prefix = _generate_scope_prefix
Tag._apply_scoped_mapping = _apply_scoped_mapping
Tag._restore_scoped_mapping = _restore_scoped_mapping
Tag._collect_rules_for_bundle = _collect_rules_for_bundle
Tag.bundle = bundle


# Minimal demo (runs when module executed directly)
def _demo():
	header = H1("Welcome to JUSU")
	para = P("A tiny HTML builder for beginners.")
	button = Button("Click me", onclick="alert('Hello from JUSU')", cls="btn")
	image = Img(src="https://via.placeholder.com/150", alt="Demo image")
	page = Div(header, para, button, image, cls="container")
	outfile = os.path.join(os.getcwd(), "jusu_demo.html")
	page.render_to_file(outfile)
	print(f"Demo written to {outfile}")


if __name__ == "__main__":
	_demo()

