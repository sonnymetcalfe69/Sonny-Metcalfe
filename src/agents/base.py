"""Shared helpers for the five pipeline agents."""

from __future__ import annotations

import json
from typing import Any

from src.llm import DEFAULT_MODEL, call_json

JSON_ONLY_SUFFIX = (
    "\n\nReply with a single JSON object only — no prose before or after it, "
    "no markdown code fences."
)


def run_agent(
    system_prompt: str,
    context: dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    user_content = json.dumps(context, indent=2, default=str)
    return call_json(system_prompt + JSON_ONLY_SUFFIX, user_content, model=model)
