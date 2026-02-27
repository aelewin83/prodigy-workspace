from datetime import date

from app.models.enums import UnitType
from app.services.comps.normalize import NormalizedCompRow
from app.services.comps.rollups import percentile


def dedupe_rows(rows: list[NormalizedCompRow]) -> list[NormalizedCompRow]:
    by_key: dict[str, NormalizedCompRow] = {}
    for row in rows:
        existing = by_key.get(row.dedupe_key)
        if existing is None:
            by_key[row.dedupe_key] = row
            continue
        existing_conf = existing.confidence_score or 0.0
        row_conf = row.confidence_score or 0.0
        if row_conf >= existing_conf:
            row.flags = {**row.flags, "duplicate": True}
            by_key[row.dedupe_key] = row
        else:
            existing.flags = {**existing.flags, "duplicate": True}
    return list(by_key.values())


def flag_old_rows(rows: list[NormalizedCompRow], max_age_days: int) -> None:
    now = date.today()
    for row in rows:
        if row.date_observed is None:
            continue
        age_days = (now - row.date_observed).days
        if age_days > max_age_days:
            row.flags = {**row.flags, "old": True, "age_days": age_days}


def flag_outliers_iqr(rows: list[NormalizedCompRow]) -> None:
    grouped: dict[UnitType, list[NormalizedCompRow]] = {}
    for row in rows:
        grouped.setdefault(row.unit_type, []).append(row)

    for unit_rows in grouped.values():
        rent_values = [float(r.rent) for r in unit_rows if r.rent is not None]
        if len(rent_values) < 5:
            continue
        q1 = percentile(rent_values, 0.25)
        q3 = percentile(rent_values, 0.75)
        if q1 is None or q3 is None:
            continue
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        for row in unit_rows:
            if row.rent is None:
                continue
            value = float(row.rent)
            if value < lower or value > upper:
                row.flags = {**row.flags, "outlier": True}
