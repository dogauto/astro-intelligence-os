"""End-to-end career intelligence vertical-slice tests."""

from datetime import UTC, datetime

from astro_engine.astronomy import AstronomyEngine
from astro_engine.builder import AstroStateBuilder
from astro_engine.career_vertical import (
    EventRelationship,
    NormalizedPrediction,
    TimingRelationship,
    _event_relationship,
    _timing_relationship,
    compare_career_results,
    normalize_executor_result,
    normalize_prediction,
    synthesize_career_result,
)
from astro_engine.conventions import PARASHARI_LAHIRI
from astro_engine.executor import (
    ExecutorResult,
    ExecutorStatus,
    MethodExecutionResult,
    MultiMethodExecutor,
)
from astro_engine.methods import (
    MethodRun,
    Prediction,
    PredictionDirection,
    QuestionSpec,
)
from astro_engine.methods.gochara_transit import TransitCareerMethod
from astro_engine.methods.vimshottari_career import VimshottariCareerMethod
from astro_engine.provenance import ProvenanceNodeType, ProvenanceRegistry
from astro_engine.state import BirthInput


def _normalized(
    *,
    method_id: str = "method-a",
    domain: str = "career",
    event: str = "career_transition",
    direction: PredictionDirection = PredictionDirection.POSITIVE,
    start: datetime | None = datetime(2027, 1, 1, tzinfo=UTC),
    end: datetime | None = datetime(2027, 6, 30, tzinfo=UTC),
    is_abstention: bool = False,
) -> NormalizedPrediction:
    return NormalizedPrediction(
        method_id=method_id,
        method_version="1.0.0",
        domain=domain,
        event=event,
        direction=direction,
        time_window_start=start,
        time_window_end=end,
        duration_description=None,
        signals=("signal",),
        supporting_evidence=("evidence",),
        contradictory_evidence=(),
        rules_triggered=("rule",),
        provenance_node_id=f"prediction-{method_id}",
        is_abstention=is_abstention,
    )


def _method_run(
    *,
    method_id: str,
    prediction: Prediction,
) -> MethodRun:
    question = QuestionSpec(
        question_id="comparison-test-question",
        domain="career",
        event_type="career_transition",
        time_horizon=5.0,
        required_time_precision="month",
    )
    return MethodRun(
        method_id=method_id,
        method_version="1.0.0",
        input_state_id="state-id",
        input_state_hash="state-hash",
        question_id=question.question_id,
        question=question,
        predictions=[prediction],
    )


def _executor_result(*runs: tuple[MethodRun, ExecutorStatus]) -> ExecutorResult:
    return ExecutorResult(
        question_id="comparison-test-question",
        input_state_hash="state-hash",
        executor_version="1.0.0",
        method_results=tuple(
            MethodExecutionResult(
                method_id=run.method_id,
                method_version=run.method_version,
                status=status,
                method_run=run,
            )
            for run, status in runs
        ),
    )


def test_event_relationship_branches() -> None:
    assert _event_relationship(
        _normalized(),
        _normalized(method_id="method-b"),
    ) == EventRelationship.AGREEMENT
    assert _event_relationship(
        _normalized(),
        _normalized(method_id="method-b", event="career_growth"),
    ) == EventRelationship.RELATED
    assert _event_relationship(
        _normalized(),
        _normalized(method_id="method-b", direction=PredictionDirection.NEGATIVE),
    ) == EventRelationship.CONTRADICTION
    assert _event_relationship(
        _normalized(),
        _normalized(method_id="method-b", domain="general"),
    ) == EventRelationship.INSUFFICIENT_EVIDENCE
    assert _event_relationship(
        _normalized(),
        _normalized(
            method_id="method-b",
            event="career_growth",
            direction=PredictionDirection.NEGATIVE,
        ),
    ) == EventRelationship.CONTRADICTION


def test_timing_relationship_branches() -> None:
    assert _timing_relationship(
        _normalized(),
        _normalized(
            method_id="method-b",
            start=datetime(2027, 6, 30, tzinfo=UTC),
            end=datetime(2027, 12, 31, tzinfo=UTC),
        ),
    ) == TimingRelationship.OVERLAPPING
    assert _timing_relationship(
        _normalized(),
        _normalized(
            method_id="method-b",
            start=datetime(2027, 7, 1, tzinfo=UTC),
            end=datetime(2027, 12, 31, tzinfo=UTC),
        ),
    ) == TimingRelationship.DIFFERENT
    assert _timing_relationship(
        _normalized(),
        _normalized(method_id="method-b", start=None),
    ) == TimingRelationship.UNAVAILABLE
    assert _timing_relationship(
        _normalized(),
        _normalized(method_id="method-b", end=None),
    ) == TimingRelationship.UNAVAILABLE


def test_comparison_matrix_preserves_abstention_and_insufficient_evidence() -> None:
    affirmative = Prediction(
        domain="career",
        event="career_transition",
        direction=PredictionDirection.POSITIVE,
        method_id="method-a",
        method_version="1.0.0",
        provenance_node_id="prediction-method-a",
    )
    abstention = Prediction(
        domain="career",
        event="career_transition",
        is_abstention=True,
        abstention_reason="missing transit data",
        method_id="method-b",
        method_version="1.0.0",
        provenance_node_id="prediction-method-b",
    )
    comparison = compare_career_results(
        _executor_result(
            (_method_run(method_id="method-a", prediction=affirmative), ExecutorStatus.SUCCESS),
            (_method_run(method_id="method-b", prediction=abstention), ExecutorStatus.ABSTAINED),
        )
    )

    assert comparison.relationships == ()
    assert comparison.abstained_methods == ("method-b",)
    assert comparison.evidence_sources == ("method-a",)
    assert comparison.insufficient_evidence == (
        "Fewer than two non-abstaining method predictions are available.",
    )
    assert any(pred.is_abstention for pred in comparison.predictions)


def test_comparison_does_not_mutate_runs_or_predictions() -> None:
    first = Prediction(
        domain="career",
        event="career_transition",
        direction=PredictionDirection.POSITIVE,
        signal_strength=0.9,
        conditions=["condition"],
        supporting_signals=["signal"],
        method_id="method-a",
        method_version="1.0.0",
        provenance_node_id="prediction-method-a",
    )
    second = first.model_copy(
        deep=True,
        update={
            "method_id": "method-b",
            "provenance_node_id": "prediction-method-b",
        },
    )
    first_run = _method_run(method_id="method-a", prediction=first)
    second_run = _method_run(method_id="method-b", prediction=second)
    before = (first_run.model_dump(mode="json"), second_run.model_dump(mode="json"))

    compare_career_results(
        _executor_result(
            (first_run, ExecutorStatus.SUCCESS),
            (second_run, ExecutorStatus.SUCCESS),
        )
    )

    after = (first_run.model_dump(mode="json"), second_run.model_dump(mode="json"))
    assert after == before
    assert first.signal_strength == 0.9
    assert first.conditions == ["condition"]


def test_method_order_does_not_change_substantive_comparison() -> None:
    predictions = [
        Prediction(
            domain="career",
            event="career_transition",
            direction=PredictionDirection.POSITIVE,
            method_id=method_id,
            method_version="1.0.0",
            provenance_node_id=f"prediction-{method_id}",
        )
        for method_id in ("method-a", "method-b")
    ]
    runs = [
        _method_run(method_id=prediction.method_id, prediction=prediction)
        for prediction in predictions
    ]
    forward = compare_career_results(
        _executor_result(
            (runs[0], ExecutorStatus.SUCCESS),
            (runs[1], ExecutorStatus.SUCCESS),
        )
    )
    reverse = compare_career_results(
        _executor_result(
            (runs[1], ExecutorStatus.SUCCESS),
            (runs[0], ExecutorStatus.SUCCESS),
        )
    )

    assert set(forward.evidence_sources) == set(reverse.evidence_sources)
    assert {
        (
            relationship.event_relationship,
            relationship.timing_relationship,
            frozenset(
                (relationship.left_method_id, relationship.right_method_id)
            ),
        )
        for relationship in forward.relationships
    } == {
        (
            relationship.event_relationship,
            relationship.timing_relationship,
            frozenset(
                (relationship.left_method_id, relationship.right_method_id)
            ),
        )
        for relationship in reverse.relationships
    }
    def canonical_insufficient(messages: tuple[str, ...]) -> set[str]:
        canonical: set[str] = set()
        for message in messages:
            if message.startswith("Timing window unavailable for "):
                methods = message.removeprefix(
                    "Timing window unavailable for "
                ).removesuffix(".").split(" or ")
                canonical.add(
                    "Timing window unavailable for "
                    + " or ".join(sorted(methods))
                    + "."
                )
            else:
                canonical.add(message)
        return canonical

    assert canonical_insufficient(forward.insufficient_evidence) == (
        canonical_insufficient(reverse.insufficient_evidence)
    )


def test_normalization_preserves_provenance_without_probability_conversion() -> None:
    prediction = Prediction(
        domain="career",
        event="career_transition",
        direction=PredictionDirection.POSITIVE,
        signal_strength=0.75,
        method_id="method-a",
        method_version="1.0.0",
        provenance_node_id="prediction-node-a",
    )
    normalized = normalize_prediction(
        _method_run(method_id="method-a", prediction=prediction),
        prediction,
    )

    assert normalized.provenance_node_id == "prediction-node-a"
    assert normalized.signals == ()
    assert not hasattr(normalized, "signal_strength")
    assert not hasattr(normalized, "probability")
    assert not hasattr(normalized, "confidence")


def _build_inputs() -> tuple[BirthInput, QuestionSpec]:
    birth = BirthInput(
        datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=UTC),
        timezone_name="UTC",
        latitude=28.6139,
        longitude=77.2090,
    )
    question = QuestionSpec(
        question_id="career-transition-vertical-slice",
        domain="career",
        event_type="career_transition",
        time_horizon=5.0,
        required_time_precision="month",
        requested_methods=[
            "vimshottari-career-timing-v1",
            "gochara-career-transit-v1",
        ],
    )
    return birth, question


def test_career_question_executes_end_to_end() -> None:
    birth, question = _build_inputs()
    registry = ProvenanceRegistry()
    state = AstroStateBuilder(AstronomyEngine()).build(
        birth,
        PARASHARI_LAHIRI,
        transit_datetime=datetime(2026, 9, 26, 12, 0, tzinfo=UTC),
        provenance_registry=registry,
    )
    result = MultiMethodExecutor().execute(
        question,
        state,
        [VimshottariCareerMethod(), TransitCareerMethod()],
        provenance_registry=registry,
    )

    assert result.question_id == question.question_id
    assert result.input_state_hash == state.state_id
    assert len(result.method_results) == 2
    assert {run.method_id for run in result.all_method_runs} == {
        "vimshottari-career-timing-v1",
        "gochara-career-transit-v1",
    }
    assert all(run.question_id == question.question_id for run in result.all_method_runs)
    assert all(run.input_state_id == state.state_id for run in result.all_method_runs)
    assert all(run.input_state_hash == state.state_id for run in result.all_method_runs)

    normalized = normalize_executor_result(result)
    assert normalized
    assert {pred.domain for pred in normalized} <= {"career", "general"}
    assert all(pred.provenance_node_id for pred in normalized)
    for prediction in normalized:
        trace = registry.trace_prediction(prediction.provenance_node_id)
        node_types = {node.node_type for node in trace}
        assert ProvenanceNodeType.PREDICTION in node_types
        assert ProvenanceNodeType.METHOD_RUN in node_types
        assert ProvenanceNodeType.ASTROSTATE in node_types

    comparison = compare_career_results(result)
    assert len(comparison.evidence_sources) == 2
    assert len(comparison.relationships) == 1
    assert comparison.relationships[0].event_relationship in {
        EventRelationship.RELATED,
        EventRelationship.AGREEMENT,
        EventRelationship.INSUFFICIENT_EVIDENCE,
    }
    assert comparison.relationships[0].timing_relationship == TimingRelationship.UNAVAILABLE
    assert comparison.insufficient_evidence

    synthesis = synthesize_career_result(comparison)
    assert synthesis.calculated_facts
    assert synthesis.method_interpretations
    assert synthesis.combined_observations
    assert synthesis.uncertainty
    assert "Calculated facts:" in synthesis.text
    assert "Uncertainty / abstention:" in synthesis.text
    assert "voted" not in synthesis.text.lower()


def test_career_vertical_slice_repeats_deterministically() -> None:
    birth, question = _build_inputs()

    def run_once() -> tuple[object, object]:
        registry = ProvenanceRegistry()
        state = AstroStateBuilder(AstronomyEngine()).build(
            birth,
            PARASHARI_LAHIRI,
            transit_datetime=datetime(2026, 9, 26, 12, 0, tzinfo=UTC),
            provenance_registry=registry,
        )
        result = MultiMethodExecutor().execute(
            question,
            state,
            [VimshottariCareerMethod(), TransitCareerMethod()],
            provenance_registry=registry,
        )
        comparison = compare_career_results(result)
        synthesis = synthesize_career_result(comparison)
        return comparison, synthesis

    first_comparison, first_synthesis = run_once()
    second_comparison, second_synthesis = run_once()
    assert first_comparison == second_comparison
    assert first_synthesis == second_synthesis


def test_career_vertical_slice_preserves_abstention() -> None:
    birth, question = _build_inputs()
    registry = ProvenanceRegistry()
    state = AstroStateBuilder(AstronomyEngine()).build(
        birth,
        PARASHARI_LAHIRI,
        provenance_registry=registry,
    )
    result = MultiMethodExecutor().execute(
        question,
        state,
        [VimshottariCareerMethod(), TransitCareerMethod()],
        provenance_registry=registry,
    )
    comparison = compare_career_results(result)

    assert "gochara-career-transit-v1" in comparison.abstained_methods
    assert comparison.insufficient_evidence
    assert any(pred.is_abstention for pred in comparison.predictions)
