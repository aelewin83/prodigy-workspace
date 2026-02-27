from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import DealGateState


class DealCreate(BaseModel):
    workspace_id: UUID
    name: str
    address: str | None = None
    asking_price: Decimal | None = None


class DealUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    asking_price: Decimal | None = None


class DealOut(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    address: str | None
    asking_price: Decimal | None
    current_gate_state: DealGateState
    latest_boe_run_id: UUID | None
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
