"""
API Gateway instrumentation utilities for Lambda handlers.
Extracts HTTP semantic attributes from API Gateway events (REST API v1 and HTTP API v2).
"""

import json
import re
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from .http_utils import (
    filter_important_headers,
    capture_request_body,
    auto_detect_route_pattern
)
from .http_constants import (
    HTTP_REQUEST_METHOD, HTTP_REQUEST_HEADERS, HTTP_REQUEST_HEADER_TRACEPARENT,
    HTTP_REQUEST_BODY, HTTP_ROUTE, URL_FULL, URL_SCHEME,
    URL_PATH, URL_QUERY, USER_AGENT_ORIGINAL, SERVER_ADDRESS, SERVER_PORT,
    CLIENT_ADDRESS, NETWORK_PROTOCOL_VERSION,
    USER_ID, REBRANDLY_WORKSPACE, REBRANDLY_ORGANIZATION
)


def is_api_gateway_event(event: Any) -> bool:
    """
    Check if the event is from API Gateway (REST v1 or HTTP v2).

    Args:
        event: Lambda event object

    Returns:
        True if the event is from API Gateway
    """
    if not isinstance(event, dict):
        return False
    return bool(
        event.get('httpMethod') or
        event.get('requestContext', {}).get('http', {}).get('method')
    )


def _is_valid_authorizer_value(value: Any) -> bool:
    """
    Check if a value is meaningful (not null/None/"None"/empty).
    Per OpenTelemetry conventions, attributes should only be set when they have meaningful values.
    """
    return value is not None and value != 'None' and value != 'null' and value != ''


def extract_api_gateway_authorizer_attributes(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user and workspace context from API Gateway requestContext.authorizer.
    Only sets attributes when values are present (per OpenTelemetry conventions).

    Args:
        event: API Gateway event object

    Returns:
        Dict with user.id, rebrandly.workspace, rebrandly.organization attributes (only if present)
    """
    attrs = {}
    if not event or not isinstance(event, dict):
        return attrs
    authorizer = event.get('requestContext', {}).get('authorizer', {})

    if not authorizer:
        return attrs

    user_id = authorizer.get('id')
    if _is_valid_authorizer_value(user_id):
        attrs[USER_ID] = str(user_id)

    workspace = authorizer.get('workspace')
    if _is_valid_authorizer_value(workspace):
        attrs[REBRANDLY_WORKSPACE] = str(workspace)

    organization = authorizer.get('organization')
    if _is_valid_authorizer_value(organization):
        attrs[REBRANDLY_ORGANIZATION] = str(organization)

    return attrs


def extract_api_gateway_http_attributes(event: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Extract HTTP semantic attributes from API Gateway event.
    Supports both REST API (v1) and HTTP API (v2) formats.

    Args:
        event: API Gateway event object

    Returns:
        tuple: (attributes_dict, span_name)
    """
    attrs = {}

    # Detect API Gateway v1 (REST) or v2 (HTTP API)
    http_method = event.get('httpMethod') or (
        event.get('requestContext', {}).get('http', {}).get('method')
    )
    if not http_method:
        return attrs, None

    # Extract path
    path = event.get('path') or event.get('rawPath') or (
        event.get('requestContext', {}).get('http', {}).get('path')
    )

    # Get request context
    req_ctx = event.get('requestContext', {})
    headers = event.get('headers') or {}

    # Determine route pattern
    if event.get('resource'):
        route_pattern = event.get('resource')
    elif event.get('routeKey'):
        # HTTP API format (e.g., "GET /users/{id}") - strip the method prefix
        route_pattern = re.sub(r'^[A-Z]+\s+', '', event.get('routeKey'))
    else:
        route_pattern = auto_detect_route_pattern(path) if path else '/'

    # Build query string
    query_params = event.get('queryStringParameters')
    query_string = ''
    if query_params:
        query_string = urlencode(query_params)

    # Extract server details
    domain_name = req_ctx.get('domainName') or headers.get('host') or headers.get('Host')
    protocol = req_ctx.get('protocol') or req_ctx.get('http', {}).get('protocol') or 'HTTP/1.1'

    # Extract client IP (different locations for REST vs HTTP API)
    client_ip = req_ctx.get('identity', {}).get('sourceIp') or req_ctx.get('http', {}).get('sourceIp')

    # Extract user agent (case-insensitive header lookup)
    user_agent = headers.get('user-agent') or headers.get('User-Agent')

    # Set HTTP semantic attributes
    attrs[HTTP_REQUEST_METHOD] = http_method
    attrs[HTTP_ROUTE] = route_pattern
    attrs[URL_PATH] = path
    attrs[URL_SCHEME] = 'https'

    if query_string:
        attrs[URL_QUERY] = query_string

    if domain_name:
        attrs[SERVER_ADDRESS] = domain_name
        attrs[SERVER_PORT] = 443
        full_url = f"https://{domain_name}{path}"
        if query_string:
            full_url += f"?{query_string}"
        attrs[URL_FULL] = full_url

    if client_ip:
        attrs[CLIENT_ADDRESS] = client_ip

    if user_agent:
        attrs[USER_AGENT_ORIGINAL] = user_agent

    if protocol:
        attrs[NETWORK_PROTOCOL_VERSION] = protocol

    # Capture filtered headers (exclude sensitive ones)
    if headers:
        filtered_headers = filter_important_headers(headers)
        if filtered_headers:
            attrs[HTTP_REQUEST_HEADERS] = json.dumps(filtered_headers)
        # Store traceparent for debugging/correlation
        traceparent = headers.get('traceparent') or headers.get('Traceparent')
        if traceparent:
            attrs[HTTP_REQUEST_HEADER_TRACEPARENT] = traceparent

    # Capture request body for POST/PUT/PATCH requests (with redaction)
    body = event.get('body')
    if body and http_method in ['POST', 'PUT', 'PATCH']:
        content_type = headers.get('content-type') or headers.get('Content-Type')
        captured_body = capture_request_body(body, content_type)
        if captured_body:
            attrs[HTTP_REQUEST_BODY] = captured_body

    # Add request context ID for correlation
    if req_ctx.get('requestId'):
        attrs['http.request_id'] = req_ctx.get('requestId')

    # Extract authorizer context (user, workspace, organization)
    authorizer_attrs = extract_api_gateway_authorizer_attributes(event)
    attrs.update(authorizer_attrs)

    # Keep legacy attributes for backward compatibility
    attrs['http.method'] = http_method
    attrs['http.target'] = path + (f"?{query_string}" if query_string else '')
    if domain_name:
        attrs['http.scheme'] = 'https'
        attrs['http.url'] = f"https://{domain_name}{path}" + (f"?{query_string}" if query_string else '')

    # Build span name
    span_name = f"{http_method} {route_pattern}"

    return attrs, span_name


def extract_api_gateway_context(event: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Extract trace context carrier from API Gateway headers.
    Returns a dict with traceparent/tracestate if present.

    Args:
        event: API Gateway event object

    Returns:
        Dict with traceparent/tracestate if present, None otherwise
    """
    if not event or not isinstance(event, dict):
        return None
    headers = event.get('headers')
    if not headers:
        return None

    # Normalize header keys to lowercase
    normalized = {k.lower(): v for k, v in headers.items()}

    carrier = {}
    if 'traceparent' in normalized:
        carrier['traceparent'] = normalized['traceparent']
    if 'tracestate' in normalized:
        carrier['tracestate'] = normalized['tracestate']

    return carrier if carrier else None
