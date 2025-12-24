"""Authentication utilities for PagerDuty toolkit."""

from arcade_mcp_server.auth import PagerDuty

from arcade_pagerduty.constants import USE_SCOPED_OAUTH


def get_pagerduty_auth(scopes: list[str] | None = None) -> PagerDuty:
    """Get PagerDuty authentication configuration.

    When USE_SCOPED_OAUTH is True, returns PagerDuty(scopes=[...])
    with granular scopes for fine-grained access control.

    When USE_SCOPED_OAUTH is False (default, classic mode), returns
    PagerDuty(scopes=[]) with empty scopes array, as classic OAuth apps
    don't require scopes to be specified.

    See: https://developer.pagerduty.com/docs/oauth-functionality

    Args:
        scopes: List of required granular scopes.
                In Scoped OAuth mode: used directly (e.g., ["users.read", "incidents.write"]).
                In Classic OAuth mode: ignored, returns empty scopes array.

    Returns:
        PagerDuty authentication configuration instance.
    """
    if USE_SCOPED_OAUTH:
        return PagerDuty(scopes=scopes or [])

    return PagerDuty(scopes=[])
