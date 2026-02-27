from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GateSummaryTestOutcomeOut(BaseModel):
    key: str
    name: str
    test_class: str
    threshold: float | None
    actual: float | None
    threshold_display: str | None
    actual_display: str | None
    result: str


class GateExplainabilityOut(BaseModel):
    tests: list[GateSummaryTestOutcomeOut]
    binding_constraint: str | None
    boe_max_bid: float | None
    max_bid_by_constraint: dict


class GateSummaryOut(BaseModel):
    gate_payload_version: str
    deal_id: UUID
    deal_name: str | None
    latest_run_id: UUID | None
    computed_status: str
    computed_pass_count: int
    computed_hard_veto_ok: bool
    computed_advance: bool
    computed_failed_hard_tests: list[str]
    computed_failed_soft_tests: list[str]
    computed_warn_tests: list[str]
    computed_pass_tests: list[str]
    computed_na_tests: list[str]
    has_override: bool
    override_status: str | None
    override_reason: str | None
    override_user: str | None
    override_created_at: datetime | None
    effective_status: str
    effective_advance: bool
    effective_pass_count: int
    explainability: GateExplainabilityOut
    ic_score: int
    ic_score_breakdown: dict
    last_updated_at: datetime | None
    audit_trail_count: int


class PortfolioSummaryOut(BaseModel):
    portfolio_payload_version: str
    deal_count: int
    status_counts: list[dict]
    avg_ic_score: float | None
    override_count: int
    override_frequency_pct: float
    binding_constraint_distribution: list[dict]


class ICPacketOut(BaseModel):
    packet_version: str
    generated_at: datetime
    deal_snapshot: dict
    gate_summary: GateSummaryOut
    recommended_max_bid: dict
    audit_history: list[dict]


class DealOutcomeCreate(BaseModel):
    recorded_at: datetime | None = None
    realized_irr: float | None = None
    realized_multiple: float | None = None
    underperformed_flag: bool | None = None
    notes: str | None = None


class DealOutcomeOut(BaseModel):
    id: UUID
    deal_id: UUID
    recorded_at: datetime
    realized_irr: float | None
    realized_multiple: float | None
    underperformed_flag: bool | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskMetricsOut(BaseModel):
    risk_payload_version: str
    limitations: list[str]
    advance_underperformance_rate: dict
    ic_score_vs_realized_irr_bins: list[dict]
    override_vs_outcome: dict
