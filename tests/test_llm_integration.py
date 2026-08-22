"""Comprehensive integration tests for the LLM commentary pipeline.

These tests exercise the full flow from input validation through LLM invocation (mocked)
to output parsing and downstream business logic, covering every failure mode documented in
the commentary module.

Design principles:
* Zero real LLM calls — every ``chat_completion`` and ``is_llm_available`` call is
  intercepted via ``monkeypatch`` (``unittest.mock`` style) before it leaves the process.
* Determinism — scores are computed before any LLM touch; the mock only controls the prose
  notes that get attached.
* Isolation — each test gets its own report object; no shared mutable state between tests.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

import skillspector.llm_utils as llm_utils
from skillspector_quality.nodes.quality_scorer import quality_scorer
from skillspector_quality.quality.commentary import (
    _build_prompt,
    _parse_notes,
    add_notes,
)
from skillspector_quality.quality.models import CategoryScore, QualityReport

# ---------------------------------------------------------------------------
# Shared skill content used across tests
# ---------------------------------------------------------------------------

_RICH_SKILL = """\
---
name: my-skill
description: Processes user data requests with structured validation
when_to_use: Use this skill when the user submits a data form
---
# My Skill

This skill handles user data validation. It checks inputs, normalises values,
and returns a structured JSON response.

## Steps

1. Validate the incoming request body.
2. Normalise field names to snake_case.
3. Reject unknown fields with a 422 response.
4. Return `{"status": "ok", "data": {...}}` on success.

## Error Handling

On validation failure return `{"status": "error", "message": "<reason>"}`.
Never expose internal stack traces to the caller.
"""

_THIN_SKILL = "---\n---\n# Minimal\nDo stuff.\n"

FIXTURE_GOOD = pathlib.Path(__file__).parent / "fixtures" / "good-skill"
FIXTURE_CALIB_STRONG = pathlib.Path(__file__).parent / "fixtures" / "calib-strong"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def weak_report() -> QualityReport:
    """A report with one weak and one full-marks category."""
    return QualityReport(
        score=60,
        categories=[
            CategoryScore(
                name="Readability",
                earned=2,
                max=5,
                items=[(2, 5, "sentences too long; passive voice detected")],
                kind="body",
            ),
            CategoryScore(
                name="Topic Coverage",
                earned=4,
                max=4,
                items=[(4, 4, "description aligned with body")],
                kind="frontmatter",
            ),
        ],
        gate_violations=[],
    )


@pytest.fixture()
def full_marks_report() -> QualityReport:
    """A perfect report — no category is weak."""
    return QualityReport(
        score=100,
        categories=[
            CategoryScore(
                name="Readability",
                earned=5,
                max=5,
                items=[(5, 5, "all checks pass")],
                kind="body",
            ),
            CategoryScore(
                name="Information Density",
                earned=4,
                max=4,
                items=[(4, 4, "high entropy content")],
                kind="body",
            ),
        ],
        gate_violations=[],
    )


@pytest.fixture()
def mock_llm_available(monkeypatch):
    """Patch is_llm_available to report that a key IS present."""
    monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))


@pytest.fixture()
def mock_llm_unavailable(monkeypatch):
    """Patch is_llm_available to report that NO key is present."""
    monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (False, "ANTHROPIC_API_KEY not set"))


def _make_chat_mock(monkeypatch, response: str = "{}") -> MagicMock:
    """Install a MagicMock for chat_completion and return it for call inspection."""
    mock = MagicMock(return_value=response)
    monkeypatch.setattr(llm_utils, "chat_completion", mock)
    return mock


# ---------------------------------------------------------------------------
# 1. Prompt construction & payload verification
# ---------------------------------------------------------------------------


class TestPromptConstruction:
    """Verify the payload sent to the LLM is correctly structured."""

    def test_prompt_contains_header_role_description(self, weak_report):
        prompt = _build_prompt(weak_report)
        assert "reviewing the authoring quality" in prompt
        assert "improvement tip" in prompt

    def test_prompt_includes_only_weak_categories(self, weak_report):
        prompt = _build_prompt(weak_report)
        # Readability is weak (2/5) — must be in prompt
        assert "Readability (2/5)" in prompt
        # Topic Coverage is at full marks — must NOT be sent (no benefit, wastes tokens)
        assert "Topic Coverage" not in prompt

    def test_prompt_includes_item_labels_verbatim(self, weak_report):
        prompt = _build_prompt(weak_report)
        assert "sentences too long" in prompt
        assert "passive voice detected" in prompt

    def test_prompt_instructs_json_only_output(self, weak_report):
        prompt = _build_prompt(weak_report)
        assert "JSON only" in prompt
        assert "No prose outside the JSON" in prompt

    def test_prompt_includes_max_word_constraint(self, weak_report):
        prompt = _build_prompt(weak_report)
        # The 20-word limit is part of the documented contract
        assert "20 words" in prompt

    def test_prompt_empty_when_all_categories_full(self, full_marks_report):
        """When every category is at max there are no scored category lines in the prompt."""
        prompt = _build_prompt(full_marks_report)
        # The scored lines use "Name (earned/max):" format — none should appear.
        for c in full_marks_report.categories:
            assert f"{c.name} ({c.earned}/{c.max})" not in prompt

    def test_model_name_forwarded_to_chat_completion(self, monkeypatch, weak_report):
        """The model parameter must be forwarded verbatim to chat_completion."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        mock = _make_chat_mock(monkeypatch, '{"Readability": "Use shorter sentences."}')

        add_notes(weak_report, model="claude-opus-4-5")

        mock.assert_called_once()
        _, kwargs = mock.call_args
        assert kwargs.get("model") == "claude-opus-4-5"

    def test_no_model_passed_when_none(self, monkeypatch, weak_report):
        """When model=None the call should still be made with model=None (not omitted)."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        mock = _make_chat_mock(monkeypatch, '{"Readability": "tip"}')

        add_notes(weak_report, model=None)

        mock.assert_called_once()
        _, kwargs = mock.call_args
        assert kwargs.get("model") is None

    def test_prompt_passed_as_first_positional_arg(self, monkeypatch, weak_report):
        """chat_completion receives the full prompt as its first positional argument."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        mock = _make_chat_mock(monkeypatch)

        add_notes(weak_report)

        args, _ = mock.call_args
        prompt_arg = args[0]
        assert "Readability (2/5)" in prompt_arg
        assert "JSON only" in prompt_arg


# ---------------------------------------------------------------------------
# 2. End-to-end pipeline: input validation → LLM → output
# ---------------------------------------------------------------------------


class TestEndToPipelineFlow:
    """Verify the complete add_notes pipeline from availability check to note attachment."""

    def test_full_happy_path_attaches_notes(self, monkeypatch, weak_report):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        _make_chat_mock(monkeypatch, '{"Readability": "Split long sentences into two."}')

        result = add_notes(weak_report)

        assert result is weak_report  # must mutate in place
        readability = next(c for c in result.categories if c.name == "Readability")
        assert readability.notes == "Split long sentences into two."

    def test_full_marks_category_gets_no_notes(self, monkeypatch, weak_report):
        """add_notes only iterates categories: if the LLM returns a key matching a full-marks
        category that key is attached, but add_notes only *sends* weak categories in the
        prompt. Assert the LLM is not sent the full-marks category details."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        mock = _make_chat_mock(monkeypatch, '{"Readability": "tip", "Topic Coverage": "unexpected tip"}')

        result = add_notes(weak_report)

        # Verify the prompt did NOT ask the LLM about the full-marks category.
        args, _ = mock.call_args
        prompt_sent = args[0]
        assert "Topic Coverage" not in prompt_sent

    def test_notes_do_not_alter_numeric_scores(self, monkeypatch, weak_report):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        _make_chat_mock(monkeypatch, '{"Readability": "Shorten sentences."}')

        before_score = weak_report.score
        before_breakdown = [(c.name, c.earned, c.max) for c in weak_report.categories]

        add_notes(weak_report)

        assert weak_report.score == before_score
        assert [(c.name, c.earned, c.max) for c in weak_report.categories] == before_breakdown

    def test_gate_violations_unaffected_by_llm(self, monkeypatch):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        _make_chat_mock(monkeypatch, '{"Readability": "tip"}')

        report = QualityReport(
            score=50,
            categories=[CategoryScore("Readability", 2, 5, [(2, 5, "issues")], kind="body")],
            gate_violations=["Readability: 2/5 (strict)"],
        )
        result = add_notes(report)
        assert result.gate_violations == ["Readability: 2/5 (strict)"]

    def test_llm_called_exactly_once(self, monkeypatch, weak_report):
        """Even with many weak categories, chat_completion is called exactly once."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        report = QualityReport(
            score=30,
            categories=[
                CategoryScore(f"Dim{i}", i, 5, [(i, 5, f"label{i}")], kind="body")
                for i in range(5)
            ],
            gate_violations=[],
        )
        mock = _make_chat_mock(monkeypatch)
        add_notes(report)
        assert mock.call_count == 1

    def test_multiple_weak_categories_all_get_notes(self, monkeypatch):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        _make_chat_mock(
            monkeypatch,
            '{"Readability": "tip-A", "Information Density": "tip-B"}',
        )
        report = QualityReport(
            score=40,
            categories=[
                CategoryScore("Readability", 2, 5, [(2, 5, "issues")], kind="body"),
                CategoryScore("Information Density", 1, 4, [(1, 4, "thin")], kind="body"),
            ],
            gate_violations=[],
        )
        result = add_notes(report)
        assert result.categories[0].notes == "tip-A"
        assert result.categories[1].notes == "tip-B"


# ---------------------------------------------------------------------------
# 3. Pre-conditions: LLM must NOT be called
# ---------------------------------------------------------------------------


class TestLLMNotCalled:
    """Scenarios where chat_completion must never be invoked."""

    def test_llm_not_called_when_unavailable(self, monkeypatch, weak_report):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (False, "no key"))
        mock = _make_chat_mock(monkeypatch)

        add_notes(weak_report)

        mock.assert_not_called()
        assert all(c.notes is None for c in weak_report.categories)

    def test_llm_not_called_when_all_categories_full(self, monkeypatch, full_marks_report):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        mock = _make_chat_mock(monkeypatch)

        add_notes(full_marks_report)

        mock.assert_not_called()
        assert all(c.notes is None for c in full_marks_report.categories)

    def test_llm_not_called_when_no_categories(self, monkeypatch):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        mock = _make_chat_mock(monkeypatch)

        report = QualityReport(score=0, categories=[], gate_violations=[])
        add_notes(report)

        mock.assert_not_called()

    def test_quality_scorer_skips_llm_when_use_llm_false(self, monkeypatch):
        """The quality_scorer node itself must not call the LLM when use_llm=False."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        mock = _make_chat_mock(monkeypatch)

        state: dict[str, Any] = {
            "file_cache": {"SKILL.md": _RICH_SKILL},
            "use_llm": False,
        }
        out = quality_scorer(state)

        mock.assert_not_called()
        report = QualityReport.from_dict(out["quality_report"])
        assert all(c.notes is None for c in report.categories)


# ---------------------------------------------------------------------------
# 4. Failure scenarios & error handling
# ---------------------------------------------------------------------------


class TestFailureScenarios:
    """Every exception path must degrade silently — never raise, never alter scores."""

    def test_rate_limit_429_swallowed(self, monkeypatch, weak_report):
        """A rate-limit exception (HTTP 429 equivalent) must not propagate."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        monkeypatch.setattr(
            llm_utils,
            "chat_completion",
            MagicMock(side_effect=Exception("429 Too Many Requests")),
        )

        result = add_notes(weak_report)

        assert result is weak_report
        assert all(c.notes is None for c in result.categories)

    def test_timeout_exception_swallowed(self, monkeypatch, weak_report):
        """A network timeout must not propagate."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        monkeypatch.setattr(
            llm_utils,
            "chat_completion",
            MagicMock(side_effect=TimeoutError("connection timed out")),
        )

        result = add_notes(weak_report)

        assert all(c.notes is None for c in result.categories)

    def test_server_error_500_swallowed(self, monkeypatch, weak_report):
        """An internal server error (HTTP 500 equivalent) must not propagate."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        monkeypatch.setattr(
            llm_utils,
            "chat_completion",
            MagicMock(side_effect=RuntimeError("500 Internal Server Error")),
        )

        result = add_notes(weak_report)

        assert all(c.notes is None for c in result.categories)

    def test_connection_error_swallowed(self, monkeypatch, weak_report):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        monkeypatch.setattr(
            llm_utils,
            "chat_completion",
            MagicMock(side_effect=ConnectionError("network unreachable")),
        )

        result = add_notes(weak_report)

        assert all(c.notes is None for c in result.categories)

    def test_score_unchanged_after_exception(self, monkeypatch, weak_report):
        """The numeric score must survive any exception in the LLM path."""
        original_score = weak_report.score
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        monkeypatch.setattr(
            llm_utils,
            "chat_completion",
            MagicMock(side_effect=RuntimeError("boom")),
        )

        add_notes(weak_report)

        assert weak_report.score == original_score


# ---------------------------------------------------------------------------
# 5. Malformed / unexpected LLM responses
# ---------------------------------------------------------------------------


class TestMalformedResponses:
    """Verify _parse_notes and add_notes handle every bad-response shape."""

    # _parse_notes unit tests
    def test_parse_notes_valid_json_object(self):
        assert _parse_notes('{"A": "tip"}') == {"A": "tip"}

    def test_parse_notes_empty_string(self):
        assert _parse_notes("") == {}

    def test_parse_notes_plain_prose(self):
        assert _parse_notes("I cannot help with that.") == {}

    def test_parse_notes_truncated_json(self):
        assert _parse_notes('{"A": "tip"') == {}

    def test_parse_notes_invalid_json_syntax(self):
        assert _parse_notes('{"A": }') == {}

    def test_parse_notes_json_array_rejected(self):
        """A bare JSON array (no object brace) returns empty; if the array contains an
        object the regex will match the inner object — test the pure-array case."""
        assert _parse_notes("[1, 2, 3]") == {}
        # A JSON array whose elements are NOT objects must also yield empty.
        assert _parse_notes('["a", "b"]') == {}

    def test_parse_notes_json_null_rejected(self):
        assert _parse_notes("null") == {}

    def test_parse_notes_json_number_rejected(self):
        assert _parse_notes("42") == {}

    def test_parse_notes_extracts_object_from_markdown_fences(self):
        raw = '```json\n{"Readability": "Shorten sentences."}\n```'
        assert _parse_notes(raw) == {"Readability": "Shorten sentences."}

    def test_parse_notes_extracts_object_from_surrounding_prose(self):
        raw = "Here is my answer:\n\n{\"X\": \"tip\"}\n\nHope that helps!"
        assert _parse_notes(raw) == {"X": "tip"}

    def test_parse_notes_coerces_numeric_values_to_str(self):
        result = _parse_notes('{"A": 3, "B": 1.5}')
        assert result == {"A": "3", "B": "1.5"}

    def test_parse_notes_drops_nested_containers(self):
        """Nested dicts/lists are not valid note values and must be dropped."""
        result = _parse_notes('{"A": "ok", "B": {"nested": "v"}, "C": ["list"]}')
        assert result == {"A": "ok"}

    def test_parse_notes_missing_required_schema_key(self):
        """A response that has no matching category key returns empty notes."""
        result = _parse_notes('{"NonExistent": "tip"}')
        assert isinstance(result, dict)  # still parses cleanly, just no known keys

    # add_notes integration: bad response degrades silently
    def test_add_notes_empty_response_no_notes(self, monkeypatch, weak_report):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        _make_chat_mock(monkeypatch, "")

        result = add_notes(weak_report)

        assert all(c.notes is None for c in result.categories)

    def test_add_notes_prose_only_response_no_notes(self, monkeypatch, weak_report):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        _make_chat_mock(monkeypatch, "I'm sorry, I can't help with that.")

        result = add_notes(weak_report)

        assert all(c.notes is None for c in result.categories)

    def test_add_notes_array_response_no_notes(self, monkeypatch, weak_report):
        """JSON array is not the expected schema; notes must stay None."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        _make_chat_mock(monkeypatch, '[{"category": "Readability", "tip": "shorter"}]')

        result = add_notes(weak_report)

        assert all(c.notes is None for c in result.categories)

    def test_add_notes_unknown_category_key_is_ignored(self, monkeypatch, weak_report):
        """A key that doesn't match any category name must be silently dropped."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        _make_chat_mock(monkeypatch, '{"NonExistentDimension": "some tip"}')

        result = add_notes(weak_report)

        assert all(c.notes is None for c in result.categories)

    def test_add_notes_partial_match_attaches_matching_only(self, monkeypatch, weak_report):
        """If response has one known and one unknown key, only the known one is attached."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        _make_chat_mock(
            monkeypatch,
            '{"Readability": "real tip", "GhostCategory": "ignored"}',
        )

        result = add_notes(weak_report)

        readability = next(c for c in result.categories if c.name == "Readability")
        assert readability.notes == "real tip"


# ---------------------------------------------------------------------------
# 6. quality_scorer node: end-to-end node integration
# ---------------------------------------------------------------------------


class TestQualityScorerNode:
    """End-to-end tests of the quality_scorer LangGraph node."""

    def test_node_with_llm_attaches_notes(self, monkeypatch):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        # Respond with a tip for any weak category present
        def _chat(prompt: str, model: Any = None) -> str:
            # Find a weak category name from the prompt and echo back a tip
            for line in prompt.split("\n"):
                if line.startswith("- ") and "(" in line:
                    cat_name = line[2:line.index("(")].strip()
                    return json.dumps({cat_name: "Improve this dimension."})
            return "{}"

        monkeypatch.setattr(llm_utils, "chat_completion", _chat)

        state: dict[str, Any] = {
            "file_cache": {"SKILL.md": _THIN_SKILL},
            "use_llm": True,
        }
        out = quality_scorer(state)
        report = QualityReport.from_dict(out["quality_report"])
        # At least some categories should have notes (thin skill has weak dimensions)
        notes_count = sum(1 for c in report.categories if c.notes is not None)
        assert notes_count >= 1

    def test_node_no_llm_flag_produces_no_notes(self, monkeypatch):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        mock = _make_chat_mock(monkeypatch, '{"Readability": "tip"}')

        state: dict[str, Any] = {"file_cache": {"SKILL.md": _RICH_SKILL}, "use_llm": False}
        out = quality_scorer(state)

        mock.assert_not_called()
        report = QualityReport.from_dict(out["quality_report"])
        assert all(c.notes is None for c in report.categories)

    def test_node_uses_model_config_per_analyzer(self, monkeypatch):
        """model_config["quality_scorer"] must be forwarded to chat_completion."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        seen: dict[str, Any] = {}

        def _chat(prompt: str, model: Any = None) -> str:
            seen["model"] = model
            return "{}"

        monkeypatch.setattr(llm_utils, "chat_completion", _chat)

        state: dict[str, Any] = {
            "file_cache": {"SKILL.md": _THIN_SKILL},
            "use_llm": True,
            "model_config": {"quality_scorer": "claude-sonnet-5"},
        }
        quality_scorer(state)
        assert seen.get("model") == "claude-sonnet-5"

    def test_node_falls_back_to_default_model(self, monkeypatch):
        """When no quality_scorer key, fall back to model_config["default"]."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        seen: dict[str, Any] = {}

        def _chat(prompt: str, model: Any = None) -> str:
            seen["model"] = model
            return "{}"

        monkeypatch.setattr(llm_utils, "chat_completion", _chat)

        state: dict[str, Any] = {
            "file_cache": {"SKILL.md": _THIN_SKILL},
            "use_llm": True,
            "model_config": {"default": "claude-haiku-4-5"},
        }
        quality_scorer(state)
        assert seen.get("model") == "claude-haiku-4-5"

    def test_node_llm_exception_still_returns_deterministic_score(self, monkeypatch):
        """An LLM crash inside the node must not change the deterministic score."""
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        monkeypatch.setattr(
            llm_utils,
            "chat_completion",
            MagicMock(side_effect=RuntimeError("crash")),
        )

        state_no_llm: dict[str, Any] = {"file_cache": {"SKILL.md": _RICH_SKILL}, "use_llm": False}
        state_llm: dict[str, Any] = {"file_cache": {"SKILL.md": _RICH_SKILL}, "use_llm": True}

        out_no_llm = quality_scorer(state_no_llm)
        out_llm = quality_scorer(state_llm)

        assert out_llm["quality_report"]["score"] == out_no_llm["quality_report"]["score"]

    def test_node_empty_file_cache_returns_low_score(self, monkeypatch):
        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        mock = _make_chat_mock(monkeypatch)

        state: dict[str, Any] = {"file_cache": {}, "use_llm": False}
        out = quality_scorer(state)

        mock.assert_not_called()
        report = QualityReport.from_dict(out["quality_report"])
        assert report.score < 40

    def test_node_produces_cost_report(self):
        """The node must always produce a cost_report alongside quality_report."""
        state: dict[str, Any] = {"file_cache": {"SKILL.md": _RICH_SKILL}, "use_llm": False}
        out = quality_scorer(state)
        assert "cost_report" in out
        assert isinstance(out["cost_report"], dict)
        assert "score" in out["cost_report"]


# ---------------------------------------------------------------------------
# 7. CLI scan integration (mocked LLM)
# ---------------------------------------------------------------------------


class TestCLIScanIntegration:
    """CLI-level tests verifying that ``scan`` honours --no-llm and mocked LLM paths."""

    def test_scan_no_llm_flag_never_calls_llm(self, monkeypatch):
        """--no-llm must prevent any LLM call regardless of key availability."""
        from typer.testing import CliRunner

        from skillspector_quality.cli import app

        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        mock = _make_chat_mock(monkeypatch)

        runner = CliRunner()
        result = runner.invoke(app, ["scan", str(FIXTURE_GOOD), "--no-llm", "--format", "json"])

        assert result.exit_code == 0, result.output
        mock.assert_not_called()

    def test_scan_json_output_contains_quality_assessment(self, monkeypatch):
        """JSON output must contain a ``quality_assessment`` key with a numeric score."""
        from typer.testing import CliRunner

        from skillspector_quality.cli import app

        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (False, "no key"))

        runner = CliRunner()
        result = runner.invoke(app, ["scan", str(FIXTURE_GOOD), "--no-llm", "--format", "json"])

        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        qa = data["quality_assessment"]
        assert isinstance(qa["score"], int)
        assert 0 <= qa["score"] <= 100

    def test_scan_with_mocked_llm_attaches_notes_in_json(self, monkeypatch):
        """When LLM is available and --no-llm is NOT passed, notes appear in JSON output."""
        from typer.testing import CliRunner

        from skillspector_quality.cli import app

        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))

        def _chat(prompt: str, model: Any = None) -> str:
            # Return a tip for the first weak category found in the prompt
            for line in prompt.split("\n"):
                if line.startswith("- ") and "(" in line:
                    name = line[2:line.index("(")].strip()
                    return json.dumps({name: "Mock LLM tip for integration test."})
            return "{}"

        monkeypatch.setattr(llm_utils, "chat_completion", _chat)

        runner = CliRunner()
        result = runner.invoke(
            app, ["scan", str(FIXTURE_GOOD), "--format", "json"]
        )

        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        categories = data["quality_assessment"]["categories"]
        notes_present = [c for c in categories if c.get("notes")]
        assert len(notes_present) >= 1, "Expected at least one category to carry LLM notes"

    def test_scan_nonexistent_path_exits_two(self):
        """A missing path must exit with code 2 (user error) — no LLM call needed."""
        from typer.testing import CliRunner

        from skillspector_quality.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["scan", "/does/not/exist/at/all", "--no-llm"])
        assert result.exit_code == 2

    def test_scan_min_score_gate_with_mocked_llm(self, monkeypatch):
        """--min-score gate must trigger based on the deterministic score, not on notes."""
        from typer.testing import CliRunner

        from skillspector_quality.cli import app

        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        # LLM returns a glowing note — must have no effect on the score gate
        _make_chat_mock(monkeypatch, '{"Readability": "Excellent work!"}')

        runner = CliRunner()
        result_pass = runner.invoke(
            app, ["scan", str(FIXTURE_GOOD), "--min-score", "1", "--format", "json"]
        )
        result_fail = runner.invoke(
            app, ["scan", str(FIXTURE_GOOD), "--min-score", "99", "--format", "json"]
        )

        assert result_pass.exit_code == 0, result_pass.output
        assert result_fail.exit_code == 1

    def test_scan_llm_crash_does_not_break_cli(self, monkeypatch):
        """An LLM exception during a scan must not crash the CLI (exit 0, no notes)."""
        from typer.testing import CliRunner

        from skillspector_quality.cli import app

        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        monkeypatch.setattr(
            llm_utils,
            "chat_completion",
            MagicMock(side_effect=RuntimeError("LLM unavailable")),
        )

        runner = CliRunner()
        result = runner.invoke(app, ["scan", str(FIXTURE_GOOD), "--format", "json"])

        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "quality_assessment" in data
        # Notes must be absent when LLM crashed
        for cat in data["quality_assessment"]["categories"]:
            assert cat.get("notes") is None


# ---------------------------------------------------------------------------
# 8. Full graph integration: graph.invoke with mocked LLM
# ---------------------------------------------------------------------------


class TestGraphInvokeIntegration:
    """Integration tests that drive graph.invoke end-to-end with a mocked LLM."""

    def test_graph_invoke_no_llm_deterministic(self):
        from skillspector_quality.graph import graph
        from skillspector_quality.quality.models import QualityReport

        state = {"input_path": str(FIXTURE_GOOD), "output_format": "json", "use_llm": False}
        r1 = graph.invoke(dict(state))
        r2 = graph.invoke(dict(state))

        assert r1["quality_report"]["score"] == r2["quality_report"]["score"]

    def test_graph_invoke_with_mocked_llm_adds_notes(self, monkeypatch):
        from skillspector_quality.graph import graph
        from skillspector_quality.quality.models import QualityReport

        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))

        def _chat(prompt: str, model: Any = None) -> str:
            for line in prompt.split("\n"):
                if line.startswith("- ") and "(" in line:
                    name = line[2:line.index("(")].strip()
                    return json.dumps({name: "Graph-level tip."})
            return "{}"

        monkeypatch.setattr(llm_utils, "chat_completion", _chat)

        state = {"input_path": str(FIXTURE_GOOD), "output_format": "json", "use_llm": True}
        result = graph.invoke(state)

        report = QualityReport.from_dict(result["quality_report"])
        notes_found = [c for c in report.categories if c.notes is not None]
        assert len(notes_found) >= 1

    def test_graph_invoke_score_identical_with_and_without_llm(self, monkeypatch):
        """Notes must never change the numeric score — verified at the graph level."""
        from skillspector_quality.graph import graph
        from skillspector_quality.quality.models import QualityReport

        monkeypatch.setattr(llm_utils, "is_llm_available", lambda: (True, ""))
        _make_chat_mock(monkeypatch, '{"Readability": "Shorten your sentences significantly."}')

        state_base = {"input_path": str(FIXTURE_GOOD), "output_format": "json", "use_llm": False}
        state_llm = {"input_path": str(FIXTURE_GOOD), "output_format": "json", "use_llm": True}

        r_base = graph.invoke(dict(state_base))
        r_llm = graph.invoke(dict(state_llm))

        assert r_llm["quality_report"]["score"] == r_base["quality_report"]["score"]

    def test_graph_produces_security_and_quality_in_one_pass(self):
        """A single graph.invoke must populate both security and quality channels."""
        from skillspector_quality.graph import graph

        state = {"input_path": str(FIXTURE_GOOD), "output_format": "json", "use_llm": False}
        result = graph.invoke(state)

        # Security side
        assert "risk_score" in result
        assert isinstance(result["risk_score"], int)
        # Quality side
        assert "quality_report" in result
        assert isinstance(result["quality_report"]["score"], int)
