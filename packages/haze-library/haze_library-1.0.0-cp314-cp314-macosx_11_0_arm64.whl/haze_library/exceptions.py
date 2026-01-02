from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


class HazeError(Exception):
    """Base exception for haze-library errors."""


@dataclass
class InvalidPeriodError(HazeError):
    """Raised when an indicator period is invalid for the given data length."""

    period: int
    data_length: int
    indicator: str
    min_period: int = 1

    def __str__(self) -> str:
        return (
            f"{self.indicator}: invalid period {self.period} for data length "
            f"{self.data_length} (min {self.min_period})"
        )


@dataclass
class InsufficientDataError(HazeError):
    """Raised when there is not enough data to compute an indicator."""

    required: int
    provided: int
    indicator: str

    def __str__(self) -> str:
        return (
            f"{self.indicator}: insufficient data (required {self.required}, "
            f"provided {self.provided})"
        )


@dataclass
class ColumnNotFoundError(HazeError):
    """Raised when a required column is not present in a DataFrame-like object."""

    column: str
    available_columns: Sequence[str]
    indicator: str | None = None

    def __str__(self) -> str:
        prefix = f"{self.indicator}: " if self.indicator else ""
        available = ", ".join(self.available_columns)
        return f"{prefix}column '{self.column}' not found (available: {available})"


@dataclass
class InvalidParameterError(HazeError):
    """Raised when an invalid parameter value is supplied."""

    name: str
    value: object
    indicator: str | None = None

    def __str__(self) -> str:
        prefix = f"{self.indicator}: " if self.indicator else ""
        return f"{prefix}invalid parameter '{self.name}'={self.value!r}"


@dataclass
class ComputationError(HazeError):
    """Raised when a computation fails unexpectedly."""

    indicator: str
    message: str

    def __str__(self) -> str:
        return f"{self.indicator}: computation failed ({self.message})"


def validate_period(
    period: int,
    data_length: int,
    indicator: str,
    *,
    min_period: int = 1,
) -> None:
    if period < min_period or period > data_length:
        raise InvalidPeriodError(
            period=period,
            data_length=data_length,
            indicator=indicator,
            min_period=min_period,
        )


def validate_data_length(provided: int, required: int, indicator: str) -> None:
    if provided < required:
        raise InsufficientDataError(required=required, provided=provided, indicator=indicator)


def require_columns(
    columns: Iterable[str],
    required: Sequence[str],
    *,
    indicator: str | None = None,
) -> None:
    available = set(columns)
    for name in required:
        if name not in available:
            raise ColumnNotFoundError(name, sorted(available), indicator=indicator)
