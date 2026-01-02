//! Momentum Indicators Module
//!
//! # Overview
//! This module provides a comprehensive set of momentum-based technical indicators
//! used for measuring the rate of change in price movements. Momentum indicators
//! help identify overbought/oversold conditions, trend strength, and potential
//! reversal points.
//!
//! # Error Handling
//! All public functions return `Result<T, HazeError>` for proper error propagation:
//! - `HazeError::InvalidPeriod`: when period == 0 or period > data_len
//! - `HazeError::InsufficientData`: when data length is insufficient for computation
//! - `HazeError::LengthMismatch`: when input arrays have different lengths
//! - `HazeError::EmptyInput`: when input array is empty
//!
//! # Available Functions
//! - [`rsi`] - Relative Strength Index (0-100 oscillator for overbought/oversold)
//! - [`macd`] - Moving Average Convergence Divergence (trend-following momentum)
//! - [`stochastic`] - Stochastic Oscillator (%K and %D lines)
//! - [`stochrsi`] - Stochastic RSI (RSI applied to Stochastic formula)
//! - [`cci`] - Commodity Channel Index (deviation from statistical mean)
//! - [`williams_r`] - Williams %R (momentum oscillator, -100 to 0)
//! - [`awesome_oscillator`] - Awesome Oscillator (market momentum via median price)
//! - [`fisher_transform`] - Fisher Transform (Gaussian price distribution)
//! - [`kdj`] - KDJ Indicator (extended Stochastic with J line)
//! - [`tsi`] - True Strength Index (double-smoothed momentum)
//! - [`ultimate_oscillator`] - Ultimate Oscillator (multi-timeframe weighted momentum)
//! - [`apo`] - Absolute Price Oscillator (EMA difference)
//! - [`ppo`] - Percentage Price Oscillator (EMA difference as percentage)
//! - [`cmo`] - Chande Momentum Oscillator (normalized momentum)
//!
//! # Examples
//! ```rust,ignore
//! use haze_library::indicators::momentum::{rsi, macd};
//!
//! let close = vec![44.0, 44.25, 44.5, 44.0, 43.75, 44.0, 44.25, 44.5,
//!                  44.75, 45.0, 45.25, 45.0, 44.75, 45.0, 45.25];
//!
//! // Calculate RSI with 14-period
//! let rsi_values = rsi(&close, 14)?;
//!
//! // Calculate MACD with standard 12/26/9 settings
//! let (macd_line, signal, histogram) = macd(&close, 12, 26, 9)?;
//! ```
//!
//! # Performance Characteristics
//! - RSI/MACD: O(n) time complexity with single pass using Wilder's smoothing
//! - Stochastic: O(n) with efficient rolling max/min using monotonic deque
//! - All functions return NaN for warmup periods where insufficient data exists
//!
//! # Cross-References
//! - [`crate::indicators::volatility`] - ATR used in some momentum calculations
//! - [`crate::utils::ma`] - EMA/SMA building blocks
//! - [`crate::utils::stats`] - Rolling max/min utilities

#![allow(clippy::needless_range_loop)]

use crate::errors::validation::{
    validate_min_length, validate_not_empty, validate_period, validate_same_length,
};
use crate::errors::{HazeError, HazeResult};
use crate::init_result;
use crate::utils::ma::{ema_allow_nan, sma_allow_nan};
use crate::utils::math::{is_not_zero, is_zero, kahan_sum};
use crate::utils::{ema, rolling_max, rolling_min, sma};

/// Calculates the Relative Strength Index (RSI).
///
/// RSI is a momentum oscillator that measures the speed and magnitude of price changes.
/// It ranges from 0 to 100, with readings above 70 typically indicating overbought conditions
/// and below 30 indicating oversold conditions. RSI helps identify potential trend reversals
/// and price extremes.
///
/// # Formula
/// ```text
/// 1. Calculate price changes: change[i] = close[i] - close[i-1]
/// 2. Separate gains and losses:
///    gain[i] = max(change[i], 0)
///    loss[i] = max(-change[i], 0)
/// 3. Initial averages (simple mean over period):
///    avg_gain = SMA(gain[1..=period])
///    avg_loss = SMA(loss[1..=period])
/// 4. Wilder's smoothing (exponential smoothing):
///    avg_gain[i] = (avg_gain[i-1] * (period-1) + gain[i]) / period
///    avg_loss[i] = (avg_loss[i-1] * (period-1) + loss[i]) / period
/// 5. Relative Strength:
///    RS = avg_gain / avg_loss
/// 6. RSI calculation:
///    RSI = 100 - (100 / (1 + RS))
///
/// Special cases:
/// - When avg_loss = 0 and avg_gain > 0: RSI = 100
/// - When both are 0: RSI = 0
/// ```
///
/// # Arguments
/// * `close` - Price data series (typically closing prices)
/// * `period` - Lookback period for RSI calculation (commonly 14)
///
/// # Returns
/// Vector of RSI values ranging from 0 to 100. First `period` values will be NaN.
/// The first valid RSI value appears at index `period`.
///
/// # Errors
/// Returns error if:
/// - [`HazeError::EmptyInput`] - `close` array is empty
/// - [`HazeError::InvalidPeriod`] - `period` is 0
/// - [`HazeError::InsufficientData`] - `period` >= length of `close`
///
/// # Examples
/// ```rust
/// use haze_library::indicators::momentum::rsi;
///
/// let prices = vec![
///     44.0, 44.25, 44.375, 44.0, 43.75, 43.625, 43.875, 44.0,
///     44.25, 44.5, 44.75, 44.875, 45.0, 45.125, 45.25, 45.5
/// ];
/// let rsi_values = rsi(&prices, 14).unwrap();
///
/// // First 14 values are NaN (warmup period)
/// assert!(rsi_values[13].is_nan());
/// // First valid value at index 14
/// assert!(!rsi_values[14].is_nan());
/// assert!(rsi_values[14] >= 0.0 && rsi_values[14] <= 100.0);
/// ```
///
/// # Performance
/// - Time complexity: O(n) where n = data.len()
/// - Space complexity: O(n) for intermediate gain/loss arrays
/// - Uses single-pass Wilder's smoothing algorithm
///
/// # References
/// - Wilder, J. W. (1978). New Concepts in Technical Trading Systems
/// - Standard period: 14 (can be adjusted based on trading timeframe)
///
/// # See Also
/// - [`stochrsi`] - Stochastic RSI (applies Stochastic formula to RSI)
/// - [`cmo`] - Chande Momentum Oscillator (similar concept, different normalization)
pub fn rsi(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    let n = close.len();

    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }
    if period >= n {
        return Err(HazeError::InsufficientData {
            required: period + 1,
            actual: n,
        });
    }

    // 计算价格变化
    let mut gains = vec![0.0; n];
    let mut losses = vec![0.0; n];

    for i in 1..n {
        let change = close[i] - close[i - 1];
        if change > 0.0 {
            gains[i] = change;
        } else {
            losses[i] = -change;
        }
    }

    let mut result = init_result!(n);
    let period_f = period as f64;

    // 初始平均值使用 gains/losses 的前 period 个变动（从索引 1 开始）
    let mut sum_gain = 0.0;
    let mut sum_loss = 0.0;
    for i in 1..=period {
        sum_gain += gains[i];
        sum_loss += losses[i];
    }

    let mut avg_gain = sum_gain / period_f;
    let mut avg_loss = sum_loss / period_f;

    let rsi_value = |gain: f64, loss: f64| -> f64 {
        if gain.is_nan() || loss.is_nan() {
            f64::NAN
        } else if is_zero(loss) {
            if is_zero(gain) {
                0.0
            } else {
                100.0
            }
        } else {
            let rs = gain / loss;
            100.0 - (100.0 / (1.0 + rs))
        }
    };

    result[period] = rsi_value(avg_gain, avg_loss);

    // Wilder 平滑
    for i in (period + 1)..n {
        avg_gain = (avg_gain * (period_f - 1.0) + gains[i]) / period_f;
        avg_loss = (avg_loss * (period_f - 1.0) + losses[i]) / period_f;
        result[i] = rsi_value(avg_gain, avg_loss);
    }

    Ok(result)
}

/// Calculates the Moving Average Convergence Divergence (MACD).
///
/// MACD is a trend-following momentum indicator that shows the relationship between
/// two moving averages of a security's price. It consists of three components:
/// the MACD line, signal line, and histogram. MACD is widely used to identify
/// trend direction, strength, and potential reversal points.
///
/// # Formula
/// ```text
/// 1. MACD Line = EMA(close, fast_period) - EMA(close, slow_period)
/// 2. Signal Line = EMA(MACD Line, signal_period)
/// 3. Histogram = MACD Line - Signal Line
///
/// Trading Signals:
/// - Bullish: MACD crosses above Signal (Histogram > 0)
/// - Bearish: MACD crosses below Signal (Histogram < 0)
/// - Divergence: Price and MACD move in opposite directions
/// ```
///
/// # Implementation Details
/// This implementation follows TA-Lib conventions:
/// - Fast EMA is reseeded at index `slow_period - 1` for alignment
/// - MACD line values before `lookback` are set to NaN
/// - Lookback period = `slow_period + signal_period - 2`
///
/// # Arguments
/// * `close` - Price data series (typically closing prices)
/// * `fast_period` - Fast EMA period (commonly 12)
/// * `slow_period` - Slow EMA period (commonly 26)
/// * `signal_period` - Signal line EMA period (commonly 9)
///
/// # Returns
/// Tuple of three vectors: `(macd_line, signal_line, histogram)`
/// - `macd_line`: Difference between fast and slow EMAs
/// - `signal_line`: EMA of MACD line
/// - `histogram`: Difference between MACD line and signal line
///
/// All vectors have the same length as input. First `lookback` values are NaN.
///
/// # Errors
/// Returns error if:
/// - [`HazeError::EmptyInput`] - `close` array is empty
/// - [`HazeError::InvalidPeriod`] - Any period parameter is 0
/// - [`HazeError::InvalidPeriod`] - `fast_period` constraints violated
/// - [`HazeError::InsufficientData`] - `slow_period` > data length
/// - [`HazeError::InsufficientData`] - `lookback` >= data length
///
/// # Examples
/// ```rust
/// use haze_library::indicators::momentum::macd;
///
/// let close = vec![
///     100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 104.5, 104.0,
///     105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0,
///     113.0, 114.0, 115.0, 116.0, 117.0, 118.0, 119.0, 120.0,
///     121.0, 122.0, 123.0, 124.0, 125.0, 126.0, 127.0, 128.0,
///     129.0, 130.0, 131.0
/// ];
///
/// // Standard MACD with 12/26/9 settings
/// let (macd_line, signal, histogram) = macd(&close, 12, 26, 9).unwrap();
///
/// assert_eq!(macd_line.len(), close.len());
/// assert_eq!(signal.len(), close.len());
/// assert_eq!(histogram.len(), close.len());
///
/// // Check for bullish crossover (histogram turns positive)
/// let lookback = 26 + 9 - 2; // 33
/// if close.len() > lookback {
///     let recent_hist = &histogram[lookback..];
///     // Analyze histogram for trend signals
/// }
/// ```
///
/// # Performance
/// - Time complexity: O(n) where n = data.len()
/// - Space complexity: O(n) for intermediate EMA calculations
/// - Uses efficient single-pass EMA with seed indexing
///
/// # Trading Interpretation
/// - **Zero Line Crossover**: MACD crosses zero indicates trend change
/// - **Signal Line Crossover**: Primary buy/sell signals
/// - **Histogram Divergence**: Momentum weakening or strengthening
/// - **Centerline**: Above = bullish bias, Below = bearish bias
///
/// # References
/// - Gerald Appel (1979). The Moving Average Convergence-Divergence Method
/// - Standard parameters: 12/26/9 for daily charts
/// - TA-Lib compatible implementation
///
/// # See Also
/// - [`apo`] - Absolute Price Oscillator (MACD without signal line)
/// - [`ppo`] - Percentage Price Oscillator (MACD as percentage)
pub fn macd(
    close: &[f64],
    fast_period: usize,
    slow_period: usize,
    signal_period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_not_empty(close, "close")?;
    let n = close.len();

    if fast_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: fast_period,
            data_len: n,
        });
    }
    if slow_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: slow_period,
            data_len: n,
        });
    }
    if signal_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: signal_period,
            data_len: n,
        });
    }
    if slow_period > n {
        return Err(HazeError::InsufficientData {
            required: slow_period,
            actual: n,
        });
    }

    // TA-Lib 兼容：fast EMA 以 slow_period-1 为起点重新初始化
    let seed_index = slow_period - 1;
    let lookback = slow_period + signal_period - 2;

    if seed_index < fast_period - 1 {
        return Err(HazeError::InvalidPeriod {
            period: fast_period,
            data_len: n,
        });
    }
    if lookback >= n {
        return Err(HazeError::InsufficientData {
            required: lookback + 1,
            actual: n,
        });
    }

    let ema_fast = ema_with_seed(close, fast_period, seed_index)?;
    let ema_slow = ema_with_seed(close, slow_period, seed_index)?;

    let mut macd_raw = init_result!(n);
    for i in 0..n {
        if !ema_fast[i].is_nan() && !ema_slow[i].is_nan() {
            macd_raw[i] = ema_fast[i] - ema_slow[i];
        }
    }

    let signal_line = ema_with_seed(&macd_raw, signal_period, lookback)?;

    // 输出对齐 TA-Lib：macd_line 与 signal 同起点
    let mut macd_line = macd_raw;
    for val in macd_line.iter_mut().take(lookback) {
        *val = f64::NAN;
    }

    let histogram: Vec<f64> = macd_line
        .iter()
        .zip(&signal_line)
        .map(|(&macd, &signal)| {
            if macd.is_nan() || signal.is_nan() {
                f64::NAN
            } else {
                macd - signal
            }
        })
        .collect();

    Ok((macd_line, signal_line, histogram))
}

/// EMA with seed index - internal helper function
///
/// # Errors
/// - `HazeError::InvalidPeriod`: if period == 0 or seed_index constraints violated
/// - `HazeError::InsufficientData`: if seed_index < period - 1
fn ema_with_seed(values: &[f64], period: usize, seed_index: usize) -> HazeResult<Vec<f64>> {
    let n = values.len();

    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }
    if n == 0 {
        return Err(HazeError::EmptyInput { name: "values" });
    }
    if seed_index >= n {
        return Err(HazeError::InvalidPeriod {
            period: seed_index,
            data_len: n,
        });
    }
    if seed_index < period - 1 {
        return Err(HazeError::InsufficientData {
            required: period,
            actual: seed_index + 1,
        });
    }

    let mut result = init_result!(n);
    let start = seed_index + 1 - period;
    // 使用 Kahan 补偿求和提高 EMA 初始化精度
    let sum: f64 = kahan_sum(&values[start..=seed_index]);
    let alpha = 2.0 / (period as f64 + 1.0);
    result[seed_index] = sum / period as f64;

    for i in (seed_index + 1)..n {
        result[i] = alpha * values[i] + (1.0 - alpha) * result[i - 1];
    }

    Ok(result)
}

/// Stochastic Oscillator（随机振荡器）
///
/// 算法：
/// - fast %K = ((close - lowest_low) / (highest_high - lowest_low)) * 100
/// - slow %K = SMA(fast %K, smooth_k)
/// - %D = SMA(slow %K, d_period)
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `k_period`: %K 周期（默认 14）
/// - `smooth_k`: %K 平滑周期（默认 3）
/// - `d_period`: %D 平滑周期（默认 3）
///
/// # 返回
/// - `Ok((%K, %D))`: Stochastic 指标
///
/// # 错误
/// - `HazeError::EmptyInput`: 如果输入为空
/// - `HazeError::LengthMismatch`: 如果输入数组长度不一致
/// - `HazeError::InvalidPeriod`: 如果周期参数无效
pub fn stochastic(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    k_period: usize,
    smooth_k: usize,
    d_period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_same_length(high, "high", low, "low")?;
    validate_same_length(high, "high", close, "close")?;

    let n = high.len();
    validate_period(k_period, n)?;
    validate_period(smooth_k, n)?;
    validate_period(d_period, n)?;

    let highest_high = rolling_max(high, k_period);
    let lowest_low = rolling_min(low, k_period);

    // 计算 fast %K
    let fast_k: Vec<f64> = (0..n)
        .map(|i| {
            if highest_high[i].is_nan() || lowest_low[i].is_nan() {
                f64::NAN
            } else {
                let range = highest_high[i] - lowest_low[i];
                if is_zero(range) {
                    50.0 // 避免除零
                } else {
                    ((close[i] - lowest_low[i]) / range) * 100.0
                }
            }
        })
        .collect();

    // 平滑 %K
    let k = sma_allow_nan(&fast_k, smooth_k)?;

    // 计算 %D（slow %K 的 SMA）
    let d = sma_allow_nan(&k, d_period)?;

    Ok((k, d))
}

/// StochRSI - Stochastic RSI（随机 RSI）
///
/// 算法：
/// 1. 计算 RSI
/// 2. 对 RSI 应用 Stochastic 公式
/// - StochRSI = (RSI - lowest_RSI) / (highest_RSI - lowest_RSI) * 100
///
/// # 参数
/// - `close`: 收盘价序列
/// - `rsi_period`: RSI 周期（默认 14）
/// - `stoch_period`: Stochastic 周期（默认 14）
/// - `k_period`: %K 平滑周期（默认 3）
/// - `d_period`: %D 平滑周期（默认 3）
///
/// # 返回
/// - `Ok((%K, %D))`: StochRSI 指标
///
/// # 错误
/// - `HazeError::EmptyInput`: 如果输入为空
/// - `HazeError::InvalidPeriod`: 如果任何周期参数为 0
/// - `HazeError::InsufficientData`: 如果数据不足
pub fn stochrsi(
    close: &[f64],
    rsi_period: usize,
    stoch_period: usize,
    k_period: usize,
    d_period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(close, "close")?;
    let n = close.len();

    if rsi_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: rsi_period,
            data_len: n,
        });
    }
    if stoch_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: stoch_period,
            data_len: n,
        });
    }
    if k_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: k_period,
            data_len: n,
        });
    }
    if d_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: d_period,
            data_len: n,
        });
    }

    let rsi_values = rsi(close, rsi_period)?;

    let highest_rsi = rolling_max(&rsi_values, stoch_period);
    let lowest_rsi = rolling_min(&rsi_values, stoch_period);

    // 计算 StochRSI
    let stochrsi_raw: Vec<f64> = (0..rsi_values.len())
        .map(|i| {
            if highest_rsi[i].is_nan() || lowest_rsi[i].is_nan() {
                f64::NAN
            } else {
                let range = highest_rsi[i] - lowest_rsi[i];
                if is_zero(range) {
                    50.0
                } else {
                    ((rsi_values[i] - lowest_rsi[i]) / range) * 100.0
                }
            }
        })
        .collect();

    // %K 和 %D
    let k = sma_allow_nan(&stochrsi_raw, k_period)?;
    let d = sma_allow_nan(&k, d_period)?;

    Ok((k, d))
}

/// CCI - Commodity Channel Index（商品通道指标）
///
/// 算法：
/// 1. 计算 Typical Price = (H + L + C) / 3
/// 2. 计算 SMA(TP, period)
/// 3. 计算 Mean Deviation = mean(|TP - SMA|)
/// 4. CCI = (TP - SMA) / (0.015 * Mean Deviation)
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 20）
///
/// # 返回
/// - `Ok(Vec<f64>)`: CCI 值，范围通常在 -100 到 +100
///
/// # 错误
/// - `HazeError::EmptyInput`: 如果输入为空
/// - `HazeError::LengthMismatch`: 如果输入数组长度不一致
/// - `HazeError::InvalidPeriod`: 如果周期参数无效
pub fn cci(high: &[f64], low: &[f64], close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(high, "high")?;
    validate_same_length(high, "high", low, "low")?;
    validate_same_length(high, "high", close, "close")?;

    let n = high.len();
    validate_period(period, n)?;

    // 典型价格
    let typical_price: Vec<f64> = (0..n)
        .map(|i| (high[i] + low[i] + close[i]) / 3.0)
        .collect();

    let tp_sma = sma(&typical_price, period)?;

    let mut result = init_result!(n);

    for i in (period - 1)..n {
        let sma_val = tp_sma[i];
        if sma_val.is_nan() {
            continue;
        }

        // 计算 Mean Deviation
        let window = &typical_price[i + 1 - period..=i];
        let mean_dev: f64 =
            window.iter().map(|&tp| (tp - sma_val).abs()).sum::<f64>() / period as f64;

        if is_zero(mean_dev) {
            result[i] = 0.0;
        } else {
            result[i] = (typical_price[i] - sma_val) / (0.015 * mean_dev);
        }
    }

    Ok(result)
}

/// Williams %R（威廉指标）
///
/// 算法：
/// - %R = ((highest_high - close) / (highest_high - lowest_low)) * -100
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 14）
///
/// # 返回
/// - `Ok(Vec<f64>)`: -100 到 0 之间的值
///
/// # 错误
/// - `HazeError::EmptyInput`: 如果输入为空
/// - `HazeError::LengthMismatch`: 如果输入数组长度不一致
/// - `HazeError::InvalidPeriod`: 如果周期参数无效
pub fn williams_r(high: &[f64], low: &[f64], close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(high, "high")?;
    validate_same_length(high, "high", low, "low")?;
    validate_same_length(high, "high", close, "close")?;

    let n = high.len();
    validate_period(period, n)?;

    let highest_high = rolling_max(high, period);
    let lowest_low = rolling_min(low, period);

    let result: Vec<f64> = (0..n)
        .map(|i| {
            if highest_high[i].is_nan() || lowest_low[i].is_nan() {
                f64::NAN
            } else {
                let range = highest_high[i] - lowest_low[i];
                if is_zero(range) {
                    -50.0
                } else {
                    ((highest_high[i] - close[i]) / range) * -100.0
                }
            }
        })
        .collect();

    Ok(result)
}

/// Awesome Oscillator (AO)（动量振荡器）
///
/// 算法：
/// - Median Price = (H + L) / 2
/// - AO = SMA(Median Price, fast) - SMA(Median Price, slow)
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `fast_period`: 短周期（默认 5）
/// - `slow_period`: 长周期（默认 34）
///
/// # 返回
/// - `Ok(Vec<f64>)`: AO 值
///
/// # 错误
/// - `HazeError::EmptyInput`: 如果输入为空
/// - `HazeError::LengthMismatch`: 如果输入数组长度不一致
/// - `HazeError::InvalidPeriod`: 如果周期参数无效
pub fn awesome_oscillator(
    high: &[f64],
    low: &[f64],
    fast_period: usize,
    slow_period: usize,
) -> HazeResult<Vec<f64>> {
    validate_not_empty(high, "high")?;
    validate_same_length(high, "high", low, "low")?;

    let n = high.len();

    if fast_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: fast_period,
            data_len: n,
        });
    }
    if slow_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: slow_period,
            data_len: n,
        });
    }

    // Fail-Fast: 参数顺序验证
    if fast_period > slow_period {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("fast_period ({fast_period}) must be <= slow_period ({slow_period})"),
        });
    }

    let fast = fast_period.min(n);
    let slow = slow_period.min(n);

    // Validate the larger period
    validate_period(slow, n)?;

    // Post-clipping validation: ensure fast < slow still holds
    // This catches the case where both get clipped to n (e.g., fast=10, slow=20, n=8 → both become 8)
    if fast >= slow {
        return Err(HazeError::InsufficientData {
            required: slow_period,
            actual: n,
        });
    }

    // 中间价
    let median_price: Vec<f64> = (0..n).map(|i| (high[i] + low[i]) / 2.0).collect();

    let sma_fast = sma(&median_price, fast)?;
    let sma_slow = sma(&median_price, slow)?;

    let result: Vec<f64> = sma_fast
        .iter()
        .zip(&sma_slow)
        .map(|(&s_fast, &s_slow)| {
            if s_fast.is_nan() || s_slow.is_nan() {
                f64::NAN
            } else {
                s_fast - s_slow
            }
        })
        .collect();

    Ok(result)
}

/// Fisher Transform（费舍尔变换）
///
/// 算法：
/// 1. 归一化价格：value = (close - lowest) / (highest - lowest) * 2 - 1
/// 2. 限制范围：value = max(-0.999, min(0.999, value))
/// 3. Fisher = 0.5 * ln((1 + value) / (1 - value))
/// 4. Trigger = Fisher`[i-1]`
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 9）
///
/// # 返回
/// - `Ok((fisher, trigger))`: Fisher Transform 指标
///
/// # 错误
/// - `HazeError::EmptyInput`: 如果输入为空
/// - `HazeError::LengthMismatch`: 如果输入数组长度不一致
/// - `HazeError::InvalidPeriod`: 如果周期参数无效
pub fn fisher_transform(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_same_length(high, "high", low, "low")?;
    validate_same_length(high, "high", close, "close")?;

    let n = high.len();
    validate_period(period, n)?;

    let highest = rolling_max(high, period);
    let lowest = rolling_min(low, period);

    let mut fisher = init_result!(n);
    let mut trigger = init_result!(n);

    for i in (period - 1)..n {
        if highest[i].is_nan() || lowest[i].is_nan() {
            continue;
        }

        let range = highest[i] - lowest[i];
        let value = if is_zero(range) {
            0.0
        } else {
            ((close[i] - lowest[i]) / range) * 2.0 - 1.0
        };

        // 限制在 -0.999 到 0.999
        let value = value.clamp(-0.999, 0.999);

        // Fisher Transform
        fisher[i] = 0.5 * ((1.0 + value) / (1.0 - value)).ln();

        // Trigger = 前一个 Fisher 值
        if i > 0 {
            trigger[i] = fisher[i - 1];
        }
    }

    Ok((fisher, trigger))
}

/// KDJ 指标（随机指标扩展）
///
/// KDJ 在 Stochastic 基础上增加 J 线，J = 3*K - 2*D
///
/// # 参数
/// - `high`: 高价序列
/// - `low`: 低价序列
/// - `close`: 收盘价序列
/// - `k_period`: K 线周期（默认 9）
/// - `smooth_k`: K 线平滑周期（默认 3）
/// - `d_period`: D 线平滑周期（默认 3）
///
/// # 返回
/// - `Ok((K, D, J))`: KDJ 指标
///
/// # 错误
/// - `HazeError::EmptyInput`: 如果输入为空
/// - `HazeError::LengthMismatch`: 如果输入数组长度不一致
/// - `HazeError::InvalidPeriod`: 如果周期参数无效
pub fn kdj(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    k_period: usize,
    smooth_k: usize,
    d_period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    // 先计算 Stochastic 的 K 和 D
    let (k, d) = stochastic(high, low, close, k_period, smooth_k, d_period)?;

    // 计算 J = 3*K - 2*D
    let j: Vec<f64> = k
        .iter()
        .zip(&d)
        .map(|(&k_val, &d_val)| {
            if k_val.is_nan() || d_val.is_nan() {
                f64::NAN
            } else {
                3.0 * k_val - 2.0 * d_val
            }
        })
        .collect();

    Ok((k, d, j))
}

/// TSI (True Strength Index) 真实强度指数
///
/// 双重平滑的动量指标，比 RSI 更平滑
///
/// # 参数
/// - `close`: 收盘价序列
/// - `long_period`: 长周期（默认 25）
/// - `short_period`: 短周期（默认 13）
/// - `signal_period`: 信号线周期（默认 13）
///
/// # 返回
/// - `Ok((TSI, Signal))`: TSI 指标及信号线
///
/// # 错误
/// - `HazeError::EmptyInput`: 如果输入为空
/// - `HazeError::InvalidPeriod`: 如果任何周期参数为 0
/// - `HazeError::InsufficientData`: 如果数据不足
///
/// # 算法
/// 1. Momentum = Close`[i]` - Close`[i-1]`
/// 2. Double_Smoothed_Momentum = EMA(EMA(Momentum, long), short)
/// 3. Double_Smoothed_Abs_Momentum = EMA(EMA(|Momentum|, long), short)
/// 4. TSI = 100 * Double_Smoothed_Momentum / Double_Smoothed_Abs_Momentum
/// 5. Signal = EMA(TSI, signal_period)
pub fn tsi(
    close: &[f64],
    long_period: usize,
    short_period: usize,
    signal_period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(close, "close")?;
    let n = close.len();

    validate_min_length(close, 2)?;

    if long_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: long_period,
            data_len: n,
        });
    }
    if short_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: short_period,
            data_len: n,
        });
    }
    if signal_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: signal_period,
            data_len: n,
        });
    }

    // 1. 计算动量（价格变化）
    let mut momentum = init_result!(n);
    for i in 1..n {
        momentum[i] = close[i] - close[i - 1];
    }

    // 2. 计算动量的绝对值
    let abs_momentum: Vec<f64> = momentum.iter().map(|&m| m.abs()).collect();

    // 3. 双重 EMA 平滑
    let ema_momentum_long = ema_allow_nan(&momentum, long_period)?;
    let ema_momentum = ema_allow_nan(&ema_momentum_long, short_period)?;

    let ema_abs_momentum_long = ema_allow_nan(&abs_momentum, long_period)?;
    let ema_abs_momentum = ema_allow_nan(&ema_abs_momentum_long, short_period)?;

    // 4. 计算 TSI
    let mut tsi_values = init_result!(n);
    for i in 0..n {
        if !ema_momentum[i].is_nan()
            && !ema_abs_momentum[i].is_nan()
            && is_not_zero(ema_abs_momentum[i])
        {
            tsi_values[i] = 100.0 * ema_momentum[i] / ema_abs_momentum[i];
        }
    }

    // 5. 信号线（TSI 的 EMA）
    let signal = ema_allow_nan(&tsi_values, signal_period)?;

    Ok((tsi_values, signal))
}

/// UO (Ultimate Oscillator) 终极振荡器
///
/// 多周期加权动量指标，结合短中长期动量
///
/// # 参数
/// - `high`: 高价序列
/// - `low`: 低价序列
/// - `close`: 收盘价序列
/// - `period1`: 短周期（默认 7）
/// - `period2`: 中周期（默认 14）
/// - `period3`: 长周期（默认 28）
///
/// # 返回
/// - `Ok(Vec<f64>)`: UO 值（0-100）
///
/// # 错误
/// - `HazeError::EmptyInput`: 如果输入为空
/// - `HazeError::LengthMismatch`: 如果输入数组长度不一致
/// - `HazeError::InvalidPeriod`: 如果任何周期参数为 0
/// - `HazeError::InsufficientData`: 如果数据不足
///
/// # 算法
/// 1. BP (Buying Pressure) = Close - Min(Low, Prev_Close)
/// 2. TR (True Range) = Max(High, Prev_Close) - Min(Low, Prev_Close)
/// 3. Average_BP_period = Sum(BP, period) / Sum(TR, period)
/// 4. UO = 100 * (4*Avg7 + 2*Avg14 + Avg28) / (4 + 2 + 1)
pub fn ultimate_oscillator(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period1: usize,
    period2: usize,
    period3: usize,
) -> HazeResult<Vec<f64>> {
    validate_not_empty(high, "high")?;
    validate_same_length(high, "high", low, "low")?;
    validate_same_length(high, "high", close, "close")?;

    let n = close.len();
    validate_min_length(close, 2)?;

    if period1 == 0 {
        return Err(HazeError::InvalidPeriod {
            period: period1,
            data_len: n,
        });
    }
    if period2 == 0 {
        return Err(HazeError::InvalidPeriod {
            period: period2,
            data_len: n,
        });
    }
    if period3 == 0 {
        return Err(HazeError::InvalidPeriod {
            period: period3,
            data_len: n,
        });
    }

    // 1. 计算 BP 和 TR
    let mut bp = init_result!(n);
    let mut tr = init_result!(n);

    for i in 1..n {
        let prev_close = close[i - 1];
        let true_low = low[i].min(prev_close);
        let true_high = high[i].max(prev_close);

        bp[i] = close[i] - true_low;
        tr[i] = true_high - true_low;
    }

    // 2. 计算三个周期的平均 BP/TR 比率
    let avg1 = calc_uo_avg(&bp, &tr, period1);
    let avg2 = calc_uo_avg(&bp, &tr, period2);
    let avg3 = calc_uo_avg(&bp, &tr, period3);

    // 3. 加权计算 UO
    let mut uo = init_result!(n);
    for i in 0..n {
        if !avg1[i].is_nan() && !avg2[i].is_nan() && !avg3[i].is_nan() {
            uo[i] = 100.0 * (4.0 * avg1[i] + 2.0 * avg2[i] + avg3[i]) / 7.0;
        }
    }

    Ok(uo)
}

/// APO (Absolute Price Oscillator) 绝对价格振荡器
///
/// MACD的简化版本，仅返回快慢EMA差值
///
/// # 参数
/// - `close`: 收盘价序列
/// - `fast_period`: 快速EMA周期（默认 12）
/// - `slow_period`: 慢速EMA周期（默认 26）
///
/// # 返回
/// - `Ok(Vec<f64>)`: APO 值（快EMA - 慢EMA）
///
/// # 错误
/// - `HazeError::EmptyInput`: 如果输入为空
/// - `HazeError::InvalidPeriod`: 如果任何周期参数为 0
///
/// # 算法
/// APO = EMA(close, fast) - EMA(close, slow)
pub fn apo(close: &[f64], fast_period: usize, slow_period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    let n = close.len();

    if fast_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: fast_period,
            data_len: n,
        });
    }
    if slow_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: slow_period,
            data_len: n,
        });
    }

    // Fail-Fast: 参数顺序验证
    if fast_period > slow_period {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("fast_period ({fast_period}) must be <= slow_period ({slow_period})"),
        });
    }

    let fast = fast_period.min(n);
    let slow = slow_period.min(n);

    validate_period(slow, n)?;

    // Post-clipping validation: ensure fast < slow still holds
    if fast >= slow {
        return Err(HazeError::InsufficientData {
            required: slow_period,
            actual: n,
        });
    }

    let ema_fast = ema(close, fast)?;
    let ema_slow = ema(close, slow)?;

    let result: Vec<f64> = ema_fast
        .iter()
        .zip(&ema_slow)
        .map(|(&fast, &slow)| {
            if fast.is_nan() || slow.is_nan() {
                f64::NAN
            } else {
                fast - slow
            }
        })
        .collect();

    Ok(result)
}

/// PPO (Percentage Price Oscillator) 百分比价格振荡器
///
/// MACD的百分比版本
///
/// # 参数
/// - `close`: 收盘价序列
/// - `fast_period`: 快速EMA周期（默认 12）
/// - `slow_period`: 慢速EMA周期（默认 26）
///
/// # 返回
/// - `Ok(Vec<f64>)`: PPO 值（百分比）
///
/// # 错误
/// - `HazeError::EmptyInput`: 如果输入为空
/// - `HazeError::InvalidPeriod`: 如果任何周期参数为 0
///
/// # 算法
/// PPO = ((EMA_fast - EMA_slow) / EMA_slow) * 100
pub fn ppo(close: &[f64], fast_period: usize, slow_period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    let n = close.len();

    if fast_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: fast_period,
            data_len: n,
        });
    }
    if slow_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: slow_period,
            data_len: n,
        });
    }

    // Fail-Fast: 参数顺序验证
    if fast_period > slow_period {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("fast_period ({fast_period}) must be <= slow_period ({slow_period})"),
        });
    }

    let fast = fast_period.min(n);
    let slow = slow_period.min(n);

    validate_period(slow, n)?;

    // Post-clipping validation: ensure fast < slow still holds
    if fast >= slow {
        return Err(HazeError::InsufficientData {
            required: slow_period,
            actual: n,
        });
    }

    let ema_fast = ema(close, fast)?;
    let ema_slow = ema(close, slow)?;

    let result: Vec<f64> = ema_fast
        .iter()
        .zip(&ema_slow)
        .map(|(&fast, &slow)| {
            if fast.is_nan() || slow.is_nan() || is_zero(slow) {
                f64::NAN
            } else {
                ((fast - slow) / slow) * 100.0
            }
        })
        .collect();

    Ok(result)
}

/// CMO (Chande Momentum Oscillator) 钱德动量振荡器
///
/// 类似RSI，但使用不同的归一化公式
///
/// # 参数
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 14）
///
/// # 返回
/// - `Ok(Vec<f64>)`: CMO 值（-100 到 +100）
///
/// # 错误
/// - `HazeError::EmptyInput`: 如果输入为空
/// - `HazeError::InvalidPeriod`: 如果 period == 0
/// - `HazeError::InsufficientData`: 如果 period >= n
///
/// # 算法 (TA-Lib 对齐)
/// 1. 计算涨跌幅（只保留正值/负值）
/// 2. 使用 Wilder 平滑 (RMA) 得到平均涨/跌幅
/// 3. CMO = 100 * (avg_up - avg_down) / (avg_up + avg_down)
pub fn cmo(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    let n = close.len();

    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }
    if period >= n {
        return Err(HazeError::InsufficientData {
            required: period + 1,
            actual: n,
        });
    }

    let mut result = init_result!(n);

    let mut avg_gain = 0.0;
    let mut avg_loss = 0.0;

    // 初始均值：使用第 1..=period 根的涨跌幅
    for i in 1..=period {
        let change = close[i] - close[i - 1];
        if change > 0.0 {
            avg_gain += change;
        } else if change < 0.0 {
            avg_loss += -change;
        }
    }
    let period_f = period as f64;
    avg_gain /= period_f;
    avg_loss /= period_f;

    let sum_total = avg_gain + avg_loss;
    result[period] = if is_zero(sum_total) {
        0.0
    } else {
        100.0 * (avg_gain - avg_loss) / sum_total
    };

    for i in (period + 1)..n {
        let change = close[i] - close[i - 1];
        let gain = if change > 0.0 { change } else { 0.0 };
        let loss = if change < 0.0 { -change } else { 0.0 };

        avg_gain = (avg_gain * (period_f - 1.0) + gain) / period_f;
        avg_loss = (avg_loss * (period_f - 1.0) + loss) / period_f;

        let sum_total = avg_gain + avg_loss;
        result[i] = if is_zero(sum_total) {
            0.0
        } else {
            100.0 * (avg_gain - avg_loss) / sum_total
        };
    }

    Ok(result)
}

/// UO 辅助函数：计算指定周期的平均 BP/TR 比率
/// 使用 Kahan 补偿求和提高数值精度
fn calc_uo_avg(bp: &[f64], tr: &[f64], period: usize) -> Vec<f64> {
    let n = bp.len();
    let mut result = init_result!(n);

    for i in period..n {
        let start = i - period + 1;
        let end = i + 1;

        // 使用 Kahan 补偿求和，过滤掉 NaN 值
        let sum_bp = kahan_sum(&bp[start..end]);
        let sum_tr = kahan_sum(&tr[start..end]);

        if is_not_zero(sum_tr) {
            result[i] = sum_bp / sum_tr;
        }
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rsi() {
        // RSI 需要 period+1 个数据点才能产生第一个有效值
        // period=14 时，第一个有效值在 index 14
        let close = vec![
            44.0, 44.25, 44.375, 44.0, 43.75, 43.625, 43.875, 44.0, 44.25, 44.5, 44.75, 44.875,
            45.0, 45.125, 45.25, 45.5,
        ];
        let result = rsi(&close, 14).unwrap();

        assert!(result[0..14].iter().all(|x| x.is_nan()));
        assert!(!result[14].is_nan());
        assert!(result[14] >= 0.0 && result[14] <= 100.0);
    }

    #[test]
    fn test_rsi_invalid_period() {
        let close = vec![1.0, 2.0, 3.0];

        // period == 0 should return InvalidPeriod error
        let result = rsi(&close, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        // period >= n should return InsufficientData error
        let result = rsi(&close, 3);
        assert!(matches!(result, Err(HazeError::InsufficientData { .. })));

        let result = rsi(&close, 10);
        assert!(matches!(result, Err(HazeError::InsufficientData { .. })));
    }

    #[test]
    fn test_rsi_empty_input() {
        let close: Vec<f64> = vec![];
        let result = rsi(&close, 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_macd() {
        let close = vec![
            100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 104.5, 104.0, 105.0, 106.0,
        ];
        let (macd_line, signal, histogram) = macd(&close, 5, 8, 3).unwrap();

        assert!(!macd_line.is_empty());
        assert_eq!(macd_line.len(), close.len());
        assert_eq!(signal.len(), close.len());
        assert_eq!(histogram.len(), close.len());
    }

    #[test]
    fn test_macd_invalid_periods() {
        let close = vec![100.0, 101.0, 102.0];

        // fast_period == 0
        let result = macd(&close, 0, 8, 3);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        // slow_period == 0
        let result = macd(&close, 5, 0, 3);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        // signal_period == 0
        let result = macd(&close, 5, 8, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }

    #[test]
    fn test_macd_empty_input() {
        let close: Vec<f64> = vec![];
        let result = macd(&close, 12, 26, 9);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_stochastic() {
        let high = vec![110.0, 111.0, 112.0, 113.0, 114.0];
        let low = vec![100.0, 101.0, 102.0, 103.0, 104.0];
        let close = vec![105.0, 106.0, 107.0, 108.0, 109.0];

        let (k, d) = stochastic(&high, &low, &close, 3, 2, 2).unwrap();

        assert_eq!(k.len(), 5);
        assert_eq!(d.len(), 5);
        let valid_k = k.iter().copied().find(|v| !v.is_nan()).expect("valid k");
        assert!((0.0..=100.0).contains(&valid_k));
    }

    #[test]
    fn test_stochastic_length_mismatch() {
        let high = vec![110.0, 111.0, 112.0];
        let low = vec![100.0, 101.0];
        let close = vec![105.0, 106.0, 107.0];

        let result = stochastic(&high, &low, &close, 3, 2, 2);
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }

    #[test]
    fn test_stochastic_invalid_period() {
        let high = vec![110.0, 111.0, 112.0];
        let low = vec![100.0, 101.0, 102.0];
        let close = vec![105.0, 106.0, 107.0];

        // k_period == 0
        let result = stochastic(&high, &low, &close, 0, 2, 2);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        // smooth_k == 0
        let result = stochastic(&high, &low, &close, 3, 0, 2);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        // d_period == 0
        let result = stochastic(&high, &low, &close, 3, 2, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }

    #[test]
    fn test_williams_r() {
        let high = vec![110.0, 111.0, 112.0, 113.0, 114.0];
        let low = vec![100.0, 101.0, 102.0, 103.0, 104.0];
        let close = vec![105.0, 106.0, 107.0, 108.0, 109.0];

        let result = williams_r(&high, &low, &close, 3).unwrap();

        assert!(result[2] >= -100.0 && result[2] <= 0.0);
    }

    #[test]
    fn test_cci() {
        let high = vec![110.0, 111.0, 112.0, 113.0, 114.0, 115.0];
        let low = vec![100.0, 101.0, 102.0, 103.0, 104.0, 105.0];
        let close = vec![105.0, 106.0, 107.0, 108.0, 109.0, 110.0];

        let result = cci(&high, &low, &close, 3).unwrap();

        assert!(result[0].is_nan());
        assert!(!result[2].is_nan());
    }

    #[test]
    fn test_cci_invalid_period() {
        let high = vec![110.0, 111.0];
        let low = vec![100.0, 101.0];
        let close = vec![105.0, 106.0];

        let result = cci(&high, &low, &close, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }

    #[test]
    fn test_fisher_transform_invalid_period() {
        let high = vec![110.0, 111.0];
        let low = vec![100.0, 101.0];
        let close = vec![105.0, 106.0];

        let result = fisher_transform(&high, &low, &close, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }

    #[test]
    fn test_fisher_transform_valid() {
        let high = vec![110.0, 111.0, 112.0, 113.0, 114.0];
        let low = vec![100.0, 101.0, 102.0, 103.0, 104.0];
        let close = vec![105.0, 106.0, 107.0, 108.0, 109.0];

        let (fisher, trigger) = fisher_transform(&high, &low, &close, 3).unwrap();

        assert_eq!(fisher.len(), 5);
        assert_eq!(trigger.len(), 5);
        assert!(!fisher[2].is_nan());
    }

    #[test]
    fn test_cmo_invalid_period() {
        let close = vec![1.0, 2.0, 3.0];

        // period == 0
        let result = cmo(&close, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        // period >= n
        let result = cmo(&close, 3);
        assert!(matches!(result, Err(HazeError::InsufficientData { .. })));
    }

    #[test]
    fn test_apo_invalid_period() {
        let close = vec![1.0, 2.0, 3.0];

        let result = apo(&close, 0, 5);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = apo(&close, 5, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }

    #[test]
    fn test_ppo_invalid_period() {
        let close = vec![1.0, 2.0, 3.0];

        let result = ppo(&close, 0, 5);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = ppo(&close, 5, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }
}

#[cfg(test)]
mod kdj_tests {
    use super::*;

    #[test]
    fn test_kdj_basic() {
        let high = vec![110.0; 30];
        let low = vec![100.0; 30];
        let close = vec![105.0; 30];

        let (k, d, j) = kdj(&high, &low, &close, 9, 3, 3).unwrap();

        // 横盘市场中，K=D=50，J=3*50-2*50=50
        let valid_idx = k
            .iter()
            .zip(&d)
            .position(|(&k_val, &d_val)| !k_val.is_nan() && !d_val.is_nan())
            .expect("should have valid values");
        assert!((k[valid_idx] - 50.0).abs() < 5.0);
        assert!((d[valid_idx] - 50.0).abs() < 5.0);
        assert!((j[valid_idx] - 50.0).abs() < 5.0);
    }

    #[test]
    fn test_tsi_basic() {
        let close: Vec<f64> = (100..150).map(|x| x as f64).collect();

        let (tsi_vals, _signal) = tsi(&close, 5, 3, 3).unwrap();

        // 上升趋势中，TSI 应为正值
        let valid_idx = 10;
        assert!(!tsi_vals[valid_idx].is_nan());
        assert!(tsi_vals[valid_idx] > 0.0);
    }

    #[test]
    fn test_tsi_invalid_periods() {
        let close = vec![1.0, 2.0, 3.0];

        let result = tsi(&close, 0, 3, 3);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = tsi(&close, 5, 0, 3);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = tsi(&close, 5, 3, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }

    #[test]
    fn test_uo_basic() {
        let high: Vec<f64> = (100..150).map(|x| x as f64 + 5.0).collect();
        let low: Vec<f64> = (100..150).map(|x| x as f64).collect();
        let close: Vec<f64> = (100..150).map(|x| x as f64 + 2.5).collect();

        let uo = ultimate_oscillator(&high, &low, &close, 7, 14, 28).unwrap();

        // 横盘市场中，UO 应接近 50
        let valid_idx = 30;
        assert!(!uo[valid_idx].is_nan());
        assert!(uo[valid_idx] > 30.0 && uo[valid_idx] < 70.0);
    }

    #[test]
    fn test_uo_invalid_periods() {
        let high = vec![110.0, 111.0, 112.0];
        let low = vec![100.0, 101.0, 102.0];
        let close = vec![105.0, 106.0, 107.0];

        let result = ultimate_oscillator(&high, &low, &close, 0, 14, 28);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = ultimate_oscillator(&high, &low, &close, 7, 0, 28);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = ultimate_oscillator(&high, &low, &close, 7, 14, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }

    #[test]
    fn test_stochrsi_invalid_periods() {
        let close = vec![1.0, 2.0, 3.0, 4.0, 5.0];

        let result = stochrsi(&close, 0, 3, 3, 3);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = stochrsi(&close, 3, 0, 3, 3);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = stochrsi(&close, 3, 3, 0, 3);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = stochrsi(&close, 3, 3, 3, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }

    #[test]
    fn test_awesome_oscillator_invalid_periods() {
        let high = vec![110.0, 111.0, 112.0];
        let low = vec![100.0, 101.0, 102.0];

        let result = awesome_oscillator(&high, &low, 0, 34);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = awesome_oscillator(&high, &low, 5, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }
}
