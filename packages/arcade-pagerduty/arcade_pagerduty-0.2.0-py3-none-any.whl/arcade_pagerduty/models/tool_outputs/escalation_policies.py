"""Tool outputs for escalation policies."""

from typing_extensions import TypedDict

from arcade_pagerduty.models.tool_outputs.common import ReferenceOutput


class EscalationTargetOutput(TypedDict, total=False):
    """Target user or schedule in escalation level."""

    id: str
    name: str | None
    type: str | None


class EscalationLevelOutput(TypedDict, total=False):
    """Escalation level with targets."""

    level: int | None
    targets: list[EscalationTargetOutput]
    targets_summary: str | None


class EscalationPolicySummaryOutput(TypedDict, total=False):
    """Escalation policy summary."""

    id: str
    name: str | None
    description: str | None
    team: ReferenceOutput | None
    levels: list[EscalationLevelOutput]
    html_url: str | None


class EscalationPoliciesListOutput(TypedDict, total=False):
    """Paginated escalation policies list."""

    policies: list[EscalationPolicySummaryOutput]
    limit: int | None
    offset: int | None
    more: bool | None


class EscalationPolicyDetailOutput(TypedDict, total=False):
    """Escalation policy detail."""

    id: str
    name: str | None
    description: str | None
    html_url: str | None
    team: ReferenceOutput | None
    repeat_count: int | None
    escalation_delay: int | None
    levels: list[EscalationLevelOutput]
