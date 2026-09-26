# Astronomy Reference Registry

**Status:** CANONICAL

## 1. Reference Sources Available

The following external sources are cleared for use in generating ground-truth validation fixtures:
- NASA JPL Horizons (Geocentric Apparent Ephemeris)
- Swiss Ephemeris (`swetest`) Official Distribution
- NC Lahiri Published Ephemeris (for historical Ayanamsa verification)
- Jagannatha Hora (v8.0+) (for Astrological Convention verification)

## 2. Reference Fixtures Actually Verified

> **Currently, ZERO fixtures have been formally cross-validated against these external references.** The core engine relies on internal regressions only. Phase 1 is strictly `VERIFIED_SUBSET` until this registry is populated and automated.

### Registry Format

Once generated, verified fixtures must be listed here in the following tabular format:

| Fixture ID | Source | Version/Date | Input (UTC) | Time Scale | Coord System | Expected Output | Tolerance | Validation Result | Date |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FIX_ASTRO_001` | NASA_JPL | 2024-01 | `1869-10-02T01:37:00Z` | UTC | Geo Apparent | `<TBD>` | 0.0001 | PENDING | - |

*(Do NOT populate expected outputs manually. They must be mathematically extracted directly from the reference source.)*
