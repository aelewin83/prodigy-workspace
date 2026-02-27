from __future__ import annotations

from app.services.gate_summary import status_sort_key


def build_portfolio_summary_payload(summaries: list[dict]) -> dict:
    status_counts_map = {}
    binding_counts_map = {}
    override_count = 0
    ic_scores = []

    for summary in summaries:
        status = summary["effective_status"]
        status_counts_map[status] = status_counts_map.get(status, 0) + 1
        if summary["has_override"]:
            override_count += 1
        ic_scores.append(summary["ic_score"])
        binding = summary["explainability"]["binding_constraint"]
        if binding:
            binding_counts_map[binding] = binding_counts_map.get(binding, 0) + 1

    status_counts = [
        {"status": k, "count": status_counts_map[k]}
        for k in sorted(status_counts_map.keys(), key=status_sort_key)
    ]
    binding_constraint_distribution = [
        {"binding_constraint": k, "count": binding_counts_map[k]}
        for k in sorted(binding_counts_map.keys())
    ]
    deal_count = len(summaries)
    override_frequency_pct = (override_count / deal_count * 100.0) if deal_count else 0.0
    avg_ic_score = (sum(ic_scores) / len(ic_scores)) if ic_scores else None
    return {
        "portfolio_payload_version": "1.0",
        "deal_count": deal_count,
        "status_counts": status_counts,
        "avg_ic_score": avg_ic_score,
        "override_count": override_count,
        "override_frequency_pct": override_frequency_pct,
        "binding_constraint_distribution": binding_constraint_distribution,
    }


def build_risk_metrics_payload(records: list[tuple[dict, object | None]]) -> dict:
    def _rate(numerator: int, denominator: int) -> float | None:
        if denominator == 0:
            return None
        return numerator / denominator

    adv_num = 0
    adv_den = 0
    ov_num = 0
    ov_den = 0
    nov_num = 0
    nov_den = 0
    bins = [
        {"label": "0-39", "min": 0, "max": 39, "count": 0, "irr_sum": 0.0},
        {"label": "40-59", "min": 40, "max": 59, "count": 0, "irr_sum": 0.0},
        {"label": "60-79", "min": 60, "max": 79, "count": 0, "irr_sum": 0.0},
        {"label": "80-100", "min": 80, "max": 100, "count": 0, "irr_sum": 0.0},
    ]

    for summary, outcome in records:
        if outcome is None:
            continue
        underperformed = getattr(outcome, "underperformed_flag", None)
        realized_irr = getattr(outcome, "realized_irr", None)
        if summary["effective_status"] in {"ADVANCE", "APPROVED"} and underperformed is not None:
            adv_den += 1
            if underperformed:
                adv_num += 1

        if underperformed is not None:
            if summary["has_override"]:
                ov_den += 1
                if underperformed:
                    ov_num += 1
            else:
                nov_den += 1
                if underperformed:
                    nov_num += 1

        if realized_irr is not None:
            score = summary["ic_score"]
            for b in bins:
                if b["min"] <= score <= b["max"]:
                    b["count"] += 1
                    b["irr_sum"] += float(realized_irr)
                    break

    bin_rows = [
        {
            "bin": b["label"],
            "count": b["count"],
            "avg_realized_irr": (b["irr_sum"] / b["count"]) if b["count"] else None,
        }
        for b in bins
    ]
    return {
        "risk_payload_version": "1.0",
        "limitations": ["Metrics use current effective_status as a proxy for decision-time status."],
        "advance_underperformance_rate": {
            "numerator": adv_num,
            "denominator": adv_den,
            "rate": _rate(adv_num, adv_den),
        },
        "ic_score_vs_realized_irr_bins": bin_rows,
        "override_vs_outcome": {
            "override": {"numerator": ov_num, "denominator": ov_den, "rate": _rate(ov_num, ov_den)},
            "no_override": {"numerator": nov_num, "denominator": nov_den, "rate": _rate(nov_num, nov_den)},
        },
    }
