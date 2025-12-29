from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from fastapi_mongo_base.schemas import TenantUserEntitySchema
from fastapi_mongo_base.utils import bsontools, timezone
from pydantic import BaseModel, field_validator

from .enums import Currency


class HoldStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    RELEASED = "released"
    FAILED = "failed"


class WalletHoldSchema(TenantUserEntitySchema):
    wallet_id: str
    currency: str
    amount: Decimal
    expires_at: datetime | None = None
    status: HoldStatus = HoldStatus.ACTIVE
    description: str | None = None

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return bsontools.decimal_amount(value)

    def is_expired(self) -> bool:
        return (
            self.expires_at < datetime.now(timezone.tz)
            if self.expires_at
            else False
        )


class WalletHoldCreateSchema(BaseModel):
    currency: Currency
    amount: Decimal
    expires_at: datetime | None = None
    status: HoldStatus = HoldStatus.ACTIVE
    meta_data: dict | None = None
    description: str | None = None


class WalletHoldUpdateSchema(BaseModel):
    expires_at: datetime | None = None
    status: HoldStatus | None = None
    meta_data: dict | None = None
    description: str | None = None
