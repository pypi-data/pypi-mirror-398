"""
SQLite3 instrumentation for Rebrandly OTEL SDK
Provides query tracing and slow query detection
"""

import os
import time
import functools
from opentelemetry.trace import Status, StatusCode, SpanKind

# Environment configuration
SLOW_QUERY_THRESHOLD_MS = int(os.getenv('SQLITE3_SLOW_QUERY_THRESHOLD_MS', '1000'))
MAX_QUERY_LENGTH = 2000  # Truncate long queries


def instrument_sqlite3(otel_instance, connection, options=None):
    """
    Instrument a SQLite3 connection for OpenTelemetry tracing

    Args:
        otel_instance: The RebrandlyOTEL instance
        connection: The sqlite3 connection to instrument
        options: Configuration options dict with:
            - slow_query_threshold_ms: Threshold for slow query detection (default: 1000ms)
            - capture_bindings: Include query bindings in spans (default: False for security)

    Returns:
        The instrumented connection
    """
    if options is None:
        options = {}

    slow_query_threshold_ms = options.get('slow_query_threshold_ms', SLOW_QUERY_THRESHOLD_MS)
    capture_bindings = options.get('capture_bindings', False)

    if not connection:
        print('[Rebrandly OTEL SQLite3] No connection provided for instrumentation')
        return connection

    if not otel_instance or not hasattr(otel_instance, 'tracer'):
        print('[Rebrandly OTEL SQLite3] No valid OTEL instance provided for instrumentation')
        return connection

    # Get the underlying OpenTelemetry tracer from RebrandlyOTEL instance
    tracer = otel_instance.tracer.tracer

    # Extract database name from connection
    db_name = _get_database_name(connection)

    # Wrap the cursor method to return instrumented cursors
    original_cursor = connection.cursor

    def instrumented_cursor(*args, **kwargs):
        cursor = original_cursor(*args, **kwargs)
        return _instrument_cursor(cursor, tracer, slow_query_threshold_ms, capture_bindings, db_name)

    connection.cursor = instrumented_cursor

    # Instrument connection-level execute methods (SQLite supports direct connection execution)
    _instrument_connection_execute_methods(connection, tracer, slow_query_threshold_ms, capture_bindings, db_name)

    return connection


def _get_database_name(connection):
    """
    Extract database name/path from SQLite connection

    Args:
        connection: sqlite3.Connection object

    Returns:
        Database identifier (file path or ":memory:")
    """
    # Try to get database list via PRAGMA
    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA database_list")
        result = cursor.fetchone()
        if result and len(result) >= 3:
            # result is (seq, name, file)
            db_path = result[2]
            if db_path:
                return db_path
            else:
                return ':memory:'
        cursor.close()
    except Exception:
        pass

    # Fallback to unknown
    return 'unknown'


def _instrument_connection_execute_methods(connection, tracer, slow_query_threshold_ms, capture_bindings, db_name):
    """
    Instrument connection-level execute methods (execute, executemany, executescript)
    SQLite supports direct connection execution which is commonly used.
    """
    # Store original methods
    original_execute = getattr(connection, 'execute', None)
    original_executemany = getattr(connection, 'executemany', None)
    original_executescript = getattr(connection, 'executescript', None)

    if original_execute:
        @functools.wraps(original_execute)
        def instrumented_execute(query, args=()):
            return _trace_query(
                original_execute,
                tracer,
                slow_query_threshold_ms,
                capture_bindings,
                db_name,
                query,
                args,
                many=False,
                script=False
            )
        connection.execute = instrumented_execute

    if original_executemany:
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
                many=True,
                script=False
            )
        connection.executemany = instrumented_executemany

    if original_executescript:
        @functools.wraps(original_executescript)
        def instrumented_executescript(script):
            return _trace_query(
                original_executescript,
                tracer,
                slow_query_threshold_ms,
                capture_bindings,
                db_name,
                script,
                None,
                many=False,
                script=True
            )
        connection.executescript = instrumented_executescript


def _instrument_cursor(cursor, tracer, slow_query_threshold_ms, capture_bindings, db_name):
    """
    Instrument a cursor's execute methods
    """
    original_execute = cursor.execute
    original_executemany = cursor.executemany
    original_executescript = getattr(cursor, 'executescript', None)

    @functools.wraps(original_execute)
    def instrumented_execute(query, args=()):
        return _trace_query(
            original_execute,
            tracer,
            slow_query_threshold_ms,
            capture_bindings,
            db_name,
            query,
            args,
            many=False,
            script=False
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
            many=True,
            script=False
        )

    cursor.execute = instrumented_execute
    cursor.executemany = instrumented_executemany

    if original_executescript:
        @functools.wraps(original_executescript)
        def instrumented_executescript(script):
            return _trace_query(
                original_executescript,
                tracer,
                slow_query_threshold_ms,
                capture_bindings,
                db_name,
                script,
                None,
                many=False,
                script=True
            )
        cursor.executescript = instrumented_executescript

    return cursor


def _trace_query(func, tracer, slow_query_threshold_ms, capture_bindings, db_name, query, args, many=False, script=False):
    """
    Trace a query execution with OpenTelemetry
    """
    if script:
        # Special handling for executescript
        operation = 'SCRIPT'
        truncated_query = _truncate_script(query)
    else:
        operation = _extract_operation(query)
        truncated_query = _truncate_query(query)

    # Start span
    if script:
        span_name = "sqlite3.executescript"
    elif many:
        span_name = "sqlite3.executemany"
    else:
        span_name = "sqlite3.execute"

    with tracer.start_as_current_span(
        name=span_name,
        kind=SpanKind.CLIENT
    ) as span:
        # Set database attributes
        span.set_attribute('db.system', 'sqlite')
        span.set_attribute('db.operation.name', operation)
        span.set_attribute('db.statement', truncated_query)

        # Set database name
        if db_name:
            span.set_attribute('db.name', db_name)
        else:
            span.set_attribute('db.name', 'unknown')

        # Add bindings if enabled (be cautious with sensitive data)
        if capture_bindings and args and not script:
            if many:
                span.set_attribute('db.bindings_count', len(args))
            else:
                span.set_attribute('db.bindings', str(args))

        start_time = time.time()

        try:
            # Execute the query
            if script or args is None:
                result = func(query)
            else:
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
    Extract operation type from SQL statement (extended for SQLite)

    Args:
        sql: SQL query string

    Returns:
        Operation type (SELECT, INSERT, UPDATE, PRAGMA, VACUUM, etc.)
    """
    if not sql:
        return 'unknown'

    normalized = sql.strip().upper()

    # Standard SQL operations
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

    # SQLite-specific operations
    if normalized.startswith('PRAGMA'):
        return 'PRAGMA'
    if normalized.startswith('VACUUM'):
        return 'VACUUM'
    if normalized.startswith('ATTACH'):
        return 'ATTACH'
    if normalized.startswith('DETACH'):
        return 'DETACH'
    if normalized.startswith('ANALYZE'):
        return 'ANALYZE'
    if normalized.startswith('BEGIN'):
        return 'BEGIN'
    if normalized.startswith('COMMIT'):
        return 'COMMIT'
    if normalized.startswith('ROLLBACK'):
        return 'ROLLBACK'
    if normalized.startswith('EXPLAIN'):
        return 'EXPLAIN'
    if normalized.startswith('REINDEX'):
        return 'REINDEX'

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


def _truncate_script(script):
    """
    Truncate SQL scripts for span attributes (scripts can contain multiple statements)

    Args:
        script: SQL script string

    Returns:
        Truncated script with marker
    """
    if not script:
        return ''

    # For scripts, truncate to first 100 characters and add marker
    max_script_length = 100
    if len(script) <= max_script_length:
        return script

    return script[:max_script_length] + '... [multi-statement script]'
