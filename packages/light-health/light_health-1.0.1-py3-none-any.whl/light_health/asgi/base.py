from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Literal, Optional

import msgspec


class HealthStatus(msgspec.Struct, frozen=True):
    status: Literal["UP", "DOWN"]
    details: Optional[Dict[str, Any]] = None

    @classmethod
    def up(cls, details: Optional[Dict[str, Any]] = None) -> "HealthStatus":
        return cls(status="UP", details=details)

    @classmethod
    def down(cls, details: Optional[Dict[str, Any]] = None) -> "HealthStatus":
        return cls(status="DOWN", details=details)


class HealthCheck(ABC):
    """
    Base class for all health checks.
    """

    name: str

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name or self.__class__.__name__

    @abstractmethod
    async def check(self) -> HealthStatus:
        raise NotImplementedError
