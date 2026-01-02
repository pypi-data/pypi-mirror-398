from __future__ import annotations

from dataclasses import dataclass

from .errors import ExecutionRiskError
from .models import CreateOrderRequest, OrderType
from .permissions import ExecutionPermissions


@dataclass(frozen=True)
class NotionalCheck:
    notional: float
    limit: float


def validate_create_order_request(
    req: CreateOrderRequest,
    permissions: ExecutionPermissions,
    *,
    reference_price: float | None = None,
) -> NotionalCheck | None:
    if req.amount <= 0.0:
        raise ExecutionRiskError("amount must be > 0")

    if req.order_type == OrderType.LIMIT and (req.price is None or req.price <= 0.0):
        raise ExecutionRiskError("limit order requires price > 0")

    if req.symbol.strip() == "":
        raise ExecutionRiskError("symbol must be non-empty")

    if not permissions.is_symbol_allowed(req.symbol):
        raise ExecutionRiskError(f"symbol not allowed: {req.symbol}")

    if permissions.max_notional_per_order is None:
        return None

    limit = float(permissions.max_notional_per_order)
    if limit <= 0.0:
        raise ExecutionRiskError("max_notional_per_order must be > 0 when set")

    if req.order_type == OrderType.LIMIT:
        assert req.price is not None  # validated above
        notional = float(req.amount) * float(req.price)
        if notional > limit:
            raise ExecutionRiskError(f"order notional {notional} exceeds limit {limit}")
        return NotionalCheck(notional=notional, limit=limit)

    if reference_price is None or reference_price <= 0.0:
        raise ExecutionRiskError(
            "market order notional check requires reference_price > 0"
        )
    notional = float(req.amount) * float(reference_price)
    if notional > limit:
        raise ExecutionRiskError(f"order notional {notional} exceeds limit {limit}")
    return NotionalCheck(notional=notional, limit=limit)
