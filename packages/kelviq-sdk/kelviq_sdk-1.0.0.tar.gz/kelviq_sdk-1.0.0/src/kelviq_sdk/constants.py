# kelviq/constants.py

from typing import Literal

# Defines the allowed choices for the 'behaviour' parameter in usage reporting.
# 'SET': Indicates that the reported value is an absolute value.
# 'DELTA': Indicates that the reported value is a change increment to a previous value.
BEHAVIOUR_CHOICES = Literal['SET', 'DELTA']

# For example:
API_BASE_PATH_PREFIX = "/api"
DEFAULT_API_VERSION = "v1"
MAX_RETRIES = 3



API_URLS = {
    "prod": "https://api.kelviq.com",
    "staging": "https://stagingapi.kelviq.com",
    "sandbox": "https://sandboxapi.kelviq.com",
}

# Environment-specific URLs for the edge API
EDGE_API_URLS = {
    "prod": "https://edge.api.kelviq.com",
    "staging": "https://edge.stagingapi.kelviq.com",
    "sandbox": "https://edge.sandboxapi.kelviq.com",
}

# Default values for backward compatibility and convenience.
# These point to the production environment.
DEFAULT_API_URL = API_URLS["prod"]
EDGE_API_URL = EDGE_API_URLS["prod"]