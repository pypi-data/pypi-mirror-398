"""User context tools for PagerDuty toolkit."""

from typing import Annotated, cast

from arcade_mcp_server import Context, tool

from arcade_pagerduty.client import PagerDutyClient
from arcade_pagerduty.models.mappers import map_whoami
from arcade_pagerduty.models.tool_outputs import WhoAmIOutput
from arcade_pagerduty.utils.auth_utils import get_pagerduty_auth
from arcade_pagerduty.utils.response_utils import remove_none_values_recursive


# =============================================================================
# whoami
# API Calls: 2 (1 for user profile, 1 for on-call status)
# APIs Used: GET /users/me, GET /oncalls (REST)
# Response Complexity: MEDIUM - profile with contact methods and notification rules
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "WhoAmI"
#   readOnlyHint: true       - Only reads user data, no modifications
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=[
            "users.read",  # /users/me, notification_rules included
            "users:contact_methods.read",  # contact_methods include
            "teams.read",  # teams include
            "oncalls.read",  # /oncalls
        ],
    )
)
async def whoami(
    context: Context,
) -> Annotated[
    WhoAmIOutput, "Authenticated PagerDuty user profile with contact and notification summaries."
]:
    """Get the authenticated PagerDuty user's profile with contact and notification summaries."""
    token = context.get_auth_token_or_empty()
    oncalls_response = None
    async with PagerDutyClient(token) as client:
        me_data = await client.get_me()
        user_id = me_data.get("user", {}).get("id", "")
        if user_id:
            oncalls_response = await client.get_oncalls(user_ids=[user_id])

    result = map_whoami(me_data, oncalls_response)
    return cast(WhoAmIOutput, remove_none_values_recursive(result))
