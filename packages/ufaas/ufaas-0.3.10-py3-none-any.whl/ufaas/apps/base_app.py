"""Base application classes for UFaaS."""

import os

from fastapi_mongo_base.schemas import PaginatedResponse
from usso.client import AsyncUssoClient, UssoClient


class App(UssoClient):
    """Base synchronous UFaaS application client."""

    def __init__(
        self,
        app_name: str = "saas",
        *,
        ufaas_base_url: str = os.getenv("UFAAS_URL"),
        usso_base_url: str | None = os.getenv("USSO_URL"),
        api_key: str | None = os.getenv("UFAAS_API_KEY"),
        usso_refresh_url: str | None = os.getenv("USSO_REFRESH_URL"),
        refresh_token: str | None = os.getenv("USSO_REFRESH_TOKEN"),
        client: UssoClient | None = None,
    ) -> None:
        """Initialize the App client.

        Args:
            app_name: Name of the application
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO client to reuse
        """
        super().__init__(
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )
        if not ufaas_base_url and client and hasattr(client, "ufaas_base_url"):
            ufaas_base_url = client.ufaas_base_url
        if ufaas_base_url.endswith("/"):
            ufaas_base_url = ufaas_base_url[:-1]
        if not ufaas_base_url.endswith("/api/v1/apps"):
            ufaas_base_url = f"{ufaas_base_url}/api/v1/apps"
        self.ufaas_base_url = ufaas_base_url
        self.app_name = app_name
        self.app_url = f"{ufaas_base_url}/{app_name}/"
        self.initiate_resources()

    def initiate_resources(self, **kwargs: object) -> None:
        pass


class AsyncApp(AsyncUssoClient):
    """Base asynchronous UFaaS application client."""

    def __init__(
        self,
        app_name: str = "saas",
        *,
        ufaas_base_url: str = os.getenv("UFAAS_URL"),
        usso_base_url: str | None = os.getenv("USSO_URL"),
        api_key: str | None = os.getenv("UFAAS_API_KEY"),
        usso_refresh_url: str | None = os.getenv("USSO_REFRESH_URL"),
        refresh_token: str | None = os.getenv("USSO_REFRESH_TOKEN"),
        client: AsyncUssoClient | None = None,
    ) -> None:
        """Initialize the AsyncApp client.

        Args:
            app_name: Name of the application
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO client to reuse
        """
        super().__init__(
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )
        if not ufaas_base_url and client and hasattr(client, "ufaas_base_url"):
            ufaas_base_url = client.ufaas_base_url
        if ufaas_base_url.endswith("/"):
            ufaas_base_url = ufaas_base_url[:-1]
        if not ufaas_base_url.endswith("/api/v1/apps"):
            ufaas_base_url = f"{ufaas_base_url}/api/v1/apps"
        self.ufaas_base_url = ufaas_base_url
        self.app_name = app_name
        self.app_url = f"{ufaas_base_url}/{app_name}/"
        self.initiate_resources()

    def initiate_resources(self, **kwargs: object) -> None:
        pass


class Resource(UssoClient):
    """Base synchronous UFaaS resource client."""

    def __init__(
        self,
        app_name: str = "saas",
        resource_name: str = "usages",
        schema: type = dict,
        *,
        ufaas_base_url: str = os.getenv("UFAAS_URL"),
        usso_base_url: str | None = os.getenv("USSO_URL"),
        api_key: str | None = os.getenv("UFAAS_API_KEY"),
        usso_refresh_url: str | None = os.getenv("USSO_REFRESH_URL"),
        refresh_token: str | None = os.getenv("USSO_REFRESH_TOKEN"),
        client: UssoClient | None = None,
    ) -> None:
        """Initialize the Resource client.

        Args:
            app_name: Name of the application
            resource_name: Name of the resource
            schema: Schema class for the resource
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO client to reuse
        """
        super().__init__(
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )
        if not ufaas_base_url and client and hasattr(client, "ufaas_base_url"):
            ufaas_base_url = client.ufaas_base_url
        if ufaas_base_url.endswith("/"):
            ufaas_base_url = ufaas_base_url[:-1]
        if not ufaas_base_url.endswith("/api/v1/apps"):
            ufaas_base_url = f"{ufaas_base_url}/api/v1/apps"
        self.ufaas_base_url = ufaas_base_url
        self.app_name = app_name
        self.resource_name = resource_name
        self.app_url = f"{ufaas_base_url}/{app_name}/"
        self.resource_url = f"{self.app_url}{resource_name}/"
        self._config_schemas(schema)

    def _config_schemas(self, schema: type = dict, **kwargs: object) -> None:
        self.schema = schema
        if isinstance(schema, dict):
            self.list_response_schema = dict
        else:
            self.list_response_schema = PaginatedResponse[schema]
        self.list_item_schema = schema
        self.retrieve_response_schema = schema
        self.create_response_schema = schema
        self.update_response_schema = schema
        self.delete_response_schema = schema

    def list_items(
        self, offset: int = 0, limit: int = 10, **kwargs: object
    ) -> object:
        kwparams = kwargs.pop("params", {})

        resp = self.get(
            self.resource_url,
            params={"offset": offset, "limit": limit} | kwparams,
            **kwargs,
        )
        resp.raise_for_status()
        return self.list_response_schema(**resp.json())

    def retrieve_item(self, uid: str, **kwargs: object) -> object:
        resp = self.get(f"{self.resource_url}/{uid}", **kwargs)
        resp.raise_for_status()
        return self.retrieve_response_schema(**resp.json())

    def create_item(self, obj: dict, **kwargs: object) -> object:
        resp = self.post(self.resource_url, json=obj, **kwargs)
        resp.raise_for_status()
        return self.create_response_schema(**resp.json())

    def update_item(self, uid: str, obj: dict, **kwargs: object) -> object:
        resp = self.patch(f"{self.resource_url}/{uid}", json=obj, **kwargs)
        resp.raise_for_status()
        return self.update_response_schema(**resp.json())

    def delete_item(self, uid: str, **kwargs: object) -> object:
        resp = self.delete(f"{self.resource_url}/{uid}", **kwargs)
        resp.raise_for_status()
        return self.delete_response_schema(**resp.json())


class AsyncResource(AsyncUssoClient):
    """Base asynchronous UFaaS resource client."""

    def __init__(
        self,
        app_name: str = "saas",
        resource_name: str = "usages",
        schema: type = dict,
        *,
        ufaas_base_url: str = os.getenv("UFAAS_URL"),
        usso_base_url: str | None = os.getenv("USSO_URL"),
        api_key: str | None = os.getenv("UFAAS_API_KEY"),
        usso_refresh_url: str | None = os.getenv("USSO_REFRESH_URL"),
        refresh_token: str | None = os.getenv("USSO_REFRESH_TOKEN"),
        client: AsyncUssoClient | None = None,
    ) -> None:
        """Initialize the AsyncResource client.

        Args:
            app_name: Name of the application
            resource_name: Name of the resource
            schema: Schema class for the resource
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO client to reuse
        """
        super().__init__(
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )
        if not ufaas_base_url and client and hasattr(client, "ufaas_base_url"):
            ufaas_base_url = client.ufaas_base_url
        if ufaas_base_url.endswith("/"):
            ufaas_base_url = ufaas_base_url[:-1]
        if not ufaas_base_url.endswith("/api/v1/apps"):
            ufaas_base_url = f"{ufaas_base_url}/api/v1/apps"
        self.ufaas_base_url = ufaas_base_url
        self.app_name = app_name
        self.resource_name = resource_name
        self.app_url = f"{ufaas_base_url}/{app_name}/"
        self.resource_url = f"{self.app_url}{resource_name}/"
        self._config_schemas(schema)

    def _config_schemas(self, schema: type = dict, **kwargs: object) -> None:
        self.schema = schema
        if isinstance(schema, dict):
            self.list_response_schema = dict
        else:
            self.list_response_schema = PaginatedResponse[schema]
        self.list_item_schema = schema
        self.retrieve_response_schema = schema
        self.create_response_schema = schema
        self.update_response_schema = schema
        self.delete_response_schema = schema

    async def list_items(
        self, offset: int = 0, limit: int = 10, **kwargs: object
    ) -> object:
        kwparams = kwargs.pop("params", {})
        resp = await self.get(
            self.resource_url,
            params={"offset": offset, "limit": limit} | kwparams,
            **kwargs,
        )
        resp.raise_for_status()
        return self.list_response_schema(**resp.json())

    async def retrieve_item(self, uid: str, **kwargs: object) -> object:
        resp = await self.get(f"{self.resource_url}/{uid}", **kwargs)
        resp.raise_for_status()
        return self.retrieve_response_schema(**resp.json())

    async def create_item(self, obj: dict, **kwargs: object) -> object:
        resp = await self.post(self.resource_url, json=obj, **kwargs)
        resp.raise_for_status()
        return self.create_response_schema(**resp.json())

    async def update_item(
        self, uid: str, obj: dict, **kwargs: object
    ) -> object:
        resp = await self.patch(
            f"{self.resource_url}/{uid}", json=obj, **kwargs
        )
        resp.raise_for_status()
        return self.update_response_schema(**resp.json())

    async def delete_item(self, uid: str, **kwargs: object) -> object:
        resp = await self.delete(f"{self.resource_url}/{uid}", **kwargs)
        resp.raise_for_status()
        return self.delete_response_schema(**resp.json())
