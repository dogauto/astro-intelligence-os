"""Deterministic calculation-layer Chara Karaka foundation.

This module consumes planetary positions already present in :class:`AstroState`.
It contains no method, prediction, timing, or career interpretation logic.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from astro_engine.conventions import AyanamsaType, ConventionProfile, ZodiacType
from astro_engine.provenance import (
    CalculationNode,
    ConventionProfileNode,
    ProvenanceRegistry,
    RuleNode,
)

if TYPE_CHECKING:
    from astro_engine.state import AstroState


SOURCE_ID = "jaimini-course-upadesa-sutra-rath-sagittarius-2007"
CONVENTION_ID = "jaimini-chara-karaka-7-sidereal-v1"
CONVENTION_ID_8 = "jaimini-chara-karaka-8-sidereal-v1"
RULE_ID = "jaimini-chara-karaka-ranking-v2"
CALCULATION_VERSION = "2.0.0"
SOURCE_LOCATION = (
    "A Course on Jaimini Maharshi's Upadesa Sutra, Volume I, "
    "Sanjay Rath, Sagittarius Publications, pp. 288-303, Sutra 1.1.10 onward"
)
PARTICIPATING_PLANETS = (
    "Sun",
    "Moon",
    "Mars",
    "Mercury",
    "Jupiter",
    "Venus",
    "Saturn",
)
PARTICIPATING_PLANETS_8 = PARTICIPATING_PLANETS + ("Rahu",)


class CharaKarakaScheme(enum.StrEnum):
    """Explicit planet-count choice for Chara Karaka calculation."""

    SEVEN_PLANET = "seven_planet"
    EIGHT_PLANET = "eight_planet"


class CharaKarakaRole(enum.StrEnum):
    """Roles assigned in descending effective longitude order."""

    ATMAKARAKA = "Atmakaraka"
    AMATYAKARAKA = "Amatyakaraka"
    BHRATRAKARAKA = "Bhratrikaraka"
    MATRUKARAKA = "Matrikaraka"
    PITRAKARAKA = "Pitrakaraka"
    PUTRAKARAKA = "Putrakaraka"
    GNATIKARAKA = "Gnatikaraka"
    DARAKARAKA = "Darakaraka"


KARAKA_ROLES_7 = (
    CharaKarakaRole.ATMAKARAKA,
    CharaKarakaRole.AMATYAKARAKA,
    CharaKarakaRole.BHRATRAKARAKA,
    CharaKarakaRole.MATRUKARAKA,
    CharaKarakaRole.PITRAKARAKA,
    CharaKarakaRole.GNATIKARAKA,
    CharaKarakaRole.DARAKARAKA,
)
KARAKA_ROLES_8 = (
    CharaKarakaRole.ATMAKARAKA,
    CharaKarakaRole.AMATYAKARAKA,
    CharaKarakaRole.BHRATRAKARAKA,
    CharaKarakaRole.MATRUKARAKA,
    CharaKarakaRole.PITRAKARAKA,
    CharaKarakaRole.PUTRAKARAKA,
    CharaKarakaRole.GNATIKARAKA,
    CharaKarakaRole.DARAKARAKA,
)
# Backward-compatible alias for the approved seven-planet foundation.
KARAKA_ROLES = tuple(role.value for role in KARAKA_ROLES_7)


@dataclass(frozen=True)
class CharaKarakaEntry:
    """One ranked planet and its assigned role, if unambiguous."""

    planet: str
    role: CharaKarakaRole | None
    rank: int
    raw_longitude_within_sign: float
    effective_chara_karaka_longitude: float
    raw_arcseconds: Decimal
    effective_arcseconds: Decimal
    scheme: CharaKarakaScheme


@dataclass(frozen=True)
class CharaKarakaResult:
    """Structured Chara Karaka calculation output."""

    calculation_version: str
    convention_id: str
    input_state_id: str
    scheme: CharaKarakaScheme
    participating_planets: tuple[str, ...]
    entries: tuple[CharaKarakaEntry, ...]
    atmakaraka: str | None
    amatyakaraka: str | None
    karaka_lagna: int | None
    normalized_degree_values: tuple[tuple[str, float], ...]
    raw_degree_values: tuple[tuple[str, float], ...]
    ranked_groups: tuple[tuple[str, ...], ...]
    role_assignments: tuple[tuple[str, str | None], ...]
    warnings: tuple[str, ...]
    ambiguities: tuple[str, ...]
    resolved: bool
    abstained: bool
    provenance_node_id: str | None


def compute_chara_karakas(
    state: AstroState,
    convention: ConventionProfile,
    provenance_registry: ProvenanceRegistry | None = None,
) -> CharaKarakaResult:
    """Compute Chara Karakas from existing AstroState planetary positions."""
    scheme = _validate_convention(convention)
    participating = (
        PARTICIPATING_PLANETS
        if scheme is CharaKarakaScheme.SEVEN_PLANET
        else PARTICIPATING_PLANETS_8
    )
    positions = {entry.planet: entry for entry in state.planets}
    missing = [planet for planet in participating if planet not in positions]
    if missing:
        raise ValueError(
            f"AstroState is missing participating planets: {', '.join(missing)}"
        )

    values = tuple(
        _build_value(planet, positions[planet].degrees_in_sign, scheme)
        for planet in participating
    )
    sorted_values = sorted(values, key=lambda item: item[4], reverse=True)
    ranked_groups = _group_equal_values(sorted_values)
    ambiguities = tuple(
        f"Equal Chara Karaka degree for: {', '.join(group)}"
        for group in ranked_groups
        if len(group) > 1
    )
    role_values = _roles_for_scheme(scheme)
    role_assignments = _assign_roles(ranked_groups, role_values)
    role_by_planet = {
        planet: CharaKarakaRole(role)
        for role, planet in role_assignments
        if planet is not None
    }
    entries = tuple(
        CharaKarakaEntry(
            planet=planet,
            role=role_by_planet.get(planet),
            rank=index,
            raw_longitude_within_sign=raw_float,
            effective_chara_karaka_longitude=effective_float,
            raw_arcseconds=raw_arcseconds,
            effective_arcseconds=effective_arcseconds,
            scheme=scheme,
        )
        for index, (planet, raw_float, effective_float, raw_arcseconds, effective_arcseconds)
        in enumerate(sorted_values, start=1)
    )
    atmakaraka = _planet_for_role(role_assignments, CharaKarakaRole.ATMAKARAKA)
    amatyakaraka = _planet_for_role(role_assignments, CharaKarakaRole.AMATYAKARAKA)
    ak_entry = next((entry for entry in entries if entry.planet == atmakaraka), None)
    karaka_lagna = (
        positions[atmakaraka].sign_index
        if ak_entry is not None and atmakaraka is not None
        else None
    )
    provenance_node_id = _register_provenance(
        state,
        convention,
        scheme,
        provenance_registry,
    )
    return CharaKarakaResult(
        calculation_version=CALCULATION_VERSION,
        convention_id=convention.id,
        input_state_id=state.state_id,
        scheme=scheme,
        participating_planets=participating,
        entries=entries,
        atmakaraka=atmakaraka,
        amatyakaraka=amatyakaraka,
        karaka_lagna=karaka_lagna,
        normalized_degree_values=tuple(
            (planet, effective_float)
            for planet, _, effective_float, _, _ in values
        ),
        raw_degree_values=tuple((planet, raw_float) for planet, raw_float, *_ in values),
        ranked_groups=ranked_groups,
        role_assignments=role_assignments,
        warnings=(
            ("Exact Chara Karaka equality remains unresolved; role assignments are abstained.",)
            if ambiguities
            else ()
        ),
        ambiguities=ambiguities,
        resolved=not ambiguities,
        abstained=bool(ambiguities),
        provenance_node_id=provenance_node_id,
    )


def _validate_convention(convention: ConventionProfile) -> CharaKarakaScheme:
    if convention.id == CONVENTION_ID and convention.chara_karaka_scheme != 7:
        raise ValueError("The v1 Chara Karaka calculation requires the 7-karaka scheme.")
    if convention.id == CONVENTION_ID_8 and convention.chara_karaka_scheme != 8:
        raise ValueError("The v1 Chara Karaka calculation requires the 8-karaka scheme.")
    if convention.id not in {CONVENTION_ID, CONVENTION_ID_8}:
        raise ValueError(
            f"Unsupported Chara Karaka convention: {convention.id}; "
            f"expected {CONVENTION_ID} or {CONVENTION_ID_8}."
        )
    if convention.zodiac != ZodiacType.SIDEREAL:
        raise ValueError("Chara Karaka calculation requires sidereal longitudes.")
    if convention.ayanamsa != AyanamsaType.LAHIRI:
        raise ValueError("Chara Karaka calculation requires Lahiri ayanamsa.")
    return (
        CharaKarakaScheme.SEVEN_PLANET
        if convention.chara_karaka_scheme == 7
        else CharaKarakaScheme.EIGHT_PLANET
    )


def _build_value(
    planet: str,
    raw_value: float,
    scheme: CharaKarakaScheme,
) -> tuple[str, float, float, Decimal, Decimal]:
    raw_arcseconds = _to_arcseconds(planet, raw_value)
    effective_arcseconds = (
        Decimal(30 * 60 * 60) - raw_arcseconds
        if planet == "Rahu" and scheme is CharaKarakaScheme.EIGHT_PLANET
        else raw_arcseconds
    )
    return (
        planet,
        raw_value,
        float(effective_arcseconds / Decimal(3600)),
        raw_arcseconds,
        effective_arcseconds,
    )


def effective_chara_karaka_longitude(
    planet: str,
    degrees_in_sign: float,
    scheme: CharaKarakaScheme,
) -> float:
    """Return effective ranking longitude without changing astronomical input."""
    return _build_value(planet, degrees_in_sign, scheme)[2]


def _to_arcseconds(planet: str, value: float) -> Decimal:
    if not math.isfinite(value) or not 0.0 <= value < 30.0:
        raise ValueError(
            f"Invalid degrees_in_sign for {planet}: expected 0 <= value < 30, got {value}."
        )
    return Decimal(str(value)) * Decimal(3600)


def _roles_for_scheme(scheme: CharaKarakaScheme) -> tuple[CharaKarakaRole, ...]:
    return KARAKA_ROLES_7 if scheme is CharaKarakaScheme.SEVEN_PLANET else KARAKA_ROLES_8


def _group_equal_values(
    sorted_values: list[tuple[str, float, float, Decimal, Decimal]],
) -> tuple[tuple[str, ...], ...]:
    groups: list[list[str]] = []
    previous_value: Decimal | None = None
    for planet, _, _, _, effective_arcseconds in sorted_values:
        if previous_value is None or effective_arcseconds != previous_value:
            groups.append([planet])
            previous_value = effective_arcseconds
        else:
            groups[-1].append(planet)
    return tuple(tuple(group) for group in groups)


def _assign_roles(
    ranked_groups: tuple[tuple[str, ...], ...],
    roles: tuple[CharaKarakaRole, ...],
) -> tuple[tuple[str, str | None], ...]:
    assignments: list[tuple[str, str | None]] = []
    role_index = 0
    for group in ranked_groups:
        if len(group) == 1:
            assignments.append((roles[role_index].value, group[0]))
        else:
            for _ in group:
                assignments.append((roles[role_index].value, None))
                role_index += 1
            continue
        role_index += 1
    return tuple(assignments)


def _planet_for_role(
    assignments: tuple[tuple[str, str | None], ...],
    role: CharaKarakaRole,
) -> str | None:
    return next(
        (planet for assigned_role, planet in assignments if assigned_role == role.value),
        None,
    )


def _register_provenance(
    state: AstroState,
    convention: ConventionProfile,
    scheme: CharaKarakaScheme,
    registry: ProvenanceRegistry | None,
) -> str | None:
    if registry is None:
        return None
    state_node_id = state.provenance.astrostate_node_id
    if state_node_id is None:
        raise ValueError("AstroState provenance must include an AstroState node.")

    convention_node = ConventionProfileNode(
        version=CALCULATION_VERSION,
        convention_id=convention.id,
        ayanamsa=convention.ayanamsa.value,
        house_system=convention.house_system.value,
        chara_karaka_scheme=convention.chara_karaka_scheme,
        rahu_rule=(
            "reverse from end of sign for effective Chara Karaka longitude"
            if scheme is CharaKarakaScheme.EIGHT_PLANET
            else "excluded from seven-planet scheme"
        ),
        ketu_excluded=True,
        precision="degrees, minutes, seconds; Decimal arcsecond ordering",
    )
    convention_node.content_hash = convention_node.compute_hash(
        convention_node._content_dict()
    )
    registry.add_node(convention_node)

    rule_node = RuleNode(
        version=CALCULATION_VERSION,
        parent_ids=[state_node_id, convention_node.node_id],
        rule_id=RULE_ID,
        logic_description=(
            "Rank eligible planets by descending longitude within sign; "
            "reverse Rahu from 30 degrees in the eight-planet scheme; "
            "leave exact ties unresolved."
        ),
        source_id=SOURCE_ID,
        source_location=SOURCE_LOCATION,
        convention_id=convention.id,
    )
    rule_node.content_hash = rule_node.compute_hash(rule_node._content_dict())
    registry.add_node(rule_node)

    calculation_node = CalculationNode(
        version=CALCULATION_VERSION,
        parent_ids=[state_node_id, convention_node.node_id, rule_node.node_id],
        calculation_name="chara_karaka",
        convention_id=convention.id,
        input_state_id=state.state_id,
        source_rule_ids=[RULE_ID],
        source_id=SOURCE_ID,
        source_location=SOURCE_LOCATION,
        chara_karaka_scheme=convention.chara_karaka_scheme,
        rahu_rule=(
            "reverse from end of sign" if scheme is CharaKarakaScheme.EIGHT_PLANET
            else "excluded"
        ),
        ketu_excluded=True,
        precision="Decimal arcseconds derived from AstroState degrees_in_sign",
    )
    calculation_node.content_hash = calculation_node.compute_hash(
        calculation_node._content_dict()
    )
    registry.add_node(calculation_node)
    return calculation_node.node_id
