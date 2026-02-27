from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"


def test_phase1_migration_contains_required_tables():
    migration = (MIGRATIONS_DIR / "0001_phase1_schema.py").read_text(encoding="utf-8")

    required_tables = [
        "users",
        "workspaces",
        "workspace_members",
        "deals",
        "boe_runs",
        "boe_test_results",
    ]

    for table in required_tables:
        assert f'"{table}"' in migration


def test_boe_runs_uses_json_inputs_outputs():
    migration = (MIGRATIONS_DIR / "0001_phase1_schema.py").read_text(encoding="utf-8")
    assert 'sa.Column("inputs", sa.JSON(), nullable=False)' in migration
    assert 'sa.Column("outputs", sa.JSON(), nullable=False)' in migration


def test_phase2_boe_display_fields_migration_exists():
    migration = (MIGRATIONS_DIR / "0003_boe_test_display_fields.py").read_text(encoding="utf-8")
    assert 'op.add_column("boe_test_results", sa.Column("threshold_display"' in migration
    assert 'op.add_column("boe_test_results", sa.Column("actual_display"' in migration


def test_gate_state_and_audit_fields_migration_exists():
    migration = (MIGRATIONS_DIR / "0004_gate_state_and_audit_fields.py").read_text(encoding="utf-8")
    assert "dealgatestate" in migration
    assert "current_gate_state" in migration
    assert "latest_boe_run_id" in migration
    assert "previous_state" in migration
    assert "new_state" in migration
    assert "created_by" in migration
