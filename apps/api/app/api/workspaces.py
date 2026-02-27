from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import AuditLog, BOERun, Deal, DealGateEvent, User, Workspace, WorkspaceMember
from app.models.enums import MemberRole, WorkspaceEdition
from app.schemas.boe import BOEDecisionSummaryOut
from app.schemas.deal_workspace import DealWorkspaceSummaryOut
from app.schemas.workspace import WorkspaceCreate, WorkspaceEditionUpdate, WorkspaceOut
from app.services.gate_summary import build_gate_summary
from app.services.workspace_capabilities import capabilities_for_edition

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _workspace_membership(db: Session, workspace_id, user_id) -> WorkspaceMember | None:
    return db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )


def _workspace_out(workspace: Workspace, *, is_admin: bool) -> dict:
    return {
        "id": workspace.id,
        "name": workspace.name,
        "edition": workspace.edition,
        "capabilities": capabilities_for_edition(workspace.edition),
        "is_admin": is_admin,
        "edition_updated_at": workspace.edition_updated_at,
        "edition_updated_by_user_id": workspace.edition_updated_by_user_id,
        "created_by": workspace.created_by,
        "created_at": workspace.created_at,
    }


@router.post("", response_model=WorkspaceOut)
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = Workspace(name=payload.name, created_by=user.id, edition=WorkspaceEdition.SYNDICATOR)
    db.add(workspace)
    db.flush()
    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=MemberRole.OWNER)
    db.add(member)
    db.commit()
    db.refresh(workspace)
    return _workspace_out(workspace, is_admin=True)


@router.get("", response_model=list[WorkspaceOut])
def list_workspaces(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = (
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user.id)
        .order_by(Workspace.created_at.desc())
    )
    rows = db.execute(stmt).all()
    return [_workspace_out(workspace, is_admin=(role == MemberRole.OWNER)) for workspace, role in rows]


@router.get("/{workspace_id}", response_model=WorkspaceOut)
def get_workspace(workspace_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id))
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    member = _workspace_membership(db, workspace.id, user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied")
    return _workspace_out(workspace, is_admin=(member.role == MemberRole.OWNER))


@router.get("/{workspace_id}/capabilities")
def get_workspace_capabilities(workspace_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id))
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    member = _workspace_membership(db, workspace.id, user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied")
    return capabilities_for_edition(workspace.edition)


@router.get("/{workspace_id}/deals/{deal_id}/summary", response_model=DealWorkspaceSummaryOut)
def get_workspace_deal_summary(
    workspace_id: str,
    deal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id))
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    member = _workspace_membership(db, workspace.id, user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied")
    deal = db.scalar(select(Deal).where(Deal.id == deal_id, Deal.workspace_id == workspace.id))
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    latest_run = db.scalar(
        select(BOERun)
        .options(selectinload(BOERun.tests))
        .where(BOERun.deal_id == deal.id)
        .order_by(BOERun.created_at.desc())
    )
    tests = latest_run.tests if latest_run else []
    audit_trail_count = db.scalar(select(DealGateEvent).where(DealGateEvent.deal_id == deal.id).limit(1))
    gate_summary = build_gate_summary(
        deal=deal,
        latest_run=latest_run,
        tests=tests,
        audit_trail_count=1 if audit_trail_count else 0,
    )

    decision_summary = None
    if latest_run:
        decision_summary = BOEDecisionSummaryOut(
            status=gate_summary["computed_status"],
            hard_veto_ok=gate_summary["computed_hard_veto_ok"],
            pass_count=gate_summary["computed_pass_count"],
            total_tests=len(gate_summary["explainability"]["tests"]),
            advance=gate_summary["computed_advance"],
            failed_hard_tests=gate_summary["computed_failed_hard_tests"],
            failed_soft_tests=gate_summary["computed_failed_soft_tests"],
            warn_tests=gate_summary["computed_warn_tests"],
            pass_tests=gate_summary["computed_pass_tests"],
            na_tests=gate_summary["computed_na_tests"],
            ic_score=gate_summary["ic_score"],
            ic_score_breakdown=gate_summary["ic_score_breakdown"],
        )

    outputs = latest_run.outputs if latest_run else {}
    return {
        "deal_id": deal.id,
        "workspace_id": workspace.id,
        "deal_name": deal.name,
        "address": deal.address,
        "gate_status": deal.gate_status_computed.value,
        "gate_status_effective": deal.gate_status.value,
        "ic_score": gate_summary["ic_score"] if latest_run else None,
        "recommended_max_bid": outputs.get("boe_max_bid") if outputs else None,
        "binding_constraint": latest_run.binding_constraint if latest_run else None,
        "latest_run_id": latest_run.id if latest_run else None,
        "latest_run_created_at": latest_run.created_at if latest_run else None,
        "decision_summary": decision_summary,
        "override": {
            "status": deal.gate_override_status.value if deal.gate_override_status else None,
            "reason": deal.gate_override_reason,
            "by": deal.gate_override_by,
            "at": deal.gate_override_at,
        },
        "capabilities": capabilities_for_edition(workspace.edition),
    }


@router.patch("/{workspace_id}/edition", response_model=WorkspaceOut)
def update_workspace_edition(
    workspace_id: str,
    payload: WorkspaceEditionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id))
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    member = _workspace_membership(db, workspace.id, user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied")
    if member.role != MemberRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only workspace admins can change edition")

    if workspace.edition == payload.edition:
        return _workspace_out(workspace, is_admin=True)

    previous = workspace.edition
    workspace.edition = payload.edition
    workspace.edition_updated_at = datetime.now(timezone.utc)
    workspace.edition_updated_by_user_id = user.id
    db.add(
        AuditLog(
            workspace_id=workspace.id,
            user_id=user.id,
            entity_type="workspace",
            entity_id=workspace.id,
            action="workspace.edition_changed",
            previous_state=previous.value,
            new_state=workspace.edition.value,
            created_by=user.id,
            payload={"from_edition": previous.value, "to_edition": workspace.edition.value},
        )
    )
    db.commit()
    db.refresh(workspace)
    return _workspace_out(workspace, is_admin=True)
