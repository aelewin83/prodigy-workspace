from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class TestClass(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class TestResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    NA = "N/A"


@dataclass(frozen=True)
class BOEInput:
    asking_price: float | None = None
    deposit_pct: float | None = None
    interest_rate: float | None = None
    ltc: float | None = None
    capex_budget: float | None = None
    soft_cost_pct: float | None = None
    reserves: float | None = None
    seller_noi_from_om: float | None = None
    gross_income: float | None = None
    operating_expenses: float | None = None
    y1_noi: float | None = None
    market_cap_rate: float | None = None
    y1_exit_cap_rate: float | None = None


@dataclass(frozen=True)
class BOETestOutcome:
    key: str
    name: str
    test_class: TestClass
    threshold: float | None
    actual: float | None
    threshold_display: str
    actual_display: str
    result: TestResult


@dataclass(frozen=True)
class BOEDecision:
    hard_veto_ok: bool
    pass_count: int
    total_tests: int
    failed_hard_tests: list[str]
    failed_soft_tests: list[str]
    warn_tests: list[str]
    pass_tests: list[str]
    na_tests: list[str]
    advance: bool


@dataclass(frozen=True)
class BOEConstraintMaxBids:
    max_price_at_yoc: float | None
    max_price_at_capex_multiple: float | None
    max_price_at_coc_threshold: float | None


@dataclass(frozen=True)
class BOEOutput:
    market_cap_rate: float | None
    seller_noi_from_om: float | None
    asking_cap_rate: float | None
    analysis_cap_rate: float | None
    y1_exit_cap_rate: float | None
    y1_dscr: float | None
    y1_capex_value_multiple: float | None
    y1_expense_ratio: float | None
    y1_cash_on_cash: float | None
    y1_yield_on_cost_unlevered: float | None
    residual_sale_at_exit_cap: float | None
    profit_potential: float | None
    max_price_at_yoc: float | None
    max_price_at_capex_multiple: float | None
    max_price_at_coc_threshold: float | None
    max_bid_by_constraint: BOEConstraintMaxBids
    boe_max_bid: float | None
    delta_vs_asking: float | None
    deposit_amount: float | None
    binding_constraint: str | None


TARGET_COC = 0.045
TARGET_CAPEX_MULTIPLE = 2.0
QUORUM_REQUIRED = 4
PASSING_RESULTS = {TestResult.PASS, TestResult.WARN}


def _f(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_div(n: float | None, d: float | None) -> float | None:
    if n is None or d in (None, 0):
        return None
    return n / d


def _fmt_pct(v: float | None) -> str:
    return "N/A" if v is None else f"{v:.2%}"


def _fmt_num(v: float | None) -> str:
    return "N/A" if v is None else f"{v:.2f}"


def _fmt_mult(v: float | None) -> str:
    return "N/A" if v is None else f"{v:.2f}x"


def _counts_as_pass(result: TestResult) -> bool:
    return result in PASSING_RESULTS


def _evaluate_tests(metrics: BOEOutput, interest_rate: float | None) -> tuple[list[BOETestOutcome], BOEDecision]:
    tests: list[BOETestOutcome] = []

    yoc = metrics.y1_yield_on_cost_unlevered
    exit_cap = metrics.y1_exit_cap_rate
    if yoc is None or exit_cap is None:
        result = TestResult.NA
    else:
        result = TestResult.PASS if yoc >= exit_cap + 0.01 else TestResult.FAIL
    tests.append(
        BOETestOutcome(
            key="yield_on_cost",
            name="Yield on Cost Test",
            test_class=TestClass.HARD,
            threshold=(exit_cap + 0.01) if exit_cap is not None else None,
            actual=yoc,
            threshold_display=f">= Exit Cap + 1.00% ({_fmt_pct(exit_cap)} + 1.00%)",
            actual_display=_fmt_pct(yoc),
            result=result,
        )
    )

    capex_multiple = metrics.y1_capex_value_multiple
    if capex_multiple is None:
        result = TestResult.NA
    else:
        result = TestResult.PASS if capex_multiple >= TARGET_CAPEX_MULTIPLE else TestResult.FAIL
    tests.append(
        BOETestOutcome(
            key="capex_value_multiple",
            name="CapEx Value Multiple Test",
            test_class=TestClass.HARD,
            threshold=TARGET_CAPEX_MULTIPLE,
            actual=capex_multiple,
            threshold_display=">= 2.00x",
            actual_display=_fmt_mult(capex_multiple),
            result=result,
        )
    )

    if yoc is None or interest_rate is None or yoc <= 0 or interest_rate <= 0:
        result = TestResult.NA
    else:
        result = TestResult.PASS if yoc >= interest_rate else TestResult.FAIL
    tests.append(
        BOETestOutcome(
            key="positive_leverage",
            name="Positive Leverage Test",
            test_class=TestClass.HARD,
            threshold=interest_rate,
            actual=yoc,
            threshold_display=f">= Interest Rate ({_fmt_pct(interest_rate)})",
            actual_display=_fmt_pct(yoc),
            result=result,
        )
    )

    coc = metrics.y1_cash_on_cash
    if coc is None:
        result = TestResult.NA
    else:
        result = TestResult.PASS if coc >= TARGET_COC else TestResult.FAIL
    tests.append(
        BOETestOutcome(
            key="cash_on_cash",
            name="Cash on Cash Test",
            test_class=TestClass.SOFT,
            threshold=TARGET_COC,
            actual=coc,
            threshold_display=">= 4.50%",
            actual_display=_fmt_pct(coc),
            result=result,
        )
    )

    dscr = metrics.y1_dscr
    if dscr is None or dscr <= 0:
        result = TestResult.NA
    elif dscr >= 1.25:
        result = TestResult.PASS
    elif dscr >= 1.15:
        result = TestResult.WARN
    else:
        result = TestResult.FAIL
    tests.append(
        BOETestOutcome(
            key="dscr",
            name="DSCR Test",
            test_class=TestClass.SOFT,
            threshold=1.25,
            actual=dscr,
            threshold_display="PASS>=1.25 | WARN>=1.15 | FAIL<1.15",
            actual_display=_fmt_num(dscr),
            result=result,
        )
    )

    expense_ratio = metrics.y1_expense_ratio
    if expense_ratio is None:
        result = TestResult.NA
    else:
        result = TestResult.PASS if expense_ratio >= 0.28 else TestResult.FAIL
    tests.append(
        BOETestOutcome(
            key="expense_ratio",
            name="Expense Ratio Test",
            test_class=TestClass.SOFT,
            threshold=0.28,
            actual=expense_ratio,
            threshold_display=">= 28.00%",
            actual_display=_fmt_pct(expense_ratio),
            result=result,
        )
    )

    market_cap = metrics.market_cap_rate
    asking_cap = metrics.asking_cap_rate
    if market_cap is None or asking_cap is None or market_cap <= 0 or asking_cap <= 0:
        result = TestResult.NA
    else:
        result = TestResult.PASS if market_cap >= asking_cap else TestResult.FAIL
    tests.append(
        BOETestOutcome(
            key="market_cap_rate",
            name="Market Cap Rate Test",
            test_class=TestClass.SOFT,
            threshold=asking_cap,
            actual=market_cap,
            threshold_display=f">= Asking Cap Rate ({_fmt_pct(asking_cap)})",
            actual_display=_fmt_pct(market_cap),
            result=result,
        )
    )

    hard_veto_ok = all(t.result == TestResult.PASS for t in tests if t.test_class == TestClass.HARD)
    pass_count = sum(1 for t in tests if _counts_as_pass(t.result))
    total_tests = len(tests)
    failed_hard_tests = [
        t.key for t in tests
        if t.test_class == TestClass.HARD and t.result == TestResult.FAIL
    ]
    failed_soft_tests = [
        t.key for t in tests
        if t.test_class == TestClass.SOFT and t.result == TestResult.FAIL
    ]
    warn_tests = [
        t.key for t in tests
        if t.result == TestResult.WARN
    ]
    pass_tests = [
        t.key for t in tests
        if t.result == TestResult.PASS
    ]
    na_tests = [
        t.key for t in tests
        if t.result == TestResult.NA
    ]
    quorum_met = pass_count >= QUORUM_REQUIRED

    advance = hard_veto_ok and quorum_met

    return tests, BOEDecision(
        hard_veto_ok=hard_veto_ok,
        pass_count=pass_count,
        total_tests=total_tests,
        failed_hard_tests=failed_hard_tests,
        failed_soft_tests=failed_soft_tests,
        warn_tests=warn_tests,
        pass_tests=pass_tests,
        na_tests=na_tests,
        advance=advance,
    )


def calculate_boe(inputs: BOEInput) -> tuple[BOEOutput, list[BOETestOutcome], BOEDecision]:
    asking_price = _f(inputs.asking_price)
    deposit_pct = _f(inputs.deposit_pct) or 0.0
    interest_rate = _f(inputs.interest_rate)
    ltc = _f(inputs.ltc) or 0.0
    capex_budget = _f(inputs.capex_budget) or 0.0
    soft_cost_pct = _f(inputs.soft_cost_pct) or 0.0
    reserves = _f(inputs.reserves) or 0.0
    seller_noi = _f(inputs.seller_noi_from_om)
    gross_income = _f(inputs.gross_income)
    operating_expenses = _f(inputs.operating_expenses)

    y1_noi = _f(inputs.y1_noi)
    if y1_noi is None and gross_income is not None and operating_expenses is not None:
        y1_noi = gross_income - operating_expenses

    total_project_cost = None
    if asking_price is not None:
        total_project_cost = asking_price * (1 + soft_cost_pct) + capex_budget + reserves

    debt_amount = total_project_cost * ltc if total_project_cost is not None else None
    equity_required = total_project_cost - debt_amount if total_project_cost is not None and debt_amount is not None else None
    debt_service = debt_amount * interest_rate if debt_amount is not None and interest_rate is not None else None

    market_cap_rate = _f(inputs.market_cap_rate)
    if market_cap_rate is None:
        market_cap_rate = _safe_div(y1_noi, asking_price)

    asking_cap_rate = _safe_div(seller_noi, asking_price)
    analysis_cap_rate = _safe_div(y1_noi, asking_price)

    y1_exit_cap_rate = _f(inputs.y1_exit_cap_rate)
    if y1_exit_cap_rate is None:
        y1_exit_cap_rate = market_cap_rate

    y1_dscr = _safe_div(y1_noi, debt_service)
    residual_sale = _safe_div(y1_noi, y1_exit_cap_rate)

    y1_capex_value_multiple = None
    if residual_sale is not None and asking_price is not None and capex_budget > 0:
        y1_capex_value_multiple = (residual_sale - asking_price) / capex_budget

    y1_expense_ratio = _safe_div(operating_expenses, gross_income)
    y1_cash_on_cash = _safe_div((y1_noi - debt_service) if y1_noi is not None and debt_service is not None else None, equity_required)
    y1_yoc = _safe_div(y1_noi, total_project_cost)

    max_price_at_yoc = _safe_div(y1_noi, (y1_exit_cap_rate + 0.01) if y1_exit_cap_rate is not None else None)

    max_price_at_capex_multiple = None
    if residual_sale is not None and capex_budget is not None:
        max_price_at_capex_multiple = residual_sale - TARGET_CAPEX_MULTIPLE * capex_budget

    max_price_at_coc_threshold = None
    if y1_noi is not None:
        coeff = (interest_rate or 0) * ltc + TARGET_COC * (1 - ltc)
        if coeff > 0:
            target_total_cost = y1_noi / coeff
            max_price_at_coc_threshold = (target_total_cost - capex_budget - reserves) / (1 + soft_cost_pct)

    candidates = {
        "YOC": max_price_at_yoc,
        "CapEx Multiple": max_price_at_capex_multiple,
        "CoC": max_price_at_coc_threshold,
    }
    valid_candidates = {k: v for k, v in candidates.items() if v is not None}
    boe_max_bid = min(valid_candidates.values()) if valid_candidates else None
    binding_constraint = min(valid_candidates, key=valid_candidates.get) if valid_candidates else None

    delta_vs_asking = boe_max_bid - asking_price if boe_max_bid is not None and asking_price is not None else None
    deposit_amount = asking_price * deposit_pct if asking_price is not None else None
    profit_potential = residual_sale - boe_max_bid if residual_sale is not None and boe_max_bid is not None else None

    output = BOEOutput(
        market_cap_rate=market_cap_rate,
        seller_noi_from_om=seller_noi,
        asking_cap_rate=asking_cap_rate,
        analysis_cap_rate=analysis_cap_rate,
        y1_exit_cap_rate=y1_exit_cap_rate,
        y1_dscr=y1_dscr,
        y1_capex_value_multiple=y1_capex_value_multiple,
        y1_expense_ratio=y1_expense_ratio,
        y1_cash_on_cash=y1_cash_on_cash,
        y1_yield_on_cost_unlevered=y1_yoc,
        residual_sale_at_exit_cap=residual_sale,
        profit_potential=profit_potential,
        max_price_at_yoc=max_price_at_yoc,
        max_price_at_capex_multiple=max_price_at_capex_multiple,
        max_price_at_coc_threshold=max_price_at_coc_threshold,
        max_bid_by_constraint=BOEConstraintMaxBids(
            max_price_at_yoc=max_price_at_yoc,
            max_price_at_capex_multiple=max_price_at_capex_multiple,
            max_price_at_coc_threshold=max_price_at_coc_threshold,
        ),
        boe_max_bid=boe_max_bid,
        delta_vs_asking=delta_vs_asking,
        deposit_amount=deposit_amount,
        binding_constraint=binding_constraint,
    )

    tests, decision = _evaluate_tests(output, interest_rate=interest_rate)
    return output, tests, decision


def serialize_output(output: BOEOutput) -> dict[str, Any]:
    return asdict(output)
