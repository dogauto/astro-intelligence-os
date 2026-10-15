"""
Tests for the Varga (Divisional Charts) module.
"""

import pytest

from astro_engine.vargas import VargaType, compute_all_vargas, compute_varga


class TestD1Rasi:
    """D1 chart is simply the rasi chart."""

    def test_aries(self) -> None:
        result = compute_varga(15.0, VargaType.D1)
        assert result.sign_name == "Aries"
        assert abs(result.degrees_in_sign - 15.0) < 0.001

    def test_scorpio(self) -> None:
        result = compute_varga(225.0, VargaType.D1)
        assert result.sign_name == "Scorpio"


class TestD9Navamsa:
    """D9 Navamsa — the most important divisional chart."""

    def test_aries_first_navamsa(self) -> None:
        """0°–3°20' Aries → Aries navamsa."""
        result = compute_varga(1.0, VargaType.D9)
        assert result.sign_name == "Aries"

    def test_aries_second_navamsa(self) -> None:
        """3°20'–6°40' Aries → Taurus navamsa."""
        result = compute_varga(4.0, VargaType.D9)
        assert result.sign_name == "Taurus"

    def test_aries_last_navamsa(self) -> None:
        """26°40'–30° Aries → Sagittarius navamsa."""
        result = compute_varga(28.0, VargaType.D9)
        assert result.sign_name == "Sagittarius"

    def test_taurus_first_navamsa(self) -> None:
        """0°–3°20' Taurus → Capricorn navamsa."""
        result = compute_varga(31.0, VargaType.D9)
        assert result.sign_name == "Capricorn"

    def test_cancer_first_navamsa(self) -> None:
        """Cancer is the 4th sign (index 3), first navamsa should be Cancer."""
        result = compute_varga(91.0, VargaType.D9)
        # (3*9 + 0) % 12 = 27 % 12 = 3 = Cancer
        assert result.sign_name == "Cancer"


class TestD2Hora:
    """D2 Hora chart."""

    def test_odd_sign_first_half_leo(self) -> None:
        """First 15° of Aries (odd sign) → Leo."""
        result = compute_varga(10.0, VargaType.D2)
        assert result.sign_name == "Leo"

    def test_odd_sign_second_half_cancer(self) -> None:
        """Last 15° of Aries (odd sign) → Cancer."""
        result = compute_varga(20.0, VargaType.D2)
        assert result.sign_name == "Cancer"

    def test_even_sign_first_half_cancer(self) -> None:
        """First 15° of Taurus (even sign) → Cancer."""
        result = compute_varga(35.0, VargaType.D2)
        assert result.sign_name == "Cancer"


class TestD3Drekkana:
    """D3 Drekkana chart."""

    def test_first_decanate_same_sign(self) -> None:
        """0°–10° of Aries → Aries."""
        result = compute_varga(5.0, VargaType.D3)
        assert result.sign_name == "Aries"

    def test_second_decanate_5th_from(self) -> None:
        """10°–20° of Aries → Leo (5th from Aries)."""
        result = compute_varga(15.0, VargaType.D3)
        assert result.sign_name == "Leo"

    def test_third_decanate_9th_from(self) -> None:
        """20°–30° of Aries → Sagittarius (9th from Aries)."""
        result = compute_varga(25.0, VargaType.D3)
        assert result.sign_name == "Sagittarius"


class TestComputeAllVargas:
    """Test computing all vargas at once."""

    def test_returns_all_types(self) -> None:
        result = compute_all_vargas(100.0)
        assert len(result) == len(VargaType)
        for vt in VargaType:
            assert vt in result

    def test_d1_matches_direct(self) -> None:
        all_v = compute_all_vargas(100.0)
        direct = compute_varga(100.0, VargaType.D1)
        assert all_v[VargaType.D1].sign_name == direct.sign_name

    def test_immutability(self) -> None:
        result = compute_varga(100.0, VargaType.D9)
        with pytest.raises(AttributeError):
            result.sign_index = 99  # type: ignore[misc]
