"""
Convention Profile Module
=========================

A ConventionProfile explicitly specifies every astrological convention choice
used in a calculation. This prevents silent convention mixing and ensures
full reproducibility.

Every AstroState is tagged with the exact ConventionProfile that produced it.
"""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Ayanamsa choices
# ---------------------------------------------------------------------------

class AyanamsaType(enum.StrEnum):
    """Supported ayanamsa (precession correction) systems."""

    LAHIRI = "lahiri"
    RAMAN = "raman"
    KRISHNAMURTI = "krishnamurti"
    FAGAN_BRADLEY = "fagan_bradley"
    YUKTESHWAR = "yukteshwar"
    TRUE_CHITRA = "true_chitra"
    TROPICAL = "tropical"  # No precession correction (Western)


# ---------------------------------------------------------------------------
# House system choices
# ---------------------------------------------------------------------------

class HouseSystem(enum.StrEnum):
    """Supported house division systems."""

    WHOLE_SIGN = "whole_sign"
    EQUAL = "equal"
    PLACIDUS = "placidus"
    KOCH = "koch"
    SRIPATI = "sripati"
    CAMPANUS = "campanus"
    REGIOMONTANUS = "regiomontanus"
    PORPHYRY = "porphyry"


# ---------------------------------------------------------------------------
# Rahu / Ketu node type
# ---------------------------------------------------------------------------

class NodeType(enum.StrEnum):
    """True vs Mean lunar node calculation."""

    TRUE_NODE = "true_node"
    MEAN_NODE = "mean_node"


# ---------------------------------------------------------------------------
# Zodiac type
# ---------------------------------------------------------------------------

class ZodiacType(enum.StrEnum):
    """Tropical (Western) vs Sidereal (Vedic)."""

    SIDEREAL = "sidereal"
    TROPICAL = "tropical"


# ---------------------------------------------------------------------------
# Dasha system choices
# ---------------------------------------------------------------------------

class DashaSystem(enum.StrEnum):
    """Primary dasha timing system to use."""

    VIMSHOTTARI = "vimshottari"
    YOGINI = "yogini"
    ASHTOTTARI = "ashtottari"


# ---------------------------------------------------------------------------
# Convention Profile
# ---------------------------------------------------------------------------

class ConventionProfile(BaseModel):
    """
    Explicitly declares every convention choice for a calculation run.

    No calculation should proceed without knowing which ConventionProfile
    produced it. This is the foundation of reproducibility.
    """

    id: str = Field(
        ...,
        description="Unique identifier for this convention profile.",
    )
    name: str = Field(
        ...,
        description="Human-readable name (e.g. 'Parashari-Lahiri-WS').",
    )
    description: str = Field(
        default="",
        description="Optional description of this profile.",
    )

    # Core choices
    zodiac: ZodiacType = Field(
        default=ZodiacType.SIDEREAL,
        description="Sidereal or tropical zodiac.",
    )
    ayanamsa: AyanamsaType = Field(
        default=AyanamsaType.LAHIRI,
        description="Ayanamsa system for sidereal calculations.",
    )
    house_system: HouseSystem = Field(
        default=HouseSystem.WHOLE_SIGN,
        description="House division system.",
    )
    node_type: NodeType = Field(
        default=NodeType.MEAN_NODE,
        description="True or mean lunar nodes (Rahu/Ketu).",
    )
    primary_dasha: DashaSystem = Field(
        default=DashaSystem.VIMSHOTTARI,
        description="Primary dasha system.",
    )

    # Optional outer planets
    include_outer_planets: bool = Field(
        default=False,
        description="Whether to include Uranus, Neptune, Pluto.",
    )

    # Karakamsa / Chara Karaka scheme
    chara_karaka_scheme: int = Field(
        default=8,
        description="7 or 8 planet chara karaka scheme.",
    )

    @field_validator("chara_karaka_scheme")
    @classmethod
    def _validate_chara_karaka_scheme(cls, value: int) -> int:
        if value not in (7, 8):
            raise ValueError("chara_karaka_scheme must be 7 or 8.")
        return value

    # Birth-time rectification tolerance
    birth_time_precision_seconds: int | None = Field(
        default=None,
        description="Known precision of the birth time in seconds, if declared.",
    )

    model_config = ConfigDict(frozen=True)


# ---------------------------------------------------------------------------
# Pre-built profiles
# ---------------------------------------------------------------------------

PARASHARI_LAHIRI = ConventionProfile(
    id="parashari-lahiri-ws-v1",
    name="Parashari-Lahiri-WholeSgn",
    description="Standard North Indian Parashari tradition with Lahiri ayanamsa"
    " and whole-sign houses.",
    zodiac=ZodiacType.SIDEREAL,
    ayanamsa=AyanamsaType.LAHIRI,
    house_system=HouseSystem.WHOLE_SIGN,
    node_type=NodeType.MEAN_NODE,
    primary_dasha=DashaSystem.VIMSHOTTARI,
)

JAIMINI_LAHIRI_7 = ConventionProfile(
    id="jaimini-chara-karaka-7-sidereal-v1",
    name="Jaimini-Chara-Karaka-7-Lahiri",
    description="Seven-karaka Chara Karaka calculation using sidereal Lahiri longitudes.",
    zodiac=ZodiacType.SIDEREAL,
    ayanamsa=AyanamsaType.LAHIRI,
    house_system=HouseSystem.WHOLE_SIGN,
    node_type=NodeType.MEAN_NODE,
    primary_dasha=DashaSystem.VIMSHOTTARI,
    chara_karaka_scheme=7,
)

JAIMINI_LAHIRI_8 = ConventionProfile(
    id="jaimini-chara-karaka-8-sidereal-v1",
    name="Jaimini-Chara-Karaka-8-Lahiri",
    description=(
        "Eight-karaka Chara Karaka calculation with Rahu reversed "
        "from the end of the sign."
    ),
    zodiac=ZodiacType.SIDEREAL,
    ayanamsa=AyanamsaType.LAHIRI,
    house_system=HouseSystem.WHOLE_SIGN,
    node_type=NodeType.MEAN_NODE,
    primary_dasha=DashaSystem.VIMSHOTTARI,
    chara_karaka_scheme=8,
)

KP_PROFILE = ConventionProfile(
    id="kp-krishnamurti-placidus-v1",
    name="KP-Krishnamurti-Placidus",
    description="Krishnamurti Paddhati with KP ayanamsa and Placidus houses.",
    zodiac=ZodiacType.SIDEREAL,
    ayanamsa=AyanamsaType.KRISHNAMURTI,
    house_system=HouseSystem.PLACIDUS,
    node_type=NodeType.MEAN_NODE,
    primary_dasha=DashaSystem.VIMSHOTTARI,
)
