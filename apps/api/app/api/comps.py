from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.entities import (
    CompListing,
    CompRollup,
    CompRun,
    CompSubject,
    CompSubjectVariance,
    Deal,
    User,
    WorkspaceMember,
)
from app.models.enums import CompRunStatus, CompSourceType, ListingSourceType, VarianceBasis
from app.schemas.comps import (
    CompListingOut,
    CompRecommendationsResponse,
    CompRecommendationsUnit,
    CompRollupOut,
    CompRunManualCreate,
    CompRunOut,
    CompRunPrivateImportCreate,
    CompRunPublicPullCreate,
    CompSubjectUpsert,
    CompVarianceOut,
)
from app.services.comps import (
    build_normalized_row,
    compute_rollups,
    compute_subject_variance,
    dedupe_rows,
    flag_old_rows,
    flag_outliers_iqr,
)
from app.workers.jobs import process_private_file_run, process_public_connector_run
from app.workers.queue import get_comp_queue

router = APIRouter(prefix="/deals/{deal_id}/comps", tags=["comps"])


def _assert_deal_access(db: Session, deal_id, user_id):
    deal = db.scalar(select(Deal).where(Deal.id == deal_id))
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    member = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == deal.workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Deal access denied")
    return deal


def _recompute_run_aggregates(db: Session, run: CompRun):
    rows = list(db.scalars(select(CompListing).where(CompListing.comp_run_id == run.id)).all())

    rollups = compute_rollups(rows)
    db.execute(delete(CompRollup).where(CompRollup.comp_run_id == run.id))
    db.execute(delete(CompSubjectVariance).where(CompSubjectVariance.comp_run_id == run.id))

    for unit_type, payload in rollups.items():
        db.add(
            CompRollup(
                comp_run_id=run.id,
                unit_type=unit_type,
                avg_rent=payload["avg_rent"],
                avg_gross_rent=payload["avg_gross_rent"],
                avg_discount_premium=payload["avg_discount_premium"],
                median_rent=payload["median_rent"],
                p25_rent=payload["p25_rent"],
                p75_rent=payload["p75_rent"],
                sample_size=payload["sample_size"],
            )
        )

    subject_rows = list(db.scalars(select(CompSubject).where(CompSubject.deal_id == run.deal_id)).all())
    subject_map = {
        s.unit_type: {"subject_rent": s.subject_rent, "subject_gross_rent": s.subject_gross_rent}
        for s in subject_rows
    }
    variances = compute_subject_variance(rollups, subject_map)
    for unit_type, payload in variances.items():
        db.add(
            CompSubjectVariance(
                comp_run_id=run.id,
                unit_type=unit_type,
                variance_net=payload["variance_net"],
                variance_gross=payload["variance_gross"],
                basis=payload["basis"],
                computed_at=payload["computed_at"],
            )
        )


@router.post("/runs/manual", response_model=CompRunOut)
def create_manual_comp_run(
    deal_id: UUID,
    payload: CompRunManualCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deal = _assert_deal_access(db, deal_id, user.id)

    run = CompRun(
        workspace_id=deal.workspace_id,
        deal_id=deal.id,
        filters=payload.filters,
        status=CompRunStatus.RUNNING,
        source_mix={"mode": "manual"},
        started_at=datetime.now(UTC),
        created_by=user.id,
    )
    db.add(run)
    db.flush()

    rows = []
    for row in payload.listings:
        rows.append(
            build_normalized_row(
                address=row.address,
                unit=row.unit,
                beds=row.beds,
                baths=row.baths,
                rent=row.rent,
                gross_rent=row.gross_rent,
                date_observed=row.date_observed,
                link=row.link,
                notes=row.notes,
                source_type=ListingSourceType.MANUAL,
                source_ref="manual",
                confidence_score=row.confidence_score or 1.0,
            )
        )

    rows = dedupe_rows(rows)
    flag_outliers_iqr(rows)
    flag_old_rows(rows, max_age_days=settings.comp_old_days_threshold)

    for row in rows:
        db.add(
            CompListing(
                comp_run_id=run.id,
                unit_type=row.unit_type,
                address=row.address,
                unit=row.unit,
                beds=row.beds,
                baths=row.baths,
                rent=row.rent,
                gross_rent=row.gross_rent,
                discount_premium=row.discount_premium,
                date_observed=row.date_observed,
                link=row.link,
                notes=row.notes,
                source_type=row.source_type,
                source_ref=row.source_ref,
                observed_at=row.observed_at,
                confidence_score=row.confidence_score,
                dedupe_key=row.dedupe_key,
                flags=row.flags,
            )
        )

    run.status = CompRunStatus.SUCCEEDED
    run.finished_at = datetime.now(UTC)
    run.parse_report = {"rows_written": len(rows), "mode": "manual"}

    _recompute_run_aggregates(db, run)
    db.commit()
    db.refresh(run)
    return run


@router.post("/runs/private-import", response_model=CompRunOut)
def create_private_import_run(
    deal_id: UUID,
    payload: CompRunPrivateImportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deal = _assert_deal_access(db, deal_id, user.id)

    run = CompRun(
        workspace_id=deal.workspace_id,
        deal_id=deal.id,
        filters=payload.filters,
        status=CompRunStatus.QUEUED,
        source_mix={
            "mode": "private_file",
            "file_type": payload.file_type,
            "file_key": payload.file_key,
        },
        created_by=user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    queue = get_comp_queue()
    queue.enqueue(process_private_file_run, str(run.id), payload.file_key, payload.file_type)
    return run


@router.post("/runs/public-pull", response_model=CompRunOut)
def create_public_pull_run(
    deal_id: UUID,
    payload: CompRunPublicPullCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deal = _assert_deal_access(db, deal_id, user.id)

    run = CompRun(
        workspace_id=deal.workspace_id,
        deal_id=deal.id,
        filters=payload.filters,
        status=CompRunStatus.QUEUED,
        source_mix={
            "mode": "public_connectors",
            "connector_ids": payload.connector_ids,
            "source_type": CompSourceType.PUBLIC_CONNECTOR.value,
        },
        created_by=user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    queue = get_comp_queue()
    queue.enqueue(process_public_connector_run, str(run.id), payload.connector_ids, payload.filters)
    return run


@router.get("/runs", response_model=list[CompRunOut])
def list_comp_runs(
    deal_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _assert_deal_access(db, deal_id, user.id)
    stmt = select(CompRun).where(CompRun.deal_id == deal_id).order_by(CompRun.created_at.desc())
    return list(db.scalars(stmt).all())


@router.get("/runs/{comp_run_id}/listings", response_model=list[CompListingOut])
def list_comp_listings(
    deal_id: UUID,
    comp_run_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _assert_deal_access(db, deal_id, user.id)
    stmt = select(CompListing).where(CompListing.comp_run_id == comp_run_id)
    return list(db.scalars(stmt).all())


@router.get("/runs/{comp_run_id}/rollups", response_model=list[CompRollupOut])
def list_comp_rollups(
    deal_id: UUID,
    comp_run_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _assert_deal_access(db, deal_id, user.id)
    stmt = select(CompRollup).where(CompRollup.comp_run_id == comp_run_id)
    return list(db.scalars(stmt).all())


@router.get("/runs/{comp_run_id}/variance", response_model=list[CompVarianceOut])
def list_comp_variance(
    deal_id: UUID,
    comp_run_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _assert_deal_access(db, deal_id, user.id)
    stmt = select(CompSubjectVariance).where(CompSubjectVariance.comp_run_id == comp_run_id)
    return list(db.scalars(stmt).all())


@router.put("/subjects")
def upsert_comp_subjects(
    deal_id: UUID,
    payload: list[CompSubjectUpsert],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _assert_deal_access(db, deal_id, user.id)
    for item in payload:
        existing = db.scalar(
            select(CompSubject).where(CompSubject.deal_id == deal_id, CompSubject.unit_type == item.unit_type)
        )
        if existing:
            existing.subject_rent = item.subject_rent
            existing.subject_gross_rent = item.subject_gross_rent
            existing.updated_at = datetime.now(UTC)
            existing.updated_by = user.id
        else:
            db.add(
                CompSubject(
                    deal_id=deal_id,
                    unit_type=item.unit_type,
                    subject_rent=item.subject_rent,
                    subject_gross_rent=item.subject_gross_rent,
                    updated_by=user.id,
                )
            )
    db.commit()
    return {"updated": len(payload)}


@router.get("/recommendations", response_model=CompRecommendationsResponse)
def get_comps_recommendations(
    deal_id: UUID,
    basis: VarianceBasis = VarianceBasis.AVG,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _assert_deal_access(db, deal_id, user.id)

    latest = db.scalar(select(CompRun).where(CompRun.deal_id == deal_id).order_by(CompRun.created_at.desc()))
    if not latest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No comp runs found for deal")

    rollups = list(db.scalars(select(CompRollup).where(CompRollup.comp_run_id == latest.id)).all())
    recs: list[CompRecommendationsUnit] = []
    for row in rollups:
        base = row.avg_rent if basis == VarianceBasis.AVG else (row.median_rent or row.avg_rent)
        confidence = min(1.0, 0.3 + (row.sample_size * 0.07))
        recs.append(
            CompRecommendationsUnit(
                unit_type=row.unit_type,
                suggested_fm_rent=base,
                low=row.p25_rent,
                high=row.p75_rent,
                confidence_score=confidence,
                sample_size=row.sample_size,
            )
        )

    return CompRecommendationsResponse(deal_id=deal_id, basis=basis, recommendations=recs)
