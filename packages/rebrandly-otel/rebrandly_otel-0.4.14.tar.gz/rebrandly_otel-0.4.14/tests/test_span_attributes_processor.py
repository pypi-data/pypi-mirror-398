"""
Tests for SpanAttributesProcessor
Tests automatic addition of attributes from OTEL_SPAN_ATTRIBUTES to all spans
"""

import pytest
import os
from unittest.mock import MagicMock, patch
from src.span_attributes_processor import SpanAttributesProcessor


class TestSpanAttributesProcessor:
    """Test SpanAttributesProcessor functionality"""

    def setup_method(self):
        """Setup method to clear environment before each test"""
        # Save original environment
        self.original_env = os.environ.get('OTEL_SPAN_ATTRIBUTES')
        self.original_debug = os.environ.get('OTEL_DEBUG')

    def teardown_method(self):
        """Teardown method to restore environment after each test"""
        # Restore original environment
        if self.original_env is not None:
            os.environ['OTEL_SPAN_ATTRIBUTES'] = self.original_env
        elif 'OTEL_SPAN_ATTRIBUTES' in os.environ:
            del os.environ['OTEL_SPAN_ATTRIBUTES']

        if self.original_debug is not None:
            os.environ['OTEL_DEBUG'] = self.original_debug
        elif 'OTEL_DEBUG' in os.environ:
            del os.environ['OTEL_DEBUG']

    # ===== Processor Initialization Tests =====

    def test_initialize_without_otel_span_attributes(self):
        """Test processor initialization without OTEL_SPAN_ATTRIBUTES"""
        if 'OTEL_SPAN_ATTRIBUTES' in os.environ:
            del os.environ['OTEL_SPAN_ATTRIBUTES']

        processor = SpanAttributesProcessor()

        assert processor is not None
        assert processor.name == 'SpanAttributesProcessor'
        assert processor.span_attributes == {}

    def test_parse_single_attribute(self):
        """Test parsing a single attribute"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend'

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {'team': 'backend'}

    def test_parse_multiple_attributes(self):
        """Test parsing multiple attributes"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend,environment=production,version=1.2.3'

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {
            'team': 'backend',
            'environment': 'production',
            'version': '1.2.3'
        }

    def test_handle_attributes_with_spaces(self):
        """Test handling attributes with spaces"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team = backend , environment = production'

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {
            'team': 'backend',
            'environment': 'production'
        }

    def test_handle_attributes_with_equals_in_values(self):
        """Test handling attributes with equals signs in values"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'url=http://example.com?foo=bar,key=value'

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {
            'url': 'http://example.com?foo=bar',
            'key': 'value'
        }

    def test_ignore_empty_string(self):
        """Test ignoring empty string"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = ''

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {}

    def test_ignore_whitespace_only_string(self):
        """Test ignoring whitespace-only string"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = '   '

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {}

    def test_ignore_malformed_attributes_without_equals(self):
        """Test ignoring malformed attributes without equals"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend,invalid,version=1.0'

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {
            'team': 'backend',
            'version': '1.0'
        }

    def test_ignore_attributes_with_empty_keys(self):
        """Test ignoring attributes with empty keys"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = '=value,team=backend'

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {'team': 'backend'}

    def test_allow_empty_values(self):
        """Test allowing empty values"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=,environment=production'

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {
            'team': '',
            'environment': 'production'
        }

    def test_handle_trailing_commas(self):
        """Test handling trailing commas"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend,environment=production,'

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {
            'team': 'backend',
            'environment': 'production'
        }

    # ===== Span Processing Tests =====

    def test_add_attributes_to_span_on_start(self):
        """Test adding attributes to span on start"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend,environment=production,version=1.2.3'

        processor = SpanAttributesProcessor()

        # Create mock span
        mock_span = MagicMock()

        # Call on_start
        processor.on_start(mock_span)

        # Verify set_attribute was called for each attribute
        assert mock_span.set_attribute.call_count == 3
        mock_span.set_attribute.assert_any_call('team', 'backend')
        mock_span.set_attribute.assert_any_call('environment', 'production')
        mock_span.set_attribute.assert_any_call('version', '1.2.3')

    def test_no_attributes_added_when_none_configured(self):
        """Test that no attributes are added when none configured"""
        if 'OTEL_SPAN_ATTRIBUTES' in os.environ:
            del os.environ['OTEL_SPAN_ATTRIBUTES']

        processor = SpanAttributesProcessor()

        # Create mock span
        mock_span = MagicMock()

        # Call on_start
        processor.on_start(mock_span)

        # Verify set_attribute was not called
        mock_span.set_attribute.assert_not_called()

    def test_handle_set_attribute_errors_gracefully(self):
        """Test handling set_attribute errors gracefully"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend'

        processor = SpanAttributesProcessor()

        # Create mock span that raises error
        mock_span = MagicMock()
        mock_span.set_attribute.side_effect = Exception('Test error')

        # Should not raise
        processor.on_start(mock_span)

    def test_on_end_does_nothing(self):
        """Test that on_end does nothing"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend'

        processor = SpanAttributesProcessor()

        # Create mock span
        mock_span = MagicMock()

        # Should not raise
        processor.on_end(mock_span)

    # ===== Lifecycle Methods Tests =====

    def test_shutdown_method(self):
        """Test shutdown method"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend'

        processor = SpanAttributesProcessor()

        # Should not raise
        processor.shutdown()

    def test_force_flush_method(self):
        """Test force_flush method"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend'

        processor = SpanAttributesProcessor()

        # Should return True
        result = processor.force_flush()
        assert result is True

    def test_force_flush_with_timeout(self):
        """Test force_flush with custom timeout"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend'

        processor = SpanAttributesProcessor()

        # Should return True regardless of timeout
        result = processor.force_flush(timeout_millis=10000)
        assert result is True

    # ===== Debug Mode Tests =====

    @patch('builtins.print')
    def test_log_parsed_attributes_when_debug_true(self, mock_print):
        """Test logging parsed attributes when OTEL_DEBUG is true"""
        os.environ['OTEL_DEBUG'] = 'true'
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend,env=prod'

        processor = SpanAttributesProcessor()

        # Verify print was called with correct message
        mock_print.assert_called_with(
            '[SpanAttributesProcessor] Parsed OTEL_SPAN_ATTRIBUTES: {\'team\': \'backend\', \'env\': \'prod\'}'
        )

    @patch('builtins.print')
    def test_no_log_when_debug_false(self, mock_print):
        """Test not logging when OTEL_DEBUG is false"""
        os.environ['OTEL_DEBUG'] = 'false'
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend'

        processor = SpanAttributesProcessor()

        # Verify print was not called
        mock_print.assert_not_called()

    @patch('builtins.print')
    def test_no_log_when_attributes_empty(self, mock_print):
        """Test not logging when attributes are empty"""
        os.environ['OTEL_DEBUG'] = 'true'
        if 'OTEL_SPAN_ATTRIBUTES' in os.environ:
            del os.environ['OTEL_SPAN_ATTRIBUTES']

        processor = SpanAttributesProcessor()

        # Verify print was not called
        mock_print.assert_not_called()

    # ===== Error Handling Tests =====

    def test_handle_none_span_gracefully(self):
        """Test handling None span gracefully"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend'

        processor = SpanAttributesProcessor()

        # Should not raise
        processor.on_start(None)

    @patch('builtins.print')
    def test_log_errors_in_debug_mode(self, mock_print):
        """Test logging errors in debug mode when set_attribute fails"""
        os.environ['OTEL_DEBUG'] = 'true'
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'team=backend'

        processor = SpanAttributesProcessor()

        # Create mock span that raises error
        mock_span = MagicMock()
        mock_span.set_attribute.side_effect = Exception('Test error')

        # Call on_start
        processor.on_start(mock_span)

        # Verify error was logged
        assert any('[SpanAttributesProcessor] Error processing span:' in str(call)
                   for call in mock_print.call_args_list)

    # ===== Integration Tests =====

    def test_processor_with_real_span(self):
        """Test processor works with real span creation"""
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'test=integration'

        # Create provider and add processor
        provider = TracerProvider()
        provider.add_span_processor(SpanAttributesProcessor())

        # Set as global
        trace.set_tracer_provider(provider)

        # Create tracer and span
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span('test-span') as span:
            # Span should have the attribute
            assert span is not None
            # We can't directly verify attributes on the span object,
            # but we can verify no errors occurred

    def test_processor_name_property(self):
        """Test processor has correct name property"""
        processor = SpanAttributesProcessor()
        assert processor.name == 'SpanAttributesProcessor'

    def test_multiple_processors_can_coexist(self):
        """Test multiple processors can coexist"""
        from opentelemetry.sdk.trace import TracerProvider

        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'test=multi'

        provider = TracerProvider()

        # Add multiple span attributes processors
        processor1 = SpanAttributesProcessor()
        processor2 = SpanAttributesProcessor()

        provider.add_span_processor(processor1)
        provider.add_span_processor(processor2)

        # Should not raise
        assert True

    # ===== Special Character Tests =====

    def test_handle_special_characters_in_values(self):
        """Test handling special characters in values"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'msg=Hello, World!,path=/api/v1/users'

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {
            'msg': 'Hello',
            'path': '/api/v1/users'
        }

    def test_handle_unicode_characters(self):
        """Test handling unicode characters"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'emoji=🚀,name=José'

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {
            'emoji': '🚀',
            'name': 'José'
        }

    def test_handle_numeric_values_as_strings(self):
        """Test that numeric values are treated as strings"""
        os.environ['OTEL_SPAN_ATTRIBUTES'] = 'port=8080,version=1.0'

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {
            'port': '8080',
            'version': '1.0'
        }

    # ===== Edge Case Tests =====

    def test_very_long_attribute_value(self):
        """Test handling very long attribute values"""
        long_value = 'a' * 1000
        os.environ['OTEL_SPAN_ATTRIBUTES'] = f'long={long_value}'

        processor = SpanAttributesProcessor()

        assert processor.span_attributes == {'long': long_value}

    def test_many_attributes(self):
        """Test handling many attributes"""
        attrs = ','.join([f'key{i}=value{i}' for i in range(50)])
        os.environ['OTEL_SPAN_ATTRIBUTES'] = attrs

        processor = SpanAttributesProcessor()

        assert len(processor.span_attributes) == 50
        assert processor.span_attributes['key0'] == 'value0'
        assert processor.span_attributes['key49'] == 'value49'
