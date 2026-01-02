// lib.rs - Haze-Library Rust 扩展模块
//
// PyO3 入口点，暴露所有指标函数给 Python

#[cfg(feature = "python")]
use pyo3::prelude::*;

mod dataframe;
pub mod errors;
pub mod indicators;
mod ml;
#[cfg(feature = "python")]
mod streaming_py;
pub mod types;
pub mod utils;
#[macro_use]
mod macros;

pub use dataframe::{create_ohlcv_frame, OhlcvFrame};
pub use errors::{HazeError, HazeResult};

#[cfg(feature = "python")]
use types::{Candle, IndicatorResult, MultiIndicatorResult};

// ==================== OhlcvFrame (Python) ====================
//
// Expose the cached Rust OHLCV frame to Python so users can compute many
// indicators without repeatedly copying OHLCV arrays across the FFI boundary.

#[cfg(feature = "python")]
#[pyclass(name = "OhlcvFrame")]
pub struct PyOhlcvFrame {
    inner: OhlcvFrame,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOhlcvFrame {
    #[new]
    pub fn new(
        timestamps: Vec<i64>,
        open: Vec<f64>,
        high: Vec<f64>,
        low: Vec<f64>,
        close: Vec<f64>,
        volume: Vec<f64>,
    ) -> PyResult<Self> {
        Ok(Self {
            inner: OhlcvFrame::new(timestamps, open, high, low, close, volume)?,
        })
    }

    pub fn len(&self) -> usize {
        self.inner.len()
    }

    pub fn __len__(&self) -> usize {
        self.inner.len()
    }

    pub fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }

    pub fn clear_cache(&mut self) {
        self.inner.clear_cache();
    }

    pub fn cached_indicators(&self) -> Vec<String> {
        self.inner
            .cached_indicators()
            .into_iter()
            .cloned()
            .collect()
    }

    pub fn get_cached(&self, name: String) -> Option<Vec<f64>> {
        self.inner.get_cached(&name).map(|v| v.to_vec())
    }

    pub fn compute_common_indicators(
        &mut self,
    ) -> PyResult<std::collections::HashMap<String, Vec<f64>>> {
        Ok(self.inner.compute_common_indicators()?)
    }

    // -------------------- Moving averages --------------------

    pub fn sma(&mut self, period: usize) -> PyResult<Vec<f64>> {
        Ok(self.inner.sma(period)?.to_vec())
    }

    pub fn ema(&mut self, period: usize) -> PyResult<Vec<f64>> {
        Ok(self.inner.ema(period)?.to_vec())
    }

    pub fn wma(&mut self, period: usize) -> PyResult<Vec<f64>> {
        Ok(self.inner.wma(period)?.to_vec())
    }

    pub fn hma(&mut self, period: usize) -> PyResult<Vec<f64>> {
        Ok(self.inner.hma(period)?.to_vec())
    }

    // -------------------- Volatility --------------------

    pub fn atr(&mut self, period: usize) -> PyResult<Vec<f64>> {
        Ok(self.inner.atr(period)?.to_vec())
    }

    pub fn true_range(&mut self) -> PyResult<Vec<f64>> {
        Ok(self.inner.true_range()?.to_vec())
    }

    pub fn bollinger_bands(
        &mut self,
        period: usize,
        std_dev: f64,
    ) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
        let (upper, middle, lower) = self.inner.bollinger_bands(period, std_dev)?;
        Ok((upper.to_vec(), middle.to_vec(), lower.to_vec()))
    }

    // -------------------- Momentum --------------------

    pub fn rsi(&mut self, period: usize) -> PyResult<Vec<f64>> {
        Ok(self.inner.rsi(period)?.to_vec())
    }

    pub fn macd(
        &mut self,
        fast: usize,
        slow: usize,
        signal: usize,
    ) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
        let (macd, signal_line, hist) = self.inner.macd(fast, slow, signal)?;
        Ok((macd.to_vec(), signal_line.to_vec(), hist.to_vec()))
    }

    pub fn stochastic(
        &mut self,
        k_period: usize,
        smooth_k: usize,
        d_period: usize,
    ) -> PyResult<(Vec<f64>, Vec<f64>)> {
        let (k, d) = self.inner.stochastic(k_period, smooth_k, d_period)?;
        Ok((k.to_vec(), d.to_vec()))
    }

    pub fn cci(&mut self, period: usize) -> PyResult<Vec<f64>> {
        Ok(self.inner.cci(period)?.to_vec())
    }

    pub fn williams_r(&mut self, period: usize) -> PyResult<Vec<f64>> {
        Ok(self.inner.williams_r(period)?.to_vec())
    }

    // -------------------- Trend --------------------

    pub fn supertrend(&mut self, period: usize, multiplier: f64) -> types::SuperTrendVecs {
        let (st, dir, upper, lower) = self.inner.supertrend(period, multiplier)?;
        Ok((st.to_vec(), dir.to_vec(), upper.to_vec(), lower.to_vec()))
    }

    pub fn adx(&mut self, period: usize) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
        let (adx, plus_di, minus_di) = self.inner.adx(period)?;
        Ok((adx.to_vec(), plus_di.to_vec(), minus_di.to_vec()))
    }

    // -------------------- Volume --------------------

    pub fn obv(&mut self) -> PyResult<Vec<f64>> {
        Ok(self.inner.obv()?.to_vec())
    }

    pub fn vwap(&mut self, period: usize) -> PyResult<Vec<f64>> {
        Ok(self.inner.vwap(period)?.to_vec())
    }

    pub fn mfi(&mut self, period: usize) -> PyResult<Vec<f64>> {
        Ok(self.inner.mfi(period)?.to_vec())
    }
}

#[cfg(feature = "python")]
type Vec4F64 = (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>);

#[cfg(feature = "python")]
type Vec5F64 = (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>);

#[cfg(feature = "python")]
type Vec6F64 = (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>);

#[cfg(feature = "python")]
type Vec7F64 = (
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
    Vec<f64>,
);

#[cfg(feature = "python")]
type Pivots9F64 = (f64, f64, f64, f64, f64, f64, f64, f64, f64);

/// Macro for fail-fast error handling in Python FFI.
///
/// Converts `HazeResult<T>` to `PyResult<T>` and propagates all errors
/// to Python without NaN fallbacks.
///
/// # Usage
/// ```ignore
/// // Single vector
/// ok_or_nan!(result, len)
///
/// // Tuple of 2 vectors
/// ok_or_nan!(result, len, 2)
///
/// // Tuple of 3 vectors
/// ok_or_nan!(result, len, 3)
/// ```
#[cfg(feature = "python")]
macro_rules! ok_or_nan {
    // Single vector case: ok_or_nan!(result, len)
    ($result:expr, $len:expr) => {{
        let _ = $len;
        match $result {
            Ok(values) => Ok(values),
            Err(err) => Err(err.into()),
        }
    }};
    // 2-tuple case: ok_or_nan!(result, len, 2)
    ($result:expr, $len:expr, 2) => {{
        let _ = $len;
        match $result {
            Ok(values) => Ok(values),
            Err(err) => Err(err.into()),
        }
    }};
    // 3-tuple case: ok_or_nan!(result, len, 3)
    ($result:expr, $len:expr, 3) => {{
        let _ = $len;
        match $result {
            Ok(values) => Ok(values),
            Err(err) => Err(err.into()),
        }
    }};
    // 4-tuple case: ok_or_nan!(result, len, 4)
    ($result:expr, $len:expr, 4) => {{
        let _ = $len;
        match $result {
            Ok(values) => Ok(values),
            Err(err) => Err(err.into()),
        }
    }};
    // 5-tuple case: ok_or_nan!(result, len, 5)
    ($result:expr, $len:expr, 5) => {{
        let _ = $len;
        match $result {
            Ok(values) => Ok(values),
            Err(err) => Err(err.into()),
        }
    }};
    // 6-tuple case: ok_or_nan!(result, len, 6)
    ($result:expr, $len:expr, 6) => {{
        let _ = $len;
        match $result {
            Ok(values) => Ok(values),
            Err(err) => Err(err.into()),
        }
    }};
    // 7-tuple case: ok_or_nan!(result, len, 7)
    ($result:expr, $len:expr, 7) => {{
        let _ = $len;
        match $result {
            Ok(values) => Ok(values),
            Err(err) => Err(err.into()),
        }
    }};
    // Special case: 2 vectors + 1 f64: ok_or_nan!(result, len, 2, f64)
    ($result:expr, $len:expr, 2, f64) => {{
        let _ = $len;
        match $result {
            Ok(values) => Ok(values),
            Err(err) => Err(err.into()),
        }
    }};
}

// Legacy function wrappers for backward compatibility
// These delegate to the ok_or_nan! macro

#[cfg(feature = "python")]
#[inline]
fn ok_or_nan_vec(result: HazeResult<Vec<f64>>, len: usize) -> PyResult<Vec<f64>> {
    ok_or_nan!(result, len)
}

#[cfg(feature = "python")]
#[inline]
fn ok_or_nan_vec2(
    result: HazeResult<(Vec<f64>, Vec<f64>)>,
    len: usize,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    ok_or_nan!(result, len, 2)
}

#[cfg(feature = "python")]
#[inline]
fn ok_or_nan_vec3(
    result: HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)>,
    len: usize,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    ok_or_nan!(result, len, 3)
}

#[cfg(feature = "python")]
#[inline]
fn ok_or_nan_vec4(result: HazeResult<Vec4F64>, len: usize) -> PyResult<Vec4F64> {
    ok_or_nan!(result, len, 4)
}

#[cfg(feature = "python")]
#[inline]
fn ok_or_nan_vec5(result: HazeResult<Vec5F64>, len: usize) -> PyResult<Vec5F64> {
    ok_or_nan!(result, len, 5)
}

#[cfg(feature = "python")]
#[inline]
fn ok_or_nan_vec6(result: HazeResult<Vec6F64>, len: usize) -> PyResult<Vec6F64> {
    ok_or_nan!(result, len, 6)
}

#[cfg(feature = "python")]
#[inline]
fn ok_or_nan_vec7(result: HazeResult<Vec7F64>, len: usize) -> PyResult<Vec7F64> {
    ok_or_nan!(result, len, 7)
}

#[cfg(feature = "python")]
#[inline]
fn ok_or_nan_vec2_f64(
    result: HazeResult<(Vec<f64>, Vec<f64>, f64)>,
    len: usize,
) -> PyResult<(Vec<f64>, Vec<f64>, f64)> {
    ok_or_nan!(result, len, 2, f64)
}

// ==================== PyO3 模块定义 ====================

#[cfg(feature = "python")]
#[pymodule]
fn haze_library(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // 类型
    m.add_class::<Candle>()?;
    m.add_class::<IndicatorResult>()?;
    m.add_class::<MultiIndicatorResult>()?;
    m.add_class::<PyOhlcvFrame>()?;

    // Volatility 指标
    m.add_function(wrap_pyfunction!(py_true_range, m)?)?;
    m.add_function(wrap_pyfunction!(py_atr, m)?)?;
    m.add_function(wrap_pyfunction!(py_natr, m)?)?;
    m.add_function(wrap_pyfunction!(py_bollinger_bands, m)?)?;
    m.add_function(wrap_pyfunction!(py_keltner_channel, m)?)?;
    m.add_function(wrap_pyfunction!(py_donchian_channel, m)?)?;
    m.add_function(wrap_pyfunction!(py_chandelier_exit, m)?)?;
    m.add_function(wrap_pyfunction!(py_historical_volatility, m)?)?;
    m.add_function(wrap_pyfunction!(py_ulcer_index, m)?)?;
    m.add_function(wrap_pyfunction!(py_mass_index, m)?)?;

    // Momentum 指标
    m.add_function(wrap_pyfunction!(py_rsi, m)?)?;
    m.add_function(wrap_pyfunction!(py_macd, m)?)?;
    m.add_function(wrap_pyfunction!(py_stochastic, m)?)?;
    m.add_function(wrap_pyfunction!(py_stochrsi, m)?)?;
    m.add_function(wrap_pyfunction!(py_stoch_rsi, m)?)?;
    m.add_function(wrap_pyfunction!(py_cci, m)?)?;
    m.add_function(wrap_pyfunction!(py_williams_r, m)?)?;
    m.add_function(wrap_pyfunction!(py_awesome_oscillator, m)?)?;
    m.add_function(wrap_pyfunction!(py_fisher_transform, m)?)?;

    // Trend 指标
    m.add_function(wrap_pyfunction!(py_supertrend, m)?)?;
    m.add_function(wrap_pyfunction!(py_adx, m)?)?;
    m.add_function(wrap_pyfunction!(py_dmi, m)?)?;
    m.add_function(wrap_pyfunction!(py_aroon, m)?)?;
    m.add_function(wrap_pyfunction!(py_psar, m)?)?;
    m.add_function(wrap_pyfunction!(py_parabolic_sar, m)?)?;
    m.add_function(wrap_pyfunction!(py_trix, m)?)?;
    m.add_function(wrap_pyfunction!(py_dpo, m)?)?;

    // Volume 指标
    m.add_function(wrap_pyfunction!(py_obv, m)?)?;
    m.add_function(wrap_pyfunction!(py_vwap, m)?)?;
    m.add_function(wrap_pyfunction!(py_mfi, m)?)?;
    m.add_function(wrap_pyfunction!(py_force_index, m)?)?;
    m.add_function(wrap_pyfunction!(py_cmf, m)?)?;
    m.add_function(wrap_pyfunction!(py_volume_oscillator, m)?)?;
    m.add_function(wrap_pyfunction!(py_volume_profile, m)?)?;

    // MA/Overlap 指标
    m.add_function(wrap_pyfunction!(py_sma, m)?)?;
    m.add_function(wrap_pyfunction!(py_ema, m)?)?;
    m.add_function(wrap_pyfunction!(py_rma, m)?)?;
    m.add_function(wrap_pyfunction!(py_wma, m)?)?;
    m.add_function(wrap_pyfunction!(py_hma, m)?)?;
    m.add_function(wrap_pyfunction!(py_dema, m)?)?;
    m.add_function(wrap_pyfunction!(py_tema, m)?)?;

    // Fibonacci 指标
    m.add_function(wrap_pyfunction!(py_fib_retracement, m)?)?;
    m.add_function(wrap_pyfunction!(py_fib_extension, m)?)?;
    m.add_function(wrap_pyfunction!(py_fibonacci_retracement, m)?)?;
    m.add_function(wrap_pyfunction!(py_fibonacci_extension, m)?)?;
    m.add_function(wrap_pyfunction!(py_dynamic_fib_retracement, m)?)?;
    m.add_function(wrap_pyfunction!(py_detect_fib_touch, m)?)?;
    m.add_function(wrap_pyfunction!(py_fib_fan_lines, m)?)?;
    m.add_function(wrap_pyfunction!(py_fib_time_zones, m)?)?;

    // Ichimoku 指标
    m.add_function(wrap_pyfunction!(py_ichimoku_cloud, m)?)?;
    m.add_function(wrap_pyfunction!(py_ichimoku_signals, m)?)?;
    m.add_function(wrap_pyfunction!(py_ichimoku_tk_cross, m)?)?;
    m.add_function(wrap_pyfunction!(py_cloud_thickness, m)?)?;
    m.add_function(wrap_pyfunction!(py_cloud_color, m)?)?;

    // Pivot Points 指标
    m.add_function(wrap_pyfunction!(py_standard_pivots, m)?)?;
    m.add_function(wrap_pyfunction!(py_classic_pivots, m)?)?;
    m.add_function(wrap_pyfunction!(py_fibonacci_pivots, m)?)?;
    m.add_function(wrap_pyfunction!(py_camarilla_pivots, m)?)?;
    m.add_function(wrap_pyfunction!(py_woodie_pivots, m)?)?;
    m.add_function(wrap_pyfunction!(py_demark_pivots, m)?)?;
    m.add_function(wrap_pyfunction!(py_calc_pivot_series, m)?)?;
    m.add_function(wrap_pyfunction!(py_detect_pivot_touch, m)?)?;
    m.add_function(wrap_pyfunction!(py_pivot_zone, m)?)?;

    // 扩展 Momentum 指标
    m.add_function(wrap_pyfunction!(py_kdj, m)?)?;
    m.add_function(wrap_pyfunction!(py_tsi, m)?)?;
    m.add_function(wrap_pyfunction!(py_ultimate_oscillator, m)?)?;
    m.add_function(wrap_pyfunction!(py_mom, m)?)?;
    m.add_function(wrap_pyfunction!(py_roc, m)?)?;

    // 扩展 Trend 指标
    m.add_function(wrap_pyfunction!(py_vortex, m)?)?;
    m.add_function(wrap_pyfunction!(py_choppiness, m)?)?;
    m.add_function(wrap_pyfunction!(py_qstick, m)?)?;
    m.add_function(wrap_pyfunction!(py_vhf, m)?)?;

    // 扩展 Volume 指标
    m.add_function(wrap_pyfunction!(py_ad, m)?)?;
    m.add_function(wrap_pyfunction!(py_pvt, m)?)?;
    m.add_function(wrap_pyfunction!(py_nvi, m)?)?;
    m.add_function(wrap_pyfunction!(py_pvi, m)?)?;
    m.add_function(wrap_pyfunction!(py_eom, m)?)?;

    // 扩展 MA 指标
    m.add_function(wrap_pyfunction!(py_zlma, m)?)?;
    m.add_function(wrap_pyfunction!(py_t3, m)?)?;
    m.add_function(wrap_pyfunction!(py_kama, m)?)?;
    m.add_function(wrap_pyfunction!(py_frama, m)?)?;
    // 蜡烛图形态识别
    m.add_function(wrap_pyfunction!(py_doji, m)?)?;
    m.add_function(wrap_pyfunction!(py_hammer, m)?)?;
    m.add_function(wrap_pyfunction!(py_inverted_hammer, m)?)?;
    m.add_function(wrap_pyfunction!(py_hanging_man, m)?)?;
    m.add_function(wrap_pyfunction!(py_bullish_engulfing, m)?)?;
    m.add_function(wrap_pyfunction!(py_bearish_engulfing, m)?)?;
    m.add_function(wrap_pyfunction!(py_bullish_harami, m)?)?;
    m.add_function(wrap_pyfunction!(py_bearish_harami, m)?)?;
    m.add_function(wrap_pyfunction!(py_piercing_pattern, m)?)?;
    m.add_function(wrap_pyfunction!(py_dark_cloud_cover, m)?)?;
    m.add_function(wrap_pyfunction!(py_morning_star, m)?)?;
    m.add_function(wrap_pyfunction!(py_evening_star, m)?)?;
    m.add_function(wrap_pyfunction!(py_three_white_soldiers, m)?)?;
    m.add_function(wrap_pyfunction!(py_three_black_crows, m)?)?;
    // 统计指标
    m.add_function(wrap_pyfunction!(py_linear_regression, m)?)?;
    m.add_function(wrap_pyfunction!(py_correlation, m)?)?;
    m.add_function(wrap_pyfunction!(py_zscore, m)?)?;
    m.add_function(wrap_pyfunction!(py_covariance, m)?)?;
    m.add_function(wrap_pyfunction!(py_beta, m)?)?;
    m.add_function(wrap_pyfunction!(py_standard_error, m)?)?;
    m.add_function(wrap_pyfunction!(py_stderr, m)?)?;
    // 价格变换指标
    m.add_function(wrap_pyfunction!(py_avgprice, m)?)?;
    m.add_function(wrap_pyfunction!(py_medprice, m)?)?;
    m.add_function(wrap_pyfunction!(py_typprice, m)?)?;
    m.add_function(wrap_pyfunction!(py_wclprice, m)?)?;
    // 数学运算函数
    m.add_function(wrap_pyfunction!(py_max, m)?)?;
    m.add_function(wrap_pyfunction!(py_min, m)?)?;
    m.add_function(wrap_pyfunction!(py_sum, m)?)?;
    m.add_function(wrap_pyfunction!(py_sqrt, m)?)?;
    m.add_function(wrap_pyfunction!(py_ln, m)?)?;
    m.add_function(wrap_pyfunction!(py_log10, m)?)?;
    m.add_function(wrap_pyfunction!(py_exp, m)?)?;
    m.add_function(wrap_pyfunction!(py_abs, m)?)?;
    m.add_function(wrap_pyfunction!(py_ceil, m)?)?;
    m.add_function(wrap_pyfunction!(py_floor, m)?)?;
    m.add_function(wrap_pyfunction!(py_sin, m)?)?;
    m.add_function(wrap_pyfunction!(py_cos, m)?)?;
    m.add_function(wrap_pyfunction!(py_tan, m)?)?;
    m.add_function(wrap_pyfunction!(py_asin, m)?)?;
    m.add_function(wrap_pyfunction!(py_acos, m)?)?;
    m.add_function(wrap_pyfunction!(py_atan, m)?)?;
    m.add_function(wrap_pyfunction!(py_sinh, m)?)?;
    m.add_function(wrap_pyfunction!(py_cosh, m)?)?;
    m.add_function(wrap_pyfunction!(py_tanh, m)?)?;
    m.add_function(wrap_pyfunction!(py_add, m)?)?;
    m.add_function(wrap_pyfunction!(py_sub, m)?)?;
    m.add_function(wrap_pyfunction!(py_mult, m)?)?;
    m.add_function(wrap_pyfunction!(py_div, m)?)?;
    m.add_function(wrap_pyfunction!(py_minmax, m)?)?;
    m.add_function(wrap_pyfunction!(py_minmaxindex, m)?)?;
    // 扩展蜡烛图形态
    m.add_function(wrap_pyfunction!(py_shooting_star, m)?)?;
    m.add_function(wrap_pyfunction!(py_marubozu, m)?)?;
    m.add_function(wrap_pyfunction!(py_spinning_top, m)?)?;
    m.add_function(wrap_pyfunction!(py_dragonfly_doji, m)?)?;
    m.add_function(wrap_pyfunction!(py_gravestone_doji, m)?)?;
    m.add_function(wrap_pyfunction!(py_long_legged_doji, m)?)?;
    m.add_function(wrap_pyfunction!(py_tweezers_top, m)?)?;
    m.add_function(wrap_pyfunction!(py_tweezers_bottom, m)?)?;
    m.add_function(wrap_pyfunction!(py_rising_three_methods, m)?)?;
    m.add_function(wrap_pyfunction!(py_falling_three_methods, m)?)?;
    // 新增蜡烛图形态（第二批）
    m.add_function(wrap_pyfunction!(py_harami_cross, m)?)?;
    m.add_function(wrap_pyfunction!(py_morning_doji_star, m)?)?;
    m.add_function(wrap_pyfunction!(py_evening_doji_star, m)?)?;
    m.add_function(wrap_pyfunction!(py_three_inside, m)?)?;
    m.add_function(wrap_pyfunction!(py_three_outside, m)?)?;
    m.add_function(wrap_pyfunction!(py_abandoned_baby, m)?)?;
    m.add_function(wrap_pyfunction!(py_kicking, m)?)?;
    m.add_function(wrap_pyfunction!(py_long_line, m)?)?;
    m.add_function(wrap_pyfunction!(py_short_line, m)?)?;
    m.add_function(wrap_pyfunction!(py_doji_star, m)?)?;
    // 新增蜡烛图形态（第三批）
    m.add_function(wrap_pyfunction!(py_identical_three_crows, m)?)?;
    m.add_function(wrap_pyfunction!(py_stick_sandwich, m)?)?;
    m.add_function(wrap_pyfunction!(py_tristar, m)?)?;
    m.add_function(wrap_pyfunction!(py_upside_gap_two_crows, m)?)?;
    m.add_function(wrap_pyfunction!(py_gap_sidesidewhite, m)?)?;
    m.add_function(wrap_pyfunction!(py_takuri, m)?)?;
    m.add_function(wrap_pyfunction!(py_homing_pigeon, m)?)?;
    m.add_function(wrap_pyfunction!(py_matching_low, m)?)?;
    m.add_function(wrap_pyfunction!(py_separating_lines, m)?)?;
    m.add_function(wrap_pyfunction!(py_thrusting, m)?)?;
    m.add_function(wrap_pyfunction!(py_inneck, m)?)?;
    m.add_function(wrap_pyfunction!(py_onneck, m)?)?;
    m.add_function(wrap_pyfunction!(py_advance_block, m)?)?;
    m.add_function(wrap_pyfunction!(py_stalled_pattern, m)?)?;
    m.add_function(wrap_pyfunction!(py_belthold, m)?)?;
    // 新增蜡烛图形态（第四批 - TA-Lib 61 完整集合补充）
    m.add_function(wrap_pyfunction!(py_concealing_baby_swallow, m)?)?;
    m.add_function(wrap_pyfunction!(py_counterattack, m)?)?;
    m.add_function(wrap_pyfunction!(py_highwave, m)?)?;
    m.add_function(wrap_pyfunction!(py_hikkake, m)?)?;
    m.add_function(wrap_pyfunction!(py_hikkake_mod, m)?)?;
    m.add_function(wrap_pyfunction!(py_ladder_bottom, m)?)?;
    m.add_function(wrap_pyfunction!(py_mat_hold, m)?)?;
    m.add_function(wrap_pyfunction!(py_rickshaw_man, m)?)?;
    m.add_function(wrap_pyfunction!(py_unique_3_river, m)?)?;
    m.add_function(wrap_pyfunction!(py_xside_gap_3_methods, m)?)?;
    m.add_function(wrap_pyfunction!(py_closing_marubozu, m)?)?;
    m.add_function(wrap_pyfunction!(py_breakaway, m)?)?;

    // Overlap Studies 指标
    m.add_function(wrap_pyfunction!(py_midpoint, m)?)?;
    m.add_function(wrap_pyfunction!(py_midprice, m)?)?;
    m.add_function(wrap_pyfunction!(py_trima, m)?)?;
    m.add_function(wrap_pyfunction!(py_sar, m)?)?;
    m.add_function(wrap_pyfunction!(py_sarext, m)?)?;
    m.add_function(wrap_pyfunction!(py_mama, m)?)?;

    // SFG 交易信号指标 (KNN 版本)
    m.add_function(wrap_pyfunction!(py_ai_supertrend, m)?)?;
    m.add_function(wrap_pyfunction!(py_ai_momentum_index, m)?)?;
    m.add_function(wrap_pyfunction!(py_dynamic_macd, m)?)?;
    m.add_function(wrap_pyfunction!(py_atr2_signals, m)?)?;

    // SFG ML 增强版指标 (linfa)
    m.add_function(wrap_pyfunction!(py_ai_supertrend_ml, m)?)?;
    m.add_function(wrap_pyfunction!(py_atr2_signals_ml, m)?)?;
    m.add_function(wrap_pyfunction!(py_ai_momentum_index_ml, m)?)?;
    m.add_function(wrap_pyfunction!(py_pivot_buy_sell, m)?)?;

    // SFG 市场结构分析
    m.add_function(wrap_pyfunction!(py_detect_divergence, m)?)?;
    m.add_function(wrap_pyfunction!(py_fvg_signals, m)?)?;
    m.add_function(wrap_pyfunction!(py_volume_filter, m)?)?;

    // SFG 信号工具
    m.add_function(wrap_pyfunction!(py_combine_signals, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_stops, m)?)?;
    m.add_function(wrap_pyfunction!(py_trailing_stop, m)?)?;

    // SFG 新增指标 (PD Array, Breaker Block, General Parameters, LinReg S/D)
    m.add_function(wrap_pyfunction!(py_pd_array_signals, m)?)?;
    m.add_function(wrap_pyfunction!(py_breaker_block_signals, m)?)?;
    m.add_function(wrap_pyfunction!(py_general_parameters_signals, m)?)?;
    m.add_function(wrap_pyfunction!(py_linreg_supply_demand_signals, m)?)?;

    // 周期指标 (Hilbert Transform)
    m.add_function(wrap_pyfunction!(py_ht_dcperiod, m)?)?;
    m.add_function(wrap_pyfunction!(py_ht_dcphase, m)?)?;
    m.add_function(wrap_pyfunction!(py_ht_phasor, m)?)?;
    m.add_function(wrap_pyfunction!(py_ht_sine, m)?)?;
    m.add_function(wrap_pyfunction!(py_ht_trendmode, m)?)?;

    // 统计函数 (TA-Lib Compatible)
    m.add_function(wrap_pyfunction!(py_correl, m)?)?;
    m.add_function(wrap_pyfunction!(py_linearreg, m)?)?;
    m.add_function(wrap_pyfunction!(py_linearreg_slope, m)?)?;
    m.add_function(wrap_pyfunction!(py_linearreg_angle, m)?)?;
    m.add_function(wrap_pyfunction!(py_linearreg_intercept, m)?)?;
    m.add_function(wrap_pyfunction!(py_var, m)?)?;
    m.add_function(wrap_pyfunction!(py_tsf, m)?)?;

    // Batch 7: TA-Lib Advanced Indicators (170 → 180)
    // Note: py_ad already registered at line ~80, only new indicators below
    m.add_function(wrap_pyfunction!(py_adosc, m)?)?;
    m.add_function(wrap_pyfunction!(py_apo, m)?)?;
    m.add_function(wrap_pyfunction!(py_ppo, m)?)?;
    m.add_function(wrap_pyfunction!(py_cmo, m)?)?;
    m.add_function(wrap_pyfunction!(py_dx, m)?)?;
    m.add_function(wrap_pyfunction!(py_plus_di, m)?)?;
    m.add_function(wrap_pyfunction!(py_minus_di, m)?)?;

    // Batch 8: pandas-ta 独有指标 (180 → 190)
    m.add_function(wrap_pyfunction!(py_entropy, m)?)?;
    m.add_function(wrap_pyfunction!(py_aberration, m)?)?;
    m.add_function(wrap_pyfunction!(py_squeeze, m)?)?;
    m.add_function(wrap_pyfunction!(py_qqe, m)?)?;
    m.add_function(wrap_pyfunction!(py_cti, m)?)?;
    m.add_function(wrap_pyfunction!(py_er, m)?)?;
    m.add_function(wrap_pyfunction!(py_bias, m)?)?;
    m.add_function(wrap_pyfunction!(py_psl, m)?)?;
    m.add_function(wrap_pyfunction!(py_rvi, m)?)?;
    m.add_function(wrap_pyfunction!(py_inertia, m)?)?;

    // Batch 9: pandas-ta 独有指标（第二批）(190 → 200)
    m.add_function(wrap_pyfunction!(py_alligator, m)?)?;
    m.add_function(wrap_pyfunction!(py_efi, m)?)?;
    m.add_function(wrap_pyfunction!(py_kst, m)?)?;
    m.add_function(wrap_pyfunction!(py_stc, m)?)?;
    m.add_function(wrap_pyfunction!(py_tdfi, m)?)?;
    m.add_function(wrap_pyfunction!(py_wae, m)?)?;
    m.add_function(wrap_pyfunction!(py_smi, m)?)?;
    m.add_function(wrap_pyfunction!(py_coppock, m)?)?;
    m.add_function(wrap_pyfunction!(py_pgo, m)?)?;
    m.add_function(wrap_pyfunction!(py_vwma, m)?)?;

    // Batch 10: 最终批次（202 → 212 指标，达成 100%）
    m.add_function(wrap_pyfunction!(py_alma, m)?)?;
    m.add_function(wrap_pyfunction!(py_vidya, m)?)?;
    m.add_function(wrap_pyfunction!(py_pwma, m)?)?;
    m.add_function(wrap_pyfunction!(py_sinwma, m)?)?;
    m.add_function(wrap_pyfunction!(py_swma, m)?)?;
    m.add_function(wrap_pyfunction!(py_bop, m)?)?;
    m.add_function(wrap_pyfunction!(py_ssl_channel, m)?)?;
    m.add_function(wrap_pyfunction!(py_cfo, m)?)?;
    m.add_function(wrap_pyfunction!(py_slope, m)?)?;
    m.add_function(wrap_pyfunction!(py_percent_rank, m)?)?;

    // 谐波形态指标 (Harmonic Patterns)
    m.add_class::<PyHarmonicPattern>()?;
    m.add_function(wrap_pyfunction!(py_harmonics, m)?)?;
    m.add_function(wrap_pyfunction!(py_harmonics_patterns, m)?)?;
    m.add_function(wrap_pyfunction!(py_swing_points, m)?)?;

    // 流式/在线计算器 (Streaming Calculators)
    streaming_py::register_streaming_classes(m)?;

    // ML 模块 (Machine Learning)
    m.add_class::<PySFGModel>()?;
    m.add_function(wrap_pyfunction!(py_train_supertrend_model, m)?)?;
    m.add_function(wrap_pyfunction!(py_train_atr2_model, m)?)?;
    m.add_function(wrap_pyfunction!(py_train_momentum_model, m)?)?;
    m.add_function(wrap_pyfunction!(py_prepare_supertrend_features, m)?)?;
    m.add_function(wrap_pyfunction!(py_prepare_atr2_features, m)?)?;
    m.add_function(wrap_pyfunction!(py_prepare_momentum_features, m)?)?;

    Ok(())
}

// ==================== Volatility 指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (high, low, close, drift=1))]
#[pyo3(text_signature = "(high, low, close, drift=1)")]
/// Calculate True Range (TR)
///
/// Maximum of high-low, |high-prev close|, |low-prev close|.
/// Foundation for ATR calculation.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// drift : int, optional
///     Lookback for previous close (default: 1)
///
/// Returns
/// -------
/// list of float - True Range values
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_true_range(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    drift: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::true_range(&high, &low, &close, drift.unwrap_or(1)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=14)")]
/// Calculate Average True Range (ATR)
///
/// Measures market volatility by decomposing the entire range
/// of a price bar.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// list of float - ATR values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_atr(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::atr(&high, &low, &close, period.unwrap_or(14)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=14)")]
/// Calculate Normalized ATR (NATR)
///
/// ATR expressed as percentage of price, enabling cross-asset comparison.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// list of float - NATR values (percentage)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_natr(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::natr(&high, &low, &close, period.unwrap_or(14)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, period=20, std_multiplier=2.0)")]
/// Calculate Bollinger Bands
///
/// Volatility bands placed above and below a moving average.
/// Useful for identifying overbought/oversold conditions.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// period : int, optional
///     MA period (default: 20)
/// std_multiplier : float, optional
///     Standard deviation multiplier (default: 2.0)
///
/// Returns
/// -------
/// tuple of (list, list, list) - (upper band, middle band, lower band)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_bollinger_bands(
    close: Vec<f64>,
    period: Option<usize>,
    std_multiplier: Option<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec3(
        indicators::bollinger_bands(&close, period.unwrap_or(20), std_multiplier.unwrap_or(2.0)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (high, low, close, period=20, atr_period=None, multiplier=2.0))]
#[pyo3(text_signature = "(high, low, close, period=20, atr_period=None, multiplier=2.0)")]
/// Calculate Keltner Channel
///
/// Volatility-based envelope using ATR instead of standard deviation.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     EMA period (default: 20)
/// atr_period : int, optional
///     ATR period (default: period)
/// multiplier : float, optional
///     ATR multiplier (default: 2.0)
///
/// Returns
/// -------
/// tuple of (list, list, list) - (upper band, middle band, lower band)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_keltner_channel(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: usize,
    atr_period: Option<usize>,
    multiplier: f64,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = close.len();
    let atr_period = atr_period.unwrap_or(period);
    ok_or_nan_vec3(
        indicators::keltner_channel(&high, &low, &close, period, atr_period, multiplier),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, period=20)")]
/// Calculate Donchian Channel
///
/// Price channel based on highest high and lowest low over a period.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// period : int, optional
///     Lookback period (default: 20)
///
/// Returns
/// -------
/// tuple of (list, list, list) - (upper band, middle band, lower band)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_donchian_channel(
    high: Vec<f64>,
    low: Vec<f64>,
    period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = high.len();
    ok_or_nan_vec3(
        indicators::donchian_channel(&high, &low, period.unwrap_or(20)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (high, low, close, period=None, atr_period=None, multiplier=None))]
#[pyo3(text_signature = "(high, low, close, period=22, atr_period=22, multiplier=3.0)")]
/// Calculate Chandelier Exit
///
/// A volatility-based trailing stop indicator that sets exit levels based on ATR.
/// Helps identify optimal stop-loss levels for long and short positions.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period for highest/lowest (default: 22)
/// atr_period : int, optional
///     ATR calculation period (default: 22)
/// multiplier : float, optional
///     ATR multiplier for exit distance (default: 3.0)
///
/// Returns
/// -------
/// tuple of (list, list) - (long_exit, short_exit), NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_chandelier_exit(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
    atr_period: Option<usize>,
    multiplier: Option<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::chandelier_exit(
            &high,
            &low,
            &close,
            period.unwrap_or(22),
            atr_period.unwrap_or(22),
            multiplier.unwrap_or(3.0),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, period=20)")]
/// Calculate Historical Volatility
///
/// Measures the standard deviation of logarithmic returns annualized to represent
/// price volatility. Higher values indicate more volatile price movements.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 20)
///
/// Returns
/// -------
/// list of float - Annualized volatility values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_historical_volatility(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::historical_volatility(&close, period.unwrap_or(20)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, period=14)")]
/// Calculate Ulcer Index
///
/// Measures downside volatility and risk by calculating the depth and duration
/// of price declines from recent highs. Unlike standard deviation, it focuses
/// exclusively on downside risk.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// list of float - Ulcer Index values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
///
/// Examples
/// --------
/// >>> ui = py_ulcer_index([50.0, 49.5, 48.0, 49.0, 51.0], period=14)
/// >>> ui`[13]`  # First valid value
/// 2.45
fn py_ulcer_index(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::ulcer_index(&close, period.unwrap_or(14)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (high, low, fast=9, slow=25))]
#[pyo3(text_signature = "(high, low, fast=9, slow=25)")]
/// Calculate Mass Index
///
/// Identifies trend reversals by analyzing the range between high and low prices.
/// Uses the ratio of EMA of range to EMA of EMA of range. Values above 27 suggest
/// a reversal bulge, while drops below 26.5 indicate potential trend changes.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// fast : int, optional
///     EMA calculation period (default: 9)
/// slow : int, optional
///     Summation period (default: 25)
///
/// Returns
/// -------
/// list of float - Mass Index values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
///
/// Examples
/// --------
/// >>> mi = py_mass_index([10.5, 10.8, 11.0], [10.0, 10.3, 10.5], fast=9, slow=25)
/// >>> mi`[33]`  # First valid value after warmup
/// 26.8
fn py_mass_index(high: Vec<f64>, low: Vec<f64>, fast: usize, slow: usize) -> PyResult<Vec<f64>> {
    let len = high.len();
    ok_or_nan_vec(indicators::mass_index(&high, &low, fast, slow), len)
}

// ==================== Momentum 指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, period=14)")]
/// Calculate Relative Strength Index (RSI)
///
/// Measures the magnitude of recent price changes to evaluate
/// overbought or oversold conditions.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// list of float - RSI values (0-100), NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
///
/// Examples
/// --------
/// >>> rsi = py_rsi([44.0, 44.25, 44.375, ...], period=14)
/// >>> rsi`[14]`  # First valid value
/// 52.3
fn py_rsi(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::rsi(&close, period.unwrap_or(14)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, fast_period=12, slow_period=26, signal_period=9)")]
/// Calculate Moving Average Convergence Divergence (MACD)
///
/// Trend-following momentum indicator showing the relationship
/// between two moving averages.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// fast_period : int, optional
///     Fast EMA period (default: 12)
/// slow_period : int, optional
///     Slow EMA period (default: 26)
/// signal_period : int, optional
///     Signal line period (default: 9)
///
/// Returns
/// -------
/// tuple of (list, list, list) - (MACD line, signal line, histogram)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_macd(
    close: Vec<f64>,
    fast_period: Option<usize>,
    slow_period: Option<usize>,
    signal_period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec3(
        indicators::macd(
            &close,
            fast_period.unwrap_or(12),
            slow_period.unwrap_or(26),
            signal_period.unwrap_or(9),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (high, low, close, k_period=14, smooth_k=3, d_period=3))]
#[pyo3(text_signature = "(high, low, close, k_period=14, smooth_k=3, d_period=3)")]
/// Calculate Stochastic Oscillator
///
/// Compares closing price to price range over a period.
/// Identifies overbought (>80) and oversold (<20) conditions.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// k_period : int, optional
///     %K period (default: 14)
/// smooth_k : int, optional
///     %K smoothing period (default: 3)
/// d_period : int, optional
///     %D period (default: 3)
///
/// Returns
/// -------
/// tuple of (list, list) - (%K line, %D line)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_stochastic(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    k_period: usize,
    smooth_k: usize,
    d_period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::stochastic(&high, &low, &close, k_period, smooth_k, d_period),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, rsi_period=14, stoch_period=14, k_period=3, d_period=3)")]
/// Calculate Stochastic RSI
///
/// Applies Stochastic formula to RSI values for increased sensitivity.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// rsi_period : int, optional
///     RSI period (default: 14)
/// stoch_period : int, optional
///     Stochastic period (default: 14)
/// k_period : int, optional
///     %K smoothing period (default: 3)
/// d_period : int, optional
///     %D period (default: 3)
///
/// Returns
/// -------
/// tuple of (list, list) - (StochRSI %K, StochRSI %D)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_stochrsi(
    close: Vec<f64>,
    rsi_period: Option<usize>,
    stoch_period: Option<usize>,
    k_period: Option<usize>,
    d_period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::stochrsi(
            &close,
            rsi_period.unwrap_or(14),
            stoch_period.unwrap_or(14),
            k_period.unwrap_or(3),
            d_period.unwrap_or(3),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, rsi_period=14, stoch_period=14, k_period=3, d_period=3)")]
fn py_stoch_rsi(
    close: Vec<f64>,
    rsi_period: Option<usize>,
    stoch_period: Option<usize>,
    k_period: Option<usize>,
    d_period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    py_stochrsi(close, rsi_period, stoch_period, k_period, d_period)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=20)")]
/// Calculate Commodity Channel Index (CCI)
///
/// Identifies cyclical trends and measures deviation from
/// statistical mean.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 20)
///
/// Returns
/// -------
/// list of float - CCI values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_cci(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::cci(&high, &low, &close, period.unwrap_or(20)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=14)")]
/// Calculate Williams %R
///
/// Momentum indicator showing overbought/oversold levels.
/// Values range from -100 to 0.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// list of float - Williams %R values (-100 to 0)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_williams_r(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::williams_r(&high, &low, &close, period.unwrap_or(14)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, fast_period=5, slow_period=34)")]
/// Calculate Awesome Oscillator (AO)
///
/// Momentum indicator based on difference between 5 and 34 period SMAs
/// of midpoint prices.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// fast_period : int, optional
///     Fast period (default: 5)
/// slow_period : int, optional
///     Slow period (default: 34)
///
/// Returns
/// -------
/// list of float - AO values
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_awesome_oscillator(
    high: Vec<f64>,
    low: Vec<f64>,
    fast_period: Option<usize>,
    slow_period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = high.len();
    ok_or_nan_vec(
        indicators::awesome_oscillator(
            &high,
            &low,
            fast_period.unwrap_or(5),
            slow_period.unwrap_or(34),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, period=10)")]
/// Calculate Fisher Transform
///
/// Converts prices to Gaussian normal distribution for clearer
/// turning points.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// period : int, optional
///     Lookback period (default: 10)
///
/// Returns
/// -------
/// tuple of (list, list) - (Fisher Transform, Signal line)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_fisher_transform(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::fisher_transform(&high, &low, &close, period.unwrap_or(9)),
        len,
    )
}

// ==================== Trend 指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=10, multiplier=3.0)")]
/// Calculate SuperTrend
///
/// Trend-following indicator using ATR to identify support/resistance.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     ATR period (default: 10)
/// multiplier : float, optional
///     ATR multiplier (default: 3.0)
///
/// Returns
/// -------
/// tuple of (list, list) - (supertrend values, direction: 1=up, -1=down)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_supertrend(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
    multiplier: Option<f64>,
) -> PyResult<Vec4F64> {
    let len = close.len();
    ok_or_nan_vec4(
        indicators::supertrend(
            &high,
            &low,
            &close,
            period.unwrap_or(7),
            multiplier.unwrap_or(3.0),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=14)")]
/// Calculate Average Directional Index (ADX)
///
/// Measures trend strength regardless of direction.
/// Values above 25 indicate strong trend.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// tuple of (list, list, list) - (ADX, +DI, -DI)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_adx(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec3(
        indicators::adx(&high, &low, &close, period.unwrap_or(14)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=14)")]
fn py_dmi(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::dmi(&high, &low, &close, period.unwrap_or(14)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, period=25)")]
/// Calculate Aroon Indicator
///
/// Identifies trend changes and strength by measuring time
/// between highs/lows.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// period : int, optional
///     Lookback period (default: 25)
///
/// Returns
/// -------
/// tuple of (list, list, list) - (Aroon Up, Aroon Down, Aroon Oscillator)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_aroon(
    high: Vec<f64>,
    low: Vec<f64>,
    period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = high.len();
    ok_or_nan_vec3(indicators::aroon(&high, &low, period.unwrap_or(25)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, af_initial=0.02, af_increment=0.02, af_max=0.2)")]
/// Calculate Parabolic SAR
///
/// Time/price-based trend-following indicator.
/// Dots below price = uptrend, above = downtrend.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// af_initial : float, optional
///     Initial acceleration factor (default: 0.02)
/// af_increment : float, optional
///     AF increment (default: 0.02)
/// af_max : float, optional
///     Maximum AF (default: 0.2)
///
/// Returns
/// -------
/// tuple of (list, list) - (PSAR values, direction: 1=long, -1=short)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_psar(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    af_init: Option<f64>,
    af_increment: Option<f64>,
    af_max: Option<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::psar(
            &high,
            &low,
            &close,
            af_init.unwrap_or(0.02),
            af_increment.unwrap_or(0.02),
            af_max.unwrap_or(0.2),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, af_init=0.02, af_increment=0.02, af_max=0.2)")]
fn py_parabolic_sar(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    af_init: Option<f64>,
    af_increment: Option<f64>,
    af_max: Option<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    py_psar(high, low, close, af_init, af_increment, af_max)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, period=15)")]
/// Calculate TRIX (Triple Exponential Average)
///
/// A momentum oscillator showing the percent rate of change of a triple exponentially
/// smoothed moving average. Filters out insignificant price movements and identifies
/// trend direction. Positive values indicate bullish momentum, negative values bearish.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// period : int, optional
///     EMA period (default: 15)
///
/// Returns
/// -------
/// list of float - TRIX values as percentage, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
///
/// Examples
/// --------
/// >>> trix = py_trix([44.0, 44.5, 45.0, 44.8, 45.5], period=15)
/// >>> trix`[45]`  # First valid value after triple EMA warmup
/// 0.12
fn py_trix(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::trix(&close, period.unwrap_or(15)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, period=20)")]
/// Calculate Detrended Price Oscillator (DPO)
///
/// Removes the trend from prices to isolate cycles. Calculated by shifting a moving
/// average backward in time and subtracting it from the price. Helps identify
/// overbought/oversold levels and cycle turning points.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 20)
///
/// Returns
/// -------
/// list of float - DPO values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
///
/// Examples
/// --------
/// >>> dpo = py_dpo([44.0, 44.5, 45.0, 44.8, 45.5], period=20)
/// >>> dpo`[20]`  # First valid value
/// 0.35
fn py_dpo(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::dpo(&close, period.unwrap_or(20)), len)
}

// ==================== Volume 指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, volume)")]
/// Calculate On-Balance Volume (OBV)
///
/// Cumulative volume-based indicator measuring buying/selling pressure.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// volume : list of float
///     Volume data
///
/// Returns
/// -------
/// list of float - OBV values
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_obv(close: Vec<f64>, volume: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::obv(&close, &volume), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (high, low, close, volume, period=0))]
#[pyo3(text_signature = "(high, low, close, volume)")]
/// Calculate Volume Weighted Average Price (VWAP)
///
/// Average price weighted by volume. Used to assess fair value.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// volume : list of float
///     Volume data
///
/// Returns
/// -------
/// list of float - VWAP values
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_vwap(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::volume::vwap(&high, &low, &close, &volume, period.unwrap_or(0)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, volume, period=13)")]
/// Calculate Force Index (Elder's Force Index)
///
/// Measures the power behind price movements by combining price change direction
/// and volume. Positive values indicate bullish force, negative values bearish force.
/// Uses EMA smoothing to filter out noise and identify significant trend changes.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// volume : list of float
///     Volume data
/// period : int, optional
///     EMA smoothing period (default: 13)
///
/// Returns
/// -------
/// list of float - Force Index values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
///
/// Examples
/// --------
/// >>> fi = py_force_index([44.0, 44.5, 45.0], [1000, 1200, 1500], period=13)
/// >>> fi`[13]`  # First valid value
/// 625.5
fn py_force_index(close: Vec<f64>, volume: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::efi(&close, &volume, period.unwrap_or(13)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(volume, short_period=5, long_period=10)")]
/// Calculate Volume Oscillator
///
/// Measures the difference between two volume moving averages as a percentage.
/// Identifies divergences between price and volume trends. Positive values indicate
/// volume is increasing, negative values indicate decreasing volume.
///
/// Parameters
/// ----------
/// volume : list of float
///     Volume data
/// short_period : int, optional
///     Short moving average period (default: 5)
/// long_period : int, optional
///     Long moving average period (default: 10)
///
/// Returns
/// -------
/// list of float - Volume Oscillator percentage values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
///
/// Examples
/// --------
/// >>> vo = py_volume_oscillator([1000, 1200, 1500, 1300], short_period=5, long_period=10)
/// >>> vo`[9]`  # First valid value
/// 12.5
fn py_volume_oscillator(
    volume: Vec<f64>,
    short_period: Option<usize>,
    long_period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = volume.len();
    ok_or_nan_vec(
        indicators::volume_oscillator(
            &volume,
            short_period.unwrap_or(5),
            long_period.unwrap_or(10),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, volume, period=14)")]
/// Calculate Money Flow Index (MFI)
///
/// Volume-weighted RSI showing money flow momentum.
/// Overbought >80, oversold <20.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// volume : list of float
///     Volume data
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// list of float - MFI values (0-100)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_mfi(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::mfi(&high, &low, &close, &volume, period.unwrap_or(14)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, volume, period=20)")]
/// Calculate Chaikin Money Flow (CMF)
///
/// Measures money flow volume over a period.
/// Positive = buying pressure, negative = selling pressure.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// volume : list of float
///     Volume data
/// period : int, optional
///     Lookback period (default: 20)
///
/// Returns
/// -------
/// list of float - CMF values (-1 to 1)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_cmf(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::cmf(&high, &low, &close, &volume, period.unwrap_or(20)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_volume_profile(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    num_bins: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>, f64)> {
    let len = close.len();
    ok_or_nan_vec2_f64(
        indicators::volume_profile(&high, &low, &close, &volume, num_bins.unwrap_or(24)),
        len,
    )
}

// ==================== MA/Overlap 指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period)")]
/// Calculate Simple Moving Average (SMA)
///
/// Computes the arithmetic mean of values over a rolling window.
///
/// Parameters
/// ----------
/// values : list of float
///     Price data (typically close prices)
/// period : int
///     Lookback period (default: 20)
///
/// Returns
/// -------
/// list of float - SMA values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
///
/// Examples
/// --------
/// >>> sma = py_sma([44.0, 44.25, 44.375, ...], period=20)
fn py_sma(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::sma(&values, period), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period)")]
/// Calculate Exponential Moving Average (EMA)
///
/// Weighted moving average giving more importance to recent prices.
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int
///     Lookback period (default: 20)
///
/// Returns
/// -------
/// list of float - EMA values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_ema(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::ema(&values, period), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period)")]
/// Calculate Rolling/Wilder Moving Average (RMA)
///
/// Modified EMA used in RSI calculation, smoother than standard EMA.
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - RMA values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_rma(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::rma(&values, period), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period)")]
/// Calculate Weighted Moving Average (WMA)
///
/// Linear-weighted moving average giving more weight to recent data.
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - WMA values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_wma(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::wma(&values, period), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period)")]
/// Calculate Hull Moving Average (HMA)
///
/// Reduces lag while improving smoothness using weighted moving averages.
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - HMA values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_hma(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::hma(&values, period), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period)")]
/// Calculate Double Exponential Moving Average (DEMA)
///
/// Reduced lag EMA using double smoothing technique.
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - DEMA values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_dema(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::dema(&values, period), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period)")]
/// Calculate Triple Exponential Moving Average (TEMA)
///
/// Further reduced lag EMA using triple smoothing.
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - TEMA values, NaN for warmup period
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_tema(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::tema(&values, period), len)
}

// ==================== Fibonacci 指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
fn py_fib_retracement(start_price: f64, end_price: f64) -> PyResult<Vec<(String, f64)>> {
    let fib = indicators::fibonacci::fib_retracement(start_price, end_price, None)?;
    let mut levels: Vec<(String, f64)> = fib.levels.into_iter().collect();
    levels.sort_by(|a, b| a.0.cmp(&b.0));
    Ok(levels)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_fibonacci_retracement(start_price: f64, end_price: f64) -> PyResult<Vec<(String, f64)>> {
    py_fib_retracement(start_price, end_price)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_fib_extension(
    start_price: f64,
    end_price: f64,
    retracement_price: f64,
) -> PyResult<Vec<(String, f64)>> {
    let ext =
        indicators::fibonacci::fib_extension(start_price, end_price, retracement_price, None)?;
    let mut levels: Vec<(String, f64)> = ext.levels.into_iter().collect();
    levels.sort_by(|a, b| a.0.cmp(&b.0));
    Ok(levels)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_fibonacci_extension(
    start_price: f64,
    end_price: f64,
    retracement_price: f64,
) -> PyResult<Vec<(String, f64)>> {
    py_fib_extension(start_price, end_price, retracement_price)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_dynamic_fib_retracement(
    prices: Vec<f64>,
    lookback: Option<usize>,
) -> PyResult<Vec<std::collections::HashMap<String, f64>>> {
    Ok(indicators::dynamic_fib_retracement(
        &prices,
        lookback.unwrap_or(20),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_detect_fib_touch(
    current_price: f64,
    levels: Vec<(String, f64)>,
    tolerance: Option<f64>,
) -> PyResult<Option<String>> {
    let mut map = std::collections::HashMap::with_capacity(levels.len());
    for (k, v) in levels {
        map.insert(k, v);
    }
    Ok(indicators::detect_fib_touch(
        current_price,
        &map,
        tolerance.unwrap_or(0.001),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_fib_fan_lines(
    start_index: usize,
    end_index: usize,
    start_price: f64,
    end_price: f64,
    target_index: usize,
) -> PyResult<(f64, f64, f64)> {
    Ok(indicators::fib_fan_lines(
        start_index,
        end_index,
        start_price,
        end_price,
        target_index,
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_fib_time_zones(start_index: usize, max_zones: usize) -> PyResult<Vec<usize>> {
    Ok(indicators::fib_time_zones(start_index, max_zones)?)
}

// ==================== Ichimoku 指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, conversion=9, base=26, span_b=52, displacement=26)")]
/// Calculate Ichimoku Cloud
///
/// Comprehensive trend-following system with support/resistance levels.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// conversion : int, optional
///     Conversion line period (default: 9)
/// base : int, optional
///     Base line period (default: 26)
/// span_b : int, optional
///     Span B period (default: 52)
/// displacement : int, optional
///     Cloud displacement (default: 26)
///
/// Returns
/// -------
/// tuple of (list, list, list, list, list) - (Tenkan, Kijun, Senkou A, Senkou B, Chikou)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_ichimoku_cloud(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    tenkan_period: Option<usize>,
    kijun_period: Option<usize>,
    senkou_b_period: Option<usize>,
) -> PyResult<Vec5F64> {
    let ichimoku = indicators::ichimoku::ichimoku_cloud(
        &high,
        &low,
        &close,
        tenkan_period.unwrap_or(9),
        kijun_period.unwrap_or(26),
        senkou_b_period.unwrap_or(52),
    )?;

    Ok((
        ichimoku.tenkan_sen,
        ichimoku.kijun_sen,
        ichimoku.senkou_span_a,
        ichimoku.senkou_span_b,
        ichimoku.chikou_span,
    ))
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_ichimoku_signals(
    close: Vec<f64>,
    tenkan_sen: Vec<f64>,
    kijun_sen: Vec<f64>,
    senkou_span_a: Vec<f64>,
    senkou_span_b: Vec<f64>,
    chikou_span: Vec<f64>,
) -> PyResult<Vec<i32>> {
    let ichimoku = indicators::ichimoku::IchimokuCloud {
        tenkan_sen,
        kijun_sen,
        senkou_span_a,
        senkou_span_b,
        chikou_span,
    };
    let signals = indicators::ichimoku::ichimoku_signals(&close, &ichimoku)?;
    Ok(signals
        .into_iter()
        .map(|s| match s {
            indicators::ichimoku::IchimokuSignal::StrongBullish => 2,
            indicators::ichimoku::IchimokuSignal::Bullish => 1,
            indicators::ichimoku::IchimokuSignal::Neutral => 0,
            indicators::ichimoku::IchimokuSignal::Bearish => -1,
            indicators::ichimoku::IchimokuSignal::StrongBearish => -2,
        })
        .collect())
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_ichimoku_tk_cross(
    tenkan_sen: Vec<f64>,
    kijun_sen: Vec<f64>,
    senkou_span_a: Vec<f64>,
    senkou_span_b: Vec<f64>,
    chikou_span: Vec<f64>,
) -> PyResult<Vec<f64>> {
    let ichimoku = indicators::ichimoku::IchimokuCloud {
        tenkan_sen,
        kijun_sen,
        senkou_span_a,
        senkou_span_b,
        chikou_span,
    };
    Ok(indicators::ichimoku::ichimoku_tk_cross(&ichimoku)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_cloud_thickness(
    tenkan_sen: Vec<f64>,
    kijun_sen: Vec<f64>,
    senkou_span_a: Vec<f64>,
    senkou_span_b: Vec<f64>,
    chikou_span: Vec<f64>,
) -> PyResult<Vec<f64>> {
    let ichimoku = indicators::ichimoku::IchimokuCloud {
        tenkan_sen,
        kijun_sen,
        senkou_span_a,
        senkou_span_b,
        chikou_span,
    };
    Ok(indicators::ichimoku::cloud_thickness(&ichimoku)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_cloud_color(
    tenkan_sen: Vec<f64>,
    kijun_sen: Vec<f64>,
    senkou_span_a: Vec<f64>,
    senkou_span_b: Vec<f64>,
    chikou_span: Vec<f64>,
) -> PyResult<Vec<f64>> {
    let ichimoku = indicators::ichimoku::IchimokuCloud {
        tenkan_sen,
        kijun_sen,
        senkou_span_a,
        senkou_span_b,
        chikou_span,
    };
    Ok(indicators::ichimoku::cloud_color(&ichimoku)?)
}

// ==================== Pivot Points 指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
fn py_standard_pivots(
    high: f64,
    low: f64,
    close: f64,
) -> PyResult<(f64, f64, f64, f64, f64, f64, f64)> {
    let pivots = indicators::pivots::standard_pivots(high, low, close)?;
    Ok((
        pivots.pivot,
        pivots.r1,
        pivots.r2,
        pivots.r3,
        pivots.s1,
        pivots.s2,
        pivots.s3,
    ))
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_classic_pivots(
    high: f64,
    low: f64,
    close: f64,
) -> PyResult<(f64, f64, f64, f64, f64, f64, f64)> {
    py_standard_pivots(high, low, close)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_fibonacci_pivots(
    high: f64,
    low: f64,
    close: f64,
) -> PyResult<(f64, f64, f64, f64, f64, f64, f64)> {
    let pivots = indicators::pivots::fibonacci_pivots(high, low, close)?;
    Ok((
        pivots.pivot,
        pivots.r1,
        pivots.r2,
        pivots.r3,
        pivots.s1,
        pivots.s2,
        pivots.s3,
    ))
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_camarilla_pivots(high: f64, low: f64, close: f64) -> PyResult<Pivots9F64> {
    let pivots = indicators::pivots::camarilla_pivots(high, low, close)?;
    Ok((
        pivots.pivot,
        pivots.r1,
        pivots.r2,
        pivots.r3,
        pivots.r4.unwrap_or(f64::NAN),
        pivots.s1,
        pivots.s2,
        pivots.s3,
        pivots.s4.unwrap_or(f64::NAN),
    ))
}

#[cfg(feature = "python")]
fn pivot_levels_from_tuple(levels: Pivots9F64) -> indicators::pivots::PivotLevels {
    let (pivot, r1, r2, r3, r4, s1, s2, s3, s4) = levels;
    indicators::pivots::PivotLevels {
        pivot,
        r1,
        r2,
        r3,
        r4: if r4.is_finite() { Some(r4) } else { None },
        s1,
        s2,
        s3,
        s4: if s4.is_finite() { Some(s4) } else { None },
    }
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_woodie_pivots(
    high: f64,
    low: f64,
    close: f64,
) -> PyResult<(f64, f64, f64, f64, f64, f64, f64)> {
    let pivots = indicators::pivots::woodie_pivots(high, low, close)?;
    Ok((
        pivots.pivot,
        pivots.r1,
        pivots.r2,
        pivots.r3,
        pivots.s1,
        pivots.s2,
        pivots.s3,
    ))
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_demark_pivots(
    open: f64,
    high: f64,
    low: f64,
    close: f64,
) -> PyResult<(f64, f64, f64, f64, f64, f64, f64)> {
    let pivots = indicators::pivots::demark_pivots(open, high, low, close)?;
    Ok((
        pivots.pivot,
        pivots.r1,
        pivots.r2,
        pivots.r3,
        pivots.s1,
        pivots.s2,
        pivots.s3,
    ))
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_calc_pivot_series(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    method: String,
) -> PyResult<Vec<Pivots9F64>> {
    let pivots = indicators::pivots::calc_pivot_series(&open, &high, &low, &close, &method)?;
    let mut out = Vec::with_capacity(pivots.len());
    for p in pivots {
        out.push((
            p.pivot,
            p.r1,
            p.r2,
            p.r3,
            p.r4.unwrap_or(f64::NAN),
            p.s1,
            p.s2,
            p.s3,
            p.s4.unwrap_or(f64::NAN),
        ));
    }
    Ok(out)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_detect_pivot_touch(
    current_price: f64,
    levels: Pivots9F64,
    tolerance: Option<f64>,
) -> PyResult<Option<String>> {
    let pivots = pivot_levels_from_tuple(levels);
    Ok(indicators::pivots::detect_pivot_touch(
        current_price,
        &pivots,
        tolerance.unwrap_or(0.001),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_pivot_zone(current_price: f64, levels: Pivots9F64) -> PyResult<String> {
    let pivots = pivot_levels_from_tuple(levels);
    Ok(indicators::pivots::pivot_zone(current_price, &pivots)?)
}

// ==================== 扩展 Momentum 指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (high, low, close, k_period=9, smooth_k=3, d_period=3))]
#[pyo3(text_signature = "(high, low, close, k_period=9, smooth_k=3, d_period=3)")]
/// Calculate KDJ Indicator
///
/// Extension of Stochastic Oscillator popular in Asian markets.
/// Adds J line: J = 3*K - 2*D for more sensitive signals.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// k_period : int, optional
///     %K period (default: 9)
/// smooth_k : int, optional
///     %K smoothing period (default: 3)
/// d_period : int, optional
///     %D period (default: 3)
///
/// Returns
/// -------
/// tuple of (list, list, list) - (K line, D line, J line)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_kdj(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    k_period: usize,
    smooth_k: usize,
    d_period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec3(
        indicators::kdj(&high, &low, &close, k_period, smooth_k, d_period),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, long_period=25, short_period=13, signal_period=13)")]
/// Calculate True Strength Index (TSI)
///
/// Double-smoothed momentum oscillator that reduces noise.
/// Uses two EMA passes for smoother signals than RSI.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// long_period : int, optional
///     First EMA period (default: 25)
/// short_period : int, optional
///     Second EMA period (default: 13)
/// signal_period : int, optional
///     Signal line period (default: 13)
///
/// Returns
/// -------
/// tuple of (list, list) - (TSI line, signal line)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_tsi(
    close: Vec<f64>,
    long_period: Option<usize>,
    short_period: Option<usize>,
    signal_period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::tsi(
            &close,
            long_period.unwrap_or(25),
            short_period.unwrap_or(13),
            signal_period.unwrap_or(13),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period1=7, period2=14, period3=28)")]
/// Calculate Ultimate Oscillator
///
/// Multi-timeframe momentum indicator combining three periods
/// to reduce false signals. Values range 0-100.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period1 : int, optional
///     Short period (default: 7)
/// period2 : int, optional
///     Medium period (default: 14)
/// period3 : int, optional
///     Long period (default: 28)
///
/// Returns
/// -------
/// list of float - Ultimate Oscillator values (0-100)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_ultimate_oscillator(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period1: Option<usize>,
    period2: Option<usize>,
    period3: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::ultimate_oscillator(
            &high,
            &low,
            &close,
            period1.unwrap_or(7),
            period2.unwrap_or(14),
            period3.unwrap_or(28),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period=10)")]
/// Calculate Momentum
///
/// Simple price difference over a lookback period.
/// Positive = upward momentum, negative = downward.
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int, optional
///     Lookback period (default: 10)
///
/// Returns
/// -------
/// list of float - Momentum values (price`[i]` - price[i-period])
fn py_mom(values: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let period = period.unwrap_or(10);
    let len = validate_single!(&values, "values");
    validate_period!(period, len);
    Ok(utils::stats::momentum(&values, period))
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period=10)")]
/// Calculate Rate of Change (ROC)
///
/// Percentage change over a lookback period.
/// ROC = ((price - price`[n]`) / price`[n]`) * 100
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int, optional
///     Lookback period (default: 10)
///
/// Returns
/// -------
/// list of float - ROC values as percentages
fn py_roc(values: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let period = period.unwrap_or(10);
    let len = validate_single!(&values, "values");
    validate_period!(period, len);
    Ok(utils::stats::roc(&values, period))
}

// ==================== 扩展 Trend 指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=14)")]
/// Calculate Vortex Indicator
///
/// Two oscillators (+VI and -VI) capturing positive and negative
/// trend movement. Crossovers generate trading signals.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// tuple of (list, list) - (+VI, -VI)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_vortex(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::vortex(&high, &low, &close, period.unwrap_or(14)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=14)")]
/// Calculate Choppiness Index
///
/// Measures whether market is trending or range-bound.
/// Values 0-38.2 = trending, 61.8-100 = choppy/consolidating.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// list of float - Choppiness Index values (0-100)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_choppiness(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::choppiness_index(&high, &low, &close, period.unwrap_or(14)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, close, period=14)")]
/// Calculate Qstick Indicator
///
/// Moving average of open-close differences.
/// Positive = bullish (closes > opens), negative = bearish.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     MA period (default: 14)
///
/// Returns
/// -------
/// list of float - Qstick values
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_qstick(open: Vec<f64>, close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::qstick(&open, &close, period.unwrap_or(14)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, period=28)")]
/// Calculate Vertical Horizontal Filter (VHF)
///
/// Measures trend strength. Higher values = stronger trend.
/// Can be used to determine when to use trend-following vs
/// oscillator strategies.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 28)
///
/// Returns
/// -------
/// list of float - VHF values
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_vhf(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::vhf(&close, period.unwrap_or(28)), len)
}

// ==================== 扩展 Volume 指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
fn py_ad(high: Vec<f64>, low: Vec<f64>, close: Vec<f64>, volume: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::accumulation_distribution(&high, &low, &close, &volume),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_pvt(close: Vec<f64>, volume: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::price_volume_trend(&close, &volume), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_nvi(close: Vec<f64>, volume: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::negative_volume_index(&close, &volume), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_pvi(close: Vec<f64>, volume: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::positive_volume_index(&close, &volume), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_eom(
    high: Vec<f64>,
    low: Vec<f64>,
    volume: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = high.len();
    ok_or_nan_vec(
        indicators::ease_of_movement(&high, &low, &volume, period.unwrap_or(14)),
        len,
    )
}

// ==================== 扩展 MA 指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
fn py_zlma(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::zlma(&values, period), len)
}

// Note: py_t3 and py_kama are defined later in the file with better Optional parameter support

#[cfg(feature = "python")]
#[pyfunction]
fn py_frama(values: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::frama(&values, period.unwrap_or(16)), len)
}

// ==================== 蜡烛图形态识别包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, body_threshold=0.1))]
#[pyo3(text_signature = "(open, high, low, close, body_threshold=0.1)")]
/// Detect Doji Candlestick Pattern
///
/// Identifies doji patterns where open and close prices are nearly equal, indicating
/// market indecision. The small body (relative to the range) suggests equilibrium
/// between buyers and sellers. Often signals potential trend reversals.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// body_threshold : float, optional
///     Maximum body-to-range ratio to qualify as doji (default: 0.1)
///
/// Returns
/// -------
/// list of float - 100 where doji detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> doji = py_doji([10.0, 10.5], [10.8, 11.0], [9.8, 10.0], [10.05, 10.48])
/// >>> doji`[0]`  # First candle is doji
/// 100.0
fn py_doji(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    body_threshold: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::doji(
        &open,
        &high,
        &low,
        &close,
        body_threshold.unwrap_or(0.1),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, high, low, close)")]
/// Detect Hammer candlestick pattern
///
/// Bullish reversal pattern with small body and long lower shadow.
/// Appears at bottom of downtrends.
///
/// Returns
/// -------
/// list of float - 100.0 = hammer detected, 0.0 = no pattern
fn py_hammer(open: Vec<f64>, high: Vec<f64>, low: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::hammer(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, high, low, close)")]
/// Detect Inverted Hammer candlestick pattern
///
/// Bullish reversal with small body and long upper shadow.
/// Appears at bottom of downtrends.
///
/// Returns
/// -------
/// list of float - 100.0 = pattern detected, 0.0 = no pattern
fn py_inverted_hammer(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::inverted_hammer(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, high, low, close)")]
/// Detect Hanging Man candlestick pattern
///
/// Bearish reversal pattern (hammer shape at top of uptrend).
/// Small body with long lower shadow.
///
/// Returns
/// -------
/// list of float - -100.0 = pattern detected, 0.0 = no pattern
fn py_hanging_man(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::hanging_man(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, close)")]
/// Detect Bullish Engulfing pattern
///
/// Two-candle bullish reversal. Second candle's body completely
/// engulfs the first (smaller bearish) candle.
///
/// Returns
/// -------
/// list of float - 100.0 = pattern detected, 0.0 = no pattern
fn py_bullish_engulfing(open: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::bullish_engulfing(&open, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, close)")]
/// Detect Bearish Engulfing pattern
///
/// Two-candle bearish reversal. Second candle's body completely
/// engulfs the first (smaller bullish) candle.
///
/// Returns
/// -------
/// list of float - -100.0 = pattern detected, 0.0 = no pattern
fn py_bearish_engulfing(open: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::bearish_engulfing(&open, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, close)")]
/// Detect Bullish Harami pattern
///
/// Two-candle bullish reversal. Small bullish candle contained
/// within prior large bearish candle.
///
/// Returns
/// -------
/// list of float - 100.0 = pattern detected, 0.0 = no pattern
fn py_bullish_harami(open: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::bullish_harami(&open, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, close)")]
/// Detect Bearish Harami pattern
///
/// Two-candle bearish reversal. Small bearish candle contained
/// within prior large bullish candle.
///
/// Returns
/// -------
/// list of float - -100.0 = pattern detected, 0.0 = no pattern
fn py_bearish_harami(open: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::bearish_harami(&open, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, low, close)")]
/// Detect Piercing Pattern
///
/// Two-candle bullish reversal. Bearish candle followed by
/// bullish candle that closes above midpoint of first.
///
/// Returns
/// -------
/// list of float - 100.0 = pattern detected, 0.0 = no pattern
fn py_piercing_pattern(open: Vec<f64>, low: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::piercing_pattern(&open, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, high, close)")]
/// Detect Dark Cloud Cover pattern
///
/// Two-candle bearish reversal. Bullish candle followed by
/// bearish candle that closes below midpoint of first.
///
/// Returns
/// -------
/// list of float - -100.0 = pattern detected, 0.0 = no pattern
fn py_dark_cloud_cover(open: Vec<f64>, high: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::dark_cloud_cover(&open, &high, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, high, low, close)")]
/// Detect Morning Star pattern
///
/// Three-candle bullish reversal. Large bearish, small body,
/// then large bullish candle.
///
/// Returns
/// -------
/// list of float - 100.0 = pattern detected, 0.0 = no pattern
fn py_morning_star(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::morning_star(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, high, low, close)")]
/// Detect Evening Star pattern
///
/// Three-candle bearish reversal. Large bullish, small body,
/// then large bearish candle.
///
/// Returns
/// -------
/// list of float - -100.0 = pattern detected, 0.0 = no pattern
fn py_evening_star(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::evening_star(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, high, close)")]
/// Detect Three White Soldiers pattern
///
/// Three consecutive bullish candles with progressively higher
/// closes. Strong bullish continuation signal.
///
/// Returns
/// -------
/// list of float - 100.0 = pattern detected, 0.0 = no pattern
fn py_three_white_soldiers(open: Vec<f64>, high: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::three_white_soldiers(&open, &high, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, low, close)")]
/// Detect Three Black Crows pattern
///
/// Three consecutive bearish candles with progressively lower
/// closes. Strong bearish continuation signal.
///
/// Returns
/// -------
/// list of float - -100.0 = pattern detected, 0.0 = no pattern
fn py_three_black_crows(open: Vec<f64>, low: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::three_black_crows(&open, &low, &close)?)
}

// ==================== 统计指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(y_values, period)")]
/// Calculate Linear Regression
///
/// Returns slope, intercept, and R-squared values over rolling window.
///
/// Parameters
/// ----------
/// y_values : list of float
///     Values to regress
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// tuple of (list, list, list) - (slope, intercept, r_squared)
fn py_linear_regression(
    y_values: Vec<f64>,
    period: usize,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = validate_single!(&y_values, "y_values");
    validate_period!(period, len);
    Ok(utils::linear_regression(&y_values, period))
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(x, y, period)")]
/// Calculate Correlation Coefficient
///
/// Pearson correlation between two series. Values -1 to +1.
///
/// Parameters
/// ----------
/// x : list of float
///     First series
/// y : list of float
///     Second series
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - Correlation values (-1 to +1)
fn py_correlation(x: Vec<f64>, y: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = validate_pair!(&x, "x", &y, "y");
    validate_period!(period, len);
    Ok(utils::correlation(&x, &y, period))
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period)")]
/// Calculate Z-Score
///
/// Number of standard deviations from the mean.
/// Used for mean reversion strategies.
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - Z-score values
fn py_zscore(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = validate_single!(&values, "values");
    validate_period!(period, len);
    Ok(utils::zscore(&values, period))
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(x, y, period)")]
/// Calculate Covariance
///
/// Measures how two variables change together.
///
/// Parameters
/// ----------
/// x : list of float
///     First series
/// y : list of float
///     Second series
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - Covariance values
fn py_covariance(x: Vec<f64>, y: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = validate_pair!(&x, "x", &y, "y");
    validate_period!(period, len);
    Ok(utils::covariance(&x, &y, period))
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(asset_returns, benchmark_returns, period)")]
/// Calculate Beta
///
/// Sensitivity of asset to benchmark movements.
/// Beta > 1 = more volatile, Beta < 1 = less volatile.
///
/// Parameters
/// ----------
/// asset_returns : list of float
///     Asset return series
/// benchmark_returns : list of float
///     Benchmark return series
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - Beta values
fn py_beta(
    asset_returns: Vec<f64>,
    benchmark_returns: Vec<f64>,
    period: usize,
) -> PyResult<Vec<f64>> {
    let len = validate_pair!(
        &asset_returns,
        "asset_returns",
        &benchmark_returns,
        "benchmark_returns"
    );
    validate_period!(period, len);
    Ok(utils::beta(&asset_returns, &benchmark_returns, period))
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(y_values, period)")]
/// Calculate Standard Error
///
/// Standard deviation of the regression residuals.
///
/// Parameters
/// ----------
/// y_values : list of float
///     Values
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - Standard error values
fn py_standard_error(y_values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = validate_single!(&y_values, "y_values");
    validate_period!(period, len);
    Ok(utils::standard_error(&y_values, period))
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(y_values, period)")]
/// Calculate Standard Error (alias for standard_error)
fn py_stderr(y_values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = validate_single!(&y_values, "y_values");
    validate_period!(period, len);
    Ok(utils::standard_error(&y_values, period))
}

// ==================== 价格变换指标包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(open, high, low, close)")]
/// Calculate Average Price (OHLC/4)
///
/// Simple average of open, high, low, close prices.
///
/// Returns
/// -------
/// list of float - Average prices
fn py_avgprice(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::avgprice(&open, &high, &low, &close), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low)")]
/// Calculate Median Price (HL/2)
///
/// Average of high and low prices.
///
/// Returns
/// -------
/// list of float - Median prices
fn py_medprice(high: Vec<f64>, low: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = high.len();
    ok_or_nan_vec(indicators::medprice(&high, &low), len)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close)")]
/// Calculate Typical Price (HLC/3)
///
/// Average of high, low, and close prices.
///
/// Returns
/// -------
/// list of float - Typical prices
fn py_typprice(high: Vec<f64>, low: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = high.len();
    ok_or_nan_vec(indicators::typprice(&high, &low, &close), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_wclprice(high: Vec<f64>, low: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = high.len();
    ok_or_nan_vec(indicators::wclprice(&high, &low, &close), len)
}

// ==================== 数学运算函数包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
fn py_max(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::max(&values, period), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_min(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::min(&values, period), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_sum(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::sum(&values, period), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_sqrt(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::sqrt(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_ln(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::ln(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_log10(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::log10(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_exp(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::exp(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_abs(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::abs(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_ceil(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::ceil(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_floor(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::floor(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_sin(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::sin(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_cos(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::cos(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_tan(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::tan(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_asin(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::asin(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_acos(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::acos(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_atan(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::atan(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_sinh(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::sinh(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_cosh(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::cosh(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_tanh(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(utils::tanh(&values), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_add(values1: Vec<f64>, values2: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values1.len();
    ok_or_nan_vec(utils::add(&values1, &values2), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_sub(values1: Vec<f64>, values2: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values1.len();
    ok_or_nan_vec(utils::sub(&values1, &values2), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_mult(values1: Vec<f64>, values2: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values1.len();
    ok_or_nan_vec(utils::mult(&values1, &values2), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_div(values1: Vec<f64>, values2: Vec<f64>) -> PyResult<Vec<f64>> {
    let len = values1.len();
    ok_or_nan_vec(utils::div(&values1, &values2), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_minmax(values: Vec<f64>, period: usize) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = values.len();
    ok_or_nan_vec2(utils::minmax(&values, period), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_minmaxindex(values: Vec<f64>, period: usize) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = values.len();
    ok_or_nan_vec2(utils::minmaxindex(&values, period), len)
}

// ==================== 扩展蜡烛图形态包装 ====================

#[cfg(feature = "python")]
#[pyfunction]
fn py_shooting_star(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::shooting_star(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_marubozu(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::marubozu(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_spinning_top(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::spinning_top(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, body_threshold=0.1))]
#[pyo3(text_signature = "(open, high, low, close, body_threshold=0.1)")]
/// Detect Dragonfly Doji Candlestick Pattern
///
/// Identifies dragonfly doji patterns characterized by a long lower shadow with
/// open/close near the high and minimal upper shadow. Forms a "T" shape. Indicates
/// strong rejection of lower prices and potential bullish reversal at support levels.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// body_threshold : float, optional
///     Maximum body-to-range ratio (default: 0.1)
///
/// Returns
/// -------
/// list of float - 100 where dragonfly doji detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> dd = py_dragonfly_doji([10.5], [10.6], [9.8], [10.55])
/// >>> dd`[0]`  # Dragonfly doji detected
/// 100.0
fn py_dragonfly_doji(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    body_threshold: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::dragonfly_doji(
        &open,
        &high,
        &low,
        &close,
        body_threshold.unwrap_or(0.1),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, body_threshold=0.1))]
#[pyo3(text_signature = "(open, high, low, close, body_threshold=0.1)")]
/// Detect Gravestone Doji Candlestick Pattern
///
/// Identifies gravestone doji patterns characterized by a long upper shadow with
/// open/close near the low and minimal lower shadow. Forms an inverted "T" shape.
/// Indicates strong rejection of higher prices and potential bearish reversal at
/// resistance levels.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// body_threshold : float, optional
///     Maximum body-to-range ratio (default: 0.1)
///
/// Returns
/// -------
/// list of float - 100 where gravestone doji detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> gd = py_gravestone_doji([10.0], [10.8], [9.95], [10.05])
/// >>> gd`[0]`  # Gravestone doji detected
/// 100.0
fn py_gravestone_doji(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    body_threshold: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::gravestone_doji(
        &open,
        &high,
        &low,
        &close,
        body_threshold.unwrap_or(0.1),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, body_threshold=0.1))]
#[pyo3(text_signature = "(open, high, low, close, body_threshold=0.1)")]
/// Detect Long-Legged Doji Candlestick Pattern
///
/// Identifies long-legged doji patterns with long shadows both above and below a
/// small body. Open and close are near the middle of the range. Indicates extreme
/// indecision and volatility with neither bulls nor bears in control. Often precedes
/// major price movements.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// body_threshold : float, optional
///     Maximum body-to-range ratio (default: 0.1)
///
/// Returns
/// -------
/// list of float - 100 where long-legged doji detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> lld = py_long_legged_doji([10.3], [11.0], [9.5], [10.35])
/// >>> lld`[0]`  # Long-legged doji detected
/// 100.0
fn py_long_legged_doji(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    body_threshold: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::long_legged_doji(
        &open,
        &high,
        &low,
        &close,
        body_threshold.unwrap_or(0.1),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, close, tolerance=0.01))]
#[pyo3(text_signature = "(open, high, close, tolerance=0.01)")]
/// Detect Tweezers Top Candlestick Pattern
///
/// Identifies tweezers top patterns where two consecutive candles have nearly equal
/// highs. First candle is bullish, second is bearish. The matching highs suggest
/// strong resistance and potential bearish reversal at market tops.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// close : list of float
///     Closing prices
/// tolerance : float, optional
///     Maximum price difference ratio for matching highs (default: 0.01)
///
/// Returns
/// -------
/// list of float - 100 where tweezers top detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> tt = py_tweezers_top([10.0, 10.5], [11.0, 11.02], [10.8, 10.3])
/// >>> tt`[1]`  # Tweezers top detected on second candle
/// 100.0
fn py_tweezers_top(
    open: Vec<f64>,
    high: Vec<f64>,
    close: Vec<f64>,
    tolerance: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::tweezers_top(
        &open,
        &high,
        &close,
        tolerance.unwrap_or(0.01),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, low, close, tolerance=0.01))]
#[pyo3(text_signature = "(open, low, close, tolerance=0.01)")]
/// Detect Tweezers Bottom Candlestick Pattern
///
/// Identifies tweezers bottom patterns where two consecutive candles have nearly
/// equal lows. First candle is bearish, second is bullish. The matching lows suggest
/// strong support and potential bullish reversal at market bottoms.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// tolerance : float, optional
///     Maximum price difference ratio for matching lows (default: 0.01)
///
/// Returns
/// -------
/// list of float - 100 where tweezers bottom detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> tb = py_tweezers_bottom([10.5, 10.0], [9.0, 8.98], [10.2, 10.7])
/// >>> tb`[1]`  # Tweezers bottom detected on second candle
/// 100.0
fn py_tweezers_bottom(
    open: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    tolerance: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::tweezers_bottom(
        &open,
        &low,
        &close,
        tolerance.unwrap_or(0.01),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_rising_three_methods(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::rising_three_methods(
        &open, &high, &low, &close,
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_falling_three_methods(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::falling_three_methods(
        &open, &high, &low, &close,
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, body_threshold=0.1))]
#[pyo3(text_signature = "(open, high, low, close, body_threshold=0.1)")]
/// Detect Harami Cross Candlestick Pattern
///
/// Identifies harami cross patterns where a large candle is followed by a doji
/// contained within the first candle's body. The doji's indecision after a strong
/// move suggests potential trend reversal. Bullish harami cross appears in downtrends,
/// bearish in uptrends.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// body_threshold : float, optional
///     Maximum body-to-range ratio for doji (default: 0.1)
///
/// Returns
/// -------
/// list of float - 100 for bullish, -100 for bearish harami cross, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> hc = py_harami_cross([11.0, 10.5], [11.2, 10.6], [10.5, 10.4], [10.6, 10.52])
/// >>> hc`[1]`  # Bullish harami cross detected
/// 100.0
fn py_harami_cross(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    body_threshold: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::harami_cross(
        &open,
        &high,
        &low,
        &close,
        body_threshold.unwrap_or(0.1),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, body_threshold=0.1))]
#[pyo3(text_signature = "(open, high, low, close, body_threshold=0.1)")]
/// Detect Morning Doji Star Candlestick Pattern
///
/// Identifies morning doji star patterns, a three-candle bullish reversal formation.
/// Consists of: (1) long bearish candle, (2) doji gapping down, (3) long bullish
/// candle closing above the first candle's midpoint. Signals potential trend reversal
/// from bearish to bullish.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// body_threshold : float, optional
///     Maximum body-to-range ratio for middle doji (default: 0.1)
///
/// Returns
/// -------
/// list of float - 100 where morning doji star detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> mds = py_morning_doji_star([11.0, 10.0, 10.1], [11.0, 10.1, 11.2], [10.0, 9.8, 10.0], [10.0, 9.95, 11.0])
/// >>> mds`[2]`  # Morning doji star detected
/// 100.0
fn py_morning_doji_star(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    body_threshold: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::morning_doji_star(
        &open,
        &high,
        &low,
        &close,
        body_threshold.unwrap_or(0.1),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, body_threshold=0.1))]
#[pyo3(text_signature = "(open, high, low, close, body_threshold=0.1)")]
/// Detect Evening Doji Star Candlestick Pattern
///
/// Identifies evening doji star patterns, a three-candle bearish reversal formation.
/// Consists of: (1) long bullish candle, (2) doji gapping up, (3) long bearish
/// candle closing below the first candle's midpoint. Signals potential trend reversal
/// from bullish to bearish.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// body_threshold : float, optional
///     Maximum body-to-range ratio for middle doji (default: 0.1)
///
/// Returns
/// -------
/// list of float - -100 where evening doji star detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> eds = py_evening_doji_star([10.0, 11.0, 10.9], [10.0, 11.1, 11.0], [10.0, 10.8, 9.8], [11.0, 11.05, 10.0])
/// >>> eds`[2]`  # Evening doji star detected
/// -100.0
fn py_evening_doji_star(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    body_threshold: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::evening_doji_star(
        &open,
        &high,
        &low,
        &close,
        body_threshold.unwrap_or(0.1),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_three_inside(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::three_inside(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_three_outside(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::three_outside(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, body_threshold=0.1))]
#[pyo3(text_signature = "(open, high, low, close, body_threshold=0.1)")]
/// Detect Abandoned Baby Candlestick Pattern
///
/// Identifies abandoned baby patterns, a rare three-candle reversal formation with
/// gaps. Middle candle is a doji that gaps away from both surrounding candles,
/// appearing "abandoned". Bullish version signals reversal from down to up trend,
/// bearish version signals reversal from up to down trend.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// body_threshold : float, optional
///     Maximum body-to-range ratio for middle doji (default: 0.1)
///
/// Returns
/// -------
/// list of float - 100 for bullish, -100 for bearish abandoned baby, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> ab = py_abandoned_baby([11.0, 9.5, 9.6], [11.0, 9.6, 10.5], [10.0, 9.4, 9.5], [10.0, 9.5, 10.5])
/// >>> ab`[2]`  # Bullish abandoned baby detected
/// 100.0
fn py_abandoned_baby(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    body_threshold: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::abandoned_baby(
        &open,
        &high,
        &low,
        &close,
        body_threshold.unwrap_or(0.1),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_kicking(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::kicking(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, lookback=10))]
#[pyo3(text_signature = "(open, high, low, close, lookback=10)")]
/// Detect Long Line Candlestick Pattern
///
/// Identifies candles with exceptionally long bodies relative to recent candles,
/// indicating strong directional pressure. Long white (bullish) lines show strong
/// buying, long black (bearish) lines show strong selling. Body length is compared
/// against the average of recent candles.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// lookback : int, optional
///     Period to calculate average body length (default: 10)
///
/// Returns
/// -------
/// list of float - 100 for bullish long line, -100 for bearish, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> ll = py_long_line([10.0, 10.1], [10.5, 11.5], [9.8, 10.0], [10.2, 11.4], lookback=10)
/// >>> ll`[1]`  # Long bullish line detected
/// 100.0
fn py_long_line(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    lookback: Option<usize>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::long_line(
        &open,
        &high,
        &low,
        &close,
        lookback.unwrap_or(10),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, lookback=10))]
#[pyo3(text_signature = "(open, high, low, close, lookback=10)")]
/// Detect Short Line Candlestick Pattern
///
/// Identifies candles with exceptionally short bodies relative to recent candles,
/// indicating weak directional pressure or consolidation. Short bodies suggest
/// indecision or equilibrium between buyers and sellers. Body length is compared
/// against the average of recent candles.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// lookback : int, optional
///     Period to calculate average body length (default: 10)
///
/// Returns
/// -------
/// list of float - 100 where short line detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> sl = py_short_line([10.0, 10.2], [10.3, 10.5], [9.9, 10.1], [10.1, 10.25], lookback=10)
/// >>> sl`[1]`  # Short line detected
/// 100.0
fn py_short_line(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    lookback: Option<usize>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::short_line(
        &open,
        &high,
        &low,
        &close,
        lookback.unwrap_or(10),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, body_threshold=0.1))]
#[pyo3(text_signature = "(open, high, low, close, body_threshold=0.1)")]
/// Detect Doji Star Candlestick Pattern
///
/// Identifies doji star patterns where a doji gaps away from the previous candle's
/// body. The gap indicates a potential shift in sentiment. Bullish doji star gaps
/// down after a bearish candle, bearish doji star gaps up after a bullish candle.
/// Signals potential trend reversal.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// body_threshold : float, optional
///     Maximum body-to-range ratio for doji (default: 0.1)
///
/// Returns
/// -------
/// list of float - 100 for bullish, -100 for bearish doji star, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> ds = py_doji_star([11.0, 10.0], [11.0, 10.1], [10.0, 9.8], [10.0, 9.95])
/// >>> ds`[1]`  # Bullish doji star detected
/// 100.0
fn py_doji_star(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    body_threshold: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::doji_star(
        &open,
        &high,
        &low,
        &close,
        body_threshold.unwrap_or(0.1),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_identical_three_crows(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::identical_three_crows(
        &open, &high, &low, &close,
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, tolerance=0.01))]
#[pyo3(text_signature = "(open, high, low, close, tolerance=0.01)")]
/// Detect Stick Sandwich Candlestick Pattern
///
/// Identifies stick sandwich patterns, a three-candle bullish reversal formation.
/// Two bearish candles with matching closes "sandwich" a bullish middle candle.
/// The matching closes at support suggest buyers are defending a level, indicating
/// potential upside reversal.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// tolerance : float, optional
///     Maximum price difference ratio for matching closes (default: 0.01)
///
/// Returns
/// -------
/// list of float - 100 where stick sandwich detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> ss = py_stick_sandwich([11.0, 10.0, 10.5], [11.0, 10.8, 11.0], [10.0, 10.0, 10.0], [10.0, 10.5, 10.02])
/// >>> ss`[2]`  # Stick sandwich detected
/// 100.0
fn py_stick_sandwich(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    tolerance: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::stick_sandwich(
        &open,
        &high,
        &low,
        &close,
        tolerance.unwrap_or(0.01),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, body_threshold=0.1))]
#[pyo3(text_signature = "(open, high, low, close, body_threshold=0.1)")]
/// Detect Tristar Candlestick Pattern
///
/// Identifies tristar patterns consisting of three consecutive doji candles,
/// forming a reversal signal. The middle doji should gap away from the surrounding
/// dojis. Bullish tristar appears at bottoms, bearish at tops. Rare pattern indicating
/// extreme indecision before a trend change.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// body_threshold : float, optional
///     Maximum body-to-range ratio for doji (default: 0.1)
///
/// Returns
/// -------
/// list of float - 100 for bullish, -100 for bearish tristar, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> ts = py_tristar([10.0, 9.5, 10.0], [10.2, 9.6, 10.2], [9.8, 9.3, 9.8], [10.05, 9.52, 10.03])
/// >>> ts`[2]`  # Bullish tristar detected
/// 100.0
fn py_tristar(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    body_threshold: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::tristar(
        &open,
        &high,
        &low,
        &close,
        body_threshold.unwrap_or(0.1),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_upside_gap_two_crows(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::upside_gap_two_crows(
        &open, &high, &low, &close,
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_gap_sidesidewhite(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::gap_sidesidewhite(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_takuri(open: Vec<f64>, high: Vec<f64>, low: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::takuri(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_homing_pigeon(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::homing_pigeon(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, tolerance=0.01))]
#[pyo3(text_signature = "(open, high, low, close, tolerance=0.01)")]
/// Detect Matching Low Candlestick Pattern
///
/// Identifies matching low patterns where two consecutive bearish candles have
/// nearly equal closing lows. The matching lows suggest a support level is being
/// tested and may hold, indicating potential bullish reversal. Pattern appears
/// during downtrends.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// tolerance : float, optional
///     Maximum price difference ratio for matching closes (default: 0.01)
///
/// Returns
/// -------
/// list of float - 100 where matching low detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> ml = py_matching_low([10.5, 10.2], [10.5, 10.2], [9.0, 8.98], [9.0, 9.02])
/// >>> ml`[1]`  # Matching low detected
/// 100.0
fn py_matching_low(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    tolerance: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::matching_low(
        &open,
        &high,
        &low,
        &close,
        tolerance.unwrap_or(0.01),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, tolerance=0.005))]
#[pyo3(text_signature = "(open, high, low, close, tolerance=0.005)")]
/// Detect Separating Lines Candlestick Pattern
///
/// Identifies separating lines patterns where two candles of opposite color have
/// nearly equal opening prices but close in opposite directions. The second candle's
/// strong move confirms trend continuation. Bullish version shows uptrend continuation,
/// bearish version shows downtrend continuation.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// tolerance : float, optional
///     Maximum price difference ratio for matching opens (default: 0.005)
///
/// Returns
/// -------
/// list of float - 100 for bullish, -100 for bearish separating lines, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> sl = py_separating_lines([10.0, 10.02], [10.5, 11.0], [9.5, 10.0], [9.8, 10.8])
/// >>> sl`[1]`  # Bullish separating lines detected
/// 100.0
fn py_separating_lines(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    tolerance: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::separating_lines(
        &open,
        &high,
        &low,
        &close,
        tolerance.unwrap_or(0.005),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_thrusting(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::thrusting(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, tolerance=0.01))]
#[pyo3(text_signature = "(open, high, low, close, tolerance=0.01)")]
/// Detect In-Neck Candlestick Pattern
///
/// Identifies in-neck patterns, a bearish continuation formation. After a long
/// bearish candle, a small bullish candle closes near the previous candle's low,
/// failing to penetrate significantly. The weak bounce suggests continued downside
/// pressure and trend continuation.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// tolerance : float, optional
///     Maximum price difference for close matching previous low (default: 0.01)
///
/// Returns
/// -------
/// list of float - -100 where in-neck pattern detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> inn = py_inneck([11.0, 9.5], [11.0, 10.0], [9.0, 9.5], [9.0, 9.05])
/// >>> inn`[1]`  # In-neck pattern detected
/// -100.0
fn py_inneck(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    tolerance: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::inneck(
        &open,
        &high,
        &low,
        &close,
        tolerance.unwrap_or(0.01),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, tolerance=0.01))]
#[pyo3(text_signature = "(open, high, low, close, tolerance=0.01)")]
/// Detect On-Neck Candlestick Pattern
///
/// Identifies on-neck patterns, a bearish continuation formation similar to in-neck.
/// After a long bearish candle, a small bullish candle closes at or very near the
/// previous candle's close. The failure to close above suggests sellers remain in
/// control and downtrend continues.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// tolerance : float, optional
///     Maximum price difference for matching closes (default: 0.01)
///
/// Returns
/// -------
/// list of float - -100 where on-neck pattern detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> onn = py_onneck([11.0, 9.5], [11.0, 10.2], [9.0, 9.5], [9.0, 9.02])
/// >>> onn`[1]`  # On-neck pattern detected
/// -100.0
fn py_onneck(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    tolerance: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::onneck(
        &open,
        &high,
        &low,
        &close,
        tolerance.unwrap_or(0.01),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_advance_block(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::advance_block(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_stalled_pattern(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::stalled_pattern(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_belthold(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::belthold(&open, &high, &low, &close)?)
}

// 新增蜡烛图形态（第四批 - TA-Lib 61 完整集合补充）
#[cfg(feature = "python")]
#[pyfunction]
fn py_concealing_baby_swallow(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::concealing_baby_swallow(
        &open, &high, &low, &close,
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, tolerance=0.005))]
#[pyo3(text_signature = "(open, high, low, close, tolerance=0.005)")]
/// Detect Counterattack Candlestick Pattern
///
/// Identifies counterattack patterns where two opposite-colored candles have matching
/// closes but move in opposite directions. Bullish counterattack: bearish candle
/// followed by bullish candle opening lower but closing at same level. Bearish
/// counterattack: opposite. Signals potential trend reversal.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// tolerance : float, optional
///     Maximum price difference for matching closes (default: 0.005)
///
/// Returns
/// -------
/// list of float - 100 for bullish, -100 for bearish counterattack, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> ca = py_counterattack([11.0, 9.5], [11.0, 10.5], [10.0, 9.5], [10.0, 10.02])
/// >>> ca`[1]`  # Bullish counterattack detected
/// 100.0
fn py_counterattack(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    tolerance: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::counterattack(
        &open,
        &high,
        &low,
        &close,
        tolerance.unwrap_or(0.005),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, body_threshold=0.15))]
#[pyo3(text_signature = "(open, high, low, close, body_threshold=0.15)")]
/// Detect High Wave Candlestick Pattern
///
/// Identifies high wave candles characterized by long upper and lower shadows with
/// a very small body. Similar to long-legged doji but allows slightly larger body.
/// Indicates extreme volatility and market indecision. Often signals potential
/// reversal or consolidation.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// body_threshold : float, optional
///     Maximum body-to-range ratio (default: 0.15)
///
/// Returns
/// -------
/// list of float - 100 where high wave detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> hw = py_highwave([10.3], [11.5], [9.0], [10.5])
/// >>> hw`[0]`  # High wave detected
/// 100.0
fn py_highwave(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    body_threshold: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::highwave(
        &open,
        &high,
        &low,
        &close,
        body_threshold.unwrap_or(0.15),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_hikkake(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::hikkake(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_hikkake_mod(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::hikkake_mod(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_ladder_bottom(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::ladder_bottom(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_mat_hold(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::mat_hold(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (open, high, low, close, body_threshold=0.1))]
#[pyo3(text_signature = "(open, high, low, close, body_threshold=0.1)")]
/// Detect Rickshaw Man Candlestick Pattern
///
/// Identifies rickshaw man patterns, a doji with long shadows and open/close near
/// the middle of the range. Similar to long-legged doji but specifically requires
/// the body to be centered. Indicates extreme indecision with bulls and bears
/// fighting to a standstill. Often precedes reversals.
///
/// Parameters
/// ----------
/// open : list of float
///     Opening prices
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// body_threshold : float, optional
///     Maximum body-to-range ratio (default: 0.1)
///
/// Returns
/// -------
/// list of float - 100 where rickshaw man detected, 0 otherwise
///
/// Raises
/// ------
/// ValueError
///     If input arrays have different lengths or insufficient data
///
/// Examples
/// --------
/// >>> rm = py_rickshaw_man([10.5], [11.5], [9.5], [10.55])
/// >>> rm`[0]`  # Rickshaw man detected
/// 100.0
fn py_rickshaw_man(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    body_threshold: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::rickshaw_man(
        &open,
        &high,
        &low,
        &close,
        body_threshold.unwrap_or(0.1),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_unique_3_river(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::unique_3_river(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_xside_gap_3_methods(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::xside_gap_3_methods(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_closing_marubozu(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::closing_marubozu(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_breakaway(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::breakaway(&open, &high, &low, &close)?)
}

// ==================== Overlap Studies 指标包装 ====================
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period)")]
/// Calculate Midpoint over Period
///
/// Average of highest and lowest values over the lookback period.
/// (Highest + Lowest) / 2
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - Midpoint values
fn py_midpoint(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    Ok(indicators::midpoint(&values, period)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, period)")]
/// Calculate Midprice over Period
///
/// Average of highest high and lowest low over the lookback period.
/// (Highest High + Lowest Low) / 2
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - Midprice values
fn py_midprice(high: Vec<f64>, low: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    Ok(indicators::midprice(&high, &low, period)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period)")]
/// Calculate Triangular Moving Average (TRIMA)
///
/// Double-smoothed SMA with triangular weighting.
/// More weight to middle of period, smoother than SMA.
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int
///     Lookback period
///
/// Returns
/// -------
/// list of float - TRIMA values
fn py_trima(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    Ok(indicators::trima(&values, period)?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, acceleration=0.02, maximum=0.2)")]
/// Calculate Parabolic SAR (Stop and Reverse)
///
/// Trailing stop system that follows price. Dots flip from
/// below to above price on trend reversals.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// acceleration : float, optional
///     Acceleration factor step (default: 0.02)
/// maximum : float, optional
///     Maximum acceleration (default: 0.2)
///
/// Returns
/// -------
/// list of float - SAR values
fn py_sar(
    high: Vec<f64>,
    low: Vec<f64>,
    acceleration: Option<f64>,
    maximum: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::sar(
        &high,
        &low,
        acceleration.unwrap_or(0.02),
        maximum.unwrap_or(0.2),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn py_sarext(
    high: Vec<f64>,
    low: Vec<f64>,
    start_value: Option<f64>,
    offset_on_reverse: Option<f64>,
    af_init_long: Option<f64>,
    af_long: Option<f64>,
    af_max_long: Option<f64>,
    af_init_short: Option<f64>,
    af_short: Option<f64>,
    af_max_short: Option<f64>,
) -> PyResult<Vec<f64>> {
    Ok(indicators::sarext(
        &high,
        &low,
        start_value.unwrap_or(0.0),
        offset_on_reverse.unwrap_or(0.0),
        af_init_long.unwrap_or(0.02),
        af_long.unwrap_or(0.02),
        af_max_long.unwrap_or(0.2),
        af_init_short.unwrap_or(0.02),
        af_short.unwrap_or(0.02),
        af_max_short.unwrap_or(0.2),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_mama(
    values: Vec<f64>,
    fast_limit: Option<f64>,
    slow_limit: Option<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    Ok(indicators::mama(
        &values,
        fast_limit.unwrap_or(0.5),
        slow_limit.unwrap_or(0.05),
    )?)
}

// ==================== SFG 交易信号指标包装 ====================
#[cfg(feature = "python")]
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn py_ai_supertrend(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    k: Option<usize>,
    n: Option<usize>,
    price_trend: Option<usize>,
    predict_trend: Option<usize>,
    st_length: Option<usize>,
    st_multiplier: Option<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::ai_supertrend(
            &high,
            &low,
            &close,
            k.unwrap_or(5),
            n.unwrap_or(100),
            price_trend.unwrap_or(10),
            predict_trend.unwrap_or(10),
            st_length.unwrap_or(10),
            st_multiplier.unwrap_or(3.0),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_ai_momentum_index(
    close: Vec<f64>,
    k: Option<usize>,
    trend_length: Option<usize>,
    smooth: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::ai_momentum_index(
            &close,
            k.unwrap_or(50),
            trend_length.unwrap_or(14),
            smooth.unwrap_or(3),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_dynamic_macd(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    fast_length: Option<usize>,
    slow_length: Option<usize>,
    signal_smooth: Option<usize>,
) -> PyResult<Vec5F64> {
    let len = close.len();
    ok_or_nan_vec5(
        indicators::dynamic_macd(
            &open,
            &high,
            &low,
            &close,
            fast_length.unwrap_or(12),
            slow_length.unwrap_or(26),
            signal_smooth.unwrap_or(9),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_atr2_signals(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    trend_length: Option<usize>,
    confirmation_threshold: Option<f64>,
    momentum_window: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec3(
        indicators::atr2_signals(
            &high,
            &low,
            &close,
            &volume,
            trend_length.unwrap_or(14),
            confirmation_threshold.unwrap_or(2.0),
            momentum_window.unwrap_or(10),
        ),
        len,
    )
}

// ==================== SFG ML 增强版指标包装 ====================

/// AI SuperTrend ML 增强版
/// 返回: (supertrend, direction, buy_signals, sell_signals, stop_loss, take_profit)
#[cfg(feature = "python")]
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn py_ai_supertrend_ml(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    st_length: Option<usize>,
    st_multiplier: Option<f64>,
    model_type: Option<String>,
    lookback: Option<usize>,
    train_window: Option<usize>,
) -> PyResult<Vec6F64> {
    let len = close.len();
    let model_str = model_type.unwrap_or_else(|| "linreg".to_string());
    let result = indicators::ai_supertrend_ml(
        &high,
        &low,
        &close,
        st_length.unwrap_or(10),
        st_multiplier.unwrap_or(3.0),
        &model_str,
        lookback.unwrap_or(10),
        train_window.unwrap_or(200),
    )
    .map(|result| {
        (
            result.supertrend,
            result.direction,
            result.buy_signals,
            result.sell_signals,
            result.stop_loss,
            result.take_profit,
        )
    });
    ok_or_nan_vec6(result, len)
}

/// ATR2 信号 ML 增强版
/// 返回: (rsi, buy_signals, sell_signals, signal_strength, stop_loss, take_profit)
#[cfg(feature = "python")]
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn py_atr2_signals_ml(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    rsi_period: Option<usize>,
    atr_period: Option<usize>,
    ridge_alpha: Option<f64>,
    momentum_window: Option<usize>,
) -> PyResult<Vec6F64> {
    let len = close.len();
    let result = indicators::atr2_signals_ml(
        &high,
        &low,
        &close,
        &volume,
        rsi_period.unwrap_or(14),
        atr_period.unwrap_or(14),
        ridge_alpha.unwrap_or(1.0),
        momentum_window.unwrap_or(10),
    )
    .map(|result| {
        (
            result.rsi,
            result.buy_signals,
            result.sell_signals,
            result.signal_strength,
            result.stop_loss,
            result.take_profit,
        )
    });
    ok_or_nan_vec6(result, len)
}

/// AI Momentum Index ML 增强版
/// 返回: (rsi, predicted_momentum, zero_cross_buy, zero_cross_sell, overbought, oversold)
#[cfg(feature = "python")]
#[pyfunction]
fn py_ai_momentum_index_ml(
    close: Vec<f64>,
    rsi_period: Option<usize>,
    smooth_period: Option<usize>,
    use_polynomial: Option<bool>,
    lookback: Option<usize>,
    train_window: Option<usize>,
) -> PyResult<Vec6F64> {
    let len = close.len();
    let result = indicators::ai_momentum_index_ml(
        &close,
        rsi_period.unwrap_or(14),
        smooth_period.unwrap_or(3),
        use_polynomial.unwrap_or(false),
        lookback.unwrap_or(5),
        train_window.unwrap_or(200),
    )
    .map(|result| {
        (
            result.rsi,
            result.predicted_momentum,
            result.zero_cross_buy,
            result.zero_cross_sell,
            result.overbought,
            result.oversold,
        )
    });
    ok_or_nan_vec6(result, len)
}

/// Pivot 买卖信号
/// 返回: (pivot, r1, r2, s1, s2, buy_signals, sell_signals)
#[cfg(feature = "python")]
#[pyfunction]
fn py_pivot_buy_sell(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    lookback: Option<usize>,
) -> PyResult<Vec7F64> {
    let len = close.len();
    let result =
        indicators::pivot_buy_sell(&high, &low, &close, lookback.unwrap_or(5)).map(|result| {
            (
                result.pivot,
                result.r1,
                result.r2,
                result.s1,
                result.s2,
                result.buy_signals,
                result.sell_signals,
            )
        });
    ok_or_nan_vec7(result, len)
}

// ==================== SFG 市场结构分析包装 ====================

/// 背离检测
/// 返回: (divergence_type, strength)
/// divergence_type: 0=None, 1=RegularBullish, 2=RegularBearish, 3=HiddenBullish, 4=HiddenBearish
#[cfg(feature = "python")]
#[pyfunction]
fn py_detect_divergence(
    price: Vec<f64>,
    indicator: Vec<f64>,
    lookback: Option<usize>,
    threshold: Option<f64>,
) -> PyResult<(Vec<i32>, Vec<f64>)> {
    let result = indicators::detect_divergence(
        &price,
        &indicator,
        lookback.unwrap_or(5),
        threshold.unwrap_or(0.01),
    )?;
    let divergence_type: Vec<i32> = result
        .divergence_type
        .iter()
        .map(|d| match d {
            indicators::DivergenceType::None => 0,
            indicators::DivergenceType::RegularBullish => 1,
            indicators::DivergenceType::RegularBearish => 2,
            indicators::DivergenceType::HiddenBullish => 3,
            indicators::DivergenceType::HiddenBearish => 4,
        })
        .collect();
    Ok((divergence_type, result.strength))
}

/// FVG (Fair Value Gap) 信号
/// 返回: (bullish_fvg, bearish_fvg, fvg_upper, fvg_lower)
#[cfg(feature = "python")]
#[pyfunction]
fn py_fvg_signals(high: Vec<f64>, low: Vec<f64>) -> PyResult<Vec4F64> {
    let (bullish, bearish, upper, lower) = indicators::fvg_signals(&high, &low)?;
    Ok((bullish, bearish, upper, lower))
}

/// 成交量过滤器
/// 返回: (above_average, relative_volume, volume_spike)
#[cfg(feature = "python")]
#[pyfunction]
fn py_volume_filter(
    volume: Vec<f64>,
    period: Option<usize>,
) -> PyResult<(Vec<bool>, Vec<f64>, Vec<bool>)> {
    let result = indicators::volume_filter(&volume, period.unwrap_or(20))?;
    Ok((
        result.above_average,
        result.relative_volume,
        result.volume_spike,
    ))
}

// ==================== SFG 信号工具包装 ====================

#[cfg(feature = "python")]
fn build_sfg_signal(buy: Vec<f64>, sell: Vec<f64>) -> HazeResult<indicators::SFGSignal> {
    let len = validate_pair!(&buy, "buy", &sell, "sell");
    let mut signal = indicators::SFGSignal::new(len);

    for i in 0..len {
        let buy_val = buy[i];
        let sell_val = sell[i];
        signal.buy_signals[i] = buy_val;
        signal.sell_signals[i] = sell_val;
        signal.signal_strength[i] = buy_val.max(sell_val).clamp(0.0, 1.0);
    }

    Ok(signal)
}

/// 简单信号组合 (加权平均)
/// 返回: (combined_buy, combined_sell)
#[cfg(feature = "python")]
#[pyfunction]
fn py_combine_signals(
    buy1: Vec<f64>,
    sell1: Vec<f64>,
    buy2: Vec<f64>,
    sell2: Vec<f64>,
    weight1: Option<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let w1 = weight1.unwrap_or(0.5);
    crate::errors::validation::validate_range("weight1", w1, 0.0, 1.0)?;
    let weights = [w1, 1.0 - w1];
    let sig1 = build_sfg_signal(buy1, sell1)?;
    let sig2 = build_sfg_signal(buy2, sell2)?;
    let combined = indicators::combine_signals(&[&sig1, &sig2], Some(&weights))?;
    Ok((
        combined.buy_signals,
        combined.sell_signals,
        combined.signal_strength,
    ))
}

/// 计算止损止盈
/// 返回: (stop_loss, take_profit)
#[cfg(feature = "python")]
#[pyfunction]
fn py_calculate_stops(
    close: Vec<f64>,
    atr_values: Vec<f64>,
    buy_signals: Vec<f64>,
    sell_signals: Vec<f64>,
    sl_multiplier: Option<f64>,
    tp_multiplier: Option<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let sl_mult = sl_multiplier.unwrap_or(1.5);
    let tp_mult = tp_multiplier.unwrap_or(2.5);
    let signals = build_sfg_signal(buy_signals, sell_signals)?;
    Ok(indicators::calculate_stops(
        &close,
        &atr_values,
        &signals,
        sl_mult,
        tp_mult,
    )?)
}

/// 计算追踪止损
#[cfg(feature = "python")]
#[pyfunction]
fn py_trailing_stop(
    close: Vec<f64>,
    atr_values: Vec<f64>,
    direction: Vec<f64>,
    multiplier: Option<f64>,
) -> PyResult<Vec<f64>> {
    let mult = multiplier.unwrap_or(2.0);
    Ok(indicators::trailing_stop(
        &close,
        &atr_values,
        &direction,
        mult,
    )?)
}

// ==================== SFG 新增指标包装 ====================

/// PD Array (Premium/Discount Array) 信号
/// 返回: (buy_signals, sell_signals, stop_loss, take_profit)
#[cfg(feature = "python")]
#[pyfunction]
fn py_pd_array_signals(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    swing_lookback: Option<usize>,
) -> PyResult<Vec4F64> {
    // Compute ATR internally for convenience
    let atr_values = indicators::atr(&high, &low, &close, 14)?;
    let (buy, sell, sl, tp) = indicators::pd_array_signals(
        &high,
        &low,
        &close,
        swing_lookback.unwrap_or(20),
        &atr_values,
    )?;
    Ok((buy, sell, sl, tp))
}

/// Breaker Block 信号
/// 返回: (buy_signals, sell_signals, breaker_upper, breaker_lower)
#[cfg(feature = "python")]
#[pyfunction]
fn py_breaker_block_signals(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    lookback: Option<usize>,
) -> PyResult<Vec4F64> {
    let (buy, sell, upper, lower) =
        indicators::breaker_block_signals(&open, &high, &low, &close, lookback.unwrap_or(20))?;
    Ok((buy, sell, upper, lower))
}

/// General Parameters 信号 (EMA通道 + 网格入场)
/// 返回: (buy_signals, sell_signals, stop_loss, take_profit)
#[cfg(feature = "python")]
#[pyfunction]
fn py_general_parameters_signals(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    ema_fast: Option<usize>,
    ema_slow: Option<usize>,
    atr_period: Option<usize>,
    grid_multiplier: Option<f64>,
) -> PyResult<Vec4F64> {
    let len = close.len();
    ok_or_nan_vec4(
        indicators::general_parameters_signals(
            &high,
            &low,
            &close,
            ema_fast.unwrap_or(20),
            ema_slow.unwrap_or(50),
            atr_period.unwrap_or(14),
            grid_multiplier.unwrap_or(1.0),
        ),
        len,
    )
}

/// Linear Regression + Supply/Demand Zones 信号
/// 返回: (buy_signals, sell_signals, stop_loss, take_profit)
#[cfg(feature = "python")]
#[pyfunction]
fn py_linreg_supply_demand_signals(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    linreg_period: Option<usize>,
    tolerance: Option<f64>,
) -> PyResult<Vec4F64> {
    // Compute ATR internally for convenience
    let atr_values = indicators::atr(&high, &low, &close, 14)?;
    let (buy, sell, sl, tp) = indicators::linreg_supply_demand_signals(
        &high,
        &low,
        &close,
        &volume,
        &atr_values,
        linreg_period.unwrap_or(20),
        tolerance.unwrap_or(0.02),
    )?;
    Ok((buy, sell, sl, tp))
}

// ==================== 周期指标包装 (Hilbert Transform) ====================
#[cfg(feature = "python")]
#[pyfunction]
fn py_ht_dcperiod(values: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::ht_dcperiod(&values)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_ht_dcphase(values: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::ht_dcphase(&values)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_ht_phasor(values: Vec<f64>) -> PyResult<(Vec<f64>, Vec<f64>)> {
    Ok(indicators::ht_phasor(&values)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_ht_sine(values: Vec<f64>) -> PyResult<(Vec<f64>, Vec<f64>)> {
    Ok(indicators::ht_sine(&values)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_ht_trendmode(values: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::ht_trendmode(&values)?)
}

#[cfg(test)]
mod coverage_tests;

// ==================== 统计函数包装 (TA-Lib Compatible) ====================
#[cfg(feature = "python")]
#[pyfunction]
fn py_correl(values1: Vec<f64>, values2: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = validate_pair!(&values1, "values1", &values2, "values2");
    validate_period!(period, len);
    Ok(utils::correl(&values1, &values2, period))
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_linearreg(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = validate_single!(&values, "values");
    validate_period!(period, len);
    Ok(utils::linearreg(&values, period))
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_linearreg_slope(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = validate_single!(&values, "values");
    validate_period!(period, len);
    Ok(utils::linearreg_slope(&values, period))
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_linearreg_angle(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = validate_single!(&values, "values");
    validate_period!(period, len);
    Ok(utils::linearreg_angle(&values, period))
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_linearreg_intercept(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = validate_single!(&values, "values");
    validate_period!(period, len);
    Ok(utils::linearreg_intercept(&values, period))
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_var(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = validate_single!(&values, "values");
    validate_period!(period, len);
    Ok(utils::var(&values, period))
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_tsf(values: Vec<f64>, period: usize) -> PyResult<Vec<f64>> {
    let len = validate_single!(&values, "values");
    validate_period!(period, len);
    Ok(utils::tsf(&values, period))
}

// ==================== Batch 7: TA-Lib Advanced Indicators ====================
// Volume Indicators (AD already exists at line 766)
#[cfg(feature = "python")]
#[pyfunction]
fn py_adosc(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<f64>,
    fast_period: Option<usize>,
    slow_period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::chaikin_ad_oscillator(
            &high,
            &low,
            &close,
            &volume,
            fast_period.unwrap_or(3),
            slow_period.unwrap_or(10),
        ),
        len,
    )
}

// Momentum Indicators
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, fast_period=12, slow_period=26)")]
/// Calculate Absolute Price Oscillator (APO)
///
/// Difference between two EMAs. Similar to MACD but without
/// the signal line.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// fast_period : int, optional
///     Fast EMA period (default: 12)
/// slow_period : int, optional
///     Slow EMA period (default: 26)
///
/// Returns
/// -------
/// list of float - APO values (fast_ema - slow_ema)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_apo(
    close: Vec<f64>,
    fast_period: Option<usize>,
    slow_period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::apo(&close, fast_period.unwrap_or(12), slow_period.unwrap_or(26)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, fast_period=12, slow_period=26)")]
/// Calculate Percentage Price Oscillator (PPO)
///
/// Percentage difference between two EMAs. Normalizes APO
/// as percentage for comparison across different price levels.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// fast_period : int, optional
///     Fast EMA period (default: 12)
/// slow_period : int, optional
///     Slow EMA period (default: 26)
///
/// Returns
/// -------
/// list of float - PPO values as percentages
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_ppo(
    close: Vec<f64>,
    fast_period: Option<usize>,
    slow_period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::ppo(&close, fast_period.unwrap_or(12), slow_period.unwrap_or(26)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, period=14)")]
/// Calculate Chande Momentum Oscillator (CMO)
///
/// Similar to RSI but uses raw momentum sums instead of
/// smoothed averages. Values range -100 to +100.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// list of float - CMO values (-100 to +100)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_cmo(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::cmo(&close, period.unwrap_or(14)), len)
}

// Trend Indicators
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=14)")]
/// Calculate Directional Movement Index (DX)
///
/// Measures the difference between +DI and -DI.
/// Used in ADX calculation to measure trend strength.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// list of float - DX values (0-100)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_dx(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::dx(&high, &low, &close, period.unwrap_or(14)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=14)")]
/// Calculate Plus Directional Indicator (+DI)
///
/// Measures upward price movement. Part of the DMI system.
/// Higher values indicate stronger upward momentum.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// list of float - +DI values (0-100)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_plus_di(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::plus_di(&high, &low, &close, period.unwrap_or(14)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=14)")]
/// Calculate Minus Directional Indicator (-DI)
///
/// Measures downward price movement. Part of the DMI system.
/// Higher values indicate stronger downward momentum.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 14)
///
/// Returns
/// -------
/// list of float - -DI values (0-100)
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_minus_di(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::minus_di(&high, &low, &close, period.unwrap_or(14)),
        len,
    )
}

// Overlap Studies (Advanced MA)
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period=5, vfactor=0.7)")]
/// Calculate T3 Moving Average (Tilson T3)
///
/// Triple smoothed EMA with reduced lag. Uses volume factor
/// to control smoothing vs responsiveness tradeoff.
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int, optional
///     Lookback period (default: 5)
/// vfactor : float, optional
///     Volume factor 0-1 (default: 0.7). Higher = smoother.
///
/// Returns
/// -------
/// list of float - T3 values
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_t3(values: Vec<f64>, period: Option<usize>, vfactor: Option<f64>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(
        utils::t3(&values, period.unwrap_or(5), vfactor.unwrap_or(0.7)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(values, period=10, fast_period=2, slow_period=30)")]
/// Calculate Kaufman Adaptive Moving Average (KAMA)
///
/// Self-adjusting MA that adapts to market volatility.
/// Fast in trending markets, slow in choppy markets.
///
/// Parameters
/// ----------
/// values : list of float
///     Price data
/// period : int, optional
///     Efficiency ratio period (default: 10)
/// fast_period : int, optional
///     Fast EMA period (default: 2)
/// slow_period : int, optional
///     Slow EMA period (default: 30)
///
/// Returns
/// -------
/// list of float - KAMA values
///
/// Raises
/// ------
/// ValueError
///     If period <= 0 or insufficient data
fn py_kama(
    values: Vec<f64>,
    period: Option<usize>,
    fast_period: Option<usize>,
    slow_period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(
        utils::kama(
            &values,
            period.unwrap_or(10),
            fast_period.unwrap_or(2),
            slow_period.unwrap_or(30),
        ),
        len,
    )
}

// ==================== Batch 8: pandas-ta 独有指标 (180 → 190) ====================

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, period=10, bins=10)")]
/// Calculate Shannon Entropy
///
/// Measures price distribution randomness/unpredictability.
/// Higher values = more random/uncertain market.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 10)
/// bins : int, optional
///     Histogram bins (default: 10)
///
/// Returns
/// -------
/// list of float - Entropy values
fn py_entropy(close: Vec<f64>, period: Option<usize>, bins: Option<usize>) -> PyResult<Vec<f64>> {
    Ok(indicators::entropy(
        &close,
        period.unwrap_or(10),
        bins.unwrap_or(10),
    )?)
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(high, low, close, period=20, atr_period=20)")]
/// Calculate Aberration Indicator
///
/// Measures deviation from expected price movement based on
/// ATR. Identifies abnormal price behavior.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// period : int, optional
///     SMA period (default: 20)
/// atr_period : int, optional
///     ATR period (default: 20)
///
/// Returns
/// -------
/// list of float - Aberration values
fn py_aberration(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
    atr_period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::aberration(
            &high,
            &low,
            &close,
            period.unwrap_or(20),
            atr_period.unwrap_or(20),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(
    text_signature = "(high, low, close, bb_period=20, bb_std=2.0, kc_period=20, kc_atr_period=20, kc_mult=1.5)"
)]
#[allow(clippy::too_many_arguments)]
/// Calculate Squeeze Momentum Indicator
///
/// Detects when BB is inside KC (squeeze on) indicating
/// low volatility before potential breakout.
///
/// Parameters
/// ----------
/// high : list of float
///     High prices
/// low : list of float
///     Low prices
/// close : list of float
///     Closing prices
/// bb_period : int, optional
///     Bollinger Bands period (default: 20)
/// bb_std : float, optional
///     BB standard deviation (default: 2.0)
/// kc_period : int, optional
///     Keltner Channel period (default: 20)
/// kc_atr_period : int, optional
///     KC ATR period (default: 20)
/// kc_mult : float, optional
///     KC ATR multiplier (default: 1.5)
///
/// Returns
/// -------
/// tuple of (list, list, list) - (momentum, squeeze_on, squeeze_off)
fn py_squeeze(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    bb_period: Option<usize>,
    bb_std: Option<f64>,
    kc_period: Option<usize>,
    kc_atr_period: Option<usize>,
    kc_mult: Option<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec3(
        indicators::squeeze(
            &high,
            &low,
            &close,
            bb_period.unwrap_or(20),
            bb_std.unwrap_or(2.0),
            kc_period.unwrap_or(20),
            kc_atr_period.unwrap_or(20),
            kc_mult.unwrap_or(1.5),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, rsi_period=14, smooth=5, multiplier=4.236)")]
/// Calculate QQE (Quantitative Qualitative Estimation)
///
/// Smoothed RSI with dynamic volatility-based trailing stops.
/// Generates cleaner signals than standard RSI.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// rsi_period : int, optional
///     RSI period (default: 14)
/// smooth : int, optional
///     Smoothing period (default: 5)
/// multiplier : float, optional
///     ATR multiplier for bands (default: 4.236)
///
/// Returns
/// -------
/// tuple of (list, list, list) - (QQE line, trailing line, histogram)
fn py_qqe(
    close: Vec<f64>,
    rsi_period: Option<usize>,
    smooth: Option<usize>,
    multiplier: Option<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec3(
        indicators::qqe(
            &close,
            rsi_period.unwrap_or(14),
            smooth.unwrap_or(5),
            multiplier.unwrap_or(4.236),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(text_signature = "(close, period=12)")]
/// Calculate Correlation Trend Indicator (CTI)
///
/// Measures correlation between price and linear regression.
/// Values -1 to +1, high positive = strong uptrend.
///
/// Parameters
/// ----------
/// close : list of float
///     Closing prices
/// period : int, optional
///     Lookback period (default: 12)
///
/// Returns
/// -------
/// list of float - CTI values (-1 to +1)
fn py_cti(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::cti(&close, period.unwrap_or(12)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_er(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::er(&close, period.unwrap_or(10)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_bias(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::bias(&close, period.unwrap_or(20)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_psl(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::psl(&close, period.unwrap_or(12)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_rvi(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
    signal_period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::rvi(
            &open,
            &high,
            &low,
            &close,
            period.unwrap_or(10),
            signal_period.unwrap_or(4),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_inertia(
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    rvi_period: Option<usize>,
    regression_period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::inertia(
            &open,
            &high,
            &low,
            &close,
            rvi_period.unwrap_or(14),
            regression_period.unwrap_or(20),
        ),
        len,
    )
}

// ==================== Batch 9: pandas-ta 独有指标（第二批）(190 → 200) ====================

#[cfg(feature = "python")]
#[pyfunction]
fn py_alligator(
    high: Vec<f64>,
    low: Vec<f64>,
    jaw_period: Option<usize>,
    teeth_period: Option<usize>,
    lips_period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = high.len();
    ok_or_nan_vec3(
        indicators::alligator(
            &high,
            &low,
            jaw_period.unwrap_or(13),
            teeth_period.unwrap_or(8),
            lips_period.unwrap_or(5),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_efi(close: Vec<f64>, volume: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::efi(&close, &volume, period.unwrap_or(13)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_kst(
    close: Vec<f64>,
    roc1: Option<usize>,
    roc2: Option<usize>,
    roc3: Option<usize>,
    roc4: Option<usize>,
    signal_period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::kst(
            &close,
            roc1.unwrap_or(10),
            roc2.unwrap_or(15),
            roc3.unwrap_or(20),
            roc4.unwrap_or(30),
            signal_period.unwrap_or(9),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_stc(
    close: Vec<f64>,
    fast: Option<usize>,
    slow: Option<usize>,
    cycle: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::stc(
            &close,
            fast.unwrap_or(23),
            slow.unwrap_or(50),
            cycle.unwrap_or(10),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_tdfi(close: Vec<f64>, period: Option<usize>, smooth: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::tdfi(&close, period.unwrap_or(13), smooth.unwrap_or(3)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_wae(
    close: Vec<f64>,
    fast: Option<usize>,
    slow: Option<usize>,
    signal: Option<usize>,
    bb_period: Option<usize>,
    multiplier: Option<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::wae(
            &close,
            fast.unwrap_or(20),
            slow.unwrap_or(40),
            signal.unwrap_or(9),
            bb_period.unwrap_or(20),
            multiplier.unwrap_or(2.0),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_smi(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
    smooth1: Option<usize>,
    smooth2: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::smi(
            &high,
            &low,
            &close,
            period.unwrap_or(13),
            smooth1.unwrap_or(25),
            smooth2.unwrap_or(2),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_coppock(
    close: Vec<f64>,
    period1: Option<usize>,
    period2: Option<usize>,
    wma_period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::coppock(
            &close,
            period1.unwrap_or(11),
            period2.unwrap_or(14),
            wma_period.unwrap_or(10),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_pgo(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(
        indicators::pgo(&high, &low, &close, period.unwrap_or(14)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_vwma(close: Vec<f64>, volume: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::vwma(&close, &volume, period.unwrap_or(20)), len)
}

// Batch 10: 最终批次（202 → 212 指标，达成 100%）

#[cfg(feature = "python")]
#[pyfunction]
fn py_alma(
    values: Vec<f64>,
    period: Option<usize>,
    offset: Option<f64>,
    sigma: Option<f64>,
) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(
        indicators::alma(
            &values,
            period.unwrap_or(9),
            offset.unwrap_or(0.85),
            sigma.unwrap_or(6.0),
        ),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_vidya(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::vidya(&close, period.unwrap_or(14)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_pwma(values: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(indicators::pwma(&values, period.unwrap_or(5)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_sinwma(values: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(indicators::sinwma(&values, period.unwrap_or(14)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_swma(values: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(indicators::swma(&values, period.unwrap_or(7)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_bop(open: Vec<f64>, high: Vec<f64>, low: Vec<f64>, close: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(indicators::bop(&open, &high, &low, &close)?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_ssl_channel(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    period: Option<usize>,
) -> PyResult<(Vec<f64>, Vec<f64>)> {
    let len = close.len();
    ok_or_nan_vec2(
        indicators::ssl_channel(&high, &low, &close, period.unwrap_or(10)),
        len,
    )
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_cfo(close: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = close.len();
    ok_or_nan_vec(indicators::cfo(&close, period.unwrap_or(14)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_slope(values: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(indicators::slope(&values, period.unwrap_or(14)), len)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_percent_rank(values: Vec<f64>, period: Option<usize>) -> PyResult<Vec<f64>> {
    let len = values.len();
    ok_or_nan_vec(indicators::percent_rank(&values, period.unwrap_or(14)), len)
}

// ==================== 谐波形态指标包装 ====================

/// 谐波形态 Python 类
#[cfg(feature = "python")]
#[pyclass]
#[derive(Clone)]
pub struct PyHarmonicPattern {
    #[pyo3(get)]
    pub pattern_type: String,
    #[pyo3(get)]
    pub pattern_type_zh: String,
    #[pyo3(get)]
    pub is_bullish: bool,
    #[pyo3(get)]
    pub state: String,
    #[pyo3(get)]
    pub x_index: usize,
    #[pyo3(get)]
    pub x_price: f64,
    #[pyo3(get)]
    pub a_index: usize,
    #[pyo3(get)]
    pub a_price: f64,
    #[pyo3(get)]
    pub b_index: usize,
    #[pyo3(get)]
    pub b_price: f64,
    #[pyo3(get)]
    pub c_index: Option<usize>,
    #[pyo3(get)]
    pub c_price: Option<f64>,
    #[pyo3(get)]
    pub d_index: Option<usize>,
    #[pyo3(get)]
    pub d_price: Option<f64>,
    #[pyo3(get)]
    pub prz_high: Option<f64>,
    #[pyo3(get)]
    pub prz_low: Option<f64>,
    #[pyo3(get)]
    pub prz_center: Option<f64>,
    #[pyo3(get)]
    pub probability: f64,
    #[pyo3(get)]
    pub target_prices: Vec<f64>,
    #[pyo3(get)]
    pub stop_loss: Option<f64>,
}

/// 谐波形态信号（时间序列格式）
/// 返回: (signals, prz_upper, prz_lower, probability)
/// - signals: 1=看涨, -1=看跌, 0=无信号
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (high, low, close, left_bars=None, right_bars=None, min_probability=None))]
fn py_harmonics(
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    left_bars: Option<usize>,
    right_bars: Option<usize>,
    min_probability: Option<f64>,
) -> PyResult<Vec4F64> {
    Ok(indicators::harmonics::harmonics_signal(
        &high,
        &low,
        &close,
        left_bars.unwrap_or(5),
        right_bars.unwrap_or(5),
        min_probability.unwrap_or(0.5),
    )?)
}

/// 谐波形态详细信息
/// 返回 PyHarmonicPattern 列表
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (high, low, left_bars=None, right_bars=None, include_forming=None))]
fn py_harmonics_patterns(
    high: Vec<f64>,
    low: Vec<f64>,
    left_bars: Option<usize>,
    right_bars: Option<usize>,
    include_forming: Option<bool>,
) -> PyResult<Vec<PyHarmonicPattern>> {
    let patterns = indicators::harmonics::detect_all_harmonics_ext(
        &high,
        &low,
        left_bars.unwrap_or(5),
        right_bars.unwrap_or(5),
        include_forming.unwrap_or(true),
    )?;

    let result = patterns
        .iter()
        .map(|p| {
            let state = match p.state {
                indicators::harmonics::PatternState::Forming => "forming".to_string(),
                indicators::harmonics::PatternState::Complete => "complete".to_string(),
            };

            PyHarmonicPattern {
                pattern_type: p.pattern_type.name_en().to_string(),
                pattern_type_zh: p.pattern_type.name_zh().to_string(),
                is_bullish: p.is_bullish,
                state,
                x_index: p.x.index,
                x_price: p.x.price,
                a_index: p.a.index,
                a_price: p.a.price,
                b_index: p.b.index,
                b_price: p.b.price,
                c_index: p.c.map(|c| c.index),
                c_price: p.c.map(|c| c.price),
                d_index: p.d.map(|d| d.index),
                d_price: p.d.map(|d| d.price),
                prz_high: p.prz.as_ref().map(|prz| prz.price_high),
                prz_low: p.prz.as_ref().map(|prz| prz.price_low),
                prz_center: p.prz.as_ref().map(|prz| prz.price_center),
                probability: p.completion_probability,
                target_prices: p.target_prices.clone(),
                stop_loss: p.stop_loss,
            }
        })
        .collect();

    Ok(result)
}

/// 检测摆动点
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (high, low, left_bars=None, right_bars=None))]
fn py_swing_points(
    high: Vec<f64>,
    low: Vec<f64>,
    left_bars: Option<usize>,
    right_bars: Option<usize>,
) -> PyResult<Vec<(usize, f64, bool)>> {
    let swings = indicators::harmonics::detect_swing_points(
        &high,
        &low,
        left_bars.unwrap_or(5),
        right_bars.unwrap_or(5),
    )?;
    Ok(swings
        .iter()
        .map(|s| (s.index, s.price, s.is_high))
        .collect())
}

// ==================== ML 模块 PyO3 绑定 ====================

/// Python-accessible ML model wrapper
#[cfg(feature = "python")]
#[pyclass(name = "SFGModel")]
pub struct PySFGModel {
    inner: ml::SFGModel,
    features_dim: usize,
}

#[cfg(feature = "python")]
#[pymethods]
impl PySFGModel {
    /// Check if model is trained
    pub fn is_trained(&self) -> bool {
        self.inner.is_trained()
    }

    /// Get feature dimension
    pub fn features_dim(&self) -> usize {
        self.features_dim
    }

    /// Predict using the trained model
    ///
    /// # Arguments
    /// * `features` - Flattened feature array (n_samples * n_features)
    /// * `n_samples` - Number of samples
    ///
    /// # Returns
    /// Predictions for each sample
    pub fn predict(&self, features: Vec<f64>, n_samples: usize) -> PyResult<Vec<f64>> {
        if !self.inner.is_trained() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Model is not trained",
            ));
        }

        let n_features = self.features_dim;
        if features.len() != n_samples * n_features {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Expected {} features ({}x{}), got {}",
                n_samples * n_features,
                n_samples,
                n_features,
                features.len()
            )));
        }

        let features_array = ndarray::Array2::from_shape_vec((n_samples, n_features), features)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("{e}")))?;

        Ok(self.inner.predict(&features_array).to_vec())
    }
}

/// Train an AI SuperTrend model
///
/// # Arguments
/// * `close` - Close prices
/// * `atr` - ATR values (same length as close)
/// * `train_window` - Training window size (default: 200)
/// * `lookback` - Feature lookback period (default: 10)
/// * `use_ridge` - Use Ridge regression instead of OLS (default: false)
/// * `ridge_alpha` - Ridge regularization strength (default: 1.0)
///
/// # Returns
/// Trained SFGModel
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (close, atr, train_window=None, lookback=None, use_ridge=None, ridge_alpha=None))]
fn py_train_supertrend_model(
    close: Vec<f64>,
    atr: Vec<f64>,
    train_window: Option<usize>,
    lookback: Option<usize>,
    use_ridge: Option<bool>,
    ridge_alpha: Option<f64>,
) -> PyResult<PySFGModel> {
    use ml::models::ModelType;
    use ml::trainer::{train_supertrend_model, TrainConfig};

    let config = TrainConfig {
        train_window: train_window.unwrap_or(200),
        lookback: lookback.unwrap_or(10),
        rolling: true,
        model_type: if use_ridge.unwrap_or(false) {
            ModelType::Ridge
        } else {
            ModelType::LinearRegression
        },
        ridge_alpha: ridge_alpha.unwrap_or(1.0),
        use_polynomial: false,
    };

    let result = train_supertrend_model(&close, &atr, &config)
        .map_err(pyo3::exceptions::PyValueError::new_err)?;

    Ok(PySFGModel {
        inner: result.model,
        features_dim: result.features_dim,
    })
}

/// Train an ATR2 model with volume features
///
/// # Arguments
/// * `close` - Close prices
/// * `atr` - ATR values
/// * `volume` - Volume values
/// * `train_window` - Training window size (default: 200)
/// * `lookback` - Feature lookback period (default: 10)
/// * `ridge_alpha` - Ridge regularization strength (default: 1.0)
///
/// # Returns
/// Trained SFGModel
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (close, atr, volume, train_window=None, lookback=None, ridge_alpha=None))]
fn py_train_atr2_model(
    close: Vec<f64>,
    atr: Vec<f64>,
    volume: Vec<f64>,
    train_window: Option<usize>,
    lookback: Option<usize>,
    ridge_alpha: Option<f64>,
) -> PyResult<PySFGModel> {
    use ml::models::ModelType;
    use ml::trainer::{train_atr2_model, TrainConfig};

    let config = TrainConfig {
        train_window: train_window.unwrap_or(200),
        lookback: lookback.unwrap_or(10),
        rolling: true,
        model_type: ModelType::Ridge,
        ridge_alpha: ridge_alpha.unwrap_or(1.0),
        use_polynomial: false,
    };

    let result = train_atr2_model(&close, &atr, &volume, &config)
        .map_err(pyo3::exceptions::PyValueError::new_err)?;

    Ok(PySFGModel {
        inner: result.model,
        features_dim: result.features_dim,
    })
}

/// Train a momentum model
///
/// # Arguments
/// * `rsi` - RSI indicator values (pre-computed)
/// * `train_window` - Training window size (default: 200)
/// * `lookback` - Feature lookback period (default: 10)
///
/// # Returns
/// Trained SFGModel
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (rsi, train_window=None, lookback=None))]
fn py_train_momentum_model(
    rsi: Vec<f64>,
    train_window: Option<usize>,
    lookback: Option<usize>,
) -> PyResult<PySFGModel> {
    use ml::models::ModelType;
    use ml::trainer::{train_momentum_model, TrainConfig};

    let config = TrainConfig {
        train_window: train_window.unwrap_or(200),
        lookback: lookback.unwrap_or(10),
        rolling: true,
        model_type: ModelType::LinearRegression,
        ridge_alpha: 1.0,
        use_polynomial: false,
    };

    let result =
        train_momentum_model(&rsi, &config).map_err(pyo3::exceptions::PyValueError::new_err)?;

    Ok(PySFGModel {
        inner: result.model,
        features_dim: result.features_dim,
    })
}

/// Prepare SuperTrend features for prediction
///
/// # Arguments
/// * `close` - Close prices
/// * `atr` - ATR values
/// * `lookback` - Feature lookback period
///
/// # Returns
/// Tuple of (features_flat, n_samples, n_features)
#[cfg(feature = "python")]
#[pyfunction]
fn py_prepare_supertrend_features(
    close: Vec<f64>,
    atr: Vec<f64>,
    lookback: usize,
) -> PyResult<(Vec<f64>, usize, usize)> {
    let (features, _targets) = ml::features::prepare_supertrend_features(&close, &atr, lookback);
    let (n_samples, n_features) = features.dim();
    let flat: Vec<f64> = features.into_iter().collect();
    Ok((flat, n_samples, n_features))
}

/// Prepare ATR2 features for prediction
///
/// # Arguments
/// * `close` - Close prices
/// * `atr` - ATR values
/// * `volume` - Volume values
/// * `lookback` - Feature lookback period
///
/// # Returns
/// Tuple of (features_flat, n_samples, n_features)
#[cfg(feature = "python")]
#[pyfunction]
fn py_prepare_atr2_features(
    close: Vec<f64>,
    atr: Vec<f64>,
    volume: Vec<f64>,
    lookback: usize,
) -> PyResult<(Vec<f64>, usize, usize)> {
    let (features, _targets) = ml::features::prepare_atr2_features(&close, &atr, &volume, lookback);
    let (n_samples, n_features) = features.dim();
    let flat: Vec<f64> = features.into_iter().collect();
    Ok((flat, n_samples, n_features))
}

/// Prepare momentum features for prediction
///
/// # Arguments
/// * `rsi` - RSI indicator values (pre-computed)
/// * `lookback` - Feature lookback period
///
/// # Returns
/// Tuple of (features_flat, n_samples, n_features)
#[cfg(feature = "python")]
#[pyfunction]
fn py_prepare_momentum_features(
    rsi: Vec<f64>,
    lookback: usize,
) -> PyResult<(Vec<f64>, usize, usize)> {
    let (features, _targets) = ml::features::prepare_momentum_features(&rsi, lookback);
    let (n_samples, n_features) = features.dim();
    let flat: Vec<f64> = features.into_iter().collect();
    Ok((flat, n_samples, n_features))
}
