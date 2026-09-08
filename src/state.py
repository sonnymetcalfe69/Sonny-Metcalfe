"""Per-business persistent state: a JSON file under state/<business_id>.json.

Keeps last cycle's priorities, research notes, and metrics history so each
day's agents have continuity instead of starting from zero.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_DIR = Path(__file__).resolve().parent.parent / "state"

# Pseudo business id the portfolio-level manager agent's cycle results are
# stored under (see src/agents/manager.py, src/orchestrator.py). Not a real
# business — a business config should never use this as its id.
OVERVIEW_ID = "_overview"


def _path(business_id: str) -> Path:
    return STATE_DIR / f"{business_id}.json"


def load(business_id: str) -> dict[str, Any]:
    path = _path(business_id)
    if not path.exists():
        return {"business_id": business_id, "history": []}
    return json.loads(path.read_text())


def save(business_id: str, state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    _path(business_id).write_text(json.dumps(state, indent=2, default=str))


def record_cycle(business_id: str, entry: dict[str, Any]) -> dict[str, Any]:
    """Append a cycle's results to history and persist. Returns updated state."""
    state = load(business_id)
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), **entry}
    state.setdefault("history", []).append(entry)
    state["history"] = state["history"][-30:]  # keep last 30 cycles
    state["last_cycle"] = entry
    save(business_id, state)
    return state


def recent_history(business_id: str, n: int = 5) -> list[dict[str, Any]]:
    return load(business_id).get("history", [])[-n:]
