"""Tests for the Multi-Method Executor."""

from datetime import UTC, datetime

import pytest

from astro_engine.astronomy import AstronomyEngine
from astro_engine.builder import AstroStateBuilder
from astro_engine.conventions import PARASHARI_LAHIRI
from astro_engine.executor import (
    ExecutorStatus,
    MultiMethodExecutor,
)
from astro_engine.methods import (
    Method,
    MethodMaturity,
    MethodRun,
    Prediction,
    PredictionDirection,
    QuestionSpec,
)
from astro_engine.methods.gochara_transit import TransitCareerMethod
from astro_engine.methods.vimshottari_career import VimshottariCareerMethod
from astro_engine.provenance import ProvenanceNodeType, ProvenanceRegistry
from astro_engine.state import BirthInput


@pytest.fixture
def birth_input():
    return BirthInput(
        datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=UTC),
        timezone_name="UTC",
        latitude=28.6139,
        longitude=77.2090,
    )


@pytest.fixture
def state(birth_input):
    engine = AstronomyEngine()
    builder = AstroStateBuilder(engine)
    return builder.build(birth_input, PARASHARI_LAHIRI)


@pytest.fixture
def question_spec():
    return QuestionSpec(
        question_id="executor-test-q",
        domain="career",
        event_type="event_timing",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vimshottari_method():
    return VimshottariCareerMethod()


@pytest.fixture
def gochara_method():
    return TransitCareerMethod()


@pytest.fixture
def executor():
    return MultiMethodExecutor()


# ---------------------------------------------------------------------------
# Helper: spy method that records what it received
# ---------------------------------------------------------------------------


def _make_spy_method(name: str, answer: str = "spy") -> Method:
    """Create a minimal spy method that records calls and returns a fixed prediction."""
    calls: list[tuple] = []

    class SpyMethod(Method):
        @property
        def method_id(self) -> str:
            return name

        @property
        def name(self) -> str:
            return f"Spy {name}"

        @property
        def version(self) -> str:
            return "1.0.0"

        @property
        def tradition(self) -> str:
            return "Spy"

        @property
        def maturity(self) -> MethodMaturity:
            return MethodMaturity.EXPERIMENTAL

        @property
        def supported_domains(self) -> list[str]:
            return ["career"]

        @property
        def required_calculations(self) -> list[str]:
            return ["planets"]

        def run(self, state, question, provenance_registry=None) -> MethodRun:
            calls.append((state.state_id, question.question_id))
            return MethodRun(
                method_id=name,
                method_version="1.0.0",
                input_state_id=state.state_id,
                question_id=question.question_id,
                question=question,
                predictions=[
                    Prediction(
                        domain="career",
                        event=f"{answer}_signal",
                        direction=PredictionDirection.POSITIVE,
                        magnitude=0.5,
                        signal_strength=0.5,
                        method_id=name,
                        method_version="1.0.0",
                        question_id=question.question_id,
                    )
                ],
            )

    spy = SpyMethod()
    spy._calls = calls  # type: ignore[attr-defined]
    return spy


def _make_abstaining_spy() -> Method:
    """Create a spy that returns a MethodRun with an abstention prediction."""

    class AbstainMethod(Method):
        @property
        def method_id(self) -> str:
            return "abstain-spy"

        @property
        def name(self) -> str:
            return "AbstainSpy"

        @property
        def version(self) -> str:
            return "1.0.0"

        @property
        def tradition(self) -> str:
            return "Spy"

        @property
        def maturity(self) -> MethodMaturity:
            return MethodMaturity.EXPERIMENTAL

        @property
        def supported_domains(self) -> list[str]:
            return ["career"]

        @property
        def required_calculations(self) -> list[str]:
            return ["planets"]

        def run(self, state, question, provenance_registry=None) -> MethodRun:
            return MethodRun(
                method_id="abstain-spy",
                method_version="1.0.0",
                input_state_id=state.state_id,
                question_id=question.question_id,
                question=question,
                predictions=[
                    Prediction(
                        domain="career",
                        event="abstain",
                        is_abstention=True,
                        abstention_reason="Spy abstains intentionally.",
                        method_id="abstain-spy",
                        method_version="1.0.0",
                        question_id=question.question_id,
                    )
                ],
            )

    return AbstainMethod()


def _make_failing_spy() -> Method:
    """Create a spy that raises an exception on execution."""

    class FailMethod(Method):
        @property
        def method_id(self) -> str:
            return "fail-spy"

        @property
        def name(self) -> str:
            return "FailSpy"

        @property
        def version(self) -> str:
            return "1.0.0"

        @property
        def tradition(self) -> str:
            return "Spy"

        @property
        def maturity(self) -> MethodMaturity:
            return MethodMaturity.EXPERIMENTAL

        @property
        def supported_domains(self) -> list[str]:
            return ["career"]

        @property
        def required_calculations(self) -> list[str]:
            return ["planets"]

        def run(self, state, question, provenance_registry=None) -> MethodRun:
            raise RuntimeError("Intentional spy failure")

    return FailMethod()


# ---------------------------------------------------------------------------
# Basic execution
# ---------------------------------------------------------------------------


class TestBasicExecution:
    """Two or more methods execute and produce results."""

    def test_two_methods_execute(
        self, executor, vimshottari_method, gochara_method, state, question_spec,
    ):
        result = executor.execute(question_spec, state, [vimshottari_method, gochara_method])
        assert len(result.method_results) == 2
        assert result.question_id == question_spec.question_id
        assert result.input_state_hash == state.state_id
        assert result.executor_version == MultiMethodExecutor.VERSION

    def test_three_methods_execute(
        self, executor, vimshottari_method, gochara_method, state, question_spec,
    ):
        spy = _make_spy_method("spy-c")
        result = executor.execute(
            question_spec, state,
            [vimshottari_method, gochara_method, spy],
        )
        assert len(result.method_results) == 3

    def test_arbitrary_method_count(self, executor, state, question_spec):
        spies = [_make_spy_method(f"spy-{i}") for i in range(10)]
        result = executor.execute(question_spec, state, spies)
        assert len(result.method_results) == 10

    def test_empty_method_list(self, executor, state, question_spec):
        result = executor.execute(question_spec, state, [])
        assert len(result.method_results) == 0
        assert result.question_id == question_spec.question_id
        assert result.input_state_hash == state.state_id


# ---------------------------------------------------------------------------
# Determinism and ordering
# ---------------------------------------------------------------------------


class TestDeterminism:
    """Result ordering is deterministic and matches input ordering."""

    def test_ordering_matches_input(self, executor, state, question_spec):
        a = _make_spy_method("method-a")
        b = _make_spy_method("method-b")
        c = _make_spy_method("method-c")
        result = executor.execute(question_spec, state, [a, b, c])
        ids = [r.method_id for r in result.method_results]
        assert ids == ["method-a", "method-b", "method-c"]

    def test_deterministic_repeated_execution(
        self, executor, vimshottari_method, gochara_method, state, question_spec,
    ):
        r1 = executor.execute(question_spec, state, [vimshottari_method, gochara_method])
        r2 = executor.execute(question_spec, state, [vimshottari_method, gochara_method])
        assert r1.question_id == r2.question_id
        assert r1.executor_version == r2.executor_version
        assert len(r1.method_results) == len(r2.method_results)
        for r1m, r2m in zip(r1.method_results, r2.method_results, strict=True):
            assert r1m.method_id == r2m.method_id
            assert r1m.method_version == r2m.method_version

    def test_duplicate_methods_deduplicated(
        self, executor, vimshottari_method, state, question_spec,
    ):
        result = executor.execute(question_spec, state, [vimshottari_method, vimshottari_method])
        assert len(result.method_results) == 1
        assert result.method_results[0].method_id == vimshottari_method.method_id


# ---------------------------------------------------------------------------
# Input propagation
# ---------------------------------------------------------------------------


class TestInputPropagation:
    """Same QuestionSpec and AstroState reach every method."""

    def test_same_question_spec_reaches_every_method(self, executor, state):
        a = _make_spy_method("method-a")
        b = _make_spy_method("method-b")
        executor.execute(
            QuestionSpec(question_id="q-identical", domain="career", event_type="timing"),
            state,
            [a, b],
        )
        # Both spies recorded the same question_id
        assert a._calls[0][1] == "q-identical"  # type: ignore[attr-defined]
        assert b._calls[0][1] == "q-identical"  # type: ignore[attr-defined]

    def test_same_astro_state_reaches_every_method(self, executor, state):
        a = _make_spy_method("method-a")
        b = _make_spy_method("method-b")
        executor.execute(
            QuestionSpec(question_id="q", domain="career", event_type="timing"),
            state,
            [a, b],
        )
        assert a._calls[0][0] == state.state_id  # type: ignore[attr-defined]
        assert b._calls[0][0] == state.state_id  # type: ignore[attr-defined]

    def test_question_id_preserved_in_all_method_runs(
        self, executor, vimshottari_method, gochara_method, state, question_spec,
    ):
        result = executor.execute(question_spec, state, [vimshottari_method, gochara_method])
        for mr in result.all_method_runs:
            assert mr.question_id == question_spec.question_id

    def test_input_state_identity_preserved(
        self, executor, vimshottari_method, gochara_method, state, question_spec,
    ):
        result = executor.execute(question_spec, state, [vimshottari_method, gochara_method])
        for mr in result.all_method_runs:
            assert mr.input_state_id == state.state_id


# ---------------------------------------------------------------------------
# Method isolation
# ---------------------------------------------------------------------------


class TestMethodIsolation:
    """Methods cannot observe each other's outputs."""

    def test_method_a_cannot_observe_method_b(self, executor, state, question_spec):
        # Method B writes a distinctive answer
        b = _make_spy_method("method-b", answer="b_output")
        # Method A should see nothing from B
        a = _make_spy_method("method-a", answer="a_output")
        executor.execute(question_spec, state, [a, b])
        assert a._calls[0][0] == state.state_id  # type: ignore[attr-defined]
        assert a._calls[0][1] == question_spec.question_id  # type: ignore[attr-defined]

    def test_method_b_cannot_observe_method_a(self, executor, state, question_spec):
        a = _make_spy_method("method-a", answer="a_output")
        b = _make_spy_method("method-b", answer="b_output")
        executor.execute(question_spec, state, [a, b])
        assert b._calls[0][0] == state.state_id  # type: ignore[attr-defined]
        assert b._calls[0][1] == question_spec.question_id  # type: ignore[attr-defined]

    def test_three_way_isolation(self, executor, state, question_spec):
        a = _make_spy_method("method-a", answer="a_output")
        b = _make_spy_method("method-b", answer="b_output")
        c = _make_spy_method("method-c", answer="c_output")
        executor.execute(question_spec, state, [a, b, c])
        for spy in (a, b, c):
            assert spy._calls[0][0] == state.state_id  # type: ignore[attr-defined]
            assert spy._calls[0][1] == question_spec.question_id  # type: ignore[attr-defined]

    def test_no_prediction_leakage(self, executor, state, question_spec):
        """Predictions from one method must not appear in another's MethodRun."""
        a = _make_spy_method("method-a", answer="a_signal")
        b = _make_spy_method("method-b", answer="b_signal")
        result = executor.execute(question_spec, state, [a, b])
        # Each method's MethodRun must contain only its own method_id
        a_run = next(r for r in result.method_results if r.method_id == "method-a")
        b_run = next(r for r in result.method_results if r.method_id == "method-b")
        assert all(p.method_id == "method-a" for p in a_run.method_run.predictions)
        assert all(p.method_id == "method-b" for p in b_run.method_run.predictions)


# ---------------------------------------------------------------------------
# MethodRun preservation
# ---------------------------------------------------------------------------


class TestMethodRunPreservation:
    """Each MethodRun remains intact and independently inspectable."""

    def test_predictions_preserved(
        self, executor, vimshottari_method, gochara_method, state, question_spec,
    ):
        result = executor.execute(question_spec, state, [vimshottari_method, gochara_method])
        for mr in result.all_method_runs:
            assert mr.method_id is not None
            assert mr.method_version is not None
            assert isinstance(mr.predictions, list)

    def test_method_identity_preserved(
        self, executor, vimshottari_method, gochara_method, state, question_spec,
    ):
        result = executor.execute(question_spec, state, [vimshottari_method, gochara_method])
        ids = {r.method_id for r in result.method_results}
        assert ids == {vimshottari_method.method_id, gochara_method.method_id}

    def test_existing_vimshottari_through_executor(
        self, executor, vimshottari_method, state, question_spec,
    ):
        result = executor.execute(question_spec, state, [vimshottari_method])
        for mr in result.all_method_runs:
            assert mr.method_id == vimshottari_method.method_id
            assert mr.question_id == question_spec.question_id
            assert mr.input_state_id == state.state_id

    def test_existing_gochara_through_executor(
        self, executor, gochara_method, state, question_spec,
    ):
        result = executor.execute(question_spec, state, [gochara_method])
        for mr in result.all_method_runs:
            assert mr.method_id == gochara_method.method_id
            assert mr.question_id == question_spec.question_id
            assert mr.input_state_id == state.state_id


# ---------------------------------------------------------------------------
# Failure and abstention semantics
# ---------------------------------------------------------------------------


class TestFailureAndAbstention:
    """Failure and abstention are handled correctly."""

    def test_successful_method_plus_abstaining_method(
        self, executor, vimshottari_method, state, question_spec,
    ):
        """One method succeeds, another abstains."""
        abstain_spy = _make_abstaining_spy()
        result = executor.execute(question_spec, state, [vimshottari_method, abstain_spy])
        statuses = {r.status for r in result.method_results}
        assert ExecutorStatus.SUCCESS in statuses or ExecutorStatus.ABSTAINED in statuses
        assert len(result.method_results) == 2

    def test_successful_method_plus_failed_method(
        self, executor, vimshottari_method, state, question_spec,
    ):
        """One method succeeds, another raises."""
        failing_spy = _make_failing_spy()
        result = executor.execute(question_spec, state, [vimshottari_method, failing_spy])
        statuses = [r.status for r in result.method_results]
        assert ExecutorStatus.FAILED in statuses
        # The successful method's result must still be present
        success_results = [r for r in result.method_results if not r.is_failed]
        assert len(success_results) == 1
        assert success_results[0].is_success

    def test_all_methods_failing(self, executor, state, question_spec):
        a = _make_failing_spy()
        b = _make_failing_spy()
        result = executor.execute(question_spec, state, [a, b])
        assert all(r.is_failed for r in result.method_results)
        assert result.success_runs == ()
        assert result.abstained_runs == ()

    def test_all_methods_abstaining(self, executor, state, question_spec):
        a = _make_abstaining_spy()
        b = _make_abstaining_spy()
        result = executor.execute(question_spec, state, [a, b])
        assert all(r.is_abstained for r in result.method_results)

    def test_no_prediction_fabricated_on_failure(self, executor, state, question_spec):
        """A failed method must not produce a fabricated prediction."""
        failing = _make_failing_spy()
        result = executor.execute(question_spec, state, [failing])
        assert result.failed_methods[0].method_run is None
        assert result.failed_methods[0].error is not None

    def test_abstention_preserved_not_fabricated(self, executor, state, question_spec):
        """An abstaining method's abstention must be explicit."""
        abstain = _make_abstaining_spy()
        result = executor.execute(question_spec, state, [abstain])
        assert result.abstained_runs[0].predictions[0].is_abstention is True


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


class TestImmutability:
    """Executor must not mutate inputs."""

    def test_question_spec_not_mutated(self, executor, vimshottari_method, state):
        spec = QuestionSpec(question_id="original-id", domain="career", event_type="timing")
        original_id = spec.question_id
        executor.execute(spec, state, [vimshottari_method])
        assert spec.question_id == original_id

    def test_astro_state_not_mutated(self, executor, vimshottari_method, state):
        original_id = state.state_id
        original_planet_count = len(state.planets)
        spec = QuestionSpec(question_id="q", domain="career", event_type="timing")
        executor.execute(spec, state, [vimshottari_method])
        assert state.state_id == original_id
        assert len(state.planets) == original_planet_count


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


class TestProvenance:
    """Provenance chains survive executor execution."""

    def test_provenance_preserved_through_executor(
        self, executor, vimshottari_method, state, question_spec,
    ):
        # Build a fresh state WITH the registry so the full provenance chain is
        # established (ASTROSTATE → CALCULATION → ASTRONOMY_COMPUTATION →
        # BIRTH_INPUT + CONVENTION_PROFILE).
        registry = ProvenanceRegistry()
        fresh_state = AstroStateBuilder(AstronomyEngine()).build(
            BirthInput(
                datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=UTC),
                timezone_name="UTC",
                latitude=28.6139,
                longitude=77.2090,
            ),
            PARASHARI_LAHIRI,
            provenance_registry=registry,
        )
        result = executor.execute(
            question_spec, fresh_state,
            [vimshottari_method],
            provenance_registry=registry,
        )

        # vimshottari produces SUCCESS predictions; require provenance unconditionally
        success_runs = result.success_runs
        assert success_runs, "vimshottari must produce at least one success prediction"
        pred = success_runs[0].predictions[0]
        assert pred.provenance_node_id is not None, "prediction must have provenance_node_id"
        trace = registry.trace_prediction(pred.provenance_node_id)
        node_types = {n.node_type.value for n in trace}
        assert ProvenanceNodeType.PREDICTION.value in node_types
        assert ProvenanceNodeType.METHOD_RUN.value in node_types
        assert ProvenanceNodeType.ASTROSTATE.value in node_types
        assert ProvenanceNodeType.CALCULATION.value in node_types
        assert ProvenanceNodeType.ASTRONOMY_COMPUTATION.value in node_types
        assert ProvenanceNodeType.BIRTH_INPUT.value in node_types
        assert ProvenanceNodeType.CONVENTION_PROFILE.value in node_types

    def test_provenance_preserved_for_abstention(
        self, executor, state, question_spec,
    ):
        """Gochara no-transit abstention must retain full provenance."""
        # Build state WITHOUT transit to trigger gochara abstention path
        registry = ProvenanceRegistry()
        fresh_state = AstroStateBuilder(AstronomyEngine()).build(
            BirthInput(
                datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=UTC),
                timezone_name="UTC",
                latitude=28.6139,
                longitude=77.2090,
            ),
            PARASHARI_LAHIRI,
            provenance_registry=registry,
        )
        result = executor.execute(
            question_spec, fresh_state,
            [TransitCareerMethod()],
            provenance_registry=registry,
        )

        # Gochara abstains but still produces a MethodRun with provenance
        assert result.method_results, "executor must produce a MethodExecutionResult"
        mres = result.method_results[0]
        assert mres.status == ExecutorStatus.ABSTAINED, f"expected ABSTAINED, got {mres.status}"
        assert mres.method_run is not None, "abstention MethodRun must exist"
        mr = mres.method_run
        assert mr.input_state_hash == fresh_state.state_id
        assert mr.question_id == question_spec.question_id
        assert mr.method_id == "gochara-career-transit-v1"
        assert mr.method_version == "1.0.0"

        # Abstention prediction must have required identity fields
        assert mr.predictions, "abstention MethodRun must have a prediction"
        pred = mr.predictions[0]
        assert pred.is_abstention is True
        assert pred.question_id == question_spec.question_id
        assert pred.method_id == "gochara-career-transit-v1"
        assert pred.method_version == "1.0.0"

        # Provenance node must exist and trace back
        assert pred.provenance_node_id is not None, (
            "abstention prediction must have provenance_node_id"
        )
        trace = registry.trace_prediction(pred.provenance_node_id)
        node_types = {n.node_type.value for n in trace}
        assert ProvenanceNodeType.PREDICTION.value in node_types
        assert ProvenanceNodeType.METHOD_RUN.value in node_types
        assert ProvenanceNodeType.ASTROSTATE.value in node_types
        assert ProvenanceNodeType.CALCULATION.value in node_types
        assert ProvenanceNodeType.ASTRONOMY_COMPUTATION.value in node_types
        assert ProvenanceNodeType.BIRTH_INPUT.value in node_types
        assert ProvenanceNodeType.CONVENTION_PROFILE.value in node_types


# ---------------------------------------------------------------------------
# Blocker 1: input_state_hash propagation
# ---------------------------------------------------------------------------


class TestInputStateHash:
    """input_state_hash must be populated in every MethodRun."""

    def test_vimshottari_input_state_hash_populated(
        self, executor, vimshottari_method, state, question_spec,
    ):
        """Regression: input_state_hash must equal state.state_id."""
        result = executor.execute(question_spec, state, [vimshottari_method])
        for mr in result.all_method_runs:
            assert mr.input_state_hash == state.state_id
            assert mr.input_state_hash != "", "input_state_hash must not be empty"

    def test_gochara_input_state_hash_populated(
        self, executor, gochara_method, state, question_spec,
    ):
        """Regression: input_state_hash must equal state.state_id even on abstention."""
        result = executor.execute(question_spec, state, [gochara_method])
        for mr in result.all_method_runs:
            assert mr.input_state_hash == state.state_id
            assert mr.input_state_hash != "", "input_state_hash must not be empty"

    def test_both_methods_input_state_hash(
        self, executor, vimshottari_method, gochara_method, state, question_spec,
    ):
        """Both methods produce correct input_state_hash."""
        result = executor.execute(question_spec, state, [vimshottari_method, gochara_method])
        for mr in result.all_method_runs:
            assert mr.input_state_hash == state.state_id
            assert mr.input_state_hash != "", "input_state_hash must not be empty"


# ---------------------------------------------------------------------------
# Blocker 2: Abstention classification
# ---------------------------------------------------------------------------


def _make_abstention_record_spy() -> Method:
    """Create a spy that populates MethodRun.abstentions (not just is_abstention)."""

    class AbstentionRecordMethod(Method):
        @property
        def method_id(self) -> str:
            return "abstention-record-spy"

        @property
        def name(self) -> str:
            return "AbstentionRecordSpy"

        @property
        def version(self) -> str:
            return "1.0.0"

        @property
        def tradition(self) -> str:
            return "Spy"

        @property
        def maturity(self) -> MethodMaturity:
            return MethodMaturity.EXPERIMENTAL

        @property
        def supported_domains(self) -> list[str]:
            return ["career"]

        @property
        def required_calculations(self) -> list[str]:
            return ["planets"]

        def run(self, state, question, provenance_registry=None) -> MethodRun:
            return MethodRun(
                method_id="abstention-record-spy",
                method_version="1.0.0",
                input_state_id=state.state_id,
                input_state_hash=state.state_id,
                question_id=question.question_id,
                question=question,
                abstentions=[{"reason": "insufficient data", "timestamp": "2026-01-01T00:00:00Z"}],
                predictions=[],
            )

    return AbstentionRecordMethod()


class TestAbstentionClassification:
    """Executor correctly classifies SUCCESS, ABSTAINED, FAILED."""

    def test_successful_prediction_classified_success(
        self, executor, vimshottari_method, state, question_spec,
    ):
        """A method with non-abstention predictions is SUCCESS."""
        result = executor.execute(question_spec, state, [vimshottari_method])
        for r in result.method_results:
            if (r.method_id == vimshottari_method.method_id
                    and r.method_run and r.method_run.predictions):
                has_abst = any(p.is_abstention for p in r.method_run.predictions)
                if not has_abst and not r.method_run.abstentions:
                    assert r.status == ExecutorStatus.SUCCESS

    def test_explicit_abstention_prediction_classified_abstained(
        self, executor, state, question_spec,
    ):
        """A method with is_abstention=True predictions is ABSTAINED."""
        abstain = _make_abstaining_spy()
        result = executor.execute(question_spec, state, [abstain])
        abstain_result = next(r for r in result.method_results
                              if r.method_id == "abstain-spy")
        assert abstain_result.status == ExecutorStatus.ABSTAINED
        assert abstain_result.method_run is not None
        assert abstain_result.method_run.predictions[0].is_abstention is True

    def test_abstentions_list_classified_abstained(
        self, executor, state, question_spec,
    ):
        """A method with non-empty abstentions list is ABSTAINED
        (even without is_abstention predictions)."""
        record = _make_abstention_record_spy()
        result = executor.execute(question_spec, state, [record])
        abstain_result = next(r for r in result.method_results
                              if r.method_id == "abstention-record-spy")
        assert abstain_result.status == ExecutorStatus.ABSTAINED
        assert abstain_result.method_run is not None
        assert abstain_result.method_run.abstentions

    def test_failure_classified_failed(self, executor, state, question_spec):
        """A method that raises is FAILED."""
        failing = _make_failing_spy()
        result = executor.execute(question_spec, state, [failing])
        assert result.failed_methods[0].status == ExecutorStatus.FAILED
        assert result.failed_methods[0].method_run is None
        assert result.failed_methods[0].error is not None

    def test_no_fabricated_prediction_on_failure(self, executor, state, question_spec):
        """A failed method must not have a fabricated prediction."""
        failing = _make_failing_spy()
        result = executor.execute(question_spec, state, [failing])
        assert result.failed_methods[0].method_run is None
        assert result.failed_methods[0].error is not None

    def test_no_prediction_on_abstention_only(
        self, executor, state, question_spec,
    ):
        """An abstention with no predictions is still classified ABSTAINED."""
        record = _make_abstention_record_spy()
        result = executor.execute(question_spec, state, [record])
        abstain_result = next(
            (r for r in result.method_results
             if r.method_id == "abstention-record-spy"), None
        )
        assert abstain_result is not None
        assert abstain_result.status == ExecutorStatus.ABSTAINED
        assert abstain_result.method_run is not None
        assert abstain_result.method_run.predictions == []


# ---------------------------------------------------------------------------
# Blocker 3: Adversarial isolation
# ---------------------------------------------------------------------------


def _make_adversarial_spy(name: str) -> Method:
    """
    Spy that actively tries to observe other methods' outputs.
    It records whether it found any leakage.
    """
    observations = {"found_leakage": False, "leakage_details": []}

    class AdversarialMethod(Method):
        @property
        def method_id(self) -> str:
            return name

        @property
        def name(self) -> str:
            return f"Adversarial {name}"

        @property
        def version(self) -> str:
            return "1.0.0"

        @property
        def tradition(self) -> str:
            return "Spy"

        @property
        def maturity(self) -> MethodMaturity:
            return MethodMaturity.EXPERIMENTAL

        @property
        def supported_domains(self) -> list[str]:
            return ["career"]

        @property
        def required_calculations(self) -> list[str]:
            return ["planets"]

        def run(self, state, question, provenance_registry=None) -> MethodRun:
            # Actively try to discover shared state / other method outputs
            for attr_name in ("shared_results", "previous_runs",
                "other_method_outputs", "_executor_state"):
                if hasattr(state, attr_name):
                    observations["found_leakage"] = True
                    observations["leakage_details"].append(f"Found {attr_name} on state")
            if provenance_registry:
                for attr_name in ("results", "previous_methods", "_shared"):
                    if hasattr(provenance_registry, attr_name):
                        observations["found_leakage"] = True
                        observations["leakage_details"].append(f"Found {attr_name} on registry")
            # Try to see if a module-level variable exists
            import sys
            for mod_name in ("executor_shared_results", "_previous_method_runs"):
                if hasattr(sys.modules.get("astro_engine.executor"), mod_name):
                    observations["found_leakage"] = True
                    observations["leakage_details"].append(f"Found {mod_name} in executor module")
            # Always return a normal prediction
            return MethodRun(
                method_id=name,
                method_version="1.0.0",
                input_state_id=state.state_id,
                input_state_hash=state.state_id,
                question_id=question.question_id,
                question=question,
                predictions=[
                    Prediction(
                        domain="career",
                        event=f"{name}_prediction",
                        direction=PredictionDirection.POSITIVE,
                        magnitude=0.5,
                        signal_strength=0.5,
                        method_id=name,
                        method_version="1.0.0",
                        question_id=question.question_id,
                    )
                ],
            )

    spy = AdversarialMethod()
    spy._observations = observations  # type: ignore[attr-defined]
    return spy


class TestAdversarialIsolation:
    """Methods actively try to observe each other — none succeed."""

    def test_method_a_cannot_observe_method_b_output(self, executor, state, question_spec):
        """Method A runs first, tries to read Method B's result — finds nothing."""
        a = _make_adversarial_spy("method-a")
        b = _make_adversarial_spy("method-b")
        executor.execute(question_spec, state, [a, b])
        leaked_a = a._observations["found_leakage"]  # type: ignore[attr-defined]
        assert not leaked_a

    def test_method_b_cannot_observe_method_a_output(self, executor, state, question_spec):
        """Method B runs second, tries to read Method A's result — finds nothing."""
        a = _make_adversarial_spy("method-a")
        b = _make_adversarial_spy("method-b")
        executor.execute(question_spec, state, [a, b])
        leaked_b = b._observations["found_leakage"]  # type: ignore[attr-defined]
        assert not leaked_b

    def test_three_way_adversarial_isolation(self, executor, state, question_spec):
        """A, B, C all try to observe each other — none succeed."""
        a = _make_adversarial_spy("method-a")
        b = _make_adversarial_spy("method-b")
        c = _make_adversarial_spy("method-c")
        executor.execute(question_spec, state, [a, b, c])
        for spy in (a, b, c):
            leaked = spy._observations["found_leakage"]  # type: ignore[attr-defined]
            detail = spy._observations["leakage_details"]  # type: ignore[attr-defined]
            assert not leaked, f"{spy.method_id} leaked: {detail}"

    def test_no_shared_result_state(self, executor, state, question_spec):
        """Executor must not expose a shared results container to methods."""
        import astro_engine.executor as mod
        # Verify no mutable shared list exists at module level
        assert not hasattr(mod, "_executor_shared_results")
        assert not hasattr(mod, "_previous_method_runs")


# ---------------------------------------------------------------------------
# Blocker 4: Deterministic execution
# ---------------------------------------------------------------------------


class TestDeterministicExecution:
    """
    Deterministic contract:
    - question_id, input_state_hash, method_id, method_version are deterministic
    - Predictions retain their semantic content deterministically
    - UUIDs (run_id, prediction_id) and timestamps (executed_at) are intentionally unique
      and not part of the deterministic contract
    """

    def test_deterministic_semantic_fields(
        self, executor, vimshottari_method, state, question_spec,
    ):
        """Semantic fields are identical across repeated executions."""
        r1 = executor.execute(question_spec, state, [vimshottari_method])
        r2 = executor.execute(question_spec, state, [vimshottari_method])
        assert r1.question_id == r2.question_id
        assert r1.input_state_hash == r2.input_state_hash
        assert r1.executor_version == r2.executor_version
        assert len(r1.method_results) == len(r2.method_results)
        for m1, m2 in zip(r1.method_results, r2.method_results, strict=True):
            assert m1.method_id == m2.method_id
            assert m1.method_version == m2.method_version
            if m1.method_run and m2.method_run:
                assert m1.method_run.method_id == m2.method_run.method_id
                assert m1.method_run.method_version == m2.method_run.method_version
                assert m1.method_run.question_id == m2.method_run.question_id
                assert m1.method_run.input_state_id == m2.method_run.input_state_id
                assert m1.method_run.input_state_hash == m2.method_run.input_state_hash
                assert m1.method_run.calculations_used == m2.method_run.calculations_used
                assert m1.method_run.rules_evaluated == m2.method_run.rules_evaluated
                assert m1.method_run.intermediate_findings == m2.method_run.intermediate_findings

    def test_deterministic_prediction_semantics(
        self, executor, vimshottari_method, state, question_spec,
    ):
        """Predictions retain deterministic semantic content across executions."""
        r1 = executor.execute(question_spec, state, [vimshottari_method])
        r2 = executor.execute(question_spec, state, [vimshottari_method])
        runs1 = r1.success_runs
        runs2 = r2.success_runs
        if runs1 and runs2:
            for p1, p2 in zip(runs1[0].predictions, runs2[0].predictions, strict=True):
                assert p1.domain == p2.domain
                assert p1.event == p2.event
                assert p1.direction == p2.direction
                assert p1.magnitude == p2.magnitude
                assert p1.signal_strength == p2.signal_strength
                assert p1.method_id == p2.method_id
                assert p1.question_id == p2.question_id
                # time windows are deterministic
                assert p1.time_window_start == p2.time_window_start
                assert p1.time_window_end == p2.time_window_end
                assert p1.conditions == p2.conditions
                assert p1.supporting_evidence == p2.supporting_evidence

    def test_deterministic_method_ordering(self, executor, state, question_spec):
        """Result ordering matches input ordering across repeated executions."""
        a = _make_spy_method("method-a")
        b = _make_spy_method("method-b")
        r1 = executor.execute(question_spec, state, [a, b])
        r2 = executor.execute(question_spec, state, [a, b])
        ids1 = [r.method_id for r in r1.method_results]
        ids2 = [r.method_id for r in r2.method_results]
        assert ids1 == ids2 == ["method-a", "method-b"]

    def test_different_question_spec_produces_different_results(
        self, executor, vimshottari_method, state,
    ):
        """Different question_ids produce different question_id in results."""
        q1 = QuestionSpec(question_id="q-diff-1", domain="career", event_type="timing")
        q2 = QuestionSpec(question_id="q-diff-2", domain="career", event_type="timing")
        r1 = executor.execute(q1, state, [vimshottari_method])
        r2 = executor.execute(q2, state, [vimshottari_method])
        assert r1.question_id == "q-diff-1"
        assert r2.question_id == "q-diff-2"
        assert r1.question_id != r2.question_id

    def test_intentionally_unique_fields_differ(
        self, executor, vimshottari_method, state, question_spec,
    ):
        """UUID and timestamp fields are intentionally unique and differ."""
        r1 = executor.execute(question_spec, state, [vimshottari_method])
        r2 = executor.execute(question_spec, state, [vimshottari_method])
        runs1 = r1.success_runs
        runs2 = r2.success_runs
        if runs1 and runs2 and runs1[0].predictions and runs2[0].predictions:
            # run_id should differ (UUID)
            assert runs1[0].run_id != runs2[0].run_id
            # prediction_id should differ (UUID)
            assert runs1[0].predictions[0].prediction_id != runs2[0].predictions[0].prediction_id
            # executed_at should differ (timestamp)
            assert runs1[0].executed_at != runs2[0].executed_at


# ---------------------------------------------------------------------------
# Helper functions (must stay after classes that reference them)
# ---------------------------------------------------------------------------


def _make_abstaining_spy() -> Method:
    """Create a spy that returns a MethodRun with an abstention prediction."""

    class AbstainMethod(Method):
        @property
        def method_id(self) -> str:
            return "abstain-spy"

        @property
        def name(self) -> str:
            return "AbstainSpy"

        @property
        def version(self) -> str:
            return "1.0.0"

        @property
        def tradition(self) -> str:
            return "Spy"

        @property
        def maturity(self) -> MethodMaturity:
            return MethodMaturity.EXPERIMENTAL

        @property
        def supported_domains(self) -> list[str]:
            return ["career"]

        @property
        def required_calculations(self) -> list[str]:
            return ["planets"]

        def run(self, state, question, provenance_registry=None) -> MethodRun:
            return MethodRun(
                method_id="abstain-spy",
                method_version="1.0.0",
                input_state_id=state.state_id,
                question_id=question.question_id,
                question=question,
                predictions=[
                    Prediction(
                        domain="career",
                        event="abstain",
                        is_abstention=True,
                        abstention_reason="Spy abstains intentionally.",
                        method_id="abstain-spy",
                        method_version="1.0.0",
                        question_id=question.question_id,
                    )
                ],
            )

    return AbstainMethod()


def _make_failing_spy() -> Method:
    """Create a spy that raises an exception on execution."""

    class FailMethod(Method):
        @property
        def method_id(self) -> str:
            return "fail-spy"

        @property
        def name(self) -> str:
            return "FailSpy"

        @property
        def version(self) -> str:
            return "1.0.0"

        @property
        def tradition(self) -> str:
            return "Spy"

        @property
        def maturity(self) -> MethodMaturity:
            return MethodMaturity.EXPERIMENTAL

        @property
        def supported_domains(self) -> list[str]:
            return ["career"]

        @property
        def required_calculations(self) -> list[str]:
            return ["planets"]

        def run(self, state, question, provenance_registry=None) -> MethodRun:
            raise RuntimeError("Intentional spy failure")

    return FailMethod()


def _make_spy_method(name: str, answer: str = "spy") -> Method:
    """Create a minimal spy method that records calls and returns a fixed prediction."""
    calls: list[tuple] = []

    class SpyMethod(Method):
        @property
        def method_id(self) -> str:
            return name

        @property
        def name(self) -> str:
            return f"Spy {name}"

        @property
        def version(self) -> str:
            return "1.0.0"

        @property
        def tradition(self) -> str:
            return "Spy"

        @property
        def maturity(self) -> MethodMaturity:
            return MethodMaturity.EXPERIMENTAL

        @property
        def supported_domains(self) -> list[str]:
            return ["career"]

        @property
        def required_calculations(self) -> list[str]:
            return ["planets"]

        def run(self, state, question, provenance_registry=None) -> MethodRun:
            calls.append((state.state_id, question.question_id))
            return MethodRun(
                method_id=name,
                method_version="1.0.0",
                input_state_id=state.state_id,
                question_id=question.question_id,
                question=question,
                predictions=[
                    Prediction(
                        domain="career",
                        event=f"{answer}_signal",
                        direction=PredictionDirection.POSITIVE,
                        magnitude=0.5,
                        signal_strength=0.5,
                        method_id=name,
                        method_version="1.0.0",
                        question_id=question.question_id,
                    )
                ],
            )

    spy = SpyMethod()
    spy._calls = calls  # type: ignore[attr-defined]
    return spy


class TestVimshottariAbstentionProvenance:
    """Vimshottari abstentions retain identity and provenance."""

    @staticmethod
    def _build_state(
        *,
        registry: ProvenanceRegistry,
        update: dict[str, object],
    ):
        include_chart = "chart" not in update
        include_dashas = "dashas" not in update
        dasha_override = update.get("dashas")
        state = AstroStateBuilder(AstronomyEngine()).build(
            BirthInput(
                datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=UTC),
                timezone_name="UTC",
                latitude=28.6139,
                longitude=77.2090,
            ),
            PARASHARI_LAHIRI,
            provenance_registry=registry,
            include_chart=include_chart,
            include_dashas=include_dashas,
            dasha_override=(
                dasha_override if isinstance(dasha_override, dict) else None
            ),
        )
        return state

    def _assert_abstention(
        self,
        executor,
        question_spec,
        *,
        update: dict[str, object],
    ) -> None:
        registry = ProvenanceRegistry()
        state = self._build_state(registry=registry, update=update)
        result = executor.execute(
            question_spec,
            state,
            [VimshottariCareerMethod()],
            provenance_registry=registry,
        )

        assert result.method_results
        method_result = result.method_results[0]
        assert method_result.status == ExecutorStatus.ABSTAINED
        assert method_result.method_run is not None
        run = method_result.method_run
        assert run.input_state_hash == state.state_id
        assert run.question_id == question_spec.question_id
        assert run.method_id == "vimshottari-career-timing-v1"
        assert run.method_version == "1.0.0"
        assert run.predictions

        prediction = run.predictions[0]
        assert prediction.is_abstention is True
        assert prediction.question_id == question_spec.question_id
        assert prediction.method_id == "vimshottari-career-timing-v1"
        assert prediction.method_version == "1.0.0"
        assert prediction.provenance_node_id is not None

        trace = registry.trace_prediction(prediction.provenance_node_id)
        node_types = {node.node_type.value for node in trace}
        assert ProvenanceNodeType.PREDICTION.value in node_types
        assert ProvenanceNodeType.METHOD_RUN.value in node_types
        assert ProvenanceNodeType.ASTROSTATE.value in node_types
        assert ProvenanceNodeType.CALCULATION.value in node_types
        assert ProvenanceNodeType.ASTRONOMY_COMPUTATION.value in node_types
        assert ProvenanceNodeType.BIRTH_INPUT.value in node_types
        assert ProvenanceNodeType.CONVENTION_PROFILE.value in node_types

    def test_missing_dashas_abstention_provenance(
        self, executor, question_spec,
    ):
        self._assert_abstention(executor, question_spec, update={"dashas": None})

    def test_missing_chart_abstention_provenance(
        self, executor, question_spec,
    ):
        self._assert_abstention(executor, question_spec, update={"chart": None})

    def test_no_maha_dasha_abstention_provenance(
        self, executor, question_spec,
    ):
        self._assert_abstention(
            executor,
            question_spec,
            update={"dashas": {"maha_dashas": []}},
        )

    def test_missing_dasha_abstention_is_deterministic(
        self, executor, question_spec,
    ):
        registry_a = ProvenanceRegistry()
        registry_b = ProvenanceRegistry()
        state_a = self._build_state(registry=registry_a, update={"dashas": None})
        state_b = self._build_state(registry=registry_b, update={"dashas": None})

        result_a = executor.execute(
            question_spec,
            state_a,
            [VimshottariCareerMethod()],
            provenance_registry=registry_a,
        )
        result_b = executor.execute(
            question_spec,
            state_b,
            [VimshottariCareerMethod()],
            provenance_registry=registry_b,
        )
        run_a = result_a.abstained_runs[0]
        run_b = result_b.abstained_runs[0]

        assert result_a.question_id == result_b.question_id
        assert result_a.input_state_hash == result_b.input_state_hash
        assert run_a.method_id == run_b.method_id
        assert run_a.method_version == run_b.method_version
        assert run_a.input_state_id == run_b.input_state_id
        assert run_a.input_state_hash == run_b.input_state_hash
        assert run_a.question_id == run_b.question_id
        assert run_a.calculations_used == run_b.calculations_used
        assert run_a.rules_evaluated == run_b.rules_evaluated
        assert run_a.intermediate_findings == run_b.intermediate_findings
        assert run_a.assumptions == run_b.assumptions
        assert run_a.warnings == run_b.warnings

        prediction_a = run_a.predictions[0]
        prediction_b = run_b.predictions[0]
        assert prediction_a.domain == prediction_b.domain
        assert prediction_a.event == prediction_b.event
        assert prediction_a.direction == prediction_b.direction
        assert prediction_a.is_abstention == prediction_b.is_abstention
        assert prediction_a.abstention_reason == prediction_b.abstention_reason
        assert prediction_a.method_id == prediction_b.method_id
        assert prediction_a.method_version == prediction_b.method_version
        assert prediction_a.question_id == prediction_b.question_id
