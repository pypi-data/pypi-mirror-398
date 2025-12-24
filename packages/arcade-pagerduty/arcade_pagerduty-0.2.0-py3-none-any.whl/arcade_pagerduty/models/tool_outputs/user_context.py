"""Tool output types for user context."""

from typing_extensions import TypedDict


class TeamSummaryOutput(TypedDict, total=False):
    """Team reference for the user."""

    id: str
    """Team identifier."""

    name: str
    """Team display name."""


class ContactMethodsSummaryOutput(TypedDict, total=False):
    """Summarized contact methods for the user."""

    email_addresses: list[str]
    """Email contact addresses."""

    phone_numbers: list[str]
    """Phone or SMS contact numbers."""

    push_devices: list[str]
    """Push-capable device labels or descriptions."""


class NotificationRulesSummaryOutput(TypedDict, total=False):
    """Summarized notification rules for the user."""

    rule_count: int
    """Total notification rules."""

    channels: list[str]
    """Channels used by notification rules (e.g., email, phone, push)."""


class WhoAmIOutput(TypedDict, total=False):
    """Output for whoami tool."""

    id: str
    """User identifier."""

    name: str | None
    """User full name."""

    email: str | None
    """User email address."""

    role: str | None
    """User role."""

    job_title: str | None
    """User job title."""

    time_zone: str | None
    """User time zone."""

    html_url: str | None
    """User profile HTML URL."""

    teams: list[TeamSummaryOutput]
    """Teams the user belongs to."""

    contact_methods: ContactMethodsSummaryOutput
    """Summary of user contact methods."""

    notification_rules: NotificationRulesSummaryOutput
    """Summary of user notification rules."""

    is_on_call_now: bool
    """Whether the user is currently on call."""

    next_on_call_start: str | None
    """Start time of the user's next on-call window (ISO 8601 UTC)."""

    next_on_call_end: str | None
    """End time of the user's next on-call window (ISO 8601 UTC)."""
