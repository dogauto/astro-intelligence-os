# Phase 0–4 Validation Report

**Status:** CANONICAL
**Date:** 2026-09-26

This report validates the foundational architecture and calculation capabilities of the engine. A subsystem is only marked `VERIFIED` if implementation, passing tests, and no critical placeholders exist.

| Subsystem | Requirement | Implementation Location | Test Location | Result / Coverage | Reference Validation | Known Limitation | Production Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Astronomy Core** | Geo-apparent positions | `astronomy.py` | `test_astronomy.py` | PASSED | Pending JPL check | Depends on `pyswisseph` | **VERIFIED_SUBSET** |
| **ConventionProfile**| Explicit configuration | `conventions.py` | `test_conventions.py` | PASSED | N/A | None | **VERIFIED** |
| **AstroState** | Immutable canon data | `state.py`, `builder.py` | `test_builder_integration.py` | PASSED | N/A | None | **VERIFIED** |
| **Vargas** | D1-D60 divisionals | `vargas.py` | `test_vargas.py` | PASSED | Pending JH check | D2/D3 Parashari only | **VERIFIED** |
| **Dasha** | Vimshottari cycles | `dasha.py` | `test_dasha.py` | PASSED | Pending JH check | Pratyantar skipped in builder | **VERIFIED_SUBSET** |
| **Shadbala** | 6-fold planetary strength | `shadbala.py` | `test_shadbala.py` | PASSED | Pending JH check | Kala/Drik use placeholders | **PARTIAL** |
| **Ashtakavarga** | BAV/SAV totals | `ashtakavarga.py` | `test_ashtakavarga.py` | PASSED | Internal 337-invariant | None | **VERIFIED** |
| **Method SDK** | Independent execution | `methods/__init__.py` | `test_method_isolation.py`| PASSED | N/A | None | **VERIFIED** |

## Notes
- Phase 3 overall status is `VERIFIED_SUBSET` because `Shadbala` and `Pratyantar Dasha` are currently partial or excluded. 
- No methodology may blindly consume `Shadbala` as if it were complete. The `capabilities.py` matrix now enforces this.
