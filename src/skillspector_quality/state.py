"""Graph state for the quality layer.

Subclasses the upstream ``SkillspectorState`` (a ``total=False`` TypedDict) to add the
``quality_report`` channel, without touching the upstream package.
"""

from __future__ import annotations

from skillspector.state import SkillspectorState


class QualityState(SkillspectorState, total=False):  # type: ignore[misc, call-arg]
    """Upstream state plus the quality report produced by ``quality_scorer``."""

    # Serialized QualityReport.to_dict(); a plain dict so it round-trips cleanly
    # through LangGraph state.
    quality_report: dict[str, object]
