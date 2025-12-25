# logs.py
"""Logging implementation for Rebrandly OTEL SDK."""
import logging
from datetime import datetime
from typing import Optional
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
    ConsoleLogExporter,
    SimpleLogRecordProcessor
)
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry._logs import set_logger_provider

from .otel_utils import *


class HybridJsonFormatter(logging.Formatter):
    """
    Formatter that outputs: timestamp [level]: message {json_metadata}
    Matches Node.js Winston hybrid format for consistency.
    """

    def __init__(self, service_name, service_version):
        super().__init__()
        self.service_name = service_name
        self.service_version = service_version

    def format(self, record):
        # Base format: timestamp [level]: message
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname.lower()
        message = record.getMessage()

        # Build metadata dictionary
        metadata = {
            'service': self.service_name,
            'version': self.service_version,
        }

        # Add trace context if present (using camelCase to match Node.js)
        if hasattr(record, 'trace_id') and record.trace_id != '0':
            metadata['traceId'] = record.trace_id
        if hasattr(record, 'span_id') and record.span_id != '0':
            metadata['spanId'] = record.span_id

        # Add any extra fields from logger.info("msg", extra={...})
        # Exclude standard logging fields
        standard_fields = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
            'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName', 'exc_info',
            'exc_text', 'stack_info', 'trace_id', 'span_id', 'taskName'
        }

        for key, value in record.__dict__.items():
            if key not in standard_fields and not key.startswith('_'):
                metadata[key] = value

        # Format output
        metadata_str = json.dumps(metadata, default=str)
        return f"{timestamp} [{level}]: {message} {metadata_str}"


class RebrandlyLogger:
    """Wrapper for OpenTelemetry logging with Rebrandly-specific features."""

    # Expose logging levels for convenience (compatible with standard logging)
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    NOTSET = logging.NOTSET

    def __init__(self):
        self._logger: Optional[logging.Logger] = None
        self._provider: Optional[LoggerProvider] = None
        self._setup_logging()

    def _setup_logging(self):
        """Initialize logging with configured exporters."""

        # Create provider with resource
        self._provider = LoggerProvider(resource=create_resource())

        # Add console exporter for local debugging
        if is_otel_debug():
            console_exporter = ConsoleLogExporter()
            self._provider.add_log_record_processor(SimpleLogRecordProcessor(console_exporter))

        # Add OTLP exporter if configured
        otel_endpoint = get_otlp_endpoint()
        if otel_endpoint:
            otlp_exporter = OTLPLogExporter(
                timeout=5,
                endpoint=otel_endpoint
            )
            batch_processor = BatchLogRecordProcessor(otlp_exporter, export_timeout_millis=get_millis_batch_time())
            self._provider.add_log_record_processor(batch_processor)

        set_logger_provider(self._provider)

        # Configure standard logging
        self._configure_standard_logging()

    def _configure_standard_logging(self):
        """Configure standard Python logging with OTEL handler."""
        # Get root logger
        root_logger = logging.getLogger()

        # Only configure basic logging if no handlers exist (not in Lambda)
        if not root_logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)

            formatter = HybridJsonFormatter(
                service_name=get_service_name(),
                service_version=get_service_version()
            )
            handler.setFormatter(formatter)

            root_logger.addHandler(handler)
            root_logger.setLevel(logging.INFO)

        # Add custom filter to inject trace context into log records
        class TraceContextFilter(logging.Filter):
            """Filter that adds trace context to log records"""
            def filter(self, record):
                # Always set trace context attributes (even if no span is active)
                try:
                    from opentelemetry import trace

                    span = trace.get_current_span()
                    if span and span.get_span_context():
                        span_context = span.get_span_context()
                        if span_context.trace_id and span_context.span_id:
                            # Add trace context as log record attributes (for structured logging)
                            record.trace_id = format(span_context.trace_id, '032x')
                            record.span_id = format(span_context.span_id, '016x')
                        else:
                            record.trace_id = '0'
                            record.span_id = '0'
                    else:
                        record.trace_id = '0'
                        record.span_id = '0'
                except Exception:
                    # Silently ignore errors to avoid breaking logging
                    record.trace_id = '0'
                    record.span_id = '0'

                return True

        # Create filter instance
        trace_filter = TraceContextFilter()

        # Add trace context filter to all existing handlers
        for handler in root_logger.handlers:
            handler.addFilter(trace_filter)

        # Add OTEL handler without removing existing handlers
        otel_handler = LoggingHandler(logger_provider=self._provider)
        otel_handler.setLevel(logging.INFO)

        # Add trace context filter to OTEL handler
        otel_handler.addFilter(trace_filter)

        # Add filter to prevent OpenTelemetry's internal logs from being captured
        # This prevents infinite recursion when OTEL tries to log warnings
        otel_handler.addFilter(lambda record: not record.name.startswith('opentelemetry'))

        root_logger.addHandler(otel_handler)

        # Create service-specific logger
        self._logger = logging.getLogger(get_service_name())


    @property
    def logger(self) -> logging.Logger:
        """Get the standard Python logger."""
        if not self._logger:
            self._logger = logging.getLogger(get_service_name())
        return self._logger

    def getLogger(self) -> logging.Logger:
        """
        Get the internal logger instance.
        Alias for the logger property for consistency with standard logging API.
        """
        return self.logger

    def setLevel(self, level: int):
        """
        Set the logging level for both the internal logger and OTEL handler.

        Args:
            level: Logging level (e.g., logging.INFO, logging.DEBUG, logging.WARNING)
        """
        # Set level on the service-specific logger using the original unbound method
        # This avoids infinite recursion if the logger's setLevel has been monkey-patched
        if self._logger:
            logging.Logger.setLevel(self._logger, level)

        # Set level on the OTEL handler
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, LoggingHandler):
                handler.setLevel(level)

    def force_flush(self, timeout_millis: int = 5000) -> bool:
        """
        Force flush all pending logs.

        Args:
            timeout_millis: Maximum time to wait for flush in milliseconds

        Returns:
            True if flush succeeded, False otherwise
        """
        if not self._provider:
            return True

        try:
            # Force flush the logger provider
            success = self._provider.force_flush(timeout_millis)

            # Also flush Python's logging handlers
            if self._logger:
                for handler in self._logger.handlers:
                    if hasattr(handler, 'flush'):
                        handler.flush()

            return success
        except Exception as e:
            print(f"[Logger] Error during force flush: {e}")
            return False

    def shutdown(self):
        """Shutdown the logger provider."""
        if self._provider:
            try:
                self.force_flush()
                self._provider.shutdown()
                print("[Logger] Shutdown completed")
            except Exception as e:
                print(f"[Logger] Error during shutdown: {e}")
