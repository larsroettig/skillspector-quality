"""CLI tests — exercises the scan command via Typer's CliRunner."""

from __future__ import annotations

import pathlib

import pytest
from typer.testing import CliRunner

from skillspector_quality.cli import app

RUNNER = CliRunner()
GOOD_FIXTURE = str(pathlib.Path(__file__).parent / "fixtures" / "good-skill")


def test_scan_help_exits_zero() -> None:
    result = RUNNER.invoke(app, ["scan", "--help"])
    assert result.exit_code == 0
    assert "input-path" in result.output.lower() or "input_path" in result.output.lower()


def test_scan_no_llm_exits_zero() -> None:
    result = RUNNER.invoke(app, ["scan", GOOD_FIXTURE, "--no-llm"])
    assert result.exit_code == 0, result.output


def test_scan_json_format() -> None:
    import json

    result = RUNNER.invoke(app, ["scan", GOOD_FIXTURE, "--no-llm", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "quality_assessment" in data


def test_scan_markdown_format() -> None:
    result = RUNNER.invoke(app, ["scan", GOOD_FIXTURE, "--no-llm", "--format", "markdown"])
    assert result.exit_code == 0, result.output
    assert "## Quality Assessment" in result.output


def test_scan_min_score_gate_fails_when_below_threshold() -> None:
    result = RUNNER.invoke(app, ["scan", GOOD_FIXTURE, "--no-llm", "--min-score", "99"])
    assert result.exit_code == 1


def test_scan_min_score_gate_passes_when_above_threshold() -> None:
    result = RUNNER.invoke(app, ["scan", GOOD_FIXTURE, "--no-llm", "--min-score", "1"])
    assert result.exit_code == 0, result.output


def test_scan_nonexistent_path_exits_two() -> None:
    result = RUNNER.invoke(app, ["scan", "/does/not/exist", "--no-llm"])
    assert result.exit_code == 2


@pytest.mark.integration
def test_scan_output_file(tmp_path: pathlib.Path) -> None:
    out = tmp_path / "report.json"
    result = RUNNER.invoke(
        app, ["scan", GOOD_FIXTURE, "--no-llm", "--format", "json", "--output", str(out)]
    )
    assert result.exit_code == 0
    assert out.exists()
    import json

    data = json.loads(out.read_text())
    assert "quality_assessment" in data
