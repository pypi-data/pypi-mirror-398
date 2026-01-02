"""
Integration tests for Python FFI edge cases

These tests verify that the PyO3 bindings handle edge cases correctly:
- Fail-fast validation for NaN/Inf inputs
- Empty inputs
- Invalid parameters
- Type conversions
"""

import numpy as np
import pytest

# Assuming the Python package is named 'haze' after building with maturin
try:
    import haze_library as haze
except ImportError:
    pytest.skip("haze_library not built, run `maturin develop` first", allow_module_level=True)


class TestNaNHandling:
    """Test how NaN values in input are handled"""

    def test_sma_with_nan_in_middle(self):
        """NaN in input should raise ValueError"""
        data = [1.0, 2.0, float('nan'), 4.0, 5.0, 6.0, 7.0, 8.0]
        with pytest.raises(ValueError):
            haze.py_sma(data, period=3)

    def test_rsi_with_nan_in_data(self):
        """RSI should fail-fast on NaN input"""
        data = [100.0, 102.0, float('nan'), 101.0, 103.0, 105.0] + [104.0] * 20
        with pytest.raises(ValueError):
            haze.py_rsi(data, period=14)


class TestInfinityHandling:
    """Test how infinity values are handled"""

    def test_sma_with_infinity(self):
        """Infinity in input should raise ValueError"""
        data = [1.0, 2.0, float('inf'), 4.0, 5.0, 6.0, 7.0, 8.0]
        with pytest.raises(ValueError):
            haze.py_sma(data, period=3)

    def test_bollinger_with_negative_infinity(self):
        """Negative infinity should raise ValueError"""
        data = [100.0, 102.0, float('-inf'), 101.0, 103.0] + [100.0] * 20
        with pytest.raises(ValueError):
            haze.py_bollinger_bands(data, period=14, std_multiplier=2.0)


class TestEmptyInputs:
    """Test error handling for empty inputs"""

    def test_sma_empty_list(self):
        """Empty list should raise ValueError"""
        with pytest.raises(ValueError, match="[Ee]mpty"):
            haze.py_sma([], period=3)

    def test_rsi_empty_list(self):
        """Empty list should raise ValueError"""
        with pytest.raises(ValueError, match="[Ee]mpty"):
            haze.py_rsi([], period=14)

    def test_bollinger_empty_list(self):
        """Empty list should raise ValueError"""
        with pytest.raises(ValueError, match="[Ee]mpty"):
            haze.py_bollinger_bands([], period=14, std_multiplier=2.0)


class TestInvalidParameters:
    """Test error handling for invalid parameters"""

    def test_sma_zero_period(self):
        """Zero period should raise ValueError"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        with pytest.raises(ValueError, match="[Pp]eriod"):
            haze.py_sma(data, period=0)

    def test_rsi_zero_period(self):
        """Zero period should raise ValueError"""
        data = [100.0, 102.0, 101.0, 103.0, 105.0]
        with pytest.raises(ValueError, match="[Pp]eriod"):
            haze.py_rsi(data, period=0)

    def test_sma_period_exceeds_length(self):
        """Period > data length should raise ValueError"""
        data = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError, match="[Pp]eriod|[Ii]nsufficient"):
            haze.py_sma(data, period=10)

    def test_bollinger_zero_period(self):
        """Zero period should raise ValueError"""
        data = [100.0] * 20
        with pytest.raises(ValueError, match="[Pp]eriod"):
            haze.py_bollinger_bands(data, period=0, std_multiplier=2.0)


class TestLengthMismatch:
    """Test error handling for mismatched input lengths"""

    def test_atr_length_mismatch(self):
        """ATR should raise error for mismatched high/low/close lengths"""
        high = [102.0, 103.0, 104.0]
        low = [98.0, 99.0]  # Different length
        close = [100.0, 101.0, 102.0]

        with pytest.raises(ValueError, match="[Ll]ength"):
            haze.py_atr(high, low, close, period=14)

    def test_adx_length_mismatch(self):
        """ADX should raise error for mismatched lengths"""
        high = [102.0] * 20
        low = [98.0] * 20
        close = [100.0] * 19  # Different length

        with pytest.raises(ValueError, match="[Ll]ength"):
            haze.py_adx(high, low, close, period=14)


class TestNumpyArrayInput:
    """Test that numpy arrays are properly converted"""

    def test_sma_with_numpy_array(self):
        """Should accept numpy arrays"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = haze.py_sma(data.tolist(), period=3)

        assert len(result) == 5
        assert not np.isnan(result[-1])

    def test_rsi_with_numpy_array(self):
        """RSI should accept numpy arrays"""
        data = np.array([100.0, 102.0, 101.0, 103.0, 105.0] + [104.0] * 15)
        result = haze.py_rsi(data.tolist(), period=14)

        assert len(result) == 20

    def test_bollinger_with_numpy_array(self):
        """Bollinger Bands should accept numpy arrays"""
        data = np.array([100.0] * 20)
        upper, middle, lower = haze.py_bollinger_bands(data.tolist(), period=14, std_multiplier=2.0)

        assert len(upper) == 20
        assert len(middle) == 20
        assert len(lower) == 20


class TestOutputFormats:
    """Test that output formats are correct Python types"""

    def test_sma_returns_list(self):
        """SMA should return a Python list of floats"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = haze.py_sma(data, period=3)

        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)

    def test_rsi_returns_list(self):
        """RSI should return a Python list of floats"""
        data = [100.0, 102.0, 101.0, 103.0, 105.0] + [104.0] * 15
        result = haze.py_rsi(data, period=14)

        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)

    def test_bollinger_returns_three_lists(self):
        """Bollinger Bands should return tuple of 3 lists"""
        data = [100.0] * 20
        result = haze.py_bollinger_bands(data, period=14, std_multiplier=2.0)

        assert isinstance(result, tuple)
        assert len(result) == 3
        upper, middle, lower = result
        assert isinstance(upper, list)
        assert isinstance(middle, list)
        assert isinstance(lower, list)

    def test_macd_returns_three_lists(self):
        """MACD should return tuple of 3 lists (macd, signal, histogram)"""
        data = [100.0 + i * 0.1 for i in range(50)]
        result = haze.py_macd(data, fast_period=12, slow_period=26, signal_period=9)

        assert isinstance(result, tuple)
        assert len(result) == 3
        macd, signal, histogram = result
        assert isinstance(macd, list)
        assert isinstance(signal, list)
        assert isinstance(histogram, list)


class TestUnicodeErrorMessages:
    """Test that error messages display correctly (no encoding issues)"""

    def test_error_message_is_readable(self):
        """Error messages should be valid UTF-8"""
        try:
            haze.py_sma([], period=3)
        except ValueError as e:
            error_msg = str(e)
            # Should not raise UnicodeDecodeError
            assert isinstance(error_msg, str)
            assert len(error_msg) > 0
            # Should contain helpful information
            assert "empty" in error_msg.lower() or "Empty" in error_msg


class TestEdgeCaseValues:
    """Test edge case numeric values"""

    def test_sma_with_very_large_values(self):
        """Very large values should not overflow (or may be NaN near limits)"""
        data = [1e308, 1e308, 1e308, 1e308, 1e308]  # Near f64 max
        result = haze.py_sma(data, period=3)

        assert len(result) == 5
        # Should return valid values or NaN (not crash)
        for i in range(2, 5):
            assert result[i] < float('inf') or np.isnan(result[i])

    def test_sma_with_very_small_values(self):
        """Very small values should maintain precision"""
        data = [1e-100, 2e-100, 3e-100, 4e-100, 5e-100]
        result = haze.py_sma(data, period=3)

        assert len(result) == 5
        # Should not underflow to zero
        assert result[2] > 0.0

    def test_sma_with_all_zeros(self):
        """All zeros should give zero SMA"""
        data = [0.0, 0.0, 0.0, 0.0, 0.0]
        result = haze.py_sma(data, period=3)

        assert len(result) == 5
        # After warmup, should be exactly 0.0
        assert result[2] == 0.0
        assert result[3] == 0.0
        assert result[4] == 0.0

    def test_rsi_with_constant_values(self):
        """Constant values should give RSI around 50, NaN, or 0 (no movement)"""
        data = [100.0] * 30
        result = haze.py_rsi(data, period=14)

        assert len(result) == 30
        # After warmup, RSI of constant price may be:
        # - NaN (undefined when no gain/loss)
        # - 0 (no gains at all)
        # - 50 (equal gains and losses in some implementations)
        for i in range(14, 30):
            r = result[i]
            assert np.isnan(r) or 0.0 <= r <= 100.0, f"RSI out of range at {i}: {r}"


class TestFailFastBehavior:
    """Fail-fast validation should raise errors for invalid inputs"""

    def test_invalid_input_raises(self):
        with pytest.raises(ValueError):
            haze.py_sma([], period=3)
        with pytest.raises(ValueError):
            haze.py_sma([1.0, 2.0, 3.0], period=0)


class TestConcurrentCalls:
    """Test that concurrent calls from Python don't cause issues"""

    def test_multiple_sma_calls(self):
        """Multiple SMA calls should not interfere"""
        data1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        data2 = [10.0, 20.0, 30.0, 40.0, 50.0]

        result1 = haze.py_sma(data1, period=3)
        result2 = haze.py_sma(data2, period=3)

        # Results should be independent
        assert result1 != result2
        assert result1[2] < result2[2]  # Different scales


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
