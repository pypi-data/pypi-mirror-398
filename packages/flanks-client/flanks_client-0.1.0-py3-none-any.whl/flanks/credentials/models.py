from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Credential(BaseModel):
    """A stored credential from the list endpoint."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    credentials_token: str
    external_id: str | None = None
    bank: str | None = None
    status: str | None = None


class CredentialsListResponse(BaseModel):
    """Response from the list credentials endpoint."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    items: list[Credential]
    page: int
    pages: int


class CredentialStatus(BaseModel):
    """Response from get_status endpoint with full credential status."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    pending: bool | None = None
    blocked: bool | None = None
    reset_token: str | None = None
    sca_token: str | None = None
    transaction_token: str | None = None
    name: str | None = None
    last_update: datetime | None = None
    last_transaction_date: datetime | None = None
    errored: bool | None = None
    created: datetime | None = None
