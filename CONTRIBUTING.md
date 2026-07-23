# Contributing

Follows the shared aleonard.us SDLC — see
[`SDLC.md`](https://github.com/ALeonard9/druthers-api/blob/main/SDLC.md) (canonical).

- **Branches**: `main` is protected. Use `feat/…`, `fix/…`, `chore/…`; open a PR;
  merge on green CI (squash).
- **Before pushing**: `task lint && task format && task test`.
- **Pre-commit**: `pre-commit install` runs black + pylint + pytest on commit.
- Strings are single-quoted (black `--skip-string-normalization`); modules and
  functions have docstrings.
