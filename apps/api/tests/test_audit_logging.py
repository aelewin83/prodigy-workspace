from types import SimpleNamespace
from uuid import uuid4

from app.services.gating import log_boe_run_created


class FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)


def test_create_run_audit_log_written():
    db = FakeDB()
    run = SimpleNamespace(id=uuid4(), deal_id=uuid4(), version=3, advance=True)
    user_id = uuid4()

    log_boe_run_created(db, run, user_id)

    assert len(db.added) == 2
    log = db.added[0]
    assert log.entity_type == "boe_run"
    assert log.action == "CREATE_RUN"
    assert log.new_state == "ADVANCE"
    assert log.created_by == user_id
    gate_event = db.added[1]
    assert gate_event.event_type == "BOE_RUN_CREATED"
