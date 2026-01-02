# Volatility Module Documentation

## File Path
`/Users/zhaoleon/Desktop/haze/haze/rust/src/indicators/volatility.rs`

## Proposed Module-Level Documentation

```rust
//! # Volatility Indicators Module
//!
//! This module provides volatility-based technical indicators that measure the
//! degree and pattern of price variation over time. Volatility indicators are
//! essential for risk management, position sizing, breakout detection, and
//! identifying periods of market consolidation versus expansion.
//!
//! ## Module Purpose
//!
//! Volatility indicators help traders and analysts:
//! - Assess market risk and adjust position sizes accordingly
//! - Identify price breakouts from consolidation ranges
//! - Set dynamic stop-loss levels based on market conditions
//! - Detect volatility expansion (potential trend starts) and contraction (ranging markets)
//! - Compare volatility across different instruments and timeframes
//!
//! All functions implement industry-standard algorithms with TA-Lib compatibility
//! for seamless integration into trading systems.
//!
//! ## Main Exports
//!
//! ### True Range Components
//! - [`true_range`] - True Range (max range considering gaps)
//! - [`atr`] - Average True Range (Wilder's smoothed TR)
//! - [`natr`] - Normalized ATR (percentage of price)
//!
//! ### Volatility Bands
//! - [`bollinger_bands`] - Bollinger Bands (SMA ± standard deviation)
//! - [`keltner_channel`] - Keltner Channel (EMA ± ATR)
//! - [`donchian_channel`] - Donchian Channel (highest high/lowest low)
//!
//! ### Trailing Stop Systems
//! - [`chandelier_exit`] - Chandelier Exit (ATR-based trailing stops)
//!
//! ### Statistical Volatility
//! - [`historical_volatility`] - Historical Volatility (annualized log returns)
//! - [`ulcer_index`] - Ulcer Index (downside risk measure)
//! - [`mass_index`] - Mass Index (range expansion indicator)
//!
//! ## Usage Examples
//!
//! ### Basic ATR Calculation
//! ```rust,ignore
//! use haze_library::indicators::volatility::atr;
//!
//! let high = vec![102.0, 105.0, 104.0, 106.0, 108.0];
//! let low = vec![99.0, 101.0, 100.0, 102.0, 104.0];
//! let close = vec![101.0, 103.0, 102.0, 105.0, 107.0];
//!
//! // Calculate 3-period ATR
//! let atr_values = atr(&high, &low, &close, 3)?;
//!
//! // Use ATR for position sizing
//! let risk_per_trade = 100.0; // $100 risk
//! let atr_multiplier = 2.0;   // 2x ATR stop
//! let current_atr = atr_values.last().unwrap();
//! let position_size = risk_per_trade / (current_atr * atr_multiplier);
//! println!("Position size: {:.2} shares", position_size);
//! ```
//!
//! ### Bollinger Bands Squeeze Strategy
//! ```rust,ignore
//! use haze_library::indicators::volatility::bollinger_bands;
//!
//! let close = vec![100.0, 101.0, 102.0, 103.0, 104.0, 105.0];
//!
//! // 20-period BB with 2 std dev
//! let (upper, middle, lower) = bollinger_bands(&close, 20, 2.0)?;
//!
//! // Detect squeeze (narrow bands = low volatility)
//! for i in 20..close.len() {
//!     let bandwidth = (upper[i] - lower[i]) / middle[i] * 100.0;
//!     if bandwidth < 5.0 {
//!         println!("Squeeze detected at bar {} - breakout imminent", i);
//!     }
//! }
//! ```
//!
//! ### Dynamic Stop Loss with Chandelier Exit
//! ```rust,ignore
//! use haze_library::indicators::volatility::chandelier_exit;
//!
//! let high = vec![102.0, 105.0, 104.0, 106.0, 108.0, 110.0];
//! let low = vec![99.0, 101.0, 100.0, 102.0, 104.0, 106.0];
//! let close = vec![101.0, 103.0, 102.0, 105.0, 107.0, 109.0];
//!
//! // 22-period Chandelier with 3x ATR
//! let (long_stop, short_stop) = chandelier_exit(
//!     &high, &low, &close,
//!     22,  // period
//!     22,  // ATR period
//!     3.0  // ATR multiplier
//! )?;
//!
//! // Long position: exit if close < long_stop
//! let current_price = close.last().unwrap();
//! let stop_level = long_stop.last().unwrap();
//! println!("Long stop: {:.2} ({:.1}% below price)",
//!          stop_level, (current_price - stop_level) / current_price * 100.0);
//! ```
//!
//! ### Multi-Channel Confirmation
//! ```rust,ignore
//! use haze_library::indicators::volatility::{
//!     bollinger_bands, keltner_channel, donchian_channel
//! };
//!
//! let high = vec![/* ... */];
//! let low = vec![/* ... */];
//! let close = vec![/* ... */];
//!
//! let (bb_upper, bb_mid, bb_lower) = bollinger_bands(&close, 20, 2.0)?;
//! let (kc_upper, kc_mid, kc_lower) = keltner_channel(&high, &low, &close, 20, 10, 2.0)?;
//! let (dc_upper, dc_mid, dc_lower) = donchian_channel(&high, &low, 20)?;
//!
//! // Squeeze: BB inside KC
//! let idx = close.len() - 1;
//! if bb_upper[idx] < kc_upper[idx] && bb_lower[idx] > kc_lower[idx] {
//!     println!("TTM Squeeze active - consolidation phase");
//! }
//! ```
//!
//! ## Performance Characteristics
//!
//! - **ATR**: O(n) using incremental Wilder's smoothing (RMA)
//! - **Bollinger Bands**: O(n) with rolling mean and standard deviation
//! - **Donchian Channel**: O(n) using monotonic deque for rolling max/min
//! - **Keltner Channel**: O(n) combining EMA and ATR calculations
//! - **Historical Volatility**: O(n) with logarithmic returns calculation
//!
//! All functions minimize memory allocations and use efficient rolling window
//! algorithms. For large datasets (>10k bars), expect microsecond-level latency
//! per indicator on modern CPUs.
//!
//! ## Error Handling
//!
//! All public functions return `HazeResult<T>` with specific error types:
//!
//! - `HazeError::EmptyInput`: Any input array is empty
//! - `HazeError::LengthMismatch`: Input arrays have different lengths
//! - `HazeError::InvalidPeriod`: Period is 0 or exceeds data length
//! - `HazeError::InsufficientData`: Not enough data for computation
//! - `HazeError::ParameterOutOfRange`: Invalid multiplier or parameter value
//!
//! ## Related Modules
//!
//! - [`crate::indicators::trend`] - SuperTrend uses ATR for band calculation
//! - [`crate::indicators::momentum`] - Normalized momentum with ATR
//! - [`crate::utils::stats`] - Standard deviation and rolling functions
//! - [`crate::utils::ma`] - EMA/SMA for band center lines
```

## Implementation Notes

- **Current State**: Module has good basic documentation
- **Improvements**: Added multi-channel examples, position sizing use cases, squeeze detection
- **Coverage Impact**: Adds ~140 lines of practical examples and performance details
