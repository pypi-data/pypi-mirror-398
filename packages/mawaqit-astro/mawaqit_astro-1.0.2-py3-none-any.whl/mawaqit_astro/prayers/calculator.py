from typing import Optional
from ..types import Location, InputData, PrayerTimes, Madhab, CalculationMethod, HighLatitudeRule
from .methods import ALA_HAZRAT
from .base import format_time
from .dhuhr import get_solar_noon

# Separate calculation modules
from .fajr import calculate_fajr
from .sunrise import calculate_sunrise
from .dhuhr import calculate_dhuhr
from .asr import calculate_asr
from .maghrib import calculate_maghrib
from .isha import calculate_isha

class PrayerCalculator:
    def __init__(
        self,
        method: CalculationMethod = ALA_HAZRAT,
        madhab: Madhab = Madhab.HANAFI,
        high_lat_rule: HighLatitudeRule = HighLatitudeRule.TWILIGHT_ANGLE
    ):
        """
        Initialize the Prayer Calculator.

        Args:
            method: The calculation method. Default is ALA_HAZRAT (Fajr 18, Isha 18).
            madhab: Juristic method for Asr. Default is HANAFI.
            high_lat_rule: Rule for higher latitude regions.
        """
        self.method = method
        self.madhab = madhab
        self.high_lat_rule = high_lat_rule

    @staticmethod
    def create_custom_method(name: str, fajr_angle: float, isha_angle: float, maghrib_min: float = 0, isha_min: float = 0) -> CalculationMethod:
        """
        Create a custom calculation method.
        """
        return CalculationMethod(name, fajr_angle, isha_angle, maghrib_min, isha_min)

    def calculate(self, location: Location, date: Optional[InputData] = None) -> PrayerTimes:
        """
        Calculate prayer times for a specific location and date.

        Args:
            location: The geographic location.
            date: The date for calculation. Defaults to current system date/time.
        """
        if date is None:
            date = InputData()

        loc = location
        date_input = date

        # 1. Get Sun position at solar noon (initial estimate at 12:00 local)
        noon, delta, sd, hp = get_solar_noon(date_input, loc)
        phi = loc.latitude

        # Helper to refine prayer times iteratively for deep accuracy
        # Recalculates Noon, SunDeclination, SD, and HP for the specific moment of each prayer
        from .base import get_solar_parameters

        def refine(initial_time, calc_func, *args, iterations=10):
            if initial_time is None:
                return None
            current_time = initial_time
            for _ in range(iterations):
                # Recalculate parameters for the current estimated time
                n, d, s, h = get_solar_parameters(date_input, loc, current_time)

                # Check if calc_func accepts sd and hp (for sunrise, asr, maghrib)
                import inspect
                sig = inspect.signature(calc_func)

                kwargs = {}
                if 'temp_c' in sig.parameters: kwargs['temp_c'] = loc.temp_c
                if 'pressure_hpa' in sig.parameters: kwargs['pressure_hpa'] = loc.pressure_hpa

                if 'sd' in sig.parameters and 'hp' in sig.parameters:
                    current_time = calc_func(n, d, phi, s, h, *args, **kwargs)
                else:
                    current_time = calc_func(n, d, phi, *args, **kwargs)

                if current_time is None:
                    break
            return current_time

        # 2. Calculate initial estimates
        fajr_init = calculate_fajr(noon, delta, phi, self.method.fajr_angle)
        sunrise_init = calculate_sunrise(noon, delta, phi, sd, hp, loc.elevation)
        dhuhr_init = calculate_dhuhr(noon)
        asr_init = calculate_asr(noon, delta, phi, sd, hp, self.madhab, loc.temp_c, loc.pressure_hpa)
        maghrib_init = calculate_maghrib(noon, delta, phi, sd, hp, self.method.maghrib_minutes, loc.elevation)
        isha_init = calculate_isha(
            noon,
            delta,
            phi,
            isha_angle=self.method.isha_angle,
            isha_minutes=self.method.isha_minutes,
            maghrib_val=maghrib_init
        )

        # 3. Refine each prayer time iteratively
        fajr_val = refine(fajr_init, calculate_fajr, self.method.fajr_angle)
        sunrise_val = refine(sunrise_init, calculate_sunrise, loc.elevation)

        # Dhuhr refinement (Noon + offset)
        def _dhuhr_calc(n, d, p): return calculate_dhuhr(n)
        dhuhr_val = refine(dhuhr_init, _dhuhr_calc)

        asr_val = refine(asr_init, calculate_asr, self.madhab)
        maghrib_val = refine(maghrib_init, calculate_maghrib, self.method.maghrib_minutes, loc.elevation)

        # Isha refinement depends on whether it's angle-based or minute-based
        if self.method.isha_angle > 0:
            isha_val = refine(isha_init, calculate_isha, self.method.isha_angle, 0, None)
        else:
            # If based on minutes after Maghrib, use the already refined Maghrib
            isha_val = calculate_isha(
                None, None, phi,
                isha_angle=0,
                isha_minutes=self.method.isha_minutes,
                maghrib_val=maghrib_val
            )

        # 4. Final Validation: Ensure times were calculated
        prayer_vals = {
            "Fajr": fajr_val, "Sunrise": sunrise_val, "Dhuhr": dhuhr_val,
            "Asr": asr_val, "Maghrib": maghrib_val, "Isha": isha_val
        }

        missing = [name for name, val in prayer_vals.items() if val is None]
        if missing:
            from ..exceptions import CalculationError
            raise CalculationError(
                f"Could not calculate {', '.join(missing)} for the given location and date. "
                "This often happens in polar regions where the sun may not rise or set."
            )

        return PrayerTimes(
            fajr=format_time(fajr_val),
            sunrise=format_time(sunrise_val),
            dhuhr=format_time(dhuhr_val),
            asr=format_time(asr_val),
            maghrib=format_time(maghrib_val),
            isha=format_time(isha_val),
            metadata={
                "method": self.method.name,
                "madhab": self.madhab.name,
                "date": f"{date_input.year}-{date_input.month:02d}-{date_input.day:02d}"
            }
        )

