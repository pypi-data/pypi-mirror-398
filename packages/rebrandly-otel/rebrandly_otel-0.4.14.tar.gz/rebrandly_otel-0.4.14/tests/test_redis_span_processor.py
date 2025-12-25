"""
Tests for RedisSpanProcessor
"""

import pytest
from unittest.mock import MagicMock
from src.redis_span_processor import RedisSpanProcessor


class TestRedisSpanProcessor:
    """Test Redis Span Processor"""

    @pytest.fixture
    def processor(self):
        """Create a RedisSpanProcessor instance"""
        return RedisSpanProcessor()

    @pytest.fixture
    def mock_span(self):
        """Create a mock span"""
        span = MagicMock()
        span.set_attribute = MagicMock()
        return span

    def test_processor_initializes(self, processor):
        """Test that processor initializes correctly"""
        assert processor.name == 'RedisSpanProcessor'

    def test_processor_implements_span_processor_interface(self, processor):
        """Test that processor implements all required methods"""
        assert hasattr(processor, 'on_start')
        assert hasattr(processor, 'on_end')
        assert hasattr(processor, 'shutdown')
        assert hasattr(processor, 'force_flush')

    def test_on_start_ignores_non_redis_spans(self, processor, mock_span):
        """Test that processor ignores non-Redis spans"""
        mock_span.attributes = {'db.system': 'mysql'}

        processor.on_start(mock_span)

        # Verify no attributes were set
        mock_span.set_attribute.assert_not_called()

    def test_on_start_sets_db_name_from_database_index(self, processor, mock_span):
        """Test extracting db.name from db.redis.database_index"""
        mock_span.attributes = {
            'db.system': 'redis',
            'db.redis.database_index': 2
        }

        processor.on_start(mock_span)

        # Verify db.name was set correctly
        mock_span.set_attribute.assert_called_once_with('db.name', 'redis-2')

    def test_on_start_sets_db_name_from_connection_string(self, processor, mock_span):
        """Test extracting db.name from connection string"""
        mock_span.attributes = {
            'db.system': 'redis',
            'db.connection_string': 'redis://localhost:6379/3'
        }

        processor.on_start(mock_span)

        # Verify db.name was set correctly
        mock_span.set_attribute.assert_called_once_with('db.name', 'redis-3')

    def test_on_start_defaults_to_redis(self, processor, mock_span):
        """Test fallback to 'redis' when no database index found"""
        mock_span.attributes = {
            'db.system': 'redis'
        }

        processor.on_start(mock_span)

        # Verify db.name was set to default
        mock_span.set_attribute.assert_called_once_with('db.name', 'redis')

    def test_on_start_does_not_override_existing_db_name(self, processor, mock_span):
        """Test that existing db.name is not overridden"""
        mock_span.attributes = {
            'db.system': 'redis',
            'db.name': 'custom-redis-name',
            'db.redis.database_index': 5
        }

        processor.on_start(mock_span)

        # Verify db.name was not changed
        mock_span.set_attribute.assert_not_called()

    def test_on_start_sets_db_statement_from_operation(self, processor, mock_span):
        """Test setting db.statement from db.operation"""
        mock_span.attributes = {
            'db.system': 'redis',
            'db.operation': 'GET'
        }

        processor.on_start(mock_span)

        # Verify both db.name and db.statement were set
        assert mock_span.set_attribute.call_count == 2
        calls = [call.args for call in mock_span.set_attribute.call_args_list]
        assert ('db.name', 'redis') in calls
        assert ('db.statement', 'GET') in calls

    def test_on_start_handles_exceptions_gracefully(self, processor, mock_span):
        """Test that exceptions don't crash the processor"""
        mock_span.attributes = {'db.system': 'redis'}
        mock_span.set_attribute.side_effect = Exception("Attribute error")

        # Should not raise exception
        processor.on_start(mock_span)

    def test_on_end_is_noop(self, processor, mock_span):
        """Test that on_end does nothing"""
        processor.on_end(mock_span)
        # No assertion needed - just verify it doesn't crash

    def test_force_flush_returns_true(self, processor):
        """Test that force_flush always returns True"""
        assert processor.force_flush() is True
        assert processor.force_flush(timeout_millis=5000) is True

    def test_shutdown_is_noop(self, processor):
        """Test that shutdown does nothing"""
        processor.shutdown()
        # No assertion needed - just verify it doesn't crash


class TestExtractDbName:
    """Test database name extraction logic"""

    @pytest.fixture
    def processor(self):
        return RedisSpanProcessor()

    def test_extract_from_database_index(self, processor):
        """Test extraction from db.redis.database_index"""
        attributes = {'db.redis.database_index': 0}
        assert processor._extract_db_name(attributes) == 'redis-0'

        attributes = {'db.redis.database_index': 15}
        assert processor._extract_db_name(attributes) == 'redis-15'

    def test_extract_from_redis_url(self, processor):
        """Test extraction from redis:// URL"""
        attributes = {'db.connection_string': 'redis://localhost:6379/0'}
        assert processor._extract_db_name(attributes) == 'redis-0'

        attributes = {'db.connection_string': 'redis://host.example.com:6379/5'}
        assert processor._extract_db_name(attributes) == 'redis-5'

    def test_extract_from_rediss_url(self, processor):
        """Test extraction from rediss:// (SSL) URL"""
        attributes = {'db.connection_string': 'rediss://localhost:6379/2'}
        assert processor._extract_db_name(attributes) == 'redis-2'

    def test_extract_with_auth_in_url(self, processor):
        """Test extraction from URL with authentication"""
        attributes = {'db.connection_string': 'redis://user:pass@host:6379/3'}
        assert processor._extract_db_name(attributes) == 'redis-3'

    def test_extract_priority_database_index_over_connection_string(self, processor):
        """Test that db.redis.database_index takes priority"""
        attributes = {
            'db.redis.database_index': 3,
            'db.connection_string': 'redis://localhost:6379/5'
        }
        assert processor._extract_db_name(attributes) == 'redis-3'

    def test_extract_fallback_to_redis(self, processor):
        """Test fallback when no database info available"""
        attributes = {}
        assert processor._extract_db_name(attributes) == 'redis'

        attributes = {'db.namespace': 'localhost:6379'}
        assert processor._extract_db_name(attributes) == 'redis'

    def test_extract_handles_invalid_connection_string(self, processor):
        """Test handling of invalid connection strings"""
        attributes = {'db.connection_string': 'invalid-url'}
        assert processor._extract_db_name(attributes) == 'redis'

        attributes = {'db.connection_string': 'redis://localhost'}
        assert processor._extract_db_name(attributes) == 'redis'

    def test_extract_handles_none_connection_string(self, processor):
        """Test handling of None connection string"""
        attributes = {'db.connection_string': None}
        assert processor._extract_db_name(attributes) == 'redis'

    def test_on_start_preserves_existing_db_statement(self, processor):
        """Test that existing db.statement is not overridden"""
        mock_span = MagicMock()
        mock_span.attributes = {
            'db.system': 'redis',
            'db.statement': 'CUSTOM STATEMENT'
        }
        mock_span.set_attribute = MagicMock()

        processor = RedisSpanProcessor()
        processor.on_start(mock_span)

        # Should only set db.name, not db.statement
        mock_span.set_attribute.assert_called_once_with('db.name', 'redis')

    def test_on_start_handles_missing_attributes(self, processor):
        """Test handling of None/missing attributes"""
        mock_span = MagicMock()
        mock_span.attributes = None

        processor = RedisSpanProcessor()
        # Should not crash
        processor.on_start(mock_span)
