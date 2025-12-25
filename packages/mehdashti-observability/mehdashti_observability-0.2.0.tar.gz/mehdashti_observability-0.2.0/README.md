# smart-observability

> Observability utilities for Smart Platform - correlation IDs, health checks, and request tracing

## Features

- ✅ **Correlation ID Middleware** - Automatic request tracing across frontend and backend
- ✅ **Health Check Endpoints** - Standardized /health and /ready endpoints
- ✅ **Context Management** - Store correlation IDs in context for the request lifecycle
- ✅ **FastAPI Integration** - Drop-in middleware and helpers for FastAPI/Starlette apps
- ✅ **Header Standardization** - Uses `X-Correlation-Id` header (RFC 6648)
- ✅ **Kubernetes Ready** - Compatible with liveness and readiness probes

## Installation

```bash
uv add smart-observability
```

## Quick Start

### Basic Setup

```python
from fastapi import FastAPI
from mehdashti_observability import CorrelationMiddleware

app = FastAPI()

# Add correlation middleware
app.add_middleware(CorrelationMiddleware)

@app.get("/users")
async def get_users():
    # Correlation ID is automatically available in context
    return {"users": []}
```

### Using Correlation IDs

```python
from mehdashti_observability import get_correlation_id
from loguru import logger

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    correlation_id = get_correlation_id()

    logger.info(
        f"Fetching user {user_id}",
        extra={"correlation_id": correlation_id}
    )

    # Your logic here
    return {"id": user_id}
```

### With smart-errors

```python
from fastapi import FastAPI
from mehdashti_observability import CorrelationMiddleware
from mehdashti_errors import setup_error_handlers

app = FastAPI()

# IMPORTANT: Add CorrelationMiddleware BEFORE setting up error handlers
app.add_middleware(CorrelationMiddleware)

# Error handlers will automatically include correlation IDs
setup_error_handlers(app)
```

## API Reference

### Middleware

#### `CorrelationMiddleware`

FastAPI/Starlette middleware that:
1. Extracts correlation ID from `X-Correlation-Id` header
2. Generates a new UUID v7 if none provided
3. Stores the ID in context for request duration
4. Adds the ID to response headers

### Functions

#### `get_correlation_id() -> str | None`

Get the current correlation ID from context.

#### `generate_correlation_id() -> str`

Generate a new UUID v7 correlation ID.

### Constants

#### `CORRELATION_ID_HEADER = "X-Correlation-Id"`

The HTTP header name for correlation IDs.

## How It Works

### Request Flow

1. Frontend sends request with `X-Correlation-Id` header (auto-generated)
2. CorrelationMiddleware extracts or generates correlation ID
3. Context Variable stores ID for the request duration
4. Your Code can access ID via `get_correlation_id()`
5. Error Handlers include ID in error responses
6. Response includes `X-Correlation-Id` header

## Health Check Endpoints

### Quick Setup

```python
from fastapi import FastAPI
from mehdashti_observability import (
    create_liveness_endpoint,
    create_readiness_endpoint,
)

app = FastAPI()

# Simple liveness probe
app.get("/health")(create_liveness_endpoint("1.0.0"))

# Readiness probe with dependency checks
async def check_database():
    await db.execute("SELECT 1")

async def check_redis():
    await redis.ping()

app.get("/ready")(
    create_readiness_endpoint([check_database, check_redis], "1.0.0")
)
```

### Health Check Responses

**Liveness** (`/health`):
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2025-12-21T10:00:00Z"
}
```

**Readiness** (`/ready`):
```json
{
  "status": "ok",
  "checks": [
    {
      "name": "check_database",
      "status": "ok",
      "latency_ms": 12.5
    },
    {
      "name": "check_redis",
      "status": "ok",
      "latency_ms": 5.2
    }
  ],
  "version": "1.0.0",
  "timestamp": "2025-12-21T10:00:00Z"
}
```

### Kubernetes Integration

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-service
spec:
  containers:
    - name: app
      image: my-service:latest
      livenessProbe:
        httpGet:
          path: /health
          port: 8000
        initialDelaySeconds: 5
        periodSeconds: 10
      readinessProbe:
        httpGet:
          path: /ready
          port: 8000
        initialDelaySeconds: 10
        periodSeconds: 5
```

### Custom Health Checks

```python
from mehdashti_observability import (
    measure_health_check,
    create_readiness_response,
    HealthCheck,
    CheckStatus,
)

@app.get("/ready")
async def custom_readiness():
    # Automatic timing and error handling
    db_check = await measure_health_check("database", check_database)
    redis_check = await measure_health_check("redis", check_redis)

    # Manual checks
    api_check = HealthCheck(
        name="external-api",
        status=CheckStatus.OK if api_available else CheckStatus.FAIL,
        latency_ms=api_latency,
        message="API reachable" if api_available else "API timeout"
    )

    return create_readiness_response(
        [db_check, redis_check, api_check],
        version="1.0.0"
    )
```

## Integration with Frontend

The frontend (@smart/data-client) automatically adds correlation IDs:

```typescript
import { apiFetch } from "@smart/data-client";

// Automatically includes X-Correlation-Id header
const user = await apiFetch<User>("/api/users/123");
```

## License

MIT
