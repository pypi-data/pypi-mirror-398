"""Tool outputs for teams."""

from typing_extensions import TypedDict

from arcade_pagerduty.models.tool_outputs.common import ReferenceOutput


class TeamSummaryWithPolicyOutput(TypedDict, total=False):
    """Team summary with default policy reference."""

    id: str
    name: str | None
    html_url: str | None
    default_escalation_policy_id: str | None
    default_escalation_policy_name: str | None


class TeamsListOutput(TypedDict, total=False):
    """Paginated teams list."""

    teams: list[TeamSummaryWithPolicyOutput]
    limit: int | None
    offset: int | None
    more: bool | None


class TeamMemberOutput(TypedDict, total=False):
    """Team member entry."""

    id: str
    name: str | None
    role: str | None
    email: str | None


class TeamDetailOutput(TypedDict, total=False):
    """Team detail."""

    id: str
    name: str | None
    description: str | None
    html_url: str | None
    default_escalation_policy_id: str | None
    default_escalation_policy_name: str | None
    members: list[TeamMemberOutput]
    schedules: list[ReferenceOutput]
    services: list[ReferenceOutput]
