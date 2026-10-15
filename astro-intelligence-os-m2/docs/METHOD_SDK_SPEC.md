# Method SDK Specification

## Overview
The Method SDK defines how astrological algorithms (Rules) operate on a computed `AstroState`. Methods must be purely independent and fully deterministic based on their ruleset, not relying on LLM logic for the astrological inference.

## The Method Interface
```
Method
├── id
├── name
├── version
├── tradition
├── school
├── supported_questions
├── required_calculations
├── convention_profile
├── rules
├── timing_model
├── exceptions
├── limitations
├── tests
└── run(AstroState, QuestionContext) -> MethodRun
```

### Method Mastery Lifecycle
1. DRAFT
2. EXPERIMENTAL
3. VALIDATED
4. PRODUCTION
5. DEPRECATED

## The MethodRun Output
Every time a `Method` executes, it returns a canonical, reproducible `MethodRun` object:
```
MethodRun
├── run_id
├── method_id
├── method_version
├── input_state_hash
├── question
├── context
├── calculations_used
├── rules_evaluated
├── intermediate_findings
├── candidate_events
├── timing_windows
├── predictions (Normalized Predictions)
├── supporting_evidence
├── contradictory_evidence
├── assumptions
├── abstentions
├── warnings
└── provenance
```
