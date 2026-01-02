"""Pydantic request models for the API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class CalculateIndicatorsRequest(BaseModel):
    """Request model for batch indicator calculation.

    Example:
        {
            "indicators": ["sma", "rsi", "macd"],
            "data": {
                "close": [100, 101, 102, ...],
                "high": [...],
                "low": [...]
            },
            "params": {
                "sma": {"period": 20},
                "rsi": {"period": 14},
                "macd": {"fast": 12, "slow": 26, "signal": 9}
            }
        }
    """

    indicators: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of indicator names to calculate",
        examples=[["sma", "rsi", "macd"]],
    )
    data: dict[str, list[float]] = Field(
        ...,
        description="OHLCV data arrays (close, high, low, open, volume)",
        examples=[{"close": [100.0, 101.0, 102.0], "high": [102.0, 103.0, 104.0]}],
    )
    params: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Parameters for each indicator",
        examples=[{"sma": {"period": 20}, "rsi": {"period": 14}}],
    )

    @field_validator("indicators")
    @classmethod
    def validate_indicators(cls, v: list[str]) -> list[str]:
        """Validate indicator names."""
        from haze_library import numpy_compat as np_ta

        available = set(np_ta.__all__)
        invalid = [ind for ind in v if ind not in available]
        if invalid:
            raise ValueError(f"Unknown indicators: {invalid}")
        return v

    @field_validator("data")
    @classmethod
    def validate_data(cls, v: dict[str, list[float]]) -> dict[str, list[float]]:
        """Validate data arrays have consistent lengths."""
        if not v:
            raise ValueError("Data cannot be empty")

        lengths = {k: len(arr) for k, arr in v.items()}
        unique_lengths = set(lengths.values())

        if len(unique_lengths) > 1:
            raise ValueError(f"Data arrays have inconsistent lengths: {lengths}")

        return v


class CreateOrderRequest(BaseModel):
    """Request model for creating a new order."""

    symbol: str = Field(
        ...,
        min_length=1,
        description="Trading pair symbol",
        examples=["BTC/USDT", "ETH/USDT"],
    )
    side: str = Field(
        ...,
        pattern="^(buy|sell)$",
        description="Order side: 'buy' or 'sell'",
    )
    order_type: str = Field(
        default="limit",
        alias="type",
        pattern="^(market|limit|stop_loss|take_profit)$",
        description="Order type",
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Order amount in base currency",
    )
    price: float | None = Field(
        default=None,
        gt=0,
        description="Limit price (required for limit orders)",
    )
    client_order_id: str | None = Field(
        default=None,
        max_length=64,
        description="Client-provided order ID",
    )
    dry_run: bool = Field(
        default=False,
        description="If true, validate order without executing",
    )


class CancelOrderRequest(BaseModel):
    """Request model for canceling an order."""

    order_id: str = Field(
        ...,
        min_length=1,
        description="Exchange order ID to cancel",
    )
    symbol: str = Field(
        ...,
        min_length=1,
        description="Trading pair symbol",
    )


class StreamingSubscribeRequest(BaseModel):
    """Request model for WebSocket streaming subscription."""

    symbols: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Symbols to subscribe to",
        examples=[["BTC/USDT", "ETH/USDT"]],
    )
    indicators: list[str] = Field(
        default=["rsi", "supertrend"],
        min_length=1,
        max_length=10,
        description="Indicators to calculate in real-time",
    )
    timeframe: str = Field(
        default="1m",
        pattern="^(1m|5m|15m|1h|4h|1d)$",
        description="Candle timeframe",
    )
