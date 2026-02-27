from dataclasses import dataclass

from app.core.config import settings
from app.models.enums import VarianceBasis
from app.services.comps.connector_registry import REGISTRY
from app.services.comps.dedupe_outliers import dedupe_rows, flag_old_rows, flag_outliers_iqr
from app.services.comps.ingest.csv_ingestor import ingest_csv
from app.services.comps.ingest.pdf_ingestor import ingest_pdf
from app.services.comps.ingest.xlsx_ingestor import ingest_xlsx
from app.services.comps.rollups import compute_rollups, compute_subject_variance


@dataclass
class CompRunResult:
    normalized_rows: list
    rollups: dict
    subject_variance: dict
    report: dict


def run_public_connectors_job(query: dict, allowlisted_connectors: tuple[str, ...], allowlisted_domains: tuple[str, ...]) -> CompRunResult:
    connector_ids = query.get("connectors") or []
    all_rows = []
    report: dict = {"connectors": {}, "total_raw": 0}

    for cid in connector_ids:
        if cid not in allowlisted_connectors:
            raise PermissionError(f"Connector not allowlisted: {cid}")
        connector = REGISTRY.get(cid)
        for domain in getattr(connector, "domains", ()):
            if domain not in allowlisted_domains:
                raise PermissionError(f"Connector domain not allowlisted: {domain}")

        raw = connector.fetch_raw(query)
        rows = connector.parse_raw_to_rows(raw, query)
        report["connectors"][cid] = {"raw_items": len(raw), "rows": len(rows)}
        report["total_raw"] += len(raw)
        all_rows.extend(rows)

    all_rows = dedupe_rows(all_rows)
    flag_old_rows(all_rows, settings.comp_old_days_threshold)
    flag_outliers_iqr(all_rows)

    rollups = compute_rollups(all_rows)
    subject_variance = compute_subject_variance(rollups, query.get("subject", {}), basis=VarianceBasis.AVG)
    return CompRunResult(all_rows, rollups, subject_variance, report)


def run_private_file_ingest_job(file_path: str, query: dict) -> CompRunResult:
    lower = file_path.lower()
    if lower.endswith(".csv"):
        rows, parse_report = ingest_csv(file_path)
    elif lower.endswith(".xlsx"):
        rows, parse_report = ingest_xlsx(file_path)
    elif lower.endswith(".pdf"):
        rows, parse_report = ingest_pdf(file_path)
    else:
        raise ValueError("Unsupported file type. Use CSV/XLSX/PDF.")

    rows = dedupe_rows(rows)
    flag_old_rows(rows, settings.comp_old_days_threshold)
    flag_outliers_iqr(rows)

    rollups = compute_rollups(rows)
    subject_variance = compute_subject_variance(rollups, query.get("subject", {}), basis=VarianceBasis.AVG)
    return CompRunResult(rows, rollups, subject_variance, {"parse_report": parse_report, "file_path": file_path})
