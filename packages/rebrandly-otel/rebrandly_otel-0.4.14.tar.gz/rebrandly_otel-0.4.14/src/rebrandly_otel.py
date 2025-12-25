
import json
import time
import psutil
import functools
from contextlib import contextmanager
from datetime import datetime
from opentelemetry.trace import Status, StatusCode, SpanKind
from typing import Optional, Dict, Any, Callable, TypeVar
from opentelemetry import baggage, propagate, context as otel_context

from .traces import RebrandlyTracer
from .metrics import RebrandlyMeter
from .logs import RebrandlyLogger
from .otel_utils import extract_event_from
from .http_constants import (
    HTTP_RESPONSE_STATUS_CODE,
)
from .api_gateway_utils import (
    is_api_gateway_event,
    extract_api_gateway_http_attributes,
    extract_api_gateway_context
)


def convert_xray_to_w3c_traceparent(aws_trace_header: str) -> Optional[str]:
    """
    Convert AWS X-Ray trace header format to W3C traceparent format.

    X-Ray format: Root=1-{trace-id};Parent={span-id};Sampled={flags}
    W3C format: 00-{trace-id}-{span-id}-{flags}

    Args:
        aws_trace_header: X-Ray formatted trace header

    Returns:
        W3C traceparent string, or None if parsing fails

    Example:
        Input: "Root=1-e68ce196-91dc659dda45c25136ca9a2b;Parent=3ea7495ca0fa56ef;Sampled=1"
        Output: "00-e68ce19691dc659dda45c25136ca9a2b-3ea7495ca0fa56ef-01"
    """
    try:
        if not aws_trace_header or not isinstance(aws_trace_header, str):
            return None

        parts = aws_trace_header.split(';')
        trace_id = None
        span_id = None
        sampled = None

        for part in parts:
            part = part.strip()
            if part.startswith('Root='):
                # Extract trace ID from "Root=1-{timestamp}-{trace-id}"
                root_value = part.split('=', 1)[1]
                # X-Ray format: 1-{8-char-timestamp}-{24-char-trace-id}
                # We need to remove the "1-" prefix and the timestamp to get full 32-char trace-id
                root_parts = root_value.split('-')
                if len(root_parts) >= 3:
                    # Combine timestamp + trace-id to form complete 32-character trace ID
                    trace_id = root_parts[1] + root_parts[2]
            elif part.startswith('Parent='):
                # Extract parent span ID
                span_id = part.split('=', 1)[1]
            elif part.startswith('Sampled='):
                # Convert sampled flag: 1 -> 01, 0 -> 00
                sampled_value = part.split('=', 1)[1]
                sampled = '01' if sampled_value == '1' else '00'

        # Validate all required parts are present
        if trace_id and span_id and sampled:
            # W3C traceparent format: version-trace_id-parent_id-trace_flags
            return f'00-{trace_id}-{span_id}-{sampled}'

        return None

    except Exception as e:
        # Log error but don't fail
        print(f'[Rebrandly OTEL] Failed to convert X-Ray trace header: {str(e)}')
        return None


T = TypeVar('T')

class RebrandlyOTEL:
    """Main entry point for Rebrandly's OpenTelemetry instrumentation."""

    _instance: Optional['RebrandlyOTEL'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._tracer: Optional[RebrandlyTracer] = None
            self._meter: Optional[RebrandlyMeter] = None
            self._logger: Optional[RebrandlyLogger] = None
            self.__class__._initialized = True

    def initialize(self, **kwargs) -> 'RebrandlyOTEL':
        # Force initialization of components
        _ = self.tracer
        _ = self.meter
        _ = self.logger

        return self

    @property
    def tracer(self) -> RebrandlyTracer:
        """Get the tracer instance."""
        if self._tracer is None:
            self._tracer = RebrandlyTracer()
        return self._tracer

    @property
    def meter(self) -> RebrandlyMeter:
        """Get the meter instance."""
        if self._meter is None:
            self._meter = RebrandlyMeter()
        return self._meter

    @property
    def logger(self) -> RebrandlyLogger:
        """Get the logger instance."""
        if self._logger is None:
            self._logger = RebrandlyLogger()
        return self._logger

    # Convenience methods for common operations

    @contextmanager
    def span(self,
             name: str,
             attributes: Optional[Dict[str, Any]] = None,
             kind: SpanKind = SpanKind.INTERNAL,
             message=None):
        """Create a span using context manager."""
        with self.tracer.start_span(name=name, attributes=attributes, kind=kind) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def trace_decorator(self,
                        name: Optional[str] = None,
                        attributes: Optional[Dict[str, Any]] = None,
                        kind: SpanKind = SpanKind.INTERNAL) -> Callable[[T], T]:
        """Decorator for tracing functions."""
        def decorator(func: T) -> T:
            span_name = name or f"{func.__module__}.{func.__name__}"

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.span(span_name, attributes=attributes, kind=kind):
                    return func(*args, **kwargs)

            return wrapper
        return decorator

    def lambda_handler(self,
                       name: Optional[str] = None,
                       attributes: Optional[Dict[str, Any]] = None,
                       kind: SpanKind = SpanKind.SERVER,
                       auto_flush: bool = True,
                       skip_aws_link: bool = False):
        """
        Decorator specifically for Lambda handlers with automatic flushing.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(event=None, lambda_context=None):
                # Determine span name
                span_name = name or f"lambda.{func.__name__}"
                start_time = datetime.now()

                # Build span attributes
                span_attributes = attributes.copy() if attributes else {}
                span_attributes['faas.trigger'] = self._detect_lambda_trigger(event)

                # Add Lambda-specific attributes if context is available
                if lambda_context is not None:
                    span_attributes.update({
                        "faas.execution": getattr(lambda_context, 'aws_request_id', 'unknown'),
                        "faas.id": getattr(lambda_context, 'function_arn', 'unknown'),
                        "faas.name": getattr(lambda_context, 'function_name', 'unknown'),
                        "faas.version": getattr(lambda_context, 'function_version', 'unknown')
                    })

                # Handle context extraction from AWS events
                token = None
                is_api_gateway = False

                # Detect and extract HTTP attributes for API Gateway events
                if event and isinstance(event, dict) and is_api_gateway_event(event):
                    is_api_gateway = True
                    http_attrs, updated_span_name = extract_api_gateway_http_attributes(event)
                    span_attributes.update(http_attrs)

                    # Update span name to HTTP format if not explicitly set
                    if not name and updated_span_name:
                        span_name = updated_span_name

                    # Extract traceparent from API Gateway headers
                    carrier = extract_api_gateway_context(event)
                    if carrier:
                        extracted_context = propagate.extract(carrier)
                        token = otel_context.attach(extracted_context)

                if not is_api_gateway and not skip_aws_link and event and isinstance(event, dict) and 'Records' in event:
                    first_record = event['Records'][0] if event['Records'] else None
                    if first_record:
                        carrier = {}

                        # Extract from SQS
                        if 'MessageAttributes' in first_record:
                            for key, value in first_record['MessageAttributes'].items():
                                if isinstance(value, dict) and 'StringValue' in value:
                                    carrier[key] = value['StringValue']
                        if ('messageAttributes' in first_record and 'traceparent' in first_record['messageAttributes']
                                and 'stringValue' in first_record['messageAttributes']['traceparent']):
                            carrier['traceparent'] = first_record['messageAttributes']['traceparent']['stringValue']

                        # Extract from SNS
                        elif 'Sns' in first_record and 'MessageAttributes' in first_record['Sns']:
                            for key, value in first_record['Sns']['MessageAttributes'].items():
                                if isinstance(value, dict):
                                    if 'Value' in value:
                                        carrier[key] = value['Value']
                                    elif 'StringValue' in value:
                                        carrier[key] = value['StringValue']

                        # Fallback: Extract from AWSTraceHeader (X-Ray format) if no W3C traceparent found
                        if not carrier.get('traceparent') and 'attributes' in first_record and 'AWSTraceHeader' in first_record['attributes']:
                            aws_trace_header = first_record['attributes']['AWSTraceHeader']
                            traceparent = convert_xray_to_w3c_traceparent(aws_trace_header)
                            if traceparent:
                                carrier['traceparent'] = traceparent
                                print(f'[Rebrandly OTEL] Extracted trace context from AWSTraceHeader: {traceparent}')

                        # Attach extracted context
                        if carrier:
                            extracted_context = propagate.extract(carrier)
                            token = otel_context.attach(extracted_context)

                result = None
                span = None
                try:

                    # Create and execute within span
                    with self.tracer.start_span(
                            name=span_name,
                            attributes=span_attributes,
                            kind=kind
                    ) as span:
                        # Add invocation start event with standardized attributes
                        start_event_attrs = {
                            'event.type': type(event).__name__ if event else 'None'
                        }

                        # Add records count if present
                        if event and isinstance(event, dict) and 'Records' in event:
                            start_event_attrs['event.records'] = f"{len(event['Records'])}"

                        span.add_event("lambda.invocation.start", start_event_attrs)

                        # Execute handler
                        result = func(event, lambda_context)

                        # Process result with standardized attributes
                        success = True
                        complete_event_attrs = {}

                        if isinstance(result, dict) and 'statusCode' in result:
                            span.set_attribute(HTTP_RESPONSE_STATUS_CODE, result['statusCode'])
                            complete_event_attrs['status_code'] = result['statusCode']

                            # Per OTel spec for HTTP: only 5xx are server errors, 4xx are client errors
                            # Leave status UNSET for HTTP success - don't call set_status
                            if result['statusCode'] >= 500:
                                success = False
                                span.set_status(Status(StatusCode.ERROR, f"HTTP {result['statusCode']}"))
                            elif result['statusCode'] >= 400:
                                success = False
                            # HTTP success: leave UNSET per OTel spec
                        else:
                            # Non-HTTP response: set OK for success
                            span.set_status(Status(StatusCode.OK))

                        # Add completion event with success indicator
                        complete_event_attrs['success'] = success
                        span.add_event("lambda.invocation.complete", complete_event_attrs)

                    return result

                except Exception as e:

                    # Add failed completion event with error attribute (only if span exists)
                    if span is not None and hasattr(span, 'is_recording') and span.is_recording():
                        span.add_event("lambda.invocation.complete", {
                            'success': False,
                            'error': type(e).__name__
                        })

                        # Record the exception in the span
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))

                    # Log error
                    print(f"Lambda execution failed: {e}")
                    raise

                finally:
                    # Always detach context if we attached it
                    if token is not None:
                        otel_context.detach(token)

                    # Force flush if enabled
                    if auto_flush:
                        print(f"[Rebrandly OTEL] Lambda '{span_name}', flushing...", flush=True)
                        flush_success = self.force_flush(timeout_millis=1000)
                        if not flush_success:
                            print("[Rebrandly OTEL] Force flush may not have completed fully", flush=True)

                        # Also call shutdown to ensure exporters are closed
                        print(f"[Rebrandly OTEL] Shutting down OTEL providers...", flush=True)
                        self.shutdown()
                        print(f"[Rebrandly OTEL] Shutdown complete", flush=True)

            return wrapper
        return decorator

    def aws_message_handler(self,
                            name: Optional[str] = None,
                            attributes: Optional[Dict[str, Any]] = None,
                            kind: SpanKind = SpanKind.CONSUMER,
                            auto_flush: bool = True):
        """
        Decorator for AWS message handlers (SQS/SNS record processing).
        Requires a record object parameter to the function.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(record=None, *args, **kwargs):
                # Determine span name
                span_name = name or f"message.{func.__name__}"
                start_func = datetime.now()

                # Build span attributes
                span_attributes = attributes.copy() if attributes else {}
                span_attributes['messaging.operation'] = 'process'

                # Check if the record body contains an API Gateway event
                record_body = None
                is_api_gateway_record = False
                actual_kind = kind

                if record and isinstance(record, dict):
                    # Try to get body from SQS record
                    if 'body' in record:
                        try:
                            record_body = json.loads(record['body'])
                        except (json.JSONDecodeError, TypeError):
                            record_body = None
                    # Try to get message from SNS record
                    elif 'Sns' in record and 'Message' in record['Sns']:
                        try:
                            record_body = json.loads(record['Sns']['Message'])
                        except (json.JSONDecodeError, TypeError):
                            record_body = None

                # If the body looks like an API Gateway event, extract HTTP attributes
                if record_body and isinstance(record_body, dict) and is_api_gateway_event(record_body):
                    is_api_gateway_record = True
                    http_attrs, updated_span_name = extract_api_gateway_http_attributes(record_body)
                    span_attributes.update(http_attrs)
                    # Update span name to HTTP format if not explicitly set
                    if not name and updated_span_name:
                        span_name = updated_span_name
                    # Change span kind to SERVER for HTTP requests
                    actual_kind = SpanKind.SERVER

                result = None
                try:
                    # Create span and execute function
                    span_function = self.span
                    if record is not None and (('MessageAttributes' in record or 'messageAttributes' in record) or ('Sns' in record and 'MessageAttributes' in record['Sns'])):
                        span_function = self.aws_message_span
                        evt = extract_event_from(record)
                        if evt:
                            span_attributes['event.type'] = evt

                    with span_function(span_name, message=record, attributes=span_attributes, kind=actual_kind) as span_context:
                        # Add processing start event with standardized name
                        span_context.add_event("message.processing.start", {})

                        # Execute the actual handler function
                        result = func(record, *args, **kwargs)

                        # Process result
                        success = True
                        complete_event_attrs = {}

                        has_http_status = False
                        if result and isinstance(result, dict):
                            if 'statusCode' in result:
                                has_http_status = True
                                span_context.set_attribute("http.response.status_code", result['statusCode'])

                                # Per OTel spec for HTTP: only 5xx are server errors
                                if result['statusCode'] >= 500:
                                    success = False
                                    span_context.set_status(
                                        Status(StatusCode.ERROR, f"Handler returned {result['statusCode']}")
                                    )
                                elif result['statusCode'] >= 400:
                                    success = False
                                # HTTP success: leave UNSET per OTel spec

                            # Add custom result attributes if present
                            if 'processed' in result:
                                complete_event_attrs['processed'] = result['processed']
                                span_context.set_attribute("message.processed", result['processed'])
                            if 'skipped' in result:
                                complete_event_attrs['skipped'] = result['skipped']
                                span_context.set_attribute("message.skipped", result['skipped'])

                        # Non-HTTP response: set OK for success
                        if not has_http_status:
                            span_context.set_status(Status(StatusCode.OK))

                        # Add completion event with standardized name
                        complete_event_attrs['success'] = success
                        span_context.add_event("message.processing.complete", complete_event_attrs)

                        return result

                except Exception as e:
                    # Record the exception in the span
                    if 'span_context' in locals():
                        span_context.record_exception(e)
                        span_context.set_status(Status(StatusCode.ERROR, str(e)))

                        # Add failed processing event
                        span_context.add_event("message.processing.complete", {
                            'success': False,
                            'error': type(e).__name__
                        })

                    # Re-raise the exception
                    raise

                finally:
                    if auto_flush:
                        print(f"[Rebrandly OTEL] Lambda '{span_name}', flushing...", flush=True)
                        flush_success = self.force_flush(start_datetime=start_func, timeout_millis=1000)
                        if not flush_success:
                            print("[Rebrandly OTEL] Force flush may not have completed fully", flush=True)

                        # Also call shutdown to ensure exporters are closed
                        print(f"[Rebrandly OTEL] Shutting down OTEL providers...", flush=True)
                        self.shutdown()
                        print(f"[Rebrandly OTEL] Shutdown complete", flush=True)

            return wrapper
        return decorator

    def force_flush(self, start_datetime: datetime=None, timeout_millis: int = 1000) -> bool:
        """
        Force flush all telemetry data.
        This is CRITICAL for Lambda functions to ensure data is sent before function freezes.

        Args:
            start_datetime: Optional start time for system metrics capture
            timeout_millis: Maximum time to wait for flush in milliseconds

        Returns:
            True if all flushes succeeded, False otherwise
        """
        success = True

        if start_datetime is not None:
            end_func = datetime.now()
            cpu_percent = psutil.cpu_percent(interval=0.1)  # Shorter interval for Lambda
            memory = psutil.virtual_memory()

            # Record metrics using standardized names (with safety checks)
            try:
                if self.meter.GlobalMetrics.memory_usage_bytes:
                    self.meter.GlobalMetrics.memory_usage_bytes.set(memory.used)
                if self.meter.GlobalMetrics.cpu_usage_percentage:
                    self.meter.GlobalMetrics.cpu_usage_percentage.set(cpu_percent)
            except Exception as e:
                print(f"[Rebrandly OTEL] Warning: Could not record system metrics: {e}")

            print(f"Function Memory usage: {memory.percent}%, CPU usage: {cpu_percent}%")

        try:
            # Flush traces
            if self._tracer:
                if not self._tracer.force_flush(timeout_millis):
                    success = False

            # Flush metrics
            if self._meter:
                if not self._meter.force_flush(timeout_millis):
                    success = False

            # Flush logs
            if self._logger:
                if not self._logger.force_flush(timeout_millis):
                    success = False

            # Add a small delay to ensure network operations complete
            time.sleep(0.1)

        except Exception as e:
            print(f"[Rebrandly OTEL] Error during force flush: {e}")
            success = False

        return success

    def shutdown(self):
        """
        Shutdown all OTEL components gracefully.
        Call this at the end of your Lambda handler if you want to ensure clean shutdown.
        """
        try:
            if self._tracer:
                self._tracer.shutdown()
            if self._meter:
                self._meter.shutdown()
            if self._logger:
                self._logger.shutdown()
        except Exception as e:
            print(f"[Rebrandly OTEL] Error during shutdown: {e}")

    def _detect_lambda_trigger(self, event: Any) -> str:
        """Detect Lambda trigger type from event."""
        if not event or not isinstance(event, dict):
            return 'direct'

        if 'Records' in event:
            first_record = event['Records'][0] if event['Records'] else None
            if first_record:
                event_source = first_record.get('eventSource', '')
                if event_source == 'aws:sqs':
                    return 'sqs'
                elif event_source == 'aws:sns':
                    return 'sns'
                elif event_source == 'aws:s3':
                    return 's3'
                elif event_source == 'aws:kinesis':
                    return 'kinesis'
                elif event_source == 'aws:dynamodb':
                    return 'dynamodb'

        if 'httpMethod' in event:
            return 'api_gateway'
        if 'requestContext' in event and 'http' in event.get('requestContext', {}):
            return 'api_gateway_v2'
        if event.get('source') == 'aws.events':
            return 'eventbridge'
        if event.get('source') == 'aws.scheduler':
            return 'eventbridge_scheduler'
        if 'jobName' in event:
            return 'batch'

        return 'unknown'

    def set_baggage(self, key: str, value: str):
        """Set baggage item."""
        return baggage.set_baggage(key, value)

    def get_baggage(self, key: str) -> Optional[str]:
        """Get baggage item."""
        return baggage.get_baggage(key)

    def inject_context(self, carrier: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Inject trace context into headers for outbound requests."""
        if carrier is None:
            carrier = {}
        propagate.inject(carrier)
        return carrier

    def extract_context(self, carrier: Dict[str, Any]) -> otel_context.Context:
        """Extract trace context from incoming request headers."""
        return propagate.extract(carrier)

    def attach_context(self, carrier: Dict[str, Any]) -> object:
        """Extract and attach context, returning a token for cleanup."""
        ctx = self.extract_context(carrier)
        return otel_context.attach(ctx)

    def detach_context(self, token):
        """Detach a previously attached context."""
        otel_context.detach(token)

    @contextmanager
    def aws_message_span(self,
                         name: str,
                         message: Dict[str, Any]=None,
                         attributes: Optional[Dict[str, Any]] = None,
                         kind: SpanKind = SpanKind.CONSUMER):
        """Create span from AWS message - properly handling trace context."""

        from opentelemetry import trace, context as otel_context

        combined_attributes = attributes or {}
        combined_attributes['messaging.operation'] = 'process'

        # Extract message attributes for linking/attributes
        if message and isinstance(message, dict):
            # Add message-specific attributes
            if 'Sns' in message:
                sns_msg = message['Sns']
                if sns_msg.get('MessageId'):
                    combined_attributes['messaging.message_id'] = sns_msg['MessageId']
                if sns_msg.get('Subject'):
                    combined_attributes['messaging.sns.subject'] = sns_msg['Subject']
                if sns_msg.get('TopicArn'):
                    combined_attributes['messaging.destination'] = sns_msg['TopicArn']
                combined_attributes['messaging.system'] = 'aws_sns'

            elif 'messageId' in message:
                # SQS message
                combined_attributes['messaging.message_id'] = message['messageId']
                if 'eventSource' in message:
                    # Convert AWS eventSource format (aws:sqs) to OTel format (aws_sqs)
                    combined_attributes['messaging.system'] = message['eventSource'].replace(':', '_')


            if 'awsRegion' in message:
                combined_attributes['cloud.region'] = message['awsRegion']

            evt = extract_event_from(message)
            if evt:
                combined_attributes['event.type'] = evt


        # Use the tracer's start_span method directly to ensure it works
        # This creates a child span of whatever is currently active
        with self.tracer.start_span(
                name=name,
                attributes=combined_attributes,
                kind=kind
        ) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise


# Create Singleton instance
otel = RebrandlyOTEL()

# Export commonly used functions
span = otel.span
aws_message_span = otel.aws_message_span
traces = otel.trace_decorator
tracer = otel.tracer
meter = otel.meter
logger = otel.logger.logger
lambda_handler = otel.lambda_handler
aws_message_handler = otel.aws_message_handler
initialize = otel.initialize
inject_context = otel.inject_context
extract_context = otel.extract_context
attach_context = otel.attach_context
detach_context = otel.detach_context
force_flush = otel.force_flush
shutdown = otel.shutdown

# Attach logging levels to logger for convenience
# This allows: from rebrandly_otel import logger; logger.setLevel(logger.INFO)
import logging as _logging
logger.DEBUG = _logging.DEBUG
logger.INFO = _logging.INFO
logger.WARNING = _logging.WARNING
logger.ERROR = _logging.ERROR
logger.CRITICAL = _logging.CRITICAL
logger.NOTSET = _logging.NOTSET
logger.setLevel = otel.logger.setLevel
logger.getLogger = otel.logger.getLogger
