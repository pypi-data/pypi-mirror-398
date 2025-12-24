"""API response types for services endpoints."""

from typing_extensions import TypedDict

from arcade_pagerduty.models.api_responses.incidents import Reference


class ServiceData(TypedDict, total=False):
    """Raw service data."""

    id: str
    name: str
    status: str
    html_url: str
    escalation_policy: Reference
    teams: list[Reference]


class ServicesListResponse(TypedDict, total=False):
    """Response from GET /services."""

    services: list[ServiceData]
    limit: int
    offset: int
    more: bool


class ServiceSingleResponse(TypedDict, total=False):
    """Response from GET /services/{id}."""

    service: ServiceData
