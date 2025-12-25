import unittest
from unittest.mock import patch, MagicMock, ANY, call
import importlib
import os

# Import the module under test
import src.rebrandly_otel
from src.rebrandly_otel import RebrandlyOTEL, otel, lambda_handler, aws_message_handler, span, force_flush, shutdown
from opentelemetry.trace import SpanKind, Status, StatusCode


class TestRebrandlyOTELUsage(unittest.TestCase):

    def setUp(self):
        # Reset the singleton and reload the module before each test
        RebrandlyOTEL._instance = None
        RebrandlyOTEL._initialized = False
        importlib.reload(src.rebrandly_otel)

        # Patch external dependencies at the module level (where they are used)
        self.mock_propagate = patch('src.rebrandly_otel.propagate').start()
        self.mock_context = patch('src.rebrandly_otel.otel_context').start()
        self.mock_psutil = patch('src.rebrandly_otel.psutil').start()

        # Patch the attributes of the otel instance directly
        self.mock_tracer = MagicMock()
        self.mock_meter = MagicMock()
        self.mock_logger = MagicMock()

        otel._tracer = self.mock_tracer
        otel._meter = self.mock_meter
        otel._logger = self.mock_logger

        # Configure mock behaviors for tracer
        mock_span_instance = MagicMock()
        mock_span_instance.set_status = MagicMock()
        mock_span_instance.record_exception = MagicMock()
        mock_span_instance.set_attribute = MagicMock()

        mock_start_span_context_manager = MagicMock()
        mock_start_span_context_manager.__enter__.return_value = mock_span_instance
        mock_start_span_context_manager.__exit__.return_value = None

        self.mock_tracer.start_span.return_value = mock_start_span_context_manager

        # Configure mock behaviors for meter
        self.mock_meter.GlobalMetrics.memory_usage_bytes.set = MagicMock()
        self.mock_meter.GlobalMetrics.cpu_usage_percentage.set = MagicMock()

        # Configure mock behaviors for psutil
        self.mock_psutil.cpu_percent.return_value = 10.0
        mock_virtual_memory = MagicMock()
        mock_virtual_memory.used = 1000000
        mock_virtual_memory.percent = 50.0
        self.mock_psutil.virtual_memory.return_value = mock_virtual_memory

        self.addCleanup(patch.stopall)

    def test_initialization(self):
        # otel instance is already created and initialized in setUp
        self.assertIsInstance(otel, RebrandlyOTEL)
        # The tracer, meter, logger properties are accessed during otel initialization
        # which happens when the module is reloaded in setUp.
        # So, we check that the mocks were assigned.
        self.assertIs(otel.tracer, self.mock_tracer)
        self.assertIs(otel.meter, self.mock_meter)
        self.assertIs(otel.logger, self.mock_logger)

    def test_span_context_manager(self):
        with span("test_span", attributes={"key": "value"}) as s:
            self.assertIsNotNone(s)
            s.set_attribute("another_key", "another_value")

        self.mock_tracer.start_span.assert_called_once_with(
            name="test_span", attributes={"key": "value"}, kind=SpanKind.INTERNAL
        )
        span_mock = self.mock_tracer.start_span.return_value.__enter__.return_value
        self.assertEqual(span_mock.set_status.call_args[0][0].status_code, StatusCode.OK)

    def test_span_context_manager_with_exception(self):
        with self.assertRaises(ValueError):
            with span("error_span"):
                raise ValueError("Something went wrong")

        self.mock_tracer.start_span.assert_called_once_with(
            name="error_span", attributes=None, kind=SpanKind.INTERNAL
        )
        span_mock = self.mock_tracer.start_span.return_value.__enter__.return_value
        span_mock.record_exception.assert_called_once()
        self.assertEqual(span_mock.set_status.call_args[0][0].status_code, StatusCode.ERROR)
        self.assertEqual(span_mock.set_status.call_args[0][0].description, "Something went wrong")

    def test_lambda_handler_basic(self):
        @lambda_handler("my_lambda")
        def handler(event, context):
            return {"statusCode": 200, "body": "OK"}

        mock_context = MagicMock()
        mock_context.aws_request_id = "req123"
        mock_context.function_arn = "arn:aws:lambda:us-east-1:123456789012:function:my_lambda"
        mock_context.function_name = "my_lambda"
        mock_context.function_version = "$LATEST"

        result = handler({}, mock_context)

        self.assertEqual(result, {"statusCode": 200, "body": "OK"})
        self.mock_tracer.start_span.assert_called_once_with(
            name="my_lambda",
            attributes={
                "faas.trigger": "direct",
                "faas.execution": "req123",
                "faas.id": "arn:aws:lambda:us-east-1:123456789012:function:my_lambda",
                "faas.name": "my_lambda",
                "faas.version": "$LATEST"
            },
            kind=SpanKind.SERVER
        )
        span_mock = self.mock_tracer.start_span.return_value.__enter__.return_value
        # Per OTel spec: success leaves status UNSET (no set_status called)
        span_mock.set_status.assert_not_called()
        self.mock_tracer.force_flush.assert_called_once()
        self.mock_meter.force_flush.assert_called_once()
        self.mock_logger.force_flush.assert_called_once()

    def test_lambda_handler_with_sqs_event(self):
        @lambda_handler("sqs_processor")
        def handler(event, context):
            return {"statusCode": 200}

        sqs_event = {
            "Records": [
                {
                    "messageId": "msg1",
                    "eventSource": "aws:sqs",
                    "messageAttributes": {
                        "traceparent": {"stringValue": "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01", "dataType": "String"}
                    }
                }
            ]
        }
        mock_context = MagicMock()
        mock_context.aws_request_id = "req456"

        handler(sqs_event, mock_context)

        self.mock_propagate.extract.assert_called_once_with({'traceparent': '00-0123456789abcdef0123456789abcdef-0123456789abcdef-01'})
        self.mock_context.attach.assert_called_once()
        self.mock_context.detach.assert_called_once()
        self.mock_tracer.start_span.assert_called_once_with(
            name="sqs_processor",
            attributes=ANY,
            kind=SpanKind.SERVER
        )
        span_mock = self.mock_tracer.start_span.return_value.__enter__.return_value
        # Per OTel spec: success leaves status UNSET (no set_status called)
        span_mock.set_status.assert_not_called()
        self.mock_tracer.force_flush.assert_called_once()
        self.mock_meter.force_flush.assert_called_once()
        self.mock_logger.force_flush.assert_called_once()

    def test_lambda_handler_with_sns_event(self):
        @lambda_handler("sns_processor")
        def handler(event, context):
            return {"statusCode": 200}

        sns_event = {
            "Records": [
                {
                    "EventSource": "aws:sns",
                    "Sns": {
                        "MessageId": "sns_msg1",
                        "TopicArn": "arn:aws:sns:us-east-1:123456789012:my-topic",
                        "Subject": "test_subject",
                        "MessageAttributes": {
                            "traceparent": {"Type": "String", "Value": "00-fedcba9876543210fedcba9876543210-fedcba9876543210-01"}
                        }
                    }
                }
            ]
        }
        mock_context = MagicMock()
        mock_context.aws_request_id = "req789"

        handler(sns_event, mock_context)

        self.mock_propagate.extract.assert_called_once_with({'traceparent': '00-fedcba9876543210fedcba9876543210-fedcba9876543210-01'})
        self.mock_context.attach.assert_called_once()
        self.mock_context.detach.assert_called_once()
        self.mock_tracer.start_span.assert_called_once_with(
            name="sns_processor",
            attributes=ANY,
            kind=SpanKind.SERVER
        )
        span_mock = self.mock_tracer.start_span.return_value.__enter__.return_value
        # Per OTel spec: success leaves status UNSET (no set_status called)
        span_mock.set_status.assert_not_called()
        self.mock_tracer.force_flush.assert_called_once()
        self.mock_meter.force_flush.assert_called_once()
        self.mock_logger.force_flush.assert_called_once()

    def test_aws_message_handler_basic(self):
        @aws_message_handler("msg_processor")
        def handler(record):
            return {"processed": True}

        record = {"messageId": "rec123"}
        result = handler(record)

        self.assertEqual(result, {"processed": True})
        self.mock_tracer.start_span.assert_called_once_with(
            name="msg_processor",
            attributes={'messaging.operation': 'process'},
            kind=SpanKind.CONSUMER
        )
        span_mock = self.mock_tracer.start_span.return_value.__enter__.return_value
        # Non-HTTP response: set OK for success
        self.assertEqual(span_mock.set_status.call_args[0][0].status_code, StatusCode.OK)
        self.mock_psutil.cpu_percent.assert_called_once()
        self.mock_psutil.virtual_memory.assert_called_once()
        self.mock_meter.GlobalMetrics.memory_usage_bytes.set.assert_called_once()
        self.mock_meter.GlobalMetrics.cpu_usage_percentage.set.assert_called_once()
        self.mock_tracer.force_flush.assert_called_once()
        self.mock_meter.force_flush.assert_called_once()
        self.mock_logger.force_flush.assert_called_once()

    def test_aws_message_span_context_manager(self):
        sqs_message = {
            "messageId": "sqs_msg_id",
            "eventSource": "aws:sqs",
            "awsRegion": "us-east-1",
            "messageAttributes": {
                "traceparent": {"stringValue": "00-11111111111111111111111111111111-2222222222222222-01", "dataType": "String"}
            }
        }
        with otel.aws_message_span("process_sqs", message=sqs_message) as s:
            self.assertIsNotNone(s)
            s.set_attribute("custom_attr", "custom_value")

        self.mock_tracer.start_span.assert_called_once_with(
            name="process_sqs",
            attributes={
                'messaging.operation': 'process',
                'messaging.message_id': 'sqs_msg_id',
                'messaging.system': 'aws_sqs',
                'cloud.region': 'us-east-1'
            },
            kind=SpanKind.CONSUMER
        )
        span_mock = self.mock_tracer.start_span.return_value.__enter__.return_value
        span_mock.set_attribute.assert_called_once_with("custom_attr", "custom_value")
        # Non-HTTP span: set OK for success
        self.assertEqual(span_mock.set_status.call_args[0][0].status_code, StatusCode.OK)

    def test_force_flush(self):
        otel.force_flush()
        self.mock_tracer.force_flush.assert_called_once()
        self.mock_meter.force_flush.assert_called_once()
        self.mock_logger.force_flush.assert_called_once()

    def test_shutdown(self):
        otel.shutdown()
        self.mock_tracer.shutdown.assert_called_once()
        self.mock_meter.shutdown.assert_called_once()
        self.mock_logger.shutdown.assert_called_once()

    def test_detect_lambda_trigger(self):
        # Test direct invocation
        self.assertEqual(otel._detect_lambda_trigger(None), 'direct')
        self.assertEqual(otel._detect_lambda_trigger({}), 'direct')

        # Test SQS
        sqs_event = {'Records': [{'eventSource': 'aws:sqs'}]}
        self.assertEqual(otel._detect_lambda_trigger(sqs_event), 'sqs')

        # Test SNS
        sns_event = {'Records': [{'eventSource': 'aws:sns'}]}
        self.assertEqual(otel._detect_lambda_trigger(sns_event), 'sns')

        # Test API Gateway
        api_gw_event = {'httpMethod': 'GET'}
        self.assertEqual(otel._detect_lambda_trigger(api_gw_event), 'api_gateway')

        api_gw_v2_event = {'requestContext': {'http': {}}}
        self.assertEqual(otel._detect_lambda_trigger(api_gw_v2_event), 'api_gateway_v2')

        # Test EventBridge
        eventbridge_event = {'source': 'aws.events'}
        self.assertEqual(otel._detect_lambda_trigger(eventbridge_event), 'eventbridge')

        # Test unknown
        unknown_event = {'some_key': 'some_value'}
        self.assertEqual(otel._detect_lambda_trigger(unknown_event), 'unknown')

    def test_context_propagation_methods(self):
        # Mock the global propagate and context objects
        mock_propagate = MagicMock()
        mock_context = MagicMock()

        with patch('src.rebrandly_otel.propagate', mock_propagate), patch('src.rebrandly_otel.otel_context', mock_context):

            # Test inject_context
            carrier = {}
            otel.inject_context(carrier)
            mock_propagate.inject.assert_called_once_with(carrier)

            # Test extract_context
            extracted_ctx = otel.extract_context(carrier)
            mock_propagate.extract.assert_called_once_with(carrier)
            self.assertEqual(extracted_ctx, mock_propagate.extract.return_value)

            # Test attach_context
            mock_propagate.extract.reset_mock()
            mock_context.attach.reset_mock()
            token = otel.attach_context(carrier)
            mock_propagate.extract.assert_called_once_with(carrier)
            mock_context.attach.assert_called_once_with(mock_propagate.extract.return_value)
            self.assertEqual(token, mock_context.attach.return_value)

            # Test detach_context
            mock_context.detach.reset_mock()
            otel.detach_context(token)
            mock_context.detach.assert_called_once_with(token)


if __name__ == '__main__':
    unittest.main()