"""
Tests for automatic Redis instrumentation
"""

import pytest
from unittest.mock import MagicMock, patch, call
from src.traces import RebrandlyTracer
from src.redis_span_processor import RedisSpanProcessor

# Skip all tests in this module if Redis instrumentation package is not installed
pytest.importorskip(
    "opentelemetry.instrumentation.redis",
    reason="opentelemetry-instrumentation-redis not installed"
)


class TestAutomaticRedisInstrumentation:
    """Test automatic Redis instrumentation during SDK initialization"""

    def test_redis_instrumentor_called_on_tracer_init(self):
        """Test that RedisInstrumentor is called during tracer initialization"""
        with patch('opentelemetry.instrumentation.redis.RedisInstrumentor') as mock_instrumentor:
            mock_instance = MagicMock()
            mock_instance.is_instrumented_by_opentelemetry = False
            mock_instrumentor.return_value = mock_instance

            # Initialize tracer (triggers automatic Redis instrumentation)
            tracer = RebrandlyTracer()

            # Verify RedisInstrumentor was instantiated and instrument() was called
            mock_instrumentor.assert_called()
            mock_instance.instrument.assert_called_once()

    def test_redis_instrumentor_not_called_if_already_instrumented(self):
        """Test that instrumentation is skipped if already instrumented"""
        with patch('opentelemetry.instrumentation.redis.RedisInstrumentor') as mock_instrumentor:
            mock_instance = MagicMock()
            mock_instance.is_instrumented_by_opentelemetry = True
            mock_instrumentor.return_value = mock_instance

            # Initialize tracer
            tracer = RebrandlyTracer()

            # Verify instrument() was NOT called
            mock_instance.instrument.assert_not_called()

    def test_redis_span_processor_registered(self):
        """Test that RedisSpanProcessor is registered in the provider"""
        with patch('opentelemetry.instrumentation.redis.RedisInstrumentor'):
            tracer = RebrandlyTracer()

            # Check that RedisSpanProcessor was added to the provider
            processors = tracer._provider._active_span_processor._span_processors
            processor_types = [type(p).__name__ for p in processors]

            assert 'RedisSpanProcessor' in processor_types

    def test_redis_instrumentation_failure_does_not_crash_sdk(self):
        """Test that SDK initialization succeeds even if Redis instrumentation fails"""
        with patch('opentelemetry.instrumentation.redis.RedisInstrumentor') as mock_instrumentor:
            mock_instance = MagicMock()
            mock_instance.is_instrumented_by_opentelemetry = False
            mock_instance.instrument.side_effect = Exception("Instrumentation error")
            mock_instrumentor.return_value = mock_instance

            # Should not raise exception
            tracer = RebrandlyTracer()

            # Tracer should still be initialized
            assert tracer._tracer is not None
            assert tracer._provider is not None

    def test_missing_redis_package_handled(self):
        """Test that missing Redis package is handled gracefully"""
        with patch('opentelemetry.instrumentation.redis.RedisInstrumentor', side_effect=ImportError("No module named 'redis'")):
            # Should not raise exception
            tracer = RebrandlyTracer()

            # Tracer should still be initialized
            assert tracer._tracer is not None
            assert tracer._provider is not None

    def test_debug_mode_logs_success(self, capsys):
        """Test that debug mode logs successful instrumentation"""
        import os
        os.environ['OTEL_DEBUG'] = 'true'

        with patch('opentelemetry.instrumentation.redis.RedisInstrumentor') as mock_instrumentor:
            mock_instance = MagicMock()
            mock_instance.is_instrumented_by_opentelemetry = False
            mock_instrumentor.return_value = mock_instance

            # Initialize tracer
            tracer = RebrandlyTracer()

            # Capture output
            captured = capsys.readouterr()

            # Verify debug message was printed
            assert '[Rebrandly OTEL] Redis instrumentation enabled' in captured.out or \
                   '[RedisSpanProcessor] Initialized' in captured.out

        # Cleanup
        del os.environ['OTEL_DEBUG']

    def test_debug_mode_logs_errors(self, capsys):
        """Test that debug mode logs instrumentation errors"""
        import os
        os.environ['OTEL_DEBUG'] = 'true'

        with patch('opentelemetry.instrumentation.redis.RedisInstrumentor') as mock_instrumentor:
            mock_instance = MagicMock()
            mock_instance.is_instrumented_by_opentelemetry = False
            mock_instance.instrument.side_effect = Exception("Test error")
            mock_instrumentor.return_value = mock_instance

            # Initialize tracer
            tracer = RebrandlyTracer()

            # Capture output
            captured = capsys.readouterr()

            # Verify error message was printed
            assert '[Rebrandly OTEL] Redis instrumentation failed' in captured.out

        # Cleanup
        del os.environ['OTEL_DEBUG']


class TestRedisSpanProcessorIntegration:
    """Integration tests for RedisSpanProcessor with actual tracer"""

    def test_span_processor_in_provider(self):
        """Test that RedisSpanProcessor is properly integrated into the provider"""
        with patch('opentelemetry.instrumentation.redis.RedisInstrumentor'):
            tracer = RebrandlyTracer()

            # Get all span processors
            processors = tracer._provider._active_span_processor._span_processors

            # Find RedisSpanProcessor
            redis_processors = [p for p in processors if isinstance(p, RedisSpanProcessor)]

            assert len(redis_processors) == 1
            assert redis_processors[0].name == 'RedisSpanProcessor'

    def test_multiple_tracer_initializations_dont_duplicate_instrumentation(self):
        """Test that multiple tracer initializations don't duplicate Redis instrumentation"""
        with patch('opentelemetry.instrumentation.redis.RedisInstrumentor') as mock_instrumentor:
            mock_instance = MagicMock()
            mock_instance.is_instrumented_by_opentelemetry = False
            mock_instrumentor.return_value = mock_instance

            # Initialize first tracer
            tracer1 = RebrandlyTracer()

            # Set flag to indicate instrumentation happened
            mock_instance.is_instrumented_by_opentelemetry = True

            # Initialize second tracer
            tracer2 = RebrandlyTracer()

            # Verify instrument() was only called once
            assert mock_instance.instrument.call_count == 1
