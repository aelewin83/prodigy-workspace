import pytest

from app.boe.engine import BOEInput, GateStatus as BOEGateStatus, TestResult as BOETestResult, calculate_boe


@pytest.fixture
def boe_base_inputs() -> dict:
    return dict(
        asking_price=10_000_000,
        deposit_pct=0.05,
        interest_rate=0.045,
        ltc=0.7,
        capex_budget=1_000_000,
        seller_noi_from_om=500_000,
        gross_income=1_000_000,
        operating_expenses=300_000,
        y1_exit_cap_rate=0.03,
    )


def _get_test_result(tests, key: str) -> BOETestResult:
    return next(t for t in tests if t.key == key).result


def _solve_noi_for_target_dscr(base: dict, target_dscr: float) -> int:
    ref_noi = 600_000
    output, _, _ = calculate_boe(BOEInput(y1_noi=ref_noi, **base))
    assert output.y1_dscr is not None and output.y1_dscr > 0
    debt_service = ref_noi / output.y1_dscr
    return int(round(target_dscr * debt_service))


def test_testresult_enum_values_are_stable():
    assert BOETestResult.PASS.value == "PASS"
    assert BOETestResult.FAIL.value == "FAIL"
    assert BOETestResult.WARN.value == "WARN"
    assert BOETestResult.NA.value == "N/A"


def test_dscr_warn_counts_toward_gate_pass_count(boe_base_inputs):
    # This test must be robust to small BOE threshold changes.
    # It searches for a NOI that yields DSCR=WARN for a fixed base case,
    # and then asserts WARN is counted toward the pass tally.
    base = boe_base_inputs

    warn_noi = None
    fail_noi = None

    # Search a reasonable range of NOI values for a WARN and FAIL DSCR case
    for noi in range(900_000, 200_000, -5_000):
        _, tests, _ = calculate_boe(BOEInput(y1_noi=noi, **base))
        dscr = _get_test_result(tests, "dscr")
        if dscr == BOETestResult.WARN and warn_noi is None:
            warn_noi = noi
        if dscr == BOETestResult.FAIL and fail_noi is None:
            fail_noi = noi
        if warn_noi is not None and fail_noi is not None:
            break

    assert warn_noi is not None, "Could not find a DSCR WARN case for this base"
    assert fail_noi is not None, "Could not find a DSCR FAIL case for this base"

    output_warn, tests_warn, decision_warn = calculate_boe(BOEInput(y1_noi=warn_noi, **base))
    _, tests_fail, decision_fail = calculate_boe(BOEInput(y1_noi=fail_noi, **base))

    dscr = next(t for t in tests_warn if t.key == "dscr")
    assert dscr.result == BOETestResult.WARN
    assert _get_test_result(tests_fail, "dscr") == BOETestResult.FAIL

    # Core requirement: WARN counts toward the pass tally more than FAIL does.
    assert decision_warn.pass_count >= decision_fail.pass_count
    assert decision_warn.pass_count == len(decision_warn.pass_tests) + len(decision_warn.warn_tests)
    assert decision_warn.total_tests == 7
    assert decision_fail.total_tests == 7

    # Also ensure binding constraint is one of the expected labels
    assert output_warn.binding_constraint in {"YOC", "CapEx Multiple", "CoC"}


@pytest.mark.parametrize(
    ("target_dscr", "expected"),
    [
        (1.25, BOETestResult.PASS),
        (1.249, BOETestResult.WARN),
        (1.20, BOETestResult.WARN),
        (1.15, BOETestResult.WARN),
        (1.149, BOETestResult.FAIL),
    ],
)
def test_dscr_threshold_boundaries_follow_rules(boe_base_inputs, target_dscr: float, expected: BOETestResult):
    noi = _solve_noi_for_target_dscr(boe_base_inputs, target_dscr)
    _, tests, _ = calculate_boe(BOEInput(y1_noi=noi, **boe_base_inputs))
    assert _get_test_result(tests, "dscr") == expected


def test_gate_pass_count_warn_counts_more_than_fail(boe_base_inputs):
    warn_noi = None
    fail_noi = None

    for noi in range(900_000, 200_000, -5_000):
        _, tests, _ = calculate_boe(BOEInput(y1_noi=noi, **boe_base_inputs))
        if _get_test_result(tests, "dscr") == BOETestResult.WARN:
            warn_noi = noi
        if _get_test_result(tests, "dscr") == BOETestResult.FAIL:
            fail_noi = noi
        if warn_noi is not None and fail_noi is not None:
            break

    assert warn_noi is not None, "Could not find DSCR WARN case"
    assert fail_noi is not None, "Could not find DSCR FAIL case"

    _, tests_warn, decision_warn = calculate_boe(BOEInput(y1_noi=warn_noi, **boe_base_inputs))
    _, tests_fail, decision_fail = calculate_boe(BOEInput(y1_noi=fail_noi, **boe_base_inputs))

    assert _get_test_result(tests_warn, "dscr") == BOETestResult.WARN
    assert _get_test_result(tests_fail, "dscr") == BOETestResult.FAIL
    assert decision_warn.pass_count > decision_fail.pass_count
    assert decision_fail.status == BOEGateStatus.BLOCKED


def test_gate_decision_has_stable_advance_and_kill_cases():
    advance_case = BOEInput(
        asking_price=10_000_000,
        deposit_pct=0.05,
        interest_rate=0.06,
        ltc=0.7,
        capex_budget=1_000_000,
        soft_cost_pct=0.0,
        reserves=0.0,
        seller_noi_from_om=600_000,
        gross_income=1_000_000,
        operating_expenses=300_000,
        y1_noi=700_000,
        y1_exit_cap_rate=0.05,
    )
    kill_case = BOEInput(
        asking_price=10_000_000,
        deposit_pct=0.05,
        interest_rate=0.06,
        ltc=0.7,
        capex_budget=1_000_000,
        soft_cost_pct=0.0,
        reserves=0.0,
        seller_noi_from_om=500_000,
        gross_income=1_000_000,
        operating_expenses=350_000,
        y1_noi=416_000,
        y1_exit_cap_rate=0.05,
    )

    advance_output, _, advance_decision = calculate_boe(advance_case)
    _, _, kill_decision = calculate_boe(kill_case)

    assert advance_decision.total_tests == 7
    assert advance_decision.advance is True
    assert advance_decision.status == BOEGateStatus.ADVANCE
    assert kill_decision.total_tests == 7
    assert kill_decision.advance is False
    assert kill_decision.status == BOEGateStatus.BLOCKED
    assert "yield_on_cost" in kill_decision.failed_hard_tests
    assert set(advance_output.max_bid_by_constraint.__dict__.keys()) == {
        "max_price_at_yoc",
        "max_price_at_capex_multiple",
        "max_price_at_coc_threshold",
    }
    assert advance_output.max_bid_by_constraint.max_price_at_yoc == advance_output.max_price_at_yoc
    assert advance_output.max_bid_by_constraint.max_price_at_capex_multiple == advance_output.max_price_at_capex_multiple
    assert advance_output.max_bid_by_constraint.max_price_at_coc_threshold == advance_output.max_price_at_coc_threshold


def test_gate_status_needs_work_when_not_blocked_and_not_advance(monkeypatch):
    from app.boe import engine as boe_engine

    monkeypatch.setattr(boe_engine, "QUORUM_REQUIRED", 8)
    needs_work_case = BOEInput(
        asking_price=10_000_000,
        deposit_pct=0.05,
        interest_rate=0.06,
        ltc=0.7,
        capex_budget=1_000_000,
        soft_cost_pct=0.0,
        reserves=0.0,
        seller_noi_from_om=600_000,
        gross_income=1_000_000,
        operating_expenses=300_000,
        y1_noi=700_000,
        y1_exit_cap_rate=0.05,
    )

    _, tests, decision = calculate_boe(needs_work_case)
    assert decision.hard_veto_ok is True
    assert decision.advance is False
    assert decision.status == BOEGateStatus.NEEDS_WORK
    assert decision.pass_count < 8
    assert _get_test_result(tests, "dscr") == BOETestResult.PASS
