# http_utils.py
"""Shared HTTP utilities for Rebrandly OTEL SDK."""

import os
import json
import re
from typing import Any, Dict, Optional

from opentelemetry import context, propagate


# ============================================
# CONSTANTS
# ============================================

# Sensitive field names to redact from request bodies (case-insensitive matching)
SENSITIVE_FIELD_NAMES = [
    'password',
    'passwd',
    'pwd',
    'token',
    'access_token',
    'accesstoken',
    'refresh_token',
    'refreshtoken',
    'auth_token',
    'authtoken',
    'apikey',
    'api_key',
    'api-key',
    'secret',
    'client_secret',
    'clientsecret',
    'authorization',
    'creditcard',
    'credit_card',
    'cardnumber',
    'card_number',
    'cvv',
    'cvc',
    'ssn',
    'social_security',
    'socialsecurity'
]

# Content types that should be captured (JSON only)
CAPTURABLE_CONTENT_TYPES = [
    'application/json',
    'application/ld+json',
    'application/vnd.api+json'
]


# ============================================
# ROUTE PATTERN DETECTION
# ============================================

def auto_detect_route_pattern(path: str) -> str:
    """
    Automatically detect and normalize route patterns using heuristics.
    Replaces common ID patterns (UUIDs, hex strings, numeric IDs) with placeholders.

    Critical for maintaining low cardinality in telemetry data per OpenTelemetry spec.

    Args:
        path: The actual request path (e.g., '/users/550e8400-e29b-41d4-a716-446655440000')

    Returns:
        str: Normalized route pattern (e.g., '/users/{id}')

    Example:
        auto_detect_route_pattern('/users/550e8400-e29b-41d4-a716-446655440000')
        # Returns: '/users/{id}'

        auto_detect_route_pattern('/templates/0301fb0436d949979b6688a5c6d91e8f/schedule')
        # Returns: '/templates/{id}/schedule'
    """
    pattern = path

    # Replace UUIDs (8-4-4-4-12 hex format)
    # Example: /users/550e8400-e29b-41d4-a716-446655440000/posts -> /users/{id}/posts
    pattern = re.sub(
        r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(/|$)',
        r'/{id}\1', pattern, flags=re.IGNORECASE
    )

    # Replace 32-character hex strings (MongoDB ObjectId without dashes)
    # Example: /templates/0301fb0436d949979b6688a5c6d91e8f/schedule -> /templates/{id}/schedule
    pattern = re.sub(r'/[0-9a-f]{32}(/|$)', r'/{id}\1', pattern, flags=re.IGNORECASE)

    # Replace 24-character hex strings (MongoDB ObjectId)
    # Example: /users/507f1f77bcf86cd799439011/posts -> /users/{id}/posts
    pattern = re.sub(r'/[0-9a-f]{24}(/|$)', r'/{id}\1', pattern, flags=re.IGNORECASE)

    # Replace 40-character hex strings (SHA-1 hashes)
    pattern = re.sub(r'/[0-9a-f]{40}(/|$)', r'/{id}\1', pattern, flags=re.IGNORECASE)

    # Replace other long hex strings (16+ chars)
    pattern = re.sub(r'/[0-9a-f]{16,}(/|$)', r'/{id}\1', pattern, flags=re.IGNORECASE)

    # Replace numeric IDs (4+ digits, but not version numbers like /v1, /v2)
    # Example: /users/12345/posts -> /users/{id}/posts
    pattern = re.sub(r'/(\d{4,})(/|$)', r'/{id}\2', pattern)

    # Replace shorter numeric IDs in typical ID positions (after nouns)
    # Example: /items/123/details -> /items/{id}/details
    # But preserve /v1, /v2, /api/v1, etc.
    def replace_short_ids(match):
        noun, num, trailing = match.groups()
        # Don't replace version numbers
        if noun in ('v', 'api'):
            return match.group(0)
        return f'/{noun}/{{id}}{trailing}'

    pattern = re.sub(r'/([\w-]+)/(\d{1,3})(/|$)', replace_short_ids, pattern)

    return pattern


def reconstruct_route_pattern(path: str, params: Dict[str, Any]) -> str:
    """
    Reconstruct route pattern from actual path and extracted params.
    Replaces parameter values with their keys to create a low-cardinality template.

    Args:
        path: The actual request path (e.g., '/users/123/posts/456')
        params: Route params dict (e.g., {'user_id': '123', 'post_id': '456'})

    Returns:
        str: Route pattern (e.g., '/users/{user_id}/posts/{post_id}')

    Example:
        reconstruct_route_pattern('/users/123/posts/456', {'user_id': '123', 'post_id': '456'})
        # Returns: '/users/{user_id}/posts/{post_id}'
    """
    if not params:
        return path

    pattern = path

    # Sort by value length descending to avoid partial replacements
    sorted_params = sorted(
        params.items(),
        key=lambda x: -len(str(x[1])) if x[1] is not None else 0
    )

    for key, value in sorted_params:
        if value is not None:
            # Use word boundaries to avoid partial replacements
            pattern = re.sub(
                rf'/{re.escape(str(value))}(/|$)',
                rf'/{{{key}}}\1',
                pattern
            )

    return pattern


def strip_query_params(url_or_path: str) -> str:
    """
    Strip query parameters from a URL path.
    Critical for maintaining low cardinality in span names per OpenTelemetry spec.

    Args:
        url_or_path: URL or path string (may include query params)

    Returns:
        str: Path without query parameters

    Example:
        strip_query_params('/jobs?status=active')  # Returns: '/jobs'
        strip_query_params('/users')               # Returns: '/users'
    """
    if not url_or_path or not isinstance(url_or_path, str):
        return '/'

    if not url_or_path.strip():
        return '/'

    try:
        from urllib.parse import urlparse

        # Handle full URLs
        if url_or_path.startswith('http://') or url_or_path.startswith('https://'):
            parsed = urlparse(url_or_path)
            return parsed.path or '/'

        # Handle paths - split on '?'
        question_mark_index = url_or_path.find('?')
        if question_mark_index == -1:
            return url_or_path

        path_only = url_or_path[:question_mark_index]
        return path_only or '/'
    except Exception:
        # Fallback
        question_mark_index = url_or_path.find('?')
        if question_mark_index == -1:
            return url_or_path
        path_only = url_or_path[:question_mark_index]
        return path_only or '/'


# ============================================
# DOMAIN DETECTION FOR AUTOMATIC INSTRUMENTATION
# ============================================

def is_rebrandly_domain(url: str) -> bool:
    """
    Check if a URL belongs to a Rebrandly domain that should be automatically instrumented.
    Matches api.rebrandly.com, api.test.rebrandly.com, and any subdomain of rebrandly.com.

    Args:
        url: Full URL or hostname to check

    Returns:
        bool: True if URL is a Rebrandly domain

    Example:
        is_rebrandly_domain('https://api.rebrandly.com/v1/links')  # True
        is_rebrandly_domain('api.rebrandly.com')  # True
        is_rebrandly_domain('api.test.rebrandly.com')  # True
        is_rebrandly_domain('internal.rebrandly.com')  # True
        is_rebrandly_domain('https://example.com/api')  # False
        is_rebrandly_domain('localhost')  # False
    """
    if not url or not isinstance(url, str):
        return False

    try:
        from urllib.parse import urlparse

        # Extract hostname from full URL or direct hostname
        if url.startswith('http://') or url.startswith('https://'):
            parsed = urlparse(url)
            hostname = parsed.hostname
        else:
            # Parse hostname from path-like string (e.g., "api.rebrandly.com/v1/links")
            hostname = url.split('/')[0].split(':')[0]

        if not hostname:
            return False

        # Exclude localhost and loopback addresses
        if hostname in ('localhost', '127.0.0.1'):
            return False

        # Check exact matches for primary domains
        if hostname in ('api.rebrandly.com', 'api.test.rebrandly.com'):
            return True

        # Check for any subdomain of rebrandly.com
        if hostname.endswith('.rebrandly.com'):
            return True

        return False
    except Exception as e:
        # If URL parsing fails, return False to avoid breaking requests
        print(f'[Rebrandly OTEL] Domain detection failed for URL: {url}, {str(e)}')
        return False


def is_auto_domain_instrumentation_enabled() -> bool:
    """
    Check if automatic domain instrumentation is enabled via environment variable.
    Enabled by default (opt-out model). Can be disabled by setting OTEL_INSTRUMENT_REBRANDLY_DOMAINS=false.

    Returns:
        bool: True if automatic instrumentation is enabled

    Example:
        # Default behavior (enabled)
        is_auto_domain_instrumentation_enabled()  # True

        # Disabled via environment variable
        os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = 'false'
        is_auto_domain_instrumentation_enabled()  # False
    """
    env_value = os.environ.get('OTEL_INSTRUMENT_REBRANDLY_DOMAINS', '').lower()

    # If not set, default to enabled
    if not env_value:
        return True

    # Check for false values
    return env_value not in ('false', '0', 'no')


def should_inject_trace_context(url: str, options: Optional[Dict[str, Any]] = None) -> bool:
    """
    Determine if trace context should be injected for a given URL.
    Combines domain detection with environment configuration and per-request opt-out.

    Args:
        url: URL to check
        options: Request options dict (may contain skip_tracing flag)

    Returns:
        bool: True if trace context should be injected

    Example:
        # Automatic instrumentation for Rebrandly domains
        should_inject_trace_context('https://api.rebrandly.com/v1/links')  # True

        # External domains not instrumented automatically
        should_inject_trace_context('https://external-api.com/data')  # False

        # Per-request opt-out
        should_inject_trace_context('https://api.rebrandly.com/v1/links', {'skip_tracing': True})  # False

        # Global opt-out via environment
        os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = 'false'
        should_inject_trace_context('https://api.rebrandly.com/v1/links')  # False
    """
    if options is None:
        options = {}

    # Per-request opt-out takes precedence
    if options.get('skip_tracing', False) is True:
        return False

    # Check if automatic instrumentation is globally disabled
    if not is_auto_domain_instrumentation_enabled():
        return False

    # Check if URL is a Rebrandly domain
    return is_rebrandly_domain(url)


# ============================================
# HEADER FILTERING
# ============================================

def filter_important_headers(headers):
    """
    Filter headers to keep only important ones for observability.
    Excludes sensitive headers like authorization, cookies, and tokens.
    """
    important_headers = [
        'content-type',
        'content-length',
        'accept',
        'accept-encoding',
        'accept-language',
        'host',
        'x-forwarded-for',
        'x-forwarded-proto',
        'x-request-id',
        'x-correlation-id',
        'x-trace-id',
        'user-agent',
        'traceparent',
        'tracestate'
    ]

    filtered = {}
    for key, value in headers.items():
        if key.lower() in important_headers:
            filtered[key] = value
    return filtered


# ============================================
# REQUEST BODY CAPTURE
# ============================================

def is_body_capture_enabled() -> bool:
    """
    Check if request body capture is enabled.
    Enabled by default (opt-out model), can be disabled via environment variable.

    Returns:
        bool: True if body capture is enabled

    Example:
        # Disable body capture
        os.environ['OTEL_CAPTURE_REQUEST_BODY'] = 'false'
        is_body_capture_enabled()  # Returns: False
    """
    env_value = os.environ.get('OTEL_CAPTURE_REQUEST_BODY', '').lower()
    if not env_value:
        return True  # Enabled by default
    return env_value not in ('false', '0', 'no')


def should_capture_body(content_type: Optional[str]) -> bool:
    """
    Check if content type should be captured.
    Only JSON content types are captured (application/json and variants).

    Args:
        content_type: Content-Type header value

    Returns:
        bool: True if content type should be captured

    Example:
        should_capture_body('application/json')  # Returns: True
        should_capture_body('application/json; charset=utf-8')  # Returns: True
        should_capture_body('text/html')  # Returns: False
        should_capture_body('multipart/form-data')  # Returns: False
    """
    if not content_type or not isinstance(content_type, str):
        return False

    # Extract base content type (before semicolon for charset, etc.)
    base_content_type = content_type.split(';')[0].strip().lower()

    # Check if it matches any capturable content type
    return any(
        base_content_type == ct or base_content_type.endswith('+json')
        for ct in CAPTURABLE_CONTENT_TYPES
    )


def redact_sensitive_fields(obj: Any) -> Any:
    """
    Recursively redact sensitive fields from an object.
    Creates a deep copy to avoid mutating the original object.

    Args:
        obj: Object to redact (can be dict, list, or primitive)

    Returns:
        Any: Redacted copy of the object

    Example:
        data = {'username': 'john', 'password': 'secret123', 'nested': {'token': 'abc'}}
        redact_sensitive_fields(data)
        # Returns: {'username': 'john', 'password': '[REDACTED]', 'nested': {'token': '[REDACTED]'}}
    """
    # Handle None and primitives
    if obj is None or not isinstance(obj, (dict, list)):
        return obj

    # Handle lists
    if isinstance(obj, list):
        return [redact_sensitive_fields(item) for item in obj]

    # Handle dictionaries
    redacted = {}
    for key, value in obj.items():
        lower_key = key.lower() if isinstance(key, str) else str(key).lower()

        # Check if key matches any sensitive field name
        # Only match if the key exactly matches or contains the sensitive name
        # (not if the sensitive name contains the key, to avoid false positives like "auth" matching "auth_token")
        is_sensitive = any(
            lower_key == sensitive_name or
            sensitive_name in lower_key
            for sensitive_name in SENSITIVE_FIELD_NAMES
        )

        if is_sensitive:
            redacted[key] = '[REDACTED]'
        elif isinstance(value, (dict, list)):
            # Recursively redact nested objects and arrays
            redacted[key] = redact_sensitive_fields(value)
        else:
            redacted[key] = value

    return redacted


def capture_request_body(body: Any, content_type: Optional[str]) -> Optional[str]:
    """
    Capture and process request body for telemetry.
    Handles JSON parsing, content-type filtering, and sensitive data redaction.

    Args:
        body: Request body (can be string, dict, bytes, or other)
        content_type: Content-Type header value

    Returns:
        Optional[str]: Processed body as JSON string, or None if not capturable

    Example:
        # With parsed dict body
        body = {'user': 'john', 'password': 'secret'}
        capture_request_body(body, 'application/json')
        # Returns: '{"user":"john","password":"[REDACTED]"}'

        # With string body
        body = '{"user":"john","password":"secret"}'
        capture_request_body(body, 'application/json')
        # Returns: '{"user":"john","password":"[REDACTED]"}'

        # With non-JSON content type
        capture_request_body(body, 'text/html')
        # Returns: None
    """
    try:
        # Check if body capture is enabled
        if not is_body_capture_enabled():
            return None

        # Check if content type should be captured
        if not should_capture_body(content_type):
            return None

        # Handle empty body
        if not body:
            return None

        # Parse body if it's a string or bytes
        parsed_body = body
        if isinstance(body, str):
            try:
                parsed_body = json.loads(body)
            except (json.JSONDecodeError, ValueError):
                # If parsing fails, return None (invalid JSON)
                return None
        elif isinstance(body, bytes):
            try:
                parsed_body = json.loads(body.decode('utf-8'))
            except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
                return None

        # Redact sensitive fields
        redacted = redact_sensitive_fields(parsed_body)

        # Convert back to JSON string
        return json.dumps(redacted)
    except Exception as e:
        # Silently fail - don't break the request if body capture fails
        print(f'[Rebrandly OTEL] Body capture failed: {str(e)}')
        return None


# ============================================
# TRACEPARENT INJECTION UTILITIES
# ============================================

def get_traceparent_header() -> Dict[str, str]:
    """
    Get the current trace context as a traceparent header dict.
    Returns a dict with 'traceparent' key for easy spreading into headers.

    Returns:
        Dict with traceparent header {'traceparent': '00-...'} or empty dict if no active span

    Example:
        headers = {**get_traceparent_header(), 'Content-Type': 'application/json'}
        requests.get(url, headers=headers)
    """
    try:
        active_context = context.get_current()
        headers = {}
        propagate.inject(headers, active_context)

        if 'traceparent' in headers:
            return {'traceparent': headers['traceparent']}
        return {}
    except Exception as e:
        print(f'[Rebrandly OTEL] Failed to get traceparent header: {str(e)}')
        return {}


def inject_traceparent(headers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject the current trace context into an existing headers dict.
    Modifies the headers dict in place by adding the traceparent header.

    Args:
        headers: Headers dict to inject traceparent into

    Returns:
        The modified headers dict (for chaining)

    Example:
        headers = {'Content-Type': 'application/json'}
        inject_traceparent(headers)
        requests.get(url, headers=headers)
    """
    if not isinstance(headers, dict):
        print('[Rebrandly OTEL] Invalid headers dict provided to inject_traceparent')
        return headers

    try:
        active_context = context.get_current()
        propagate.inject(headers, active_context)
    except Exception as e:
        print(f'[Rebrandly OTEL] Failed to inject traceparent: {str(e)}')

    return headers


def requests_with_tracing(session=None):
    """
    Create a requests Session or enhance existing session with automatic traceparent injection for Rebrandly domains.
    Uses request hooks to inject traceparent header automatically for *.rebrandly.com domains.

    Args:
        session: Optional requests Session to enhance. If not provided, creates a new one.

    Returns:
        requests.Session with traceparent injection hook

    Example:
        # Option 1: Create new session with tracing (automatic domain filtering)
        session = requests_with_tracing()
        response = session.get('https://api.rebrandly.com/v1/links')  # Traced
        response = session.get('https://external-api.com/data')  # Not traced

        # Option 2: Enhance existing session
        import requests
        my_session = requests.Session()
        traced_session = requests_with_tracing(my_session)

        # Per-request opt-out
        response = session.get('https://api.rebrandly.com/v1/links', skip_tracing=True)
    """
    try:
        import requests
    except ImportError:
        raise ImportError('requests library not installed. Install with: pip install requests')

    if session is None:
        session = requests.Session()

    # Store original hooks
    original_hooks = session.hooks.get('response', [])

    def inject_trace_context(r, *args, **kwargs):
        """Hook to inject traceparent before sending request if it's a Rebrandly domain."""
        try:
            # Get URL from request
            url = r.request.url

            # Check if we should inject trace context for this URL
            # Extract skip_tracing from kwargs if present
            options = {}
            if 'skip_tracing' in kwargs:
                options['skip_tracing'] = kwargs['skip_tracing']

            if should_inject_trace_context(url, options):
                active_context = context.get_current()
                propagate.inject(r.request.headers, active_context)
        except Exception as e:
            print(f'[Rebrandly OTEL] Failed to inject traceparent in requests hook: {str(e)}')
        return r

    # Add our hook while preserving existing hooks
    session.hooks['response'] = original_hooks + [inject_trace_context]

    return session


def httpx_with_tracing(client=None):
    """
    Create an httpx Client or enhance existing client with automatic traceparent injection for Rebrandly domains.
    Uses event hooks to inject traceparent header automatically for *.rebrandly.com domains.

    Args:
        client: Optional httpx Client to enhance. If not provided, creates a new one.

    Returns:
        httpx.Client with traceparent injection hook

    Example:
        # Option 1: Create new client with tracing (automatic domain filtering)
        client = httpx_with_tracing()
        response = client.get('https://api.rebrandly.com/v1/links')  # Traced
        response = client.get('https://external-api.com/data')  # Not traced

        # Option 2: Enhance existing client
        import httpx
        my_client = httpx.Client()
        traced_client = httpx_with_tracing(my_client)

        # Per-request opt-out
        response = client.get('https://api.rebrandly.com/v1/links', extensions={'skip_tracing': True})
    """
    try:
        import httpx
    except ImportError:
        raise ImportError('httpx library not installed. Install with: pip install httpx')

    def inject_trace_context(request):
        """Hook to inject traceparent before sending request if it's a Rebrandly domain."""
        try:
            # Get URL from request
            url = str(request.url)

            # Check if we should inject trace context for this URL
            # Extract skip_tracing from request extensions if present
            options = {}
            if hasattr(request, 'extensions') and 'skip_tracing' in request.extensions:
                options['skip_tracing'] = request.extensions['skip_tracing']

            if should_inject_trace_context(url, options):
                active_context = context.get_current()
                propagate.inject(request.headers, active_context)
        except Exception as e:
            print(f'[Rebrandly OTEL] Failed to inject traceparent in httpx hook: {str(e)}')

    if client is None:
        client = httpx.Client(event_hooks={'request': [inject_trace_context]})
    else:
        # Add our hook to existing event hooks
        existing_hooks = client.event_hooks.get('request', [])
        client.event_hooks['request'] = existing_hooks + [inject_trace_context]

    return client
