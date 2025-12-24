"""API response types for teams endpoints."""

from typing_extensions import TypedDict

from arcade_pagerduty.models.api_responses.users import UserData


class TeamReference(TypedDict, total=False):
    """Minimal team ref."""

    id: str
    summary: str
    type: str
    html_url: str


class TeamData(TypedDict, total=False):
    """Team record."""

    id: str
    name: str
    description: str
    html_url: str
    default_escalation_policy: dict[str, str]
    members: list[UserData]
    escalation_policies: list[dict[str, str]]
    services: list[dict[str, str]]
    schedules: list[dict[str, str]]


class TeamsListResponse(TypedDict, total=False):
    """Response from GET /teams."""

    teams: list[TeamData]
    limit: int
    offset: int
    more: bool


class TeamSingleResponse(TypedDict, total=False):
    """Response from GET /teams/{id}."""

    team: TeamData
