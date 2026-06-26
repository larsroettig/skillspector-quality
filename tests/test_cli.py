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


def test_scan_verbose_flag() -> None:
    result = RUNNER.invoke(app, ["scan", GOOD_FIXTURE, "--no-llm", "--verbose"])
    assert result.exit_code == 0, result.output


def test_scan_output_file_non_integration(tmp_path: pathlib.Path) -> None:
    import json

    out = tmp_path / "report.json"
    result = RUNNER.invoke(
        app, ["scan", GOOD_FIXTURE, "--no-llm", "--format", "json", "--output", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    data = json.loads(out.read_text())
    assert "quality_assessment" in data


def test_scan_high_risk_score_exits_one(tmp_path: pathlib.Path) -> None:
    """When the stub returns risk_score > 50 the CLI exits with code 1."""
    from unittest.mock import patch

    high_risk_state = {
        "quality_report": {"score": 80, "categories": []},
        "risk_score": 99,
        "report_body": "{}",
    }
    with patch("skillspector_quality.cli.graph") as mock_graph:
        mock_graph.invoke.return_value = high_risk_state
        result = RUNNER.invoke(app, ["scan", GOOD_FIXTURE, "--no-llm"])
    assert result.exit_code == 1


def test_scan_merge_json_invalid_report_body(tmp_path: pathlib.Path) -> None:
    """Invalid JSON in report_body should not crash — falls back to empty dict."""
    from unittest.mock import patch

    broken_state = {
        "quality_report": {"score": 70, "categories": []},
        "risk_score": 0,
        "report_body": "NOT_JSON",
    }
    with patch("skillspector_quality.cli.graph") as mock_graph:
        mock_graph.invoke.return_value = broken_state
        result = RUNNER.invoke(app, ["scan", GOOD_FIXTURE, "--no-llm", "--format", "json"])
    assert result.exit_code == 0, result.output


def test_scan_sarif_format() -> None:
    result = RUNNER.invoke(app, ["scan", GOOD_FIXTURE, "--no-llm", "--format", "sarif"])
    assert result.exit_code == 0, result.output


def test_scan_cleans_up_temp_dir() -> None:
    """temp_dir_for_cleanup inside tempfile.gettempdir() is removed after the scan."""
    import os
    import tempfile
    from unittest.mock import patch

    temp_dir = tempfile.mkdtemp()
    state = {
        "quality_report": {"score": 60, "categories": []},
        "risk_score": 0,
        "report_body": "{}",
        "temp_dir_for_cleanup": temp_dir,
    }
    with patch("skillspector_quality.cli.graph") as mock_graph:
        mock_graph.invoke.return_value = state
        RUNNER.invoke(app, ["scan", GOOD_FIXTURE, "--no-llm"])
    assert not os.path.exists(temp_dir)


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
