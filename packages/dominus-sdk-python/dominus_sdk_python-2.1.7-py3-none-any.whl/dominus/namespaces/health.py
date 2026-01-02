"""
Health Namespace - Service health check operations.

Provides health check endpoints for the orchestrator service.
"""
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class HealthNamespace:
    """
    Health check namespace.

    Usage:
        status = await dominus.health.check()
        await dominus.health.ping()
        await dominus.health.warmup()
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of orchestrator and dependencies.

        Returns:
            Dict with "status", "latency_ms", and service-specific info
        """
        from ..helpers.core import health_check
        from ..config.endpoints import get_base_url

        return await health_check(get_base_url())

    async def ping(self) -> Dict[str, Any]:
        """
        Simple ping check (fastest response).

        Returns:
            Dict with "status": "ok"
        """
        return await self._client._request(
            endpoint="/api/health/ping",
            method="GET"
        )

    async def warmup(self) -> Dict[str, Any]:
        """
        Warmup request (triggers cold start if needed).

        Returns:
            Dict with warmup status
        """
        return await self._client._request(
            endpoint="/api/health/warmup",
            method="GET"
        )
