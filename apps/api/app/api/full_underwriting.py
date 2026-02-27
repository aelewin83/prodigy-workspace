from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import require_deal_advance
from app.models.entities import Deal

router = APIRouter(prefix="/full-underwriting", tags=["full-underwriting"])


@router.get("/deals/{deal_id}")
def get_full_underwriting_placeholder(
    deal_id: UUID,
    deal: Deal = Depends(require_deal_advance),
):
    return {
        "deal_id": str(deal_id),
        "status": "enabled",
        "message": "Full Underwriting Enabled",
        "tabs": ["Pro Forma", "Rent Roll", "Waterfall", "Debt Model"],
    }
