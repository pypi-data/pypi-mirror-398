import math
from ..types import TimeMeasures, NutationResult, MoonResult, MoonPhaseResult
from .utils import sind, cosd, asind, acosd, norm360

def compute_moon(time: TimeMeasures, nutation: NutationResult, gast: float) -> MoonResult:
    te = time.julianEphemerisCenturies

    # Mean longitude
    l_prime = 218.3164477 + 481267.88123385 * te
    # Mean elongation
    d = 297.8501921 + 445267.1114034 * te
    # Sun mean anomaly
    m = 357.5291092 + 35999.0502909 * te
    # Moon mean anomaly
    m_prime = 134.9633964 + 477198.8675055 * te
    # Moon argument of latitude
    f = 93.2720950 + 483202.0175233 * te

    # Simplified Meeus Chap 47
    long_corr = 6.288774 * sind(m_prime) + 1.274027 * sind(2 * d - m_prime) + 0.658311 * sind(2 * d)
    lat_corr = 5.128122 * sind(f) + 0.280602 * sind(m_prime + f) + 0.277693 * sind(m_prime - f)

    moon_long = norm360(l_prime + long_corr)
    moon_lat = lat_corr

    eps = nutation.trueObliquity

    # Coordinates
    # RA: atan2(sin(L)cos(eps) - tan(B)sin(eps), cos(L))
    moon_ra = norm360(math.degrees(math.atan2(
        sind(moon_long) * cosd(eps) - math.tan(math.radians(moon_lat)) * sind(eps),
        cosd(moon_long)
    )))
    moon_dec = asind(sind(moon_lat) * cosd(eps) + cosd(moon_lat) * sind(eps) * sind(moon_long))

    return MoonResult(
        eclipticLongitude=moon_long,
        eclipticLatitude=moon_lat,
        rightAscension=moon_ra,
        declination=moon_dec,
        apparentLongitude=moon_long
    )

def compute_moon_phase(moon_long: float, sun_long: float) -> MoonPhaseResult:
    d = norm360(moon_long - sun_long)
    illum = (1 - cosd(d)) / 2 * 100

    if d < 90: phase = "First Quarter"
    elif d < 180: phase = "Full Moon"
    elif d < 270: phase = "Last Quarter"
    else: phase = "New Moon"

    return MoonPhaseResult(illuminationPercentage=round(illum, 2), phaseQuarter=phase)

