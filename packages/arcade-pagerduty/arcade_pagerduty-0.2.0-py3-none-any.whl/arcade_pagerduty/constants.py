"""Constants for PagerDuty toolkit configuration."""

import os

PAGERDUTY_API_URL = "https://api.pagerduty.com"
PAGERDUTY_APP_URL = "https://app.pagerduty.com"

# Authentication mode: True = Scoped OAuth (granular), False = Classic OAuth (read/write)
# Scoped OAuth uses granular scopes like users.read, incidents.read, etc.
# Classic OAuth uses broad "read" or "write" scopes.
# See: https://developer.pagerduty.com/docs/oauth-functionality
USE_SCOPED_OAUTH = False

try:
    PAGERDUTY_MAX_TIMEOUT_SECONDS = int(os.getenv("PAGERDUTY_MAX_TIMEOUT_SECONDS", 30))
except ValueError:
    PAGERDUTY_MAX_TIMEOUT_SECONDS = 30

LOCK_ACQUIRE_TIMEOUT_SECONDS = 60.0

# Fuzzy matching constants
FUZZY_MATCH_THRESHOLD = 0.60  # Minimum confidence to include in results
FUZZY_AUTO_ACCEPT_CONFIDENCE = 0.90  # Auto-accept threshold when enabled
DISABLE_AUTO_ACCEPT_THRESHOLD = 1.01  # Impossible threshold to disable auto-accept
MAX_FUZZY_SUGGESTIONS = 10  # Max suggestions to return
