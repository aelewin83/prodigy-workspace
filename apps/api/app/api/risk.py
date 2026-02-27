from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import BOERun, Deal, DealGateEvent, DealOutcome, User, WorkspaceMember
from app.schemas.gate import RiskMetricsOut
from app.services.analytics import build_risk_metrics_payload
from app.services.gate_summary import build_gate_summary

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/metrics", response_model=RiskMetricsOut)
def get_risk_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace_ids = list(
        db.scalars(select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user.id)).all()
    )
    if not workspace_ids:
        return build_risk_metrics_payload([])

    deals = list(db.scalars(select(Deal).where(Deal.workspace_id.in_(workspace_ids))).all())
    outcomes_by_deal = {}
    for o in db.scalars(select(DealOutcome).order_by(DealOutcome.recorded_at.desc())).all():
        outcomes_by_deal.setdefault(o.deal_id, o)

    records = []
    for deal in deals:
        latest_run = db.scalar(
            select(BOERun)
            .options(selectinload(BOERun.tests))
            .where(BOERun.deal_id == deal.id)
            .order_by(BOERun.created_at.desc())
        )
        tests = latest_run.tests if latest_run else []
        audit_count = db.scalar(select(DealGateEvent).where(DealGateEvent.deal_id == deal.id).limit(1))
        summary = build_gate_summary(
            deal=deal,
            latest_run=latest_run,
            tests=tests,
            audit_trail_count=1 if audit_count else 0,
        )
        records.append((summary, outcomes_by_deal.get(deal.id)))

    return build_risk_metrics_payload(records)
