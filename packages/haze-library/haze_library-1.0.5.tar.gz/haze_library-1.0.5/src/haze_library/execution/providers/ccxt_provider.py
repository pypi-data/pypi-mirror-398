from __future__ import annotations

import json
from typing import Any, Mapping

from ..errors import ExecutionProviderError
from ..models import (
    AmendOrderRequest,
    Balance,
    CancelOrderRequest,
    CreateOrderRequest,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)
from .base import ExecutionProvider


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _order_status_from_ccxt(status: Any) -> OrderStatus:
    if not isinstance(status, str):
        return OrderStatus.UNKNOWN
    s = status.lower()
    if s in ("open", "new"):
        return OrderStatus.OPEN
    if s in ("closed", "filled"):
        return OrderStatus.CLOSED
    if s in ("canceled", "cancelled"):
        return OrderStatus.CANCELED
    if s in ("rejected",):
        return OrderStatus.REJECTED
    return OrderStatus.UNKNOWN


def _order_side_from_ccxt(side: Any) -> OrderSide | None:
    if not isinstance(side, str):
        return None
    s = side.lower()
    if s == "buy":
        return OrderSide.BUY
    if s == "sell":
        return OrderSide.SELL
    return None


def _order_type_from_ccxt(order_type: Any) -> OrderType | None:
    if not isinstance(order_type, str):
        return None
    t = order_type.lower()
    if t == "market":
        return OrderType.MARKET
    if t == "limit":
        return OrderType.LIMIT
    return None


def _parse_ccxt_order(data: Mapping[str, Any]) -> Order:
    info = data.get("info")
    client_order_id = data.get("clientOrderId") or data.get("client_order_id")
    ts = _safe_float(data.get("timestamp"))
    return Order(
        id=str(data.get("id") or ""),
        symbol=data.get("symbol"),
        side=_order_side_from_ccxt(data.get("side")),
        order_type=_order_type_from_ccxt(data.get("type")),
        status=_order_status_from_ccxt(data.get("status")),
        amount=_safe_float(data.get("amount")),
        filled=_safe_float(data.get("filled")),
        remaining=_safe_float(data.get("remaining")),
        price=_safe_float(data.get("price")),
        average=_safe_float(data.get("average")),
        client_order_id=str(client_order_id) if client_order_id is not None else None,
        timestamp_ms=None if ts is None else int(ts),
        raw=dict(info) if isinstance(info, dict) else {"info": info} if info is not None else None,
    )


class CCXTExecutionProvider(ExecutionProvider):
    def __init__(
        self,
        *,
        exchange_id: str,
        api_key: str,
        api_secret: str,
        password: str | None = None,
        sandbox: bool = False,
        enable_rate_limit: bool = True,
        options: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> None:
        try:
            import ccxt  # type: ignore[import-untyped]
        except Exception as e:  # pragma: no cover
            raise ExecutionProviderError(
                "ccxt is required for CCXTExecutionProvider (pip install ccxt)",
                provider="ccxt",
            ) from e

        exchange_id = exchange_id.strip()
        if exchange_id == "":
            raise ExecutionProviderError("exchange_id must be non-empty", provider="ccxt")

        if api_key.strip() == "" or api_secret.strip() == "":
            raise ExecutionProviderError(
                "api_key/api_secret must be set for live trading",
                provider="ccxt",
            )

        if exchange_id == "bitget" and (password is None or password.strip() == ""):
            raise ExecutionProviderError(
                "bitget requires API passphrase (HAZE_EXCHANGE_PASSWORD)",
                provider="ccxt:bitget",
            )

        exchange_class = getattr(ccxt, exchange_id, None)
        if exchange_class is None:
            raise ExecutionProviderError(f"Unknown ccxt exchange: {exchange_id}", provider="ccxt")

        config: dict[str, Any] = {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": bool(enable_rate_limit),
        }
        if password:
            config["password"] = password
        if options:
            config["options"] = dict(options)
        if params:
            config.update(dict(params))

        self._exchange_id = exchange_id
        self._sandbox = bool(sandbox)
        self._exchange = exchange_class(config)
        if sandbox:
            try:
                self._exchange.set_sandbox_mode(True)
            except Exception:
                # Not all exchanges implement sandbox mode.
                pass

    @property
    def name(self) -> str:
        return f"ccxt:{self._exchange_id}"

    def _bitget_default_product_type(self) -> str | None:
        if self._exchange_id != "bitget":
            return None

        default_sub_type = None
        try:
            default_sub_type = self._exchange.options.get("defaultSubType")
        except Exception:
            default_sub_type = None

        base = "USDT-FUTURES"
        if isinstance(default_sub_type, str):
            sub_type = default_sub_type.lower()
            if sub_type == "inverse":
                base = "COIN-FUTURES"
            elif "usdc" in sub_type:
                base = "USDC-FUTURES"
            elif "-" in default_sub_type:
                base = default_sub_type.upper()

        if not self._sandbox:
            return base

        if base.startswith("USDT-"):
            return "SUSDT-FUTURES"
        if base.startswith("USDC-"):
            return "SUSDC-FUTURES"
        if base.startswith("COIN-"):
            return "SCOIN-FUTURES"
        return base

    @property
    def supports_amend(self) -> bool:
        has = getattr(self._exchange, "has", None)
        try:
            return bool(has and has.get("editOrder"))
        except Exception:
            return False

    def create_order(self, req: CreateOrderRequest) -> Order:
        try:
            params = dict(req.params)
            if req.client_order_id:
                params.setdefault("clientOrderId", req.client_order_id)
            raw = self._exchange.create_order(
                req.symbol,
                req.order_type.value,
                req.side.value,
                req.amount,
                req.price,
                params,
            )
            if not isinstance(raw, dict):
                raise ExecutionProviderError("Unexpected order response", provider=self.name)
            return _parse_ccxt_order(raw)
        except ExecutionProviderError:
            raise
        except Exception as e:
            raise ExecutionProviderError(str(e), provider=self.name) from e

    def cancel_order(self, req: CancelOrderRequest) -> Order:
        try:
            raw = self._exchange.cancel_order(req.order_id, req.symbol, dict(req.params))
            if not isinstance(raw, dict):
                raise ExecutionProviderError("Unexpected cancel response", provider=self.name)
            return _parse_ccxt_order(raw)
        except ExecutionProviderError:
            raise
        except Exception as e:
            raise ExecutionProviderError(str(e), provider=self.name) from e

    def amend_order(self, req: AmendOrderRequest) -> Order:
        if not self.supports_amend:
            raise ExecutionProviderError("editOrder not supported", provider=self.name)
        try:
            existing = self.fetch_order(req.order_id, symbol=req.symbol)
            if existing.symbol is None or existing.side is None or existing.order_type is None:
                raise ExecutionProviderError(
                    "existing order missing required fields for amend",
                    provider=self.name,
                )

            amount = existing.amount if req.amount is None else float(req.amount)
            if amount is None:
                raise ExecutionProviderError(
                    "existing order missing amount for amend",
                    provider=self.name,
                )
            price = existing.price if req.price is None else float(req.price)

            raw = self._exchange.edit_order(
                req.order_id,
                existing.symbol,
                existing.order_type.value,
                existing.side.value,
                float(amount),
                price,
                dict(req.params),
            )
            if not isinstance(raw, dict):
                raise ExecutionProviderError("Unexpected edit response", provider=self.name)
            return _parse_ccxt_order(raw)
        except ExecutionProviderError:
            raise
        except Exception as e:
            raise ExecutionProviderError(str(e), provider=self.name) from e

    def fetch_order(self, order_id: str, *, symbol: str | None = None) -> Order:
        try:
            raw = self._exchange.fetch_order(order_id, symbol)
            if not isinstance(raw, dict):
                raise ExecutionProviderError("Unexpected fetch_order response", provider=self.name)
            return _parse_ccxt_order(raw)
        except ExecutionProviderError:
            raise
        except Exception as e:
            raise ExecutionProviderError(str(e), provider=self.name) from e

    def get_open_orders(self, *, symbol: str | None = None) -> list[Order]:
        try:
            params: dict[str, Any] = {}
            if self._exchange_id == "bitget" and symbol is None and self._sandbox:
                product_type = self._bitget_default_product_type()
                if product_type:
                    params["productType"] = product_type

            raw = self._exchange.fetch_open_orders(symbol, None, None, params)
            if not isinstance(raw, list):
                raise ExecutionProviderError("Unexpected open orders response", provider=self.name)
            orders: list[Order] = []
            for item in raw:
                if isinstance(item, dict):
                    orders.append(_parse_ccxt_order(item))
            return orders
        except ExecutionProviderError:
            raise
        except Exception as e:
            raise ExecutionProviderError(str(e), provider=self.name) from e

    def get_balances(self) -> list[Balance]:
        try:
            raw = self._exchange.fetch_balance()
            if not isinstance(raw, dict):
                raise ExecutionProviderError("Unexpected balance response", provider=self.name)
            free: dict[str, Any] = raw.get("free") if isinstance(raw.get("free"), dict) else {}
            used: dict[str, Any] = raw.get("used") if isinstance(raw.get("used"), dict) else {}
            total: dict[str, Any] = raw.get("total") if isinstance(raw.get("total"), dict) else {}

            assets: set[str] = set()
            assets.update(free.keys())
            assets.update(used.keys())
            assets.update(total.keys())

            balances: list[Balance] = []
            for asset in sorted(a for a in assets if isinstance(a, str) and a):
                balances.append(
                    Balance(
                        asset=asset,
                        free=_safe_float(free.get(asset)),
                        used=_safe_float(used.get(asset)),
                        total=_safe_float(total.get(asset)),
                    )
                )
            return balances
        except ExecutionProviderError:
            raise
        except Exception as e:
            raise ExecutionProviderError(str(e), provider=self.name) from e

    def get_positions(self, *, symbol: str | None = None) -> list[Position]:
        has = getattr(self._exchange, "has", None)
        if not (has and has.get("fetchPositions")):
            return []

        try:
            symbols = [symbol] if symbol else None
            params: dict[str, Any] = {}
            if self._exchange_id == "bitget" and symbols is None and self._sandbox:
                product_type = self._bitget_default_product_type()
                if product_type:
                    params["productType"] = product_type

            raw = self._exchange.fetch_positions(symbols, params)
            if not isinstance(raw, list):
                raise ExecutionProviderError("Unexpected positions response", provider=self.name)
            positions: list[Position] = []
            for item in raw:
                if not isinstance(item, dict):
                    continue
                sym = item.get("symbol")
                if not isinstance(sym, str) or sym == "":
                    continue
                positions.append(
                    Position(
                        symbol=sym,
                        size=_safe_float(item.get("contracts") or item.get("size") or item.get("amount")),
                        side=item.get("side") if isinstance(item.get("side"), str) else None,
                        entry_price=_safe_float(item.get("entryPrice") or item.get("entry_price")),
                        unrealized_pnl=_safe_float(item.get("unrealizedPnl") or item.get("unrealized_pnl")),
                        raw=dict(item),
                    )
                )
            return positions
        except ExecutionProviderError:
            raise
        except Exception as e:
            raise ExecutionProviderError(str(e), provider=self.name) from e

    def get_reference_price(self, symbol: str) -> float | None:
        try:
            ticker = self._exchange.fetch_ticker(symbol)
            if not isinstance(ticker, dict):
                return None
            price = ticker.get("last")
            if price is None:
                price = ticker.get("close")
            return _safe_float(price)
        except Exception:
            return None

    @classmethod
    def options_from_env_json(cls, value: str | None) -> dict[str, Any]:
        if value is None:
            return {}
        raw = value.strip()
        if raw == "":
            return {}
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON in HAZE_CCXT_OPTIONS") from e
        if not isinstance(decoded, dict):
            raise ValueError("HAZE_CCXT_OPTIONS must be a JSON object")
        return decoded
