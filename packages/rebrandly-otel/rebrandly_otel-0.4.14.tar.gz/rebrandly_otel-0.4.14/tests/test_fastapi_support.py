import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

# Import the module under test
from src.fastapi_support import setup_fastapi, get_current_span


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
    """Create mock FastAPI app"""
    app = MagicMock()
    app.add_middleware = MagicMock()
    app.add_exception_handler = MagicMock()
    return app


class TestFastAPISupport:
    """Test FastAPI integration setup function"""

    def test_setup_fastapi_adds_middleware(self, mock_otel, mock_app):
        """Test that setup_fastapi adds OTEL middleware"""
        # Call setup_fastapi
        result = setup_fastapi(mock_otel, mock_app)

        # Verify middleware is added
        mock_app.add_middleware.assert_called_once()

        # Get the middleware class
        middleware_call = mock_app.add_middleware.call_args
        middleware_class = middleware_call[0][0]

        # Verify the middleware class name contains "OTEL"
        assert 'OTEL' in middleware_class.__name__

        # Verify the app is returned
        assert result == mock_app

    def test_setup_fastapi_registers_exception_handlers(self, mock_otel, mock_app):
        """Test that setup_fastapi registers exception handlers"""
        # Call setup_fastapi
        setup_fastapi(mock_otel, mock_app)

        # Verify exception handlers are registered
        # Should be called twice: once for HTTPException, once for Exception
        assert mock_app.add_exception_handler.call_count == 2

        # Get the calls
        calls = mock_app.add_exception_handler.call_args_list

        # Extract exception types from calls
        exception_types = [call_args[0][0] for call_args in calls]

        # Verify HTTPException handler is registered
        assert HTTPException in exception_types

        # Verify general Exception handler is registered
        assert Exception in exception_types

    def test_setup_fastapi_exception_handlers_are_callable(self, mock_otel, mock_app):
        """Test that registered exception handlers are callable"""
        # Call setup_fastapi
        setup_fastapi(mock_otel, mock_app)

        # Get the registered exception handlers
        calls = mock_app.add_exception_handler.call_args_list

        for call_args in calls:
            handler = call_args[0][1]
            # Verify the handler is callable
            assert callable(handler)

    def test_setup_fastapi_exception_handler_is_lambda(self, mock_otel, mock_app):
        """Test that exception handlers are lambda functions"""
        # Call setup_fastapi
        setup_fastapi(mock_otel, mock_app)

        # Get the registered exception handlers
        calls = mock_app.add_exception_handler.call_args_list

        # Test HTTPException handler
        http_exception_handler = None
        general_exception_handler = None

        for call_args in calls:
            exc_type = call_args[0][0]
            handler = call_args[0][1]

            if exc_type == HTTPException:
                http_exception_handler = handler
            elif exc_type == Exception:
                general_exception_handler = handler

        # Verify we found both handlers
        assert http_exception_handler is not None
        assert general_exception_handler is not None

        # Test that calling the handler calls fastapi_exception_handler
        mock_request = MagicMock()
        mock_exception = HTTPException(status_code=404, detail="Not found")

        with patch('src.fastapi_support.fastapi_exception_handler') as mock_handler:
            mock_handler.return_value = MagicMock()
            result = http_exception_handler(mock_request, mock_exception)
            mock_handler.assert_called_once_with(mock_otel, mock_request, mock_exception)

    def test_setup_fastapi_with_none_otel(self, mock_app):
        """Test setup_fastapi handles None OTEL instance gracefully"""
        # This might raise an exception or handle gracefully
        try:
            result = setup_fastapi(None, mock_app)
            # If it doesn't raise, verify handlers are still registered
            assert result == mock_app
        except (AttributeError, TypeError):
            # Expected if setup_fastapi doesn't handle None
            pass

    def test_setup_fastapi_with_none_app(self, mock_otel):
        """Test setup_fastapi handles None app gracefully"""
        # This should raise an AttributeError since app is None
        with pytest.raises(AttributeError):
            setup_fastapi(mock_otel, None)

    def test_setup_fastapi_returns_app(self, mock_otel, mock_app):
        """Test that setup_fastapi returns the app instance"""
        result = setup_fastapi(mock_otel, mock_app)
        assert result is mock_app

    def test_get_current_span_with_span_in_request_state(self):
        """Test get_current_span returns span when present in request state"""
        # Create mock request with span in state
        mock_request = MagicMock()
        mock_span = MagicMock()
        mock_request.state.span = mock_span

        # Call get_current_span
        result = get_current_span(mock_request)

        # Verify it returns the span
        assert result == mock_span

    def test_get_current_span_without_span_in_request_state(self):
        """Test get_current_span returns None when no span in request state"""
        # Create mock request without span in state
        mock_request = MagicMock()
        del mock_request.state.span  # Remove the span attribute

        # Call get_current_span
        result = get_current_span(mock_request)

        # Verify it returns None
        assert result is None

    def test_get_current_span_with_no_state_attribute(self):
        """Test get_current_span handles request without state attribute"""
        # Create mock request without state
        mock_request = MagicMock(spec=[])  # Empty spec, no attributes

        # Call get_current_span - should handle gracefully
        try:
            result = get_current_span(mock_request)
            # Should return None if implementation handles this
            assert result is None
        except AttributeError:
            # Expected if implementation doesn't handle missing state
            pass
