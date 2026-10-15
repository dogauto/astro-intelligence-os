"""Tests for MethodRun — hardened output contract."""

import pytest

from astro_engine.methods import MethodRun
from astro_engine.methods.question_spec import QuestionSpec


class TestMethodRunSchema:
    """Test MethodRun schema validation."""

    def test_minimal_valid(self) -> None:
        """Test that a minimal MethodRun can be constructed."""
        run = MethodRun(
            method_id="test-method-v1",
            method_version="1.0.0",
            input_state_id="state-abc123",
            question=QuestionSpec(question_id="test", domain="career", event_type="event_timing"),
        )
        assert run.method_id == "test-method-v1"
        assert run.method_version == "1.0.0"
        assert run.input_state_id == "state-abc123"
        assert len(run.predictions) == 0
        assert len(run.rules_evaluated) == 0

    def test_full_valid(self) -> None:
        """Test that a full MethodRun can be constructed."""
        run = MethodRun(
            method_id="test-method-v1",
            method_version="1.0.0",
            input_state_id="state-abc123",
            input_state_hash="state-abc123",
            question_id="q-1",
            question=QuestionSpec(
                question_id="q-1",
                domain="career",
                event_type="event_timing",
            ),
            calculations_used=["planets", "dashas"],
            rules_evaluated=["R1", "R2"],
            intermediate_findings=[{"finding": "test"}],
            candidate_events=[{"event": "test_event"}],
            timing_windows=[{"window": "2024-01-01"}],
            predictions=[],
            assumptions=["assumption 1"],
            abstentions=[{"reason": "missing data"}],
            unknowns=["unknown factor"],
            warnings=["warning 1"],
        )
        assert run.method_id == "test-method-v1"
        assert run.input_state_hash == "state-abc123"
        assert run.question_id == "q-1"
        assert len(run.calculations_used) == 2
        assert len(run.rules_evaluated) == 2


class TestMethodRunImmutability:
    """Test that MethodRun cannot be mutated."""

    def test_frozen(self) -> None:
        """MethodRun must be immutable after creation."""
        run = MethodRun(
            method_id="test-method-v1",
            method_version="1.0.0",
            input_state_id="state-abc123",
            question=QuestionSpec(question_id="test", domain="career", event_type="event_timing"),
        )
        with pytest.raises((ValueError, TypeError)):
            run.method_id = "changed"


class TestMethodRunIdentity:
    """Test MethodRun identity."""

    def test_method_identity(self) -> None:
        run = MethodRun(
            method_id="my-method",
            method_version="2.0.0",
            input_state_id="state-1",
            question=QuestionSpec(question_id="test", domain="career", event_type="event_timing"),
        )
        assert run.method_id == "my-method"
        assert run.method_version == "2.0.0"

    def test_input_state_identity(self) -> None:
        """input_state_id must be populated."""
        run = MethodRun(
            method_id="test",
            method_version="1.0.0",
            input_state_id="state-abc",
            question=QuestionSpec(question_id="test", domain="career", event_type="event_timing"),
        )
        assert run.input_state_id == "state-abc"

    def test_question_id_preserved(self) -> None:
        """question_id must be preserved through MethodRun."""
        spec = QuestionSpec(
            question_id="q-123",
            domain="career",
            event_type="event_timing",
        )
        run = MethodRun(
            method_id="test",
            method_version="1.0.0",
            input_state_id="state-abc",
            question_id="q-123",
            question=spec,
        )
        assert run.question_id == "q-123"


class TestMethodRunAbstention:
    """Test abstention handling."""

    def test_abstention_record(self) -> None:
        """MethodRun should preserve abstention records."""
        run = MethodRun(
            method_id="test",
            method_version="1.0.0",
            input_state_id="state-abc",
            question=QuestionSpec(question_id="test", domain="career", event_type="event_timing"),
            abstentions=[
                {"reason": "missing dasha data", "timestamp": "2024-01-01T00:00:00Z"}
            ],
        )
        assert len(run.abstentions) == 1
        assert run.abstentions[0]["reason"] == "missing dasha data"

    def test_unknowns_recorded(self) -> None:
        """MethodRun should record unknowns."""
        run = MethodRun(
            method_id="test",
            method_version="1.0.0",
            input_state_id="state-abc",
            question=QuestionSpec(question_id="test", domain="career", event_type="event_timing"),
            unknowns=["nakshatra_pada_not_computed"],
        )
        assert "nakshatra_pada_not_computed" in run.unknowns


class TestMethodRunWithQuestionSpec:
    """Test MethodRun with QuestionSpec."""

    def test_accepts_question_spec(self) -> None:
        """MethodRun should accept QuestionSpec as question."""
        spec = QuestionSpec(
            question_id="q-1",
            domain="career",
            event_type="event_timing",
        )
        run = MethodRun(
            method_id="test",
            method_version="1.0.0",
            input_state_id="state-abc",
            question_id="q-1",
            question=spec,
        )
        assert run.question_id == "q-1"
        assert run.question.domain == "career"
        assert run.question_id == "q-1"
