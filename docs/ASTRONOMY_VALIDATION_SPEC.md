# Astronomy Validation Specification

**Version:** 1.0.0
**Status:** CANONICAL

## 1. Objective
To independently verify the absolute correctness of astronomical calculations against legitimate, independent reference data. Internal integration tests passing against the same implementation do not prove astrological correctness.

## 2. Validation Scope
The validation framework must verify:
- Julian date/time conversion (J2000 epoch handling).
- Planetary Longitude and Latitude (apparent and geocentric).
- Planetary Speed (daily motion).
- Retrograde Status boundaries (station points).
- Ayanamsa (precession of equinoxes) across historical dates.
- Ascendant (Lagna) based on precise geographic coordinates.
- House boundaries (Bhava Chalit).
- Nakshatra boundaries (27-star division).

## 3. Acceptable Reference Sources
Testing against `pyswisseph` directly within the engine only proves we call the library correctly. Ground truth requires independent references:
- Swiss Ephemeris official `swetest` output datasets.
- NASA JPL/Horizons system.
- Established rigorous software (e.g., Jagannatha Hora, Kala).
- Published astronomical tables (e.g., NC Lahiri Ephemeris for specific years).

## 4. Fixture Structure
Every astronomical golden fixture MUST declare:
```json
{
  "source": "NASA_JPL_HORIZONS",
  "source_version": "2024-01",
  "input": {
    "datetime_utc": "1869-10-02T01:37:00Z",
    "latitude": 21.6417,
    "longitude": 69.6293
  },
  "time_scale": "UTC",
  "coordinate_system": "geocentric_apparent",
  "expected_result": {
    "Sun": 166.4523
  },
  "tolerance": 0.0001,
  "reference_methodology": "Parashari_Lahiri",
  "validation_date": "2026-09-26"
}
```

## 5. Failure Protocol
Any drift beyond the stated `tolerance` for any planet or house calculation MUST instantly fail the CI build and mark the Phase 1/3 calculation status as `BLOCKED` until the mathematical deviation is resolved and explained.
