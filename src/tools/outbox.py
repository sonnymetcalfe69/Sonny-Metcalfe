"""Approval queue for anything an agent produces that would touch the
outside world (an email draft, a social post, a listing update, a proposed
purchase). Items are plain JSON files — nothing here calls a real API.

Lifecycle: outbox/pending/<id>.json -> outbox/approved/ or outbox/rejected/
via cli.py. Sending/posting/paying is a separate, deliberate integration
you add per channel once you trust the output (see README.md).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUTBOX_DIR = Path(__file__).resolve().parent.parent.parent / "outbox"
PENDING = OUTBOX_DIR / "pending"
APPROVED = OUTBOX_DIR / "approved"
REJECTED = OUTBOX_DIR / "rejected"


def submit(
    business_id: str,
    channel: str,
    action_type: str,  # e.g. "email", "post", "listing_update", "purchase"
    payload: dict[str, Any],
) -> str:
    PENDING.mkdir(parents=True, exist_ok=True)
    item_id = uuid.uuid4().hex[:8]
    item = {
        "id": item_id,
        "business_id": business_id,
        "channel": channel,
        "action_type": action_type,
        "payload": payload,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
    }
    (PENDING / f"{item_id}.json").write_text(json.dumps(item, indent=2))
    return item_id


def list_pending() -> list[dict[str, Any]]:
    PENDING.mkdir(parents=True, exist_ok=True)
    return [json.loads(p.read_text()) for p in sorted(PENDING.glob("*.json"))]


def _find_pending(item_id: str) -> Path | None:
    path = PENDING / f"{item_id}.json"
    return path if path.exists() else None


def approve(item_id: str) -> bool:
    path = _find_pending(item_id)
    if not path:
        return False
    APPROVED.mkdir(parents=True, exist_ok=True)
    item = json.loads(path.read_text())
    item["status"] = "approved"
    item["decided_at"] = datetime.now(timezone.utc).isoformat()
    (APPROVED / path.name).write_text(json.dumps(item, indent=2))
    path.unlink()
    return True


def reject(item_id: str) -> bool:
    path = _find_pending(item_id)
    if not path:
        return False
    REJECTED.mkdir(parents=True, exist_ok=True)
    item = json.loads(path.read_text())
    item["status"] = "rejected"
    item["decided_at"] = datetime.now(timezone.utc).isoformat()
    (REJECTED / path.name).write_text(json.dumps(item, indent=2))
    path.unlink()
    return True
