"""
PyMySQL instrumentation for Rebrandly OTEL SDK
Provides query tracing and slow query detection
"""

import os
import time
import functools
from opentelemetry.trace import Status, StatusCode, SpanKind

# Environment configuration
SLOW_QUERY_THRESHOLD_MS = int(os.getenv('PYMYSQL_SLOW_QUERY_THRESHOLD_MS', '1500'))
MAX_QUERY_LENGTH = 2000  # Truncate long queries


def instrument_pymysql(otel_instance, connection, options=None):
    """
    Instrument a PyMySQL connection for OpenTelemetry tracing

    Args:
        otel_instance: The RebrandlyOTEL instance
        connection: The PyMySQL connection to instrument
        options: Configuration options dict with:
            - slow_query_threshold_ms: Threshold for slow query detection (default: 1500ms)
            - capture_bindings: Include query bindings in spans (default: False for security)

    Returns:
        The instrumented connection
    """
    if options is None:
        options = {}

    slow_query_threshold_ms = options.get('slow_query_threshold_ms', SLOW_QUERY_THRESHOLD_MS)
    capture_bindings = options.get('capture_bindings', False)

    if not connection:
        print('[Rebrandly OTEL PyMySQL] No connection provided for instrumentation')
        return connection

    if not otel_instance or not hasattr(otel_instance, 'tracer'):
        print('[Rebrandly OTEL PyMySQL] No valid OTEL instance provided for instrumentation')
        return connection

    # Get the underlying OpenTelemetry tracer from RebrandlyOTEL instance
    tracer = otel_instance.tracer.tracer

    # Extract database name from connection
    db_name = getattr(connection, 'db', None) or getattr(connection, 'database', None)
    if db_name and isinstance(db_name, bytes):
        db_name = db_name.decode('utf-8')

    # Wrap the cursor method to return instrumented cursors
    original_cursor = connection.cursor

    def instrumented_cursor(*args, **kwargs):
        cursor = original_cursor(*args, **kwargs)
        return _instrument_cursor(cursor, tracer, slow_query_threshold_ms, capture_bindings, db_name)

    connection.cursor = instrumented_cursor

    return connection


def _instrument_cursor(cursor, tracer, slow_query_threshold_ms, capture_bindings, db_name=None):
    """
    Instrument a cursor's execute methods
    """
    original_execute = cursor.execute
    original_executemany = cursor.executemany

    @functools.wraps(original_execute)
    def instrumented_execute(query, args=None):
        return _trace_query(
            original_execute,
            tracer,
            slow_query_threshold_ms,
            capture_bindings,
            db_name,
            query,
            args,
            many=False
        )

    @functools.wraps(original_executemany)
    def instrumented_executemany(query, args):
        return _trace_query(
            original_executemany,
            tracer,
            slow_query_threshold_ms,
            capture_bindings,
            db_name,
            query,
            args,
            many=True
        )

    cursor.execute = instrumented_execute
    cursor.executemany = instrumented_executemany

    return cursor


def _trace_query(func, tracer, slow_query_threshold_ms, capture_bindings, db_name, query, args, many=False):
    """
    Trace a query execution with OpenTelemetry
    """
    operation = _extract_operation(query)
    truncated_query = _truncate_query(query)

    # Start span
    span_name = f"pymysql.{'executemany' if many else 'execute'}"

    with tracer.start_as_current_span(
        name=span_name,
        kind=SpanKind.CLIENT
    ) as span:
        # Set database attributes
        span.set_attribute('db.system', 'mysql')
        span.set_attribute('db.operation.name', operation)
        span.set_attribute('db.statement', truncated_query)

        # Set database name if available
        if db_name:
            span.set_attribute('db.name', db_name)
        else:
            span.set_attribute('db.name', 'unknown')

        # Add bindings if enabled (be cautious with sensitive data)
        if capture_bindings and args:
            if many:
                span.set_attribute('db.bindings_count', len(args))
            else:
                span.set_attribute('db.bindings', str(args))

        start_time = time.time()

        try:
            # Execute the query
            result = func(query, args)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            span.set_attribute('db.duration_ms', duration_ms)

            # Check for slow query
            if duration_ms >= slow_query_threshold_ms:
                span.set_attribute('db.slow_query', True)
                span.add_event('slow_query_detected', {
                    'db.duration_ms': duration_ms,
                    'db.threshold_ms': slow_query_threshold_ms
                })

            # Set success status
            span.set_status(Status(StatusCode.OK))

            return result

        except Exception as error:
            # Calculate duration even on error
            duration_ms = (time.time() - start_time) * 1000
            span.set_attribute('db.duration_ms', duration_ms)

            # Record exception
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, str(error)))

            raise


def _extract_operation(sql):
    """
    Extract operation type from SQL statement

    Args:
        sql: SQL query string

    Returns:
        Operation type (SELECT, INSERT, UPDATE, etc.)
    """
    if not sql:
        return 'unknown'

    normalized = sql.strip().upper()

    if normalized.startswith('SELECT'):
        return 'SELECT'
    if normalized.startswith('INSERT'):
        return 'INSERT'
    if normalized.startswith('UPDATE'):
        return 'UPDATE'
    if normalized.startswith('DELETE'):
        return 'DELETE'
    if normalized.startswith('CREATE'):
        return 'CREATE'
    if normalized.startswith('DROP'):
        return 'DROP'
    if normalized.startswith('ALTER'):
        return 'ALTER'
    if normalized.startswith('TRUNCATE'):
        return 'TRUNCATE'

    return 'unknown'


def _truncate_query(sql):
    """
    Truncate long queries for span attributes

    Args:
        sql: SQL query string

    Returns:
        Truncated query
    """
    if not sql:
        return ''
    if len(sql) <= MAX_QUERY_LENGTH:
        return sql
    return sql[:MAX_QUERY_LENGTH] + '... [truncated]'
