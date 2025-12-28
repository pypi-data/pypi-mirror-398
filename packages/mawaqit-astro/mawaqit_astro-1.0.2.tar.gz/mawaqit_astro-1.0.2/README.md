# Mawaqit-Astro

[![PyPI version](https://img.shields.io/pypi/v/mawaqit-astro.svg)](https://pypi.org/project/mawaqit-astro/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Mawaqit-Astro** is a high-precision Python library for astronomical calculations and Islamic prayer times. It is a port of advanced astronomical logic, providing features for sun and moon positioning, sidereal time, and prayer time calculations based on various global standards.

## Features

- **Comprehensive Astronomical Data**: Compute Sun, Moon, Polaris positions, Nutation, and more.
- **Accurate Prayer Times**: Default support for Islamic Scholar Ala Hazrat method, with full support for custom angles and minute-based offsets.
- **Flexible Madhab Support**: Shafi and Hanafi methods for Asr calculations.
- **High Latitude Support**: Robust rules for regions with extreme day/night cycles.
- **Pure Python**: No external dependencies required.

## Installation

```bash
pip install mawaqit-astro
```

## Quick Start

### 1. Calculate Prayer Times

```python
from mawaqit_astro import PrayerCalculator, Location

# 1. Provide only required location data
location = Location(latitude=24.8607, longitude=67.0011, timezone=5.0)

# 2. Calculate using professional defaults
# (Current date, Ala Hazrat method, Hanafi Madhab)
times = PrayerCalculator().calculate(location)

print(f"Fajr: {times.fajr}")
print(f"Isha: {times.isha}")
```

### 2. High-Level Almanac Calculations

```python
from mawaqit_astro.core.almanac import compute_almanac, InputData

# Advanced astronomical data for a specific moment
data = InputData(year=2025, month=12, day=24, hour=12, minute=0, second=0)
almanac = compute_almanac(data)

print(f"Sun Right Ascension: {almanac.sun.rightAscension}")
print(f"Moon Phase: {almanac.moon.phase}")
```

## Project Structure

```text
mawaqit-astro/
├── src/
│   └── mawaqit_astro/
│       ├── core/       # High-precision astronomy logic (Sun, Moon, Nutation, etc.)
│       ├── prayers/    # Prayer time calculation modules
│       ├── utils/      # Mathematical and date utilities
│       └── types.py    # Common data structures
├── tests/              # Comprehensive test suite
├── pyproject.toml      # Package configuration
└── README.md           # Documentation
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
