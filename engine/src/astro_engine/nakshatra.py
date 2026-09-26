"""
Nakshatra Module
================

Computes Nakshatra (lunar mansion) and Pada from Moon longitude.

The 27 Nakshatras divide the 360° zodiac into 13°20' segments.
Each Nakshatra has 4 Padas of 3°20' each.
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Nakshatra data
# ---------------------------------------------------------------------------

NAKSHATRA_NAMES: list[str] = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra",
    "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_LORDS: list[str] = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]

NAKSHATRA_SPAN = 360.0 / 27.0  # 13°20' = 13.3333...°
PADA_SPAN = NAKSHATRA_SPAN / 4.0  # 3°20' = 3.3333...°


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NakshatraResult:
    """Computed Nakshatra information for a given longitude."""

    nakshatra_index: int  # 0-based (0 = Ashwini, 26 = Revati)
    nakshatra_name: str
    pada: int  # 1-based (1, 2, 3, or 4)
    nakshatra_lord: str  # Vimshottari dasha lord
    degrees_in_nakshatra: float  # [0, 13.333...)
    absolute_longitude: float  # The input longitude


# ---------------------------------------------------------------------------
# Computation
# ---------------------------------------------------------------------------

def compute_nakshatra(longitude: float) -> NakshatraResult:
    """
    Compute the Nakshatra and Pada for a given ecliptic longitude.

    Args:
        longitude: Sidereal longitude in degrees [0, 360).

    Returns:
        NakshatraResult with full provenance.
    """
    longitude = longitude % 360.0

    nakshatra_index = int(longitude / NAKSHATRA_SPAN)
    if nakshatra_index >= 27:
        nakshatra_index = 26  # Safety clamp

    degrees_in_nakshatra = longitude - (nakshatra_index * NAKSHATRA_SPAN)
    pada = int(degrees_in_nakshatra / PADA_SPAN) + 1
    if pada > 4:
        pada = 4  # Safety clamp

    return NakshatraResult(
        nakshatra_index=nakshatra_index,
        nakshatra_name=NAKSHATRA_NAMES[nakshatra_index],
        pada=pada,
        nakshatra_lord=NAKSHATRA_LORDS[nakshatra_index],
        degrees_in_nakshatra=degrees_in_nakshatra,
        absolute_longitude=longitude,
    )
