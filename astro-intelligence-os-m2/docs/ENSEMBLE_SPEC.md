# Multi-Method Ensemble & Convergence Specification

## Overview
The Ensemble Engine orchestrates running multiple methodologies (`MethodRuns`) independently and in parallel to prevent contamination. It aggregates the results and computes convergences and dissents.

## 1. Method Orchestrator
**Role:** Coordinates parallel execution of methods.
**Flow:**
1. Receives `QuestionContext`
2. Identifies applicable methods
3. Selects methods based on maturity and constraints
4. Schedules independent parallel executions
5. Collects `MethodRuns` and normalizes them

## 2. Prediction Normalization
Converts varying method outputs into a standard `Prediction` object:
```
Prediction
├── domain
├── event
├── direction
├── magnitude/intensity
├── time_window
├── duration
├── conditions
├── evidence[]
├── contradictions[]
├── method_id
├── method_version
├── raw_confidence
├── abstention
└── provenance
```

## 3. Convergence Engine
Measures agreement across normalized `Predictions`. Instead of simple majority voting, it measures:
- Event & Direction agreement
- Time-window overlap
- Mechanism diversity (do they arrive at the same conclusion via different rules?)
- Evidence overlap
- Method independence & Abstention behavior

## 4. Dissent Engine
Disagreement is valuable information. Rather than simply throwing out dissenting methods, it aims to answer "Why do they disagree?"
- Checks convention differences
- Checks timing differences
- Investigates shared assumptions vs. distinct mechanisms
- Evaluates sensitivity to birth-time uncertainty
