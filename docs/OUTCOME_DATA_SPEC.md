# Outcome Data Specification

**Version:** 1.0.0
**Status:** CANONICAL

## 1. Objective
To define a rigorous standard for collecting, adjudicating, and storing real-world outcomes against which astrological predictions will be evaluated.

## 2. The Core Problem
An outcome is not automatically "ground truth" just because a user reports it. Human memory is fallible, reporting is subject to bias, and astrological phenomena are often subjective.

## 3. Required Metadata
Every `OutcomeEvent` must record:
- **Source Type:** Self-reported, verified public record, third-party observer, API integration (e.g. LinkedIn for jobs).
- **Outcome Provenance:** URI, document reference, or cryptographic signature of the source.
- **Timestamp of Occurrence:** The exact or bounded time window when the event occurred.
- **Timestamp of Record:** When it was added to the OS.
- **Evidence:** Textual, categorical, or binary evidence (e.g., "Signed offer letter on Oct 1").

## 4. Bias Mitigation
The evaluation pipeline must explicitly account for:
- **Reporting Bias:** Users are more likely to report dramatic events.
- **Selection Bias:** The user base may skew toward individuals seeking guidance.
- **Survivorship Bias:** Methods that predict early death cannot be easily backtested on a living user base.
- **Leakage:** The system must cryptographically lock predictions *before* the outcome is adjudicated.

## 5. Adjudication & Blinding
- Generating predictions and adjudicating outcomes must be two separate, isolated steps.
- The outcome adjudicator (whether human or LLM) MUST be blinded to the methodology that generated the prediction.

## 6. Baselines
Every evaluation run must compare method performance against:
1. **Base Rate Baseline:** The historical probability of the event occurring randomly.
2. **No-Change Baseline:** The assumption that tomorrow will be the same as today.
3. **Naive Temporal Baseline:** e.g., "Most people get promoted in Q1."
