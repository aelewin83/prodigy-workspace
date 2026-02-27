"""deal gate status columns

Revision ID: 0005_deal_gate_status
Revises: 0004_gate_state
Create Date: 2026-02-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_deal_gate_status"
down_revision = "0004_gate_state"
branch_labels = None
depends_on = None


deal_status = sa.Enum("KILL", "REVIEW", "ADVANCE", name="dealstatus")


def upgrade() -> None:
    deal_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "deals",
        sa.Column("gate_status", deal_status, nullable=False, server_default="REVIEW"),
    )
    op.add_column("deals", sa.Column("gate_updated_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE deals SET gate_status = 'REVIEW' WHERE gate_status IS NULL")
    op.execute("UPDATE deals SET gate_updated_at = NOW() WHERE gate_updated_at IS NULL")


def downgrade() -> None:
    op.drop_column("deals", "gate_updated_at")
    op.drop_column("deals", "gate_status")

    deal_status.drop(op.get_bind(), checkfirst=True)
