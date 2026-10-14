# Astro Engine

Offline deterministic astronomy and astrology calculation engine with an
experimental method-comparison kernel.

## Install

Use the locked development environment from this directory:

```bash
uv sync --locked --extra dev
```

## Run checks

```bash
uv run pytest -v
uv run ruff check src/astro_engine src/astro_cli tests
uv run mypy src/astro_engine src/astro_cli
```

The alternate ephemeris validation modules are not part of the current clean
baseline. Do not install or claim that validation path unless its optional
dependency and fixture policy are adopted explicitly.
