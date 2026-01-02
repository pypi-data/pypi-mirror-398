from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, TypeAlias, Union
from types import ModuleType

# ==================== Type Aliases ====================
FloatList: TypeAlias = List[float]
IntList: TypeAlias = List[int]
BoolList: TypeAlias = List[bool]
ArrayLike: TypeAlias = Union[List[float], Sequence[float]]

# ==================== Version Info ====================
__version__: str
__author__: str
__all__: List[str]

# ==================== Submodules ====================
accessor: ModuleType
ai_indicators: ModuleType
exceptions: ModuleType
haze_library: ModuleType
np_ta: ModuleType
numpy_compat: ModuleType
polars_ta: ModuleType
stream_ta: ModuleType
streaming: ModuleType
torch_ta: ModuleType

# ==================== Core PyO3 Exports ====================

from .haze_library import *

# ==================== Error Classes ====================

class HazeError(Exception):

    ...

class InvalidParameterError(HazeError):

    ...

class InvalidPeriodError(HazeError):

    ...

class InsufficientDataError(HazeError):

    ...

class ComputationError(HazeError):

    ...

class ColumnNotFoundError(HazeError):

    ...

# ==================== Incremental/Streaming Indicators ====================

class IncrementalSMA:

    def __init__(self, period: int) -> None: ...

class IncrementalEMA:

    def __init__(self, period: int) -> None: ...

class IncrementalRSI:

    def __init__(self, period: int = 14) -> None: ...

class IncrementalMACD:

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9) -> None: ...
    def update(self, value: float) -> Tuple[float, float, float]: ...

class IncrementalATR:

    def __init__(self, period: int = 14) -> None: ...
    def update(self, high: float, low: float, close: float) -> float: ...

class IncrementalBollingerBands:

    def __init__(self, period: int = 20, std_dev: float = 2.0) -> None: ...
    def update(self, value: float) -> Tuple[float, float, float]: ...

class IncrementalStochastic:

    def __init__(self, k_period: int = 14, d_period: int = 3) -> None: ...
    def update(self, high: float, low: float, close: float) -> Tuple[float, float]: ...

class IncrementalSuperTrend:

    def __init__(self, period: int = 10, multiplier: float = 3.0) -> None: ...
    def update(self, high: float, low: float, close: float) -> Tuple[float, int]: ...

class IncrementalAdaptiveRSI:

    def __init__(
        self,
        *,
        base_period: int = 14,
        min_period: int = 7,
        max_period: int = 28,
        volatility_window: int = 14,
    ) -> None: ...

class IncrementalEnsembleSignal:

    def __init__(self, *, weights: Dict[str, float] | None = None) -> None: ...

class IncrementalMLSuperTrend:

    def __init__(
        self,
        *,
        period: int = 10,
        multiplier: float = 3.0,
        confirmation_bars: int = 2,
        use_atr_filter: bool = True,
    ) -> None: ...

class CCXTStreamProcessor:

    def __init__(self) -> None: ...
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]: ...

# ==================== Accessor Classes ====================

class TechnicalAnalysisAccessor:

    def __init__(self, df: Any) -> None: ...
    def sma(self, period: int = 20) -> Any: ...
    def ema(self, period: int = 20) -> Any: ...
    def rsi(self, period: int = 14) -> Any: ...
    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[Any, Any, Any]: ...
    def bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> Tuple[Any, Any, Any]: ...
    def atr(self, period: int = 14) -> Any: ...
    def supertrend(self, period: int = 10, multiplier: float = 3.0) -> Tuple[Any, Any]: ...
    # ... many more methods

class SeriesTechnicalAnalysisAccessor:

    def __init__(self, series: Any) -> None: ...
    def sma(self, period: int = 20) -> Any: ...
    def ema(self, period: int = 20) -> Any: ...
    def rsi(self, period: int = 14) -> Any: ...

# ==================== Moving Averages ====================

def sma(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def ema(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def wma(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def dema(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def tema(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def trima(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def kama(close: ArrayLike, period: int = 10, fast: int = 2, slow: int = 30) -> FloatList:

    ...

def zlma(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def hma(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def vwma(close: ArrayLike, volume: ArrayLike, period: int = 20) -> FloatList:

    ...

def frama(close: ArrayLike, period: int = 16) -> FloatList:

    ...

def alma(close: ArrayLike, period: int = 9, offset: float = 0.85, sigma: float = 6.0) -> FloatList:

    ...

def t3(close: ArrayLike, period: int = 5, vfactor: float = 0.7) -> FloatList:

    ...

def swma(close: ArrayLike) -> FloatList:

    ...

def vidya(close: ArrayLike, period: int = 14, cmo_period: int = 9) -> FloatList:

    ...

def rma(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def sinwma(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def pwma(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def mama(close: ArrayLike, fast_limit: float = 0.5, slow_limit: float = 0.05) -> Tuple[FloatList, FloatList]:

    ...

# ==================== Momentum Indicators ====================

def rsi(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def stochrsi(close: ArrayLike, period: int = 14, stoch_period: int = 14, k_period: int = 3, d_period: int = 3) -> Tuple[FloatList, FloatList]:

    ...

def stochastic(high: ArrayLike, low: ArrayLike, close: ArrayLike, k_period: int = 14, smooth_k: int = 3, d_period: int = 3) -> Tuple[FloatList, FloatList]:

    ...

def macd(close: ArrayLike, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[FloatList, FloatList, FloatList]:

    ...

def mom(close: ArrayLike, period: int = 10) -> FloatList:

    ...

def roc(close: ArrayLike, period: int = 10) -> FloatList:

    ...

def ppo(close: ArrayLike, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[FloatList, FloatList, FloatList]:

    ...

def cci(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 20) -> FloatList:

    ...

def williams_r(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> FloatList:

    ...

def cmf(high: ArrayLike, low: ArrayLike, close: ArrayLike, volume: ArrayLike, period: int = 20) -> FloatList:

    ...

def ultimate_oscillator(high: ArrayLike, low: ArrayLike, close: ArrayLike, short: int = 7, medium: int = 14, long: int = 28) -> FloatList:

    ...

def tsi(close: ArrayLike, long: int = 25, short: int = 13, signal: int = 13) -> Tuple[FloatList, FloatList]:

    ...

def trix(close: ArrayLike, period: int = 15, signal: int = 9) -> Tuple[FloatList, FloatList]:

    ...

def dpo(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def awesome_oscillator(high: ArrayLike, low: ArrayLike, fast: int = 5, slow: int = 34) -> FloatList:

    ...

def coppock(close: ArrayLike, wma: int = 10, roc1: int = 14, roc2: int = 11) -> FloatList:

    ...

def fisher_transform(high: ArrayLike, low: ArrayLike, period: int = 9) -> Tuple[FloatList, FloatList]:

    ...

def pgo(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> FloatList:

    ...

def inertia(close: ArrayLike, high: ArrayLike, low: ArrayLike, rvi_period: int = 20, regression_period: int = 14) -> FloatList:

    ...

def cmo(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def kdj(high: ArrayLike, low: ArrayLike, close: ArrayLike, k_period: int = 9, smooth_k: int = 3, d_period: int = 3) -> Tuple[FloatList, FloatList, FloatList]:

    ...

def kst(close: ArrayLike, roc1: int = 10, roc2: int = 15, roc3: int = 20, roc4: int = 30, sma1: int = 10, sma2: int = 10, sma3: int = 10, sma4: int = 15, signal: int = 9) -> Tuple[FloatList, FloatList]:

    ...

def smi(high: ArrayLike, low: ArrayLike, close: ArrayLike, k_period: int = 5, d_period: int = 3) -> Tuple[FloatList, FloatList]:

    ...

def qqe(close: ArrayLike, rsi_period: int = 14, sf: int = 5, threshold: float = 4.236) -> Tuple[FloatList, FloatList, FloatList]:

    ...

def rvi(close: ArrayLike, high: ArrayLike, low: ArrayLike, open: ArrayLike, period: int = 10) -> Tuple[FloatList, FloatList]:

    ...

def stc(close: ArrayLike, fast: int = 23, slow: int = 50, cycle: int = 10, d1: int = 3, d2: int = 3) -> FloatList:

    ...

def tdfi(close: ArrayLike, period: int = 13) -> FloatList:

    ...

def cti(close: ArrayLike, period: int = 12) -> FloatList:

    ...

def cfo(close: ArrayLike, period: int = 9) -> FloatList:

    ...

def er(close: ArrayLike, period: int = 10) -> FloatList:

    ...

def bias(close: ArrayLike, period: int = 26) -> FloatList:

    ...

def bop(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> FloatList:

    ...

# ==================== Trend Indicators ====================

def supertrend(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 10, multiplier: float = 3.0) -> Tuple[FloatList, IntList]:

    ...

def adx(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> FloatList:

    ...

def plus_di(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> FloatList:

    ...

def minus_di(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> FloatList:

    ...

def dx(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> FloatList:

    ...

def aroon(high: ArrayLike, low: ArrayLike, period: int = 25) -> Tuple[FloatList, FloatList, FloatList]:

    ...

def vortex(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> Tuple[FloatList, FloatList]:

    ...

def psar(high: ArrayLike, low: ArrayLike, af: float = 0.02, max_af: float = 0.2) -> FloatList:

    ...

def sar(high: ArrayLike, low: ArrayLike, af: float = 0.02, max_af: float = 0.2) -> FloatList:

    ...

def sarext(high: ArrayLike, low: ArrayLike, start_value: float = 0.0, offset_on_reverse: float = 0.0, af_init: float = 0.02, af_step: float = 0.02, af_max: float = 0.2) -> FloatList:

    ...

def linear_regression(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def linearreg(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def linearreg_slope(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def linearreg_intercept(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def linearreg_angle(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def tsf(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def vhf(close: ArrayLike, period: int = 28) -> FloatList:

    ...

def qstick(open: ArrayLike, close: ArrayLike, period: int = 14) -> FloatList:

    ...

def slope(close: ArrayLike, period: int = 1) -> FloatList:

    ...

def ichimoku_cloud(high: ArrayLike, low: ArrayLike, close: ArrayLike, tenkan: int = 9, kijun: int = 26, senkou: int = 52) -> Tuple[FloatList, FloatList, FloatList, FloatList, FloatList]:

    ...

def ichimoku_signals(close: ArrayLike, tenkan_sen: ArrayLike, kijun_sen: ArrayLike, senkou_span_a: ArrayLike, senkou_span_b: ArrayLike, chikou_span: ArrayLike) -> IntList:

    ...

def ichimoku_tk_cross(tenkan_sen: ArrayLike, kijun_sen: ArrayLike, senkou_span_a: ArrayLike, senkou_span_b: ArrayLike, chikou_span: ArrayLike) -> FloatList:

    ...

def cloud_thickness(tenkan_sen: ArrayLike, kijun_sen: ArrayLike, senkou_span_a: ArrayLike, senkou_span_b: ArrayLike, chikou_span: ArrayLike) -> FloatList:

    ...

def cloud_color(tenkan_sen: ArrayLike, kijun_sen: ArrayLike, senkou_span_a: ArrayLike, senkou_span_b: ArrayLike, chikou_span: ArrayLike) -> FloatList:

    ...

def alligator(close: ArrayLike, jaw: int = 13, teeth: int = 8, lips: int = 5, jaw_offset: int = 8, teeth_offset: int = 5, lips_offset: int = 3) -> Tuple[FloatList, FloatList, FloatList]:

    ...

def ssl_channel(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 10) -> Tuple[FloatList, FloatList]:

    ...

def choppiness(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> FloatList:

    ...

def dynamic_macd(
    open: ArrayLike,
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    fast_length: int = 12,
    slow_length: int = 26,
    signal_smooth: int = 9,
) -> Tuple[FloatList, FloatList, FloatList, FloatList, FloatList]:

    ...

def ml_supertrend(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 10, multiplier: float = 3.0, confirmation_bars: int = 2, use_atr_filter: bool = True) -> Tuple[FloatList, FloatList, FloatList]:

    ...

def adaptive_rsi(close: ArrayLike, base_period: int = 14, min_period: int = 7, max_period: int = 28, volatility_window: int = 14) -> Tuple[FloatList, IntList]:

    ...

# ==================== Volatility Indicators ====================

def true_range(high: ArrayLike, low: ArrayLike, close: ArrayLike) -> FloatList:

    ...

def atr(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> FloatList:

    ...

def natr(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> FloatList:

    ...

def bollinger_bands(close: ArrayLike, period: int = 20, std_dev: float = 2.0) -> Tuple[FloatList, FloatList, FloatList]:

    ...

def keltner_channel(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 20, atr_period: int | None = None, multiplier: float = 2.0) -> Tuple[FloatList, FloatList, FloatList]:

    ...

def donchian_channel(high: ArrayLike, low: ArrayLike, period: int = 20) -> Tuple[FloatList, FloatList, FloatList]:

    ...

def chandelier_exit(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 22, multiplier: float = 3.0) -> Tuple[FloatList, FloatList]:

    ...

def historical_volatility(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def ulcer_index(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def mass_index(high: ArrayLike, low: ArrayLike, fast: int = 9, slow: int = 25) -> FloatList:

    ...

def squeeze(close: ArrayLike, high: ArrayLike, low: ArrayLike, bb_period: int = 20, bb_mult: float = 2.0, kc_period: int = 20, kc_mult: float = 1.5) -> Tuple[FloatList, IntList]:

    ...

def aberration(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 5, atr_period: int = 14) -> Tuple[FloatList, FloatList, FloatList, FloatList]:

    ...

# ==================== Volume Indicators ====================

def obv(close: ArrayLike, volume: ArrayLike) -> FloatList:

    ...

def vwap(high: ArrayLike, low: ArrayLike, close: ArrayLike, volume: ArrayLike) -> FloatList:

    ...

def ad(high: ArrayLike, low: ArrayLike, close: ArrayLike, volume: ArrayLike) -> FloatList:

    ...

def adosc(high: ArrayLike, low: ArrayLike, close: ArrayLike, volume: ArrayLike, fast: int = 3, slow: int = 10) -> FloatList:

    ...

def mfi(high: ArrayLike, low: ArrayLike, close: ArrayLike, volume: ArrayLike, period: int = 14) -> FloatList:

    ...

def pvt(close: ArrayLike, volume: ArrayLike) -> FloatList:

    ...

def nvi(close: ArrayLike, volume: ArrayLike) -> FloatList:

    ...

def pvi(close: ArrayLike, volume: ArrayLike) -> FloatList:

    ...

def eom(high: ArrayLike, low: ArrayLike, volume: ArrayLike, period: int = 14, divisor: float = 10000.0) -> FloatList:

    ...

def force_index(close: ArrayLike, volume: ArrayLike, period: int = 13) -> FloatList:

    ...

def efi(close: ArrayLike, volume: ArrayLike, period: int = 13) -> FloatList:

    ...

def volume_oscillator(volume: ArrayLike, fast: int = 5, slow: int = 10) -> FloatList:

    ...

def volume_profile(high: ArrayLike, low: ArrayLike, close: ArrayLike, volume: ArrayLike, bins: int = 12) -> Dict[str, Any]:

    ...

def volume_filter(close: ArrayLike, volume: ArrayLike, period: int = 14) -> FloatList:

    ...

def wae(close: ArrayLike, volume: ArrayLike, sensitivity: float = 150.0, fast: int = 20, slow: int = 40, bb_period: int = 20, bb_mult: float = 2.0) -> Tuple[FloatList, FloatList, FloatList, FloatList]:

    ...

# ==================== Statistical Functions ====================

def correl(x: ArrayLike, y: ArrayLike, period: int = 20) -> FloatList:

    ...

def correlation(x: ArrayLike, y: ArrayLike, period: int = 20) -> FloatList:

    ...

def covariance(x: ArrayLike, y: ArrayLike, period: int = 20) -> FloatList:

    ...

def beta(close: ArrayLike, benchmark: ArrayLike, period: int = 20) -> FloatList:

    ...

def var(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def zscore(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def percent_rank(close: ArrayLike, period: int = 20) -> FloatList:

    ...

def entropy(close: ArrayLike, period: int = 10) -> FloatList:

    ...

def standard_error(close: ArrayLike, period: int = 21) -> FloatList:

    ...

# ==================== Math Functions ====================

def abs(x: ArrayLike) -> FloatList:

    ...

def acos(x: ArrayLike) -> FloatList:

    ...

def asin(x: ArrayLike) -> FloatList:

    ...

def atan(x: ArrayLike) -> FloatList:

    ...

def ceil(x: ArrayLike) -> FloatList:

    ...

def cos(x: ArrayLike) -> FloatList:

    ...

def cosh(x: ArrayLike) -> FloatList:

    ...

def exp(x: ArrayLike) -> FloatList:

    ...

def floor(x: ArrayLike) -> FloatList:

    ...

def ln(x: ArrayLike) -> FloatList:

    ...

def log10(x: ArrayLike) -> FloatList:

    ...

def sin(x: ArrayLike) -> FloatList:

    ...

def sinh(x: ArrayLike) -> FloatList:

    ...

def sqrt(x: ArrayLike) -> FloatList:

    ...

def tan(x: ArrayLike) -> FloatList:

    ...

def tanh(x: ArrayLike) -> FloatList:

    ...

def add(x: ArrayLike, y: ArrayLike) -> FloatList:

    ...

def sub(x: ArrayLike, y: ArrayLike) -> FloatList:

    ...

def mult(x: ArrayLike, y: ArrayLike) -> FloatList:

    ...

def div(x: ArrayLike, y: ArrayLike) -> FloatList:

    ...

def max(x: ArrayLike, period: int = 30) -> FloatList:

    ...

def min(x: ArrayLike, period: int = 30) -> FloatList:

    ...

def sum(x: ArrayLike, period: int = 30) -> FloatList:

    ...

def minmax(x: ArrayLike, period: int = 30) -> Tuple[FloatList, FloatList]:

    ...

def minmaxindex(x: ArrayLike, period: int = 30) -> Tuple[IntList, IntList]:

    ...

# ==================== Price Transform ====================

def avgprice(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> FloatList:

    ...

def medprice(high: ArrayLike, low: ArrayLike) -> FloatList:

    ...

def typprice(high: ArrayLike, low: ArrayLike, close: ArrayLike) -> FloatList:

    ...

def wclprice(high: ArrayLike, low: ArrayLike, close: ArrayLike) -> FloatList:

    ...

def midpoint(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def midprice(high: ArrayLike, low: ArrayLike, period: int = 14) -> FloatList:

    ...

# ==================== Hilbert Transform ====================

def ht_dcperiod(close: ArrayLike) -> FloatList:

    ...

def ht_dcphase(close: ArrayLike) -> FloatList:

    ...

def ht_phasor(close: ArrayLike) -> Tuple[FloatList, FloatList]:

    ...

def ht_sine(close: ArrayLike) -> Tuple[FloatList, FloatList]:

    ...

def ht_trendmode(close: ArrayLike) -> IntList:

    ...

# ==================== Pivot Points ====================

def standard_pivots(high: ArrayLike, low: ArrayLike, close: ArrayLike) -> Tuple[FloatList, FloatList, FloatList, FloatList, FloatList]:

    ...

def fibonacci_pivots(high: ArrayLike, low: ArrayLike, close: ArrayLike) -> Tuple[FloatList, FloatList, FloatList, FloatList, FloatList, FloatList, FloatList]:

    ...

def camarilla_pivots(high: ArrayLike, low: ArrayLike, close: ArrayLike) -> Tuple[FloatList, FloatList, FloatList, FloatList, FloatList, FloatList, FloatList, FloatList, FloatList]:

    ...

def woodie_pivots(high: ArrayLike, low: ArrayLike, close: ArrayLike) -> Tuple[FloatList, FloatList, FloatList, FloatList, FloatList, FloatList, FloatList]:

    ...

def demark_pivots(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> Tuple[FloatList, FloatList, FloatList, FloatList, FloatList, FloatList, FloatList]:

    ...

def calc_pivot_series(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike, method: str) -> List[Tuple[float, float, float, float, float, float, float, float, float]]:

    ...

def detect_pivot_touch(current_price: float, levels: Tuple[float, float, float, float, float, float, float, float, float], tolerance: float = 0.001) -> Optional[str]:

    ...

def pivot_zone(current_price: float, levels: Tuple[float, float, float, float, float, float, float, float, float]) -> str:

    ...

def fib_retracement(high: float, low: float) -> Dict[str, float]:

    ...

def fib_extension(high: float, low: float, retracement: float) -> Dict[str, float]:

    ...

def dynamic_fib_retracement(prices: ArrayLike, lookback: int = 20) -> List[Dict[str, float]]:

    ...

def detect_fib_touch(current_price: float, levels: List[Tuple[str, float]], tolerance: float = 0.001) -> Optional[str]:

    ...

def fib_fan_lines(start_index: int, end_index: int, start_price: float, end_price: float, target_index: int) -> Tuple[float, float, float]:

    ...

def fib_time_zones(start_index: int, max_zones: int) -> List[int]:

    ...

# ==================== Candlestick Patterns ====================

def doji(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def doji_star(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def dragonfly_doji(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def gravestone_doji(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def long_legged_doji(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def hammer(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def inverted_hammer(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def hanging_man(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def shooting_star(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def bullish_engulfing(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def bearish_engulfing(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def bullish_harami(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def bearish_harami(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def harami_cross(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def morning_star(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def morning_doji_star(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def evening_star(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def evening_doji_star(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def three_white_soldiers(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def three_black_crows(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def dark_cloud_cover(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def piercing_pattern(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def spinning_top(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def marubozu(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def closing_marubozu(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def tweezers_top(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def tweezers_bottom(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def rising_three_methods(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def falling_three_methods(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def three_inside(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def three_outside(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def long_line(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def short_line(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def highwave(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def rickshaw_man(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def takuri(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def belthold(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def kicking(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def counterattack(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def separating_lines(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def thrusting(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def inneck(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def onneck(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def abandoned_baby(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def advance_block(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def breakaway(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def concealing_baby_swallow(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def gap_sidesidewhite(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def hikkake(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def hikkake_mod(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def homing_pigeon(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def identical_three_crows(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def ladder_bottom(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def matching_low(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def mat_hold(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def stalled_pattern(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def stick_sandwich(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def tristar(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def unique_3_river(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def upside_gap_two_crows(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

def xside_gap_3_methods(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

# ==================== AI/ML Indicators ====================

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
) -> Tuple[FloatList, FloatList]:

    ...

def ai_supertrend_ml(
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    st_length: int = 10,
    st_multiplier: float = 3.0,
    model_type: str = "linreg",
    lookback: int = 10,
    train_window: int = 200,
) -> Tuple[FloatList, FloatList, FloatList, FloatList, FloatList, FloatList]:

    ...

def ai_momentum_index(
    close: ArrayLike,
    k: int = 50,
    trend_length: int = 14,
    smooth: int = 3,
) -> Tuple[FloatList, FloatList]:

    ...

def ai_momentum_index_ml(
    close: ArrayLike,
    rsi_period: int = 14,
    smooth_period: int = 3,
    use_polynomial: bool = False,
    lookback: int = 5,
    train_window: int = 200,
) -> Tuple[FloatList, FloatList, FloatList, FloatList, FloatList, FloatList]:

    ...

def ensemble_signal(high: ArrayLike, low: ArrayLike, close: ArrayLike, volume: Optional[ArrayLike] = None, *, weights: Optional[Mapping[str, float]] = None) -> Tuple[FloatList, Dict[str, FloatList]]:

    ...

def detect_divergence(close: ArrayLike, indicator: ArrayLike, lookback: int = 14) -> IntList:

    ...

# ==================== Trading Signals ====================

def pivot_buy_sell(high: ArrayLike, low: ArrayLike, close: ArrayLike, lookback: int = 5) -> Tuple[FloatList, FloatList, FloatList, FloatList, FloatList, FloatList, FloatList]:

    ...

def combine_signals(buy1: ArrayLike, sell1: ArrayLike, buy2: ArrayLike, sell2: ArrayLike, weight1: Optional[float] = None) -> Tuple[FloatList, FloatList, FloatList]:

    ...

def calculate_stops(close: ArrayLike, atr_values: ArrayLike, buy_signals: ArrayLike, sell_signals: ArrayLike, sl_multiplier: float = 1.5, tp_multiplier: float = 2.5) -> Tuple[FloatList, FloatList]:

    ...

def trailing_stop(close: ArrayLike, atr_values: ArrayLike, direction: ArrayLike, multiplier: float = 2.0) -> FloatList:

    ...

def atr2_signals(
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    volume: ArrayLike,
    trend_length: int = 14,
    confirmation_threshold: float = 2.0,
    momentum_window: int = 10,
) -> Tuple[FloatList, FloatList, FloatList]:

    ...

def atr2_signals_ml(
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    volume: ArrayLike,
    rsi_period: int = 14,
    atr_period: int = 14,
    ridge_alpha: float = 1.0,
    momentum_window: int = 10,
) -> Tuple[FloatList, FloatList, FloatList, FloatList, FloatList, FloatList]:

    ...

def fvg_signals(open: ArrayLike, high: ArrayLike, low: ArrayLike, close: ArrayLike) -> IntList:

    ...

# ==================== Real-time Functions ====================

def realtime_rsi(close: ArrayLike, period: int = 14) -> FloatList:

    ...

def realtime_supertrend(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 10, multiplier: float = 3.0) -> Tuple[FloatList, IntList]:

    ...

def realtime_multi_indicator(high: ArrayLike, low: ArrayLike, close: ArrayLike, volume: ArrayLike) -> Dict[str, FloatList]:

    ...

def get_available_streaming_indicators() -> List[str]:

    ...

def create_indicator(name: str, **kwargs: Any) -> Any:

    ...
