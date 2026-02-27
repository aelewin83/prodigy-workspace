"""add viewer role to workspace members

Revision ID: 0010_workspace_member_viewer
Revises: 0009_deal_comments
Create Date: 2026-02-27
"""

from alembic import op


revision = "0010_workspace_member_viewer"
down_revision = "0009_deal_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE memberrole ADD VALUE IF NOT EXISTS 'VIEWER'")


def downgrade() -> None:
    # Enum value removal is intentionally omitted for Postgres safety.
    pass
