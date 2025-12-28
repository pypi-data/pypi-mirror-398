from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum, auto

class Madhab(Enum):
    SHAFI = 1
    HANAFI = 2

class HighLatitudeRule(Enum):
    MIDDLE_OF_NIGHT = 'MiddleOfTheNight'
    SEVENTH_OF_NIGHT = 'SeventhOfTheNight'
    TWILIGHT_ANGLE = 'TwilightAngle'

@dataclass
class CalculationMethod:
    name: str
    fajr_angle: float
    isha_angle: float
    maghrib_minutes: float = 0
    isha_minutes: float = 0

    def __post_init__(self):
        from .exceptions import ValidationError
        if self.fajr_angle < 0 or self.fajr_angle > 90:
            raise ValidationError(f"Fajr angle must be between 0 and 90, got {self.fajr_angle}")
        if self.isha_angle < 0 or self.isha_angle > 90:
            raise ValidationError(f"Isha angle must be between 0 and 90, got {self.isha_angle}")

@dataclass
class Location:
    latitude: float
    longitude: float
    timezone: float
    elevation: float = 0.0
    temp_c: float = 15.0
    pressure_hpa: float = 1013.25

    def __post_init__(self):
        from .exceptions import LocationError
        if not (-90 <= self.latitude <= 90):
            raise LocationError(f"Latitude must be between -90 and 90 degrees, got {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise LocationError(f"Longitude must be between -180 and 180 degrees, got {self.longitude}")
        if not (-14 <= self.timezone <= 14):
            # Timezones range roughly from -12 to +14 (Line Islands)
            raise LocationError(f"Timezone offset seems invalid: {self.timezone}")

@dataclass
class PrayerTimes:
    fajr: str
    sunrise: str
    dhuhr: str
    asr: str
    maghrib: str
    isha: str
    metadata: Dict = field(default_factory=dict)

# Original Astro Types (Internal)
@dataclass
class InputData:
    year: int | None = None
    month: int | None = None
    day: int | None = None
    hour: int | None = None
    minute: int | None = None
    second: int | None = None
    deltaT: float = 70.0

@dataclass
class TimeMeasures:
    julianDay: float
    julianEphemerisDay: float
    julianCenturies: float
    julianEphemerisCenturies: float
    dayFraction: float

@dataclass
class NutationResult:
    nutationLongitude: float
    nutationObliquity: float
    meanObliquity: float
    trueObliquity: float

@dataclass
class SunResult:
    eclipticLongitude: float
    eclipticLatitude: float
    rightAscension: float
    declination: float
    apparentLongitude: Optional[float] = None
    geocentricLongitude: Optional[float] = None
    distanceAU: Optional[float] = None
    equationOfTime: Optional[float] = None
    horizontalParallax: Optional[float] = None
    semidiameter: Optional[float] = None

@dataclass
class MoonResult:
    eclipticLongitude: float
    eclipticLatitude: float
    rightAscension: float
    declination: float
    apparentLongitude: Optional[float] = None
    distanceKm: Optional[float] = None
    distanceAU: Optional[float] = None
    semidiameter: Optional[float] = None
    horizontalParallax: Optional[float] = None

@dataclass
class AriesResult:
    greenwichMeanSiderealTime: float
    greenwichApparentSiderealTime: float
    equationOfEquinoxes: float

@dataclass
class MoonPhaseResult:
    illuminationPercentage: float
    phaseQuarter: str

@dataclass
class PolarisResult:
    rightAscension: float
    declination: float
    greenwichHourAngle: float
    siderealHourAngle: float

@dataclass
class AlmanacResult:
    input: InputData
    time: TimeMeasures
    sun: SunResult
    moon: MoonResult
    nutation: NutationResult
    aries: AriesResult
    weekday: str
    moonPhase: MoonPhaseResult
    lunarDistance: float
    polaris: Optional[PolarisResult] = None

