"""Smart Platform Observability - Correlation IDs, health checks, and request tracing."""

# Correlation ID utilities
from smart_observability.correlation import (
    CORRELATION_ID_HEADER,
    CorrelationMiddleware,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
)

# Health check utilities
from smart_observability.health import (
    CheckStatus,
    HealthCheck,
    HealthStatus,
    LivenessResponse,
    ReadinessResponse,
    calculate_overall_status,
    create_health_check,
    create_liveness_endpoint,
    create_liveness_response,
    create_readiness_endpoint,
    create_readiness_response,
    measure_health_check,
)

__all__ = [
    # Correlation IDs
    "CORRELATION_ID_HEADER",
    "CorrelationMiddleware",
    "generate_correlation_id",
    "get_correlation_id",
    "set_correlation_id",
    # Health Checks
    "CheckStatus",
    "HealthCheck",
    "HealthStatus",
    "LivenessResponse",
    "ReadinessResponse",
    "calculate_overall_status",
    "create_health_check",
    "create_liveness_endpoint",
    "create_liveness_response",
    "create_readiness_endpoint",
    "create_readiness_response",
    "measure_health_check",
]
