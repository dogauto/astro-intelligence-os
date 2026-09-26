# Agent Architecture Specification

## Overview
AI Agents in Astro Intelligence OS act as an implementation workforce and analytical Parliament. They operate on strict tool-restricted policies and do NOT have the authority to invent astrological calculations. 

## Agent Parliament
A collection of specialized agents running in a structured debate/review format:
1. **Planner Agent:** Coordinates complex research flows.
2. **Methodologist Agent:** Validates if methods were applied correctly and correctly models new rules.
3. **Analyst Agent:** Reviews ensemble outputs.
4. **Timing Agent:** Synthesizes time windows from multiple sources.
5. **Contradiction Hunter:** Focuses exclusively on finding weak points in convergences.
6. **Skeptic:** Generates counterarguments against primary predictions.
7. **Data Auditor:** Validates `AstroState` and checks input quality.
8. **Research/Historian Agent:** Grounds analysis in classical texts and historical examples.
9. **Ensemble Analyst:** Evaluates convergence metrics.
10. **Synthesizer:** Turns structured ensemble output into readable language for the user.

## Tool Policy
- Agents receive highly restrictive toolsets tailored to their purpose.
- e.g. Data Auditor can only read `AstroState` and report problems.
- e.g. Skeptic can read predictions and evidence, and search contradictions.
- Agents MUST NOT modify calculation source code silently without human review gates.
