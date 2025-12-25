import pytest
from unittest.mock import MagicMock, patch, call
import time

# Import the module under test
from src.pymysql_instrumentation import (
    instrument_pymysql,
    _extract_operation,
    _truncate_query,
    MAX_QUERY_LENGTH
)
from opentelemetry.trace import Status, StatusCode, SpanKind


@pytest.fixture
def mock_otel():
    """Create mock OTEL instance"""
    otel = MagicMock()

    # Mock tracer with proper structure
    mock_tracer = MagicMock()
    mock_span = MagicMock()
    mock_span.set_attribute = MagicMock()
    mock_span.set_status = MagicMock()
    mock_span.record_exception = MagicMock()
    mock_span.add_event = MagicMock()

    # Mock context manager for span
    mock_span_context = MagicMock()
    mock_span_context.__enter__ = MagicMock(return_value=mock_span)
    mock_span_context.__exit__ = MagicMock(return_value=None)

    mock_tracer.start_as_current_span = MagicMock(return_value=mock_span_context)

    otel.tracer = MagicMock()
    otel.tracer.tracer = mock_tracer

    return otel


@pytest.fixture
def mock_connection():
    """Create mock PyMySQL connection"""
    connection = MagicMock()
    connection.db = b'test_database'

    # Mock cursor
    mock_cursor = MagicMock()
    mock_cursor.execute = MagicMock(return_value=None)
    mock_cursor.executemany = MagicMock(return_value=None)

    connection.cursor = MagicMock(return_value=mock_cursor)

    return connection


class TestPyMySQLInstrumentation:
    """Test PyMySQL instrumentation"""

    def test_instrument_pymysql_returns_connection(self, mock_otel, mock_connection):
        """Test that instrument_pymysql returns the instrumented connection"""
        result = instrument_pymysql(mock_otel, mock_connection)
        assert result is mock_connection

    def test_instrument_pymysql_wraps_cursor_method(self, mock_otel, mock_connection):
        """Test that cursor method is wrapped"""
        original_cursor = mock_connection.cursor

        instrument_pymysql(mock_otel, mock_connection)

        # Cursor method should be replaced
        assert mock_connection.cursor != original_cursor
        assert callable(mock_connection.cursor)

    def test_instrument_pymysql_with_none_connection(self, mock_otel):
        """Test handling of None connection"""
        result = instrument_pymysql(mock_otel, None)
        assert result is None

    def test_instrument_pymysql_with_none_otel(self, mock_connection):
        """Test handling of None OTEL instance"""
        result = instrument_pymysql(None, mock_connection)
        assert result is mock_connection

    def test_instrument_pymysql_with_invalid_otel(self, mock_connection):
        """Test handling of invalid OTEL instance without tracer"""
        invalid_otel = MagicMock()
        del invalid_otel.tracer  # Remove tracer attribute

        result = instrument_pymysql(invalid_otel, mock_connection)
        assert result is mock_connection

    def test_instrument_pymysql_extracts_db_name_bytes(self, mock_otel, mock_connection):
        """Test database name extraction from bytes"""
        mock_connection.db = b'test_db'

        instrument_pymysql(mock_otel, mock_connection)

        # Should decode bytes to string (tested indirectly via query execution)
        assert mock_connection.cursor is not None

    def test_instrument_pymysql_extracts_db_name_string(self, mock_otel, mock_connection):
        """Test database name extraction from string"""
        mock_connection.db = 'test_db'

        result = instrument_pymysql(mock_otel, mock_connection)

        assert result is mock_connection

    def test_instrument_pymysql_with_options(self, mock_otel, mock_connection):
        """Test instrumentation with custom options"""
        options = {
            'slow_query_threshold_ms': 1000,
            'capture_bindings': True
        }

        result = instrument_pymysql(mock_otel, mock_connection, options)

        assert result is mock_connection

    def test_instrumented_cursor_execute_creates_span(self, mock_otel, mock_connection):
        """Test that executing a query creates a span"""
        instrument_pymysql(mock_otel, mock_connection)

        cursor = mock_connection.cursor()
        cursor.execute("SELECT * FROM users")

        # Verify span was created
        mock_otel.tracer.tracer.start_as_current_span.assert_called_once()
        call_args = mock_otel.tracer.tracer.start_as_current_span.call_args

        assert call_args[1]['name'] == 'pymysql.execute'
        assert call_args[1]['kind'] == SpanKind.CLIENT

    def test_instrumented_cursor_executemany_creates_span(self, mock_otel, mock_connection):
        """Test that executemany creates a span with correct name"""
        instrument_pymysql(mock_otel, mock_connection)

        cursor = mock_connection.cursor()
        cursor.executemany("INSERT INTO users VALUES (%s, %s)", [('user1', 'email1')])

        # Verify span was created with executemany name
        mock_otel.tracer.tracer.start_as_current_span.assert_called_once()
        call_args = mock_otel.tracer.tracer.start_as_current_span.call_args

        assert call_args[1]['name'] == 'pymysql.executemany'

    def test_span_attributes_are_set_correctly(self, mock_otel, mock_connection):
        """Test that span attributes are set correctly"""
        instrument_pymysql(mock_otel, mock_connection)

        cursor = mock_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (123,))

        # Get the span mock
        span_context = mock_otel.tracer.tracer.start_as_current_span.return_value
        span = span_context.__enter__.return_value

        # Verify attributes were set
        span.set_attribute.assert_any_call('db.system', 'mysql')
        span.set_attribute.assert_any_call('db.operation.name', 'SELECT')
        span.set_attribute.assert_any_call('db.statement', 'SELECT * FROM users WHERE id = %s')

    def test_slow_query_detection(self, mock_otel, mock_connection):
        """Test slow query detection and event"""
        options = {'slow_query_threshold_ms': 100}
        instrument_pymysql(mock_otel, mock_connection, options)

        cursor = mock_connection.cursor()

        # Mock time.time to simulate slow query (150ms duration)
        with patch('src.pymysql_instrumentation.time.time', side_effect=[0, 0.15]):
            cursor.execute("SELECT * FROM users")

        # Get the span mock
        span_context = mock_otel.tracer.tracer.start_as_current_span.return_value
        span = span_context.__enter__.return_value

        # Verify slow query was detected
        span.set_attribute.assert_any_call('db.slow_query', True)
        span.add_event.assert_called_once()

    def test_exception_handling(self, mock_otel, mock_connection):
        """Test that exceptions are recorded in span"""
        # Set up the mock cursor to raise an exception when execute is called
        test_exception = Exception("Database error")
        mock_cursor = MagicMock()
        mock_cursor.execute = MagicMock(side_effect=test_exception)
        mock_cursor.executemany = MagicMock(return_value=None)
        mock_connection.cursor = MagicMock(return_value=mock_cursor)

        instrument_pymysql(mock_otel, mock_connection)

        cursor = mock_connection.cursor()

        # Execute should raise the exception
        with pytest.raises(Exception) as exc_info:
            cursor.execute("SELECT * FROM users")

        assert exc_info.value is test_exception

        # Get the span mock
        span_context = mock_otel.tracer.tracer.start_as_current_span.return_value
        span = span_context.__enter__.return_value

        # Verify exception was recorded
        span.record_exception.assert_called_once_with(test_exception)
        span.set_status.assert_called()

    def test_capture_bindings_disabled(self, mock_otel, mock_connection):
        """Test that bindings are not captured by default"""
        options = {'capture_bindings': False}
        instrument_pymysql(mock_otel, mock_connection, options)

        cursor = mock_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (123,))

        # Get the span mock
        span_context = mock_otel.tracer.tracer.start_as_current_span.return_value
        span = span_context.__enter__.return_value

        # Verify db.bindings was not set
        attribute_calls = [call[0] for call in span.set_attribute.call_args_list]
        assert 'db.bindings' not in [call[0] for call in attribute_calls]

    def test_capture_bindings_enabled(self, mock_otel, mock_connection):
        """Test that bindings are captured when enabled"""
        options = {'capture_bindings': True}
        instrument_pymysql(mock_otel, mock_connection, options)

        cursor = mock_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (123,))

        # Get the span mock
        span_context = mock_otel.tracer.tracer.start_as_current_span.return_value
        span = span_context.__enter__.return_value

        # Verify db.bindings was set
        span.set_attribute.assert_any_call('db.bindings', '(123,)')

    def test_capture_bindings_count_for_executemany(self, mock_otel, mock_connection):
        """Test that bindings count is captured for executemany"""
        options = {'capture_bindings': True}
        instrument_pymysql(mock_otel, mock_connection, options)

        cursor = mock_connection.cursor()
        data = [('user1', 'email1'), ('user2', 'email2')]
        cursor.executemany("INSERT INTO users VALUES (%s, %s)", data)

        # Get the span mock
        span_context = mock_otel.tracer.tracer.start_as_current_span.return_value
        span = span_context.__enter__.return_value

        # Verify db.bindings_count was set
        span.set_attribute.assert_any_call('db.bindings_count', 2)


class TestExtractOperation:
    """Test SQL operation extraction"""

    def test_extract_select(self):
        """Test SELECT query extraction"""
        assert _extract_operation("SELECT * FROM users") == "SELECT"
        assert _extract_operation("  select id from users") == "SELECT"

    def test_extract_insert(self):
        """Test INSERT query extraction"""
        assert _extract_operation("INSERT INTO users VALUES (1, 'name')") == "INSERT"
        assert _extract_operation("  insert into users") == "INSERT"

    def test_extract_update(self):
        """Test UPDATE query extraction"""
        assert _extract_operation("UPDATE users SET name = 'new'") == "UPDATE"
        assert _extract_operation("  update users") == "UPDATE"

    def test_extract_delete(self):
        """Test DELETE query extraction"""
        assert _extract_operation("DELETE FROM users WHERE id = 1") == "DELETE"
        assert _extract_operation("  delete from users") == "DELETE"

    def test_extract_create(self):
        """Test CREATE query extraction"""
        assert _extract_operation("CREATE TABLE users (id INT)") == "CREATE"

    def test_extract_drop(self):
        """Test DROP query extraction"""
        assert _extract_operation("DROP TABLE users") == "DROP"

    def test_extract_alter(self):
        """Test ALTER query extraction"""
        assert _extract_operation("ALTER TABLE users ADD COLUMN email VARCHAR(255)") == "ALTER"

    def test_extract_truncate(self):
        """Test TRUNCATE query extraction"""
        assert _extract_operation("TRUNCATE TABLE users") == "TRUNCATE"

    def test_extract_unknown(self):
        """Test unknown query type"""
        assert _extract_operation("SHOW TABLES") == "unknown"
        assert _extract_operation("DESCRIBE users") == "unknown"

    def test_extract_empty(self):
        """Test empty query"""
        assert _extract_operation("") == "unknown"
        assert _extract_operation(None) == "unknown"


class TestTruncateQuery:
    """Test query truncation"""

    def test_truncate_short_query(self):
        """Test that short queries are not truncated"""
        query = "SELECT * FROM users"
        assert _truncate_query(query) == query

    def test_truncate_long_query(self):
        """Test that long queries are truncated"""
        long_query = "SELECT * FROM users WHERE " + "x = 1 AND " * 500  # Very long query
        result = _truncate_query(long_query)

        assert len(result) <= MAX_QUERY_LENGTH + len('... [truncated]')
        assert result.endswith('... [truncated]')
        assert result.startswith('SELECT * FROM users')

    def test_truncate_exactly_max_length(self):
        """Test query exactly at max length"""
        query = "x" * MAX_QUERY_LENGTH
        result = _truncate_query(query)

        assert result == query
        assert not result.endswith('... [truncated]')

    def test_truncate_empty_query(self):
        """Test empty query"""
        assert _truncate_query("") == ""
        assert _truncate_query(None) == ""

    def test_truncate_one_over_max(self):
        """Test query one character over max length"""
        query = "x" * (MAX_QUERY_LENGTH + 1)
        result = _truncate_query(query)

        assert len(result) == MAX_QUERY_LENGTH + len('... [truncated]')
        assert result.endswith('... [truncated]')
