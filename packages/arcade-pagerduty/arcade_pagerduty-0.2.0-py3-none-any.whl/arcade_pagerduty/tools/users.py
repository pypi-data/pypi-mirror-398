"""User tools for PagerDuty toolkit."""

from typing import Annotated, cast

from arcade_mcp_server import Context, tool

from arcade_pagerduty.client import PagerDutyClient
from arcade_pagerduty.constants import FUZZY_AUTO_ACCEPT_CONFIDENCE
from arcade_pagerduty.models.mappers import map_users_list
from arcade_pagerduty.models.tool_outputs import (
    SearchUsersOutput,
    UsersListOutput,
    UserSummaryOutput,
)
from arcade_pagerduty.utils.auth_utils import get_pagerduty_auth
from arcade_pagerduty.utils.fuzzy import match_users
from arcade_pagerduty.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_users
# API Calls: 1
# APIs Used: GET /users (REST)
# Response Complexity: LOW - user summaries with teams
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Users"
#   readOnlyHint: true       - Only reads users
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=["users.read"],  # /users
    )
)
async def list_users(
    context: Context,
    limit: Annotated[int, "Maximum users to return (1-50). Default is 10."] = 10,
    offset: Annotated[int | None, "Offset for pagination. Default is None."] = None,
) -> Annotated[UsersListOutput, "Users with pagination fields"]:
    """List users."""
    token = context.get_auth_token_or_empty()
    limit = min(50, max(1, limit))
    async with PagerDutyClient(token) as client:
        response = await client.get_users(limit=limit, offset=offset)

    result = map_users_list(response)
    return cast(UsersListOutput, remove_none_values_recursive(result))


# =============================================================================
# search_users
# API Calls: 1+ (paginates through all users)
# APIs Used: GET /users (REST) + local fuzzy matching
# Response Complexity: LOW - fuzzy matches with confidence
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Search Users"
#   readOnlyHint: true       - Only reads users
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=["users.read"],  # /users
    )
)
async def search_users(
    context: Context,
    query: Annotated[str, "Search string to match against user name and email."],
    auto_accept_matches: Annotated[
        bool,
        f"Auto-accept fuzzy matches above {FUZZY_AUTO_ACCEPT_CONFIDENCE} confidence. Default is False",
    ] = False,
) -> Annotated[SearchUsersOutput, "Fuzzy user matches with confidence scores"]:
    """Search users using local fuzzy matching on name/email."""
    token = context.get_auth_token_or_empty()
    all_users: list[UserSummaryOutput] = []
    offset = 0
    limit = 50

    async with PagerDutyClient(token) as client:
        while True:
            response = await client.get_users(limit=limit, offset=offset)
            page = map_users_list(response)
            all_users.extend(page.get("users") or [])
            if not page.get("more"):
                break
            offset += page.get("limit") or limit

    matches, auto_accepted = match_users(all_users, query, auto_accept_matches)

    return cast(
        SearchUsersOutput,
        remove_none_values_recursive({
            "query": query,
            "matches": matches,
            "auto_accepted": auto_accepted,
        }),
    )
