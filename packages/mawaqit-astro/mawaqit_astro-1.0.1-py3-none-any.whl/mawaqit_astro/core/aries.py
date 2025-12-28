from ..types import TimeMeasures, NutationResult, AriesResult
from .utils import norm360, cosd

def compute_aries(time: TimeMeasures, nutation: NutationResult) -> AriesResult:
    t = time.julianCenturies

    # Greenwich Mean Sidereal Time (IAU 1982)
    gmst = 280.46061837 + 360.98564736629 * (time.julianDay - 2451545.0) \
           + 0.000387933 * t**2 - (t**3 / 38710000.0)

    gmst = norm360(gmst)

    # Equation of Equinoxes
    eq_eq = nutation.nutationLongitude * cosd(nutation.trueObliquity)

    gast = norm360(gmst + eq_eq)

    return AriesResult(
        greenwichMeanSiderealTime=gmst,
        greenwichApparentSiderealTime=gast,
        equationOfEquinoxes=eq_eq
    )

