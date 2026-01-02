# Stats Module Documentation

## File Path
`/Users/zhaoleon/Desktop/haze/haze/rust/src/utils/stats.rs`

## Proposed Module-Level Documentation

```rust
//! # Statistical Utilities Module
//!
//! This module provides fundamental statistical functions and analysis tools for
//! technical analysis, including rolling window calculations, regression analysis,
//! and correlation metrics. These functions serve as building blocks for indicators,
//! risk assessment calculations, and quantitative strategy development.
//!
//! ## Module Purpose
//!
//! Statistical utilities enable:
//! - Rolling window analytics (mean, variance, extremes, percentiles)
//! - Linear regression for trend analysis and forecasting
//! - Correlation and covariance for pair trading and portfolio analysis
//! - Risk metrics (beta, standard deviation, drawdown measures)
//! - Momentum calculations (ROC, raw momentum)
//!
//! All functions are optimized for financial time series with proper NaN handling
//! and efficient rolling window algorithms.
//!
//! ## Main Exports
//!
//! ### Basic Rolling Statistics
//! - [`stdev`] - Sample standard deviation (n-1 denominator)
//! - [`stdev_population`] - Population standard deviation (n denominator)
//! - [`var`] - Rolling variance (with Kahan summation for precision)
//! - [`var_precise`] - High-precision variance (always uses Kahan)
//! - [`stdev_precise`] - High-precision standard deviation
//!
//! ### Rolling Window Aggregations
//! - [`rolling_max`] - O(n) rolling maximum using monotonic deque
//! - [`rolling_min`] - O(n) rolling minimum using monotonic deque
//! - [`rolling_sum`] - O(n) rolling sum with error correction
//! - [`rolling_percentile`] - Rolling percentile/median calculation
//!
//! ### Momentum Statistics
//! - [`roc`] - Rate of Change (percentage price change)
//! - [`momentum`] - Momentum (absolute price change)
//!
//! ### Linear Regression Analysis
//! - [`linear_regression`] - Full regression (slope, intercept, R²)
//! - [`linearreg`] - Regression endpoint value (TA-Lib compatible)
//! - [`linearreg_slope`] - Regression slope
//! - [`linearreg_angle`] - Regression angle in degrees
//! - [`linearreg_intercept`] - Regression intercept
//! - [`standard_error`] - Regression standard error
//! - [`tsf`] - Time Series Forecast (next point prediction)
//!
//! ### Correlation and Risk Metrics
//! - [`correlation`] / [`correl`] - Pearson correlation coefficient
//! - [`covariance`] - Rolling covariance between two series
//! - [`beta`] - Beta coefficient (systematic risk measure)
//! - [`zscore`] - Z-Score standardization
//!
//! ## Usage Examples
//!
//! ### Rolling Statistics for Indicators
//! ```rust,ignore
//! use haze_library::utils::stats::{stdev, rolling_max, rolling_min};
//!
//! let close = vec![100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0];
//!
//! // Calculate 3-period rolling standard deviation
//! let std_values = stdev(&close, 3);
//!
//! // Calculate rolling high/low for range identification
//! let highs = rolling_max(&close, 3);
//! let lows = rolling_min(&close, 3);
//!
//! for i in 2..close.len() {
//!     let range = highs[i] - lows[i];
//!     let volatility = std_values[i];
//!     println!("Bar {}: range={:.2}, vol={:.2}", i, range, volatility);
//! }
//! ```
//!
//! ### Linear Regression Trend Analysis
//! ```rust,ignore
//! use haze_library::utils::stats::{linear_regression, linearreg_slope};
//!
//! let prices = vec![100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 106.0];
//!
//! // Full regression analysis
//! let (slopes, intercepts, r_squared) = linear_regression(&prices, 5);
//!
//! // Identify trend strength
//! for i in 4..prices.len() {
//!     if !slopes[i].is_nan() {
//!         let trend_strength = if r_squared[i] > 0.8 { "strong" }
//!                             else if r_squared[i] > 0.5 { "moderate" }
//!                             else { "weak" };
//!         println!("Trend: slope={:.2}, R²={:.2} ({})",
//!                  slopes[i], r_squared[i], trend_strength);
//!     }
//! }
//!
//! // Calculate regression angle for visual interpretation
//! let angles = linearreg_slope(&prices, 5)
//!     .iter()
//!     .map(|&slope| slope.atan().to_degrees())
//!     .collect::<Vec<_>>();
//! ```
//!
//! ### Pair Trading with Correlation
//! ```rust,ignore
//! use haze_library::utils::stats::{correlation, covariance, beta};
//!
//! let asset_a = vec![100.0, 102.0, 101.0, 103.0, 105.0];
//! let asset_b = vec![50.0, 51.0, 50.5, 51.5, 52.5];
//!
//! // Calculate rolling correlation
//! let corr = correlation(&asset_a, &asset_b, 5);
//!
//! // Calculate covariance for spread calculation
//! let cov = covariance(&asset_a, &asset_b, 5);
//!
//! // Beta for hedge ratio
//! let beta_vals = beta(&asset_a, &asset_b, 5);
//!
//! if let Some(&correlation) = corr.last() {
//!     if correlation > 0.8 {
//!         println!("Strong positive correlation: {:.3}", correlation);
//!         println!("Hedge ratio (beta): {:.3}", beta_vals.last().unwrap());
//!     }
//! }
//! ```
//!
//! ### Z-Score for Mean Reversion
//! ```rust,ignore
//! use haze_library::utils::stats::zscore;
//!
//! let prices = vec![100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 102.0];
//!
//! // Calculate z-score with 5-period lookback
//! let z_scores = zscore(&prices, 5);
//!
//! // Generate mean reversion signals
//! for i in 4..prices.len() {
//!     if !z_scores[i].is_nan() {
//!         if z_scores[i] > 2.0 {
//!             println!("Overbought: Z-score = {:.2}", z_scores[i]);
//!         } else if z_scores[i] < -2.0 {
//!             println!("Oversold: Z-score = {:.2}", z_scores[i]);
//!         }
//!     }
//! }
//! ```
//!
//! ### Time Series Forecasting
//! ```rust,ignore
//! use haze_library::utils::stats::tsf;
//!
//! let prices = vec![100.0, 102.0, 104.0, 106.0, 108.0, 110.0];
//!
//! // Forecast next price using linear regression
//! let forecasts = tsf(&prices, 5);
//!
//! if let Some(&forecast) = forecasts.last() {
//!     if !forecast.is_nan() {
//!         let current = prices.last().unwrap();
//!         let expected_move = forecast - current;
//!         println!("Current: {:.2}, Forecast: {:.2}, Expected: {:+.2}",
//!                  current, forecast, expected_move);
//!     }
//! }
//! ```
//!
//! ## Performance Characteristics
//!
//! - **Rolling max/min**: O(n) amortized using monotonic deque algorithm
//! - **Rolling sum**: O(n) with incremental updates and periodic recalibration
//! - **Standard deviation/variance**: O(n * period) for rolling windows
//! - **Regression**: O(n * period) for full computation at each point
//! - **Correlation/Beta**: O(n * period) with rolling windows
//!
//! ### Numerical Precision
//!
//! - **Kahan Summation**: Used in `rolling_sum` (recalc every 1000 iterations)
//! - **var_precise/stdev_precise**: Always use Kahan for ML/critical paths
//! - **var/stdev**: Use Kahan when period >= threshold (default 100)
//!
//! For high-precision requirements (ML feature engineering, risk calculations),
//! prefer `*_precise` variants at ~10% performance cost for improved accuracy.
//!
//! ## NaN Handling
//!
//! All functions follow consistent NaN handling:
//! - Return NaN for warmup periods (first `period-1` values)
//! - NaN values in input propagate through calculations
//! - Rolling max/min skip NaN values within windows when possible
//! - Division by zero or invalid operations return NaN
//!
//! Always check for NaN before using results:
//! ```rust,ignore
//! if !result[i].is_nan() {
//!     // Safe to use result[i]
//! }
//! ```
//!
//! ## Error Handling
//!
//! Functions return empty vectors or NaN-filled vectors for invalid inputs:
//! - Empty input → empty Vec or all-NaN Vec
//! - Invalid period (0 or > data length) → all-NaN Vec
//! - Mismatched input lengths → all-NaN Vec
//!
//! No panics occur from normal usage - all edge cases handled gracefully.
//!
//! ## Related Modules
//!
//! - [`crate::indicators::volatility`] - Uses stdev for Bollinger Bands
//! - [`crate::indicators::momentum`] - Uses rolling_max/min for Stochastic
//! - [`crate::indicators::trend`] - Uses regression for trend analysis
//! - [`crate::utils::ma`] - Complementary moving average functions
//! - [`crate::utils::math`] - Kahan summation and math utilities
```

## Implementation Notes

- **Current State**: Module has excellent comprehensive documentation already
- **Improvements**: Enhanced examples for pair trading, forecasting, z-score strategies
- **Coverage Impact**: Adds ~150 lines with more practical use cases and precision notes
