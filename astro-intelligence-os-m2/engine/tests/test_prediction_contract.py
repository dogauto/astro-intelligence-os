"""Tests for Prediction — canonical contract."""

import pytest

from astro_engine.methods import Prediction, PredictionDirection


class TestPredictionSchema:
    """Test Prediction schema validation."""

    def test_minimal_valid(self) -> None:
        """Test minimal Prediction construction."""
        pred = Prediction(
            domain="career",
            event="career_period_activation",
        )
        assert pred.domain == "career"
        assert pred.event == "career_period_activation"
        assert pred.direction == PredictionDirection.UNKNOWN
        assert pred.is_abstention is False

    def test_full_valid(self) -> None:
        """Test full Prediction construction."""
        pred = Prediction(
            prediction_id="pred-1",
            question_id="q-1",
            domain="career",
            event="career_period_activation",
            event_type="career_activation",
            direction=PredictionDirection.POSITIVE,
            magnitude=0.75,
            signal_strength=0.8,
            time_window_start=None,
            time_window_end=None,
            duration_description="Maha Dasha of Jupiter (16 years)",
            conditions=["10th lord in 10th house"],
            supporting_signals=["Jupiter in good house"],
            supporting_evidence=["Rule R1 applied"],
            contradictory_evidence=[],
            evidence_references=["rule_R1", "dasha_jupiter"],
            method_id="vimshottari-career-timing-v1",
            method_version="1.0.0",
            raw_confidence=0.75,
            is_abstention=False,
            abstention_reason=None,
            provenance={},
            provenance_node_id="pred-node-1",
        )
        assert pred.prediction_id == "pred-1"
        assert pred.question_id == "q-1"
        assert pred.event_type == "career_activation"
        assert pred.signal_strength == 0.8


class TestPredictionImmutability:
    """Test Prediction immutability."""

    def test_frozen(self) -> None:
        pred = Prediction(domain="career", event="test")
        with pytest.raises((ValueError, TypeError)):
            pred.domain = "health"


class TestPredictionSignalStrength:
    """Test that signal_strength is distinct from confidence."""

    def test_signal_strength_no_probability(self) -> None:
        """signal_strength should exist without raw_confidence."""
        pred = Prediction(
            domain="career",
            event="test",
            signal_strength=0.75,
        )
        assert pred.signal_strength == 0.75
        assert pred.raw_confidence is None

    def test_signal_strength_not_probability(self) -> None:
        """signal_strength should be heuristic, not calibrated."""
        pred = Prediction(
            domain="career",
            event="test",
            signal_strength=0.5,
            raw_confidence=0.9,
        )
        assert pred.signal_strength is not None
        assert pred.raw_confidence is not None
        # They can be different - signal_strength is method heuristic,
        # raw_confidence is the method's own calibration
        assert pred.signal_strength != pred.raw_confidence


class TestPredictionAbstention:
    """Test abstention handling."""

    def test_is_abstention_default_false(self) -> None:
        pred = Prediction(domain="career", event="test")
        assert pred.is_abstention is False

    def test_is_abstention_true(self) -> None:
        pred = Prediction(
            domain="career",
            event="test",
            is_abstention=True,
            abstention_reason="Missing transit data",
        )
        assert pred.is_abstention is True
        assert pred.abstention_reason == "Missing transit data"

    def test_abstention_has_no_direction(self) -> None:
        """Abstention predictions should have UNKNOWN direction."""
        pred = Prediction(
            domain="career",
            event="test",
            is_abstention=True,
            abstention_reason="No data",
        )
        assert pred.direction == PredictionDirection.UNKNOWN


class TestPredictionTimeWindow:
    """Test time window validation."""

    def test_time_window_valid(self) -> None:
        from datetime import UTC, datetime
        pred = Prediction(
            domain="career",
            event="test",
            time_window_start=datetime(2024, 1, 1, tzinfo=UTC),
            time_window_end=datetime(2025, 1, 1, tzinfo=UTC),
        )
        assert pred.time_window_start is not None and pred.time_window_start.year == 2024
        assert pred.time_window_end is not None and pred.time_window_end.year == 2025

    def test_time_window_optional(self) -> None:
        pred = Prediction(domain="career", event="test")
        assert pred.time_window_start is None
        assert pred.time_window_end is None


class TestPredictionQuestionLink:
    """Test Prediction links to QuestionSpec."""

    def test_question_id_preserved(self) -> None:
        pred = Prediction(
            domain="career",
            event="test",
            question_id="q-123",
        )
        assert pred.question_id == "q-123"

    def test_question_id_optional(self) -> None:
        pred = Prediction(domain="career", event="test")
        assert pred.question_id is None


class TestPredictionProvenance:
    """Test Prediction provenance link."""

    def test_provenance_node_id(self) -> None:
        pred = Prediction(
            domain="career",
            event="test",
            provenance_node_id="pred-node-abc",
        )
        assert pred.provenance_node_id == "pred-node-abc"

    def test_provenance_empty_by_default(self) -> None:
        pred = Prediction(domain="career", event="test")
        assert pred.provenance == {}
