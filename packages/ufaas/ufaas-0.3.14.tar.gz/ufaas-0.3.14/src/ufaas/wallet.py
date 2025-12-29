"""Wallet schemas for UFaaS."""

from decimal import Decimal
from enum import StrEnum

from fastapi_mongo_base.schemas import TenantUserEntitySchema
from pydantic import BaseModel, Field, model_validator

from .enums import Currency


class WalletOwnerType(StrEnum):
    """Wallet owner type."""

    user = "user"
    tenant = "tenant"
    app = "app"
    system = "system"
    broker = "broker"


class WalletPurpose(StrEnum):
    """Wallet purpose."""

    regular = "regular"
    treasury = "treasury"
    test = "test"
    fees = "fees"

    # settlement = "settlement"
    # fee_collector = "fee_collector"
    # income_wallet = "income_wallet"
    # bonus_wallet = "bonus_wallet"
    # reserve = "reserve"


class WalletBalanceType(StrEnum):
    """Wallet balance type."""

    positive = "positive"
    negative = "negative"


class WalletStatus(StrEnum):
    """Wallet status."""

    active = "active"
    inactive = "inactive"
    pending = "pending"
    blocked = "blocked"
    deleted = "deleted"


class WalletSchema(TenantUserEntitySchema):
    """Wallet schema."""

    wallet_purpose: WalletPurpose = WalletPurpose.regular
    owner_type: WalletOwnerType = WalletOwnerType.user
    balance_type: WalletBalanceType = WalletBalanceType.positive
    status: WalletStatus = WalletStatus.active

    main_currency: Currency = Currency.main_currency()
    is_default: bool = True


class BalanceSchema(BaseModel):
    """Balance schema."""

    currency: Currency
    total: Decimal
    held: Decimal
    available: Decimal

    @model_validator(mode="before")
    @classmethod
    def validate_balance(cls, values: dict[str, object]) -> dict[str, object]:
        """Validate balance."""

        total = Decimal(values.get("total"))
        held = Decimal(values.get("held"))
        available = Decimal(values.get("available"))
        set_fields = [x is not None for x in (total, held, available)]
        num_set = sum(set_fields)

        if num_set < 2:
            raise ValueError(
                "At least two of 'total', 'held', and 'available' must be set."
            )

        if num_set == 2:
            if total is None:
                values["total"] = held + available
            elif held is None:
                values["held"] = total - available
            elif available is None:
                values["available"] = total - held
        elif num_set == 3 and (total != held + available):
            raise ValueError(
                f"'total' ({total}) must equal "
                f"'held' ({held}) + 'available' ({available})"
            )
        return values


class WalletDetailSchema(WalletSchema):
    """Wallet detail schema."""

    balance: dict[str, BalanceSchema] = Field(default_factory=dict)


class WalletCreateSchema(BaseModel):
    """Wallet create schema."""

    user_id: str | None = None
    meta_data: dict | None = None

    wallet_purpose: WalletPurpose = WalletPurpose.regular
    owner_type: WalletOwnerType = WalletOwnerType.user
    balance_type: WalletBalanceType = WalletBalanceType.positive
    status: WalletStatus = WalletStatus.active

    main_currency: Currency = Currency.main_currency()
    is_default: bool = False


class WalletUpdateSchema(BaseModel):
    """Wallet update schema."""

    meta_data: dict | None = None
    is_default: bool | None = None
