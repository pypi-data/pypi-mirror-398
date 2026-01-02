from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from .errors import ExecutionPermissionError


class Scope(str, Enum):
    READ = "read"
    TRADE = "trade"
    CANCEL = "cancel"
    AMEND = "amend"


@dataclass(frozen=True)
class ExecutionPermissions:
    """
    Permission + guardrails for an ExecutionEngine.

    This is intended to be enforced in-process (e.g. by an LLM agent runtime).
    It does not replace exchange-level API key permissions.
    """

    scopes: set[Scope] = field(default_factory=set)
    live_trading: bool = False
    allowed_symbols: set[str] | None = None
    max_notional_per_order: float | None = None

    def require(self, scope: Scope) -> None:
        if scope not in self.scopes:
            raise ExecutionPermissionError(f"Missing required scope: {scope.value}")

    def is_symbol_allowed(self, symbol: str) -> bool:
        if self.allowed_symbols is None:
            return True
        return symbol in self.allowed_symbols

    @classmethod
    def from_scopes(
        cls,
        scopes: Iterable[Scope | str],
        *,
        live_trading: bool = False,
        allowed_symbols: set[str] | None = None,
        max_notional_per_order: float | None = None,
    ) -> "ExecutionPermissions":
        normalized: set[Scope] = set()
        for scope in scopes:
            if isinstance(scope, Scope):
                normalized.add(scope)
            else:
                normalized.add(Scope(scope))
        return cls(
            scopes=normalized,
            live_trading=live_trading,
            allowed_symbols=allowed_symbols,
            max_notional_per_order=max_notional_per_order,
        )
