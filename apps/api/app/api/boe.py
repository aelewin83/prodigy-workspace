from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from uuid import UUID

from app.api.deps import get_current_user, get_deal_with_access
from app.boe.engine import BOEInput, GateStatus, calculate_boe, serialize_output
from app.db.session import get_db
from app.models.entities import BOERun, BOETestResult, Deal, User
from app.models.enums import DealStatus, TestClass, TestResult
from app.schemas.boe import BOEDecisionSummaryOut, BOERunCreate, BOERunOut
from app.services.gating import log_boe_run_created, transition_deal_gate

router = APIRouter(prefix="/deals/{deal_id}/boe/runs", tags=["boe"])


def _compute_deal_gate_status(hard_veto_ok: bool, advance: bool) -> DealStatus:
    if not hard_veto_ok:
        return DealStatus.KILL
    if advance:
        return DealStatus.ADVANCE
    return DealStatus.REVIEW


def _persist_deal_gate_status(deal: Deal, hard_veto_ok: bool, advance: bool) -> None:
    deal.gate_status = _compute_deal_gate_status(hard_veto_ok=hard_veto_ok, advance=advance)
    deal.gate_updated_at = datetime.now(timezone.utc)


def _decision_summary_from_tests(run: BOERun) -> BOEDecisionSummaryOut:
    failed_hard = [t.test_key for t in run.tests if t.test_class == TestClass.HARD and t.result == TestResult.FAIL]
    failed_soft = [t.test_key for t in run.tests if t.test_class == TestClass.SOFT and t.result == TestResult.FAIL]
    warn_tests = [t.test_key for t in run.tests if t.result == TestResult.WARN]
    pass_tests = [t.test_key for t in run.tests if t.result == TestResult.PASS]
    na_tests = [t.test_key for t in run.tests if t.result == TestResult.NA]
    if not run.hard_veto_ok:
        status = GateStatus.BLOCKED.value
    elif run.advance:
        status = GateStatus.ADVANCE.value
    else:
        status = GateStatus.NEEDS_WORK.value
    return BOEDecisionSummaryOut(
        status=status,
        hard_veto_ok=run.hard_veto_ok,
        pass_count=run.pass_count,
        total_tests=len(run.tests),
        advance=run.advance,
        failed_hard_tests=failed_hard,
        failed_soft_tests=failed_soft,
        warn_tests=warn_tests,
        pass_tests=pass_tests,
        na_tests=na_tests,
    )


def _serialize_boe_run(run: BOERun) -> dict:
    return {
        "id": run.id,
        "deal_id": run.deal_id,
        "version": run.version,
        "inputs": run.inputs,
        "outputs": run.outputs,
        "decision": run.decision,
        "binding_constraint": run.binding_constraint,
        "hard_veto_ok": run.hard_veto_ok,
        "pass_count": run.pass_count,
        "advance": run.advance,
        "decision_summary": _decision_summary_from_tests(run),
        "created_by": run.created_by,
        "created_at": run.created_at,
        "tests": run.tests,
    }


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
    _persist_deal_gate_status(deal, hard_veto_ok=decision.hard_veto_ok, advance=decision.advance)
    db.commit()
    reloaded = db.scalar(select(BOERun).options(selectinload(BOERun.tests)).where(BOERun.id == run.id))
    return _serialize_boe_run(reloaded)


@router.get("", response_model=list[BOERunOut])
def list_boe_runs(deal_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_deal_with_access(str(deal_id), db, user.id)
    stmt = (
        select(BOERun)
        .options(selectinload(BOERun.tests))
        .where(BOERun.deal_id == deal_id)
        .order_by(BOERun.created_at.desc())
    )
    return [_serialize_boe_run(run) for run in db.scalars(stmt).all()]


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
    return _serialize_boe_run(run)
