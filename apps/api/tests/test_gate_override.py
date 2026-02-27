from types import SimpleNamespace
from uuid import uuid4

from app.boe.engine import BOEDecision, GateStatus
from app.models.enums import DealStatus
from app.services.gating import apply_computed_gate_status, map_decision_to_deal_status, set_gate_override


class FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)


def _decision(status: GateStatus, advance: bool) -> BOEDecision:
    return BOEDecision(
        status=status,
        hard_veto_ok=status != GateStatus.BLOCKED,
        pass_count=4 if advance else 3,
        total_tests=7,
        failed_hard_tests=[],
        failed_soft_tests=[],
        warn_tests=[],
        pass_tests=[],
        na_tests=[],
        advance=advance,
    )


def test_computed_transition_logs_once_for_initial_change():
    db = FakeDB()
    deal = SimpleNamespace(
        id=uuid4(),
        gate_status=DealStatus.NEEDS_WORK,
        gate_status_computed=DealStatus.NEEDS_WORK,
        gate_override_status=None,
        gate_updated_at=None,
    )

    changed = apply_computed_gate_status(
        db,
        deal,
        DealStatus.ADVANCE,
        reason="Computed from BOE run",
        metadata_json={"run_id": str(uuid4())},
    )

    assert changed is True
    assert deal.gate_status == DealStatus.ADVANCE
    assert deal.gate_status_computed == DealStatus.ADVANCE
    assert len(db.added) == 1
    assert db.added[0].event_type == "COMPUTED_TRANSITION"


def test_computed_transition_no_duplicate_when_status_unchanged():
    db = FakeDB()
    deal = SimpleNamespace(
        id=uuid4(),
        gate_status=DealStatus.BLOCKED,
        gate_status_computed=DealStatus.BLOCKED,
        gate_override_status=None,
        gate_updated_at=None,
    )

    changed = apply_computed_gate_status(
        db,
        deal,
        DealStatus.BLOCKED,
        reason="Computed from BOE run",
        metadata_json={"run_id": str(uuid4())},
    )

    assert changed is False
    assert len(db.added) == 0


def test_computed_transition_first_then_same_status_logs_once():
    db = FakeDB()
    deal = SimpleNamespace(
        id=uuid4(),
        gate_status=DealStatus.NEEDS_WORK,
        gate_status_computed=DealStatus.NEEDS_WORK,
        gate_override_status=None,
        gate_updated_at=None,
    )
    first = apply_computed_gate_status(
        db,
        deal,
        DealStatus.BLOCKED,
        reason="Computed from BOE run",
        metadata_json={"run_id": str(uuid4())},
    )
    second = apply_computed_gate_status(
        db,
        deal,
        DealStatus.BLOCKED,
        reason="Computed from BOE run",
        metadata_json={"run_id": str(uuid4())},
    )
    assert first is True
    assert second is False
    assert len(db.added) == 1


def test_override_set_and_clear_updates_effective_status_and_logs():
    db = FakeDB()
    deal = SimpleNamespace(
        id=uuid4(),
        gate_status=DealStatus.NEEDS_WORK,
        gate_status_computed=DealStatus.NEEDS_WORK,
        gate_override_status=None,
        gate_override_reason=None,
        gate_override_by=None,
        gate_override_at=None,
        gate_updated_at=None,
    )

    changed_set = set_gate_override(
        db,
        deal,
        override_status=DealStatus.APPROVED,
        reason="IC approval override",
        override_by=str(uuid4()),
    )
    assert changed_set is True
    assert deal.gate_status == DealStatus.APPROVED
    assert deal.gate_override_status == DealStatus.APPROVED
    assert db.added[-1].event_type == "OVERRIDE_SET"

    changed_clear = set_gate_override(
        db,
        deal,
        override_status=None,
        reason=None,
        override_by=str(uuid4()),
    )
    assert changed_clear is True
    assert deal.gate_override_status is None
    assert deal.gate_status == DealStatus.NEEDS_WORK
    assert db.added[-1].event_type == "OVERRIDE_CLEARED"


def test_map_decision_to_deal_status_matches_expected_buckets():
    assert map_decision_to_deal_status(_decision(GateStatus.BLOCKED, advance=False)) == DealStatus.BLOCKED
    assert map_decision_to_deal_status(_decision(GateStatus.NEEDS_WORK, advance=False)) == DealStatus.NEEDS_WORK
    assert map_decision_to_deal_status(_decision(GateStatus.ADVANCE, advance=True)) == DealStatus.ADVANCE
