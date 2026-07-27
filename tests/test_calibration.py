"""Regression tests pinning the percentile calibration (ADR-0007).

These guard the failure mode the calibration existed to fix: a dimension quietly collapsing
to a constant, so it adds points to every skill while ranking nothing. Unit tests on band
edges catch a changed constant; the saturation guards catch a changed *code path* that
happens to leave the constants alone.

Fixture anchors — measured against a 207-skill corpus (see ``benchmarks/calibrate.py``):

===============  =====  ================================================
fixture          score  intended position
===============  =====  ================================================
``calib-thin``    ~56   below corpus p10 (61): repetitive, unaligned
``calib-typical`` ~72   near corpus p50 (73): ordinary, competent skill
``calib-strong``  ~82   at corpus p90 (82): dense, linked, demonstrated
===============  =====  ================================================
"""

from __future__ import annotations

import pathlib

import pytest

from skillspector_quality.quality import score_quality
from skillspector_quality.quality.render import _quality_status
from skillspector_quality.quality.scorers import (
    COHESION_FULL_COSINE,
    COHESION_ZERO_COSINE,
    COVERAGE_FULL_COSINE,
    COVERAGE_ZERO_COSINE,
    DENSITY_FULL_RATIO,
    DENSITY_ZERO_RATIO,
    EXAMPLE_DEPTH_FULL,
    LEXICAL_FULL_MTLD,
    LEXICAL_MIN_TOKENS,
    LEXICAL_ZERO_MTLD,
    READABILITY_BAND,
    SkillDoc,
    _demo_richness,
    _demonstrations,
    _when_specificity,
    clamp01,
)

FIXTURES = pathlib.Path(__file__).parent / "fixtures"

# Corpus percentiles the tiers and bands are anchored to.
CORPUS_P10, CORPUS_P50, CORPUS_P90 = 61, 73, 82


def _bundle(name: str) -> dict[str, str]:
    root = FIXTURES / name
    return {
        str(p.relative_to(root)): p.read_text(encoding="utf-8")
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def _fractions(name: str) -> dict[str, float]:
    report = score_quality(_bundle(name))
    return {c.name: c.earned / c.max for c in report.categories if c.max}


# --------------------------------------------------------------------------- #
# Fixture anchors
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("fixture", "low", "high"),
    [
        ("calib-thin", 45, CORPUS_P10),
        ("calib-typical", CORPUS_P10, CORPUS_P90),
        ("calib-strong", CORPUS_P90 - 3, 95),
    ],
)
def test_fixture_lands_at_its_anchor(fixture: str, low: int, high: int) -> None:
    """Each fixture stays in the percentile band it was authored to occupy."""
    score = score_quality(_bundle(fixture)).score
    assert low <= score <= high, f"{fixture} scored {score}, outside [{low}, {high}]"


def test_fixtures_are_strictly_ordered() -> None:
    """Thin < typical < strong. A calibration that inverts these is broken outright."""
    thin = score_quality(_bundle("calib-thin")).score
    typical = score_quality(_bundle("calib-typical")).score
    strong = score_quality(_bundle("calib-strong")).score
    assert thin < typical < strong


def test_fixture_tiers_match_population_position() -> None:
    """Tier labels track corpus position: strong is top-decile, thin is below p10."""
    assert _quality_status(score_quality(_bundle("calib-strong")).score)[0] == "EXCELLENT"
    assert _quality_status(score_quality(_bundle("calib-thin")).score)[0] in {"POOR", "FAIR"}


# --------------------------------------------------------------------------- #
# Anti-saturation guards — the failure mode calibration existed to fix
# --------------------------------------------------------------------------- #

# Dimensions that were percentile-anchored and must therefore vary across the fixtures.
# Readability, Structural Coherence and Behavioral Configuration are deliberately excluded:
# measurement showed real skills genuinely cluster at full marks on those, so they act as
# violation detectors rather than discriminators (ADR-0007).
CALIBRATED_DIMENSIONS = (
    "Information Density",
    "Lexical Diversity",
    "Topic Coverage",
    "Example Quality",
)


@pytest.mark.parametrize("dimension", CALIBRATED_DIMENSIONS)
def test_calibrated_dimension_is_not_constant(dimension: str) -> None:
    """A calibrated dimension must produce different values for different-quality skills.

    This is the regression guard for the v1 pathology: ``Metadata & Discovery`` returned
    0.875 for all 207 corpus skills and ``Example Quality`` returned 0.0 for 90% of them,
    so both contributed a constant that could not rank anything.
    """
    observed = {
        _fractions(f).get(dimension) for f in ("calib-thin", "calib-typical", "calib-strong")
    }
    observed.discard(None)  # N/A in a fixture is acceptable; being constant is not
    assert len(observed) >= 2, f"{dimension} returned a constant {observed} across fixtures"


def test_example_quality_separates_demonstrated_from_undemonstrated() -> None:
    """The v1 detector scored 90% of real skills at zero. Absence must stay distinguishable."""
    assert _fractions("calib-thin")["Example Quality"] == 0.0
    assert _fractions("calib-strong")["Example Quality"] >= 0.6


# --------------------------------------------------------------------------- #
# Band-edge mapping
# --------------------------------------------------------------------------- #


def _ramp(value: float, zero: float, full: float) -> float:
    """The band-edge mapping every percentile-anchored dimension applies."""
    return clamp01((value - zero) / (full - zero))


def test_density_band_maps_anchors_to_endpoints() -> None:
    assert _ramp(DENSITY_ZERO_RATIO, DENSITY_ZERO_RATIO, DENSITY_FULL_RATIO) == 0.0
    assert _ramp(DENSITY_FULL_RATIO, DENSITY_ZERO_RATIO, DENSITY_FULL_RATIO) == 1.0
    midpoint = (DENSITY_ZERO_RATIO + DENSITY_FULL_RATIO) / 2
    assert 0.4 < _ramp(midpoint, DENSITY_ZERO_RATIO, DENSITY_FULL_RATIO) < 0.6


def test_lexical_band_maps_anchors_to_endpoints() -> None:
    assert _ramp(LEXICAL_ZERO_MTLD, LEXICAL_ZERO_MTLD, LEXICAL_FULL_MTLD) == 0.0
    assert _ramp(LEXICAL_FULL_MTLD, LEXICAL_ZERO_MTLD, LEXICAL_FULL_MTLD) == 1.0


def test_coverage_bands_map_anchors_to_endpoints() -> None:
    """Coverage and cohesion are anchored separately, not to one shared reference."""
    assert _ramp(COVERAGE_ZERO_COSINE, COVERAGE_ZERO_COSINE, COVERAGE_FULL_COSINE) == 0.0
    assert _ramp(COVERAGE_FULL_COSINE, COVERAGE_ZERO_COSINE, COVERAGE_FULL_COSINE) == 1.0
    assert _ramp(COHESION_ZERO_COSINE, COHESION_ZERO_COSINE, COHESION_FULL_COSINE) == 0.0
    assert _ramp(COHESION_FULL_COSINE, COHESION_ZERO_COSINE, COHESION_FULL_COSINE) == 1.0
    assert COVERAGE_FULL_COSINE != COHESION_FULL_COSINE


def test_band_anchors_stay_ordered_and_strict_is_harder() -> None:
    """Zero anchor below full anchor, and strict genuinely raises the bar."""
    from skillspector_quality.quality.scorers import (
        DENSITY_FULL_RATIO_STRICT,
        LEXICAL_FULL_MTLD_STRICT,
    )

    assert DENSITY_ZERO_RATIO < DENSITY_FULL_RATIO < DENSITY_FULL_RATIO_STRICT
    assert LEXICAL_ZERO_MTLD < LEXICAL_FULL_MTLD < LEXICAL_FULL_MTLD_STRICT
    assert READABILITY_BAND[0] < READABILITY_BAND[1]


# --------------------------------------------------------------------------- #
# Length-neutrality — the property calibration must not break
# --------------------------------------------------------------------------- #


def test_specificity_does_not_reward_length_alone() -> None:
    """Padding a description must not raise its score (ADR-0007).

    The v1 function awarded +0.30 for ``len >= 15`` and +0.10 for ``len > 80``, which fired
    for 100% and 99% of real descriptions — a constant, plus an incentive to inflate the most
    token-sensitive text in the system.
    """
    terse = "Use when reconciling invoices. Do not use for payroll."
    padded = terse + " " + ("This skill is quite helpful and generally useful. " * 12)
    assert _when_specificity(padded) <= _when_specificity(terse)


def test_lexical_diversity_is_na_below_reliability_floor() -> None:
    """MTLD is unstable and downward-biased on short text, so it must not be scored there."""
    short = "---\ndescription: a tiny skill\n---\n# Tiny\n" + "Some prose here. " * 20
    names = {c.name for c in score_quality({"SKILL.md": short}).categories}
    assert "Lexical Diversity" not in names

    long_enough = "---\ndescription: a longer skill\n---\n# Longer\n" + " ".join(
        f"Distinct clause number {i} describing separate operational behaviour." for i in range(60)
    )
    doc = SkillDoc.from_file_cache({"SKILL.md": long_enough})
    assert len(doc.all_prose.split()) > LEXICAL_MIN_TOKENS


# --------------------------------------------------------------------------- #
# Example detection breadth
# --------------------------------------------------------------------------- #


def test_demonstrations_detected_by_heading_synonym_and_by_fence() -> None:
    """Both ways real skills write examples must be found (v1 caught only 10% of them)."""
    by_heading = SkillDoc.from_file_cache(
        {"SKILL.md": "# S\n\n## Usage\n\nRun the tool against a directory of inputs.\n"}
    )
    by_fence = SkillDoc.from_file_cache(
        {
            "SKILL.md": "# S\n\n## Running it\n\nInvoke the command like so:\n\n```sh\ntool run\n```\n"
        }
    )
    assert _demonstrations(by_heading)
    assert _demonstrations(by_fence)


def test_demo_richness_grades_rather_than_gates() -> None:
    """Richness must have a middle value, or Example Quality re-saturates at 0/1."""
    paired = "Input:\n```\na\n```\nOutput:\n```\nb\n```\n"
    single = (
        "Invoke the command as shown below to process a batch of records:\n```\ntool run\n```\n"
    )
    empty = "See above for details.\n"
    assert _demo_richness(paired) == 1.0
    assert _demo_richness(single) == 0.5
    assert _demo_richness(empty) == 0.0


def test_example_depth_anchor_is_median_not_upper_percentile() -> None:
    """Depth is length-shaped, so its anchor sits at the corpus median (84), not p90 (191).

    Anchoring a raw word count at p90 would reward padding examples, which costs runtime
    tokens on every invocation.
    """
    assert EXAMPLE_DEPTH_FULL == 84.0
