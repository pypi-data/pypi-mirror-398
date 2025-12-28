import math
from .base import get_hour_angle
from ..types import Madhab

def get_refraction(alt_deg: float) -> float:
    """
    Calculate atmospheric refraction in degrees for a given altitude in degrees.
    Uses Bennet's (1982) formula: R = cot(h + 7.31/(h + 4.4)) arcminutes.
    """
    if alt_deg <= -0.575:
        # For very low or negative altitudes, refraction is complex.
        # However, Asr always occurs at positive solar altitudes.
        return 0.0

    # Internal math.tan needs radians.
    h_rad = math.radians(alt_deg + (7.31 / (alt_deg + 4.4)))
    refraction_arcmin = 1.0 / math.tan(h_rad)
    return refraction_arcmin / 60.0

def calculate_asr(noon: float, delta: float, phi: float, sd: float = 0.0, hp: float = 0.0, madhab: Madhab = Madhab.HANAFI) -> float:
    """
    Calculate Asr prayer time using the shadow length definition,
    accounting for the sun's disk (semi-diameter) and atmospheric refraction.
    """
    # 1. Shadow Factor: 1 for Shafi/Maliki/Hanbali, 2 for Hanafi
    shadow_factor = 2.0 if madhab == Madhab.HANAFI else 1.0

    # 2. Geometric Noon Altitude
    alt_noon_geom = 90.0 - abs(phi - delta)

    # 3. Consider the "Upper Limb" and "Refraction" for the shadow edge at noon.
    # The shadow is cast by the top edge of the sun.
    # Apparent Altitude = Geometric Altitude + SD + Refraction
    alt_noon_app_upper = alt_noon_geom + sd + get_refraction(alt_noon_geom + sd)

    # 4. Apparent Zenith Distance of the Upper Limb at Noon
    # This determines the length of the shortest shadow of the day.
    zen_noon_app_upper = 90.0 - alt_noon_app_upper

    # 5. Calculate Shadow Length ratio (L/H) at Asr
    # Asr starts when Shadow = Shadow_at_Noon + Shadow_Factor * Object_Height
    shadow_ratio_asr = math.tan(math.radians(zen_noon_app_upper)) + shadow_factor

    # 6. Apparent Altitude of Upper Limb at Asr
    # cot(alt_app_upper) = shadow_ratio_asr  =>  alt_app_upper = atan(1 / shadow_ratio_asr)
    alt_asr_app_upper = math.degrees(math.atan(1.0 / shadow_ratio_asr))

    # 7. Back-calculate the Geometric Altitude of the Center at Asr
    # To find the time (hour angle), we need the geometric position of the sun's center.
    # Geometric Center = Apparent Upper Limb - SD - Refraction
    alt_asr_geom_center = alt_asr_app_upper - sd - get_refraction(alt_asr_app_upper)

    # 8. Calculate Hour Angle
    ha_asr = get_hour_angle(alt_asr_geom_center, phi, delta)

    return noon + (ha_asr / 15.0) if ha_asr else None

