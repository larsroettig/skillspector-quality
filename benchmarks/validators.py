"""Output validators for the 3-arm benchmark.

Two-layer validation mirrors the ponytail benchmark design:
  1. Schema validation  — required keys present, types correct  (always measured)
  2. Semantic check     — deterministic values match known expected output (pass/fail gate)

A response must pass BOTH layers to be counted as correct.
"""

from __future__ import annotations

import json
import re
from typing import Any


def _strip_fences(text: str) -> str:
    """Remove markdown code fences from LLM output before JSON parsing."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # drop opening fence line (```json, ```  etc.)
        start = 1
        # drop closing fence if present
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[start:end]).strip()
    return text


def _extract_json(text: str) -> str:
    """Extract a JSON object from text that may contain prose or markdown fences.

    Handles three cases:
      1. Bare JSON object — returned as-is after stripping fences.
      2. Markdown-fenced JSON — fences stripped by _strip_fences.
      3. JSON embedded in prose — scan for the first balanced {...} block.
    """
    text = _strip_fences(text)
    if not text:
        return text
    if text.lstrip().startswith("{"):
        return text.lstrip()
    # Scan for a balanced JSON object in prose responses
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text


def validate(
    output: str,
    required_keys: list[str],
    expected: dict[str, Any],
    enum_fields: dict[str, list[str]] | None = None,
) -> tuple[bool, str]:
    """Validate LLM output against a JSON schema and known expected values.

    Args:
        output: Raw LLM response text.
        required_keys: All keys that must be present in the JSON object.
        expected: Deterministic key→value pairs to check for exact equality.
            Booleans and integers are checked exactly; strings case-insensitively.
        enum_fields: Optional map of field → allowed string values (checked
            case-insensitively).

    Returns:
        (passed, reason) where reason is "ok" on success or a human-readable
        failure description.
    """
    # ── 1. Parse JSON ────────────────────────────────────────────────────────
    text = _extract_json(output)
    if not text:
        return False, "empty output"
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return False, f"invalid JSON: {exc}"

    if not isinstance(data, dict):
        return False, f"expected a JSON object, got {type(data).__name__}"

    # ── 2. Required keys ─────────────────────────────────────────────────────
    missing = [k for k in required_keys if k not in data]
    if missing:
        return False, f"missing keys: {missing}"

    # ── 3. Type checks for list fields ───────────────────────────────────────
    for key in required_keys:
        val = data.get(key)
        if val is None:
            continue
        # If the expected value is a list, the actual value must also be a
        # non-empty list.
        if isinstance(expected.get(key), list) or (
            enum_fields is None and isinstance(val, list)
        ):
            pass  # lists validated below in semantic check
        # Any field whose name suggests a list but has no expected entry:
        # just check it isn't a string disguised as a list.

    # ── 4. Enum field checks ─────────────────────────────────────────────────
    if enum_fields:
        for key, allowed in enum_fields.items():
            if key not in data:
                continue
            actual_str = str(data[key]).lower()
            allowed_lower = [v.lower() for v in allowed]
            if actual_str not in allowed_lower:
                return False, f"{key}={data[key]!r} not in {allowed}"

    # ── 5. Exact semantic checks ─────────────────────────────────────────────
    for key, exp_val in expected.items():
        if key not in data:
            continue
        actual = data[key]

        if isinstance(exp_val, bool):
            # bool must come before int check (bool is subclass of int in Python)
            if not isinstance(actual, bool) or actual != exp_val:
                return False, f"{key}: expected {exp_val}, got {actual!r}"

        elif isinstance(exp_val, int):
            if not isinstance(actual, int) or actual != exp_val:
                return False, f"{key}: expected {exp_val}, got {actual!r}"

        elif isinstance(exp_val, str):
            if str(actual).lower() != exp_val.lower():
                return False, f"{key}: expected {exp_val!r}, got {actual!r}"

        elif isinstance(exp_val, list):
            # Just check it is a non-empty list — exact items vary across runs
            if not isinstance(actual, list) or len(actual) == 0:
                return False, f"{key}: expected non-empty list, got {actual!r}"

    return True, "ok"
