# AstroState Canonical Specification

## Overview
`AstroState` is a canonical, immutable, and serializable object that represents the comprehensive astrological baseline for a given moment and location under a specific `ConventionProfile`. It is purely calculated and deterministic.

## Schema Concept
```
AstroState
├── input
│   ├── date/time
│   ├── location
│   ├── timezone
│   └── source metadata
├── convention (The ConventionProfile that generated this state)
├── astronomy (Raw planetary positions, speeds, etc.)
├── chart
├── nakshatra
├── vargas
├── dashas
├── strengths (Shadbala, Bhava Bala, etc.)
├── ashtakavarga
├── yogas
├── doshas
├── arudhas
├── karakas
├── sphutas
├── upagrahas
├── special_lagnas
├── transit (Current gochara)
├── panchanga
├── muhurta
├── matching
├── longevity
├── chakras
└── provenance (Graph linking state back to calculations and inputs)
```

## Principle
Every field inside `AstroState` must be traceable to the calculation function and version that produced it. It should never contain outputs from LLMs or methodologies, only absolute mathematical truths based on the selected convention.
