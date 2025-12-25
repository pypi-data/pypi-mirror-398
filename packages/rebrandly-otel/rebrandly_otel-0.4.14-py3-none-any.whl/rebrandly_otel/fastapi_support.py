# fastapi_integration.py
"""FastAPI integration for Rebrandly OTEL SDK."""
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
from fastapi import HTTPException, Depends
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

import time

def setup_fastapi(otel , app):
    """
    Setup FastAPI application with OTEL instrumentation.

    Example:
        from fastapi import FastAPI
        from rebrandly_otel import otel
        from rebrandly_otel.fastapi_integration import setup_fastapi

        app = FastAPI()
        setup_fastapi(otel, app)
    """

    # Add middleware
    add_otel_middleware(otel, app)

    # Add exception handlers
    app.add_exception_handler(HTTPException, lambda request, exc: fastapi_exception_handler(otel, request, exc))
    app.add_exception_handler(Exception, lambda request, exc: fastapi_exception_handler(otel, request, exc))

    return app

def add_otel_middleware(otel, app):
    """
    Add OTEL middleware to FastAPI application.
    """

    class OTELMiddleware(BaseHTTPMiddleware):
        def __init__(self, app):
            super().__init__(app)
            self.otel = otel

        async def dispatch(self, request: Request, call_next):
            # Extract trace context from headers
            headers = dict(request.headers)
            token = self.otel.attach_context(headers)

            # Initial span name - will be updated with route pattern after routing completes
            # Using just method initially for low cardinality
            span_name = f"{request.method}"

            # Filter headers to keep only important ones
            filtered_headers = filter_important_headers(headers)

            # Capture request body if available (before span creation)
            request_body = None
            try:
                content_type = request.headers.get('content-type', '')
                # Read body (this caches it so FastAPI can still access it later)
                body_bytes = await request.body()
                # Try to parse as JSON, fallback to raw bytes
                try:
                    body = json.loads(body_bytes.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                    body = body_bytes

                request_body = capture_request_body(body, content_type)
            except Exception:
                # Silently skip body capture if it fails
                pass

            # Build attributes dict, excluding None values
            attributes = {
                # Required HTTP attributes per semantic conventions
                HTTP_REQUEST_METHOD: request.method,
                HTTP_REQUEST_HEADERS: json.dumps(filtered_headers, default=str),
                URL_FULL: str(request.url),
                URL_SCHEME: request.url.scheme,
                URL_PATH: strip_query_params(request.url.path),
                NETWORK_PROTOCOL_VERSION: "1.1",  # FastAPI/Starlette typically uses HTTP/1.1
                SERVER_ADDRESS: request.url.hostname,
                SERVER_PORT: request.url.port or (443 if request.url.scheme == 'https' else 80),
            }

            # Add optional attributes only if they have non-None values
            traceparent = headers.get('traceparent')
            if traceparent:
                attributes[HTTP_REQUEST_HEADER_TRACEPARENT] = traceparent
            if request_body:
                attributes[HTTP_REQUEST_BODY] = request_body

            # Add optional attributes only if they have values
            if request.url.query:
                attributes[URL_QUERY] = request.url.query

            user_agent = request.headers.get("user-agent")
            if user_agent:
                attributes[USER_AGENT_ORIGINAL] = user_agent

            if request.client and request.client.host:
                attributes[CLIENT_ADDRESS] = request.client.host

            # Extract authorizer context if available (when running behind API Gateway via Lambda)
            # The Lambda handler should store the event in request.state.lambda_event
            if hasattr(request.state, 'lambda_event') and request.state.lambda_event:
                authorizer_attrs = extract_api_gateway_authorizer_attributes(request.state.lambda_event)
                attributes.update(authorizer_attrs)

            # Use start_as_current_span for proper context propagation
            with self.otel.tracer.tracer.start_as_current_span(
                    span_name,
                    attributes=attributes,
                    kind=SpanKind.SERVER
            ) as span:
                # Log request start
                self.otel.logger.logger.info(f"Request started: {request.method} {request.url.path}",
                                             extra={"http.method": request.method, "http.path": request.url.path})

                # Store span in request state for access in routes
                request.state.span = span
                request.state.trace_token = token

                start_time = time.time()

                try:
                    # Process request
                    response = await call_next(request)

                    # After routing completes, extract the route template
                    # This is critical for OpenTelemetry compliance - http.route must be low cardinality
                    route_pattern = None

                    # Method 1: Get route from matched endpoint in scope
                    # FastAPI/Starlette stores the matched route after routing completes
                    if 'endpoint' in request.scope and 'router' in request.scope:
                        endpoint = request.scope['endpoint']
                        router = request.scope['router']

                        # Find the route that matches this endpoint
                        if hasattr(router, 'routes'):
                            for route in router.routes:
                                if hasattr(route, 'endpoint') and route.endpoint == endpoint:
                                    if hasattr(route, 'path'):
                                        route_pattern = route.path  # e.g., '/items/{item_id}'
                                        break

                    # Method 2: Fallback - auto-detect pattern from path using heuristics
                    if not route_pattern:
                        route_pattern = auto_detect_route_pattern(strip_query_params(request.url.path))

                    # Update span with route pattern (REQUIRED by OTEL spec)
                    # Per spec: span name should be "{method} {http.route}" for low cardinality
                    if route_pattern:
                        span.update_name(f"{request.method} {route_pattern}")
                        span.set_attribute(HTTP_ROUTE, route_pattern)

                    # Set response attributes using semantic conventions
                    span.set_attribute(HTTP_RESPONSE_STATUS_CODE, response.status_code)

                    # Set span status based on HTTP status code following OpenTelemetry semantic conventions
                    # For SERVER spans: only 5xx codes are marked as ERROR, all others left UNSET
                    # Per spec: https://opentelemetry.io/docs/specs/semconv/http/http-spans/
                    if response.status_code >= 500:
                        span.set_status(Status(StatusCode.ERROR))
                    # For all other codes (1xx, 2xx, 3xx, 4xx), leave status unset

                    # Log request completion
                    self.otel.logger.logger.info(f"Request completed: {response.status_code}",
                                                 extra={"http.response.status_code": response.status_code})
                    otel.force_flush(timeout_millis=100)
                    return response

                except Exception as e:
                    # Record exception
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.add_event("exception", {
                        "exception.type": type(e).__name__,
                        "exception.message": str(e)
                    })

                    # Log error
                    self.otel.logger.logger.error(f"Unhandled exception: {e}",
                                                  exc_info=True,
                                                  extra={"exception.type": type(e).__name__})

                    raise

                finally:
                    # Detach context
                    self.otel.detach_context(token)

    # Add middleware to app
    app.add_middleware(OTELMiddleware)

def fastapi_exception_handler(otel, request, exc):
    """
    Handle FastAPI exceptions and record them in the current span.
    """

    # Determine the status code
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        error_detail = exc.detail
    elif hasattr(exc, 'status_code'):
        status_code = exc.status_code
        error_detail = str(exc)
    elif hasattr(exc, 'code'):
        status_code = exc.code if isinstance(exc.code, int) else 500
        error_detail = str(exc)
    else:
        status_code = 500
        error_detail = str(exc)

    # Record exception in span if available and still recording
    if hasattr(request.state, 'span') and request.state.span.is_recording():
        # Update response status code and error type
        request.state.span.set_attribute(HTTP_RESPONSE_STATUS_CODE, status_code)
        request.state.span.set_attribute(ERROR_TYPE, type(exc).__name__)

        request.state.span.record_exception(exc)
        request.state.span.set_status(Status(StatusCode.ERROR, str(exc)))
        request.state.span.add_event("exception", {
            "exception.type": type(exc).__name__,
            "exception.message": str(exc)
        })

    # Log the error
    otel.logger.logger.error(f"Unhandled exception: {exc} (status: {status_code})",
                             exc_info=True,
                             extra={
                                 "exception.type": type(exc).__name__,
                                 "http.response.status_code": status_code
                             })

    # Return error response
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_detail,
            "type": type(exc).__name__
        }
    )

# Optional: Dependency injection helper for accessing the span in routes
def get_current_span(request: Request):
    """
    FastAPI dependency to get the current span in route handlers.

    Example:
        from fastapi import Depends
        from rebrandly_otel.fastapi_integration import get_current_span

        @app.get("/example")
        async def example(span = Depends(get_current_span)):
            if span:
                span.add_event("custom_event", {"key": "value"})
            return {"status": "ok"}
    """
    if hasattr(request.state, 'span'):
        return request.state.span
    return None