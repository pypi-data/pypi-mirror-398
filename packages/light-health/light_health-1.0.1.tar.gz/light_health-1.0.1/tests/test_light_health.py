import asyncio
import os
import pytest
import aiohttp
from fastapi import FastAPI

from light_health.registry import AsyncHealthRegistry
from light_health.asgi.health import HealthASGIApp
from light_health.asgi.management import ManagementASGIApp


@pytest.mark.asyncio
async def test_health_and_management_endpoints():
    # ---------- setup app ----------
    registry = AsyncHealthRegistry()
    health_app = HealthASGIApp(registry)
    management_app = ManagementASGIApp()

    app = FastAPI()
    app.mount("/health", health_app)
    app.mount("/management", management_app)

    # ---------- start server ----------
    import uvicorn

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=18080,
        log_level="critical",
    )
    server = uvicorn.Server(config)

    server_task = asyncio.create_task(server.serve())

    # aguarda o servidor subir
    await asyncio.sleep(0.5)

    try:
        async with aiohttp.ClientSession() as session:

            # -------- health ----------
            async with session.get("http://127.0.0.1:18080/health/liveness") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert "status" in data

            async with session.get("http://127.0.0.1:18080/health/readiness") as resp:
                assert resp.status in (200, 503)
                data = await resp.json()
                assert "status" in data

            # -------- management / loggers ----------
            async with session.get("http://127.0.0.1:18080/management/loggers") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert "root" in data

            payload = {"level": "DEBUG", "logger_name": "root"}
            async with session.post(
                "http://127.0.0.1:18080/management/loggers/update",
                json=payload,
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data["message"] == "Logger level updated"

            # -------- management / env ----------
            async with session.get("http://127.0.0.1:18080/management/env") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert isinstance(data, dict)

            payload = {"key": "TEST_VAR", "value": "123"}
            async with session.post(
                "http://127.0.0.1:18080/management/env/update",
                json=payload,
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert "TEST_VAR" in os.environ
                assert os.environ["TEST_VAR"] == "123"

    finally:
        # ---------- shutdown ----------
        server.should_exit = True
        await server_task
