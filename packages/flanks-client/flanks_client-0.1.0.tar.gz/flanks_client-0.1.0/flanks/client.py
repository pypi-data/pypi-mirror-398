import os
from datetime import date
from functools import cached_property

from flanks.aggregation_v1.client import AggregationV1Client
from flanks.aggregation_v2.client import AggregationV2Client
from flanks.connect.client import ConnectClient
from flanks.connection import FlanksConnection
from flanks.credentials.client import CredentialsClient
from flanks.entities.client import EntitiesClient
from flanks.exceptions import FlanksConfigError
from flanks.links.client import LinksClient
from flanks.report.client import ReportClient


class FlanksClient:
    """Flanks API client with sub-clients for each API domain."""

    _client_id: str
    _client_secret: str

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        *,
        base_url: str = "https://api.flanks.io",
        timeout: float = 60.0,
        retries: int = 1,
        retry_backoff: float = 1.0,
        version: str = "2026-01-01",
    ) -> None:
        resolved_client_id = client_id or os.environ.get("FLANKS_CLIENT_ID")
        resolved_client_secret = client_secret or os.environ.get("FLANKS_CLIENT_SECRET")

        if not resolved_client_id or not resolved_client_secret:
            raise FlanksConfigError(
                "Missing credentials. Provide client_id and client_secret "
                "or set FLANKS_CLIENT_ID and FLANKS_CLIENT_SECRET environment variables."
            )

        self._client_id = resolved_client_id
        self._client_secret = resolved_client_secret

        self._base_url = base_url
        self._timeout = timeout
        self._retries = retries
        self._retry_backoff = retry_backoff
        self._version = date.fromisoformat(version)

    @cached_property
    def transport(self) -> FlanksConnection:
        """Access underlying transport for raw API calls."""
        return FlanksConnection(
            client_id=self._client_id,
            client_secret=self._client_secret,
            base_url=self._base_url,
            timeout=self._timeout,
            retries=self._retries,
            retry_backoff=self._retry_backoff,
        )

    @cached_property
    def entities(self) -> EntitiesClient:
        """Client for Entities API."""
        return EntitiesClient(self.transport)

    @cached_property
    def connect(self) -> ConnectClient:
        """Client for Connect API v2."""
        return ConnectClient(self.transport)

    @cached_property
    def credentials(self) -> CredentialsClient:
        """Client for Credentials API."""
        return CredentialsClient(self.transport)

    @cached_property
    def aggregation_v1(self) -> AggregationV1Client:
        """Client for Aggregation API v1."""
        return AggregationV1Client(self.transport)

    @cached_property
    def aggregation_v2(self) -> AggregationV2Client:
        """Client for Aggregation API v2."""
        return AggregationV2Client(self.transport)

    @property
    def aggregation(self) -> AggregationV1Client | AggregationV2Client:
        """Version-based aggregation client (v2 for versions >= 2026-01-01, v1 otherwise)."""
        if self._version >= date(2026, 1, 1):
            return self.aggregation_v2
        return self.aggregation_v1

    @cached_property
    def links(self) -> LinksClient:
        """Client for Links API (legacy)."""
        return LinksClient(self.transport)

    @cached_property
    def report(self) -> ReportClient:
        """Client for Report API (beta)."""
        return ReportClient(self.transport)

    async def close(self) -> None:
        """Close the client and release resources."""
        if "transport" in self.__dict__:
            await self.transport.close()

    async def __aenter__(self) -> "FlanksClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        await self.close()
