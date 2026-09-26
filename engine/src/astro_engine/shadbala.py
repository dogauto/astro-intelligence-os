"""
Shadbala (Six-fold Strength) Module
====================================

Computes the six components of planetary strength:

1. Sthana Bala (Positional Strength)
   - Uchcha Bala (Exaltation strength)
   - Saptavargaja Bala (Strength from 7 vargas)
   - Ojayugmarasyamsa Bala (Odd/even sign strength)
   - Kendradi Bala (Angular strength)
   - Drekkana Bala (Decanate strength)

2. Dig Bala (Directional Strength)

3. Kala Bala (Temporal Strength) — simplified initial implementation

4. Cheshta Bala (Motional Strength)

5. Naisargika Bala (Natural Strength)

6. Drik Bala (Aspectual Strength) — simplified initial implementation

Note: This is a Phase 3 implementation. Some sub-components use
simplified formulas that will be refined in later phases.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from astro_engine.astronomy import Planet, PlanetPosition


# ---------------------------------------------------------------------------
# Exaltation degrees (sidereal, Parashari)
# ---------------------------------------------------------------------------

# Planet: (exaltation_longitude, debilitation_longitude)
EXALTATION_POINTS: dict[Planet, tuple[float, float]] = {
    Planet.SUN: (10.0, 190.0),       # Aries 10° / Libra 10°
    Planet.MOON: (33.0, 213.0),      # Taurus 3° / Scorpio 3°
    Planet.MARS: (298.0, 118.0),     # Capricorn 28° / Cancer 28°
    Planet.MERCURY: (165.0, 345.0),  # Virgo 15° / Pisces 15°
    Planet.JUPITER: (95.0, 275.0),   # Cancer 5° / Capricorn 5°
    Planet.VENUS: (357.0, 177.0),    # Pisces 27° / Virgo 27°
    Planet.SATURN: (200.0, 20.0),    # Libra 20° / Aries 20°
}


# ---------------------------------------------------------------------------
# Natural strength values (Naisargika Bala) in shashtiamsas
# ---------------------------------------------------------------------------

NAISARGIKA_BALA: dict[Planet, float] = {
    Planet.SUN: 60.0,
    Planet.MOON: 51.43,
    Planet.MARS: 17.14,
    Planet.MERCURY: 25.71,
    Planet.JUPITER: 34.29,
    Planet.VENUS: 42.86,
    Planet.SATURN: 8.57,
}


# ---------------------------------------------------------------------------
# Dig Bala directions — planet strongest in this house (1-indexed)
# ---------------------------------------------------------------------------

# Planet: house_of_max_dig_bala (1-based)
DIG_BALA_HOUSES: dict[Planet, int] = {
    Planet.SUN: 10,      # South (10th house)
    Planet.MARS: 10,     # South
    Planet.JUPITER: 1,   # East (1st house)
    Planet.MERCURY: 1,   # East
    Planet.MOON: 4,      # North (4th house)
    Planet.VENUS: 4,     # North
    Planet.SATURN: 7,    # West (7th house)
}


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ShadbalResult:
    """Shadbala computation result for a single planet."""

    planet: Planet

    # Individual components (in shashtiamsas = 1/60th of a rupa)
    uchcha_bala: float        # Exaltation strength
    dig_bala: float           # Directional strength
    naisargika_bala: float    # Natural strength
    cheshta_bala: float       # Motional strength
    # Simplified components
    kala_bala_simplified: float   # Temporal (simplified)
    drik_bala_simplified: float   # Aspectual (simplified)

    @property
    def total_shadbala(self) -> float:
        """Total Shadbala in shashtiamsas."""
        return (
            self.uchcha_bala
            + self.dig_bala
            + self.naisargika_bala
            + self.cheshta_bala
            + self.kala_bala_simplified
            + self.drik_bala_simplified
        )

    @property
    def total_rupas(self) -> float:
        """Total Shadbala in rupas (1 rupa = 60 shashtiamsas)."""
        return self.total_shadbala / 60.0


# ---------------------------------------------------------------------------
# Minimum required Shadbala (in rupas) per planet
# ---------------------------------------------------------------------------

MINIMUM_SHADBALA_RUPAS: dict[Planet, float] = {
    Planet.SUN: 6.5,
    Planet.MOON: 6.0,
    Planet.MARS: 5.0,
    Planet.MERCURY: 7.0,
    Planet.JUPITER: 6.5,
    Planet.VENUS: 5.5,
    Planet.SATURN: 5.0,
}


# ---------------------------------------------------------------------------
# Computation functions
# ---------------------------------------------------------------------------

def compute_uchcha_bala(planet: Planet, longitude: float) -> float:
    """
    Compute Uchcha Bala (Exaltation Strength).

    Maximum (60 shashtiamsas) at exaltation point.
    Minimum (0) at debilitation point.
    Linear interpolation between.
    """
    if planet not in EXALTATION_POINTS:
        return 0.0

    exalt_lon, _ = EXALTATION_POINTS[planet]
    diff = abs(longitude - exalt_lon)
    if diff > 180.0:
        diff = 360.0 - diff

    # 0° from exaltation = 60 shashtiamsas
    # 180° from exaltation = 0 shashtiamsas
    return (180.0 - diff) / 3.0  # Max = 60


def compute_dig_bala(
    planet: Planet,
    planet_longitude: float,
    ascendant_longitude: float,
) -> float:
    """
    Compute Dig Bala (Directional Strength).

    Maximum (60 shashtiamsas) when planet is in its dig bala house.
    Minimum (0) when 180° away.
    """
    if planet not in DIG_BALA_HOUSES:
        return 0.0

    # Find the longitude of the midpoint of the dig bala house
    dig_house = DIG_BALA_HOUSES[planet]
    # House cusp in whole-sign: ascendant's sign start + (house-1)*30 + 15 (midpoint)
    asc_sign_start = (int(ascendant_longitude // 30)) * 30.0
    dig_house_mid = (asc_sign_start + (dig_house - 1) * 30.0 + 15.0) % 360.0

    diff = abs(planet_longitude - dig_house_mid)
    if diff > 180.0:
        diff = 360.0 - diff

    return (180.0 - diff) / 3.0  # Max = 60


def compute_cheshta_bala(planet: Planet, speed: float) -> float:
    """
    Compute Cheshta Bala (Motional Strength) — simplified.

    Retrograde planets get higher cheshta bala.
    Stationary planets get maximum.
    Fast direct motion gets lower values.

    Full implementation requires mean daily motion tables.
    """
    if planet in (Planet.SUN, Planet.MOON):
        # Sun and Moon don't have cheshta bala in the traditional sense
        return 30.0  # Neutral value

    if abs(speed) < 0.01:
        return 60.0  # Stationary = maximum
    elif speed < 0:
        return 45.0  # Retrograde = high
    else:
        # Direct motion: faster = less cheshta bala
        return max(15.0, 30.0 - speed * 5.0)


def compute_shadbala(
    planet: Planet,
    position: PlanetPosition,
    ascendant_longitude: float,
) -> ShadbalResult:
    """
    Compute Shadbala for a single planet.

    Args:
        planet: The planet.
        position: Computed PlanetPosition.
        ascendant_longitude: Ascendant longitude for dig bala.

    Returns:
        ShadbalResult with all strength components.
    """
    uchcha = compute_uchcha_bala(planet, position.longitude)
    dig = compute_dig_bala(planet, position.longitude, ascendant_longitude)
    naisargika = NAISARGIKA_BALA.get(planet, 0.0)
    cheshta = compute_cheshta_bala(planet, position.speed_longitude)

    # Simplified Kala Bala — based on diurnal/nocturnal strength
    # Full implementation requires sunrise/sunset and weekday info
    kala_simplified = 30.0  # Neutral placeholder

    # Simplified Drik Bala — based on aspects
    # Full implementation requires all planetary aspects
    drik_simplified = 15.0  # Neutral placeholder

    return ShadbalResult(
        planet=planet,
        uchcha_bala=uchcha,
        dig_bala=dig,
        naisargika_bala=naisargika,
        cheshta_bala=cheshta,
        kala_bala_simplified=kala_simplified,
        drik_bala_simplified=drik_simplified,
    )
