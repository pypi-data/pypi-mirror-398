from ..types import InputData, Location
from ..core.almanac import compute_almanac
from ..core.measures import parse_input

def get_solar_noon(date: InputData, loc: Location) -> tuple[float, float]:
    # Ensure the input date is normalized (fills missing parts if needed)
    date = parse_input(date)


    # Calculate Sun parameters at 12:00 UTC (or current time if provided)
    # But for a stable starting point, we often use 12:00 UTC for the day.
    # However, parse_input already handled filling defaults.
    # We'll use the day fraction if available, otherwise default to 0.5 (12:00)

    noon_input = InputData(
        year=date["year"],
        month=date["month"],
        day=date["day"],
        hour=0,
        minute=0,
        second=date["dayfraction"] * 86400,
        deltaT=date["deltaT"]
    )

    res = compute_almanac(noon_input)
    sun = res.sun

    eot = sun.equationOfTime # minutes
    # Local Noon = 12 + timezone - longitude/15 - EOT/60
    standard_adjustment =  12.0 + loc.timezone - (loc.longitude / 15.0)
    noon = standard_adjustment - (eot / 60.0)

    # Convert SD and HP from arcseconds to degrees
    sd = (sun.semidiameter or 0) / 3600.0
    hp = (sun.horizontalParallax or 0) / 3600.0

    return noon, sun.declination, sd, hp


def calculate_dhuhr(noon: float) -> float:
    # Dhuhr (Noon + slight offset usually 1 min for safety/zawal)
    return noon + (0.01 / 60.0)

