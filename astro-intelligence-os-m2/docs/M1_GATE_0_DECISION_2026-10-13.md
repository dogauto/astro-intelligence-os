# M1 / Gate 0 Decision Record

**Date:** 2026-10-13
**Branch:** `plan/m1-gate-0-hardening`
**Baseline:** `09ddbd33319a9aeb951fb3d21535d7a9cd48d93e`
**Decision:** **Pass — local and remote CI evidence complete**

## Scope

M1 establishes a truthful, reproducible package and CI boundary. It does not claim
that astronomy, conventions, deep immutability, input validation, method capability
enforcement, provenance eligibility, evaluation, security, or production readiness
are complete.

## Changes accepted for M1

- Replaced undeclared Flake8 and non-blocking `--exit-zero` checks with blocking Ruff.
- Added locked `uv` dependency resolution and regenerated `engine/uv.lock`.
- Added parse, Ruff, Mypy, test, coverage, wheel-build, package-boundary, and dependency checks to CI.
- Added an explicit allow-list for `astro_engine` and `astro_cli` package discovery and excluded governance names.
- Added CLI and wheel-boundary smoke tests.
- Added installed-wheel CLI smoke checks to CI.
- Added the minimum combined coverage floor of 88%, based on the clean baseline’s 88.79% combined line/branch result before the final M1 test additions.
- Narrowed README claims to the current offline experimental engine and marked application/evaluation layers as planned.
- Repaired only mechanical Ruff/Mypy/type-contract defects in `jaimini_career.py`; no rule behavior or method scope was changed.
- Quarantined governance WIP by keeping it outside the clean M1 baseline/package boundary.
- Ignored generated `engine/build/` output.

## Evidence

The final local verification used Python 3.11.14 in a temporary clean environment:

```text
uv sync --locked --python 3.11 --extra dev       PASS
uv lock --check                                  PASS
python -m compileall -q src tests                PASS
ruff check src/astro_engine src/astro_cli tests  PASS
mypy src/astro_engine src/astro_cli            PASS
pytest + branch coverage                         257 passed, 1 skipped
coverage                                         88.74% combined; floor 88%
uv pip check                                     PASS
wheel build                                      PASS
wheel-boundary tests                             3 passed
installed wheel astro --version                  PASS
installed wheel astro list-methods               PASS
git diff --check                                 PASS
```

## Final conditions

1. Resolve the non-blocking setuptools license-table deprecation warning and the
   repository’s unresolved MIT-versus-Proprietary licensing metadata before a
   distribution release.
2. M2 may begin from a fresh implementation worktree after this decision record
   is reviewed by the release/build owner. M2 remains a separate milestone.

## Remote verification

PR #1: https://github.com/dogauto/astro-intelligence-os/pull/1

- `Astro Engine CI / build-and-test`: passed;
- CodeRabbit review status: passed;
- GitHub Actions run: `38503332771`;
- no merge was performed by this session.

## Explicit non-decisions

- No new astronomy or domain calculations were adopted.
- No Astropy validation extra was added because the clean baseline does not contain
  the alternate validation modules.
- No governance WIP was repaired or included.
- No M2/M3 semantic work was started.
