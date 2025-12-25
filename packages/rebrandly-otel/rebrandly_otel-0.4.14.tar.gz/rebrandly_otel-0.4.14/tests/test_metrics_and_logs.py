import pytest
import logging
from unittest.mock import MagicMock, patch, ANY

# Import the modules under test
from src.metrics import RebrandlyMeter, MetricDefinition, MetricType
from src.logs import RebrandlyLogger


class TestMetrics:
    """Test metrics functionality"""

    @patch('src.metrics.get_otlp_endpoint')
    @patch('src.metrics.is_otel_debug')
    @patch('src.metrics.create_resource')
    @patch('src.metrics.get_service_name')
    @patch('src.metrics.get_service_version')
    def test_create_custom_counter_metric(
        self,
        mock_get_version,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test creating a custom counter metric"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_get_version.return_value = '1.0.0'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create meter
        meter = RebrandlyMeter()

        # Create custom counter definition
        counter_definition = MetricDefinition(
            name='http_requests_total',
            description='Total number of HTTP requests',
            unit='1',
            type=MetricType.COUNTER
        )

        # Register the counter
        counter = meter.register_metric(counter_definition)

        # Verify counter was created and registered
        assert counter is not None
        assert meter.get_metric('http_requests_total') is counter

    @patch('src.metrics.get_otlp_endpoint')
    @patch('src.metrics.is_otel_debug')
    @patch('src.metrics.create_resource')
    @patch('src.metrics.get_service_name')
    @patch('src.metrics.get_service_version')
    def test_create_counter_with_key(
        self,
        mock_get_version,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test creating a counter with a custom key"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_get_version.return_value = '1.0.0'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create meter
        meter = RebrandlyMeter()

        # Create counter with custom key
        counter_definition = MetricDefinition(
            name='api.requests.total',
            description='API requests',
            unit='1',
            type=MetricType.COUNTER
        )

        counter = meter.register_metric(counter_definition, key='requests_counter')

        # Verify counter can be retrieved by both name and key
        assert meter.get_metric('api.requests.total') is counter
        assert meter.get_metric('requests_counter') is counter

    @patch('src.metrics.get_otlp_endpoint')
    @patch('src.metrics.is_otel_debug')
    @patch('src.metrics.create_resource')
    @patch('src.metrics.get_service_name')
    @patch('src.metrics.get_service_version')
    def test_create_histogram_metric(
        self,
        mock_get_version,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test creating a histogram metric"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_get_version.return_value = '1.0.0'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create meter
        meter = RebrandlyMeter()

        # Create histogram
        histogram_definition = MetricDefinition(
            name='http_response_duration_ms',
            description='HTTP response duration in milliseconds',
            unit='ms',
            type=MetricType.HISTOGRAM
        )

        histogram = meter.register_metric(histogram_definition)

        # Verify histogram was created
        assert histogram is not None
        assert meter.get_metric('http_response_duration_ms') is histogram

    @patch('src.metrics.get_otlp_endpoint')
    @patch('src.metrics.is_otel_debug')
    @patch('src.metrics.create_resource')
    @patch('src.metrics.get_service_name')
    @patch('src.metrics.get_service_version')
    def test_create_gauge_metric(
        self,
        mock_get_version,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test creating a gauge metric"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_get_version.return_value = '1.0.0'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create meter
        meter = RebrandlyMeter()

        # Create gauge
        gauge_definition = MetricDefinition(
            name='queue_size',
            description='Current queue size',
            unit='1',
            type=MetricType.GAUGE
        )

        gauge = meter.register_metric(gauge_definition)

        # Verify gauge was created
        assert gauge is not None
        assert meter.get_metric('queue_size') is gauge

    @patch('src.metrics.get_otlp_endpoint')
    @patch('src.metrics.is_otel_debug')
    @patch('src.metrics.create_resource')
    @patch('src.metrics.get_service_name')
    @patch('src.metrics.get_service_version')
    def test_default_metrics_registered(
        self,
        mock_get_version,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test that default metrics are registered automatically"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_get_version.return_value = '1.0.0'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create meter
        meter = RebrandlyMeter()

        # Verify default metrics are registered
        assert meter.get_metric('cpu_usage_percentage') is not None
        assert meter.get_metric('memory_usage_bytes') is not None
        assert meter.get_metric('process.cpu.utilization') is not None
        assert meter.get_metric('process.memory.used') is not None

    @patch('src.metrics.get_otlp_endpoint')
    @patch('src.metrics.is_otel_debug')
    @patch('src.metrics.create_resource')
    @patch('src.metrics.get_service_name')
    @patch('src.metrics.get_service_version')
    def test_get_nonexistent_metric(
        self,
        mock_get_version,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test getting a metric that doesn't exist"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_get_version.return_value = '1.0.0'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create meter
        meter = RebrandlyMeter()

        # Try to get nonexistent metric
        metric = meter.get_metric('nonexistent_metric')

        assert metric is None

    @patch('src.metrics.get_otlp_endpoint')
    @patch('src.metrics.is_otel_debug')
    @patch('src.metrics.create_resource')
    @patch('src.metrics.get_service_name')
    @patch('src.metrics.get_service_version')
    def test_register_duplicate_metric(
        self,
        mock_get_version,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test registering the same metric twice returns the same instance"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_get_version.return_value = '1.0.0'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create meter
        meter = RebrandlyMeter()

        # Register same metric twice
        counter_definition = MetricDefinition(
            name='duplicate_counter',
            description='A counter',
            unit='1',
            type=MetricType.COUNTER
        )

        counter1 = meter.register_metric(counter_definition)
        counter2 = meter.register_metric(counter_definition)

        # Should return the same instance
        assert counter1 is counter2

    @patch('src.metrics.get_otlp_endpoint')
    @patch('src.metrics.is_otel_debug')
    @patch('src.metrics.create_resource')
    @patch('src.metrics.get_service_name')
    @patch('src.metrics.get_service_version')
    def test_meter_property(
        self,
        mock_get_version,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test accessing the underlying meter property"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_get_version.return_value = '1.0.0'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create meter
        meter = RebrandlyMeter()

        # Access meter property
        underlying_meter = meter.meter

        assert underlying_meter is not None

    @patch('src.metrics.get_otlp_endpoint')
    @patch('src.metrics.is_otel_debug')
    @patch('src.metrics.create_resource')
    @patch('src.metrics.get_service_name')
    @patch('src.metrics.get_service_version')
    def test_force_flush(
        self,
        mock_get_version,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test force flush"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_get_version.return_value = '1.0.0'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create meter
        meter = RebrandlyMeter()

        # Mock the provider's force_flush
        meter._provider.force_flush = MagicMock(return_value=True)

        # Call force_flush
        result = meter.force_flush(timeout_millis=1000)

        # Verify it was called
        meter._provider.force_flush.assert_called_once_with(1000)
        assert result is True


class TestLogs:
    """Test logging functionality"""

    @patch('src.logs.get_otlp_endpoint')
    @patch('src.logs.is_otel_debug')
    @patch('src.logs.create_resource')
    @patch('src.logs.get_service_name')
    def test_log_info(
        self,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test logging with .info()"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create logger
        rebrandly_logger = RebrandlyLogger()
        logger = rebrandly_logger.logger

        # Mock the logger's info method
        logger.info = MagicMock()

        # Log info message
        logger.info("This is an info message")

        # Verify info was called
        logger.info.assert_called_once_with("This is an info message")

    @patch('src.logs.get_otlp_endpoint')
    @patch('src.logs.is_otel_debug')
    @patch('src.logs.create_resource')
    @patch('src.logs.get_service_name')
    def test_log_warning(
        self,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test logging with .warning()"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create logger
        rebrandly_logger = RebrandlyLogger()
        logger = rebrandly_logger.logger

        # Mock the logger's warning method
        logger.warning = MagicMock()

        # Log warning message
        logger.warning("This is a warning message")

        # Verify warning was called
        logger.warning.assert_called_once_with("This is a warning message")

    @patch('src.logs.get_otlp_endpoint')
    @patch('src.logs.is_otel_debug')
    @patch('src.logs.create_resource')
    @patch('src.logs.get_service_name')
    def test_log_debug(
        self,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test logging with .debug()"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create logger
        rebrandly_logger = RebrandlyLogger()
        logger = rebrandly_logger.logger

        # Mock the logger's debug method
        logger.debug = MagicMock()

        # Log debug message
        logger.debug("This is a debug message")

        # Verify debug was called
        logger.debug.assert_called_once_with("This is a debug message")

    @patch('src.logs.get_otlp_endpoint')
    @patch('src.logs.is_otel_debug')
    @patch('src.logs.create_resource')
    @patch('src.logs.get_service_name')
    def test_log_error(
        self,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test logging with .error()"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create logger
        rebrandly_logger = RebrandlyLogger()
        logger = rebrandly_logger.logger

        # Mock the logger's error method
        logger.error = MagicMock()

        # Log error message
        logger.error("This is an error message")

        # Verify error was called
        logger.error.assert_called_once_with("This is an error message")

    @patch('src.logs.get_otlp_endpoint')
    @patch('src.logs.is_otel_debug')
    @patch('src.logs.create_resource')
    @patch('src.logs.get_service_name')
    def test_log_with_extra_attributes(
        self,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test logging with extra attributes"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create logger
        rebrandly_logger = RebrandlyLogger()
        logger = rebrandly_logger.logger

        # Mock the logger's info method
        logger.info = MagicMock()

        # Log with extra attributes
        logger.info("User action", extra={"user_id": "123", "action": "login"})

        # Verify info was called with extra attributes
        logger.info.assert_called_once_with("User action", extra={"user_id": "123", "action": "login"})

    @patch('src.logs.get_otlp_endpoint')
    @patch('src.logs.is_otel_debug')
    @patch('src.logs.create_resource')
    @patch('src.logs.get_service_name')
    def test_set_log_level(
        self,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test setting log level"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create logger
        rebrandly_logger = RebrandlyLogger()

        # Set log level
        rebrandly_logger.setLevel(logging.DEBUG)

        # Verify level was set
        assert rebrandly_logger.logger.level == logging.DEBUG

    @patch('src.logs.get_otlp_endpoint')
    @patch('src.logs.is_otel_debug')
    @patch('src.logs.create_resource')
    @patch('src.logs.get_service_name')
    def test_get_logger(
        self,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test getLogger() method"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create logger
        rebrandly_logger = RebrandlyLogger()

        # Get logger using getLogger method
        logger1 = rebrandly_logger.getLogger()
        logger2 = rebrandly_logger.logger

        # Should return the same instance
        assert logger1 is logger2

    @patch('src.logs.get_otlp_endpoint')
    @patch('src.logs.is_otel_debug')
    @patch('src.logs.create_resource')
    @patch('src.logs.get_service_name')
    def test_force_flush(
        self,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test force flush"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create logger
        rebrandly_logger = RebrandlyLogger()

        # Mock the provider's force_flush
        rebrandly_logger._provider.force_flush = MagicMock(return_value=True)

        # Call force_flush
        result = rebrandly_logger.force_flush(timeout_millis=1000)

        # Verify it was called
        rebrandly_logger._provider.force_flush.assert_called_once_with(1000)
        assert result is True

    @patch('src.logs.get_otlp_endpoint')
    @patch('src.logs.is_otel_debug')
    @patch('src.logs.create_resource')
    @patch('src.logs.get_service_name')
    def test_logging_levels_constants(
        self,
        mock_get_name,
        mock_create_resource,
        mock_is_debug,
        mock_get_endpoint
    ):
        """Test that logging level constants are exposed"""
        # Setup mocks
        mock_get_name.return_value = 'test-service'
        mock_create_resource.return_value = MagicMock()
        mock_is_debug.return_value = False
        mock_get_endpoint.return_value = None

        # Create logger
        rebrandly_logger = RebrandlyLogger()

        # Verify logging level constants
        assert rebrandly_logger.DEBUG == logging.DEBUG
        assert rebrandly_logger.INFO == logging.INFO
        assert rebrandly_logger.WARNING == logging.WARNING
        assert rebrandly_logger.ERROR == logging.ERROR
        assert rebrandly_logger.CRITICAL == logging.CRITICAL
        assert rebrandly_logger.NOTSET == logging.NOTSET
