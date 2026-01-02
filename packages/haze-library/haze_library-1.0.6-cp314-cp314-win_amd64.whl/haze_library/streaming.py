"""Streaming/incremental indicator calculators.

This module provides O(1) online calculators for real-time indicator computation.
All algorithms are implemented in Rust for performance; this module provides
thin Python wrappers that maintain API compatibility.

Note: The "Incremental*" class names are kept for backwards compatibility.
The underlying implementation uses Rust "Online*" calculators.
"""
from __future__ import annotations

import math
import threading
from typing import Any, Iterable, Mapping

# Import Rust streaming calculators directly from the extension module
# These are registered in streaming_py.rs via PyO3
# Use relative import to avoid circular dependency with __init__.py
from .haze_library import (
    OnlineSMA,
    OnlineEMA,
    OnlineRSI,
    OnlineATR,
    OnlineMACD,
    OnlineBollingerBands,
    OnlineStochastic,
    OnlineSuperTrend,
    OnlineAdaptiveRSI,
    OnlineEnsembleSignal,
    OnlineMLSuperTrend,
    OnlineAISuperTrendML,
)

_NAN = float("nan")


def _is_nan(value: float) -> bool:
    """Check if value is NaN."""
    return math.isnan(value)


_ENSEMBLE_COMPONENTS = ("rsi", "macd", "stochastic", "supertrend")


def _normalize_weights(weights: Mapping[str, float], keys: Iterable[str]) -> dict[str, float]:
    filtered = {k: float(weights.get(k, 0.0)) for k in keys}
    for name, weight in filtered.items():
        if not math.isfinite(weight):
            raise ValueError(f"weights contains non-finite value for {name}: {weight}")
    weight_sum = sum(filtered.values())
    if not math.isfinite(weight_sum) or weight_sum == 0.0:
        raise ValueError("weights sum cannot be zero")
    return {k: v / weight_sum for k, v in filtered.items()}


class IncrementalSMA:
    """Incremental Simple Moving Average calculator.

    Thin wrapper around Rust OnlineSMA for O(1) updates.
    """

    def __init__(self, period: int) -> None:
        if period <= 0:
            raise ValueError("period must be > 0")
        self.period = int(period)
        self._inner = OnlineSMA(period)
        self._lock = threading.Lock()
        self.count = 0
        self._current = _NAN

    def reset(self) -> None:
        with self._lock:
            self._inner.reset()
            self.count = 0
            self._current = _NAN

    @property
    def is_ready(self) -> bool:
        return self.count >= self.period

    @property
    def current(self) -> float:
        return self._current

    @property
    def value(self) -> float:
        return self._current

    def update(self, value: float) -> float:
        v = float(value)
        with self._lock:
            result = self._inner.update(v)
            self.count += 1
            self._current = result if result is not None else _NAN
            return self._current

    def update_batch(self, values: Iterable[float]) -> list[float]:
        return [self.update(v) for v in values]

    def status(self) -> dict[str, Any]:
        return {"count": self.count, "is_ready": self.is_ready, "current": self.current}


class IncrementalEMA:
    """Incremental Exponential Moving Average calculator.

    Thin wrapper around Rust OnlineEMA for O(1) updates.
    """

    def __init__(self, period: int) -> None:
        if period <= 0:
            raise ValueError("period must be > 0")
        self.period = int(period)
        self._inner = OnlineEMA(period)
        self._lock = threading.Lock()
        self.count = 0
        self._current = _NAN

    def reset(self) -> None:
        with self._lock:
            self._inner.reset()
            self.count = 0
            self._current = _NAN

    @property
    def is_ready(self) -> bool:
        return self._inner.is_ready()

    @property
    def current(self) -> float:
        return self._current

    def update(self, value: float) -> float:
        v = float(value)
        with self._lock:
            result = self._inner.update(v)
            self.count += 1
            self._current = result if result is not None else _NAN
            return self._current

    def status(self) -> dict[str, Any]:
        return {"count": self.count, "is_ready": self.is_ready, "current": self.current}


class IncrementalRSI:
    """Incremental Relative Strength Index calculator.

    Thin wrapper around Rust OnlineRSI for O(1) updates.
    """

    def __init__(self, period: int = 14) -> None:
        if period <= 0:
            raise ValueError("period must be > 0")
        self.period = int(period)
        self._inner = OnlineRSI(period)
        self._lock = threading.Lock()
        self.count = 0
        self._current = _NAN
        self._is_ready = False

    def reset(self) -> None:
        with self._lock:
            self._inner.reset()
            self.count = 0
            self._current = _NAN
            self._is_ready = False

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @property
    def current(self) -> float:
        return self._current

    def update(self, value: float) -> float:
        v = float(value)
        with self._lock:
            result = self._inner.update(v)
            self.count += 1
            if result is not None:
                self._current = result
                self._is_ready = True
            else:
                self._current = _NAN
                self._is_ready = False
            return self._current

    def status(self) -> dict[str, Any]:
        return {"count": self.count, "is_ready": self.is_ready, "current": self.current}


class IncrementalMACD:
    """Incremental MACD calculator.

    Thin wrapper around Rust OnlineMACD for O(1) updates.
    Returns (MACD line, Signal line, Histogram).
    """

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9) -> None:
        if fast <= 0 or slow <= 0 or signal <= 0:
            raise ValueError("fast/slow/signal must be > 0")
        if slow <= fast:
            raise ValueError("slow must be > fast")

        self.fast = int(fast)
        self.slow = int(slow)
        self.signal = int(signal)

        self._inner = OnlineMACD(fast, slow, signal)
        self._lock = threading.Lock()
        self.count = 0
        self._current = (_NAN, _NAN, _NAN)
        self._is_ready = False

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def reset(self) -> None:
        with self._lock:
            self._inner.reset()
            self.count = 0
            self._current = (_NAN, _NAN, _NAN)
            self._is_ready = False

    def update(self, value: float) -> tuple[float, float, float]:
        v = float(value)
        with self._lock:
            result = self._inner.update(v)
            self.count += 1
            if result is not None:
                self._current = result
                self._is_ready = True
            else:
                self._current = (_NAN, _NAN, _NAN)
                self._is_ready = False
            return self._current

    def status(self) -> dict[str, Any]:
        line, sig, hist = self._current
        return {
            "count": self.count,
            "is_ready": self.is_ready,
            "macd": line,
            "signal": sig,
            "histogram": hist,
        }


class IncrementalATR:
    """Incremental Average True Range calculator.

    Thin wrapper around Rust OnlineATR for O(1) updates.
    """

    def __init__(self, period: int = 14) -> None:
        if period <= 0:
            raise ValueError("period must be > 0")
        self.period = int(period)
        self._inner = OnlineATR(period)
        self._lock = threading.Lock()
        self.count = 0
        self._atr = _NAN

    def reset(self) -> None:
        with self._lock:
            self._inner.reset()
            self.count = 0
            self._atr = _NAN

    @property
    def is_ready(self) -> bool:
        return self._inner.is_ready()

    @property
    def current(self) -> float:
        return self._atr

    def update(self, high: float, low: float, close: float) -> float:
        h = float(high)
        lo = float(low)
        c = float(close)
        with self._lock:
            result = self._inner.update(h, lo, c)
            self.count += 1
            self._atr = result if result is not None else _NAN
            return self._atr

    def status(self) -> dict[str, Any]:
        return {"count": self.count, "is_ready": self.is_ready, "current": self.current}


class IncrementalSuperTrend:
    """Incremental SuperTrend calculator.

    Thin wrapper around Rust OnlineSuperTrend for O(1) updates.
    Returns (trend_value, direction) where direction is 1 (up) or -1 (down).
    """

    def __init__(self, period: int = 10, multiplier: float = 3.0) -> None:
        if period <= 0:
            raise ValueError("period must be > 0")
        self.period = int(period)
        self.multiplier = float(multiplier)
        self._inner = OnlineSuperTrend(period, multiplier)
        self._lock = threading.Lock()
        self.count = 0
        self._trend = _NAN
        self._direction = _NAN
        self.current_direction = _NAN

    def reset(self) -> None:
        with self._lock:
            self._inner.reset()
            self.count = 0
            self._trend = _NAN
            self._direction = _NAN
            self.current_direction = _NAN

    @property
    def is_ready(self) -> bool:
        return not _is_nan(self._trend)

    def update(self, high: float, low: float, close: float) -> tuple[float, float]:
        h = float(high)
        lo = float(low)
        c = float(close)
        with self._lock:
            result = self._inner.update(h, lo, c)
            self.count += 1
            if result is not None:
                value, direction = result
                self._trend = value
                self._direction = float(direction)
                self.current_direction = float(direction)
            else:
                self._trend = _NAN
                self._direction = _NAN
            return self._trend, self._direction

    def status(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "is_ready": self.is_ready,
            "trend": self._trend,
            "direction": self._direction,
        }


class IncrementalBollingerBands:
    """Incremental Bollinger Bands calculator.

    Thin wrapper around Rust OnlineBollingerBands for O(1) updates.
    Returns (upper_band, middle_band, lower_band).
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0) -> None:
        if period <= 0:
            raise ValueError("period must be > 0")
        self.period = int(period)
        self.std_dev = float(std_dev)
        self._inner = OnlineBollingerBands(period, std_dev)
        self._lock = threading.Lock()
        self.count = 0
        self._current = (_NAN, _NAN, _NAN)

    def reset(self) -> None:
        with self._lock:
            self._inner.reset()
            self.count = 0
            self._current = (_NAN, _NAN, _NAN)

    @property
    def is_ready(self) -> bool:
        return self.count >= self.period

    def update(self, value: float) -> tuple[float, float, float]:
        v = float(value)
        with self._lock:
            result = self._inner.update(v)
            self.count += 1
            if result is not None:
                self._current = result
            else:
                self._current = (_NAN, _NAN, _NAN)
            return self._current

    def status(self) -> dict[str, Any]:
        upper, middle, lower = self._current
        return {
            "count": self.count,
            "is_ready": self.is_ready,
            "upper": upper,
            "middle": middle,
            "lower": lower,
        }


class IncrementalStochastic:
    """Incremental Stochastic Oscillator calculator.

    Thin wrapper around Rust OnlineStochastic for O(1) updates.
    Returns (%K, %D).
    """

    def __init__(self, k_period: int = 14, smooth_k: int = 3, d_period: int = 3) -> None:
        if k_period <= 0 or smooth_k <= 0 or d_period <= 0:
            raise ValueError("k_period/smooth_k/d_period must be > 0")
        self.k_period = int(k_period)
        self.smooth_k = int(smooth_k)
        self.d_period = int(d_period)
        self._inner = OnlineStochastic(k_period, smooth_k, d_period)
        self._lock = threading.Lock()
        self.count = 0
        self._current = (_NAN, _NAN)

    def reset(self) -> None:
        with self._lock:
            self._inner.reset()
            self.count = 0
            self._current = (_NAN, _NAN)

    @property
    def is_ready(self) -> bool:
        return self.count >= (self.k_period + self.smooth_k + self.d_period - 2)

    def update(self, high: float, low: float, close: float) -> tuple[float, float]:
        h = float(high)
        lo = float(low)
        c = float(close)
        with self._lock:
            result = self._inner.update(h, lo, c)
            self.count += 1
            if result is not None:
                self._current = result
            else:
                self._current = (_NAN, _NAN)
            return self._current

    def status(self) -> dict[str, Any]:
        k, d = self._current
        return {"count": self.count, "is_ready": self.is_ready, "k": k, "d": d}


class IncrementalAdaptiveRSI:
    """Incremental Adaptive RSI calculator.

    Thin wrapper around Rust OnlineAdaptiveRSI for O(1) updates.
    RSI period adapts based on market volatility.
    Returns (rsi_value, effective_period).
    """

    def __init__(
        self,
        *,
        base_period: int = 14,
        min_period: int = 7,
        max_period: int = 28,
        volatility_window: int = 14,
    ) -> None:
        if min_period <= 0 or max_period <= 0:
            raise ValueError("periods must be > 0")
        if min_period > max_period:
            raise ValueError("min_period must be <= max_period")
        if base_period <= 0:
            raise ValueError("base_period must be > 0")
        if not (min_period <= base_period <= max_period):
            raise ValueError("base_period must be within [min_period, max_period]")
        if volatility_window <= 0:
            raise ValueError("volatility_window must be > 0")

        # Note: base_period is not used in Rust implementation
        self.base_period = int(base_period)
        self.min_period = int(min_period)
        self.max_period = int(max_period)
        self.volatility_window = int(volatility_window)
        self._default_period = self.base_period

        self._inner = OnlineAdaptiveRSI(min_period, max_period, volatility_window)
        self._lock = threading.Lock()
        self.count = 0
        self._is_ready = False

    def reset(self) -> None:
        with self._lock:
            self._inner.reset()
            self.count = 0
            self._is_ready = False

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def update(self, price: float) -> tuple[float, int]:
        p = float(price)
        with self._lock:
            result = self._inner.update(p)
            self.count += 1
            if result is not None:
                rsi, period = result
                self._is_ready = True
                return rsi, period

            self._is_ready = False
            return _NAN, self._default_period


class IncrementalEnsembleSignal:
    """Incremental Ensemble Signal calculator.

    Thin wrapper around Rust OnlineEnsembleSignal for O(1) updates.
    Combines RSI, MACD, Stochastic, and SuperTrend signals.
    Returns (combined_signal, component_breakdown).
    """

    def __init__(self, *, weights: Mapping[str, float] | None = None) -> None:
        self._lock = threading.Lock()
        # Use default parameters - Rust implementation has sensible defaults
        self._inner = OnlineEnsembleSignal.with_defaults()
        self.weights = {k: float(v) for k, v in (weights or {}).items()}
        for name, weight in self.weights.items():
            if not math.isfinite(weight):
                raise ValueError(f"weights contains non-finite value for {name}: {weight}")
        self._weight_map: dict[str, float] | None = None
        self._is_ready = False
        self.count = 0

    def reset(self) -> None:
        with self._lock:
            self._inner.reset()
            self.count = 0
            self._is_ready = False

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def update(self, high: float, low: float, close: float) -> tuple[float, dict[str, float]]:
        h = float(high)
        lo = float(low)
        c = float(close)
        with self._lock:
            result = self._inner.update(h, lo, c)
            self.count += 1
            if result is not None:
                self._is_ready = True
                # EnsembleSignalResult has: signal, rsi_contrib, macd_contrib, stoch_contrib, trend_contrib, confidence
                components = {
                    "rsi": result.rsi_contrib,
                    "macd": result.macd_contrib,
                    "stochastic": result.stoch_contrib,
                    "supertrend": result.trend_contrib,
                }

                weight_map = self._weight_map
                if weight_map is None and self.weights:
                    weight_map = _normalize_weights(self.weights, _ENSEMBLE_COMPONENTS)
                    self._weight_map = weight_map

                # Apply custom weights if provided
                if weight_map is not None:
                    signal = sum(float(weight_map.get(k, 0.0)) * float(v) for k, v in components.items())
                    signal = max(-1.0, min(1.0, signal))
                else:
                    signal = result.signal

                return signal, components

            # Not ready yet
            self._is_ready = False
            return 0.0, {"rsi": 0.0, "macd": 0.0, "stochastic": 0.0, "supertrend": 0.0}


class IncrementalMLSuperTrend:
    """Incremental ML-enhanced SuperTrend calculator.

    Thin wrapper around Rust OnlineMLSuperTrend for O(1) updates.
    Adds confirmation bars and volatility-based confidence.
    Returns (trend_value, confirmed_direction, confidence).
    """

    def __init__(
        self,
        *,
        period: int = 10,
        multiplier: float = 3.0,
        confirmation_bars: int = 2,
        use_atr_filter: bool = True,
    ) -> None:
        if period <= 0:
            raise ValueError("period must be > 0")
        if not math.isfinite(multiplier) or multiplier <= 0.0:
            raise ValueError("multiplier must be > 0")
        if confirmation_bars <= 0:
            raise ValueError("confirmation_bars must be > 0")

        self.period = int(period)
        self.multiplier = float(multiplier)
        self.confirmation_bars = int(confirmation_bars)
        self.use_atr_filter = bool(use_atr_filter)

        # Note: use_atr_filter not exposed in Rust - uses volatility_period instead
        self._inner = OnlineMLSuperTrend(period, multiplier, confirmation_bars, period)
        self._lock = threading.Lock()
        self.count = 0
        self.current_direction = _NAN
        self._is_ready = False

    def reset(self) -> None:
        with self._lock:
            self._inner.reset()
            self.count = 0
            self.current_direction = _NAN
            self._is_ready = False

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def update(self, high: float, low: float, close: float) -> tuple[float, float, float]:
        h = float(high)
        lo = float(low)
        c = float(close)
        with self._lock:
            result = self._inner.update(h, lo, c)
            self.count += 1
            if result is not None:
                # MLSuperTrendResult has: value, confirmed_trend, raw_trend, confidence, effective_multiplier
                confirmed = float(result.confirmed_trend)
                if confirmed == 0.0:
                    self.current_direction = _NAN
                    self._is_ready = False
                    return result.value, _NAN, result.confidence
                self.current_direction = confirmed
                self._is_ready = True
                return result.value, confirmed, result.confidence
            self.current_direction = _NAN
            self._is_ready = False
            return _NAN, _NAN, _NAN


class IncrementalAISuperTrend:
    """Incremental AI SuperTrend ML calculator.

    ML-enhanced SuperTrend indicator with sliding window linear regression
    for trend prediction. Provides buy/sell signals, stop-loss, and take-profit
    levels based on ATR and ML-predicted trend direction.

    Returns a dict with 7 fields:
    - supertrend: float - SuperTrend line value
    - direction: int - Trend direction (-1, 0, 1)
    - trend_offset: float - ML-predicted trend offset
    - buy_signal: bool - True if buy signal triggered
    - sell_signal: bool - True if sell signal triggered
    - stop_loss: float - Suggested stop-loss level
    - take_profit: float - Suggested take-profit level
    """

    def __init__(
        self,
        *,
        st_length: int = 10,
        st_multiplier: float = 3.0,
        lookback: int = 10,
        train_window: int = 200,
    ) -> None:
        if st_length <= 0:
            raise ValueError("st_length must be > 0")
        if not math.isfinite(st_multiplier) or st_multiplier <= 0.0:
            raise ValueError("st_multiplier must be > 0")
        if lookback <= 0:
            raise ValueError("lookback must be > 0")
        if train_window <= lookback:
            raise ValueError("train_window must be > lookback")

        self.st_length = int(st_length)
        self.st_multiplier = float(st_multiplier)
        self.lookback = int(lookback)
        self.train_window = int(train_window)

        self._inner = OnlineAISuperTrendML(st_length, st_multiplier, lookback, train_window)
        self._lock = threading.Lock()
        self.count = 0
        self.current_direction = 0
        self._is_ready = False

    def reset(self) -> None:
        with self._lock:
            self._inner.reset()
            self.count = 0
            self.current_direction = 0
            self._is_ready = False

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def update(self, high: float, low: float, close: float) -> dict[str, Any]:
        """Update with new OHLC bar and return signals.

        Parameters
        ----------
        high : float
            High price of the bar
        low : float
            Low price of the bar
        close : float
            Close price of the bar

        Returns
        -------
        dict
            Dictionary with keys: supertrend, direction, trend_offset,
            buy_signal, sell_signal, stop_loss, take_profit
        """
        h = float(high)
        lo = float(low)
        c = float(close)

        with self._lock:
            result = self._inner.update(h, lo, c)
            self.count += 1

            if result is not None:
                self.current_direction = result.direction
                self._is_ready = True
                return {
                    "supertrend": result.supertrend,
                    "direction": result.direction,
                    "trend_offset": result.trend_offset,
                    "buy_signal": result.buy_signal,
                    "sell_signal": result.sell_signal,
                    "stop_loss": result.stop_loss,
                    "take_profit": result.take_profit,
                }

            self._is_ready = False
            return {
                "supertrend": _NAN,
                "direction": 0,
                "trend_offset": _NAN,
                "buy_signal": False,
                "sell_signal": False,
                "stop_loss": _NAN,
                "take_profit": _NAN,
            }

    def status(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "is_ready": self.is_ready,
            "direction": self.current_direction,
            "st_length": self.st_length,
            "st_multiplier": self.st_multiplier,
            "lookback": self.lookback,
            "train_window": self.train_window,
        }


class CCXTStreamProcessor:
    """Utility class for processing CCXT-style candles with multiple indicators.

    Add indicators by name, then process candles to update all at once.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._indicators: dict[str, Any] = {}

    def add_indicator(self, name: str, indicator: Any) -> None:
        with self._lock:
            self._indicators[name] = indicator

    def remove_indicator(self, name: str) -> None:
        with self._lock:
            self._indicators.pop(name, None)

    def reset_all(self) -> None:
        with self._lock:
            for ind in self._indicators.values():
                if hasattr(ind, "reset"):
                    ind.reset()

    def get_status(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            status: dict[str, dict[str, Any]] = {}
            for name, ind in self._indicators.items():
                if hasattr(ind, "status"):
                    status[name] = ind.status()
                else:
                    status[name] = {"count": getattr(ind, "count", None)}
            return status

    def process_candle(self, candle: Iterable[float]) -> dict[str, Any]:
        data = list(candle)
        if len(data) == 6:
            _ts, open_, high, low, close, volume = data
        elif len(data) == 5:
            open_, high, low, close, volume = data
        else:
            raise ValueError("candle must be length 5 or 6")

        results: dict[str, Any] = {}
        with self._lock:
            for name, ind in self._indicators.items():
                if isinstance(ind, (IncrementalATR, IncrementalSuperTrend, IncrementalStochastic,
                                   IncrementalEnsembleSignal, IncrementalMLSuperTrend,
                                   IncrementalAISuperTrend)):
                    out = ind.update(high, low, close)
                else:
                    out = ind.update(close)

                results[name] = out
        return results


def get_available_streaming_indicators() -> list[str]:
    """Return list of available streaming indicator class names."""
    return [
        "IncrementalSMA",
        "IncrementalEMA",
        "IncrementalRSI",
        "IncrementalMACD",
        "IncrementalATR",
        "IncrementalSuperTrend",
        "IncrementalBollingerBands",
        "IncrementalStochastic",
        "IncrementalAdaptiveRSI",
        "IncrementalEnsembleSignal",
        "IncrementalMLSuperTrend",
        "IncrementalAISuperTrend",
    ]


def create_indicator(name: str, /, **kwargs: Any) -> Any:
    """Factory function to create streaming indicators by name.

    Parameters
    ----------
    name : str
        Indicator name (case-insensitive). Supported:
        sma, ema, rsi, macd, atr, supertrend, stochastic/stoch,
        bb/bollinger/bollinger_bands
    **kwargs
        Parameters passed to indicator constructor

    Returns
    -------
    Indicator instance

    Raises
    ------
    ValueError
        If indicator name is unknown
    """
    key = name.strip().lower()
    aliases: dict[str, Any] = {
        "sma": IncrementalSMA,
        "ema": IncrementalEMA,
        "rsi": IncrementalRSI,
        "macd": IncrementalMACD,
        "atr": IncrementalATR,
        "supertrend": IncrementalSuperTrend,
        "stochastic": IncrementalStochastic,
        "stoch": IncrementalStochastic,
        "bb": IncrementalBollingerBands,
        "bollinger": IncrementalBollingerBands,
        "bollinger_bands": IncrementalBollingerBands,
        "adaptive_rsi": IncrementalAdaptiveRSI,
        "ensemble": IncrementalEnsembleSignal,
        "ml_supertrend": IncrementalMLSuperTrend,
        "ai_supertrend": IncrementalAISuperTrend,
        "ai_supertrend_ml": IncrementalAISuperTrend,
    }
    cls = aliases.get(key)
    if cls is None:
        raise ValueError(f"Unknown indicator: {name}")
    return cls(**kwargs)
