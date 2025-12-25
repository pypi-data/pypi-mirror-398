# Lesson 6 — Interactivity & Minimal JS helpers

Author: **Francis Jusu**

## Objectives
- Learn how small JS helpers can add interactivity without heavy tooling.
- Embed scripts or link to the `jusu-assets` npm package if you published it.

## Example
```py
from JUSU import Div, Button

page = Div(Button('Toggle', onclick="toggleClass(document.querySelector('.box'), 'hidden')"), cls='container')
page.render_to_file('interactive.html')
```

## Exercises
- Add a JS file that toggles dark mode using a CSS variable.
- Package the JS in `package_assets/js/` and import it in the bundled HTML.

Solutions: `course/solutions/lesson-06.md`.
