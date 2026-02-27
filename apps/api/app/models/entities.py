from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    CompRunStatus,
    CompSourceType,
    DealStatus,
    DealGateState,
    ListingSourceType,
    MemberRole,
    TestClass,
    TestResult,
    UnitType,
    VarianceBasis,
    WorkspaceEdition,
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    edition: Mapped[WorkspaceEdition] = mapped_column(
        Enum(WorkspaceEdition), nullable=False, default=WorkspaceEdition.SYNDICATOR
    )
    edition_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    edition_updated_by_user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), nullable=False, default=MemberRole.MEMBER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asking_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    current_gate_state: Mapped[DealGateState] = mapped_column(
        Enum(DealGateState), nullable=False, default=DealGateState.NO_RUN
    )
    latest_boe_run_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("boe_runs.id"), nullable=True, index=True
    )
    gate_status: Mapped[DealStatus] = mapped_column(
        Enum(DealStatus), nullable=False, default=DealStatus.NEEDS_WORK
    )
    gate_status_computed: Mapped[DealStatus] = mapped_column(
        Enum(DealStatus), nullable=False, default=DealStatus.NEEDS_WORK
    )
    gate_override_status: Mapped[DealStatus | None] = mapped_column(Enum(DealStatus), nullable=True)
    gate_override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    gate_override_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gate_override_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gate_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class BOERun(Base):
    __tablename__ = "boe_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    inputs: Mapped[dict] = mapped_column(JSON, nullable=False)
    outputs: Mapped[dict] = mapped_column(JSON, nullable=False)
    decision: Mapped[str] = mapped_column(String(24), nullable=False, default="KILL")
    binding_constraint: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hard_veto_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pass_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    advance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    tests: Mapped[list["BOETestResult"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class BOETestResult(Base):
    __tablename__ = "boe_test_results"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    boe_run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("boe_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    test_key: Mapped[str] = mapped_column(String(64), nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    test_class: Mapped[TestClass] = mapped_column(Enum(TestClass), nullable=False)
    threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_display: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actual_display: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result: Mapped[TestResult] = mapped_column(Enum(TestResult), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    run: Mapped[BOERun] = relationship(back_populates="tests")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DealGateEvent(Base):
    __tablename__ = "deal_gate_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DealOutcome(Base):
    __tablename__ = "deal_outcomes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    realized_irr: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_multiple: Mapped[float | None] = mapped_column(Float, nullable=True)
    underperformed_flag: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DealComment(Base):
    __tablename__ = "deal_comments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CompSource(Base):
    __tablename__ = "comp_sources"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type: Mapped[CompSourceType] = mapped_column(Enum(CompSourceType), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain_or_dataset: Mapped[str | None] = mapped_column(String(255), nullable=True)
    allowlisted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CompRun(Base):
    __tablename__ = "comp_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[CompRunStatus] = mapped_column(Enum(CompRunStatus), nullable=False, default=CompRunStatus.QUEUED)
    source_mix: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    parse_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CompListing(Base):
    __tablename__ = "comp_listings"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    comp_run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comp_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_type: Mapped[UnitType] = mapped_column(Enum(UnitType), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    beds: Mapped[float | None] = mapped_column(Float, nullable=True)
    baths: Mapped[float | None] = mapped_column(Float, nullable=True)
    rent: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    gross_rent: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    discount_premium: Mapped[float | None] = mapped_column(Float, nullable=True)
    date_observed: Mapped[date | None] = mapped_column(Date, nullable=True)
    link: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[ListingSourceType] = mapped_column(Enum(ListingSourceType), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    flags: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class CompRollup(Base):
    __tablename__ = "comp_rollups"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    comp_run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comp_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_type: Mapped[UnitType] = mapped_column(Enum(UnitType), nullable=False)
    avg_rent: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_gross_rent: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_discount_premium: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_rent: Mapped[float | None] = mapped_column(Float, nullable=True)
    p25_rent: Mapped[float | None] = mapped_column(Float, nullable=True)
    p75_rent: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CompSubject(Base):
    __tablename__ = "comp_subjects"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_type: Mapped[UnitType] = mapped_column(Enum(UnitType), nullable=False)
    subject_rent: Mapped[float | None] = mapped_column(Float, nullable=True)
    subject_gross_rent: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_by: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)


class CompSubjectVariance(Base):
    __tablename__ = "comp_subject_variance"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    comp_run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comp_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_type: Mapped[UnitType] = mapped_column(Enum(UnitType), nullable=False)
    variance_net: Mapped[float | None] = mapped_column(Float, nullable=True)
    variance_gross: Mapped[float | None] = mapped_column(Float, nullable=True)
    basis: Mapped[VarianceBasis] = mapped_column(Enum(VarianceBasis), nullable=False, default=VarianceBasis.AVG)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_key: Mapped[str] = mapped_column(Text, nullable=False)
    doc_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    uploaded_by: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DocumentSpan(Base):
    __tablename__ = "document_spans"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    text_span: Mapped[str | None] = mapped_column(Text, nullable=True)
    table_cell: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
