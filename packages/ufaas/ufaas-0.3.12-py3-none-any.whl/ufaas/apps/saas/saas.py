"""SaaS client implementation for UFaaS."""

import os
import uuid

from usso.session import AsyncUssoSession, UssoSession

from ..base_app import App, AsyncApp, AsyncResource, Resource
from .schemas import EnrollmentSchema, QuotaSchema, UsageSchema


class SaaS(App):
    """Synchronous SaaS application client."""

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
        """Initialize SaaS client.

        Args:
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO session to reuse
        """
        super().__init__(
            app_name="saas",
            ufaas_base_url=ufaas_base_url,
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )

    def initiate_resources(self, **kwargs: object) -> None:
        self.usages = Usage(client=self)
        self.enrollments = Enrollment(client=self)


class AsyncSaaS(AsyncApp):
    """Asynchronous SaaS application client."""

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
        """Initialize AsyncSaaS client.

        Args:
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO session to reuse
        """
        super().__init__(
            app_name="saas",
            ufaas_base_url=ufaas_base_url,
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )

    def initiate_resources(self, **kwargs: object) -> None:
        self.usages = AsyncUsage(client=self)
        self.enrollments = AsyncEnrollment(client=self)


class Usage(Resource):
    """Synchronous usage resource client."""

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
        """Initialize Usage resource client.

        Args:
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO session to reuse
        """
        super().__init__(
            app_name="saas",
            resource_name="usages",
            schema=UsageSchema,
            ufaas_base_url=ufaas_base_url,
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )

    def cancel_item(self, uid: str, **kwargs: object) -> UsageSchema:
        """Cancel a usage item.

        Args:
            uid: Unique identifier of the usage item
            **kwargs: Additional keyword arguments

        Returns:
            Updated usage schema
        """
        resp = self.post(f"{self.resource_url}{uid}/cancel", **kwargs)
        resp.raise_for_status()
        return self.retrieve_response_schema(**resp.json())


class AsyncUsage(AsyncResource):
    """Asynchronous usage resource client."""

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
        """Initialize AsyncUsage resource client.

        Args:
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO session to reuse
        """
        super().__init__(
            app_name="saas",
            resource_name="usages",
            schema=UsageSchema,
            ufaas_base_url=ufaas_base_url,
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )

    async def cancel_item(self, uid: str, **kwargs: object) -> UsageSchema:
        """Cancel a usage item asynchronously.

        Args:
            uid: Unique identifier of the usage item
            **kwargs: Additional keyword arguments

        Returns:
            Updated usage schema
        """
        resp = await self.post(f"{self.resource_url}{uid}/cancel", **kwargs)
        resp.raise_for_status()
        return self.retrieve_response_schema(**resp.json())


class Enrollment(Resource):
    """Synchronous enrollment resource client."""

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
        """Initialize Enrollment resource client.

        Args:
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO session to reuse
        """
        super().__init__(
            app_name="saas",
            resource_name="enrollments",
            schema=EnrollmentSchema,
            ufaas_base_url=ufaas_base_url,
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )

    def get_quotas(
        self,
        asset: str,
        user_id: uuid.UUID | None = None,
        variant: str | None = None,
        **kwargs: object,
    ) -> QuotaSchema:
        """Get quota information for a user and asset.

        Args:
            asset: Asset identifier
            user_id: User UUID (optional)
            variant: Variant identifier (optional)
            **kwargs: Additional keyword arguments

        Returns:
            Quota information
        """
        if isinstance(user_id, uuid.UUID):
            user_id = str(user_id)
        kwparams = kwargs.pop("params", {})
        params = {
            "asset": asset,
            "user_id": user_id,
            "variant": variant,
        } | kwparams
        resp = self.get(f"{self.resource_url}quotas", params=params, **kwargs)
        resp.raise_for_status()
        return QuotaSchema(**resp.json())


class AsyncEnrollment(AsyncResource):
    """Asynchronous enrollment resource client."""

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
        """Initialize AsyncEnrollment resource client.

        Args:
            ufaas_base_url: Base URL for UFaaS API
            usso_base_url: Base URL for USSO service
            api_key: API key for authentication
            usso_refresh_url: URL for token refresh
            refresh_token: Refresh token for authentication
            client: Existing USSO session to reuse
        """
        super().__init__(
            app_name="saas",
            resource_name="enrollments",
            schema=EnrollmentSchema,
            ufaas_base_url=ufaas_base_url,
            usso_base_url=usso_base_url,
            api_key=api_key,
            usso_refresh_url=usso_refresh_url,
            refresh_token=refresh_token,
            client=client,
        )

    async def get_quotas(
        self,
        asset: str,
        user_id: uuid.UUID | None = None,
        variant: str | None = None,
        **kwargs: object,
    ) -> QuotaSchema:
        """Get quota information asynchronously for a user and asset.

        Args:
            asset: Asset identifier
            user_id: User UUID (optional)
            variant: Variant identifier (optional)
            **kwargs: Additional keyword arguments

        Returns:
            Quota information
        """
        if isinstance(user_id, uuid.UUID):
            user_id = str(user_id)
        kwparams = kwargs.pop("params", {})
        params = {
            "asset": asset,
            "user_id": user_id,
            "variant": variant,
        } | kwparams
        resp = await self.get(
            f"{self.resource_url}quotas", params=params, **kwargs
        )
        resp.raise_for_status()
        return QuotaSchema(**resp.json())
