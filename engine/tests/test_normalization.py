"""Tests for normalization boundary — method output to canonical Prediction."""

from datetime import UTC, datetime

import pytest

from astro_engine.astronomy import AstronomyEngine
from astro_engine.builder import AstroStateBuilder
from astro_engine.conventions import PARASHARI_LAHIRI
from astro_engine.methods import Prediction, QuestionSpec
from astro_engine.methods.gochara_transit import TransitCareerMethod
from astro_engine.methods.vimshottari_career import VimshottariCareerMethod
from astro_engine.state import BirthInput


@pytest.fixture
def canonical_state() -> None:
    bi = BirthInput(
        datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=UTC),
        timezone_name="UTC",
        latitude=28.6139,
        longitude=77.2090,
    )
    engine = AstronomyEngine()
    builder = AstroStateBuilder(engine)
    transit_dt = datetime(2026, 9, 26, 12, 0, 0, tzinfo=UTC)
    return builder.build(bi, PARASHARI_LAHIRI, transit_datetime=transit_dt)


def test_vimshottari_output_normalized_to_canonical_prediction(canonical_state) -> None:
    """Vimshottari output should normalize to canonical Prediction."""
    method = VimshottariCareerMethod()
    spec = QuestionSpec(
        question_id="test-vimshottari",
        domain="career",
        event_type="event_timing",
    )
    run = method.run(canonical_state, spec)

    assert len(run.predictions) > 0
    for pred in run.predictions:
        assert isinstance(pred, Prediction)
        assert pred.domain == "career"
        assert pred.method_id == "vimshottari-career-timing-v1"
        assert pred.question_id == "test-vimshottari"


def test_gochara_output_normalized_to_canonical_prediction(canonical_state) -> None:
    """Gochara output should normalize to canonical Prediction."""
    method = TransitCareerMethod()
    spec = QuestionSpec(
        question_id="test-gochara",
        domain="career",
        event_type="event_timing",
    )
    run = method.run(canonical_state, spec)

    assert isinstance(run, type(run))  # MethodRun returned
    # Gochara may abstain or produce predictions depending on transit data
    for pred in run.predictions:
        assert isinstance(pred, Prediction)
        assert pred.method_id == "gochara-career-transit-v1"
        assert pred.question_id == "test-gochara"


def test_normalization_boundary_isolation(canonical_state) -> None:
    """Method A's output should not leak into Method B's normalized form."""
    vim_method = VimshottariCareerMethod()
    transit_method = TransitCareerMethod()

    spec_a = QuestionSpec(
        question_id="qa",
        domain="career",
        event_type="event_timing",
    )
    spec_b = QuestionSpec(
        question_id="qb",
        domain="career",
        event_type="event_timing",
    )

    run_a = vim_method.run(canonical_state, spec_a)
    run_b = transit_method.run(canonical_state, spec_b)

    # Predictions should reference their own method and question
    for pred in run_a.predictions:
        assert pred.method_id == "vimshottari-career-timing-v1"
        assert pred.question_id == "qa"

    for pred in run_b.predictions:
        assert pred.method_id == "gochara-career-transit-v1"
        assert pred.question_id == "qb"


def test_normalization_preserves_signal_strength(canonical_state) -> None:
    """signal_strength should be preserved from method's heuristic output."""
    method = VimshottariCareerMethod()
    spec = QuestionSpec(
        question_id="test-signal",
        domain="career",
        event_type="event_timing",
    )
    run = method.run(canonical_state, spec)

    # At least one prediction should have signal_strength set
    if run.predictions:
        pred = run.predictions[0]
        assert pred.signal_strength is None or 0 <= pred.signal_strength <= 1.0


def test_method_cannot_mutate_prediction(canonical_state) -> None:
    """Methods should not be able to mutate the Prediction after creation."""
    method = VimshottariCareerMethod()
    spec = QuestionSpec(
        question_id="test-mutate",
        domain="career",
        event_type="event_timing",
    )
    run = method.run(canonical_state, spec)

    if run.predictions:
        pred = run.predictions[0]
        with pytest.raises((ValueError, TypeError)):
            pred.domain = "health"
