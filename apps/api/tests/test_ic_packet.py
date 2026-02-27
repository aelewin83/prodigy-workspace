from types import SimpleNamespace
from uuid import uuid4

from app.api import deals


class FakeScalarList:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class FakeDB:
    def scalar(self, _stmt):
        return 2

    def scalars(self, _stmt):
        events = [
            SimpleNamespace(
                event_type="OVERRIDE_SET",
                from_status="BLOCKED",
                to_status="APPROVED",
                source="USER_OVERRIDE",
                reason="IC approval",
                created_at=None,
                metadata_json={"override_by": "u1"},
            )
        ]
        return FakeScalarList(events)


def test_ic_packet_structure_contains_gate_summary_and_versions(monkeypatch):
    deal = SimpleNamespace(id=uuid4(), name="Deal X", address="A", asking_price=10_000_000)
    run = SimpleNamespace(
        id=uuid4(),
        outputs={"boe_max_bid": 9_000_000, "delta_vs_asking": -1_000_000},
        binding_constraint="YOC",
        tests=[],
    )
    monkeypatch.setattr(deals, "_get_deal_with_access", lambda *_args, **_kwargs: deal)
    monkeypatch.setattr(deals, "_get_latest_run_with_tests", lambda *_args, **_kwargs: run)
    monkeypatch.setattr(
        deals,
        "build_gate_summary",
        lambda **_kwargs: {
            "gate_payload_version": "1.0",
            "deal_id": deal.id,
            "deal_name": deal.name,
            "latest_run_id": run.id,
            "computed_status": "ADVANCE",
            "computed_pass_count": 5,
            "computed_hard_veto_ok": True,
            "computed_advance": True,
            "computed_failed_hard_tests": [],
            "computed_failed_soft_tests": [],
            "computed_warn_tests": [],
            "computed_pass_tests": [],
            "computed_na_tests": [],
            "has_override": False,
            "override_status": None,
            "override_reason": None,
            "override_user": None,
            "override_created_at": None,
            "effective_status": "ADVANCE",
            "effective_advance": True,
            "effective_pass_count": 5,
            "explainability": {"tests": [], "binding_constraint": "YOC", "boe_max_bid": 9000000, "max_bid_by_constraint": {}},
            "ic_score": 90,
            "ic_score_breakdown": {},
            "last_updated_at": None,
            "audit_trail_count": 2,
        },
    )

    payload = deals.get_deal_ic_packet(deal_id=str(deal.id), db=FakeDB(), user=SimpleNamespace(id=uuid4()))
    assert payload["packet_version"] == "1.0"
    assert payload["gate_summary"]["gate_payload_version"] == "1.0"
    assert payload["recommended_max_bid"]["boe_max_bid"] == 9_000_000
    assert payload["audit_history"][0]["event_type"] == "OVERRIDE_SET"
