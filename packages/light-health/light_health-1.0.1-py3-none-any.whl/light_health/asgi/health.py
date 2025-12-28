import msgspec
from light_health.registry import AsyncHealthRegistry
from light_health.status import HealthState


class HealthASGIApp:
    def __init__(self, registry: AsyncHealthRegistry):
        self.registry = registry
        self.encoder = msgspec.json.Encoder()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return

        if scope["method"] != "GET":
            await self._send(send, 405, {"error": "Method Not Allowed"})
            return

        path = scope["path"]
        root_path = scope.get("root_path", "")

        if path == f"{root_path}/liveness":
            await self._send(send, 200, await self.registry.liveness())
            return

        if path == f"{root_path}/readiness":
            payload = await self.registry.readiness()
            status = 200 if payload.status == HealthState.UP else 503
            await self._send(send, status, payload)
            return

        if path == f"{root_path}/health":
            payload = await self.registry.readiness()
            status = 200 if payload.status == HealthState.UP else 503
            await self._send(send, status, payload)
            return
        
        if path == f"{root_path}/up":
            payload = await self.registry.readiness()
            status = 200 if payload.status == HealthState.UP else 503
            await self._send(send, status, payload)
            return
        
        if path == root_path:
            payload = await self.registry.readiness()
            status = 200 if payload.status == HealthState.UP else 503
            await self._send(send, status, payload)
            return     

        await self._send(send, 404, {"error": "Not Found"})

    async def _send(self, send, status: int, body):
        raw = (
            self.encoder.encode(body)
            if not isinstance(body, dict)
            else msgspec.json.encode(body)
        )

        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": raw,
            }
        )
