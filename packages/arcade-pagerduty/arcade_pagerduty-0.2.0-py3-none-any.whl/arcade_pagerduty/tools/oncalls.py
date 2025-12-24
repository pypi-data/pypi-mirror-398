"""On-call tools for PagerDuty toolkit."""

from typing import Annotated, cast

from arcade_mcp_server import Context, tool

from arcade_pagerduty.client import PagerDutyClient
from arcade_pagerduty.models.mappers import map_oncalls_list
from arcade_pagerduty.models.tool_outputs import OnCallsListOutput
from arcade_pagerduty.utils.auth_utils import get_pagerduty_auth
from arcade_pagerduty.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_oncalls
# API Calls: 1
# APIs Used: GET /oncalls (REST)
# Response Complexity: MEDIUM - includes policy and schedule references
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List On-Calls"
#   readOnlyHint: true       - Only reads on-call data
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=[
            "oncalls.read",  # /oncalls
            "schedules.read",  # schedule references in /oncalls
            "escalation_policies.read",  # escalation policy references in /oncalls
        ],
    )
)
async def list_oncalls(
    context: Context,
    schedule_ids: Annotated[list[str] | None, "Filter by schedule IDs. Default is None."] = None,
    escalation_policy_ids: Annotated[
        list[str] | None, "Filter by escalation policy IDs. Default is None."
    ] = None,
    team_ids: Annotated[list[str] | None, "Filter by team IDs. Default is None."] = None,
    time_zone: Annotated[str | None, "Optional time zone for times. Default is None."] = None,
    limit: Annotated[int, "Maximum on-call entries to return (1-50). Default is 10."] = 10,
    offset: Annotated[int | None, "Offset for pagination. Default is None."] = None,
    since: Annotated[
        str | None, "Filter entries starting at or after this ISO 8601 time. Default is None."
    ] = None,
    until: Annotated[
        str | None, "Filter entries ending at or before this ISO 8601 time. Default is None."
    ] = None,
) -> Annotated[OnCallsListOutput, "On-call entries with pagination fields"]:
    """List on-call entries with optional filters."""
    token = context.get_auth_token_or_empty()
    limit = min(50, max(1, limit))
    async with PagerDutyClient(token) as client:
        response = await client.get_oncalls(
            schedule_ids=schedule_ids,
            escalation_policy_ids=escalation_policy_ids,
            team_ids=team_ids,
            limit=limit,
            offset=offset,
            time_zone=time_zone,
            since=since,
            until=until,
        )

    result = map_oncalls_list(response)
    return cast(OnCallsListOutput, remove_none_values_recursive(result))
