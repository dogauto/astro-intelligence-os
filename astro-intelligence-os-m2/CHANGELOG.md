# Changelog

All notable changes to the Astro Intelligence OS will be documented in this file.

## [Unreleased]

### Added
- **Phase 0 (Architecture & Documentation)**
  - Full suite of architectural documentation in `/docs` (MASTER_ARCHITECTURE, IMPLEMENTATION_ROADMAP, ASTROSTATE_SPEC, METHOD_SDK_SPEC, ENSEMBLE_SPEC, AGENT_ARCHITECTURE, EVALUATION_SPEC, DECISION_LOG).
- **Phase 1 (Astronomy Foundation)**
  - `ConventionProfile`: Enforces explicit tracking of ayanamsa, house system, node type, and zodiac logic (e.g. Parashari-Lahiri, KP presets).
  - `AstronomyEngine`: Core wrapper around Swiss Ephemeris for planetary positions, ascendant, houses, and Julian Day conversions.
  - `Nakshatra` module: 27 nakshatras, 4 padas, Vimshottari lords calculation.
  - Initial tests and build fixtures using `uv` and `pytest`.
- **Phase 2 (AstroState)**
  - `AstroState`: Canonical, immutable, serializable representation of all computed astrological data, serving as the Single Source of Truth for methods.
  - `AstroStateBuilder`: Orchestrates the computation of a full AstroState from raw input.
- **Phase 3 (Core Professional Calculation Engine)**
  - `Vargas`: Standard 16 divisional charts (D1-D60) with classical Parashari formulas for Hora, Drekkana, and Trimsamsa.
  - `Vimshottari Dasha`: Full Maha, Antar, and Pratyantar Dasha period computation using the 120-year cycle.
  - `Shadbala`: Initial six-fold strength calculation including Uchcha, Dig, Naisargika, and Cheshta Bala.
  - `Ashtakavarga`: BAV and SAV tables validating the standard 337-bindu invariant.
- **Phase 4 (Method SDK)**
  - Formal `Method` interface enforcing independent execution.
  - Structured output schemas (`MethodRun`, `Prediction`, `QuestionContext`) ensuring LLMs don't become the source of truth for calculation.
- **Phase 5 (First Complete Methodologies)**
  - `Vimshottari Career Timing`: Experimental methodology applying 10 classical Parashari rules to infer career signals without any LLM involvement.
  - `TransitCareerMethod` (Gochara): Second methodology analyzing current transits relative to the natal Moon.
  - Method Isolation: Test suite formally validates that multiple methods can run on the same canonical state without side-effects or inter-method prediction access.
  - End-to-end integration tests validating methodology and ASTRO_STATE pipeline.

### Fixed
- Pydantic v2 `class Config` deprecation warnings by adopting `model_config = ConfigDict(frozen=True)` across all schema definitions.
- Swiss Ephemeris constant `SIDM_YUKTESWAR` corrected to `SIDM_YUKTESHWAR`.
- `swe.houses_ex` zero-index tuple boundary issues.

### Infrastructure
- `uv` set as the primary dependency manager.
- `docker-compose.yml` and `Dockerfile.engine` added for containerized setup (including PostgreSQL + Redis scaffolding).
- API JSON schemas defined for the `ComputeChartRequest` contract.
