from types import SimpleNamespace
from uuid import uuid4

from app.services.gate_summary import build_gate_summary


def _test_result(key: str, test_class: str, result: str, threshold: float | None = None, actual: float | None = None):
    return SimpleNamespace(
        test_key=key,
        test_name=key,
        test_class=SimpleNamespace(value=test_class),
        threshold=threshold,
        actual=actual,
        threshold_display="t",
        actual_display="a",
        result=SimpleNamespace(value=result),
    )


def test_gate_summary_no_override_effective_matches_computed_and_order_is_stable():
    deal = SimpleNamespace(
        id=uuid4(),
        name="Deal A",
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
        binding_constraint="CapEx Multiple",
        outputs={"boe_max_bid": 9_500_000, "max_bid_by_constraint": {"max_price_at_yoc": 9600000}},
        created_at=None,
    )
    tests = [
        _test_result("dscr", "soft", "WARN"),
        _test_result("yield_on_cost", "hard", "PASS"),
        _test_result("positive_leverage", "hard", "PASS"),
        _test_result("capex_value_multiple", "hard", "PASS"),
        _test_result("cash_on_cash", "soft", "PASS"),
        _test_result("expense_ratio", "soft", "FAIL"),
        _test_result("market_cap_rate", "soft", "PASS"),
    ]

    summary = build_gate_summary(deal=deal, latest_run=run, tests=tests, audit_trail_count=2)
    assert summary["computed_status"] == "ADVANCE"
    assert summary["effective_status"] == "ADVANCE"
    assert summary["computed_pass_count"] == 6  # WARN counts
    assert summary["effective_pass_count"] == 6
    assert summary["audit_trail_count"] == 2
    assert [t["key"] for t in summary["explainability"]["tests"]] == [
        "yield_on_cost",
        "capex_value_multiple",
        "positive_leverage",
        "cash_on_cash",
        "dscr",
        "expense_ratio",
        "market_cap_rate",
    ]


def test_gate_summary_override_changes_effective_not_computed():
    deal = SimpleNamespace(
        id=uuid4(),
        name="Deal B",
        gate_status=SimpleNamespace(value="APPROVED"),
        gate_status_computed=SimpleNamespace(value="BLOCKED"),
        gate_override_status=SimpleNamespace(value="APPROVED"),
        gate_override_reason="Manual IC override",
        gate_override_by="user-1",
        gate_override_at=None,
        gate_updated_at=None,
    )
    run = SimpleNamespace(id=uuid4(), binding_constraint=None, outputs={}, created_at=None)
    tests = [
        _test_result("yield_on_cost", "hard", "FAIL"),
        _test_result("capex_value_multiple", "hard", "PASS"),
        _test_result("positive_leverage", "hard", "PASS"),
    ]

    summary = build_gate_summary(deal=deal, latest_run=run, tests=tests, audit_trail_count=1)
    assert summary["has_override"] is True
    assert summary["computed_status"] == "BLOCKED"
    assert summary["effective_status"] == "APPROVED"
    assert summary["computed_failed_hard_tests"] == ["yield_on_cost"]
