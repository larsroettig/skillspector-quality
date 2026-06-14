"""Optional LLM commentary for the quality report.

This is strictly advisory: it attaches a short prose ``notes`` string to weak categories.
It NEVER changes any numeric score. Every failure mode (no key, ``--no-llm``, network
error, malformed response) degrades silently to "no notes".
"""

from __future__ import annotations

import json
import re

from skillspector_quality.quality.models import QualityReport

_PROMPT_HEADER = (
    "You are reviewing the authoring quality of an AI agent 'skill'. Below are quality "
    "categories with their earned/max points. For each category that did NOT earn full "
    "marks, give ONE concise, concrete improvement tip (max 20 words). Return ONLY a JSON "
    "object mapping the exact category name to its tip. No prose outside the JSON.\n\n"
)


def _build_prompt(report: QualityReport) -> str:
    lines = [_PROMPT_HEADER]
    for c in report.categories:
        if c.earned < c.max:
            detail = "; ".join(label for _, _, label in c.items)
            lines.append(f"- {c.name} ({c.earned}/{c.max}): {detail}")
    lines.append('\n\nJSON only, e.g. {"Readability": "Shorten sentences..."}')
    return "\n".join(lines)


def _parse_notes(raw: str) -> dict[str, str]:
    """Best-effort extraction of a JSON object from the model response."""
    raw = raw.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items() if isinstance(v, (str, int, float))}


def add_notes(report: QualityReport, model: str | None = None) -> QualityReport:
    """Attach advisory notes to weak categories by mutating ``report`` in-place.

    Returns the same (mutated) report object. On any error the report is returned
    unchanged (notes stay ``None``).
    """
    # Import here so the engine has no hard import-time dependency on LLM internals.
    from skillspector.llm_utils import chat_completion, is_llm_available

    available, _ = is_llm_available()
    if not available:
        return report

    weak = [c for c in report.categories if c.earned < c.max]
    if not weak:
        return report

    try:
        raw = chat_completion(_build_prompt(report), model=model)
    except Exception:
        return report

    notes = _parse_notes(raw)
    if not notes:
        return report

    for c in report.categories:
        if c.name in notes:
            c.notes = notes[c.name]
    return report
