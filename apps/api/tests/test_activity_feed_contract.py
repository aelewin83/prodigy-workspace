from types import SimpleNamespace
from uuid import uuid4

from app.api import deals
from app.services.gating import log_boe_run_created


class FakeDB:
    def __init__(self, scalar_responses=None, scalar_list_responses=None):
        self.scalar_responses = list(scalar_responses or [])
        self.scalar_list_responses = list(scalar_list_responses or [])
        self.added = []

    def scalar(self, _stmt):
        return self.scalar_responses.pop(0) if self.scalar_responses else None

    def scalars(self, _stmt):
        values = self.scalar_list_responses.pop(0) if self.scalar_list_responses else []
        return SimpleNamespace(all=lambda: values)

    def add(self, obj):
        self.added.append(obj)


def test_log_boe_run_created_writes_activity_event():
    db = FakeDB()
    run = SimpleNamespace(id=uuid4(), deal_id=uuid4(), version=1, advance=True)
    user_id = uuid4()
    log_boe_run_created(db, run, user_id)
    assert len(db.added) == 2
    gate_event = db.added[1]
    assert gate_event.event_type == "BOE_RUN_CREATED"
    assert gate_event.metadata_json["run_id"] == str(run.id)


def test_activity_feed_returns_normalized_shape():
    deal_obj = SimpleNamespace(id=uuid4(), workspace_id=uuid4())
    gate_event = SimpleNamespace(
        id=uuid4(),
        event_type="OVERRIDE_SET",
        created_at=None,
        metadata_json={"override_by": "u-1"},
        from_status="NEEDS_WORK",
        to_status="ADVANCE",
    )
    comment = SimpleNamespace(id=uuid4(), created_by="u-2", created_at=None, body="Need revised debt quote.")
    user1 = SimpleNamespace(id="u-1", email="owner@example.com", full_name="Owner User")
    user2 = SimpleNamespace(id="u-2", email="member@example.com", full_name="Member User")
    db = FakeDB(
        scalar_responses=[deal_obj, SimpleNamespace(role="OWNER"), SimpleNamespace(role="OWNER")],
        scalar_list_responses=[[gate_event], [comment], [user1, user2]],
    )
    events = deals.get_deal_activity(str(deal_obj.id), 50, db, SimpleNamespace(id=uuid4()))
    assert len(events) == 2
    assert {"id", "type", "created_at", "actor", "summary", "metadata"} <= set(events[0].keys())
    event_types = {e["type"] for e in events}
    assert "GATE_OVERRIDE_SET" in event_types
    assert "COMMENT_ADDED" in event_types
