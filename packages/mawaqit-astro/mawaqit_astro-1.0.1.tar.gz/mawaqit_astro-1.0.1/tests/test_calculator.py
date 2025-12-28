import unittest
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mawaqit_astro import PrayerCalculator, Location, InputData, Madhab, ALA_HAZRAT

class TestPrayerCalculator(unittest.TestCase):
    def setUp(self):
        self.location = Location(latitude=24.8607, longitude=67.0011, timezone=5.0)
        self.date = InputData(year=2025, month=12, day=22)
        self.calculator = PrayerCalculator(method=ALA_HAZRAT, madhab=Madhab.HANAFI)

    def test_calculation_not_none(self):
        prayers = self.calculator.calculate(self.location, self.date)
        self.assertIsNotNone(prayers.fajr)
        self.assertIsNotNone(prayers.dhuhr)
        self.assertIsNotNone(prayers.maghrib)

    def test_asr_madhab_difference(self):
        calc_hanafi = PrayerCalculator(method=ALA_HAZRAT, madhab=Madhab.HANAFI)
        calc_shafi = PrayerCalculator(method=ALA_HAZRAT, madhab=Madhab.SHAFI)

        prayers_h = calc_hanafi.calculate(self.location, self.date)
        prayers_s = calc_shafi.calculate(self.location, self.date)

        # Asr Hanafi should be later than Asr Shafi
        self.assertNotEqual(prayers_h.asr, prayers_s.asr)

    def test_format_time(self):
        from mawaqit_astro.prayers.base import format_time
        self.assertEqual(format_time(12.5), "12:30:00")
        self.assertEqual(format_time(0.0), "00:00:00")
        self.assertEqual(format_time(23.99), "23:59:24")
        self.assertEqual(format_time(23.999), "23:59:56")
        self.assertEqual(format_time(24.0), "00:00:00")

    def test_missing_date_uses_current(self):
        from datetime import datetime
        # Create InputData with missing date parts
        today = datetime.now()
        missing_date = InputData(year=None, month=None, day=None)
        prayers = self.calculator.calculate(self.location, missing_date)
        self.assertIn("date", prayers.metadata)
        self.assertEqual(prayers.metadata["date"], f"{today.year}-{today.month:02d}-{today.day:02d}")

if __name__ == '__main__':
    unittest.main()

