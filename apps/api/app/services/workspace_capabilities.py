from __future__ import annotations

from app.models.enums import WorkspaceEdition


def capabilities_for_edition(edition: WorkspaceEdition) -> dict:
    base = {
        "deals": True,
        "boe": True,
        "ic_packet_basic": True,
        "portfolio_view": True,
        "fund_mode": False,
        "fund_admin": False,
        "fund_reporting": False,
    }
    if edition == WorkspaceEdition.FUND:
        base.update(
            {
                "fund_mode": True,
                "fund_admin": True,
                "fund_reporting": True,
            }
        )
    return {"features": base}
