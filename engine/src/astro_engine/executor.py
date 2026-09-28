"""
Multi-Method Executor — Orchestration Layer
=============================================

Executes multiple independent astrology methods against the same
QuestionSpec and AstroState. The executor collects each method's
canonical MethodRun into an ExecutorResult.

It does NOT:
- merge predictions
- calculate consensus / convergence / dissent
- route or rank methods
- calibrate signal strengths
- introduce agents or ML

It only orchestrates independent method executions and preserves
their individual MethodRuns intact.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from astro_engine.methods import Method, MethodRun, QuestionSpec
    from astro_engine.provenance import ProvenanceRegistry
    from astro_engine.state import AstroState


# ---------------------------------------------------------------------------
# Execution status
# ---------------------------------------------------------------------------


class ExecutorStatus(enum.StrEnum):
    """Status of a single method execution within the executor."""

    SUCCESS = "success"
    ABSTAINED = "abstained"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Method execution result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MethodExecutionResult:
    """
    The result of executing a single method through the executor.

    Preserves the full MethodRun when successful or abstaining.
    Records the error when the method failed.
    """

    method_id: str
    method_version: str
    status: ExecutorStatus
    method_run: MethodRun | None
    error: str | None = None

    @property
    def is_success(self) -> bool:
        return self.status == ExecutorStatus.SUCCESS

    @property
    def is_abstained(self) -> bool:
        return self.status == ExecutorStatus.ABSTAINED

    @property
    def is_failed(self) -> bool:
        return self.status == ExecutorStatus.FAILED


# ---------------------------------------------------------------------------
# Executor result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutorResult:
    """
    The complete result of executing multiple methods through the executor.

    Every MethodRun is preserved intact and individually inspectable.
    Predictions are never merged, aggregated, or transformed.
    """

    question_id: str
    input_state_hash: str
    executor_version: str
    method_results: tuple[MethodExecutionResult, ...]
    provenance_node_id: str | None = None

    @property
    def all_method_runs(self) -> tuple[MethodRun, ...]:
        """Return only successful or abstaining MethodRuns."""
        return tuple(
            r.method_run
            for r in self.method_results
            if r.method_run is not None
        )

    @property
    def success_runs(self) -> tuple[MethodRun, ...]:
        """Return MethodRuns from methods that succeeded."""
        return tuple(
            r.method_run
            for r in self.method_results
            if r.is_success and r.method_run is not None
        )

    @property
    def abstained_runs(self) -> tuple[MethodRun, ...]:
        """Return MethodRuns from methods that abstained."""
        return tuple(
            r.method_run
            for r in self.method_results
            if r.is_abstained and r.method_run is not None
        )

    @property
    def failed_methods(self) -> tuple[MethodExecutionResult, ...]:
        """Return results from methods that failed."""
        return tuple(r for r in self.method_results if r.is_failed)


# ---------------------------------------------------------------------------
# Multi-Method Executor
# ---------------------------------------------------------------------------


class MultiMethodExecutor:
    """
    Orchestrates independent execution of multiple astrology methods.

    Each method receives the same immutable QuestionSpec and AstroState.
    Methods execute in the order supplied by the caller and cannot observe
    each other's outputs — independence is enforced by construction.

    Execution ordering is deterministic and matches the input ordering.

    Version: 1.0.0
    """

    VERSION = "1.0.0"

    def execute(
        self,
        question: QuestionSpec,
        state: AstroState,
        methods: list[Method],
        provenance_registry: ProvenanceRegistry | None = None,
    ) -> ExecutorResult:
        """
        Execute all supplied methods independently against the same input.

        Args:
            question: Canonical question spec — identical for all methods.
            state: Immutable AstroState — identical for all methods.
            methods: Ordered list of methods to execute.
                Duplicates are deduplicated by identity (method_id);
                the first occurrence is kept.
            provenance_registry: Optional registry for provenance nodes.

        Returns:
            ExecutorResult with one MethodExecutionResult per method,
            in the same order as the input (after deduplication).
        """
        # Deduplicate methods by method_id, preserving first occurrence
        seen: set[str] = set()
        unique_methods: list[Method] = []
        for m in methods:
            if m.method_id not in seen:
                seen.add(m.method_id)
                unique_methods.append(m)

        results: list[MethodExecutionResult] = []

        for method in unique_methods:
            result = self._execute_single(method, question, state, provenance_registry)
            results.append(result)

        return ExecutorResult(
            question_id=question.question_id,
            input_state_hash=state.state_id,
            executor_version=self.VERSION,
            method_results=tuple(results),
        )

    def _execute_single(
        self,
        method: Method,
        question: QuestionSpec,
        state: AstroState,
        provenance_registry: ProvenanceRegistry | None,
    ) -> MethodExecutionResult:
        """Execute one method and capture its result or failure."""
        try:
            run: MethodRun = method.run(state, question, provenance_registry)
        except Exception as exc:
            return MethodExecutionResult(
                method_id=method.method_id,
                method_version=method.version,
                status=ExecutorStatus.FAILED,
                method_run=None,
                error=str(exc),
            )

        # Determine status from the MethodRun's abstention contract.
        # A MethodRun abstains when it records an explicit abstention (via the
        # abstentions list) or carries abstention predictions. Either signal
        # classifies the run as ABSTAINED.
        has_abstention_prediction = any(p.is_abstention for p in run.predictions)
        has_abstention_record = bool(run.abstentions)
        status = (
            ExecutorStatus.ABSTAINED
            if has_abstention_prediction or has_abstention_record
            else ExecutorStatus.SUCCESS
        )

        return MethodExecutionResult(
            method_id=method.method_id,
            method_version=method.version,
            status=status,
            method_run=run,
        )
