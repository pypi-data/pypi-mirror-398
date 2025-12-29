"""SaaS schemas for UFaaS application."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from fastapi_mongo_base.schemas import TenantScopedEntitySchema
from fastapi_mongo_base.utils import bsontools
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Bundle(BaseModel):
    asset: str
    quota: Decimal
    unit: str | None = None

    model_config = ConfigDict(allow_inf_nan=True)

    @field_validator("quota", mode="before")
    def validate_quota(self, value: Decimal) -> Decimal:
        return bsontools.decimal_amount(value)


class AcquisitionType(StrEnum):
    trial = "trial"
    # credit = "credit"
    purchased = "purchased"
    gifted = "gifted"
    # deferred = "deferred"
    promotion = "promotion"
    # subscription = "subscription"
    # on_demand = "on_demand"
    borrowed = "borrowed"
    # freemium = "freemium"
    postpaid = "postpaid"


class EnrollmentCreateSchema(BaseModel):
    user_id: uuid.UUID
    bundles: list[Bundle]

    price: Decimal = Decimal(0)
    invoice_id: str | None = None
    start_at: datetime = Field(default_factory=datetime.now)
    expire_at: datetime | None = None
    duration: int | None = Field(None, description="Duration in days")
    status: Literal["active", "inactive"] = "active"
    acquisition_type: AcquisitionType = AcquisitionType.purchased

    variant: str | None = None
    meta_data: dict | None = None

    due_date: datetime | None = None


class EnrollmentSchema(EnrollmentCreateSchema, TenantScopedEntitySchema):
    paid_at: datetime | None = None
    leftover_bundles: list[Bundle] = []


class QuotaSchema(BaseModel):
    asset: str
    quota: Decimal
    unit: str | None = None
    variant: str | None = None
    _quota: Decimal | None = None

    model_config = ConfigDict(allow_inf_nan=True)


class UsageCreateSchema(BaseModel):
    user_id: uuid.UUID
    enrollment_id: uuid.UUID | None = None
    asset: str
    amount: Decimal = Decimal(1)
    variant: str | None = None
    meta_data: dict | None = None


class UsageConsumption(BaseModel):
    enrollment_id: uuid.UUID
    amount: Decimal
    leftover_bundles: list[Bundle] = []


class UsageSchema(TenantScopedEntitySchema):
    # enrollment_id: uuid.UUID
    # asset: str
    # amount: Decimal

    consumptions: list[UsageConsumption]
    asset: str
    amount: Decimal
    variant: str | None = None
