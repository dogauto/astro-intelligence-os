"""
Integration test: Build a full AstroState for a known chart and verify.

This test requires pyswisseph to be installed.
"""

from datetime import UTC, datetime

import pytest

from astro_engine.astronomy import AstronomyEngine
from astro_engine.builder import AstroStateBuilder
from astro_engine.conventions import PARASHARI_LAHIRI
from astro_engine.state import BirthInput

# A well-known reference chart:
# Mahatma Gandhi — Oct 2, 1869, 7:11:40 AM LMT, Porbandar, India
# (Approximate — used for structural validation, not precision claims)
GANDHI_INPUT = BirthInput(
    datetime_utc=datetime(1869, 10, 2, 1, 37, 0, tzinfo=UTC),
    datetime_local=datetime(1869, 10, 2, 7, 11, 40),
    timezone_name="Asia/Kolkata",
    latitude=21.6417,
    longitude=69.6293,
    location_name="Porbandar, Gujarat, India",
    source="Historical records (approximate)",
    rodden_rating="B",
)


class TestAstroStateBuilder:
    """Integration tests for building a full AstroState."""

    @pytest.fixture()
    def builder(self) -> AstroStateBuilder:
        engine = AstronomyEngine()
        return AstroStateBuilder(engine)

    def test_build_produces_valid_state(self, builder: AstroStateBuilder) -> None:
        """Building an AstroState should produce a valid object."""
        state = builder.build(GANDHI_INPUT, PARASHARI_LAHIRI)

        # Should have 9 standard planets (Sun–Ketu)
        assert len(state.planets) == 9
        planet_names = {p.planet for p in state.planets}
        assert "Sun" in planet_names
        assert "Moon" in planet_names
        assert "Rahu" in planet_names
        assert "Ketu" in planet_names

    def test_rahu_ketu_opposite(self, builder: AstroStateBuilder) -> None:
        """Rahu and Ketu must be approximately 180° apart."""
        state = builder.build(GANDHI_INPUT, PARASHARI_LAHIRI)

        rahu = next(p for p in state.planets if p.planet == "Rahu")
        ketu = next(p for p in state.planets if p.planet == "Ketu")

        diff = abs(rahu.longitude - ketu.longitude)
        # Should be very close to 180°
        assert abs(diff - 180.0) < 0.5, f"Rahu-Ketu diff was {diff}°"

    def test_longitudes_in_range(self, builder: AstroStateBuilder) -> None:
        """All longitudes should be in [0, 360)."""
        state = builder.build(GANDHI_INPUT, PARASHARI_LAHIRI)
        for p in state.planets:
            assert 0.0 <= p.longitude < 360.0, f"{p.planet} longitude out of range: {p.longitude}"

    def test_ascendant_in_range(self, builder: AstroStateBuilder) -> None:
        """Ascendant should be in [0, 360)."""
        state = builder.build(GANDHI_INPUT, PARASHARI_LAHIRI)
        assert state.chart is not None
        assert 0.0 <= state.chart.ascendant_longitude < 360.0

    def test_12_house_cusps(self, builder: AstroStateBuilder) -> None:
        """Should compute exactly 12 house cusps."""
        state = builder.build(GANDHI_INPUT, PARASHARI_LAHIRI)
        assert state.chart is not None
        assert len(state.chart.house_cusps) == 12

    def test_convention_attached(self, builder: AstroStateBuilder) -> None:
        """AstroState must carry its convention."""
        state = builder.build(GANDHI_INPUT, PARASHARI_LAHIRI)
        assert state.convention.id == PARASHARI_LAHIRI.id

    def test_provenance_attached(self, builder: AstroStateBuilder) -> None:
        """AstroState must carry provenance."""
        state = builder.build(GANDHI_INPUT, PARASHARI_LAHIRI)
        assert state.provenance.engine_version == "0.1.0"
        assert state.provenance.julian_day > 0

    def test_nakshatra_computed_for_moon(self, builder: AstroStateBuilder) -> None:
        """Moon should have nakshatra information."""
        state = builder.build(GANDHI_INPUT, PARASHARI_LAHIRI)
        moon = next(p for p in state.planets if p.planet == "Moon")
        assert moon.nakshatra_name is not None
        assert moon.pada is not None
        assert 1 <= moon.pada <= 4

    def test_serialization_roundtrip(self, builder: AstroStateBuilder) -> None:
        """AstroState should survive JSON serialization."""
        state = builder.build(GANDHI_INPUT, PARASHARI_LAHIRI)
        json_str = state.model_dump_json()
        recovered = state.model_validate_json(json_str)
        assert recovered.state_id == state.state_id
        assert len(recovered.planets) == len(state.planets)
