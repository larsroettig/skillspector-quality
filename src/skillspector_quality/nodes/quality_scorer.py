"""quality_scorer node: computes the deterministic quality report, then (optionally)
adds advisory LLM notes.

The numeric score/grade are computed BEFORE and INDEPENDENTLY of any LLM call, so the
result is byte-identical with or without an LLM.
"""

from __future__ import annotations

import logging

from skillspector_quality.quality import score_quality
from skillspector_quality.state import QualityState

logger = logging.getLogger(__name__)

# Model-config slot key, so users can override the commentary model if desired.
ANALYZER_ID = "quality_scorer"


def quality_scorer(state: QualityState) -> dict[str, object]:
    """Score quality from the shared file_cache; attach LLM notes when available."""
    file_cache: dict[str, str] = state.get("file_cache") or {}
    report = score_quality(file_cache)

    # Advisory LLM commentary — last, optional, and never affects the score.
    if state.get("use_llm", True):
        try:
            from skillspector_quality.quality.commentary import add_notes

            model_config: dict[str, str] = state.get("model_config") or {}
            model = model_config.get(ANALYZER_ID) or model_config.get("default")
            report = add_notes(report, model=model)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("quality commentary skipped: %s", exc)

    return {"quality_report": report.to_dict()}
