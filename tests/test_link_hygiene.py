"""Tests for link-hygiene scoring (ADR-0005) and configurable/gateable metrics (ADR-0006)."""

from __future__ import annotations

import pathlib

from skillspector_quality.config import ScoringConfig
from skillspector_quality.quality import score_quality
from skillspector_quality.quality.scorers import (
    SkillDoc,
    _link_hygiene,
    _link_valid_score,
    dim_information_density,
    dim_lexical_diversity,
    dim_structural_coherence,
    link_gate_violations,
)

_FM = "---\nname: s\ndescription: d\n---\n# Title\n"


def _doc(skill_md: str, **files: str) -> SkillDoc:
    cache = {"SKILL.md": skill_md}
    cache.update(files)
    return SkillDoc.from_file_cache(cache)


def _cache_of(name: str) -> dict[str, str]:
    base = pathlib.Path(__file__).parent / "fixtures" / name
    return {str(p.relative_to(base)): p.read_text() for p in base.rglob("*") if p.is_file()}


# --- detection --------------------------------------------------------------- #


def test_broken_text_link_flagged() -> None:
    h = _link_hygiene(_doc(_FM + "See [x](reference/missing.md).\n"))
    assert h.broken == ["reference/missing.md"]
    assert not h.platform and not h.case_mismatch


def test_binary_asset_link_not_flagged() -> None:
    # a missing .pptx/.png is unverifiable (loader can't see binaries) -> never broken
    h = _link_hygiene(_doc(_FM + "[deck](Template.pptx) [logo](assets/logo.png)\n"))
    assert h.broken == []


def test_existing_text_link_clean() -> None:
    h = _link_hygiene(_doc(_FM + "[r](reference.md)\n", **{"reference.md": "x"}))
    assert not h.has_any()


def test_platform_coupled_patterns_flagged() -> None:
    md = _FM + (
        "[a](/Users/me/x.md)\n[b](C:\\proj\\y.md)\n"
        "[c](~/notes.md)\n[d](file:///Users/me/z.md)\n[e](docs\\ref.md)\n"
    )
    h = _link_hygiene(_doc(md))
    assert len(h.platform) == 5
    assert not h.broken  # platform classification wins, no double-count


def test_case_mismatch_flagged_with_real_key() -> None:
    h = _link_hygiene(
        _doc(_FM + "[c](reference/Catalog.md)\n", **{"reference/catalog.md": "x"})
    )
    assert h.case_mismatch == [("reference/Catalog.md", "reference/catalog.md")]
    assert not h.broken


def test_redundant_markdown_only_not_bare() -> None:
    # two markdown links to the same existing file -> 1 redundant;
    # repeated bare reference paths are per-step reads, not redundant
    md = (
        _FM
        + "[g](reference/a.md) and again [g](reference/a.md)\n"
        + "Read `reference/a.md` at step 1. Read `reference/a.md` at step 2.\n"
    )
    h = _link_hygiene(_doc(md, **{"reference/a.md": "x"}))
    assert h.redundant == [("reference/a.md", 2)]


def test_external_and_anchor_links_ignored() -> None:
    h = _link_hygiene(_doc(_FM + "[w](https://x.com) [m](mailto:a@b.c) [s](#section)\n"))
    assert not h.has_any()


# --- scoring ----------------------------------------------------------------- #


def test_link_valid_penalties_match_formula() -> None:
    h = _link_hygiene(_doc(_FM + "[x](reference/missing.md)\n[y](/Users/me/z.md)\n"))
    # 1 broken (0.34) + 1 platform (0.34) -> 1 - 0.68 = 0.32
    assert abs(_link_valid_score(h, ScoringConfig()) - 0.32) < 1e-9


def test_structural_coherence_penalizes_broken_link() -> None:
    clean = _doc(_FM + "[r](reference.md)\n", **{"reference.md": "x"})
    bad = _doc(_FM + "[r](reference.md)\n[x](missing.md)\n", **{"reference.md": "x"})
    ((clean_e, _, _),) = dim_structural_coherence(clean, 13)
    ((bad_e, _, lbl),) = dim_structural_coherence(bad, 13)
    assert bad_e < clean_e
    assert "broken link" in lbl


def test_structural_label_mentions_case_mismatch_linux() -> None:
    doc = _doc(_FM + "[c](reference/Catalog.md)\n", **{"reference/catalog.md": "x"})
    ((_, _, lbl),) = dim_structural_coherence(doc, 13)
    assert "case-mismatched" in lbl and "Linux" in lbl


# --- config: disable --------------------------------------------------------- #


def test_disable_sub_check_removes_penalty() -> None:
    h = _link_hygiene(_doc(_FM + "[x](reference/missing.md)\n"))
    cfg = ScoringConfig.from_lists(disable=["link.broken"], strict=[])
    assert _link_valid_score(h, cfg) == 1.0


def test_disable_dimension_renormalizes() -> None:
    cache = _cache_of("good-skill")
    full = score_quality(cache)
    without = score_quality(cache, ScoringConfig.from_lists(disable=["Structural Coherence"], strict=[]))
    assert any(c.name == "Structural Coherence" for c in full.categories)
    assert not any(c.name == "Structural Coherence" for c in without.categories)


# --- config: strict + gate --------------------------------------------------- #


def test_strict_raises_broken_severity() -> None:
    h = _link_hygiene(_doc(_FM + "[x](reference/missing.md)\n"))
    normal = _link_valid_score(h, ScoringConfig())
    strict = _link_valid_score(h, ScoringConfig.from_lists(disable=[], strict=["link.broken"]))
    assert strict < normal  # 0.50 vs 0.34 penalty


def test_strict_link_broken_creates_gate_violation() -> None:
    doc = _doc(_FM + "[x](reference/missing.md)\n")
    cfg = ScoringConfig.from_lists(disable=[], strict=["link.broken"])
    assert link_gate_violations(doc, cfg)
    assert not link_gate_violations(doc, ScoringConfig())  # no gate without strict


def test_score_quality_reports_gate_violations() -> None:
    cache = {"SKILL.md": _FM + "[x](reference/missing.md)\n"}
    rep = score_quality(cache, ScoringConfig.from_lists(disable=[], strict=["link.broken"]))
    assert rep.gate_violations
    assert rep.to_dict()["gate_violations"] == rep.gate_violations  # round-trips to JSON


def test_strict_density_lowers_or_equal() -> None:
    doc = SkillDoc.from_file_cache(_cache_of("good-skill"))
    ((normal, _, _),) = dim_information_density(doc, 15)
    ((strict, _, _),) = dim_information_density(
        doc, 15, ScoringConfig.from_lists(disable=[], strict=["Information Density"])
    )
    assert strict <= normal


def test_strict_lexical_lowers_or_equal() -> None:
    doc = SkillDoc.from_file_cache(_cache_of("good-skill"))
    res_n = dim_lexical_diversity(doc, 6)
    res_s = dim_lexical_diversity(
        doc, 6, ScoringConfig.from_lists(disable=[], strict=["Lexical Diversity"])
    )
    if res_n and res_s:  # N/A if too little prose
        assert res_s[0][0] <= res_n[0][0]


# --- config: loading --------------------------------------------------------- #


def test_config_load_pyproject_and_cli_union(tmp_path: pathlib.Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[tool.skillspector-quality]\n"
        'disable = ["Lexical Diversity"]\n'
        'strict = ["link.broken"]\n'
    )
    cfg = ScoringConfig.load(tmp_path, cli_disable=["Readability"], cli_strict=[])
    assert cfg.is_disabled("Lexical Diversity")  # from file
    assert cfg.is_disabled("readability")  # from CLI, slug form
    assert cfg.is_strict("link.broken")


def test_config_id_normalization() -> None:
    cfg = ScoringConfig.from_lists(disable=["Information Density"], strict=[])
    assert cfg.is_disabled("information-density")
    assert cfg.is_disabled("Information Density")


def test_config_comma_separated_split() -> None:
    cfg = ScoringConfig.from_lists(disable=["Readability, Lexical Diversity"], strict=[])
    assert cfg.is_disabled("Readability")
    assert cfg.is_disabled("Lexical Diversity")


def test_config_unknown_ids() -> None:
    cfg = ScoringConfig.from_lists(disable=["Nonsense Dim"], strict=[])
    known = {"Readability", "link.broken"}
    assert cfg.unknown_ids(known) == {"nonsense-dim"}
