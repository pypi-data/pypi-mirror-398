from light_health.status import HealthCheckResult, HealthState


def mongo_health_check(mongo_client):
    async def check():
        try:
            await mongo_client.admin.command("ping")
            return HealthCheckResult(status=HealthState.UP)
        except Exception as e:
            return HealthCheckResult(
                status=HealthState.DOWN,
                details={"error": str(e)},
            )

    return check
