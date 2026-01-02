from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class TimeInForce(str, Enum):
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class OrderStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CreateOrderRequest:
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    price: float | None = None
    time_in_force: TimeInForce | None = None
    client_order_id: str | None = None
    params: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CancelOrderRequest:
    order_id: str
    symbol: str | None = None
    params: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AmendOrderRequest:
    order_id: str
    symbol: str | None = None
    amount: float | None = None
    price: float | None = None
    params: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Order:
    id: str
    symbol: str | None = None
    side: OrderSide | None = None
    order_type: OrderType | None = None
    status: OrderStatus = OrderStatus.UNKNOWN
    amount: float | None = None
    filled: float | None = None
    remaining: float | None = None
    price: float | None = None
    average: float | None = None
    client_order_id: str | None = None
    timestamp_ms: int | None = None
    raw: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": None if self.side is None else self.side.value,
            "type": None if self.order_type is None else self.order_type.value,
            "status": self.status.value,
            "amount": self.amount,
            "filled": self.filled,
            "remaining": self.remaining,
            "price": self.price,
            "average": self.average,
            "client_order_id": self.client_order_id,
            "timestamp_ms": self.timestamp_ms,
            "raw": dict(self.raw) if self.raw is not None else None,
        }


@dataclass(frozen=True)
class Balance:
    asset: str
    free: float | None = None
    used: float | None = None
    total: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset": self.asset,
            "free": self.free,
            "used": self.used,
            "total": self.total,
        }


@dataclass(frozen=True)
class Position:
    symbol: str
    size: float | None = None
    side: str | None = None
    entry_price: float | None = None
    unrealized_pnl: float | None = None
    raw: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "size": self.size,
            "side": self.side,
            "entry_price": self.entry_price,
            "unrealized_pnl": self.unrealized_pnl,
            "raw": dict(self.raw) if self.raw is not None else None,
        }

