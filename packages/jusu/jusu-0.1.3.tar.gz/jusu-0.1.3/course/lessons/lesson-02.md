# Lesson 2 — Core concepts: Elements & Attributes

Author: **Francis Jusu**

## Objectives
- Learn about `Tag` / `Element` basics: creating elements, nesting, and text nodes.
- Understand attribute naming, `cls` shorthand, boolean attributes, and ARIA attributes.
- Use comments and minified vs pretty-printed output.

## Example
```py
from JUSU import Div, H2, P, Input, Comment

page = Div(
    H2("About JUSU"),
    P("JUSU makes HTML readable in Python."),
    Comment("This is a generated comment"),
    Input(type="checkbox", checked=True, aria_label="accept"),
    cls="content"
)

print(page.render(pretty=True))
```

## Exercises
- Create a simple form with `Input`, `Label`, and a submit `Button`.
- Add ARIA attributes to the form controls.
- Render the markup with `pretty=False` and compare sizes.

## Hints & Solutions
- Use `cls` for HTML `class` attribute because `class` is a keyword in Python.
- Boolean attributes should be passed as True/False; `True` will render the attribute name only.

See `course/solutions/lesson-02.md` for a reference solution.
