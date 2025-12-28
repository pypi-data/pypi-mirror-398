import math
from ..types import InputData, Location
from ..core.almanac import compute_almanac
from ..core.measures import parse_input


def get_hour_angle(alt_deg: float, phi: float, delta: float) -> float:
    alt_rad = math.radians(alt_deg)
    phi_rad = math.radians(phi)
    delta_rad = math.radians(delta)

    # cos(H) = (sin(h) - sin(phi)sin(delta)) / (cos(phi)cos(delta))
    cos_h = (math.sin(alt_rad) - math.sin(phi_rad) * math.sin(delta_rad)) / (math.cos(phi_rad) * math.cos(delta_rad))

    if cos_h > 1 or cos_h < -1:
        return None

    return math.degrees(math.acos(cos_h))


def get_solar_parameters(date: InputData, loc: Location, local_hour: float) -> tuple[float, float]:
    """
    Get (solar_noon, declination) for a specific local hour.
    Calculates accurately by considering the exact time of day.
    """
    if local_hour is None:
        local_hour = 12.0  # Default to noon if no time provided

    # Convert local hour to UTC components for Julian Day calculation
    utc_hour_raw = local_hour - loc.timezone

    # We can pass fractional hours to InputData if parse_input/compute_time_measures handles it.
    # Looking at compute_time_measures:
    # dayfraction = (hour + minute / 60 + second / 3600) / 24
    # It works with floats.

    test_input = InputData(
        year=date.year,
        month=date.month,
        day=date.day,
        hour=0,
        minute=0,
        second=utc_hour_raw * 3600, # Pass everything as seconds to avoid overflow in hour/min
        deltaT=date.deltaT
    )

    res = compute_almanac(test_input)
    sun = res.sun

    eot = sun.equationOfTime # in minutes
    # Local Noon = 12 + timezone - longitude/15 - EOT/60
    standard_adjustment = 12.0 + loc.timezone - (loc.longitude / 15.0)
    noon = standard_adjustment - (eot / 60.0)

    # Convert SD and HP from arcseconds to degrees
    sd = (sun.semidiameter or 0) / 3600.0
    hp = (sun.horizontalParallax or 0) / 3600.0

    return noon, sun.declination, sd, hp

def format_time(hours: float) -> str:
    if hours is None: return "--:--"
    hours = hours % 24

    # Use total seconds for more reliable rounding
    total_seconds = round(hours * 3600)
    h = (total_seconds // 3600) % 24
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60

    return f"{h:02d}:{m:02d}:{s:02d}"

