"""
Capability Registry
===================

Enforces the Calculation Completeness Matrix in code.
"""

from enum import Enum


class CalculationStatus(str, Enum):
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    PARTIAL = "PARTIAL"
    EXPERIMENTAL = "EXPERIMENTAL"
    VALIDATED = "VALIDATED"
    PRODUCTION = "PRODUCTION"


# Machine-enforceable representation of docs/CALCULATION_COMPLETENESS_MATRIX.md
CALCULATION_CAPABILITIES: dict[str, CalculationStatus] = {
    "planets": CalculationStatus.EXPERIMENTAL,
    "houses": CalculationStatus.EXPERIMENTAL,
    "nakshatra": CalculationStatus.EXPERIMENTAL,
    "vargas": CalculationStatus.EXPERIMENTAL,
    "dasha_maha_antar": CalculationStatus.EXPERIMENTAL,
    "dasha_pratyantar": CalculationStatus.PARTIAL,
    "shadbala": CalculationStatus.PARTIAL,
    "ashtakavarga": CalculationStatus.EXPERIMENTAL,
    "transit": CalculationStatus.EXPERIMENTAL,
}


class CapabilityError(Exception):
    """Raised when a method requires a capability that does not meet the minimum status."""
    pass


def validate_method_capabilities(method_maturity: str, required_calculations: list[str]) -> list[str]:
    """
    Validates that the required calculations are sufficient for the method's maturity.
    Returns a list of warnings, or raises CapabilityError if a PRODUCTION method relies on PARTIAL features.
    """
    warnings = []
    for calc in required_calculations:
        status = CALCULATION_CAPABILITIES.get(calc, CalculationStatus.NOT_IMPLEMENTED)
        
        if status == CalculationStatus.NOT_IMPLEMENTED:
            raise CapabilityError(f"Calculation '{calc}' is NOT_IMPLEMENTED.")
            
        if status == CalculationStatus.PARTIAL:
            if method_maturity == "production":
                raise CapabilityError(f"PRODUCTION method cannot depend on PARTIAL calculation '{calc}'.")
            else:
                warnings.append(f"Method depends on PARTIAL calculation '{calc}'. Expect incomplete data.")
                
    return warnings
