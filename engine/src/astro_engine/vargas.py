"""
Varga (Divisional Charts) Module
================================

Computes divisional chart positions for all standard vargas.

Each varga divides each sign into sub-divisions. The planet's position
in the varga chart is determined by which sub-division it falls in.

Supported vargas:
D1 (Rasi), D2 (Hora), D3 (Drekkana), D4 (Chaturthamsa),
D7 (Saptamsa), D9 (Navamsa), D10 (Dasamsa), D12 (Dwadasamsa),
D16 (Shodasamsa), D20 (Vimsamsa), D24 (Chaturvimsamsa),
D27 (Saptavimsamsa/Bhamsa), D30 (Trimsamsa), D40 (Khavedamsa),
D45 (Akshavedamsa), D60 (Shashtiamsa)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from astro_engine.astronomy import SIGN_NAMES


# ---------------------------------------------------------------------------
# Varga types
# ---------------------------------------------------------------------------

class VargaType(IntEnum):
    """Standard divisional chart types."""

    D1 = 1
    D2 = 2
    D3 = 3
    D4 = 4
    D7 = 7
    D9 = 9
    D10 = 10
    D12 = 12
    D16 = 16
    D20 = 20
    D24 = 24
    D27 = 27
    D30 = 30
    D40 = 40
    D45 = 45
    D60 = 60


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VargaPosition:
    """A planet's position in a specific divisional chart."""

    varga: VargaType
    sign_index: int  # 0-based (0=Aries, 11=Pisces)
    sign_name: str
    degrees_in_sign: float
    source_longitude: float  # The original sidereal longitude


# ---------------------------------------------------------------------------
# Generic equal-division varga computation
# ---------------------------------------------------------------------------

def _compute_equal_division_varga(
    longitude: float,
    division: int,
) -> tuple[int, float]:
    """
    Generic computation for vargas that use equal division of each sign.

    For a D-N chart, each sign (30°) is divided into N equal parts of (30/N)°.
    The sub-division index determines the resulting sign.

    Args:
        longitude: Sidereal longitude [0, 360).
        division: The division number (e.g. 9 for Navamsa).

    Returns:
        (resulting_sign_index, degrees_in_resulting_sign)
    """
    longitude = longitude % 360.0
    sign_index = int(longitude // 30)
    degrees_in_sign = longitude % 30.0

    part_size = 30.0 / division
    part_index = int(degrees_in_sign / part_size)
    if part_index >= division:
        part_index = division - 1  # Safety clamp

    # The resulting sign = (original_sign * division + part_index) % 12
    # This is the standard Parashari formula for equal-division vargas
    result_sign = (sign_index * division + part_index) % 12

    # Degrees in the resulting sign — stretch the sub-part to fill 30°
    degrees_into_part = degrees_in_sign - (part_index * part_size)
    result_degrees = (degrees_into_part / part_size) * 30.0

    return result_sign, result_degrees


# ---------------------------------------------------------------------------
# D2 — Hora
# ---------------------------------------------------------------------------

def _compute_hora(longitude: float) -> tuple[int, float]:
    """
    D2 (Hora) chart — Parashari method.

    Sun's hora = Leo (sign 4), Moon's hora = Cancer (sign 3).
    First 15° of odd signs → Sun's hora (Leo).
    Last 15° of odd signs → Moon's hora (Cancer).
    First 15° of even signs → Moon's hora (Cancer).
    Last 15° of even signs → Sun's hora (Leo).
    """
    longitude = longitude % 360.0
    sign_index = int(longitude // 30)
    degrees_in_sign = longitude % 30.0

    is_odd_sign = (sign_index % 2) == 0  # 0-indexed: Aries=0 is odd sign

    if is_odd_sign:
        result_sign = 4 if degrees_in_sign < 15.0 else 3  # Leo or Cancer
    else:
        result_sign = 3 if degrees_in_sign < 15.0 else 4  # Cancer or Leo

    result_degrees = (degrees_in_sign % 15.0) * 2.0  # Scale to 30°
    return result_sign, result_degrees


# ---------------------------------------------------------------------------
# D3 — Drekkana
# ---------------------------------------------------------------------------

def _compute_drekkana(longitude: float) -> tuple[int, float]:
    """
    D3 (Drekkana) — Parashari method.

    1st decanate (0-10°): same sign
    2nd decanate (10-20°): 5th from sign
    3rd decanate (20-30°): 9th from sign
    """
    longitude = longitude % 360.0
    sign_index = int(longitude // 30)
    degrees_in_sign = longitude % 30.0

    if degrees_in_sign < 10.0:
        result_sign = sign_index
        result_degrees = degrees_in_sign * 3.0
    elif degrees_in_sign < 20.0:
        result_sign = (sign_index + 4) % 12
        result_degrees = (degrees_in_sign - 10.0) * 3.0
    else:
        result_sign = (sign_index + 8) % 12
        result_degrees = (degrees_in_sign - 20.0) * 3.0

    return result_sign, result_degrees


# ---------------------------------------------------------------------------
# D30 — Trimsamsa
# ---------------------------------------------------------------------------

# Trimsamsa rulers for odd signs: Mars, Saturn, Jupiter, Mercury, Venus
_TRIMSAMSA_ODD = [
    (5.0, 0),   # 0-5°: Mars (Aries=0)
    (5.0, 10),  # 5-10°: Saturn (Aquarius=10)
    (8.0, 8),   # 10-18°: Jupiter (Sagittarius=8)
    (7.0, 5),   # 18-25°: Mercury (Virgo=5)
    (5.0, 1),   # 25-30°: Venus (Taurus=1)
]

# Trimsamsa rulers for even signs: Venus, Mercury, Jupiter, Saturn, Mars
_TRIMSAMSA_EVEN = [
    (5.0, 1),   # 0-5°: Venus (Taurus=1)
    (7.0, 5),   # 5-12°: Mercury (Virgo=5)
    (8.0, 8),   # 12-20°: Jupiter (Sagittarius=8)
    (5.0, 10),  # 20-25°: Saturn (Aquarius=10)
    (5.0, 0),   # 25-30°: Mars (Aries=0)
]


def _compute_trimsamsa(longitude: float) -> tuple[int, float]:
    """D30 (Trimsamsa) — uses the classical Parashari method."""
    longitude = longitude % 360.0
    sign_index = int(longitude // 30)
    degrees_in_sign = longitude % 30.0

    is_odd_sign = (sign_index % 2) == 0
    table = _TRIMSAMSA_ODD if is_odd_sign else _TRIMSAMSA_EVEN

    accumulated = 0.0
    for span, result_sign in table:
        if degrees_in_sign < accumulated + span:
            degrees_into_part = degrees_in_sign - accumulated
            result_degrees = (degrees_into_part / span) * 30.0
            return result_sign, result_degrees
        accumulated += span

    # Fallback (should not reach here)
    return table[-1][1], 0.0


# ---------------------------------------------------------------------------
# Main computation function
# ---------------------------------------------------------------------------

def compute_varga(
    longitude: float,
    varga: VargaType,
) -> VargaPosition:
    """
    Compute a planet's position in a specific divisional chart.

    Args:
        longitude: Sidereal longitude [0, 360).
        varga: The divisional chart type.

    Returns:
        VargaPosition with the resulting sign and degrees.
    """
    if varga == VargaType.D1:
        sign_idx = int((longitude % 360.0) // 30)
        deg = longitude % 30.0
        return VargaPosition(
            varga=varga,
            sign_index=sign_idx,
            sign_name=SIGN_NAMES[sign_idx],
            degrees_in_sign=deg,
            source_longitude=longitude,
        )

    if varga == VargaType.D2:
        sign_idx, deg = _compute_hora(longitude)
    elif varga == VargaType.D3:
        sign_idx, deg = _compute_drekkana(longitude)
    elif varga == VargaType.D30:
        sign_idx, deg = _compute_trimsamsa(longitude)
    else:
        # All other standard vargas use equal division
        sign_idx, deg = _compute_equal_division_varga(longitude, int(varga))

    return VargaPosition(
        varga=varga,
        sign_index=sign_idx,
        sign_name=SIGN_NAMES[sign_idx],
        degrees_in_sign=deg,
        source_longitude=longitude,
    )


def compute_all_vargas(longitude: float) -> dict[VargaType, VargaPosition]:
    """Compute all standard varga positions for a given longitude."""
    return {v: compute_varga(longitude, v) for v in VargaType}
