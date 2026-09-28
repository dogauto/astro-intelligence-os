"""Narrow, deterministic Jaimini career/profession method.

This method exposes only the source-backed Amatyakaraka career factor and
related Chara Karaka context. It does not classify professions or provide
timing, aspects, Karakamsa interpretation, or probabilities.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

from astro_engine.chara_karaka import (
    CONVENTION_ID,
    CONVENTION_ID_8,
    RULE_ID as CHARAKA_RULE_ID,
    SOURCE_ID as CHARAKA_SOURCE_ID,
    CharaKarakaResult,
    compute_chara_karakas,
)
from astro_engine.methods import (
    Method,
    MethodMaturity,
    MethodRun,
    Prediction,
    PredictionDirection,
    QuestionSpec,
)
from astro_engine.provenance import (
    CalculationNode,
    MethodRunNode,
    PredictionNode,
    ProvenanceRegistry,
    RuleNode,
)

if TYPE_CHECKING:
    from astro_engine.state import AstroState


METHOD_ID = "jaimini-career-profession-v1"
METHOD_VERSION = "1.0.0"
CAREER_RULE_ID = "jaimini-career-amatyakaraka-profession-v1"
SOURCE_ID = "jaimini-course-upadesa-sutra-rath-sagittarius-2007"
SOURCE_LOCATION = (
    "A Course on Jaimini Maharshi's Upadesa Sutra, Volume I, "
    "Sanjay Rath, Sagittarius Publications, pp. 288-303: "
    "Chara Karaka, Atmakaraka/Amatyakaraka, and career/profession discussion"
)


class JaiminiCareerMethod(Method):
    """Expose the narrow source-backed Amatyakaraka career factor."""

    @property
    def method_id(self) -> str:
        return METHOD_ID

    @property
    def name(self) -> str:
        return "Jaimini Career Profession Signal"

    @property
    def version(self) -> str:
        return METHOD_VERSION

    @property
    def tradition(self) -> str:
        return "Jaimini"

    @property
    def maturity(self) -> MethodMaturity:
        return MethodMaturity.EXPERIMENTAL

    @property
    def supported_domains(self) -> list[str]:
        return ["career", "profession"]

    @property
    def required_calculations(self) -> list[str]:
        return ["planets", "chara_karaka"]

    def run(
        self,
        state: AstroState,
        question: QuestionSpec,
        provenance_registry: ProvenanceRegistry | None = None,
    ) -> MethodRun:
        """Execute the independent Chara Karaka career signal."""
        calculations_used = ["planets", "chara_karaka"]
        if question.domain not in self.supported_domains:
            return self._build_abstention(
                state,
                question,
                calculations_used,
                "Question domain is outside the Jaimini career method scope.",
                provenance_registry,
            )
        if state.convention.id not in {CONVENTION_ID, CONVENTION_ID_8}:
            return self._build_abstention(
                state,
                question,
                calculations_used,
                "AstroState does not use an approved Chara Karaka convention.",
                provenance_registry,
            )

        try:
            chara_result = compute_chara_karakas(
                state,
                state.convention,
                provenance_registry,
            )
        except ValueError as exc:
            return self._build_abstention(
                state,
                question,
                calculations_used,
                f"Chara Karaka calculation unavailable: {exc}",
                provenance_registry,
            )

        if chara_result.abstained or chara_result.amatyakaraka is None:
            return self._build_abstention(
                state,
                question,
                calculations_used,
                "Amatyakaraka is unresolved because Chara Karaka ranking is ambiguous.",
                provenance_registry,
                chara_result,
            )

        finding = {
            "finding": "jaimini_career_factors",
            "career_factor": "Amatyakaraka",
            "amatyakaraka": chara_result.amatyakaraka,
            "atmakaraka": chara_result.atmakaraka,
            "karaka_lagna": chara_result.karaka_lagna,
            "scheme": chara_result.scheme.value,
            "source_id": SOURCE_ID,
            "rule_id": CAREER_RULE_ID,
        }
        prediction = Prediction(
            prediction_id=_stable_id(
                "prediction",
                state.state_id,
                question.question_id,
                chara_result.amatyakaraka,
            ),
            question_id=question.question_id,
            domain="career",
            event="career_profession_indication",
            direction=PredictionDirection.UNKNOWN,
            conditions=[
                f"Amatyakaraka identified as {chara_result.amatyakaraka}.",
                "No profession classification is produced by this method.",
            ],
            supporting_signals=["Amatyakaraka is the source-backed career/profession factor."],
            supporting_evidence=[
                f"Amatyakaraka: {chara_result.amatyakaraka}.",
                f"Atmakaraka: {chara_result.atmakaraka or 'unresolved'}.",
                f"Karaka Lagna sign index: {chara_result.karaka_lagna}.",
            ],
            evidence_references=[
                SOURCE_ID,
                SOURCE_LOCATION,
                CAREER_RULE_ID,
                CHARAKA_RULE_ID,
                chara_result.convention_id,
                chara_result.provenance_node_id or "chara_karaka_calculation",
            ],
            method_id=self.method_id,
            method_version=self.version,
            provenance={
                "source_id": SOURCE_ID,
                "source_location": SOURCE_LOCATION,
                "rule_id": CAREER_RULE_ID,
                "chara_karaka_rule_id": CHARAKA_RULE_ID,
                "calculation_version": chara_result.calculation_version,
                "convention_id": chara_result.convention_id,
                "chara_karaka_provenance_node_id": chara_result.provenance_node_id,
            },
        )
        return self._build_run(
            state,
            question,
            calculations_used,
            [CAREER_RULE_ID],
            [finding],
            [prediction],
            [
                "Amatyakaraka is exposed as a structured career/profession signal only.",
                "Tenth-house/lord relationships are not evaluated in this milestone.",
                "Atmakaraka activity/work interpretation is not expanded beyond Chara Karaka context.",
                "Timing is unavailable because no Jaimini timing rule is implemented.",
            ],
            [],
            provenance_registry,
            chara_result,
        )

    def _build_abstention(
        self,
        state: AstroState,
        question: QuestionSpec,
        calculations_used: list[str],
        reason: str,
        provenance_registry: ProvenanceRegistry | None,
        chara_result: CharaKarakaResult | None = None,
    ) -> MethodRun:
        prediction = Prediction(
            prediction_id=_stable_id("abstention", state.state_id, question.question_id, reason),
            question_id=question.question_id,
            domain="career",
            event="career_profession_abstention",
            direction=PredictionDirection.UNKNOWN,
            is_abstention=True,
            abstention_reason=reason,
            method_id=self.method_id,
            method_version=self.version,
            provenance={
                "source_id": SOURCE_ID,
                "rule_id": CAREER_RULE_ID,
                "chara_karaka_rule_id": CHARAKA_RULE_ID,
                "chara_karaka_provenance_node_id": (
                    chara_result.provenance_node_id if chara_result else None
                ),
            },
        )
        return self._build_run(
            state,
            question,
            calculations_used,
            [CAREER_RULE_ID],
            [],
            [prediction],
            [],
            [reason],
            provenance_registry,
            chara_result,
        )

    def _build_run(
        self,
        state: AstroState,
        question: QuestionSpec,
        calculations_used: list[str],
        rules_evaluated: list[str],
        findings: list[dict[str, Any]],
        predictions: list[Prediction],
        assumptions: list[str],
        warnings: list[str],
        provenance_registry: ProvenanceRegistry | None,
        chara_result: CharaKarakaResult | None,
    ) -> MethodRun:
        run_id = _stable_id(self.method_id, self.version, state.state_id, question.question_id)
        run_node_id: str | None = None
        if provenance_registry is not None:
            parent_ids = [state.provenance.astrostate_node_id] if state.provenance.astrostate_node_id else []
            if chara_result and chara_result.provenance_node_id:
                parent_ids.append(chara_result.provenance_node_id)
            run_node = MethodRunNode(
                version=self.version,
                run_id=run_id,
                method_id=self.method_id,
                input_state_hash=state.state_id,
                parent_ids=parent_ids,
            )
            run_node.compute_hash(run_node._content_dict())
            provenance_registry.add_node(run_node)
            run_node_id = run_node.node_id

            rule_nodes: list[str] = []
            for rule_id in rules_evaluated:
                rule_node = RuleNode(
                    version=self.version,
                    rule_id=rule_id,
                    logic_description=(
                        "Expose the source-backed Amatyakaraka career/profession "
                        "factor without profession classification."
                    ),
                    source_id=SOURCE_ID,
                    source_location=SOURCE_LOCATION,
                    convention_id=chara_result.convention_id if chara_result else state.convention.id,
                    parent_ids=(
                        [run_node_id]
                        + ([chara_result.provenance_node_id]
                           if chara_result and chara_result.provenance_node_id else [])
                    ),
                )
                rule_node.compute_hash(rule_node._content_dict())
                provenance_registry.add_node(rule_node)
                rule_nodes.append(rule_node.node_id)

            rebuilt: list[Prediction] = []
            for prediction in predictions:
                prediction_node = PredictionNode(
                    version=self.version,
                    prediction_id=prediction.prediction_id,
                    domain=prediction.domain,
                    event=prediction.event,
                    question_id=question.question_id,
                    parent_ids=[run_node_id, *rule_nodes],
                )
                prediction_node.compute_hash(prediction_node._content_dict())
                provenance_registry.add_node(prediction_node)
                rebuilt.append(
                    Prediction(
                        **prediction.model_dump(
                            exclude={"provenance_node_id"},
                        ),
                        provenance_node_id=prediction_node.node_id,
                    )
                )
            predictions = rebuilt

        return MethodRun(
            run_id=run_id,
            method_id=self.method_id,
            method_version=self.version,
            input_state_id=state.state_id,
            input_state_hash=state.state_id,
            question_id=question.question_id,
            question=question,
            calculations_used=calculations_used,
            rules_evaluated=rules_evaluated,
            intermediate_findings=findings,
            predictions=predictions,
            assumptions=assumptions,
            abstentions=(
                [{"reason": prediction.abstention_reason}]
                for prediction in predictions
                if prediction.is_abstention
            ),
            unknowns=[
                "Tenth-house/lord relationship is not implemented.",
                "Atmakaraka activity/work interpretation is not implemented.",
                "Career timing is unavailable.",
            ],
            warnings=warnings,
            provenance_node_id=run_node_id,
        )


def _stable_id(*parts: str) -> str:
    payload = json.dumps(parts, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
