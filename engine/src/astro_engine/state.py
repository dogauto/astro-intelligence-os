"""
AstroState Module
=================

The canonical, immutable representation of all computed astrological data
for a given moment, location, and ConventionProfile.

AstroState is PURELY CALCULATED. It contains no methodology inferences,
no LLM outputs, and no subjective interpretations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from astro_engine.conventions import ConventionProfile

# ---------------------------------------------------------------------------
# Input metadata
# ---------------------------------------------------------------------------

class BirthInput(BaseModel):
    """The raw input data for a chart calculation."""

    datetime_utc: datetime = Field(
        ..., description="Birth date/time in UTC."
    )
    datetime_local: datetime | None = Field(
        default=None, description="Birth date/time in local timezone (for display)."
    )
    timezone_name: str = Field(
        ..., description="IANA timezone identifier (e.g. 'Asia/Kolkata')."
    )
    latitude: float = Field(
        ..., description="Geographic latitude in degrees."
    )
    longitude: float = Field(
        ..., description="Geographic longitude in degrees."
    )
    altitude_m: float = Field(
        default=0.0, description="Altitude in meters."
    )
    location_name: str | None = Field(
        default=None, description="Human-readable location name."
    )
    source: str | None = Field(
        default=None, description="Source of the birth data (e.g. 'birth certificate')."
    )
    rodden_rating: str | None = Field(
        default=None, description="Rodden accuracy rating (AA, A, B, C, DD, X, XX)."
    )

    model_config = ConfigDict(frozen=True)


# ---------------------------------------------------------------------------
# Planetary position in state
# ---------------------------------------------------------------------------

class PlanetaryStateEntry(BaseModel):
    """Single planet's computed state within AstroState."""

    planet: str
    longitude: float
    latitude: float
    speed: float
    is_retrograde: bool
    sign_index: int
    sign_name: str
    degrees_in_sign: float
    nakshatra_name: str | None = None
    nakshatra_index: int | None = None
    pada: int | None = None
    nakshatra_lord: str | None = None

    model_config = ConfigDict(frozen=True)


# ---------------------------------------------------------------------------
# Chart section
# ---------------------------------------------------------------------------

class ChartState(BaseModel):
    """House cusps and ascendant."""

    ascendant_longitude: float
    ascendant_sign_index: int
    ascendant_sign_name: str
    ascendant_nakshatra: str | None = None
    house_cusps: list[float] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

class ComputationProvenance(BaseModel):
    """Tracks what produced this AstroState."""

    engine_version: str
    computed_at: datetime
    ephemeris_type: str = Field(
        default="moshier", description="'moshier' or 'swiss' or path."
    )
    ayanamsa_value: float = Field(
        default=0.0, description="Exact ayanamsa offset applied."
    )
    julian_day: float = Field(
        ..., description="Julian Day used for computation."
    )
    warnings: list[str] = Field(default_factory=list)
    provenance_node_id: str | None = Field(
        default=None, description="ID of the AstronomyComputationNode in the registry."
    )
    astrostate_node_id: str | None = Field(
        default=None, description="ID of the AstroStateNode in the registry."
    )

    model_config = ConfigDict(frozen=True)


# ---------------------------------------------------------------------------
# AstroState — the canonical object
# ---------------------------------------------------------------------------

class AstroState(BaseModel):
    """
    Canonical, immutable, serializable representation of all computed
    astrological data for a moment/location/convention.

    This is the SINGLE SOURCE OF TRUTH that all Methods consume.
    It must never contain LLM outputs or methodology inferences.
    """

    # Identity
    state_id: str = Field(
        ..., description="Unique identifier for this state computation."
    )

    # Input
    input: BirthInput

    # Convention that produced this state
    convention: ConventionProfile

    # Computed sections
    planets: list[PlanetaryStateEntry] = Field(default_factory=list)
    chart: ChartState | None = None

    # Placeholder sections — will be populated as the engine grows
    # Each is typed as Optional[Any] initially to allow incremental development
    vargas: Any | None = Field(default=None, description="Divisional charts (D1-D60+).")
    dashas: Any | None = Field(default=None, description="Dasha periods.")
    strengths: Any | None = Field(default=None, description="Shadbala, Bhava Bala, etc.")
    ashtakavarga: Any | None = Field(default=None, description="Ashtakavarga tables.")
    yogas: Any | None = Field(default=None, description="Detected yogas.")
    doshas: Any | None = Field(default=None, description="Detected doshas.")
    arudhas: Any | None = Field(default=None, description="Arudha Lagnas.")
    karakas: Any | None = Field(default=None, description="Chara Karakas.")
    sphutas: Any | None = Field(default=None, description="Special sphutas.")
    upagrahas: Any | None = Field(default=None, description="Sub-planets.")
    special_lagnas: Any | None = Field(default=None, description="Hora Lagna, Ghati Lagna, etc.")
    transit: Any | None = Field(default=None, description="Current gochara.")
    panchanga: Any | None = Field(default=None, description="Tithi, Yoga, Karana, etc.")
    muhurta: Any | None = Field(default=None, description="Muhurta data.")
    matching: Any | None = Field(default=None, description="Compatibility/matching data.")

    # Provenance
    provenance: ComputationProvenance

    model_config = ConfigDict(frozen=True)
