//! Volatility Indicators Module
//!
//! # Overview
//! This module provides volatility-based technical indicators that measure the
//! degree of price variation over time. Volatility indicators are essential for
//! risk management, position sizing, and identifying potential breakout conditions.
//!
//! # Error Handling
//! All public functions return `HazeResult<T>` with proper error types:
//! - `HazeError::EmptyInput` - when input arrays are empty
//! - `HazeError::LengthMismatch` - when input arrays have different lengths
//! - `HazeError::InvalidPeriod` - when period is 0 or exceeds data length
//! - `HazeError::InsufficientData` - when data length is insufficient for the operation
//! - `HazeError::ParameterOutOfRange` - when parameters like multipliers are invalid
//!
//! # Available Functions
//! - [`true_range`] - True Range (maximum of H-L, |H-Prev_C|, |L-Prev_C|)
//! - [`atr`] - Average True Range (smoothed TR using Wilder's RMA)
//! - [`natr`] - Normalized ATR (ATR as percentage of close price)
//! - [`bollinger_bands`] - Bollinger Bands (SMA +/- standard deviation bands)
//! - [`keltner_channel`] - Keltner Channel (EMA +/- ATR-based bands)
//! - [`donchian_channel`] - Donchian Channel (highest high / lowest low bands)
//! - [`chandelier_exit`] - Chandelier Exit (ATR-based trailing stop levels)
//! - [`historical_volatility`] - Historical Volatility (annualized log returns std)
//! - [`ulcer_index`] - Ulcer Index (drawdown-based risk measure)
//! - [`mass_index`] - Mass Index (range expansion indicator)
//!
//! # Examples
//! ```rust
//! use haze_library::indicators::volatility::{atr, bollinger_bands};
//!
//! let high = vec![102.0, 105.0, 104.0, 106.0, 108.0];
//! let low = vec![99.0, 101.0, 100.0, 102.0, 104.0];
//! let close = vec![101.0, 103.0, 102.0, 105.0, 107.0];
//!
//! // Calculate 3-period ATR (returns Result)
//! let atr_values = atr(&high, &low, &close, 3).unwrap();
//!
//! // Calculate Bollinger Bands with 3-period SMA and 2 std dev
//! let (upper, middle, lower) = bollinger_bands(&close, 3, 2.0).unwrap();
//! ```
//!
//! # Performance Characteristics
//! - ATR: O(n) using incremental Wilder's smoothing (RMA)
//! - Bollinger Bands: O(n) with rolling statistics computation
//! - Donchian Channel: O(n) using monotonic deque for rolling max/min
//!
//! # Cross-References
//! - [`crate::indicators::trend`] - SuperTrend uses ATR for band calculation
//! - [`crate::utils::stats`] - Standard deviation and rolling functions
//! - [`crate::utils::ma`] - EMA/SMA for band center lines

#![allow(clippy::needless_range_loop)]

use crate::errors::validation::{
    validate_lengths_match, validate_min_length, validate_not_empty, validate_period,
};
use crate::errors::{HazeError, HazeResult};
use crate::init_result;
use crate::utils::ma::ema_allow_nan;
use crate::utils::math::{is_not_zero, is_zero, kahan_sum};
use crate::utils::{
    ema, mean_and_stdev_population, rolling_max, rolling_min, rolling_sum_kahan, sma, stdev,
    stdev_population,
};

/// True Range (TR)
///
/// Calculates the true range, which is the greatest of:
/// - Current High - Current Low
/// - |Current High - Previous Close|
/// - |Current Low - Previous Close|
///
/// # Algorithm
/// ```text
/// TR = MAX(high - low, ABS(high - prev_close), ABS(low - prev_close))
/// ```
///
/// # Parameters
/// - `high`: High price series
/// - `low`: Low price series
/// - `close`: Close price series
/// - `drift`: Lookback period for previous close (typically 1)
///
/// # Returns
/// - `Ok(Vec<f64>)`: Vector of same length as input, first `drift` values are NaN
///
/// # Errors
/// - [`HazeError::EmptyInput`]: Any input array is empty
/// - [`HazeError::LengthMismatch`]: Input arrays have different lengths
/// - [`HazeError::InvalidPeriod`]: drift is 0
/// - [`HazeError::InsufficientData`]: drift >= data length
///
/// # Example
/// ```rust
/// use haze_library::indicators::volatility::true_range;
///
/// let high = vec![102.0, 105.0, 104.0];
/// let low = vec![99.0, 101.0, 100.0];
/// let close = vec![101.0, 103.0, 102.0];
///
/// let tr = true_range(&high, &low, &close, 1).unwrap();
/// assert!(tr[0].is_nan()); // No previous close available
/// assert_eq!(tr[1], 4.0);  // MAX(4, 4, 0) = 4.0
/// ```
pub fn true_range(high: &[f64], low: &[f64], close: &[f64], drift: usize) -> HazeResult<Vec<f64>> {
    // Validate inputs
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let n = high.len();

    // Validate drift parameter
    if drift == 0 {
        return Err(HazeError::InvalidPeriod {
            period: drift,
            data_len: n,
        });
    }
    if drift >= n {
        return Err(HazeError::InsufficientData {
            required: drift + 1,
            actual: n,
        });
    }

    let mut result = init_result!(n);

    // Calculate TR from index `drift` onwards (earlier values have no previous close)
    for i in drift..n {
        let prev_close = close[i - drift];
        let tr1 = high[i] - low[i];
        let tr2 = (high[i] - prev_close).abs();
        let tr3 = (low[i] - prev_close).abs();
        result[i] = tr1.max(tr2).max(tr3);
    }

    Ok(result)
}

/// Calculates the Average True Range (ATR).
///
/// ATR is a technical analysis volatility indicator that measures market volatility
/// by decomposing the entire range of an asset price for a given period. It was
/// developed by J. Welles Wilder Jr. and is widely used for position sizing,
/// stop-loss placement, and volatility-based trading strategies.
///
/// # Formula
/// ```text
/// 1. Calculate True Range (TR) for each period:
///    TR = MAX(high - low, |high - prev_close|, |low - prev_close|)
///
/// 2. Initial ATR (at period n):
///    ATR[n] = SMA(TR[1..=n])
///
/// 3. Subsequent ATR values (Wilder's smoothing/RMA):
///    ATR[i] = (ATR[i-1] * (period-1) + TR[i]) / period
///
/// Note: This uses Wilder's smoothing, which is similar to an exponential
/// moving average but with α = 1/period instead of 2/(period+1).
/// ```
///
/// # Arguments
/// * `high` - High price series
/// * `low` - Low price series
/// * `close` - Close price series
/// * `period` - Smoothing period for ATR calculation (typically 14)
///
/// # Returns
/// Vector of ATR values. First `period` values will be NaN, as ATR requires
/// a full period of TR values plus one for the initial average.
///
/// # Errors
/// Returns error if:
/// - [`HazeError::EmptyInput`] - Any input array is empty
/// - [`HazeError::LengthMismatch`] - Input arrays have different lengths
/// - [`HazeError::InvalidPeriod`] - `period` is 0
/// - [`HazeError::InsufficientData`] - `period` >= length of data
///
/// # Examples
/// ```rust
/// use haze_library::indicators::volatility::atr;
///
/// let high = vec![102.0, 105.0, 104.0, 106.0, 108.0, 110.0, 112.0, 114.0,
///                 116.0, 118.0, 120.0, 122.0, 124.0, 126.0, 128.0];
/// let low = vec![99.0, 101.0, 100.0, 102.0, 104.0, 106.0, 108.0, 110.0,
///                112.0, 114.0, 116.0, 118.0, 120.0, 122.0, 124.0];
/// let close = vec![101.0, 103.0, 102.0, 105.0, 107.0, 109.0, 111.0, 113.0,
///                  115.0, 117.0, 119.0, 121.0, 123.0, 125.0, 127.0];
///
/// // Calculate 14-period ATR
/// let atr_values = atr(&high, &low, &close, 14).unwrap();
///
/// // First 14 values are NaN (warmup period)
/// assert!(atr_values[13].is_nan());
/// // First valid ATR at index 14
/// assert!(!atr_values[14].is_nan());
/// assert!(atr_values[14] > 0.0);
/// ```
///
/// # Performance
/// - Time complexity: O(n) where n = data.len()
/// - Space complexity: O(n) for TR and result vectors
/// - Single-pass algorithm using incremental Wilder's smoothing
///
/// # Trading Applications
/// - **Volatility Measurement**: Higher ATR = higher volatility
/// - **Position Sizing**: Risk a fixed multiple of ATR per trade
/// - **Stop-Loss Placement**: Place stops at 2-3x ATR from entry
/// - **Breakout Confirmation**: Rising ATR confirms breakout strength
/// - **Trailing Stops**: Use in Chandelier Exit and similar systems
///
/// # Implementation Notes
/// This implementation follows TA-Lib conventions:
/// - TR`[0]` is ignored in ATR calculation
/// - Initial ATR uses simple average of TR[1..=period]
/// - Subsequent values use Wilder's smoothing (RMA)
///
/// # References
/// - Wilder, J. W. (1978). New Concepts in Technical Trading Systems
/// - Standard period: 14 (can be adjusted for different timeframes)
///
/// # See Also
/// - [`true_range`] - Underlying TR calculation
/// - [`natr`] - Normalized ATR (as percentage of price)
/// - [`chandelier_exit`] - ATR-based trailing stop
/// - [`keltner_channel`] - ATR-based volatility bands
pub fn atr(high: &[f64], low: &[f64], close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Validate inputs
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let n = high.len();

    // Validate period parameter
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

    let tr = true_range(high, low, close, 1)?;
    let mut result = init_result!(n);

    // TA-Lib compatible: ignore TR[0], initial ATR = mean(TR[1..=period])
    let sum = kahan_sum(&tr[1..=period]);
    let period_f = period as f64;
    result[period] = sum / period_f;

    // Wilder's smoothing (RMA)
    for i in (period + 1)..n {
        result[i] = (result[i - 1] * (period_f - 1.0) + tr[i]) / period_f;
    }

    Ok(result)
}

/// NATR - Normalized Average True Range
///
/// Expresses ATR as a percentage of the close price, making it comparable
/// across different price levels and instruments.
///
/// # Algorithm
/// ```text
/// NATR = (ATR / close) * 100
/// ```
///
/// # Parameters
/// - `high`: High price series
/// - `low`: Low price series
/// - `close`: Close price series
/// - `period`: ATR period (typically 14)
///
/// # Returns
/// - `Ok(Vec<f64>)`: NATR values as percentages
///
/// # Errors
/// - [`HazeError::EmptyInput`]: Any input array is empty
/// - [`HazeError::LengthMismatch`]: Input arrays have different lengths
/// - [`HazeError::InvalidPeriod`]: period is 0 or >= data length
///
/// # Example
/// ```rust
/// use haze_library::indicators::volatility::natr;
///
/// let high = vec![102.0, 105.0, 104.0, 106.0, 108.0];
/// let low = vec![99.0, 101.0, 100.0, 102.0, 104.0];
/// let close = vec![101.0, 103.0, 102.0, 105.0, 107.0];
///
/// let natr_values = natr(&high, &low, &close, 3).unwrap();
/// // NATR is expressed as percentage (e.g., 3.5 means 3.5%)
/// ```
pub fn natr(high: &[f64], low: &[f64], close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Validate close is not empty (atr will validate the rest)
    validate_not_empty(close, "close")?;

    let atr_values = atr(high, low, close, period)?;

    let result = atr_values
        .iter()
        .zip(close)
        .map(|(&a, &c)| {
            if a.is_nan() || is_zero(c) {
                f64::NAN
            } else {
                (a / c) * 100.0
            }
        })
        .collect();

    Ok(result)
}

/// Calculates Bollinger Bands.
///
/// Bollinger Bands are a volatility indicator consisting of a middle band (SMA)
/// with upper and lower bands at a specified number of standard deviations away.
/// Developed by John Bollinger, they help identify overbought/oversold conditions,
/// volatility expansion/contraction, and potential reversal points.
///
/// # Formula
/// ```text
/// 1. Middle Band (BASIS):
///    MB = SMA(close, period)
///
/// 2. Standard Deviation:
///    σ = StdDev(close, period)    [Population StdDev]
///
/// 3. Upper Band:
///    UB = MB + (σ * std_multiplier)
///
/// 4. Lower Band:
///    LB = MB - (σ * std_multiplier)
///
/// Typical Settings:
/// - Period: 20
/// - Multiplier: 2.0 (captures ~95% of price action)
/// ```
///
/// # Arguments
/// * `close` - Close price series
/// * `period` - SMA period for middle band (commonly 20)
/// * `std_multiplier` - Standard deviation multiplier for band width (commonly 2.0)
///
/// # Returns
/// Tuple of three vectors: `(upper_band, middle_band, lower_band)`
/// - `upper_band`: Upper Bollinger Band
/// - `middle_band`: Middle band (SMA)
/// - `lower_band`: Lower Bollinger Band
///
/// All vectors have the same length as input. First `period - 1` values are NaN.
///
/// # Errors
/// Returns error if:
/// - [`HazeError::EmptyInput`] - `close` array is empty
/// - [`HazeError::InvalidPeriod`] - `period` is 0 or > data length
/// - [`HazeError::ParameterOutOfRange`] - `std_multiplier` < 0
///
/// # Examples
/// ```rust
/// use haze_library::indicators::volatility::bollinger_bands;
///
/// let close = vec![
///     100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 104.5, 104.0,
///     105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0,
///     113.0, 114.0, 115.0, 116.0, 117.0
/// ];
///
/// // Standard Bollinger Bands (20-period, 2 std dev)
/// let (upper, middle, lower) = bollinger_bands(&close, 20, 2.0).unwrap();
///
/// // Check band values
/// assert!((middle[19] - 107.475).abs() < 1e-10);  // SMA of first 20 values
/// assert!(upper[19] > middle[19]);
/// assert!(lower[19] < middle[19]);
///
/// // Detect squeeze (bands narrowing)
/// let bandwidth = (upper[19] - lower[19]) / middle[19];
/// if bandwidth < 0.05 {  // Less than 5%
///     println!("Bollinger Squeeze detected - volatility contraction");
/// }
/// ```
///
/// # Performance
/// - Time complexity: O(n) where n = data.len()
/// - Space complexity: O(n) for SMA and StdDev calculations
/// - Efficient rolling statistics implementation
///
/// # Trading Strategies
///
/// **1. Bollinger Bounce**
/// - Buy when price touches lower band
/// - Sell when price touches upper band
/// - Works best in ranging markets
///
/// **2. Bollinger Squeeze**
/// - Narrow bands indicate low volatility
/// - Often precedes significant price moves
/// - Breakout direction determined by first band touch
///
/// **3. Band Walk**
/// - Price consistently touching upper band = strong uptrend
/// - Price consistently touching lower band = strong downtrend
/// - Stay with trend until bands widen significantly
///
/// **4. %B Indicator**
/// - %B = (close - lower) / (upper - lower)
/// - %B > 1: Price above upper band
/// - %B < 0: Price below lower band
/// - %B = 0.5: Price at middle band
///
/// # Implementation Notes
/// - Uses population standard deviation (divides by n, not n-1)
/// - TA-Lib compatible calculation
/// - Bands widen during volatility expansion
/// - Bands narrow during volatility contraction
///
/// # References
/// - Bollinger, J. (2001). Bollinger on Bollinger Bands
/// - Standard parameters: 20-period SMA, 2.0 standard deviations
/// - Covers approximately 95% of price action under normal distribution
///
/// # See Also
/// - [`keltner_channel`] - Similar concept using ATR instead of StdDev
/// - [`donchian_channel`] - Price channel using highest/lowest
/// - [`sma`] - Simple Moving Average (middle band basis)
/// - [`stdev_population`] - Population standard deviation calculation
pub fn bollinger_bands(
    close: &[f64],
    period: usize,
    std_multiplier: f64,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    // Validate inputs
    validate_not_empty(close, "close")?;
    validate_period(period, close.len())?;

    // Validate std_multiplier
    if std_multiplier < 0.0 {
        return Err(HazeError::ParameterOutOfRange {
            name: "std_multiplier",
            value: std_multiplier,
            min: 0.0,
            max: f64::INFINITY,
        });
    }

    // 单次遍历同时计算 mean 和 stdev（Welford 算法优化）
    let (middle, std) = mean_and_stdev_population(close, period);

    let upper: Vec<f64> = middle
        .iter()
        .zip(&std)
        .map(|(&m, &s)| {
            if m.is_nan() || s.is_nan() {
                f64::NAN
            } else {
                m + s * std_multiplier
            }
        })
        .collect();

    let lower: Vec<f64> = middle
        .iter()
        .zip(&std)
        .map(|(&m, &s)| {
            if m.is_nan() || s.is_nan() {
                f64::NAN
            } else {
                m - s * std_multiplier
            }
        })
        .collect();

    Ok((upper, middle, lower))
}

/// Keltner Channel
///
/// A volatility-based envelope indicator using EMA as the center line
/// and ATR for band width calculation.
///
/// # Algorithm
/// ```text
/// Middle Line = EMA(close, period)
/// Upper Line  = Middle Line + (ATR * multiplier)
/// Lower Line  = Middle Line - (ATR * multiplier)
/// ```
///
/// # Parameters
/// - `high`: High price series
/// - `low`: Low price series
/// - `close`: Close price series
/// - `period`: EMA period for middle line (typically 20)
/// - `atr_period`: ATR period for band width (typically 10)
/// - `multiplier`: ATR multiplier for band distance (typically 2.0)
///
/// # Returns
/// - `Ok((upper, middle, lower))`: Three vectors of channel values
///
/// # Errors
/// - [`HazeError::EmptyInput`]: Any input array is empty
/// - [`HazeError::LengthMismatch`]: Input arrays have different lengths
/// - [`HazeError::InvalidPeriod`]: period or atr_period is 0
/// - [`HazeError::InsufficientData`]: atr_period >= data length
///
/// # Example
/// ```rust
/// use haze_library::indicators::volatility::keltner_channel;
///
/// let high = vec![102.0, 105.0, 104.0, 106.0, 108.0, 110.0];
/// let low = vec![99.0, 101.0, 100.0, 102.0, 104.0, 106.0];
/// let close = vec![101.0, 103.0, 102.0, 105.0, 107.0, 109.0];
///
/// let (upper, middle, lower) = keltner_channel(&high, &low, &close, 3, 3, 2.0).unwrap();
/// ```
pub fn keltner_channel(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
    atr_period: usize,
    multiplier: f64,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    // Validate inputs
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let n = high.len();
    validate_period(period, n)?;

    // Validate ATR period
    if atr_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: atr_period,
            data_len: n,
        });
    }
    if atr_period >= n {
        return Err(HazeError::InsufficientData {
            required: atr_period + 1,
            actual: n,
        });
    }

    // Validate multiplier
    if multiplier < 0.0 {
        return Err(HazeError::ParameterOutOfRange {
            name: "multiplier",
            value: multiplier,
            min: 0.0,
            max: f64::INFINITY,
        });
    }

    let middle = ema(close, period)?;
    let atr_values = atr(high, low, close, atr_period)?;

    let upper: Vec<f64> = middle
        .iter()
        .zip(&atr_values)
        .map(|(&m, &a)| {
            if m.is_nan() || a.is_nan() {
                f64::NAN
            } else {
                m + a * multiplier
            }
        })
        .collect();

    let lower: Vec<f64> = middle
        .iter()
        .zip(&atr_values)
        .map(|(&m, &a)| {
            if m.is_nan() || a.is_nan() {
                f64::NAN
            } else {
                m - a * multiplier
            }
        })
        .collect();

    Ok((upper, middle, lower))
}

/// Donchian Channel
///
/// A price channel indicator showing the highest high and lowest low
/// over a specified period.
///
/// # Algorithm
/// ```text
/// Upper Band  = MAX(high, period)
/// Lower Band  = MIN(low, period)
/// Middle Band = (Upper + Lower) / 2
/// ```
///
/// # Parameters
/// - `high`: High price series
/// - `low`: Low price series
/// - `period`: Lookback period (typically 20)
///
/// # Returns
/// - `Ok((upper, middle, lower))`: Three vectors of channel values
///
/// # Errors
/// - [`HazeError::EmptyInput`]: Any input array is empty
/// - [`HazeError::LengthMismatch`]: Input arrays have different lengths
/// - [`HazeError::InvalidPeriod`]: period is 0 or > data length
///
/// # Example
/// ```rust
/// use haze_library::indicators::volatility::donchian_channel;
///
/// let high = vec![102.0, 105.0, 104.0, 106.0, 103.0];
/// let low = vec![99.0, 101.0, 100.0, 102.0, 98.0];
///
/// let (upper, middle, lower) = donchian_channel(&high, &low, 3).unwrap();
/// assert_eq!(upper[2], 105.0);  // MAX of first 3 highs
/// assert_eq!(lower[2], 99.0);   // MIN of first 3 lows
/// assert_eq!(middle[2], 102.0); // (105 + 99) / 2
/// ```
pub fn donchian_channel(
    high: &[f64],
    low: &[f64],
    period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    // Validate inputs
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low")])?;
    validate_period(period, high.len())?;

    let upper = rolling_max(high, period);
    let lower = rolling_min(low, period);

    let middle: Vec<f64> = upper
        .iter()
        .zip(&lower)
        .map(|(&u, &l)| {
            if u.is_nan() || l.is_nan() {
                f64::NAN
            } else {
                (u + l) / 2.0
            }
        })
        .collect();

    Ok((upper, middle, lower))
}

/// Chandelier Exit
///
/// A volatility-based trailing stop system that uses ATR to set exit levels
/// for both long and short positions.
///
/// # Algorithm
/// ```text
/// Long Exit  = MAX(high, period) - ATR(atr_period) * multiplier
/// Short Exit = MIN(low, period) + ATR(atr_period) * multiplier
/// ```
///
/// # Parameters
/// - `high`: High price series
/// - `low`: Low price series
/// - `close`: Close price series
/// - `period`: Lookback period for highest high / lowest low (typically 22)
/// - `atr_period`: ATR period (typically 22)
/// - `multiplier`: ATR multiplier for stop distance (typically 3.0)
///
/// # Returns
/// - `Ok((long_exit, short_exit))`: Two vectors of exit levels
///
/// # Errors
/// - [`HazeError::EmptyInput`]: Any input array is empty
/// - [`HazeError::LengthMismatch`]: Input arrays have different lengths
/// - [`HazeError::InvalidPeriod`]: period or atr_period is 0
/// - [`HazeError::InsufficientData`]: period or atr_period > data length
///
/// # Example
/// ```rust
/// use haze_library::indicators::volatility::chandelier_exit;
///
/// let high = vec![102.0, 105.0, 104.0, 106.0, 108.0, 110.0];
/// let low = vec![99.0, 101.0, 100.0, 102.0, 104.0, 106.0];
/// let close = vec![101.0, 103.0, 102.0, 105.0, 107.0, 109.0];
///
/// let (long_exit, short_exit) = chandelier_exit(&high, &low, &close, 3, 3, 3.0).unwrap();
/// ```
pub fn chandelier_exit(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
    atr_period: usize,
    multiplier: f64,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    // Validate inputs
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let n = high.len();
    validate_period(period, n)?;

    // Validate ATR period
    if atr_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: atr_period,
            data_len: n,
        });
    }
    if atr_period >= n {
        return Err(HazeError::InsufficientData {
            required: atr_period + 1,
            actual: n,
        });
    }

    // Validate multiplier
    if multiplier < 0.0 {
        return Err(HazeError::ParameterOutOfRange {
            name: "multiplier",
            value: multiplier,
            min: 0.0,
            max: f64::INFINITY,
        });
    }

    let max_high = rolling_max(high, period);
    let min_low = rolling_min(low, period);
    let atr_values = atr(high, low, close, atr_period)?;

    let mut long_exit = init_result!(n);
    let mut short_exit = init_result!(n);

    for i in 0..n {
        let mh = max_high[i];
        let ml = min_low[i];
        let atr_val = atr_values[i];
        if mh.is_nan() || ml.is_nan() || atr_val.is_nan() {
            continue;
        }
        long_exit[i] = mh - atr_val * multiplier;
        short_exit[i] = ml + atr_val * multiplier;
    }

    Ok((long_exit, short_exit))
}

/// Historical Volatility (HV)
///
/// Measures the annualized standard deviation of logarithmic returns,
/// commonly used in options pricing and risk assessment.
///
/// # Algorithm
/// ```text
/// log_return[i] = ln(close[i] / close[i-1])
/// HV = StdDev(log_returns, period) * sqrt(period) * 100
/// ```
///
/// # Parameters
/// - `close`: Close price series
/// - `period`: Lookback period (typically 20)
///
/// # Returns
/// - `Ok(Vec<f64>)`: Historical volatility as percentage
///
/// # Errors
/// - [`HazeError::EmptyInput`]: close array is empty
/// - [`HazeError::InvalidPeriod`]: period < 2 or > data length
///
/// # Example
/// ```rust
/// use haze_library::indicators::volatility::historical_volatility;
///
/// let close: Vec<f64> = (100..120).map(|x| x as f64).collect();
/// let hv = historical_volatility(&close, 5).unwrap();
/// ```
pub fn historical_volatility(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Validate inputs
    validate_not_empty(close, "close")?;

    let n = close.len();

    // Historical volatility requires period >= 2 for meaningful std dev
    if period < 2 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }
    validate_period(period, n)?;

    let mut log_returns = init_result!(n);
    for i in 1..n {
        if is_zero(close[i - 1]) || close[i].is_nan() || close[i - 1].is_nan() {
            continue;
        }
        log_returns[i] = (close[i] / close[i - 1]).ln();
    }

    let stdev_values = stdev(&log_returns, period);
    let scale = (period as f64).sqrt() * 100.0;

    let result = stdev_values
        .iter()
        .map(|&v| if v.is_nan() { f64::NAN } else { v * scale })
        .collect();

    Ok(result)
}

/// Ulcer Index
///
/// A volatility measure focusing on downside risk by measuring the depth
/// and duration of drawdowns from recent highs.
///
/// # Algorithm
/// ```text
/// drawdown[i] = ((close[i] - rolling_max[i]) / rolling_max[i]) * 100
/// Ulcer Index[i] = sqrt(mean(drawdown[i-period+1..i]^2))
/// ```
///
/// # Parameters
/// - `close`: Close price series
/// - `period`: Lookback period (typically 14)
///
/// # Returns
/// - `Ok(Vec<f64>)`: Ulcer Index values
///
/// # Errors
/// - [`HazeError::EmptyInput`]: close array is empty
/// - [`HazeError::InvalidPeriod`]: period is 0 or > data length
///
/// # Example
/// ```rust
/// use haze_library::indicators::volatility::ulcer_index;
///
/// let close = vec![100.0, 98.0, 99.0, 97.0, 100.0, 102.0];
/// let ui = ulcer_index(&close, 3).unwrap();
/// ```
pub fn ulcer_index(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Validate inputs
    validate_not_empty(close, "close")?;
    validate_period(period, close.len())?;

    let n = close.len();
    let rolling_max_close = rolling_max(close, period);

    let mut dd_sq = init_result!(n);
    for i in 0..n {
        let max_close = rolling_max_close[i];
        let c = close[i];
        if max_close.is_nan() || c.is_nan() || max_close <= 0.0 {
            continue;
        }
        let dd = (c - max_close) / max_close * 100.0;
        dd_sq[i] = dd * dd;
    }

    let dd_sq_clean: Vec<f64> = dd_sq
        .iter()
        .map(|&v| if v.is_finite() { v } else { 0.0 })
        .collect();
    let dd_sq_sum = rolling_sum_kahan(&dd_sq_clean, period);

    let mut valid_prefix = vec![0usize; n + 1];
    for i in 0..n {
        let valid = if dd_sq[i].is_finite() { 1 } else { 0 };
        valid_prefix[i + 1] = valid_prefix[i] + valid;
    }

    let mut result = init_result!(n);
    for i in (period - 1)..n {
        let valid_count = valid_prefix[i + 1] - valid_prefix[i + 1 - period];
        if valid_count == period {
            result[i] = (dd_sq_sum[i] / period as f64).sqrt();
        }
    }

    Ok(result)
}

/// Mass Index
///
/// A volatility indicator that uses the ratio of two EMAs of the high-low range
/// to identify potential trend reversals.
///
/// # Algorithm
/// ```text
/// Range = high - low
/// EMA1  = EMA(Range, fast)
/// EMA2  = EMA(EMA1, fast)
/// Ratio = EMA1 / EMA2
/// Mass Index = Sum(Ratio, slow)
/// ```
///
/// A "reversal bulge" occurs when Mass Index rises above 27 and then falls below 26.5.
///
/// # Parameters
/// - `high`: High price series
/// - `low`: Low price series
/// - `fast`: EMA period for smoothing (typically 9)
/// - `slow`: Sum period (typically 25)
///
/// # Returns
/// - `Ok(Vec<f64>)`: Mass Index values
///
/// # Errors
/// - [`HazeError::EmptyInput`]: Any input array is empty
/// - [`HazeError::LengthMismatch`]: Input arrays have different lengths
/// - [`HazeError::InvalidPeriod`]: fast or slow is 0
/// - [`HazeError::InsufficientData`]: data length is insufficient for fast/slow
///
/// # Example
/// ```rust
/// use haze_library::indicators::volatility::mass_index;
///
/// let high: Vec<f64> = (100..160).map(|x| x as f64 + 5.0).collect();
/// let low: Vec<f64> = (100..160).map(|x| x as f64).collect();
///
/// let mi = mass_index(&high, &low, 9, 25).unwrap();
/// ```
pub fn mass_index(high: &[f64], low: &[f64], fast: usize, slow: usize) -> HazeResult<Vec<f64>> {
    // Validate inputs
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low")])?;

    let n = high.len();
    if fast == 0 {
        return Err(HazeError::InvalidPeriod {
            period: fast,
            data_len: n,
        });
    }
    if slow == 0 {
        return Err(HazeError::InvalidPeriod {
            period: slow,
            data_len: n,
        });
    }
    let (fast, slow) = if slow < fast {
        (slow, fast)
    } else {
        (fast, slow)
    };
    let required = 2 * slow - fast;
    validate_min_length(high, required)?;

    let range: Vec<f64> = (0..n).map(|i| high[i] - low[i]).collect();
    let ema1 = ema(&range, fast)?;
    let ema2 = ema_allow_nan(&ema1, fast)?;

    let ratio: Vec<f64> = ema1
        .iter()
        .zip(&ema2)
        .map(|(&e1, &e2)| {
            if e1.is_nan() || e2.is_nan() || is_zero(e2) {
                f64::NAN
            } else {
                e1 / e2
            }
        })
        .collect();

    let ratio_clean: Vec<f64> = ratio
        .iter()
        .map(|&v| if v.is_finite() { v } else { 0.0 })
        .collect();
    let ratio_sum = rolling_sum_kahan(&ratio_clean, slow);

    let mut valid_prefix = vec![0usize; n + 1];
    for i in 0..n {
        let valid = if ratio[i].is_finite() { 1 } else { 0 };
        valid_prefix[i + 1] = valid_prefix[i] + valid;
    }

    let mut result = init_result!(n);
    for i in (slow - 1)..n {
        let valid_count = valid_prefix[i + 1] - valid_prefix[i + 1 - slow];
        if valid_count == slow {
            result[i] = ratio_sum[i];
        }
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ==================== true_range tests ====================

    #[test]
    fn test_true_range_basic() {
        let high = vec![102.0, 105.0, 104.0];
        let low = vec![99.0, 101.0, 100.0];
        let close = vec![101.0, 103.0, 102.0];

        let tr = true_range(&high, &low, &close, 1).unwrap();

        // TR[0] has no previous close, returns NaN
        assert!(tr[0].is_nan());

        // TR[1] = MAX(105-101, |105-101|, |101-101|) = MAX(4, 4, 0) = 4.0
        assert_eq!(tr[1], 4.0);

        // TR[2] = MAX(104-100, |104-103|, |100-103|) = MAX(4, 1, 3) = 4.0
        assert_eq!(tr[2], 4.0);
    }

    #[test]
    fn test_true_range_empty_input() {
        let result = true_range(&[], &[], &[], 1);
        assert!(result.is_err());
        match result {
            Err(HazeError::EmptyInput { name }) => assert_eq!(name, "high"),
            _ => panic!("Expected EmptyInput error"),
        }
    }

    #[test]
    fn test_true_range_invalid_drift_zero() {
        let high = vec![102.0, 105.0];
        let low = vec![99.0, 101.0];
        let close = vec![101.0, 103.0];

        let result = true_range(&high, &low, &close, 0);
        assert!(result.is_err());
        match result {
            Err(HazeError::InvalidPeriod { period, .. }) => assert_eq!(period, 0),
            _ => panic!("Expected InvalidPeriod error"),
        }
    }

    #[test]
    fn test_true_range_insufficient_data() {
        let high = vec![102.0, 105.0];
        let low = vec![99.0, 101.0];
        let close = vec![101.0, 103.0];

        let result = true_range(&high, &low, &close, 5);
        assert!(result.is_err());
        match result {
            Err(HazeError::InsufficientData { required, actual }) => {
                assert_eq!(required, 6);
                assert_eq!(actual, 2);
            }
            _ => panic!("Expected InsufficientData error"),
        }
    }

    #[test]
    fn test_true_range_length_mismatch() {
        let high = vec![102.0, 105.0, 104.0];
        let low = vec![99.0, 101.0];
        let close = vec![101.0, 103.0, 102.0];

        let result = true_range(&high, &low, &close, 1);
        assert!(result.is_err());
        match result {
            Err(HazeError::LengthMismatch { .. }) => {}
            _ => panic!("Expected LengthMismatch error"),
        }
    }

    // ==================== atr tests ====================

    #[test]
    fn test_atr_basic() {
        let high = vec![102.0, 105.0, 104.0, 106.0, 108.0];
        let low = vec![99.0, 101.0, 100.0, 102.0, 104.0];
        let close = vec![101.0, 103.0, 102.0, 105.0, 107.0];

        let result = atr(&high, &low, &close, 3).unwrap();

        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        assert!(result[2].is_nan());
        assert!(!result[3].is_nan()); // ATR starts at index `period`
    }

    #[test]
    fn test_atr_invalid_period_zero() {
        let high = vec![102.0, 105.0];
        let low = vec![99.0, 101.0];
        let close = vec![101.0, 103.0];

        let result = atr(&high, &low, &close, 0);
        assert!(result.is_err());
        match result {
            Err(HazeError::InvalidPeriod { period, .. }) => assert_eq!(period, 0),
            _ => panic!("Expected InvalidPeriod error"),
        }
    }

    #[test]
    fn test_atr_insufficient_data() {
        let high = vec![102.0, 105.0];
        let low = vec![99.0, 101.0];
        let close = vec![101.0, 103.0];

        let result = atr(&high, &low, &close, 5);
        assert!(result.is_err());
        match result {
            Err(HazeError::InsufficientData { .. }) => {}
            _ => panic!("Expected InsufficientData error"),
        }
    }

    // ==================== bollinger_bands tests ====================

    #[test]
    fn test_bollinger_bands_basic() {
        let close = vec![100.0, 101.0, 102.0, 103.0, 104.0, 105.0];
        let (upper, middle, lower) = bollinger_bands(&close, 3, 2.0).unwrap();

        assert!(upper[0].is_nan());
        assert!(upper[1].is_nan());
        assert!(!upper[2].is_nan());

        // Middle band[2] = SMA([100, 101, 102]) = 101.0
        assert_eq!(middle[2], 101.0);

        // Upper > Middle > Lower
        assert!(upper[2] > middle[2]);
        assert!(middle[2] > lower[2]);
    }

    #[test]
    fn test_bollinger_bands_invalid_period() {
        let close = vec![100.0, 101.0];

        let result = bollinger_bands(&close, 0, 2.0);
        assert!(result.is_err());

        let result = bollinger_bands(&close, 5, 2.0);
        assert!(result.is_err());
    }

    #[test]
    fn test_bollinger_bands_negative_multiplier() {
        let close = vec![100.0, 101.0, 102.0, 103.0];

        let result = bollinger_bands(&close, 2, -1.0);
        assert!(result.is_err());
        match result {
            Err(HazeError::ParameterOutOfRange { name, .. }) => {
                assert_eq!(name, "std_multiplier");
            }
            _ => panic!("Expected ParameterOutOfRange error"),
        }
    }

    #[test]
    fn test_bollinger_bands_empty_input() {
        let result = bollinger_bands(&[], 3, 2.0);
        assert!(result.is_err());
        match result {
            Err(HazeError::EmptyInput { name }) => assert_eq!(name, "close"),
            _ => panic!("Expected EmptyInput error"),
        }
    }

    // ==================== donchian_channel tests ====================

    #[test]
    fn test_donchian_channel_basic() {
        let high = vec![102.0, 105.0, 104.0, 106.0, 103.0];
        let low = vec![99.0, 101.0, 100.0, 102.0, 98.0];

        let (upper, middle, lower) = donchian_channel(&high, &low, 3).unwrap();

        // Upper[2] = MAX([102, 105, 104]) = 105
        assert_eq!(upper[2], 105.0);

        // Lower[2] = MIN([99, 101, 100]) = 99
        assert_eq!(lower[2], 99.0);

        // Middle[2] = (105 + 99) / 2 = 102
        assert_eq!(middle[2], 102.0);
    }

    #[test]
    fn test_donchian_channel_invalid_period() {
        let high = vec![102.0, 105.0];
        let low = vec![99.0, 101.0];

        let result = donchian_channel(&high, &low, 0);
        assert!(result.is_err());

        let result = donchian_channel(&high, &low, 5);
        assert!(result.is_err());
    }

    #[test]
    fn test_donchian_channel_empty_input() {
        let result = donchian_channel(&[], &[], 3);
        assert!(result.is_err());
    }

    // ==================== keltner_channel tests ====================

    #[test]
    fn test_keltner_channel_basic() {
        let high = vec![102.0, 105.0, 104.0, 106.0, 108.0, 110.0];
        let low = vec![99.0, 101.0, 100.0, 102.0, 104.0, 106.0];
        let close = vec![101.0, 103.0, 102.0, 105.0, 107.0, 109.0];

        let result = keltner_channel(&high, &low, &close, 3, 3, 2.0);
        assert!(result.is_ok());

        let (upper, middle, lower) = result.unwrap();
        assert_eq!(upper.len(), 6);
        assert_eq!(middle.len(), 6);
        assert_eq!(lower.len(), 6);
    }

    #[test]
    fn test_keltner_channel_invalid_atr_period() {
        let high = vec![102.0, 105.0, 104.0];
        let low = vec![99.0, 101.0, 100.0];
        let close = vec![101.0, 103.0, 102.0];

        let result = keltner_channel(&high, &low, &close, 2, 0, 2.0);
        assert!(result.is_err());
    }

    // ==================== chandelier_exit tests ====================

    #[test]
    fn test_chandelier_exit_basic() {
        let high = vec![102.0, 105.0, 104.0, 106.0, 108.0, 110.0];
        let low = vec![99.0, 101.0, 100.0, 102.0, 104.0, 106.0];
        let close = vec![101.0, 103.0, 102.0, 105.0, 107.0, 109.0];

        let result = chandelier_exit(&high, &low, &close, 3, 3, 3.0);
        assert!(result.is_ok());

        let (long_exit, short_exit) = result.unwrap();
        assert_eq!(long_exit.len(), 6);
        assert_eq!(short_exit.len(), 6);
    }

    #[test]
    fn test_chandelier_exit_invalid_period() {
        let high = vec![102.0, 105.0];
        let low = vec![99.0, 101.0];
        let close = vec![101.0, 103.0];

        let result = chandelier_exit(&high, &low, &close, 0, 1, 3.0);
        assert!(result.is_err());
    }

    // ==================== historical_volatility tests ====================

    #[test]
    fn test_historical_volatility_basic() {
        let close: Vec<f64> = (100..120).map(|x| x as f64).collect();

        let result = historical_volatility(&close, 5);
        assert!(result.is_ok());

        let hv = result.unwrap();
        assert_eq!(hv.len(), 20);
    }

    #[test]
    fn test_historical_volatility_invalid_period_less_than_2() {
        let close = vec![100.0, 101.0, 102.0];

        let result = historical_volatility(&close, 1);
        assert!(result.is_err());
        match result {
            Err(HazeError::InvalidPeriod { period, .. }) => assert_eq!(period, 1),
            _ => panic!("Expected InvalidPeriod error"),
        }
    }

    #[test]
    fn test_historical_volatility_period_exceeds_data() {
        let close = vec![100.0, 101.0, 102.0];

        let result = historical_volatility(&close, 10);
        assert!(result.is_err());
    }

    // ==================== ulcer_index tests ====================

    #[test]
    fn test_ulcer_index_basic() {
        let close = vec![100.0, 98.0, 99.0, 97.0, 100.0, 102.0];

        let result = ulcer_index(&close, 3);
        assert!(result.is_ok());

        let ui = result.unwrap();
        assert_eq!(ui.len(), 6);
    }

    #[test]
    fn test_ulcer_index_invalid_period() {
        let close = vec![100.0, 101.0];

        let result = ulcer_index(&close, 0);
        assert!(result.is_err());

        let result = ulcer_index(&close, 5);
        assert!(result.is_err());
    }

    // ==================== mass_index tests ====================

    #[test]
    fn test_mass_index_basic() {
        let high: Vec<f64> = (100..120).map(|x| x as f64 + 5.0).collect();
        let low: Vec<f64> = (100..120).map(|x| x as f64).collect();

        let result = mass_index(&high, &low, 3, 5);
        assert!(result.is_ok());

        let mi = result.unwrap();
        assert_eq!(mi.len(), 20);
    }

    #[test]
    fn test_mass_index_invalid_ema_period() {
        let high = vec![100.0, 101.0];
        let low = vec![99.0, 100.0];

        let result = mass_index(&high, &low, 0, 5);
        assert!(result.is_err());
        match result {
            Err(HazeError::InvalidPeriod { period, .. }) => assert_eq!(period, 0),
            _ => panic!("Expected InvalidPeriod error"),
        }

        let result = mass_index(&high, &low, 3, 0);
        assert!(result.is_err());
    }

    #[test]
    fn test_mass_index_length_mismatch() {
        let high = vec![100.0, 101.0, 102.0];
        let low = vec![99.0, 100.0];

        let result = mass_index(&high, &low, 2, 2);
        assert!(result.is_err());
        match result {
            Err(HazeError::LengthMismatch { .. }) => {}
            _ => panic!("Expected LengthMismatch error"),
        }
    }
}
