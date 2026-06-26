"""Tests for render.py — covers paths missed by the main test suite."""

from __future__ import annotations

from unittest.mock import MagicMock

from skillspector_quality.quality.models import CategoryScore, QualityReport
from skillspector_quality.quality.render import (
    _quality_status,
    _score_color,
    quality_json_dict,
    quality_markdown_section,
    quality_sarif_properties,
    unified_terminal_text,
)


def _report(score: int, *, notes: str | None = None) -> QualityReport:
    cat = CategoryScore(
        name="Metadata & Discovery",
        earned=score // 10,
        max=10,
        items=[(score // 10, 10, "test label")],
        notes=notes,
        kind="frontmatter",
    )
    return QualityReport(score=score, categories=[cat])


# ── _score_color ─────────────────────────────────────────────────────────────


def test_score_color_green() -> None:
    assert _score_color(80) == "green"


def test_score_color_yellow() -> None:
    assert _score_color(55) == "yellow"


def test_score_color_red() -> None:
    assert _score_color(30) == "red"


def test_score_color_boundary_70() -> None:
    assert _score_color(70) == "green"


def test_score_color_boundary_40() -> None:
    assert _score_color(40) == "yellow"


# ── _quality_status ───────────────────────────────────────────────────────────


def test_quality_status_excellent() -> None:
    sev, _ = _quality_status(90)
    assert sev == "EXCELLENT"


def test_quality_status_good() -> None:
    sev, _ = _quality_status(72)
    assert sev == "GOOD"


def test_quality_status_fair() -> None:
    sev, _ = _quality_status(60)
    assert sev == "FAIR"


def test_quality_status_critical() -> None:
    sev, _ = _quality_status(10)
    assert sev == "CRITICAL"


# ── unified_terminal_text ─────────────────────────────────────────────────────


def test_terminal_text_no_findings() -> None:
    report = _report(80)
    text = unified_terminal_text({"risk_score": 0, "filtered_findings": []}, report)
    assert "No security issues detected" in text
    assert "Quality Dimensions" in text


def test_terminal_text_with_components() -> None:
    report = _report(75)
    comp = {"path": "SKILL.md", "type": "markdown", "lines": 42, "executable": False}
    result = {
        "risk_score": 0,
        "filtered_findings": [],
        "component_metadata": [comp],
    }
    text = unified_terminal_text(result, report)
    assert "Components" in text
    assert "SKILL.md" in text


def test_terminal_text_with_findings() -> None:
    report = _report(60)
    finding = MagicMock()
    finding.severity = "HIGH"
    finding.rule_id = "TEST001"
    finding.message = "Test finding"
    finding.file = "SKILL.md"
    finding.start_line = 10
    finding.confidence = 0.9
    finding.remediation = "Fix it."
    result = {
        "risk_score": 80,
        "risk_severity": "HIGH",
        "filtered_findings": [finding],
    }
    text = unified_terminal_text(result, report)
    assert "TEST001" in text
    assert "Fix it." in text


def test_terminal_text_with_notes() -> None:
    report = _report(65, notes="Add more examples.")
    text = unified_terminal_text({"risk_score": 0, "filtered_findings": []}, report)
    assert "Add more examples." in text


def test_terminal_text_finding_no_remediation() -> None:
    report = _report(50)
    finding = MagicMock()
    finding.severity = "LOW"
    finding.rule_id = "T002"
    finding.message = "Minor issue"
    finding.file = "x.md"
    finding.start_line = 1
    finding.confidence = 0.5
    finding.remediation = ""
    result = {"risk_score": 10, "filtered_findings": [finding]}
    text = unified_terminal_text(result, report)
    assert "T002" in text


# ── quality_markdown_section ──────────────────────────────────────────────────


def test_markdown_section_basic() -> None:
    report = _report(80)
    md = quality_markdown_section(report)
    assert "## Quality Assessment" in md
    assert "80/100" in md


def test_markdown_section_with_notes() -> None:
    report = _report(55, notes="Improve readability.")
    md = quality_markdown_section(report)
    assert "### Suggestions" in md
    assert "Improve readability." in md


def test_markdown_section_no_notes() -> None:
    report = _report(90)
    md = quality_markdown_section(report)
    assert "### Suggestions" not in md


# ── quality_json_dict / quality_sarif_properties ──────────────────────────────


def test_json_dict_has_caveat() -> None:
    report = _report(70)
    d = quality_json_dict(report)
    assert "caveat" in d
    assert "score" in d


def test_sarif_properties_structure() -> None:
    report = _report(82)
    props = quality_sarif_properties(report)
    assert props["score"] == 82
    assert "categories" in props
    assert "Metadata & Discovery" in props["categories"]
