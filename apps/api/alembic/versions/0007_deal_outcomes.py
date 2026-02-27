"""deal outcomes risk memory table

Revision ID: 0007_deal_outcomes
Revises: 0006_gate_overrides_events
Create Date: 2026-02-27
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007_deal_outcomes"
down_revision = "0006_gate_overrides_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deal_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("realized_irr", sa.Float(), nullable=True),
        sa.Column("realized_multiple", sa.Float(), nullable=True),
        sa.Column("underperformed_flag", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deal_outcomes_deal_id", "deal_outcomes", ["deal_id"])


def downgrade() -> None:
    op.drop_index("ix_deal_outcomes_deal_id", table_name="deal_outcomes")
    op.drop_table("deal_outcomes")
