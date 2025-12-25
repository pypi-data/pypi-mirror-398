# Lesson 3 — Styling with JUSU: StyleSheet & CSS classes

Author: **Francis Jusu**

## Objectives
- Use `StyleSheet` to add classes, variables, and media queries.
- Register styles on components and render CSS files with `render_to_file`.
- Learn minified vs pretty CSS and basic autoprefixing.

## Example
```py
from JUSU import Div, P, StyleSheet

styles = StyleSheet()
styles.add_class("container", {"max-width": "900px", "margin": "0 auto"})
styles.add_variable("--brand", "#007bff")

page = Div(P("Hello styled world"), cls="container")
page.register_css(styles)
page.render_to_file("styled.html", styles=styles)
```

## Exercises
- Build a responsive header using media queries.
- Use CSS variables to implement a theme color switch.

Solutions: see `course/solutions/lesson-03.md`.
