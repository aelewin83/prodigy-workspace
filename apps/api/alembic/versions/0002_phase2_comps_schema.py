"""phase2 comps schema

Revision ID: 0002_phase2
Revises: 0001_phase1
Create Date: 2026-02-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_phase2"
down_revision = "0001_phase1"
branch_labels = None
depends_on = None


comp_source_type = sa.Enum("public_connector", "private_file", "manual", name="compsourcetype")
listing_source_type = sa.Enum("public_web", "public_dataset", "private_file", "manual", name="listingsourcetype")
comp_run_status = sa.Enum("queued", "running", "succeeded", "failed", name="comprunstatus")
unit_type = sa.Enum("studio", "1BR", "2BR", "3BR", "4BR+", name="unittype")
variance_basis = sa.Enum("avg", "median", name="variancebasis")


def upgrade() -> None:
    comp_source_type.create(op.get_bind(), checkfirst=True)
    listing_source_type.create(op.get_bind(), checkfirst=True)
    comp_run_status.create(op.get_bind(), checkfirst=True)
    unit_type.create(op.get_bind(), checkfirst=True)
    variance_basis.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "comp_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", comp_source_type, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain_or_dataset", sa.String(length=255), nullable=True),
        sa.Column("allowlisted", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "comp_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("status", comp_run_status, nullable=False),
        sa.Column("source_mix", sa.JSON(), nullable=False),
        sa.Column("parse_report", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_comp_runs_workspace_id", "comp_runs", ["workspace_id"])
    op.create_index("ix_comp_runs_deal_id", "comp_runs", ["deal_id"])

    op.create_table(
        "comp_listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("comp_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("comp_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_type", unit_type, nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("beds", sa.Float(), nullable=True),
        sa.Column("baths", sa.Float(), nullable=True),
        sa.Column("rent", sa.Numeric(12, 2), nullable=True),
        sa.Column("gross_rent", sa.Numeric(12, 2), nullable=True),
        sa.Column("discount_premium", sa.Float(), nullable=True),
        sa.Column("date_observed", sa.Date(), nullable=True),
        sa.Column("link", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source_type", listing_source_type, nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False),
        sa.Column("flags", sa.JSON(), nullable=False),
    )
    op.create_index("ix_comp_listings_comp_run_id", "comp_listings", ["comp_run_id"])
    op.create_index("ix_comp_listings_dedupe_key", "comp_listings", ["dedupe_key"])

    op.create_table(
        "comp_rollups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("comp_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("comp_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_type", unit_type, nullable=False),
        sa.Column("avg_rent", sa.Float(), nullable=True),
        sa.Column("avg_gross_rent", sa.Float(), nullable=True),
        sa.Column("avg_discount_premium", sa.Float(), nullable=True),
        sa.Column("median_rent", sa.Float(), nullable=True),
        sa.Column("p25_rent", sa.Float(), nullable=True),
        sa.Column("p75_rent", sa.Float(), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False),
    )
    op.create_index("ix_comp_rollups_comp_run_id", "comp_rollups", ["comp_run_id"])

    op.create_table(
        "comp_subjects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_type", unit_type, nullable=False),
        sa.Column("subject_rent", sa.Float(), nullable=True),
        sa.Column("subject_gross_rent", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_comp_subjects_deal_id", "comp_subjects", ["deal_id"])

    op.create_table(
        "comp_subject_variance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("comp_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("comp_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_type", unit_type, nullable=False),
        sa.Column("variance_net", sa.Float(), nullable=True),
        sa.Column("variance_gross", sa.Float(), nullable=True),
        sa.Column("basis", variance_basis, nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_comp_subject_variance_comp_run_id", "comp_subject_variance", ["comp_run_id"])

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_key", sa.Text(), nullable=False),
        sa.Column("doc_type", sa.String(length=64), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_deal_id", "documents", ["deal_id"])

    op.create_table(
        "document_spans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("bbox", sa.JSON(), nullable=True),
        sa.Column("text_span", sa.Text(), nullable=True),
        sa.Column("table_cell", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_document_spans_document_id", "document_spans", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_document_spans_document_id", table_name="document_spans")
    op.drop_table("document_spans")

    op.drop_index("ix_documents_deal_id", table_name="documents")
    op.drop_table("documents")

    op.drop_index("ix_comp_subject_variance_comp_run_id", table_name="comp_subject_variance")
    op.drop_table("comp_subject_variance")

    op.drop_index("ix_comp_subjects_deal_id", table_name="comp_subjects")
    op.drop_table("comp_subjects")

    op.drop_index("ix_comp_rollups_comp_run_id", table_name="comp_rollups")
    op.drop_table("comp_rollups")

    op.drop_index("ix_comp_listings_dedupe_key", table_name="comp_listings")
    op.drop_index("ix_comp_listings_comp_run_id", table_name="comp_listings")
    op.drop_table("comp_listings")

    op.drop_index("ix_comp_runs_deal_id", table_name="comp_runs")
    op.drop_index("ix_comp_runs_workspace_id", table_name="comp_runs")
    op.drop_table("comp_runs")

    op.drop_table("comp_sources")

    variance_basis.drop(op.get_bind(), checkfirst=True)
    unit_type.drop(op.get_bind(), checkfirst=True)
    comp_run_status.drop(op.get_bind(), checkfirst=True)
    listing_source_type.drop(op.get_bind(), checkfirst=True)
    comp_source_type.drop(op.get_bind(), checkfirst=True)
