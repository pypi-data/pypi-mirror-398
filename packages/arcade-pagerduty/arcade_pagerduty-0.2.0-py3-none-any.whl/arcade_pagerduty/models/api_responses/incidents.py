"""API response types for incidents endpoints."""

from typing_extensions import TypedDict


class Reference(TypedDict, total=False):
    """Generic reference object."""

    id: str
    type: str
    summary: str
    html_url: str


class Assignment(TypedDict, total=False):
    """Incident assignment record."""

    at: str
    assignee: Reference


class PriorityRef(TypedDict, total=False):
    """Priority reference."""

    id: str
    summary: str
    name: str


class IncidentData(TypedDict, total=False):
    """Raw incident data from PagerDuty."""

    id: str
    summary: str
    status: str
    urgency: str
    priority: PriorityRef
    service: Reference
    escalation_policy: Reference
    teams: list[Reference]
    assignments: list[Assignment]
    created_at: str
    last_status_change_at: str
    resolved_at: str
    html_url: str


class IncidentsListResponse(TypedDict, total=False):
    """Response from GET /incidents."""

    incidents: list[IncidentData]
    limit: int
    offset: int
    more: bool


class IncidentSingleResponse(TypedDict, total=False):
    """Response from GET /incidents/{id}."""

    incident: IncidentData
