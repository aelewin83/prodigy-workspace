from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import TestClass, TestResult


class BOERunCreate(BaseModel):
    inputs: dict


class BOEDecisionSummaryOut(BaseModel):
    status: str
    hard_veto_ok: bool
    pass_count: int
    total_tests: int
    advance: bool
    failed_hard_tests: list[str]
    failed_soft_tests: list[str]
    warn_tests: list[str]
    pass_tests: list[str]
    na_tests: list[str]


class BOETestResultOut(BaseModel):
    test_key: str
    test_name: str
    test_class: TestClass
    threshold: float | None = None
    actual: float | None = None
    threshold_display: str | None = None
    actual_display: str | None = None
    result: TestResult
    note: str | None = None

    model_config = {"from_attributes": True}


class BOERunOut(BaseModel):
    id: UUID
    deal_id: UUID
    version: int
    inputs: dict
    outputs: dict
    decision: str
    binding_constraint: str | None
    hard_veto_ok: bool
    pass_count: int
    advance: bool
    decision_summary: BOEDecisionSummaryOut | None = None
    created_by: UUID
    created_at: datetime
    tests: list[BOETestResultOut]

    model_config = {"from_attributes": True}
