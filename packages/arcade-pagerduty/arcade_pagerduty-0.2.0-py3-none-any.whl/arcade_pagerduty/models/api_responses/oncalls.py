"""API response types for on-call endpoints."""

from typing_extensions import TypedDict

from arcade_pagerduty.models.api_responses.users import UserData


class OnCallData(TypedDict, total=False):
    """Raw on-call record."""

    user: UserData
    """User who is on call."""

    schedule: dict[str, str]
    """Schedule reference (id, summary, type, html_url)."""

    escalation_policy: dict[str, str]
    """Escalation policy reference."""

    start: str
    """On-call start timestamp (ISO 8601)."""

    end: str
    """On-call end timestamp (ISO 8601)."""

    level: int
    """Escalation level."""


class OnCallListResponse(TypedDict, total=False):
    """Response from GET /oncalls."""

    oncalls: list[OnCallData]
    """List of on-call entries."""

    limit: int
    """Max items returned per request."""

    offset: int
    """Offset applied."""

    more: bool
    """True when more data is available."""
