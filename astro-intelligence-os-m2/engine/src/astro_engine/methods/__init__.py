"""
Method SDK
==========

Defines the formal Method interface that every astrological methodology
must implement. A Method is independently executable, deterministic
(given its rules), and produces a MethodRun as output.

No LLM is required to execute a Method.
"""

from __future__ import annotations

import enum
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from astro_engine.state import AstroState

from pydantic import BaseModel, ConfigDict, Field, field_validator

from astro_engine.methods.question_spec import (
    DataQualityRequirement,
    MethodSelectionMode,
    QuestionSpec,
    make_question_spec,
)

__all__ = [
    "MethodMaturity",
    "QuestionContext",
    "PredictionDirection",
    "Prediction",
    "MethodRun",
    "Method",
    "QuestionSpec",
    "MethodSelectionMode",
    "DataQualityRequirement",
    "make_question_spec",
]

# ---------------------------------------------------------------------------
# Method maturity lifecycle
# ---------------------------------------------------------------------------

class MethodMaturity(enum.StrEnum):
    """Lifecycle stage of a methodology implementation."""

    DRAFT = "draft"
    EXPERIMENTAL = "experimental"
    VALIDATED = "validated"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"


# ---------------------------------------------------------------------------
# Question context
# ---------------------------------------------------------------------------

class QuestionContext(BaseModel):
    """Structured representation of an analytical question."""

    domain: str = Field(..., description="e.g. 'career', 'health', 'relationship'.")
    task: str = Field(..., description="e.g. 'event_timing', 'trend_analysis'.")
    event: str | None = Field(default=None, description="Specific event type.")
    time_horizon_years: float | None = Field(default=None)
    raw_question: str | None = Field(default=None, description="Original user question.")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)


# ---------------------------------------------------------------------------
# Prediction — the normalized output from any method
# ---------------------------------------------------------------------------

class PredictionDirection(enum.StrEnum):
    """Predicted direction of an event or trend."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class Prediction(BaseModel):
    """
    Canonical, method-agnostic prediction contract.

    Represents the semantic result of a method independently of the
    method's internal implementation. Does NOT introduce uncalibrated
    probability — signal_strength is preserved from the method's own
    heuristic output and is explicitly NOT called confidence or probability.
    """

    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str | None = Field(
        default=None, description="QuestionSpec id this prediction addresses."
    )
    domain: str
    event: str
    event_type: str | None = Field(
        default=None, description="Canonical event type (e.g. 'career_activation')."
    )
    direction: PredictionDirection = PredictionDirection.UNKNOWN
    magnitude: float | None = Field(
        default=None, description="Intensity 0.0–1.0, if quantifiable."
    )
    signal_strength: float | None = Field(
        default=None,
        description=(
            "Method's own heuristic strength. NOT calibrated probability. "
            "Do NOT interpret as confidence."
        ),
    )

    @field_validator("signal_strength")
    @classmethod
    def _validate_signal_strength(cls, v: float | None) -> float | None:
        """Validate signal_strength: None allowed, otherwise must be in [0.0, 1.0]."""
        if v is None:
            return v
        if v < 0.0:
            raise ValueError(
                f"signal_strength must be >= 0.0, got {v}"
            )
        if v > 1.0:
            raise ValueError(
                f"signal_strength must be <= 1.0, got {v}"
            )
        return v
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None
    duration_description: str | None = None
    conditions: list[str] = Field(default_factory=list)
    supporting_signals: list[str] = Field(
        default_factory=list, description="Signals that support this prediction."
    )
    supporting_evidence: list[str] = Field(default_factory=list)
    contradictory_evidence: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(
        default_factory=list,
        description="References to rules, dasha periods, transit data, etc.",
    )
    method_id: str = ""
    method_version: str = ""
    raw_confidence: float | None = Field(
        default=None, description="Method's own confidence. NOT calibrated."
    )
    is_abstention: bool = Field(
        default=False, description="True if method cannot make a prediction."
    )
    abstention_reason: str | None = None
    provenance: dict[str, Any] = Field(
        default_factory=dict, description="Traceability metadata for this specific prediction."
    )
    provenance_node_id: str | None = Field(
        default=None, description="ID of the PredictionNode in the registry."
    )

    model_config = ConfigDict(frozen=True)


# ---------------------------------------------------------------------------
# MethodRun — the complete record of a single method execution
# ---------------------------------------------------------------------------

class MethodRun(BaseModel):
    """
    Complete, reproducible record of executing a Method against an AstroState.

    Every field must be traceable. A MethodRun must be reproducible given
    the same AstroState and Method version.

    A MethodRun is immutable after execution. Methods must not mutate it.
    """

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    method_id: str
    method_version: str
    input_state_id: str = Field(
        ..., description="state_id of the AstroState consumed."
    )
    input_state_hash: str = Field(
        default="",
        description="Hash of the input AstroState (same as state_id).",
    )
    question_id: str | None = Field(
        default=None, description="QuestionSpec id this run addresses."
    )
    question: QuestionSpec
    calculations_used: list[str] = Field(
        default_factory=list, description="Names of calculations consumed."
    )
    rules_evaluated: list[str] = Field(
        default_factory=list, description="Rule IDs that were checked."
    )
    intermediate_findings: list[dict[str, Any]] = Field(default_factory=list)
    candidate_events: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Candidate events detected but not yet normalized into predictions.",
    )
    timing_windows: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Time windows identified by the method.",
    )
    predictions: list[Prediction] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(
        default_factory=list, description="Evidence supporting the run as a whole."
    )
    contradictory_evidence: list[str] = Field(
        default_factory=list, description="Evidence contradicting the run's conclusions."
    )
    assumptions: list[str] = Field(default_factory=list)
    abstentions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Explicit abstention records when the method cannot answer.",
    )
    unknowns: list[str] = Field(
        default_factory=list, description="Aspects the method cannot determine."
    )
    warnings: list[str] = Field(default_factory=list)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    provenance_node_id: str | None = Field(
        default=None, description="ID of the MethodRunNode in the registry."
    )

    model_config = ConfigDict(frozen=True)


# ---------------------------------------------------------------------------
# Abstract Method interface
# ---------------------------------------------------------------------------

class Method(ABC):
    """
    Abstract base class for all astrological methodologies.

    Every methodology must:
    - Declare its identity and capabilities.
    - Specify which calculations it needs from AstroState.
    - Execute independently without seeing other methods' outputs.
    - Return a complete MethodRun.
    """

    @property
    @abstractmethod
    def method_id(self) -> str:
        """Unique identifier for this method."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version string."""
        ...

    @property
    @abstractmethod
    def tradition(self) -> str:
        """Astrological tradition (e.g. 'Parashari', 'Jaimini', 'KP')."""
        ...

    @property
    @abstractmethod
    def maturity(self) -> MethodMaturity:
        """Current maturity level."""
        ...

    @property
    @abstractmethod
    def supported_domains(self) -> list[str]:
        """Domains this method can address (e.g. ['career', 'health'])."""
        ...

    @property
    @abstractmethod
    def required_calculations(self) -> list[str]:
        """AstroState sections this method requires (e.g. ['planets', 'dashas'])."""
        ...

    @abstractmethod
    def run(
        self,
        state: AstroState,
        question: QuestionSpec,
        provenance_registry: Any | None = None,
    ) -> MethodRun:
        """
        Execute this methodology against the given AstroState.

        The canonical input is QuestionSpec. Legacy QuestionContext inputs
        must be converted via question_context_to_spec() before reaching
        this interface.

        This method must:
        - NOT use any LLM for the astrological inference.
        - NOT access other methods' outputs.
        - Return a complete MethodRun with full provenance.
        """
        ...

    def can_handle(self, question: QuestionSpec) -> bool:
        """Check if this method can address the given question."""
        return question.domain in self.supported_domains

    def validate_capabilities(self) -> list[str]:
        """
        Validates that required calculations exist and meet the minimum maturity standard.
        Raises CapabilityError if a PRODUCTION method relies on PARTIAL calculations.
        Returns a list of warnings for EXPERIMENTAL methods relying on PARTIAL calculations.
        """
        from astro_engine.capabilities import validate_method_capabilities
        return validate_method_capabilities(self.maturity.value, self.required_calculations)
