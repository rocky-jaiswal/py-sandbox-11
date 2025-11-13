# Structured Logging Guide

This API uses **structlog** for structured, machine-readable logging that's optimized for log aggregation systems (ELK Stack, Datadog, CloudWatch, Splunk, etc.).

## Log Format

### Development (Console)
Human-readable console output with colored formatting:
```
2025-01-15T10:30:45.123456Z [info     ] http_request_complete request_id=abc-123 method=POST path=/v1/auth/login status_code=200 response_time_ms=45.23 client_ip=127.0.0.1 success=True
```

### Production (JSON)
Machine-readable JSON format for log ingestion:
```json
{
  "event": "http_request_complete",
  "timestamp": "2025-01-15T10:30:45.123456Z",
  "level": "info",
  "logger": "api.main",
  "request_id": "abc-123-def-456",
  "method": "POST",
  "path": "/v1/auth/login",
  "status_code": 200,
  "response_time_ms": 45.23,
  "client_ip": "127.0.0.1",
  "user_agent": "curl/7.81.0",
  "http_version": "1.1",
  "success": true
}
```

## Log Events

### HTTP Request Lifecycle

#### 1. Request Start
```json
{
  "event": "http_request_start",
  "request_id": "uuid-v4",
  "method": "POST",
  "path": "/v1/todos",
  "query_params": "page=1&limit=10",
  "client_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "http_version": "1.1"
}
```

#### 2. Request Complete (Success)
```json
{
  "event": "http_request_complete",
  "request_id": "uuid-v4",
  "method": "POST",
  "path": "/v1/todos",
  "status_code": 201,
  "response_time_ms": 123.45,
  "client_ip": "192.168.1.100",
  "success": true
}
```

#### 3. Request Failed (Exception)
```json
{
  "event": "http_request_failed",
  "level": "error",
  "request_id": "uuid-v4",
  "method": "POST",
  "path": "/v1/todos",
  "response_time_ms": 56.78,
  "error": "Connection timeout",
  "error_type": "TimeoutError",
  "client_ip": "192.168.1.100"
}
```

### Application Events

#### Client Errors (4xx)
```json
{
  "event": "client_error",
  "level": "warning",
  "request_id": "uuid-v4",
  "status_code": 404,
  "message": "Todo with ID 999 not found",
  "path": "/v1/todos/999",
  "method": "GET"
}
```

#### Server Errors (5xx)
```json
{
  "event": "server_error",
  "level": "error",
  "request_id": "uuid-v4",
  "status_code": 500,
  "message": "Database connection lost",
  "path": "/v1/todos",
  "method": "POST",
  "details": {...}
}
```

#### Validation Errors
```json
{
  "event": "validation_error",
  "level": "warning",
  "request_id": "uuid-v4",
  "path": "/v1/auth/register",
  "method": "POST",
  "errors": [
    {
      "field": "body.email",
      "message": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

#### Database Errors
```json
{
  "event": "database_error",
  "level": "error",
  "request_id": "uuid-v4",
  "path": "/v1/todos",
  "method": "POST",
  "error": "Connection refused",
  "exc_info": true
}
```

## Key Fields

### Standard Fields (All Logs)
- `event` - Event type/name (required for indexing)
- `timestamp` - ISO 8601 timestamp with timezone
- `level` - Log level (debug, info, warning, error)
- `logger` - Logger name (module path)

### HTTP Request Fields
- `request_id` - Unique UUID for request tracing
- `method` - HTTP method (GET, POST, etc.)
- `path` - Request path
- `query_params` - Query parameters (if present)
- `status_code` - HTTP response status
- `response_time_ms` - Response time in milliseconds (float)
- `client_ip` - Client IP address
- `user_agent` - User-Agent header
- `http_version` - HTTP protocol version
- `success` - Boolean indicating success (2xx/3xx)

### Error Fields
- `error` - Error message
- `error_type` - Exception class name
- `traceback` - Full stack trace (for 5xx errors)
- `details` - Additional error context

## Response Headers

Every response includes tracking headers:
- `X-Request-ID` - Unique request identifier
- `X-Process-Time` - Response time in milliseconds

## Configuration

Set via environment variables:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# JSON output for production (true/false)
LOG_JSON=false  # Development: console format
LOG_JSON=true   # Production: JSON format
```

## Querying Logs

### Example: Find slow requests (>1000ms)
```
response_time_ms:[1000 TO *]
```

### Example: Find all errors for a specific request
```
request_id:"abc-123-def-456" AND level:error
```

### Example: Authentication failures
```
event:client_error AND path:/v1/auth/login AND status_code:401
```

### Example: Average response time by endpoint
```
event:http_request_complete | stats avg(response_time_ms) by path
```

### Example: Error rate by status code
```
event:http_request_complete | stats count by status_code
```

## Best Practices

1. **Request Tracing** - Use `X-Request-ID` header to trace requests across services
2. **Structured Fields** - Always use key-value pairs, never log unstructured strings
3. **Performance Monitoring** - Monitor `response_time_ms` for SLA compliance
4. **Error Alerting** - Set up alerts on `level:error` with specific event types
5. **Retention** - Keep INFO logs for 7-30 days, ERROR logs for 90+ days

## Integration Examples

### ELK Stack (Elasticsearch, Logstash, Kibana)
```json
{
  "index_pattern": "fastapi-logs-*",
  "timestamp_field": "@timestamp",
  "fields": {
    "request_id": { "type": "keyword" },
    "response_time_ms": { "type": "float" },
    "status_code": { "type": "integer" },
    "client_ip": { "type": "ip" }
  }
}
```

### Datadog
```python
# All structured fields automatically become tags
# Query: service:fastapi-api status_code:500
```

### CloudWatch Insights
```sql
fields @timestamp, request_id, response_time_ms, status_code
| filter event = "http_request_complete"
| stats avg(response_time_ms) by path
```

### Prometheus Metrics (from logs)
```promql
# P95 latency
histogram_quantile(0.95,
  rate(http_request_duration_milliseconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m])
```
