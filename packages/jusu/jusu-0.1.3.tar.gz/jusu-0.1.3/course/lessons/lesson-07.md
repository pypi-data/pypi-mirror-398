# Lesson 7 — Testing, Linting & CI

Author: **Francis Jusu**

## Objectives
- Write unit tests for Tag rendering, CSS, and bundle outputs using `pytest`.
- Add basic linting and formatting guidance.
- Create a GitHub Actions workflow that runs tests and builds docs.

## Example test (pytest)
```py
from JUSU import Div

def test_div_renders_basic_html(tmp_path):
    out = tmp_path / 'test.html'
    Div('hi').render_to_file(str(out))
    assert out.exists()
```

## Exercises
- Add tests for a component `Card` ensuring its HTML contains `.card` and the CSS file exists when bundled.
- Add `black` and `flake8` to the dev requirements and a pre-commit config.

Solutions: `course/solutions/lesson-07.md`.
