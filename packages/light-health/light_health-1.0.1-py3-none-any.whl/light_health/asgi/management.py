import os
import logging
import msgspec

from light_health.asgi.management_models import (
    LoggerUpdate,
    EnvUpdate,
    SimpleMessage,
)


class ManagementASGIApp:
    def __init__(self):
        self.json_encoder = msgspec.json.Encoder()
        self.logger_decoder = msgspec.json.Decoder(LoggerUpdate)
        self.env_decoder = msgspec.json.Decoder(EnvUpdate)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return

        method = scope["method"]
        path = self._internal_path(scope)

        if path == "/loggers" and method == "GET":
            await self._list_loggers(send)
            return

        if path == "/loggers/update" and method == "POST":
            await self._update_logger(receive, send)
            return

        if path == "/env" and method == "GET":
            await self._list_env(send)
            return

        if path == "/env/update" and method == "POST":
            await self._update_env(receive, send)
            return

        await self._send(send, 404, {"error": "Not Found"})

    # ---------- handlers ----------

    async def _list_loggers(self, send):
        loggers = {
            name: logging.getLevelName(logger.level)
            for name, logger in logging.Logger.manager.loggerDict.items()
            if isinstance(logger, logging.Logger)
        }
        loggers["root"] = logging.getLevelName(logging.getLogger().level)
        await self._send(send, 200, loggers)

    async def _update_logger(self, receive, send):
        body = await self._read_body(receive)
        data: LoggerUpdate = self.logger_decoder.decode(body)

        logger = (
            logging.getLogger()
            if data.logger_name == "root"
            else logging.getLogger(data.logger_name)
        )

        level = data.level.upper()
        if level not in logging._nameToLevel:
            await self._send(send, 400, {"error": f"Invalid level: {level}"})
            return

        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)

        await self._send(
            send,
            200,
            SimpleMessage(message="Logger level updated"),
        )

    async def _list_env(self, send):
        await self._send(send, 200, dict(os.environ))

    async def _update_env(self, receive, send):
        body = await self._read_body(receive)
        data: EnvUpdate = self.env_decoder.decode(body)

        os.environ[data.key] = data.value

        await self._send(
            send,
            200,
            SimpleMessage(message=f"Environment variable '{data.key}' updated"),
        )

    # ---------- infra ----------

    async def _read_body(self, receive) -> bytes:
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break
        return body

    def _internal_path(self, scope) -> str:
        path = scope["path"]
        root = scope.get("root_path", "")
        return path[len(root) :] if path.startswith(root) else path

    async def _send(self, send, status: int, body):
        raw = (
            self.json_encoder.encode(body)
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
