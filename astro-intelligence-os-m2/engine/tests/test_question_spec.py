"""Tests for QuestionSpec — canonical question contract."""

import pytest

from astro_engine.methods.question_spec import (
    DataQualityRequirement,
    MethodSelectionMode,
    QuestionSpec,
    make_question_spec,
)


class TestQuestionSpecIdentity:
    """Test deterministic identity and hashing."""

    def test_content_hash_stable(self) -> None:
        spec1 = QuestionSpec(
            question_id="test-1",
            domain="career",
            event_type="event_timing",
        )
        spec2 = QuestionSpec(
            question_id="test-2",  # different ID
            domain="career",
            event_type="event_timing",
        )
        # Different IDs should produce same content_hash (hash excludes question_id)
        assert spec1.content_hash() == spec2.content_hash()

    def test_content_hash_differs_on_domain(self) -> None:
        spec1 = QuestionSpec(
            question_id="test-1",
            domain="career",
            event_type="event_timing",
        )
        spec2 = QuestionSpec(
            question_id="test-1",
            domain="health",
            event_type="event_timing",
        )
        assert spec1.content_hash() != spec2.content_hash()

    def test_version_stable(self) -> None:
        spec = QuestionSpec(
            question_id="test-1",
            domain="career",
            event_type="event_timing",
        )
        version = spec.version()
        assert len(version) == 12
        assert isinstance(version, str)
        # Version is first 12 hex chars of content hash
        assert version == spec.content_hash()[:12]

    def test_with_question_id_preserves_hash(self) -> None:
        spec1 = QuestionSpec(
            question_id="original",
            domain="career",
            event_type="event_timing",
        )
        spec2 = spec1.with_question_id("new-id")
        assert spec1.content_hash() == spec2.content_hash()
        assert spec1.question_id != spec2.question_id

    def test_deterministic_serialization(self) -> None:
        import json
        spec = QuestionSpec(
            question_id="test-1",
            domain="career",
            event_type="event_timing",
            time_horizon=10.0,
            required_time_precision="month",
            requested_methods=["vimshottari-career-timing-v1"],
            method_selection_mode=MethodSelectionMode.EXPLICIT,
            data_quality_requirements=[DataQualityRequirement.RODDEN_A],
            constraints=["only_dasha_based"],
            metadata={"custom_key": "custom_value"},
        )
        data = spec.model_dump(mode="json")
        serialized = json.dumps(data, sort_keys=True)
        # Deserialize and re-serialize should match
        deserialized = json.loads(serialized)
        assert json.dumps(deserialized, sort_keys=True) == serialized


class TestQuestionSpecValidation:
    """Test validation of incomplete specs."""

    def test_is_complete_all_fields(self) -> None:
        spec = QuestionSpec(
            question_id="test-1",
            domain="career",
            event_type="event_timing",
        )
        assert spec.is_complete() is True

    def test_is_complete_missing_domain(self) -> None:
        spec = QuestionSpec(
            question_id="test-1",
            domain="",
            event_type="event_timing",
        )
        assert spec.is_complete() is False

    def test_is_complete_missing_event_type(self) -> None:
        spec = QuestionSpec(
            question_id="test-1",
            domain="career",
            event_type="",
        )
        assert spec.is_complete() is False

    def test_missing_fields(self) -> None:
        spec = QuestionSpec(
            question_id="",
            domain="",
            event_type="",
        )
        missing = spec.missing_fields()
        assert "question_id" in missing
        assert "domain" in missing
        assert "event_type" in missing

    def test_missing_fields_partial(self) -> None:
        spec = QuestionSpec(
            question_id="test-1",
            domain="career",
            event_type="",
        )
        missing = spec.missing_fields()
        assert "event_type" in missing
        assert "domain" not in missing


class TestQuestionSpecDefaults:
    """Test default values."""

    def test_defaults(self) -> None:
        spec = QuestionSpec(
            question_id="test-1",
            domain="career",
            event_type="event_timing",
        )
        assert spec.time_horizon is None
        assert spec.required_time_precision == "day"
        assert spec.requested_methods == []
        assert spec.method_selection_mode == MethodSelectionMode.AUTO
        assert spec.input_state_id is None
        assert spec.data_quality_requirements == []
        assert spec.constraints == []
        assert spec.metadata == {}


class TestQuestionSpecImmutability:
    """Test that QuestionSpec is frozen."""

    def test_cannot_mutation(self) -> None:
        spec = QuestionSpec(
            question_id="test-1",
            domain="career",
            event_type="event_timing",
        )
        with pytest.raises((ValueError, TypeError)):
            spec.domain = "health"


class TestMakeQuestionSpec:
    """Test the factory function."""

    def test_basic(self) -> None:
        spec = make_question_spec(
            question_id="q1",
            domain="career",
            event_type="event_timing",
        )
        assert spec.question_id == "q1"
        assert spec.domain == "career"

    def test_full(self) -> None:
        spec = make_question_spec(
            question_id="q1",
            domain="career",
            event_type="event_timing",
            time_horizon=20.0,
            required_time_precision="month",
            requested_methods=["method-a", "method-b"],
            method_selection_mode=MethodSelectionMode.ALL,
            data_quality_requirements=[DataQualityRequirement.RODDEN_AA],
            constraints=["no_transit"],
            metadata={"user_id": "u1"},
        )
        assert spec.time_horizon == 20.0
        assert spec.required_time_precision == "month"
        assert len(spec.requested_methods) == 2
        assert spec.method_selection_mode == MethodSelectionMode.ALL
        assert spec.input_state_id is None


class TestQuestionSpecInheritance:
    """Test QuestionSpec compatibility with existing methods."""

    def test_method_accepts_question_spec(self) -> None:
        """Vimshottari method should accept QuestionSpec."""
        from datetime import UTC, datetime

        from astro_engine.astronomy import AstronomyEngine
        from astro_engine.builder import AstroStateBuilder
        from astro_engine.conventions import PARASHARI_LAHIRI
        from astro_engine.methods.vimshottari_career import VimshottariCareerMethod
        from astro_engine.state import BirthInput

        bi = BirthInput(
            datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=UTC),
            timezone_name="UTC",
            latitude=28.6139,
            longitude=77.2090,
        )
        engine = AstronomyEngine()
        builder = AstroStateBuilder(engine)
        state = builder.build(bi, PARASHARI_LAHIRI)

        method = VimshottariCareerMethod()
        spec = QuestionSpec(
            question_id="test-1",
            domain="career",
            event_type="event_timing",
        )
        run = method.run(state, spec)
        assert run.method_id == "vimshottari-career-timing-v1"
        assert run.question_id == "test-1"
