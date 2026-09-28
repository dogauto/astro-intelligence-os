"""
Provenance Graph Infrastructure
===============================

Implements a deterministic, hashable graph for tracing the exact origins
of any astrological prediction back to the ephemeris and birth input.
"""

from __future__ import annotations

import enum
import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProvenanceNodeType(enum.StrEnum):
    BIRTH_INPUT = "BIRTH_INPUT"
    CONVENTION_PROFILE = "CONVENTION_PROFILE"
    ASTRONOMY_COMPUTATION = "ASTRONOMY_COMPUTATION"
    ASTROSTATE = "ASTROSTATE"
    CALCULATION = "CALCULATION"
    RULE = "RULE"
    METHOD_RUN = "METHOD_RUN"
    PREDICTION = "PREDICTION"


class ProvenanceIntegrityError(Exception):
    """Raised when a provenance chain is broken, missing, or has invalid hashes."""
    pass


def compute_deterministic_hash(data: dict[str, Any]) -> str:
    """Computes a SHA-256 hash of a dictionary deterministically."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ProvenanceNode(BaseModel):
    """Base class for all provenance nodes."""

    node_id: str = ""
    node_type: ProvenanceNodeType
    version: str
    parent_ids: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    content_hash: str = ""

    model_config = ConfigDict(frozen=False)

    def compute_hash(self, content_data: dict[str, Any]) -> str:
        h = compute_deterministic_hash(content_data)
        self.content_hash = h
        self.node_id = h
        return h

    def _content_dict(self) -> dict[str, Any]:
        """Canonical content representation used for hash computation/validation.

        Excludes auto-generated/derived fields that are set after hashing
        (node_id, content_hash, timestamp, run_id, prediction_id).
        """
        return self.model_dump(
            exclude={
                "node_id",
                "timestamp",
                "content_hash",
                "run_id",
                "prediction_id",
            }
        )


# Specific Nodes

class BirthInputNode(ProvenanceNode):
    node_type: ProvenanceNodeType = ProvenanceNodeType.BIRTH_INPUT
    datetime_utc: str
    latitude: float
    longitude: float


class ConventionProfileNode(ProvenanceNode):
    node_type: ProvenanceNodeType = ProvenanceNodeType.CONVENTION_PROFILE
    convention_id: str
    ayanamsa: str
    house_system: str
    chara_karaka_scheme: int | None = None
    rahu_rule: str | None = None
    ketu_excluded: bool | None = None
    precision: str | None = None


class AstronomyComputationNode(ProvenanceNode):
    node_type: ProvenanceNodeType = ProvenanceNodeType.ASTRONOMY_COMPUTATION
    engine_version: str
    ephemeris_source: str
    ephemeris_version: str


class AstroStateNode(ProvenanceNode):
    """Provenance node for a fully computed AstroState."""

    node_type: ProvenanceNodeType = ProvenanceNodeType.ASTROSTATE
    state_id: str
    engine_version: str
    ephemeris_type: str
    ayanamsa_value: float
    julian_day: float


class CalculationNode(ProvenanceNode):
    node_type: ProvenanceNodeType = ProvenanceNodeType.CALCULATION
    calculation_name: str
    convention_id: str | None = None
    input_state_id: str | None = None
    source_rule_ids: list[str] = Field(default_factory=list)
    source_id: str | None = None
    source_location: str | None = None
    chara_karaka_scheme: int | None = None
    rahu_rule: str | None = None
    ketu_excluded: bool | None = None
    precision: str | None = None


class RuleNode(ProvenanceNode):
    node_type: ProvenanceNodeType = ProvenanceNodeType.RULE
    rule_id: str
    logic_description: str
    source_id: str | None = None
    source_location: str | None = None
    convention_id: str | None = None


class MethodRunNode(ProvenanceNode):
    node_type: ProvenanceNodeType = ProvenanceNodeType.METHOD_RUN
    run_id: str
    method_id: str
    input_state_hash: str


class PredictionNode(ProvenanceNode):
    node_type: ProvenanceNodeType = ProvenanceNodeType.PREDICTION
    prediction_id: str
    domain: str
    event: str
    question_id: str | None = Field(
        default=None,
        description="QuestionSpec id this prediction addresses.",
    )


class ProvenanceRegistry:
    """In-memory store for provenance nodes during a system execution."""

    def __init__(self) -> None:
        self._nodes: dict[str, ProvenanceNode] = {}

    def add_node(self, node: ProvenanceNode) -> None:
        if node.node_id in self._nodes:
            existing = self._nodes[node.node_id]
            if existing.content_hash != node.content_hash:
                raise ProvenanceIntegrityError(
                    f"Duplicate node ID with different content hash: {node.node_id}"
                )
            # Same content, idempotent add - this is OK
            return
        self._nodes[node.node_id] = node

    def get_node(self, node_id: str) -> ProvenanceNode:
        if node_id not in self._nodes:
            raise ProvenanceIntegrityError(
                f"Missing provenance node: {node_id}"
            )
        return self._nodes[node_id]

    def validate_node(self, node: ProvenanceNode) -> None:
        """Validate that a node's content_hash matches its current content."""
        content_data = node._content_dict()
        expected_hash = compute_deterministic_hash(content_data)
        if node.content_hash != expected_hash:
            raise ProvenanceIntegrityError(
                f"Node content hash mismatch for {node.node_id}: "
                f"expected {expected_hash}, got {node.content_hash}"
            )

    def trace_prediction(self, prediction_node_id: str) -> list[ProvenanceNode]:
        """
        Traverses the graph backwards from a PredictionNode to the roots.
        Raises ProvenanceIntegrityError if any link is broken or a cycle is detected.
        Returns a list of all ancestor nodes.
        """
        trace: list[ProvenanceNode] = []
        visiting: set[str] = set()  # for cycle detection
        visited: set[str] = set()

        def dfs(current_id: str) -> None:
            if current_id in visiting:
                raise ProvenanceIntegrityError(
                    f"Cycle detected in provenance graph at node: {current_id}"
                )
            if current_id in visited:
                return
            visiting.add(current_id)
            node = self.get_node(current_id)
            # Validate node content hash during traversal
            self.validate_node(node)
            trace.append(node)
            for parent_id in node.parent_ids:
                dfs(parent_id)
            visiting.remove(current_id)
            visited.add(current_id)

        dfs(prediction_node_id)
        return trace
