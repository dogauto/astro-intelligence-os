"""Tests for the QuestionContext → QuestionSpec compatibility adapter.

These tests verify that:
1. The abstract Method contract uses QuestionSpec (not QuestionContext).
2. QuestionContext can only enter through the explicit adapter.
3. The adapter produces an equivalent QuestionSpec.
4. No concrete method requires QuestionContext directly.
5. question_id propagates identically through the full chain.
"""

from datetime import UTC, datetime
from inspect import signature as inspect_signature

from astro_engine.astronomy import AstronomyEngine
from astro_engine.builder import AstroStateBuilder
from astro_engine.conventions import PARASHARI_LAHIRI
from astro_engine.methods import Method, MethodRun, QuestionSpec
from astro_engine.methods.gochara_transit import TransitCareerMethod
from astro_engine.methods.question_spec import question_context_to_spec
from astro_engine.methods.vimshottari_career import VimshottariCareerMethod
from astro_engine.provenance import ProvenanceRegistry
from astro_engine.state import BirthInput


def _make_state() -> object:
    engine = AstronomyEngine()
    builder = AstroStateBuilder(engine)
    bi = BirthInput(
        datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=UTC),
        timezone_name="UTC",
        latitude=28.6139,
        longitude=77.2090,
    )
    return builder.build(bi, PARASHARI_LAHIRI)


class TestAbstractMethodContract:
    """The canonical Method interface must accept QuestionSpec only."""

    def test_method_run_signature_accepts_question_spec(self) -> None:
        """Method.run question parameter is QuestionSpec in the signature."""
        sig = inspect_signature(Method.run)
        q_param = sig.parameters["question"]
        assert q_param.annotation == "QuestionSpec"

    def test_method_can_handle_signature_accepts_question_spec(self) -> None:
        """Method.can_handle question parameter is QuestionSpec in the signature."""
        sig = inspect_signature(Method.can_handle)
        q_param = sig.parameters["question"]
        assert q_param.annotation == "QuestionSpec"

    def test_method_run_accepts_question_spec(self) -> None:
        """Vimshottari accepts a canonical QuestionSpec."""
        state = _make_state()
        method = VimshottariCareerMethod()
        spec = QuestionSpec(
            question_id="test-q",
            domain="career",
            event_type="event_timing",
        )
        run = method.run(state, spec)
        assert isinstance(run, MethodRun)
        assert run.question_id == "test-q"

    def test_gochara_accepts_question_spec(self) -> None:
        """Gochara accepts a canonical QuestionSpec."""
        state = _make_state()
        method = TransitCareerMethod()
        spec = QuestionSpec(
            question_id="test-gc",
            domain="career",
            event_type="event_timing",
        )
        run = method.run(state, spec)
        assert isinstance(run, MethodRun)
        assert run.question_id == "test-gc"


class TestAdapterBoundary:
    """QuestionContext can only enter via the adapter."""

    def test_adapter_produces_question_spec(self) -> None:
        """question_context_to_spec returns a QuestionSpec."""
        from astro_engine.methods import QuestionContext

        ctx = QuestionContext(
            domain="career",
            task="event_timing",
            event="career_transition",
            time_horizon_years=10.0,
            raw_question="When will my career activate?",
        )
        spec = question_context_to_spec(ctx)
        assert isinstance(spec, QuestionSpec)
        assert spec.domain == "career"
        assert spec.event_type == "career_transition"
        assert spec.time_horizon == 10.0

    def test_adapter_derives_question_id(self) -> None:
        """Adapter derives a deterministic question_id when none given."""
        from astro_engine.methods import QuestionContext

        ctx = QuestionContext(
            domain="career",
            task="event_timing",
        )
        spec = question_context_to_spec(ctx)
        assert spec.question_id is not None
        assert len(spec.question_id) == 16

    def test_adapter_explicit_question_id(self) -> None:
        """Adapter respects an explicit question_id."""
        from astro_engine.methods import QuestionContext

        ctx = QuestionContext(
            domain="career",
            task="event_timing",
        )
        spec = question_context_to_spec(ctx, question_id="my-explicit-id")
        assert spec.question_id == "my-explicit-id"

    def test_adapter_is_documented_deprecated(self) -> None:
        """The adapter is documented as deprecated."""
        from astro_engine.methods.question_spec import question_context_to_spec

        doc = question_context_to_spec.__doc__ or ""
        assert "deprecated" in doc.lower() or "compatibility" in doc.lower()


class TestQuestionIdPropagation:
    """question_id must flow identically through the entire chain."""

    def test_question_id_flow_vimshottari(self) -> None:
        """question_id: QuestionSpec → MethodRun → Prediction → PredictionNode."""
        state = _make_state()
        method = VimshottariCareerMethod()
        registry = ProvenanceRegistry()
        spec = QuestionSpec(
            question_id="q-propagation-1",
            domain="career",
            event_type="event_timing",
        )
        run = method.run(state, spec, provenance_registry=registry)

        assert run.question_id == "q-propagation-1"
        assert len(run.predictions) > 0
        pred = run.predictions[0]
        assert pred.question_id == "q-propagation-1"
        assert pred.provenance_node_id is not None
        node = registry.get_node(pred.provenance_node_id)
        assert node.question_id == "q-propagation-1"

    def test_question_id_flow_gochara(self) -> None:
        """question_id: QuestionSpec → MethodRun (even if abstaining)."""
        state = _make_state()
        method = TransitCareerMethod()
        spec = QuestionSpec(
            question_id="q-propagation-2",
            domain="career",
            event_type="event_timing",
        )
        run = method.run(state, spec)

        # MethodRun must always carry question_id regardless of predictions
        assert run.question_id == "q-propagation-2"

    def test_adapter_preserves_question_id_identity(self) -> None:
        """Adapter-derived question_id is stable for identical Context input."""
        from astro_engine.methods import QuestionContext

        ctx = QuestionContext(
            domain="career",
            task="event_timing",
            event="career_transition",
        )
        spec1 = question_context_to_spec(ctx)
        spec2 = question_context_to_spec(ctx)
        assert spec1.question_id == spec2.question_id


class TestNoQuestionContextInMethodSignatures:
    """Verify that no concrete method accepts QuestionContext in its signature."""

    def test_vimshottari_does_not_accept_question_context(self) -> None:
        """VimshottariCareerMethod.run signature does not include QuestionContext."""
        sig = inspect_signature(VimshottariCareerMethod.run)
        annotation = str(sig.parameters["question"].annotation)
        assert "QuestionSpec" in annotation
        assert "QuestionContext" not in annotation

    def test_gochara_does_not_accept_question_context(self) -> None:
        """TransitCareerMethod.run signature does not include QuestionContext."""
        sig = inspect_signature(TransitCareerMethod.run)
        annotation = str(sig.parameters["question"].annotation)
        assert "QuestionSpec" in annotation
        assert "QuestionContext" not in annotation

    def test_methodrun_question_field_is_question_spec_only(self) -> None:
        """MethodRun.question field type annotation is QuestionSpec only."""
        import typing
        hints = typing.get_type_hints(MethodRun)
        q_hint = str(hints["question"])
        assert "QuestionSpec" in q_hint
        assert "QuestionContext" not in q_hint
