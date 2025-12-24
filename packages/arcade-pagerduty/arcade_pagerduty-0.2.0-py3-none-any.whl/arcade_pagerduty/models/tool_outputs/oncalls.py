"""Tool outputs for on-call listings."""

from typing_extensions import TypedDict


class OnCallUserOutput(TypedDict, total=False):
    """User assigned to an on-call entry."""

    id: str
    name: str
    email: str | None


class OnCallEntryOutput(TypedDict, total=False):
    """Single on-call record."""

    user: OnCallUserOutput
    escalation_policy_id: str | None
    escalation_policy_name: str | None
    schedule_id: str | None
    schedule_name: str | None
    level: int | None
    start: str | None
    end: str | None


class OnCallsListOutput(TypedDict, total=False):
    """Paginated on-call list."""

    oncalls: list[OnCallEntryOutput]
    limit: int | None
    offset: int | None
    more: bool | None
