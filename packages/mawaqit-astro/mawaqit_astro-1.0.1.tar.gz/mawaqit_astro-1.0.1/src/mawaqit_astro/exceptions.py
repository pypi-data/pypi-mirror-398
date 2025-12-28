class MawaqitError(Exception):
    """Base exception for Mawaqit"""
    pass

class LocationError(MawaqitError):
    """Raised for invalid geographic coordinates"""
    pass

class CalculationError(MawaqitError):
    """Raised when prayer times cannot be calculated (e.g., polar regions)"""
    pass

class ValidationError(MawaqitError):
    """Raised for invalid input parameters (months, days, angles)"""
    pass

