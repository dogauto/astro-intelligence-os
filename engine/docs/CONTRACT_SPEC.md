# Contract Specification — Astro Intelligence OS

Canonical contracts for QuestionSpec, MethodRun, Prediction, and the
provenance/evidence layer.

---

## 1. Layering

The system has two distinct layers:

| Layer | Purpose | Contract |
|-------|---------|----------|
| **Semantic** | What the prediction *says* | `Prediction`, `MethodRun` |
| **Provenance/Evidence** | Where the prediction *came from* | `ProvenanceRegistry` nodes |

A `Prediction` is a normalized, method-agnostic statement about an event.
It does **not** carry its own calculation or engine version. That
information lives in the provenance chain.

---

## 2. `Prediction` — Semantic Contract

`Prediction` describes the normalized semantic prediction:

- `domain`, `event`, `event_type` — what is being predicted.
- `direction` — positive / negative / neutral / mixed / unknown.
- `magnitude` — intensity 0.0–1.0, if quantifiable.
- `signal_strength` — the method's own heuristic strength.
- `method_id`, `method_version` — which method produced it.
- `provenance_node_id` — reference into the provenance graph.

`signal_strength` is **not** calibrated probability, confidence, or
likelihood. It is a heuristic value preserved from the method's own
output. Consumers must not treat it as a probability.

---

## 3. `calculation_version` — Invariant

### 3.1 Intentional architecture

`calculation_version` is **not** a first-class field of `Prediction`. This
is an architectural decision, not an omission.

The reasoning:

- `Prediction` is the *semantic* layer. It says "career growth is
  likely in Q3 2026".
- The *calculation version* (which engine version, which calculation
  pipeline, which ephemeris) is *provenance* information. It answers
  "how was this computed, and can it be reproduced?"
- Mixing the two layers would couple every semantic statement to a
  specific calculation pipeline, making the semantic contract unstable
  across engine upgrades.
- `Prediction` already carries `method_version`, which identifies the
  method's own version. The engine/calculation version is a separate
  concern tracked at the provenance level.

### 3.2 The invariant

```
Prediction
  └─ provenance_node_id  (reference)
       └─ PredictionNode
            └─ parent_ids
                 └─ MethodRunNode
                      └─ parent_ids
                           └─ AstroStateNode
                                └─ parent_ids
                                     └─ CalculationNode
                                          └─ calculation_name
                                           + version (ProvenanceNode.version)
                                     └─ AstronomyComputationNode
                                          └─ engine_version
                                          └─ ephemeris_source
                                          └─ ephemeris_version
```

The chain is:

```
Prediction → provenance reference → MethodRun / CalculationNode → calculation_version
```

### 3.3 What this guarantees

- **`calculation_version` must not be lost.** Every `Prediction` has a
  `provenance_node_id`. That node is always reachable in the registry.
- **It must be immutable/reproducible through provenance.** The
  `ProvenanceNode.content_hash` is a deterministic SHA-256 of the node's
  content. Two executions with identical inputs produce identical hashes
  and identical version strings.
- **Consumers can recover it.** Starting from
  `prediction.provenance_node_id`, call `registry.trace_prediction(...)`
  and walk the chain to `AstronomyComputationNode.engine_version` and
  `CalculationNode` / `MethodRunNode.version`.
- **`Prediction` does not treat it as probability/confidence/signal
  strength.** The semantic fields (`signal_strength`, `magnitude`,
  `direction`) are independent of the calculation version. A consumer
  comparing two predictions from different engine versions compares
  them through provenance, not through a `Prediction` field.

### 3.4 Verification

The provenance integration tests
(`tests/test_provenance_integration.py`) assert that every prediction
traces through the full chain including `CALCULATION` and
`ASTRONOMY_COMPUTATION` nodes. This guarantees the invariant holds for
both Vimshottari and Gochara methods.

---

## 4. Contracts

### 4.1 QuestionSpec — Canonical Method Input

`QuestionSpec` is the **canonical input** for every `Method`. The abstract
`Method` interface declares:

```python
class Method(ABC):
    @abstractmethod
    def run(self, state: AstroState, question: QuestionSpec, ...) -> MethodRun: ...

    def can_handle(self, question: QuestionSpec) -> bool: ...
```

`QuestionSpec` is:

- **Deterministic** — identical inputs produce identical specs.
- **Serializable** — round-trips through JSON.
- **Hashable/versionable** — a stable SHA-256 `content_hash()` identifies the spec.
- **LLM-independent** — methods receive `QuestionSpec`, not raw natural language.
- **Method-independent** — no reference to any particular astrology method.

### 4.2 QuestionContext — Legacy Compatibility Only

`QuestionContext` is a **legacy compatibility input**, not part of the canonical
method contract. It must **not** appear in the `Method` interface.

Legacy callers convert via the adapter:

```
QuestionContext
       ↓
question_context_to_spec()
       ↓
QuestionSpec
       ↓
Method.run()
```

The adapter is documented as `.. deprecated::` and exists only for backward
compatibility. New code must use `QuestionSpec` directly.

### 4.3 MethodRun

Complete, reproducible record of executing a `Method` against an
`AstroState`. Immutable after execution. Carries `question_id`,
`method_version`, `calculations_used`, `rules_evaluated`, predictions,
assumptions, abstentions, unknowns, and warnings.

### 4.3 Provenance nodes

`BIRTH_INPUT`, `CONVENTION_PROFILE`, `ASTRONOMY_COMPUTATION`, `ASTROSTATE`,
`CALCULATION`, `RULE`, `METHOD_RUN`, `PREDICTION`.

---

## 5. Normalization boundary

```
Method-specific output
  → MethodRun (canonical output contract)
  → Prediction (normalized semantic prediction)
```

`QuestionContext` is deprecated. The adapter
`question_context_to_spec()` is the only supported path for legacy
contexts during the deprecation period.
---

## 7. Multi-Method Executor

The executor is an **orchestration layer only**. It executes multiple
independent methods against the same `QuestionSpec` and `AstroState`, and
collects each method's canonical `MethodRun` into an `ExecutorResult`.

```
QuestionSpec
       ↓
MultiMethodExecutor
       ↓
┌──────────────────────┐
│ Method A             │
│ independent execution│
└──────────────────────┘
       ↓
MethodRun

┌──────────────────────┐
│ Method B             │
│ independent execution│
└──────────────────────┘
       ↓
MethodRun

┌──────────────────────┐
│ Method C             │
│ independent execution│
└──────────────────────┘
       ↓
MethodRun

       ↓
ExecutorResult
```

### 7.1 Invariants

- **Methods execute independently.** Each method receives only the same
  immutable `QuestionSpec` and the same immutable `AstroState`. A method
  cannot observe another method's `Prediction`, `MethodRun`, `signal_strength`,
  or conclusions.
- **Execution independence does not imply evidence independence.** Methods
  may share the same underlying `AstroState`/astronomical signals. The
  executor does not compare or rank predictions.
- **No convergence.** The executor does not merge, aggregate, or vote on
  predictions.
- **No dissent analysis.** The executor does not identify disagreements.
- **No routing.** The caller explicitly supplies the methods; there is no
  contextual method selection.
- **No calibration.** `signal_strength` values are not adjusted.
- **No agents, no ML, no JEPA.**

### 7.2 Execution ordering

Execution ordering is deterministic and matches the input ordering.
Duplicate methods are deduplicated by `method_id`, keeping the first
occurrence.

### 7.3 Failure and abstention semantics

| Status | Meaning |
|--------|---------|
| `SUCCESS` | Method produced a `MethodRun` without abstentions. |
| `ABSTAINED` | Method produced a `MethodRun` with abstention predictions. |
| `FAILED` | Method raised an exception. No prediction is fabricated. |

One method failure does not corrupt successful method results. The
`ExecutorResult` preserves all successful and abstaining `MethodRun`s
and records failures explicitly.

### 7.4 Versioning

- `executor_version` — executor version (`1.0.0`).
- `method_version` — per-method version, preserved from `MethodRun`.
- Calculation/provenance version — preserved through the existing provenance chain.
