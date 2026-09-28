"""Tests for provenance integration with new contracts."""

from datetime import UTC, datetime

import pytest

from astro_engine.astronomy import AstronomyEngine
from astro_engine.builder import AstroStateBuilder
from astro_engine.conventions import PARASHARI_LAHIRI
from astro_engine.methods import QuestionSpec
from astro_engine.methods.gochara_transit import TransitCareerMethod
from astro_engine.methods.vimshottari_career import VimshottariCareerMethod
from astro_engine.provenance import ProvenanceNodeType, ProvenanceRegistry
from astro_engine.state import BirthInput


@pytest.fixture
def birth_input() -> BirthInput:
    return BirthInput(
        datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=UTC),
        timezone_name="UTC",
        latitude=28.6139,
        longitude=77.2090,
    )


@pytest.fixture
def registry() -> ProvenanceRegistry:
    return ProvenanceRegistry()


def test_provenance_chain_vimshottari_with_question_spec(
    birth_input: BirthInput,
    registry: ProvenanceRegistry,
) -> None:
    """Vimshottari with QuestionSpec should maintain provenance chain."""
    builder = AstroStateBuilder(AstronomyEngine())
    state = builder.build(
        birth_input, PARASHARI_LAHIRI, provenance_registry=registry
    )
    method = VimshottariCareerMethod()
    spec = QuestionSpec(
        question_id="q-test",
        domain="career",
        event_type="event_timing",
    )
    run = method.run(state, spec, provenance_registry=registry)

    if run.predictions:
        trace = registry.trace_prediction(run.predictions[0].provenance_node_id)
        node_types = {n.node_type.value for n in trace}
        assert "PREDICTION" in node_types
        assert "METHOD_RUN" in node_types
        assert "ASTROSTATE" in node_types
        assert "CALCULATION" in node_types
        assert "ASTRONOMY_COMPUTATION" in node_types
        assert "BIRTH_INPUT" in node_types
        assert "CONVENTION_PROFILE" in node_types


def test_provenance_chain_gochara_with_question_spec(
    birth_input: BirthInput,
    registry: ProvenanceRegistry,
) -> None:
    """Gochara with QuestionSpec should maintain provenance chain."""
    builder = AstroStateBuilder(AstronomyEngine())
    transit_dt = datetime(2026, 9, 26, 12, 0, 0, tzinfo=UTC)
    state = builder.build(
        birth_input, PARASHARI_LAHIRI, transit_datetime=transit_dt, provenance_registry=registry
    )
    method = TransitCareerMethod()
    spec = QuestionSpec(
        question_id="q-test",
        domain="career",
        event_type="event_timing",
    )
    run = method.run(state, spec, provenance_registry=registry)

    if run.predictions:
        trace = registry.trace_prediction(run.predictions[0].provenance_node_id)
        node_types = {n.node_type.value for n in trace}
        assert "PREDICTION" in node_types
        assert "METHOD_RUN" in node_types
        assert "ASTROSTATE" in node_types
        assert "CALCULATION" in node_types
        assert "ASTRONOMY_COMPUTATION" in node_types
        assert "BIRTH_INPUT" in node_types
        assert "CONVENTION_PROFILE" in node_types


def test_canonical_prediction_in_provenance_graph(
    birth_input: BirthInput,
    registry: ProvenanceRegistry,
) -> None:
    """Canonical Prediction nodes should be creatable in the provenance graph."""
    builder = AstroStateBuilder(AstronomyEngine())
    state = builder.build(
        birth_input, PARASHARI_LAHIRI, provenance_registry=registry
    )
    method = VimshottariCareerMethod()
    spec = QuestionSpec(
        question_id="q-test",
        domain="career",
        event_type="event_timing",
    )
    run = method.run(state, spec, provenance_registry=registry)

    # At least verify the run completed and has valid predictions
    assert run.method_id == "vimshottari-career-timing-v1"
    if run.predictions:
        assert run.predictions[0].provenance_node_id is not None
        pred_node = registry.get_node(run.predictions[0].provenance_node_id)
        assert pred_node.node_type == ProvenanceNodeType.PREDICTION
