# CI Verification Report

**Date:** 2026-10-13
**Scope:** M1 / Gate 0 package and CI hardening
**Status:** M1 verified locally and by GitHub Actions

## 1. Current workflow

The workflow at `.github/workflows/ci.yml` runs on pushes and pull requests to
`master`/`main` using Python 3.11 and the locked `engine/uv.lock` environment.

It now performs:

1. locked dependency installation with `uv sync --locked --extra dev`;
2. source parsing with `compileall`;
3. blocking Ruff lint checks;
4. blocking Mypy checks for the engine and CLI;
5. wheel build;
6. pytest with package-targeted line and branch coverage;
7. wheel package-boundary inspection;
8. installed dependency verification with `uv pip check`.

Flake8 and non-blocking `--exit-zero` checks were removed. Coverage is configured
in `engine/pyproject.toml` with branch measurement and a combined minimum threshold
of 88%, selected from the clean M1 baseline below. This is an interim Gate 0 floor,
not a claim that later gates have adequate coverage.

## 2. Clean M1 baseline

Baseline commit:

```text
09ddbd33319a9aeb951fb3d21535d7a9cd48d93e
```

The clean baseline was installed with only the declared `.[dev]` dependencies.
No undeclared Astropy dependency was added because the alternate validation modules
are not part of this clean baseline.

Observed before M1 changes:

- 252 tests passed;
- line coverage: 90.76% for `astro_engine`;
- branch coverage: 78.39%;
- Flake8 unavailable because it is not declared;
- Ruff reported six existing Jaimini source issues;
- Mypy reported one existing Jaimini type error;
- the old CI coverage selector produced a no-data report because it targeted `src`
  rather than the importable packages.

## 3. M1 verification target

The M1 gate requires:

- all included Python sources parse;
- the locked environment installs without manual dependencies;
- Ruff and Mypy are blocking and pass;
- the full discovered test suite passes;
- coverage is collected for `astro_engine` with branches enabled; CLI behavior is
  covered by separate process-level smoke tests;
- the configured combined coverage threshold is met;
- the wheel contains only the allow-listed `astro_engine` and `astro_cli` roots;
- the wheel can run the CLI smoke path;
- the README and status documents do not claim missing application/evaluation features
  are already implemented.

## 4. Scope boundary

This report does not mark astronomy correctness, deep immutability, input validation,
method capability enforcement, provenance eligibility, evaluation, security, or
production readiness as verified. Those remain later gates in the implementation plan.

## 5. M1 local result

Using a clean Python 3.11.14 environment and only the locked `.[dev]` dependencies:

- `uv lock --check`: passed;
- source compilation: passed;
- Ruff: passed;
- Mypy: passed (with a non-failing note about the unused `tests.*` override);
- pytest: **257 passed, 1 skipped**;
- combined line/branch coverage: **88.74%**, above the configured 88% floor;
- `uv pip check`: passed;
- wheel build: passed;
- wheel boundary test: **3 passed**;
- installed wheel `astro --version`: passed;
- installed wheel `astro list-methods`: passed;
- `git diff --check`: passed.

The single skipped test is the package-boundary test when no wheel path is supplied;
the same test passed in the explicit wheel-inspection step. The wheel build still
emits a non-blocking setuptools license-table deprecation warning.

The remote GitHub Actions workflow passed for PR #1:

- workflow: `Astro Engine CI`;
- job: `build-and-test`;
- run: `38503332771`;
- job: https://github.com/dogauto/astro-intelligence-os/actions/runs/38503332771/job/115655075217.

M1 is verified for the branch. Merging remains a separate repository action.
