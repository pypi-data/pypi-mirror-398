//! Technical Indicators Module
//!
//! # Overview
//! This module provides a comprehensive suite of technical analysis indicators
//! commonly used in quantitative trading. All indicators are implemented with
//! O(n) time complexity and follow consistent NaN-handling conventions for
//! warmup periods.
//!
//! # Available Sub-modules
//!
//! ## Core Indicators
//! - [`momentum`] - RSI, MACD, Stochastic, CCI, Williams %R, ROC, MOM, etc.
//! - [`volatility`] - ATR, Bollinger Bands, Keltner Channels, Donchian, etc.
//! - [`trend`] - ADX, SuperTrend, PSAR, Aroon, Choppiness Index, etc.
//! - [`volume`] - OBV, VWAP, MFI, CMF, Accumulation/Distribution, etc.
//! - [`overlap`] - Moving averages and overlay studies
//!
//! ## Advanced Indicators
//! - [`harmonics`] - Harmonic pattern detection
//! - [`fibonacci`] - Fibonacci retracement and extension levels
//! - [`ichimoku`] - Ichimoku Cloud components
//! - [`pivots`] - Pivot points and support/resistance levels
//! - [`candlestick`] - Candlestick pattern recognition
//!
//! ## Specialized Indicators
//! - [`price_transform`] - Price transformation functions
//! - [`cycle`] - Cycle analysis indicators
//! - [`sfg`] - SFG indicator suite
//! - [`sfg_signals`] - SFG signal generation
//! - [`sfg_utils`] - SFG utility functions
//! - [`pandas_ta`] - Pandas-TA compatible implementations
//!
//! # Usage Pattern
//! All indicators follow a consistent API pattern:
//! - Input: Price arrays (close, high, low, open, volume as needed)
//! - Output: `Vec<f64>` with NaN for warmup periods
//! - Period parameter controls lookback window
//!
//! # Examples
//! ```rust,no_run
//! use haze_library::indicators::{momentum::rsi, trend::supertrend};
//!
//! let close = vec![
//!     100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 104.5, 104.0, 105.0, 106.0,
//!     107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0, 115.0, 116.0,
//! ];
//! let high: Vec<f64> = close.iter().map(|&v| v + 1.0).collect();
//! let low: Vec<f64> = close.iter().map(|&v| v - 1.0).collect();
//!
//! // Momentum indicator
//! let rsi_values = rsi(&close, 14).unwrap();
//! assert_eq!(rsi_values.len(), close.len());
//!
//! // Trend indicator with OHLC data
//! let (st_line, direction, upper, lower) = supertrend(&high, &low, &close, 10, 3.0).unwrap();
//! assert_eq!(st_line.len(), close.len());
//! assert_eq!(direction.len(), close.len());
//! assert_eq!(upper.len(), close.len());
//! assert_eq!(lower.len(), close.len());
//! ```
//!
//! # Cross-References
//! - [`crate::utils::ma`] - Moving average implementations used by indicators
//! - [`crate::utils::stats`] - Statistical utilities for calculations
//! - [`crate::utils::streaming`] - Online/incremental indicator versions

#![allow(unused_imports)]
#![allow(dead_code)] // 内部函数通过 PyO3 绑定使用
                     // indicators/mod.rs - 指标模块
pub mod candlestick;
pub mod cycle;
pub mod fibonacci;
pub mod harmonics;
pub mod ichimoku;
pub mod momentum;
pub mod overlap;
pub mod pandas_ta;
pub mod pandas_ta_compat;
pub mod pivots;
pub mod price_transform;
pub mod sfg;
pub mod sfg_signals;
pub mod sfg_utils;
pub mod trend;
pub mod volatility;
pub mod volume;

pub use candlestick::*;
pub use cycle::*;
pub use fibonacci::*;
pub use harmonics::*;
pub use ichimoku::*;
pub use momentum::*;
pub use overlap::*;
pub use pandas_ta::*;
pub use pivots::*;
pub use price_transform::{avgprice, medprice, typprice, wclprice};
pub use sfg::*;
pub use sfg_signals::*;
pub use sfg_utils::*;
pub use trend::*;
pub use volatility::*;
pub use volume::*;
