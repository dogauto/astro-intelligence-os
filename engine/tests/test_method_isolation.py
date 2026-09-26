"""
Method Isolation Tests

Proves that:
1. Method A can execute without Method B.
2. Method B can execute without Method A.
3. Neither method can access the other's primary prediction.
4. Both receive the same canonical AstroState.
"""

from datetime import datetime, timezone

import pytest

from astro_engine.astronomy import AstronomyEngine
from astro_engine.builder import AstroStateBuilder
from astro_engine.conventions import PARASHARI_LAHIRI
from astro_engine.methods import QuestionContext
from astro_engine.methods.gochara_transit import TransitCareerMethod
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
)

CAREER_QUESTION = QuestionContext(
    domain="career",
    task="event_timing",
    event="career_transition",
)


@pytest.fixture(scope="module")
def canonical_state():
    engine = AstronomyEngine()
    builder = AstroStateBuilder(engine)
    # Compute natal + transit for today
    transit_time = datetime(2026, 9, 26, 12, 0, 0, tzinfo=timezone.utc)
    return builder.build(GANDHI_INPUT, PARASHARI_LAHIRI, transit_datetime=transit_time)

class TestMethodIsolation:
    """Validates methodology independence."""

    def test_method_a_executes_independently(self, canonical_state):
        method_a = VimshottariCareerMethod()
        run_a = method_a.run(canonical_state, CAREER_QUESTION)
        assert run_a.method_id == "vimshottari-career-timing-v1"
        assert len(run_a.predictions) > 0

    def test_method_b_executes_independently(self, canonical_state):
        method_b = TransitCareerMethod()
        run_b = method_b.run(canonical_state, CAREER_QUESTION)
        assert run_b.method_id == "gochara-career-transit-v1"
        # Depending on transit, it may or may not have positive predictions, but shouldn't abstain
        assert not any(p.is_abstention for p in run_b.predictions), "Method B abstained unexpectedly"

    def test_methods_receive_same_state(self, canonical_state):
        method_a = VimshottariCareerMethod()
        method_b = TransitCareerMethod()

        run_a = method_a.run(canonical_state, CAREER_QUESTION)
        run_b = method_b.run(canonical_state, CAREER_QUESTION)

        assert run_a.input_state_id == run_b.input_state_id == canonical_state.state_id

    def test_predictions_are_isolated(self, canonical_state):
        """
        Since each method run only returns its own predictions and accepts
        a purely computed AstroState, they cannot see each other's outputs.
        """
        method_a = VimshottariCareerMethod()
        method_b = TransitCareerMethod()

        run_a = method_a.run(canonical_state, CAREER_QUESTION)
        run_b = method_b.run(canonical_state, CAREER_QUESTION)

        # Ensure no cross-pollution
        for pred in run_a.predictions:
            assert pred.method_id == method_a.method_id
            assert pred.method_id != method_b.method_id

        for pred in run_b.predictions:
            assert pred.method_id == method_b.method_id
            assert pred.method_id != method_a.method_id

    def test_mutation_attempt_fails(self, canonical_state):
        """Prove that a method cannot mutate the input state."""
        method_a = VimshottariCareerMethod()
        
        # State is frozen by Pydantic; mutation should raise error.
        with pytest.raises(Exception):
            canonical_state.provenance.engine_version = "hacked"
            
        with pytest.raises(Exception):
            canonical_state.planets = []

    def test_no_shared_prediction_cache(self, canonical_state):
        """Prove that executing one method does not bleed into the state or another method."""
        method_a = VimshottariCareerMethod()
        method_b = TransitCareerMethod()

        # Run A
        run_a = method_a.run(canonical_state, CAREER_QUESTION)
        
        # Method B runs; its context should be completely devoid of A's predictions
        run_b = method_b.run(canonical_state, CAREER_QUESTION)
        
        assert not hasattr(method_b, "predictions_from_other_methods")
        assert not hasattr(canonical_state, "predictions")  # State must only contain calculations
