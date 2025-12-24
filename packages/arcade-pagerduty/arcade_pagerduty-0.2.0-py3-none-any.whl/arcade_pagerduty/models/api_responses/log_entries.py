"""API response types for log entries."""

from typing_extensions import TypedDict


class LogEntryAgent(TypedDict, total=False):
    """Agent (user) who performed the action."""

    id: str
    type: str
    summary: str
    html_url: str


class LogEntryIncident(TypedDict, total=False):
    """Incident reference in log entry."""

    id: str
    type: str
    summary: str
    html_url: str


class LogEntryService(TypedDict, total=False):
    """Service reference in log entry."""

    id: str
    type: str
    summary: str
    html_url: str


class LogEntryData(TypedDict, total=False):
    """Single log entry from API response."""

    id: str
    type: str
    summary: str
    created_at: str
    agent: LogEntryAgent
    incident: LogEntryIncident
    service: LogEntryService
    html_url: str


class LogEntriesListResponse(TypedDict, total=False):
    """Response from GET /log_entries."""

    log_entries: list[LogEntryData]
    limit: int
    offset: int
    more: bool
    total: int
