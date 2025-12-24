"""Service tools for PagerDuty toolkit."""

from typing import Annotated, cast

from arcade_mcp_server import Context, tool

from arcade_pagerduty.client import PagerDutyClient
from arcade_pagerduty.models.mappers import map_service_detail, map_services_list
from arcade_pagerduty.models.tool_outputs import ServiceDetailOutput, ServicesListOutput
from arcade_pagerduty.utils.auth_utils import get_pagerduty_auth
from arcade_pagerduty.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_services
# API Calls: 1
# APIs Used: GET /services (REST)
# Response Complexity: LOW - list of services
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Services"
#   readOnlyHint: true       - Only reads services
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=["services.read"],  # /services
    )
)
async def list_services(
    context: Context,
    query: Annotated[str | None, "Search services by name. Default is None."] = None,
    limit: Annotated[int, "Maximum services to return (1-50). Default is 10."] = 10,
    offset: Annotated[int | None, "Offset for pagination. Default is None."] = None,
) -> Annotated[ServicesListOutput, "List of services with pagination fields"]:
    """List services with optional name search."""
    token = context.get_auth_token_or_empty()
    limit = min(50, max(1, limit))
    async with PagerDutyClient(token) as client:
        response = await client.get_services(query=query, limit=limit, offset=offset)

    result = map_services_list(response)
    return cast(ServicesListOutput, remove_none_values_recursive(result))


# =============================================================================
# get_service
# API Calls: 1
# APIs Used: GET /services/{id} (REST)
# Response Complexity: LOW - single service
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Service"
#   readOnlyHint: true       - Only reads services
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=["services.read"],  # /services/{id}
    )
)
async def get_service(
    context: Context,
    service_id: Annotated[str, "Service ID to fetch."],
) -> Annotated[ServiceDetailOutput, "Service details."]:
    """Get a single service by ID."""
    token = context.get_auth_token_or_empty()
    async with PagerDutyClient(token) as client:
        response = await client.get_service_by_id(service_id)

    result = map_service_detail(response)
    return cast(ServiceDetailOutput, remove_none_values_recursive(result))
