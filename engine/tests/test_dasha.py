"""
Tests for the Vimshottari Dasha module.
"""

from datetime import datetime, timezone

import pytest

from astro_engine.dasha import (
    DASHA_LORD_ORDER,
    DASHA_YEARS,
    TOTAL_DASHA_YEARS,
    YEAR_IN_DAYS,
    DashaState,
    compute_vimshottari_dasha,
)
from astro_engine.nakshatra import NAKSHATRA_SPAN


class TestDashaConstants:
    """Verify fundamental dasha constants."""

    def test_total_years_120(self) -> None:
        """Total of all dasha periods should be 120 years."""
        assert sum(DASHA_YEARS.values()) == 120.0
        assert TOTAL_DASHA_YEARS == 120.0

    def test_nine_lords(self) -> None:
        assert len(DASHA_LORD_ORDER) == 9

    def test_lord_order_starts_with_ketu(self) -> None:
        assert DASHA_LORD_ORDER[0] == "Ketu"


class TestVimshottariDasha:
    """Tests for dasha computation."""

    @pytest.fixture()
    def sample_dasha(self) -> DashaState:
        """Compute dasha for Moon at 0° (Ashwini, lord = Ketu)."""
        birth = datetime(1990, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        return compute_vimshottari_dasha(0.0, birth)

    def test_first_lord_is_nakshatra_lord(self, sample_dasha: DashaState) -> None:
        """First Maha Dasha should be of the nakshatra lord."""
        assert sample_dasha.maha_dashas[0].lord == "Ketu"

    def test_nine_maha_dashas(self, sample_dasha: DashaState) -> None:
        """Should compute exactly 9 Maha Dashas."""
        assert len(sample_dasha.maha_dashas) == 9

    def test_maha_dasha_order(self, sample_dasha: DashaState) -> None:
        """Maha Dashas should follow the standard order from Ketu."""
        lords = [md.lord for md in sample_dasha.maha_dashas]
        assert lords == DASHA_LORD_ORDER

    def test_total_duration_120_years(self) -> None:
        """For Moon at 0° (start of nakshatra), balance = 1.0,
        so total should be very close to 120 years."""
        birth = datetime(1990, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        dasha = compute_vimshottari_dasha(0.0, birth)
        total_days = sum(md.duration_days for md in dasha.maha_dashas)
        total_years = total_days / YEAR_IN_DAYS
        assert abs(total_years - 120.0) < 0.01

    def test_balance_at_start_of_nakshatra(self) -> None:
        """At 0° (start of Ashwini), balance should be ~1.0."""
        birth = datetime(1990, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        dasha = compute_vimshottari_dasha(0.0, birth)
        assert abs(dasha.nakshatra_balance - 1.0) < 0.001

    def test_balance_at_mid_nakshatra(self) -> None:
        """At midpoint of Ashwini, balance should be ~0.5."""
        mid = NAKSHATRA_SPAN / 2.0
        birth = datetime(1990, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        dasha = compute_vimshottari_dasha(mid, birth)
        assert abs(dasha.nakshatra_balance - 0.5) < 0.01

    def test_maha_dashas_are_contiguous(self, sample_dasha: DashaState) -> None:
        """Each Maha Dasha should start exactly where the previous one ended."""
        for i in range(len(sample_dasha.maha_dashas) - 1):
            current_end = sample_dasha.maha_dashas[i].end
            next_start = sample_dasha.maha_dashas[i + 1].start
            diff = abs((current_end - next_start).total_seconds())
            assert diff < 1.0, f"Gap between MD {i} and {i+1}: {diff}s"

    def test_antar_dashas_present(self, sample_dasha: DashaState) -> None:
        """Each Maha Dasha should have 9 Antar Dashas."""
        for md in sample_dasha.maha_dashas:
            assert len(md.sub_periods) == 9

    def test_antar_dasha_starts_with_maha_lord(self, sample_dasha: DashaState) -> None:
        """First Antar Dasha should be of the Maha Dasha lord."""
        for md in sample_dasha.maha_dashas:
            assert md.sub_periods[0].lord == md.lord

    def test_antar_dasha_durations_sum_to_maha(self, sample_dasha: DashaState) -> None:
        """Antar dasha durations should sum to Maha dasha duration."""
        for md in sample_dasha.maha_dashas:
            antar_total = sum(ad.duration_days for ad in md.sub_periods)
            assert abs(antar_total - md.duration_days) < 0.01

    def test_get_active_maha(self, sample_dasha: DashaState) -> None:
        """Should find the active Maha Dasha at birth."""
        birth = datetime(1990, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        active = sample_dasha.get_active_maha(birth)
        assert active is not None
        assert active.lord == "Ketu"

    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            compute_vimshottari_dasha(0.0, datetime(1990, 1, 1))
