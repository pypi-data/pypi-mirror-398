"""Simple CSS builder for JUSU

Provides a small, dependency-free StyleSheet class that can collect class
rules, media queries and render to a .css file. The API is intentionally
compact to keep the surface area minimal for the MVP.
"""
from __future__ import annotations

from typing import Dict, Any, List


def _prop_name(prop: str) -> str:
    # allow python-style names like "font_weight" -> "font-weight"
    return prop.replace("_", "-")


class StyleSheet:
    def __init__(self) -> None:
        self.classes: Dict[str, Dict[str, Any]] = {}
        self.media: List[tuple[str, Dict[str, Dict[str, Any]]]] = []
        self.vars: Dict[str, str] = {}
        self._autoprefixers: List[callable] = []

    def add_autoprefixer(self, fn: callable) -> "StyleSheet":
        """Register a custom autoprefixer function.

        The function should accept a props dict and return a list of (prop, value)
        tuples to be included in the final rule.
        """
        self._autoprefixers.append(fn)
        return self
    def add_class(self, name: str, props: Dict[str, Any]) -> "StyleSheet":
        self.classes[name] = props
        return self

    def add_media_query(self, query: str, rules: Dict[str, Dict[str, Any]]) -> "StyleSheet":
        self.media.append((query, rules))
        return self

    def add_variable(self, name: str, value: str) -> "StyleSheet":
        # name without leading '--'
        self.vars[name.lstrip("-")] = value
        return self

    def _apply_autoprefix(self, props: Dict[str, Any]) -> List[tuple[str, Any]]:
        # Simple autoprefixer mapping for common properties
        prefix_map = {
            "user-select": ["-webkit-user-select", "-ms-user-select"],
            "appearance": ["-webkit-appearance", "-moz-appearance"],
            "transform": ["-webkit-transform"],
            "box-shadow": ["-webkit-box-shadow"],
        }
        out: List[tuple[str, Any]] = []
        for k, v in props.items():
            key = _prop_name(k)
            if key == "display" and str(v).strip() == "flex":
                # older flexbox fallbacks
                out.append(("display", "-webkit-box"))
                out.append(("display", "-ms-flexbox"))
            if key in prefix_map:
                for pref in prefix_map[key]:
                    out.append((pref, v))
            out.append((key, v))
        # Run user-provided autoprefixers
        for fn in getattr(self, "_autoprefixers", []):
            try:
                extra = fn(props)
                if extra:
                    out.extend(extra)
            except Exception:
                # ensure autoprefixers don't break render
                pass
        return out

    def render(self, pretty: bool = True, minify: bool = False, autoprefix: bool = False) -> str:
        nl = "\n" if pretty and not minify else ""
        indent = "  " if pretty and not minify else ""
        parts: List[str] = []
        # CSS variables
        if self.vars:
            parts.append(f":root {{{nl}")
            for k, v in self.vars.items():
                parts.append(f"{indent}--{k}: {v};{nl}")
            parts.append(f"}}{nl}")

        for cls, props in self.classes.items():
            parts.append(f".{cls} {{{nl}")
            entries = (
                self._apply_autoprefix(props) if autoprefix else [( _prop_name(k), v) for k, v in props.items()]
            )
            for k, v in entries:
                parts.append(f"{indent}{k}: {v};{nl}")
            parts.append(f"}}{nl}")

        for query, rules in self.media:
            parts.append(f"@media {query} {{{nl}")
            for cls, props in rules.items():
                parts.append(f"{indent}.{cls} {{{nl}")
                entries = (
                    self._apply_autoprefix(props) if autoprefix else [( _prop_name(k), v) for k, v in props.items()]
                )
                for k, v in entries:
                    parts.append(f"{indent}{indent}{k}: {v};{nl}")
                parts.append(f"{indent}}}{nl}")
            parts.append(f"}}{nl}")

        css = "".join(parts)
        if minify:
            # Rudimentary minify: strip newlines and extra spaces
            css = css.replace("\n", "").replace("  ", "")
        return css

    def write(self, filename: str, pretty: bool = True, minify: bool = False, autoprefix: bool = False) -> None:
        content = self.render(pretty=pretty, minify=minify, autoprefix=autoprefix)
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(content)
