from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.models.enums import ListingSourceType, UnitType


@dataclass
class NormalizedCompRow:
    unit_type: UnitType
    address: str
    unit: str | None
    beds: float | None
    baths: float | None
    rent: float | None
    gross_rent: float | None
    discount_premium: float | None
    date_observed: date | None
    link: str | None
    notes: str | None
    source_type: ListingSourceType
    source_ref: str | None
    observed_at: datetime
    confidence_score: float | None
    dedupe_key: str
    flags: dict


def unit_type_from_beds(beds: float | None) -> UnitType:
    if beds is None or beds <= 0:
        return UnitType.STUDIO
    if beds < 1.5:
        return UnitType.BR1
    if beds < 2.5:
        return UnitType.BR2
    if beds < 3.5:
        return UnitType.BR3
    return UnitType.BR4_PLUS


def normalize_address(value: str) -> str:
    return " ".join(value.lower().strip().split())


def build_dedupe_key(address: str, unit: str | None, beds: float | None, baths: float | None, date_observed: date | None) -> str:
    addr = normalize_address(address)
    unit_norm = (unit or "").strip().lower()
    beds_norm = "" if beds is None else f"{beds:.2f}"
    baths_norm = "" if baths is None else f"{baths:.2f}"
    date_norm = date_observed.isoformat() if date_observed else ""
    return f"{addr}|{unit_norm}|{beds_norm}|{baths_norm}|{date_norm}"


def compute_discount_premium(rent: float | None, gross_rent: float | None) -> float | None:
    if rent is None or gross_rent is None or gross_rent == 0:
        return None
    return (gross_rent - rent) / gross_rent


def build_normalized_row(
    *,
    address: str,
    unit: str | None,
    beds: float | None,
    baths: float | None,
    rent: float | None,
    gross_rent: float | None,
    date_observed: date | None,
    link: str | None,
    notes: str | None,
    source_type: ListingSourceType,
    source_ref: str | None,
    confidence_score: float | None,
) -> NormalizedCompRow:
    unit_type = unit_type_from_beds(beds)
    discount_premium = compute_discount_premium(rent, gross_rent)
    dedupe_key = build_dedupe_key(address, unit, beds, baths, date_observed)

    return NormalizedCompRow(
        unit_type=unit_type,
        address=address,
        unit=unit,
        beds=beds,
        baths=baths,
        rent=rent,
        gross_rent=gross_rent,
        discount_premium=discount_premium,
        date_observed=date_observed,
        link=link,
        notes=notes,
        source_type=source_type,
        source_ref=source_ref,
        observed_at=datetime.now(UTC),
        confidence_score=confidence_score,
        dedupe_key=dedupe_key,
        flags={},
    )
