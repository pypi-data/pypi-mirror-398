import pytest
from unittest.mock import MagicMock, patch

# Import the module under test
from src.flask_support import setup_flask


@pytest.fixture
def mock_otel():
    """Create mock OTEL instance"""
    otel = MagicMock()
    otel.tracer = MagicMock()
    otel.meter = MagicMock()
    otel.logger = MagicMock()
    otel.attach_context = MagicMock(return_value='mock_token')
    otel.detach_context = MagicMock()
    otel.force_flush = MagicMock()
    return otel


@pytest.fixture
def mock_app():
    """Create mock Flask app"""
    app = MagicMock()
    app.before_request = MagicMock()
    app.after_request = MagicMock()
    app.register_error_handler = MagicMock()
    return app


class TestFlaskSupport:
    """Test Flask integration setup function"""

    def test_setup_flask_registers_all_hooks(self, mock_otel, mock_app):
        """Test that setup_flask registers all required hooks"""
        # Call setup_flask
        result = setup_flask(mock_otel, mock_app)

        # Verify before_request hook is registered
        mock_app.before_request.assert_called_once()
        assert len(mock_app.before_request.call_args_list) == 1

        # Verify after_request hook is registered
        mock_app.after_request.assert_called_once()
        assert len(mock_app.after_request.call_args_list) == 1

        # Verify error handler is registered
        mock_app.register_error_handler.assert_called_once()
        error_handler_call = mock_app.register_error_handler.call_args
        assert error_handler_call[0][0] == Exception

        # Verify the app is returned
        assert result == mock_app

    def test_setup_flask_hooks_are_callable(self, mock_otel, mock_app):
        """Test that registered hooks are callable functions"""
        # Call setup_flask
        setup_flask(mock_otel, mock_app)

        # Get the registered callbacks
        before_request_callback = mock_app.before_request.call_args[0][0]
        after_request_callback = mock_app.after_request.call_args[0][0]
        error_handler_callback = mock_app.register_error_handler.call_args[0][1]

        # Verify they are callable
        assert callable(before_request_callback)
        assert callable(after_request_callback)
        assert callable(error_handler_callback)

    def test_setup_flask_before_request_hook_is_lambda(self, mock_otel, mock_app):
        """Test that before_request hook is a lambda calling app_before_request"""
        # Call setup_flask
        setup_flask(mock_otel, mock_app)

        # Get the registered before_request callback
        before_request_callback = mock_app.before_request.call_args[0][0]

        # Verify it's a lambda function (check by calling it)
        with patch('src.flask_support.app_before_request') as mock_before_request:
            before_request_callback()
            mock_before_request.assert_called_once_with(mock_otel)

    def test_setup_flask_after_request_hook_is_lambda(self, mock_otel, mock_app):
        """Test that after_request hook is a lambda calling app_after_request"""
        # Call setup_flask
        setup_flask(mock_otel, mock_app)

        # Get the registered after_request callback
        after_request_callback = mock_app.after_request.call_args[0][0]

        # Create mock response
        mock_response = MagicMock()

        # Verify it's a lambda function
        with patch('src.flask_support.app_after_request') as mock_after_request:
            mock_after_request.return_value = mock_response
            result = after_request_callback(mock_response)
            mock_after_request.assert_called_once_with(mock_otel, mock_response)
            assert result == mock_response

    def test_setup_flask_error_handler_is_lambda(self, mock_otel, mock_app):
        """Test that error handler is a lambda calling flask_error_handler"""
        # Call setup_flask
        setup_flask(mock_otel, mock_app)

        # Get the registered error handler callback
        error_handler_callback = mock_app.register_error_handler.call_args[0][1]

        # Create mock exception
        mock_exception = Exception("Test error")

        # Verify it's a lambda function
        with patch('src.flask_support.flask_error_handler') as mock_error_handler:
            mock_error_handler.return_value = ('error response', 500)
            result = error_handler_callback(mock_exception)
            mock_error_handler.assert_called_once_with(mock_otel, mock_exception)
            assert result == ('error response', 500)

    def test_setup_flask_with_none_otel(self, mock_app):
        """Test setup_flask handles None OTEL instance gracefully"""
        # This might raise an exception or handle gracefully
        # Depending on implementation, adjust assertion
        try:
            result = setup_flask(None, mock_app)
            # If it doesn't raise, verify hooks are still registered
            assert result == mock_app
        except (AttributeError, TypeError):
            # Expected if setup_flask doesn't handle None
            pass

    def test_setup_flask_with_none_app(self, mock_otel):
        """Test setup_flask handles None app gracefully"""
        # This should raise an AttributeError since app is None
        with pytest.raises(AttributeError):
            setup_flask(mock_otel, None)

    def test_setup_flask_returns_app(self, mock_otel, mock_app):
        """Test that setup_flask returns the app instance"""
        result = setup_flask(mock_otel, mock_app)
        assert result is mock_app


class TestFlaskSpanStatus:
    """Test Flask span status handling per OpenTelemetry semantic conventions"""

    def test_flask_after_request_leaves_status_unset_for_2xx(self, mock_otel):
        """Test that 2xx responses leave span status UNSET"""
        from src.flask_support import app_after_request
        from opentelemetry.trace import StatusCode

        # Create mock request with span
        mock_request = MagicMock()
        mock_span = MagicMock()
        mock_span.is_recording.return_value = True
        mock_request.span = mock_span
        mock_request.span_context = MagicMock()
        mock_request.trace_token = 'token'

        # Create mock response with 200 status
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Patch request context
        with patch('src.flask_support.request', mock_request):
            result = app_after_request(mock_otel, mock_response)

        # Verify span status was NOT set (left UNSET per OTEL spec)
        mock_span.set_status.assert_not_called()
        assert result == mock_response

    def test_flask_after_request_leaves_status_unset_for_4xx(self, mock_otel):
        """Test that 4xx responses leave span status UNSET per OTEL spec"""
        from src.flask_support import app_after_request
        from opentelemetry.trace import StatusCode

        # Create mock request with span
        mock_request = MagicMock()
        mock_span = MagicMock()
        mock_span.is_recording.return_value = True
        mock_request.span = mock_span
        mock_request.span_context = MagicMock()
        mock_request.trace_token = 'token'

        # Create mock response with 404 status
        mock_response = MagicMock()
        mock_response.status_code = 404

        # Patch request context
        with patch('src.flask_support.request', mock_request):
            result = app_after_request(mock_otel, mock_response)

        # Verify span status was NOT set (left UNSET per OTEL spec)
        mock_span.set_status.assert_not_called()
        assert result == mock_response

    def test_flask_after_request_sets_error_for_5xx(self, mock_otel):
        """Test that 5xx responses set span status to ERROR"""
        from src.flask_support import app_after_request
        from opentelemetry.trace import Status, StatusCode

        # Create mock request with span
        mock_request = MagicMock()
        mock_span = MagicMock()
        mock_span.is_recording.return_value = True
        mock_request.span = mock_span
        mock_request.span_context = MagicMock()
        mock_request.trace_token = 'token'

        # Create mock response with 500 status
        mock_response = MagicMock()
        mock_response.status_code = 500

        # Patch request context
        with patch('src.flask_support.request', mock_request):
            result = app_after_request(mock_otel, mock_response)

        # Verify span status was set to ERROR
        mock_span.set_status.assert_called_once()
        call_args = mock_span.set_status.call_args[0][0]
        assert call_args.status_code == StatusCode.ERROR
        assert result == mock_response
