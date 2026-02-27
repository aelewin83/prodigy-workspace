from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.boe.engine import BOEDecision, GateStatus
from app.models.entities import AuditLog, BOERun, Deal, DealGateEvent
from app.models.enums import DealGateState, DealStatus


@dataclass(frozen=True)
class GateTransition:
    previous_state: DealGateState
    new_state: DealGateState


def compute_gate_state(latest_run: BOERun | None) -> DealGateState:
    if latest_run is None:
        return DealGateState.NO_RUN
    return DealGateState.ADVANCE if latest_run.advance else DealGateState.KILL


def map_decision_to_deal_status(decision: BOEDecision) -> DealStatus:
    if decision.status == GateStatus.BLOCKED:
        return DealStatus.BLOCKED
    if decision.status == GateStatus.ADVANCE:
        return DealStatus.ADVANCE
    return DealStatus.NEEDS_WORK


def _append_deal_gate_event(
    db: Session,
    *,
    deal_id,
    event_type: str,
    from_status: DealStatus | None,
    to_status: DealStatus,
    source: str,
    reason: str | None,
    metadata_json: dict[str, Any] | None,
) -> None:
    db.add(
        DealGateEvent(
            deal_id=deal_id,
            event_type=event_type,
            from_status=from_status.value if from_status is not None else None,
            to_status=to_status.value,
            source=source,
            reason=reason,
            metadata_json=metadata_json,
        )
    )


def apply_computed_gate_status(
    db: Session,
    deal: Deal,
    computed_status: DealStatus,
    *,
    reason: str | None = None,
    metadata_json: dict[str, Any] | None = None,
) -> bool:
    previous_effective = deal.gate_status
    deal.gate_status_computed = computed_status
    if deal.gate_override_status is None:
        deal.gate_status = computed_status
    deal.gate_updated_at = datetime.now(timezone.utc)

    if previous_effective == deal.gate_status:
        return False

    _append_deal_gate_event(
        db,
        deal_id=deal.id,
        event_type="COMPUTED_TRANSITION",
        from_status=previous_effective,
        to_status=deal.gate_status,
        source="BOE_RUN",
        reason=reason,
        metadata_json=metadata_json,
    )
    return True


def set_gate_override(
    db: Session,
    deal: Deal,
    *,
    override_status: DealStatus | None,
    reason: str | None,
    override_by: str | None,
) -> bool:
    previous_effective = deal.gate_status

    if override_status is None:
        deal.gate_override_status = None
        deal.gate_override_reason = None
        deal.gate_override_by = None
        deal.gate_override_at = None
        deal.gate_status = deal.gate_status_computed
        event_type = "OVERRIDE_CLEARED"
        source = "USER_OVERRIDE"
    else:
        deal.gate_override_status = override_status
        deal.gate_override_reason = reason
        deal.gate_override_by = override_by
        deal.gate_override_at = datetime.now(timezone.utc)
        deal.gate_status = override_status
        event_type = "OVERRIDE_SET"
        source = "USER_OVERRIDE"

    deal.gate_updated_at = datetime.now(timezone.utc)
    if previous_effective == deal.gate_status:
        return False

    _append_deal_gate_event(
        db,
        deal_id=deal.id,
        event_type=event_type,
        from_status=previous_effective,
        to_status=deal.gate_status,
        source=source,
        reason=reason,
        metadata_json={"override_by": override_by} if override_by else None,
    )
    return True


def transition_deal_gate(db: Session, deal: Deal, latest_run: BOERun | None, user_id) -> GateTransition | None:
    previous = deal.current_gate_state or DealGateState.NO_RUN
    new_state = compute_gate_state(latest_run)
    deal.current_gate_state = new_state
    deal.latest_boe_run_id = latest_run.id if latest_run else None

    if previous == new_state:
        return None

    db.add(
        AuditLog(
            entity_type="deal",
            entity_id=deal.id,
            action="GATE_TRANSITION",
            previous_state=previous.value,
            new_state=new_state.value,
            created_by=user_id,
        )
    )
    return GateTransition(previous_state=previous, new_state=new_state)


def log_boe_run_created(db: Session, run: BOERun, user_id) -> None:
    db.add(
        AuditLog(
            entity_type="boe_run",
            entity_id=run.id,
            action="CREATE_RUN",
            previous_state=None,
            new_state="ADVANCE" if run.advance else "KILL",
            created_by=user_id,
            payload={"deal_id": str(run.deal_id), "version": run.version},
        )
    )
