from __future__ import annotations
from typing import Any


def is_llm_available() -> bool:
    return False


def chat_completion(*args: Any, **kwargs: Any) -> str:
    return ""
