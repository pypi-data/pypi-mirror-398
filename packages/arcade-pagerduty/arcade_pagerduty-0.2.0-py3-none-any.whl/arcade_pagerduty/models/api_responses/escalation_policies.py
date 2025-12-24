"""API response types for escalation policies endpoints."""

from typing_extensions import TypedDict


class TargetRef(TypedDict, total=False):
    """Target reference in escalation level."""

    id: str
    type: str
    summary: str


class EscalationRule(TypedDict, total=False):
    """Escalation rule entry."""

    id: str
    escalation_delay_in_minutes: int
    rule_object: dict[str, str]
    targets: list[TargetRef]


class EscalationPolicyData(TypedDict, total=False):
    """Escalation policy record."""

    id: str
    name: str
    description: str
    html_url: str
    escalation_rules: list[EscalationRule]
    num_loops: int
    teams: list[dict[str, str]]


class EscalationPoliciesListResponse(TypedDict, total=False):
    """Response from GET /escalation_policies."""

    escalation_policies: list[EscalationPolicyData]
    limit: int
    offset: int
    more: bool


class EscalationPolicySingleResponse(TypedDict, total=False):
    """Response from GET /escalation_policies/{id}."""

    escalation_policy: EscalationPolicyData
