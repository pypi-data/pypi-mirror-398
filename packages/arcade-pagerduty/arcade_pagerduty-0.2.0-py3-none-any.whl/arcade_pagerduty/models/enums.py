"""Enum definitions for PagerDuty toolkit."""

from enum import Enum


class IncidentStatus(str, Enum):
    """Incident status values."""

    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class IncidentUrgency(str, Enum):
    """Incident urgency values."""

    HIGH = "high"
    LOW = "low"
