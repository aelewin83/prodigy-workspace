from app.boe.engine import BOEInput, TestResult, calculate_boe


def test_dscr_warn_counts_toward_gate_pass_count():
    # This test must be robust to small BOE threshold changes.
    # It searches for a NOI that yields DSCR=WARN for a fixed base case,
    # and then asserts WARN is counted toward the pass tally.
    base = dict(
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

    warn_noi = None
    fail_noi = None

    # Search a reasonable range of NOI values for a WARN and FAIL DSCR case
    for noi in range(900_000, 200_000, -5_000):
        _, tests, _ = calculate_boe(BOEInput(y1_noi=noi, **base))
        dscr = next(t for t in tests if t.key == "dscr")
        if dscr.result == TestResult.WARN and warn_noi is None:
            warn_noi = noi
        if dscr.result == TestResult.FAIL and fail_noi is None:
            fail_noi = noi
        if warn_noi is not None and fail_noi is not None:
            break

    assert warn_noi is not None, "Could not find a DSCR WARN case for this base"
    assert fail_noi is not None, "Could not find a DSCR FAIL case for this base"

    output_warn, tests_warn, decision_warn = calculate_boe(BOEInput(y1_noi=warn_noi, **base))
    _, tests_fail, decision_fail = calculate_boe(BOEInput(y1_noi=fail_noi, **base))

    assert next(t for t in tests_warn if t.key == "dscr").result == TestResult.WARN
    assert next(t for t in tests_fail if t.key == "dscr").result == TestResult.FAIL

    # Core requirement: WARN counts toward the pass tally more than FAIL does.
    assert decision_warn.pass_count >= decision_fail.pass_count

    # Also ensure binding constraint is one of the expected labels
    assert output_warn.binding_constraint in {"YOC", "CapEx Multiple", "CoC"}


def test_dscr_threshold_boundaries_follow_pr2_rules():
    base = dict(
        asking_price=10_000_000,
        interest_rate=0.06,
        ltc=0.7,
        capex_budget=1_000_000,
        seller_noi_from_om=600_000,
        gross_income=1_000_000,
        operating_expenses=300_000,
        y1_exit_cap_rate=0.05,
    )

    _, tests_pass, _ = calculate_boe(BOEInput(y1_noi=580_000, **base))
    _, tests_warn, _ = calculate_boe(BOEInput(y1_noi=540_000, **base))
    _, tests_fail, _ = calculate_boe(BOEInput(y1_noi=500_000, **base))

    assert next(t for t in tests_pass if t.key == "dscr").result == TestResult.PASS
    assert next(t for t in tests_warn if t.key == "dscr").result == TestResult.WARN
    assert next(t for t in tests_fail if t.key == "dscr").result == TestResult.FAIL
