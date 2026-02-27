from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import BOERun, Deal, DealGateEvent, User, WorkspaceMember
from app.schemas.gate import PortfolioSummaryOut
from app.services.analytics import build_portfolio_summary_payload
from app.services.gate_summary import build_gate_summary

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/summary", response_model=PortfolioSummaryOut)
def get_portfolio_summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace_ids = list(
        db.scalars(select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user.id)).all()
    )
    if not workspace_ids:
        return build_portfolio_summary_payload([])

    deals = list(
        db.scalars(select(Deal).where(Deal.workspace_id.in_(workspace_ids)).order_by(Deal.created_at.desc())).all()
    )
    summaries = []
    for deal in deals:
        latest_run = db.scalar(
            select(BOERun)
            .options(selectinload(BOERun.tests))
            .where(BOERun.deal_id == deal.id)
            .order_by(BOERun.created_at.desc())
        )
        tests = latest_run.tests if latest_run else []
        audit_trail_count = (
            db.scalar(select(func.count()).select_from(DealGateEvent).where(DealGateEvent.deal_id == deal.id)) or 0
        )
        summaries.append(
            build_gate_summary(
                deal=deal,
                latest_run=latest_run,
                tests=tests,
                audit_trail_count=int(audit_trail_count),
            )
        )

    return build_portfolio_summary_payload(summaries)
