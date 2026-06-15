"""Deterministic quality rating engine.

``score_quality`` runs every category scorer over a ``file_cache`` and returns a
normalized 0-100 :class:`QualityReport`. No LLM is involved; the result is fully
reproducible.
"""

from __future__ import annotations

from skillspector_quality.quality.models import CategoryScore, QualityReport
from skillspector_quality.quality.scorers import CATEGORY_SCORERS, SkillDoc

__all__ = ["score_quality", "QualityReport", "CategoryScore", "SkillDoc"]

# Dimensions whose primary signal comes from YAML frontmatter fields.
# The frontmatter is stripped before the skill body reaches the LLM, so improvements
# here raise the quality score but do NOT reduce token spend or change LLM output.
# All other dimensions score the prompt body and predict real LLM efficiency.
_FRONTMATTER_CATEGORY_NAMES: frozenset[str] = frozenset({
    "Metadata & Discovery",    # name, description, when_to_use, author, version
    "Behavioral Configuration", # user-invocable, allowed-tools, effort, …
    "Topic Coverage",           # cosine(description, body) — description is frontmatter
})


def score_quality(file_cache: dict[str, str]) -> QualityReport:
    """Compute the quality report for a skill from its file_cache.

    Weighting is additive + normalized: each category contributes its raw ``earned``
    out of its raw ``max``; the final score is ``round(sum(earned)/sum(max) x 100)``.
    Adding categories therefore never breaks the 0-100 range.
    """
    doc = SkillDoc.from_file_cache(file_cache)

    categories: list[CategoryScore] = []
    for name, scorer in CATEGORY_SCORERS:
        items = scorer(doc)
        if not items:
            continue  # N/A dimension: omit so its weight renormalizes away
        earned = sum(e for e, _, _ in items)
        cat_max = sum(m for _, m, _ in items)
        kind = "frontmatter" if name in _FRONTMATTER_CATEGORY_NAMES else "body"
        categories.append(CategoryScore(name=name, earned=earned, max=cat_max, items=items, kind=kind))

    total_earned = sum(c.earned for c in categories)
    total_max = sum(c.max for c in categories)
    score = round(100 * total_earned / total_max) if total_max else 0
    score = max(0, min(100, score))

    return QualityReport(score=score, categories=categories)
