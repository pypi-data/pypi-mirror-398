"""PagerDuty REST API client with HTTP/2 support and connection pooling."""

import asyncio
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, ClassVar, cast

import httpx
from arcade_mcp_server.exceptions import FatalToolError, UpstreamError

from arcade_pagerduty.constants import (
    LOCK_ACQUIRE_TIMEOUT_SECONDS,
    PAGERDUTY_API_URL,
    PAGERDUTY_MAX_TIMEOUT_SECONDS,
)
from arcade_pagerduty.models.api_responses import (
    EscalationPoliciesListResponse,
    EscalationPolicySingleResponse,
    IncidentSingleResponse,
    IncidentsListResponse,
    LogEntriesListResponse,
    MeResponse,
    OnCallListResponse,
    SchedulesListResponse,
    ServiceSingleResponse,
    ServicesListResponse,
    TeamSingleResponse,
    TeamsListResponse,
    UsersListResponse,
)
from arcade_pagerduty.models.enums import IncidentStatus, IncidentUrgency


@dataclass
class PagerDutyClient:
    """Client for interacting with PagerDuty REST API.

    Supports HTTP/2, connection pooling, and retry logic for server errors.
    Use as async context manager:
        async with PagerDutyClient(token) as client:
            result = await client.get_me()
    """

    auth_token: str
    base_url: str = PAGERDUTY_API_URL
    timeout_seconds: int = PAGERDUTY_MAX_TIMEOUT_SECONDS

    _clients: ClassVar[dict[str, httpx.AsyncClient]] = {}
    _client_locks: ClassVar[dict[str, asyncio.Lock]] = {}
    _global_lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    _client: httpx.AsyncClient | None = field(default=None, repr=False)

    async def __aenter__(self) -> "PagerDutyClient":
        """Enter async context - get or create pooled HTTP client."""
        self._client = await self._get_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context - client remains pooled for reuse."""
        self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create a pooled HTTP client for the base URL (async-safe)."""
        base_url = self.base_url

        try:
            await asyncio.wait_for(
                self._global_lock.acquire(), timeout=LOCK_ACQUIRE_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError as error:
            raise FatalToolError(
                f"Timeout acquiring global lock after {LOCK_ACQUIRE_TIMEOUT_SECONDS}s"
            ) from error

        try:
            if base_url not in self._client_locks:
                self._client_locks[base_url] = asyncio.Lock()
            lock = self._client_locks[base_url]
        finally:
            self._global_lock.release()

        try:
            await asyncio.wait_for(lock.acquire(), timeout=LOCK_ACQUIRE_TIMEOUT_SECONDS)
        except asyncio.TimeoutError as error:
            raise FatalToolError(
                f"Timeout acquiring client lock after {LOCK_ACQUIRE_TIMEOUT_SECONDS}s"
            ) from error

        try:
            if base_url not in self._clients:
                self._clients[base_url] = httpx.AsyncClient(
                    base_url=base_url,
                    http2=True,
                    headers={
                        "Accept": "application/vnd.pagerduty+json;version=2",
                        "Content-Type": "application/json",
                    },
                    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
                    timeout=self.timeout_seconds,
                )
            return self._clients[base_url]
        finally:
            lock.release()

    @classmethod
    async def close_all(cls) -> None:
        """Close all pooled HTTP clients and clear the pool.

        Call this on application shutdown or in tests to properly clean up resources.
        """
        async with cls._global_lock:
            for client in cls._clients.values():
                await client.aclose()
            cls._clients.clear()
            cls._client_locks.clear()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute HTTP request with retry logic for 5xx server errors only.

        4xx client errors are raised immediately without retry.
        """
        if not self._client:
            raise FatalToolError(
                "Client not initialized. Use 'async with PagerDutyClient() as client:'",
            )

        backoff_delays = [0.3, 0.6, 1.2]

        for attempt, delay in enumerate(backoff_delays):
            try:
                response = await self._client.request(
                    method,
                    endpoint,
                    params=params,
                    json=json,
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                )
                response.raise_for_status()
                try:
                    return cast(dict[str, Any], response.json())
                except (ValueError, TypeError) as json_error:
                    raise UpstreamError(
                        "PagerDuty API returned invalid JSON response",
                        developer_message=f"JSON parse error: {json_error}. Response text: {response.text[:500]}",
                        status_code=response.status_code,
                    ) from json_error
            except httpx.HTTPStatusError as error:
                status = error.response.status_code
                if status >= 500:
                    is_last_attempt = attempt == len(backoff_delays) - 1
                    if not is_last_attempt:
                        await asyncio.sleep(delay)
                        continue
                    _handle_server_error(error)
                raise
            except httpx.RequestError as error:
                raise UpstreamError(
                    f"Failed to connect to PagerDuty API: {error}",
                    developer_message=str(error),
                    status_code=503,
                ) from error

        raise RuntimeError("Retry logic exited unexpectedly without returning or raising.")

    async def get_me(self) -> MeResponse:
        """Get authenticated user information."""
        params = {
            "include[]": [
                "contact_methods",
                "notification_rules",
                "teams",
            ]
        }
        response = await self._request("GET", "/users/me", params=params)
        return cast(MeResponse, response)

    async def get_oncalls(
        self,
        user_ids: list[str] | None = None,
        schedule_ids: list[str] | None = None,
        escalation_policy_ids: list[str] | None = None,
        team_ids: list[str] | None = None,
        limit: int = 10,
        offset: int | None = None,
        time_zone: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> OnCallListResponse:
        """Get on-call entries with optional filters."""
        limit = _clamp_limit(limit)
        params: dict[str, Any] = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        if time_zone:
            params["time_zone"] = time_zone
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        for user_id in user_ids or []:
            params.setdefault("user_ids[]", []).append(user_id)
        for schedule_id in schedule_ids or []:
            params.setdefault("schedule_ids[]", []).append(schedule_id)
        for policy_id in escalation_policy_ids or []:
            params.setdefault("escalation_policy_ids[]", []).append(policy_id)
        for team_id in team_ids or []:
            params.setdefault("team_ids[]", []).append(team_id)

        response = await self._request("GET", "/oncalls", params=params)
        return cast(OnCallListResponse, response)

    async def get_schedules(
        self,
        limit: int = 10,
        offset: int | None = None,
        time_zone: str | None = None,
    ) -> SchedulesListResponse:
        """List schedules."""
        limit = _clamp_limit(limit)
        params: dict[str, Any] = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        if time_zone:
            params["time_zone"] = time_zone

        response = await self._request("GET", "/schedules", params=params)
        return cast(SchedulesListResponse, response)

    async def get_incidents(
        self,
        statuses: list[IncidentStatus] | None = None,
        urgencies: list[IncidentUrgency] | None = None,
        service_ids: list[str] | None = None,
        team_ids: list[str] | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 10,
        offset: int | None = None,
    ) -> IncidentsListResponse:
        """List incidents with filters."""
        limit = _clamp_limit(limit)
        params: dict[str, Any] = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        for status in statuses or []:
            params.setdefault("statuses[]", []).append(status.value)
        for urgency in urgencies or []:
            params.setdefault("urgencies[]", []).append(urgency.value)
        for service_id in service_ids or []:
            params.setdefault("service_ids[]", []).append(service_id)
        for team_id in team_ids or []:
            params.setdefault("team_ids[]", []).append(team_id)
        if since:
            params["since"] = since
        if until:
            params["until"] = until

        response = await self._request("GET", "/incidents", params=params)
        return cast(IncidentsListResponse, response)

    async def get_incident_by_id(self, incident_id: str) -> IncidentSingleResponse:
        """Get a single incident by ID."""
        if not incident_id or "/" in incident_id or "\\" in incident_id:
            raise ValueError("Invalid incident_id: must not contain path separators")
        response = await self._request("GET", f"/incidents/{incident_id}")
        return cast(IncidentSingleResponse, response)

    async def get_services(
        self,
        query: str | None = None,
        limit: int = 10,
        offset: int | None = None,
    ) -> ServicesListResponse:
        """List services with optional name search."""
        limit = _clamp_limit(limit)
        params: dict[str, Any] = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        if query:
            params["query"] = query
        response = await self._request("GET", "/services", params=params)
        return cast(ServicesListResponse, response)

    async def get_service_by_id(self, service_id: str) -> ServiceSingleResponse:
        """Get a single service by ID."""
        if not service_id or "/" in service_id or "\\" in service_id:
            raise ValueError("Invalid service_id: must not contain path separators")
        response = await self._request("GET", f"/services/{service_id}")
        return cast(ServiceSingleResponse, response)

    async def get_users(
        self,
        limit: int = 10,
        offset: int | None = None,
    ) -> UsersListResponse:
        """List users with team information."""
        limit = _clamp_limit(limit)
        params: dict[str, Any] = {"limit": limit, "include[]": ["teams"]}
        if offset is not None:
            params["offset"] = offset
        response = await self._request("GET", "/users", params=params)
        return cast(UsersListResponse, response)

    async def get_escalation_policies(
        self,
        limit: int = 10,
        offset: int | None = None,
    ) -> EscalationPoliciesListResponse:
        """List escalation policies."""
        limit = _clamp_limit(limit)
        params: dict[str, Any] = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        response = await self._request("GET", "/escalation_policies", params=params)
        return cast(EscalationPoliciesListResponse, response)

    async def get_escalation_policy_by_id(
        self,
        policy_id: str,
    ) -> EscalationPolicySingleResponse:
        """Get a single escalation policy by ID."""
        if not policy_id or "/" in policy_id or "\\" in policy_id:
            raise ValueError("Invalid policy_id: must not contain path separators")
        response = await self._request("GET", f"/escalation_policies/{policy_id}")
        return cast(EscalationPolicySingleResponse, response)

    async def get_teams(
        self,
        limit: int = 10,
        offset: int | None = None,
    ) -> TeamsListResponse:
        """List teams."""
        limit = _clamp_limit(limit)
        params: dict[str, Any] = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        response = await self._request("GET", "/teams", params=params)
        return cast(TeamsListResponse, response)

    async def get_team_by_id(
        self,
        team_id: str,
    ) -> TeamSingleResponse:
        """Get a single team by ID with related entities."""
        if not team_id or "/" in team_id or "\\" in team_id:
            raise ValueError("Invalid team_id: must not contain path separators")
        params = {"include[]": ["members", "services", "schedules", "escalation_policies"]}
        response = await self._request("GET", f"/teams/{team_id}", params=params)
        return cast(TeamSingleResponse, response)

    async def get_log_entries(
        self,
        since: str | None = None,
        until: str | None = None,
        team_ids: list[str] | None = None,
        time_zone: str | None = None,
        is_overview: bool = True,
        limit: int = 10,
        offset: int | None = None,
    ) -> LogEntriesListResponse:
        """List log entries (activity feed) across the account."""
        limit = _clamp_limit(limit)
        params: dict[str, Any] = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        if time_zone:
            params["time_zone"] = time_zone
        params["is_overview"] = "true" if is_overview else "false"
        for team_id in team_ids or []:
            params.setdefault("team_ids[]", []).append(team_id)

        response = await self._request("GET", "/log_entries", params=params)
        return cast(LogEntriesListResponse, response)


def _handle_server_error(error: httpx.HTTPStatusError) -> None:
    """Handle 5xx server errors from PagerDuty API after retry exhaustion."""
    status = error.response.status_code
    try:
        body = error.response.json()
        message = body.get("error", {}).get("message", f"HTTP {status}")
    except (ValueError, TypeError, KeyError):
        message = f"HTTP {status}"

    raise UpstreamError(
        f"PagerDuty API server error: {message}",
        developer_message=f"PagerDuty API {status}: {error.response.text}",
        status_code=status,
    ) from error


def _clamp_limit(limit: int) -> int:
    """Clamp limit to PagerDuty bounds (1-50)."""
    return min(50, max(1, limit))
