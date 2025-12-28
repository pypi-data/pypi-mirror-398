import msgspec
from enum import Enum
from typing import Dict, Any, Optional


class HealthState(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


class HealthCheckResult(msgspec.Struct, frozen=True):
    status: HealthState
    details: Optional[Dict[str, Any]] = None


class HealthResponse(msgspec.Struct, frozen=True):
    status: HealthState
    checks: Dict[str, HealthCheckResult]
