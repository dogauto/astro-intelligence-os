# ⚙️ Astro Intelligence OS

> A professional-grade, research-oriented astrology platform — deterministic calculations, isolated methodology execution, and rigorous outcome evaluation.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![Node.js](https://img.shields.io/badge/node-18%2B-green.svg)](https://nodejs.org)
[![Tests](https://img.shields.io/badge/tests-92%20passed-brightgreen.svg)]()
[![Status](https://img.shields.io/badge/status-Phase%205%20IN_PROGRESS-orange.svg)]()

---

## 🌟 What Is This?

**Astro Intelligence OS** is a hybrid astronomical-astrological computation engine. It separates what can be **calculated with certainty** (planetary positions, dashas, vargas, nakshatras) from what must be **evaluated empirically** (method predictions vs. outcomes).

Think of it as a **scientific instrument** for astrology research — not a horoscope app, not a belief system, but a rigorous testing framework.

### The Core Insight

| Layer | What It Does | How It Works |
|-------|-------------|-------------|
| **Layer 1 — Astronomy** | Computes exact planetary positions | Deterministic math via Swiss Ephemeris |
| **Layer 2 — Methodology** | Applies classical/modern rules | Isolated, auditable rule engines |
| **Layer 3 — Convergence** | Resolves disagreements between methods | Statistical analysis, dissent tracking |
| **Layer 4 — Evaluation** | Measures prediction accuracy | Blinded against actual outcomes |
| **Layer 5 — LLM Synthesis** | Generates human-readable reports | Only at the final layer, never in calculation |

---

## 🔬 Why Does This Exist?

Most astrology software:
- Gives you a chart reading with no provenance
- Can't tell you *why* a prediction was made
- Has no way to verify if it was correct
- Mixes calculation with belief

**Astro Intelligence OS** is different because:

1. **No LLM in the calculation layer** — astronomical positions are pure math
2. **Method isolation** — Parashari cannot leak information into Jaimini results
3. **Immutable state** — `AstroState` is frozen once generated; no hidden mutations
4. **Full provenance** — every prediction traces back to exact ephemeris calculations
5. **Empirical evaluation** — predictions are logged before outcomes; accuracy is measured honestly

---

## 🏗️ Architecture

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
- **AstroState** — immutable, serializable chart snapshot
- **ConventionProfile** — explicit ayanamsa/house system selection
- **Method SDK** — isolated execution framework
- **Provenance Tracking** — full audit trail for every prediction

### TypeScript Apps (`/apps`)
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
- Node.js 18+
- Docker (optional, for sandboxed execution)

### Install

```bash
# Clone the repo
git clone https://github.com/dogauto/astro-intelligence-os.git
cd "astro-intelligence-os"

# Python engine
cd engine && pip install -e ".[dev]"

# TypeScript apps
cd ../apps/api && npm install && npm run dev
```

### Run Tests

```bash
# Python
cd engine && pytest -v

# TypeScript
cd apps/api && npm test
```

---

## 🎯 Current Status

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 0** | Architecture documentation | ✅ VERIFIED |
| **Phase 1** | Astronomy engine, ConventionProfile | ✅ VERIFIED |
| **Phase 2** | AstroState builder, immutability | ✅ VERIFIED |
| **Phase 3** | Core calculations (Vargas, Dasha, Shadbala) | ✅ VERIFIED_SUBSET |
| **Phase 4** | Method SDK, isolation enforcement | ✅ VERIFIED |
| **Phase 5** | First complete methodologies | 🔄 IN_PROGRESS |
| **Phase 6** | Convergence engine | 📋 SPECIFIED |
| **Phase 7** | LLM synthesis layer | 📋 PLANNED |
| **Phase 8** | Evaluation framework | 📋 PLANNED |

**Latest Commit:** Gate 8 provenance + multi-method execution + Jaimini career methods

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

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Swiss Ephemeris for astronomical calculations
- Parashari and Jaimini classical text traditions
- The scientific method for epistemic rigor

---

**Built with rigor. Evaluated with honesty.**
