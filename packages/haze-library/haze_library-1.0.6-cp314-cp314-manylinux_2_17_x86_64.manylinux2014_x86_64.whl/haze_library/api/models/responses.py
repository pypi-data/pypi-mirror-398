"""Pydantic response models for the API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IndicatorResult(BaseModel):
    """Single indicator calculation result."""

    name: str = Field(..., description="Indicator name")
    values: list[float | None] | dict[str, list[float | None]] = Field(
        ...,
        description="Calculated values (single array or named arrays for multi-output). NaN values are represented as null.",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters used for calculation",
    )


class CalculateIndicatorsResponse(BaseModel):
    """Response for batch indicator calculation."""

    success: bool = Field(default=True)
    results: dict[str, list[float | None] | dict[str, list[float | None]]] = Field(
        ...,
        description="Indicator results keyed by name. NaN values are represented as null.",
    )
    errors: dict[str, str] = Field(
        default_factory=dict,
        description="Errors for failed indicators",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (timing, data length, etc.)",
    )


class OrderResponse(BaseModel):
    """Response for order operations."""

    success: bool = Field(default=True)
    order_id: str | None = Field(default=None, description="Exchange order ID")
    client_order_id: str | None = Field(default=None)
    symbol: str = Field(..., description="Trading pair symbol")
    side: str = Field(..., description="Order side")
    order_type: str = Field(..., alias="type", description="Order type")
    amount: float = Field(..., description="Order amount")
    price: float | None = Field(default=None, description="Order price")
    status: str = Field(..., description="Order status")
    filled: float = Field(default=0.0, description="Filled amount")
    remaining: float = Field(default=0.0, description="Remaining amount")
    cost: float = Field(default=0.0, description="Total cost")
    timestamp: datetime | None = Field(default=None, description="Order timestamp")
    raw: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw exchange response",
    )

    model_config = {"populate_by_name": True}


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    error_code: str = Field(default="UNKNOWN_ERROR", description="Error code")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error details",
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service status")
    version: str = Field(..., description="Library version")
    indicators_available: int = Field(..., description="Number of available indicators")
    streaming_indicators: int = Field(..., description="Number of streaming indicators")
    execution_enabled: bool = Field(
        default=False,
        description="Whether execution engine is available",
    )
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


class StreamingMessage(BaseModel):
    """WebSocket streaming message."""

    event: str = Field(..., description="Event type: 'update', 'error', 'subscribed'")
    symbol: str | None = Field(default=None, description="Symbol for this update")
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Event data (indicator values, error info, etc.)",
    )
