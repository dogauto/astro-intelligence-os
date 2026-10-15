# Outcome & Evaluation Specification

## Overview
Predictions in the Astro Intelligence OS must be testable. The evaluation engine scores how accurate the methodologies are in retrospect and uses these scores to calibrate future weights.

## Prediction Lifecycle
1. **Prediction:** Event is predicted.
2. **Lock:** The prediction is sealed before the outcome window opens to prevent data leakage.
3. **Outcome:** Real-world outcome is recorded.
4. **Match:** Automated check if the outcome aligns with the prediction.
5. **Evaluate:** Score precision, recall, timing error.
6. **Calibrate:** Update confidence and weighting for the methodologies used.
7. **Update Routing:** Adjust which methods are selected in future queries of this type.

## Evaluation Metrics
- Precision & Recall
- F1 Score
- Timing error (interval overlap)
- False Positives & False Negatives
- Calibration Quality
- Abstention Quality (Knowing when to say "I don't know")
- Robustness
- Method Correlation & Redundancy

## Contextual Weighting
The system does not establish a universal ranking of methodologies. Instead it learns:
`weight = f(method, question_type, domain, time_horizon, chart_context, data_quality, historical_performance)`

## Exploration vs Exploitation
The router maintains an exploration component to randomly test alternative methods, ensuring newer or less common methods have a chance to prove utility over time.
