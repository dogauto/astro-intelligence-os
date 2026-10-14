# Astro Intelligence OS — Master Architecture

## 1. Current implementation state

**Assessment date:** 2026-10-13
**Status:** M1 / Gate 0 local pass; remote CI pending

The current release boundary is a modular Python engine:

- `engine/src/astro_engine/` contains the Swiss Ephemeris-backed calculation
  core, state models, conventions, method SDK, provenance primitives, and the
  experimental career-comparison slice.
- `engine/src/astro_cli/` contains the current command-line adapter.
- `contracts/` contains shared request-schema material.
- No `/apps`, `/packages`, or `/services` implementation is present in this
  checkout.
- Governance/control-plane WIP is quarantined from the product package.

### Current M1 evidence

In a clean Python 3.11.14 environment using only the locked development
dependencies:

- 257 tests passed and 1 package-boundary test was skipped when no wheel path
  was supplied;
- combined line/branch coverage was 88.74%, above the configured 88% floor;
- Ruff and Mypy passed;
- the wheel contained only `astro_cli` and `astro_engine`;
- the installed wheel passed `astro --version` and `astro list-methods` smoke
  checks.

The GitHub Actions workflow has not yet run for this branch, so M1 remains
conditionally open until the remote result is green.

### Maturity boundary

The following are not asserted as complete by this document:

- deep immutability of nested state values;
- complete input/timezone validation;
- full Swiss Ephemeris convention isolation under concurrency;
- independent validation of every calculation or named rule;
- executor capability enforcement;
- mandatory provenance eligibility;
- locked/blinded outcome evaluation;
- production security or multi-user deployment.

These are later gates. Local test counts do not promote them to verified status.

## 2. Target architecture

The target for the next delivery cycle is a **modular Python monolith**, not a
microservice fleet:

```text
validated request
    -> convention resolver
    -> AstronomyEngine
    -> AstroStateBuilder
    -> immutable AstroState
    -> isolated method execution
    -> MethodRun records
    -> provenance validation
    -> bounded comparison kernel
    -> locked evaluation artifacts
```

API, UI, storage, and language synthesis are future application boundaries.
They must not be added until the deterministic kernel and research contracts
pass their gates.

## 3. Pipeline responsibilities

1. **Boundary validation** — reject malformed datetime, timezone, and location
   inputs before astronomy.
2. **Astronomy foundation** — calculate supported bodies under an explicit
   ephemeris and convention policy.
3. **Astrological calculations** — expose each calculation with an explicit
   maturity, dependency, and limitation status.
4. **Canonical state** — produce a serializable, deeply immutable snapshot with
   stable identity.
5. **Method SDK** — run one method against one state and question without
   access to sibling predictions.
6. **Executor** — enforce question and capability preconditions and preserve
   `SUCCESS`, `ABSTAINED`, and `FAILED` outcomes.
7. **Comparison kernel** — report factual relationships and dissent without
   silently voting, ranking, or turning heuristics into probabilities.
8. **Provenance** — require a complete trace for research-eligible output.
9. **Evaluation** — lock predictions before outcomes and compare against
   predeclared baselines only after the provenance gate passes.

## 4. Architectural risks and controls

| Risk | Required control |
|---|---|
| Global Swiss Ephemeris convention state | Protect the complete convention-sensitive operation; prove mixed-profile results against serial references |
| Nested mutable state | Use a deep immutable representation or explicit copy-on-write and test hash stability |
| Unsupported or partial calculations | Enforce a machine-readable capability catalog before method execution |
| Missing or colliding provenance | Use deterministic, prediction-specific identities and fail closed for auditable output |
| Evaluation leakage | Seal predictions before outcomes and blind method identity during adjudication |
| Real birth-data exposure | Keep the current boundary synthetic/public and offline until the security gate is implemented |
| Architecture overreach | Keep the engine in one process until measurements justify another boundary |

## 5. Migration strategy

1. Preserve the current dirty audit checkout as evidence; implement in a clean
   worktree.
2. Adopt or park existing WIP clusters as units; do not cherry-pick generated
   metadata or individual coupled calculation files.
3. Preserve public method IDs and historical state artifacts through versioned
   adapters; never silently reinterpret old records.
4. Use fixed fixtures to compare old and hardened behavior, and record
   intentional changes such as newly rejected invalid inputs.
5. Add an application wrapper only after the kernel passes the relevant
   evaluation and security gates. Do not split the calculation core into
   services without measured need.
