from __future__ import annotations

import os
from pathlib import Path

from app.boe.parity import run_fixture_parity, workbook_available


def resolve_workbook_path() -> Path:
    env_path = os.getenv("BOE_WORKBOOK_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return (
        Path(__file__).resolve().parents[3]
        / "fixtures"
        / "boe"
        / "BOE_MF_Template_NYC.xlsx"
    )


def ensure_workbook_exists(path: Path) -> None:
    if workbook_available(path):
        try:
            from openpyxl import load_workbook

            load_workbook(path, read_only=True, data_only=True)
            return
        except ModuleNotFoundError as exc:  # pragma: no cover - env setup issue
            raise SystemExit(
                "Missing dependency 'openpyxl'. Install API dev dependencies before running parity "
                "(for example: `make install-api-dev`)."
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive failure path for local setup issues
            raise SystemExit(f"Workbook exists but could not be opened: {path}\nError: {exc}") from exc

    msg = "\n".join(
        [
            f"Missing BOE workbook at: {path}",
            "Set BOE_WORKBOOK_PATH to your workbook location, or place the file at:",
            "fixtures/boe/BOE_MF_Template_NYC.xlsx",
            "See fixtures/boe/README.md for setup instructions.",
        ]
    )
    raise SystemExit(msg)


if __name__ == "__main__":
    workbook = resolve_workbook_path()
    ensure_workbook_exists(workbook)

    fixtures = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "boe"
    errors = run_fixture_parity(fixtures)
    if errors:
        for err in errors:
            print(err)
        raise SystemExit(1)
    print(f"BOE parity checks passed for fixtures in {fixtures}")
    print(f"Workbook path validated: {workbook}")
