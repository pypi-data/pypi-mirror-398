# traces.py
"""Tracing implementation for Rebrandly OTEL SDK."""
import os
from typing import Optional, Dict, Any, ContextManager
from contextlib import contextmanager
from opentelemetry import trace, propagate, context
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider, Span
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    BatchSpanProcessor,
    SimpleSpanProcessor
)

from .otel_utils import *
from .span_attributes_processor import SpanAttributesProcessor
from .redis_span_processor import RedisSpanProcessor

class RebrandlyTracer:
    """Wrapper for OpenTelemetry tracing with Rebrandly-specific features."""

    def __init__(self):
        self._tracer: Optional[trace.Tracer] = None
        self._provider: Optional[TracerProvider] = None
        self._setup_tracing()

    def _setup_tracing(self):

        # Create provider with resource
        self._provider = TracerProvider(resource=create_resource())

        # Add span attributes processor to automatically add OTEL_SPAN_ATTRIBUTES to all spans
        self._provider.add_span_processor(SpanAttributesProcessor())

        # Add Redis span processor to ensure db.name is always set
        self._provider.add_span_processor(RedisSpanProcessor())

        # Add console exporter for local debugging
        if is_otel_debug():
            console_exporter = ConsoleSpanExporter()
            self._provider.add_span_processor(SimpleSpanProcessor(console_exporter))

        # Add OTLP exporter if configured
        otel_endpoint = get_otlp_endpoint()
        if otel_endpoint is not None:
            otlp_exporter = OTLPSpanExporter(
                endpoint=otel_endpoint,
                timeout=5
            )

            # Use batch processor for production
            batch_processor = BatchSpanProcessor(otlp_exporter, export_timeout_millis=get_millis_batch_time())
            self._provider.add_span_processor(batch_processor)

        # Set as global provider
        trace.set_tracer_provider(self._provider)

        # Automatically instrument Redis
        self._instrument_redis()

        # Automatically instrument boto3/botocore for AWS SDK calls
        self._instrument_botocore()

        # Get tracer
        self._tracer = trace.get_tracer(get_service_name(), get_service_version())

    def _instrument_redis(self):
        """
        Automatically instrument Redis clients for OpenTelemetry tracing.
        This method is called during SDK initialization to enable automatic Redis tracing.
        """
        try:
            from opentelemetry.instrumentation.redis import RedisInstrumentor

            # Only instrument if not already instrumented
            if not RedisInstrumentor().is_instrumented_by_opentelemetry:
                RedisInstrumentor().instrument()

                if os.environ.get('OTEL_DEBUG', 'false').lower() == 'true':
                    print('[Rebrandly OTEL] Redis instrumentation enabled')

        except ImportError:
            # Redis instrumentation package not installed - skip silently
            if os.environ.get('OTEL_DEBUG', 'false').lower() == 'true':
                print('[Rebrandly OTEL] Redis instrumentation not available (package not installed)')

        except Exception as e:
            # Log but don't fail if Redis instrumentation fails
            if os.environ.get('OTEL_DEBUG', 'false').lower() == 'true':
                print(f'[Rebrandly OTEL] Redis instrumentation failed: {e}')

    def _instrument_botocore(self):
        """
        Automatically instrument boto3/botocore for AWS SDK calls (SQS, SNS, DynamoDB, etc.).
        This enables automatic trace context propagation through AWS services.
        """
        try:
            from opentelemetry.instrumentation.botocore import BotocoreInstrumentor

            # Only instrument if not already instrumented
            if not BotocoreInstrumentor().is_instrumented_by_opentelemetry:
                BotocoreInstrumentor().instrument()

                if os.environ.get('OTEL_DEBUG', 'false').lower() == 'true':
                    print('[Rebrandly OTEL] Botocore instrumentation enabled')

        except ImportError:
            # Botocore instrumentation package not installed - skip silently
            if os.environ.get('OTEL_DEBUG', 'false').lower() == 'true':
                print('[Rebrandly OTEL] Botocore instrumentation not available (package not installed)')

        except Exception as e:
            # Log but don't fail if Botocore instrumentation fails
            if os.environ.get('OTEL_DEBUG', 'false').lower() == 'true':
                print(f'[Rebrandly OTEL] Botocore instrumentation failed: {e}')

    def force_flush(self, timeout_millis: int = 5000) -> bool:
        """
        Force flush all pending spans.

        Args:
            timeout_millis: Maximum time to wait for flush in milliseconds

        Returns:
            True if flush succeeded, False otherwise
        """
        if not self._provider:
            return True

        try:
            # ForceFlush on the TracerProvider will flush all processors
            success = self._provider.force_flush(timeout_millis)

            if not success:
                print(f"[Tracer] Force flush timed out after {timeout_millis}ms")

            return success
        except Exception as e:
            print(f"[Tracer] Error during force flush: {e}")
            return False

    def shutdown(self):
        """Shutdown the tracer provider and all processors."""
        if self._provider:
            try:
                self._provider.shutdown()
                print("[Tracer] Shutdown completed")
            except Exception as e:
                print(f"[Tracer] Error during shutdown: {e}")

    @property
    def tracer(self) -> trace.Tracer:
        """Get the underlying OpenTelemetry tracer."""
        if not self._tracer:
            # Return no-op tracer if tracing is disabled
            return trace.get_tracer(__name__)
        return self._tracer

    def start_as_current_span(self, name: str, **kwargs):
        """Start a span as the current span (delegates to underlying tracer)."""
        return self.tracer.start_as_current_span(name, **kwargs)

    @contextmanager
    def start_span(self,
                   name: str,
                   attributes: Optional[Dict[str, Any]] = None,
                   kind: trace.SpanKind = trace.SpanKind.INTERNAL) -> ContextManager[Span]:
        """Start a new span as the current span."""
        # Ensure we use the tracer to create a child span of the current span
        with self.tracer.start_as_current_span(
                name,
                attributes=attributes,
                kind=kind
        ) as span:
            yield span

    def start_span_with_context(self,
                                name: str,
                                attributes: Dict[str, str],
                                context_attributes: Optional[Dict[str, Any]] = None):
        """Start a span with extracted context (e.g., from message headers)."""
        # Extract context from carrier

        carrier, extracted_context = self.__get_aws_message_context_attributes(context_attributes)
        ctx = propagate.extract(extracted_context)

        if context_attributes is not None:
            # Start span with extracted context
            with self.tracer.start_as_current_span(
                    name,
                    context=ctx,
                    attributes=attributes
            ) as span:
                yield span
        else:
            # Start span with current context
            with self.tracer.start_as_current_span(
                    name,
                    context=context.get_current(),
                    attributes=attributes
            ) as span:
                yield span

    def get_current_span(self) -> Span:
        """Get the currently active span."""
        return trace.get_current_span()


    def record_span_exception(self, exception: Exception=None, span: Optional[Span] = None, msg: Optional[str] = None):
        """Record an exception on a span."""
        target_span = span or self.get_current_span()
        if target_span and hasattr(target_span, 'record_exception'):
            if exception is not None:
                target_span.record_exception(exception)
                target_span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))


    def record_span_success(self, span: Optional[Span] = None, msg: Optional[str] = None):
        """Record success on a span."""
        target_span = span or self.get_current_span()
        if target_span and hasattr(target_span, 'set_status'):
            target_span.set_status(trace.Status(trace.StatusCode.OK))

    # Convenience methods for setting span status
    def set_span_error(self, message: str, exception: Optional[Exception] = None, span: Optional[Span] = None):
        """
        Convenience method to set span status to ERROR.

        Args:
            message: Error message to attach to span
            exception: Optional exception to record
            span: Span to mark as error (defaults to current span)
        """
        target_span = span or self.get_current_span()
        if target_span and hasattr(target_span, 'is_recording') and target_span.is_recording():
            if exception:
                target_span.record_exception(exception)
            target_span.set_status(trace.Status(trace.StatusCode.ERROR, message))

    def set_span_success(self, message: Optional[str] = None, span: Optional[Span] = None):
        """
        Convenience method to set span status to OK.

        Args:
            message: Optional success message (ignored - OK status doesn't support descriptions per OTEL spec)
            span: Span to mark as success (defaults to current span)
        """
        target_span = span or self.get_current_span()
        if target_span and hasattr(target_span, 'is_recording') and target_span.is_recording():
            # OK status doesn't support description per OpenTelemetry spec
            target_span.set_status(trace.Status(trace.StatusCode.OK))

    def set_span_unset(self, span: Optional[Span] = None):
        """
        Convenience method to set span status to UNSET (default/neutral state).

        Args:
            span: Span to mark as unset (defaults to current span)
        """
        target_span = span or self.get_current_span()
        if target_span and hasattr(target_span, 'is_recording') and target_span.is_recording():
            target_span.set_status(trace.Status(trace.StatusCode.UNSET))

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None, span: Optional[Span] = None):
        """Add an event to a span."""
        target_span = span or self.get_current_span()
        if target_span and hasattr(target_span, 'add_event'):
            target_span.add_event(name, attributes=attributes or {})

    # AWS-specific helpers
    def __get_aws_message_context_attributes(self, msg: dict):
        """
        Get trace context as AWS message attributes format.
        Used for SQS/SNS message propagation.
        """
        carrier = {}
        # Convert to AWS message attributes format
        message_attributes = {}
        if msg is not None and 'MessageAttributes' in msg:
            for key, value in msg['MessageAttributes'].items():
                carrier[key] = {
                    'StringValue': value,
                    'DataType': 'String'
                }
        context_extracted = propagate.extract(carrier)
        return carrier, context_extracted

    def get_attributes_for_aws_from_context(self):
        # Create carrier for message attributes
        carrier = {}

        # Inject trace context into carrier
        propagate.inject(carrier)

        # Convert carrier to SQS message attributes format
        message_attributes = {}
        for key, value in carrier.items():
            message_attributes[key] = {
                'StringValue': value,
                'DataType': 'String'
            }
        return message_attributes