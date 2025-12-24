"""Tool output types for log entries."""

from typing_extensions import TypedDict

from arcade_pagerduty.models.tool_outputs.common import ReferenceOutput


class LogEntryOutput(TypedDict, total=False):
    """Single log entry output."""

    id: str
    """Log entry ID."""

    type: str
    """Log entry type (e.g., trigger_log_entry, acknowledge_log_entry)."""

    summary: str
    """Human-readable summary of the event."""

    created_at: str
    """ISO 8601 timestamp when event occurred."""

    incident: ReferenceOutput
    """Incident this entry belongs to."""

    service: ReferenceOutput
    """Service associated with the incident."""

    user: ReferenceOutput
    """User who performed the action (if applicable)."""


class LogEntriesListOutput(TypedDict, total=False):
    """Output for list_log_entries tool."""

    log_entries: list[LogEntryOutput]
    """List of log entries."""

    limit: int
    """Maximum entries requested."""

    offset: int
    """Pagination offset."""

    more: bool
    """True if more entries exist."""
