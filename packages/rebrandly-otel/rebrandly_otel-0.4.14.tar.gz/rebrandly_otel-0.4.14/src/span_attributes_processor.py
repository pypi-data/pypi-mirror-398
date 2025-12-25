"""
Span Attributes Processor for Rebrandly OTEL SDK
Automatically adds attributes from OTEL_SPAN_ATTRIBUTES environment variable to all spans
"""

import os
from typing import Optional
from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan, Span
from opentelemetry.sdk.trace.export import SpanProcessor


class SpanAttributesProcessor(SpanProcessor):
    """
    Span processor that automatically adds attributes from OTEL_SPAN_ATTRIBUTES
    environment variable to all spans at creation time.
    """

    def __init__(self):
        """Initialize the processor and parse OTEL_SPAN_ATTRIBUTES."""
        self.name = 'SpanAttributesProcessor'
        self.span_attributes = self._parse_span_attributes()

        # Log parsed attributes in debug mode
        if os.environ.get('OTEL_DEBUG', 'false').lower() == 'true' and self.span_attributes:
            print(f'[SpanAttributesProcessor] Parsed OTEL_SPAN_ATTRIBUTES: {self.span_attributes}')

    def _parse_span_attributes(self) -> dict:
        """
        Parse OTEL_SPAN_ATTRIBUTES environment variable.
        Format: key1=value1,key2=value2

        Returns:
            Dictionary of parsed attributes as key-value pairs
        """
        attributes = {}
        otel_span_attrs = os.environ.get('OTEL_SPAN_ATTRIBUTES', None)

        if not otel_span_attrs or otel_span_attrs.strip() == '':
            return attributes

        try:
            pairs = otel_span_attrs.split(',')
            for attr in pairs:
                trimmed_attr = attr.strip()
                if trimmed_attr and '=' in trimmed_attr:
                    # Split on first '=' only, in case value contains '='
                    key, value = trimmed_attr.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key:
                        attributes[key] = value
        except Exception as e:
            print(f'[SpanAttributesProcessor] Warning: Invalid OTEL_SPAN_ATTRIBUTES value: {e}')

        return attributes

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        """
        Called when a span is started.
        Adds configured attributes to the span.

        Args:
            span: The span that was just started
            parent_context: The parent context (optional)
        """
        try:
            # Add all parsed attributes to the span
            if self.span_attributes:
                for key, value in self.span_attributes.items():
                    span.set_attribute(key, value)
        except Exception as e:
            # Fail silently to avoid breaking the entire tracing pipeline
            # Log only in debug mode to avoid noise
            if os.environ.get('OTEL_DEBUG', 'false').lower() == 'true':
                print(f'[SpanAttributesProcessor] Error processing span: {e}')

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
