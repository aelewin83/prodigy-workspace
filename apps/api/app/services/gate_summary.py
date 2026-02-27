from __future__ import annotations

from datetime import datetime
from typing import Iterable

from app.models.entities import BOERun, BOETestResult, Deal

TEST_KEY_ORDER = [
    "yield_on_cost",
    "capex_value_multiple",
    "positive_leverage",
    "cash_on_cash",
    "dscr",
    "expense_ratio",
    "market_cap_rate",
]
TEST_KEY_INDEX = {k: i for i, k in enumerate(TEST_KEY_ORDER)}
ADVANCE_STATUSES = {"ADVANCE", "APPROVED"}


def _sorted_tests(tests: Iterable[BOETestResult]) -> list[BOETestResult]:
    return sorted(
        list(tests),
        key=lambda t: (TEST_KEY_INDEX.get(t.test_key, 999), t.test_key),
    )


def _test_keys_for(tests: list[BOETestResult], test_class: str | None = None, result: str | None = None) -> list[str]:
    out = []
    for t in tests:
        if test_class and t.test_class.value != test_class:
            continue
        if result and t.result.value != result:
            continue
        out.append(t.test_key)
    return out


def _compute_ic_score_from_tests(tests: list[BOETestResult]) -> tuple[int, dict]:
    hard_fail_count = sum(1 for t in tests if t.test_class.value == "hard" and t.result.value == "FAIL")
    soft_fail_count = sum(1 for t in tests if t.test_class.value == "soft" and t.result.value == "FAIL")
    warn_count = sum(1 for t in tests if t.result.value == "WARN")
    hard_penalty = hard_fail_count * 25
    soft_penalty = soft_fail_count * 10
    warn_penalty = warn_count * 5
    total_penalty = hard_penalty + soft_penalty + warn_penalty
    score = max(0, min(100, 100 - total_penalty))
    return score, {
        "hard_fail_count": hard_fail_count,
        "soft_fail_count": soft_fail_count,
        "warn_count": warn_count,
        "hard_fail_penalty": hard_penalty,
        "soft_fail_penalty": soft_penalty,
        "warn_penalty": warn_penalty,
        "base_score": 100,
        "total_penalty": total_penalty,
    }


def build_gate_summary(
    *,
    deal: Deal,
    latest_run: BOERun | None,
    tests: Iterable[BOETestResult],
    audit_trail_count: int,
) -> dict:
    sorted_tests = _sorted_tests(tests)
    pass_count = sum(1 for t in sorted_tests if t.result.value in {"PASS", "WARN"})
    hard_veto_ok = all(t.result.value == "PASS" for t in sorted_tests if t.test_class.value == "hard")
    computed_status = deal.gate_status_computed.value if latest_run else "NO_RUN"
    computed_advance = hard_veto_ok and pass_count >= 4 if latest_run else False

    failed_hard = _test_keys_for(sorted_tests, test_class="hard", result="FAIL")
    failed_soft = _test_keys_for(sorted_tests, test_class="soft", result="FAIL")
    warn_tests = _test_keys_for(sorted_tests, result="WARN")
    pass_tests = _test_keys_for(sorted_tests, result="PASS")
    na_tests = _test_keys_for(sorted_tests, result="N/A")

    has_override = deal.gate_override_status is not None
    effective_status = deal.gate_status.value
    effective_advance = effective_status in ADVANCE_STATUSES
    ic_score, ic_score_breakdown = _compute_ic_score_from_tests(sorted_tests)

    outputs = latest_run.outputs if latest_run else {}
    explainability = {
        "tests": [
            {
                "key": t.test_key,
                "name": t.test_name,
                "test_class": t.test_class.value,
                "threshold": t.threshold,
                "actual": t.actual,
                "threshold_display": t.threshold_display,
                "actual_display": t.actual_display,
                "result": t.result.value,
            }
            for t in sorted_tests
        ],
        "binding_constraint": latest_run.binding_constraint if latest_run else None,
        "boe_max_bid": outputs.get("boe_max_bid") if outputs else None,
        "max_bid_by_constraint": outputs.get(
            "max_bid_by_constraint",
            {
                "max_price_at_yoc": outputs.get("max_price_at_yoc") if outputs else None,
                "max_price_at_capex_multiple": outputs.get("max_price_at_capex_multiple") if outputs else None,
                "max_price_at_coc_threshold": outputs.get("max_price_at_coc_threshold") if outputs else None,
            },
        ),
    }

    return {
        "gate_payload_version": "1.0",
        "deal_id": deal.id,
        "deal_name": deal.name,
        "latest_run_id": latest_run.id if latest_run else None,
        "computed_status": computed_status,
        "computed_pass_count": pass_count,
        "computed_hard_veto_ok": hard_veto_ok,
        "computed_advance": computed_advance,
        "computed_failed_hard_tests": failed_hard,
        "computed_failed_soft_tests": failed_soft,
        "computed_warn_tests": warn_tests,
        "computed_pass_tests": pass_tests,
        "computed_na_tests": na_tests,
        "has_override": has_override,
        "override_status": deal.gate_override_status.value if deal.gate_override_status else None,
        "override_reason": deal.gate_override_reason,
        "override_user": deal.gate_override_by,
        "override_created_at": deal.gate_override_at,
        "effective_status": effective_status,
        "effective_advance": effective_advance,
        "effective_pass_count": pass_count,
        "explainability": explainability,
        "ic_score": ic_score,
        "ic_score_breakdown": ic_score_breakdown,
        "last_updated_at": deal.gate_updated_at or (latest_run.created_at if latest_run else None),
        "audit_trail_count": audit_trail_count,
    }


def status_sort_key(status: str) -> int:
    order = ["BLOCKED", "NEEDS_WORK", "ADVANCE", "APPROVED", "NO_RUN"]
    try:
        return order.index(status)
    except ValueError:
        return 999
