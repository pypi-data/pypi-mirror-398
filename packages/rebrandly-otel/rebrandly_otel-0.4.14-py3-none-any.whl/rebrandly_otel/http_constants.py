"""HTTP semantic attribute constants for OpenTelemetry instrumentation."""

# HTTP Semantic Attributes following OpenTelemetry conventions
# https://opentelemetry.io/docs/specs/semconv/http/http-spans/

HTTP_REQUEST_METHOD = "http.request.method"
HTTP_REQUEST_HEADERS = "http.request.headers"
HTTP_REQUEST_HEADER_TRACEPARENT = "http.request.header.traceparent"
HTTP_REQUEST_BODY = "http.request.body.content"
HTTP_RESPONSE_STATUS_CODE = "http.response.status_code"
HTTP_ROUTE = "http.route"

# URL attributes
URL_FULL = "url.full"
URL_SCHEME = "url.scheme"
URL_PATH = "url.path"
URL_QUERY = "url.query"

# Network attributes
NETWORK_PROTOCOL_VERSION = "network.protocol.version"

# Server attributes
SERVER_ADDRESS = "server.address"
SERVER_PORT = "server.port"

# Client attributes
CLIENT_ADDRESS = "client.address"

# User agent
USER_AGENT_ORIGINAL = "user_agent.original"

# Error attributes
ERROR_TYPE = "error.type"

# User and organization attributes (Rebrandly-specific)
USER_ID = "user.id"
REBRANDLY_WORKSPACE = "rebrandly.workspace"
REBRANDLY_ORGANIZATION = "rebrandly.organization"
