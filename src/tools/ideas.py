"""Per-business idea queue: state/<business_id>_ideas.json.

You drop in raw ideas (a video concept, a product concept); the next cycle
picks the oldest pending one and the pipeline expands it into a full draft
instead of working from generic goals. This is the mechanism behind
"automated after I input my ideas" — you feed ideas, the agents turn each
into a finished draft for your approval.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

IDEAS_DIR = Path(__file__).resolve().parent.parent.parent / "state"


def _path(business_id: str) -> Path:
    return IDEAS_DIR / f"{business_id}_ideas.json"


def load(business_id: str) -> list[dict[str, Any]]:
    path = _path(business_id)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _save(business_id: str, ideas: list[dict[str, Any]]) -> None:
    IDEAS_DIR.mkdir(parents=True, exist_ok=True)
    _path(business_id).write_text(json.dumps(ideas, indent=2))


def add_idea(business_id: str, text: str) -> dict[str, Any]:
    ideas = load(business_id)
    idea = {
        "id": uuid.uuid4().hex[:8],
        "text": text,
        "status": "pending",  # pending -> in_progress -> done
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    ideas.append(idea)
    _save(business_id, ideas)
    return idea


def list_ideas(business_id: str, status: str | None = None) -> list[dict[str, Any]]:
    ideas = load(business_id)
    if status:
        ideas = [i for i in ideas if i["status"] == status]
    return ideas


def next_pending(business_id: str) -> dict[str, Any] | None:
    for idea in load(business_id):
        if idea["status"] == "pending":
            return idea
    return None


def mark_status(business_id: str, idea_id: str, status: str) -> bool:
    ideas = load(business_id)
    for idea in ideas:
        if idea["id"] == idea_id:
            idea["status"] = status
            idea["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save(business_id, ideas)
            return True
    return False
