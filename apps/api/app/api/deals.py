from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import BOERun, BOETestResult, Deal, DealComment, DealGateEvent, DealOutcome, User, WorkspaceMember
from app.models.enums import DealStatus, MemberRole
from app.schemas.deal import DealCreate, DealOut, DealUpdate
from app.schemas.deal_workspace import DealActivityEventOut, DealCommentCreate, DealOverrideActionRequest
from app.schemas.gate import DealOutcomeCreate, DealOutcomeOut, GateSummaryOut, ICPacketOut
from app.services.gate_summary import build_gate_summary
from app.services.gating import set_gate_override

router = APIRouter(prefix="/deals", tags=["deals"])


def _assert_workspace_access(db: Session, workspace_id, user_id):
    is_member = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    if not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied")


def _workspace_member(db: Session, workspace_id, user_id) -> WorkspaceMember | None:
    return db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )


def _get_deal_with_access(db: Session, deal_id, user_id) -> Deal:
    deal = db.scalar(select(Deal).where(Deal.id == deal_id))
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    member = _workspace_member(db, deal.workspace_id, user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Deal access denied")
    return deal


def _get_deal_member(db: Session, deal: Deal, user_id) -> WorkspaceMember:
    member = _workspace_member(db, deal.workspace_id, user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Deal access denied")
    return member


def _get_latest_run_with_tests(db: Session, deal_id):
    return db.scalar(
        select(BOERun)
        .options(selectinload(BOERun.tests))
        .where(BOERun.deal_id == deal_id)
        .order_by(BOERun.created_at.desc())
    )


@router.post("", response_model=DealOut)
def create_deal(
    payload: DealCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _assert_workspace_access(db, payload.workspace_id, user.id)
    deal = Deal(
        workspace_id=payload.workspace_id,
        name=payload.name,
        address=payload.address,
        asking_price=payload.asking_price,
        created_by=user.id,
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


@router.get("/workspace/{workspace_id}", response_model=list[DealOut])
def list_deals(workspace_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _assert_workspace_access(db, workspace_id, user.id)
    return list(db.scalars(select(Deal).where(Deal.workspace_id == workspace_id).order_by(Deal.created_at.desc())).all())


@router.get("/{deal_id}", response_model=DealOut)
def get_deal(deal_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_deal_with_access(db, deal_id, user.id)


@router.patch("/{deal_id}", response_model=DealOut)
def update_deal(
    deal_id: str,
    payload: DealUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deal = _get_deal_with_access(db, deal_id, user.id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(deal, key, value)
    db.commit()
    db.refresh(deal)
    return deal


@router.post("/{deal_id}/gate/override", response_model=DealOut)
def override_deal_gate_status(
    deal_id: str,
    payload: DealOverrideActionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deal = _get_deal_with_access(db, deal_id, user.id)
    member = _get_deal_member(db, deal, user.id)
    if member.role != MemberRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can override gate status")

    override_status_raw = (payload.status or payload.override_status or "").strip().upper()
    comment = payload.comment if payload.comment is not None else payload.reason

    if override_status_raw not in {"ADVANCE", "REVIEW", "KILL", "CLEAR", "APPROVED", "BLOCKED"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="status must be one of ADVANCE, REVIEW, KILL, CLEAR",
        )
    if override_status_raw != "CLEAR" and not (comment and comment.strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="comment is required when setting an override",
        )

    target_status = None
    if override_status_raw != "CLEAR":
        status_map = {
            "ADVANCE": DealStatus.ADVANCE,
            "REVIEW": DealStatus.NEEDS_WORK,
            "KILL": DealStatus.BLOCKED,
            "APPROVED": DealStatus.APPROVED,
            "BLOCKED": DealStatus.BLOCKED,
        }
        target_status = status_map[override_status_raw]

    set_gate_override(
        db,
        deal,
        override_status=target_status,
        reason=comment,
        override_by=str(user.id),
    )
    db.commit()
    db.refresh(deal)
    return deal


@router.post("/{deal_id}/comments")
def create_deal_comment(
    deal_id: str,
    payload: DealCommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deal = _get_deal_with_access(db, deal_id, user.id)
    member = _get_deal_member(db, deal, user.id)
    if member.role not in {MemberRole.OWNER, MemberRole.MEMBER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for comments")
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Comment body cannot be empty")
    comment = DealComment(deal_id=deal.id, body=body, created_by=user.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {"id": str(comment.id), "body": comment.body, "created_at": comment.created_at}


@router.get("/{deal_id}/activity", response_model=list[DealActivityEventOut])
def get_deal_activity(
    deal_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deal = _get_deal_with_access(db, deal_id, user.id)
    _ = _get_deal_member(db, deal, user.id)
    limit = max(1, min(limit, 200))

    gate_events = list(
        db.scalars(
            select(DealGateEvent)
            .where(DealGateEvent.deal_id == deal.id)
            .order_by(DealGateEvent.created_at.desc())
            .limit(limit)
        ).all()
    )
    comments = list(
        db.scalars(
            select(DealComment)
            .where(DealComment.deal_id == deal.id)
            .order_by(DealComment.created_at.desc())
            .limit(limit)
        ).all()
    )
    actor_ids: set[str] = set()
    for e in gate_events:
        actor = (e.metadata_json or {}).get("override_by") or (e.metadata_json or {}).get("actor_user_id")
        if actor:
            actor_ids.add(str(actor))
    for c in comments:
        actor_ids.add(str(c.created_by))
    users = {}
    if actor_ids:
        for u in db.scalars(select(User).where(User.id.in_(list(actor_ids)))).all():
            users[str(u.id)] = u

    events: list[dict] = []
    for e in gate_events:
        actor_id = (e.metadata_json or {}).get("override_by") or (e.metadata_json or {}).get("actor_user_id")
        actor = users.get(str(actor_id)) if actor_id else None
        if e.event_type == "BOE_RUN_CREATED":
            event_type = "BOE_RUN_CREATED"
            summary = "BOE run created"
        elif e.event_type == "OVERRIDE_SET":
            event_type = "GATE_OVERRIDE_SET"
            summary = f"Gate override set to {e.to_status}"
        elif e.event_type == "OVERRIDE_CLEARED":
            event_type = "GATE_OVERRIDE_CLEARED"
            summary = "Gate override cleared"
        else:
            event_type = e.event_type
            summary = e.event_type.replace("_", " ").title()
        events.append(
            {
                "id": f"gate-{e.id}",
                "type": event_type,
                "created_at": e.created_at,
                "actor": {"id": str(actor.id) if actor else str(actor_id) if actor_id else None, "email": actor.email if actor else None, "name": actor.full_name if actor else None},
                "summary": summary,
                "metadata": e.metadata_json or {},
            }
        )

    for c in comments:
        actor = users.get(str(c.created_by))
        events.append(
            {
                "id": f"comment-{c.id}",
                "type": "COMMENT_ADDED",
                "created_at": c.created_at,
                "actor": {"id": str(c.created_by), "email": actor.email if actor else None, "name": actor.full_name if actor else None},
                "summary": c.body,
                "metadata": {"body": c.body},
            }
        )

    events.sort(key=lambda x: (x["created_at"], x["id"]), reverse=True)
    return events[:limit]


@router.get("/{deal_id}/gate_summary", response_model=GateSummaryOut)
def get_deal_gate_summary(
    deal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deal = _get_deal_with_access(db, deal_id, user.id)
    latest_run = _get_latest_run_with_tests(db, deal.id)
    tests = latest_run.tests if latest_run else []
    audit_trail_count = db.scalar(select(func.count()).select_from(DealGateEvent).where(DealGateEvent.deal_id == deal.id)) or 0
    return build_gate_summary(
        deal=deal,
        latest_run=latest_run,
        tests=tests,
        audit_trail_count=int(audit_trail_count),
    )


@router.get("/{deal_id}/ic_packet", response_model=ICPacketOut)
def get_deal_ic_packet(
    deal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deal = _get_deal_with_access(db, deal_id, user.id)
    latest_run = _get_latest_run_with_tests(db, deal.id)
    tests = latest_run.tests if latest_run else []
    audit_trail_count = db.scalar(select(func.count()).select_from(DealGateEvent).where(DealGateEvent.deal_id == deal.id)) or 0
    gate_summary = build_gate_summary(
        deal=deal,
        latest_run=latest_run,
        tests=tests,
        audit_trail_count=int(audit_trail_count),
    )
    events = db.scalars(
        select(DealGateEvent)
        .where(DealGateEvent.deal_id == deal.id)
        .order_by(DealGateEvent.created_at.desc())
    ).all()
    override_events = [
        {
            "event_type": e.event_type,
            "from_status": e.from_status,
            "to_status": e.to_status,
            "source": e.source,
            "reason": e.reason,
            "created_at": e.created_at,
            "user": (e.metadata_json or {}).get("override_by"),
        }
        for e in events
        if e.event_type in {"OVERRIDE_SET", "OVERRIDE_CLEARED"}
    ]
    outputs = latest_run.outputs if latest_run else {}
    return {
        "packet_version": "1.0",
        "generated_at": datetime.now(timezone.utc),
        "deal_snapshot": {
            "deal_id": deal.id,
            "deal_name": deal.name,
            "address": deal.address,
            "asking_price": float(deal.asking_price) if deal.asking_price is not None else None,
            "latest_run_id": latest_run.id if latest_run else None,
        },
        "gate_summary": gate_summary,
        "recommended_max_bid": {
            "boe_max_bid": outputs.get("boe_max_bid") if outputs else None,
            "binding_constraint": latest_run.binding_constraint if latest_run else None,
            "delta_vs_asking": outputs.get("delta_vs_asking") if outputs else None,
        },
        "audit_history": override_events,
    }


@router.post("/{deal_id}/outcomes", response_model=DealOutcomeOut)
def create_or_update_deal_outcome(
    deal_id: str,
    payload: DealOutcomeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deal = _get_deal_with_access(db, deal_id, user.id)
    recorded_at = payload.recorded_at or datetime.now(timezone.utc)
    existing = db.scalar(
        select(DealOutcome).where(
            DealOutcome.deal_id == deal.id,
            DealOutcome.recorded_at == recorded_at,
        )
    )
    if existing:
        existing.realized_irr = payload.realized_irr
        existing.realized_multiple = payload.realized_multiple
        existing.underperformed_flag = payload.underperformed_flag
        existing.notes = payload.notes
        db.commit()
        db.refresh(existing)
        return existing

    outcome = DealOutcome(
        deal_id=deal.id,
        recorded_at=recorded_at,
        realized_irr=payload.realized_irr,
        realized_multiple=payload.realized_multiple,
        underperformed_flag=payload.underperformed_flag,
        notes=payload.notes,
    )
    db.add(outcome)
    db.commit()
    db.refresh(outcome)
    return outcome


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deal(deal_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    deal = _get_deal_with_access(db, deal_id, user.id)
    db.delete(deal)
    db.commit()
