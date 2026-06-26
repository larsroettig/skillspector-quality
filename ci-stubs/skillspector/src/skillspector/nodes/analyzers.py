from __future__ import annotations

from typing import Any


def _stub_analyzer(state: dict[str, Any]) -> dict[str, Any]:
    return {"findings": []}


ANALYZER_NODE_IDS: list[str] = ["stub_analyzer"]
ANALYZER_NODES: dict[str, Any] = {"stub_analyzer": _stub_analyzer}
