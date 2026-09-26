# Astro Intelligence OS - Master Architecture

## 1. Current State
**Assessment Date:** 2026-09-26
**Status:** Greenfield (Empty Repository)

Upon repository inspection, no existing functionality, code, frameworks, or databases exist. The only file present is the foundational `ASTRO_INTELLIGENCE_OS_MASTER_SPEC.md`.

## 2. Target State
We will adopt a modular monorepo structure to isolate the calculation engine from the inference layers and product UIs.

### Conceptual Directory Structure
```
/apps
    /web
    /research-cockpit
    /api
/packages
    /astro-engine
    /astronomy
    /astro-state
    /conventions
    /methods
    /method-sdk
    /ensemble
    /prediction
    /evidence
    /temporal
    /agents
    /evaluation
    /learning
    /knowledge
    /shared
/services
    /calculation
    /method-runner
    /ensemble-runner
    /agent-orchestrator
    /evaluation-worker
/tests
/docs
```

## 3. Pipeline Architecture
The epistemic layers enforce separation of calculated facts, method inferences, ensemble reasoning, and generation:
1. **Astronomy Foundation** (Determinism)
2. **Astrological Calculation Engine** 
3. **Unified AstroState** (Canonical Snapshot)
4. **Method Orchestrator**
5. **Parallel Independent Method Runs**
6. **Prediction Normalizer**
7. **Convergence & Dissent Engine**
8. **Agent Review / Debate**
9. **Temporal Synthesis & Evaluation**

## 4. Technical Risks & Mitigations
- **Risk:** LLM Hallucinations in Calculations.
  **Mitigation:** The system strictly separates Layer 1 (Computed Fact) from Layer 6 (Language Generation). All calculations are deterministic code.
- **Risk:** Contamination across Methodologies.
  **Mitigation:** Methods are executed entirely independently in parallel.

## 5. Migration Strategy
Not applicable at this stage as there is no legacy code.
