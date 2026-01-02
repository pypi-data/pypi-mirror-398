from __future__ import annotations

import time
from dataclasses import replace
from typing import Any, Mapping

from ..errors import ExecutionProviderError
from ..models import (
    AmendOrderRequest,
    Balance,
    CancelOrderRequest,
    CreateOrderRequest,
    Order,
    OrderStatus,
    Position,
)
from .base import ExecutionProvider


class InMemoryExecutionProvider(ExecutionProvider):
    """
    Simple in-memory provider for tests / dry simulations.

    This is not a market simulator. It just stores orders and supports
    cancel/amend flows without external dependencies.
    """

    def __init__(self, *, reference_prices: Mapping[str, float] | None = None) -> None:
        self._orders: dict[str, Order] = {}
        self._next_id = 1
        self._reference_prices = dict(reference_prices or {})

    @property
    def name(self) -> str:
        return "memory"

    @property
    def supports_amend(self) -> bool:
        return True

    def _new_id(self) -> str:
        oid = f"mem_{self._next_id}"
        self._next_id += 1
        return oid

    def create_order(self, req: CreateOrderRequest) -> Order:
        if req.amount <= 0.0:
            raise ExecutionProviderError("amount must be > 0", provider=self.name)

        now = int(time.time() * 1000)
        order = Order(
            id=self._new_id(),
            symbol=req.symbol,
            side=req.side,
            order_type=req.order_type,
            status=OrderStatus.OPEN,
            amount=req.amount,
            filled=0.0,
            remaining=req.amount,
            price=req.price,
            average=None,
            client_order_id=req.client_order_id,
            timestamp_ms=now,
            raw={"provider": "memory"},
        )
        self._orders[order.id] = order
        return order

    def cancel_order(self, req: CancelOrderRequest) -> Order:
        order = self._orders.get(req.order_id)
        if order is None:
            raise ExecutionProviderError("order not found", provider=self.name)
        updated = replace(order, status=OrderStatus.CANCELED)
        self._orders[req.order_id] = updated
        return updated

    def amend_order(self, req: AmendOrderRequest) -> Order:
        order = self._orders.get(req.order_id)
        if order is None:
            raise ExecutionProviderError("order not found", provider=self.name)

        updates: dict[str, Any] = {}
        if req.amount is not None:
            if req.amount <= 0.0:
                raise ExecutionProviderError("amount must be > 0", provider=self.name)
            updates["amount"] = req.amount
            updates["remaining"] = req.amount if order.filled in (None, 0.0) else None
        if req.price is not None:
            if req.price <= 0.0:
                raise ExecutionProviderError("price must be > 0", provider=self.name)
            updates["price"] = req.price

        updated = replace(order, **updates)
        self._orders[req.order_id] = updated
        return updated

    def fetch_order(self, order_id: str, *, symbol: str | None = None) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise ExecutionProviderError("order not found", provider=self.name)
        if symbol is not None and order.symbol not in (None, symbol):
            raise ExecutionProviderError("symbol mismatch", provider=self.name)
        return order

    def get_open_orders(self, *, symbol: str | None = None) -> list[Order]:
        orders = [o for o in self._orders.values() if o.status == OrderStatus.OPEN]
        if symbol is not None:
            orders = [o for o in orders if o.symbol == symbol]
        return orders

    def get_balances(self) -> list[Balance]:
        return []

    def get_positions(self, *, symbol: str | None = None) -> list[Position]:
        return []

    def get_reference_price(self, symbol: str) -> float | None:
        return self._reference_prices.get(symbol)

