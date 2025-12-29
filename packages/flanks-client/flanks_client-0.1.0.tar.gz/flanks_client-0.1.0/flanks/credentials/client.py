from __future__ import annotations

import builtins

from flanks.base import BaseClient
from flanks.credentials.models import Credential, CredentialsListResponse, CredentialStatus


class CredentialsClient(BaseClient):
    """Client for Credentials API.

    See: https://docs.flanks.io/pages/flanks-apis/credentials-api/
    """

    async def get_status(self, credentials_token: str) -> CredentialStatus:
        """Get status of a credential.

        See: https://docs.flanks.io/pages/flanks-apis/credentials-api/#get-credentials-status
        """
        return await self.api_call(
            "/v0/bank/credentials/status",
            {"credentials_token": credentials_token},
            model=CredentialStatus,
        )

    async def list(self, page: int = 1) -> CredentialsListResponse:
        """List credentials with page-number pagination.

        Returns a response with items, page number, and total pages.

        See: https://docs.flanks.io/pages/flanks-apis/credentials-api/#list-credentials
        """
        return await self.api_call(
            "/v0/bank/credentials/list",
            {"page": page},
            model=CredentialsListResponse,
        )

    async def list_all(self) -> builtins.list[Credential]:
        """List all credentials across all pages.

        See: https://docs.flanks.io/pages/flanks-apis/credentials-api/#list-credentials
        """
        all_credentials: builtins.list[Credential] = []
        page = 1
        while True:
            response = await self.list(page)
            all_credentials.extend(response.items)
            if page >= response.pages:
                break
            page += 1
        return all_credentials

    async def force_sca(self, credentials_token: str) -> str:
        """Force SCA (Strong Customer Authentication) refresh.

        Returns the sca_token to use with Connect API.

        See: https://docs.flanks.io/pages/flanks-apis/credentials-api/#force-sca-reset-or-transactions-token
        """
        response = await self.transport.api_call(
            "/v0/bank/credentials/status",
            {"credentials_token": credentials_token, "force": "sca"},
            method="PUT",
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return str(response["sca_token"])

    async def force_reset(self, credentials_token: str) -> str:
        """Force credential reset.

        Returns the reset_token to use with Connect API.

        See: https://docs.flanks.io/pages/flanks-apis/credentials-api/#force-sca-reset-or-transactions-token
        """
        response = await self.transport.api_call(
            "/v0/bank/credentials/status",
            {"credentials_token": credentials_token, "force": "reset"},
            method="PUT",
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return str(response["reset_token"])

    async def force_transaction(self, credentials_token: str) -> str:
        """Force transaction data refresh.

        Returns the transaction_token to use with Connect API.

        See: https://docs.flanks.io/pages/flanks-apis/credentials-api/#force-sca-reset-or-transactions-token
        """
        response = await self.transport.api_call(
            "/v0/bank/credentials/status",
            {"credentials_token": credentials_token, "force": "transaction"},
            method="PUT",
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return str(response["transaction_token"])

    async def delete(self, credentials_token: str) -> None:
        """Delete a credential.

        See: https://docs.flanks.io/pages/flanks-apis/credentials-api/#delete-credentials
        """
        await self.transport.api_call(
            "/v0/bank/credentials",
            {"credentials_token": credentials_token},
            method="DELETE",
        )
