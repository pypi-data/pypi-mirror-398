"""Accounting service client for UFaaS."""

import os
from datetime import datetime
from decimal import Decimal

import httpx
from usso.utils import agent

from .exceptions import NotFoundError
from .hold import (
    HoldStatus,
    WalletHoldCreateSchema,
    WalletHoldSchema,
    WalletHoldUpdateSchema,
)
from .proposal import Participant, ProposalCreateSchema, ProposalSchema
from .wallet import WalletDetailSchema


class AccountingClient(httpx.AsyncClient):
    """Async client for accounting service operations."""

    def __init__(self, tenant_id: str) -> None:
        """
        Initialize AccountingClient.

        Args:
            tenant_id: Tenant identifier for authentication
        """
        accounting_service_url = os.getenv(
            "ACCOUNTING_SERVICE_URL", "https://wallets.uln.me"
        )
        super().__init__(
            base_url=f"{accounting_service_url}/api/accounting/v1"
        )
        self.tenant_id = tenant_id

    async def get_token(self, scopes: str | list[str]) -> str:
        """
        Get authentication token for accounting service.

        Args:
            scopes: Permission scopes required

        Returns:
            JWT token string
        """
        if isinstance(scopes, str):
            scopes = [scopes]

        jwt = agent.generate_agent_jwt(
            scopes=scopes,
            aud="accounting",
            tenant_id=self.tenant_id,
        )
        token = await agent.get_agent_token_async(jwt)
        self.headers["Authorization"] = f"Bearer {token}"
        return token

    async def get_wallet(
        self,
        wallet_id: str | None = None,
        *,
        user_id: str | None = None,
        **kwargs: object,
    ) -> WalletDetailSchema:
        """
        Get wallet information.

        Args:
            wallet_id: Specific wallet ID (optional)
            user_id: User ID filter (optional)
            **kwargs: Additional keyword arguments

        Returns:
            Wallet detail schema

        Raises:
            NotFoundError: When wallet not found
        """
        await self.get_token("read:finance/accounting/wallet")

        params = kwargs.pop("params", {}) or {}
        params.update({"user_id": user_id})
        response = await self.get(
            f"/wallets/{wallet_id}" if wallet_id else "/wallets",
            params=params,
            **kwargs,
        )
        response.raise_for_status()
        if wallet_id:
            return WalletDetailSchema.model_validate(response.json())

        for item in response.json().get("items", []):
            if item.get("is_default"):
                return WalletDetailSchema.model_validate(item)

        raise NotFoundError("Wallet not found")

    async def get_holds(self, wallet_id: str) -> list[WalletHoldSchema]:
        """
        Get holds for a wallet.

        Args:
            wallet_id: Wallet identifier

        Returns:
            List of wallet hold schemas
        """
        await self.get_token("read:finance/accounting/hold")
        response = await self.get(f"/wallets/{wallet_id}/holds")
        response.raise_for_status()
        return [
            WalletHoldSchema.model_validate(item)
            for item in response.json().get("items", [])
        ]

    async def total_held_amount(
        self,
        wallet_id: str,
        currency: str,
        status: HoldStatus = HoldStatus.ACTIVE,
    ) -> float:
        """
        Calculate total held amount for a wallet.

        Args:
            wallet_id: Wallet identifier
            currency: Currency to filter by
            status: Hold status to filter by

        Returns:
            Total held amount
        """
        holds = await self.get_holds(wallet_id)
        return sum(
            hold.amount
            for hold in holds
            if hold.currency == currency and hold.status == status
        )

    async def create_hold(
        self,
        wallet_id: str,
        currency: str,
        amount: float,
        expires_at: datetime,
    ) -> WalletHoldSchema:
        """
        Create a wallet hold.

        Args:
            wallet_id: Wallet identifier
            currency: Currency code
            amount: Amount to hold
            expires_at: Expiration datetime

        Returns:
            Created wallet hold schema
        """
        await self.get_token("create:finance/accounting/hold")
        response = await self.post(
            f"/wallets/{wallet_id}/holds",
            json=WalletHoldCreateSchema(
                currency=currency,
                amount=amount,
                expires_at=expires_at,
                status=HoldStatus.ACTIVE,
            ).model_dump(mode="json"),
        )
        response.raise_for_status()
        return WalletHoldSchema.model_validate(response.json())

    async def release_hold(
        self, wallet_id: str, hold_id: str
    ) -> WalletHoldSchema:
        """
        Release a wallet hold.

        Args:
            wallet_id: Wallet identifier
            hold_id: Hold identifier to release

        Returns:
            Updated wallet hold schema
        """
        await self.get_token("update:finance/accounting/hold")
        response = await self.patch(
            f"/wallets/{wallet_id}/holds/{hold_id}",
            json=WalletHoldUpdateSchema(status=HoldStatus.RELEASED).model_dump(
                mode="json"
            ),
        )
        response.raise_for_status()
        return WalletHoldSchema.model_validate(response.json())

    async def create_proposal(
        self,
        *,
        from_wallet_id: str,
        to_wallet_id: str,
        currency: str,
        amount: float | Decimal,
        description: str | None = None,
        note: str | None = None,
        hold_id: str | None = None,
    ) -> ProposalSchema:
        """
        Create a transfer proposal.

        Args:
            from_wallet_id: Source wallet ID
            to_wallet_id: Destination wallet ID
            currency: Currency code
            amount: Transfer amount
            description: Optional description
            note: Optional note
            hold_id: Optional hold ID to use

        Returns:
            Created proposal schema
        """
        await self.get_token("create:finance/accounting/proposal")
        response = await self.post(
            "/proposals",
            json=ProposalCreateSchema(
                participants=[
                    Participant(
                        wallet_id=from_wallet_id,
                        amount=-amount,
                        hold_id=hold_id,
                    ),
                    Participant(wallet_id=to_wallet_id, amount=amount),
                ],
                amount=amount,
                currency=currency,
                description=description,
                note=note,
            ).model_dump(mode="json"),
        )
        response.raise_for_status()
        return ProposalSchema.model_validate(response.json())

    async def create_multi_recipient_proposal(
        self,
        *,
        from_wallet_id: str,
        to_wallet_ids: list[str],
        currency: str,
        amount: list[float | Decimal],
        description: str | None = None,
        note: str | None = None,
        hold_id: str | None = None,
    ) -> ProposalSchema:
        """
        Create a transfer proposal.

        Args:
            from_wallet_id: Source wallet ID
            to_wallet_ids: Destination wallet IDs
            currency: Currency code
            amount: Transfer amount
            description: Optional description
            note: Optional note
            hold_id: Optional hold ID to use

        Returns:
            Created proposal schema
        """
        await self.get_token("create:finance/accounting/proposal")
        total_amount = sum(amount)
        response = await self.post(
            "/proposals",
            json=ProposalCreateSchema(
                participants=[
                    Participant(
                        wallet_id=from_wallet_id,
                        amount=-total_amount,
                        hold_id=hold_id,
                    ),
                    *[
                        Participant(wallet_id=to_wallet_id, amount=amount)
                        for to_wallet_id in to_wallet_ids
                    ],
                ],
                amount=total_amount,
                currency=currency,
                description=description,
                note=note,
            ).model_dump(mode="json"),
        )
        response.raise_for_status()
        return ProposalSchema.model_validate(response.json())
