"""
Transit (Gochara) Career Methodology
====================================

SECOND COMPLETE METHODOLOGY in the Astro Intelligence OS.

This method uses Gochara (Transit) principles to identify current or
impending career conditions. It is traditionally calculated relative
to the natal Moon (Chandra Lagna).

Rules applied:
1. Jupiter transiting 2nd, 5th, 7th, 9th, or 11th from natal Moon = Growth/Opportunity.
2. Saturn transiting 10th from natal Moon = Career pressure, hard work, restructuring.
3. Saturn transiting 12th, 1st, or 2nd from natal Moon = Sade Sati (deep transition).
4. Rahu transiting 10th from natal Moon = Career ambition, foreign opportunities.
5. Jupiter transiting 10th from natal Moon = Career changes, sometimes loss of position.

Maturity: EXPERIMENTAL
"""

from __future__ import annotations

from typing import Any

from astro_engine.methods import (
    Method,
    MethodMaturity,
    MethodRun,
    Prediction,
    PredictionDirection,
    QuestionContext,
)
from astro_engine.state import AstroState


class TransitCareerMethod(Method):
    """
    Transit/Gochara-based career timing methodology.
    Analyzes current transits relative to the natal Moon.
    """

    @property
    def method_id(self) -> str:
        return "gochara-career-transit-v1"

    @property
    def name(self) -> str:
        return "Gochara Career Transit"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def tradition(self) -> str:
        return "Parashari/Gochara"

    @property
    def maturity(self) -> MethodMaturity:
        return MethodMaturity.EXPERIMENTAL

    @property
    def supported_domains(self) -> list[str]:
        return ["career", "finance", "general"]

    @property
    def required_calculations(self) -> list[str]:
        return ["planets", "transit"]

    def run(self, state: AstroState, question: QuestionContext) -> MethodRun:
        rules_evaluated: list[str] = []
        calculations_used: list[str] = ["planets", "transit"]
        intermediate_findings: list[dict[str, Any]] = []
        predictions: list[Prediction] = []
        assumptions: list[str] = []
        warnings: list[str] = []

        if not state.transit:
            return MethodRun(
                method_id=self.method_id,
                method_version=self.version,
                input_state_id=state.state_id,
                question=question,
                rules_evaluated=[],
                calculations_used=calculations_used,
                intermediate_findings=[],
                predictions=[
                    Prediction(
                        domain=question.domain,
                        event=question.event,
                        is_abstention=True,
                        abstention_reason="No transit data available in AstroState.",
                    )
                ],
                assumptions=["Requires transit positions computed in AstroState."],
                warnings=["Transit data missing, abstaining."],
            )

        # Find natal Moon sign
        natal_moon_sign = None
        for p in state.planets:
            if p.planet == "Moon":
                natal_moon_sign = p.sign_index
                break

        if natal_moon_sign is None:
            warnings.append("Natal Moon not found.")
            return self._build_abstention(state, question, calculations_used, warnings)

        intermediate_findings.append({
            "finding": "natal_moon_sign",
            "sign_index": natal_moon_sign,
        })

        # Analyze transits
        transit_planets = state.transit.get("planets", [])
        transit_date = state.transit.get("datetime_utc", "Unknown")

        for tp in transit_planets:
            planet = tp["planet"]
            t_sign = tp["sign_index"]

            # Calculate house from Moon (1-indexed)
            house_from_moon = (t_sign - natal_moon_sign) % 12 + 1

            # Rule 1: Jupiter benefic transits
            if planet == "Jupiter":
                if house_from_moon in [2, 5, 7, 9, 11]:
                    rules_evaluated.append(f"jupiter_transit_{house_from_moon}_from_moon")
                    predictions.append(Prediction(
                        domain="career",
                        event="career_growth",
                        direction=PredictionDirection.POSITIVE,
                        magnitude=0.7, # HEURISTIC
                        duration_description=f"Current Jupiter transit in house {house_from_moon} from Moon",
                        conditions=["Jupiter transiting auspicious house from natal Moon"],
                        supporting_evidence=[f"Jupiter in sign {t_sign}, {house_from_moon}th from Moon"],
                        method_id=self.method_id,
                        method_version=self.version,
                        provenance={"transit_datetime": transit_date},
                    ))
                elif house_from_moon == 10:
                    rules_evaluated.append("jupiter_transit_10_from_moon")
                    predictions.append(Prediction(
                        domain="career",
                        event="career_transition",
                        direction=PredictionDirection.MIXED,
                        magnitude=0.6, # HEURISTIC
                        duration_description="Current Jupiter transit in 10th from Moon",
                        conditions=["Jupiter transiting 10th house from natal Moon (traditionally brings changes or loss of status)"],
                        supporting_evidence=[f"Jupiter in sign {t_sign}, 10th from Moon"],
                        method_id=self.method_id,
                        method_version=self.version,
                        provenance={"transit_datetime": transit_date},
                    ))

            # Rules 2 & 3: Saturn transits
            if planet == "Saturn":
                if house_from_moon == 10:
                    rules_evaluated.append("saturn_transit_10_from_moon")
                    predictions.append(Prediction(
                        domain="career",
                        event="career_pressure",
                        direction=PredictionDirection.MIXED,
                        magnitude=0.8, # HEURISTIC
                        duration_description="Current Saturn transit in 10th from Moon",
                        conditions=["Saturn transiting 10th house from natal Moon (intense pressure, hard work, restructuring)"],
                        supporting_evidence=[f"Saturn in sign {t_sign}, 10th from Moon"],
                        method_id=self.method_id,
                        method_version=self.version,
                        provenance={"transit_datetime": transit_date},
                    ))
                elif house_from_moon in [12, 1, 2]:
                    rules_evaluated.append("saturn_sade_sati")
                    predictions.append(Prediction(
                        domain="general",
                        event="major_life_transition",
                        direction=PredictionDirection.MIXED,
                        magnitude=0.9, # HEURISTIC
                        duration_description="Current Sade Sati phase",
                        conditions=[f"Saturn transiting {house_from_moon}th house from natal Moon (Sade Sati)"],
                        supporting_evidence=[f"Saturn in sign {t_sign}, near natal Moon"],
                        method_id=self.method_id,
                        method_version=self.version,
                        provenance={"transit_datetime": transit_date},
                    ))

            # Rule 4: Rahu transit
            if planet == "Rahu":
                if house_from_moon == 10:
                    rules_evaluated.append("rahu_transit_10_from_moon")
                    predictions.append(Prediction(
                        domain="career",
                        event="career_ambition",
                        direction=PredictionDirection.POSITIVE,
                        magnitude=0.7, # HEURISTIC
                        duration_description="Current Rahu transit in 10th from Moon",
                        conditions=["Rahu transiting 10th house from natal Moon (ambition, sudden changes, foreign links)"],
                        supporting_evidence=[f"Rahu in sign {t_sign}, 10th from Moon"],
                        method_id=self.method_id,
                        method_version=self.version,
                        provenance={"transit_datetime": transit_date},
                    ))

        assumptions.append("All prediction magnitudes are purely HEURISTIC and not calibrated probabilities.")
        assumptions.append("Transit houses are calculated using whole sign houses from the natal Moon (Chandra Lagna).")

        return MethodRun(
            method_id=self.method_id,
            method_version=self.version,
            input_state_id=state.state_id,
            question=question,
            rules_evaluated=rules_evaluated,
            calculations_used=calculations_used,
            intermediate_findings=intermediate_findings,
            predictions=predictions,
            assumptions=assumptions,
            warnings=warnings,
        )

    def _build_abstention(self, state, question, calc, warnings):
        return MethodRun(
            method_id=self.method_id,
            method_version=self.version,
            input_state_id=state.state_id,
            question=question,
            rules_evaluated=[],
            calculations_used=calc,
            intermediate_findings=[],
            predictions=[
                Prediction(
                    domain=question.domain,
                    event=question.event,
                    is_abstention=True,
                    abstention_reason="Missing necessary calculations.",
                )
            ],
            assumptions=[],
            warnings=warnings,
        )
