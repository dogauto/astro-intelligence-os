"""Tests for the explicit source and wheel package boundary."""

from __future__ import annotations

import os
import tomllib
import zipfile
from pathlib import Path

import pytest

ENGINE_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PACKAGE_ROOTS = {"astro_cli", "astro_engine"}


def _package_discovery_config() -> dict[str, object]:
    with (ENGINE_ROOT / "pyproject.toml").open("rb") as pyproject:
        document = tomllib.load(pyproject)
    return document["tool"]["setuptools"]["packages"]["find"]


def test_package_discovery_is_an_explicit_allow_list() -> None:
    config = _package_discovery_config()

    assert config["where"] == ["src"]
    assert config["namespaces"] is False
    assert set(config["include"]) == {
        "astro_engine",
        "astro_engine.*",
        "astro_cli",
        "astro_cli.*",
    }
    assert set(config["exclude"]) == {
        "governance",
        "governance.*",
        "astro_engine.governance",
        "astro_engine.governance.*",
    }


def test_source_package_roots_match_the_public_boundary() -> None:
    source_roots = {
        package.name
        for package in (ENGINE_ROOT / "src").iterdir()
        if (package / "__init__.py").is_file()
    }

    assert source_roots == EXPECTED_PACKAGE_ROOTS


def test_built_wheel_contains_only_the_public_package_roots() -> None:
    wheel_path = os.environ.get("ASTRO_WHEEL")
    if wheel_path is None:
        pytest.skip("ASTRO_WHEEL is provided by the CI wheel-boundary inspection step")

    with zipfile.ZipFile(wheel_path) as wheel:
        package_members = [
            name
            for name in wheel.namelist()
            if ".dist-info/" not in name
        ]

    package_roots = {name.split("/", maxsplit=1)[0] for name in package_members}
    assert package_roots == EXPECTED_PACKAGE_ROOTS
    assert not any("governance" in name.split("/") for name in package_members)
