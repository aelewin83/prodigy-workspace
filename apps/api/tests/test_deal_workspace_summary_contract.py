from types import SimpleNamespace
from uuid import uuid4

from app.api import workspaces
from app.models.enums import MemberRole, WorkspaceEdition


class FakeDB:
    def __init__(self, scalar_responses):
        self.scalar_responses = list(scalar_responses)

    def scalar(self, _stmt):
        return self.scalar_responses.pop(0)


def _test_result(key: str, test_class: str, result: str):
    return SimpleNamespace(
        test_key=key,
        test_name=key,
        test_class=SimpleNamespace(value=test_class),
        threshold=None,
        actual=None,
        threshold_display="threshold",
        actual_display="actual",
        result=SimpleNamespace(value=result),
    )


def test_workspace_deal_summary_contract_includes_required_fields():
    workspace = SimpleNamespace(id=uuid4(), edition=WorkspaceEdition.SYNDICATOR)
    member = SimpleNamespace(role=MemberRole.OWNER)
    deal = SimpleNamespace(
        id=uuid4(),
        workspace_id=workspace.id,
        name="Queens 24-Unit",
        address="31-18 37th St",
        gate_status=SimpleNamespace(value="ADVANCE"),
        gate_status_computed=SimpleNamespace(value="ADVANCE"),
        gate_override_status=None,
        gate_override_reason=None,
        gate_override_by=None,
        gate_override_at=None,
        gate_updated_at=None,
    )
    run = SimpleNamespace(
        id=uuid4(),
        created_at=None,
        binding_constraint="CapEx Multiple",
        outputs={"boe_max_bid": 9725000},
        tests=[
            _test_result("yield_on_cost", "hard", "PASS"),
            _test_result("capex_value_multiple", "hard", "PASS"),
            _test_result("positive_leverage", "hard", "PASS"),
            _test_result("cash_on_cash", "soft", "PASS"),
            _test_result("dscr", "soft", "WARN"),
            _test_result("expense_ratio", "soft", "PASS"),
            _test_result("market_cap_rate", "soft", "PASS"),
        ],
    )
    db = FakeDB([workspace, member, deal, run, True])
    out = workspaces.get_workspace_deal_summary(str(workspace.id), str(deal.id), db, SimpleNamespace(id=uuid4()))

    assert str(out["deal_id"]) == str(deal.id)
    assert out["deal_name"] == "Queens 24-Unit"
    assert out["binding_constraint"] == "CapEx Multiple"
    assert out["recommended_max_bid"] == 9725000
    assert out["decision_summary"] is not None
    assert out["decision_summary"].pass_count >= 4
