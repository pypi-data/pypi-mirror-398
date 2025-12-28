from math import floor
from datetime import datetime
from ..types import InputData, TimeMeasures

def parse_input(in_data: InputData) -> dict:
    year = in_data.year
    month = in_data.month
    day = in_data.day
    hour = in_data.hour
    minute = in_data.minute
    second = in_data.second
    deltaT = in_data.deltaT

    # If any date or time parts are missing, use the current local datetime
    now = datetime.now()

    if year is None or month is None or day is None:
        year = now.year
        month = now.month
        day = now.day
        # update the input object so callers see the filled values
        in_data.year = year
        in_data.month = month
        in_data.day = day

    if hour is None:
        hour = now.hour
        in_data.hour = hour
    if minute is None:
        minute = now.minute
        in_data.minute = minute
    if second is None:
        second = now.second
        in_data.second = second

    dayfraction = (hour + minute / 60 + second / 3600) / 24

    from ..exceptions import ValidationError

    # Validation
    if year is None or month is None or day is None:
        raise ValidationError("Required date parts (year, month, day) are missing or could not be determined.")
    if month < 1 or month > 12:
        raise ValidationError(f"Month must be between 1 and 12, got {month}")
    if day < 1 or day > 31:
        raise ValidationError(f"Day must be between 1 and 31, got {day}")

    # Allow dayfraction to be slightly outside [0, 1] due to UTC offsets
    # or handle it by normalizing the date. For simplicity in this core logic,
    # we'll allow it and let the Julian Day calculation handle it.

    return {
        "year": year,
        "month": month,
        "day": day,
        "dayfraction": dayfraction,
        "deltaT": deltaT
    }

def compute_time_measures(parsed: dict) -> TimeMeasures:
    year = parsed["year"]
    month = parsed["month"]
    day = parsed["day"]
    dayfraction = parsed["dayfraction"]
    deltaT = parsed["deltaT"]

    y = year
    m = month
    if m <= 2:
        y -= 1
        m += 12

    A = floor(y / 100)
    B = 2 - A + floor(A / 4)

    JD0h = floor(365.25 * (y + 4716)) + floor(30.6001 * (m + 1)) + day + B - 1524.5
    JD = JD0h + dayfraction

    T = (JD - 2451545) / 36525

    JDE = JD + deltaT / 86400
    TE = (JDE - 2451545) / 36525

    return TimeMeasures(
        julianDay=JD,
        julianEphemerisDay=JDE,
        julianCenturies=T,
        julianEphemerisCenturies=TE,
        dayFraction=dayfraction
    )

