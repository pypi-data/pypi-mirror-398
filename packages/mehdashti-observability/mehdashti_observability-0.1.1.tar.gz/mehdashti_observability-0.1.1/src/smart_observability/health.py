"""
Health Check Utilities

Standardized health and readiness check endpoints for FastAPI services.
Compatible with @smart/contracts health schemas.
"""

import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class HealthStatus(str, Enum):
    """Overall health status"""

    OK = "ok"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class CheckStatus(str, Enum):
    """Individual check status"""

    OK = "ok"
    FAIL = "fail"


# =============================================================================
# Models
# =============================================================================


class HealthCheck(BaseModel):
    """Individual dependency check result"""

    name: str = Field(..., description="Name of the dependency")
    status: CheckStatus = Field(..., description="Status of the check")
    latency_ms: float | None = Field(None, description="Response time in milliseconds")
    message: str | None = Field(None, description="Additional details")


class LivenessResponse(BaseModel):
    """
    Health endpoint response (/health)

    Simple liveness check - is the service process running?
    """

    status: HealthStatus = Field(..., description="Overall service status")
    version: str | None = Field(None, description="Service version")
    timestamp: str = Field(..., description="Timestamp of the check")


class ReadinessResponse(BaseModel):
    """
    Readiness endpoint response (/ready)

    Full readiness check - are all dependencies healthy?
    """

    status: HealthStatus = Field(..., description="Overall status")
    checks: list[HealthCheck] = Field(..., description="Individual dependency checks")
    version: str | None = Field(None, description="Service version")
    timestamp: str = Field(..., description="Timestamp of the check")


# =============================================================================
# Helper Functions
# =============================================================================


def calculate_overall_status(checks: list[HealthCheck]) -> HealthStatus:
    """
    Calculate overall health status from checks

    Args:
        checks: List of health check results

    Returns:
        Overall health status (ok, degraded, or unhealthy)
    """
    if not checks:
        return HealthStatus.OK

    has_failure = any(check.status == CheckStatus.FAIL for check in checks)
    all_ok = all(check.status == CheckStatus.OK for check in checks)

    if all_ok:
        return HealthStatus.OK
    if has_failure:
        return HealthStatus.UNHEALTHY
    return HealthStatus.DEGRADED


def create_liveness_response(
    status: HealthStatus = HealthStatus.OK, version: str | None = None
) -> LivenessResponse:
    """
    Create a liveness response

    Args:
        status: Overall health status
        version: Optional service version

    Returns:
        Liveness response

    Example:
        ```python
        response = create_liveness_response(HealthStatus.OK, "1.0.0")
        # => LivenessResponse(status="ok", version="1.0.0", timestamp="...")
        ```
    """
    return LivenessResponse(
        status=status,
        version=version,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def create_readiness_response(
    checks: list[HealthCheck], version: str | None = None
) -> ReadinessResponse:
    """
    Create a readiness response

    Args:
        checks: List of health check results
        version: Optional service version

    Returns:
        Readiness response

    Example:
        ```python
        checks = [
            HealthCheck(name="database", status=CheckStatus.OK, latency_ms=12.5),
            HealthCheck(name="redis", status=CheckStatus.OK, latency_ms=5.2),
        ]
        response = create_readiness_response(checks, "1.0.0")
        # => ReadinessResponse(status="ok", checks=[...], ...)
        ```
    """
    return ReadinessResponse(
        status=calculate_overall_status(checks),
        checks=checks,
        version=version,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def create_health_check(
    name: str,
    status: CheckStatus,
    latency_ms: float | None = None,
    message: str | None = None,
) -> HealthCheck:
    """
    Create a health check result

    Args:
        name: Name of the dependency
        status: Check status (ok or fail)
        latency_ms: Optional response time in milliseconds
        message: Optional additional details

    Returns:
        Health check result

    Example:
        ```python
        check = create_health_check("database", CheckStatus.OK, latency_ms=15.3)
        # => HealthCheck(name="database", status="ok", latency_ms=15.3)
        ```
    """
    return HealthCheck(
        name=name,
        status=status,
        latency_ms=latency_ms,
        message=message,
    )


async def measure_health_check(
    name: str, check_fn: Callable[[], Awaitable[None]]
) -> HealthCheck:
    """
    Measure and create a health check with timing

    Args:
        name: Name of the dependency
        check_fn: Async function that performs the health check

    Returns:
        Health check result with latency

    Example:
        ```python
        async def check_database():
            await db.execute("SELECT 1")

        check = await measure_health_check("database", check_database)
        # => HealthCheck(name="database", status="ok", latency_ms=12.5)
        ```
    """
    start = time.perf_counter()
    try:
        await check_fn()
        latency_ms = (time.perf_counter() - start) * 1000
        return create_health_check(name, CheckStatus.OK, latency_ms)
    except Exception as error:
        latency_ms = (time.perf_counter() - start) * 1000
        message = str(error)
        return create_health_check(name, CheckStatus.FAIL, latency_ms, message)


# =============================================================================
# FastAPI Route Helpers
# =============================================================================


def create_liveness_endpoint(version: str | None = None):
    """
    Create a FastAPI liveness endpoint function

    Args:
        version: Optional service version

    Returns:
        Async endpoint function

    Example:
        ```python
        from fastapi import FastAPI
        from smart_observability.health import create_liveness_endpoint

        app = FastAPI()
        app.get("/health")(create_liveness_endpoint("1.0.0"))
        ```
    """

    async def liveness() -> LivenessResponse:
        """Liveness probe - is the service running?"""
        return create_liveness_response(HealthStatus.OK, version)

    return liveness


def create_readiness_endpoint(
    checks: list[Callable[[], Awaitable[None]]] | None = None, version: str | None = None
):
    """
    Create a FastAPI readiness endpoint function

    Args:
        checks: List of async check functions
        version: Optional service version

    Returns:
        Async endpoint function

    Example:
        ```python
        from fastapi import FastAPI
        from smart_observability.health import create_readiness_endpoint

        async def check_db():
            await db.execute("SELECT 1")

        async def check_redis():
            await redis.ping()

        app = FastAPI()
        app.get("/ready")(
            create_readiness_endpoint([check_db, check_redis], "1.0.0")
        )
        ```
    """

    async def readiness() -> ReadinessResponse:
        """Readiness probe - are all dependencies healthy?"""
        if not checks:
            return create_readiness_response([], version)

        # Run all health checks
        check_results = []
        for i, check_fn in enumerate(checks):
            check_name = getattr(check_fn, "__name__", f"check_{i}")
            result = await measure_health_check(check_name, check_fn)
            check_results.append(result)

        return create_readiness_response(check_results, version)

    return readiness
