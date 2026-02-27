from types import SimpleNamespace

from app.api.boe import _compute_ic_score
from app.models.enums import TestClass, TestResult


def _test_result(test_class: TestClass, result: TestResult):
    return SimpleNamespace(test_class=test_class, result=result, test_key="x")


def test_ic_score_warn_penalty():
    run = SimpleNamespace(
        tests=[
            _test_result(TestClass.HARD, TestResult.PASS),
            _test_result(TestClass.HARD, TestResult.PASS),
            _test_result(TestClass.HARD, TestResult.PASS),
            _test_result(TestClass.SOFT, TestResult.WARN),
            _test_result(TestClass.SOFT, TestResult.WARN),
        ]
    )
    score, breakdown = _compute_ic_score(run)
    assert score == 90
    assert breakdown["warn_penalty"] == 10


def test_ic_score_hard_fail_penalty_and_clamp():
    run = SimpleNamespace(
        tests=[
            _test_result(TestClass.HARD, TestResult.FAIL),
            _test_result(TestClass.HARD, TestResult.FAIL),
            _test_result(TestClass.HARD, TestResult.FAIL),
            _test_result(TestClass.SOFT, TestResult.FAIL),
            _test_result(TestClass.SOFT, TestResult.WARN),
            _test_result(TestClass.SOFT, TestResult.WARN),
        ]
    )
    score, breakdown = _compute_ic_score(run)
    assert breakdown["hard_fail_penalty"] == 75
    assert breakdown["soft_fail_penalty"] == 10
    assert breakdown["warn_penalty"] == 10
    assert score == 5
