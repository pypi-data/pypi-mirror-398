from __future__ import annotations

import builtins

from flanks.base import BaseClient
from flanks.links.models import Link, LinkCode, LinkCodeExchangeResult


class LinksClient(BaseClient):
    """Client for Links API (legacy).

    See: https://docs.flanks.io/pages/flanks-apis/links-api/
    """

    async def list(self) -> builtins.list[Link]:
        """List all links.

        See: https://docs.flanks.io/pages/flanks-apis/links-api/#list-links
        """
        return await self.api_call(
            "/v0/links/list-links",
            model=list[Link],
        )

    async def create(
        self,
        redirect_uri: str,
        *,
        name: str | None = None,
        company_name: str | None = None,
        terms_and_conditions_url: str | None = None,
        privacy_policy_url: str | None = None,
    ) -> Link:
        """Create a new link.

        See: https://docs.flanks.io/pages/flanks-apis/links-api/#create-link
        """
        body: dict[str, str] = {"redirect_uri": redirect_uri}
        if name is not None:
            body["name"] = name
        if company_name is not None:
            body["company_name"] = company_name
        if terms_and_conditions_url is not None:
            body["terms_and_conditions_url"] = terms_and_conditions_url
        if privacy_policy_url is not None:
            body["privacy_policy_url"] = privacy_policy_url

        return await self.api_call(
            "/v0/links/create-link",
            body,
            model=Link,
        )

    async def edit(
        self,
        token: str,
        *,
        redirect_uri: str | None = None,
        name: str | None = None,
        company_name: str | None = None,
        terms_and_conditions_url: str | None = None,
        privacy_policy_url: str | None = None,
    ) -> Link:
        """Edit an existing link. Pass None to remove an attribute.

        See: https://docs.flanks.io/pages/flanks-apis/links-api/#edit-link
        """
        body: dict[str, str | None] = {"token": token}
        if redirect_uri is not None:
            body["redirect_uri"] = redirect_uri
        if name is not None:
            body["name"] = name
        if company_name is not None:
            body["company_name"] = company_name
        if terms_and_conditions_url is not None:
            body["terms_and_conditions_url"] = terms_and_conditions_url
        if privacy_policy_url is not None:
            body["privacy_policy_url"] = privacy_policy_url

        return await self.api_call(
            "/v0/links/edit-link",
            body,
            model=Link,
        )

    async def delete(self, token: str) -> None:
        """Delete a link. Only links with no pending codes can be deleted.

        See: https://docs.flanks.io/pages/flanks-apis/links-api/#delete-link
        """
        await self.transport.api_call("/v0/links/delete-link", {"token": token})

    async def pause(self, token: str) -> Link:
        """Pause a link.

        See: https://docs.flanks.io/pages/flanks-apis/links-api/#pause-link
        """
        return await self.api_call(
            "/v0/links/pause-link",
            {"token": token},
            model=Link,
        )

    async def resume(self, token: str) -> Link:
        """Resume a paused link.

        See: https://docs.flanks.io/pages/flanks-apis/links-api/#resume-link
        """
        return await self.api_call(
            "/v0/links/resume-link",
            {"token": token},
            model=Link,
        )

    async def get_unused_codes(self, link_token: str | None = None) -> builtins.list[LinkCode]:
        """Get unused exchange codes, optionally filtered by link_token.

        See: https://docs.flanks.io/pages/flanks-apis/links-api/#get-unused-link-codes
        """
        params = {"link_token": link_token} if link_token else None
        return await self.api_call(
            "/v0/platform/link",
            method="GET",
            params=params,
            model=list[LinkCode],
        )

    async def exchange_code(self, code: str) -> LinkCodeExchangeResult:
        """Exchange a code for credentials. The code is single-use.

        See: https://docs.flanks.io/pages/flanks-apis/links-api/#exchange-link-code-for-credentials-token
        """
        return await self.api_call(
            "/v0/platform/link",
            {"code": code},
            model=LinkCodeExchangeResult,
        )
