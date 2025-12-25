"""Tests for HTTP utilities (Body Capture, Traceparent Injection, and Route Pattern Detection)"""

import os
import pytest
from unittest.mock import MagicMock, patch
from src.http_utils import (
    is_body_capture_enabled,
    should_capture_body,
    redact_sensitive_fields,
    capture_request_body,
    filter_important_headers,
    get_traceparent_header,
    inject_traceparent,
    requests_with_tracing,
    httpx_with_tracing,
    auto_detect_route_pattern,
    reconstruct_route_pattern,
    strip_query_params
)


class TestIsBodyCaptureEnabled:
    """Tests for is_body_capture_enabled function"""

    def test_default_enabled(self, monkeypatch):
        """Should return True by default (opt-out)"""
        monkeypatch.delenv('OTEL_CAPTURE_REQUEST_BODY', raising=False)
        assert is_body_capture_enabled() is True

    def test_explicitly_disabled(self, monkeypatch):
        """Should return False when explicitly disabled"""
        monkeypatch.setenv('OTEL_CAPTURE_REQUEST_BODY', 'false')
        assert is_body_capture_enabled() is False

    def test_disabled_with_zero(self, monkeypatch):
        """Should return False when set to 0"""
        monkeypatch.setenv('OTEL_CAPTURE_REQUEST_BODY', '0')
        assert is_body_capture_enabled() is False

    def test_disabled_with_no(self, monkeypatch):
        """Should return False when set to 'no'"""
        monkeypatch.setenv('OTEL_CAPTURE_REQUEST_BODY', 'no')
        assert is_body_capture_enabled() is False

    def test_explicitly_enabled(self, monkeypatch):
        """Should return True when set to true"""
        monkeypatch.setenv('OTEL_CAPTURE_REQUEST_BODY', 'true')
        assert is_body_capture_enabled() is True


class TestShouldCaptureBody:
    """Tests for should_capture_body function"""

    def test_application_json(self):
        """Should return True for application/json"""
        assert should_capture_body('application/json') is True

    def test_application_json_with_charset(self):
        """Should return True for application/json with charset"""
        assert should_capture_body('application/json; charset=utf-8') is True

    def test_application_ld_json(self):
        """Should return True for application/ld+json"""
        assert should_capture_body('application/ld+json') is True

    def test_custom_json_type(self):
        """Should return True for custom JSON types"""
        assert should_capture_body('application/vnd.api+json') is True

    def test_text_html(self):
        """Should return False for text/html"""
        assert should_capture_body('text/html') is False

    def test_multipart_form_data(self):
        """Should return False for multipart/form-data"""
        assert should_capture_body('multipart/form-data') is False

    def test_application_octet_stream(self):
        """Should return False for application/octet-stream"""
        assert should_capture_body('application/octet-stream') is False

    def test_null_or_empty(self):
        """Should return False for null or empty"""
        assert should_capture_body(None) is False
        assert should_capture_body('') is False


class TestRedactSensitiveFields:
    """Tests for redact_sensitive_fields function"""

    def test_redact_password(self):
        """Should redact password field"""
        input_data = {'username': 'john', 'password': 'secret123'}
        result = redact_sensitive_fields(input_data)
        assert result['username'] == 'john'
        assert result['password'] == '[REDACTED]'

    def test_redact_token(self):
        """Should redact token field"""
        input_data = {'data': 'test', 'token': 'abc123'}
        result = redact_sensitive_fields(input_data)
        assert result['data'] == 'test'
        assert result['token'] == '[REDACTED]'

    def test_redact_nested_fields(self):
        """Should redact nested sensitive fields"""
        input_data = {
            'user': 'john',
            'auth': {
                'password': 'secret',
                'token': 'abc'
            }
        }
        result = redact_sensitive_fields(input_data)
        assert result['user'] == 'john'
        assert result['auth']['password'] == '[REDACTED]'
        assert result['auth']['token'] == '[REDACTED]'

    def test_redact_arrays(self):
        """Should redact fields in arrays"""
        input_data = {
            'users': [
                {'name': 'john', 'password': 'secret1'},
                {'name': 'jane', 'password': 'secret2'}
            ]
        }
        result = redact_sensitive_fields(input_data)
        assert result['users'][0]['name'] == 'john'
        assert result['users'][0]['password'] == '[REDACTED]'
        assert result['users'][1]['name'] == 'jane'
        assert result['users'][1]['password'] == '[REDACTED]'

    def test_case_insensitive(self):
        """Should handle case-insensitive matching"""
        input_data = {'PASSWORD': 'secret', 'Token': 'abc', 'ApiKey': 'xyz'}
        result = redact_sensitive_fields(input_data)
        assert result['PASSWORD'] == '[REDACTED]'
        assert result['Token'] == '[REDACTED]'
        assert result['ApiKey'] == '[REDACTED]'

    def test_no_mutation(self):
        """Should not mutate original object"""
        input_data = {'username': 'john', 'password': 'secret'}
        result = redact_sensitive_fields(input_data)
        assert input_data['password'] == 'secret'  # Original unchanged
        assert result['password'] == '[REDACTED]'

    def test_primitives(self):
        """Should handle primitives"""
        assert redact_sensitive_fields(None) is None
        assert redact_sensitive_fields('string') == 'string'
        assert redact_sensitive_fields(123) == 123


class TestCaptureRequestBody:
    """Tests for capture_request_body function"""

    def test_capture_json_dict(self):
        """Should capture and redact JSON dict body"""
        body = {'username': 'john', 'password': 'secret123'}
        result = capture_request_body(body, 'application/json')
        assert result is not None
        import json
        parsed = json.loads(result)
        assert parsed['username'] == 'john'
        assert parsed['password'] == '[REDACTED]'

    def test_capture_json_string(self):
        """Should capture and redact JSON string body"""
        body = '{"username":"john","password":"secret123"}'
        result = capture_request_body(body, 'application/json')
        assert result is not None
        import json
        parsed = json.loads(result)
        assert parsed['username'] == 'john'
        assert parsed['password'] == '[REDACTED]'

    def test_capture_bytes(self):
        """Should capture and redact bytes body"""
        body = b'{"username":"john","password":"secret"}'
        result = capture_request_body(body, 'application/json')
        assert result is not None
        import json
        parsed = json.loads(result)
        assert parsed['username'] == 'john'
        assert parsed['password'] == '[REDACTED]'

    def test_non_json_content_type(self):
        """Should return None for non-JSON content type"""
        body = {'data': 'test'}
        result = capture_request_body(body, 'text/html')
        assert result is None

    def test_disabled(self, monkeypatch):
        """Should return None when capture is disabled"""
        monkeypatch.setenv('OTEL_CAPTURE_REQUEST_BODY', 'false')
        body = {'username': 'john'}
        result = capture_request_body(body, 'application/json')
        assert result is None

    def test_empty_body(self):
        """Should return None for empty body"""
        result = capture_request_body(None, 'application/json')
        assert result is None

    def test_invalid_json_string(self):
        """Should return None for invalid JSON string"""
        body = 'not valid json'
        result = capture_request_body(body, 'application/json')
        assert result is None

    def test_complex_nested(self):
        """Should handle complex nested structures"""
        body = {
            'user': 'john',
            'credentials': {
                'password': 'secret',
                'apiKey': 'key123'
            },
            'profile': {
                'email': 'john@example.com',
                'settings': {
                    'token': 'abc'
                }
            }
        }
        result = capture_request_body(body, 'application/json')
        assert result is not None
        import json
        parsed = json.loads(result)
        assert parsed['user'] == 'john'
        assert parsed['credentials']['password'] == '[REDACTED]'
        assert parsed['credentials']['apiKey'] == '[REDACTED]'
        assert parsed['profile']['email'] == 'john@example.com'
        assert parsed['profile']['settings']['token'] == '[REDACTED]'


class TestFilterImportantHeaders:
    """Tests for filter_important_headers function"""

    def test_includes_traceparent(self):
        """Should include traceparent in filtered headers"""
        headers = {'traceparent': '00-test-trace-id', 'content-type': 'application/json'}
        result = filter_important_headers(headers)
        assert 'traceparent' in result
        assert result['traceparent'] == '00-test-trace-id'

    def test_includes_tracestate(self):
        """Should include tracestate in filtered headers"""
        headers = {'tracestate': 'vendor=value', 'content-type': 'application/json'}
        result = filter_important_headers(headers)
        assert 'tracestate' in result
        assert result['tracestate'] == 'vendor=value'

    def test_filters_out_sensitive_headers(self):
        """Should not include authorization headers"""
        headers = {'authorization': 'Bearer token', 'content-type': 'application/json'}
        result = filter_important_headers(headers)
        assert 'authorization' not in result
        assert 'content-type' in result


class TestGetTraceparentHeader:
    """Tests for get_traceparent_header function"""

    def test_empty_when_no_active_span(self):
        """Should return empty dict when no active span"""
        with patch('opentelemetry.propagate.inject') as mock_inject:
            # Don't add traceparent to carrier
            mock_inject.return_value = None
            result = get_traceparent_header()
            assert result == {}

    def test_returns_traceparent_with_active_span(self):
        """Should return traceparent header when active span exists"""
        with patch('opentelemetry.propagate.inject') as mock_inject:
            def mock_inject_func(carrier, ctx):
                carrier['traceparent'] = '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01'

            mock_inject.side_effect = mock_inject_func
            result = get_traceparent_header()

            assert 'traceparent' in result
            assert result['traceparent'] == '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01'

    def test_handles_errors_gracefully(self):
        """Should return empty dict on exception"""
        with patch('opentelemetry.propagate.inject') as mock_inject:
            mock_inject.side_effect = Exception('Injection failed')
            result = get_traceparent_header()
            assert result == {}


class TestInjectTraceparent:
    """Tests for inject_traceparent function"""

    def test_injects_traceparent_into_dict(self):
        """Should inject traceparent into headers dict"""
        headers = {'content-type': 'application/json'}

        with patch('opentelemetry.propagate.inject') as mock_inject:
            def mock_inject_func(carrier, ctx):
                carrier['traceparent'] = '00-test-trace-id'

            mock_inject.side_effect = mock_inject_func
            result = inject_traceparent(headers)

            assert result is headers  # Returns same object
            assert 'traceparent' in headers

    def test_handles_none_input(self):
        """Should handle None input gracefully"""
        result = inject_traceparent(None)
        assert result is None

    def test_handles_non_dict_input(self):
        """Should handle non-dict input gracefully"""
        result = inject_traceparent('not a dict')
        assert result == 'not a dict'

    def test_handles_injection_errors(self):
        """Should handle injection errors gracefully"""
        headers = {'content-type': 'application/json'}

        with patch('opentelemetry.propagate.inject') as mock_inject:
            mock_inject.side_effect = Exception('Injection failed')
            # Should not raise exception
            result = inject_traceparent(headers)
            assert result is headers

    def test_returns_same_dict_for_chaining(self):
        """Should return same dict for chaining"""
        headers = {'x-custom': 'value'}
        result = inject_traceparent(headers)
        assert result is headers


class TestRequestsWithTracing:
    """Tests for requests_with_tracing function"""

    def test_creates_new_session(self):
        """Should create new Session with hooks"""
        try:
            import requests
            session = requests_with_tracing()
            assert session is not None
            assert hasattr(session, 'hooks')
            assert 'response' in session.hooks
        except ImportError:
            pytest.skip("requests library not installed")

    def test_enhances_existing_session(self):
        """Should add hooks to provided session"""
        try:
            import requests
            my_session = requests.Session()
            original_hooks_count = len(my_session.hooks.get('response', []))

            traced_session = requests_with_tracing(my_session)

            assert traced_session is my_session
            assert len(my_session.hooks['response']) == original_hooks_count + 1
        except ImportError:
            pytest.skip("requests library not installed")

    def test_injects_traceparent_on_request(self):
        """Should inject traceparent via hook for Rebrandly domains"""
        try:
            import requests
            from unittest.mock import Mock

            # Create a mock response with request to Rebrandly domain
            mock_response = Mock()
            mock_response.request = Mock()
            mock_response.request.url = 'https://api.rebrandly.com/v1/links'
            mock_response.request.headers = {}

            with patch('opentelemetry.propagate.inject') as mock_inject:
                def mock_inject_func(carrier, ctx):
                    carrier['traceparent'] = '00-test-id'

                mock_inject.side_effect = mock_inject_func

                session = requests_with_tracing()
                # Manually trigger the hook
                for hook in session.hooks['response']:
                    hook(mock_response)

                assert 'traceparent' in mock_response.request.headers
        except ImportError:
            pytest.skip("requests library not installed")

    def test_raises_import_error_if_requests_missing(self):
        """Should raise ImportError if requests not installed"""
        with patch.dict('sys.modules', {'requests': None}):
            with pytest.raises(ImportError, match='requests library not installed'):
                requests_with_tracing()


class TestHttpxWithTracing:
    """Tests for httpx_with_tracing function"""

    def test_creates_new_client(self):
        """Should create new Client with event hooks"""
        try:
            import httpx
            client = httpx_with_tracing()
            assert client is not None
            assert hasattr(client, 'event_hooks')
            assert 'request' in client.event_hooks
        except ImportError:
            pytest.skip("httpx library not installed")

    def test_enhances_existing_client(self):
        """Should add hooks to provided client"""
        try:
            import httpx
            my_client = httpx.Client()
            original_hooks_count = len(my_client.event_hooks.get('request', []))

            traced_client = httpx_with_tracing(my_client)

            assert traced_client is my_client
            assert len(my_client.event_hooks['request']) == original_hooks_count + 1
        except ImportError:
            pytest.skip("httpx library not installed")

    def test_injects_traceparent_on_request(self):
        """Should inject traceparent via hook for Rebrandly domains"""
        try:
            import httpx
            from unittest.mock import Mock

            # Create a mock request to Rebrandly domain
            mock_request = Mock()
            mock_request.url = 'https://api.rebrandly.com/v1/links'
            mock_request.headers = {}
            mock_request.extensions = {}

            with patch('opentelemetry.propagate.inject') as mock_inject:
                def mock_inject_func(carrier, ctx):
                    carrier['traceparent'] = '00-test-id'

                mock_inject.side_effect = mock_inject_func

                client = httpx_with_tracing()
                # Manually trigger the hook
                for hook in client.event_hooks['request']:
                    hook(mock_request)

                assert 'traceparent' in mock_request.headers
        except ImportError:
            pytest.skip("httpx library not installed")

    def test_raises_import_error_if_httpx_missing(self):
        """Should raise ImportError if httpx not installed"""
        with patch.dict('sys.modules', {'httpx': None}):
            with pytest.raises(ImportError, match='httpx library not installed'):
                httpx_with_tracing()


class TestAutoDetectRoutePattern:
    """Tests for auto_detect_route_pattern function"""

    def test_replace_uuids(self):
        """Should replace UUIDs with {id}"""
        path = '/users/550e8400-e29b-41d4-a716-446655440000/posts'
        assert auto_detect_route_pattern(path) == '/users/{id}/posts'

    def test_replace_multiple_uuids(self):
        """Should replace multiple UUIDs with {id}"""
        path = '/users/550e8400-e29b-41d4-a716-446655440000/posts/650e8400-e29b-41d4-a716-446655440001'
        assert auto_detect_route_pattern(path) == '/users/{id}/posts/{id}'

    def test_replace_32_char_hex_ids(self):
        """Should replace 32-char hex IDs with {id}"""
        path = '/templates/0301fb0436d949979b6688a5c6d91e8f/schedule'
        assert auto_detect_route_pattern(path) == '/templates/{id}/schedule'

    def test_replace_24_char_hex_ids(self):
        """Should replace 24-char hex IDs (MongoDB ObjectId) with {id}"""
        path = '/posts/507f1f77bcf86cd799439011/comments'
        assert auto_detect_route_pattern(path) == '/posts/{id}/comments'

    def test_replace_40_char_hex_ids(self):
        """Should replace 40-char hex IDs (SHA-1) with {id}"""
        path = '/files/356a192b7913b04c54574d18c28d46e6395428ab/download'
        assert auto_detect_route_pattern(path) == '/files/{id}/download'

    def test_replace_long_numeric_ids(self):
        """Should replace long numeric IDs (4+ digits) with {id}"""
        path = '/orders/12345678/items'
        assert auto_detect_route_pattern(path) == '/orders/{id}/items'

    def test_replace_short_numeric_ids_in_id_positions(self):
        """Should replace short numeric IDs (1-3 digits) in ID positions"""
        path = '/items/123/details'
        assert auto_detect_route_pattern(path) == '/items/{id}/details'

    def test_preserve_version_numbers(self):
        """Should preserve version numbers like /v1 and /v2"""
        path = '/v1/api/v2/resources'
        assert auto_detect_route_pattern(path) == '/v1/api/v2/resources'

    def test_preserve_version_numbers_but_replace_ids(self):
        """Should preserve version numbers but replace IDs"""
        path = '/v1/users/12345/profile'
        assert auto_detect_route_pattern(path) == '/v1/users/{id}/profile'

    def test_no_ids(self):
        """Should handle paths with no IDs"""
        path = '/health'
        assert auto_detect_route_pattern(path) == '/health'

    def test_trailing_slash(self):
        """Should handle paths with trailing slash"""
        path = '/users/550e8400-e29b-41d4-a716-446655440000/'
        assert auto_detect_route_pattern(path) == '/users/{id}/'

    def test_complex_nested_paths(self):
        """Should handle complex nested paths"""
        path = '/api/v1/tenants/507f1f77bcf86cd799439011/users/550e8400-e29b-41d4-a716-446655440000/orders/12345'
        assert auto_detect_route_pattern(path) == '/api/v1/tenants/{id}/users/{id}/orders/{id}'

    def test_path_ending_with_id(self):
        """Should handle paths ending with ID"""
        path = '/users/550e8400-e29b-41d4-a716-446655440000'
        assert auto_detect_route_pattern(path) == '/users/{id}'


class TestReconstructRoutePattern:
    """Tests for reconstruct_route_pattern function"""

    def test_reconstruct_from_params(self):
        """Should reconstruct pattern from params"""
        path = '/users/123/posts/456'
        params = {'userId': '123', 'postId': '456'}
        assert reconstruct_route_pattern(path, params) == '/users/{userId}/posts/{postId}'

    def test_single_param(self):
        """Should handle single param"""
        path = '/users/123'
        params = {'id': '123'}
        assert reconstruct_route_pattern(path, params) == '/users/{id}'

    def test_empty_params(self):
        """Should handle empty params"""
        path = '/health'
        params = {}
        assert reconstruct_route_pattern(path, params) == '/health'

    def test_none_params(self):
        """Should handle None params"""
        path = '/health'
        assert reconstruct_route_pattern(path, None) == '/health'

    def test_sort_by_value_length(self):
        """Should sort by value length to avoid partial replacements"""
        path = '/users/1/posts/123'
        params = {'userId': '1', 'postId': '123'}
        # Should replace '123' first, then '1'
        assert reconstruct_route_pattern(path, params) == '/users/{userId}/posts/{postId}'

    def test_params_with_special_characters(self):
        """Should handle params with special characters"""
        path = '/users/user-123/profile'
        params = {'id': 'user-123'}
        assert reconstruct_route_pattern(path, params) == '/users/{id}/profile'

    def test_null_param_values(self):
        """Should handle null param values"""
        path = '/users/123'
        params = {'id': None, 'other': None}
        assert reconstruct_route_pattern(path, params) == '/users/123'


class TestStripQueryParams:
    """Tests for strip_query_params function"""

    def test_strip_query_params(self):
        """Should strip query params from path"""
        assert strip_query_params('/jobs?status=active') == '/jobs'

    def test_strip_multiple_query_params(self):
        """Should strip multiple query params"""
        assert strip_query_params('/jobs?status=active&page=2') == '/jobs'

    def test_path_without_query_params(self):
        """Should handle path without query params"""
        assert strip_query_params('/jobs') == '/jobs'

    def test_root_path(self):
        """Should handle root path"""
        assert strip_query_params('/?key=value') == '/'
        assert strip_query_params('/') == '/'

    def test_full_urls(self):
        """Should handle full URLs"""
        assert strip_query_params('http://example.com/api?key=123') == '/api'
        assert strip_query_params('https://example.com/api?key=123') == '/api'

    def test_edge_cases(self):
        """Should handle edge cases"""
        assert strip_query_params('') == '/'
        assert strip_query_params(None) == '/'

    def test_complex_paths(self):
        """Should handle complex paths with query params"""
        assert strip_query_params('/api/v1/users/123?include=profile') == '/api/v1/users/123'


class TestDomainDetection:
    """Tests for domain detection functions"""

    def test_is_rebrandly_domain_api_rebrandly_com(self):
        """Should return True for api.rebrandly.com"""
        from src.http_utils import is_rebrandly_domain

        assert is_rebrandly_domain('https://api.rebrandly.com/v1/links') is True
        assert is_rebrandly_domain('api.rebrandly.com') is True
        assert is_rebrandly_domain('http://api.rebrandly.com') is True

    def test_is_rebrandly_domain_api_test_rebrandly_com(self):
        """Should return True for api.test.rebrandly.com"""
        from src.http_utils import is_rebrandly_domain

        assert is_rebrandly_domain('https://api.test.rebrandly.com/v1/links') is True
        assert is_rebrandly_domain('api.test.rebrandly.com') is True
        assert is_rebrandly_domain('http://api.test.rebrandly.com') is True

    def test_is_rebrandly_domain_subdomains(self):
        """Should return True for any subdomain of rebrandly.com"""
        from src.http_utils import is_rebrandly_domain

        assert is_rebrandly_domain('https://internal.rebrandly.com') is True
        assert is_rebrandly_domain('https://cdn.rebrandly.com/assets/logo.png') is True
        assert is_rebrandly_domain('https://dashboard.rebrandly.com') is True
        assert is_rebrandly_domain('https://sub.domain.rebrandly.com') is True

    def test_is_rebrandly_domain_external_domains(self):
        """Should return False for external domains"""
        from src.http_utils import is_rebrandly_domain

        assert is_rebrandly_domain('https://example.com') is False
        assert is_rebrandly_domain('https://api.external.com') is False
        assert is_rebrandly_domain('https://rebrandly.com.evil.com') is False

    def test_is_rebrandly_domain_localhost(self):
        """Should return False for localhost and loopback"""
        from src.http_utils import is_rebrandly_domain

        assert is_rebrandly_domain('http://localhost:3000') is False
        assert is_rebrandly_domain('http://127.0.0.1:3000') is False
        assert is_rebrandly_domain('localhost') is False
        assert is_rebrandly_domain('127.0.0.1') is False

    def test_is_rebrandly_domain_invalid_urls(self):
        """Should handle invalid URLs gracefully"""
        from src.http_utils import is_rebrandly_domain

        assert is_rebrandly_domain('') is False
        assert is_rebrandly_domain(None) is False
        assert is_rebrandly_domain(123) is False

    def test_is_rebrandly_domain_with_ports(self):
        """Should handle URLs with ports"""
        from src.http_utils import is_rebrandly_domain

        assert is_rebrandly_domain('https://api.rebrandly.com:443/v1/links') is True
        assert is_rebrandly_domain('http://api.test.rebrandly.com:8080') is True

    def test_is_rebrandly_domain_with_query_params(self):
        """Should handle URLs with query parameters"""
        from src.http_utils import is_rebrandly_domain

        assert is_rebrandly_domain('https://api.rebrandly.com/v1/links?status=active') is True

    def test_is_rebrandly_domain_hostname_without_protocol(self):
        """Should handle hostname strings without protocol"""
        from src.http_utils import is_rebrandly_domain

        assert is_rebrandly_domain('api.rebrandly.com/v1/links') is True
        assert is_rebrandly_domain('api.test.rebrandly.com/v1/links') is True

    def test_is_auto_domain_instrumentation_enabled_default(self):
        """Should return True by default when env var not set"""
        import os
        from src.http_utils import is_auto_domain_instrumentation_enabled

        # Save original value
        original = os.environ.get('OTEL_INSTRUMENT_REBRANDLY_DOMAINS')

        try:
            # Remove env var
            if 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']

            assert is_auto_domain_instrumentation_enabled() is True
        finally:
            # Restore original value
            if original is not None:
                os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = original
            elif 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']

    def test_is_auto_domain_instrumentation_enabled_disabled(self):
        """Should return False when explicitly disabled"""
        import os
        from src.http_utils import is_auto_domain_instrumentation_enabled

        original = os.environ.get('OTEL_INSTRUMENT_REBRANDLY_DOMAINS')

        try:
            os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = 'false'
            assert is_auto_domain_instrumentation_enabled() is False

            os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = '0'
            assert is_auto_domain_instrumentation_enabled() is False

            os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = 'no'
            assert is_auto_domain_instrumentation_enabled() is False
        finally:
            if original is not None:
                os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = original
            elif 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']

    def test_is_auto_domain_instrumentation_enabled_true_values(self):
        """Should return True for any other value"""
        import os
        from src.http_utils import is_auto_domain_instrumentation_enabled

        original = os.environ.get('OTEL_INSTRUMENT_REBRANDLY_DOMAINS')

        try:
            os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = 'true'
            assert is_auto_domain_instrumentation_enabled() is True

            os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = '1'
            assert is_auto_domain_instrumentation_enabled() is True

            os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = 'yes'
            assert is_auto_domain_instrumentation_enabled() is True
        finally:
            if original is not None:
                os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = original
            elif 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']

    def test_is_auto_domain_instrumentation_enabled_case_insensitive(self):
        """Should be case insensitive for false values"""
        import os
        from src.http_utils import is_auto_domain_instrumentation_enabled

        original = os.environ.get('OTEL_INSTRUMENT_REBRANDLY_DOMAINS')

        try:
            os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = 'FALSE'
            assert is_auto_domain_instrumentation_enabled() is False

            os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = 'False'
            assert is_auto_domain_instrumentation_enabled() is False

            os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = 'NO'
            assert is_auto_domain_instrumentation_enabled() is False
        finally:
            if original is not None:
                os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = original
            elif 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']

    def test_should_inject_trace_context_rebrandly_domains(self):
        """Should return True for Rebrandly domains when auto-instrumentation is enabled"""
        import os
        from src.http_utils import should_inject_trace_context

        original = os.environ.get('OTEL_INSTRUMENT_REBRANDLY_DOMAINS')

        try:
            if 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']

            assert should_inject_trace_context('https://api.rebrandly.com/v1/links') is True
            assert should_inject_trace_context('https://api.test.rebrandly.com/v1/links') is True
            assert should_inject_trace_context('https://internal.rebrandly.com') is True
        finally:
            if original is not None:
                os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = original

    def test_should_inject_trace_context_external_domains(self):
        """Should return False for external domains"""
        import os
        from src.http_utils import should_inject_trace_context

        original = os.environ.get('OTEL_INSTRUMENT_REBRANDLY_DOMAINS')

        try:
            if 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']

            assert should_inject_trace_context('https://example.com') is False
            assert should_inject_trace_context('https://api.external.com') is False
        finally:
            if original is not None:
                os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = original

    def test_should_inject_trace_context_globally_disabled(self):
        """Should return False when auto-instrumentation is disabled globally"""
        import os
        from src.http_utils import should_inject_trace_context

        original = os.environ.get('OTEL_INSTRUMENT_REBRANDLY_DOMAINS')

        try:
            os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = 'false'

            assert should_inject_trace_context('https://api.rebrandly.com/v1/links') is False
            assert should_inject_trace_context('https://api.test.rebrandly.com/v1/links') is False
        finally:
            if original is not None:
                os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = original
            elif 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']

    def test_should_inject_trace_context_per_request_opt_out(self):
        """Should return False when skip_tracing is True"""
        import os
        from src.http_utils import should_inject_trace_context

        original = os.environ.get('OTEL_INSTRUMENT_REBRANDLY_DOMAINS')

        try:
            if 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']

            assert should_inject_trace_context('https://api.rebrandly.com/v1/links', {'skip_tracing': True}) is False
            assert should_inject_trace_context('https://api.test.rebrandly.com/v1/links', {'skip_tracing': True}) is False
        finally:
            if original is not None:
                os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = original

    def test_should_inject_trace_context_empty_options(self):
        """Should handle empty options dict"""
        import os
        from src.http_utils import should_inject_trace_context

        original = os.environ.get('OTEL_INSTRUMENT_REBRANDLY_DOMAINS')

        try:
            if 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']

            assert should_inject_trace_context('https://api.rebrandly.com/v1/links', {}) is True
        finally:
            if original is not None:
                os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = original

    def test_should_inject_trace_context_none_options(self):
        """Should handle None options"""
        import os
        from src.http_utils import should_inject_trace_context

        original = os.environ.get('OTEL_INSTRUMENT_REBRANDLY_DOMAINS')

        try:
            if 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']

            assert should_inject_trace_context('https://api.rebrandly.com/v1/links', None) is True
            assert should_inject_trace_context('https://api.rebrandly.com/v1/links') is True
        finally:
            if original is not None:
                os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = original

    def test_should_inject_trace_context_combined_checks(self):
        """Should combine all checks correctly"""
        import os
        from src.http_utils import should_inject_trace_context

        original = os.environ.get('OTEL_INSTRUMENT_REBRANDLY_DOMAINS')

        try:
            # Global disabled + Rebrandly domain = False
            os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = 'false'
            assert should_inject_trace_context('https://api.rebrandly.com/v1/links') is False

            # Global enabled + external domain = False
            if 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']
            assert should_inject_trace_context('https://example.com') is False

            # Global enabled + Rebrandly domain + skip_tracing = False
            assert should_inject_trace_context('https://api.rebrandly.com/v1/links', {'skip_tracing': True}) is False

            # Global enabled + Rebrandly domain + no skip_tracing = True
            assert should_inject_trace_context('https://api.rebrandly.com/v1/links', {'skip_tracing': False}) is True
            assert should_inject_trace_context('https://api.rebrandly.com/v1/links') is True
        finally:
            if original is not None:
                os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS'] = original
            elif 'OTEL_INSTRUMENT_REBRANDLY_DOMAINS' in os.environ:
                del os.environ['OTEL_INSTRUMENT_REBRANDLY_DOMAINS']
