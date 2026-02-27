from app.services.boe import evaluate_boe


def test_service_wrapper_executes_engine():
    outputs, tests, decision = evaluate_boe(
        {
            "asking_price": 10_000_000,
            "interest_rate": 0.06,
            "ltc": 0.7,
            "capex_budget": 1_000_000,
            "seller_noi_from_om": 600_000,
            "gross_income": 1_000_000,
            "operating_expenses": 300_000,
            "y1_noi": 700_000,
            "y1_exit_cap_rate": 0.05,
        }
    )

    assert "boe_max_bid" in outputs
    assert len(tests) == 7
    assert decision.total_tests == 7
