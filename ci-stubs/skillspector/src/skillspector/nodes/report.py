from __future__ import annotations

import json
from typing import Any


def report(state: dict[str, Any]) -> dict[str, Any]:
    fmt = state.get("output_format", "json")
    risk_payload = {"risk_assessment": {"risk_score": 0, "findings": []}, "risk_score": 0}

    if fmt == "markdown":
        body = "# SkillSpector Security Report\n\nNo security issues detected.\n"
    elif fmt == "sarif":
        body = json.dumps({"runs": [{"results": [], "tool": {"driver": {"name": "skillspector-stub"}}}]})
    else:
        body = json.dumps(risk_payload)

    return {
        "report_body": body,
        "risk_score": 0,
        "sarif_report": {"runs": [{"results": [], "tool": {"driver": {"name": "skillspector-stub"}}}]},
    }
