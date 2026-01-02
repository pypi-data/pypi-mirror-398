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


# ==================== SFG Indicators (ML-Enhanced) ====================

def ai_supertrend_ml(
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    st_length: int = 10,
    st_multiplier: float = 3.0,
    model_type: str = "linreg",
    lookback: int = 10,
    train_window: int = 200,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    AI SuperTrend ML - ML 增强的 SuperTrend 指标。

    使用线性回归或岭回归预测趋势偏移，提供更准确的趋势跟踪。

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        st_length: SuperTrend ATR 周期 (默认 10)
        st_multiplier: ATR 乘数 (默认 3.0)
        model_type: ML 模型类型 "linreg" 或 "ridge" (默认 "linreg")
        lookback: ML 特征回溯期 (默认 10)
        train_window: ML 训练窗口大小 (默认 200)

    Returns:
        Tuple of 6 arrays:
        - supertrend: SuperTrend 值
        - direction: 趋势方向 (1.0=看涨, -1.0=看跌)
        - buy_signals: 买入信号 (1.0=信号, 0.0=无)
        - sell_signals: 卖出信号 (1.0=信号, 0.0=无)
        - stop_loss: 动态止损价位
        - take_profit: 动态止盈价位
    """
    supertrend, direction, buy, sell, sl, tp = _lib.py_ai_supertrend_ml(
        _to_list_fast(high),
        _to_list_fast(low),
        _to_list_fast(close),
        st_length,
        st_multiplier,
        model_type,
        lookback,
        train_window,
    )
    return (
        _to_array(supertrend),
        _to_array(direction),
        _to_array(buy),
        _to_array(sell),
        _to_array(sl),
        _to_array(tp),
    )


def atr2_signals_ml(
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    volume: ArrayLike,
    rsi_period: int = 14,
    atr_period: int = 14,
    ridge_alpha: float = 1.0,
    momentum_window: int = 10,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    ATR2 Signals ML - 基于 ATR 和动量的 ML 增强信号。

    使用岭回归动态调整 RSI 阈值，提供自适应的买卖信号。

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        volume: 成交量序列
        rsi_period: RSI 计算周期 (默认 14)
        atr_period: ATR 计算周期 (默认 14)
        ridge_alpha: 岭回归正则化参数 (默认 1.0)
        momentum_window: 动量计算窗口 (默认 10)

    Returns:
        Tuple of 6 arrays:
        - rsi: RSI 值
        - buy_signals: 买入信号 (1.0=信号, 0.0=无)
        - sell_signals: 卖出信号 (1.0=信号, 0.0=无)
        - signal_strength: 信号强度 (0.0-1.0)
        - stop_loss: 动态止损价位
        - take_profit: 动态止盈价位
    """
    rsi, buy, sell, strength, sl, tp = _lib.py_atr2_signals_ml(
        _to_list_fast(high),
        _to_list_fast(low),
        _to_list_fast(close),
        _to_list_fast(volume),
        rsi_period,
        atr_period,
        ridge_alpha,
        momentum_window,
    )
    return (
        _to_array(rsi),
        _to_array(buy),
        _to_array(sell),
        _to_array(strength),
        _to_array(sl),
        _to_array(tp),
    )


def ai_momentum_index_ml(
    close: ArrayLike,
    rsi_period: int = 14,
    smooth_period: int = 3,
    use_polynomial: bool = False,
    lookback: int = 5,
    train_window: int = 200,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    AI Momentum Index ML - ML 增强的动量指标。

    使用机器学习预测动量方向，提供超买超卖和零线穿越信号。

    Args:
        close: 收盘价序列
        rsi_period: RSI 计算周期 (默认 14)
        smooth_period: 平滑周期 (默认 3)
        use_polynomial: 是否使用多项式特征 (默认 False)
        lookback: ML 特征回溯期 (默认 5)
        train_window: ML 训练窗口大小 (默认 200)

    Returns:
        Tuple of 6 arrays:
        - rsi: RSI 值
        - predicted_momentum: 预测动量值
        - zero_cross_buy: 零线向上穿越信号 (买入)
        - zero_cross_sell: 零线向下穿越信号 (卖出)
        - overbought: 超买信号
        - oversold: 超卖信号
    """
    rsi, momentum, buy, sell, overbought, oversold = _lib.py_ai_momentum_index_ml(
        _to_list_fast(close),
        rsi_period,
        smooth_period,
        use_polynomial,
        lookback,
        train_window,
    )
    return (
        _to_array(rsi),
        _to_array(momentum),
        _to_array(buy),
        _to_array(sell),
        _to_array(overbought),
        _to_array(oversold),
    )


def general_parameters_signals(
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    ema_fast: int = 20,
    ema_slow: int = 50,
    atr_period: int = 14,
    grid_multiplier: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    General Parameters Signals - EMA 通道 + 网格入场信号。

    基于 EMA 通道和 ATR 生成网格交易信号。

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        ema_fast: 快速 EMA 周期 (默认 20)
        ema_slow: 慢速 EMA 周期 (默认 50)
        atr_period: ATR 计算周期 (默认 14)
        grid_multiplier: 网格间距乘数 (默认 1.0)

    Returns:
        Tuple of 4 arrays:
        - buy_signals: 买入信号 (1.0=信号, 0.0=无)
        - sell_signals: 卖出信号 (1.0=信号, 0.0=无)
        - stop_loss: 动态止损价位
        - take_profit: 动态止盈价位
    """
    buy, sell, sl, tp = _lib.py_general_parameters_signals(
        _to_list_fast(high),
        _to_list_fast(low),
        _to_list_fast(close),
        ema_fast,
        ema_slow,
        atr_period,
        grid_multiplier,
    )
    return _to_array(buy), _to_array(sell), _to_array(sl), _to_array(tp)


def ai_supertrend(
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    k: int = 5,
    n: int = 100,
    price_trend: int = 10,
    predict_trend: int = 10,
    st_length: int = 10,
    st_multiplier: float = 3.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    AI SuperTrend - KNN 增强的 SuperTrend 指标（非 ML 版本）。

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        k: KNN 近邻数 (默认 5)
        n: 训练样本数 (默认 100)
        price_trend: 价格趋势周期 (默认 10)
        predict_trend: 预测趋势周期 (默认 10)
        st_length: SuperTrend ATR 周期 (默认 10)
        st_multiplier: ATR 乘数 (默认 3.0)

    Returns:
        Tuple of 2 arrays: (supertrend, direction)
    """
    supertrend, direction = _lib.py_ai_supertrend(
        _to_list_fast(high),
        _to_list_fast(low),
        _to_list_fast(close),
        k, n, price_trend, predict_trend, st_length, st_multiplier,
    )
    return _to_array(supertrend), _to_array(direction)


def ai_momentum_index(
    close: ArrayLike,
    k: int = 5,
    trend_length: int = 10,
    smooth: int = 3,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    AI Momentum Index - KNN 增强的动量指标（非 ML 版本）。

    Args:
        close: 收盘价序列
        k: KNN 近邻数 (默认 5)
        trend_length: 趋势长度 (默认 10)
        smooth: 平滑周期 (默认 3)

    Returns:
        Tuple of 2 arrays: (momentum, smoothed_momentum)
    """
    momentum, smoothed = _lib.py_ai_momentum_index(
        _to_list_fast(close), k, trend_length, smooth,
    )
    return _to_array(momentum), _to_array(smoothed)


def atr2_signals(
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    volume: ArrayLike,
    trend_length: int = 14,
    confirmation_threshold: float = 0.5,
    momentum_window: int = 10,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    ATR2 Signals - ATR 和动量信号生成器（非 ML 版本）。

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        volume: 成交量序列
        trend_length: 趋势周期 (默认 14)
        confirmation_threshold: 确认阈值 (默认 0.5)
        momentum_window: 动量窗口 (默认 10)

    Returns:
        Tuple of 3 arrays: (buy_signals, sell_signals, signal_strength)
    """
    buy, sell, strength = _lib.py_atr2_signals(
        _to_list_fast(high),
        _to_list_fast(low),
        _to_list_fast(close),
        _to_list_fast(volume),
        trend_length, confirmation_threshold, momentum_window,
    )
    return _to_array(buy), _to_array(sell), _to_array(strength)


def pivot_buy_sell(
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    lookback: int = 5,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Pivot Buy/Sell - 枢轴点买卖信号。

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        lookback: 回溯周期 (默认 5)

    Returns:
        Tuple of 7 arrays: (pivot, r1, r2, s1, s2, buy_signals, sell_signals)
    """
    pivot, r1, r2, s1, s2, buy, sell = _lib.py_pivot_buy_sell(
        _to_list_fast(high),
        _to_list_fast(low),
        _to_list_fast(close),
        lookback,
    )
    return (
        _to_array(pivot), _to_array(r1), _to_array(r2),
        _to_array(s1), _to_array(s2),
        _to_array(buy), _to_array(sell),
    )


def detect_divergence(
    price: ArrayLike,
    indicator: ArrayLike,
    lookback: int = 5,
    threshold: float = 0.01,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    背离检测 - 检测价格与指标之间的背离。

    Args:
        price: 价格序列
        indicator: 指标序列 (如 RSI, MACD)
        lookback: 回溯周期 (默认 5)
        threshold: 背离阈值 (默认 0.01)

    Returns:
        Tuple of 2 arrays:
        - divergence_type: 背离类型 (0=无, 1=常规看涨, 2=常规看跌, 3=隐藏看涨, 4=隐藏看跌)
        - strength: 背离强度 (0.0-1.0)
    """
    div_type, strength = _lib.py_detect_divergence(
        _to_list_fast(price),
        _to_list_fast(indicator),
        lookback, threshold,
    )
    return _to_array(div_type), _to_array(strength)


def fvg_signals(
    high: ArrayLike,
    low: ArrayLike,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    FVG (Fair Value Gap) 信号 - 公平价值缺口检测。

    ICT (Inner Circle Trader) 概念，检测价格中的失衡区域。

    Args:
        high: 最高价序列
        low: 最低价序列

    Returns:
        Tuple of 4 arrays:
        - bullish_fvg: 看涨 FVG (1.0=存在, 0.0=无)
        - bearish_fvg: 看跌 FVG (1.0=存在, 0.0=无)
        - fvg_upper: FVG 上边界
        - fvg_lower: FVG 下边界
    """
    bullish, bearish, upper, lower = _lib.py_fvg_signals(
        _to_list_fast(high),
        _to_list_fast(low),
    )
    return _to_array(bullish), _to_array(bearish), _to_array(upper), _to_array(lower)


def pd_array_signals(
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    swing_lookback: int = 10,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    PD Array Signals - 溢价/折扣区域信号。

    ICT 概念，基于 swing high/low 计算溢价和折扣区域。

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        swing_lookback: Swing 点回溯周期 (默认 10)

    Returns:
        Tuple of 4 arrays:
        - premium_zone: 溢价区 (1.0=在区域内, 0.0=无)
        - discount_zone: 折扣区 (1.0=在区域内, 0.0=无)
        - equilibrium: 平衡点价格
        - zone_strength: 区域强度
    """
    premium, discount, equilibrium, strength = _lib.py_pd_array_signals(
        _to_list_fast(high),
        _to_list_fast(low),
        _to_list_fast(close),
        swing_lookback,
    )
    return _to_array(premium), _to_array(discount), _to_array(equilibrium), _to_array(strength)


def combine_signals(
    buy1: ArrayLike,
    sell1: ArrayLike,
    buy2: ArrayLike,
    sell2: ArrayLike,
    weight1: float = 0.5,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    组合信号 - 加权组合两组交易信号。

    Args:
        buy1: 第一组买入信号
        sell1: 第一组卖出信号
        buy2: 第二组买入信号
        sell2: 第二组卖出信号
        weight1: 第一组权重 (默认 0.5, 第二组为 1-weight1)

    Returns:
        Tuple of 3 arrays:
        - combined_buy: 组合买入信号
        - combined_sell: 组合卖出信号
        - signal_strength: 信号强度
    """
    buy, sell, strength = _lib.py_combine_signals(
        _to_list_fast(buy1),
        _to_list_fast(sell1),
        _to_list_fast(buy2),
        _to_list_fast(sell2),
        weight1,
    )
    return _to_array(buy), _to_array(sell), _to_array(strength)


def calculate_stops(
    close: ArrayLike,
    atr_values: ArrayLike,
    buy_signals: ArrayLike,
    sell_signals: ArrayLike,
    sl_multiplier: float = 1.5,
    tp_multiplier: float = 2.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    计算止损止盈 - 基于 ATR 计算动态止损止盈价位。

    Args:
        close: 收盘价序列
        atr_values: ATR 值序列
        buy_signals: 买入信号序列
        sell_signals: 卖出信号序列
        sl_multiplier: 止损 ATR 乘数 (默认 1.5)
        tp_multiplier: 止盈 ATR 乘数 (默认 2.0)

    Returns:
        Tuple of 2 arrays:
        - stop_loss: 止损价位
        - take_profit: 止盈价位
    """
    sl, tp = _lib.py_calculate_stops(
        _to_list_fast(close),
        _to_list_fast(atr_values),
        _to_list_fast(buy_signals),
        _to_list_fast(sell_signals),
        sl_multiplier, tp_multiplier,
    )
    return _to_array(sl), _to_array(tp)


def dynamic_macd(
    open_: ArrayLike,
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    fast_length: int = 12,
    slow_length: int = 26,
    signal_smooth: int = 9,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Dynamic MACD - Heikin-Ashi 增强的 MACD 指标

    使用 HLCC4 (High+Low+Close+Close)/4 作为数据源计算 MACD，
    并同时输出 Heikin-Ashi 蜡烛图数据用于趋势确认。

    Args:
        open_: 开盘价序列
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        fast_length: 快速 EMA 周期（默认 12）
        slow_length: 慢速 EMA 周期（默认 26）
        signal_smooth: 信号线平滑周期（默认 9）

    Returns:
        Tuple of 5 arrays:
        - macd: MACD 线
        - signal: 信号线
        - histogram: MACD 柱状图
        - ha_open: Heikin-Ashi 开盘价
        - ha_close: Heikin-Ashi 收盘价
    """
    macd, signal, histogram, ha_open, ha_close = _lib.py_dynamic_macd(
        _to_list_fast(open_),
        _to_list_fast(high),
        _to_list_fast(low),
        _to_list_fast(close),
        fast_length, slow_length, signal_smooth,
    )
    return (
        _to_array(macd),
        _to_array(signal),
        _to_array(histogram),
        _to_array(ha_open),
        _to_array(ha_close),
    )


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
    # SFG (Signal Force Generator - ML-Enhanced + Market Structure)
    'ai_supertrend_ml', 'atr2_signals_ml', 'ai_momentum_index_ml',
    'general_parameters_signals',
    # SFG Non-ML versions
    'ai_supertrend', 'ai_momentum_index', 'atr2_signals',
    # SFG Market Structure (ICT Concepts)
    'pivot_buy_sell', 'detect_divergence', 'fvg_signals',
    'pd_array_signals', 'combine_signals', 'calculate_stops',
    # SFG Enhanced MACD
    'dynamic_macd',
]
