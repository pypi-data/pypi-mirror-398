"""Log entries tools for PagerDuty toolkit."""

from typing import Annotated, cast

from arcade_mcp_server import Context, tool

from arcade_pagerduty.client import PagerDutyClient
from arcade_pagerduty.models.mappers import map_log_entries_list
from arcade_pagerduty.models.tool_outputs import LogEntriesListOutput
from arcade_pagerduty.utils.auth_utils import get_pagerduty_auth
from arcade_pagerduty.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_log_entries
# API Calls: 1
# APIs Used: GET /log_entries (REST)
# Response Complexity: MEDIUM - activity feed with incident/service refs
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Log Entries"
#   readOnlyHint: true       - Only reads log entries
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=["incidents.read"],  # /log_entries
    )
)
async def list_log_entries(
    context: Context,
    since: Annotated[str | None, "Start time filter (ISO 8601 UTC). Default is None."] = None,
    until: Annotated[str | None, "End time filter (ISO 8601 UTC). Default is None."] = None,
    team_ids: Annotated[list[str] | None, "Filter by team IDs. Default is None."] = None,
    time_zone: Annotated[
        str | None,
        "Time zone for times (IANA format, e.g., America/New_York). Default is None.",
    ] = None,
    is_overview: Annotated[bool, "Return compact overview entries. Default is True."] = True,
    limit: Annotated[int, "Maximum entries to return (1-50). Default is 10."] = 10,
    offset: Annotated[int | None, "Offset for pagination. Default is None."] = None,
) -> Annotated[LogEntriesListOutput, "Activity log entries with pagination fields"]:
    """List log entries (activity feed) showing recent incident events.

    Returns events like incident triggers, acknowledgments, escalations,
    and resolutions across the account.
    """
    token = context.get_auth_token_or_empty()
    limit = min(50, max(1, limit))
    async with PagerDutyClient(token) as client:
        response = await client.get_log_entries(
            since=since,
            until=until,
            team_ids=team_ids,
            time_zone=time_zone,
            is_overview=is_overview,
            limit=limit,
            offset=offset,
        )

    result = map_log_entries_list(response)
    return cast(LogEntriesListOutput, remove_none_values_recursive(result))
