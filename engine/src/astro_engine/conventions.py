"""
Convention Profile Module
=========================

A ConventionProfile explicitly specifies every astrological convention choice
used in a calculation. This prevents silent convention mixing and ensures
full reproducibility.

Every AstroState is tagged with the exact ConventionProfile that produced it.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Ayanamsa choices
# ---------------------------------------------------------------------------

class AyanamsaType(str, Enum):
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

class HouseSystem(str, Enum):
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

class NodeType(str, Enum):
    """True vs Mean lunar node calculation."""

    TRUE_NODE = "true_node"
    MEAN_NODE = "mean_node"


# ---------------------------------------------------------------------------
# Zodiac type
# ---------------------------------------------------------------------------

class ZodiacType(str, Enum):
    """Tropical (Western) vs Sidereal (Vedic)."""

    SIDEREAL = "sidereal"
    TROPICAL = "tropical"


# ---------------------------------------------------------------------------
# Dasha system choices
# ---------------------------------------------------------------------------

class DashaSystem(str, Enum):
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

    # Birth-time rectification tolerance
    birth_time_precision_seconds: Optional[int] = Field(
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
    description="Standard North Indian Parashari tradition with Lahiri ayanamsa and whole-sign houses.",
    zodiac=ZodiacType.SIDEREAL,
    ayanamsa=AyanamsaType.LAHIRI,
    house_system=HouseSystem.WHOLE_SIGN,
    node_type=NodeType.MEAN_NODE,
    primary_dasha=DashaSystem.VIMSHOTTARI,
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
