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

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

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
from astro_engine.provenance import (
    AstronomyComputationNode,
    AstroStateNode,
    BirthInputNode,
    ConventionProfileNode,
    ProvenanceRegistry,
)
from astro_engine.shadbala import compute_shadbala
from astro_engine.state import (
    AstroState,
    BirthInput,
    ChartState,
    ComputationProvenance,
    PlanetaryStateEntry,
)
from astro_engine.vargas import compute_all_vargas


class AstroStateBuilder:
    """Builds a complete AstroState from input + convention."""

    def __init__(self, engine: AstronomyEngine) -> None:
        self._engine = engine

    def build(
        self,
        birth_input: BirthInput,
        convention: ConventionProfile,
        transit_datetime: datetime | None = None,
        provenance_registry: ProvenanceRegistry | None = None,
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
            p_pos = planet_positions.get(planet)
            if p_pos is None:
                continue
            sb = compute_shadbala(planet, p_pos, ascendant)
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
        transit_data: dict[str, Any] | None = None
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

        # Derive state_id deterministically from the computed content so that
        # two identical inputs produce an identical state_id (and therefore
        # identical downstream provenance hashes). The provenance block is
        # excluded because it contains non-deterministic metadata (computed_at).
        state_payload = {
            "engine_version": __version__,
            "input": birth_input.model_dump(mode="json"),
            "convention": convention.model_dump(mode="json"),
            "planets": [p.model_dump(mode="json") for p in planet_entries],
            "chart": chart.model_dump(mode="json") if chart else None,
            "vargas": vargas_data,
            "dashas": dasha_data,
            "strengths": strengths_data,
            "ashtakavarga": ashtakavarga_data,
            "transit": transit_data,
        }
        state_id = hashlib.sha256(
            json.dumps(state_payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        # --- Provenance ---
        astronomy_node_id = None
        astrostate_node_id = None
        if provenance_registry:
            birth_node = BirthInputNode(
                version="1.0",
                datetime_utc=birth_input.datetime_utc.isoformat(),
                latitude=birth_input.latitude,
                longitude=birth_input.longitude,
            )
            birth_node.content_hash = birth_node.compute_hash(birth_node._content_dict())
            provenance_registry.add_node(birth_node)

            conv_node = ConventionProfileNode(
                version="1.0",
                convention_id=convention.id,
                ayanamsa=convention.ayanamsa.value,
                house_system=convention.house_system.value,
            )
            conv_node.content_hash = conv_node.compute_hash(conv_node._content_dict())
            provenance_registry.add_node(conv_node)

            astronomy_node = AstronomyComputationNode(
                version=__version__,
                parent_ids=[birth_node.node_id, conv_node.node_id],
                engine_version=__version__,
                ephemeris_source="moshier" if not self._engine._ephemeris_path else "swiss",
                ephemeris_version="unknown",
            )
            astronomy_node.content_hash = astronomy_node.compute_hash(astronomy_node.model_dump(exclude={"node_id", "timestamp", "content_hash"}))
            provenance_registry.add_node(astronomy_node)
            astronomy_node_id = astronomy_node.node_id

            # Register AstroState node — must happen BEFORE ComputationProvenance
            # so that the state_id and node_id are both known.
            astrostate_node = AstroStateNode(
                version=__version__,
                state_id=state_id,
                engine_version=__version__,
                ephemeris_type="moshier" if not self._engine._ephemeris_path else "swiss",
                ayanamsa_value=ayanamsa_value,
                julian_day=jd,
                parent_ids=[astronomy_node_id] if astronomy_node_id else [],
            )
            astrostate_node.content_hash = astrostate_node.compute_hash(
                astrostate_node.model_dump(exclude={"node_id", "timestamp", "content_hash"})
            )
            provenance_registry.add_node(astrostate_node)
            astrostate_node_id = astrostate_node.node_id

        provenance = ComputationProvenance(
            engine_version=__version__,
            computed_at=datetime.now(UTC),
            ephemeris_type="moshier" if not self._engine._ephemeris_path else "swiss",
            ayanamsa_value=ayanamsa_value,
            julian_day=jd,
            provenance_node_id=astronomy_node_id,
            astrostate_node_id=astrostate_node_id,
        )

        return AstroState(
            state_id=state_id,
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
