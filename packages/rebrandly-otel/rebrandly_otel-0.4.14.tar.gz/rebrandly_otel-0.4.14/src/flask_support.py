# flask_integration.py
"""Flask integration for Rebrandly OTEL SDK."""

import json
from opentelemetry.trace import Status, StatusCode, SpanKind
from .http_utils import filter_important_headers, capture_request_body, auto_detect_route_pattern, strip_query_params
from .http_constants import (
    HTTP_REQUEST_METHOD,
    HTTP_REQUEST_HEADERS,
    HTTP_REQUEST_HEADER_TRACEPARENT,
    HTTP_REQUEST_BODY,
    HTTP_RESPONSE_STATUS_CODE,
    HTTP_ROUTE,
    URL_FULL,
    URL_SCHEME,
    URL_PATH,
    URL_QUERY,
    USER_AGENT_ORIGINAL,
    NETWORK_PROTOCOL_VERSION,
    SERVER_ADDRESS,
    SERVER_PORT,
    CLIENT_ADDRESS,
    ERROR_TYPE
)
from .api_gateway_utils import extract_api_gateway_authorizer_attributes

from flask import request, jsonify, g
from werkzeug.exceptions import HTTPException


def setup_flask(otel, app):
    """
    Setup Flask application with OTEL instrumentation.

    Example:
        from flask import Flask
        from rebrandly_otel import otel
        from rebrandly_otel.flask_integration import setup_flask
        
        app = Flask(__name__)
        setup_flask(otel, app)
    """
    app.before_request(lambda: app_before_request(otel))
    app.after_request(lambda response: app_after_request(otel, response))
    app.register_error_handler(Exception, lambda e: flask_error_handler(otel, e))
    return app

def app_before_request(otel):
    """
    Setup tracing for incoming Flask request.
    To be used with Flask's before_request hook.
    """

    # Extract trace context from headers
    headers = dict(request.headers)
    token = otel.attach_context(headers)
    request.trace_token = token

    # Initial span name - will be updated with route pattern in after_request
    # Using just method initially since route is not available before routing completes
    span_name = f"{request.method}"

    # Filter headers to keep only important ones
    filtered_headers = filter_important_headers(headers)

    # Capture request body if available (before span creation)
    request_body = None
    try:
        content_type = request.headers.get('Content-Type', '')
        # Try to get JSON body first, fallback to raw data
        body = request.get_json(silent=True) or request.data
        request_body = capture_request_body(body, content_type)
    except Exception:
        # Silently skip body capture if it fails
        pass

    # Build attributes dict, excluding None values
    # Note: HTTP_ROUTE will be set in after_request when route pattern is available
    attributes = {
        # Required HTTP attributes per semantic conventions
        HTTP_REQUEST_METHOD: request.method,
        HTTP_REQUEST_HEADERS: json.dumps(filtered_headers, default=str),
        URL_FULL: request.url,
        URL_SCHEME: request.scheme,
        URL_PATH: strip_query_params(request.path),
        # HTTP_ROUTE will be set in after_request after routing completes
        NETWORK_PROTOCOL_VERSION: request.environ.get('SERVER_PROTOCOL', 'HTTP/1.1').split('/')[-1],
        SERVER_ADDRESS: request.host.split(':')[0],
        SERVER_PORT: request.host.split(':')[1] if ':' in request.host else (443 if request.scheme == 'https' else 80),
    }

    # Add optional attributes only if they have non-None values
    traceparent = headers.get('traceparent')
    if traceparent:
        attributes[HTTP_REQUEST_HEADER_TRACEPARENT] = traceparent
    if request_body:
        attributes[HTTP_REQUEST_BODY] = request_body

    # Add optional attributes only if they have values
    if request.query_string:
        attributes[URL_QUERY] = request.query_string.decode('utf-8')

    if request.user_agent and request.user_agent.string:
        attributes[USER_AGENT_ORIGINAL] = request.user_agent.string

    if request.remote_addr:
        attributes[CLIENT_ADDRESS] = request.remote_addr

    # Extract authorizer context if available (when running behind API Gateway via Lambda)
    # The Lambda handler should store the event in flask.g.lambda_event
    if hasattr(g, 'lambda_event') and g.lambda_event:
        authorizer_attrs = extract_api_gateway_authorizer_attributes(g.lambda_event)
        attributes.update(authorizer_attrs)

    # Start span for request using start_as_current_span to make it the active span
    span = otel.tracer.tracer.start_as_current_span(
        span_name,
        attributes=attributes,
        kind=SpanKind.SERVER
    )
    # Store both the span context manager and the span itself
    request.span_context = span
    request.span = span.__enter__()  # This activates the span and returns the span object

    # Log request start
    otel.logger.logger.info(f"Request started: {request.method} {request.path}",
                            extra={"http.method": request.method, "http.path": request.path})

def app_after_request(otel, response):
    """
    Cleanup tracing after Flask request completes.
    To be used with Flask's after_request hook.
    """

    # Check if we have a span and it's still recording
    if hasattr(request, 'span') and request.span.is_recording():
        # Extract route template from Flask's url_rule (available after routing)
        # This is critical for OpenTelemetry compliance - http.route must be low cardinality
        route_pattern = None
        if hasattr(request, 'url_rule') and request.url_rule is not None:
            # Flask's url_rule.rule contains the route template (e.g., '/users/<user_id>')
            route_pattern = request.url_rule.rule
        else:
            # Fallback: auto-detect pattern from path using heuristics
            route_pattern = auto_detect_route_pattern(strip_query_params(request.path))

        # Update span name with route pattern (REQUIRED by OTEL spec)
        # Per spec: span name should be "{method} {http.route}" for low cardinality
        if route_pattern:
            request.span.update_name(f"{request.method} {route_pattern}")
            request.span.set_attribute(HTTP_ROUTE, route_pattern)

        # Update response status code
        request.span.set_attribute(HTTP_RESPONSE_STATUS_CODE, response.status_code)

        # Set span status based on HTTP status code following OpenTelemetry semantic conventions
        # For SERVER spans: only 5xx codes are marked as ERROR, all others left UNSET
        # Per spec: https://opentelemetry.io/docs/specs/semconv/http/http-spans/
        if response.status_code >= 500:
            request.span.set_status(Status(StatusCode.ERROR))
        # For all other codes (1xx, 2xx, 3xx, 4xx), leave status unset

        # Properly close the span context manager
        if hasattr(request, 'span_context'):
            request.span_context.__exit__(None, None, None)
        else:
            # Fallback if we don't have the context manager
            request.span.end()

    # Detach context
    if hasattr(request, 'trace_token'):
        otel.detach_context(request.trace_token)

    # Log request completion
    otel.logger.logger.info(f"Request completed: {response.status_code}",
                            extra={"http.response.status_code": response.status_code})

    otel.force_flush(timeout_millis=100)
    return response

def flask_error_handler(otel, exception):
    """
    Handle Flask exceptions and record them in the current span.
    To be used with Flask's errorhandler decorator.
    """

    # Determine the status code
    if isinstance(exception, HTTPException):
        status_code = exception.code
    elif hasattr(exception, 'status_code'):
        status_code = exception.status_code
    elif hasattr(exception, 'code'):
        status_code = exception.code if isinstance(exception.code, int) else 500
    else:
        status_code = 500

    # Record exception in span if available and still recording
    if hasattr(request, 'span') and request.span.is_recording():
        request.span.set_attribute(HTTP_RESPONSE_STATUS_CODE, status_code)
        request.span.set_attribute(ERROR_TYPE, type(exception).__name__)

        request.span.record_exception(exception)
        request.span.set_status(Status(StatusCode.ERROR, str(exception)))
        request.span.add_event("exception", {
            "exception.type": type(exception).__name__,
            "exception.message": str(exception)
        })

        # Only close the span if it's still recording (not already ended)
        if hasattr(request, 'span_context'):
            request.span_context.__exit__(type(exception), exception, None)
        else:
            request.span.end()

    # Log the error with status code
    otel.logger.logger.error(f"Unhandled exception: {exception} (status: {status_code})",
                             exc_info=True,
                             extra={
                                 "exception.type": type(exception).__name__,
                                 "http.response.status_code": status_code
                             })

    # Return error response with the determined status code
    return jsonify({
        "error": str(exception),
        "type": type(exception).__name__
    }), status_code