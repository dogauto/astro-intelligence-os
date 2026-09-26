"""
Tests for the Shadbala module.
"""

import pytest

from astro_engine.astronomy import Planet, PlanetPosition
from astro_engine.shadbala import (
    EXALTATION_POINTS,
    MINIMUM_SHADBALA_RUPAS,
    NAISARGIKA_BALA,
    compute_cheshta_bala,
    compute_dig_bala,
    compute_shadbala,
    compute_uchcha_bala,
)


def _make_position(
    planet: Planet,
    longitude: float,
    speed: float = 1.0,
) -> PlanetPosition:
    """Helper to create a PlanetPosition for testing."""
    sign_idx = int(longitude // 30) % 12
    return PlanetPosition(
        planet=planet,
        longitude=longitude,
        latitude=0.0,
        distance=1.0,
        speed_longitude=speed,
        is_retrograde=speed < 0,
        sign_index=sign_idx,
        sign_name="Test",
        degrees_in_sign=longitude % 30.0,
        is_sidereal=True,
        ayanamsa_applied=23.0,
    )


class TestUchchaBala:
    """Tests for exaltation strength."""

    def test_at_exaltation_maximum(self) -> None:
        """Planet at exact exaltation point should get 60 shashtiamsas."""
        exalt_lon, _ = EXALTATION_POINTS[Planet.SUN]
        result = compute_uchcha_bala(Planet.SUN, exalt_lon)
        assert abs(result - 60.0) < 0.01

    def test_at_debilitation_minimum(self) -> None:
        """Planet at debilitation should get ~0 shashtiamsas."""
        _, debil_lon = EXALTATION_POINTS[Planet.SUN]
        result = compute_uchcha_bala(Planet.SUN, debil_lon)
        assert result < 1.0

    def test_range(self) -> None:
        """Uchcha Bala should always be between 0 and 60."""
        for lon in range(0, 360, 10):
            result = compute_uchcha_bala(Planet.JUPITER, float(lon))
            assert 0.0 <= result <= 60.0


class TestDigBala:
    """Tests for directional strength."""

    def test_jupiter_strong_in_east(self) -> None:
        """Jupiter should be strong near ascendant (1st house)."""
        # Put Jupiter at the ascendant
        result = compute_dig_bala(Planet.JUPITER, 100.0, 100.0)
        # Should be near maximum (planet near midpoint of 1st house)
        assert result > 40.0

    def test_range(self) -> None:
        """Dig Bala should always be between 0 and 60."""
        for lon in range(0, 360, 30):
            result = compute_dig_bala(Planet.SUN, float(lon), 0.0)
            assert 0.0 <= result <= 60.0


class TestCheshtaBala:
    """Tests for motional strength."""

    def test_stationary_maximum(self) -> None:
        """Stationary planet should get maximum cheshta bala."""
        result = compute_cheshta_bala(Planet.MARS, 0.001)
        assert result == 60.0

    def test_retrograde_high(self) -> None:
        """Retrograde planet should get high cheshta bala."""
        result = compute_cheshta_bala(Planet.JUPITER, -0.1)
        assert result >= 40.0


class TestShadbala:
    """Integration tests for full Shadbala computation."""

    def test_produces_result(self) -> None:
        """Should produce a valid ShadbalResult."""
        pos = _make_position(Planet.SUN, 10.0)
        result = compute_shadbala(Planet.SUN, pos, 0.0)
        assert result.total_shadbala > 0
        assert result.total_rupas > 0

    def test_naisargika_sun_highest(self) -> None:
        """Sun should have the highest Naisargika Bala."""
        assert NAISARGIKA_BALA[Planet.SUN] == 60.0
        assert NAISARGIKA_BALA[Planet.SATURN] < NAISARGIKA_BALA[Planet.SUN]

    def test_all_components_non_negative(self) -> None:
        """All strength components should be >= 0."""
        pos = _make_position(Planet.MARS, 200.0, speed=-0.5)
        result = compute_shadbala(Planet.MARS, pos, 100.0)
        assert result.uchcha_bala >= 0
        assert result.dig_bala >= 0
        assert result.naisargika_bala >= 0
        assert result.cheshta_bala >= 0
