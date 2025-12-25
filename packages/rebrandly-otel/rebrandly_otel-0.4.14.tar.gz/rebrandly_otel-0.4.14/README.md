# rebrandly-otel (Python)

OpenTelemetry SDK for Rebrandly Python services.

## Installation

```bash
pip install rebrandly-otel
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OTEL_SERVICE_NAME` | Yes | Service identifier |
| `OTEL_SERVICE_APPLICATION` | Yes | Application namespace (groups services) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Yes | OTLP collector endpoint |
| `OTEL_REPO_NAME` | No | Repository name |
| `OTEL_COMMIT_ID` | No | Commit ID for version tracking |

## Lambda Handler

```python
from rebrandly_otel import lambda_handler, logger

@lambda_handler(name="my-function")
def handler(event, context):
    logger.info("Processing", extra={"event_id": event.get("id")})
    return {"statusCode": 200}
```

## AWS Message Handler

```python
from rebrandly_otel import aws_message_handler

@aws_message_handler(name="process-message")
def process_record(record):
    # trace context automatically extracted from message
    return {"success": True}
```

## Framework Middleware

### Flask

```python
from flask import Flask
from rebrandly_otel import otel, setup_flask

app = Flask(__name__)
setup_flask(otel, app)

@app.route('/api/users')
def get_users():
    return {"users": []}
```

### FastAPI

```python
from fastapi import FastAPI
from rebrandly_otel import otel, setup_fastapi

app = FastAPI()
setup_fastapi(otel, app)

@app.get('/api/users')
async def get_users():
    return {"users": []}
```

## Custom Instrumentation

### Manual Spans

```python
from rebrandly_otel import otel

with otel.span("operation-name", attributes={"user.id": user_id}):
    # your code
```

### Structured Logging

```python
from rebrandly_otel import logger

logger.info("Order processed", extra={"order_id": order_id, "amount": amount})
```

## HTTP Client Tracing

### Using requests

```python
from rebrandly_otel import requests_with_tracing

session = requests_with_tracing()
response = session.get('https://api.rebrandly.com/v1/links')
```

### Using httpx

```python
from rebrandly_otel import httpx_with_tracing

client = httpx_with_tracing()
response = client.get('https://api.rebrandly.com/v1/links')
```

### Manual Header Injection

```python
from rebrandly_otel import inject_traceparent

headers = {'Content-Type': 'application/json'}
inject_traceparent(headers)
# headers now includes traceparent
```

## Custom Metrics

```python
from rebrandly_otel import meter

# Counter
request_counter = meter.meter.create_counter(
    name='http.requests.total',
    description='Total HTTP requests'
)
request_counter.add(1, {'method': 'GET', 'endpoint': '/api/users'})

# Histogram
duration = meter.meter.create_histogram(
    name='http.request.duration',
    description='Request duration in ms',
    unit='ms'
)
duration.record(123, {'endpoint': '/api/users'})

# Gauge
gauge = meter.meter.create_gauge(
    name='queue.size',
    description='Current queue size'
)
gauge.record(42)
```

## Database Instrumentation

### PyMySQL

```python
import pymysql
from rebrandly_otel import otel, instrument_pymysql

connection = pymysql.connect(host='localhost', user='user', password='pass', database='db')
connection = instrument_pymysql(otel, connection)

# All queries now automatically traced
with connection.cursor() as cursor:
    cursor.execute("SELECT * FROM users WHERE id = %s", (123,))
```

### SQLite3

```python
import sqlite3
from rebrandly_otel import otel, instrument_sqlite3

# Create connection
connection = sqlite3.connect('database.db')  # or ':memory:'

# Instrument connection
connection = instrument_sqlite3(otel, connection, options={
    'slow_query_threshold_ms': 1000,
    'capture_bindings': False
})

# Use normally - all queries are traced
cursor = connection.cursor()
cursor.execute("SELECT * FROM users WHERE id = ?", (123,))

# SQLite also supports direct connection execution
connection.execute("CREATE TABLE test (id INTEGER)")
```

### Redis

Redis operations are automatically traced - just initialize the SDK:

```python
from rebrandly_otel import otel
import redis

otel.initialize()  # Redis instrumentation enabled automatically

client = redis.Redis(host='localhost', port=6379, db=0)
client.set('key', 'value')  # Automatically traced
```

**Note:** Unlike PyMySQL/SQLite3, Redis requires no explicit instrumentation call. All Redis clients (including async and cluster) are automatically traced when the SDK initializes.

## AWS Message Handling (SQS/SNS)

### Sending with Trace Context

```python
from rebrandly_otel import otel

trace_attrs = otel.tracer.get_attributes_for_aws_from_context()
sqs.send_message(QueueUrl=url, MessageBody=json.dumps(data), MessageAttributes=trace_attrs)
```

### Receiving with Context Extraction

```python
from rebrandly_otel import aws_message_span

with aws_message_span("process-message", message=record):
    # trace context automatically extracted
```

## Force Flush (Critical for Lambda)

```python
from rebrandly_otel import force_flush, shutdown

# Before Lambda exits
force_flush(timeout_millis=5000)
shutdown()
```

## Span Status Methods

```python
from rebrandly_otel import otel

otel.tracer.set_span_error("Operation failed")
otel.tracer.set_span_error("Failed", exception=e)
otel.tracer.set_span_success()
```

## Cost Optimization (Errors-Only Filtering)

For high-volume services, filter out successful spans to reduce costs by 90-99%:

```bash
export OTEL_SPAN_ATTRIBUTES="span.filter=errors-only"
```

This adds the filter attribute to all spans. The OTEL Gateway drops successful spans while keeping all errors. Metrics are still generated from 100% of traces at the agent level.

## Tips

- Always call `force_flush()` before Lambda exits
- Use `OTEL_DEBUG=true` for local debugging
- Keep metric cardinality low (< 1000 combinations)
- Add 2-3 seconds buffer to Lambda timeout for flush

## Troubleshooting

**No Data Exported:**
- Verify `OTEL_EXPORTER_OTLP_ENDPOINT` is set
- Enable `OTEL_DEBUG=true` for console output
- Check network connectivity to collector

**Missing Traces in Lambda:**
- Ensure `force_flush()` is called before exit
- Add 2-3s buffer to Lambda timeout
- Use `@lambda_handler` decorator with `auto_flush=True`

**Context Not Propagating:**
- Sending: Use `otel.tracer.get_attributes_for_aws_from_context()` for SQS/SNS
- HTTP: Use `inject_traceparent(headers)` before requests
- Receiving: Use `aws_message_span` context manager

## Best Practices

**Do:**
- Use context managers for spans (auto-cleanup)
- Use meaningful span names (`fetch-user-profile`, not `handler`)
- Add business context (`order.id`, `user.id`) to spans
- Flush telemetry before Lambda exits
- Use bounded attribute values in metrics

**Don't:**
- Store large payloads in span attributes (< 1KB)
- Use high-cardinality attributes in metrics (`user_id`, `request_id`)
- Hardcode service names (use env vars)
- Skip error recording in except blocks
