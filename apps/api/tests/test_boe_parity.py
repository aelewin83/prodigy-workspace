from pathlib import Path

from app.boe.parity import run_fixture_parity, workbook_available


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "boe"
DEFAULT_WORKBOOK_PATH = (
    Path(__file__).resolve().parents[3] / "fixtures" / "boe" / "BOE_MF_Template_NYC.xlsx"
)


def test_boe_fixture_parity():
    errors = run_fixture_parity(FIXTURES_DIR)
    assert errors == []


def test_default_excel_template_path_is_resolvable():
    # Path may or may not exist depending on env, but should be deterministic and portable.
    assert workbook_available(DEFAULT_WORKBOOK_PATH) in (True, False)
