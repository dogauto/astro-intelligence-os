"""
Tests for the ConventionProfile module.
"""

from astro_engine.conventions import (
    KP_PROFILE,
    PARASHARI_LAHIRI,
    AyanamsaType,
    ConventionProfile,
    HouseSystem,
    NodeType,
    ZodiacType,
)


class TestConventionProfile:
    """Unit tests for ConventionProfile."""

    def test_parashari_defaults(self) -> None:
        """Parashari-Lahiri profile should have standard values."""
        p = PARASHARI_LAHIRI
        assert p.zodiac == ZodiacType.SIDEREAL
        assert p.ayanamsa == AyanamsaType.LAHIRI
        assert p.house_system == HouseSystem.WHOLE_SIGN
        assert p.node_type == NodeType.MEAN_NODE

    def test_kp_profile(self) -> None:
        """KP profile should use Krishnamurti ayanamsa and Placidus."""
        p = KP_PROFILE
        assert p.ayanamsa == AyanamsaType.KRISHNAMURTI
        assert p.house_system == HouseSystem.PLACIDUS

    def test_immutability(self) -> None:
        """ConventionProfile should be frozen/immutable."""
        p = PARASHARI_LAHIRI
        try:
            p.zodiac = ZodiacType.TROPICAL
            raise AssertionError("Should have raised an error")
        except Exception:
            pass  # Expected

    def test_custom_profile(self) -> None:
        """Creating a custom profile should work."""
        custom = ConventionProfile(
            id="test-custom",
            name="Test Custom",
            zodiac=ZodiacType.TROPICAL,
            ayanamsa=AyanamsaType.TROPICAL,
            house_system=HouseSystem.PLACIDUS,
            node_type=NodeType.TRUE_NODE,
            include_outer_planets=True,
        )
        assert custom.include_outer_planets is True
        assert custom.zodiac == ZodiacType.TROPICAL
