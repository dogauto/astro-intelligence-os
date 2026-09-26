# Time and Location Validation Specification

**Version:** 1.0.0
**Status:** CANONICAL

## 1. Objective
To rigorously audit and validate the conversion of local birth inputs into standard astronomical UTC/Julian formats.

## 2. Validation Scope
The engine must flawlessly handle:
- **Timezone-aware datetimes:** Parsing local time with correct IANA timezone strings.
- **Historical DST transitions:** War-time offsets, local political changes.
- **Historical Timezone rules:** Changes in base LMT before standard time adoption.
- **Midnight boundaries & Date Rollover:** Correct assignment of date when born exactly at 00:00 or crossing GMT boundaries.
- **Leap years:** 29th February edge cases.
- **Longitude/Latitude bounds:** Validating bounds (-90 to +90 lat, -180 to +180 lon).
- **Sub-second precision:** Millisecond or second precision where standard ephemeris requires it.

## 3. Fixture Requirements
Deterministic tests must be created for historical edge cases.
Examples:
- India adopting IST in 1906 (pre/post boundary).
- London double summer time during WWII.
- US timezones before the Uniform Time Act of 1966.
- A birth in Kiribati on December 31, 1994 (Line Islands International Date Line skip).

## 4. Rejection Criteria
Inputs providing invalid coordinates or impossible dates (e.g., Feb 29, 2023) MUST raise an explicit `InvalidBirthDataException` before any calculation is attempted.
