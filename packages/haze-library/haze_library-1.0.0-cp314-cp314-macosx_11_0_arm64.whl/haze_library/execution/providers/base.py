from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import (
    AmendOrderRequest,
    Balance,
    CancelOrderRequest,
    CreateOrderRequest,
    Order,
    Position,
)


class ExecutionProvider(ABC):
    """
    Abstract trading provider used by ExecutionEngine.

    Providers should avoid storing secrets in returned objects.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def supports_amend(self) -> bool:
        return False

    @abstractmethod
    def create_order(self, req: CreateOrderRequest) -> Order: ...

    @abstractmethod
    def cancel_order(self, req: CancelOrderRequest) -> Order: ...

    def amend_order(self, req: AmendOrderRequest) -> Order:
        raise NotImplementedError

    @abstractmethod
    def fetch_order(self, order_id: str, *, symbol: str | None = None) -> Order: ...

    @abstractmethod
    def get_open_orders(self, *, symbol: str | None = None) -> list[Order]: ...

    @abstractmethod
    def get_balances(self) -> list[Balance]: ...

    @abstractmethod
    def get_positions(self, *, symbol: str | None = None) -> list[Position]: ...

    def get_reference_price(self, symbol: str) -> float | None:
        return None
