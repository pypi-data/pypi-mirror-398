from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AcceleratorType(str, Enum):
    NONE = ""
    GPU = "GPU"
    TPU = "TPU"

    @classmethod
    def from_string(cls, value: str) -> "AcceleratorType":
        if not value or value.upper() == "NONE":
            return cls.NONE
        try:
            return cls(value)
        except ValueError:
            return cls.NONE


class RuntimeVariant(str, Enum):
    DEFAULT = "DEFAULT"
    STANDARD_GPU = "STANDARD_GPU"
    PREMIUM_GPU = "PREMIUM_GPU"
    TPU = "TPU"
    CASCADE_LAKE = "CASCADE_LAKE"
    SKYLAKE = "SKYLAKE"

    @classmethod
    def from_string(cls, value: str) -> "RuntimeVariant":
        if not value:
            return cls.DEFAULT
        try:
            return cls(value)
        except ValueError:
            return cls.DEFAULT


class KernelState(str, Enum):
    STARTING = "starting"
    IDLE = "idle"
    BUSY = "busy"
    DEAD = "dead"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProxyInfo:
    url: str
    token: str


@dataclass
class Assignment:
    endpoint: str
    accelerator: AcceleratorType = AcceleratorType.NONE
    variant: RuntimeVariant = RuntimeVariant.DEFAULT
    proxy_info: ProxyInfo | None = None

    @property
    def proxy_url(self) -> str:
        return self.proxy_info.url if self.proxy_info else ""

    @property
    def proxy_token(self) -> str:
        return self.proxy_info.token if self.proxy_info else ""


@dataclass
class Session:
    id: str
    kernel_id: str
    path: str
    state: KernelState = KernelState.UNKNOWN


@dataclass
class ExecutionResult:
    stdout: str = ""
    stderr: str = ""
    result: dict[str, Any] | None = None
    error: ExecutionError | None = None
    display_data: list[dict[str, Any]] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.error is None


@dataclass
class ExecutionError:
    name: str
    value: str
    traceback: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"
