"""Incident tools for PagerDuty toolkit."""

from typing import Annotated, cast

from arcade_mcp_server import Context, tool

from arcade_pagerduty.client import PagerDutyClient
from arcade_pagerduty.models.enums import IncidentStatus, IncidentUrgency
from arcade_pagerduty.models.mappers import map_incident_detail, map_incidents_list
from arcade_pagerduty.models.tool_outputs import IncidentDetailOutput, IncidentsListOutput
from arcade_pagerduty.utils.auth_utils import get_pagerduty_auth
from arcade_pagerduty.utils.response_utils import remove_none_values_recursive


# =============================================================================
# list_incidents
# API Calls: 1
# APIs Used: GET /incidents (REST)
# Response Complexity: MEDIUM - list with pagination and filters
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "List Incidents"
#   readOnlyHint: true       - Only reads incidents
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=["incidents.read"],  # /incidents
    )
)
async def list_incidents(
    context: Context,
    status: Annotated[IncidentStatus | None, "Filter by status. Default is None."] = None,
    urgency: Annotated[IncidentUrgency | None, "Filter by urgency. Default is None."] = None,
    service_ids: Annotated[list[str] | None, "Filter by service IDs. Default is None."] = None,
    team_ids: Annotated[list[str] | None, "Filter by team IDs. Default is None."] = None,
    since: Annotated[str | None, "Start time filter ISO 8601 UTC. Default is None."] = None,
    until: Annotated[str | None, "End time filter ISO 8601 UTC. Default is None."] = None,
    limit: Annotated[int, "Maximum incidents to return (1-50). Default is 10."] = 10,
    offset: Annotated[int | None, "Offset for pagination. Default is None."] = None,
) -> Annotated[IncidentsListOutput, "List of incidents with pagination fields"]:
    """List incidents with optional status, urgency, service, team, and time filters."""
    token = context.get_auth_token_or_empty()
    limit = min(50, max(1, limit))
    async with PagerDutyClient(token) as client:
        response = await client.get_incidents(
            statuses=[status] if status else None,
            urgencies=[urgency] if urgency else None,
            service_ids=service_ids,
            team_ids=team_ids,
            since=since,
            until=until,
            limit=limit,
            offset=offset,
        )

    result = map_incidents_list(response)
    return cast(IncidentsListOutput, remove_none_values_recursive(result))


# =============================================================================
# get_incident
# API Calls: 1
# APIs Used: GET /incidents/{id} (REST)
# Response Complexity: MEDIUM - single incident with associations
# -----------------------------------------------------------------------------
# ToolAnnotations:
#   title: "Get Incident"
#   readOnlyHint: true       - Only reads incidents
#   openWorldHint: true      - Interacts with PagerDuty external API
# =============================================================================
@tool(
    requires_auth=get_pagerduty_auth(
        scopes=["incidents.read"],  # /incidents/{id}
    )
)
async def get_incident(
    context: Context,
    incident_id: Annotated[str, "Incident ID to fetch."],
) -> Annotated[IncidentDetailOutput, "Incident details."]:
    """Get a single incident by ID."""
    token = context.get_auth_token_or_empty()
    async with PagerDutyClient(token) as client:
        response = await client.get_incident_by_id(incident_id)

    result = map_incident_detail(response)
    return cast(IncidentDetailOutput, remove_none_values_recursive(result))
