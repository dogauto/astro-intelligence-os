from astro_engine.capabilities import CapabilityError, validate_method_capabilities
import pytest

def test_experimental_method_allows_partial_with_warning():
    warnings = validate_method_capabilities("experimental", ["shadbala"])
    assert len(warnings) == 1
    assert "PARTIAL calculation 'shadbala'" in warnings[0]

def test_production_method_rejects_partial():
    with pytest.raises(CapabilityError, match="PRODUCTION method cannot depend on PARTIAL"):
        validate_method_capabilities("production", ["shadbala"])

def test_method_rejects_not_implemented():
    with pytest.raises(CapabilityError, match="NOT_IMPLEMENTED"):
        validate_method_capabilities("experimental", ["yogas"])
