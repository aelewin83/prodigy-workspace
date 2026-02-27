from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.deps import require_deal_advance
from app.api.router import api_router
from app.models.enums import DealGateState
from app.services.gating import compute_gate_state, transition_deal_gate


def test_compute_gate_state_rules():
    assert compute_gate_state(None) == DealGateState.NO_RUN
    assert compute_gate_state(SimpleNamespace(advance=False)) == DealGateState.KILL
    assert compute_gate_state(SimpleNamespace(advance=True)) == DealGateState.ADVANCE


class FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)


def test_transition_logs_only_on_state_change():
    db = FakeDB()
    deal = SimpleNamespace(id=uuid4(), current_gate_state=DealGateState.KILL, latest_boe_run_id=None)
    run = SimpleNamespace(id=uuid4(), advance=True)

    transition = transition_deal_gate(db, deal, run, uuid4())
    assert transition is not None
    assert transition.previous_state == DealGateState.KILL
    assert transition.new_state == DealGateState.ADVANCE
    assert deal.current_gate_state == DealGateState.ADVANCE
    assert deal.latest_boe_run_id == run.id
    assert len(db.added) == 1


def test_transition_no_log_when_state_unchanged():
    db = FakeDB()
    deal = SimpleNamespace(id=uuid4(), current_gate_state=DealGateState.NO_RUN, latest_boe_run_id=None)

    transition = transition_deal_gate(db, deal, None, uuid4())
    assert transition is None
    assert len(db.added) == 0


class FakeScalarDB:
    def __init__(self, responses):
        self.responses = list(responses)

    def scalar(self, _stmt):
        return self.responses.pop(0)


@pytest.fixture
def fake_user():
    return SimpleNamespace(id=uuid4())


@pytest.fixture
def fake_workspace():
    return SimpleNamespace(id=uuid4())


@pytest.mark.parametrize("state", [DealGateState.NO_RUN, DealGateState.KILL])
def test_require_deal_advance_blocks_no_run_and_kill(fake_user, fake_workspace, state):
    db = FakeScalarDB([
        SimpleNamespace(id=uuid4(), workspace_id=uuid4(), current_gate_state=state),
        fake_workspace,
    ])
    with pytest.raises(HTTPException) as exc:
        require_deal_advance(str(uuid4()), db=db, user=fake_user)
    assert exc.value.status_code == 403
    assert "Full underwriting is locked" in exc.value.detail


def test_require_deal_advance_allows_advance(fake_user, fake_workspace):
    deal = SimpleNamespace(id=uuid4(), workspace_id=uuid4(), current_gate_state=DealGateState.ADVANCE)
    db = FakeScalarDB([deal, fake_workspace])

    result = require_deal_advance(str(uuid4()), db=db, user=fake_user)
    assert result == deal


def test_no_boe_run_update_route_registered():
    for route in api_router.routes:
        if getattr(route, "path", "") == "/v1/deals/{deal_id}/boe/runs/{run_id}":
            methods = route.methods or set()
            assert "PATCH" not in methods
            assert "PUT" not in methods
