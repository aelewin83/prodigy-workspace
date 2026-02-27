"""workspace edition toggle fields

Revision ID: 0008_workspace_edition
Revises: 0007_deal_outcomes
Create Date: 2026-02-27
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008_workspace_edition"
down_revision = "0007_deal_outcomes"
branch_labels = None
depends_on = None


workspace_edition = sa.Enum("SYNDICATOR", "FUND", name="workspaceedition")


def upgrade() -> None:
    workspace_edition.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "workspaces",
        sa.Column("edition", workspace_edition, nullable=False, server_default="SYNDICATOR"),
    )
    op.add_column("workspaces", sa.Column("edition_updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workspaces", sa.Column("edition_updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_workspaces_edition_updated_by_user_id", "workspaces", ["edition_updated_by_user_id"])
    op.create_foreign_key(
        "fk_workspaces_edition_updated_by_user_id_users",
        "workspaces",
        "users",
        ["edition_updated_by_user_id"],
        ["id"],
    )
    op.execute("UPDATE workspaces SET edition = 'SYNDICATOR' WHERE edition IS NULL")


def downgrade() -> None:
    op.drop_constraint("fk_workspaces_edition_updated_by_user_id_users", "workspaces", type_="foreignkey")
    op.drop_index("ix_workspaces_edition_updated_by_user_id", table_name="workspaces")
    op.drop_column("workspaces", "edition_updated_by_user_id")
    op.drop_column("workspaces", "edition_updated_at")
    op.drop_column("workspaces", "edition")
    workspace_edition.drop(op.get_bind(), checkfirst=True)
