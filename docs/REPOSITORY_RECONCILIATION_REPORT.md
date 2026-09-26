# Repository Reconciliation Report

**Date:** 2026-09-26
**Purpose:** Reconcile the current state of the implementation against previous specifications, progress reports, and roadmaps. Identify discrepancies and classify their resolution status.

## Discrepancies Identified

### 1. Master Specification is Skeleton
- **Discrepancy:** `ASTRO_INTELLIGENCE_OS_MASTER_SPEC.md` is currently an outline/skeleton rather than the authoritative high-level canonical specification.
- **Classification:** **CONFIRMED**
- **Resolution Plan:** Complete overhaul of the Master Spec to make it the single source of truth, delegating deep details to subordinate specs.

### 2. Phase 3 Verification Status Overstated
- **Discrepancy:** The roadmap and progress report marked Phase 3 (Core Professional Calculation Engine) as `VERIFIED`. However, the implementation of `Shadbala` uses simplified placeholders for Kala Bala and Drik Bala.
- **Classification:** **CONFIRMED**
- **Resolution Plan:** Downgrade Phase 3 status to `VERIFIED_SUBSET` across all roadmaps and progress logs.

### 3. Dasha Pratyantar Excluded from Default State
- **Discrepancy:** The `dasha.py` implementation natively supports recursive sub-periods down to Pratyantar, but `builder.py` explicitly skips them to save compute.
- **Classification:** **CONFIRMED**
- **Resolution Plan:** Document Pratyantar as `IMPLEMENTED_BUT_NOT_DEFAULT` in the completeness matrix.

### 4. Method Magnitude Labeled as Confidence
- **Discrepancy:** `VimshottariCareerMethod` and `TransitCareerMethod` output hardcoded heuristic values (e.g. 0.7, 0.8), but previous iterations casually referred to these as confidences or predictions without calibration.
- **Classification:** **CONFIRMED**
- **Resolution Plan:** Magnitudes are now strictly labeled as `HEURISTIC`. They are uncalibrated and forbidden from use in routing weights.

### 5. Automated CI is Missing
- **Discrepancy:** The `build_report.md` claimed 92 tests passing, which was run manually via local `pytest`. There is no automated CI pipeline in the repository.
- **Classification:** **CONFIRMED**
- **Resolution Plan:** Implement GitHub Actions CI workflow to enforce the quality gate.

### 6. Provenance is Elementary
- **Discrepancy:** `ComputationProvenance` exists as a Pydantic model tracking version and ephemeris source, but it lacks the depth required to trace from a final prediction down through hypotheses, rules, and conditions.
- **Classification:** **CONFIRMED**
- **Resolution Plan:** Create `PROVENANCE_SPEC.md` to define a rigorous, hashable tracing mechanism.

### 7. Evaluation Baseline and Security Specifications Missing
- **Discrepancy:** Advanced phases depend on evaluating outcomes and securing personal data (birth time/location), but specifications for these foundational safety/science components don't exist yet.
- **Classification:** **CONFIRMED**
- **Resolution Plan:** Create `OUTCOME_DATA_SPEC.md` and `SECURITY_PRIVACY_SPEC.md`.

---
*Note: All items marked CONFIRMED above are being actively resolved in the current validation audit.*
