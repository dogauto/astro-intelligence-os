# Astro Intelligence OS — Canonical Master Specification

**Version:** 1.0.0
**Status:** CANONICAL
**Last Audited:** 2026-09-26

## 1. Project Mission
To build a professional-grade, research-oriented astrological intelligence platform. The OS is designed to formally evaluate the efficacy of various astrological methodologies against objective outcomes using a deterministic calculation engine, strict method isolation, and a rigorous provenance chain.

## 2. Non-Negotiable Principles
1. **No LLM in the Calculation Layer:** Astronomical positions, Varga charts, Dasha periods, strengths, and classical rule evaluations MUST be purely deterministic math.
2. **Method Isolation:** Method A cannot observe, depend upon, or mutate the predictions of Method B.
3. **Immutable State:** The `AstroState` object is generated once per query and strictly frozen.
4. **No Hidden Defaults:** Every calculation requires an explicit `ConventionProfile`.
5. **No Probabilities from Heuristics:** Uncalibrated method signals must be labeled as `HEURISTIC` and never disguised as probabilities.
6. **Blinding and Baseline:** Evaluations must minimize leakage and compare against naive/base-rate baselines.

## 3. Epistemic Architecture
The OS separates knowledge into explicit layers:
- **Computed Fact (Layer 1):** Astronomical truth and deterministic calculation (`AstroState`).
- **Methodology Rule (Layer 2):** Fixed classical/modern rules (e.g., Parashari texts).
- **Method Inference (Layer 3):** Isolated deterministic rule evaluation (`MethodRun`).
- **Ensemble Inference (Layer 4):** Orchestration and independent prediction normalization.
- **Convergence Engine (Layer 5):** Conflict resolution, agreement detection, and dissent tracking.
- **Language Generation (Layer 6):** User-facing LLM synthesis.

## 4. Deterministic Calculation Layer & AstroState
The core engine (Python + Swiss Ephemeris) calculates:
- Exact planetary longitudes, speeds, and retrogrades.
- `AstroState`: A canonical, serializable, frozen snapshot of all astrological data (Rasi, Vargas, Dashas, Shadbala, Ashtakavarga, Transits).
*See subordinate specs: `ASTROSTATE_SPEC.md`, `CALCULATION_COMPLETENESS_MATRIX.md`, `ASTRONOMY_VALIDATION_SPEC.md`.*

## 5. ConventionProfile
Every operation requires explicit astronomical and astrological parameters:
- Ayanamsa (e.g., Lahiri, KP, Raman).
- House System (e.g., Placidus, Whole Sign).
- Node Type (True vs. Mean).
*See subordinate specs: `TIME_LOCATION_VALIDATION_SPEC.md`.*

## 6. Method SDK & Method Mastery
Methods are independent execution units implementing the formal SDK.
- **Mastery Levels:** `DRAFT` → `EXPERIMENTAL` → `VALIDATED` → `PRODUCTION` → `DEPRECATED`.
- **MethodRun:** Emits the evaluated rules, intermediate findings, predictions, and exact source `AstroState` ID.
*See subordinate specs: `METHOD_SDK_SPEC.md`.*

## 7. Prediction Normalization & Convergence
- **Normalization:** Predictions are mapped to standard dimensions (Domain, Event, Direction, Timing Window, Duration, Heuristic Magnitude).
- **Convergence:** An orchestrator identifies temporal overlap and mechanism diversity across methods.
- **Dissent:** The engine must actively track and explain *why* methods disagree (mechanism mismatch, timing shift).
*See subordinate specs: `ENSEMBLE_SPEC.md`.*

## 8. Temporal Intelligence
Predictions contain `time_window_start` and `time_window_end`. The OS aims to create first-class `AstroEvent` temporal objects for precise timeline rendering.

## 9. Provenance
Every prediction must carry metadata tracing its exact path from the final output, through the evaluating rule, down to the ephemeris calculation and engine version.
*See subordinate specs: `PROVENANCE_SPEC.md`.*

## 10. Evaluation & Outcomes
Predictions are logged and locked *before* outcomes occur. Outcomes are adjudicated against baselines with strict blinding to method identity where possible.
*See subordinate specs: `EVALUATION_SPEC.md`, `OUTCOME_DATA_SPEC.md`.*

## 11. Security & Privacy
Birth data (exact date, time, location) is highly sensitive. The architecture enforces encryption, strict isolation, rate limits, and audit logs.
*See subordinate specs: `SECURITY_PRIVACY_SPEC.md`.*

## 12. Implementation Roadmap
The development proceeds incrementally, ensuring foundational calculations are proven before methodologies are built, and methodologies are proven before ML/Swarm layers are introduced.
*See subordinate document: `IMPLEMENTATION_ROADMAP.md`.*

## 13. Subordinate Specification Index
- `ASTRONOMY_VALIDATION_SPEC.md`
- `TIME_LOCATION_VALIDATION_SPEC.md`
- `CALCULATION_COMPLETENESS_MATRIX.md`
- `ASTROSTATE_SPEC.md`
- `METHOD_SDK_SPEC.md`
- `PROVENANCE_SPEC.md`
- `ENSEMBLE_SPEC.md`
- `EVALUATION_SPEC.md`
- `OUTCOME_DATA_SPEC.md`
- `SECURITY_PRIVACY_SPEC.md`
- `AGENT_ARCHITECTURE.md`
