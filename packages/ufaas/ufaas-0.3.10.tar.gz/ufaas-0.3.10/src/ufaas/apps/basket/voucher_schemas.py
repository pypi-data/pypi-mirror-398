"""Voucher schemas for basket application."""

import secrets
import string
import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from fastapi_mongo_base.schemas import TenantScopedEntitySchema
from pydantic import BaseModel, Field

from ufaas.schemas import Currency


def generate_human_readable_code(length: int = 6) -> str:
    human_readable_chars = list(
        set(string.ascii_letters + string.digits) - set("oO0Il1")
    )

    return "".join(secrets.choice(human_readable_chars) for _ in range(length))


class VoucherStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    USED = "used"


class VoucherCreateSchema(BaseModel):
    code: str = Field(default_factory=lambda: generate_human_readable_code(10))
    status: VoucherStatus = VoucherStatus.ACTIVE
    rate: Decimal = Field(
        ...,
        gt=0,
        le=100,
        description="Discount proportion percentage (e.g., 10% = 10)",
    )
    cap: Decimal | None = Field(
        default=None, gt=0, description="Maximum discount amount"
    )
    currency: Currency = Currency.IRR
    expired_at: datetime | None = None
    max_uses: int | None = None
    user_id: uuid.UUID | None = None
    limited_products: list[uuid.UUID] | None = None
    meta_data: dict | None = None

    def calculate_discount(self, amount: Decimal) -> Decimal:
        discount_value = amount * self.rate / 100
        discount_value = (
            discount_value
            if self.cap is None
            else min(discount_value, self.cap)
        )
        return discount_value


class VoucherUpdateSchema(BaseModel):
    status: VoucherStatus | None = None
    expired_at: datetime | None = None
    limit: int | None = None


class VoucherSchema(VoucherCreateSchema, TenantScopedEntitySchema):
    redeemed: int
