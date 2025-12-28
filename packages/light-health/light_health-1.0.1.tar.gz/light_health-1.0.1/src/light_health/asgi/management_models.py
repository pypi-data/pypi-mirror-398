import msgspec


class LoggerUpdate(msgspec.Struct):
    level: str
    logger_name: str = "root"


class EnvUpdate(msgspec.Struct):
    key: str
    value: str


class SimpleMessage(msgspec.Struct):
    message: str
