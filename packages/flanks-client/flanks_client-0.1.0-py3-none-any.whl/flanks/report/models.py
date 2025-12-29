from enum import Enum

from pydantic import BaseModel, ConfigDict


class ReportStatus(str, Enum):
    """Report generation status."""

    NEW = "new"
    PAYLOAD = "payload"
    FILE = "file"
    READY = "ready"
    FAIL = "fail"


class ReportTemplate(BaseModel):
    """A report template."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    template_id: int
    name: str | None = None
    description: str | None = None


class Report(BaseModel):
    """A generated report."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    report_id: int
    template_id: int | None = None
    status: ReportStatus | None = None
