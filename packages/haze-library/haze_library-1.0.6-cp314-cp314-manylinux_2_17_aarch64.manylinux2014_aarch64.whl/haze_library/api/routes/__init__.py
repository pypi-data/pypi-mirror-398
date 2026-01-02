"""API route modules."""

from __future__ import annotations

from .indicators import router as indicators_router
from .execution import router as execution_router
from .streaming import router as streaming_router

__all__ = ["indicators_router", "execution_router", "streaming_router"]
