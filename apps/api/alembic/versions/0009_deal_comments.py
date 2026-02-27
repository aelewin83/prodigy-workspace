"""deal comments table

Revision ID: 0009_deal_comments
Revises: 0008_workspace_edition
Create Date: 2026-02-27
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0009_deal_comments"
down_revision = "0008_workspace_edition"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deal_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deal_comments_deal_id", "deal_comments", ["deal_id"])
    op.create_index("ix_deal_comments_created_by", "deal_comments", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_deal_comments_created_by", table_name="deal_comments")
    op.drop_index("ix_deal_comments_deal_id", table_name="deal_comments")
    op.drop_table("deal_comments")
