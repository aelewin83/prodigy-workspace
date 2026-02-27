from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.entities import AuditLog, BOERun, Deal
from app.models.enums import DealGateState


@dataclass(frozen=True)
class GateTransition:
    previous_state: DealGateState
    new_state: DealGateState


def compute_gate_state(latest_run: BOERun | None) -> DealGateState:
    if latest_run is None:
        return DealGateState.NO_RUN
    return DealGateState.ADVANCE if latest_run.advance else DealGateState.KILL


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
