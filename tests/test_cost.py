"""Tests for the token-cost axis and Instruction Clarity (ADR-0009)."""

from __future__ import annotations

import pathlib

import pytest

from skillspector_quality.quality import score_quality
from skillspector_quality.quality.cost import (
    ASSUMED_DOC_READ_RATE,
    ASSUMED_INVOCATION_RATE,
    COST_CHEAP_TOKENS,
    COST_EXPENSIVE_TOKENS,
    WEIGHT_ALWAYS_ON,
    WEIGHT_ON_DEMAND,
    WEIGHT_ON_INVOKE,
    CostReport,
    cost_status,
    estimate_tokens,
    score_cost,
)
from skillspector_quality.quality.scorers import SkillDoc, _duplicate_spans, _hedge_density

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _doc(skill_md: str, **files: str) -> SkillDoc:
    return SkillDoc.from_file_cache({"SKILL.md": skill_md, **files})


# --------------------------------------------------------------------------- #
# The cost model
# --------------------------------------------------------------------------- #


def test_tier_weights_derive_from_the_stated_assumptions() -> None:
    """The weights must stay a consequence of the documented rates, not drift into magic.

    If someone edits a weight directly instead of the assumption behind it, the model stops
    meaning what the ADR says it means.
    """
    assert WEIGHT_ALWAYS_ON == 1.0
    assert WEIGHT_ON_INVOKE == ASSUMED_INVOCATION_RATE
    assert WEIGHT_ON_DEMAND == ASSUMED_INVOCATION_RATE * ASSUMED_DOC_READ_RATE
    assert WEIGHT_ALWAYS_ON > WEIGHT_ON_INVOKE > WEIGHT_ON_DEMAND


def test_always_on_tokens_outweigh_far_larger_on_demand_tokens() -> None:
    """The whole point of the axis: a small description costs more than a big reference doc.

    A description is loaded for every skill in every session; a supporting doc is read only
    when the skill fires AND the agent opens it.
    """
    tiny_description = _doc(
        "---\ndescription: " + "x" * 400 + "\n---\n# S\n\nShort body.\n",
    )
    huge_docs = _doc(
        "---\ndescription: short\n---\n# S\n\nShort body.\n",
        **{"reference.md": "y" * 40_000},
    )
    assert score_cost(tiny_description).score < score_cost(huge_docs).score


def test_cost_score_is_higher_for_cheaper_skills() -> None:
    """Higher = cheaper, matching the quality axis direction."""
    lean = _doc("---\ndescription: terse\n---\n# S\n\nBody.\n")
    heavy = _doc("---\ndescription: " + "word " * 200 + "\n---\n# S\n\n" + "prose " * 5000)
    assert score_cost(lean).score > score_cost(heavy).score


def test_cost_anchors_map_to_score_endpoints() -> None:
    """A skill at the cheap anchor scores 100; at the expensive anchor, 0."""
    assert COST_CHEAP_TOKENS < COST_EXPENSIVE_TOKENS
    # Description-only skills put all weight in the always-on tier at weight 1.0, so the
    # weighted total equals the description's token count — a clean way to hit an anchor.
    cheap = _doc("---\ndescription: " + "x" * int(COST_CHEAP_TOKENS * 4) + "\n---\n")
    expensive = _doc("---\ndescription: " + "x" * int(COST_EXPENSIVE_TOKENS * 4) + "\n---\n")
    assert score_cost(cheap).score == 100
    assert score_cost(expensive).score == 0


def test_cost_score_stays_in_range_for_pathological_input() -> None:
    enormous = _doc("---\ndescription: " + "x" * 200_000 + "\n---\n# S\n" + "y" * 500_000)
    assert 0 <= score_cost(enormous).score <= 100


@pytest.mark.parametrize(
    ("score", "tier"),
    [(100, "LEAN"), (88, "LEAN"), (87, "MODERATE"), (58, "MODERATE"), (35, "HEAVY"), (0, "BLOATED")],
)
def test_cost_tiers_map_to_population_position(score: int, tier: str) -> None:
    assert cost_status(score)[0] == tier


def test_cost_status_fallback_below_lowest_threshold() -> None:
    """A score below every listed threshold (defensive: scores are normally 0-100) still
    resolves to the worst tier via the trailing fallback return."""
    assert cost_status(-1) == ("BLOATED", "COSTS MORE THAN IT LIKELY RETURNS")


def test_estimate_tokens_is_proportional_not_exact() -> None:
    """A consistent constant factor is enough: the score is a percentile rank."""
    assert estimate_tokens("") == 0
    assert estimate_tokens("a" * 400) == 100


def test_cost_report_round_trips_through_state() -> None:
    """LangGraph serializes state to dicts; the CLI must rebuild an equivalent report."""
    original = score_cost(_doc("---\ndescription: d\n---\n# S\n\nSome body prose here.\n"))
    restored = CostReport.from_dict(original.to_dict())
    assert restored.score == original.score
    assert restored.raw_total == original.raw_total
    assert [t.name for t in restored.tiers] == [t.name for t in original.tiers]
    assert restored.duplicate_tokens == original.duplicate_tokens


# --------------------------------------------------------------------------- #
# Duplication: diagnostic on the cost axis, deliberately not a quality signal
# --------------------------------------------------------------------------- #


def test_duplicate_spans_name_the_files_involved() -> None:
    """This is the attribution `_ngram_dup` cannot give — it returns one opaque fraction."""
    shared = " ".join(f"reconcile invoice line {i} against the purchase order" for i in range(40))
    doc = _doc(
        f"---\ndescription: d\n---\n# S\n\n{shared}\n",
        **{"reference.md": f"# Ref\n\n{shared}\n"},
    )
    spans = _duplicate_spans(doc)
    assert spans
    assert {spans[0].source, spans[0].target} == {"SKILL.md", "reference.md"}
    assert spans[0].shared_tokens > 30


def test_duplication_is_not_scored_as_its_own_quality_dimension() -> None:
    """Correlates with the existing _ngram_dup at r=+0.951 — scoring it double-counts."""
    names = {name for name, _, _ in __import__(
        "skillspector_quality.quality.scorers", fromlist=["DIMENSIONS"]
    ).DIMENSIONS}
    assert not any("duplicat" in n.lower() for n in names)


def test_duplication_surfaces_as_an_advisory_label() -> None:
    shared = " ".join(f"reconcile invoice line {i} against the purchase order" for i in range(40))
    report = score_quality(
        {
            "SKILL.md": f"---\ndescription: reconcile invoices\n---\n# S\n\n{shared}\n",
            "reference.md": f"# Ref\n\n{shared}\n",
        }
    )
    density = next(c for c in report.categories if c.name == "Information Density")
    label = density.items[0][2]
    assert "advisory (no score impact)" in label
    assert "reference.md" in label


# --------------------------------------------------------------------------- #
# Instruction Clarity
# --------------------------------------------------------------------------- #


def _clarity(report_files: dict[str, str]) -> tuple[int, int]:
    report = score_quality(report_files)
    cat = next(c for c in report.categories if c.name == "Instruction Clarity")
    return cat.earned, cat.max


def test_hedging_lowers_clarity() -> None:
    concrete = "Reconcile each invoice against its purchase order and flag variance. " * 12
    vague = "Handle things appropriately as needed, and consider various stuff etc. " * 12
    base = "---\ndescription: reconcile invoices\n---\n# S\n\n"
    assert _clarity({"SKILL.md": base + concrete}) > _clarity({"SKILL.md": base + vague})


def test_hedge_density_is_length_invariant() -> None:
    """Padding with more of the same prose must not change the density."""
    unit = "Handle things appropriately as needed and consider various options. "
    assert _hedge_density(unit * 10) == pytest.approx(_hedge_density(unit * 40), abs=0.01)


def test_untagged_fences_lower_clarity() -> None:
    body = "---\ndescription: d\n---\n# S\n\n" + ("Run the command shown below to process. " * 10)
    tagged = body + "\n```bash\ntool run\n```\n"
    untagged = body + "\n```\ntool run\n```\n"
    assert _clarity({"SKILL.md": tagged}) > _clarity({"SKILL.md": untagged})


def test_instruction_clarity_is_na_when_nothing_to_judge() -> None:
    """A tiny skill with no prose and no fences must not be penalized for silence."""
    report = score_quality({"SKILL.md": "---\ndescription: d\n---\n# S\n\nShort.\n"})
    assert "Instruction Clarity" not in {c.name for c in report.categories}


def test_instruction_clarity_is_not_constant_across_fixtures() -> None:
    """Anti-saturation guard — the failure mode calibration exists to catch."""
    observed = set()
    for name in ("calib-thin", "calib-typical", "calib-strong"):
        root = FIXTURES / name
        files = {
            str(p.relative_to(root)): p.read_text(encoding="utf-8")
            for p in sorted(root.rglob("*"))
            if p.is_file()
        }
        report = score_quality(files)
        cat = next((c for c in report.categories if c.name == "Instruction Clarity"), None)
        if cat:
            observed.add(cat.earned / cat.max)
    assert len(observed) >= 2, f"Instruction Clarity returned a constant {observed}"
