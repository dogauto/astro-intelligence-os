# Calculation Completeness Matrix

**Status Definition:**
- `NOT_IMPLEMENTED`: No code exists.
- `PARTIAL`: Incomplete features, placeholders used. Methodologies must not silently depend on these.
- `EXPERIMENTAL`: Code written, tests pass, but pending strict external validation.
- `VALIDATED`: Completely cross-checked against external references/golden fixtures.
- `PRODUCTION`: Used safely in orchestrations and evaluations.

| Calculation Layer | Status | Implementation | Tests | Reference Validation | Known Limitations / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Astronomy (Core)** | EXPERIMENTAL | `astronomy.py` | `test_astronomy.py` | Pending | Assumes `pyswisseph` correctness. Needs external NASA JPL cross-checks. |
| **D1 / Rasi** | EXPERIMENTAL | `astronomy.py`, Rasi | `test_astronomy.py` | Pending | Fully implemented. |
| **Houses / Cusp** | EXPERIMENTAL | `astronomy.py` | `test_builder_integration`| Pending | Support Placidus/Whole Sign via Swiss Eph. |
| **Nakshatra** | EXPERIMENTAL | `nakshatra.py` | `test_nakshatra.py` | Pending | 27 nakshatras + padas implemented. |
| **Vargas (D1-D60)** | EXPERIMENTAL | `vargas.py` | `test_vargas.py` | Pending | D1-D60 supported. D2/D3/D30 use Parashari non-linear formulas. |
| **Dasha (Maha/Antar)** | EXPERIMENTAL | `dasha.py` | `test_dasha.py` | Pending | Vimshottari 120-year cycle fully implemented for 2 levels. |
| **Dasha (Pratyantar)**| PARTIAL | `dasha.py` | `test_dasha.py` | Pending | Implemented recursively in code but EXCLUDED from default builder to save compute. |
| **Shadbala** | PARTIAL | `shadbala.py` | `test_shadbala.py` | Pending | Kala Bala and Drik Bala use simplified placeholders. Requires sunrise/aspect matrix. |
| **Bhava Bala** | NOT_IMPLEMENTED| None | None | None | - |
| **Ashtakavarga** | EXPERIMENTAL | `ashtakavarga.py` | `test_ashtakavarga.py` | Pending | BAV/SAV computed. 337-bindu invariant validated by internal test. |
| **Transit / Gochara** | EXPERIMENTAL | `builder.py` | `test_method_isolation` | Pending | Computes current planetary positions. Does not yet compute transit vargas/dashas. |
| **Yogas** | NOT_IMPLEMENTED| None | None | None | - |
| **Doshas** | NOT_IMPLEMENTED| None | None | None | - |
| **Panchanga** | NOT_IMPLEMENTED| None | None | None | - |
| **Arudhas** | NOT_IMPLEMENTED| None | None | None | - |
| **Karakas** | NOT_IMPLEMENTED| None | None | None | - |
| **Sphutas** | NOT_IMPLEMENTED| None | None | None | - |
| **Upagrahas** | NOT_IMPLEMENTED| None | None | None | - |
| **Special Lagnas** | NOT_IMPLEMENTED| None | None | None | - |
| **Chakras** | NOT_IMPLEMENTED| None | None | None | - |
| **Longevity** | NOT_IMPLEMENTED| None | None | None | - |
| **Matching** | NOT_IMPLEMENTED| None | None | None | - |

> **CRITICAL RULE:** A methodology may NOT silently depend on a `PARTIAL` calculation without explicitly documenting it as a limitation and raising a warning during the `MethodRun`.
