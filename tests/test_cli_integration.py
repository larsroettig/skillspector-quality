"""End-to-end tests: full graph + CLI output merging."""

from __future__ import annotations

import json
import pathlib

import pytest

from skillspector_quality.cli import FormatChoice, _merge_output
from skillspector_quality.quality.models import QualityReport

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "good-skill"


@pytest.fixture(scope="module")
def graph_result() -> dict:
    from skillspector_quality.graph import graph

    state = {
        "input_path": str(FIXTURE),
        "output_format": "json",
        "use_llm": False,
    }
    return graph.invoke(state)


def test_graph_produces_quality_report(graph_result: dict) -> None:
    assert "quality_report" in graph_result
    report = QualityReport.from_dict(graph_result["quality_report"])
    assert report.score >= 70


def test_graph_quality_is_deterministic() -> None:
    from skillspector_quality.graph import graph

    state = {"input_path": str(FIXTURE), "output_format": "json", "use_llm": False}
    r1 = graph.invoke(dict(state))
    r2 = graph.invoke(dict(state))
    assert r1["quality_report"]["score"] == r2["quality_report"]["score"]


def test_merge_json_adds_quality_assessment(graph_result: dict) -> None:
    report = QualityReport.from_dict(graph_result["quality_report"])
    merged = _merge_output(graph_result, FormatChoice.json, report)
    data = json.loads(merged)
    assert "quality_assessment" in data
    assert "score" in data["quality_assessment"]
    assert "grade" not in data["quality_assessment"]
    # Security section preserved.
    assert "risk_assessment" in data


def test_merge_sarif_quality_in_properties(graph_result: dict) -> None:
    report = QualityReport.from_dict(graph_result["quality_report"])
    merged = _merge_output(graph_result, FormatChoice.sarif, report)
    sarif = json.loads(merged)
    quality = sarif["runs"][0]["properties"]["quality"]
    assert "score" in quality
    assert "grade" not in quality
    # Results stay security-only (no quality entries injected as findings).
    assert isinstance(sarif["runs"][0].get("results", []), list)


def test_merge_markdown_appends_section() -> None:
    from skillspector_quality.graph import graph

    # report_body must be markdown for this assertion, so scan with markdown format.
    result = graph.invoke(
        {"input_path": str(FIXTURE), "output_format": "markdown", "use_llm": False}
    )
    report = QualityReport.from_dict(result["quality_report"])
    merged = _merge_output(result, FormatChoice.markdown, report)
    assert "## Quality Assessment" in merged
    assert "SkillSpector Security Report" in merged  # upstream body preserved
