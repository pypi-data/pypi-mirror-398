# Trend Module Documentation

## File Path
`/Users/zhaoleon/Desktop/haze/haze/rust/src/indicators/trend.rs`

## Proposed Module-Level Documentation

```rust
//! # Trend Indicators Module
//!
//! This module provides trend-following technical indicators that identify price
//! direction, measure trend strength, and detect potential reversals. Trend
//! indicators are fundamental for determining whether to trade with momentum or
//! against extremes, and for timing entry/exit points in directional moves.
//!
//! ## Module Purpose
//!
//! Trend indicators help traders:
//! - Identify the primary market direction (uptrend, downtrend, sideways)
//! - Measure the strength and sustainability of trends
//! - Detect early signs of trend exhaustion or reversal
//! - Filter trades to align with the dominant trend
//! - Set dynamic support/resistance levels
//!
//! All functions implement proven algorithms used by professional traders,
//! with optimizations for real-time calculation and backtesting.
//!
//! ## Main Exports
//!
//! ### Directional Movement System
//! - [`adx`] - Average Directional Index (trend strength 0-100)
//! - [`dx`] - Directional Movement Index (raw trend strength)
//! - [`plus_di`] - Positive Directional Indicator (+DI)
//! - [`minus_di`] - Negative Directional Indicator (-DI)
//!
//! ### Dynamic Support/Resistance
//! - [`supertrend`] - SuperTrend (ATR-based trailing indicator)
//! - [`psar`] - Parabolic SAR (trailing stop and reversal system)
//!
//! ### Time-Based Indicators
//! - [`aroon`] - Aroon Indicator (time since extreme highs/lows)
//!
//! ### Trend vs Range Identification
//! - [`vortex`] - Vortex Indicator (VI+ and VI- trend direction)
//! - [`choppiness_index`] - Choppiness Index (trending vs ranging market)
//! - [`vhf`] - Vertical Horizontal Filter (trend vs consolidation)
//!
//! ### Momentum-Based Trend
//! - [`qstick`] - QStick (buying/selling pressure)
//! - [`trix`] - Triple Exponential Average (rate of change)
//! - [`dpo`] - Detrended Price Oscillator (cycle identification)
//!
//! ## Usage Examples
//!
//! ### SuperTrend Trading System
//! ```rust,ignore
//! use haze_library::indicators::trend::supertrend;
//!
//! let high = vec![102.0, 105.0, 104.0, 106.0, 108.0, 107.0, 109.0, 111.0];
//! let low = vec![99.0, 101.0, 100.0, 102.0, 104.0, 103.0, 105.0, 107.0];
//! let close = vec![101.0, 103.0, 102.0, 105.0, 107.0, 106.0, 108.0, 110.0];
//!
//! // 7-period ATR with 3.0 multiplier (standard settings)
//! let (supertrend_line, direction, upper, lower) =
//!     supertrend(&high, &low, &close, 7, 3.0);
//!
//! // Generate signals
//! for i in 8..close.len() {
//!     if direction[i-1] == -1.0 && direction[i] == 1.0 {
//!         println!("Buy signal at {}: price crossed above {:.2}",
//!                  i, supertrend_line[i]);
//!     } else if direction[i-1] == 1.0 && direction[i] == -1.0 {
//!         println!("Sell signal at {}: price crossed below {:.2}",
//!                  i, supertrend_line[i]);
//!     }
//! }
//! ```
//!
//! ### ADX Trend Strength Filter
//! ```rust,ignore
//! use haze_library::indicators::trend::adx;
//!
//! let high = vec![110.0, 111.0, 112.0, 113.0, 114.0, 115.0, 116.0, 117.0];
//! let low = vec![100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0];
//! let close = vec![105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0];
//!
//! let (adx_values, plus_di_vals, minus_di_vals) = adx(&high, &low, &close, 14);
//!
//! // Only trade when trend is strong
//! let idx = close.len() - 1;
//! if adx_values[idx] > 25.0 {
//!     if plus_di_vals[idx] > minus_di_vals[idx] {
//!         println!("Strong uptrend: ADX={:.1}, +DI={:.1} > -DI={:.1}",
//!                  adx_values[idx], plus_di_vals[idx], minus_di_vals[idx]);
//!     } else {
//!         println!("Strong downtrend: ADX={:.1}, -DI={:.1} > +DI={:.1}",
//!                  adx_values[idx], minus_di_vals[idx], plus_di_vals[idx]);
//!     }
//! } else {
//!     println!("Weak trend or ranging: ADX={:.1}", adx_values[idx]);
//! }
//! ```
//!
//! ### Parabolic SAR Trailing Stop
//! ```rust,ignore
//! use haze_library::indicators::trend::psar;
//!
//! let high = vec![102.0, 105.0, 104.0, 106.0, 108.0];
//! let low = vec![99.0, 101.0, 100.0, 102.0, 104.0];
//! let close = vec![101.0, 103.0, 102.0, 105.0, 107.0];
//!
//! // Standard PSAR settings: 0.02 initial, 0.02 increment, 0.2 max
//! let (psar_values, trend) = psar(&high, &low, &close, 0.02, 0.02, 0.2);
//!
//! // Use as trailing stop
//! for i in 1..close.len() {
//!     if trend[i] == 1.0 {
//!         println!("Long position: stop at {:.2}", psar_values[i]);
//!     } else {
//!         println!("Short position: stop at {:.2}", psar_values[i]);
//!     }
//! }
//! ```
//!
//! ### Choppiness Index for Market Phase
//! ```rust,ignore
//! use haze_library::indicators::trend::choppiness_index;
//!
//! let high = vec![/* ... */];
//! let low = vec![/* ... */];
//! let close = vec![/* ... */];
//!
//! let chop = choppiness_index(&high, &low, &close, 14);
//!
//! // Determine market phase
//! let current_chop = chop.last().unwrap();
//! if *current_chop > 61.8 {
//!     println!("Market is ranging (CHOP={:.1}) - use mean reversion", current_chop);
//! } else if *current_chop < 38.2 {
//!     println!("Market is trending (CHOP={:.1}) - use trend following", current_chop);
//! } else {
//!     println!("Market is transitioning (CHOP={:.1})", current_chop);
//! }
//! ```
//!
//! ### Combined ADX and Aroon Strategy
//! ```rust,ignore
//! use haze_library::indicators::trend::{adx, aroon};
//!
//! let high = vec![/* ... */];
//! let low = vec![/* ... */];
//! let close = vec![/* ... */];
//!
//! let (adx_vals, _, _) = adx(&high, &low, &close, 14);
//! let (aroon_up, aroon_down, _) = aroon(&high, &low, 25);
//!
//! // Strong uptrend confirmation
//! let idx = close.len() - 1;
//! if adx_vals[idx] > 25.0 && aroon_up[idx] > 70.0 && aroon_down[idx] < 30.0 {
//!     println!("Confirmed uptrend: ADX={:.1}, Aroon Up={:.1}",
//!              adx_vals[idx], aroon_up[idx]);
//! }
//! ```
//!
//! ## Performance Characteristics
//!
//! - **SuperTrend**: O(n) with ATR calculation and state machine tracking
//! - **ADX**: O(n) using RMA (Relative Moving Average) smoothing for DM
//! - **PSAR**: O(n) with iterative EP (Extreme Point) and AF (Acceleration Factor) updates
//! - **Aroon**: O(n) with efficient lookback for highest high/lowest low positions
//! - **Choppiness**: O(n * period) for rolling true range sum
//!
//! All indicators are optimized for single-pass calculation where possible,
//! minimizing computational overhead for real-time applications.
//!
//! ## Trend Signal Interpretation
//!
//! - **ADX**: >25 = strong trend, 20-25 = emerging trend, <20 = weak/ranging
//! - **SuperTrend**: direction = 1.0 (uptrend), -1.0 (downtrend)
//! - **PSAR**: trend = 1.0 (bullish), -1.0 (bearish)
//! - **Aroon**: Up > 70 && Down < 30 = strong uptrend (vice versa for downtrend)
//! - **Choppiness**: >61.8 = ranging, <38.2 = trending
//! - **VHF**: High values = trending, low values = choppy
//!
//! ## Error Handling
//!
//! Functions return tuple results directly (no Result wrapper) with NaN values
//! for invalid inputs or warmup periods. Always check for NaN before using values:
//!
//! ```rust,ignore
//! let (st_line, direction, _, _) = supertrend(&high, &low, &close, 7, 3.0);
//! if !direction[i].is_nan() {
//!     // Safe to use direction[i]
//! }
//! ```
//!
//! ## Related Modules
//!
//! - [`crate::indicators::volatility`] - ATR used in SuperTrend and other calculations
//! - [`crate::indicators::momentum`] - Momentum confirmation for trend signals
//! - [`crate::utils::ma`] - RMA/EMA for smoothing directional movement
//! - [`crate::utils::stats`] - Rolling max/min for Aroon calculation
```

## Implementation Notes

- **Current State**: Module has good overview documentation
- **Improvements**: Added detailed strategy examples, signal interpretation guide, phase detection
- **Coverage Impact**: Adds ~160 lines of practical trading system examples
