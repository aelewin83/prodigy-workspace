from __future__ import annotations

from datetime import UTC, datetime
from statistics import median

from app.models.enums import UnitType, VarianceBasis
from app.services.comps.normalize import NormalizedCompRow


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * p
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def compute_rollups(rows: list[NormalizedCompRow]) -> dict[UnitType, dict]:
    grouped: dict[UnitType, list[NormalizedCompRow]] = {}
    for row in rows:
        grouped.setdefault(row.unit_type, []).append(row)

    result: dict[UnitType, dict] = {}
    for unit, unit_rows in grouped.items():
        rents = [float(r.rent) for r in unit_rows if r.rent is not None]
        gross = [float(r.gross_rent) for r in unit_rows if r.gross_rent is not None]
        disc = [float(r.discount_premium) for r in unit_rows if r.discount_premium is not None]

        result[unit] = {
            "avg_rent": sum(rents) / len(rents) if rents else None,
            "avg_gross_rent": sum(gross) / len(gross) if gross else None,
            "avg_discount_premium": sum(disc) / len(disc) if disc else None,
            "median_rent": median(rents) if rents else None,
            "p25_rent": percentile(rents, 0.25),
            "p75_rent": percentile(rents, 0.75),
            "sample_size": len(unit_rows),
        }
    return result


def compute_subject_variance(
    rollups: dict[UnitType, dict],
    subjects: dict[UnitType, dict],
    basis: VarianceBasis = VarianceBasis.AVG,
) -> dict[UnitType, dict]:
    variance: dict[UnitType, dict] = {}
    for unit, rollup in rollups.items():
        subject = subjects.get(unit, {})
        subject_rent = subject.get("subject_rent")
        subject_gross = subject.get("subject_gross_rent")
        avg_rent = rollup.get("avg_rent")
        avg_gross = rollup.get("avg_gross_rent")

        variance_net = None
        variance_gross = None
        if subject_rent is not None and avg_rent not in (None, 0):
            variance_net = (subject_rent - avg_rent) / avg_rent
        if subject_gross is not None and avg_gross not in (None, 0):
            variance_gross = (subject_gross - avg_gross) / avg_gross

        variance[unit] = {
            "variance_net": variance_net,
            "variance_gross": variance_gross,
            "basis": basis,
            "computed_at": datetime.now(UTC),
        }
    return variance
