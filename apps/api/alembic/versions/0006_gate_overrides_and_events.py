"""gate override fields and deal gate events

Revision ID: 0006_gate_overrides_events
Revises: 0005_deal_gate_status
Create Date: 2026-02-27
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_gate_overrides_events"
down_revision = "0005_deal_gate_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE dealstatus RENAME VALUE 'KILL' TO 'BLOCKED'")
    op.execute("ALTER TYPE dealstatus RENAME VALUE 'REVIEW' TO 'NEEDS_WORK'")
    op.execute("ALTER TYPE dealstatus ADD VALUE IF NOT EXISTS 'APPROVED'")

    deal_status = sa.Enum("BLOCKED", "NEEDS_WORK", "ADVANCE", "APPROVED", name="dealstatus")
    op.add_column(
        "deals",
        sa.Column("gate_status_computed", deal_status, nullable=False, server_default="NEEDS_WORK"),
    )
    op.add_column("deals", sa.Column("gate_override_status", deal_status, nullable=True))
    op.add_column("deals", sa.Column("gate_override_reason", sa.Text(), nullable=True))
    op.add_column("deals", sa.Column("gate_override_by", sa.String(length=255), nullable=True))
    op.add_column("deals", sa.Column("gate_override_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE deals SET gate_status_computed = gate_status WHERE gate_status_computed IS NULL")

    op.create_table(
        "deal_gate_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deal_gate_events_deal_id", "deal_gate_events", ["deal_id"])


def downgrade() -> None:
    op.drop_index("ix_deal_gate_events_deal_id", table_name="deal_gate_events")
    op.drop_table("deal_gate_events")

    op.drop_column("deals", "gate_override_at")
    op.drop_column("deals", "gate_override_by")
    op.drop_column("deals", "gate_override_reason")
    op.drop_column("deals", "gate_override_status")
    op.drop_column("deals", "gate_status_computed")

    op.execute("ALTER TYPE dealstatus RENAME VALUE 'BLOCKED' TO 'KILL'")
    op.execute("ALTER TYPE dealstatus RENAME VALUE 'NEEDS_WORK' TO 'REVIEW'")
