"""gate state and audit fields

Revision ID: 0004_gate_state
Revises: 0003_boe_display
Create Date: 2026-02-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_gate_state"
down_revision = "0003_boe_display"
branch_labels = None
depends_on = None


deal_gate_state = sa.Enum("NO_RUN", "KILL", "ADVANCE", name="dealgatestate")


def upgrade() -> None:
    deal_gate_state.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "deals",
        sa.Column("current_gate_state", deal_gate_state, nullable=False, server_default="NO_RUN"),
    )
    op.add_column("deals", sa.Column("latest_boe_run_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_deals_latest_boe_run_id", "deals", ["latest_boe_run_id"])
    op.create_foreign_key(
        "fk_deals_latest_boe_run_id_boe_runs",
        "deals",
        "boe_runs",
        ["latest_boe_run_id"],
        ["id"],
    )

    op.add_column("audit_log", sa.Column("previous_state", sa.String(length=32), nullable=True))
    op.add_column("audit_log", sa.Column("new_state", sa.String(length=32), nullable=True))
    op.add_column("audit_log", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_audit_log_created_by", "audit_log", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_created_by", table_name="audit_log")
    op.drop_column("audit_log", "created_by")
    op.drop_column("audit_log", "new_state")
    op.drop_column("audit_log", "previous_state")

    op.drop_constraint("fk_deals_latest_boe_run_id_boe_runs", "deals", type_="foreignkey")
    op.drop_index("ix_deals_latest_boe_run_id", table_name="deals")
    op.drop_column("deals", "latest_boe_run_id")
    op.drop_column("deals", "current_gate_state")

    deal_gate_state.drop(op.get_bind(), checkfirst=True)
