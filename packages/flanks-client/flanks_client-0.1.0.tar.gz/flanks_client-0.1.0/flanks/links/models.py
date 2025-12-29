from typing import Any

from pydantic import BaseModel, ConfigDict


class Link(BaseModel):
    """A connection link for end-user authentication."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    token: str
    name: str | None = None
    redirect_uri: str | None = None
    company_name: str | None = None
    terms_and_conditions_url: str | None = None
    privacy_policy_url: str | None = None
    active: bool = True
    pending_code_count: int | None = None


class LinkCode(BaseModel):
    """An exchange code for a link."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    code: str
    link_token: str | None = None
    extra: dict[str, Any] | None = None


class LinkCodeExchangeResult(BaseModel):
    """Result of exchanging a link code for credentials."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    credentials_token: str
    link_token: str | None = None
    extra: dict[str, Any] | None = None
    message: str | None = None
