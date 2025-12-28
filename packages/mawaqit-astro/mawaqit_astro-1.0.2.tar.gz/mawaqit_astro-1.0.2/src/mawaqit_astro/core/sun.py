import math
from ..types import TimeMeasures, NutationResult, SunResult
from .utils import sind, cosd, asind, acosd, norm360

def compute_sun(time: TimeMeasures, nutation: NutationResult, gast: float) -> SunResult:
    te = time.julianEphemerisCenturies

    # Mean longitude
    l0 = norm360(280.46646 + 36000.76983 * te + 0.0003032 * te**2)
    # Mean anomaly
    m = norm360(357.52911 + 35999.05029 * te - 0.0001537 * te**2)
    # Eccentricity
    e = 0.016708634 - 0.000042037 * te - 0.0000001267 * te**2

    # Equation of center
    c = (1.914602 - 0.004817 * te - 0.000014 * te**2) * sind(m) \
        + (0.019993 - 0.000101 * te) * sind(2 * m) \
        + 0.000289 * sind(3 * m)

    # True longitude
    sun_long = l0 + c
    # True anomaly
    v = m + c

    # Distance
    r = (1.000001018 * (1 - e**2)) / (1 + e * cosd(v))

    # Apparent longitude (Aberration + Nutation)
    omega = 125.04 - 1934.136 * te
    sun_app_long = sun_long - 0.00569 - 0.00478 * sind(omega)

    # Obliquity
    eps = nutation.trueObliquity

    # Right Ascension
    sun_ra = norm360(math.degrees(math.atan2(cosd(eps) * sind(sun_app_long), cosd(sun_app_long))))
    # Declination
    sun_dec = asind(sind(eps) * sind(sun_app_long))

    # Equation of Time
    y = math.tan(math.radians(eps) / 2)**2
    eot = 4 * math.degrees(y * sind(2 * l0) - 2 * e * sind(m) + 4 * e * y * sind(m) * cosd(2 * l0) \
        - 0.5 * y**2 * sind(4 * l0) - 1.25 * e**2 * sind(2 * m))

    # Semidiameter (arcseconds)
    sd = 959.63 / r
    # Horizontal Parallax (arcseconds)
    hp = 8.794 / r

    return SunResult(
        eclipticLongitude=sun_long,
        eclipticLatitude=0.0,
        rightAscension=sun_ra,
        declination=sun_dec,
        apparentLongitude=sun_app_long,
        geocentricLongitude=sun_long,
        distanceAU=r,
        equationOfTime=eot,
        horizontalParallax=hp,
        semidiameter=sd
    )

