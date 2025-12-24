"""API response models for schedules endpoints."""

from typing_extensions import TypedDict

from arcade_pagerduty.models.api_responses.users import UserData


class ScheduleUser(UserData, total=False):
    """User reference within a schedule."""


class ScheduleData(TypedDict, total=False):
    """Schedule fields returned from /schedules."""

    id: str
    name: str
    time_zone: str
    html_url: str
    users: list[ScheduleUser]


class SchedulesListResponse(TypedDict, total=False):
    """Schedules list response."""

    schedules: list[ScheduleData]
    limit: int
    offset: int
    more: bool
