"""Tool outputs for users."""

from typing_extensions import TypedDict

from arcade_pagerduty.models.tool_outputs.user_context import TeamSummaryOutput


class UserSummaryOutput(TypedDict, total=False):
    """User summary fields."""

    id: str
    name: str | None
    email: str | None
    role: str | None
    job_title: str | None
    time_zone: str | None
    teams: list[TeamSummaryOutput]
    html_url: str | None


class UsersListOutput(TypedDict, total=False):
    """Paginated users list."""

    users: list[UserSummaryOutput]
    limit: int | None
    offset: int | None
    more: bool | None


class SearchUserMatchOutput(TypedDict, total=False):
    """Single fuzzy match entry."""

    id: str
    name: str | None
    email: str | None
    role: str | None
    confidence: float


class SearchUsersOutput(TypedDict, total=False):
    """Fuzzy user search output."""

    query: str
    matches: list[SearchUserMatchOutput]
    auto_accepted: bool
