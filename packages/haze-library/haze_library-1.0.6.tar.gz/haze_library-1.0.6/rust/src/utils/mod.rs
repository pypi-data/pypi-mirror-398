//! Utility Functions Module
//!
//! # Overview
//! This module provides foundational utilities for technical analysis calculations.
//! It includes moving averages, statistical functions, streaming calculators,
//! mathematical operations, and performance-optimized implementations.
//!
//! # Available Sub-modules
//!
//! ## Core Utilities
//! - [`ma`] - Moving average functions (SMA, EMA, RMA, WMA, DEMA, TEMA, KAMA, etc.)
//! - [`math`] - Low-level math utilities (NaN handling, precision constants)
//! - [`stats`] - Statistical functions (std dev, correlation, regression, rolling windows)
//! - [`math_ops`] - Mathematical operations and transformations
//!
//! ## Performance Utilities
//! - [`streaming`] - Online/incremental calculators for real-time systems
//! - [`parallel`] - Parallel computation using Rayon for batch processing
//! - [`simd_ops`] - SIMD-friendly operations for auto-vectorization
//!
//! # Design Philosophy
//! - **Building Blocks**: Utilities compose into higher-level indicators
//! - **Performance First**: Critical paths optimized for speed
//! - **Fail-Fast Validation**: Non-finite inputs are rejected; warmup NaNs are explicit
//! - **Zero Allocation**: Hot paths avoid memory allocation where possible
//!
//! # Usage Examples
//! ```rust
//! use haze_library::utils::{sma, ema, rma};
//! use haze_library::utils::stats::{stdev, linear_regression};
//! use haze_library::utils::streaming::OnlineSMA;
//!
//! let prices = vec![100.0, 101.0, 102.0, 103.0, 104.0];
//!
//! // Batch calculations
//! let sma_values = sma(&prices, 3);
//! let ema_values = ema(&prices, 3);
//!
//! // Statistical analysis
//! let volatility = stdev(&prices, 5);
//! let (slope, intercept, r_squared) = linear_regression(&prices, 5);
//!
//! // Real-time streaming
//! let mut online_sma = OnlineSMA::new(20).unwrap();
//! for price in prices {
//!     if let Some(value) = online_sma.update(price).unwrap() {
//!         println!("SMA: {}", value);
//!     }
//! }
//! ```
//!
//! # Cross-References
//! - [`crate::indicators`] - Technical indicators built on these utilities
//! - Module-specific documentation for detailed function lists

// utils/mod.rs - 工具模块
#![allow(unused_imports)]
#![allow(dead_code)] // 内部函数通过 PyO3 绑定使用

pub mod float_compare;
pub mod ma;
pub mod math;
pub mod math_ops;
pub mod parallel;
pub mod simd_ops;
pub mod stats;
pub mod streaming;

pub use float_compare::{
    approx_ge, approx_gt, approx_le, approx_lt, approx_not_zero, approx_zero, relative_eq,
    DEFAULT_EPSILON, RELAXED_EPSILON, STRICT_EPSILON,
};
pub use ma::*;
pub use math::*;
pub use math_ops::*;
pub use parallel::*;
pub use simd_ops::*;
pub use stats::*;
pub use streaming::*;
