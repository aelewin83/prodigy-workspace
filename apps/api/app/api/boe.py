from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from uuid import UUID

from app.api.deps import get_current_user, get_deal_with_access
from app.boe.engine import BOEInput, calculate_boe, serialize_output
from app.db.session import get_db
from app.models.entities import BOERun, BOETestResult, User
from app.models.enums import TestClass, TestResult
from app.schemas.boe import BOERunCreate, BOERunOut
from app.services.gating import log_boe_run_created, transition_deal_gate

router = APIRouter(prefix="/deals/{deal_id}/boe/runs", tags=["boe"])


@router.post("", response_model=BOERunOut)
def create_boe_run(
    deal_id: UUID,
    payload: BOERunCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deal = get_deal_with_access(str(deal_id), db, user.id)

    max_version = db.scalar(select(func.max(BOERun.version)).where(BOERun.deal_id == deal_id)) or 0
    version = int(max_version) + 1

    boe_input = BOEInput(**payload.inputs)
    output, tests, decision = calculate_boe(boe_input)
    outputs = serialize_output(output)
    run = BOERun(
        deal_id=deal_id,
        version=version,
        inputs=payload.inputs,
        outputs=outputs,
        decision="ADVANCE" if decision.advance else "KILL",
        binding_constraint=output.binding_constraint,
        hard_veto_ok=decision.hard_veto_ok,
        pass_count=decision.pass_count,
        advance=decision.advance,
        created_by=user.id,
    )
    db.add(run)
    db.flush()

    for t in tests:
        db.add(
            BOETestResult(
                boe_run_id=run.id,
                test_key=t.key,
                test_name=t.name,
                test_class=TestClass(t.test_class.value),
                threshold=t.threshold,
                actual=t.actual,
                threshold_display=t.threshold_display,
                actual_display=t.actual_display,
                result=TestResult(t.result.value),
                note=None,
            )
        )

    log_boe_run_created(db, run, user.id)
    transition_deal_gate(db, deal, run, user.id)
    db.commit()
    reloaded = db.scalar(select(BOERun).options(selectinload(BOERun.tests)).where(BOERun.id == run.id))
    return reloaded


@router.get("", response_model=list[BOERunOut])
def list_boe_runs(deal_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_deal_with_access(str(deal_id), db, user.id)
    stmt = (
        select(BOERun)
        .options(selectinload(BOERun.tests))
        .where(BOERun.deal_id == deal_id)
        .order_by(BOERun.created_at.desc())
    )
    return list(db.scalars(stmt).all())


@router.get("/{run_id}", response_model=BOERunOut)
def get_boe_run(
    deal_id: UUID,
    run_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_deal_with_access(str(deal_id), db, user.id)
    run = db.scalar(
        select(BOERun)
        .options(selectinload(BOERun.tests))
        .where(BOERun.id == run_id, BOERun.deal_id == deal_id)
    )
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BOE run not found")
    return run
