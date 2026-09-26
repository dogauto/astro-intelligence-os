"""
State Builder (Phase 2-3)
=========================

Orchestrates the computation of a full AstroState from raw input.

This is the primary entry point for computing a chart:

    builder = AstroStateBuilder(engine)
    state = builder.build(birth_input, convention)

Phase 2-3 additions:
- Varga (divisional chart) computation
- Vimshottari Dasha computation
- Shadbala (strength) computation
- Ashtakavarga computation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from astro_engine import __version__
from astro_engine.ashtakavarga import compute_ashtakavarga
from astro_engine.astronomy import (
    PLANET_NAMES,
    AstronomyEngine,
    Planet,
    datetime_to_jd,
    longitude_to_sign,
)
from astro_engine.conventions import ConventionProfile
from astro_engine.dasha import compute_vimshottari_dasha
from astro_engine.nakshatra import compute_nakshatra
from astro_engine.shadbala import compute_shadbala
from astro_engine.state import (
    AstroState,
    BirthInput,
    ChartState,
    ComputationProvenance,
    PlanetaryStateEntry,
)
from astro_engine.vargas import VargaType, compute_all_vargas


class AstroStateBuilder:
    """Builds a complete AstroState from input + convention."""

    def __init__(self, engine: AstronomyEngine) -> None:
        self._engine = engine

    def build(
        self,
        birth_input: BirthInput,
        convention: ConventionProfile,
        transit_datetime: Optional[datetime] = None,
    ) -> AstroState:
        """
        Compute a full AstroState.

        Computes:
        - All planetary positions with nakshatra
        - Chart (ascendant + house cusps)
        - Varga positions for all planets
        - Vimshottari Dasha periods
        - Shadbala strengths
        - Ashtakavarga tables
        - Full provenance
        """
        jd = datetime_to_jd(birth_input.datetime_utc)
        ayanamsa_value = self._engine.get_ayanamsa(jd, convention)

        # --- Planets ---
        planet_positions = self._engine.compute_all_planets(jd, convention)
        planet_entries: list[PlanetaryStateEntry] = []

        for planet, pos in planet_positions.items():
            nak = compute_nakshatra(pos.longitude)
            planet_entries.append(
                PlanetaryStateEntry(
                    planet=PLANET_NAMES.get(planet, str(planet)),
                    longitude=pos.longitude,
                    latitude=pos.latitude,
                    speed=pos.speed_longitude,
                    is_retrograde=pos.is_retrograde,
                    sign_index=pos.sign_index,
                    sign_name=pos.sign_name,
                    degrees_in_sign=pos.degrees_in_sign,
                    nakshatra_name=nak.nakshatra_name,
                    nakshatra_index=nak.nakshatra_index,
                    pada=nak.pada,
                    nakshatra_lord=nak.nakshatra_lord,
                )
            )

        # --- Chart ---
        ascendant = self._engine.compute_ascendant(
            jd, birth_input.latitude, birth_input.longitude, convention,
        )
        house_cusps = self._engine.compute_houses(
            jd, birth_input.latitude, birth_input.longitude, convention,
        )
        asc_sign_idx, asc_sign_name, _ = longitude_to_sign(ascendant)
        asc_nak = compute_nakshatra(ascendant)

        chart = ChartState(
            ascendant_longitude=ascendant,
            ascendant_sign_index=asc_sign_idx,
            ascendant_sign_name=asc_sign_name,
            ascendant_nakshatra=asc_nak.nakshatra_name,
            house_cusps=house_cusps,
        )

        # --- Vargas ---
        vargas_data: dict[str, dict[str, dict[str, object]]] = {}
        for planet, pos in planet_positions.items():
            planet_name = PLANET_NAMES.get(planet, str(planet))
            planet_vargas: dict[str, dict[str, object]] = {}
            for varga_type, varga_pos in compute_all_vargas(pos.longitude).items():
                planet_vargas[f"D{varga_type.value}"] = {
                    "sign_index": varga_pos.sign_index,
                    "sign_name": varga_pos.sign_name,
                    "degrees_in_sign": round(varga_pos.degrees_in_sign, 4),
                }
            vargas_data[planet_name] = planet_vargas

        # --- Dasha ---
        moon_pos = planet_positions.get(Planet.MOON)
        dasha_data = None
        if moon_pos:
            dasha_state = compute_vimshottari_dasha(
                moon_longitude=moon_pos.longitude,
                birth_datetime=birth_input.datetime_utc,
                compute_antar=True,
                compute_pratyantar=False,  # Skip pratyantar for performance
            )
            # Serialize dasha to dict for storage
            maha_list = []
            for md in dasha_state.maha_dashas:
                antar_list = []
                for ad in md.sub_periods:
                    antar_list.append({
                        "lord": ad.lord,
                        "start": ad.start.isoformat(),
                        "end": ad.end.isoformat(),
                        "duration_days": round(ad.duration_days, 2),
                    })
                maha_list.append({
                    "lord": md.lord,
                    "start": md.start.isoformat(),
                    "end": md.end.isoformat(),
                    "duration_days": round(md.duration_days, 2),
                    "antar_dashas": antar_list,
                })
            dasha_data = {
                "system": "vimshottari",
                "moon_nakshatra": dasha_state.nakshatra_name,
                "nakshatra_lord": dasha_state.nakshatra_lord,
                "balance": round(dasha_state.nakshatra_balance, 6),
                "maha_dashas": maha_list,
            }

        # --- Shadbala ---
        strengths_data: dict[str, dict[str, float]] = {}
        shadbala_planets = [
            Planet.SUN, Planet.MOON, Planet.MARS,
            Planet.MERCURY, Planet.JUPITER, Planet.VENUS, Planet.SATURN,
        ]
        for planet in shadbala_planets:
            pos = planet_positions.get(planet)
            if pos:
                sb = compute_shadbala(planet, pos, ascendant)
                strengths_data[PLANET_NAMES[planet]] = {
                    "uchcha_bala": round(sb.uchcha_bala, 2),
                    "dig_bala": round(sb.dig_bala, 2),
                    "naisargika_bala": round(sb.naisargika_bala, 2),
                    "cheshta_bala": round(sb.cheshta_bala, 2),
                    "kala_bala": round(sb.kala_bala_simplified, 2),
                    "drik_bala": round(sb.drik_bala_simplified, 2),
                    "total_shashtiamsas": round(sb.total_shadbala, 2),
                    "total_rupas": round(sb.total_rupas, 4),
                }

        # --- Ashtakavarga ---
        planet_signs: dict[str, int] = {}
        for planet, pos in planet_positions.items():
            name = PLANET_NAMES.get(planet, str(planet))
            if name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
                planet_signs[name] = pos.sign_index
        ashtakavarga_result = compute_ashtakavarga(planet_signs, asc_sign_idx)
        ashtakavarga_data = {
            "bav": ashtakavarga_result.bav,
            "sav": ashtakavarga_result.sav,
            "total_bindus": ashtakavarga_result.total_bindus,
        }

        # --- Transit (Gochara) ---
        transit_data: Optional[dict[str, Any]] = None
        if transit_datetime is not None:
            t_jd = datetime_to_jd(transit_datetime)
            t_planets = self._engine.compute_all_planets(t_jd, convention)
            t_entries = []
            for planet, pos in t_planets.items():
                t_nak = compute_nakshatra(pos.longitude)
                t_entries.append({
                    "planet": PLANET_NAMES.get(planet, str(planet)),
                    "longitude": round(pos.longitude, 4),
                    "is_retrograde": pos.is_retrograde,
                    "sign_index": pos.sign_index,
                    "sign_name": pos.sign_name,
                    "nakshatra_name": t_nak.nakshatra_name,
                    "nakshatra_lord": t_nak.nakshatra_lord,
                })
            transit_data = {
                "datetime_utc": transit_datetime.isoformat(),
                "planets": t_entries,
            }

        # --- Provenance ---
        provenance = ComputationProvenance(
            engine_version=__version__,
            computed_at=datetime.now(timezone.utc),
            ephemeris_type="moshier" if not self._engine._ephemeris_path else "swiss",
            ayanamsa_value=ayanamsa_value,
            julian_day=jd,
        )

        return AstroState(
            state_id=str(uuid.uuid4()),
            input=birth_input,
            convention=convention,
            planets=planet_entries,
            chart=chart,
            vargas=vargas_data,
            dashas=dasha_data,
            strengths=strengths_data,
            ashtakavarga=ashtakavarga_data,
            transit=transit_data,
            provenance=provenance,
        )
