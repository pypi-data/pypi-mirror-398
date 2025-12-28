from light_health.status import HealthCheckResult, HealthState


def redis_health_check(redis_client):
    async def check():
        try:
            if await redis_client.ping():
                return HealthCheckResult(status=HealthState.UP)
            return HealthCheckResult(
                status=HealthState.DOWN,
                details={"error": "PING failed"},
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthState.DOWN,
                details={"error": str(e)},
            )

    return check
