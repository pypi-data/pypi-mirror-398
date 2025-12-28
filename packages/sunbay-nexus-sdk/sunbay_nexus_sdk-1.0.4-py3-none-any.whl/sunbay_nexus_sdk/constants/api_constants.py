"""
API-related constants for Sunbay Nexus SDK.
"""

DEFAULT_BASE_URL: str = "https://open.sunbay.us"

# Timeouts are expressed in seconds for the requests library.
DEFAULT_CONNECT_TIMEOUT: float = 30.0
DEFAULT_READ_TIMEOUT: float = 60.0

# Maximum retry attempts for idempotent GET requests.
DEFAULT_MAX_RETRIES: int = 3

# Connection pool related settings (approximate mapping from Java defaults).
DEFAULT_MAX_CONNECTIONS: int = 200

# API response success code.
RESPONSE_SUCCESS_CODE: str = "0"

# HTTP status ranges.
HTTP_STATUS_OK_START: int = 200
HTTP_STATUS_OK_END: int = 300
HTTP_STATUS_CLIENT_ERROR_START: int = 400
HTTP_STATUS_CLIENT_ERROR_END: int = 500
HTTP_STATUS_SERVER_ERROR_START: int = 500

# Header names.
HEADER_AUTHORIZATION: str = "Authorization"
HEADER_REQUEST_ID: str = "X-Client-Request-Id"
HEADER_TIMESTAMP: str = "X-Timestamp"
HEADER_CONTENT_TYPE: str = "Content-Type"
HEADER_USER_AGENT: str = "User-Agent"

AUTHORIZATION_BEARER_PREFIX: str = "Bearer "
CONTENT_TYPE_JSON: str = "application/json"

# API path prefixes.
SEMI_INTEGRATION_PREFIX: str = "/v1/semi-integration"
COMMON_PREFIX: str = "/v1"

# Semi-integration transaction API paths.
PATH_SALE: str = f"{SEMI_INTEGRATION_PREFIX}/transaction/sale"
PATH_AUTH: str = f"{SEMI_INTEGRATION_PREFIX}/transaction/auth"
PATH_FORCED_AUTH: str = f"{SEMI_INTEGRATION_PREFIX}/transaction/forced-auth"
PATH_INCREMENTAL_AUTH: str = f"{SEMI_INTEGRATION_PREFIX}/transaction/incremental-auth"
PATH_POST_AUTH: str = f"{SEMI_INTEGRATION_PREFIX}/transaction/post-auth"
PATH_REFUND: str = f"{SEMI_INTEGRATION_PREFIX}/transaction/refund"
PATH_VOID: str = f"{SEMI_INTEGRATION_PREFIX}/transaction/void"
PATH_ABORT: str = f"{SEMI_INTEGRATION_PREFIX}/transaction/abort"
PATH_TIP_ADJUST: str = f"{SEMI_INTEGRATION_PREFIX}/transaction/tip-adjust"
PATH_QUERY: str = f"{COMMON_PREFIX}/transaction/query"

# Semi-integration settlement API paths.
PATH_BATCH_CLOSE: str = f"{SEMI_INTEGRATION_PREFIX}/settlement/batch-close"


