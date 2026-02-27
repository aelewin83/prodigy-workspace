"""boe test display fields

Revision ID: 0003_boe_display
Revises: 0002_phase2
Create Date: 2026-02-26
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_boe_display"
down_revision = "0002_phase2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("boe_test_results", sa.Column("threshold_display", sa.String(length=255), nullable=True))
    op.add_column("boe_test_results", sa.Column("actual_display", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("boe_test_results", "actual_display")
    op.drop_column("boe_test_results", "threshold_display")
