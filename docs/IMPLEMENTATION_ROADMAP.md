# Implementation Roadmap

The development of the Astro Intelligence OS will proceed iteratively. We prioritize mastering a few methods over building thousands of shallow methods simultaneously.

## [VERIFIED] Phase 0: Repository Discovery & Architecture
- [x] Inspect the repository.
- [x] Establish target architecture.
- [x] Create architectural documentation (Schemas, SDK specs, Roadmaps).

## [VERIFIED] Phase 1: Astronomy Foundation
- [x] Build robust astronomy abstraction.
- [x] Include ephemeris, planetary positions, speeds, time conversion, Julian date handling, exact birth-moment handling, and ayanamsa abstraction.
- [x] Create `ConventionProfile`.

## [VERIFIED] Phase 2: AstroState
- [x] Create a canonical immutable/serializable `AstroState` object.

## [VERIFIED] Phase 3: Core Professional Calculation Engine
- [x] D1/Rasi, houses, ascendant, nakshatra.
- [x] Extended vargas, dashas, strengths, yogas, doshas, transit systems, panchanga.
- [x] Driven by test fixtures and proven reproducibility.

## [VERIFIED] Phase 4: Method SDK
- [x] Formalize `Method` interface and `MethodRun` output format.

## [IN_PROGRESS] Phase 5: First 2–3 Complete Methodologies
- [x] Implement Vimshottari Career Timing method.
- [ ] Implement 1-2 more distinct methodologies.
- [x] Ensure calculation dependencies, tests, timing behavior, limitations, and provenance are covered.

## Phase 6: Parallel Multi-Method Execution
- Question compiler, method routing, and orchestrator built to scale parallel independent method executions.

## Phase 7: Convergence + Dissent
- Normalize predictions.
- Build engine to identify agreement, timing overlaps, mechanism diversity, and meaningful disagreements.

## Phase 8: Evidence Graph
- Map relationships from prediction down to calculation and textual rules.

## Phase 9: Agent Layer
- Implement specialized, tool-restricted agents (Methodologist, Data Auditor, Skeptic, etc.).

## Phase 10: Temporal Intelligence
- Create first-class `AstroEvent` temporal objects.

## Phase 11: Outcome/Evaluation
- Implement lock mechanisms for predictions before outcomes. Match, evaluate, and calibrate using rigorous test splits.

## Phase 12: Contextual Routing/Weights
- Learn how methods perform by task and context rather than universal ranking.

## Phase 13: Professional Research Cockpit
- Build internal UI for inspecting runs, comparing methods, visualizing convergence/dissent, and experimenting.

## Phase 14: Advanced ML Research
- Introduce JEPA-like architectures or predictive encoders. Compare against deterministic baselines.
