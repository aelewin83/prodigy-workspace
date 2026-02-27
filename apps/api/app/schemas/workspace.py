from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import WorkspaceEdition

class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceEditionUpdate(BaseModel):
    edition: WorkspaceEdition


class WorkspaceOut(BaseModel):
    id: UUID
    name: str
    edition: WorkspaceEdition
    capabilities: dict
    is_admin: bool = False
    edition_updated_at: datetime | None
    edition_updated_by_user_id: UUID | None
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
