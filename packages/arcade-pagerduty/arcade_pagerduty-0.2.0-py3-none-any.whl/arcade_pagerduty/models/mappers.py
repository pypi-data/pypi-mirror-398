"""Mappers from PagerDuty API responses to tool outputs."""

from datetime import datetime, timezone
from typing import cast

from typing_extensions import TypedDict

from arcade_pagerduty.models.api_responses import (
    EscalationPoliciesListResponse,
    EscalationPolicyData,
    EscalationPolicySingleResponse,
    IncidentData,
    IncidentSingleResponse,
    IncidentsListResponse,
    LogEntriesListResponse,
    LogEntryData,
    MeResponse,
    OnCallData,
    OnCallListResponse,
    Reference,
    ScheduleData,
    SchedulesListResponse,
    ServiceData,
    ServiceSingleResponse,
    ServicesListResponse,
    TeamData,
    TeamSingleResponse,
    TeamsListResponse,
    UserData,
    UsersListResponse,
)
from arcade_pagerduty.models.tool_outputs import (
    AssignmentOutput,
    ContactMethodsSummaryOutput,
    EscalationLevelOutput,
    EscalationPoliciesListOutput,
    EscalationPolicyDetailOutput,
    EscalationPolicySummaryOutput,
    EscalationTargetOutput,
    IncidentDetailOutput,
    IncidentsListOutput,
    IncidentSummaryOutput,
    LogEntriesListOutput,
    LogEntryOutput,
    NotificationRulesSummaryOutput,
    OnCallEntryOutput,
    OnCallsListOutput,
    OnCallUserOutput,
    ReferenceOutput,
    ScheduleOutput,
    SchedulesListOutput,
    ServiceDetailOutput,
    ServicesListOutput,
    ServiceSummaryOutput,
    TeamDetailOutput,
    TeamMemberOutput,
    TeamsListOutput,
    TeamSummaryOutput,
    TeamSummaryWithPolicyOutput,
    UsersListOutput,
    UserSummaryOutput,
    WhoAmIOutput,
)


def map_whoami(
    response: MeResponse, oncalls_response: OnCallListResponse | None = None
) -> WhoAmIOutput:
    """Map GET /users/me response to WhoAmIOutput."""
    user: UserData = cast(UserData, (response or {}).get("user", {}))
    oncalls = (
        cast(list[OnCallData], oncalls_response.get("oncalls", []) or [])
        if oncalls_response
        else []
    )

    teams = _map_teams(user)
    contact_methods = _summarize_contact_methods(user)
    notification_rules = _summarize_notification_rules(user)
    oncall_info = _compute_oncall(oncalls)

    return {
        "id": user.get("id", ""),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role"),
        "job_title": user.get("job_title"),
        "time_zone": user.get("time_zone"),
        "html_url": user.get("html_url"),
        "teams": teams,
        "contact_methods": contact_methods,
        "notification_rules": notification_rules,
        "is_on_call_now": oncall_info["is_on_call_now"],
        "next_on_call_start": oncall_info["next_on_call_start"],
        "next_on_call_end": oncall_info["next_on_call_end"],
    }


def _map_teams(user: UserData) -> list[TeamSummaryOutput]:
    teams: list[TeamSummaryOutput] = []
    for team in user.get("teams", []) or []:
        teams.append({
            "id": team.get("id", ""),
            "name": team.get("summary") or team.get("id", ""),
        })
    return teams


def _summarize_contact_methods(user: UserData) -> ContactMethodsSummaryOutput:
    contact_methods: ContactMethodsSummaryOutput = {
        "email_addresses": [],
        "phone_numbers": [],
        "push_devices": [],
    }
    for method in user.get("contact_methods", []) or []:
        method_type = (method.get("type") or "").lower()
        address = method.get("address") or ""
        label = method.get("label") or ""
        if "email" in method_type and address:
            contact_methods["email_addresses"].append(address)
        elif ("phone" in method_type or "sms" in method_type) and address:
            contact_methods["phone_numbers"].append(address)
        elif "push" in method_type:
            contact_methods["push_devices"].append(label or address)
    return contact_methods


def _summarize_notification_rules(user: UserData) -> NotificationRulesSummaryOutput:
    rule_channels: list[str] = []
    for rule in user.get("notification_rules", []) or []:
        rule_type = (rule.get("type") or "").lower()
        contact_method = rule.get("contact_method", {})
        contact_type = (contact_method.get("type") or "").lower()
        if contact_type:
            rule_channels.append(contact_type)
        elif rule_type:
            rule_channels.append(rule_type)

    return {
        "rule_count": len(user.get("notification_rules", []) or []),
        "channels": sorted(set(rule_channels)),
    }


class OnCallStatus(TypedDict):
    """On-call status summary."""

    is_on_call_now: bool
    next_on_call_start: str | None
    next_on_call_end: str | None


def _compute_oncall(oncalls: list[OnCallData]) -> OnCallStatus:
    now = datetime.now(timezone.utc)
    current_on_call = False
    future_starts: list[tuple[datetime, str, str | None]] = []

    for entry in oncalls or []:
        start_str = entry.get("start")
        end_str = entry.get("end")
        if not start_str or not end_str:
            continue
        start_dt = _parse_ts(start_str)
        end_dt = _parse_ts(end_str)
        if not start_dt or not end_dt:
            continue
        if start_dt <= now < end_dt:
            current_on_call = True
        elif start_dt > now:
            future_starts.append((start_dt, start_str, end_str))

    next_start = None
    next_end = None
    if future_starts:
        future_starts.sort(key=lambda item: item[0])
        _, next_start, next_end = future_starts[0]

    return {
        "is_on_call_now": current_on_call,
        "next_on_call_start": next_start,
        "next_on_call_end": next_end,
    }


def map_incident(incident: IncidentData) -> IncidentSummaryOutput:
    """Map an incident record to summary output."""
    service = _ref_to_output(incident.get("service"))
    escalation = _ref_to_output(incident.get("escalation_policy"))
    team = _first_team(incident.get("teams"))
    priority = None
    if incident.get("priority"):
        priority = incident["priority"].get("name") or incident["priority"].get("summary")

    assignments: list[AssignmentOutput] = []
    for assignment in incident.get("assignments", []) or []:
        assignee_ref = _ref_to_output((assignment or {}).get("assignee"))
        if assignee_ref:
            assignments.append({"assignee": assignee_ref})

    return {
        "id": incident.get("id", ""),
        "title": incident.get("summary"),
        "status": incident.get("status"),
        "urgency": incident.get("urgency"),
        "priority": priority,
        "service": service,
        "team": team,
        "escalation_policy": escalation,
        "assignments": assignments,
        "html_url": incident.get("html_url"),
        "created_at": incident.get("created_at"),
        "last_status_change_at": incident.get("last_status_change_at"),
        "resolved_at": incident.get("resolved_at"),
    }


def map_incidents_list(response: IncidentsListResponse) -> IncidentsListOutput:
    """Map list incidents response."""
    incidents = [map_incident(item) for item in response.get("incidents", []) or []]
    return {
        "incidents": incidents,
        "limit": response.get("limit"),
        "offset": response.get("offset"),
        "more": response.get("more"),
    }


def map_incident_detail(response: IncidentSingleResponse) -> IncidentDetailOutput:
    """Map single incident response."""
    incident = response.get("incident", {}) or {}
    return cast(IncidentDetailOutput, map_incident(incident))


def map_oncalls_list(response: OnCallListResponse) -> OnCallsListOutput:
    """Map list on-calls response."""
    entries: list[OnCallEntryOutput] = []
    for item in response.get("oncalls", []) or []:
        user = item.get("user", {}) or {}
        entries.append({
            "user": _map_oncall_user(user),
            "escalation_policy_id": (item.get("escalation_policy") or {}).get("id"),
            "escalation_policy_name": (item.get("escalation_policy") or {}).get("summary"),
            "schedule_id": (item.get("schedule") or {}).get("id"),
            "schedule_name": (item.get("schedule") or {}).get("summary"),
            "level": item.get("level"),
            "start": item.get("start"),
            "end": item.get("end"),
        })

    return {
        "oncalls": entries,
        "limit": response.get("limit"),
        "offset": response.get("offset"),
        "more": response.get("more"),
    }


def map_schedules_list(response: SchedulesListResponse) -> SchedulesListOutput:
    """Map list schedules response."""
    schedules: list[ScheduleOutput] = []
    for item_obj in response.get("schedules", []) or []:
        item = cast(ScheduleData, item_obj)
        users: list[OnCallUserOutput] = []
        for user_obj in item.get("users", []) or []:
            users.append(_map_oncall_user(cast(UserData, user_obj)))
        schedules.append({
            "id": item.get("id", "") or "",
            "name": cast(str, (item.get("name") or item.get("summary") or "")),
            "time_zone": item.get("time_zone") or "",
            "html_url": item.get("html_url") or "",
            "current_oncalls": users,
        })

    return {
        "schedules": schedules,
        "limit": response.get("limit"),
        "offset": response.get("offset"),
        "more": response.get("more"),
    }


def _map_oncall_user(user: UserData) -> OnCallUserOutput:
    return {
        "id": user.get("id", "") or "",
        "name": cast(str, (user.get("name") or user.get("summary") or "")),
        "email": user.get("email"),
    }


def map_users_list(response: UsersListResponse) -> UsersListOutput:
    """Map list users response."""
    users: list[UserSummaryOutput] = []
    for user_obj in response.get("users", []) or []:
        user = cast(UserData, user_obj)
        users.append({
            "id": user.get("id", "") or "",
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "job_title": user.get("job_title"),
            "time_zone": user.get("time_zone"),
            "teams": _map_teams(user),
            "html_url": user.get("html_url"),
        })

    return {
        "users": users,
        "limit": response.get("limit"),
        "offset": response.get("offset"),
        "more": response.get("more"),
    }


def map_escalation_policies_list(
    response: EscalationPoliciesListResponse,
) -> EscalationPoliciesListOutput:
    """Map list escalation policies response."""
    policies: list[EscalationPolicySummaryOutput] = []
    for policy_obj in response.get("escalation_policies", []) or []:
        policy = cast(EscalationPolicyData, policy_obj)
        team_ref = _first_team(cast(list[Reference] | None, policy.get("teams")))
        levels: list[EscalationLevelOutput] = []
        for idx, rule in enumerate(policy.get("escalation_rules", []) or [], start=1):
            targets = [
                _map_target(cast(dict[str, object], t)) for t in rule.get("targets", []) or []
            ]
            targets_summary = ", ".join([
                t["name"] or t["id"] for t in targets if t.get("name") or t.get("id")
            ])
            levels.append({
                "level": idx,
                "targets": targets,
                "targets_summary": targets_summary or None,
            })
        policies.append({
            "id": policy.get("id", "") or "",
            "name": policy.get("name"),
            "description": policy.get("description"),
            "team": team_ref,
            "levels": levels,
            "html_url": policy.get("html_url"),
        })

    return {
        "policies": policies,
        "limit": response.get("limit"),
        "offset": response.get("offset"),
        "more": response.get("more"),
    }


def map_escalation_policy_detail(
    response: EscalationPolicySingleResponse,
) -> EscalationPolicyDetailOutput:
    """Map single escalation policy response."""
    policy = cast(EscalationPolicyData, response.get("escalation_policy", {}) or {})
    team_ref = _first_team(cast(list[Reference] | None, policy.get("teams")))
    levels: list[EscalationLevelOutput] = []
    for idx, rule in enumerate(policy.get("escalation_rules", []) or [], start=1):
        targets = [_map_target(cast(dict[str, object], t)) for t in rule.get("targets", []) or []]
        targets_summary = ", ".join([
            t["name"] or t["id"] for t in targets if t.get("name") or t.get("id")
        ])
        levels.append({
            "level": idx,
            "targets": targets,
            "targets_summary": targets_summary or None,
        })

    escalation_delay = None
    if policy.get("escalation_rules"):
        first_rule = policy["escalation_rules"][0]
        escalation_delay = first_rule.get("escalation_delay_in_minutes")

    return {
        "id": policy.get("id", "") or "",
        "name": policy.get("name"),
        "description": policy.get("description"),
        "html_url": policy.get("html_url"),
        "team": team_ref,
        "repeat_count": policy.get("num_loops"),
        "escalation_delay": escalation_delay,
        "levels": levels,
    }


def map_teams_list(response: TeamsListResponse) -> TeamsListOutput:
    """Map list teams response."""
    teams: list[TeamSummaryWithPolicyOutput] = []
    for team_obj in response.get("teams", []) or []:
        team = cast(TeamData, team_obj)
        default_policy = team.get("default_escalation_policy") or {}
        teams.append({
            "id": team.get("id", "") or "",
            "name": team.get("name"),
            "html_url": team.get("html_url"),
            "default_escalation_policy_id": default_policy.get("id"),
            "default_escalation_policy_name": default_policy.get("summary")
            or default_policy.get("name"),
        })

    return {
        "teams": teams,
        "limit": response.get("limit"),
        "offset": response.get("offset"),
        "more": response.get("more"),
    }


def map_team_detail(response: TeamSingleResponse) -> TeamDetailOutput:
    """Map single team response."""
    team = cast(TeamData, response.get("team", {}) or {})
    default_policy = team.get("default_escalation_policy") or {}
    members: list[TeamMemberOutput] = []
    for member in team.get("members", []) or []:
        member_user = cast(dict[str, object], member.get("user") or member)
        members.append({
            "id": cast(str, member_user.get("id", "") or ""),
            "name": cast(str | None, member_user.get("name")),
            "role": cast(str | None, member_user.get("role")),
            "email": cast(str | None, member_user.get("email")),
        })

    def _map_refs(refs: list[dict[str, object]] | None) -> list[ReferenceOutput]:
        items: list[ReferenceOutput] = []
        for ref in refs or []:
            items.append({
                "id": cast(str, ref.get("id", "") or ""),
                "name": cast(str, ref.get("summary") or ref.get("name") or ""),
                "html_url": cast(str | None, ref.get("html_url")),
            })
        return items

    return {
        "id": team.get("id", "") or "",
        "name": team.get("name"),
        "description": team.get("description"),
        "html_url": team.get("html_url"),
        "default_escalation_policy_id": default_policy.get("id"),
        "default_escalation_policy_name": default_policy.get("summary")
        or default_policy.get("name"),
        "members": members,
        "schedules": _map_refs(cast(list[dict[str, object]] | None, team.get("schedules"))),
        "services": _map_refs(cast(list[dict[str, object]] | None, team.get("services"))),
    }


def _map_target(target: dict[str, object]) -> EscalationTargetOutput:
    return {
        "id": cast(str, target.get("id", "") or ""),
        "name": cast(str, target.get("summary") or target.get("id") or ""),
        "type": cast(str | None, target.get("type")),
    }


def _ref_to_output(ref_obj: Reference | None) -> ReferenceOutput | None:
    if not ref_obj:
        return None
    return {
        "id": ref_obj.get("id", ""),
        "name": ref_obj.get("summary") or ref_obj.get("id", ""),
        "html_url": ref_obj.get("html_url"),
    }


def _first_team(teams: list[Reference] | None) -> ReferenceOutput | None:
    if not teams:
        return None
    return _ref_to_output(teams[0])


def map_service(service: ServiceData) -> ServiceSummaryOutput:
    """Map service to summary output."""
    escalation = _ref_to_output(service.get("escalation_policy"))
    team = _first_team(service.get("teams"))
    return {
        "id": service.get("id", ""),
        "name": service.get("name"),
        "status": service.get("status"),
        "escalation_policy": escalation,
        "team": team,
        "html_url": service.get("html_url"),
    }


def map_services_list(response: ServicesListResponse) -> ServicesListOutput:
    """Map list services response."""
    services = [map_service(item) for item in response.get("services", []) or []]
    return {
        "services": services,
        "limit": response.get("limit"),
        "offset": response.get("offset"),
        "more": response.get("more"),
    }


def map_service_detail(response: ServiceSingleResponse) -> ServiceDetailOutput:
    """Map single service response."""
    service = response.get("service", {}) or {}
    return cast(ServiceDetailOutput, map_service(service))


def _parse_ts(value: str | None) -> datetime | None:
    """Parse ISO 8601 timestamp to datetime in UTC."""
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except ValueError:
        return None


def map_log_entries_list(response: LogEntriesListResponse) -> LogEntriesListOutput:
    """Map list log entries response."""
    entries: list[LogEntryOutput] = []
    for item_obj in response.get("log_entries", []) or []:
        item = cast(LogEntryData, item_obj)
        incident = item.get("incident")
        service = item.get("service")
        agent = item.get("agent")

        entry: LogEntryOutput = {
            "id": item.get("id", "") or "",
            "type": item.get("type", "") or "",
            "summary": item.get("summary", "") or "",
            "created_at": item.get("created_at", "") or "",
        }

        if incident:
            entry["incident"] = {
                "id": incident.get("id", "") or "",
                "name": incident.get("summary") or incident.get("id", ""),
            }

        if service:
            entry["service"] = {
                "id": service.get("id", "") or "",
                "name": service.get("summary") or service.get("id", ""),
            }

        if agent:
            entry["user"] = {
                "id": agent.get("id", "") or "",
                "name": agent.get("summary") or agent.get("id", ""),
            }

        entries.append(entry)

    result: LogEntriesListOutput = {"log_entries": entries}
    if response.get("limit") is not None:
        result["limit"] = response["limit"]
    if response.get("offset") is not None:
        result["offset"] = response["offset"]
    if response.get("more") is not None:
        result["more"] = response["more"]

    return result
