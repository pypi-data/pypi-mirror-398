"""Trading execution REST API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from haze_library.api.models.requests import CancelOrderRequest, CreateOrderRequest
from haze_library.api.models.responses import ErrorResponse, OrderResponse

router = APIRouter(tags=["execution"])

# Global execution engine instance (set via dependency injection)
_execution_engine = None


def get_execution_engine() -> Any:
    """Dependency to get the execution engine."""
    global _execution_engine
    if _execution_engine is None:
        # Try to create from environment variables
        try:
            from haze_library.execution.llm_tools import get_default_engine

            _execution_engine = get_default_engine()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Execution engine not available: {e}",
            )
    return _execution_engine


def set_execution_engine(engine: Any) -> None:
    """Set the global execution engine (for programmatic configuration)."""
    global _execution_engine
    _execution_engine = engine


@router.post(
    "/order",
    response_model=OrderResponse,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    summary="Create a new order",
    description="Place a new trading order on the configured exchange",
)
async def create_order(
    request: CreateOrderRequest,
    engine: Any = Depends(get_execution_engine),
) -> OrderResponse:
    """Create a new trading order.

    Requires execution engine to be configured via environment variables:
    - HAZE_EXCHANGE_ID: Exchange ID (e.g., 'binance', 'bybit')
    - HAZE_EXCHANGE_API_KEY: API key
    - HAZE_EXCHANGE_SECRET: API secret
    - HAZE_LIVE_TRADING: Set to '1' for live trading
    """
    from haze_library.execution.models import (
        CreateOrderRequest as ExecutionRequest,
        OrderSide,
        OrderType,
    )

    try:
        # Map request to execution model
        side = OrderSide.BUY if request.side == "buy" else OrderSide.SELL
        order_type_map = {
            "market": OrderType.MARKET,
            "limit": OrderType.LIMIT,
            "stop_loss": OrderType.STOP_LOSS,
            "take_profit": OrderType.TAKE_PROFIT,
        }
        order_type = order_type_map.get(request.order_type, OrderType.LIMIT)

        exec_request = ExecutionRequest(
            symbol=request.symbol,
            side=side,
            type=order_type,
            amount=request.amount,
            price=request.price,
            client_order_id=request.client_order_id,
        )

        # Place the order
        order = engine.place_order(exec_request, dry_run=request.dry_run)

        return OrderResponse(
            success=True,
            order_id=order.order_id,
            client_order_id=order.client_order_id,
            symbol=order.symbol,
            side=order.side.value,
            type=order.type.value,
            amount=order.amount,
            price=order.price,
            status=order.status.value,
            filled=order.filled,
            remaining=order.remaining,
            cost=order.cost,
            timestamp=order.timestamp,
            raw=order.raw,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/order",
    response_model=OrderResponse,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    summary="Cancel an order",
    description="Cancel an existing order",
)
async def cancel_order(
    request: CancelOrderRequest,
    engine: Any = Depends(get_execution_engine),
) -> OrderResponse:
    """Cancel an existing order."""
    from haze_library.execution.models import CancelOrderRequest as ExecutionCancel

    try:
        exec_request = ExecutionCancel(
            order_id=request.order_id,
            symbol=request.symbol,
        )

        order = engine.cancel_order(exec_request)

        return OrderResponse(
            success=True,
            order_id=order.order_id,
            client_order_id=order.client_order_id,
            symbol=order.symbol,
            side=order.side.value,
            type=order.type.value,
            amount=order.amount,
            price=order.price,
            status=order.status.value,
            filled=order.filled,
            remaining=order.remaining,
            cost=order.cost,
            timestamp=order.timestamp,
            raw=order.raw,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/balances",
    summary="Get account balances",
    description="Retrieve current account balances",
)
async def get_balances(
    engine: Any = Depends(get_execution_engine),
) -> dict[str, Any]:
    """Get account balances."""
    try:
        balances = engine.provider.get_balances()
        return {
            "success": True,
            "balances": [b.to_dict() for b in balances],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/positions",
    summary="Get open positions",
    description="Retrieve current open positions",
)
async def get_positions(
    engine: Any = Depends(get_execution_engine),
) -> dict[str, Any]:
    """Get open positions."""
    try:
        positions = engine.provider.get_positions()
        return {
            "success": True,
            "positions": [p.to_dict() for p in positions],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/orders/open",
    summary="Get open orders",
    description="Retrieve current open orders",
)
async def get_open_orders(
    symbol: str | None = None,
    engine: Any = Depends(get_execution_engine),
) -> dict[str, Any]:
    """Get open orders, optionally filtered by symbol."""
    try:
        orders = engine.provider.get_open_orders(symbol)
        return {
            "success": True,
            "orders": [o.to_dict() for o in orders],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/capabilities",
    summary="Get execution capabilities",
    description="Get supported capabilities of the execution engine",
)
async def get_capabilities(
    engine: Any = Depends(get_execution_engine),
) -> dict[str, Any]:
    """Get execution engine capabilities."""
    caps = engine.capabilities()
    return {
        "success": True,
        "capabilities": caps,
        "permissions": {
            "live_trading": engine.permissions.live_trading,
            "allowed_symbols": list(engine.permissions.allowed_symbols)
            if engine.permissions.allowed_symbols
            else None,
            "max_notional_per_order": engine.permissions.max_notional_per_order,
        },
    }
