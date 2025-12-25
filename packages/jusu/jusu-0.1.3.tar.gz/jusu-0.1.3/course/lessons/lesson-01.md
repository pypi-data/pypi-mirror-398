# Lesson 1 — Welcome & Setup

Author: **Francis Jusu**

## Objectives
- Install JUSU
- Create your first page using JUSU components
- Render an HTML file and open it in the browser

## Prerequisites
- Python 3.10+
- Basic familiarity with running Python scripts

## Example
Create `hello_jusu.py`:

```py
from JUSU import Div, H1, P, Button, Img

page = Div(
    H1("Welcome to JUSU"),
    P("A tiny HTML builder."),
    Button("Click me", onclick="alert('Hello')", cls="btn"),
    Img(src="https://via.placeholder.com/150", alt="demo"),
    cls="container"
)

page.render_to_file("jusu_demo.html")
```

Run it:
```
python hello_jusu.py
```

Open `jusu_demo.html` in your browser to see the rendered page.

## Exercises
- Modify the page content and add a second image.
- Add a CSS `StyleSheet` to style the `.container` and `.btn` classes.

## Notebook
See the interactive notebook `notebooks/lesson-01.ipynb` for step-by-step guidance and exercises.
