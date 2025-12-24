"""API response types for PagerDuty users endpoints."""

from typing_extensions import TypedDict


class TeamSummary(TypedDict, total=False):
    """Minimal team reference."""

    id: str
    """Team identifier."""

    type: str
    """Entity type name."""

    summary: str
    """Display summary."""

    html_url: str
    """Team HTML URL."""


class ContactMethod(TypedDict, total=False):
    """Contact method record."""

    id: str
    """Contact method identifier."""

    type: str
    """Contact method type (e.g., email_contact_method)."""

    summary: str
    """Display summary."""

    address: str
    """Contact address (email or phone)."""

    label: str
    """User-defined label for the contact method."""


class NotificationRule(TypedDict, total=False):
    """Notification rule record."""

    id: str
    """Notification rule identifier."""

    type: str
    """Notification rule type."""

    summary: str
    """Display summary."""

    urgency: str
    """Urgency the rule applies to."""

    contact_method: ContactMethod
    """Contact method used by the rule."""


class UserData(TypedDict, total=False):
    """Raw user data from PagerDuty."""

    id: str
    """User identifier."""

    name: str
    """User's full name."""

    email: str
    """User email."""

    role: str
    """User role."""

    job_title: str
    """User job title."""

    time_zone: str
    """User time zone."""

    html_url: str
    """User HTML profile URL."""

    teams: list[TeamSummary]
    """Teams the user belongs to."""

    contact_methods: list[ContactMethod]
    """Contact methods attached to the user."""

    notification_rules: list[NotificationRule]
    """Notification rules attached to the user."""


class MeResponse(TypedDict, total=False):
    """Response from GET /users/me."""

    user: UserData
    """Authenticated user payload."""


class UsersListResponse(TypedDict, total=False):
    """Response from GET /users."""

    users: list[UserData]
    limit: int
    offset: int
    more: bool
