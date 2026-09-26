"""
Tests for the Nakshatra computation module.

These are deterministic unit tests — no external dependencies needed.
"""

import pytest

from astro_engine.nakshatra import (
    NAKSHATRA_NAMES,
    NAKSHATRA_SPAN,
    NakshatraResult,
    compute_nakshatra,
)


class TestNakshatraComputation:
    """Unit tests for compute_nakshatra."""

    def test_ashwini_start(self) -> None:
        """0° Aries = Ashwini, Pada 1."""
        result = compute_nakshatra(0.0)
        assert result.nakshatra_index == 0
        assert result.nakshatra_name == "Ashwini"
        assert result.pada == 1

    def test_ashwini_pada_2(self) -> None:
        """3°20' + ε should be Ashwini Pada 2."""
        result = compute_nakshatra(3.4)  # Slightly past 3°20'
        assert result.nakshatra_name == "Ashwini"
        assert result.pada == 2

    def test_bharani(self) -> None:
        """13°20' = start of Bharani."""
        result = compute_nakshatra(NAKSHATRA_SPAN)
        assert result.nakshatra_index == 1
        assert result.nakshatra_name == "Bharani"
        assert result.pada == 1

    def test_revati_end(self) -> None:
        """Just before 360° = Revati, Pada 4."""
        result = compute_nakshatra(359.99)
        assert result.nakshatra_index == 26
        assert result.nakshatra_name == "Revati"
        assert result.pada == 4

    def test_wrap_around(self) -> None:
        """360° wraps to 0° = Ashwini."""
        result = compute_nakshatra(360.0)
        assert result.nakshatra_name == "Ashwini"
        assert result.pada == 1

    def test_mid_zodiac(self) -> None:
        """180° should be in Chitra."""
        result = compute_nakshatra(180.0)
        # 180 / 13.333... = 13.5 → nakshatra index 13
        assert result.nakshatra_index == 13
        assert result.nakshatra_name == "Chitra"

    def test_all_27_nakshatras_reachable(self) -> None:
        """Every nakshatra should be reachable."""
        seen: set[str] = set()
        for i in range(27):
            lon = i * NAKSHATRA_SPAN + 1.0  # 1° into each nakshatra
            result = compute_nakshatra(lon)
            seen.add(result.nakshatra_name)
        assert seen == set(NAKSHATRA_NAMES)

    def test_all_padas_reachable(self) -> None:
        """All 4 padas should be reachable within a single nakshatra."""
        padas: set[int] = set()
        for p in range(4):
            lon = p * (NAKSHATRA_SPAN / 4) + 0.5
            result = compute_nakshatra(lon)
            padas.add(result.pada)
        assert padas == {1, 2, 3, 4}

    def test_negative_longitude(self) -> None:
        """Negative longitudes should wrap correctly."""
        result = compute_nakshatra(-10.0)
        expected = compute_nakshatra(350.0)
        assert result.nakshatra_name == expected.nakshatra_name
        assert result.pada == expected.pada

    def test_result_is_frozen(self) -> None:
        """NakshatraResult should be immutable."""
        result = compute_nakshatra(100.0)
        with pytest.raises(AttributeError):
            result.pada = 99  # type: ignore[misc]

    def test_lord_assignment(self) -> None:
        """Ashwini lord should be Ketu."""
        result = compute_nakshatra(0.0)
        assert result.nakshatra_lord == "Ketu"

    def test_pushya(self) -> None:
        """Pushya starts at 93°20' (nakshatra index 7)."""
        result = compute_nakshatra(94.0)
        assert result.nakshatra_name == "Pushya"
        assert result.nakshatra_lord == "Saturn"
