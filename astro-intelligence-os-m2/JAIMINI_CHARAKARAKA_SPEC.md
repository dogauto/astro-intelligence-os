# JAIMINI_CHARAKARAKA_SPEC

**Status:** DRAFT — source-derived deterministic foundation  
**Primary source:** Sanjay Rath, *A Course on Jaimini Maharshi's Upadesa Sutra, Volume I*  
**Source section:** CHARAKARAKA, approximately pp. 288–303 in the supplied scan/text extraction.

## 1. Purpose

Define the deterministic Chara Karaka calculation contract required before implementing the Jaimini career method.

This specification separates astronomical input, Chara Karaka calculation, provenance, and downstream interpretation. It does **not** define the complete Jaimini career prediction method.

## 2. Approved source

The supplied Rath course covers two Chara Karaka schemes, Atmakaraka, the remaining Chara Karakas, Rahu treatment, degree/minute/second ordering, Amatyakaraka, AK/AmK relationships, career/profession interpretation, Karaka Lagna, and worked examples.

For this first implementation, use Rath's stated operational convention. Do not silently substitute a different Jaimini convention.

## 3. Chara Karaka schemes

### Seven-planet scheme

Eligible planets:

- Sun
- Moon
- Mars
- Mercury
- Jupiter
- Venus
- Saturn

Rahu is not normally included. Putrakaraka is not a separate role. Ketu is excluded.

### Eight-planet scheme

Eligible planets:

- Sun
- Moon
- Mars
- Mercury
- Jupiter
- Venus
- Saturn
- Rahu

Ketu is excluded. Rahu is included.

The engine MUST make the scheme explicit:

```text
CHARA_KARAKA_SCHEME_7
CHARA_KARAKA_SCHEME_8
```

## 4. Longitude basis

Rank planets by longitude **irrespective of sign**.

For ordinary planets:

```text
effective_longitude = longitude_within_sign
```

The signs do not affect the ranking quantity.

## 5. Rahu transformation

For Rahu, calculate longitude from the end of the sign:

```text
effective_longitude = 30°00'00" - rahu_longitude_within_sign
```

Example from the source:

```text
Rahu = 14°33'
effective = 30°00' - 14°33' = 15°27'
```

Store both raw and effective longitude.

## 6. Precision and ordering

Ordering uses:

1. degrees
2. minutes
3. seconds

Do not round to whole degrees before ranking. Prefer exact fixed-point arcseconds or an equivalent exact representation.

## 7. Tie handling

If planets occupy the same degree, compare minutes; if minutes are also equal, compare seconds.

If two planets are exactly equal at the engine's supported precision, the supplied material does not establish a further tie-breaker. Do **not** invent one using planet name, enum order, insertion order, or ID. Return an explicit unresolved-tie/abstention result unless a later approved source resolves it.

## 8. Ranking algorithm

```python
eligible = select_planets(scheme)

for planet in eligible:
    if planet == RAHU:
        effective = 30deg - longitude_within_sign[planet]
    else:
        effective = longitude_within_sign[planet]

ranked = sort_descending(effective)

if any_exact_equal_effective_longitudes(ranked):
    return unresolved_tie(...)
```

## 9. Eight-planet role mapping

| Rank | Role | Symbol |
|---:|---|---|
| 1 | Atmakaraka | AK |
| 2 | Amatyakaraka | AmK |
| 3 | Bhratrakaraka | BK |
| 4 | Matrukaraka | MK |
| 5 | Pitrakaraka | PiK |
| 6 | Putrakaraka | PK |
| 7 | Jnatikaraka | GK |
| 8 | Darakaraka | DK |

## 10. Seven-planet role mapping

| Rank | Role | Symbol |
|---:|---|---|
| 1 | Atmakaraka | AK |
| 2 | Amatyakaraka | AmK |
| 3 | Bhratrakaraka | BK |
| 4 | Matrukaraka | MK |
| 5 | Pitrakaraka | PiK |
| 6 | Jnatikaraka | GK |
| 7 | Darakaraka | DK |

Putrakaraka is absent as a separate role.

## 11. Atmakaraka

The highest effective longitude is Atmakaraka (AK), per the source's Sutra 1.1.10 discussion.

```text
AK = ranked[0]
```

## 12. Amatyakaraka

The second-highest effective longitude is Amatyakaraka (AmK), per Sutra 1.1.12 and its commentary.

Rath explicitly states in the surrounding commentary that Amatyakaraka controls career/profession. Therefore AmK is a primary input to the first Jaimini career method.

## 13. Career-relevant interpretation

The source connects:

- Atmakaraka with the governing/self factor;
- Amatyakaraka with career/profession;
- Putrakaraka with power/support;
- AK relationships with accomplishment;
- houses/lords, Arudha Pada, and Karaka as categories of activity indicators.

Represent these as explicit evidence, not an opaque score.

Example:

```json
{
  "type": "chara_karaka",
  "role": "AMATYAKARAKA",
  "planet": "SATURN",
  "interpretation_scope": "career_profession",
  "source_rule": "rath_charakaraka_amatyakaraka"
}
```

## 14. AK-relative support

The source describes an interpretive framework in which Karakas in quadrants (1, 4, 7, 10) from AK are fully supported/strong, panaphara houses (2, 5, 8, 11) weaker, and apoklima houses (3, 6, 9, 12) weakest. It also discusses conjunction/aspect with AK.

These are **downstream interpretation rules**, not part of the Chara Karaka rank calculator.

Implement separately:

```text
calculate_chara_karakas()
    ↓
evaluate_ak_relative_support()
```

## 15. Karaka Lagna

The source uses the sign occupied by AK as Karaka Lagna.

```text
Karaka Lagna = sign of AK
```

This is a derived datum; this document does not define the complete Karaka Lagna interpretation engine.

## 16. Recommended data model

```python
class CharaKarakaRole(str, Enum):
    ATMAKARAKA = "AK"
    AMATYAKARAKA = "AmK"
    BHRATRAKARAKA = "BK"
    MATRAKARAKA = "MK"
    PITRAKARAKA = "PiK"
    PUTRAKARAKA = "PK"
    JNATIKARAKA = "GK"
    DARAKARAKA = "DK"
```

```python
class CharaKarakaEntry:
    planet: Planet
    role: CharaKarakaRole
    raw_longitude_within_sign: Angle
    effective_longitude: Angle
    rank: int
    scheme: CharaKarakaScheme
```

```python
class CharaKarakaResult:
    scheme: CharaKarakaScheme
    entries: tuple[CharaKarakaEntry, ...]
    atmakaraka: CharaKarakaEntry
    amatyakaraka: CharaKarakaEntry
    karaka_lagna: Sign
    calculation_version: str
    convention_profile_id: str
    provenance: ProvenanceRef
```

Adapt to existing project types rather than duplicating them.

## 17. Provenance

Every result must preserve:

- source
- source section
- source convention
- calculation version
- scheme
- eligible planets
- raw longitudes
- effective longitudes
- ranking
- assigned roles

Minimum provenance:

```json
{
  "calculation": "chara_karaka",
  "source": {
    "author": "Sanjay Rath",
    "title": "A Course on Jaimini Maharshi's Upadesa Sutra",
    "volume": "I",
    "section": "CHARAKARAKA"
  },
  "convention": {
    "scheme": "8_PLANET",
    "rahu_from_end_of_sign": true,
    "ketu_excluded": true,
    "precision": "degree_minute_second"
  }
}
```

## 18. Source validation fixtures

### Sri Krishna

The supplied source gives:

```text
Sun     18°10'   → AK
Saturn  17°03'   → AmK
Moon    16°28'   → BK
Venus   15°24'   → PiK
Rahu    14°33' raw
Rahu    15°27' effective → MK
Mars     3°13'   → PK
Mercury  1°51'   → GK
Jupiter  1°22'   → DK
```

Expected ordering:

```text
Sun > Saturn > Moon > Venus > Rahu(effective) > Mars > Mercury > Jupiter
```

### K.N. Rao

The supplied source gives an eight-planet example with:

```text
Sun     24°53'50" → AK
Jupiter 24°42'59"
Saturn  24°05'...
Mars    24°02'17"
Rahu    11°40' raw
Rahu    18°20' effective
```

This exercises finer-than-degree ordering, Rahu transformation, and AmK determination. When encoding the fixture, preserve the exact source values available in the supplied scan/extraction rather than reconstructing missing digits.

## 19. Tests required

### Unit tests

1. seven-planet eligible set
2. eight-planet eligible set
3. Ketu exclusion
4. Rahu transformation
5. ordinary-planet longitude preservation
6. descending ranking
7. degree tie resolution
8. minute tie resolution
9. second tie resolution
10. exact-equality abstention/error
11. role mapping for 7 planets
12. role mapping for 8 planets
13. AK extraction
14. AmK extraction
15. Karaka Lagna derivation
16. deterministic repeatability
17. provenance completeness

### Fixture tests

18. Sri Krishna source fixture
19. K.N. Rao source fixture

### Invariants

Eight-planet success:

```text
len(entries) == 8
all roles unique
all planets unique
AK rank == 1
AmK rank == 2
DK rank == 8
Ketu absent
```

Seven-planet success:

```text
len(entries) == 7
PK absent
Ketu absent
AK rank == 1
AmK rank == 2
DK rank == 7
```

## 20. Explicit non-goals

Do not yet implement:

- complete Jaimini career prediction;
- Jaimini Dasha;
- Chara Dasha timing;
- Narayana Dasha;
- Rasi Drishti interpretation;
- Arudha calculation changes;
- Karakamsa interpretation;
- Swamsa interpretation;
- Varnada Lagna;
- profession classification;
- career-event timing;
- probabilistic confidence;
- learned weights;
- convergence with Parashari;
- generic ComparisonEngine changes.

These must be separate methods/rules with their own provenance.

## 21. Source boundary

A rule becomes implementation-ready only when:

1. its source location is recorded;
2. computational inputs are identified;
3. convention is explicit;
4. the rule is deterministic enough to encode;
5. expected output can be tested.

Otherwise mark it `SPECIFIED_BUT_NOT_IMPLEMENTED` rather than filling gaps from general astrological knowledge.

## 22. Implementation sequence

### Phase 1 — foundation

Implement only:

```text
CharaKarakaScheme
CharaKarakaRole
effective_longitude()
rank_charakarakas()
CharaKarakaResult
provenance
```

### Phase 2 — fixtures

Add Sri Krishna and K.N. Rao source fixtures and verify exact outputs.

### Phase 3 — AstroState integration

Consume existing deterministic planetary positions from AstroState. Do not recalculate astronomy inside the Jaimini method.

### Phase 4 — narrow career method

Only after the foundation passes, implement `JaiminiCareerMethod` using a narrow first rule set based on AK, AmK, AK-relative support, and career/profession interpretation explicitly supported by the source.

### Phase 5 — broader Jaimini

Add further rules one at a time with independent provenance and tests.

## 23. Acceptance criteria

- [ ] seven-planet scheme deterministic
- [ ] eight-planet scheme deterministic
- [ ] Ketu excluded
- [ ] Rahu reverse-from-end-of-sign implemented
- [ ] degree/minute/second precision preserved
- [ ] exact ties not silently resolved
- [ ] role mapping explicit
- [ ] source fixtures pass
- [ ] provenance complete
- [ ] calculation version recorded
- [ ] AstroState is sole astronomical input
- [ ] no LLM participates in calculation
- [ ] no heuristic probability introduced
- [ ] no unsupported Jaimini rule added

## Source-derived conclusion

The supplied Rath course is sufficient to establish a concrete deterministic **Chara Karaka foundation**.

It is not, from the material extracted so far, sufficient to justify implementing the entire Jaimini career method.

The next coding target is therefore the Chara Karaka calculator and its source fixtures, followed by a narrow, explicitly sourced career method.
