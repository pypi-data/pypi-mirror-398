"""Team tools for PagerDuty toolkit."""

from typing import Annotated, cast

from arcade_mcp_server import Context, tool

from arcade_pagerduty.client import PagerDutyClient
from arcade_pagerduty.models.mappers import map_team_detail, map_teams_list
from arcade_pagerduty.models.tool_outputs import TeamDetailOutput, TeamsListOutput
from arcade_pagerduty.utils.auth_utils import get_pagerduty_auth
from arcade_pagerduty.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_teams
# API Calls: 1
# APIs Used: GET /teams (REST)
# Response Complexity: LOW - teams with default policy refs
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Teams"
#   readOnlyHint: true       - Only reads teams
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=["teams.read"],  # /teams
    )
)
async def list_teams(
    context: Context,
    limit: Annotated[int, "Maximum teams to return (1-50). Default is 10."] = 10,
    offset: Annotated[int | None, "Offset for pagination. Default is None."] = None,
) -> Annotated[TeamsListOutput, "Teams with pagination fields"]:
    """List teams."""
    token = context.get_auth_token_or_empty()
    limit = min(50, max(1, limit))
    async with PagerDutyClient(token) as client:
        response = await client.get_teams(limit=limit, offset=offset)

    result = map_teams_list(response)
    return cast(TeamsListOutput, remove_none_values_recursive(result))


# =============================================================================
# get_team
# API Calls: 1
# APIs Used: GET /teams/{id} (REST)
# Response Complexity: MEDIUM - includes members/services/schedules
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Team"
#   readOnlyHint: true       - Only reads teams
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=[
            "teams.read",  # /teams/{id}
            "users.read",  # members include
            "escalation_policies.read",  # escalation_policies include
            "services.read",  # services include
        ],
    )
)
async def get_team(
    context: Context,
    team_id: Annotated[str, "Team ID to fetch."],
) -> Annotated[TeamDetailOutput, "Team details."]:
    """Get a single team by ID including members and linked resources."""
    token = context.get_auth_token_or_empty()
    async with PagerDutyClient(token) as client:
        response = await client.get_team_by_id(team_id)

    result = map_team_detail(response)
    return cast(TeamDetailOutput, remove_none_values_recursive(result))
