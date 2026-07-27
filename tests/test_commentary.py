"""Tests for the optional LLM commentary layer.

``commentary`` is advisory: it attaches prose ``notes`` to weak categories and must never
touch a number. Every failure mode is supposed to degrade silently to "no notes", which is
exactly the kind of behaviour that rots unnoticed — a broken except branch looks identical
to a working one from the outside. These tests pin each path.
"""

from __future__ import annotations

import skillspector.llm_utils as llm_utils

from skillspector_quality.quality.commentary import (
    _build_prompt,
    _parse_notes,
    add_notes,
)
from skillspector_quality.quality.models import CategoryScore, QualityReport


def _report() -> QualityReport:
    return QualityReport(
        score=60,
        categories=[
            CategoryScore(
                name="Readability",
                earned=2,
                max=5,
                items=[(2, 5, "sentences too long")],
                kind="body",
            ),
            CategoryScore(
                name="Topic Coverage",
                earned=4,
                max=4,
                items=[(4, 4, "aligned")],
                kind="frontmatter",
            ),
        ],
        gate_violations=[],
    )


def _patch_llm(monkeypatch, *, available=True, response="{}", raises=None):
    monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (available, ""))

    def _chat(prompt, model=None):
        if raises is not None:
            raise raises
        return response

    monkeypatch.setattr(llm_utils, "chat_completion", _chat)


# --------------------------------------------------------------------------- #
# _build_prompt
# --------------------------------------------------------------------------- #


def test_build_prompt_lists_only_weak_categories() -> None:
    prompt = _build_prompt(_report())
    assert "Readability (2/5)" in prompt
    # A category at full marks has nothing to improve, so it must not be sent.
    assert "Topic Coverage" not in prompt


def test_build_prompt_includes_item_labels_and_json_instruction() -> None:
    prompt = _build_prompt(_report())
    assert "sentences too long" in prompt
    assert "JSON only" in prompt


# --------------------------------------------------------------------------- #
# _parse_notes
# --------------------------------------------------------------------------- #


def test_parse_notes_extracts_object_from_surrounding_prose() -> None:
    raw = 'Sure! Here you go:\n```json\n{"Readability": "Shorten sentences."}\n```'
    assert _parse_notes(raw) == {"Readability": "Shorten sentences."}


def test_parse_notes_returns_empty_without_an_object() -> None:
    assert _parse_notes("no json here") == {}


def test_parse_notes_returns_empty_on_malformed_json() -> None:
    assert _parse_notes('{"Readability": }') == {}


def test_parse_notes_rejects_non_object_json() -> None:
    assert _parse_notes("[1, 2, 3]") == {}


def test_parse_notes_coerces_scalars_and_drops_containers() -> None:
    raw = '{"a": "text", "b": 3, "c": 1.5, "d": ["list"], "e": {"k": "v"}}'
    assert _parse_notes(raw) == {"a": "text", "b": "3", "c": "1.5"}


# --------------------------------------------------------------------------- #
# add_notes
# --------------------------------------------------------------------------- #


def test_add_notes_attaches_notes_to_weak_category(monkeypatch) -> None:
    _patch_llm(monkeypatch, response='{"Readability": "Shorten sentences."}')
    report = _report()
    result = add_notes(report)

    assert result is report  # documented to mutate in place
    assert result.categories[0].notes == "Shorten sentences."


def test_add_notes_never_changes_the_score(monkeypatch) -> None:
    _patch_llm(monkeypatch, response='{"Readability": "Shorten sentences."}')
    report = _report()
    before = (report.score, [(c.earned, c.max) for c in report.categories])

    add_notes(report)

    assert (report.score, [(c.earned, c.max) for c in report.categories]) == before


def test_add_notes_ignores_names_that_match_no_category(monkeypatch) -> None:
    _patch_llm(monkeypatch, response='{"Nonexistent Category": "tip"}')
    report = add_notes(_report())
    assert all(c.notes is None for c in report.categories)


def test_add_notes_noop_when_llm_unavailable(monkeypatch) -> None:
    def _boom(prompt, model=None):
        raise AssertionError("must not call the model when unavailable")

    monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (False, "no key"))
    monkeypatch.setattr(llm_utils, "chat_completion", _boom)

    report = add_notes(_report())
    assert all(c.notes is None for c in report.categories)


def test_add_notes_noop_when_no_category_is_weak(monkeypatch) -> None:
    def _boom(prompt, model=None):
        raise AssertionError("must not call the model when nothing is weak")

    monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
    monkeypatch.setattr(llm_utils, "chat_completion", _boom)

    report = QualityReport(
        score=100,
        categories=[
            CategoryScore(name="Readability", earned=5, max=5, items=[(5, 5, "ok")], kind="body")
        ],
        gate_violations=[],
    )
    assert add_notes(report).categories[0].notes is None


def test_add_notes_swallows_model_errors(monkeypatch) -> None:
    _patch_llm(monkeypatch, raises=RuntimeError("network down"))
    report = add_notes(_report())
    assert all(c.notes is None for c in report.categories)


def test_add_notes_survives_unparseable_response(monkeypatch) -> None:
    _patch_llm(monkeypatch, response="I could not comply.")
    report = add_notes(_report())
    assert all(c.notes is None for c in report.categories)


def test_add_notes_passes_model_through(monkeypatch) -> None:
    seen: dict[str, str | None] = {}

    monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))

    def _chat(prompt, model=None):
        seen["model"] = model
        return "{}"

    monkeypatch.setattr(llm_utils, "chat_completion", _chat)
    add_notes(_report(), model="claude-opus-5")
    assert seen["model"] == "claude-opus-5"
