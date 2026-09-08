"""Thin wrapper around the Anthropic API for agent calls.

Each agent sends a system prompt plus context and asks for a JSON object
back. This keeps every agent's output structured and easy to persist/render,
without needing a full tool-use loop for what is fundamentally a
research-and-draft pipeline.
"""

from __future__ import annotations

import json
import os
from typing import Any

DEFAULT_MODEL = "claude-sonnet-5"


class LLMError(RuntimeError):
    pass


def _client():
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover
        raise LLMError(
            "The 'anthropic' package is required. Run: pip install -r requirements.txt"
        ) from exc

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMError("Set the ANTHROPIC_API_KEY environment variable.")
    return anthropic.Anthropic(api_key=api_key)


def call_json(
    system_prompt: str,
    user_content: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2000,
) -> dict[str, Any]:
    """Call the model and parse a JSON object from its reply.

    The system prompt is expected to instruct the model to reply with a
    single JSON object and nothing else. Falls back to wrapping the raw
    text if parsing fails, so a malformed response never crashes a cycle.
    """
    client = _client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return {"raw_response": text, "parse_error": True}
