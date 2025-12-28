from .base import get_hour_angle

def calculate_fajr(noon: float, delta: float, phi: float, fajr_angle: float) -> float:
    ha_fajr = get_hour_angle(-fajr_angle, phi, delta)
    return noon - (ha_fajr / 15.0) if ha_fajr else None

