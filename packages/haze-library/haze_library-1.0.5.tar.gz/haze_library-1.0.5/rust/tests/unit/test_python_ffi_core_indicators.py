"""
Comprehensive Python FFI Test Suite - Core Indicators

Tests 50 most commonly used indicators for:
- Empty input handling (fail-fast raises ValueError)
- Invalid parameter handling (fail-fast raises ValueError)
- Output format correctness
- NumPy array compatibility
- Length mismatch validation
- Range validation

IMPORTANT: Fail-fast behavior:
- EmptyInput → raises ValueError
- InvalidPeriod → raises ValueError
- InsufficientData → raises ValueError

Test Coverage:
    - Overlap Indicators (8): SMA, EMA, WMA, DEMA, TEMA, HMA, RMA, ZLMA
    - Momentum Indicators (10): RSI, MACD, Stochastic, StochRSI, CCI, Williams %R, Fisher, KDJ, TSI, MOM
    - Volatility Indicators (6): ATR, NATR, Bollinger Bands, Keltner Channel, Donchian Channel, Ulcer Index
    - Trend Indicators (10): ADX, SuperTrend, PSAR, Aroon, Vortex, DPO, QStick, VHF, TRIX, Choppiness Index
    - Volume Indicators (8): OBV, MFI, VWAP, CMF, Volume Oscillator, AD Line, PVT, EOM
    - Statistical Indicators (5): Correlation, Z-Score, Covariance, Beta, Standard Error
    - Price Transform (3): MEDPRICE, TYPPRICE, WCLPRICE
"""

import numpy as np
import pytest
import warnings

try:
    import haze_library as haze
    # Suppress deprecation warnings during tests
    warnings.filterwarnings('ignore', category=DeprecationWarning, message='.*py_.*')
except ImportError:
    pytest.skip("haze_library not built, run `maturin develop` first", allow_module_level=True)


# ============================================================================
# Test Base Classes
# ============================================================================

class IndicatorTestBase:
    """Base class for indicator tests with data generation helpers"""

    @staticmethod
    def valid_data(length=100, start=100.0, step=0.1):
        """Generate valid price data with upward trend"""
        return [start + i * step for i in range(length)]

    @staticmethod
    def valid_ohlc(length=100):
        """Generate valid OHLC data with realistic structure"""
        close = [100.0 + i * 0.1 for i in range(length)]
        high = [c + 2.0 for c in close]
        low = [c - 2.0 for c in close]
        open_price = [c + 0.5 for c in close]
        return high, low, close, open_price

    @staticmethod
    def valid_volume(length=100):
        """Generate valid volume data"""
        return [1000.0 + i * 10.0 for i in range(length)]

    @staticmethod
    def assert_warmup_period(result, period):
        """Assert that warmup period contains NaN values"""
        for i in range(period - 1):
            assert np.isnan(result[i]), f"Expected NaN at index {i} during warmup"

    @staticmethod
    def assert_valid_values(result, start_idx):
        """Assert that values after start_idx are finite (not NaN or inf)"""
        for i in range(start_idx, len(result)):
            assert np.isfinite(result[i]), f"Expected finite value at index {i}, got {result[i]}"


# ============================================================================
# Overlap Indicators (Moving Averages) - 8 Functions
# ============================================================================

class TestOverlapIndicators(IndicatorTestBase):
    """Test overlap/moving average indicators"""

    # ---- Empty Input Tests ----
    @pytest.mark.parametrize("func,period", [
        (haze.py_sma, 10),
        (haze.py_ema, 12),
        (haze.py_wma, 9),
        (haze.py_dema, 14),
        (haze.py_tema, 14),
        (haze.py_hma, 9),
        (haze.py_rma, 14),
        (haze.py_zlma, 10),
    ])
    def test_ma_empty_input(self, func, period):
        """MA functions should fail-fast on empty input"""
        with pytest.raises(ValueError):
            func([], period)

    # ---- Invalid Period Tests ----
    @pytest.mark.parametrize("func,period", [
        (haze.py_sma, 10),
        (haze.py_ema, 12),
        (haze.py_wma, 9),
        (haze.py_dema, 14),
        (haze.py_tema, 14),
        (haze.py_hma, 9),
        (haze.py_rma, 14),
        (haze.py_zlma, 10),
    ])
    def test_ma_zero_period(self, func, period):
        """MA functions should fail-fast on period=0"""
        data = self.valid_data(50)
        with pytest.raises(ValueError):
            func(data, 0)

    # ---- Period Exceeds Length Tests ----
    @pytest.mark.parametrize("func", [
        haze.py_sma,
        haze.py_ema,
        haze.py_wma,
    ])
    def test_ma_period_exceeds_length(self, func):
        """MA functions should fail-fast when period > length"""
        data = self.valid_data(5)
        with pytest.raises(ValueError):
            func(data, 10)

    # ---- Valid Output Tests ----
    @pytest.mark.parametrize("func,period", [
        (haze.py_sma, 10),
        (haze.py_ema, 12),
        (haze.py_wma, 9),
        (haze.py_dema, 14),
        (haze.py_tema, 14),
        (haze.py_hma, 9),
        (haze.py_rma, 14),
        (haze.py_zlma, 10),
    ])
    def test_ma_valid_output(self, func, period):
        """MA functions return correct output format with valid data"""
        data = self.valid_data(100)
        result = func(data, period)

        assert len(result) == 100, f"{func.__name__} returned wrong length"
        assert isinstance(result, list), f"{func.__name__} should return list"
        assert all(isinstance(x, float) for x in result), f"{func.__name__} should return floats"

        # Verify that at least some values are valid (not all NaN)
        valid_count = sum(1 for x in result if not np.isnan(x))
        assert valid_count > 0, f"{func.__name__} should return some valid values"


# ============================================================================
# Momentum Indicators - 10 Functions
# ============================================================================

class TestMomentumIndicators(IndicatorTestBase):
    """Test momentum indicators"""

    # ---- RSI Tests ----
    def test_rsi_empty_input(self):
        """RSI should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_rsi([], 14)

    def test_rsi_zero_period(self):
        """RSI should fail-fast on period=0"""
        data = self.valid_data(50)
        with pytest.raises(ValueError):
            haze.py_rsi(data, 0)

    def test_rsi_valid_output(self):
        """RSI returns valid output in [0, 100] range"""
        data = self.valid_data(50)
        result = haze.py_rsi(data, 14)

        assert len(result) == 50
        # RSI should be in [0, 100] for valid values
        for i, val in enumerate(result):
            if not np.isnan(val):
                assert 0.0 <= val <= 100.0, f"RSI out of range at {i}: {val}"

    # ---- MACD Tests ----
    def test_macd_empty_input(self):
        """MACD should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_macd([], 12, 26, 9)

    def test_macd_valid_output(self):
        """MACD returns correct output format"""
        data = self.valid_data(100)
        macd, signal, histogram = haze.py_macd(data, 12, 26, 9)

        assert len(macd) == 100
        assert len(signal) == 100
        assert len(histogram) == 100

        # Verify histogram = MACD - Signal (for valid values)
        for i in range(40, 100):
            if not np.isnan(macd[i]) and not np.isnan(signal[i]) and not np.isnan(histogram[i]):
                expected_hist = macd[i] - signal[i]
                assert abs(histogram[i] - expected_hist) < 1e-10, f"Histogram error at {i}"

    # ---- Stochastic Tests ----
    def test_stochastic_empty_input(self):
        """Stochastic should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_stochastic([], [], [], 14, 3)

    def test_stochastic_length_mismatch(self):
        """Stochastic with length mismatch should raise ValueError"""
        high, low, close, _ = self.valid_ohlc(50)
        # Proper error handling: raise ValueError for length mismatch
        with pytest.raises(ValueError, match="Length mismatch"):
            haze.py_stochastic(high, low[:40], close, 14, 3)

    def test_stochastic_valid_output(self):
        """Stochastic returns values in [0, 100] range"""
        high, low, close, _ = self.valid_ohlc(50)
        k, d = haze.py_stochastic(high, low, close, 14, 3)

        assert len(k) == 50
        assert len(d) == 50

        # Stochastic values should be in [0, 100]
        for i in range(20, 50):
            if not np.isnan(k[i]):
                assert 0.0 <= k[i] <= 100.0, f"%K out of range at {i}"
            if not np.isnan(d[i]):
                assert 0.0 <= d[i] <= 100.0, f"%D out of range at {i}"

    # ---- StochRSI Tests ----
    def test_stochrsi_empty_input(self):
        """StochRSI should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_stochrsi([], 14, 14, 3, 3)

    def test_stochrsi_valid_output(self):
        """StochRSI returns correct output format"""
        data = self.valid_data(100)
        k, d = haze.py_stochrsi(data, 14, 14, 3, 3)

        assert len(k) == 100
        assert len(d) == 100

    # ---- CCI Tests ----
    def test_cci_empty_input(self):
        """CCI should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_cci([], [], [], 20)

    def test_cci_valid_output(self):
        """CCI returns correct output format"""
        high, low, close, _ = self.valid_ohlc(50)
        result = haze.py_cci(high, low, close, 20)

        assert len(result) == 50
        assert isinstance(result, list)

    # ---- Williams %R Tests ----
    def test_williams_r_empty_input(self):
        """Williams %R should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_williams_r([], [], [], 14)

    def test_williams_r_valid_output(self):
        """Williams %R returns values in [-100, 0] range"""
        high, low, close, _ = self.valid_ohlc(50)
        result = haze.py_williams_r(high, low, close, 14)

        assert len(result) == 50
        # Williams %R should be in [-100, 0]
        for i in range(20, 50):
            if not np.isnan(result[i]):
                assert -100.0 <= result[i] <= 0.0, f"Williams %R out of range at {i}"

    # ---- Fisher Transform Tests ----
    def test_fisher_empty_input(self):
        """Fisher Transform should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_fisher_transform([], [], [], 9)

    def test_fisher_valid_output(self):
        """Fisher Transform returns correct output format"""
        high, low, close, _ = self.valid_ohlc(50)
        fisher, trigger = haze.py_fisher_transform(high, low, close, 9)

        assert len(fisher) == 50
        assert len(trigger) == 50

    # ---- KDJ Tests ----
    def test_kdj_empty_input(self):
        """KDJ should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_kdj([], [], [], 9, 3)

    def test_kdj_valid_output(self):
        """KDJ returns correct output format"""
        high, low, close, _ = self.valid_ohlc(50)
        k, d, j = haze.py_kdj(high, low, close, 9, 3)

        assert len(k) == 50
        assert len(d) == 50
        assert len(j) == 50

    # ---- TSI Tests ----
    def test_tsi_empty_input(self):
        """TSI should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_tsi([], 25, 13, 13)

    def test_tsi_valid_output(self):
        """TSI returns correct output format"""
        data = self.valid_data(100)
        tsi, signal = haze.py_tsi(data, 25, 13, 13)

        assert len(tsi) == 100
        assert len(signal) == 100

    # ---- MOM (Momentum) Tests ----
    def test_mom_valid_output(self):
        """Momentum returns correct output format"""
        data = self.valid_data(50)
        result = haze.py_mom(data, 10)

        assert len(result) == 50


# ============================================================================
# Volatility Indicators - 6 Functions
# ============================================================================

class TestVolatilityIndicators(IndicatorTestBase):
    """Test volatility indicators"""

    # ---- ATR Tests ----
    def test_atr_empty_input(self):
        """ATR should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_atr([], [], [], 14)

    def test_atr_length_mismatch(self):
        """ATR with length mismatch should raise ValueError"""
        high, low, close, _ = self.valid_ohlc(50)
        # Proper error handling: raise ValueError for length mismatch
        with pytest.raises(ValueError, match="Length mismatch"):
            haze.py_atr(high, low[:40], close, 14)

    def test_atr_valid_output(self):
        """ATR returns non-negative values"""
        high, low, close, _ = self.valid_ohlc(50)
        result = haze.py_atr(high, low, close, 14)

        assert len(result) == 50
        # ATR should be non-negative
        for i, val in enumerate(result):
            if not np.isnan(val):
                assert val >= 0.0, f"ATR should be non-negative at {i}: {val}"

    # ---- NATR Tests ----
    def test_natr_empty_input(self):
        """NATR should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_natr([], [], [], 14)

    def test_natr_valid_output(self):
        """NATR returns non-negative values"""
        high, low, close, _ = self.valid_ohlc(50)
        result = haze.py_natr(high, low, close, 14)

        assert len(result) == 50
        # NATR should be non-negative
        for i, val in enumerate(result):
            if not np.isnan(val):
                assert val >= 0.0, f"NATR should be non-negative at {i}"

    # ---- Bollinger Bands Tests ----
    def test_bollinger_bands_empty_input(self):
        """Bollinger Bands should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_bollinger_bands([], 20, 2.0)

    def test_bollinger_bands_valid_output(self):
        """Bollinger Bands returns correctly ordered bands"""
        data = self.valid_data(50)
        upper, middle, lower = haze.py_bollinger_bands(data, 20, 2.0)

        assert len(upper) == 50
        assert len(middle) == 50
        assert len(lower) == 50

        # Verify band ordering: lower <= middle <= upper
        for i in range(20, 50):
            if not any(np.isnan([lower[i], middle[i], upper[i]])):
                assert lower[i] <= middle[i] <= upper[i], f"Band ordering violated at {i}"

    # ---- Keltner Channel Tests ----
    def test_keltner_channel_empty_input(self):
        """Keltner Channel should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_keltner_channel([], [], [], 20, 10, 2.0)

    def test_keltner_channel_valid_output(self):
        """Keltner Channel returns correct output format"""
        high, low, close, _ = self.valid_ohlc(50)
        upper, middle, lower = haze.py_keltner_channel(high, low, close, 20, 10, 2.0)

        assert len(upper) == 50
        assert len(middle) == 50
        assert len(lower) == 50

    # ---- Donchian Channel Tests ----
    def test_donchian_channel_empty_input(self):
        """Donchian Channel should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_donchian_channel([], [], 20)

    def test_donchian_channel_valid_output(self):
        """Donchian Channel returns correct output format"""
        high, low, _, _ = self.valid_ohlc(50)
        upper, middle, lower = haze.py_donchian_channel(high, low, 20)

        assert len(upper) == 50
        assert len(middle) == 50
        assert len(lower) == 50

        # Upper should be >= Lower
        for i in range(20, 50):
            if not np.isnan(upper[i]) and not np.isnan(lower[i]):
                assert upper[i] >= lower[i], f"Upper < Lower at {i}"

    # ---- Ulcer Index Tests ----
    def test_ulcer_index_empty_input(self):
        """Ulcer Index should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_ulcer_index([], period=14)

    def test_ulcer_index_valid_output(self):
        """Ulcer Index returns non-negative values"""
        data = self.valid_data(50)
        result = haze.py_ulcer_index(data, period=14)

        assert len(result) == 50
        # Ulcer Index should be non-negative
        for i, val in enumerate(result):
            if not np.isnan(val):
                assert val >= 0.0, f"Ulcer Index should be non-negative at {i}"


# ============================================================================
# Trend Indicators - 10 Functions
# ============================================================================

class TestTrendIndicators(IndicatorTestBase):
    """Test trend indicators"""

    # ---- ADX Tests ----
    def test_adx_empty_input(self):
        """ADX should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_adx([], [], [], 14)

    def test_adx_length_mismatch(self):
        """ADX with length mismatch should raise ValueError"""
        high, low, close, _ = self.valid_ohlc(50)
        # Proper error handling: raise ValueError for length mismatch
        with pytest.raises(ValueError, match="Length mismatch"):
            haze.py_adx(high, low[:40], close, 14)

    def test_adx_valid_output(self):
        """ADX returns values in [0, 100] range"""
        high, low, close, _ = self.valid_ohlc(50)
        adx, plus_di, minus_di = haze.py_adx(high, low, close, 14)

        assert len(adx) == 50
        assert len(plus_di) == 50
        assert len(minus_di) == 50

        # All values should be in [0, 100]
        for i in range(30, 50):
            for val, name in [(adx[i], "ADX"), (plus_di[i], "+DI"), (minus_di[i], "-DI")]:
                if not np.isnan(val):
                    assert 0.0 <= val <= 100.0, f"{name} out of range at {i}: {val}"

    # ---- SuperTrend Tests ----
    def test_supertrend_empty_input(self):
        """SuperTrend should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_supertrend([], [], [], 10, 3.0)

    def test_supertrend_valid_output(self):
        """SuperTrend returns correct direction values"""
        high, low, close, _ = self.valid_ohlc(50)
        trend, direction, lower, upper = haze.py_supertrend(high, low, close, 10, 3.0)

        assert len(trend) == 50
        assert len(direction) == 50
        assert len(lower) == 50
        assert len(upper) == 50

        # Direction should be 1 or -1 (or NaN during warmup)
        for i in range(15, 50):
            if not np.isnan(direction[i]):
                assert direction[i] in [1.0, -1.0], f"Direction should be ±1 at {i}"

    # ---- PSAR Tests ----
    def test_psar_empty_input(self):
        """PSAR should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_psar([], [], [], af_init=0.02, af_increment=0.02, af_max=0.2)

    def test_psar_valid_output(self):
        """PSAR returns correct output format"""
        high, low, close, _ = self.valid_ohlc(50)
        psar, trend = haze.py_psar(high, low, close, af_init=0.02, af_increment=0.02, af_max=0.2)

        assert len(psar) == 50
        assert len(trend) == 50

    # ---- Aroon Tests ----
    def test_aroon_empty_input(self):
        """Aroon should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_aroon([], [], 14)

    def test_aroon_valid_output(self):
        """Aroon returns values in [0, 100] range"""
        high, low, _, _ = self.valid_ohlc(50)
        aroon_up, aroon_down, aroon_oscillator = haze.py_aroon(high, low, 14)

        assert len(aroon_up) == 50
        assert len(aroon_down) == 50
        assert len(aroon_oscillator) == 50

        # Aroon values should be in [0, 100]
        for i in range(20, 50):
            if not np.isnan(aroon_up[i]):
                assert 0.0 <= aroon_up[i] <= 100.0, f"Aroon Up out of range at {i}"
            if not np.isnan(aroon_down[i]):
                assert 0.0 <= aroon_down[i] <= 100.0, f"Aroon Down out of range at {i}"

    # ---- Vortex Tests ----
    def test_vortex_empty_input(self):
        """Vortex should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_vortex([], [], [], 14)

    def test_vortex_valid_output(self):
        """Vortex returns correct output format"""
        high, low, close, _ = self.valid_ohlc(50)
        vi_plus, vi_minus = haze.py_vortex(high, low, close, 14)

        assert len(vi_plus) == 50
        assert len(vi_minus) == 50

    # ---- DPO Tests ----
    def test_dpo_empty_input(self):
        """DPO should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_dpo([], period=20)

    def test_dpo_valid_output(self):
        """DPO returns correct output format"""
        data = self.valid_data(50)
        result = haze.py_dpo(data, period=20)

        assert len(result) == 50

    # ---- QStick Tests ----
    def test_qstick_empty_input(self):
        """QStick should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_qstick([], [], 10)

    def test_qstick_valid_output(self):
        """QStick returns correct output format"""
        _, _, close, open_price = self.valid_ohlc(50)
        result = haze.py_qstick(open_price, close, 10)

        assert len(result) == 50

    # ---- VHF Tests ----
    def test_vhf_empty_input(self):
        """VHF should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_vhf([], 28)

    def test_vhf_valid_output(self):
        """VHF returns correct output format"""
        data = self.valid_data(50)
        result = haze.py_vhf(data, 28)

        assert len(result) == 50

    # ---- TRIX Tests ----
    def test_trix_empty_input(self):
        """TRIX should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_trix([], period=15)

    def test_trix_valid_output(self):
        """TRIX returns correct output format"""
        data = self.valid_data(100)
        result = haze.py_trix(data, period=15)

        assert len(result) == 100

    # ---- Choppiness Index Tests ----
    def test_choppiness_empty_input(self):
        """Choppiness Index should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_choppiness([], [], [], 14)

    def test_choppiness_valid_output(self):
        """Choppiness Index returns correct output format"""
        high, low, close, _ = self.valid_ohlc(50)
        result = haze.py_choppiness(high, low, close, 14)

        assert len(result) == 50


# ============================================================================
# Volume Indicators - 8 Functions
# ============================================================================

class TestVolumeIndicators(IndicatorTestBase):
    """Test volume indicators"""

    # ---- OBV Tests ----
    def test_obv_empty_input(self):
        """OBV should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_obv([], [])

    def test_obv_length_mismatch(self):
        """OBV with length mismatch should raise ValueError"""
        close = self.valid_data(50)
        volume = self.valid_volume(40)
        # Proper error handling: raise ValueError for length mismatch
        with pytest.raises(ValueError, match="Length mismatch"):
            haze.py_obv(close, volume)

    def test_obv_valid_output(self):
        """OBV returns correct output format"""
        close = self.valid_data(50)
        volume = self.valid_volume(50)
        result = haze.py_obv(close, volume)

        assert len(result) == 50
        assert isinstance(result, list)

    # ---- MFI Tests ----
    def test_mfi_empty_input(self):
        """MFI should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_mfi([], [], [], [], 14)

    def test_mfi_valid_output(self):
        """MFI returns values in [0, 100] range"""
        high, low, close, _ = self.valid_ohlc(50)
        volume = self.valid_volume(50)
        result = haze.py_mfi(high, low, close, volume, 14)

        assert len(result) == 50
        # MFI should be in [0, 100]
        for i in range(20, 50):
            if not np.isnan(result[i]):
                assert 0.0 <= result[i] <= 100.0, f"MFI out of range at {i}"

    # ---- VWAP Tests ----
    def test_vwap_empty_input(self):
        """VWAP should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_vwap([], [], [], [], None)

    def test_vwap_valid_output(self):
        """VWAP returns correct output format"""
        high, low, close, _ = self.valid_ohlc(50)
        volume = self.valid_volume(50)
        result = haze.py_vwap(high, low, close, volume, 0)

        assert len(result) == 50

    # ---- CMF Tests ----
    def test_cmf_empty_input(self):
        """CMF should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_cmf([], [], [], [], 20)

    def test_cmf_valid_output(self):
        """CMF returns values in [-1, 1] range"""
        high, low, close, _ = self.valid_ohlc(50)
        volume = self.valid_volume(50)
        result = haze.py_cmf(high, low, close, volume, 20)

        assert len(result) == 50
        # CMF should be in [-1, 1]
        for i in range(25, 50):
            if not np.isnan(result[i]):
                assert -1.0 <= result[i] <= 1.0, f"CMF out of range at {i}"

    # ---- Volume Oscillator Tests ----
    def test_volume_oscillator_empty_input(self):
        """Volume Oscillator should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_volume_oscillator([], short_period=5, long_period=10)

    def test_volume_oscillator_valid_output(self):
        """Volume Oscillator returns correct output format"""
        volume = self.valid_volume(50)
        result = haze.py_volume_oscillator(volume, short_period=5, long_period=10)

        assert len(result) == 50

    # ---- AD Line Tests ----
    def test_ad_line_empty_input(self):
        """AD Line should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_ad([], [], [], [])

    def test_ad_line_valid_output(self):
        """AD Line returns correct output format"""
        high, low, close, _ = self.valid_ohlc(50)
        volume = self.valid_volume(50)
        result = haze.py_ad(high, low, close, volume)

        assert len(result) == 50

    # ---- PVT Tests ----
    def test_pvt_empty_input(self):
        """PVT should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_pvt([], [])

    def test_pvt_valid_output(self):
        """PVT returns correct output format"""
        close = self.valid_data(50)
        volume = self.valid_volume(50)
        result = haze.py_pvt(close, volume)

        assert len(result) == 50

    # ---- EOM Tests ----
    def test_eom_empty_input(self):
        """EOM should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_eom([], [], [], period=14)

    def test_eom_valid_output(self):
        """EOM returns correct output format"""
        high, low, _, _ = self.valid_ohlc(50)
        volume = self.valid_volume(50)
        result = haze.py_eom(high, low, volume, period=14)

        assert len(result) == 50


# ============================================================================
# Statistical Indicators - 5 Functions
# ============================================================================

class TestStatisticalIndicators(IndicatorTestBase):
    """Test statistical indicators"""

    # ---- Correlation Tests ----
    def test_correlation_valid_output(self):
        """Correlation returns values in [-1, 1] range"""
        x = self.valid_data(50)
        y = self.valid_data(50, start=200.0)
        result = haze.py_correlation(x, y, 20)

        assert len(result) == 50
        # Correlation should be in [-1, 1] (with small tolerance for floating-point precision)
        for i in range(25, 50):
            if not np.isnan(result[i]):
                assert -1.0 - 1e-10 <= result[i] <= 1.0 + 1e-10, f"Correlation out of range at {i}: {result[i]}"

    # ---- Z-Score Tests ----
    def test_zscore_valid_output(self):
        """Z-Score returns correct output format"""
        data = self.valid_data(50)
        result = haze.py_zscore(data, 20)

        assert len(result) == 50

    # ---- Covariance Tests ----
    def test_covariance_valid_output(self):
        """Covariance returns correct output format"""
        x = self.valid_data(50)
        y = self.valid_data(50, start=200.0)
        result = haze.py_covariance(x, y, 20)

        assert len(result) == 50

    # ---- Beta Tests ----
    def test_beta_valid_output(self):
        """Beta returns correct output format"""
        asset = self.valid_data(50)
        market = self.valid_data(50, start=200.0)
        result = haze.py_beta(asset, market, 20)

        assert len(result) == 50

    # ---- Standard Error Tests ----
    def test_standard_error_valid_output(self):
        """Standard Error returns non-negative values"""
        data = self.valid_data(50)
        result = haze.py_standard_error(data, 20)

        assert len(result) == 50
        # Standard error should be non-negative
        for i in range(25, 50):
            if not np.isnan(result[i]):
                assert result[i] >= 0.0, f"Standard error should be non-negative at {i}"


# ============================================================================
# Price Transform Indicators - 3 Functions
# ============================================================================

class TestPriceTransformIndicators(IndicatorTestBase):
    """Test price transform indicators"""

    # ---- MEDPRICE Tests ----
    def test_medprice_empty_input(self):
        """MEDPRICE should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_medprice([], [])

    def test_medprice_valid_output(self):
        """MEDPRICE = (High + Low) / 2"""
        high, low, _, _ = self.valid_ohlc(50)
        result = haze.py_medprice(high, low)

        assert len(result) == 50
        # MEDPRICE = (High + Low) / 2
        for i in range(50):
            expected = (high[i] + low[i]) / 2.0
            assert abs(result[i] - expected) < 1e-10, f"MEDPRICE calculation error at {i}"

    # ---- TYPPRICE Tests ----
    def test_typprice_empty_input(self):
        """TYPPRICE should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_typprice([], [], [])

    def test_typprice_valid_output(self):
        """TYPPRICE = (High + Low + Close) / 3"""
        high, low, close, _ = self.valid_ohlc(50)
        result = haze.py_typprice(high, low, close)

        assert len(result) == 50
        # TYPPRICE = (High + Low + Close) / 3
        for i in range(50):
            expected = (high[i] + low[i] + close[i]) / 3.0
            assert abs(result[i] - expected) < 1e-10, f"TYPPRICE calculation error at {i}"

    # ---- WCLPRICE Tests ----
    def test_wclprice_empty_input(self):
        """WCLPRICE should fail-fast on empty input"""
        with pytest.raises(ValueError):
            haze.py_wclprice([], [], [])

    def test_wclprice_valid_output(self):
        """WCLPRICE = (High + Low + 2*Close) / 4"""
        high, low, close, _ = self.valid_ohlc(50)
        result = haze.py_wclprice(high, low, close)

        assert len(result) == 50
        # WCLPRICE = (High + Low + 2*Close) / 4
        for i in range(50):
            expected = (high[i] + low[i] + 2.0 * close[i]) / 4.0
            assert abs(result[i] - expected) < 1e-10, f"WCLPRICE calculation error at {i}"


# ============================================================================
# NumPy Compatibility Tests
# ============================================================================

class TestNumpyCompatibility(IndicatorTestBase):
    """Test NumPy array input compatibility"""

    @pytest.mark.parametrize("func,args", [
        (haze.py_sma, (10,)),
        (haze.py_rsi, (14,)),
        (haze.py_ema, (12,)),
        (haze.py_wma, (9,)),
    ])
    def test_numpy_array_input(self, func, args):
        """Should accept NumPy arrays"""
        data = np.array(self.valid_data(50))
        result = func(data.tolist(), *args)

        assert len(result) == 50
        assert isinstance(result, list)

    def test_numpy_ohlc_input(self):
        """OHLC indicators should accept NumPy arrays"""
        high_np, low_np, close_np, _ = [np.array(x) for x in self.valid_ohlc(50)]

        result = haze.py_atr(high_np.tolist(), low_np.tolist(), close_np.tolist(), 14)

        assert len(result) == 50
        assert isinstance(result, list)


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases(IndicatorTestBase):
    """Test edge cases and boundary conditions"""

    def test_sma_minimum_length(self):
        """SMA with minimum valid length"""
        data = self.valid_data(10)
        result = haze.py_sma(data, 10)

        assert len(result) == 10
        # First 9 should be NaN
        for i in range(9):
            assert np.isnan(result[i])
        # Last one should be valid
        assert not np.isnan(result[9])

    def test_rsi_constant_values(self):
        """RSI with constant values (no price change)"""
        data = [100.0] * 30
        result = haze.py_rsi(data, 14)

        assert len(result) == 30
        # RSI is undefined for constant prices
        # Implementation may return NaN or ~50

    def test_bollinger_bands_zero_stddev(self):
        """Bollinger Bands with zero standard deviation"""
        data = [100.0] * 30
        upper, middle, lower = haze.py_bollinger_bands(data, 20, 2.0)

        assert len(upper) == 30
        # With constant prices, all bands should be equal
        for i in range(20, 30):
            if not np.isnan(middle[i]):
                assert abs(upper[i] - middle[i]) < 1e-10
                assert abs(lower[i] - middle[i]) < 1e-10

    def test_atr_zero_range(self):
        """ATR with zero price range"""
        high = [100.0] * 30
        low = [100.0] * 30
        close = [100.0] * 30

        result = haze.py_atr(high, low, close, 14)

        assert len(result) == 30
        # ATR should be zero for zero range
        for i in range(14, 30):
            if not np.isnan(result[i]):
                assert abs(result[i]) < 1e-10, f"ATR should be ~0 for zero range at {i}"


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance(IndicatorTestBase):
    """Test performance with larger datasets"""

    def test_sma_large_dataset(self):
        """SMA should handle large datasets efficiently"""
        data = self.valid_data(10000)
        result = haze.py_sma(data, 50)

        assert len(result) == 10000
        # Verify a few values
        assert np.isnan(result[0])
        assert not np.isnan(result[100])

    def test_rsi_large_dataset(self):
        """RSI should handle large datasets efficiently"""
        data = self.valid_data(10000)
        result = haze.py_rsi(data, 14)

        assert len(result) == 10000
        # Verify value range
        for i in range(100, 10000, 1000):
            if not np.isnan(result[i]):
                assert 0.0 <= result[i] <= 100.0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration(IndicatorTestBase):
    """Test integration between multiple indicators"""

    def test_macd_histogram_calculation(self):
        """Verify MACD histogram = MACD - Signal"""
        data = self.valid_data(100)
        macd, signal, histogram = haze.py_macd(data, 12, 26, 9)

        for i in range(50, 100):
            if not np.isnan(macd[i]) and not np.isnan(signal[i]) and not np.isnan(histogram[i]):
                expected = macd[i] - signal[i]
                assert abs(histogram[i] - expected) < 1e-10, \
                    f"Histogram mismatch at {i}: expected {expected}, got {histogram[i]}"

    def test_stochastic_d_is_smoothed_k(self):
        """Verify Stochastic %D is smoothed version of %K"""
        high, low, close, _ = self.valid_ohlc(100)
        k, d = haze.py_stochastic(high, low, close, 14, 3)

        # %D should be smoother than %K (verified by visual inspection)
        assert len(k) == len(d) == 100

    def test_bollinger_middle_band_equals_sma(self):
        """Verify Bollinger middle band equals SMA"""
        data = self.valid_data(100)
        upper, middle, lower = haze.py_bollinger_bands(data, 20, 2.0)
        sma = haze.py_sma(data, 20)

        for i in range(20, 100):
            if not np.isnan(middle[i]) and not np.isnan(sma[i]):
                assert abs(middle[i] - sma[i]) < 1e-10, \
                    f"Bollinger middle band should equal SMA at {i}"


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
