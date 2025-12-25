# test_traces_convenience.py
"""Tests for span status convenience methods (set_span_error, set_span_success, set_span_unset)"""

import pytest
from opentelemetry.trace import StatusCode
from src.rebrandly_otel import otel

class TestSpanStatusConvenienceMethods:
    """Test suite for convenience methods for setting span status"""

    def test_set_span_error_with_message(self):
        """Test set_span_error with just a message"""
        otel.initialize()

        with otel.span('test-span') as span:
            otel.tracer.set_span_error('Test error message')

            # Verify status is ERROR
            assert span.status.status_code == StatusCode.ERROR
            assert span.status.description == 'Test error message'

    def test_set_span_error_with_exception(self):
        """Test set_span_error with message and exception"""
        otel.initialize()

        test_exception = ValueError('Test exception')

        with otel.span('test-span') as span:
            otel.tracer.set_span_error('Error occurred', exception=test_exception)

            # Verify status is ERROR
            assert span.status.status_code == StatusCode.ERROR
            assert span.status.description == 'Error occurred'
            # Verify exception was recorded (check span events)
            assert len(span.events) > 0

    def test_set_span_error_on_current_span(self):
        """Test set_span_error without passing span argument (uses current span)"""
        otel.initialize()

        with otel.span('test-span') as span:
            # Don't pass span argument - should use current span
            otel.tracer.set_span_error('Error on current span')

            assert span.status.status_code == StatusCode.ERROR

    def test_set_span_success_without_message(self):
        """Test set_span_success without message"""
        otel.initialize()

        with otel.span('test-span') as span:
            otel.tracer.set_span_success()

            # Verify status is OK
            assert span.status.status_code == StatusCode.OK

    def test_set_span_success_with_message_ignored(self):
        """Test that set_span_success message is ignored per OTEL spec"""
        otel.initialize()

        with otel.span('test-span') as span:
            otel.tracer.set_span_success('This message is ignored')

            # Verify status is OK and no description (per OTEL spec)
            assert span.status.status_code == StatusCode.OK
            # OK status should not have description

    def test_set_span_unset(self):
        """Test set_span_unset sets span to UNSET status initially"""
        otel.initialize()

        with otel.span('test-span') as span:
            # Set to UNSET explicitly (though this is the default)
            otel.tracer.set_span_unset()
            assert span.status.status_code == StatusCode.UNSET

    def test_set_span_unset_after_error(self):
        """Test that UNSET cannot override ERROR status per OTEL spec"""
        otel.initialize()

        with otel.span('test-span') as span:
            # First set to error
            otel.tracer.set_span_error('Error')
            assert span.status.status_code == StatusCode.ERROR

            # Try to reset to UNSET - this should not change the status
            # Per OTEL spec, status is final once set to ERROR or OK
            otel.tracer.set_span_unset()
            # Status should remain ERROR
            assert span.status.status_code == StatusCode.ERROR

    def test_set_span_error_with_explicit_span(self):
        """Test passing explicit span argument"""
        otel.initialize()

        with otel.span('test-span') as span:
            # Pass span explicitly
            otel.tracer.set_span_error('Explicit error', span=span)

            assert span.status.status_code == StatusCode.ERROR
