"""Minimal CLI process-level smoke tests."""

from __future__ import annotations

import subprocess
import sys
from shutil import which

import pytest


def _run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "astro_cli", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_version_succeeds() -> None:
    result = _run_cli("--version")

    assert result.returncode == 0
    assert result.stdout.strip() == "astro 0.1.0"
    assert result.stderr == ""


def test_cli_rejects_unknown_commands_without_a_traceback() -> None:
    result = _run_cli("unknown-command")

    assert result.returncode == 2
    assert "invalid choice" in result.stderr
    assert "Traceback" not in result.stderr


def test_installed_console_script_version_succeeds() -> None:
    executable = which("astro")
    if executable is None:
        pytest.skip("astro console script is not installed in this environment")

    result = subprocess.run(
        [executable, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "astro 0.1.0"
    assert result.stderr == ""
