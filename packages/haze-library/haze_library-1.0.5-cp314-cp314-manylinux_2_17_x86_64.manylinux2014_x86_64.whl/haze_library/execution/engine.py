from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import ExecutionPermissionError, ExecutionProviderError
from .models import AmendOrderRequest, CancelOrderRequest, CreateOrderRequest, Order
from .permissions import ExecutionPermissions, Scope
from .providers.base import ExecutionProvider
from .risk import NotionalCheck, validate_create_order_request


@dataclass
class ExecutionEngine:
    provider: ExecutionProvider
    permissions: ExecutionPermissions

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": self.provider.name,
            "supports_amend": bool(self.provider.supports_amend),
            "live_trading": bool(self.permissions.live_trading),
            "scopes": sorted(s.value for s in self.permissions.scopes),
            "allowed_symbols": None
            if self.permissions.allowed_symbols is None
            else sorted(self.permissions.allowed_symbols),
            "max_notional_per_order": self.permissions.max_notional_per_order,
        }

    def _require_live(self, *, dry_run: bool) -> None:
        if dry_run:
            return
        if not self.permissions.live_trading:
            raise ExecutionPermissionError(
                "Live trading is disabled (set permissions.live_trading=True)"
            )

    def place_order(
        self,
        req: CreateOrderRequest,
        *,
        dry_run: bool = False,
        reason: str | None = None,  # Reserved for audit logging
    ) -> tuple[Order, NotionalCheck | None]:
        _ = reason  # Placeholder for future audit logging
        self.permissions.require(Scope.TRADE)
        self._require_live(dry_run=dry_run)

        reference_price = None
        if self.permissions.max_notional_per_order is not None and req.price is None:
            reference_price = self.provider.get_reference_price(req.symbol)

        notional_check = validate_create_order_request(
            req,
            self.permissions,
            reference_price=reference_price,
        )

        if dry_run:
            dry = Order(
                id="DRY_RUN",
                symbol=req.symbol,
                side=req.side,
                order_type=req.order_type,
                amount=req.amount,
                price=req.price,
            )
            return dry, notional_check

        try:
            return self.provider.create_order(req), notional_check
        except ExecutionProviderError:
            raise
        except Exception as e:  # pragma: no cover
            raise ExecutionProviderError(str(e), provider=self.provider.name) from e

    def cancel_order(
        self,
        req: CancelOrderRequest,
        *,
        dry_run: bool = False,
        reason: str | None = None,  # Reserved for audit logging
    ) -> Order:
        _ = reason  # Placeholder for future audit logging
        self.permissions.require(Scope.CANCEL)
        self._require_live(dry_run=dry_run)

        if dry_run:
            return Order(id=req.order_id, symbol=req.symbol)

        try:
            return self.provider.cancel_order(req)
        except ExecutionProviderError:
            raise
        except Exception as e:  # pragma: no cover
            raise ExecutionProviderError(str(e), provider=self.provider.name) from e

    def amend_order(
        self,
        req: AmendOrderRequest,
        *,
        dry_run: bool = False,
        reason: str | None = None,  # Reserved for audit logging
    ) -> Order:
        _ = reason  # Placeholder for future audit logging
        self.permissions.require(Scope.AMEND)
        self._require_live(dry_run=dry_run)

        if self.provider.supports_amend:
            if dry_run:
                return Order(id=req.order_id, symbol=req.symbol)
            try:
                return self.provider.amend_order(req)
            except ExecutionProviderError:
                raise
            except Exception as e:  # pragma: no cover
                raise ExecutionProviderError(str(e), provider=self.provider.name) from e

        # Fallback: cancel + recreate (requires cancel + trade scopes)
        self.permissions.require(Scope.CANCEL)
        self.permissions.require(Scope.TRADE)

        existing = self.provider.fetch_order(req.order_id, symbol=req.symbol)
        if existing.symbol is None or existing.side is None or existing.order_type is None:
            raise ExecutionProviderError(
                "cannot amend: provider returned incomplete order details",
                provider=self.provider.name,
            )

        new_amount = existing.amount if req.amount is None else float(req.amount)
        new_price = existing.price if req.price is None else float(req.price)
        if new_amount is None:
            raise ExecutionProviderError(
                "cannot amend: missing amount on existing order",
                provider=self.provider.name,
            )
        create_req = CreateOrderRequest(
            symbol=existing.symbol,
            side=existing.side,
            order_type=existing.order_type,
            amount=float(new_amount),
            price=new_price,
            client_order_id=existing.client_order_id,
            params=req.params,
        )

        if dry_run:
            return Order(id="DRY_RUN_AMEND", symbol=existing.symbol)

        # 原子性保护：取消-重建的竞态条件处理
        # 如果 create_order 失败，原订单已被取消，需要记录详细信息以便恢复
        cancel_result = self.provider.cancel_order(
            CancelOrderRequest(order_id=req.order_id, symbol=req.symbol)
        )
        try:
            new_order = self.provider.create_order(create_req)
            return new_order
        except Exception as create_error:
            # 创建失败但原订单已取消 - 提供详细的错误信息以便手动恢复
            raise ExecutionProviderError(
                f"CRITICAL: Order {req.order_id} was cancelled (status={cancel_result.status}) "
                f"but replacement order failed: {create_error}. "
                f"Original order details: symbol={existing.symbol}, side={existing.side}, "
                f"amount={new_amount}, price={new_price}. Manual intervention required.",
                provider=self.provider.name,
            ) from create_error

    def get_positions(self, *, symbol: str | None = None) -> list[dict[str, Any]]:
        self.permissions.require(Scope.READ)
        if symbol is None and self.permissions.allowed_symbols:
            collected = []
            for sym in sorted(self.permissions.allowed_symbols):
                collected.extend(self.provider.get_positions(symbol=sym))
            positions = collected
        else:
            positions = self.provider.get_positions(symbol=symbol)
        return [p.to_dict() for p in positions]

    def get_balances(self) -> list[dict[str, Any]]:
        self.permissions.require(Scope.READ)
        balances = self.provider.get_balances()
        return [b.to_dict() for b in balances]

    def get_open_orders(self, *, symbol: str | None = None) -> list[dict[str, Any]]:
        self.permissions.require(Scope.READ)
        if symbol is None and self.permissions.allowed_symbols:
            collected = []
            for sym in sorted(self.permissions.allowed_symbols):
                collected.extend(self.provider.get_open_orders(symbol=sym))
            orders = collected
        else:
            orders = self.provider.get_open_orders(symbol=symbol)
        return [o.to_dict() for o in orders]
