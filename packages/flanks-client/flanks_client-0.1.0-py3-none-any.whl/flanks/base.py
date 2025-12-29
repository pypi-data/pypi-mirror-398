from collections.abc import AsyncIterator
from typing import Any, TypeVar, cast, get_args, get_origin, overload

from pydantic import BaseModel

from flanks.connection import FlanksConnection
from flanks.pagination import PagedResponse

T = TypeVar("T", bound=BaseModel)


class BaseClient:
    """Base class for all API sub-clients."""

    def __init__(self, transport: FlanksConnection) -> None:
        self.transport = transport

    @overload
    async def api_call(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        params: dict[str, Any] | None = None,
        *,
        model: type[T],
    ) -> T: ...

    @overload
    async def api_call(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        params: dict[str, Any] | None = None,
        *,
        model: type[list[T]],
    ) -> list[T]: ...

    async def api_call(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        params: dict[str, Any] | None = None,
        *,
        model: type[T] | type[list[T]],
    ) -> T | list[T]:
        """Execute API call with model validation.

        Args:
            path: API endpoint path
            body: JSON body for POST/PUT/DELETE requests
            method: HTTP method (GET, POST, PUT, DELETE)
            params: Query parameters for GET requests
            model: Pydantic model to validate response.
                Use `Model` for dict responses, `list[Model]` for list responses.
        """
        result = await self.transport.api_call(path, body, method, params)

        if get_origin(model) is list:
            inner_model = get_args(model)[0]
            if not isinstance(result, list):
                raise TypeError(f"Expected list response, got {type(result)}")
            return [inner_model.model_validate(item) for item in result]

        if not isinstance(result, dict):
            raise TypeError(f"Expected dict response, got {type(result)}")
        return cast(type[T], model).model_validate(result)

    async def api_call_paged(
        self,
        path: str,
        body: dict[str, Any],
        *,
        model: type[T],
    ) -> PagedResponse[T]:
        """Execute API call and return PagedResponse.

        Args:
            path: API endpoint path
            body: JSON body (should include page_token if paginating)
            model: Pydantic model for items in the response
        """
        response = await self.transport.api_call(path, body)
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return PagedResponse(
            items=[model.model_validate(item) for item in response["items"]],
            next_page_token=response.get("next_page_token"),
        )

    async def iterate_paged(
        self,
        path: str,
        body: dict[str, Any],
        model: type[T],
    ) -> AsyncIterator[T]:
        """Iterate over all items from a paginated endpoint."""
        page_token: str | None = None
        while True:
            result = await self.api_call_paged(
                path, {**body, "page_token": page_token}, model=model
            )
            for item in result.items:
                yield item
            if not result.next_page_token:
                break
            page_token = result.next_page_token
