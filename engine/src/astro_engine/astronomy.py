"""
Astronomy Module
================

Deterministic astronomical calculations backed by the Swiss Ephemeris.

This module provides:
- Planetary position computation (longitude, latitude, distance, speed)
- Retrograde/direct state detection
- Ayanamsa application
- Julian Day conversion
- Sunrise/sunset computation

ALL outputs are purely mathematical. No astrological interpretation happens here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import IntEnum

import swisseph as swe

from astro_engine.conventions import AyanamsaType, ConventionProfile, NodeType

# ---------------------------------------------------------------------------
# Planet identifiers — maps to Swiss Ephemeris constants
# ---------------------------------------------------------------------------

class Planet(IntEnum):
    """Planets and points supported by the engine."""

    SUN = swe.SUN
    MOON = swe.MOON
    MERCURY = swe.MERCURY
    VENUS = swe.VENUS
    MARS = swe.MARS
    JUPITER = swe.JUPITER
    SATURN = swe.SATURN
    RAHU = swe.MEAN_NODE  # Will be overridden for true node
    KETU = -1  # Computed as 180° from Rahu
    URANUS = swe.URANUS
    NEPTUNE = swe.NEPTUNE
    PLUTO = swe.PLUTO


# Map of friendly names
PLANET_NAMES: dict[Planet, str] = {
    Planet.SUN: "Sun",
    Planet.MOON: "Moon",
    Planet.MERCURY: "Mercury",
    Planet.VENUS: "Venus",
    Planet.MARS: "Mars",
    Planet.JUPITER: "Jupiter",
    Planet.SATURN: "Saturn",
    Planet.RAHU: "Rahu",
    Planet.KETU: "Ketu",
    Planet.URANUS: "Uranus",
    Planet.NEPTUNE: "Neptune",
    Planet.PLUTO: "Pluto",
}


# ---------------------------------------------------------------------------
# Ayanamsa mapping to Swiss Ephemeris codes
# ---------------------------------------------------------------------------

_AYANAMSA_MAP: dict[AyanamsaType, int] = {
    AyanamsaType.LAHIRI: swe.SIDM_LAHIRI,
    AyanamsaType.RAMAN: swe.SIDM_RAMAN,
    AyanamsaType.KRISHNAMURTI: swe.SIDM_KRISHNAMURTI,
    AyanamsaType.FAGAN_BRADLEY: swe.SIDM_FAGAN_BRADLEY,
    AyanamsaType.YUKTESHWAR: swe.SIDM_YUKTESHWAR,
    AyanamsaType.TRUE_CHITRA: swe.SIDM_TRUE_CITRA,
}


# ---------------------------------------------------------------------------
# Data classes for computed results
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlanetPosition:
    """Immutable computed position for a single planet."""

    planet: Planet
    longitude: float  # Ecliptic longitude in degrees [0, 360)
    latitude: float  # Ecliptic latitude in degrees
    distance: float  # Distance in AU
    speed_longitude: float  # Daily speed in degrees/day
    is_retrograde: bool  # True if speed < 0
    sign_index: int  # 0-based zodiac sign (0=Aries, 11=Pisces)
    sign_name: str  # e.g. "Aries"
    degrees_in_sign: float  # Degrees within the sign [0, 30)

    # Provenance
    is_sidereal: bool
    ayanamsa_applied: float  # The ayanamsa value subtracted (0 if tropical)


@dataclass(frozen=True)
class SunriseSunsetResult:
    """Sunrise and sunset times for a given date and location."""

    sunrise_utc: datetime
    sunset_utc: datetime
    sunrise_jd: float
    sunset_jd: float


# ---------------------------------------------------------------------------
# Zodiac sign utilities
# ---------------------------------------------------------------------------

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def longitude_to_sign(longitude: float) -> tuple[int, str, float]:
    """Convert ecliptic longitude to (sign_index, sign_name, degrees_in_sign)."""
    sign_index = int(longitude // 30) % 12
    degrees_in_sign = longitude % 30
    return sign_index, SIGN_NAMES[sign_index], degrees_in_sign


# ---------------------------------------------------------------------------
# Julian Day conversion
# ---------------------------------------------------------------------------

def datetime_to_jd(dt: datetime) -> float:
    """
    Convert a timezone-aware datetime to Julian Day (UT).

    The datetime MUST be timezone-aware. If it represents a local birth time,
    convert it to UTC before calling this function.
    """
    if dt.tzinfo is None:
        raise ValueError(
            "datetime must be timezone-aware. "
            "Naive datetimes are rejected to prevent silent timezone errors."
        )
    utc_dt = dt.astimezone(UTC)
    hour_decimal = (
        utc_dt.hour
        + utc_dt.minute / 60.0
        + utc_dt.second / 3600.0
        + utc_dt.microsecond / 3_600_000_000.0
    )
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour_decimal)
    return float(jd)


def jd_to_datetime(jd: float) -> datetime:
    """Convert Julian Day to UTC datetime."""
    year, month, day, hour_decimal = swe.revjul(jd)
    hours = int(hour_decimal)
    remainder = (hour_decimal - hours) * 60
    minutes = int(remainder)
    seconds = (remainder - minutes) * 60
    whole_seconds = int(seconds)
    microseconds = int((seconds - whole_seconds) * 1_000_000)
    return datetime(year, month, day, hours, minutes, whole_seconds, microseconds, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Core calculation engine
# ---------------------------------------------------------------------------

class AstronomyEngine:
    """
    Deterministic astronomical calculation engine backed by Swiss Ephemeris.

    All methods require an explicit ConventionProfile to ensure reproducibility.
    """

    def __init__(self, ephemeris_path: str | None = None) -> None:
        """
        Initialize the engine.

        Args:
            ephemeris_path: Path to Swiss Ephemeris data files.
                            If None, uses the built-in Moshier ephemeris
                            (lower precision but no external files needed).
        """
        if ephemeris_path:
            swe.set_ephe_path(ephemeris_path)
        self._ephemeris_path = ephemeris_path

    def _get_swe_flags(self, convention: ConventionProfile) -> int:
        """Build Swiss Ephemeris calculation flags from convention."""
        flags = swe.FLG_SWIEPH if self._ephemeris_path else swe.FLG_MOSEPH
        flags |= swe.FLG_SPEED  # Always compute speed for retrograde detection

        if convention.zodiac.value == "sidereal":
            flags |= swe.FLG_SIDEREAL
            ayan_code = _AYANAMSA_MAP.get(convention.ayanamsa)
            if ayan_code is not None:
                swe.set_sid_mode(ayan_code)

        return int(flags)

    def get_ayanamsa(self, jd: float, convention: ConventionProfile) -> float:
        """
        Get the ayanamsa value for a given Julian Day and convention.

        Returns 0.0 for tropical zodiac.
        """
        if convention.zodiac.value == "tropical":
            return 0.0

        ayan_code = _AYANAMSA_MAP.get(convention.ayanamsa)
        if ayan_code is None:
            raise ValueError(f"Unsupported ayanamsa: {convention.ayanamsa}")

        swe.set_sid_mode(ayan_code)
        return float(swe.get_ayanamsa_ut(jd))

    def compute_planet(
        self,
        jd: float,
        planet: Planet,
        convention: ConventionProfile,
    ) -> PlanetPosition:
        """
        Compute the position of a single planet at the given Julian Day.

        For Ketu, computes as Rahu + 180°.
        """
        flags = self._get_swe_flags(convention)
        ayanamsa_value = self.get_ayanamsa(jd, convention)
        is_sidereal = convention.zodiac.value == "sidereal"

        # Handle Ketu as 180° from Rahu
        if planet == Planet.KETU:
            rahu_pos = self.compute_planet(jd, Planet.RAHU, convention)
            ketu_lon = (rahu_pos.longitude + 180.0) % 360.0
            sign_idx, sign_name, deg_in_sign = longitude_to_sign(ketu_lon)
            return PlanetPosition(
                planet=Planet.KETU,
                longitude=ketu_lon,
                latitude=-rahu_pos.latitude,
                distance=rahu_pos.distance,
                speed_longitude=-rahu_pos.speed_longitude,
                is_retrograde=True,  # Ketu is always retrograde
                sign_index=sign_idx,
                sign_name=sign_name,
                degrees_in_sign=deg_in_sign,
                is_sidereal=is_sidereal,
                ayanamsa_applied=ayanamsa_value,
            )

        # Handle Rahu node type
        swe_planet_id = int(planet)
        if planet == Planet.RAHU:
            swe_planet_id = (
                swe.TRUE_NODE
                if convention.node_type == NodeType.TRUE_NODE
                else swe.MEAN_NODE
            )

        # Swiss Ephemeris calculation
        result, _ret_flags = swe.calc_ut(jd, swe_planet_id, flags)
        longitude = result[0]
        latitude = result[1]
        distance = result[2]
        speed_lon = result[3]

        sign_idx, sign_name, deg_in_sign = longitude_to_sign(longitude)

        return PlanetPosition(
            planet=planet,
            longitude=longitude,
            latitude=latitude,
            distance=distance,
            speed_longitude=speed_lon,
            is_retrograde=speed_lon < 0,
            sign_index=sign_idx,
            sign_name=sign_name,
            degrees_in_sign=deg_in_sign,
            is_sidereal=is_sidereal,
            ayanamsa_applied=ayanamsa_value,
        )

    def compute_all_planets(
        self,
        jd: float,
        convention: ConventionProfile,
    ) -> dict[Planet, PlanetPosition]:
        """Compute positions for all standard planets (Sun through Ketu)."""
        standard_planets = [
            Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS,
            Planet.MARS, Planet.JUPITER, Planet.SATURN,
            Planet.RAHU, Planet.KETU,
        ]

        if convention.include_outer_planets:
            standard_planets.extend([Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO])

        return {p: self.compute_planet(jd, p, convention) for p in standard_planets}

    def compute_ascendant(
        self,
        jd: float,
        latitude: float,
        longitude: float,
        convention: ConventionProfile,
    ) -> float:
        """
        Compute the Ascendant (Lagna) longitude.

        Args:
            jd: Julian Day (UT).
            latitude: Geographic latitude in degrees.
            longitude: Geographic longitude in degrees.
            convention: Convention profile.

        Returns:
            Ascendant longitude in degrees [0, 360).
        """
        flags = self._get_swe_flags(convention)

        # swe.houses_ex returns (cusps_tuple, ascmc_tuple)
        cusps, ascmc = swe.houses_ex(
            jd,
            latitude,
            longitude,
            b"W",  # Whole sign by default; adjusted below
            flags,
        )

        # ascmc[0] is the Ascendant
        return float(ascmc[0])

    def compute_houses(
        self,
        jd: float,
        latitude: float,
        longitude: float,
        convention: ConventionProfile,
    ) -> list[float]:
        """
        Compute house cusps.

        Returns a list of 12 house cusp longitudes in degrees.
        """
        flags = self._get_swe_flags(convention)

        # Map house system to Swiss Ephemeris code
        house_code_map = {
            "whole_sign": b"W",
            "equal": b"E",
            "placidus": b"P",
            "koch": b"K",
            "sripati": b"B",  # Closest match
            "campanus": b"C",
            "regiomontanus": b"R",
            "porphyry": b"O",
        }
        house_code = house_code_map.get(convention.house_system.value, b"W")

        cusps, _ = swe.houses_ex(jd, latitude, longitude, house_code, flags)
        # cusps is a 12-element tuple, 0-indexed
        return [float(cusps[i]) for i in range(12)]

    def compute_sunrise_sunset(
        self,
        jd: float,
        latitude: float,
        longitude: float,
        altitude: float = 0.0,
    ) -> SunriseSunsetResult:
        """
        Compute sunrise and sunset for the given JD and location.

        Args:
            jd: Julian Day at approximately midnight (UT) of the desired date.
            latitude: Geographic latitude.
            longitude: Geographic longitude.
            altitude: Altitude in meters.
        """
        # Sunrise
        sunrise_jd = swe.rise_trans(
            jd, swe.SUN, "", longitude, latitude, altitude,
            0.0,  # atmospheric pressure
            0.0,  # atmospheric temperature
            swe.CALC_RISE | swe.BIT_DISC_CENTER,
        )

        # Sunset
        sunset_jd = swe.rise_trans(
            jd, swe.SUN, "", longitude, latitude, altitude,
            0.0,
            0.0,
            swe.CALC_SET | swe.BIT_DISC_CENTER,
        )

        # rise_trans returns a tuple: (flag, jd_result)
        sr_jd = sunrise_jd[1][0] if isinstance(sunrise_jd[1], (list, tuple)) else sunrise_jd[1]
        ss_jd = sunset_jd[1][0] if isinstance(sunset_jd[1], (list, tuple)) else sunset_jd[1]

        return SunriseSunsetResult(
            sunrise_utc=jd_to_datetime(sr_jd),
            sunset_utc=jd_to_datetime(ss_jd),
            sunrise_jd=sr_jd,
            sunset_jd=ss_jd,
        )
