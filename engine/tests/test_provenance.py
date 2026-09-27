from datetime import UTC, datetime

import pytest

from astro_engine.astronomy import AstronomyEngine
from astro_engine.builder import AstroStateBuilder
from astro_engine.conventions import AyanamsaType, ConventionProfile, HouseSystem
from astro_engine.methods import QuestionContext
from astro_engine.methods.vimshottari_career import VimshottariCareerMethod
from astro_engine.provenance import (
    ProvenanceIntegrityError,
    ProvenanceNodeType,
    ProvenanceRegistry,
)
from astro_engine.state import BirthInput


@pytest.fixture
def provenance_registry():
    return ProvenanceRegistry()

@pytest.fixture
def birth_input():
    return BirthInput(
        datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=UTC),
        timezone_name="UTC",
        latitude=28.6139,
        longitude=77.2090,
    )

@pytest.fixture
def convention():
    return ConventionProfile(
        id="test-profile",
        name="Test Profile",
        ayanamsa=AyanamsaType.LAHIRI,
        house_system=HouseSystem.PLACIDUS
    )

@pytest.fixture
def test_state_and_prediction(birth_input, convention, provenance_registry):
    engine = AstronomyEngine()
    builder = AstroStateBuilder(engine)
    state = builder.build(birth_input, convention, provenance_registry=provenance_registry)

    method = VimshottariCareerMethod()
    question = QuestionContext(domain="career", task="event_timing")
    method_run = method.run(state, question, provenance_registry=provenance_registry)

    # Asserting basic requirements
    assert method_run.provenance_node_id is not None
    assert len(method_run.predictions) > 0
    prediction = method_run.predictions[0]
    assert prediction.provenance_node_id is not None

    return state, method_run, prediction

def test_full_provenance_trace(test_state_and_prediction, provenance_registry):
    """Test tracing a prediction back to BirthInput."""
    state, method_run, prediction = test_state_and_prediction

    trace = provenance_registry.trace_prediction(prediction.provenance_node_id)

    # Trace should contain nodes of all types in the chain
    node_types = {node.node_type for node in trace}
    assert "PREDICTION" in node_types
    assert "RULE" in node_types
    assert "METHOD_RUN" in node_types
    assert "ASTRONOMY_COMPUTATION" in node_types
    assert "CONVENTION_PROFILE" in node_types
    assert "BIRTH_INPUT" in node_types

def test_missing_prediction(provenance_registry):
    with pytest.raises(ProvenanceIntegrityError):
        provenance_registry.trace_prediction("non-existent-id")

def test_broken_dependency_id(test_state_and_prediction, provenance_registry):
    """Test tracing fails if a parent ID is missing from the registry."""
    state, method_run, prediction = test_state_and_prediction

    # Get a node and intentionally mess up its parent ID
    pred_node = provenance_registry.get_node(prediction.provenance_node_id)
    original_hash = pred_node.content_hash
    pred_node.parent_ids.append("fake-broken-id")
    # Recompute hash to reflect modified content
    pred_node.content_hash = pred_node.compute_hash(pred_node._content_dict())

    with pytest.raises(ProvenanceIntegrityError, match="Missing provenance node: fake-broken-id"):
        provenance_registry.trace_prediction(prediction.provenance_node_id)

def test_modified_state_hash(test_state_and_prediction, provenance_registry):
    """Test that modifying node content changes the deterministic hash."""
    state, method_run, prediction = test_state_and_prediction

    birth_node = [n for n in provenance_registry._nodes.values() if n.node_type == "BIRTH_INPUT"][0]
    original_hash = birth_node.content_hash

    # Modify data and recompute
    new_data = birth_node.model_dump(exclude={"node_id", "timestamp", "content_hash"})
    new_data["latitude"] = 99.99
    new_hash = birth_node.compute_hash(new_data)

    assert original_hash != new_hash

def test_determinism(birth_input, convention):
    """Test that two runs with the exact same input produce the exact same hashes."""
    registry_a = ProvenanceRegistry()
    registry_b = ProvenanceRegistry()

    engine = AstronomyEngine()
    builder = AstroStateBuilder(engine)

    state_a = builder.build(birth_input, convention, provenance_registry=registry_a)
    state_b = builder.build(birth_input, convention, provenance_registry=registry_b)

    method = VimshottariCareerMethod()
    question = QuestionContext(domain="career", task="event_timing")

    run_a = method.run(state_a, question, provenance_registry=registry_a)
    run_b = method.run(state_b, question, provenance_registry=registry_b)

    pred_node_a = registry_a.get_node(run_a.predictions[0].provenance_node_id)
    pred_node_b = registry_b.get_node(run_b.predictions[0].provenance_node_id)

    # Hashes of identical predictions generated at different times must match exactly
    assert pred_node_a.content_hash == pred_node_b.content_hash

def test_provenance_does_not_alter_astrology(birth_input, convention):
    """Test that running with and without provenance registry yields identical predictions."""
    engine = AstronomyEngine()
    builder = AstroStateBuilder(engine)
    method = VimshottariCareerMethod()
    question = QuestionContext(domain="career", task="event_timing")

    # Run without provenance
    state_clean = builder.build(birth_input, convention)
    run_clean = method.run(state_clean, question)

    # Run with provenance
    registry = ProvenanceRegistry()
    state_prov = builder.build(birth_input, convention, provenance_registry=registry)
    run_prov = method.run(state_prov, question, provenance_registry=registry)

    # Validate the predictions list is identical, except for provenance metadata
    assert len(run_clean.predictions) == len(run_prov.predictions)
    for p_clean, p_prov in zip(run_clean.predictions, run_prov.predictions):
        assert p_clean.domain == p_prov.domain
        assert p_clean.event == p_prov.event
        assert p_clean.magnitude == p_prov.magnitude
        assert p_clean.conditions == p_prov.conditions

    assert run_clean.predictions[0].provenance_node_id is None
    assert run_prov.predictions[0].provenance_node_id is not None


def test_astorstate_node_registered(test_state_and_prediction, provenance_registry):
    """Test that AstroStateNode is registered in the provenance graph."""
    state, method_run, prediction = test_state_and_prediction

    trace = provenance_registry.trace_prediction(prediction.provenance_node_id)
    node_types = {node.node_type for node in trace}
    assert ProvenanceNodeType.ASTROSTATE in node_types


def test_astorstate_node_state_id_matches(test_state_and_prediction, provenance_registry):
    """Test that AstroStateNode.state_id equals the actual AstroState.state_id."""
    state, method_run, prediction = test_state_and_prediction

    trace = provenance_registry.trace_prediction(prediction.provenance_node_id)
    astrostate_node = next(n for n in trace if n.node_type == ProvenanceNodeType.ASTROSTATE)
    assert astrostate_node.state_id == state.state_id


def test_trace_reaches_astorstate_node(test_state_and_prediction, provenance_registry):
    """Test that trace_prediction reaches the AstroStateNode."""
    state, method_run, prediction = test_state_and_prediction

    trace = provenance_registry.trace_prediction(prediction.provenance_node_id)
    astrostate_node = next(n for n in trace if n.node_type == ProvenanceNodeType.ASTROSTATE)

    # AstroStateNode should have parent_ids pointing to AstronomyComputation
    assert astrostate_node.parent_ids is not None
    assert len(astrostate_node.parent_ids) > 0

    # The parent should be the AstronomyComputation node
    parent_id = astrostate_node.parent_ids[0]
    parent_node = provenance_registry.get_node(parent_id)
    assert parent_node.node_type == ProvenanceNodeType.ASTRONOMY_COMPUTATION


def test_identical_inputs_produce_identical_provenance(birth_input, convention):
    """Test that identical inputs produce identical AstroState and provenance identity."""
    registry_a = ProvenanceRegistry()
    registry_b = ProvenanceRegistry()

    engine = AstronomyEngine()
    builder = AstroStateBuilder(engine)

    state_a = builder.build(birth_input, convention, provenance_registry=registry_a)
    state_b = builder.build(birth_input, convention, provenance_registry=registry_b)

    assert state_a.state_id == state_b.state_id

    # AstroStateNode IDs should match
    astrostate_a = next(
        n for n in registry_a._nodes.values() if n.node_type == ProvenanceNodeType.ASTROSTATE
    )
    astrostate_b = next(
        n for n in registry_b._nodes.values() if n.node_type == ProvenanceNodeType.ASTROSTATE
    )
    assert astrostate_a.node_id == astrostate_b.node_id
    assert astrostate_a.state_id == astrostate_b.state_id


def test_changed_birth_input_produces_different_identity(birth_input, convention):
    """Test that changed birth input produces a different AstroState identity."""
    registry_a = ProvenanceRegistry()
    registry_b = ProvenanceRegistry()

    engine = AstronomyEngine()
    builder = AstroStateBuilder(engine)

    state_a = builder.build(birth_input, convention, provenance_registry=registry_a)

    # Create modified birth input
    from astro_engine.state import BirthInput
    modified_birth = BirthInput(
        datetime_utc=birth_input.datetime_utc,
        timezone_name=birth_input.timezone_name,
        latitude=50.0,  # Changed latitude
        longitude=birth_input.longitude,
    )
    state_b = builder.build(modified_birth, convention, provenance_registry=registry_b)

    assert state_a.state_id != state_b.state_id


def test_missing_astorstate_link_raises(birth_input, convention, provenance_registry):
    """Test that missing AstroState link raises ProvenanceIntegrityError."""
    engine = AstronomyEngine()
    builder = AstroStateBuilder(engine)
    state = builder.build(birth_input, convention, provenance_registry=provenance_registry)

    # Get the AstroStateNode and add a fake parent ID
    astrostate_node = next(
        n for n in provenance_registry._nodes.values() if n.node_type == ProvenanceNodeType.ASTROSTATE
    )
    astrostate_node.parent_ids.append("fake-missing-parent")
    # Recompute hash to reflect modified content
    astrostate_node.content_hash = astrostate_node.compute_hash(astrostate_node.model_dump(exclude={"node_id", "timestamp", "content_hash"}))

    # Now trace from any descendant should fail
    from astro_engine.methods import QuestionContext
    from astro_engine.methods.vimshottari_career import VimshottariCareerMethod

    method = VimshottariCareerMethod()
    question = QuestionContext(domain="career", task="event_timing")
    method_run = method.run(state, question, provenance_registry=provenance_registry)

    with pytest.raises(ProvenanceIntegrityError, match="Missing provenance node: fake-missing-parent"):
        provenance_registry.trace_prediction(method_run.predictions[0].provenance_node_id)


def test_duplicate_node_raises(provenance_registry):
    """Test that adding a node with same ID but different content raises error."""
    from astro_engine.provenance import BirthInputNode

    node1 = BirthInputNode(
        version="1.0",
        datetime_utc="2020-01-01T00:00:00+00:00",
        latitude=10.0,
        longitude=20.0,
    )
    node1.content_hash = node1.compute_hash(
        node1.model_dump(exclude={"node_id", "timestamp", "content_hash"})
    )
    provenance_registry.add_node(node1)

    # Try to add another node with same ID (same hash) but different content
    node2 = BirthInputNode(
        version="1.0",
        datetime_utc="2020-01-01T00:00:00+00:00",
        latitude=99.0,  # Different!
        longitude=20.0,
    )
    # Force same node_id
    node2.node_id = node1.node_id
    node2.content_hash = "different_hash"

    with pytest.raises(ProvenanceIntegrityError, match="Duplicate node ID with different content hash"):
        provenance_registry.add_node(node2)


def test_cycle_detection(provenance_registry):
    """Test that a cycle in the provenance graph raises ProvenanceIntegrityError."""
    from astro_engine.provenance import (
        BirthInputNode,
        ConventionProfileNode,
        compute_deterministic_hash,
    )

    # Create two nodes with FIXED IDs by setting them AFTER hash computation
    node_a = BirthInputNode(
        version="1.0",
        datetime_utc="2020-01-01T00:00:00+00:00",
        latitude=10.0,
        longitude=20.0,
    )
    node_b = ConventionProfileNode(
        version="1.0",
        convention_id="test",
        ayanamsa="lahiri",
        house_system="whole_sign",
    )

    # Set parent_ids BEFORE computing hash
    node_a.parent_ids.append("cycle-node-b")
    node_b.parent_ids.append("cycle-node-a")

    # Compute hashes manually without changing node_id
    node_a.content_hash = compute_deterministic_hash(node_a._content_dict())
    node_b.content_hash = compute_deterministic_hash(node_b._content_dict())

    # Set node_ids AFTER computing hashes
    node_a.node_id = "cycle-node-a"
    node_b.node_id = "cycle-node-b"

    provenance_registry.add_node(node_a)
    provenance_registry.add_node(node_b)

    with pytest.raises(ProvenanceIntegrityError, match="Cycle detected"):
        provenance_registry.trace_prediction(node_a.node_id)


def test_corrupted_node_hash_raises(birth_input, convention, provenance_registry):
    """Test that a node with corrupted content hash raises ProvenanceIntegrityError."""
    from astro_engine.provenance import BirthInputNode

    # Create a node with corrupted hash
    node = BirthInputNode(
        version="1.0",
        datetime_utc="2020-01-01T00:00:00+00:00",
        latitude=10.0,
        longitude=20.0,
    )
    node.content_hash = node.compute_hash(node.model_dump(exclude={"node_id", "timestamp", "content_hash"}))

    # Corrupt the hash
    node.content_hash = "corrupted_hash_value"

    # Validate should raise
    with pytest.raises(ProvenanceIntegrityError, match="Node content hash mismatch"):
        provenance_registry.validate_node(node)
