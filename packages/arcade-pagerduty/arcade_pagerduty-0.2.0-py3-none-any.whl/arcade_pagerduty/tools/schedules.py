"""Schedule tools for PagerDuty toolkit."""

from typing import Annotated, cast

from arcade_mcp_server import Context, tool

from arcade_pagerduty.client import PagerDutyClient
from arcade_pagerduty.models.mappers import map_schedules_list
from arcade_pagerduty.models.tool_outputs import SchedulesListOutput
from arcade_pagerduty.utils.auth_utils import get_pagerduty_auth
from arcade_pagerduty.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_schedules
# API Calls: 1
# APIs Used: GET /schedules (REST)
# Response Complexity: LOW - schedule summaries with on-call users when available
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Schedules"
#   readOnlyHint: true       - Only reads schedules
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=[
            "schedules.read",  # /schedules
            "oncalls.read",  # on-call user info in schedules responses
        ],
    )
)
async def list_schedules(
    context: Context,
    limit: Annotated[int, "Maximum schedules to return (1-50). Default is 10."] = 10,
    offset: Annotated[int | None, "Offset for pagination. Default is None."] = None,
    time_zone: Annotated[
        str | None,
        "Optional time zone (IANA format, e.g., America/New_York). Default is None.",
    ] = None,
) -> Annotated[SchedulesListOutput, "Schedules with pagination fields"]:
    """List schedules."""
    token = context.get_auth_token_or_empty()
    limit = min(50, max(1, limit))
    async with PagerDutyClient(token) as client:
        response = await client.get_schedules(
            limit=limit,
            offset=offset,
            time_zone=time_zone,
        )

    result = map_schedules_list(response)
    return cast(SchedulesListOutput, remove_none_values_recursive(result))
