import math
from ..types import NutationResult
from .utils import sind, cosd

def compute_nutation(te: float) -> NutationResult:
    # L: Mean longitude of the moon
    L = 218.3165 + 481267.8813 * te
    # LP: Mean longitude of the sun
    LP = 280.4666 + 36000.7698 * te
    # M: Mean anomaly of the moon
    M = 134.9634 + 477198.8675 * te
    # MP: Mean anomaly of the sun
    MP = 357.5291 + 35999.0503 * te
    # F: Mean argument of latitude of the moon
    F = 93.2721 + 483202.0175 * te
    # O: Mean longitude of the ascending node of the moon
    O = 125.0445 - 1934.1363 * te

    # Values from Meeus Chap 22 Table 22.A (Partial simplified)
    delta_psi = (-17.1996 - 0.01742 * te) * sind(O) \
              + (-1.3187 - 0.00016 * te) * sind(2 * (L - F + O)) \
              + (-0.2274 - 0.00002 * te) * sind(2 * (L + O)) \
              + (0.2062 + 0.00002 * te) * sind(2 * O) \
              + (0.1426 - 0.00007 * te) * sind(MP)

    delta_eps = (9.2025 + 0.00089 * te) * cosd(O) \
              + (0.5736 - 0.00031 * te) * cosd(2 * (L - F + O)) \
              + (0.0977 - 0.00005 * te) * cosd(2 * (L + O)) \
              + (-0.0895 + 0.00005 * te) * cosd(2 * O) \
              + (0.0054 - 0.00001 * te) * cosd(MP)

    delta_psi /= 3600 # to degrees
    delta_eps /= 3600 # to degrees

    # Mean obliquity of the ecliptic
    eps0 = 23.43929111 - 1.30125 / 100 * te - 1.64 / 1000000 * te**2 + 5.03 / 100000000 * te**3
    eps = eps0 + delta_eps

    return NutationResult(
        nutationLongitude=delta_psi,
        nutationObliquity=delta_eps,
        meanObliquity=eps0,
        trueObliquity=eps
    )

