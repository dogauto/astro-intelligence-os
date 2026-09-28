"""Focused tests for the calculation-layer Chara Karaka foundation."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from astro_engine.astronomy import AstronomyEngine
from astro_engine.builder import AstroStateBuilder
from astro_engine.capabilities import CALCULATION_CAPABILITIES, CalculationStatus
from astro_engine.chara_karaka import (
    CALCULATION_VERSION,
    CONVENTION_ID,
    CONVENTION_ID_8,
    KARAKA_ROLES,
    PARTICIPATING_PLANETS,
    PARTICIPATING_PLANETS_8,
    RULE_ID,
    SOURCE_ID,
    CharaKarakaRole,
    CharaKarakaScheme,
    compute_chara_karakas,
    effective_chara_karaka_longitude,
)
from astro_engine.conventions import (
    JAIMINI_LAHIRI_7,
    JAIMINI_LAHIRI_8,
    PARASHARI_LAHIRI,
    AyanamsaType,
    ZodiacType,
)
from astro_engine.provenance import ProvenanceNodeType, ProvenanceRegistry
from astro_engine.state import (
    AstroState,
    BirthInput,
    ComputationProvenance,
    PlanetaryStateEntry,
)


def _state(degrees: dict[str, float], convention=JAIMINI_LAHIRI_7) -> AstroState:
    planets = [
        PlanetaryStateEntry(
            planet=planet,
            longitude=value,
            latitude=0.0,
            speed=0.0,
            is_retrograde=False,
            sign_index=0,
            sign_name="Aries",
            degrees_in_sign=value,
        )
        for planet, value in degrees.items()
    ]
    return AstroState(
        state_id="fixture-state",
        input=BirthInput(
            datetime_utc=datetime(2000, 1, 1, tzinfo=UTC),
            timezone_name="UTC",
            latitude=0.0,
            longitude=0.0,
        ),
        convention=convention,
        planets=planets,
        provenance=ComputationProvenance(
            engine_version="fixture",
            computed_at=datetime(2000, 1, 1, tzinfo=UTC),
            julian_day=2451544.5,
        ),
    )


def test_ordinary_fixture_assigns_roles_by_descending_intra_sign_degree() -> None:
    state = _state({
        "Sun": 10.0,
        "Moon": 20.0,
        "Mars": 5.0,
        "Mercury": 29.5,
        "Jupiter": 15.0,
        "Venus": 1.0,
        "Saturn": 25.0,
    })

    result = compute_chara_karakas(state, JAIMINI_LAHIRI_7)

    assert result.ranked_groups == (
        ("Mercury",), ("Saturn",), ("Moon",), ("Jupiter",),
        ("Sun",), ("Mars",), ("Venus",),
    )
    assert result.role_assignments == tuple(zip(
        KARAKA_ROLES,
        ("Mercury", "Saturn", "Moon", "Jupiter", "Sun", "Mars", "Venus"),
        strict=True,
    ))
    assert result.participating_planets == PARTICIPATING_PLANETS
    assert result.convention_id == CONVENTION_ID


def test_boundary_and_close_degree_values_are_not_rounded() -> None:
    state = _state({
        "Sun": 0.0,
        "Moon": 29.999999,
        "Mars": 10.0,
        "Mercury": 10.000001,
        "Jupiter": 20.0,
        "Venus": 5.0,
        "Saturn": 15.0,
    })

    result = compute_chara_karakas(state, JAIMINI_LAHIRI_7)

    assert result.ranked_groups[0] == ("Moon",)
    assert result.ranked_groups[1] == ("Jupiter",)
    assert result.ranked_groups[-1] == ("Sun",)
    assert dict(result.normalized_degree_values)["Mercury"] == 10.000001


def test_tie_is_explicit_and_does_not_assign_arbitrary_roles() -> None:
    state = _state({
        "Sun": 10.0,
        "Moon": 20.0,
        "Mars": 5.0,
        "Mercury": 20.0,
        "Jupiter": 15.0,
        "Venus": 1.0,
        "Saturn": 25.0,
    })

    result = compute_chara_karakas(state, JAIMINI_LAHIRI_7)

    assert ("Moon", "Mercury") in result.ranked_groups
    assert result.ambiguities == ("Equal Chara Karaka degree for: Moon, Mercury",)
    assert ("Atmakaraka", "Saturn") in result.role_assignments
    assert ("Amatyakaraka", None) in result.role_assignments
    assert ("Bhratrikaraka", None) in result.role_assignments


def test_invalid_or_missing_positions_are_rejected() -> None:
    missing = _state({"Sun": 1.0})
    with pytest.raises(ValueError, match="missing participating planets"):
        compute_chara_karakas(missing, JAIMINI_LAHIRI_7)

    invalid = _state({
        "Sun": 30.0,
        "Moon": 20.0,
        "Mars": 5.0,
        "Mercury": 29.0,
        "Jupiter": 15.0,
        "Venus": 1.0,
        "Saturn": 25.0,
    })
    with pytest.raises(ValueError, match="Invalid degrees_in_sign"):
        compute_chara_karakas(invalid, JAIMINI_LAHIRI_7)


def test_convention_is_explicitly_required() -> None:
    state = _state({planet: float(index) for index, planet in enumerate(PARTICIPATING_PLANETS)})
    wrong_scheme = JAIMINI_LAHIRI_7.model_copy(update={"chara_karaka_scheme": 8})
    wrong_zodiac = JAIMINI_LAHIRI_7.model_copy(update={"zodiac": ZodiacType.TROPICAL})
    wrong_ayanamsa = JAIMINI_LAHIRI_7.model_copy(update={"ayanamsa": AyanamsaType.RAMAN})

    with pytest.raises(ValueError, match="7-karaka"):
        compute_chara_karakas(state, wrong_scheme)
    with pytest.raises(ValueError, match="sidereal"):
        compute_chara_karakas(state, wrong_zodiac)
    with pytest.raises(ValueError, match="Lahiri"):
        compute_chara_karakas(state, wrong_ayanamsa)

    with pytest.raises(ValueError, match="Unsupported"):
        compute_chara_karakas(state, PARASHARI_LAHIRI)


def test_capability_is_registered_as_experimental() -> None:
    assert CALCULATION_CAPABILITIES["chara_karaka"] == CalculationStatus.EXPERIMENTAL


def test_provenance_is_source_backed_and_reaches_astrostate() -> None:
    registry = ProvenanceRegistry()
    birth = BirthInput(
        datetime_utc=datetime(1990, 1, 1, tzinfo=UTC),
        timezone_name="UTC",
        latitude=28.6,
        longitude=77.2,
    )
    state = AstroStateBuilder(AstronomyEngine()).build(
        birth,
        JAIMINI_LAHIRI_7,
        provenance_registry=registry,
    )
    result = compute_chara_karakas(state, JAIMINI_LAHIRI_7, registry)

    assert result.provenance_node_id is not None
    calculation = registry.get_node(result.provenance_node_id)
    assert calculation.node_type == ProvenanceNodeType.CALCULATION
    assert calculation.source_id == SOURCE_ID
    assert calculation.convention_id == CONVENTION_ID
    assert calculation.source_rule_ids == [RULE_ID]
    rule = registry.get_node(calculation.parent_ids[2])
    assert rule.node_type == ProvenanceNodeType.RULE
    assert rule.source_id == SOURCE_ID
    assert rule.convention_id == CONVENTION_ID
    assert state.provenance.astrostate_node_id in calculation.parent_ids
    registry.validate_node(calculation)
    registry.validate_node(rule)


def test_repeatability_has_identical_substantive_output() -> None:
    state = _state({
        "Sun": 10.0,
        "Moon": 20.0,
        "Mars": 5.0,
        "Mercury": 29.5,
        "Jupiter": 15.0,
        "Venus": 1.0,
        "Saturn": 25.0,
    })

    first = compute_chara_karakas(state, JAIMINI_LAHIRI_7)
    second = compute_chara_karakas(state, JAIMINI_LAHIRI_7)

    assert first == second
    assert first.calculation_version == CALCULATION_VERSION


def test_eight_planet_scheme_reverses_rahu_and_excludes_ketu() -> None:
    state = _state({
        "Sun": 24.0,
        "Moon": 23.0,
        "Mars": 22.0,
        "Mercury": 21.0,
        "Jupiter": 20.0,
        "Venus": 19.0,
        "Saturn": 18.0,
        "Rahu": 14.55,
        "Ketu": 29.0,
    }, JAIMINI_LAHIRI_8)

    result = compute_chara_karakas(state, JAIMINI_LAHIRI_8)

    assert result.scheme is CharaKarakaScheme.EIGHT_PLANET
    assert result.participating_planets == PARTICIPATING_PLANETS_8
    assert result.entries[0].planet == "Sun"
    rahu = next(entry for entry in result.entries if entry.planet == "Rahu")
    assert rahu.raw_longitude_within_sign == 14.55
    assert rahu.effective_chara_karaka_longitude == 15.45
    assert "Ketu" not in result.participating_planets
    assert result.entries[-1].role is CharaKarakaRole.DARAKARAKA
    assert result.convention_id == CONVENTION_ID_8


def test_seven_planet_roles_have_no_putrakaraka() -> None:
    state = _state({
        "Sun": 29.0,
        "Moon": 28.0,
        "Mars": 27.0,
        "Mercury": 26.0,
        "Jupiter": 25.0,
        "Venus": 24.0,
        "Saturn": 23.0,
    })

    result = compute_chara_karakas(state, JAIMINI_LAHIRI_7)

    assert [role for role, _ in result.role_assignments] == list(KARAKA_ROLES)
    assert "Putrakaraka" not in result.role_assignments
    assert result.atmakaraka == "Sun"
    assert result.amatyakaraka == "Moon"
    assert result.karaka_lagna == 0
    assert result.entries[-1].role is CharaKarakaRole.DARAKARAKA


def test_degree_minute_and_second_ordering_uses_decimal_arcseconds() -> None:
    state = _state({
        "Sun": 10 + 59 / 60 + 59 / 3600,
        "Moon": 10 + 59 / 60 + 58 / 3600,
        "Mars": 10 + 58 / 60 + 59 / 3600,
        "Mercury": 10.0,
        "Jupiter": 9.0,
        "Venus": 8.0,
        "Saturn": 7.0,
    })

    result = compute_chara_karakas(state, JAIMINI_LAHIRI_7)

    assert [entry.planet for entry in result.entries[:3]] == ["Sun", "Moon", "Mars"]
    assert result.entries[0].effective_arcseconds > result.entries[1].effective_arcseconds


def test_second_level_ordering_preserves_degree_minute_second_components() -> None:
    state = _state({
        "Sun": 24 + 53 / 60 + 50 / 3600,
        "Moon": 24 + 53 / 60 + 49 / 3600,
        "Mars": 24 + 54 / 60,
        "Mercury": 24 + 53 / 60 + 59 / 3600,
        "Jupiter": 10.0,
        "Venus": 9.0,
        "Saturn": 8.0,
    })

    result = compute_chara_karakas(state, JAIMINI_LAHIRI_7)

    assert [entry.planet for entry in result.entries[:4]] == [
        "Mars", "Mercury", "Sun", "Moon",
    ]
    assert result.entries[1].effective_arcseconds == pytest.approx(Decimal("89639"))
    assert result.entries[2].effective_arcseconds == pytest.approx(Decimal("89630"))
    assert result.entries[3].effective_arcseconds == pytest.approx(Decimal("89629"))


def test_rahu_transformation_preserves_exact_arcseconds() -> None:
    state = _state({
        "Sun": 24.0,
        "Moon": 23.0,
        "Mars": 22.0,
        "Mercury": 21.0,
        "Jupiter": 20.0,
        "Venus": 19.0,
        "Saturn": 18.0,
        "Rahu": 14 + 33 / 60,
    }, JAIMINI_LAHIRI_8)

    result = compute_chara_karakas(state, JAIMINI_LAHIRI_8)
    rahu = next(entry for entry in result.entries if entry.planet == "Rahu")

    assert rahu.raw_arcseconds == Decimal("52380")
    assert rahu.effective_arcseconds == Decimal("55620")
    assert rahu.raw_longitude_within_sign == 14 + 33 / 60
    assert rahu.effective_chara_karaka_longitude == pytest.approx(15 + 27 / 60)


def test_exact_supported_precision_equality_abstains_explicitly() -> None:
    state = _state({
        "Sun": 10 + 1 / 60 + 2 / 3600,
        "Moon": 10 + 1 / 60 + 2 / 3600,
        "Mars": 9.0,
        "Mercury": 8.0,
        "Jupiter": 7.0,
        "Venus": 6.0,
        "Saturn": 5.0,
    })

    result = compute_chara_karakas(state, JAIMINI_LAHIRI_7)

    assert result.resolved is False
    assert result.abstained is True
    assert result.atmakaraka is None
    assert result.role_assignments[0] == ("Atmakaraka", None)


def test_sri_krishna_source_fixture_uses_rahu_effective_longitude() -> None:
    # Source note:
    # Rath's printed Sri Krishna chart labels Rahu as MK and Venus as PiK,
    # although the explicitly stated numerical longitudes and stated descending-
    # ranking rule produce Rahu 15°27' > Venus 15°24'. The implementation
    # follows the numerical rule and does not introduce a source-specific exception.
    state = _state({
        "Sun": 18 + 10 / 60,
        "Saturn": 17 + 3 / 60,
        "Moon": 16 + 28 / 60,
        "Venus": 15 + 24 / 60,
        "Mars": 3 + 13 / 60,
        "Mercury": 1 + 51 / 60,
        "Jupiter": 1 + 22 / 60,
        "Rahu": 14 + 33 / 60,
    }, JAIMINI_LAHIRI_8)

    result = compute_chara_karakas(state, JAIMINI_LAHIRI_8)

    assert [entry.planet for entry in result.entries] == [
        "Sun", "Saturn", "Moon", "Rahu", "Venus", "Mars", "Mercury", "Jupiter",
    ]
    assert result.role_assignments == (
        ("Atmakaraka", "Sun"),
        ("Amatyakaraka", "Saturn"),
        ("Bhratrikaraka", "Moon"),
        ("Matrikaraka", "Rahu"),
        ("Pitrakaraka", "Venus"),
        ("Putrakaraka", "Mars"),
        ("Gnatikaraka", "Mercury"),
        ("Darakaraka", "Jupiter"),
    )
    assert result.atmakaraka == "Sun"
    assert result.amatyakaraka == "Saturn"
    assert result.entries[3].effective_chara_karaka_longitude == 15 + 27 / 60


def test_k_n_rao_source_values_preserve_second_level_order() -> None:
    known = {
        "Sun": 24 + 53 / 60 + 50 / 3600,
        "Jupiter": 24 + 42 / 60 + 59 / 3600,
        "Mars": 24 + 2 / 60 + 17 / 3600,
        "Rahu": 11 + 40 / 60,
    }

    ordinary_order = sorted(
        (planet for planet in known if planet != "Rahu"),
        key=lambda planet: known[planet],
        reverse=True,
    )

    assert ordinary_order == ["Sun", "Jupiter", "Mars"]
    assert effective_chara_karaka_longitude(
        "Rahu", known["Rahu"], CharaKarakaScheme.EIGHT_PLANET
    ) == pytest.approx(18 + 20 / 60)
