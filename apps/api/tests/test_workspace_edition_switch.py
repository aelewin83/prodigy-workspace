from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api import workspaces
from app.models.enums import MemberRole, WorkspaceEdition
from app.schemas.workspace import WorkspaceCreate, WorkspaceEditionUpdate
from app.services.workspace_capabilities import capabilities_for_edition


class FakeDB:
    def __init__(self, scalar_responses=None):
        self.scalar_responses = list(scalar_responses or [])
        self.added = []
        self.committed = False

    def scalar(self, _stmt):
        return self.scalar_responses.pop(0) if self.scalar_responses else None

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        return None

    def commit(self):
        self.committed = True

    def refresh(self, _obj):
        return None


def test_capabilities_map_for_editions():
    synd = capabilities_for_edition(WorkspaceEdition.SYNDICATOR)["features"]
    fund = capabilities_for_edition(WorkspaceEdition.FUND)["features"]
    assert synd["fund_mode"] is False
    assert fund["fund_mode"] is True
    assert synd["deals"] is True and fund["deals"] is True


def test_create_workspace_defaults_to_syndicator():
    db = FakeDB()
    user = SimpleNamespace(id=uuid4())
    payload = WorkspaceCreate(name="WS")
    out = workspaces.create_workspace(payload=payload, db=db, user=user)
    assert out["edition"] == WorkspaceEdition.SYNDICATOR
    assert out["is_admin"] is True


def test_non_admin_cannot_change_workspace_edition():
    ws = SimpleNamespace(id=uuid4(), edition=WorkspaceEdition.SYNDICATOR)
    member = SimpleNamespace(role=MemberRole.MEMBER)
    db = FakeDB([ws, member])
    payload = WorkspaceEditionUpdate(edition=WorkspaceEdition.FUND)

    with pytest.raises(HTTPException) as exc:
        workspaces.update_workspace_edition(str(ws.id), payload, db, SimpleNamespace(id=uuid4()))
    assert exc.value.status_code == 403


def test_admin_can_change_workspace_edition_and_audit_logged():
    ws = SimpleNamespace(
        id=uuid4(),
        name="W",
        edition=WorkspaceEdition.SYNDICATOR,
        edition_updated_at=None,
        edition_updated_by_user_id=None,
        created_by=uuid4(),
        created_at=None,
    )
    member = SimpleNamespace(role=MemberRole.OWNER)
    db = FakeDB([ws, member])
    user = SimpleNamespace(id=uuid4())
    payload = WorkspaceEditionUpdate(edition=WorkspaceEdition.FUND)

    out = workspaces.update_workspace_edition(str(ws.id), payload, db, user)
    assert out["edition"] == WorkspaceEdition.FUND
    assert ws.edition_updated_by_user_id == user.id
    assert db.committed is True
    audit = db.added[-1]
    assert audit.action == "workspace.edition_changed"
    assert audit.payload["from_edition"] == "SYNDICATOR"
    assert audit.payload["to_edition"] == "FUND"


def test_noop_edition_change_returns_workspace_without_new_audit():
    ws = SimpleNamespace(
        id=uuid4(),
        name="W",
        edition=WorkspaceEdition.SYNDICATOR,
        edition_updated_at=None,
        edition_updated_by_user_id=None,
        created_by=uuid4(),
        created_at=None,
    )
    member = SimpleNamespace(role=MemberRole.OWNER)
    db = FakeDB([ws, member])
    payload = WorkspaceEditionUpdate(edition=WorkspaceEdition.SYNDICATOR)
    out = workspaces.update_workspace_edition(str(ws.id), payload, db, SimpleNamespace(id=uuid4()))
    assert out["edition"] == WorkspaceEdition.SYNDICATOR
    assert db.committed is False
    assert db.added == []


def test_get_workspace_includes_edition_and_capabilities():
    ws = SimpleNamespace(
        id=uuid4(),
        name="W",
        edition=WorkspaceEdition.FUND,
        edition_updated_at=None,
        edition_updated_by_user_id=None,
        created_by=uuid4(),
        created_at=None,
    )
    member = SimpleNamespace(role=MemberRole.OWNER)
    db = FakeDB([ws, member])
    out = workspaces.get_workspace(str(ws.id), db, SimpleNamespace(id=uuid4()))
    assert out["edition"] == WorkspaceEdition.FUND
    assert out["capabilities"]["features"]["fund_mode"] is True
    assert out["is_admin"] is True


def test_get_workspace_capabilities_requires_membership():
    ws = SimpleNamespace(id=uuid4(), edition=WorkspaceEdition.SYNDICATOR)
    db = FakeDB([ws, None])
    with pytest.raises(HTTPException) as exc:
        workspaces.get_workspace_capabilities(str(ws.id), db, SimpleNamespace(id=uuid4()))
    assert exc.value.status_code == 403
