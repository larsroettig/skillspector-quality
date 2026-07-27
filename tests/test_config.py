"""Tests for scoring-config discovery (ADR-0006).

``ScoringConfig.load`` reads project files and is documented to ignore anything
missing or unparseable. A silently-swallowed error is indistinguishable from "no config
found", so a regression here would quietly stop honouring a user's `disable`/`strict`
settings rather than failing loudly. Each ignore path is pinned below.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

from skillspector_quality.config import ScoringConfig, _norm, _split

# --------------------------------------------------------------------------- #
# Normalization
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Metadata & Discovery", "metadata-discovery"),
        ("Information Density", "information-density"),
        ("link.broken", "link.broken"),
        ("  Spaced  Out  ", "spaced-out"),
        ("ALREADY-SLUG", "already-slug"),
    ],
)
def test_norm_canonicalizes_ids(raw: str, expected: str) -> None:
    assert _norm(raw) == expected


def test_split_flattens_comma_separated_values() -> None:
    # Blank parts are dropped; surrounding whitespace is left for _norm to strip.
    assert _split(["a,b", "c", " ,d "]) == ["a", "b", "c", "d "]


def test_is_disabled_and_is_strict_accept_either_spelling() -> None:
    config = ScoringConfig.from_lists(disable=["Metadata & Discovery"], strict=["link.broken"])
    assert config.is_disabled("metadata-discovery")
    assert config.is_disabled("Metadata & Discovery")
    assert config.is_strict("link.broken")
    assert not config.is_strict("link.redundant")


def test_unknown_ids_reports_only_unrecognized() -> None:
    config = ScoringConfig.from_lists(disable=["Readability", "not-a-thing"], strict=[])
    assert config.unknown_ids({"Readability", "link.broken"}) == {"not-a-thing"}


# --------------------------------------------------------------------------- #
# pyproject.toml
# --------------------------------------------------------------------------- #


def test_load_reads_pyproject_tool_table(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.skillspector-quality]\ndisable = ["Readability"]\nstrict = ["link.broken"]\n',
        encoding="utf-8",
    )
    config = ScoringConfig.load(tmp_path)
    assert config.is_disabled("Readability")
    assert config.is_strict("link.broken")


def test_load_returns_empty_when_no_config_file_exists(tmp_path: Path) -> None:
    config = ScoringConfig.load(tmp_path)
    assert config.disabled == frozenset()
    assert config.strict == frozenset()


# --------------------------------------------------------------------------- #
# .skillspector.toml — top-level keys and the named table
# --------------------------------------------------------------------------- #


def test_load_reads_skillspector_toml_top_level_keys(tmp_path: Path) -> None:
    (tmp_path / ".skillspector.toml").write_text(
        'disable = ["Readability"]\nstrict = ["link.broken"]\n', encoding="utf-8"
    )
    config = ScoringConfig.load(tmp_path)
    assert config.is_disabled("Readability")
    assert config.is_strict("link.broken")


def test_load_reads_skillspector_toml_named_table(tmp_path: Path) -> None:
    (tmp_path / ".skillspector.toml").write_text(
        '[skillspector-quality]\ndisable = ["Topic Coverage"]\n', encoding="utf-8"
    )
    assert ScoringConfig.load(tmp_path).is_disabled("Topic Coverage")


def test_load_unions_both_files_and_cli(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.skillspector-quality]\ndisable = ["Readability"]\n', encoding="utf-8"
    )
    (tmp_path / ".skillspector.toml").write_text(
        'disable = ["Topic Coverage"]\n', encoding="utf-8"
    )
    config = ScoringConfig.load(tmp_path, cli_disable=["link.redundant"])
    assert config.is_disabled("Readability")
    assert config.is_disabled("Topic Coverage")
    assert config.is_disabled("link.redundant")


# --------------------------------------------------------------------------- #
# Ignore paths: every one of these must degrade to "no config", never raise
# --------------------------------------------------------------------------- #


def test_load_ignores_malformed_toml(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("this is not = = valid toml\n", encoding="utf-8")
    assert ScoringConfig.load(tmp_path).disabled == frozenset()


def test_load_ignores_missing_table_path(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[tool.other]\ndisable = ["x"]\n', encoding="utf-8")
    assert ScoringConfig.load(tmp_path).disabled == frozenset()


def test_load_ignores_table_path_that_is_not_a_table(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool]\n"skillspector-quality" = "a string, not a table"\n', encoding="utf-8"
    )
    assert ScoringConfig.load(tmp_path).disabled == frozenset()


def test_load_ignores_non_array_disable(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.skillspector-quality]\ndisable = "Readability"\n', encoding="utf-8"
    )
    assert ScoringConfig.load(tmp_path).disabled == frozenset()


def test_load_ignores_non_array_strict(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.skillspector-quality]\nstrict = 42\n', encoding="utf-8"
    )
    assert ScoringConfig.load(tmp_path).strict == frozenset()


def test_load_treats_null_values_as_empty(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.skillspector-quality]\ndisable = []\nstrict = []\n', encoding="utf-8"
    )
    config = ScoringConfig.load(tmp_path)
    assert config.disabled == frozenset()
    assert config.strict == frozenset()


def test_load_defaults_to_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.skillspector-quality]\ndisable = ["Readability"]\n', encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    assert ScoringConfig.load().is_disabled("Readability")


# --------------------------------------------------------------------------- #
# python -m skillspector_quality
# --------------------------------------------------------------------------- #


def test_module_entrypoint_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    """`python -m skillspector_quality --version` must reach the Typer app."""
    monkeypatch.setattr(sys, "argv", ["skillspector-quality", "--version"])
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("skillspector_quality", run_name="__main__")
    assert excinfo.value.code == 0
