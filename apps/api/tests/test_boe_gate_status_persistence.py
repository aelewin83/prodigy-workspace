from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api import boe
from app.boe.engine import BOEDecision, BOEOutput, BOETestOutcome, GateStatus, TestClass, TestResult
from app.models.enums import DealStatus
from app.schemas.boe import BOERunCreate


class FakeDB:
    def __init__(self, scalar_responses):
        self._scalar_responses = list(scalar_responses)
        self.added = []
        self.committed = False

    def scalar(self, _stmt):
        return self._scalar_responses.pop(0)

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        return None

    def commit(self):
        self.committed = True


@pytest.mark.parametrize(
    ("decision_status", "expected_status"),
    [
        (GateStatus.BLOCKED, DealStatus.BLOCKED),
        (GateStatus.NEEDS_WORK, DealStatus.NEEDS_WORK),
        (GateStatus.ADVANCE, DealStatus.ADVANCE),
    ],
)
def test_create_boe_run_persists_computed_gate_status(monkeypatch, decision_status, expected_status):
    deal = SimpleNamespace(
        id=uuid4(),
        workspace_id=uuid4(),
        current_gate_state=None,
        latest_boe_run_id=None,
        gate_status=DealStatus.NEEDS_WORK,
        gate_status_computed=DealStatus.NEEDS_WORK,
        gate_override_status=None,
        gate_updated_at=None,
    )
    fake_run_for_response = SimpleNamespace(
        id=uuid4(),
        deal_id=deal.id,
        version=1,
        inputs={},
        outputs={},
        decision="ADVANCE",
        binding_constraint="YOC",
        hard_veto_ok=True,
        pass_count=4,
        advance=True,
        created_by=uuid4(),
        created_at=None,
        tests=[],
    )
    db = FakeDB([0, fake_run_for_response])

    monkeypatch.setattr(boe, "get_deal_with_access", lambda *_args, **_kwargs: deal)
    monkeypatch.setattr(boe, "log_boe_run_created", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(boe, "transition_deal_gate", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(boe, "serialize_output", lambda _output: {})
    monkeypatch.setattr(boe, "_serialize_boe_run", lambda _run: {"ok": True})

    calls = []

    def _fake_apply_computed(db_session, deal_obj, computed_status, **kwargs):
        calls.append((db_session, deal_obj, computed_status, kwargs))
        deal_obj.gate_status_computed = computed_status
        deal_obj.gate_status = computed_status
        return True

    monkeypatch.setattr(boe, "apply_computed_gate_status", _fake_apply_computed)
    fake_output = BOEOutput(
        market_cap_rate=None,
        seller_noi_from_om=None,
        asking_cap_rate=None,
        analysis_cap_rate=None,
        y1_exit_cap_rate=None,
        y1_dscr=None,
        y1_capex_value_multiple=None,
        y1_expense_ratio=None,
        y1_cash_on_cash=None,
        y1_yield_on_cost_unlevered=None,
        residual_sale_at_exit_cap=None,
        profit_potential=None,
        max_price_at_yoc=None,
        max_price_at_capex_multiple=None,
        max_price_at_coc_threshold=None,
        max_bid_by_constraint=SimpleNamespace(
            max_price_at_yoc=None,
            max_price_at_capex_multiple=None,
            max_price_at_coc_threshold=None,
        ),
        boe_max_bid=None,
        delta_vs_asking=None,
        deposit_amount=None,
        binding_constraint="YOC",
    )
    fake_tests = [
        BOETestOutcome(
            key="yield_on_cost",
            name="Yield on Cost Test",
            test_class=TestClass.HARD,
            threshold=None,
            actual=None,
            threshold_display="N/A",
            actual_display="N/A",
            result=TestResult.PASS,
        )
    ]
    fake_decision = BOEDecision(
        status=decision_status,
        hard_veto_ok=decision_status != GateStatus.BLOCKED,
        pass_count=4 if decision_status == GateStatus.ADVANCE else 3,
        total_tests=7,
        failed_hard_tests=[],
        failed_soft_tests=[],
        warn_tests=[],
        pass_tests=[],
        na_tests=[],
        advance=decision_status == GateStatus.ADVANCE,
    )
    monkeypatch.setattr(boe, "calculate_boe", lambda *_args, **_kwargs: (fake_output, fake_tests, fake_decision))

    payload = BOERunCreate(inputs={})
    user = SimpleNamespace(id=uuid4())
    _ = boe.create_boe_run(deal_id=deal.id, payload=payload, db=db, user=user)

    assert calls
    assert calls[0][2] == expected_status
    assert deal.gate_status == expected_status
    assert deal.gate_status_computed == expected_status
    assert db.committed is True
