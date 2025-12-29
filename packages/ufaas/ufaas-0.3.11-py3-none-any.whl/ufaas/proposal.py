from decimal import Decimal
from enum import StrEnum

from fastapi_mongo_base.schemas import TenantUserEntitySchema
from fastapi_mongo_base.tasks import TaskMixin
from fastapi_mongo_base.utils import bsontools
from pydantic import BaseModel, field_validator


class ProposalStatus(StrEnum):
    draft = "draft"
    init = "init"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    error = "error"


class Participant(BaseModel):
    wallet_id: str
    amount: Decimal
    hold_id: str | None = None

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return bsontools.decimal_amount(value)


class ProposalSchema(TenantUserEntitySchema, TaskMixin):
    issuer_id: str
    amount: Decimal
    description: str | None = None
    note: str | None = None
    currency: str
    status: ProposalStatus = ProposalStatus.init
    participants: list[Participant]

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return bsontools.decimal_amount(value)


class ProposalCreateSchema(BaseModel):
    amount: Decimal
    description: str | None = None
    note: str | None = None
    currency: str
    status: ProposalStatus = ProposalStatus.init
    participants: list[Participant]
    meta_data: dict | None = None


class ProposalUpdateSchema(BaseModel):
    # status: str | None
    status: ProposalStatus | None = None
    description: str | None = None
    note: str | None = None
    meta_data: dict | None = None
