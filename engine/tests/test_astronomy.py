"""
Tests for the Astronomy module — Julian Day conversion and sign utilities.

These tests do NOT require Swiss Ephemeris and test pure utility functions.
"""

from datetime import UTC, datetime

import pytest

from astro_engine.astronomy import (
    SIGN_NAMES,
    datetime_to_jd,
    jd_to_datetime,
    longitude_to_sign,
)


class TestJulianDay:
    """Tests for Julian Day conversion."""

    def test_j2000_epoch(self) -> None:
        """J2000.0 = Jan 1.5, 2000 TT ≈ JD 2451545.0."""
        dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC)
        jd = datetime_to_jd(dt)
        assert abs(jd - 2451545.0) < 0.001

    def test_roundtrip(self) -> None:
        """Converting to JD and back should preserve the datetime."""
        original = datetime(1990, 7, 15, 10, 30, 0, tzinfo=UTC)
        jd = datetime_to_jd(original)
        recovered = jd_to_datetime(jd)
        # Allow 1 second tolerance due to floating point
        delta = abs((recovered - original).total_seconds())
        assert delta < 1.0

    def test_naive_datetime_rejected(self) -> None:
        """Naive datetimes must be rejected."""
        with pytest.raises(ValueError, match="timezone-aware"):
            datetime_to_jd(datetime(2000, 1, 1, 12, 0, 0))


class TestLongitudeToSign:
    """Tests for zodiac sign conversion."""

    def test_aries(self) -> None:
        idx, name, deg = longitude_to_sign(15.0)
        assert idx == 0
        assert name == "Aries"
        assert abs(deg - 15.0) < 0.001

    def test_pisces(self) -> None:
        idx, name, deg = longitude_to_sign(350.0)
        assert idx == 11
        assert name == "Pisces"
        assert abs(deg - 20.0) < 0.001

    def test_boundary_taurus(self) -> None:
        """Exactly 30° should be the start of Taurus."""
        idx, name, deg = longitude_to_sign(30.0)
        assert idx == 1
        assert name == "Taurus"
        assert abs(deg) < 0.001

    def test_all_signs_reachable(self) -> None:
        """Every sign should be reachable."""
        signs_seen: set[str] = set()
        for i in range(12):
            _, name, _ = longitude_to_sign(i * 30 + 15)
            signs_seen.add(name)
        assert signs_seen == set(SIGN_NAMES)
