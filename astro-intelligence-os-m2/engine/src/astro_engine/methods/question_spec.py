"""
QuestionSpec — Canonical Question Contract
===========================================

Represents the user's astrology question AFTER interpretation but BEFORE
method execution. It captures only information required to execute or
evaluate the question.

QuestionSpec is:

- Deterministic: identical inputs produce identical QuestionSpec.
- Serializable: can be serialized to/from JSON.
- Hashable/versionable: a stable content hash identifies the spec.
- LLM-independent: methods receive QuestionSpec, not raw natural language.
- Method-independent: no reference to any particular astrology method.

The LLM/question compiler may eventually create QuestionSpec, but methods
must receive QuestionSpec rather than raw natural language. The compiler
is NOT built in this phase.
"""

from __future__ import annotations

import enum
import hashlib
import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from astro_engine.methods import QuestionContext

# ---------------------------------------------------------------------------
# Method-selection mode
# ---------------------------------------------------------------------------


class MethodSelectionMode(enum.StrEnum):
    """How methods should be selected for a question."""

    AUTO = "auto"
    EXPLICIT = "explicit"
    ALL = "all"
    NONE = "none"


# ---------------------------------------------------------------------------
# Data-quality requirements
# ---------------------------------------------------------------------------


class DataQualityRequirement(enum.StrEnum):
    """Minimum data-quality bar a method may require."""

    ANY = "any"
    RODDEN_A = "rodden_a"
    RODDEN_AA = "rodden_aa"
    EXACT_TIME = "exact_time"
    VERIFIED = "verified"


# ---------------------------------------------------------------------------
# QuestionSpec
# ---------------------------------------------------------------------------


class QuestionSpec(BaseModel):
    """
    Canonical, deterministic, serializable representation of an astrology
    question after interpretation but before method execution.

    Every field is traceable and reproducible. Two QuestionSpec instances
    with identical content produce identical content hashes.
    """

    question_id: str = Field(
        ...,
        description="Stable identifier for this question (e.g. UUID or hash).",
    )
    domain: str = Field(
        ..., description="e.g. 'career', 'health', 'relationship', 'finance'."
    )
    event_type: str = Field(
        ...,
        description="e.g. 'event_timing', 'trend_analysis', 'compatibility', 'muhurta'.",
    )
    time_horizon: float | None = Field(
        default=None,
        description="Time horizon in years. None means 'no specific horizon'.",
    )
    required_time_precision: str = Field(
        default="day",
        description="e.g. 'year', 'month', 'week', 'day', 'hour'.",
    )
    requested_methods: list[str] = Field(
        default_factory=list,
        description="Method IDs explicitly requested. Empty = auto-select.",
    )
    method_selection_mode: MethodSelectionMode = Field(
        default=MethodSelectionMode.AUTO,
        description="How methods should be selected.",
    )
    input_state_id: str | None = Field(
        default=None,
        description="state_id of the AstroState to consume, if known.",
    )
    data_quality_requirements: list[DataQualityRequirement] = Field(
        default_factory=list,
        description="Minimum data-quality bars required.",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Contextual constraints (e.g. 'only_dasha_based', 'exclude_transit').",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form metadata for the question compiler.",
    )

    model_config = ConfigDict(frozen=True)

    # ------------------------------------------------------------------
    # Identity / hashing
    # ------------------------------------------------------------------

    def content_hash(self) -> str:
        """Deterministic SHA-256 hash of this spec's content."""
        payload = self.model_dump(mode="json", exclude={"question_id"})
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def version(self) -> str:
        """Version identifier derived from content hash (first 12 hex chars)."""
        return self.content_hash()[:12]

    def with_question_id(self, question_id: str) -> QuestionSpec:
        """Return a copy with a new question_id (preserves content hash)."""
        return self.model_copy(update={"question_id": question_id})

    def is_complete(self) -> bool:
        """Check if the spec has all required fields populated."""
        return bool(self.question_id and self.domain and self.event_type)

    def missing_fields(self) -> list[str]:
        """Return list of required fields that are empty/missing."""
        missing: list[str] = []
        if not self.question_id:
            missing.append("question_id")
        if not self.domain:
            missing.append("domain")
        if not self.event_type:
            missing.append("event_type")
        return missing


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def make_question_spec(
    question_id: str,
    domain: str,
    event_type: str,
    *,
    time_horizon: float | None = None,
    required_time_precision: str = "day",
    requested_methods: list[str] | None = None,
    method_selection_mode: MethodSelectionMode | None = None,
    input_state_id: str | None = None,
    data_quality_requirements: list[DataQualityRequirement] | None = None,
    constraints: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> QuestionSpec:
    """Create a QuestionSpec with sensible defaults."""
    return QuestionSpec(
        question_id=question_id,
        domain=domain,
        event_type=event_type,
        time_horizon=time_horizon,
        required_time_precision=required_time_precision,
        requested_methods=requested_methods or [],
        method_selection_mode=method_selection_mode or MethodSelectionMode.AUTO,
        input_state_id=input_state_id,
        data_quality_requirements=data_quality_requirements or [],
        constraints=constraints or [],
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# Adapter: QuestionContext → QuestionSpec
# ---------------------------------------------------------------------------


def question_context_to_spec(
    question_context: QuestionContext,
    question_id: str | None = None,
) -> QuestionSpec:
    """
    Adapter that converts a legacy QuestionContext into a canonical QuestionSpec.

    .. deprecated::
        This adapter exists for backward compatibility only.
        The canonical Method contract accepts QuestionSpec.
        New code should use QuestionSpec directly.

    Args:
        question_context: The legacy QuestionContext to convert.
        question_id: Optional explicit question_id. If None, a deterministic
            hash-based ID is derived from the QuestionContext content.

    Returns:
        A canonical QuestionSpec.
    """
    if question_id is None:
        question_id = _derive_question_id(question_context)

    return QuestionSpec(
        question_id=question_id,
        domain=question_context.domain,
        event_type=question_context.event or question_context.task,
        time_horizon=question_context.time_horizon_years,
        required_time_precision="day",
        requested_methods=[],
        method_selection_mode=MethodSelectionMode.AUTO,
        input_state_id=None,
        data_quality_requirements=[],
        constraints=[],
        metadata={
            "task": question_context.task,
            "raw_question": question_context.raw_question or "",
            "legacy_context": True,
            **question_context.metadata,
        },
    )


def _derive_question_id(question_context: QuestionContext) -> str:
    """Derive a deterministic question_id from a QuestionContext."""
    import hashlib
    import json

    payload = question_context.model_dump(mode="json")
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]
