"""Tests for API Gateway utilities module"""

import json
import pytest
from src.api_gateway_utils import (
    is_api_gateway_event,
    extract_api_gateway_http_attributes,
    extract_api_gateway_context,
    extract_api_gateway_authorizer_attributes
)
from src.http_constants import (
    HTTP_REQUEST_METHOD, HTTP_REQUEST_HEADERS, HTTP_REQUEST_HEADER_TRACEPARENT,
    HTTP_REQUEST_BODY, HTTP_ROUTE, URL_FULL, URL_SCHEME,
    URL_PATH, URL_QUERY, USER_AGENT_ORIGINAL, SERVER_ADDRESS, SERVER_PORT,
    CLIENT_ADDRESS, NETWORK_PROTOCOL_VERSION,
    USER_ID, REBRANDLY_WORKSPACE, REBRANDLY_ORGANIZATION
)


class TestIsApiGatewayEvent:
    """Tests for is_api_gateway_event function"""

    def test_returns_true_for_rest_api_v1_event(self):
        """Should return True for REST API v1 event"""
        event = {'httpMethod': 'GET', 'path': '/test'}
        assert is_api_gateway_event(event) is True

    def test_returns_true_for_http_api_v2_event(self):
        """Should return True for HTTP API v2 event"""
        event = {
            'requestContext': {
                'http': {'method': 'POST', 'path': '/test'}
            }
        }
        assert is_api_gateway_event(event) is True

    def test_returns_false_for_sqs_event(self):
        """Should return False for SQS event"""
        event = {
            'Records': [{'eventSource': 'aws:sqs', 'body': '{}'}]
        }
        assert is_api_gateway_event(event) is False

    def test_returns_false_for_sns_event(self):
        """Should return False for SNS event"""
        event = {
            'Records': [{'EventSource': 'aws:sns', 'Sns': {'Message': '{}'}}]
        }
        assert is_api_gateway_event(event) is False

    def test_returns_false_for_none(self):
        """Should return False for None event"""
        assert is_api_gateway_event(None) is False

    def test_returns_false_for_empty_object(self):
        """Should return False for empty object"""
        assert is_api_gateway_event({}) is False

    def test_returns_false_for_string(self):
        """Should return False for string input"""
        assert is_api_gateway_event('not an event') is False

    def test_returns_false_for_list(self):
        """Should return False for list input"""
        assert is_api_gateway_event([{'httpMethod': 'GET'}]) is False


class TestExtractApiGatewayHttpAttributes:
    """Tests for extract_api_gateway_http_attributes function"""

    class TestRestApiV1Events:
        """Tests for REST API v1 events"""

        @pytest.fixture
        def v1_event(self):
            return {
                'httpMethod': 'POST',
                'path': '/users/123',
                'resource': '/users/{id}',
                'headers': {
                    'Content-Type': 'application/json',
                    'User-Agent': 'TestClient/1.0',
                    'Host': 'api.example.com',
                    'Authorization': 'Bearer secret-token',
                    'traceparent': '00-trace123-span456-01'
                },
                'body': json.dumps({'name': 'John', 'password': 'secret'}),
                'queryStringParameters': {'include': 'profile'},
                'requestContext': {
                    'requestId': 'req-123',
                    'domainName': 'api.example.com',
                    'identity': {'sourceIp': '192.168.1.1'},
                    'protocol': 'HTTP/1.1'
                }
            }

        def test_extracts_http_method(self, v1_event):
            """Should extract HTTP method"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs[HTTP_REQUEST_METHOD] == 'POST'

        def test_extracts_route_from_resource(self, v1_event):
            """Should extract route from resource"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs[HTTP_ROUTE] == '/users/{id}'

        def test_extracts_url_path(self, v1_event):
            """Should extract URL path"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs[URL_PATH] == '/users/123'

        def test_extracts_query_string(self, v1_event):
            """Should extract query string"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs[URL_QUERY] == 'include=profile'

        def test_sets_url_scheme_to_https(self, v1_event):
            """Should set URL scheme to https"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs[URL_SCHEME] == 'https'

        def test_extracts_server_address(self, v1_event):
            """Should extract server address"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs[SERVER_ADDRESS] == 'api.example.com'

        def test_sets_server_port_to_443(self, v1_event):
            """Should set server port to 443"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs[SERVER_PORT] == 443

        def test_extracts_client_ip(self, v1_event):
            """Should extract client IP"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs[CLIENT_ADDRESS] == '192.168.1.1'

        def test_extracts_user_agent(self, v1_event):
            """Should extract user agent"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs[USER_AGENT_ORIGINAL] == 'TestClient/1.0'

        def test_extracts_network_protocol_version(self, v1_event):
            """Should extract network protocol version"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs[NETWORK_PROTOCOL_VERSION] == 'HTTP/1.1'

        def test_builds_span_name_from_method_and_route(self, v1_event):
            """Should build span name from method and route"""
            _, span_name = extract_api_gateway_http_attributes(v1_event)
            assert span_name == 'POST /users/{id}'

        def test_captures_filtered_headers(self, v1_event):
            """Should capture filtered headers (exclude sensitive)"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            headers = json.loads(attrs[HTTP_REQUEST_HEADERS])
            assert 'content-type' in headers or 'Content-Type' in headers
            assert 'authorization' not in headers and 'Authorization' not in headers

        def test_captures_traceparent_header(self, v1_event):
            """Should capture traceparent header"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs[HTTP_REQUEST_HEADER_TRACEPARENT] == '00-trace123-span456-01'

        def test_captures_and_redacts_request_body(self, v1_event):
            """Should capture and redact request body"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            body = json.loads(attrs[HTTP_REQUEST_BODY])
            assert body['name'] == 'John'
            assert body['password'] == '[REDACTED]'

        def test_builds_full_url(self, v1_event):
            """Should build full URL"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs[URL_FULL] == 'https://api.example.com/users/123?include=profile'

        def test_sets_legacy_http_method_attribute(self, v1_event):
            """Should set legacy http.method attribute"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs['http.method'] == 'POST'

        def test_sets_legacy_http_target_attribute(self, v1_event):
            """Should set legacy http.target attribute"""
            attrs, _ = extract_api_gateway_http_attributes(v1_event)
            assert attrs['http.target'] == '/users/123?include=profile'

    class TestHttpApiV2Events:
        """Tests for HTTP API v2 events"""

        @pytest.fixture
        def v2_event(self):
            return {
                'requestContext': {
                    'http': {
                        'method': 'PUT',
                        'path': '/items/abc123',
                        'protocol': 'HTTP/2.0',
                        'sourceIp': '10.0.0.1'
                    },
                    'requestId': 'v2-req-456',
                    'domainName': 'api-v2.example.com'
                },
                'routeKey': 'PUT /items/{itemId}',
                'rawPath': '/items/abc123',
                'headers': {
                    'content-type': 'application/json',
                    'user-agent': 'V2Client/2.0'
                },
                'body': json.dumps({'value': 'updated'})
            }

        def test_extracts_http_method_from_request_context_http(self, v2_event):
            """Should extract HTTP method from requestContext.http"""
            attrs, _ = extract_api_gateway_http_attributes(v2_event)
            assert attrs[HTTP_REQUEST_METHOD] == 'PUT'

        def test_extracts_route_from_route_key(self, v2_event):
            """Should extract route from routeKey (strip method prefix)"""
            attrs, _ = extract_api_gateway_http_attributes(v2_event)
            assert attrs[HTTP_ROUTE] == '/items/{itemId}'

        def test_extracts_path_from_raw_path(self, v2_event):
            """Should extract path from rawPath"""
            attrs, _ = extract_api_gateway_http_attributes(v2_event)
            assert attrs[URL_PATH] == '/items/abc123'

        def test_extracts_client_ip_from_request_context_http_source_ip(self, v2_event):
            """Should extract client IP from requestContext.http.sourceIp"""
            attrs, _ = extract_api_gateway_http_attributes(v2_event)
            assert attrs[CLIENT_ADDRESS] == '10.0.0.1'

        def test_extracts_protocol_from_request_context_http_protocol(self, v2_event):
            """Should extract protocol from requestContext.http.protocol"""
            attrs, _ = extract_api_gateway_http_attributes(v2_event)
            assert attrs[NETWORK_PROTOCOL_VERSION] == 'HTTP/2.0'

        def test_builds_span_name_from_method_and_route(self, v2_event):
            """Should build span name from method and route"""
            _, span_name = extract_api_gateway_http_attributes(v2_event)
            assert span_name == 'PUT /items/{itemId}'

    class TestEdgeCases:
        """Tests for edge cases"""

        def test_handles_event_with_no_headers(self):
            """Should handle event with no headers"""
            event = {'httpMethod': 'GET', 'path': '/test'}
            attrs, span_name = extract_api_gateway_http_attributes(event)
            assert attrs[HTTP_REQUEST_METHOD] == 'GET'
            assert span_name == 'GET /test'

        def test_handles_event_with_no_query_parameters(self):
            """Should handle event with no query parameters"""
            event = {'httpMethod': 'GET', 'path': '/test', 'headers': {}}
            attrs, _ = extract_api_gateway_http_attributes(event)
            assert URL_QUERY not in attrs

        def test_handles_event_with_no_body(self):
            """Should handle event with no body"""
            event = {
                'httpMethod': 'POST',
                'path': '/test',
                'headers': {'Content-Type': 'application/json'}
            }
            attrs, _ = extract_api_gateway_http_attributes(event)
            assert HTTP_REQUEST_BODY not in attrs

        def test_does_not_capture_body_for_get_requests(self):
            """Should not capture body for GET requests"""
            event = {
                'httpMethod': 'GET',
                'path': '/test',
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'test': 'data'})
            }
            attrs, _ = extract_api_gateway_http_attributes(event)
            assert HTTP_REQUEST_BODY not in attrs

        def test_auto_detects_route_pattern_when_resource_not_provided(self):
            """Should auto-detect route pattern when resource not provided"""
            # Use a proper UUID format that autoDetectRoutePattern recognizes
            event = {
                'httpMethod': 'GET',
                'path': '/users/550e8400-e29b-41d4-a716-446655440000',
                'headers': {}
            }
            attrs, _ = extract_api_gateway_http_attributes(event)
            # Should replace UUID patterns
            assert attrs[HTTP_ROUTE] == '/users/{id}'

        def test_returns_empty_attrs_for_event_without_method(self):
            """Should return empty attrs for event without method"""
            event = {'path': '/test'}
            attrs, span_name = extract_api_gateway_http_attributes(event)
            assert attrs == {}
            assert span_name is None


class TestExtractApiGatewayContext:
    """Tests for extract_api_gateway_context function"""

    def test_returns_none_for_event_without_headers(self):
        """Should return None for event without headers"""
        event = {'httpMethod': 'GET', 'path': '/test'}
        assert extract_api_gateway_context(event) is None

    def test_returns_none_for_none_event(self):
        """Should return None for None event"""
        assert extract_api_gateway_context(None) is None

    def test_extracts_context_from_headers_with_traceparent(self):
        """Should extract context from headers with traceparent"""
        event = {
            'httpMethod': 'GET',
            'path': '/test',
            'headers': {
                'traceparent': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01'
            }
        }
        context = extract_api_gateway_context(event)
        assert context is not None
        assert 'traceparent' in context
        assert context['traceparent'] == '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01'

    def test_handles_case_insensitive_header_names(self):
        """Should handle case-insensitive header names"""
        event = {
            'httpMethod': 'GET',
            'path': '/test',
            'headers': {
                'Traceparent': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01'
            }
        }
        context = extract_api_gateway_context(event)
        assert context is not None
        assert 'traceparent' in context

    def test_returns_none_for_event_with_empty_headers(self):
        """Should return None for event with empty headers (no traceparent)"""
        event = {
            'httpMethod': 'GET',
            'path': '/test',
            'headers': {}
        }
        context = extract_api_gateway_context(event)
        assert context is None

    def test_extracts_traceparent_and_tracestate(self):
        """Should extract both traceparent and tracestate"""
        event = {
            'httpMethod': 'GET',
            'path': '/test',
            'headers': {
                'traceparent': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01',
                'tracestate': 'vendor=value'
            }
        }
        context = extract_api_gateway_context(event)
        assert context is not None
        assert 'traceparent' in context
        assert 'tracestate' in context
        assert context['tracestate'] == 'vendor=value'


class TestExtractApiGatewayAuthorizerAttributes:
    """Tests for extract_api_gateway_authorizer_attributes function"""

    def test_extracts_all_authorizer_fields(self):
        """Should extract id, workspace, and organization when present"""
        event = {
            'requestContext': {
                'authorizer': {
                    'id': 'user-123',
                    'workspace': 'ws-456',
                    'organization': 'org-789'
                }
            }
        }
        attrs = extract_api_gateway_authorizer_attributes(event)
        assert attrs[USER_ID] == 'user-123'
        assert attrs[REBRANDLY_WORKSPACE] == 'ws-456'
        assert attrs[REBRANDLY_ORGANIZATION] == 'org-789'

    def test_omits_none_values(self):
        """Should omit attributes when values are None"""
        event = {
            'requestContext': {
                'authorizer': {
                    'id': 'user-123',
                    'workspace': None,
                    'organization': 'org-789'
                }
            }
        }
        attrs = extract_api_gateway_authorizer_attributes(event)
        assert attrs[USER_ID] == 'user-123'
        assert REBRANDLY_WORKSPACE not in attrs
        assert attrs[REBRANDLY_ORGANIZATION] == 'org-789'

    def test_omits_string_none_values(self):
        """Should omit attributes when values are string 'None' or 'null'"""
        event = {
            'requestContext': {
                'authorizer': {
                    'id': 'user-123',
                    'workspace': 'None',
                    'organization': 'null'
                }
            }
        }
        attrs = extract_api_gateway_authorizer_attributes(event)
        assert attrs[USER_ID] == 'user-123'
        assert REBRANDLY_WORKSPACE not in attrs
        assert REBRANDLY_ORGANIZATION not in attrs

    def test_omits_empty_string_values(self):
        """Should omit attributes when values are empty strings"""
        event = {
            'requestContext': {
                'authorizer': {
                    'id': '',
                    'workspace': 'ws-456',
                    'organization': ''
                }
            }
        }
        attrs = extract_api_gateway_authorizer_attributes(event)
        assert USER_ID not in attrs
        assert attrs[REBRANDLY_WORKSPACE] == 'ws-456'
        assert REBRANDLY_ORGANIZATION not in attrs

    def test_returns_empty_dict_when_no_authorizer(self):
        """Should return empty dict when authorizer is missing"""
        event = {
            'requestContext': {
                'requestId': 'req-123'
            }
        }
        attrs = extract_api_gateway_authorizer_attributes(event)
        assert attrs == {}

    def test_returns_empty_dict_when_no_request_context(self):
        """Should return empty dict when requestContext is missing"""
        event = {
            'httpMethod': 'GET',
            'path': '/test'
        }
        attrs = extract_api_gateway_authorizer_attributes(event)
        assert attrs == {}

    def test_returns_empty_dict_for_none_event(self):
        """Should return empty dict for None event"""
        attrs = extract_api_gateway_authorizer_attributes(None)
        assert attrs == {}

    def test_returns_empty_dict_for_empty_event(self):
        """Should return empty dict for empty event"""
        attrs = extract_api_gateway_authorizer_attributes({})
        assert attrs == {}

    def test_handles_partial_authorizer(self):
        """Should handle authorizer with only some fields"""
        event = {
            'requestContext': {
                'authorizer': {
                    'id': 'user-123'
                    # workspace and organization not present
                }
            }
        }
        attrs = extract_api_gateway_authorizer_attributes(event)
        assert attrs[USER_ID] == 'user-123'
        assert REBRANDLY_WORKSPACE not in attrs
        assert REBRANDLY_ORGANIZATION not in attrs

    def test_converts_values_to_strings(self):
        """Should convert non-string values to strings"""
        event = {
            'requestContext': {
                'authorizer': {
                    'id': 12345,
                    'workspace': 67890,
                    'organization': True
                }
            }
        }
        attrs = extract_api_gateway_authorizer_attributes(event)
        assert attrs[USER_ID] == '12345'
        assert attrs[REBRANDLY_WORKSPACE] == '67890'
        assert attrs[REBRANDLY_ORGANIZATION] == 'True'

    def test_ignores_extra_authorizer_fields(self):
        """Should only extract id, workspace, and organization"""
        event = {
            'requestContext': {
                'authorizer': {
                    'id': 'user-123',
                    'workspace': 'ws-456',
                    'organization': 'org-789',
                    'principalId': 'principal-abc',
                    'claims': {'sub': 'xyz'}
                }
            }
        }
        attrs = extract_api_gateway_authorizer_attributes(event)
        assert len(attrs) == 3
        assert attrs[USER_ID] == 'user-123'
        assert attrs[REBRANDLY_WORKSPACE] == 'ws-456'
        assert attrs[REBRANDLY_ORGANIZATION] == 'org-789'


class TestExtractApiGatewayHttpAttributesWithAuthorizer:
    """Tests for authorizer attributes in extract_api_gateway_http_attributes"""

    def test_extracts_authorizer_attributes_in_v1_event(self):
        """Should extract authorizer attributes in REST API v1 event"""
        event = {
            'httpMethod': 'GET',
            'path': '/test',
            'headers': {},
            'requestContext': {
                'authorizer': {
                    'id': 'user-123',
                    'workspace': 'ws-456',
                    'organization': 'org-789'
                }
            }
        }
        attrs, _ = extract_api_gateway_http_attributes(event)
        assert attrs[USER_ID] == 'user-123'
        assert attrs[REBRANDLY_WORKSPACE] == 'ws-456'
        assert attrs[REBRANDLY_ORGANIZATION] == 'org-789'

    def test_extracts_authorizer_attributes_in_v2_event(self):
        """Should extract authorizer attributes in HTTP API v2 event"""
        event = {
            'requestContext': {
                'http': {
                    'method': 'GET',
                    'path': '/test'
                },
                'authorizer': {
                    'id': 'user-abc',
                    'workspace': 'ws-def',
                    'organization': 'org-ghi'
                }
            }
        }
        attrs, _ = extract_api_gateway_http_attributes(event)
        assert attrs[USER_ID] == 'user-abc'
        assert attrs[REBRANDLY_WORKSPACE] == 'ws-def'
        assert attrs[REBRANDLY_ORGANIZATION] == 'org-ghi'

    def test_handles_missing_authorizer(self):
        """Should not include authorizer attributes when authorizer is missing"""
        event = {
            'httpMethod': 'GET',
            'path': '/test',
            'headers': {}
        }
        attrs, _ = extract_api_gateway_http_attributes(event)
        assert USER_ID not in attrs
        assert REBRANDLY_WORKSPACE not in attrs
        assert REBRANDLY_ORGANIZATION not in attrs
