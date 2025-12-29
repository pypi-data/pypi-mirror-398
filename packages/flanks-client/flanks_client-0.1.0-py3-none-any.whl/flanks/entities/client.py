from flanks.base import BaseClient
from flanks.entities.models import Entity


class EntitiesClient(BaseClient):
    """Client for Entities API.

    See: https://docs.flanks.io/pages/flanks-apis/entities-api/
    """

    async def list(self) -> list[Entity]:
        """List all available banking entities.

        See: https://docs.flanks.io/pages/flanks-apis/entities-api/#get-entities
        """
        return await self.api_call(
            "/v0/bank/available",
            method="GET",
            model=list[Entity],
        )
