from .base import get_hour_angle

def calculate_isha(noon: float, delta: float, phi: float, isha_angle: float = 0, isha_minutes: float = 0, maghrib_val: float = None) -> float:
    if isha_angle > 0:
        ha_isha = get_hour_angle(-isha_angle, phi, delta)
        return noon + (ha_isha / 15.0) if ha_isha else None

    if isha_minutes > 0 and maghrib_val is not None:
        return maghrib_val + (isha_minutes / 60.0)

    return None

