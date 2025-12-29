from enum import Enum

from pydantic import BaseModel, ConfigDict


class SessionStatus(str, Enum):
    WAITING_CREDENTIALS = "Waiting:ProvideCredentials"
    WAITING_CHALLENGE = "Waiting:Challenge"
    PROCESSING_CREDENTIALS = "Processing:ProvideCredentials"
    PROCESSING_CHALLENGE = "Processing:Challenge"
    FINISHED_OK = "Finished:OK"
    FINISHED_ERROR = "Finished:Error"


class SessionErrorCode(str, Enum):
    INVALID_CREDENTIALS = "InvalidCredentials"
    INVALID_CHALLENGE = "InvalidChallengeResponse"
    UNSUPPORTED_CHALLENGE = "UnsupportedChallengeMethod"
    USER_INTERACTION_NEEDED = "UserInteractionNeeded"
    INTERNAL_ERROR = "InternalError"


class Session(BaseModel):
    """A connection session."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    session_id: str
    status: SessionStatus
    connection_id: str | None = None
    error_code: SessionErrorCode | None = None


class SessionQuery(BaseModel):
    """Query parameters for listing sessions."""

    model_config = ConfigDict(extra="ignore")

    session_id_in: list[str] | None = None
    status_in: list[SessionStatus] | None = None
    connection_id_in: list[str] | None = None
    error_code_in: list[SessionErrorCode] | None = None


class SessionConfig(BaseModel):
    """Configuration for creating a session."""

    model_config = ConfigDict(extra="ignore")

    connector_id: str


class Connector(BaseModel):
    """A banking connector."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    connector_id: str
    name: str
