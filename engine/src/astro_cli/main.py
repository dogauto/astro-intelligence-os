"""
Astro CLI — Main entry point for the command-line interface.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from typing import Any

from astro_engine.astronomy import AstronomyEngine
from astro_engine.builder import AstroStateBuilder
from astro_engine.conventions import PARASHARI_LAHIRI
from astro_engine.methods import MethodRun, QuestionContext
from astro_engine.methods.gochara_transit import TransitCareerMethod
from astro_engine.methods.question_spec import question_context_to_spec
from astro_engine.methods.vimshottari_career import VimshottariCareerMethod
from astro_engine.provenance import ProvenanceRegistry
from astro_engine.state import BirthInput


def cmd_compute(args: dict[str, Any]) -> None:
    """Compute and display an astrological chart."""
    birth_str = args["birth"]
    location = args.get("location")
    include_transit = args.get("transit", False)
    output_format = args.get("output", "text")

    # Parse birth datetime
    try:
        birth_dt = datetime.fromisoformat(birth_str)
        if birth_dt.tzinfo is None:
            birth_dt = birth_dt.replace(tzinfo=UTC)
    except ValueError as e:
        print(f"Error: Invalid birth datetime format: {e}", file=sys.stderr)
        sys.exit(1)

    # Resolve timezone if location provided
    timezone_name = "UTC"
    latitude = 0.0
    longitude = 0.0

    if location:
        try:
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder()
            if "," in location:
                parts = location.split(",")
                latitude = float(parts[0])
                longitude = float(parts[1])
                tz_result = tf.timezone_at(lat=latitude, lng=longitude)
                if tz_result:
                    timezone_name = tz_result
        except ImportError:
            print("Warning: timezonefinder not installed. Using UTC.")

    # Build birth input
    birth_input = BirthInput(
        datetime_utc=birth_dt,
        timezone_name=timezone_name,
        latitude=latitude,
        longitude=longitude,
    )

    # Compute state
    engine = AstronomyEngine()
    builder = AstroStateBuilder(engine)

    transit_dt = None
    if include_transit:
        transit_dt = datetime.now(UTC)

    registry = ProvenanceRegistry() if args.get("provenance", False) else None
    state = builder.build(
        birth_input,
        PARASHARI_LAHIRI,
        transit_datetime=transit_dt,
        provenance_registry=registry,
    )

    # Output
    if output_format == "json":
        output = {
            "state_id": state.state_id,
            "input": state.input.model_dump(mode="json"),
            "convention": state.convention.model_dump(mode="json"),
            "planets": [p.model_dump(mode="json") for p in state.planets],
            "chart": state.chart.model_dump(mode="json") if state.chart else None,
            "vargas_available": state.vargas is not None,
            "dashas_available": state.dashas is not None,
            "strengths_available": state.strengths is not None,
            "ashtakavarga_available": state.ashtakavarga is not None,
            "transit_available": state.transit is not None,
            "provenance": state.provenance.model_dump(mode="json"),
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        # Text output
        print(f"\n{'='*60}")
        print("  ASTROLOGICAL CHART")
        print(f"{'='*60}")
        print(f"\nState ID: {state.state_id}")
        print("\nBirth Data:")
        print(f"  DateTime (UTC): {state.input.datetime_utc.isoformat()}")
        print(f"  Timezone: {state.input.timezone_name}")
        print(f"  Location: ({state.input.latitude}, {state.input.longitude})")
        print(f"\nConvention: {state.convention.name}")
        print(f"Ayanamsa: {state.provenance.ayanamsa_value:.6f}°")

        print(f"\n{'Planets':*^60}")
        print(f"{'Planet':<10} {'Longitude':>10} {'Sign':>10} {'Nakshatra':>15} {'Retro':>6}")
        print("-" * 60)
        for p in state.planets:
            retro = "Y" if p.is_retrograde else " "
            print(f"{p.planet:<10} {p.longitude:>9.4f}° "
                    f"{p.sign_name:>10} {p.nakshatra_name or '':>15} {retro:>6}")

        if state.chart:
            print(f"\n{'Chart':*^60}")
            sign = state.chart.ascendant_sign_name
            lon = f"{state.chart.ascendant_longitude:.4f}"
            print(f"  Ascendant: {sign} ({lon}°)")
            print(f"  Houses: {len(state.chart.house_cusps)} cusps computed")

        if state.transit:
            print(f"\n{'Transit':*^60}")
            print(f"  Computed for: {state.transit['datetime_utc']}")
            print(f"  Planets: {len(state.transit['planets'])} positions")

        print(f"\n{'Data Availability':*^60}")
        print(f"  Vargas (D1-D60): {'Y' if state.vargas else 'N'}")
        print(f"  Dashas: {'Y' if state.dashas else 'N'}")
        print(f"  Shadbala: {'Y' if state.strengths else 'N'}")
        print(f"  Ashtakavarga: {'Y' if state.ashtakavarga else 'N'}")
        print(f"  Transit: {'Y' if state.transit else 'N'}")


def cmd_career(args: dict[str, Any]) -> None:
    """Run career timing analysis using Vimshottari Dasha method."""
    state_input = args.get("state")
    horizon_years = args.get("horizon", 20)

    if not state_input:
        birth_str = args.get("birth")
        if not birth_str:
            print("Error: Either --state or --birth is required", file=sys.stderr)
            sys.exit(1)

        birth_dt = datetime.fromisoformat(birth_str)
        if birth_dt.tzinfo is None:
            birth_dt = birth_dt.replace(tzinfo=UTC)

        birth_input = BirthInput(
            datetime_utc=birth_dt,
            timezone_name=args.get("timezone", "UTC"),
            latitude=args.get("lat", 0.0) or 0.0,
            longitude=args.get("lng", 0.0) or 0.0,
        )

        engine = AstronomyEngine()
        builder = AstroStateBuilder(engine)
        state = builder.build(birth_input, PARASHARI_LAHIRI)
    else:
        # Load state from JSON file
        with open(state_input) as f:
            json.load(f)
        # Reconstruct state (simplified - would need proper deserialization in production)
        print("Note: Loading state from JSON file is not yet fully implemented.", file=sys.stderr)
        sys.exit(1)

    question = question_context_to_spec(
        QuestionContext(
            domain="career",
            task="event_timing",
            time_horizon_years=float(horizon_years),
        )
    )

    method = VimshottariCareerMethod()
    method_run = method.run(state, question)

    # Output results
    output_format = args.get("output", "text")
    if output_format == "json":
        output = {
            "method_id": method_run.method_id,
            "method_version": method_run.method_version,
            "input_state_id": method_run.input_state_id,
            "question": method_run.question.model_dump(mode="json"),
            "rules_evaluated": method_run.rules_evaluated,
            "calculations_used": method_run.calculations_used,
            "predictions": [p.model_dump(mode="json") for p in method_run.predictions],
            "assumptions": method_run.assumptions,
            "warnings": method_run.warnings,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        _print_career_results(method_run)


def _print_career_results(method_run: MethodRun) -> None:
    """Print career method results in human-readable format."""
    print(f"\n{'='*60}")
    print("  CAREER TIMING ANALYSIS")
    print(f"  Method: {method_run.method_id}")
    print(f"  Version: {method_run.method_version}")
    print(f"{'='*60}")

    print(f"\nRules Evaluated: {len(method_run.rules_evaluated)}")
    print(f"Calculations Used: {', '.join(method_run.calculations_used)}")

    if method_run.predictions:
        print(f"\n{'Predictions':*^60}")
        for i, pred in enumerate(method_run.predictions, 1):
            print(f"\n  {i}. {pred.event}")
            print(f"     Direction: {pred.direction.value}")
            if pred.magnitude:
                print(f"     Magnitude: {pred.magnitude:.2f}")
            print(f"     Period: {pred.duration_description}")
            if pred.time_window_start:
                print(f"     Start: {pred.time_window_start.isoformat()}")
            if pred.time_window_end:
                print(f"     End: {pred.time_window_end.isoformat()}")
            if pred.conditions:
                print(f"     Conditions: {'; '.join(pred.conditions)}")
            if pred.supporting_evidence:
                print(f"     Evidence: {'; '.join(pred.supporting_evidence[:3])}")
    else:
        print("\n  No predictions generated (method may lack required data).")

    if method_run.warnings:
        print(f"\n{'Warnings':*^60}")
        for w in method_run.warnings:
            print(f"  - {w}")

    print(f"\n{'Assumptions':*^60}")
    for a in method_run.assumptions:
        print(f"  - {a}")
    print()


def cmd_transit(args: dict[str, Any]) -> None:
    """Run transit-based career analysis."""
    state_input = args.get("state")

    if not state_input:
        birth_str = args.get("birth")
        if not birth_str:
            print("Error: Either --state or --birth is required", file=sys.stderr)
            sys.exit(1)

        birth_dt = datetime.fromisoformat(birth_str)
        if birth_dt.tzinfo is None:
            birth_dt = birth_dt.replace(tzinfo=UTC)

        birth_input = BirthInput(
            datetime_utc=birth_dt,
            timezone_name=args.get("timezone", "UTC"),
            latitude=args.get("lat", 0.0) or 0.0,
            longitude=args.get("lng", 0.0) or 0.0,
        )

        engine = AstronomyEngine()
        builder = AstroStateBuilder(engine)
        state = builder.build(
            birth_input, PARASHARI_LAHIRI,
            transit_datetime=datetime.now(UTC),
        )
    else:
        print("Note: Loading state from JSON is not yet fully implemented.", file=sys.stderr)
        sys.exit(1)

    question = question_context_to_spec(
        QuestionContext(
            domain="career",
            task="event_timing",
        )
    )

    method = TransitCareerMethod()
    method_run = method.run(state, question)

    output_format = args.get("output", "text")
    if output_format == "json":
        output = {
            "method_id": method_run.method_id,
            "method_version": method_run.method_version,
            "predictions": [p.model_dump(mode="json") for p in method_run.predictions],
            "warnings": method_run.warnings,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(f"\n{'='*60}")
        print("  TRANSIT CAREER ANALYSIS")
        print(f"  Method: {method_run.method_id}")
        print(f"{'='*60}")

        if method_run.predictions:
            print(f"\n{'Predictions':*^60}")
            for i, pred in enumerate(method_run.predictions, 1):
                print(f"\n  {i}. {pred.event}")
                print(f"     Direction: {pred.direction.value}")
                if pred.magnitude:
                    print(f"     Magnitude: {pred.magnitude:.2f}")
                print(f"     {pred.duration_description}")
        else:
            print("\n  No transit predictions generated.")

        if method_run.warnings:
            print(f"\n{'Warnings':*^60}")
            for w in method_run.warnings:
                print(f"  - {w}")
    print()


def cmd_trace(args: dict[str, Any]) -> None:
    """Trace provenance of a prediction."""
    prediction_id = args["prediction_id"]
    print(f"Provenance tracing for prediction '{prediction_id}' requires")
    print("a persisted ProvenanceRegistry. This feature is planned for future phases.")
    print("\nNote: The current implementation uses an in-memory registry that")
    print("cannot be queried by ID after the process exits.")


def cmd_test(args: dict[str, Any]) -> None:
    """Run the test suite."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--tb=short"],
        cwd="/Users/avipattan/new gen astro agents /engine",
    )
    sys.exit(result.returncode)


def cmd_list_methods(args: dict[str, Any]) -> None:
    """List available methods."""
    print(f"\n{'='*60}")
    print("  AVAILABLE METHODS")
    print(f"{'='*60}")

    methods = [
        VimshottariCareerMethod(),
        TransitCareerMethod(),
    ]

    print(f"\n{'Method ID':<35} {'Name':<25}")
    print("-" * 60)
    for m in methods:
        print(f"{m.method_id:<35} {m.name:<25}")

    print(f"\n{'Tradition':<20} {'Maturity':<15} {'Domains':<30}")
    print("-" * 60)
    for m in methods:
        print(f"{m.tradition:<20} {m.maturity.value:<15} {', '.join(m.supported_domains):<30}")
    print()


def main() -> None:
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="astro",
        description="Astro Intelligence OS — Professional astrology computation engine",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # compute command
    compute_parser = subparsers.add_parser(
        "compute",
        help="Compute and display an astrological chart",
    )
    compute_parser.add_argument(
        "--birth", required=True,
        help="Birth datetime in ISO format (e.g., '1990-01-01T12:00:00+05:30')",
    )
    compute_parser.add_argument(
        "--location",
        help="Location as 'latitude,longitude' (e.g., '28.6139,77.2090')",
    )
    compute_parser.add_argument(
        "--transit", action="store_true",
        help="Include current transit positions",
    )
    compute_parser.add_argument(
        "--provenance", action="store_true",
        help="Enable provenance tracking",
    )
    compute_parser.add_argument(
        "--output", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )

    # career command
    career_parser = subparsers.add_parser(
        "career",
        help="Run Vimshottari Dasha career timing analysis",
    )
    career_parser.add_argument(
        "--state",
        help="Pre-computed AstroState JSON file path",
    )
    career_parser.add_argument(
        "--birth",
        help="Birth datetime in ISO format (used if --state not provided)",
    )
    career_parser.add_argument(
        "--timezone", default="UTC",
        help="Timezone name (default: UTC)",
    )
    career_parser.add_argument(
        "--lat", type=float, default=0.0,
        help="Latitude (default: 0.0)",
    )
    career_parser.add_argument(
        "--lng", type=float, default=0.0,
        help="Longitude (default: 0.0)",
    )
    career_parser.add_argument(
        "--horizon", type=int, default=20,
        help="Time horizon in years (default: 20)",
    )
    career_parser.add_argument(
        "--output", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )

    # transit command
    transit_parser = subparsers.add_parser(
        "transit",
        help="Run Gochara transit career analysis",
    )
    transit_parser.add_argument(
        "--state",
        help="Pre-computed AstroState JSON file path",
    )
    transit_parser.add_argument(
        "--birth",
        help="Birth datetime in ISO format (used if --state not provided)",
    )
    transit_parser.add_argument(
        "--timezone", default="UTC",
        help="Timezone name (default: UTC)",
    )
    transit_parser.add_argument(
        "--lat", type=float, default=0.0,
        help="Latitude (default: 0.0)",
    )
    transit_parser.add_argument(
        "--lng", type=float, default=0.0,
        help="Longitude (default: 0.0)",
    )
    transit_parser.add_argument(
        "--output", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )

    # trace command
    trace_parser = subparsers.add_parser(
        "trace",
        help="Trace provenance of a prediction",
    )
    trace_parser.add_argument(
        "prediction_id",
        help="Prediction node ID to trace",
    )

    # test command
    subparsers.add_parser(
        "test",
        help="Run the test suite",
    )

    # list-methods command
    subparsers.add_parser(
        "list-methods",
        help="List available methods",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Route to handlers
    commands = {
        "compute": cmd_compute,
        "career": cmd_career,
        "transit": cmd_transit,
        "trace": cmd_trace,
        "test": cmd_test,
        "list-methods": cmd_list_methods,
    }

    handler = commands.get(args.command)
    if handler:
        handler(vars(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
