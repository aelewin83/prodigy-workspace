from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import delete, select

from app.connectors.registry import get_connectors
from app.core.config import settings
from app.db.session import SessionLocal
from app.ingestors.files import parse_csv, parse_pdf, parse_xlsx
from app.models.entities import CompListing, CompRollup, CompRun, CompSubject, CompSubjectVariance
from app.models.enums import CompRunStatus
from app.services.comps import compute_rollups, compute_subject_variance, dedupe_rows, flag_old_rows, flag_outliers_iqr
from app.workers.queue import get_redis


def _cache_key(connector_id: str, filters: dict) -> str:
    raw = f"{connector_id}:{json.dumps(filters, sort_keys=True)}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"comp_cache:{digest}"


def _persist_rows_and_aggregates(db, run: CompRun, rows, parse_report: dict | None = None):
    rows = dedupe_rows(rows)
    flag_outliers_iqr(rows)
    flag_old_rows(rows, settings.comp_old_days_threshold)

    db.execute(delete(CompListing).where(CompListing.comp_run_id == run.id))
    db.execute(delete(CompRollup).where(CompRollup.comp_run_id == run.id))
    db.execute(delete(CompSubjectVariance).where(CompSubjectVariance.comp_run_id == run.id))

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

    rollups = compute_rollups(rows)
    for unit, payload in rollups.items():
        db.add(
            CompRollup(
                comp_run_id=run.id,
                unit_type=unit,
                avg_rent=payload["avg_rent"],
                avg_gross_rent=payload["avg_gross_rent"],
                avg_discount_premium=payload["avg_discount_premium"],
                median_rent=payload["median_rent"],
                p25_rent=payload["p25_rent"],
                p75_rent=payload["p75_rent"],
                sample_size=payload["sample_size"],
            )
        )

    subjects = db.scalars(select(CompSubject).where(CompSubject.deal_id == run.deal_id)).all()
    subject_map = {
        s.unit_type: {"subject_rent": s.subject_rent, "subject_gross_rent": s.subject_gross_rent}
        for s in subjects
    }
    variances = compute_subject_variance(rollups, subject_map)
    for unit, payload in variances.items():
        db.add(
            CompSubjectVariance(
                comp_run_id=run.id,
                unit_type=unit,
                variance_net=payload["variance_net"],
                variance_gross=payload["variance_gross"],
                basis=payload["basis"],
                computed_at=payload["computed_at"],
            )
        )

    run.parse_report = parse_report
    run.status = CompRunStatus.SUCCEEDED
    run.finished_at = datetime.now(UTC)


def process_private_file_run(comp_run_id: str, file_path: str, file_type: str):
    db = SessionLocal()
    try:
        run = db.scalar(select(CompRun).where(CompRun.id == comp_run_id))
        if not run:
            return
        run.status = CompRunStatus.RUNNING
        run.started_at = datetime.now(UTC)

        normalized_type = file_type.lower().strip()
        if normalized_type == "csv":
            rows, report = parse_csv(file_path)
        elif normalized_type == "xlsx":
            rows, report = parse_xlsx(file_path)
        elif normalized_type == "pdf":
            rows, report = parse_pdf(file_path)
        else:
            rows, report = [], {"error": f"Unsupported file type: {file_type}"}

        _persist_rows_and_aggregates(db, run, rows, parse_report=report)
        db.commit()
    except Exception as exc:  # pragma: no cover
        run = db.scalar(select(CompRun).where(CompRun.id == comp_run_id))
        if run:
            run.status = CompRunStatus.FAILED
            run.parse_report = {"error": str(exc)}
            run.finished_at = datetime.now(UTC)
            db.commit()
        raise
    finally:
        db.close()


def process_public_connector_run(comp_run_id: str, connector_ids: list[str], filters: dict):
    db = SessionLocal()
    redis = get_redis()
    try:
        run = db.scalar(select(CompRun).where(CompRun.id == comp_run_id))
        if not run:
            return
        run.status = CompRunStatus.RUNNING
        run.started_at = datetime.now(UTC)

        registry = get_connectors()
        enabled = {item.strip() for item in settings.enabled_connectors.split(",") if item.strip()}
        all_rows = []
        source_reports = []

        for connector_id in connector_ids:
            connector = registry.get(connector_id)
            if connector is None:
                raise ValueError(f"Unknown connector '{connector_id}'")
            if not connector.allowlisted or connector_id not in enabled:
                raise ValueError(f"Connector '{connector_id}' is not allowlisted/enabled")

            key = _cache_key(connector_id, filters)
            cached = redis.get(key)
            if cached:
                raw_items = json.loads(cached)
            else:
                raw_items = connector.fetch(filters)
                redis.setex(key, settings.comp_cache_ttl_seconds, json.dumps(raw_items, default=str))

            rows = connector.parse(raw_items)
            all_rows.extend(rows)
            source_reports.append({"connector_id": connector_id, "rows": len(rows), "cached": bool(cached)})

        _persist_rows_and_aggregates(db, run, all_rows, parse_report={"sources": source_reports})
        db.commit()
    except Exception as exc:  # pragma: no cover
        run = db.scalar(select(CompRun).where(CompRun.id == comp_run_id))
        if run:
            run.status = CompRunStatus.FAILED
            run.parse_report = {"error": str(exc)}
            run.finished_at = datetime.now(UTC)
            db.commit()
        raise
    finally:
        db.close()
