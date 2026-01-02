//! Parallel Computation Module
//!
//! # Overview
//! This module provides parallel computation utilities using Rayon for batch
//! processing of technical indicators across multiple symbols or timeframes.
//! It enables efficient multi-core utilization for computationally intensive
//! indicator calculations in trading systems.
//!
//! # Design Philosophy
//! - **KISS Principle**: Only the most common parallel patterns are provided
//! - **Zero-Copy**: Uses references where possible to minimize memory overhead
//! - **Work-Stealing**: Rayon's work-stealing scheduler for load balancing
//!
//! # Available Functions
//!
//! ## Multi-Symbol Parallelization
//! - [`parallel_sma`] - Compute SMA for multiple trading pairs simultaneously
//! - [`parallel_ema`] - Compute EMA for multiple trading pairs simultaneously
//! - [`parallel_rsi`] - Compute RSI for multiple trading pairs simultaneously
//! - [`parallel_atr`] - Compute ATR for multiple trading pairs simultaneously
//!
//! ## Multi-Period Parallelization
//! - [`parallel_multi_period_sma`] - Compute multiple SMA periods (5, 10, 20, etc.)
//! - [`parallel_multi_period_ema`] - Compute multiple EMA periods (12, 26, etc.)
//!
//! ## Generic Parallelization
//! - [`parallel_compute`] - Generic parallel map for any indicator function
//!
//! ## Configuration
//! - [`configure_thread_pool`] - Configure Rayon thread pool size
//!
//! # Examples
//! ```rust
//! use haze_library::utils::parallel::{parallel_sma, parallel_multi_period_sma};
//!
//! let btc_prices = vec![100.0, 101.0, 102.0, 103.0, 104.0];
//! let eth_prices = vec![50.0, 51.0, 52.0, 53.0, 54.0];
//!
//! // Compute SMA for multiple symbols in parallel
//! let data_sets: Vec<(&str, &[f64], usize)> = vec![
//!     ("BTC", &btc_prices, 3),
//!     ("ETH", &eth_prices, 3),
//! ];
//! let results = parallel_sma(&data_sets).unwrap();
//!
//! // Compute multiple periods for single symbol
//! let multi_sma = parallel_multi_period_sma(&btc_prices, &[3, 5]).unwrap();
//! ```
//!
//! # Performance Characteristics
//! - Parallelization overhead: ~1-5 microseconds per task spawn
//! - Recommended: Use for datasets > 1000 elements or > 4 symbols
//! - For small datasets, sequential computation may be faster
//!
//! # Thread Pool Configuration
//! ```rust
//! use haze_library::utils::parallel::configure_thread_pool;
//!
//! // Use 4 threads (0 = Rayon default based on CPU cores)
//! configure_thread_pool(4).expect("Failed to configure thread pool");
//! ```
//!
//! # Cross-References
//! - [`crate::utils::ma`] - Underlying SMA/EMA implementations
//! - [`crate::indicators::momentum`] - RSI implementation
//! - [`crate::indicators::volatility`] - ATR implementation

#![allow(dead_code)]
// Parallel OHLCV dataset processing requires complex tuple types
#![allow(clippy::type_complexity)]

use crate::errors::validation::{validate_lengths_match, validate_not_empty, validate_period};
use crate::errors::{HazeError, HazeResult};
use crate::init_result;
use rayon::prelude::*;

use super::ma::{ema, sma};

/// 并行计算多组 SMA
///
/// 适用场景：同时计算多个交易对的 SMA
///
/// # 参数
/// - `data_sets`: 多组输入数据 (symbol_id, values, period)
///
/// # 返回
/// - `HazeResult<Vec<(symbol_id, sma_values)>>`
pub fn parallel_sma<'a>(
    data_sets: &[(&'a str, &[f64], usize)],
) -> HazeResult<Vec<(&'a str, Vec<f64>)>> {
    for (_, values, period) in data_sets {
        validate_not_empty(values, "values")?;
        validate_period(*period, values.len())?;
    }

    Ok(data_sets
        .par_iter()
        .map(|(symbol, values, period)| {
            (
                *symbol,
                sma(values, *period).expect("parallel_sma: validated input"),
            )
        })
        .collect())
}

/// 并行计算多组 EMA
///
/// 适用场景：同时计算多个交易对的 EMA
///
/// # 参数
/// - `data_sets`: 多组输入数据 (symbol_id, values, period)
///
/// # 返回
/// - `HazeResult<Vec<(symbol_id, ema_values)>>`
pub fn parallel_ema<'a>(
    data_sets: &[(&'a str, &[f64], usize)],
) -> HazeResult<Vec<(&'a str, Vec<f64>)>> {
    for (_, values, period) in data_sets {
        validate_not_empty(values, "values")?;
        validate_period(*period, values.len())?;
    }

    Ok(data_sets
        .par_iter()
        .map(|(symbol, values, period)| {
            (
                *symbol,
                ema(values, *period).expect("parallel_ema: validated input"),
            )
        })
        .collect())
}

/// 并行计算多周期 SMA
///
/// 适用场景：同时计算 SMA(5), SMA(10), SMA(20) 等
///
/// # 参数
/// - `values`: 输入序列
/// - `periods`: 多个周期
///
/// # 返回
/// - `HazeResult<Vec<(period, sma_values)>>`
pub fn parallel_multi_period_sma(
    values: &[f64],
    periods: &[usize],
) -> HazeResult<Vec<(usize, Vec<f64>)>> {
    validate_not_empty(values, "values")?;
    for &period in periods {
        validate_period(period, values.len())?;
    }

    Ok(periods
        .par_iter()
        .map(|&period| {
            (
                period,
                sma(values, period).expect("parallel_multi_period_sma: validated input"),
            )
        })
        .collect())
}

/// 并行计算多周期 EMA
///
/// 适用场景：同时计算 EMA(12), EMA(26) 等
///
/// # 参数
/// - `values`: 输入序列
/// - `periods`: 多个周期
///
/// # 返回
/// - `HazeResult<Vec<(period, ema_values)>>`
pub fn parallel_multi_period_ema(
    values: &[f64],
    periods: &[usize],
) -> HazeResult<Vec<(usize, Vec<f64>)>> {
    validate_not_empty(values, "values")?;
    for &period in periods {
        validate_period(period, values.len())?;
    }

    Ok(periods
        .par_iter()
        .map(|&period| {
            (
                period,
                ema(values, period).expect("parallel_multi_period_ema: validated input"),
            )
        })
        .collect())
}

/// 批量指标计算器
///
/// 通用并行计算框架，支持任意指标函数
///
/// # 类型参数
/// - `T`: 输入数据类型
/// - `R`: 输出结果类型
/// - `F`: 计算函数类型
///
/// # 参数
/// - `inputs`: 输入数据集合
/// - `compute_fn`: 计算函数
///
/// # 返回
/// - 计算结果集合
pub fn parallel_compute<T, R, F>(inputs: &[T], compute_fn: F) -> Vec<R>
where
    T: Sync,
    R: Send,
    F: Fn(&T) -> R + Sync + Send,
{
    inputs.par_iter().map(compute_fn).collect()
}

/// 并行计算多组 RSI
///
/// # 参数
/// - `data_sets`: 多组输入数据 (symbol_id, close_prices, period)
///
/// # 返回
/// - `HazeResult<Vec<(symbol_id, rsi_values)>>`
pub fn parallel_rsi<'a>(
    data_sets: &[(&'a str, &[f64], usize)],
) -> HazeResult<Vec<(&'a str, Vec<f64>)>> {
    for (_, values, period) in data_sets {
        validate_not_empty(values, "values")?;
        let n = values.len();
        if *period == 0 {
            return Err(HazeError::InvalidPeriod {
                period: *period,
                data_len: n,
            });
        }
        if *period >= n {
            return Err(HazeError::InsufficientData {
                required: period + 1,
                actual: n,
            });
        }
    }

    Ok(data_sets
        .par_iter()
        .map(|(symbol, values, period)| (*symbol, compute_rsi(values, *period)))
        .collect())
}

/// RSI 计算（内部函数）
fn compute_rsi(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    debug_assert!(period > 0);
    debug_assert!(period < n);

    let mut result = init_result!(n);
    let mut gains = Vec::with_capacity(n - 1);
    let mut losses = Vec::with_capacity(n - 1);

    // 计算价格变化
    for i in 1..n {
        let change = values[i] - values[i - 1];
        if change > 0.0 {
            gains.push(change);
            losses.push(0.0);
        } else {
            gains.push(0.0);
            losses.push(-change);
        }
    }

    // 初始 SMA
    let mut avg_gain: f64 = gains[..period].iter().sum::<f64>() / period as f64;
    let mut avg_loss: f64 = losses[..period].iter().sum::<f64>() / period as f64;

    result[period] = if avg_loss < 1e-10 {
        100.0
    } else {
        100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    };

    // Wilder's smoothing
    for i in period..(n - 1) {
        avg_gain = (avg_gain * (period - 1) as f64 + gains[i]) / period as f64;
        avg_loss = (avg_loss * (period - 1) as f64 + losses[i]) / period as f64;

        result[i + 1] = if avg_loss < 1e-10 {
            100.0
        } else {
            100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
        };
    }

    result
}

/// 并行计算多组 ATR
///
/// # 参数
/// - `data_sets`: 多组输入数据 (symbol_id, high, low, close, period)
///
/// # 返回
/// - `HazeResult<Vec<(symbol_id, atr_values)>>`
pub fn parallel_atr<'a>(
    data_sets: &[(&'a str, &[f64], &[f64], &[f64], usize)],
) -> HazeResult<Vec<(&'a str, Vec<f64>)>> {
    for (_, high, low, close, period) in data_sets {
        validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
        let n = high.len();
        if *period == 0 {
            return Err(HazeError::InvalidPeriod {
                period: *period,
                data_len: n,
            });
        }
        if *period >= n {
            return Err(HazeError::InsufficientData {
                required: period + 1,
                actual: n,
            });
        }
    }

    Ok(data_sets
        .par_iter()
        .map(|(symbol, high, low, close, period)| (*symbol, compute_atr(high, low, close, *period)))
        .collect())
}

/// ATR 计算（内部函数）
fn compute_atr(high: &[f64], low: &[f64], close: &[f64], period: usize) -> Vec<f64> {
    let n = high.len();
    debug_assert_eq!(n, low.len());
    debug_assert_eq!(n, close.len());
    debug_assert!(period > 0);
    debug_assert!(period < n);

    let mut result = init_result!(n);
    let mut tr_values = Vec::with_capacity(n);

    // True Range 计算
    tr_values.push(high[0] - low[0]);
    for i in 1..n {
        let hl = high[i] - low[i];
        let hc = (high[i] - close[i - 1]).abs();
        let lc = (low[i] - close[i - 1]).abs();
        tr_values.push(hl.max(hc).max(lc));
    }

    // 初始 ATR (SMA)
    let first_atr: f64 = tr_values[..period].iter().sum::<f64>() / period as f64;
    result[period - 1] = first_atr;

    // RMA 更新
    for i in period..n {
        result[i] = (result[i - 1] * (period - 1) as f64 + tr_values[i]) / period as f64;
    }

    result
}

/// 配置 Rayon 线程池
///
/// # 参数
/// - `num_threads`: 线程数（0 表示使用默认值）
pub fn configure_thread_pool(num_threads: usize) -> Result<(), String> {
    if num_threads == 0 {
        return Ok(()); // 使用默认配置
    }

    rayon::ThreadPoolBuilder::new()
        .num_threads(num_threads)
        .build_global()
        .map_err(|e| format!("Failed to configure thread pool: {e}"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parallel_sma() {
        let values1 = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let values2 = vec![10.0, 20.0, 30.0, 40.0, 50.0];

        let data_sets: Vec<(&str, &[f64], usize)> =
            vec![("BTC", &values1, 3), ("ETH", &values2, 3)];

        let results = parallel_sma(&data_sets).unwrap();

        assert_eq!(results.len(), 2);
        // BTC: SMA(3) = (1+2+3)/3 = 2.0 at index 2
        assert_eq!(results[0].1[2], 2.0);
        // ETH: SMA(3) = (10+20+30)/3 = 20.0 at index 2
        assert_eq!(results[1].1[2], 20.0);
    }

    #[test]
    fn test_parallel_multi_period_sma() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0];
        let periods = vec![3, 5];

        let results = parallel_multi_period_sma(&values, &periods).unwrap();

        assert_eq!(results.len(), 2);
    }

    #[test]
    fn test_parallel_rsi() {
        let values1: Vec<f64> = (100..120).map(|x| x as f64).collect();
        let values2: Vec<f64> = (200..220).map(|x| x as f64).collect();

        let data_sets: Vec<(&str, &[f64], usize)> =
            vec![("BTC", &values1, 14), ("ETH", &values2, 14)];

        let results = parallel_rsi(&data_sets).unwrap();

        assert_eq!(results.len(), 2);
        // 持续上涨，RSI 应接近 100
        let btc_rsi = &results[0].1;
        let valid_rsi = btc_rsi.iter().find(|v| !v.is_nan()).unwrap();
        assert!(*valid_rsi > 90.0);
    }

    #[test]
    fn test_parallel_atr() {
        let high = vec![102.0, 103.0, 104.0, 105.0, 106.0];
        let low = vec![98.0, 99.0, 100.0, 101.0, 102.0];
        let close = vec![100.0, 101.0, 102.0, 103.0, 104.0];

        let data_sets: Vec<(&str, &[f64], &[f64], &[f64], usize)> =
            vec![("BTC", &high, &low, &close, 3)];

        let results = parallel_atr(&data_sets).unwrap();

        assert_eq!(results.len(), 1);
        // ATR 应该有有效值
        assert!(results[0].1[2].is_finite());
    }

    #[test]
    fn test_parallel_compute_generic() {
        let inputs: Vec<i32> = vec![1, 2, 3, 4, 5];

        let results: Vec<i32> = parallel_compute(&inputs, |x| x * 2);

        assert_eq!(results, vec![2, 4, 6, 8, 10]);
    }
}
