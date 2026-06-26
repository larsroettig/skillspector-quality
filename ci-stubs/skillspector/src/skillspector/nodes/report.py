from __future__ import annotations

import json
from typing import Any


def report(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "report_body": json.dumps({"findings": [], "risk_score": 0}),
        "risk_score": 0,
        "sarif_report": {"runs": [{"results": [], "tool": {"driver": {"name": "skillspector-stub"}}}]},
    }
