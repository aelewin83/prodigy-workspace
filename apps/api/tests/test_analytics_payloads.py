from types import SimpleNamespace

from app.services.analytics import build_portfolio_summary_payload, build_risk_metrics_payload


def test_portfolio_summary_aggregates_mixed_statuses_and_overrides():
    summaries = [
        {"effective_status": "ADVANCE", "has_override": False, "ic_score": 90, "explainability": {"binding_constraint": "YOC"}},
        {"effective_status": "BLOCKED", "has_override": True, "ic_score": 55, "explainability": {"binding_constraint": "CoC"}},
        {"effective_status": "ADVANCE", "has_override": False, "ic_score": 80, "explainability": {"binding_constraint": "YOC"}},
    ]
    payload = build_portfolio_summary_payload(summaries)
    assert payload["portfolio_payload_version"] == "1.0"
    assert payload["deal_count"] == 3
    assert payload["override_count"] == 1
    assert payload["override_frequency_pct"] == (1 / 3) * 100.0
    assert payload["avg_ic_score"] == 75.0
    assert payload["status_counts"] == [
        {"status": "BLOCKED", "count": 1},
        {"status": "ADVANCE", "count": 2},
    ]


def test_risk_metrics_computation_is_deterministic():
    records = [
        (
            {"effective_status": "ADVANCE", "has_override": False, "ic_score": 85},
            SimpleNamespace(underperformed_flag=True, realized_irr=0.08),
        ),
        (
            {"effective_status": "APPROVED", "has_override": True, "ic_score": 60},
            SimpleNamespace(underperformed_flag=False, realized_irr=0.14),
        ),
        (
            {"effective_status": "BLOCKED", "has_override": False, "ic_score": 35},
            SimpleNamespace(underperformed_flag=True, realized_irr=0.02),
        ),
    ]
    payload = build_risk_metrics_payload(records)
    assert payload["risk_payload_version"] == "1.0"
    assert payload["advance_underperformance_rate"] == {"numerator": 1, "denominator": 2, "rate": 0.5}
    assert payload["override_vs_outcome"]["override"] == {"numerator": 0, "denominator": 1, "rate": 0.0}
    assert payload["override_vs_outcome"]["no_override"] == {"numerator": 2, "denominator": 2, "rate": 1.0}
    bins = {row["bin"]: row for row in payload["ic_score_vs_realized_irr_bins"]}
    assert bins["80-100"]["count"] == 1
    assert bins["80-100"]["avg_realized_irr"] == 0.08
    assert bins["60-79"]["count"] == 1
    assert bins["0-39"]["count"] == 1
