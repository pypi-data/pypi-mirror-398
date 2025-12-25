# Lesson 4 — Components & Bundling

Author: **Francis Jusu**

## Objectives
- Create reusable components (functions/classes returning `Tag` instances).
- Learn scoping via `bundle(scoped=True)` and produce distributable bundles.
- Export ZIP archives with `bundle_export()` for simple distribution.

## Example
```py
from JUSU import Div, H1, P, StyleSheet

def hero(title, subtitle):
    s = StyleSheet()
    s.add_class("hero", {"padding": "2rem", "background": "var(--brand)"})
    return Div(H1(title), P(subtitle), cls="hero", styles=s)

page = hero("Hello", "JUSU component")
page.bundle("dist", name="hero-demo", scoped=True)
```

## Exercises
- Build a `Card` component with a header, body, and footer. Bundle it and open the HTML.
- Export a ZIP of the bundle and inspect its contents.

Solutions: `course/solutions/lesson-04.md`.
