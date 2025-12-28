import math
from .base import get_hour_angle
from ..types import Madhab

def get_refraction(apparent_alt_deg: float, temp_c: float = 15.0, pressure_hpa: float = 1013.25) -> float:
    """
    Calculates atmospheric refraction using numerical integration (Ray Tracing).
    Based on the principles of Auer & Standish.
    """
    if apparent_alt_deg > 89.9:
        return 0.0

    # Constants
    R_EARTH = 6371000.0  # Earth radius in meters
    Z_STEP = 100.0       # Integration step size in meters
    Z_MAX = 80000.0      # Top of atmosphere (80km)

    # Initial conditions at observer (Refractive Index n0)
    t_k = temp_c + 273.15
    n0 = 1 + (0.000287 * (pressure_hpa / 1013.25) * (288.15 / t_k))

    # Zenith angle in radians
    z_obs = math.radians(90.0 - apparent_alt_deg)

    # Snell's Law Constant for a spherical medium: n * r * sin(z) = const
    k = n0 * R_EARTH * math.sin(z_obs)

    total_refraction_rad = 0.0
    n_current = n0

    # Numerical Integration
    z = 0.0
    while z < Z_MAX:
        z_next = z + Z_STEP
        r_next = R_EARTH + z_next

        # 1. Model Atmosphere: Calculate Temperature at altitude z_next
        if z_next < 11000:
            t_alt = t_k - 0.0065 * z_next
            p_alt = pressure_hpa * math.pow(t_alt / t_k, 5.255)
        else:
            t_alt = t_k - 71.5 # Stratosphere approx
            p_alt = pressure_hpa * 0.223 * math.exp(-0.000157 * (z_next - 11000))

        # 2. Calculate refractive index at this altitude
        n_next = 1 + (0.000287 * (p_alt / 1013.25) * (283.15 / (t_alt + 273.15)))

        # 3. Calculate bending (Differential Refraction)
        # sin(z_local) = k / (n * r)
        try:
            sin_z_local = k / (n_next * r_next)
            if sin_z_local >= 1.0:
                break
            tan_z_local = sin_z_local / math.sqrt(1 - sin_z_local**2)
        except (ValueError, ZeroDivisionError):
            break

        dn = n_next - n_current
        dR = -(dn / n_next) * tan_z_local
        total_refraction_rad += dR

        # Update for next step
        n_current = n_next
        z = z_next

    return math.degrees(total_refraction_rad)

def mid_to_limb(alt_noon_geom: float, sd: float = 0.0, hp: float = 0.0, temp_c: float = 15.0, pressure_hpa: float = 1013.25) -> float:
    """
    Calculate the difference between the sun's center and its upper limb in degrees.
    """

    alt_noon_app_upper = alt_noon_geom + sd + get_refraction(alt_noon_geom + sd, temp_c, pressure_hpa)

    return alt_noon_app_upper - alt_noon_geom

def calculate_asr(noon: float, delta: float, phi: float, sd: float = 0.0, hp: float = 0.0, madhab: Madhab = Madhab.HANAFI, temp_c: float = 15.0, pressure_hpa: float = 1013.25) -> float:
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
    alt_noon_app_upper = alt_noon_geom + sd + get_refraction(alt_noon_geom + sd, temp_c, pressure_hpa)

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
    alt_asr_geom_center = alt_asr_app_upper - sd - get_refraction(alt_asr_app_upper, temp_c, pressure_hpa)

    # 8. Calculate Hour Angle
    ha_asr = get_hour_angle(alt_asr_geom_center, phi, delta)

    return noon + (ha_asr / 15.0) if ha_asr else None

