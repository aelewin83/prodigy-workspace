from datetime import date, timedelta

from app.models.enums import ListingSourceType, UnitType
from app.services.comps import (
    build_normalized_row,
    compute_rollups,
    compute_subject_variance,
    dedupe_rows,
    flag_old_rows,
    flag_outliers_iqr,
)


def _row(address: str, unit: str, rent: float, gross_rent: float, beds: float = 1, offset_days: int = 0):
    observed = date.today() - timedelta(days=offset_days)
    return build_normalized_row(
        address=address,
        unit=unit,
        beds=beds,
        baths=1,
        rent=rent,
        gross_rent=gross_rent,
        date_observed=observed,
        link=None,
        notes=None,
        source_type=ListingSourceType.MANUAL,
        source_ref="manual",
        confidence_score=0.9,
    )


def test_dedupe_keeps_highest_confidence():
    low = _row("10 Main St", "2A", 3000, 3200)
    high = _row("10 Main St", "2A", 3050, 3200)
    low.confidence_score = 0.5
    high.confidence_score = 0.9

    result = dedupe_rows([low, high])
    assert len(result) == 1
    assert float(result[0].rent) == 3050


def test_rollup_and_variance_match_expected_math():
    rows = [
        _row("1 A", "1", 3000, 3200, beds=1),
        _row("2 B", "2", 3300, 3500, beds=1),
        _row("3 C", "3", 4500, 4700, beds=2),
    ]
    rollups = compute_rollups(rows)

    assert round(rollups[UnitType.BR1]["avg_rent"], 2) == 3150.00
    assert round(rollups[UnitType.BR1]["avg_gross_rent"], 2) == 3350.00

    subjects = {
        UnitType.BR1: {"subject_rent": 3250, "subject_gross_rent": 3400},
        UnitType.BR2: {"subject_rent": 4400, "subject_gross_rent": 4600},
    }
    variance = compute_subject_variance(rollups, subjects)
    assert round(variance[UnitType.BR1]["variance_net"], 4) == round((3250 - 3150) / 3150, 4)
    assert round(variance[UnitType.BR1]["variance_gross"], 4) == round((3400 - 3350) / 3350, 4)


def test_outlier_and_old_flags_are_set():
    rows = [
        _row("A", "1", 3000, 3100, beds=1, offset_days=10),
        _row("B", "2", 3050, 3150, beds=1, offset_days=10),
        _row("C", "3", 2990, 3090, beds=1, offset_days=10),
        _row("D", "4", 5000, 5100, beds=1, offset_days=10),
        _row("E", "5", 2800, 2900, beds=1, offset_days=400),
    ]

    flag_outliers_iqr(rows)
    flag_old_rows(rows, max_age_days=180)

    assert any(r.flags.get("outlier") for r in rows)
    assert any(r.flags.get("old") for r in rows)
