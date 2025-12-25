# Lesson 5 — CLI & Local Development

Author: **Francis Jusu**

## Objectives
- Use the `jusu` CLI to bundle and serve components.
- Learn `jusu bundle`, `jusu serve`, `--open`, `--no-block`, and `--run` hooks.
- Set up a local dev workflow that auto-bundles on change.

## Example
```bash
# Bundle a component
jusu bundle mypkg.page:main --out-dir dist --open

# Serve the dist directory
jusu serve dist --open --no-block
```

## Exercises
- Create a small dev script that runs `jusu bundle` after saves (watcher).
- Add a `--run` post-build hook that runs a formatting or test command.

Solutions: `course/solutions/lesson-05.md`.
