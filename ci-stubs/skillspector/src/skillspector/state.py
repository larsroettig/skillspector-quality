from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict


class SkillspectorState(TypedDict, total=False):
    input_path: str
    output_format: str
    use_llm: bool
    yara_rules_dir: str | None
    file_cache: dict[str, str]
    report_body: str
    risk_score: int
    filtered_findings: list[Any]
    sarif_report: dict[str, Any]
    temp_dir_for_cleanup: str | None
