from pydantic import BaseModel, ConfigDict


class Entity(BaseModel):
    """A banking entity available for connection."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str
    name: str
    country: str | None = None
    logo_url: str | None = None
