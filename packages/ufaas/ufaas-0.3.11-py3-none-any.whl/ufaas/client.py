"""Main UFaaS client implementation."""

import os
from urllib.parse import urlparse

from usso.client import AsyncUssoClient, UssoClient

from .apps.basket import AsyncBasket, Basket
from .apps.saas import AsyncSaaS, SaaS


class UFaaS(UssoClient):
    def __init__(
        self,
        *,
        ufaas_base_url: str = os.getenv("UFAAS_URL"),
        usso_base_url: str | None = os.getenv("USSO_URL"),
        api_key: str | None = os.getenv("UFAAS_API_KEY"),
        usso_refresh_url: str | None = os.getenv("USSO_REFRESH_URL"),
        refresh_token: str | None = os.getenv("USSO_REFRESH_TOKEN"),
        client: UssoClient | None = None,
    ) -> None:
        if usso_base_url is None:
            # calculate sso_url using ufiles_url
            # for example: media.pixiee.io/v1/f -> sso.pixiee.io
            # for example: media.ufaas.io/v1/f -> sso.ufaas.io
            # for example: media.pixy.ir/api/v1/f -> sso.pixy.ir
            # for example: storage.pixy.ir/api/v1/f -> sso.pixy.ir
            parsed_url = urlparse(ufaas_base_url)
            netloc = parsed_url.netloc
            netloc_parts = netloc.split(".")
            if len(netloc_parts) > 2:
                netloc_parts[0] = "sso"
            else:
                netloc_parts = ["sso", netloc]
            netloc = ".".join(netloc_parts)
            usso_base_url = f"https://{netloc}"

        super().__init__(
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )
        if not ufaas_base_url and client and hasattr(client, "ufaas_base_url"):
            ufaas_base_url = client.ufaas_base_url
        if not ufaas_base_url:
            raise ValueError("UFAAS_URL is required")
        if ufaas_base_url.endswith("/"):
            ufaas_base_url = ufaas_base_url[:-1]
        self.ufaas_base_url = ufaas_base_url
        self.headers.update({"accept-encoding": "identity"})

        self.initiate_apps()

    def initiate_apps(self) -> None:
        self.saas = SaaS(client=self)
        self.basket = Basket(client=self)


class AsyncUFaaS(AsyncUssoClient):
    def __init__(
        self,
        *,
        ufaas_base_url: str = os.getenv("UFAAS_URL"),
        usso_base_url: str | None = os.getenv("USSO_URL"),
        api_key: str | None = os.getenv("UFILES_API_KEY"),
        usso_refresh_url: str | None = os.getenv("USSO_REFRESH_URL"),
        refresh_token: str | None = os.getenv("USSO_REFRESH_TOKEN"),
        client: AsyncUssoClient | None = None,
    ) -> None:
        if usso_base_url is None:
            # calculate sso_url using ufiles_url
            # for example: media.pixiee.io/v1/f -> sso.pixiee.io
            # for example: media.ufaas.io/v1/f -> sso.ufaas.io
            # for example: media.pixy.ir/api/v1/f -> sso.pixy.ir
            # for example: storage.pixy.ir/api/v1/f -> sso.pixy.ir
            parsed_url = urlparse(ufaas_base_url)
            netloc = parsed_url.netloc
            netloc_parts = netloc.split(".")
            if len(netloc_parts) > 2:
                netloc_parts[0] = "sso"
            else:
                netloc_parts = ["sso", netloc]
            netloc = ".".join(netloc_parts)
            usso_base_url = f"https://{netloc}"

        super().__init__(
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )
        if not ufaas_base_url and client and hasattr(client, "ufaas_base_url"):
            ufaas_base_url = client.ufaas_base_url
        if not ufaas_base_url:
            raise ValueError("UFAAS_URL is required")
        if ufaas_base_url.endswith("/"):
            ufaas_base_url = ufaas_base_url[:-1]
        self.ufaas_base_url = ufaas_base_url
        self.headers.update({"accept-encoding": "identity"})
        self.initiate_apps()

    def initiate_apps(self) -> None:
        self.saas = AsyncSaaS(client=self)
        self.basket = AsyncBasket(client=self)
