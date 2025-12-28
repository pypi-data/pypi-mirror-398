import math
from .base import get_hour_angle

def calculate_maghrib(noon: float, delta: float, phi: float, sd: float, hp: float, maghrib_minutes: float = 0, elevation: float = 0) -> float:
    # Dynamic sunset altitude logic: 90 + SD - HP + Refraction(34')
    # Altitude = 90 - Zenith = HP - SD - (34.0 / 60.0)

    # Dip of the Horizon
    dip = (1.76 * math.sqrt(elevation)) / 60.0 if elevation > 0 else 0

    alt = hp - sd - (34.0 / 60.0) - dip
    ha_sunset = get_hour_angle(alt, phi, delta)

    if ha_sunset is None:
        return None

    maghrib_val = noon + (ha_sunset / 15.0)

    if maghrib_minutes > 0:
        maghrib_val += (maghrib_minutes / 60.0)

    return maghrib_val


