"""Tool output types for services."""

from typing_extensions import TypedDict

from arcade_pagerduty.models.tool_outputs.common import ReferenceOutput


class ServiceSummaryOutput(TypedDict, total=False):
    """Service summary output."""

    id: str
    """Service identifier."""

    name: str | None
    """Service name."""

    status: str | None
    """Service status."""

    escalation_policy: ReferenceOutput | None
    """Escalation policy reference."""

    team: ReferenceOutput | None
    """Primary team reference (first team)."""

    html_url: str | None
    """Service HTML URL."""


class ServicesListOutput(TypedDict, total=False):
    """Output for list_services."""

    services: list[ServiceSummaryOutput]
    """Services returned."""

    limit: int | None
    """Limit applied."""

    offset: int | None
    """Offset applied."""

    more: bool | None
    """True if more pages available."""


class ServiceDetailOutput(ServiceSummaryOutput, total=False):
    """Output for get_service."""
