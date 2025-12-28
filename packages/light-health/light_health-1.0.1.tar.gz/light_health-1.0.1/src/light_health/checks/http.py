import time
import aiohttp
from light_health.status import HealthCheckResult, HealthState


def http_health_check(url: str, timeout: float = 0.5):
    async def check():
        start = time.monotonic()
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(url) as resp:
                    latency = int((time.monotonic() - start) * 1000)
                    if resp.status == 200:
                        return HealthCheckResult(
                            status=HealthState.UP,
                            details={"latency_ms": latency},
                        )
                    return HealthCheckResult(
                        status=HealthState.DOWN,
                        details={"status": resp.status},
                    )
        except TimeoutError as e:
            return HealthCheckResult(
                status=HealthState.DOWN,
                details={"error": "TimeoutError"},
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthState.DOWN,
                details={"error": str(e)},
            )

    return check
