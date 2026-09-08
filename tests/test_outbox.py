from src.tools import outbox


def _patch_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(outbox, "OUTBOX_DIR", tmp_path)
    monkeypatch.setattr(outbox, "PENDING", tmp_path / "pending")
    monkeypatch.setattr(outbox, "APPROVED", tmp_path / "approved")
    monkeypatch.setattr(outbox, "REJECTED", tmp_path / "rejected")


def test_submit_list_approve(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)

    item_id = outbox.submit("biz1", "email", "email", {"body": "hello"})
    pending = outbox.list_pending()
    assert len(pending) == 1
    assert pending[0]["id"] == item_id
    assert pending[0]["status"] == "pending"

    assert outbox.approve(item_id) is True
    assert outbox.list_pending() == []
    assert (outbox.APPROVED / f"{item_id}.json").exists()


def test_reject_unknown_item_returns_false(tmp_path, monkeypatch):
    _patch_dirs(tmp_path, monkeypatch)
    assert outbox.reject("doesnotexist") is False
