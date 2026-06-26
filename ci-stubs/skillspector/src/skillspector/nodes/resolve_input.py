"""Stub resolve_input: reads files from input_path into file_cache."""
from __future__ import annotations

import pathlib
from typing import Any

_TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".txt", ".json", ".toml"}


def resolve_input(state: dict[str, Any]) -> dict[str, Any]:
    input_path = state.get("input_path", "")
    p = pathlib.Path(input_path)

    if not p.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    file_cache: dict[str, str] = {}
    if p.is_file():
        if p.suffix in _TEXT_SUFFIXES:
            file_cache[p.name] = p.read_text(encoding="utf-8", errors="replace")
    else:
        for child in sorted(p.rglob("*")):
            if child.is_file() and child.suffix in _TEXT_SUFFIXES:
                rel = str(child.relative_to(p))
                file_cache[rel] = child.read_text(encoding="utf-8", errors="replace")

    return {"file_cache": file_cache}
