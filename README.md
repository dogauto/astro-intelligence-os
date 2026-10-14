# ⚙️ Astro Intelligence OS

> An offline deterministic astrology calculation engine with an experimental, career-specific method-comparison kernel.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![Tests](https://img.shields.io/badge/tests-automated-brightgreen.svg)](https://github.com/dogauto/astro-intelligence-os/actions/workflows/ci.yml)
[![Status](https://img.shields.io/badge/status-M1%20GATE%200%20VERIFIED-brightgreen.svg)](https://github.com/dogauto/astro-intelligence-os/actions/workflows/ci.yml)

---

## 🌟 What Is This?

**Astro Intelligence OS** is an offline astronomical-astrological computation engine. It separates deterministic calculation paths from experimental methodology outputs that still require independent validation and outcome evaluation.

Think of the current release as an **experimental research kernel** for astrology software — not a horoscope app, not a production platform, and not evidence that any astrological method is effective.

### The Core Insight

| Layer | What It Does | How It Works |
|-------|-------------|-------------|
| **Layer 1 — Astronomy** | Computes supported planetary positions | Deterministic math via Swiss Ephemeris; validation is per calculation |
| **Layer 2 — Methodology** | Applies experimental rules | Isolated method interfaces with explicit maturity and limitations |
| **Layer 3 — Convergence** | Compares disagreements between methods | Planned; no general convergence engine is implemented |
| **Layer 4 — Evaluation** | Measures prediction behavior | Planned; no predictive-efficacy claim is made |
| **Layer 5 — LLM Synthesis** | Generates human-readable reports | Planned downstream layer; never part of calculation |

---

## 🔬 Why Does This Exist?

Most astrology software:
- Gives you a chart reading with no provenance
- Can't tell you *why* a prediction was made
- Has no way to verify if it was correct
- Mixes calculation with belief

The design direction is different because it aims to make these boundaries explicit:

1. **No LLM in the calculation layer** — astronomical positions are pure math
2. **Method isolation** — Parashari must not leak information into Jaimini results
3. **Immutable state target** — `AstroState` is intended to be frozen once generated; deep immutability is a later gate
4. **Provenance target** — auditable predictions must trace to their inputs and ephemeris; mandatory eligibility is a later gate
5. **Empirical evaluation target** — predictions must be locked before outcomes; the evaluation subsystem is not yet implemented

---

## 🏗️ Architecture

The following is the long-term target architecture. The current checkout implements
the Python engine and experimental method layer; convergence, evaluation, UI, and
LLM synthesis remain planned gates.

```
┌─────────────────────────────────────────────────────────────┐
│                    Astro Intelligence OS                     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Astronomy   │  │  AstroState  │  │  Method SDK      │  │
│  │  Engine      │──▶  Builder     │──▶  (Parashari,     │  │
│  │  (Swiss      │  │  (frozen,    │  │   Jaimini, etc.) │  │
│  │  Ephemeris)  │  │  serializable)│  │                  │  │
│  └──────────────┘  └──────────────┘  └────────┬─────────┘  │
│                                                │             │
│                              ┌─────────────────▼──────────┐  │
│                              │   Convergence Engine       │  │
│                              │  (conflict resolution,     │  │
│                              │   dissent tracking)        │  │
│                              └────────────┬───────────────┘  │
│                                           │                  │
│                      ┌────────────────────▼───────────────┐  │
│                      │      Language Generation Layer      │  │
│                      │    (LLM synthesis, reports, UI)     │  │
│                      └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 What's Inside

### Python Engine (`/engine`)
- **AstronomyEngine** — wrapper around Swiss Ephemeris
- **AstroState** — serializable chart snapshot; deep immutability is a later gate
- **ConventionProfile** — explicit ayanamsa/house system selection
- **Method SDK** — experimental isolated execution framework
- **Provenance Tracking** — provenance primitives; auditable eligibility is a later gate

### Planned product surfaces (not in this checkout)
- **API Server** — REST/GraphQL interface
- **Web UI** — interactive chart viewer
- **Research Cockpit** — evaluation dashboard

### Shared Contracts (`/contracts`)
- Versioned API schemas (JSON Schema)
- Cross-language type safety

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- `uv` 0.9+

Node.js and Docker are not required for the current offline engine boundary.

### Install

```bash
# Clone the repo
git clone https://github.com/dogauto/astro-intelligence-os.git
cd "astro-intelligence-os"

# Python engine (locked environment)
cd engine && uv sync --locked --extra dev
```

### Run Tests

```bash
# Python
cd engine && uv run pytest -v
```

---

## 🎯 Current Status

The current supported claim is:

> **An offline deterministic astrology calculation engine with an experimental, career-specific method-comparison kernel.**

| Milestone | Description | Status |
|-----------|-------------|--------|
| **M1 / Gate 0** | Reproducible package boundary and truthful CI | ✅ VERIFIED |
| **M2+** | Subsequent correctness, provenance, evaluation, and security gates | 📋 NOT_STARTED |

Later gates remain planned until their current executable checks and evidence are complete.

---

## 🛡️ Non-Negotiable Principles

These are hard constraints, not guidelines:

1. **No LLM in Calculation** — Astronomical positions must be deterministic math
2. **Method Isolation** — Methods cannot observe or mutate each other's predictions
3. **Immutable State** — AstroState is generated once, then frozen
4. **No Hidden Defaults** — Every operation requires explicit ConventionProfile
5. **No Fake Probabilities** — Uncalibrated signals labeled `HEURISTIC`
6. **Blinding & Baselines** — Evaluations minimize leakage vs naive baselines

---

## 📚 Documentation

- [Master Specification](ASTRO_INTELLIGENCE_OS_MASTER_SPEC.md) — canonical design doc
- [Architecture Docs](docs/) — detailed technical specs
- [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md) — phase-by-phase plan
- [Progress Tracking](PROJECT_PROGRESS.md) — milestone log

---

## 🤝 Contributing

This is a research project. Contributions welcome in:
- New methodology implementations
- Test fixtures and validation data
- Documentation and specification clarity
- Performance optimization

Contribution guidelines will be published with the release boundary.

---

## 📄 License

The repository metadata is currently inconsistent: no root `LICENSE` file is present,
while the engine package metadata declares `Proprietary`. Resolve this before any
distribution release; this M1 branch does not make a new licensing decision.

---

## 🙏 Acknowledgments

- Swiss Ephemeris for astronomical calculations
- Parashari and Jaimini classical text traditions
- The scientific method for epistemic rigor

---

**Built with rigor. Evaluated with honesty.**
