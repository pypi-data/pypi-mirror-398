"""
Redis Span Processor for Rebrandly OTEL SDK
Ensures db.name and db.statement are always set for Redis spans
"""

import os
import re
from typing import Optional
from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan, Span
from opentelemetry.sdk.trace.export import SpanProcessor


class RedisSpanProcessor(SpanProcessor):
    """
    Span processor that automatically enhances Redis spans with db.name and db.statement.

    This processor ensures consistency between local development and production environments
    where Redis connection strings may differ.
    """

    # Compile regex pattern once for efficiency
    _CONNECTION_STRING_PATTERN = re.compile(r'redis(?:s)?://[^/]+/(\d+)')

    def __init__(self):
        """Initialize the processor."""
        self.name = 'RedisSpanProcessor'

        # Log initialization in debug mode
        if os.environ.get('OTEL_DEBUG', 'false').lower() == 'true':
            print('[RedisSpanProcessor] Initialized')

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        """
        Called when a span is started.
        Enhances Redis spans with db.name and db.statement attributes.

        Args:
            span: The span that was just started
            parent_context: The parent context (optional)
        """
        try:
            # Check if this is a Redis span
            attributes = span.attributes or {}

            if attributes.get('db.system') == 'redis':
                # Ensure db.name is set
                if 'db.name' not in attributes or not attributes['db.name']:
                    db_name = self._extract_db_name(attributes)
                    span.set_attribute('db.name', db_name)

                # Ensure db.statement is set for better observability
                if 'db.statement' not in attributes or not attributes['db.statement']:
                    if 'db.operation' in attributes:
                        # Use operation name as statement if available
                        span.set_attribute('db.statement', attributes['db.operation'])

        except Exception as e:
            # Fail silently to avoid breaking the tracing pipeline
            if os.environ.get('OTEL_DEBUG', 'false').lower() == 'true':
                print(f'[RedisSpanProcessor] Error processing span: {e}')

    def _extract_db_name(self, attributes: dict) -> str:
        """
        Extract Redis database name from span attributes.

        Priority:
        1. db.redis.database_index - Direct database index attribute
        2. db.connection_string - Parse connection string for database index
        3. Default fallback - "redis"

        Args:
            attributes: Span attributes dictionary

        Returns:
            Database name string (e.g., "redis-0", "redis-2", or "redis")
        """
        # Try db.redis.database_index first (OpenTelemetry semantic convention)
        db_index = attributes.get('db.redis.database_index')
        if db_index is not None:
            return f"redis-{db_index}"

        # Try to extract from connection string
        conn_str = attributes.get('db.connection_string')
        if conn_str:
            try:
                # Match patterns like redis://host:6379/0 or rediss://host/2
                match = self._CONNECTION_STRING_PATTERN.search(str(conn_str))
                if match:
                    db_index = match.group(1)
                    return f"redis-{db_index}"
            except Exception:
                pass  # Fall through to default

        # Default fallback
        return 'redis'

    def on_end(self, span: ReadableSpan) -> None:
        """
        Called when a span is ended.
        No-op for this processor.

        Args:
            span: The span that was just ended
        """
        pass

    def shutdown(self) -> None:
        """
        Shutdown the processor.
        No-op for this processor.
        """
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """
        Force flush the processor.
        No-op for this processor.

        Args:
            timeout_millis: Maximum time to wait for flush in milliseconds

        Returns:
            Always returns True as there's nothing to flush
        """
        return True
