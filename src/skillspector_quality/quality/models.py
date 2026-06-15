"""Data models for the quality rating."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CategoryScore:
    """Score for a single quality category.

    ``items`` holds the per-sub-check breakdown as ``(earned, max, label)`` tuples,
    mirroring the reference rater's output. ``notes`` is optional LLM commentary; it
    never affects ``earned``/``max``.

    ``kind`` is either ``"body"`` or ``"frontmatter"``:

    * ``"body"`` — scores the prompt text that actually reaches the LLM.  Improving these
      dimensions reduces token spend and improves output quality.
    * ``"frontmatter"`` — scores the YAML metadata block (name, description, when_to_use,
      behavioral config, topic coverage).  The frontmatter is stripped before the skill body
      is sent to any LLM, so improvements here raise the quality score but have no effect on
      token count or LLM output.
    """

    name: str
    earned: int
    max: int
    items: list[tuple[int, int, str]] = field(default_factory=list)
    notes: str | None = None
    kind: str = "body"  # "body" | "frontmatter"

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "earned": self.earned,
            "max": self.max,
            "items": [{"earned": e, "max": m, "label": label} for e, m, label in self.items],
            "notes": self.notes,
            "kind": self.kind,
        }


@dataclass
class QualityReport:
    """Aggregate quality result for one skill."""

    score: int  # 0-100, normalized
    categories: list[CategoryScore] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "score": self.score,
            "categories": [c.to_dict() for c in self.categories],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QualityReport:
        """Rebuild a QualityReport from its serialized dict (graph state round-trip)."""
        cats: list[CategoryScore] = []
        for c in data.get("categories", []) or []:
            items = [(it["earned"], it["max"], it["label"]) for it in c.get("items", []) or []]
            cats.append(
                CategoryScore(
                    name=c["name"],
                    earned=c["earned"],
                    max=c["max"],
                    items=items,
                    notes=c.get("notes"),
                    kind=c.get("kind", "body"),
                )
            )
        return cls(score=int(data["score"]), categories=cats)
