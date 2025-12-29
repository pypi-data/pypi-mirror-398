from typing import Any

from flanks.aggregation_v1.models import (
    Account,
    Card,
    Holder,
    Identity,
    Investment,
    Liability,
    Portfolio,
    Transaction,
)
from flanks.base import BaseClient


class AggregationV1Client(BaseClient):
    """Client for Aggregation API v1.

    See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/
    """

    async def get_portfolios(
        self,
        credentials_token: str,
        query: dict[str, Any] | None = None,
        ignore_data_error: bool = False,
    ) -> list[Portfolio]:
        """Get investment portfolios.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/#get-portfolios
        """
        return await self.api_call(
            "/v0/bank/credentials/portfolio",
            {
                "credentials_token": credentials_token,
                "query": query or {},
                "ignore_data_error": ignore_data_error,
            },
            model=list[Portfolio],
        )

    async def get_investments(
        self,
        credentials_token: str,
        query: dict[str, Any] | None = None,
        ignore_data_error: bool = False,
    ) -> list[Investment]:
        """Get investment positions.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/#get-investments
        """
        return await self.api_call(
            "/v0/bank/credentials/investment",
            {
                "credentials_token": credentials_token,
                "query": query or {},
                "ignore_data_error": ignore_data_error,
            },
            model=list[Investment],
        )

    async def get_investment_transactions(
        self,
        credentials_token: str,
        query: dict[str, Any] | None = None,
        ignore_data_error: bool = False,
    ) -> list[Transaction]:
        """Get investment transactions.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/#get-investment-transactions
        """
        return await self.api_call(
            "/v0/bank/credentials/investment/transaction",
            {
                "credentials_token": credentials_token,
                "query": query or {},
                "ignore_data_error": ignore_data_error,
            },
            model=list[Transaction],
        )

    async def get_accounts(
        self,
        credentials_token: str,
        query: dict[str, Any] | None = None,
        ignore_data_error: bool = False,
    ) -> list[Account]:
        """Get bank accounts.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/#get-accounts
        """
        return await self.api_call(
            "/v0/bank/credentials/account",
            {
                "credentials_token": credentials_token,
                "query": query or {},
                "ignore_data_error": ignore_data_error,
            },
            model=list[Account],
        )

    async def get_account_transactions(
        self,
        credentials_token: str,
        query: dict[str, Any] | None = None,
        ignore_data_error: bool = False,
    ) -> list[Transaction]:
        """Get account transactions.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/#get-account-transactions
        """
        return await self.api_call(
            "/v0/bank/credentials/data",
            {
                "credentials_token": credentials_token,
                "query": query or {},
                "ignore_data_error": ignore_data_error,
            },
            model=list[Transaction],
        )

    async def get_liabilities(
        self,
        credentials_token: str,
        query: dict[str, Any] | None = None,
        ignore_data_error: bool = False,
    ) -> list[Liability]:
        """Get liabilities (loans, mortgages).

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/#get-liabilities
        """
        return await self.api_call(
            "/v0/bank/credentials/liability",
            {
                "credentials_token": credentials_token,
                "query": query or {},
                "ignore_data_error": ignore_data_error,
            },
            model=list[Liability],
        )

    async def get_liability_transactions(
        self,
        credentials_token: str,
        query: dict[str, Any] | None = None,
        ignore_data_error: bool = False,
    ) -> list[Transaction]:
        """Get liability transactions.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/#get-liability-transactions
        """
        return await self.api_call(
            "/v0/bank/credentials/liability/transaction",
            {
                "credentials_token": credentials_token,
                "query": query or {},
                "ignore_data_error": ignore_data_error,
            },
            model=list[Transaction],
        )

    async def get_cards(
        self,
        credentials_token: str,
        query: dict[str, Any] | None = None,
        ignore_data_error: bool = False,
    ) -> list[Card]:
        """Get credit/debit cards.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/#get-cards
        """
        return await self.api_call(
            "/v0/bank/credentials/card",
            {
                "credentials_token": credentials_token,
                "query": query or {},
                "ignore_data_error": ignore_data_error,
            },
            model=list[Card],
        )

    async def get_card_transactions(
        self,
        credentials_token: str,
        query: dict[str, Any] | None = None,
        ignore_data_error: bool = False,
    ) -> list[Transaction]:
        """Get card transactions.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/#get-card-transactions
        """
        return await self.api_call(
            "/v0/bank/credentials/card/transaction",
            {
                "credentials_token": credentials_token,
                "query": query or {},
                "ignore_data_error": ignore_data_error,
            },
            model=list[Transaction],
        )

    async def get_identity(
        self,
        credentials_token: str,
        ignore_data_error: bool = False,
    ) -> Identity | None:
        """Get account holder identity.

        Note: This endpoint returns a single object, not an array.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/#get-identity
        """
        response = await self.transport.api_call(
            "/v0/bank/credentials/auth/",
            {
                "credentials_token": credentials_token,
                "ignore_data_error": ignore_data_error,
            },
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Identity.model_validate(response) if response else None

    async def get_holders(
        self,
        credentials_token: str,
        ignore_data_error: bool = False,
    ) -> list[Holder]:
        """Get account holders.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/#get-holders
        """
        return await self.api_call(
            "/v0/bank/credentials/holder",
            {
                "credentials_token": credentials_token,
                "ignore_data_error": ignore_data_error,
            },
            model=list[Holder],
        )
