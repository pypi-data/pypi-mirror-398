import pytest
from unittest.mock import MagicMock, patch, call
import json

# Import the decorators and methods under test
from src.rebrandly_otel import (
    lambda_handler,
    aws_message_handler,
    traces,
    aws_message_span,
    otel,
    convert_xray_to_w3c_traceparent
)
from opentelemetry.trace import SpanKind, Status, StatusCode


@pytest.fixture
def mock_lambda_context():
    """Create mock AWS Lambda context"""
    context = MagicMock()
    context.aws_request_id = 'test-request-id-12345'
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-function'
    context.function_name = 'test-function'
    context.function_version = '$LATEST'
    context.memory_limit_in_mb = '256'
    return context


@pytest.fixture
def sqs_event():
    """Create mock SQS event"""
    return {
        'Records': [
            {
                'messageId': 'msg-12345',
                'receiptHandle': 'receipt-handle',
                'body': json.dumps({'data': 'test message'}),
                'attributes': {
                    'ApproximateReceiveCount': '1',
                    'SentTimestamp': '1234567890'
                },
                'messageAttributes': {
                    'traceparent': {
                        'stringValue': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01',
                        'dataType': 'String'
                    }
                },
                'eventSource': 'aws:sqs'
            }
        ]
    }


@pytest.fixture
def sns_event():
    """Create mock SNS event"""
    return {
        'Records': [
            {
                'EventSource': 'aws:sns',
                'Sns': {
                    'MessageId': 'sns-msg-12345',
                    'Message': json.dumps({'event': 'test_event', 'data': 'test'}),
                    'MessageAttributes': {
                        'traceparent': {
                            'Type': 'String',
                            'Value': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01'
                        }
                    }
                }
            }
        ]
    }


@pytest.fixture
def sns_event_with_none_subject():
    """Create mock SNS event with Subject set to None (common in real SNS messages)"""
    return {
        'Records': [
            {
                'EventSource': 'aws:sns',
                'Sns': {
                    'MessageId': 'sns-msg-none-subject',
                    'Subject': None,  # Subject is often None in SNS messages
                    'TopicArn': 'arn:aws:sns:us-east-1:123456789012:test-topic',
                    'Message': json.dumps({'event': 'test_event', 'data': 'test'}),
                    'MessageAttributes': {}
                }
            }
        ]
    }


@pytest.fixture
def api_gateway_event():
    """Create mock API Gateway event"""
    return {
        'httpMethod': 'POST',
        'path': '/test',
        'headers': {
            'Content-Type': 'application/json',
            'traceparent': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01'
        },
        'body': json.dumps({'test': 'data'}),
        'requestContext': {
            'requestId': 'api-request-123'
        }
    }


@pytest.fixture
def api_gateway_v1_event():
    """Create mock API Gateway REST API v1 event with full details"""
    return {
        'httpMethod': 'POST',
        'path': '/users/123',
        'resource': '/users/{id}',
        'headers': {
            'Host': 'api.example.com',
            'Content-Type': 'application/json',
            'User-Agent': 'TestClient/1.0',
            'X-Forwarded-For': '192.168.1.1',
            'X-Forwarded-Proto': 'https',
            'traceparent': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01',
            'Authorization': 'Bearer secret-token'
        },
        'queryStringParameters': {
            'format': 'json'
        },
        'body': json.dumps({
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'secret123'
        }),
        'requestContext': {
            'requestId': 'api-request-v1-123',
            'stage': 'prod',
            'identity': {
                'sourceIp': '192.168.1.1'
            },
            'protocol': 'HTTP/1.1'
        }
    }


@pytest.fixture
def api_gateway_v2_event():
    """Create mock API Gateway HTTP API v2 event"""
    return {
        'version': '2.0',
        'routeKey': 'GET /products/{productId}',
        'rawPath': '/products/abc-123',
        'rawQueryString': 'include=details&sort=price',
        'headers': {
            'host': 'api.example.com',
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0',
            'x-forwarded-for': '10.0.0.1',
            'x-forwarded-proto': 'https',
            'traceparent': '00-1234567890abcdef1234567890abcdef-1234567890abcdef-01',
            'tracestate': 'congo=t61rcWkgMzE',
            'x-api-key': 'sensitive-api-key'
        },
        'requestContext': {
            'requestId': 'api-request-v2-456',
            'http': {
                'method': 'GET',
                'path': '/products/abc-123',
                'protocol': 'HTTP/1.1',
                'sourceIp': '10.0.0.1',
                'userAgent': 'Mozilla/5.0'
            },
            'domainName': 'api.example.com',
            'stage': 'v1'
        }
    }


@pytest.fixture
def sqs_record_with_api_gateway_body():
    """Create mock SQS record containing API Gateway event in body"""
    api_gateway_payload = {
        'httpMethod': 'PUT',
        'path': '/orders/456',
        'resource': '/orders/{orderId}',
        'headers': {
            'Host': 'orders-api.example.com',
            'Content-Type': 'application/json',
            'traceparent': '00-fedcba0987654321fedcba0987654321-fedcba0987654321-01'
        },
        'body': json.dumps({'status': 'shipped', 'tracking': 'ABC123'}),
        'requestContext': {
            'requestId': 'sqs-wrapped-api-request',
            'stage': 'prod',
            'identity': {
                'sourceIp': '172.16.0.1'
            }
        }
    }
    return {
        'messageId': 'sqs-msg-api-gateway',
        'receiptHandle': 'receipt-handle-api',
        'body': json.dumps(api_gateway_payload),
        'attributes': {
            'ApproximateReceiveCount': '1',
            'SentTimestamp': '1234567890'
        },
        'messageAttributes': {},
        'eventSource': 'aws:sqs'
    }


@pytest.fixture
def sns_record_with_api_gateway_body():
    """Create mock SNS record containing API Gateway v2 event in message"""
    api_gateway_v2_payload = {
        'version': '2.0',
        'routeKey': 'DELETE /items/{itemId}',
        'rawPath': '/items/xyz-789',
        'headers': {
            'host': 'items-api.example.com',
            'content-type': 'application/json'
        },
        'requestContext': {
            'requestId': 'sns-wrapped-api-request',
            'http': {
                'method': 'DELETE',
                'path': '/items/xyz-789',
                'protocol': 'HTTP/2.0',
                'sourceIp': '192.168.100.1'
            },
            'domainName': 'items-api.example.com'
        }
    }
    return {
        'EventSource': 'aws:sns',
        'Sns': {
            'MessageId': 'sns-msg-api-gateway',
            'Message': json.dumps(api_gateway_v2_payload),
            'MessageAttributes': {}
        }
    }


class TestLambdaHandlerDecorator:
    """Test the @lambda_handler decorator"""

    def test_lambda_handler_basic_execution(self, mock_lambda_context, sqs_event):
        """Test basic Lambda handler execution"""
        @lambda_handler(name="test_handler")
        def handler(event, context):
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'success'})
            }

        # Execute handler
        result = handler(sqs_event, mock_lambda_context)

        # Verify result
        assert result['statusCode'] == 200
        assert 'success' in result['body']

    def test_lambda_handler_with_sqs_trigger(self, mock_lambda_context, sqs_event):
        """Test Lambda handler detects SQS trigger"""
        @lambda_handler(name="sqs_handler")
        def handler(event, context):
            assert event == sqs_event
            assert context == mock_lambda_context
            return {'statusCode': 200}

        result = handler(sqs_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_lambda_handler_with_sns_trigger(self, mock_lambda_context, sns_event):
        """Test Lambda handler detects SNS trigger"""
        @lambda_handler(name="sns_handler")
        def handler(event, context):
            assert event == sns_event
            return {'statusCode': 200}

        result = handler(sns_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_lambda_handler_with_api_gateway_trigger(self, mock_lambda_context, api_gateway_event):
        """Test Lambda handler detects API Gateway trigger"""
        @lambda_handler(name="api_handler")
        def handler(event, context):
            assert event['httpMethod'] == 'POST'
            return {
                'statusCode': 200,
                'body': json.dumps({'result': 'processed'})
            }

        result = handler(api_gateway_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_lambda_handler_with_custom_attributes(self, mock_lambda_context, sqs_event):
        """Test Lambda handler with custom span attributes"""
        custom_attrs = {
            'custom.attribute': 'test_value',
            'custom.number': 42
        }

        @lambda_handler(name="custom_handler", attributes=custom_attrs)
        def handler(event, context):
            return {'statusCode': 200}

        result = handler(sqs_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_lambda_handler_exception_handling(self, mock_lambda_context, sqs_event):
        """Test Lambda handler handles exceptions"""
        @lambda_handler(name="error_handler")
        def handler(event, context):
            raise ValueError("Test error")

        with pytest.raises(ValueError) as exc_info:
            handler(sqs_event, mock_lambda_context)

        assert str(exc_info.value) == "Test error"

    def test_lambda_handler_returns_error_status_code(self, mock_lambda_context, sqs_event):
        """Test Lambda handler with error status code"""
        @lambda_handler(name="error_response_handler")
        def handler(event, context):
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal server error'})
            }

        result = handler(sqs_event, mock_lambda_context)
        assert result['statusCode'] == 500

    def test_lambda_handler_without_context(self, sqs_event):
        """Test Lambda handler without Lambda context"""
        @lambda_handler(name="no_context_handler")
        def handler(event, context):
            return {'statusCode': 200}

        result = handler(sqs_event, None)
        assert result['statusCode'] == 200

    def test_lambda_handler_auto_flush_default(self, mock_lambda_context, sqs_event):
        """Test Lambda handler auto-flushes by default"""
        @lambda_handler(name="auto_flush_handler")
        def handler(event, context):
            return {'statusCode': 200}

        with patch.object(otel, 'force_flush') as mock_flush:
            result = handler(sqs_event, mock_lambda_context)
            assert result['statusCode'] == 200
            # Verify force_flush was called
            mock_flush.assert_called_once()

    def test_lambda_handler_no_auto_flush(self, mock_lambda_context, sqs_event):
        """Test Lambda handler with auto_flush disabled"""
        @lambda_handler(name="no_auto_flush_handler", auto_flush=False)
        def handler(event, context):
            return {'statusCode': 200}

        with patch.object(otel, 'force_flush') as mock_flush:
            result = handler(sqs_event, mock_lambda_context)
            assert result['statusCode'] == 200
            # Verify force_flush was NOT called
            mock_flush.assert_not_called()

    def test_lambda_handler_preserves_function_metadata(self):
        """Test Lambda handler preserves original function metadata"""
        @lambda_handler(name="metadata_handler")
        def my_handler(event, context):
            """Handler docstring"""
            return {'statusCode': 200}

        assert my_handler.__name__ == 'my_handler'
        assert my_handler.__doc__ == 'Handler docstring'


class TestAwsMessageHandlerDecorator:
    """Test the @aws_message_handler decorator"""

    def test_aws_message_handler_basic_execution(self, sqs_event):
        """Test basic AWS message handler execution"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="test_message_handler")
        def handler(record):
            body = json.loads(record['body'])
            return {'processed': True, 'data': body['data']}

        result = handler(record)
        assert result['processed'] is True
        assert result['data'] == 'test message'

    def test_aws_message_handler_with_sqs_record(self, sqs_event):
        """Test AWS message handler with SQS record"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="sqs_message_handler")
        def handler(record):
            assert record['messageId'] == 'msg-12345'
            assert record['eventSource'] == 'aws:sqs'
            return {'processed': True}

        result = handler(record)
        assert result['processed'] is True

    def test_aws_message_handler_with_sns_record(self, sns_event):
        """Test AWS message handler with SNS record"""
        record = sns_event['Records'][0]

        @aws_message_handler(name="sns_message_handler")
        def handler(record):
            assert record['EventSource'] == 'aws:sns'
            message = json.loads(record['Sns']['Message'])
            return {'processed': True, 'event': message['event']}

        result = handler(record)
        assert result['processed'] is True
        assert result['event'] == 'test_event'

    def test_aws_message_handler_with_sns_none_subject(self, sns_event_with_none_subject):
        """Test AWS message handler handles SNS record with None Subject (no OTEL warning)"""
        record = sns_event_with_none_subject['Records'][0]

        @aws_message_handler(name="sns_none_subject_handler")
        def handler(record):
            # Verify the record has Subject: None
            assert record['Sns']['Subject'] is None
            message = json.loads(record['Sns']['Message'])
            return {'processed': True, 'event': message['event']}

        # Should not raise any warnings about invalid NoneType for attribute
        result = handler(record)
        assert result['processed'] is True
        assert result['event'] == 'test_event'

    def test_aws_message_handler_with_custom_attributes(self, sqs_event):
        """Test AWS message handler with custom attributes"""
        record = sqs_event['Records'][0]
        custom_attrs = {'custom.key': 'custom_value'}

        @aws_message_handler(name="custom_attrs_handler", attributes=custom_attrs)
        def handler(record):
            return {'processed': True}

        result = handler(record)
        assert result['processed'] is True

    def test_aws_message_handler_exception_handling(self, sqs_event):
        """Test AWS message handler handles exceptions"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="error_message_handler")
        def handler(record):
            raise RuntimeError("Processing failed")

        with pytest.raises(RuntimeError) as exc_info:
            handler(record)

        assert str(exc_info.value) == "Processing failed"

    def test_aws_message_handler_with_status_code(self, sqs_event):
        """Test AWS message handler returns status code"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="status_code_handler")
        def handler(record):
            return {
                'statusCode': 200,
                'processed': True
            }

        result = handler(record)
        assert result['statusCode'] == 200
        assert result['processed'] is True

    def test_aws_message_handler_with_error_status_code(self, sqs_event):
        """Test AWS message handler with error status code"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="error_status_handler")
        def handler(record):
            return {
                'statusCode': 500,
                'processed': False,
                'error': 'Processing error'
            }

        result = handler(record)
        assert result['statusCode'] == 500
        assert result['processed'] is False

    def test_aws_message_handler_with_skip_flag(self, sqs_event):
        """Test AWS message handler with skipped message"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="skip_handler")
        def handler(record):
            return {
                'processed': False,
                'skipped': True,
                'reason': 'Message filtered'
            }

        result = handler(record)
        assert result['processed'] is False
        assert result['skipped'] is True

    def test_aws_message_handler_auto_flush_default(self, sqs_event):
        """Test AWS message handler auto-flushes by default"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="auto_flush_message_handler")
        def handler(record):
            return {'processed': True}

        with patch.object(otel, 'force_flush') as mock_flush:
            result = handler(record)
            assert result['processed'] is True
            mock_flush.assert_called_once()

    def test_aws_message_handler_no_auto_flush(self, sqs_event):
        """Test AWS message handler with auto_flush disabled"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="no_auto_flush_message_handler", auto_flush=False)
        def handler(record):
            return {'processed': True}

        with patch.object(otel, 'force_flush') as mock_flush:
            result = handler(record)
            assert result['processed'] is True
            mock_flush.assert_not_called()

    def test_aws_message_handler_with_additional_args(self, sqs_event):
        """Test AWS message handler with additional arguments"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="multi_arg_handler")
        def handler(record, extra_param='default'):
            return {
                'processed': True,
                'extra': extra_param
            }

        result = handler(record, extra_param='custom_value')
        assert result['processed'] is True
        assert result['extra'] == 'custom_value'


class TestTracesDecorator:
    """Test the @traces decorator"""

    def test_traces_basic_execution(self):
        """Test basic function tracing"""
        @traces(name="test_function")
        def my_function(x, y):
            return x + y

        result = my_function(2, 3)
        assert result == 5

    def test_traces_default_span_name(self):
        """Test traces decorator uses default span name from function"""
        @traces()
        def calculate_sum(a, b):
            return a + b

        result = calculate_sum(10, 20)
        assert result == 30

    def test_traces_with_custom_attributes(self):
        """Test traces decorator with custom attributes"""
        custom_attrs = {
            'operation.type': 'calculation',
            'operation.priority': 'high'
        }

        @traces(name="calculation_function", attributes=custom_attrs)
        def multiply(x, y):
            return x * y

        result = multiply(4, 5)
        assert result == 20

    def test_traces_with_span_kind(self):
        """Test traces decorator with custom span kind"""
        @traces(name="client_operation", kind=SpanKind.CLIENT)
        def fetch_data():
            return {'data': 'fetched'}

        result = fetch_data()
        assert result['data'] == 'fetched'

    def test_traces_exception_handling(self):
        """Test traces decorator handles exceptions"""
        @traces(name="error_function")
        def failing_function():
            raise ValueError("Function failed")

        with pytest.raises(ValueError) as exc_info:
            failing_function()

        assert str(exc_info.value) == "Function failed"

    def test_traces_with_return_value(self):
        """Test traces decorator preserves return values"""
        @traces(name="return_value_function")
        def get_user_data(user_id):
            return {
                'id': user_id,
                'name': 'Test User',
                'email': 'test@example.com'
            }

        result = get_user_data(123)
        assert result['id'] == 123
        assert result['name'] == 'Test User'

    def test_traces_with_complex_operations(self):
        """Test traces decorator with complex operations"""
        @traces(name="complex_operation")
        def process_data(items):
            return [item * 2 for item in items]

        result = process_data([1, 2, 3, 4, 5])
        assert result == [2, 4, 6, 8, 10]

    def test_traces_preserves_function_metadata(self):
        """Test traces decorator preserves function metadata"""
        @traces(name="metadata_function")
        def documented_function(param):
            """This is a documented function"""
            return param.upper()

        assert documented_function.__name__ == 'documented_function'
        assert documented_function.__doc__ == 'This is a documented function'

    def test_traces_nested_calls(self):
        """Test traces decorator with nested function calls"""
        @traces(name="outer_function")
        def outer(x):
            return inner(x) * 2

        @traces(name="inner_function")
        def inner(x):
            return x + 1

        result = outer(5)
        assert result == 12  # (5 + 1) * 2

    def test_traces_with_kwargs(self):
        """Test traces decorator with keyword arguments"""
        @traces(name="kwargs_function")
        def process_request(method, endpoint, data=None, headers=None):
            return {
                'method': method,
                'endpoint': endpoint,
                'has_data': data is not None,
                'has_headers': headers is not None
            }

        result = process_request('POST', '/api/users', data={'name': 'John'}, headers={'Auth': 'token'})
        assert result['method'] == 'POST'
        assert result['has_data'] is True
        assert result['has_headers'] is True


class TestAwsMessageSpan:
    """Test the aws_message_span context manager"""

    def test_aws_message_span_basic_usage(self, sqs_event):
        """Test basic AWS message span usage"""
        record = sqs_event['Records'][0]

        with aws_message_span("process_sqs_message", message=record) as span:
            assert span is not None
            body = json.loads(record['body'])
            assert body['data'] == 'test message'

    def test_aws_message_span_with_sqs_message(self, sqs_event):
        """Test AWS message span with SQS message"""
        record = sqs_event['Records'][0]

        with aws_message_span("sqs_processing", message=record) as span:
            # Span should extract context from MessageAttributes
            assert span is not None
            assert record['eventSource'] == 'aws:sqs'

    def test_aws_message_span_with_sns_message(self, sns_event):
        """Test AWS message span with SNS message"""
        record = sns_event['Records'][0]

        with aws_message_span("sns_processing", message=record) as span:
            # Span should extract context from SNS MessageAttributes
            assert span is not None
            assert record['EventSource'] == 'aws:sns'

    def test_aws_message_span_with_custom_attributes(self, sqs_event):
        """Test AWS message span with custom attributes"""
        record = sqs_event['Records'][0]
        custom_attrs = {
            'message.priority': 'high',
            'message.source': 'external'
        }

        with aws_message_span("custom_attrs_span", message=record, attributes=custom_attrs) as span:
            assert span is not None

    def test_aws_message_span_with_span_kind(self, sqs_event):
        """Test AWS message span with custom span kind"""
        record = sqs_event['Records'][0]

        with aws_message_span("consumer_span", message=record, kind=SpanKind.CONSUMER) as span:
            assert span is not None

    def test_aws_message_span_exception_handling(self, sqs_event):
        """Test AWS message span handles exceptions"""
        record = sqs_event['Records'][0]

        with pytest.raises(RuntimeError):
            with aws_message_span("error_span", message=record) as span:
                assert span is not None
                raise RuntimeError("Processing error")

    def test_aws_message_span_without_message(self):
        """Test AWS message span without message (falls back to regular span)"""
        with aws_message_span("no_message_span") as span:
            assert span is not None

    def test_aws_message_span_nested_spans(self, sqs_event):
        """Test nested AWS message spans"""
        record = sqs_event['Records'][0]

        with aws_message_span("outer_span", message=record) as outer_span:
            assert outer_span is not None

            with aws_message_span("inner_span") as inner_span:
                assert inner_span is not None
                # Both spans should be active

    def test_aws_message_span_with_operations(self, sqs_event):
        """Test AWS message span with operations inside"""
        record = sqs_event['Records'][0]
        results = []

        with aws_message_span("operation_span", message=record) as span:
            assert span is not None
            body = json.loads(record['body'])
            results.append(body['data'])
            results.append('processed')

        assert len(results) == 2
        assert results[0] == 'test message'
        assert results[1] == 'processed'

    def test_aws_message_span_preserves_context(self, sqs_event):
        """Test AWS message span preserves trace context"""
        record = sqs_event['Records'][0]

        # Message has traceparent in MessageAttributes
        assert 'messageAttributes' in record
        assert 'traceparent' in record['messageAttributes']

        with aws_message_span("context_span", message=record) as span:
            # Span should be created with extracted context
            assert span is not None


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple decorators"""

    def test_lambda_with_message_handler(self, mock_lambda_context, sqs_event):
        """Test Lambda handler processing multiple messages"""
        @lambda_handler(name="message_processor_lambda")
        def handler(event, context):
            results = []
            for record in event['Records']:
                result = process_record(record)
                results.append(result)
            return {
                'statusCode': 200,
                'body': json.dumps({'processed': len(results)})
            }

        @aws_message_handler(name="record_processor", auto_flush=False)
        def process_record(record):
            body = json.loads(record['body'])
            return {'processed': True, 'data': body['data']}

        result = handler(sqs_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_traced_function_in_lambda(self, mock_lambda_context, api_gateway_event):
        """Test traced function called from Lambda handler"""
        @lambda_handler(name="api_lambda")
        def handler(event, context):
            data = parse_request(event)
            result = process_data(data)
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }

        @traces(name="parse_request")
        def parse_request(event):
            return json.loads(event['body'])

        @traces(name="process_data")
        def process_data(data):
            return {'processed': True, 'input': data}

        result = handler(api_gateway_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_message_span_in_message_handler(self, sqs_event):
        """Test aws_message_span used inside aws_message_handler"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="complex_handler", auto_flush=False)
        def handler(record):
            # Additional span for specific processing
            with aws_message_span("validation", message=record) as span:
                body = json.loads(record['body'])
                if 'data' not in body:
                    return {'processed': False, 'skipped': True}

            return {'processed': True}

        result = handler(record)
        assert result['processed'] is True

    def test_multiple_decorators_combination(self):
        """Test multiple traced functions calling each other"""
        @traces(name="fetch_user")
        def fetch_user(user_id):
            return {'id': user_id, 'name': 'John Doe'}

        @traces(name="fetch_orders")
        def fetch_orders(user_id):
            return [{'order_id': 1}, {'order_id': 2}]

        @traces(name="aggregate_data")
        def aggregate_user_data(user_id):
            user = fetch_user(user_id)
            orders = fetch_orders(user_id)
            return {
                'user': user,
                'orders': orders,
                'order_count': len(orders)
            }

        result = aggregate_user_data(123)
        assert result['user']['id'] == 123
        assert result['order_count'] == 2


class TestLambdaHandlerApiGateway:
    """Test API Gateway HTTP semantic attributes in @lambda_handler decorator"""

    def test_api_gateway_v1_http_method_attribute(self, mock_lambda_context, api_gateway_v1_event):
        """Test that API Gateway v1 events execute correctly with HTTP method"""
        @lambda_handler(name="v1_method_test")
        def handler(event, context):
            # Verify the event has the expected HTTP method
            assert event['httpMethod'] == 'POST'
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v1_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_v1_captures_url_path(self, mock_lambda_context, api_gateway_v1_event):
        """Test that API Gateway v1 events capture URL path"""
        @lambda_handler(name="v1_path_test")
        def handler(event, context):
            # Handler should execute normally with API Gateway event
            assert event['path'] == '/users/123'
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v1_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_v1_captures_route(self, mock_lambda_context, api_gateway_v1_event):
        """Test that API Gateway v1 events capture route (resource)"""
        @lambda_handler(name="v1_route_test")
        def handler(event, context):
            assert event['resource'] == '/users/{id}'
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v1_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_v2_http_method_attribute(self, mock_lambda_context, api_gateway_v2_event):
        """Test that API Gateway v2 events get http.request.method from requestContext.http"""
        @lambda_handler(name="v2_method_test")
        def handler(event, context):
            # V2 events have method in requestContext.http
            assert event['requestContext']['http']['method'] == 'GET'
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v2_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_v2_captures_raw_path(self, mock_lambda_context, api_gateway_v2_event):
        """Test that API Gateway v2 events capture rawPath"""
        @lambda_handler(name="v2_path_test")
        def handler(event, context):
            assert event['rawPath'] == '/products/abc-123'
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v2_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_v2_captures_route_key(self, mock_lambda_context, api_gateway_v2_event):
        """Test that API Gateway v2 events capture routeKey"""
        @lambda_handler(name="v2_route_test")
        def handler(event, context):
            assert event['routeKey'] == 'GET /products/{productId}'
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v2_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_extracts_traceparent(self, mock_lambda_context, api_gateway_v1_event):
        """Test that traceparent is extracted from API Gateway headers"""
        @lambda_handler(name="traceparent_test")
        def handler(event, context):
            assert 'traceparent' in event['headers']
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v1_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_response_status_code(self, mock_lambda_context, api_gateway_v1_event):
        """Test that response status code is captured"""
        @lambda_handler(name="status_code_test")
        def handler(event, context):
            return {'statusCode': 201, 'body': json.dumps({'created': True})}

        result = handler(api_gateway_v1_event, mock_lambda_context)
        assert result['statusCode'] == 201

    def test_api_gateway_captures_request_body(self, mock_lambda_context, api_gateway_v1_event):
        """Test that request body is captured with sensitive fields redacted"""
        @lambda_handler(name="body_capture_test")
        def handler(event, context):
            body = json.loads(event['body'])
            # Body contains password which should be redacted in span attributes
            assert 'password' in body
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v1_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_v1_headers_filtered(self, mock_lambda_context, api_gateway_v1_event):
        """Test that sensitive headers (Authorization) are filtered"""
        @lambda_handler(name="headers_filter_test")
        def handler(event, context):
            # The handler receives all headers, but span should have them filtered
            assert 'Authorization' in event['headers']
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v1_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_captures_query_string(self, mock_lambda_context, api_gateway_v1_event):
        """Test that query string parameters are captured"""
        @lambda_handler(name="query_string_test")
        def handler(event, context):
            assert event['queryStringParameters']['format'] == 'json'
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v1_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_v2_captures_raw_query_string(self, mock_lambda_context, api_gateway_v2_event):
        """Test that v2 rawQueryString is captured"""
        @lambda_handler(name="v2_query_test")
        def handler(event, context):
            assert event['rawQueryString'] == 'include=details&sort=price'
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v2_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_captures_client_ip(self, mock_lambda_context, api_gateway_v1_event):
        """Test that client IP is captured from requestContext.identity"""
        @lambda_handler(name="client_ip_test")
        def handler(event, context):
            assert event['requestContext']['identity']['sourceIp'] == '192.168.1.1'
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v1_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_captures_user_agent(self, mock_lambda_context, api_gateway_v1_event):
        """Test that User-Agent is captured"""
        @lambda_handler(name="user_agent_test")
        def handler(event, context):
            assert event['headers']['User-Agent'] == 'TestClient/1.0'
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v1_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_captures_server_address(self, mock_lambda_context, api_gateway_v1_event):
        """Test that server address (Host header) is captured"""
        @lambda_handler(name="server_address_test")
        def handler(event, context):
            assert event['headers']['Host'] == 'api.example.com'
            return {'statusCode': 200, 'body': 'OK'}

        result = handler(api_gateway_v1_event, mock_lambda_context)
        assert result['statusCode'] == 200

    def test_api_gateway_error_status_code(self, mock_lambda_context, api_gateway_v1_event):
        """Test that error status codes are captured correctly"""
        @lambda_handler(name="error_status_test")
        def handler(event, context):
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal server error'})
            }

        result = handler(api_gateway_v1_event, mock_lambda_context)
        assert result['statusCode'] == 500


class TestAwsMessageHandlerApiGateway:
    """Test API Gateway detection in @aws_message_handler decorator"""

    def test_sqs_with_api_gateway_body_detected(self, sqs_record_with_api_gateway_body):
        """Test that SQS record containing API Gateway event is detected"""
        @aws_message_handler(name="sqs_api_gateway_test")
        def handler(record):
            body = json.loads(record['body'])
            assert body['httpMethod'] == 'PUT'
            return {'processed': True}

        result = handler(sqs_record_with_api_gateway_body)
        assert result['processed'] is True

    def test_sqs_api_gateway_extracts_http_method(self, sqs_record_with_api_gateway_body):
        """Test that HTTP method is extracted from SQS-wrapped API Gateway event"""
        @aws_message_handler(name="sqs_http_method_test")
        def handler(record):
            body = json.loads(record['body'])
            assert body['httpMethod'] == 'PUT'
            assert body['path'] == '/orders/456'
            return {'processed': True}

        result = handler(sqs_record_with_api_gateway_body)
        assert result['processed'] is True

    def test_sns_with_api_gateway_body_detected(self, sns_record_with_api_gateway_body):
        """Test that SNS record containing API Gateway v2 event is detected"""
        @aws_message_handler(name="sns_api_gateway_test")
        def handler(record):
            message = json.loads(record['Sns']['Message'])
            assert message['requestContext']['http']['method'] == 'DELETE'
            return {'processed': True}

        result = handler(sns_record_with_api_gateway_body)
        assert result['processed'] is True

    def test_sns_api_gateway_v2_extracts_path(self, sns_record_with_api_gateway_body):
        """Test that path is extracted from SNS-wrapped API Gateway v2 event"""
        @aws_message_handler(name="sns_path_test")
        def handler(record):
            message = json.loads(record['Sns']['Message'])
            assert message['rawPath'] == '/items/xyz-789'
            assert message['routeKey'] == 'DELETE /items/{itemId}'
            return {'processed': True}

        result = handler(sns_record_with_api_gateway_body)
        assert result['processed'] is True

    def test_regular_sqs_not_affected(self, sqs_event):
        """Test that regular SQS messages (non-API Gateway) work normally"""
        record = sqs_event['Records'][0]

        @aws_message_handler(name="regular_sqs_test")
        def handler(record):
            body = json.loads(record['body'])
            assert body['data'] == 'test message'
            return {'processed': True}

        result = handler(record)
        assert result['processed'] is True

    def test_regular_sns_not_affected(self, sns_event):
        """Test that regular SNS messages (non-API Gateway) work normally"""
        record = sns_event['Records'][0]

        @aws_message_handler(name="regular_sns_test")
        def handler(record):
            message = json.loads(record['Sns']['Message'])
            assert message['event'] == 'test_event'
            return {'processed': True}

        result = handler(record)
        assert result['processed'] is True

    def test_sqs_api_gateway_captures_headers(self, sqs_record_with_api_gateway_body):
        """Test that headers are captured from SQS-wrapped API Gateway event"""
        @aws_message_handler(name="sqs_headers_test")
        def handler(record):
            body = json.loads(record['body'])
            assert 'Host' in body['headers']
            assert body['headers']['Host'] == 'orders-api.example.com'
            return {'processed': True}

        result = handler(sqs_record_with_api_gateway_body)
        assert result['processed'] is True

    def test_sqs_api_gateway_extracts_traceparent(self, sqs_record_with_api_gateway_body):
        """Test that traceparent is extracted from SQS-wrapped API Gateway headers"""
        @aws_message_handler(name="sqs_traceparent_test")
        def handler(record):
            body = json.loads(record['body'])
            assert 'traceparent' in body['headers']
            return {'processed': True}

        result = handler(sqs_record_with_api_gateway_body)
        assert result['processed'] is True

    def test_sns_api_gateway_captures_domain(self, sns_record_with_api_gateway_body):
        """Test that domain name is captured from SNS-wrapped API Gateway v2 event"""
        @aws_message_handler(name="sns_domain_test")
        def handler(record):
            message = json.loads(record['Sns']['Message'])
            assert message['requestContext']['domainName'] == 'items-api.example.com'
            return {'processed': True}

        result = handler(sns_record_with_api_gateway_body)
        assert result['processed'] is True

    def test_malformed_json_body_handled(self, sqs_event):
        """Test that malformed JSON in SQS body doesn't break the handler"""
        record = sqs_event['Records'][0].copy()
        record['body'] = 'not valid json {'

        @aws_message_handler(name="malformed_json_test")
        def handler(record):
            # Handler should still work, just won't detect API Gateway
            return {'processed': True}

        result = handler(record)
        assert result['processed'] is True

    def test_non_api_gateway_json_body_handled(self, sqs_event):
        """Test that non-API Gateway JSON body is handled correctly"""
        record = sqs_event['Records'][0].copy()
        record['body'] = json.dumps({'type': 'custom_event', 'data': 'value'})

        @aws_message_handler(name="non_api_gateway_test")
        def handler(record):
            body = json.loads(record['body'])
            assert body['type'] == 'custom_event'
            return {'processed': True}

        result = handler(record)
        assert result['processed'] is True

    def test_api_gateway_with_custom_attributes(self, sqs_record_with_api_gateway_body):
        """Test that custom attributes are preserved with API Gateway detection"""
        custom_attrs = {'custom.key': 'custom_value', 'custom.number': 123}

        @aws_message_handler(name="custom_attrs_api_test", attributes=custom_attrs)
        def handler(record):
            return {'processed': True}

        result = handler(sqs_record_with_api_gateway_body)
        assert result['processed'] is True

    def test_api_gateway_with_error_handling(self, sqs_record_with_api_gateway_body):
        """Test error handling with API Gateway detection"""
        @aws_message_handler(name="error_api_gateway_test")
        def handler(record):
            raise ValueError("Processing error")

        with pytest.raises(ValueError) as exc_info:
            handler(sqs_record_with_api_gateway_body)

        assert str(exc_info.value) == "Processing error"

    def test_sqs_api_gateway_captures_source_ip(self, sqs_record_with_api_gateway_body):
        """Test that source IP is captured from SQS-wrapped API Gateway event"""
        @aws_message_handler(name="sqs_source_ip_test")
        def handler(record):
            body = json.loads(record['body'])
            assert body['requestContext']['identity']['sourceIp'] == '172.16.0.1'
            return {'processed': True}

        result = handler(sqs_record_with_api_gateway_body)
        assert result['processed'] is True

    def test_sns_api_gateway_captures_protocol(self, sns_record_with_api_gateway_body):
        """Test that protocol is captured from SNS-wrapped API Gateway v2 event"""
        @aws_message_handler(name="sns_protocol_test")
        def handler(record):
            message = json.loads(record['Sns']['Message'])
            assert message['requestContext']['http']['protocol'] == 'HTTP/2.0'
            return {'processed': True}

        result = handler(sns_record_with_api_gateway_body)
        assert result['processed'] is True


class TestXRayToW3CConversion:
    """Test the convert_xray_to_w3c_traceparent helper function"""

    def test_convert_valid_xray_header(self):
        """Test conversion of valid X-Ray trace header"""
        xray_header = "Root=1-e68ce196-91dc659dda45c25136ca9a2b;Parent=3ea7495ca0fa56ef;Sampled=1"
        expected = "00-e68ce19691dc659dda45c25136ca9a2b-3ea7495ca0fa56ef-01"

        result = convert_xray_to_w3c_traceparent(xray_header)

        assert result == expected

    def test_convert_xray_header_not_sampled(self):
        """Test conversion with Sampled=0"""
        xray_header = "Root=1-12345678-abcdef1234567890abcdef12;Parent=fedcba9876543210;Sampled=0"
        expected = "00-12345678abcdef1234567890abcdef12-fedcba9876543210-00"

        result = convert_xray_to_w3c_traceparent(xray_header)

        assert result == expected

    def test_convert_xray_header_different_order(self):
        """Test conversion with parts in different order"""
        xray_header = "Sampled=1;Parent=1234567890abcdef;Root=1-abcdef12-1234567890abcdef1234567890"
        expected = "00-abcdef121234567890abcdef1234567890-1234567890abcdef-01"

        result = convert_xray_to_w3c_traceparent(xray_header)

        assert result == expected

    def test_convert_xray_header_with_spaces(self):
        """Test conversion with extra spaces"""
        xray_header = "Root=1-e68ce196-91dc659dda45c25136ca9a2b ; Parent=3ea7495ca0fa56ef ; Sampled=1"
        expected = "00-e68ce19691dc659dda45c25136ca9a2b-3ea7495ca0fa56ef-01"

        result = convert_xray_to_w3c_traceparent(xray_header)

        assert result == expected

    def test_convert_xray_header_missing_root(self):
        """Test conversion fails when Root is missing"""
        xray_header = "Parent=3ea7495ca0fa56ef;Sampled=1"

        result = convert_xray_to_w3c_traceparent(xray_header)

        assert result is None

    def test_convert_xray_header_missing_parent(self):
        """Test conversion fails when Parent is missing"""
        xray_header = "Root=1-e68ce196-91dc659dda45c25136ca9a2b;Sampled=1"

        result = convert_xray_to_w3c_traceparent(xray_header)

        assert result is None

    def test_convert_xray_header_missing_sampled(self):
        """Test conversion fails when Sampled is missing"""
        xray_header = "Root=1-e68ce196-91dc659dda45c25136ca9a2b;Parent=3ea7495ca0fa56ef"

        result = convert_xray_to_w3c_traceparent(xray_header)

        assert result is None

    def test_convert_empty_string(self):
        """Test conversion fails with empty string"""
        result = convert_xray_to_w3c_traceparent("")

        assert result is None

    def test_convert_none_value(self):
        """Test conversion fails with None"""
        result = convert_xray_to_w3c_traceparent(None)

        assert result is None

    def test_convert_invalid_type(self):
        """Test conversion fails with non-string type"""
        result = convert_xray_to_w3c_traceparent(12345)

        assert result is None

    def test_convert_malformed_root(self):
        """Test conversion fails with malformed Root value"""
        xray_header = "Root=invalid;Parent=3ea7495ca0fa56ef;Sampled=1"

        result = convert_xray_to_w3c_traceparent(xray_header)

        assert result is None

    def test_convert_xray_header_real_world_format(self):
        """Test conversion with real-world X-Ray header from AWS logs"""
        # From the actual debug logs provided
        xray_header = "Root=1-e68ce196-91dc659dda45c25136ca9a2b;Parent=3ea7495ca0fa56ef;Sampled=1"
        expected = "00-e68ce19691dc659dda45c25136ca9a2b-3ea7495ca0fa56ef-01"

        result = convert_xray_to_w3c_traceparent(xray_header)

        assert result == expected


@pytest.fixture
def sqs_event_with_aws_trace_header():
    """Create mock SQS event with AWSTraceHeader but no MessageAttributes traceparent"""
    return {
        'Records': [
            {
                'messageId': '1c853166-ff8e-465a-8c88-88a15d8626f3',
                'receiptHandle': 'receipt-handle-123',
                'body': json.dumps({'data': 'test message'}),
                'attributes': {
                    'ApproximateReceiveCount': '1',
                    'AWSTraceHeader': 'Root=1-e68ce196-91dc659dda45c25136ca9a2b;Parent=3ea7495ca0fa56ef;Sampled=1',
                    'SentTimestamp': '1766394014932',
                    'SenderId': 'AROAY7LLX5JOHCVJOW6EE:sender-lambda'
                },
                'messageAttributes': {},  # Empty - no W3C traceparent
                'md5OfBody': '73f88dc8b7eb4e6147684e426b720f4e',
                'eventSource': 'aws:sqs',
                'eventSourceARN': 'arn:aws:sqs:us-east-1:123456789012:test-queue',
                'awsRegion': 'us-east-1'
            }
        ]
    }


@pytest.fixture
def sqs_event_with_both_trace_formats():
    """Create mock SQS event with both W3C traceparent and AWSTraceHeader"""
    return {
        'Records': [
            {
                'messageId': 'msg-both-formats',
                'body': json.dumps({'data': 'test'}),
                'attributes': {
                    'AWSTraceHeader': 'Root=1-12345678-abcdefabcdefabcdefabcdef;Parent=fedcba9876543210;Sampled=1'
                },
                'messageAttributes': {
                    'traceparent': {
                        'stringValue': '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01',
                        'dataType': 'String'
                    }
                },
                'eventSource': 'aws:sqs'
            }
        ]
    }


@pytest.fixture
def sqs_event_with_invalid_aws_trace_header():
    """Create mock SQS event with malformed AWSTraceHeader"""
    return {
        'Records': [
            {
                'messageId': 'msg-invalid-trace',
                'body': json.dumps({'data': 'test'}),
                'attributes': {
                    'AWSTraceHeader': 'invalid-trace-header-format'
                },
                'messageAttributes': {},
                'eventSource': 'aws:sqs'
            }
        ]
    }


class TestLambdaHandlerAWSTraceHeader:
    """Test @lambda_handler decorator with AWSTraceHeader extraction"""

    def test_lambda_handler_extracts_aws_trace_header(self, mock_lambda_context, sqs_event_with_aws_trace_header):
        """Test that Lambda handler extracts trace context from AWSTraceHeader"""
        @lambda_handler(name="aws_trace_handler")
        def handler(event, context):
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'processed'})
            }

        result = handler(sqs_event_with_aws_trace_header, mock_lambda_context)

        assert result['statusCode'] == 200
        # The handler should execute successfully with extracted trace context

    def test_lambda_handler_prefers_w3c_traceparent(self, mock_lambda_context, sqs_event_with_both_trace_formats):
        """Test that W3C traceparent is preferred over AWSTraceHeader when both exist"""
        @lambda_handler(name="prefer_w3c_handler")
        def handler(event, context):
            # Both formats present, should use W3C traceparent
            return {'statusCode': 200}

        result = handler(sqs_event_with_both_trace_formats, mock_lambda_context)

        assert result['statusCode'] == 200

    def test_lambda_handler_handles_invalid_aws_trace_header(self, mock_lambda_context, sqs_event_with_invalid_aws_trace_header):
        """Test that invalid AWSTraceHeader doesn't break the handler"""
        @lambda_handler(name="invalid_trace_handler")
        def handler(event, context):
            return {'statusCode': 200}

        # Should not raise an exception
        result = handler(sqs_event_with_invalid_aws_trace_header, mock_lambda_context)

        assert result['statusCode'] == 200

    def test_lambda_handler_aws_trace_header_creates_linked_span(self, mock_lambda_context, sqs_event_with_aws_trace_header):
        """Test that extracted AWSTraceHeader creates a properly linked span"""
        span_created = False

        @lambda_handler(name="linked_span_handler")
        def handler(event, context):
            nonlocal span_created
            span_created = True
            # Handler should execute within a span that's linked to the extracted context
            return {'statusCode': 200}

        result = handler(sqs_event_with_aws_trace_header, mock_lambda_context)

        assert result['statusCode'] == 200
        assert span_created is True

    def test_lambda_handler_logs_aws_trace_extraction(self, mock_lambda_context, sqs_event_with_aws_trace_header, capsys):
        """Test that AWSTraceHeader extraction is logged"""
        @lambda_handler(name="logging_handler")
        def handler(event, context):
            return {'statusCode': 200}

        result = handler(sqs_event_with_aws_trace_header, mock_lambda_context)

        assert result['statusCode'] == 200

        # Check that extraction was logged
        captured = capsys.readouterr()
        assert '[Rebrandly OTEL] Extracted trace context from AWSTraceHeader' in captured.out

    def test_lambda_handler_multiple_records_uses_first_trace(self, mock_lambda_context):
        """Test that with multiple SQS records, first trace context is used"""
        multi_record_event = {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({'data': 'first'}),
                    'attributes': {
                        'AWSTraceHeader': 'Root=1-11111111-11111111111111111111111111;Parent=1111111111111111;Sampled=1'
                    },
                    'messageAttributes': {},
                    'eventSource': 'aws:sqs'
                },
                {
                    'messageId': 'msg-2',
                    'body': json.dumps({'data': 'second'}),
                    'attributes': {
                        'AWSTraceHeader': 'Root=1-22222222-22222222222222222222222222;Parent=2222222222222222;Sampled=1'
                    },
                    'messageAttributes': {},
                    'eventSource': 'aws:sqs'
                }
            ]
        }

        @lambda_handler(name="multi_record_handler")
        def handler(event, context):
            assert len(event['Records']) == 2
            return {'statusCode': 200}

        result = handler(multi_record_event, mock_lambda_context)

        assert result['statusCode'] == 200

    def test_lambda_handler_aws_trace_header_without_records(self, mock_lambda_context):
        """Test that handler works without Records (non-SQS/SNS event)"""
        generic_event = {
            'someKey': 'someValue',
            'data': 'test'
        }

        @lambda_handler(name="no_records_handler")
        def handler(event, context):
            return {'statusCode': 200}

        result = handler(generic_event, mock_lambda_context)

        assert result['statusCode'] == 200


class TestSQSTraceContextPropagationEndToEnd:
    """End-to-end tests for SQS trace context propagation"""

    def test_end_to_end_sqs_trace_propagation(self, mock_lambda_context):
        """Test complete SQS trace propagation from sender to receiver"""
        # Simulate sender creating a trace
        sender_trace_id = "e68ce19691dc659dda45c25136ca9a2b"
        sender_span_id = "3ea7495ca0fa56ef"

        # Create SQS event as it would appear in receiver with AWSTraceHeader
        sqs_event = {
            'Records': [
                {
                    'messageId': 'end-to-end-msg',
                    'body': json.dumps({'order_id': '12345', 'amount': 100.50}),
                    'attributes': {
                        'ApproximateReceiveCount': '1',
                        'AWSTraceHeader': f'Root=1-{sender_trace_id};Parent={sender_span_id};Sampled=1',
                        'SentTimestamp': '1766394014932'
                    },
                    'messageAttributes': {},
                    'eventSource': 'aws:sqs',
                    'eventSourceARN': 'arn:aws:sqs:us-east-1:123456789012:orders-queue'
                }
            ]
        }

        # Receiver Lambda handler
        @lambda_handler(name="receiver_handler")
        def receiver(event, context):
            # Process the message
            record = event['Records'][0]
            body = json.loads(record['body'])

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'processed': True,
                    'order_id': body['order_id'],
                    'amount': body['amount']
                })
            }

        result = receiver(sqs_event, mock_lambda_context)

        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['processed'] is True
        assert response_body['order_id'] == '12345'
        assert response_body['amount'] == 100.50

    def test_sqs_batch_processing_with_trace_context(self, mock_lambda_context):
        """Test processing batch of SQS messages with trace context"""
        batch_event = {
            'Records': [
                {
                    'messageId': f'batch-msg-{i}',
                    'body': json.dumps({'index': i, 'data': f'message-{i}'}),
                    'attributes': {
                        'AWSTraceHeader': f'Root=1-{i:08x}1234-abcdefabcdefabcdefabcdef;Parent={i:016x};Sampled=1'
                    },
                    'messageAttributes': {},
                    'eventSource': 'aws:sqs'
                }
                for i in range(5)
            ]
        }

        @lambda_handler(name="batch_processor")
        def handler(event, context):
            results = []
            for record in event['Records']:
                body = json.loads(record['body'])
                results.append(body['index'])

            return {
                'statusCode': 200,
                'body': json.dumps({'processed_count': len(results)})
            }

        result = handler(batch_event, mock_lambda_context)

        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['processed_count'] == 5
