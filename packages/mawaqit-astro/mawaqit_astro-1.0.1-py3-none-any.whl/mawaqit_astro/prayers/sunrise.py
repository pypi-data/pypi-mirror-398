import math
from .base import get_hour_angle

def calculate_sunrise(noon: float, delta: float, phi: float, sd: float, hp: float, elevation: float = 0) -> float:
    # Dynamic sunrise altitude logic: (90 + SD + Refraction(34')) - HP
    # Altitude = 90 - Zenith = HP - SD - (34.0 / 60.0)

    # Dip of the Horizon
    dip = (1.76 * math.sqrt(elevation)) / 60.0 if elevation > 0 else 0

    alt = hp - sd - (34.0 / 60.0) - dip
    ha_sunrise = get_hour_angle(alt, phi, delta)
    return noon - (ha_sunrise / 15.0) if ha_sunrise else None


