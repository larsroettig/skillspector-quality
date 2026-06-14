"""Tests for the quality_scorer node and its no-LLM guarantees."""

from __future__ import annotations

from skillspector_quality.nodes.quality_scorer import quality_scorer
from skillspector_quality.quality import score_quality
from skillspector_quality.quality.models import QualityReport

_SKILL = "---\ndescription: d\nwhen_to_use: use it when needed here\n---\n# Body\n- one\n- two\n"


def test_node_returns_quality_report_no_llm() -> None:
    state = {"file_cache": {"SKILL.md": _SKILL}, "use_llm": False}
    out = quality_scorer(state)
    assert "quality_report" in out
    report = QualityReport.from_dict(out["quality_report"])
    assert 0 <= report.score <= 100
    # No LLM -> no notes anywhere.
    assert all(c.notes is None for c in report.categories)


def test_node_matches_engine_no_llm() -> None:
    state = {"file_cache": {"SKILL.md": _SKILL}, "use_llm": False}
    out = quality_scorer(state)
    direct = score_quality({"SKILL.md": _SKILL})
    assert out["quality_report"]["score"] == direct.score


def test_node_empty_file_cache() -> None:
    out = quality_scorer({"file_cache": {}, "use_llm": False})
    report = QualityReport.from_dict(out["quality_report"])
    assert report.score < 40  # nothing meaningful in cache → low score


def test_llm_failure_degrades_silently(monkeypatch) -> None:
    # Force commentary to raise; node must still return the deterministic report.
    import skillspector_quality.quality.commentary as commentary

    def _boom(*_a, **_k):
        raise RuntimeError("no network")

    monkeypatch.setattr(commentary, "add_notes", _boom)
    state = {"file_cache": {"SKILL.md": _SKILL}, "use_llm": True}
    out = quality_scorer(state)
    report = QualityReport.from_dict(out["quality_report"])
    assert report.score == score_quality({"SKILL.md": _SKILL}).score
    assert all(c.notes is None for c in report.categories)
