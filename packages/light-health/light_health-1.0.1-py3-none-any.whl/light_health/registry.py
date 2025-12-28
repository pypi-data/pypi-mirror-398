import asyncio
from typing import Dict, Callable, Awaitable

from light_health.status import (
    HealthState,
    HealthCheckResult,
    HealthResponse,
)


class AsyncHealthRegistry:
    def __init__(self):
        self._liveness: Dict[str, Callable[[], Awaitable[HealthCheckResult]]] = {}
        self._readiness: Dict[str, Callable[[], Awaitable[HealthCheckResult]]] = {}

    def register_liveness(self, name: str, check):
        self._liveness[name] = check

    def register_readiness(self, name: str, check):
        self._readiness[name] = check

    async def liveness(self) -> HealthResponse:
        return await self._run(self._liveness)

    async def readiness(self) -> HealthResponse:
        return await self._run(self._readiness)

    async def _run(self, checks) -> HealthResponse:
        names = list(checks.keys())
        coros = [self._safe(check) for check in checks.values()]

        results_list = await asyncio.gather(*coros)

        results = dict(zip(names, results_list))

        overall = (
            HealthState.UP
            if all(r.status is HealthState.UP for r in results.values())
            else HealthState.DOWN
        )

        return HealthResponse(status=overall, checks=results)

    async def _safe(self, check):
        try:
            return await asyncio.wait_for(check(), timeout=2.0)
        except Exception as exc:
            return HealthCheckResult.down(details={"error": str(exc)})
