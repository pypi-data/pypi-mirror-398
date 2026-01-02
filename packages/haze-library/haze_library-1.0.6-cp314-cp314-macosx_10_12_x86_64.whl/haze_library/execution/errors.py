from __future__ import annotations

from dataclasses import dataclass

from ..exceptions import HazeError


class ExecutionError(HazeError):
    """Base exception for execution/trading errors."""


@dataclass(frozen=True)
class ExecutionPermissionError(ExecutionError):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class ExecutionRiskError(ExecutionError):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class ExecutionProviderError(ExecutionError):
    message: str
    provider: str | None = None

    def __str__(self) -> str:
        if self.provider:
            return f"{self.provider}: {self.message}"
        return self.message

