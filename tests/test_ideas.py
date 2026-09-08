from src.tools import ideas


def test_add_and_list(tmp_path, monkeypatch):
    monkeypatch.setattr(ideas, "IDEAS_DIR", tmp_path)
    idea = ideas.add_idea("biz1", "a video about keyboard switches")
    assert idea["status"] == "pending"
    assert ideas.list_ideas("biz1") == [idea]
    assert ideas.list_ideas("biz1", status="pending") == [idea]
    assert ideas.list_ideas("biz1", status="done") == []


def test_next_pending_skips_non_pending(tmp_path, monkeypatch):
    monkeypatch.setattr(ideas, "IDEAS_DIR", tmp_path)
    first = ideas.add_idea("biz1", "first idea")
    ideas.mark_status("biz1", first["id"], "done")
    second = ideas.add_idea("biz1", "second idea")

    next_up = ideas.next_pending("biz1")
    assert next_up["id"] == second["id"]


def test_next_pending_none_when_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(ideas, "IDEAS_DIR", tmp_path)
    assert ideas.next_pending("biz1") is None


def test_mark_status_unknown_id_returns_false(tmp_path, monkeypatch):
    monkeypatch.setattr(ideas, "IDEAS_DIR", tmp_path)
    assert ideas.mark_status("biz1", "nope", "done") is False
