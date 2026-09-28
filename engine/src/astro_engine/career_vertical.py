"""Deterministic career vertical slice over existing method contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from astro_engine.executor import ExecutorResult, ExecutorStatus
from astro_engine.methods import MethodRun, Prediction, PredictionDirection

if TYPE_CHECKING:
    from datetime import datetime


class EventRelationship(StrEnum):
    """Factual relationship between method predictions."""

    AGREEMENT = "agreement"
    RELATED = "related"
    CONTRADICTION = "contradiction"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class TimingRelationship(StrEnum):
    """Factual relationship between available prediction windows."""

    OVERLAPPING = "overlapping"
    DIFFERENT = "different"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class NormalizedPrediction:
    """Common view of a canonical Prediction for comparison."""

    method_id: str
    method_version: str
    domain: str
    event: str
    direction: PredictionDirection
    time_window_start: datetime | None
    time_window_end: datetime | None
    duration_description: str | None
    signals: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    contradictory_evidence: tuple[str, ...]
    rules_triggered: tuple[str, ...]
    provenance_node_id: str | None
    is_abstention: bool


@dataclass(frozen=True)
class PredictionRelationship:
    """Structured, non-voting comparison of two method predictions."""

    left_method_id: str
    right_method_id: str
    event_relationship: EventRelationship
    timing_relationship: TimingRelationship


@dataclass(frozen=True)
class CareerComparison:
    """Structured factual comparison of independent method outputs."""

    predictions: tuple[NormalizedPrediction, ...]
    relationships: tuple[PredictionRelationship, ...]
    abstained_methods: tuple[str, ...]
    insufficient_evidence: tuple[str, ...]
    evidence_sources: tuple[str, ...]

    @property
    def has_agreement(self) -> bool:
        return any(
            relationship.event_relationship == EventRelationship.AGREEMENT
            for relationship in self.relationships
        )

    @property
    def has_timing_overlap(self) -> bool:
        return any(
            relationship.timing_relationship == TimingRelationship.OVERLAPPING
            for relationship in self.relationships
        )

    @property
    def has_contradiction(self) -> bool:
        return any(
            relationship.event_relationship == EventRelationship.CONTRADICTION
            for relationship in self.relationships
        )


@dataclass(frozen=True)
class CareerSynthesis:
    """Human-readable result separated by epistemic source."""

    calculated_facts: tuple[str, ...]
    method_interpretations: tuple[str, ...]
    combined_observations: tuple[str, ...]
    uncertainty: tuple[str, ...]
    text: str


def normalize_prediction(run: MethodRun, prediction: Prediction) -> NormalizedPrediction:
    """Normalize one canonical Prediction without changing its meaning."""
    return NormalizedPrediction(
        method_id=run.method_id,
        method_version=run.method_version,
        domain=prediction.domain,
        event=prediction.event,
        direction=prediction.direction,
        time_window_start=prediction.time_window_start,
        time_window_end=prediction.time_window_end,
        duration_description=prediction.duration_description,
        signals=tuple(prediction.supporting_signals + prediction.conditions),
        supporting_evidence=tuple(prediction.supporting_evidence),
        contradictory_evidence=tuple(prediction.contradictory_evidence),
        rules_triggered=tuple(run.rules_evaluated),
        provenance_node_id=prediction.provenance_node_id,
        is_abstention=prediction.is_abstention,
    )


def normalize_executor_result(result: ExecutorResult) -> tuple[NormalizedPrediction, ...]:
    """Normalize all predictions while preserving method boundaries."""
    normalized: list[NormalizedPrediction] = []
    for method_result in result.method_results:
        if method_result.method_run is None:
            continue
        normalized.extend(
            normalize_prediction(method_result.method_run, prediction)
            for prediction in method_result.method_run.predictions
        )
    return tuple(normalized)


def compare_career_results(result: ExecutorResult) -> CareerComparison:
    """Compare independent predictions factually, without aggregation or voting."""
    predictions = normalize_executor_result(result)
    usable = tuple(prediction for prediction in predictions if not prediction.is_abstention)
    abstained_methods = tuple(
        method_result.method_id
        for method_result in result.method_results
        if method_result.status == ExecutorStatus.ABSTAINED
    )
    insufficient: list[str] = []
    if len(usable) < 2:
        insufficient.append("Fewer than two non-abstaining method predictions are available.")

    relationships: list[PredictionRelationship] = []
    for index, left in enumerate(usable):
        for right in usable[index + 1:]:
            relationships.append(
                PredictionRelationship(
                    left_method_id=left.method_id,
                    right_method_id=right.method_id,
                    event_relationship=_event_relationship(left, right),
                    timing_relationship=_timing_relationship(left, right),
                )
            )
            if (
                left.time_window_start is None
                or left.time_window_end is None
                or right.time_window_start is None
                or right.time_window_end is None
            ):
                insufficient.append(
                    f"Timing window unavailable for {left.method_id} or {right.method_id}."
                )

    evidence_sources = tuple(
        sorted({prediction.method_id for prediction in usable})
    )
    return CareerComparison(
        predictions=predictions,
        relationships=tuple(relationships),
        abstained_methods=abstained_methods,
        insufficient_evidence=tuple(dict.fromkeys(insufficient)),
        evidence_sources=evidence_sources,
    )


def synthesize_career_result(comparison: CareerComparison) -> CareerSynthesis:
    """Render a deterministic synthesis from structured comparison facts."""
    calculated_facts = tuple(
        f"{prediction.method_id} produced {prediction.event} ({prediction.direction.value})."
        for prediction in comparison.predictions
        if not prediction.is_abstention
    )
    method_interpretations = tuple(
        f"{prediction.method_id} interpretation: {prediction.event}."
        for prediction in comparison.predictions
        if not prediction.is_abstention
    )
    combined: list[str] = []
    if comparison.has_agreement:
        combined.append("The available method outputs are compatible on the career domain.")
    if comparison.has_timing_overlap:
        combined.append("The available timing windows overlap.")
    if not combined and comparison.evidence_sources:
        combined.append("The methods provide independent career-domain observations.")

    uncertainty = list(comparison.insufficient_evidence)
    uncertainty.extend(
        f"{method_id} abstained and contributed no affirmative prediction."
        for method_id in comparison.abstained_methods
    )
    if comparison.has_contradiction:
        uncertainty.append("The method outputs contain a directional or event contradiction.")

    sections = [
        "Calculated facts:",
        *calculated_facts,
        "Method interpretations:",
        *method_interpretations,
        "Combined observations:",
        *combined,
        "Uncertainty / abstention:",
        *(uncertainty or ("None recorded.",)),
    ]
    return CareerSynthesis(
        calculated_facts=calculated_facts,
        method_interpretations=method_interpretations,
        combined_observations=tuple(combined),
        uncertainty=tuple(uncertainty),
        text="\n".join(sections),
    )


def _event_relationship(
    left: NormalizedPrediction,
    right: NormalizedPrediction,
) -> EventRelationship:
    if left.domain != right.domain:
        return EventRelationship.INSUFFICIENT_EVIDENCE
    if left.event == right.event and left.direction == right.direction:
        return EventRelationship.AGREEMENT
    if left.direction == right.direction:
        return EventRelationship.RELATED
    if {
        left.direction,
        right.direction,
    } <= {PredictionDirection.POSITIVE, PredictionDirection.NEGATIVE}:
        return EventRelationship.CONTRADICTION
    return EventRelationship.RELATED


def _timing_relationship(
    left: NormalizedPrediction,
    right: NormalizedPrediction,
) -> TimingRelationship:
    if (
        left.time_window_start is None
        or left.time_window_end is None
        or right.time_window_start is None
        or right.time_window_end is None
    ):
        return TimingRelationship.UNAVAILABLE
    if (
        left.time_window_start <= right.time_window_end
        and right.time_window_start <= left.time_window_end
    ):
        return TimingRelationship.OVERLAPPING
    return TimingRelationship.DIFFERENT
