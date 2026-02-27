from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import CompRunStatus, ListingSourceType, UnitType, VarianceBasis


class CompListingInput(BaseModel):
    address: str
    unit: str | None = None
    beds: float | None = None
    baths: float | None = None
    rent: float | None = None
    gross_rent: float | None = None
    date_observed: date | None = None
    link: str | None = None
    notes: str | None = None
    confidence_score: float | None = None


class CompRunManualCreate(BaseModel):
    filters: dict = Field(default_factory=dict)
    listings: list[CompListingInput]


class CompRunPrivateImportCreate(BaseModel):
    filters: dict = Field(default_factory=dict)
    file_key: str
    file_type: str


class CompRunPublicPullCreate(BaseModel):
    filters: dict = Field(default_factory=dict)
    connector_ids: list[str]


class CompSubjectUpsert(BaseModel):
    unit_type: UnitType
    subject_rent: float | None = None
    subject_gross_rent: float | None = None


class CompRunOut(BaseModel):
    id: UUID
    workspace_id: UUID
    deal_id: UUID
    filters: dict
    status: CompRunStatus
    source_mix: dict
    parse_report: dict | None
    started_at: datetime | None
    finished_at: datetime | None
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class CompRollupOut(BaseModel):
    unit_type: UnitType
    avg_rent: float | None
    avg_gross_rent: float | None
    avg_discount_premium: float | None
    median_rent: float | None
    p25_rent: float | None
    p75_rent: float | None
    sample_size: int

    model_config = {"from_attributes": True}


class CompVarianceOut(BaseModel):
    unit_type: UnitType
    variance_net: float | None
    variance_gross: float | None
    basis: VarianceBasis

    model_config = {"from_attributes": True}


class CompRecommendationsUnit(BaseModel):
    unit_type: UnitType
    suggested_fm_rent: float | None
    low: float | None
    high: float | None
    confidence_score: float
    sample_size: int


class CompRecommendationsResponse(BaseModel):
    deal_id: UUID
    basis: VarianceBasis
    recommendations: list[CompRecommendationsUnit]


class CompListingOut(BaseModel):
    id: UUID
    comp_run_id: UUID
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
    confidence_score: float | None
    dedupe_key: str
    flags: dict

    model_config = {"from_attributes": True}
