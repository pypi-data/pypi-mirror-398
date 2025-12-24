"""Tool output types for incidents."""

from typing_extensions import TypedDict

from arcade_pagerduty.models.tool_outputs.common import ReferenceOutput


class AssignmentOutput(TypedDict, total=False):
    """Assignment detail."""

    assignee: ReferenceOutput
    """Assigned user reference."""


class IncidentSummaryOutput(TypedDict, total=False):
    """Incident summary output for listings."""

    id: str
    """Incident identifier."""

    title: str | None
    """Incident title/summary."""

    status: str | None
    """Incident status."""

    urgency: str | None
    """Incident urgency."""

    priority: str | None
    """Priority name if present."""

    service: ReferenceOutput | None
    """Service reference."""

    team: ReferenceOutput | None
    """Primary team reference (first team)."""

    escalation_policy: ReferenceOutput | None
    """Escalation policy reference."""

    assignments: list[AssignmentOutput]
    """Current assignments."""

    html_url: str | None
    """Incident HTML URL."""

    created_at: str | None
    """Incident creation time (ISO 8601 UTC)."""

    last_status_change_at: str | None
    """Last status change time (ISO 8601 UTC)."""

    resolved_at: str | None
    """Resolved time if resolved (ISO 8601 UTC)."""


class IncidentsListOutput(TypedDict, total=False):
    """Output for list_incidents."""

    incidents: list[IncidentSummaryOutput]
    """Incidents returned."""

    limit: int | None
    """Limit applied."""

    offset: int | None
    """Offset applied."""

    more: bool | None
    """True if more pages available."""


class IncidentDetailOutput(IncidentSummaryOutput, total=False):
    """Output for get_incident."""

    # Same fields as summary; extended fields can be added later if needed.
