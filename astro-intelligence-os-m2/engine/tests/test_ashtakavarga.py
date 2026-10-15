"""
Tests for the Ashtakavarga module.
"""

from astro_engine.ashtakavarga import compute_ashtakavarga


class TestAshtakavarga:
    """Tests for Ashtakavarga computation."""

    def _sample_planet_signs(self) -> dict[str, int]:
        """Create a sample set of planet sign placements."""
        return {
            "Sun": 0,       # Aries
            "Moon": 3,      # Cancer
            "Mars": 9,      # Capricorn
            "Mercury": 1,   # Taurus
            "Jupiter": 7,   # Scorpio
            "Venus": 11,    # Pisces
            "Saturn": 4,    # Leo
        }

    def test_bav_has_7_planets(self) -> None:
        """BAV should have entries for all 7 planets."""
        result = compute_ashtakavarga(self._sample_planet_signs(), 0)
        assert len(result.bav) == 7

    def test_bav_each_has_12_signs(self) -> None:
        """Each BAV table should have 12 entries (one per sign)."""
        result = compute_ashtakavarga(self._sample_planet_signs(), 0)
        for planet, bindus in result.bav.items():
            assert len(bindus) == 12, f"{planet} BAV has {len(bindus)} entries"

    def test_sav_has_12_signs(self) -> None:
        """SAV should have 12 entries."""
        result = compute_ashtakavarga(self._sample_planet_signs(), 0)
        assert len(result.sav) == 12

    def test_sav_is_sum_of_bav(self) -> None:
        """SAV[i] should equal sum of all BAV[planet][i]."""
        result = compute_ashtakavarga(self._sample_planet_signs(), 0)
        for i in range(12):
            bav_sum = sum(result.bav[p][i] for p in result.bav)
            assert result.sav[i] == bav_sum

    def test_total_bindus_337(self) -> None:
        """Total SAV bindus should be 337 (standard Ashtakavarga invariant)."""
        result = compute_ashtakavarga(self._sample_planet_signs(), 0)
        assert result.total_bindus == 337, f"Total bindus: {result.total_bindus}"

    def test_bindus_non_negative(self) -> None:
        """All bindu values should be non-negative."""
        result = compute_ashtakavarga(self._sample_planet_signs(), 0)
        for planet, bindus in result.bav.items():
            for i, b in enumerate(bindus):
                assert b >= 0, f"{planet} sign {i} has negative bindus: {b}"

    def test_max_bav_bindu_8(self) -> None:
        """Maximum BAV bindu for any sign from any planet should be ≤ 8."""
        result = compute_ashtakavarga(self._sample_planet_signs(), 0)
        for planet, bindus in result.bav.items():
            for i, b in enumerate(bindus):
                assert b <= 8, f"{planet} sign {i} has {b} bindus (max is 8)"
