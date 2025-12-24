"""Common tool output types for PagerDuty toolkit."""

from typing_extensions import TypedDict


class ReferenceOutput(TypedDict, total=False):
    """Generic reference to a PagerDuty entity."""

    id: str
    """Identifier of the referenced entity."""

    name: str | None
    """Display name or summary."""

    html_url: str | None
    """HTML URL of the referenced entity, when available."""
