from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.boe import BOEDecisionSummaryOut


class DealWorkspaceSummaryOut(BaseModel):
    deal_id: UUID
    workspace_id: UUID
    deal_name: str
    address: str | None
    gate_status: str
    gate_status_effective: str
    ic_score: int | None
    recommended_max_bid: float | None
    binding_constraint: str | None
    latest_run_id: UUID | None
    latest_run_created_at: datetime | None
    decision_summary: BOEDecisionSummaryOut | None
    override: dict | None
    capabilities: dict


class DealActivityActorOut(BaseModel):
    id: str | None
    email: str | None
    name: str | None


class DealActivityEventOut(BaseModel):
    id: str
    type: str
    created_at: datetime
    actor: DealActivityActorOut
    summary: str
    metadata: dict


class DealCommentCreate(BaseModel):
    body: str


class DealOverrideActionRequest(BaseModel):
    status: str | None = None
    comment: str | None = None
    # backward-compatible aliases
    override_status: str | None = None
    reason: str | None = None
