from app.api import full_underwriting


def test_underwriting_router_path_exists():
    paths = [route.path for route in full_underwriting.router.routes]
    assert "/full-underwriting/deals/{deal_id}" in paths
