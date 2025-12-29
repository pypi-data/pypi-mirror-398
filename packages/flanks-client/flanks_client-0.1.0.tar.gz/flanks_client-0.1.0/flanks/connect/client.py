from collections.abc import AsyncIterator
from typing import Any

from flanks.base import BaseClient
from flanks.connect.models import Connector, Session, SessionConfig, SessionQuery
from flanks.pagination import PagedResponse


class ConnectClient(BaseClient):
    """Client for Connect API v2.

    See: https://docs.flanks.io/pages/flanks-apis/connect-api/v2/
    """

    async def list_sessions(
        self,
        query: SessionQuery | None = None,
    ) -> AsyncIterator[Session]:
        """Iterate over all sessions matching query.

        See: https://docs.flanks.io/pages/flanks-apis/connect-api/v2/#list-sessions
        """
        async for session in self.iterate_paged(
            "/connect/v2/sessions/list-sessions",
            {"query": query.model_dump(exclude_none=True) if query else {}},
            Session,
        ):
            yield session

    async def list_sessions_page(
        self,
        query: SessionQuery | None = None,
        page_token: str | None = None,
    ) -> PagedResponse[Session]:
        """Fetch a single page of sessions.

        See: https://docs.flanks.io/pages/flanks-apis/connect-api/v2/#list-sessions
        """
        return await self.api_call_paged(
            "/connect/v2/sessions/list-sessions",
            {
                "query": query.model_dump(exclude_none=True) if query else {},
                "page_token": page_token,
            },
            model=Session,
        )

    async def create_session(self, config: SessionConfig) -> Session:
        """Create a new connection session.

        See: https://docs.flanks.io/pages/flanks-apis/connect-api/v2/#create-session
        """
        response = await self.transport.api_call(
            "/connect/v2/sessions/create-session",
            {"configuration": config.model_dump()},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Session.model_validate(response["session"])

    async def list_connectors(
        self,
        connector_ids: list[str] | None = None,
    ) -> AsyncIterator[Connector]:
        """Iterate over available connectors.

        See: https://docs.flanks.io/pages/flanks-apis/connect-api/v2/#list-connectors
        """
        query: dict[str, Any] = {"connector_id_in": connector_ids} if connector_ids else {}
        async for connector in self.iterate_paged(
            "/connect/v2/connectors/list-connectors",
            {"query": query},
            Connector,
        ):
            yield connector
