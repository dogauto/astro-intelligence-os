# Decision Log

This document records the architectural and technical decisions made during the lifecycle of the Astro Intelligence OS.

## 2026-09-26 - Initial Repository Architecture Setup
**Context:**
The repository was completely empty except for the `ASTRO_INTELLIGENCE_OS_MASTER_SPEC.md`. Following Phase 0 instructions, we needed to establish the target state.

**Decision:**
- Adopted a modular monorepo structure.
- Separated `apps` (UI/API) from `packages` (calculation, state, methods) from `services` (runners, orchestrators).
- Generated formal specifications (`ASTROSTATE_SPEC.md`, `METHOD_SDK_SPEC.md`, `ENSEMBLE_SPEC.md`, `AGENT_ARCHITECTURE.md`, `EVALUATION_SPEC.md`, `IMPLEMENTATION_ROADMAP.md`, `MASTER_ARCHITECTURE.md`) derived directly from the Master Spec.

This structure aligns with the bottom-up development philosophy and ensures the calculation engine remains entirely decoupled from LLMs and Methodologies. It provides a clean slate for introducing strict tests and deterministic astronomy logic as Phase 1 begins.

## 2026-09-26 - Method Isolation and Independence
**Context:**
Moving into Phase 5, multiple methodologies (e.g., Vimshottari Career Timing and Gochara Transit) need to be implemented. The Convergence Engine (Phase 7) is not yet built.

**Decision:**
- Enforced strict method isolation: Method A cannot see Method B's predictions, and vice versa.
- Transit calculation is treated as a deterministic engine function added to the initial state build (`AstroState.transit`), ensuring methods remain pure functions consuming canonical data, not calling astronomical functions themselves.
- A dedicated `test_method_isolation.py` test suite was created to formally validate this independence.

**Justification:**
This prevents premature convergence or cross-pollution of predictions, aligning with the architectural requirement that methods must execute independently before an orchestrator or ensemble layer aggregates their results.
