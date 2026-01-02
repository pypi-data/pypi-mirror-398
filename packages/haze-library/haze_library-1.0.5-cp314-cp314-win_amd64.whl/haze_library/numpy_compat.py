"""
Haze-Library NumPy Compatibility Layer
======================================

Provides zero-copy or minimal-copy numpy array support for indicators.

Design:
- Accepts numpy arrays directly
- Returns numpy arrays for single outputs
- Uses optimized conversion paths to minimize memory overhead
- Automatically handles NaN values and type conversion

Usage:
    from haze_library.numpy_compat import sma, rsi, macd
    import numpy as np

    close = np.array([...])
    sma_values = sma(close, 20)  # Returns np.ndarray
"""

from __future__ import annotations

from collections import deque
from typing import Tuple

import numpy as np
# Import Rust extension
try:
    from . import haze_library as _lib
except ImportError:
    import haze_library as _lib

# Type alias for array-like inputs
ArrayLike = np.ndarray | list


def _ensure_float64(arr: ArrayLike) -> np.ndarray:
    """Convert input to float64 numpy array."""
    if isinstance(arr, np.ndarray):
        if arr.dtype != np.float64:
            return arr.astype(np.float64)
        return arr
    return np.array(arr, dtype=np.float64)


def _to_list_fast(arr: ArrayLike) -> list:
    """Fast conversion to list for Rust interface."""
    if isinstance(arr, np.ndarray):
        # Use numpy's optimized tolist() method
        return arr.astype(np.float64, copy=False).tolist()
    return list(arr)


def _to_array(result: list) -> np.ndarray:
    """Convert result list to numpy array."""
    return np.array(result, dtype=np.float64)


# ==================== Moving Averages ====================

def sma(data: ArrayLike, period: int = 20) -> np.ndarray:
    """Simple Moving Average."""
    return _to_array(_lib.py_sma(_to_list_fast(data), period))


def ema(data: ArrayLike, period: int = 20) -> np.ndarray:
    """Exponential Moving Average."""
    return _to_array(_lib.py_ema(_to_list_fast(data), period))


def rma(data: ArrayLike, period: int = 14) -> np.ndarray:
    """Wilder's Moving Average (RMA)."""
    return _to_array(_lib.py_rma(_to_list_fast(data), period))


def wma(data: ArrayLike, period: int = 20) -> np.ndarray:
    """Weighted Moving Average."""
    return _to_array(_lib.py_wma(_to_list_fast(data), period))


def hma(data: ArrayLike, period: int = 20) -> np.ndarray:
    """Hull Moving Average."""
    return _to_array(_lib.py_hma(_to_list_fast(data), period))


def dema(data: ArrayLike, period: int = 20) -> np.ndarray:
    """Double Exponential Moving Average."""
    return _to_array(_lib.py_dema(_to_list_fast(data), period))


def tema(data: ArrayLike, period: int = 20) -> np.ndarray:
    """Triple Exponential Moving Average."""
    return _to_array(_lib.py_tema(_to_list_fast(data), period))


def zlma(data: ArrayLike, period: int = 20) -> np.ndarray:
    """Zero Lag Moving Average."""
    return _to_array(_lib.py_zlma(_to_list_fast(data), period))


def kama(data: ArrayLike, period: int = 10, fast: int = 2,
         slow: int = 30) -> np.ndarray:
    """Kaufman's Adaptive Moving Average."""
    return _to_array(_lib.py_kama(_to_list_fast(data), period, fast, slow))


def t3(data: ArrayLike, period: int = 5, v_factor: float = 0.7) -> np.ndarray:
    """T3 Moving Average."""
    return _to_array(_lib.py_t3(_to_list_fast(data), period, v_factor))


def alma(data: ArrayLike, period: int = 9, offset: float = 0.85,
         sigma: float = 6.0) -> np.ndarray:
    """Arnaud Legoux Moving Average."""
    return _to_array(_lib.py_alma(_to_list_fast(data), period, offset, sigma))


def frama(data: ArrayLike, period: int = 10) -> np.ndarray:
    """Fractal Adaptive Moving Average."""
    return _to_array(_lib.py_frama(_to_list_fast(data), period))


def trima(data: ArrayLike, period: int = 20) -> np.ndarray:
    """Triangular Moving Average."""
    return _to_array(_lib.py_trima(_to_list_fast(data), period))


def vidya(data: ArrayLike, period: int = 14) -> np.ndarray:
    """Variable Index Dynamic Average."""
    return _to_array(_lib.py_vidya(_to_list_fast(data), period))


# ==================== Volatility Indicators ====================

def atr(high: ArrayLike, low: ArrayLike, close: ArrayLike,
        period: int = 14) -> np.ndarray:
    """Average True Range."""
    return _to_array(_lib.py_atr(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close), period
    ))


def natr(high: ArrayLike, low: ArrayLike, close: ArrayLike,
         period: int = 14) -> np.ndarray:
    """Normalized Average True Range (percentage)."""
    return _to_array(_lib.py_natr(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close), period
    ))


def true_range(high: ArrayLike, low: ArrayLike, close: ArrayLike,
               drift: int = 1) -> np.ndarray:
    """True Range."""
    return _to_array(_lib.py_true_range(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close), drift
    ))


def bollinger_bands(data: ArrayLike, period: int = 20,
                    std: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Bollinger Bands. Returns (upper, middle, lower)."""
    upper, middle, lower = _lib.py_bollinger_bands(
        _to_list_fast(data), period, std
    )
    return _to_array(upper), _to_array(middle), _to_array(lower)


def keltner_channel(high: ArrayLike, low: ArrayLike, close: ArrayLike,
                    period: int = 20, atr_period: int | None = None,
                    multiplier: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Keltner Channel. Returns (upper, middle, lower)."""
    if atr_period is None:
        atr_period = period
    upper, middle, lower = _lib.py_keltner_channel(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close),
        period, atr_period, multiplier
    )
    return _to_array(upper), _to_array(middle), _to_array(lower)


def donchian_channel(high: ArrayLike, low: ArrayLike,
                     period: int = 20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Donchian Channel. Returns (upper, middle, lower)."""
    upper, middle, lower = _lib.py_donchian_channel(
        _to_list_fast(high), _to_list_fast(low), period
    )
    return _to_array(upper), _to_array(middle), _to_array(lower)


# ==================== Momentum Indicators ====================

def rsi(data: ArrayLike, period: int = 14) -> np.ndarray:
    """Relative Strength Index."""
    return _to_array(_lib.py_rsi(_to_list_fast(data), period))


def macd(data: ArrayLike, fast: int = 12, slow: int = 26,
         signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """MACD. Returns (macd_line, signal_line, histogram)."""
    macd_line, signal_line, histogram = _lib.py_macd(
        _to_list_fast(data), fast, slow, signal
    )
    return _to_array(macd_line), _to_array(signal_line), _to_array(histogram)


def stochastic(high: ArrayLike, low: ArrayLike, close: ArrayLike,
               k_period: int = 14, smooth_k: int = 3,
               d_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """Stochastic Oscillator. Returns (%K, %D)."""
    k, d = _lib.py_stochastic(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close),
        k_period, smooth_k, d_period
    )
    return _to_array(k), _to_array(d)


def stochrsi(
    data: ArrayLike,
    period: int = 14,
    stoch_period: int | None = None,
    k_period: int = 3,
    d_period: int = 3,
) -> Tuple[np.ndarray, np.ndarray]:
    """Stochastic RSI. Returns (%K, %D)."""
    if stoch_period is None:
        stoch_period = period
    k, d = _lib.py_stochrsi(_to_list_fast(data), period, stoch_period, k_period, d_period)
    return _to_array(k), _to_array(d)


def cci(high: ArrayLike, low: ArrayLike, close: ArrayLike,
        period: int = 20) -> np.ndarray:
    """Commodity Channel Index."""
    return _to_array(_lib.py_cci(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close), period
    ))


def williams_r(high: ArrayLike, low: ArrayLike, close: ArrayLike,
               period: int = 14) -> np.ndarray:
    """Williams %R."""
    return _to_array(_lib.py_williams_r(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close), period
    ))


def awesome_oscillator(high: ArrayLike, low: ArrayLike,
                       fast: int = 5, slow: int = 34) -> np.ndarray:
    """Awesome Oscillator."""
    return _to_array(_lib.py_awesome_oscillator(
        _to_list_fast(high), _to_list_fast(low), fast, slow
    ))


def fisher_transform(high: ArrayLike, low: ArrayLike, close: ArrayLike,
                     period: int = 9) -> Tuple[np.ndarray, np.ndarray]:
    """Fisher Transform. Returns (fisher, signal)."""
    fisher, signal = _lib.py_fisher_transform(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close), period
    )
    return _to_array(fisher), _to_array(signal)


def kdj(high: ArrayLike, low: ArrayLike, close: ArrayLike,
        k_period: int = 9, smooth_k: int = 3,
        d_period: int = 3) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """KDJ Indicator. Returns (K, D, J)."""
    k, d, j = _lib.py_kdj(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close),
        k_period, smooth_k, d_period
    )
    return _to_array(k), _to_array(d), _to_array(j)


def tsi(data: ArrayLike, fast: int = 13, slow: int = 25,
        signal: int = 13) -> Tuple[np.ndarray, np.ndarray]:
    """True Strength Index. Returns (tsi, signal)."""
    tsi_val, signal_line = _lib.py_tsi(_to_list_fast(data), slow, fast, signal)
    return _to_array(tsi_val), _to_array(signal_line)


def ultimate_oscillator(high: ArrayLike, low: ArrayLike, close: ArrayLike,
                        short: int = 7, medium: int = 14,
                        long: int = 28) -> np.ndarray:
    """Ultimate Oscillator."""
    return _to_array(_lib.py_ultimate_oscillator(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close),
        short, medium, long
    ))


def mom(data: ArrayLike, period: int = 10) -> np.ndarray:
    """Momentum."""
    return _to_array(_lib.py_mom(_to_list_fast(data), period))


def roc(data: ArrayLike, period: int = 10) -> np.ndarray:
    """Rate of Change (percentage)."""
    return _to_array(_lib.py_roc(_to_list_fast(data), period))


def cmo(data: ArrayLike, period: int = 14) -> np.ndarray:
    """Chande Momentum Oscillator."""
    return _to_array(_lib.py_cmo(_to_list_fast(data), period))


def apo(data: ArrayLike, fast: int = 12, slow: int = 26) -> np.ndarray:
    """Absolute Price Oscillator."""
    return _to_array(_lib.py_apo(_to_list_fast(data), fast, slow))


def ppo(data: ArrayLike, fast: int = 12, slow: int = 26) -> np.ndarray:
    """Percentage Price Oscillator."""
    return _to_array(_lib.py_ppo(_to_list_fast(data), fast, slow))


# ==================== Trend Indicators ====================

def supertrend(high: ArrayLike, low: ArrayLike, close: ArrayLike,
               period: int = 10, multiplier: float = 3.0
               ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """SuperTrend. Returns (supertrend, direction, upper_band, lower_band)."""
    st, direction, upper, lower = _lib.py_supertrend(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close),
        period, multiplier
    )
    return _to_array(st), _to_array(direction), _to_array(upper), _to_array(lower)


def adx(high: ArrayLike, low: ArrayLike, close: ArrayLike,
        period: int = 14) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Average Directional Index. Returns (adx, plus_di, minus_di)."""
    adx_val, plus_di, minus_di = _lib.py_adx(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close), period
    )
    return _to_array(adx_val), _to_array(plus_di), _to_array(minus_di)


def aroon(high: ArrayLike, low: ArrayLike,
          period: int = 25) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Aroon. Returns (aroon_up, aroon_down, oscillator)."""
    up, down, osc = _lib.py_aroon(
        _to_list_fast(high), _to_list_fast(low), period
    )
    return _to_array(up), _to_array(down), _to_array(osc)


def psar(high: ArrayLike, low: ArrayLike, close: ArrayLike,
         af_start: float = 0.02, af_increment: float = 0.02,
         af_max: float = 0.2) -> Tuple[np.ndarray, np.ndarray]:
    """Parabolic SAR. Returns (sar, direction)."""
    sar, direction = _lib.py_psar(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close),
        af_start, af_increment, af_max
    )
    return _to_array(sar), _to_array(direction)


def vortex(high: ArrayLike, low: ArrayLike, close: ArrayLike,
           period: int = 14) -> Tuple[np.ndarray, np.ndarray]:
    """Vortex Indicator. Returns (VI+, VI-)."""
    vi_plus, vi_minus = _lib.py_vortex(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close), period
    )
    return _to_array(vi_plus), _to_array(vi_minus)


def choppiness(high: ArrayLike, low: ArrayLike, close: ArrayLike,
               period: int = 14) -> np.ndarray:
    """Choppiness Index."""
    return _to_array(_lib.py_choppiness(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close), period
    ))


def dx(high: ArrayLike, low: ArrayLike, close: ArrayLike,
       period: int = 14) -> np.ndarray:
    """Directional Movement Index."""
    return _to_array(_lib.py_dx(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close), period
    ))


def plus_di(high: ArrayLike, low: ArrayLike, close: ArrayLike,
            period: int = 14) -> np.ndarray:
    """Plus Directional Indicator (+DI)."""
    return _to_array(_lib.py_plus_di(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close), period
    ))


def minus_di(high: ArrayLike, low: ArrayLike, close: ArrayLike,
             period: int = 14) -> np.ndarray:
    """Minus Directional Indicator (-DI)."""
    return _to_array(_lib.py_minus_di(
        _to_list_fast(high), _to_list_fast(low), _to_list_fast(close), period
    ))


# ==================== Volume Indicators ====================

def obv(close: ArrayLike, volume: ArrayLike) -> np.ndarray:
    """On Balance Volume."""
    return _to_array(_lib.py_obv(
        _to_list_fast(close), _to_list_fast(volume)
    ))


def vwap(high: ArrayLike, low: ArrayLike, close: ArrayLike,
         volume: ArrayLike) -> np.ndarray:
    """Volume Weighted Average Price."""
    return _to_array(_lib.py_vwap(
        _to_list_fast(high), _to_list_fast(low),
        _to_list_fast(close), _to_list_fast(volume)
    ))


def mfi(high: ArrayLike, low: ArrayLike, close: ArrayLike,
        volume: ArrayLike, period: int = 14) -> np.ndarray:
    """Money Flow Index."""
    return _to_array(_lib.py_mfi(
        _to_list_fast(high), _to_list_fast(low),
        _to_list_fast(close), _to_list_fast(volume), period
    ))


def cmf(high: ArrayLike, low: ArrayLike, close: ArrayLike,
        volume: ArrayLike, period: int = 20) -> np.ndarray:
    """Chaikin Money Flow."""
    return _to_array(_lib.py_cmf(
        _to_list_fast(high), _to_list_fast(low),
        _to_list_fast(close), _to_list_fast(volume), period
    ))


def ad(high: ArrayLike, low: ArrayLike, close: ArrayLike,
       volume: ArrayLike) -> np.ndarray:
    """Accumulation/Distribution Line."""
    return _to_array(_lib.py_ad(
        _to_list_fast(high), _to_list_fast(low),
        _to_list_fast(close), _to_list_fast(volume)
    ))


def adosc(high: ArrayLike, low: ArrayLike, close: ArrayLike,
          volume: ArrayLike, fast: int = 3, slow: int = 10) -> np.ndarray:
    """Accumulation/Distribution Oscillator."""
    return _to_array(_lib.py_adosc(
        _to_list_fast(high), _to_list_fast(low),
        _to_list_fast(close), _to_list_fast(volume), fast, slow
    ))


def pvt(close: ArrayLike, volume: ArrayLike) -> np.ndarray:
    """Price Volume Trend."""
    return _to_array(_lib.py_pvt(
        _to_list_fast(close), _to_list_fast(volume)
    ))


def nvi(close: ArrayLike, volume: ArrayLike) -> np.ndarray:
    """Negative Volume Index."""
    return _to_array(_lib.py_nvi(
        _to_list_fast(close), _to_list_fast(volume)
    ))


def pvi(close: ArrayLike, volume: ArrayLike) -> np.ndarray:
    """Positive Volume Index."""
    return _to_array(_lib.py_pvi(
        _to_list_fast(close), _to_list_fast(volume)
    ))


def eom(high: ArrayLike, low: ArrayLike, volume: ArrayLike,
        period: int = 14) -> np.ndarray:
    """Ease of Movement."""
    return _to_array(_lib.py_eom(
        _to_list_fast(high), _to_list_fast(low),
        _to_list_fast(volume), period
    ))


# ==================== Statistical Indicators ====================

def variance(data: ArrayLike, period: int = 20) -> np.ndarray:
    """Rolling Variance."""
    return _to_array(_lib.py_var(_to_list_fast(data), period))


def stddev(data: ArrayLike, period: int = 20) -> np.ndarray:
    """Rolling Standard Deviation."""
    var = np.array(_lib.py_var(_to_list_fast(data), period), dtype=np.float64)
    return np.sqrt(np.clip(var, 0.0, None))


def zscore(data: ArrayLike, period: int = 20) -> np.ndarray:
    """Rolling Z-Score."""
    return _to_array(_lib.py_zscore(_to_list_fast(data), period))


def linear_regression(data: ArrayLike, period: int = 14) -> np.ndarray:
    """Linear Regression Value."""
    return _to_array(_lib.py_linearreg(_to_list_fast(data), period))


def linreg_slope(data: ArrayLike, period: int = 14) -> np.ndarray:
    """Linear Regression Slope."""
    return _to_array(_lib.py_linearreg_slope(_to_list_fast(data), period))


def linreg_angle(data: ArrayLike, period: int = 14) -> np.ndarray:
    """Linear Regression Angle (degrees)."""
    return _to_array(_lib.py_linearreg_angle(_to_list_fast(data), period))


def linreg_intercept(data: ArrayLike, period: int = 14) -> np.ndarray:
    """Linear Regression Intercept."""
    return _to_array(_lib.py_linearreg_intercept(_to_list_fast(data), period))


# ==================== Candlestick Patterns ====================

def heikin_ashi(open_: ArrayLike, high: ArrayLike, low: ArrayLike,
                close: ArrayLike) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Heikin Ashi candles. Returns (ha_open, ha_high, ha_low, ha_close)."""
    open_arr = _ensure_float64(open_)
    high_arr = _ensure_float64(high)
    low_arr = _ensure_float64(low)
    close_arr = _ensure_float64(close)

    n = len(close_arr)
    ha_close = (open_arr + high_arr + low_arr + close_arr) / 4.0
    ha_open = np.empty(n, dtype=np.float64)
    if n == 0:
        return ha_open, ha_open, ha_open, ha_close

    ha_open[0] = (open_arr[0] + close_arr[0]) / 2.0
    for i in range(1, n):
        ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2.0

    ha_high = np.maximum.reduce([high_arr, ha_open, ha_close])
    ha_low = np.minimum.reduce([low_arr, ha_open, ha_close])
    return ha_open, ha_high, ha_low, ha_close


def doji(open_: ArrayLike, high: ArrayLike, low: ArrayLike,
         close: ArrayLike, threshold: float = 0.1) -> np.ndarray:
    """Doji pattern detection."""
    return _to_array(_lib.py_doji(
        _to_list_fast(open_), _to_list_fast(high),
        _to_list_fast(low), _to_list_fast(close), threshold
    ))


def hammer(open_: ArrayLike, high: ArrayLike, low: ArrayLike,
           close: ArrayLike) -> np.ndarray:
    """Hammer pattern detection."""
    return _to_array(_lib.py_hammer(
        _to_list_fast(open_), _to_list_fast(high),
        _to_list_fast(low), _to_list_fast(close)
    ))


def engulfing(open_: ArrayLike, high: ArrayLike, low: ArrayLike,
              close: ArrayLike) -> np.ndarray:
    """Engulfing pattern detection."""
    open_list = _to_list_fast(open_)
    close_list = _to_list_fast(close)
    bullish = np.array(_lib.py_bullish_engulfing(open_list, close_list), dtype=np.float64)
    bearish = np.array(_lib.py_bearish_engulfing(open_list, close_list), dtype=np.float64)
    return bullish - bearish


def morning_star(open_: ArrayLike, high: ArrayLike, low: ArrayLike,
                 close: ArrayLike) -> np.ndarray:
    """Morning Star pattern detection."""
    return _to_array(_lib.py_morning_star(
        _to_list_fast(open_), _to_list_fast(high),
        _to_list_fast(low), _to_list_fast(close)
    ))


def evening_star(open_: ArrayLike, high: ArrayLike, low: ArrayLike,
                 close: ArrayLike) -> np.ndarray:
    """Evening Star pattern detection."""
    return _to_array(_lib.py_evening_star(
        _to_list_fast(open_), _to_list_fast(high),
        _to_list_fast(low), _to_list_fast(close)
    ))


# ==================== Utility Functions ====================

def crossover(series1: ArrayLike, series2: ArrayLike) -> np.ndarray:
    """Detect crossover (series1 crosses above series2)."""
    s1 = _ensure_float64(series1)
    s2 = _ensure_float64(series2)
    if len(s1) != len(s2):
        raise ValueError("series1 and series2 must have the same length")
    n = len(s1)
    result = np.zeros(n, dtype=np.float64)
    if n < 2:
        return result
    crossed = (s1[1:] > s2[1:]) & (s1[:-1] <= s2[:-1])
    result[1:] = crossed.astype(np.float64)
    return result


def crossunder(series1: ArrayLike, series2: ArrayLike) -> np.ndarray:
    """Detect crossunder (series1 crosses below series2)."""
    s1 = _ensure_float64(series1)
    s2 = _ensure_float64(series2)
    if len(s1) != len(s2):
        raise ValueError("series1 and series2 must have the same length")
    n = len(s1)
    result = np.zeros(n, dtype=np.float64)
    if n < 2:
        return result
    crossed = (s1[1:] < s2[1:]) & (s1[:-1] >= s2[:-1])
    result[1:] = crossed.astype(np.float64)
    return result


def highest(data: ArrayLike, period: int = 14) -> np.ndarray:
    """Rolling highest value."""
    values = _ensure_float64(data)
    n = len(values)
    out = np.full(n, np.nan, dtype=np.float64)
    if period <= 0:
        raise ValueError("period must be a positive integer")
    if n == 0:
        return out
    window = int(period)
    q: deque[int] = deque()
    for i in range(n):
        while q and q[0] <= i - window:
            q.popleft()
        while q and values[q[-1]] <= values[i]:
            q.pop()
        q.append(i)
        if i >= window - 1:
            out[i] = values[q[0]]
    return out


def lowest(data: ArrayLike, period: int = 14) -> np.ndarray:
    """Rolling lowest value."""
    values = _ensure_float64(data)
    n = len(values)
    out = np.full(n, np.nan, dtype=np.float64)
    if period <= 0:
        raise ValueError("period must be a positive integer")
    if n == 0:
        return out
    window = int(period)
    q: deque[int] = deque()
    for i in range(n):
        while q and q[0] <= i - window:
            q.popleft()
        while q and values[q[-1]] >= values[i]:
            q.pop()
        q.append(i)
        if i >= window - 1:
            out[i] = values[q[0]]
    return out


def percent_rank(data: ArrayLike, period: int = 20) -> np.ndarray:
    """Percent Rank."""
    return _to_array(_lib.py_percent_rank(_to_list_fast(data), period))


# Export all functions
__all__ = [
    # Moving Averages
    'sma', 'ema', 'rma', 'wma', 'hma', 'dema', 'tema', 'zlma',
    'kama', 't3', 'alma', 'frama', 'trima', 'vidya',
    # Volatility
    'atr', 'natr', 'true_range', 'bollinger_bands',
    'keltner_channel', 'donchian_channel',
    # Momentum
    'rsi', 'macd', 'stochastic', 'stochrsi', 'cci', 'williams_r',
    'awesome_oscillator', 'fisher_transform', 'kdj', 'tsi',
    'ultimate_oscillator', 'mom', 'roc', 'cmo', 'apo', 'ppo',
    # Trend
    'supertrend', 'adx', 'aroon', 'psar', 'vortex',
    'choppiness', 'dx', 'plus_di', 'minus_di',
    # Volume
    'obv', 'vwap', 'mfi', 'cmf', 'ad', 'adosc', 'pvt', 'nvi', 'pvi', 'eom',
    # Statistical
    'variance', 'stddev', 'zscore', 'linear_regression',
    'linreg_slope', 'linreg_angle', 'linreg_intercept',
    # Candlestick
    'heikin_ashi', 'doji', 'hammer', 'engulfing',
    'morning_star', 'evening_star',
    # Utility
    'crossover', 'crossunder', 'highest', 'lowest', 'percent_rank',
]
