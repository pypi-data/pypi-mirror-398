"""Tool outputs for schedule listings."""

from typing_extensions import TypedDict

from arcade_pagerduty.models.tool_outputs.oncalls import OnCallUserOutput


class ScheduleOutput(TypedDict, total=False):
    """Schedule summary."""

    id: str
    name: str
    time_zone: str
    html_url: str
    current_oncalls: list[OnCallUserOutput]


class SchedulesListOutput(TypedDict, total=False):
    """Paginated schedule list."""

    schedules: list[ScheduleOutput]
    limit: int | None
    offset: int | None
    more: bool | None
