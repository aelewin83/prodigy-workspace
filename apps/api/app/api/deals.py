from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import Deal, User, WorkspaceMember
from app.schemas.deal import DealCreate, DealOut, DealUpdate

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


def _get_deal_with_access(db: Session, deal_id, user_id) -> Deal:
    deal = db.scalar(select(Deal).where(Deal.id == deal_id))
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    _assert_workspace_access(db, deal.workspace_id, user_id)
    return deal


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


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deal(deal_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    deal = _get_deal_with_access(db, deal_id, user.id)
    db.delete(deal)
    db.commit()
