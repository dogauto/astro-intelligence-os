"""
Vimshottari Dasha Module
========================

Computes the Vimshottari Maha Dasha, Antar Dasha (Bhukti),
and Pratyantar Dasha periods based on the Moon's nakshatra position.

The Vimshottari system uses a 120-year cycle distributed among 9 planets
based on the nakshatra lord sequence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from astro_engine.nakshatra import NAKSHATRA_LORDS, NAKSHATRA_SPAN, compute_nakshatra


# ---------------------------------------------------------------------------
# Vimshottari Dasha periods (in years)
# ---------------------------------------------------------------------------

DASHA_YEARS: dict[str, float] = {
    "Ketu": 7.0,
    "Venus": 20.0,
    "Sun": 6.0,
    "Moon": 10.0,
    "Mars": 7.0,
    "Rahu": 18.0,
    "Jupiter": 16.0,
    "Saturn": 19.0,
    "Mercury": 17.0,
}

# The standard order of dasha lords
DASHA_LORD_ORDER: list[str] = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]

TOTAL_DASHA_YEARS: float = 120.0  # Sum of all dasha periods

# One year in days (approximate, for dasha computation)
YEAR_IN_DAYS: float = 365.25


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DashaPeriod:
    """A single dasha/antardasha/pratyantardasha period."""

    level: str  # "maha", "antar", "pratyantar"
    lord: str  # Planet name
    start: datetime
    end: datetime
    duration_days: float
    sub_periods: list[DashaPeriod] = field(default_factory=list)

    @property
    def duration_years(self) -> float:
        return self.duration_days / YEAR_IN_DAYS

    def is_active(self, dt: datetime) -> bool:
        """Check if this period is active at the given datetime."""
        return self.start <= dt < self.end


@dataclass(frozen=True)
class DashaState:
    """Complete Vimshottari dasha computation result."""

    moon_longitude: float
    nakshatra_name: str
    nakshatra_lord: str
    nakshatra_balance: float  # Fraction of first dasha remaining at birth
    birth_datetime: datetime
    maha_dashas: list[DashaPeriod]

    def get_active_maha(self, dt: datetime) -> Optional[DashaPeriod]:
        """Find the active Maha Dasha at the given time."""
        for md in self.maha_dashas:
            if md.is_active(dt):
                return md
        return None

    def get_active_periods(self, dt: datetime) -> dict[str, DashaPeriod]:
        """Find active Maha, Antar, and Pratyantar at the given time."""
        result: dict[str, DashaPeriod] = {}
        maha = self.get_active_maha(dt)
        if maha:
            result["maha"] = maha
            for antar in maha.sub_periods:
                if antar.is_active(dt):
                    result["antar"] = antar
                    for pratyantar in antar.sub_periods:
                        if pratyantar.is_active(dt):
                            result["pratyantar"] = pratyantar
                            break
                    break
        return result


# ---------------------------------------------------------------------------
# Computation
# ---------------------------------------------------------------------------

def _get_lord_order_from(start_lord: str) -> list[str]:
    """Get the 9-lord sequence starting from the given lord."""
    idx = DASHA_LORD_ORDER.index(start_lord)
    return DASHA_LORD_ORDER[idx:] + DASHA_LORD_ORDER[:idx]


def _compute_sub_periods(
    parent_lord: str,
    parent_start: datetime,
    parent_duration_days: float,
    level: str,
    compute_sub: bool = False,
) -> list[DashaPeriod]:
    """
    Compute sub-periods (antar or pratyantar) within a parent period.

    The sub-period sequence starts with the parent's lord and follows
    the standard Vimshottari order. Each sub-period's duration is
    proportional to its lord's dasha years relative to the total.
    """
    lord_order = _get_lord_order_from(parent_lord)
    periods: list[DashaPeriod] = []
    current_start = parent_start

    for lord in lord_order:
        # Sub-period duration = parent_duration * (lord_years / total_years)
        sub_duration_days = parent_duration_days * (DASHA_YEARS[lord] / TOTAL_DASHA_YEARS)
        sub_end = current_start + timedelta(days=sub_duration_days)

        sub_sub_periods: list[DashaPeriod] = []
        if compute_sub:
            sub_sub_periods = _compute_sub_periods(
                lord, current_start, sub_duration_days,
                level="pratyantar", compute_sub=False,
            )

        periods.append(DashaPeriod(
            level=level,
            lord=lord,
            start=current_start,
            end=sub_end,
            duration_days=sub_duration_days,
            sub_periods=sub_sub_periods,
        ))
        current_start = sub_end

    return periods


def compute_vimshottari_dasha(
    moon_longitude: float,
    birth_datetime: datetime,
    compute_antar: bool = True,
    compute_pratyantar: bool = True,
) -> DashaState:
    """
    Compute the full Vimshottari Dasha from the Moon's sidereal longitude.

    Args:
        moon_longitude: Sidereal longitude of the Moon [0, 360).
        birth_datetime: The birth datetime (timezone-aware).
        compute_antar: Whether to compute Antar Dasha sub-periods.
        compute_pratyantar: Whether to compute Pratyantar Dasha sub-sub-periods.

    Returns:
        DashaState with all computed periods.
    """
    if birth_datetime.tzinfo is None:
        raise ValueError("birth_datetime must be timezone-aware.")

    # Determine nakshatra and balance
    nak = compute_nakshatra(moon_longitude)
    degrees_in_nakshatra = nak.degrees_in_nakshatra
    balance = 1.0 - (degrees_in_nakshatra / NAKSHATRA_SPAN)

    # The first dasha lord is the nakshatra lord
    first_lord = nak.nakshatra_lord
    lord_order = _get_lord_order_from(first_lord)

    # Build Maha Dashas
    maha_dashas: list[DashaPeriod] = []
    current_start = birth_datetime

    for i, lord in enumerate(lord_order):
        full_duration_days = DASHA_YEARS[lord] * YEAR_IN_DAYS

        if i == 0:
            # First dasha: only the remaining balance
            duration_days = full_duration_days * balance
        else:
            duration_days = full_duration_days

        end = current_start + timedelta(days=duration_days)

        # Compute sub-periods if requested
        sub_periods: list[DashaPeriod] = []
        if compute_antar:
            sub_periods = _compute_sub_periods(
                lord, current_start, duration_days,
                level="antar", compute_sub=compute_pratyantar,
            )

        maha_dashas.append(DashaPeriod(
            level="maha",
            lord=lord,
            start=current_start,
            end=end,
            duration_days=duration_days,
            sub_periods=sub_periods,
        ))
        current_start = end

    return DashaState(
        moon_longitude=moon_longitude,
        nakshatra_name=nak.nakshatra_name,
        nakshatra_lord=nak.nakshatra_lord,
        nakshatra_balance=balance,
        birth_datetime=birth_datetime,
        maha_dashas=maha_dashas,
    )
