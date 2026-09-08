from src import state


def test_load_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", tmp_path)
    s = state.load("biz1")
    assert s == {"business_id": "biz1", "history": []}


def test_record_cycle_appends_and_caps_history(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", tmp_path)

    for i in range(35):
        state.record_cycle("biz1", {"priorities": [f"p{i}"]})

    s = state.load("biz1")
    assert len(s["history"]) == 30
    assert s["history"][-1]["priorities"] == ["p34"]
    assert s["last_cycle"]["priorities"] == ["p34"]

    recent = state.recent_history("biz1", n=2)
    assert len(recent) == 2
