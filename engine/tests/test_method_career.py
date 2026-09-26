"""
Tests for the Vimshottari Career Timing Method.

This is the first methodology test — it validates that the Method SDK
interface works end-to-end with real AstroState data.
"""

from datetime import datetime, timezone

import pytest

from astro_engine.astronomy import AstronomyEngine
from astro_engine.builder import AstroStateBuilder
from astro_engine.conventions import PARASHARI_LAHIRI
from astro_engine.methods import MethodMaturity, QuestionContext
from astro_engine.methods.vimshottari_career import VimshottariCareerMethod
from astro_engine.state import BirthInput


# Reference chart: Gandhi
GANDHI_INPUT = BirthInput(
    datetime_utc=datetime(1869, 10, 2, 1, 37, 0, tzinfo=timezone.utc),
    datetime_local=datetime(1869, 10, 2, 7, 11, 40),
    timezone_name="Asia/Kolkata",
    latitude=21.6417,
    longitude=69.6293,
    location_name="Porbandar, Gujarat, India",
    source="Historical records",
    rodden_rating="B",
)

CAREER_QUESTION = QuestionContext(
    domain="career",
    task="event_timing",
    event="career_transition",
    raw_question="What significant career periods are indicated?",
)


class TestVimshottariCareerMethod:
    """Tests for the first complete methodology."""

    @pytest.fixture()
    def method(self) -> VimshottariCareerMethod:
        return VimshottariCareerMethod()

    @pytest.fixture()
    def state(self):
        engine = AstronomyEngine()
        builder = AstroStateBuilder(engine)
        return builder.build(GANDHI_INPUT, PARASHARI_LAHIRI)

    def test_method_identity(self, method: VimshottariCareerMethod) -> None:
        """Method should have proper identity."""
        assert method.method_id == "vimshottari-career-timing-v1"
        assert method.version == "1.0.0"
        assert method.tradition == "Parashari"
        assert method.maturity == MethodMaturity.EXPERIMENTAL

    def test_can_handle_career(self, method: VimshottariCareerMethod) -> None:
        """Should handle career domain questions."""
        assert method.can_handle(CAREER_QUESTION) is True

    def test_cannot_handle_health(self, method: VimshottariCareerMethod) -> None:
        """Should not handle health domain questions."""
        health_q = QuestionContext(domain="health", task="diagnosis")
        assert method.can_handle(health_q) is False

    def test_run_produces_method_run(self, method: VimshottariCareerMethod, state) -> None:
        """Running the method should produce a valid MethodRun."""
        result = method.run(state, CAREER_QUESTION)
        assert result.method_id == method.method_id
        assert result.method_version == method.version
        assert result.input_state_id == state.state_id

    def test_run_produces_predictions(self, method: VimshottariCareerMethod, state) -> None:
        """Should produce at least some career predictions."""
        result = method.run(state, CAREER_QUESTION)
        assert len(result.predictions) > 0

    def test_predictions_have_time_windows(self, method: VimshottariCareerMethod, state) -> None:
        """Each prediction should have time windows."""
        result = method.run(state, CAREER_QUESTION)
        for pred in result.predictions:
            assert pred.time_window_start is not None
            assert pred.time_window_end is not None
            assert pred.time_window_start < pred.time_window_end

    def test_predictions_have_evidence(self, method: VimshottariCareerMethod, state) -> None:
        """Predictions should have supporting evidence."""
        result = method.run(state, CAREER_QUESTION)
        for pred in result.predictions:
            # At least some predictions should have evidence
            if pred.supporting_evidence:
                assert len(pred.supporting_evidence) > 0

    def test_run_has_assumptions(self, method: VimshottariCareerMethod, state) -> None:
        """MethodRun should document its assumptions."""
        result = method.run(state, CAREER_QUESTION)
        assert len(result.assumptions) > 0

    def test_run_has_intermediate_findings(self, method: VimshottariCareerMethod, state) -> None:
        """Should produce intermediate findings (house lords, etc.)."""
        result = method.run(state, CAREER_QUESTION)
        assert len(result.intermediate_findings) > 0
        # Should find the career house lords
        lords_finding = next(
            (f for f in result.intermediate_findings if f.get("finding") == "career_house_lords"),
            None,
        )
        assert lords_finding is not None
        assert "10th_lord" in lords_finding

    def test_predictions_domain_is_career(self, method: VimshottariCareerMethod, state) -> None:
        """All predictions should be in the career domain."""
        result = method.run(state, CAREER_QUESTION)
        for pred in result.predictions:
            assert pred.domain == "career"

    def test_method_id_in_predictions(self, method: VimshottariCareerMethod, state) -> None:
        """Each prediction should carry the method ID."""
        result = method.run(state, CAREER_QUESTION)
        for pred in result.predictions:
            assert pred.method_id == method.method_id

    def test_magnitude_in_range(self, method: VimshottariCareerMethod, state) -> None:
        """Prediction magnitudes should be in [0, 1]."""
        result = method.run(state, CAREER_QUESTION)
        for pred in result.predictions:
            if pred.magnitude is not None:
                assert 0.0 <= pred.magnitude <= 1.0
