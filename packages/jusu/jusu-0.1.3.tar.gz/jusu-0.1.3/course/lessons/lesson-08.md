# Lesson 8 — Internals & Extending JUSU

Author: **Francis Jusu**

## Objectives
- Understand the architecture of JUSU: `Tag` model, `StyleSheet`, bundling logic, CLI helpers.
- Learn how to extend the library: add an autoprefixer, register an engine, or add a new semantic tag.

## Internals overview
- `JUSU/core.py` — `Tag` and class hierarchy; rendering, attribute normalization, bundling helpers.
- `JUSU/css.py` — `StyleSheet`, rules, variables, media queries, and autoprefixer registry.
- `JUSU/cli.py` — CLI glue, `bundle`, `serve`, and engine/run hooks.

## Exercises
- Add a small extension that registers a custom autoprefixer to the `StyleSheet` instance.
- Contribute a new semantic tag (e.g., `Figure`/`Figcaption`) with tests.

Solutions: `course/solutions/lesson-08.md`.
