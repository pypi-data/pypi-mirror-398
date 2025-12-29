"""Basket client implementation for UFaaS."""

import os

from usso.session import AsyncUssoSession, UssoSession

from ..base_app import App, AsyncApp, AsyncResource, Resource
from .basket_schemas import BasketDataSchema
from .voucher_schemas import VoucherSchema


class Basket(App):
    """Synchronous basket application client."""

    def __init__(
        self,
        *,
        ufaas_base_url: str = os.getenv("UFAAS_URL"),
        usso_base_url: str | None = os.getenv("USSO_URL"),
        api_key: str | None = os.getenv("UFAAS_API_KEY"),
        usso_refresh_url: str | None = os.getenv("USSO_REFRESH_URL"),
        refresh_token: str | None = os.getenv("USSO_REFRESH_TOKEN"),
        client: UssoSession | None = None,
    ) -> None:
        """Initialize the Basket client.

        Args:
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO session to reuse
        """
        super().__init__(
            app_name="basket",
            ufaas_base_url=ufaas_base_url,
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )

    def initiate_resources(self, **kwargs: object) -> None:
        self.baskets = BasketData(client=self)
        self.vouchers = Voucher(client=self)


class AsyncBasket(AsyncApp):
    """Asynchronous basket application client."""

    def __init__(
        self,
        *,
        ufaas_base_url: str = os.getenv("UFAAS_URL"),
        usso_base_url: str | None = os.getenv("USSO_URL"),
        api_key: str | None = os.getenv("UFAAS_API_KEY"),
        usso_refresh_url: str | None = os.getenv("USSO_REFRESH_URL"),
        refresh_token: str | None = os.getenv("USSO_REFRESH_TOKEN"),
        client: AsyncUssoSession | None = None,
    ) -> None:
        """Initialize the AsyncBasket client.

        Args:
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO session to reuse
        """
        super().__init__(
            app_name="basket",
            ufaas_base_url=ufaas_base_url,
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )

    def initiate_resources(self, **kwargs: object) -> None:
        self.vouchers = AsyncVoucher(client=self)


class BasketData(Resource):
    """Synchronous basket data resource client."""

    def __init__(
        self,
        *,
        ufaas_base_url: str = os.getenv("UFAAS_URL"),
        usso_base_url: str | None = os.getenv("USSO_URL"),
        api_key: str | None = os.getenv("UFAAS_API_KEY"),
        usso_refresh_url: str | None = os.getenv("USSO_REFRESH_URL"),
        refresh_token: str | None = os.getenv("USSO_REFRESH_TOKEN"),
        client: UssoSession | None = None,
    ) -> None:
        """Initialize the BasketData resource client.

        Args:
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO session to reuse
        """
        super().__init__(
            app_name="basket",
            resource_name="baskets",
            schema=BasketDataSchema,
            ufaas_base_url=ufaas_base_url,
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )


class AsyncBasketData(AsyncResource):
    """Asynchronous basket data resource client."""

    def __init__(
        self,
        *,
        ufaas_base_url: str = os.getenv("UFAAS_URL"),
        usso_base_url: str | None = os.getenv("USSO_URL"),
        api_key: str | None = os.getenv("UFAAS_API_KEY"),
        usso_refresh_url: str | None = os.getenv("USSO_REFRESH_URL"),
        refresh_token: str | None = os.getenv("USSO_REFRESH_TOKEN"),
        client: AsyncUssoSession | None = None,
    ) -> None:
        """Initialize the AsyncBasketData resource client.

        Args:
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO session to reuse
        """
        super().__init__(
            app_name="basket",
            resource_name="baskets",
            schema=BasketDataSchema,
            ufaas_base_url=ufaas_base_url,
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )


class Voucher(Resource):
    """Synchronous voucher resource client."""

    def __init__(
        self,
        *,
        ufaas_base_url: str = os.getenv("UFAAS_URL"),
        usso_base_url: str | None = os.getenv("USSO_URL"),
        api_key: str | None = os.getenv("UFAAS_API_KEY"),
        usso_refresh_url: str | None = os.getenv("USSO_REFRESH_URL"),
        refresh_token: str | None = os.getenv("USSO_REFRESH_TOKEN"),
        client: UssoSession | None = None,
    ) -> None:
        """Initialize Voucher resource client.

        Args:
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO session to reuse
        """
        super().__init__(
            app_name="basket",
            resource_name="vouchers",
            schema=VoucherSchema,
            ufaas_base_url=ufaas_base_url,
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )


class AsyncVoucher(AsyncResource):
    """Asynchronous voucher resource client."""

    def __init__(
        self,
        *,
        ufaas_base_url: str = os.getenv("UFAAS_URL"),
        usso_base_url: str | None = os.getenv("USSO_URL"),
        api_key: str | None = os.getenv("UFAAS_API_KEY"),
        usso_refresh_url: str | None = os.getenv("USSO_REFRESH_URL"),
        refresh_token: str | None = os.getenv("USSO_REFRESH_TOKEN"),
        client: AsyncUssoSession | None = None,
    ) -> None:
        """Initialize AsyncVoucher resource client.

        Args:
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO session to reuse
        """
        super().__init__(
            app_name="basket",
            resource_name="vouchers",
            schema=VoucherSchema,
            ufaas_base_url=ufaas_base_url,
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )
