"""
Ashtakavarga Module
===================

Computes Sarva Ashtakavarga (SAV) and Bhinna Ashtakavarga (BAV)
for the 7 planets (Sun through Saturn).

Ashtakavarga is a system where each planet contributes benefic points
(bindus) to signs based on its position relative to other planets
and the ascendant.

Each planet has a fixed table of beneficial positions (houses counted
from itself and from other contributing bodies). The final BAV table
shows how many bindus each sign receives from each planet. SAV is the
sum across all 7 planets.
"""

from __future__ import annotations

from dataclasses import dataclass

from astro_engine.astronomy import Planet

# ---------------------------------------------------------------------------
# Benefic positions for each planet (houses where bindu is given)
# These are counted from each contributing body
# Format: {receiving_planet: {contributing_body: [houses_1_indexed]}}
# ---------------------------------------------------------------------------

# Simplified Parashari Ashtakavarga benefic house tables
# These define which houses (counted from each contributing body)
# give a bindu to the receiving planet.

_ASHTAKAVARGA_TABLE: dict[str, dict[str, list[int]]] = {
    "Sun": {
        "Sun":     [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon":    [3, 6, 10, 11],
        "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11],
        "Venus":   [6, 7, 12],
        "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna":   [3, 4, 6, 10, 11, 12],
    },
    "Moon": {
        "Sun":     [3, 6, 7, 8, 10, 11],
        "Moon":    [1, 3, 6, 7, 10, 11],
        "Mars":    [2, 3, 5, 6, 9, 10, 11],
        "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [1, 4, 7, 8, 10, 11, 12],
        "Venus":   [3, 4, 5, 7, 9, 10, 11],
        "Saturn":  [3, 5, 6, 11],
        "Lagna":   [3, 6, 10, 11],
    },
    "Mars": {
        "Sun":     [3, 5, 6, 10, 11],
        "Moon":    [3, 6, 11],
        "Mars":    [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [3, 5, 6, 11],
        "Jupiter": [6, 10, 11, 12],
        "Venus":   [6, 8, 11, 12],
        "Saturn":  [1, 4, 7, 8, 9, 10, 11],
        "Lagna":   [1, 3, 6, 10, 11],
    },
    "Mercury": {
        "Sun":     [5, 6, 9, 11, 12],
        "Moon":    [2, 4, 6, 8, 10, 11],
        "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [6, 8, 11, 12],
        "Venus":   [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna":   [1, 2, 4, 6, 8, 10, 11],
    },
    "Jupiter": {
        "Sun":     [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "Moon":    [2, 5, 7, 9, 11],
        "Mars":    [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
        "Venus":   [2, 5, 6, 9, 10, 11],
        "Saturn":  [3, 5, 6, 12],
        "Lagna":   [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "Venus": {
        "Sun":     [8, 11, 12],
        "Moon":    [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars":    [3, 5, 6, 9, 11, 12],
        "Mercury": [3, 5, 6, 9, 11],
        "Jupiter": [5, 8, 9, 10, 11],
        "Venus":   [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn":  [3, 4, 5, 8, 9, 10, 11],
        "Lagna":   [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "Saturn": {
        "Sun":     [1, 2, 4, 7, 8, 10, 11],
        "Moon":    [3, 6, 11],
        "Mars":    [3, 5, 6, 10, 11, 12],
        "Mercury": [6, 8, 9, 10, 11, 12],
        "Jupiter": [5, 6, 11, 12],
        "Venus":   [6, 11, 12],
        "Saturn":  [3, 5, 6, 11],
        "Lagna":   [1, 3, 4, 6, 10, 11],
    },
}

# Map planet name to Planet enum for lookups
_PLANET_NAME_MAP: dict[str, Planet] = {
    "Sun": Planet.SUN,
    "Moon": Planet.MOON,
    "Mars": Planet.MARS,
    "Mercury": Planet.MERCURY,
    "Jupiter": Planet.JUPITER,
    "Venus": Planet.VENUS,
    "Saturn": Planet.SATURN,
}

_BAV_PLANETS: list[str] = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AshtakavargaResult:
    """Complete Ashtakavarga computation result."""

    # BAV: {planet_name: [12 bindu values, one per sign 0-11]}
    bav: dict[str, list[int]]

    # SAV: [12 values, one per sign 0-11] — sum of all BAV
    sav: list[int]

    @property
    def total_bindus(self) -> int:
        """Total SAV bindus across all signs (should be 337)."""
        return sum(self.sav)

    def get_sign_strength(self, sign_index: int) -> int:
        """Get SAV bindus for a specific sign."""
        return self.sav[sign_index]


# ---------------------------------------------------------------------------
# Computation
# ---------------------------------------------------------------------------

def compute_ashtakavarga(
    planet_signs: dict[str, int],
    ascendant_sign: int,
) -> AshtakavargaResult:
    """
    Compute Bhinna (BAV) and Sarva (SAV) Ashtakavarga.

    Args:
        planet_signs: Mapping of planet name to sign index (0-based).
                      Must include Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn.
        ascendant_sign: The ascendant's sign index (0-based).

    Returns:
        AshtakavargaResult with BAV and SAV tables.
    """
    bav: dict[str, list[int]] = {}

    for receiving_planet in _BAV_PLANETS:
        bindu_table = [0] * 12  # 12 signs
        planet_table = _ASHTAKAVARGA_TABLE[receiving_planet]

        for contributing_body, benefic_houses in planet_table.items():
            if contributing_body == "Lagna":
                ref_sign = ascendant_sign
            else:
                if contributing_body not in planet_signs:
                    continue
                ref_sign = planet_signs[contributing_body]

            for house in benefic_houses:
                target_sign = (ref_sign + house - 1) % 12
                bindu_table[target_sign] += 1

        bav[receiving_planet] = bindu_table

    # Compute SAV
    sav = [0] * 12
    for sign_idx in range(12):
        for planet_name in _BAV_PLANETS:
            sav[sign_idx] += bav[planet_name][sign_idx]

    return AshtakavargaResult(bav=bav, sav=sav)
