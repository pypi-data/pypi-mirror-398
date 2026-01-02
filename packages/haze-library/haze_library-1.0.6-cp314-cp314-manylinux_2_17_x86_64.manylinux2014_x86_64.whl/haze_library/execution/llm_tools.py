from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from .engine import ExecutionEngine
from .errors import ExecutionPermissionError
from .models import AmendOrderRequest, CancelOrderRequest, CreateOrderRequest, OrderSide, OrderType
from .permissions import ExecutionPermissions, Scope
from .providers.ccxt_provider import CCXTExecutionProvider


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on", "live"}


def _parse_csv_set(value: str | None) -> set[str] | None:
    if value is None:
        return None
    items = {part.strip() for part in value.split(",") if part.strip()}
    return items or None


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    raw = value.strip()
    if raw == "":
        return None
    return float(raw)


def _get_env(name: str, *aliases: str) -> str | None:
    if name in os.environ:
        return os.environ.get(name)
    for alias in aliases:
        if alias in os.environ:
            return os.environ.get(alias)
    return None


@lru_cache(maxsize=1)
def get_default_engine() -> ExecutionEngine:
    """
    Build a singleton ExecutionEngine from environment variables.

    Required for live trading:
    - HAZE_EXCHANGE_ID (e.g. binance, okx, bybit)
    - HAZE_EXCHANGE_API_KEY
    - HAZE_EXCHANGE_SECRET
    - HAZE_LIVE_TRADING=1
    - HAZE_EXECUTION_SCOPES includes trade/cancel/amend as needed
    """

    exchange_id = (_get_env("HAZE_EXCHANGE_ID") or "binance").strip()
    api_key = (_get_env("HAZE_EXCHANGE_API_KEY", "EXCHANGE_API_KEY") or "").strip()
    secret = (_get_env("HAZE_EXCHANGE_SECRET", "HAZE_EXCHANGE_API_SECRET", "EXCHANGE_API_SECRET") or "").strip()
    password = _get_env("HAZE_EXCHANGE_PASSWORD", "EXCHANGE_API_PASSWORD")
    sandbox = _parse_bool(_get_env("HAZE_EXCHANGE_SANDBOX", "EXCHANGE_SANDBOX"))

    scopes_raw = _get_env("HAZE_EXECUTION_SCOPES") or "read"
    scopes = [Scope(part.strip()) for part in scopes_raw.split(",") if part.strip()]

    permissions = ExecutionPermissions.from_scopes(
        scopes,
        live_trading=_parse_bool(_get_env("HAZE_LIVE_TRADING")),
        allowed_symbols=_parse_csv_set(_get_env("HAZE_ALLOWED_SYMBOLS")),
        max_notional_per_order=_parse_float(_get_env("HAZE_MAX_NOTIONAL_PER_ORDER")),
    )

    options = CCXTExecutionProvider.options_from_env_json(_get_env("HAZE_CCXT_OPTIONS"))
    provider = CCXTExecutionProvider(
        exchange_id=exchange_id,
        api_key=api_key,
        api_secret=secret,
        password=password,
        sandbox=sandbox,
        options=options,
    )

    return ExecutionEngine(provider=provider, permissions=permissions)


def reset_default_engine() -> None:
    get_default_engine.cache_clear()


def get_capabilities() -> dict[str, Any]:
    return get_default_engine().capabilities()


def place_order(
    symbol: str,
    side: str,
    order_type: str,
    amount: float,
    *,
    price: float | None = None,
    dry_run: bool = False,
    reason: str | None = None,
    client_order_id: str | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    engine = get_default_engine()

    req = CreateOrderRequest(
        symbol=symbol,
        side=OrderSide(side.lower()),
        order_type=OrderType(order_type.lower()),
        amount=float(amount),
        price=None if price is None else float(price),
        client_order_id=client_order_id,
        params=params or {},
    )
    order, notional = engine.place_order(req, dry_run=dry_run, reason=reason)
    out = {"order": order.to_dict(), "notional_check": None}
    if notional is not None:
        out["notional_check"] = {"notional": notional.notional, "limit": notional.limit}
    return out


def cancel_order(
    order_id: str,
    *,
    symbol: str | None = None,
    dry_run: bool = False,
    reason: str | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    engine = get_default_engine()
    order = engine.cancel_order(
        CancelOrderRequest(order_id=order_id, symbol=symbol, params=params or {}),
        dry_run=dry_run,
        reason=reason,
    )
    return {"order": order.to_dict()}


def amend_order(
    order_id: str,
    *,
    symbol: str | None = None,
    amount: float | None = None,
    price: float | None = None,
    dry_run: bool = False,
    reason: str | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    engine = get_default_engine()
    order = engine.amend_order(
        AmendOrderRequest(
            order_id=order_id,
            symbol=symbol,
            amount=None if amount is None else float(amount),
            price=None if price is None else float(price),
            params=params or {},
        ),
        dry_run=dry_run,
        reason=reason,
    )
    return {"order": order.to_dict()}


def get_positions(*, symbol: str | None = None) -> dict[str, Any]:
    engine = get_default_engine()
    return {"positions": engine.get_positions(symbol=symbol)}


def get_balances() -> dict[str, Any]:
    engine = get_default_engine()
    return {"balances": engine.get_balances()}


def get_open_orders(*, symbol: str | None = None) -> dict[str, Any]:
    engine = get_default_engine()
    return {"open_orders": engine.get_open_orders(symbol=symbol)}


def assert_live_ready() -> None:
    """
    Helper for LLM agents: verify that live trading is enabled and scoped.
    """

    caps = get_capabilities()
    if not caps.get("live_trading", False):
        raise ExecutionPermissionError(
            "Live trading disabled. Set HAZE_LIVE_TRADING=1 and include trade scopes."
        )

