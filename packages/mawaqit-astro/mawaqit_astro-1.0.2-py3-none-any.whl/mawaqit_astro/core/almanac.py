import math
from ..types import InputData, AlmanacResult
from .measures import parse_input, compute_time_measures
from .nutation import compute_nutation
from .aries import compute_aries
from .sun import compute_sun
from .moon import compute_moon, compute_moon_phase
from .weekday import get_weekday
from .polaris import compute_polaris
from .utils import sind, cosd

def compute_almanac(input_data: InputData) -> AlmanacResult:
    parsed = parse_input(input_data)
    time = compute_time_measures(parsed)

    nutation = compute_nutation(time.julianEphemerisCenturies)
    aries = compute_aries(time, nutation)
    sun = compute_sun(time, nutation, aries.greenwichApparentSiderealTime)
    moon = compute_moon(time, nutation, aries.greenwichApparentSiderealTime)

    weekday = get_weekday(time.julianDay)
    moon_phase = compute_moon_phase(moon.apparentLongitude, sun.eclipticLongitude)
    polaris = compute_polaris(time, nutation, sun.geocentricLongitude, aries.greenwichApparentSiderealTime)

    # Angular distance between moon and sun
    lunar_dist = math.acos(
        max(-1, min(1, sind(moon.declination) * sind(sun.declination) +
        cosd(moon.declination) * cosd(sun.declination) * cosd(moon.rightAscension - sun.rightAscension)))
    ) / (math.pi / 180)

    return AlmanacResult(
        input=input_data,
        time=time,
        nutation=nutation,
        aries=aries,
        sun=sun,
        moon=moon,
        weekday=weekday,
        moonPhase=moon_phase,
        polaris=polaris,
        lunarDistance=lunar_dist
    )

