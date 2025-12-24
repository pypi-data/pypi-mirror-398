"""Escalation policy tools for PagerDuty toolkit."""

from typing import Annotated, cast

from arcade_mcp_server import Context, tool

from arcade_pagerduty.client import PagerDutyClient
from arcade_pagerduty.models.mappers import (
    map_escalation_policies_list,
    map_escalation_policy_detail,
)
from arcade_pagerduty.models.tool_outputs import (
    EscalationPoliciesListOutput,
    EscalationPolicyDetailOutput,
)
from arcade_pagerduty.utils.auth_utils import get_pagerduty_auth
from arcade_pagerduty.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_escalation_policies
# API Calls: 1
# APIs Used: GET /escalation_policies (REST)
# Response Complexity: MEDIUM - levels summary
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Escalation Policies"
#   readOnlyHint: true       - Only reads policies
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=["escalation_policies.read"],  # /escalation_policies
    )
)
async def list_escalation_policies(
    context: Context,
    limit: Annotated[int, "Maximum policies to return (1-50). Default is 10."] = 10,
    offset: Annotated[int | None, "Offset for pagination. Default is None."] = None,
) -> Annotated[EscalationPoliciesListOutput, "Escalation policies with pagination fields"]:
    """List escalation policies."""
    token = context.get_auth_token_or_empty()
    limit = min(50, max(1, limit))
    async with PagerDutyClient(token) as client:
        response = await client.get_escalation_policies(limit=limit, offset=offset)

    result = map_escalation_policies_list(response)
    return cast(EscalationPoliciesListOutput, remove_none_values_recursive(result))


# =============================================================================
# get_escalation_policy
# API Calls: 1
# APIs Used: GET /escalation_policies/{id} (REST)
# Response Complexity: MEDIUM - levels with targets
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Escalation Policy"
#   readOnlyHint: true       - Only reads policies
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=["escalation_policies.read"],  # /escalation_policies/{id}
    )
)
async def get_escalation_policy(
    context: Context,
    escalation_policy_id: Annotated[str, "Escalation policy ID to fetch."],
) -> Annotated[EscalationPolicyDetailOutput, "Escalation policy details."]:
    """Get a single escalation policy by ID."""
    token = context.get_auth_token_or_empty()
    async with PagerDutyClient(token) as client:
        response = await client.get_escalation_policy_by_id(escalation_policy_id)

    result = map_escalation_policy_detail(response)
    return cast(EscalationPolicyDetailOutput, remove_none_values_recursive(result))
