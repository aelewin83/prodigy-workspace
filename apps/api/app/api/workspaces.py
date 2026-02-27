from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import AuditLog, User, Workspace, WorkspaceMember
from app.models.enums import MemberRole, WorkspaceEdition
from app.schemas.workspace import WorkspaceCreate, WorkspaceEditionUpdate, WorkspaceOut
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
