# Momentum Module Documentation

## File Path
`/Users/zhaoleon/Desktop/haze/haze/rust/src/indicators/momentum.rs`

## Proposed Module-Level Documentation

```rust
//! # Momentum Indicators Module
//!
//! This module provides a comprehensive suite of momentum-based technical indicators
//! for measuring the rate and magnitude of price changes. Momentum indicators are
//! essential for identifying overbought/oversold conditions, trend strength validation,
//! and potential reversal points in financial markets.
//!
//! ## Module Purpose
//!
//! Momentum indicators measure the velocity of price movements to help traders:
//! - Identify market extremes (overbought/oversold levels)
//! - Confirm trend strength and sustainability
//! - Detect early reversal signals through divergence patterns
//! - Time entry and exit points based on momentum shifts
//!
//! All functions implement industry-standard algorithms with TA-Lib compatibility
//! and robust error handling for production use.
//!
//! ## Main Exports
//!
//! ### Oscillators (0-100 Range)
//! - [`rsi`] - Relative Strength Index (Wilder's RSI)
//! - [`stochastic`] - Stochastic Oscillator (%K/%D)
//! - [`stochrsi`] - Stochastic RSI (combines RSI + Stochastic)
//! - [`kdj`] - KDJ Indicator (Stochastic with J line)
//!
//! ### Divergence Indicators
//! - [`macd`] - Moving Average Convergence Divergence
//! - [`apo`] - Absolute Price Oscillator
//! - [`ppo`] - Percentage Price Oscillator
//!
//! ### Statistical Oscillators
//! - [`cci`] - Commodity Channel Index
//! - [`williams_r`] - Williams %R (-100 to 0)
//! - [`cmo`] - Chande Momentum Oscillator
//!
//! ### Advanced Momentum
//! - [`awesome_oscillator`] - Bill Williams' Awesome Oscillator
//! - [`fisher_transform`] - Fisher Transform (Gaussian normalization)
//! - [`tsi`] - True Strength Index (double-smoothed momentum)
//! - [`ultimate_oscillator`] - Multi-timeframe weighted momentum
//!
//! ## Usage Examples
//!
//! ### Basic RSI Calculation
//! ```rust,ignore
//! use haze_library::indicators::momentum::rsi;
//!
//! let close = vec![44.0, 44.25, 44.5, 44.0, 43.75, 44.0, 44.25, 44.5,
//!                  44.75, 45.0, 45.25, 45.0, 44.75, 45.0, 45.25];
//!
//! // Calculate 14-period RSI
//! let rsi_values = rsi(&close, 14)?;
//!
//! // Interpret signals
//! for (i, &value) in rsi_values.iter().enumerate() {
//!     if !value.is_nan() {
//!         if value > 70.0 {
//!             println!("Bar {}: Overbought (RSI = {:.2})", i, value);
//!         } else if value < 30.0 {
//!             println!("Bar {}: Oversold (RSI = {:.2})", i, value);
//!         }
//!     }
//! }
//! ```
//!
//! ### MACD Crossover Strategy
//! ```rust,ignore
//! use haze_library::indicators::momentum::macd;
//!
//! let close = vec![/* ... price data ... */];
//!
//! // Standard MACD(12,26,9)
//! let (macd_line, signal, histogram) = macd(&close, 12, 26, 9)?;
//!
//! // Detect crossover signals
//! for i in 1..macd_line.len() {
//!     if !macd_line[i].is_nan() && !signal[i].is_nan() {
//!         if macd_line[i-1] < signal[i-1] && macd_line[i] > signal[i] {
//!             println!("Bullish crossover at bar {}", i);
//!         }
//!     }
//! }
//! ```
//!
//! ### Multi-Indicator Confirmation
//! ```rust,ignore
//! use haze_library::indicators::momentum::{rsi, stochastic, cci};
//!
//! let high = vec![/* ... */];
//! let low = vec![/* ... */];
//! let close = vec![/* ... */];
//!
//! let rsi_vals = rsi(&close, 14)?;
//! let (stoch_k, stoch_d) = stochastic(&high, &low, &close, 14, 3, 3)?;
//! let cci_vals = cci(&high, &low, &close, 20)?;
//!
//! // Triple confirmation for oversold bounce
//! let idx = close.len() - 1;
//! if rsi_vals[idx] < 30.0 && stoch_k[idx] < 20.0 && cci_vals[idx] < -100.0 {
//!     println!("Strong oversold signal - potential reversal");
//! }
//! ```
//!
//! ## Performance Characteristics
//!
//! - **RSI/MACD**: O(n) single-pass algorithms using exponential smoothing
//! - **Stochastic/Williams %R**: O(n) with monotonic deque for rolling max/min
//! - **CCI**: O(n) with rolling mean deviation calculation
//! - **TSI/Ultimate Oscillator**: O(n) with multiple smoothing passes
//!
//! All functions use NaN for warmup periods where insufficient data exists,
//! following TA-Lib conventions. First valid value appears at index `period`
//! or later depending on the indicator's lookback requirement.
//!
//! ## Error Handling
//!
//! All public functions return `Result<T, HazeError>` with detailed error types:
//!
//! - `HazeError::EmptyInput`: Input array is empty
//! - `HazeError::InvalidPeriod`: Period is 0 or exceeds data length
//! - `HazeError::InsufficientData`: Not enough data points for computation
//! - `HazeError::LengthMismatch`: Input arrays have different lengths
//!
//! ## Related Modules
//!
//! - [`crate::indicators::volatility`] - ATR used in normalized momentum
//! - [`crate::indicators::trend`] - Directional indicators (ADX, Aroon)
//! - [`crate::utils::ma`] - EMA/SMA building blocks
//! - [`crate::utils::stats`] - Rolling max/min/stddev utilities
```

## Implementation Notes

- **Current State**: Module has basic documentation covering overview and function list
- **Improvements**: Enhanced with detailed usage examples, categorized exports, performance notes
- **Coverage Impact**: This documentation adds ~150 lines of comprehensive module-level docs
