from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api import deals
from app.models.enums import MemberRole
from app.schemas.deal_workspace import DealCommentCreate, DealOverrideActionRequest


class FakeDB:
    def __init__(self):
        self.committed = False
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, _obj):
        return None


def test_viewer_cannot_override(monkeypatch):
    db = FakeDB()
    deal_obj = SimpleNamespace(id=uuid4())
    monkeypatch.setattr(deals, "_get_deal_with_access", lambda *_args, **_kwargs: deal_obj)
    monkeypatch.setattr(deals, "_get_deal_member", lambda *_args, **_kwargs: SimpleNamespace(role=MemberRole.VIEWER))
    with pytest.raises(HTTPException) as exc:
        deals.override_deal_gate_status(str(uuid4()), DealOverrideActionRequest(status="ADVANCE", comment="ok"), db, SimpleNamespace(id=uuid4()))
    assert exc.value.status_code == 403


def test_member_cannot_override(monkeypatch):
    db = FakeDB()
    deal_obj = SimpleNamespace(id=uuid4())
    monkeypatch.setattr(deals, "_get_deal_with_access", lambda *_args, **_kwargs: deal_obj)
    monkeypatch.setattr(deals, "_get_deal_member", lambda *_args, **_kwargs: SimpleNamespace(role=MemberRole.MEMBER))
    with pytest.raises(HTTPException) as exc:
        deals.override_deal_gate_status(str(uuid4()), DealOverrideActionRequest(status="ADVANCE", comment="ok"), db, SimpleNamespace(id=uuid4()))
    assert exc.value.status_code == 403


def test_admin_override_requires_comment(monkeypatch):
    db = FakeDB()
    deal_obj = SimpleNamespace(id=uuid4())
    monkeypatch.setattr(deals, "_get_deal_with_access", lambda *_args, **_kwargs: deal_obj)
    monkeypatch.setattr(deals, "_get_deal_member", lambda *_args, **_kwargs: SimpleNamespace(role=MemberRole.OWNER))
    with pytest.raises(HTTPException) as exc:
        deals.override_deal_gate_status(str(uuid4()), DealOverrideActionRequest(status="KILL", comment=""), db, SimpleNamespace(id=uuid4()))
    assert exc.value.status_code == 422


def test_viewer_cannot_comment(monkeypatch):
    db = FakeDB()
    deal_obj = SimpleNamespace(id=uuid4())
    monkeypatch.setattr(deals, "_get_deal_with_access", lambda *_args, **_kwargs: deal_obj)
    monkeypatch.setattr(deals, "_get_deal_member", lambda *_args, **_kwargs: SimpleNamespace(role=MemberRole.VIEWER))
    with pytest.raises(HTTPException) as exc:
        deals.create_deal_comment(str(uuid4()), DealCommentCreate(body="note"), db, SimpleNamespace(id=uuid4()))
    assert exc.value.status_code == 403


@pytest.mark.parametrize("role", [MemberRole.OWNER, MemberRole.MEMBER])
def test_admin_and_member_can_comment(monkeypatch, role):
    db = FakeDB()
    deal_obj = SimpleNamespace(id=uuid4())
    monkeypatch.setattr(deals, "_get_deal_with_access", lambda *_args, **_kwargs: deal_obj)
    monkeypatch.setattr(deals, "_get_deal_member", lambda *_args, **_kwargs: SimpleNamespace(role=role))
    out = deals.create_deal_comment(str(uuid4()), DealCommentCreate(body="note"), db, SimpleNamespace(id=uuid4()))
    assert out["body"] == "note"
    assert db.committed is True
