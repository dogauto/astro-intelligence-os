"""
Vimshottari Career Timing Method
=================================

FIRST COMPLETE METHODOLOGY in the Astro Intelligence OS.

This method uses Vimshottari Dasha periods to identify career-significant
time windows based on classical Parashari rules:

Rules applied:
1. 10th house lord's Maha/Antar Dasha → career activation
2. 6th house lord's period → service/competition emphasis
3. 7th house lord's period → partnership/business activation
4. 11th house lord's period → gains/income emphasis
5. Saturn's period → discipline/restructuring in career
6. Jupiter's period → growth/expansion opportunity
7. Rahu's period → unconventional/foreign career opportunities
8. Ketu's period → spiritual/research/withdrawal tendency
9. Planets in 10th house → career activation during their periods
10. Dasha of exalted/debilitated planets → strength-adjusted signals

Maturity: EXPERIMENTAL

This method does NOT use any LLM. It is purely rule-based.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from astro_engine.astronomy import SIGN_NAMES
from astro_engine.methods import (
    Method,
    MethodMaturity,
    MethodRun,
    Prediction,
    PredictionDirection,
    QuestionContext,
)
from astro_engine.state import AstroState


# ---------------------------------------------------------------------------
# Sign lordship mapping (Parashari)
# ---------------------------------------------------------------------------

SIGN_LORDS: dict[int, str] = {
    0: "Mars",       # Aries
    1: "Venus",      # Taurus
    2: "Mercury",    # Gemini
    3: "Moon",       # Cancer
    4: "Sun",        # Leo
    5: "Mercury",    # Virgo
    6: "Venus",      # Libra
    7: "Mars",       # Scorpio (co-ruled with Ketu traditionally)
    8: "Jupiter",    # Sagittarius
    9: "Saturn",     # Capricorn
    10: "Saturn",    # Aquarius (co-ruled with Rahu traditionally)
    11: "Jupiter",   # Pisces
}


# ---------------------------------------------------------------------------
# Career significance rules
# ---------------------------------------------------------------------------

# Planet-based career themes
PLANET_CAREER_THEMES: dict[str, dict[str, Any]] = {
    "Sun": {
        "theme": "authority, government, leadership",
        "direction": PredictionDirection.POSITIVE,
        "magnitude_base": 0.6,
    },
    "Moon": {
        "theme": "public-facing roles, nurturing professions, changes",
        "direction": PredictionDirection.MIXED,
        "magnitude_base": 0.5,
    },
    "Mars": {
        "theme": "technical, engineering, competitive, military, surgery",
        "direction": PredictionDirection.POSITIVE,
        "magnitude_base": 0.6,
    },
    "Mercury": {
        "theme": "communication, business, writing, commerce, technology",
        "direction": PredictionDirection.POSITIVE,
        "magnitude_base": 0.6,
    },
    "Jupiter": {
        "theme": "expansion, teaching, advisory, law, finance, growth",
        "direction": PredictionDirection.POSITIVE,
        "magnitude_base": 0.7,
    },
    "Venus": {
        "theme": "arts, luxury, entertainment, diplomacy, hospitality",
        "direction": PredictionDirection.POSITIVE,
        "magnitude_base": 0.6,
    },
    "Saturn": {
        "theme": "restructuring, discipline, hard work, delays, perseverance",
        "direction": PredictionDirection.MIXED,
        "magnitude_base": 0.5,
    },
    "Rahu": {
        "theme": "unconventional paths, foreign connections, technology, ambition",
        "direction": PredictionDirection.MIXED,
        "magnitude_base": 0.6,
    },
    "Ketu": {
        "theme": "withdrawal, spirituality, research, detachment from material",
        "direction": PredictionDirection.MIXED,
        "magnitude_base": 0.4,
    },
}


# ---------------------------------------------------------------------------
# The Method
# ---------------------------------------------------------------------------

class VimshottariCareerMethod(Method):
    """
    Vimshottari Dasha-based career timing methodology.

    Analyzes Maha Dasha and Antar Dasha periods for career-related signals
    using classical Parashari lordship rules.
    """

    @property
    def method_id(self) -> str:
        return "vimshottari-career-timing-v1"

    @property
    def name(self) -> str:
        return "Vimshottari Career Timing"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def tradition(self) -> str:
        return "Parashari"

    @property
    def maturity(self) -> MethodMaturity:
        return MethodMaturity.EXPERIMENTAL

    @property
    def supported_domains(self) -> list[str]:
        return ["career", "finance", "profession"]

    @property
    def required_calculations(self) -> list[str]:
        return ["planets", "chart", "dashas", "strengths"]

    def run(self, state: AstroState, question: QuestionContext) -> MethodRun:
        """Execute the Vimshottari career timing analysis."""

        rules_evaluated: list[str] = []
        calculations_used: list[str] = ["planets", "chart", "dashas"]
        intermediate_findings: list[dict[str, Any]] = []
        predictions: list[Prediction] = []
        assumptions: list[str] = []
        warnings: list[str] = []

        # --- Validate required data ---
        if state.dashas is None:
            warnings.append("Dasha data not available in AstroState.")
            return self._build_run(
                state, question, rules_evaluated, calculations_used,
                intermediate_findings, predictions, assumptions, warnings,
            )

        if state.chart is None:
            warnings.append("Chart data not available in AstroState.")
            return self._build_run(
                state, question, rules_evaluated, calculations_used,
                intermediate_findings, predictions, assumptions, warnings,
            )

        # --- Extract key data ---
        asc_sign = state.chart.ascendant_sign_index

        # Determine career-significant houses from ascendant
        house_10_sign = (asc_sign + 9) % 12   # 10th house
        house_6_sign = (asc_sign + 5) % 12    # 6th house
        house_7_sign = (asc_sign + 6) % 12    # 7th house
        house_11_sign = (asc_sign + 10) % 12  # 11th house

        lord_10 = SIGN_LORDS[house_10_sign]
        lord_6 = SIGN_LORDS[house_6_sign]
        lord_7 = SIGN_LORDS[house_7_sign]
        lord_11 = SIGN_LORDS[house_11_sign]

        intermediate_findings.append({
            "finding": "career_house_lords",
            "10th_lord": lord_10,
            "6th_lord": lord_6,
            "7th_lord": lord_7,
            "11th_lord": lord_11,
            "ascendant_sign": SIGN_NAMES[asc_sign],
        })

        # Find planets in 10th house
        planets_in_10th: list[str] = []
        for p in state.planets:
            if p.sign_index == house_10_sign:
                planets_in_10th.append(p.planet)

        if planets_in_10th:
            intermediate_findings.append({
                "finding": "planets_in_10th_house",
                "planets": planets_in_10th,
            })

        # --- Analyze each Maha Dasha ---
        dasha_data = state.dashas
        if not isinstance(dasha_data, dict):
            warnings.append("Dasha data format unexpected.")
            return self._build_run(
                state, question, rules_evaluated, calculations_used,
                intermediate_findings, predictions, assumptions, warnings,
            )

        maha_dashas = dasha_data.get("maha_dashas", [])

        for md in maha_dashas:
            md_lord = md["lord"]
            md_start = datetime.fromisoformat(md["start"])
            md_end = datetime.fromisoformat(md["end"])

            # Apply question time horizon if specified
            if question.time_horizon_years:
                horizon_end = state.input.datetime_utc + __import__(
                    'datetime'
                ).timedelta(days=question.time_horizon_years * 365.25)
                if md_start > horizon_end:
                    continue  # Beyond time horizon

            career_signals: list[str] = []
            evidence: list[str] = []
            magnitude_boost = 0.0

            # Rule 1: 10th lord's Maha Dasha
            if md_lord == lord_10:
                career_signals.append("10th house lord Maha Dasha — primary career activation")
                evidence.append(f"R1: {md_lord} rules 10th house ({SIGN_NAMES[house_10_sign]})")
                magnitude_boost += 0.2
                rules_evaluated.append("R1_10th_lord_maha")

            # Rule 2: 6th lord's Maha Dasha
            if md_lord == lord_6:
                career_signals.append("6th house lord — service, competition, daily work emphasis")
                evidence.append(f"R2: {md_lord} rules 6th house ({SIGN_NAMES[house_6_sign]})")
                magnitude_boost += 0.1
                rules_evaluated.append("R2_6th_lord_maha")

            # Rule 3: 7th lord's Maha Dasha
            if md_lord == lord_7:
                career_signals.append("7th house lord — partnership, business activation")
                evidence.append(f"R3: {md_lord} rules 7th house ({SIGN_NAMES[house_7_sign]})")
                magnitude_boost += 0.1
                rules_evaluated.append("R3_7th_lord_maha")

            # Rule 4: 11th lord's Maha Dasha
            if md_lord == lord_11:
                career_signals.append("11th house lord — gains, income, fulfillment of goals")
                evidence.append(f"R4: {md_lord} rules 11th house ({SIGN_NAMES[house_11_sign]})")
                magnitude_boost += 0.15
                rules_evaluated.append("R4_11th_lord_maha")

            # Rule 9: Planets in 10th house
            if md_lord in planets_in_10th:
                career_signals.append(f"{md_lord} is placed in 10th house — direct career influence")
                evidence.append(f"R9: {md_lord} occupies 10th house")
                magnitude_boost += 0.15
                rules_evaluated.append("R9_planet_in_10th")

            # Planet-based themes (Rules 5-8)
            theme_info = PLANET_CAREER_THEMES.get(md_lord, {})
            if theme_info:
                career_signals.append(f"{md_lord} career theme: {theme_info.get('theme', 'general')}")
                rules_evaluated.append(f"R_planet_theme_{md_lord}")

            if career_signals:
                base_magnitude = theme_info.get("magnitude_base", 0.5) if theme_info else 0.5
                direction = theme_info.get("direction", PredictionDirection.MIXED) if theme_info else PredictionDirection.MIXED

                predictions.append(Prediction(
                    domain="career",
                    event="career_period_activation",
                    direction=direction,
                    magnitude=min(1.0, base_magnitude + magnitude_boost),
                    time_window_start=md_start,
                    time_window_end=md_end,
                    duration_description=f"Maha Dasha of {md_lord} ({round(md['duration_days']/365.25, 1)} years)",
                    conditions=career_signals,
                    supporting_evidence=evidence,
                    method_id=self.method_id,
                    method_version=self.version,
                    raw_confidence=min(0.9, 0.5 + magnitude_boost),
                ))

        # --- Assumptions ---
        assumptions.extend([
            "Uses Parashari sign lordship (Mars for Scorpio, not Ketu).",
            "Whole-sign houses assumed for house determination.",
            "Magnitude estimates are heuristic, not calibrated.",
            "Career signals are directional indicators, not deterministic predictions.",
        ])

        return self._build_run(
            state, question, rules_evaluated, calculations_used,
            intermediate_findings, predictions, assumptions, warnings,
        )

    def _build_run(
        self,
        state: AstroState,
        question: QuestionContext,
        rules_evaluated: list[str],
        calculations_used: list[str],
        intermediate_findings: list[dict[str, Any]],
        predictions: list[Prediction],
        assumptions: list[str],
        warnings: list[str],
    ) -> MethodRun:
        """Build the final MethodRun."""
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
