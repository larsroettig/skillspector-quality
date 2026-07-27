"""Token-cost axis: what a skill costs an agent, reported separately from what it is worth.

Cost is **orthogonal to quality**, which is why it gets its own score rather than being folded
into the quality number. Measured over 207 real skills, the correlation between the quality
score and token cost is +0.14 on-invoke and +0.05 always-on — the quality score predicts
essentially nothing about spend. Blending them would destroy information: a cheap sloppy skill
and a polished bloated one would collapse onto the same number. See ADR-0009.

Higher is cheaper, matching the quality axis's "higher is better" direction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from skillspector_quality.quality.scorers import (
    DuplicateSpan,
    SkillDoc,
    _duplicate_spans,
    clamp01,
)

# --------------------------------------------------------------------------- #
# The cost model
#
# A token's lifetime cost depends on how often it is loaded, and the three tiers differ by
# orders of magnitude. Rather than hard-code a weight ratio, the weights are DERIVED from two
# stated assumptions, so the premise is arguable instead of buried in a magic number.
#
# These are assumptions, not measurements. Nothing in the corpus can validate them — they
# encode how often a typical skill fires, which depends entirely on how someone works. Change
# them and the weights follow.
# --------------------------------------------------------------------------- #

ASSUMED_INVOCATION_RATE = 1 / 50  # a skill fires in roughly 1 session out of 50
ASSUMED_DOC_READ_RATE = 0.4  # a supporting doc is read in ~40% of invocations

# always-on: the description is loaded for EVERY skill in EVERY session, whether or not the
# skill is used. This is why a 76-token description outweighs a 1,500-token body over a
# skill's life, despite being 20x smaller.
WEIGHT_ALWAYS_ON = 1.0
WEIGHT_ON_INVOKE = ASSUMED_INVOCATION_RATE
WEIGHT_ON_DEMAND = ASSUMED_INVOCATION_RATE * ASSUMED_DOC_READ_RATE

# Percentile anchors for the weighted total, measured over the same 207-skill corpus as the
# quality bands (p10 = cheap, p90 = expensive). See docs/calibration-report.md.
COST_CHEAP_TOKENS = 75.0
COST_EXPENSIVE_TOKENS = 331.0

# Rough chars-per-token for English prose. Deliberately not a real tokenizer: that would add a
# model-specific dependency to a tool whose whole premise is determinism, and the score is a
# percentile rank where a consistent constant factor cancels out.
CHARS_PER_TOKEN = 4.0

# Cost tiers, anchored to corpus quartiles of the resulting score (p25 -> 90, p50 -> 58,
# p75 -> 35). A tier names a population position, exactly as the quality tiers do.
COST_LEVELS: list[tuple[int, str, str]] = [
    (88, "LEAN", "CHEAP TO KEEP INSTALLED"),
    (58, "MODERATE", "TYPICAL FOOTPRINT"),
    (35, "HEAVY", "TRIM THE ALWAYS-ON TIER"),
    (0, "BLOATED", "COSTS MORE THAN IT LIKELY RETURNS"),
]

# Duplicate spans smaller than this are noise (shared headings, boilerplate phrases).
_MIN_DUPLICATE_TOKENS = 30


def estimate_tokens(text: str) -> int:
    return round(len(text) / CHARS_PER_TOKEN)


@dataclass
class CostTier:
    """One loading tier: how many tokens it holds and how often they are paid."""

    name: str
    detail: str
    raw_tokens: int
    weight: float

    @property
    def weighted_tokens(self) -> float:
        return self.raw_tokens * self.weight

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "detail": self.detail,
            "raw_tokens": self.raw_tokens,
            "weight": round(self.weight, 5),
            "weighted_tokens": round(self.weighted_tokens, 2),
        }


@dataclass
class CostReport:
    """Cost result for one skill. Higher ``score`` means cheaper."""

    score: int  # 0-100, higher = cheaper
    tiers: list[CostTier] = field(default_factory=list)
    weighted_total: float = 0.0
    duplicate_tokens: int = 0
    duplicate_spans: list[DuplicateSpan] = field(default_factory=list)

    @property
    def raw_total(self) -> int:
        return sum(t.raw_tokens for t in self.tiers)

    def to_dict(self) -> dict[str, object]:
        return {
            "score": self.score,
            "weighted_total_tokens": round(self.weighted_total, 2),
            "raw_total_tokens": self.raw_total,
            "tiers": [t.to_dict() for t in self.tiers],
            "recoverable": {
                "duplicate_tokens": self.duplicate_tokens,
                "spans": [
                    {"source": s.source, "target": s.target, "shared_tokens": s.shared_tokens}
                    for s in self.duplicate_spans
                ],
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CostReport:
        """Rebuild from the serialized form (LangGraph state round-trip)."""
        raw_tiers = data.get("tiers")
        tiers = [
            CostTier(
                name=str(t.get("name", "")),
                detail=str(t.get("detail", "")),
                raw_tokens=int(t.get("raw_tokens", 0) or 0),
                weight=float(t.get("weight", 0.0) or 0.0),
            )
            for t in (raw_tiers if isinstance(raw_tiers, list) else [])
            if isinstance(t, dict)
        ]
        recoverable = data.get("recoverable")
        recoverable = recoverable if isinstance(recoverable, dict) else {}
        raw_spans = recoverable.get("spans")
        spans = [
            DuplicateSpan(
                source=str(s.get("source", "")),
                target=str(s.get("target", "")),
                shared_tokens=int(s.get("shared_tokens", 0) or 0),
            )
            for s in (raw_spans if isinstance(raw_spans, list) else [])
            if isinstance(s, dict)
        ]
        return cls(
            score=int(data.get("score", 0) or 0),
            tiers=tiers,
            weighted_total=float(data.get("weighted_total_tokens", 0.0) or 0.0),
            duplicate_tokens=int(recoverable.get("duplicate_tokens", 0) or 0),
            duplicate_spans=spans,
        )


def cost_status(score: int) -> tuple[str, str]:
    """Return ``(tier, recommendation)`` for a 0-100 cost score."""
    for threshold, tier, recommendation in COST_LEVELS:
        if score >= threshold:
            return tier, recommendation
    return "BLOATED", "COSTS MORE THAN IT LIKELY RETURNS"


def score_cost(doc: SkillDoc) -> CostReport:
    """Compute the tier-weighted cost score for a parsed skill."""
    description = str(doc.data.get("description") or "")
    on_demand_tokens = sum(estimate_tokens(c) for c in doc.markdown_docs.values())
    on_demand_tokens += sum(estimate_tokens(c) for c in doc.scripts.values())

    tiers = [
        CostTier(
            "always-on",
            "description — loaded for every skill in every session",
            estimate_tokens(description),
            WEIGHT_ALWAYS_ON,
        ),
        CostTier(
            "on-invoke",
            "SKILL.md body — loaded when the skill fires",
            estimate_tokens(doc.body),
            WEIGHT_ON_INVOKE,
        ),
        CostTier(
            "on-demand",
            "supporting docs and scripts — loaded only if the agent reads them",
            on_demand_tokens,
            WEIGHT_ON_DEMAND,
        ),
    ]

    weighted_total = sum(t.weighted_tokens for t in tiers)
    # Higher score = cheaper, so the ramp is inverted relative to the quality bands.
    ratio = (weighted_total - COST_CHEAP_TOKENS) / (COST_EXPENSIVE_TOKENS - COST_CHEAP_TOKENS)
    score = round(100 * (1.0 - clamp01(ratio)))

    spans = [s for s in _duplicate_spans(doc) if s.shared_tokens >= _MIN_DUPLICATE_TOKENS]
    duplicate_tokens = sum(s.shared_tokens for s in spans)

    return CostReport(
        score=score,
        tiers=tiers,
        weighted_total=weighted_total,
        duplicate_tokens=duplicate_tokens,
        duplicate_spans=spans,
    )
