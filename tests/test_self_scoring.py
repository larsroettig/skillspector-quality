"""Self-scoring gate: the project's own SKILL.md must score GOOD tier (>=75)."""

from pathlib import Path

import pytest

from skillspector_quality.quality import score_quality

REPO_ROOT = Path(__file__).parent.parent
MIN_SELF_SCORE = 75


@pytest.mark.self
def test_self_score_meets_threshold() -> None:
    """Tool scores its own SKILL.md at GOOD tier or above."""
    file_cache: dict[str, str] = {}
    for name in ("SKILL.md", "reference.md", "examples.md"):
        path = REPO_ROOT / name
        if path.exists():
            file_cache[name] = path.read_text(encoding="utf-8")

    report = score_quality(file_cache)
    assert report.score >= MIN_SELF_SCORE, (
        f"Self-score {report.score} < {MIN_SELF_SCORE}.\n"
        + "\n".join(f"  {c.name}: {c.earned}/{c.max}" for c in report.categories)
    )
