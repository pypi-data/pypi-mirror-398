# src/__init__.py
from .rebrandly_otel import *
from .pymysql_instrumentation import instrument_pymysql
from .sqlite3_instrumentation import instrument_sqlite3
from .api_gateway_utils import (
    is_api_gateway_event,
    extract_api_gateway_http_attributes,
    extract_api_gateway_context
)
from .http_utils import (
    inject_traceparent,
    requests_with_tracing,
    httpx_with_tracing
)

# Optional framework support - only import if available
try:
    from .flask_support import setup_flask
    _has_flask = True
except ImportError:
    _has_flask = False
    def setup_flask(*args, **kwargs):
        raise ImportError(
            "Flask support requires Flask and Werkzeug. "
            "Install with: pip install rebrandly-otel[flask]"
        )

try:
    from .fastapi_support import setup_fastapi, get_current_span
    _has_fastapi = True
except ImportError:
    _has_fastapi = False
    def setup_fastapi(*args, **kwargs):
        raise ImportError(
            "FastAPI support requires FastAPI and Starlette. "
            "Install with: pip install rebrandly-otel[fastapi]"
        )
    def get_current_span(*args, **kwargs):
        raise ImportError(
            "FastAPI support requires FastAPI and Starlette. "
            "Install with: pip install rebrandly-otel[fastapi]"
        )

# Build __all__ dynamically based on available features
__all__ = [
    'otel',
    'lambda_handler',
    'span',
    'aws_message_span',
    'traces',
    'tracer',
    'metrics',
    'logger',
    'force_flush',
    'aws_message_handler',
    'shutdown',
    'instrument_pymysql',
    'instrument_sqlite3',
    # API Gateway utilities
    'is_api_gateway_event',
    'extract_api_gateway_http_attributes',
    'extract_api_gateway_context',
    # HTTP client tracing
    'inject_traceparent',
    'requests_with_tracing',
    'httpx_with_tracing'
]

# Add framework support if available
if _has_flask:
    __all__.append('setup_flask')

if _has_fastapi:
    __all__.extend(['setup_fastapi', 'get_current_span'])