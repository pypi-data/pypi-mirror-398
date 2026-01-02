//! Moving Average Utilities Module
//!
//! # Overview
//! This module provides fundamental moving average calculations that serve as
//! building blocks for other technical indicators. All MA functions are optimized
//! for performance with incremental updates and warmup NaNs.
//!
//! # Available Functions
//! - [`sma`] - Simple Moving Average (arithmetic mean)
//! - [`ema`] - Exponential Moving Average (weighted recent values)
//! - [`rma`] - Wilder's Moving Average / Running Moving Average
//! - [`wma`] - Weighted Moving Average (linear weights)
//! - [`dema`] - Double Exponential Moving Average (reduced lag)
//! - [`tema`] - Triple Exponential Moving Average (further lag reduction)
//! - [`kama`] - Kaufman Adaptive Moving Average (volatility-adjusted)
//! - `zlema` - Zero-Lag Exponential Moving Average (lag compensation)
//! - [`hma`] - Hull Moving Average (smoothness with reduced lag)
//! - `vwma` - Volume Weighted Moving Average
//! - [`vwap`] - Volume Weighted Average Price
//!
//! # Usage Patterns
//! These functions are typically used:
//! - Directly for trend identification (crossover signals)
//! - As components in composite indicators (MACD uses EMA, ATR uses RMA)
//! - For smoothing noisy price data
//!
//! # Examples
//! ```rust
//! use haze_library::utils::ma::{sma, ema, rma};
//!
//! let prices = vec![100.0, 101.0, 102.0, 103.0, 104.0, 105.0];
//!
//! // Simple Moving Average (3-period)
//! let sma_values = sma(&prices, 3);
//!
//! // Exponential Moving Average (more weight on recent prices)
//! let ema_values = ema(&prices, 3);
//!
//! // Wilder's RMA (used in ATR, RSI calculations)
//! let rma_values = rma(&prices, 3);
//! ```
//!
//! # Performance Characteristics
//! - SMA: O(n) with incremental sum updates
//! - EMA/RMA: O(n) single pass with exponential decay
//! - WMA: O(n * period) due to weighted summation
//! - DEMA/TEMA: O(n) with chained EMA calculations
//!
//! # NaN Handling
//! - Inputs must be finite; NaN/Inf are rejected by validation
//! - Warmup periods (first period-1 values) are NaN by design
//! - Output maintains same length as input array
//!
//! # Cross-References
//! - [`crate::indicators::momentum`] - MACD uses EMA
//! - [`crate::indicators::volatility`] - ATR uses RMA
//! - [`crate::indicators::trend`] - SuperTrend uses ATR (via RMA)

#![allow(dead_code)]

use crate::errors::validation::{
    validate_not_empty, validate_not_empty_allow_nan, validate_period, validate_same_length,
};
use crate::errors::{HazeError, HazeResult};
use crate::init_result;
use crate::utils::math::{is_zero, kahan_sum};

/// SMA - Simple Moving Average（简单移动平均）
///
/// 算法：sum(values[i-period+1 .. i+1]) / period
///
/// 使用 Kahan 补偿求和的增量更新并定期重新计算以防止浮点误差累积。
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - 与输入等长的向量，前 period-1 个值为 NaN
///
/// # 错误
/// - 如果输入为空，返回 `HazeError::EmptyInput`
/// - 如果 period 为 0 或超过数据长度，返回 `HazeError::InvalidPeriod`
fn sma_impl(values: &[f64], period: usize) -> Vec<f64> {
    /// 重新计算间隔：每 1000 次迭代重新计算一次以重置累积误差
    const RECALC_INTERVAL: usize = 1000;

    let n = values.len();
    let mut result = init_result!(n);
    let mut sum = 0.0;
    let mut compensation = 0.0; // Kahan 补偿项
    let mut count = 0usize;
    let mut steps_since_recalc = 0usize;

    for i in 0..n {
        let v = values[i];
        if v.is_nan() {
            sum = 0.0;
            compensation = 0.0;
            count = 0;
            steps_since_recalc = 0;
            continue;
        }

        // 使用 Kahan 求和添加新值
        let y = v - compensation;
        let t = sum + y;
        compensation = (t - sum) - y;
        sum = t;
        count += 1;

        if count > period {
            // 使用 Kahan 求和减去旧值
            let old_val = values[i - period];
            let y = -old_val - compensation;
            let t = sum + y;
            compensation = (t - sum) - y;
            sum = t;
            count = period;
            steps_since_recalc += 1;

            // 定期完整重新计算以消除累积浮点误差
            if steps_since_recalc >= RECALC_INTERVAL {
                sum = kahan_sum(&values[i + 1 - period..=i]);
                compensation = 0.0;
                steps_since_recalc = 0;
            }
        }

        if count == period {
            result[i] = sum / period as f64;
        }
    }

    result
}

pub fn sma(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;
    Ok(sma_impl(values, period))
}

pub(crate) fn sma_allow_nan(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty_allow_nan(values, "values")?;
    validate_period(period, values.len())?;
    Ok(sma_impl(values, period))
}

/// EMA - Exponential Moving Average（指数移动平均）
///
/// 算法：
/// - alpha = 2 / (period + 1)
/// - EMA`[0]` = SMA(period)  // 初始值使用 SMA
/// - EMA`[i]` = alpha * value`[i]` + (1 - alpha) * EMA`[i-1]`
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - 与输入等长的向量，前 period-1 个值为 NaN
///
/// # 错误
/// - 如果输入为空，返回 `HazeError::EmptyInput`
/// - 如果 period 为 0 或超过数据长度，返回 `HazeError::InvalidPeriod`
fn ema_impl(values: &[f64], period: usize, alpha: f64) -> Vec<f64> {
    let n = values.len();
    let mut result = init_result!(n);
    let mut warmup_sum = 0.0;
    let mut warmup_comp = 0.0;
    let mut warmup_count = 0usize;
    let mut prev = f64::NAN;

    for i in 0..n {
        let v = values[i];
        if v.is_nan() {
            warmup_sum = 0.0;
            warmup_comp = 0.0;
            warmup_count = 0;
            prev = f64::NAN;
            continue;
        }

        if warmup_count < period {
            warmup_count += 1;
            let y = v - warmup_comp;
            let t = warmup_sum + y;
            warmup_comp = (t - warmup_sum) - y;
            warmup_sum = t;

            if warmup_count == period {
                prev = warmup_sum / period as f64;
                result[i] = prev;
            }
            continue;
        }

        prev = alpha * v + (1.0 - alpha) * prev;
        result[i] = prev;
    }

    result
}

pub fn ema(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    let alpha = 2.0 / (period as f64 + 1.0);
    Ok(ema_impl(values, period, alpha))
}

pub(crate) fn ema_allow_nan(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty_allow_nan(values, "values")?;
    validate_period(period, values.len())?;
    let alpha = 2.0 / (period as f64 + 1.0);
    Ok(ema_impl(values, period, alpha))
}

/// RMA - Wilder's Moving Average（威尔德移动平均）
///
/// 算法：RMA`[i]` = (RMA`[i-1]` * (period - 1) + value`[i]`) / period
/// 等价于 EMA with alpha = 1 / period
///
/// 用于：ATR、RSI 等指标
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - 与输入等长的向量，前 period-1 个值为 NaN
///
/// # 错误
/// - 如果输入为空，返回 `HazeError::EmptyInput`
/// - 如果 period 为 0 或超过数据长度，返回 `HazeError::InvalidPeriod`
pub fn rma(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    let alpha = 1.0 / period as f64;
    Ok(ema_impl(values, period, alpha))
}

pub(crate) fn rma_allow_nan(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty_allow_nan(values, "values")?;
    validate_period(period, values.len())?;
    let alpha = 1.0 / period as f64;
    Ok(ema_impl(values, period, alpha))
}

/// WMA - Weighted Moving Average（加权移动平均）
///
/// 使用 O(n) 增量算法实现。
///
/// 算法：WMA = sum(value`[i]` * weight`[i]`) / sum(weight)
/// 其中 weight`[i]` = i + 1（线性递增权重）
///
/// # 增量更新原理
/// 当窗口从 [v0, v1, ..., v_{n-1}] 滑动到 [v1, v2, ..., v_n] 时：
/// - 所有现有值的权重都减 1（等于减去 simple_sum）
/// - 旧值 v0（权重 1）被移除
/// - 新值 v_n（权重 period）被添加
///
/// 公式：new_weighted_sum = old_weighted_sum - simple_sum + period * new_value
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - 与输入等长的向量，前 period-1 个值为 NaN
///
/// # 性能
/// - 时间复杂度: O(n)
/// - 空间复杂度: O(n)
///
/// # 错误
/// - 如果输入为空，返回 `HazeError::EmptyInput`
/// - 如果 period 为 0 或超过数据长度，返回 `HazeError::InvalidPeriod`
fn wma_impl(values: &[f64], period: usize) -> Vec<f64> {
    const RECALC_INTERVAL: usize = 1000;

    let n = values.len();

    let period_f = period as f64;
    let weight_sum = period_f * (period_f + 1.0) / 2.0;
    let mut result = vec![f64::NAN; n];

    // Kahan 补偿求和：提升增量更新的数值稳定性
    #[inline]
    fn kahan_add(sum: &mut f64, compensation: &mut f64, value: f64) {
        let y = value - *compensation;
        let t = *sum + y;
        *compensation = (t - *sum) - y;
        *sum = t;
    }

    let mut simple_sum = 0.0;
    let mut simple_comp = 0.0;
    let mut weighted_sum = 0.0;
    let mut weighted_comp = 0.0;
    let mut count = 0usize;
    let mut steps_since_recalc = 0usize;

    // 单次遍历：累积到 period 后使用 O(n) 增量更新
    for i in 0..n {
        let v = values[i];

        if v.is_nan() {
            simple_sum = 0.0;
            simple_comp = 0.0;
            weighted_sum = 0.0;
            weighted_comp = 0.0;
            count = 0;
            steps_since_recalc = 0;
            continue;
        }

        if count < period {
            count += 1;
            kahan_add(&mut simple_sum, &mut simple_comp, v);
            kahan_add(&mut weighted_sum, &mut weighted_comp, (count as f64) * v);

            if count == period {
                result[i] = weighted_sum / weight_sum;
            }
            continue;
        }

        // count == period: 增量更新当前窗口
        if steps_since_recalc >= RECALC_INTERVAL {
            // 定期重新计算以防止浮点误差累积（同时保证遇到历史 NaN 后可恢复）
            simple_sum = 0.0;
            simple_comp = 0.0;
            weighted_sum = 0.0;
            weighted_comp = 0.0;

            let window = &values[i + 1 - period..=i];
            for (j, &val) in window.iter().enumerate() {
                kahan_add(&mut simple_sum, &mut simple_comp, val);
                kahan_add(
                    &mut weighted_sum,
                    &mut weighted_comp,
                    (j as f64 + 1.0) * val,
                );
            }
            steps_since_recalc = 0;
        } else {
            let prev_simple_sum = simple_sum;

            // new_weighted_sum = old_weighted_sum - simple_sum + period * new_value
            kahan_add(&mut weighted_sum, &mut weighted_comp, -prev_simple_sum);
            kahan_add(&mut weighted_sum, &mut weighted_comp, period_f * v);

            // new_simple_sum = old_simple_sum - old_value + new_value
            let old = values[i - period];
            kahan_add(&mut simple_sum, &mut simple_comp, -old);
            kahan_add(&mut simple_sum, &mut simple_comp, v);
        }

        result[i] = weighted_sum / weight_sum;
        steps_since_recalc += 1;
    }

    result
}

pub fn wma(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;
    Ok(wma_impl(values, period))
}

pub(crate) fn wma_allow_nan(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty_allow_nan(values, "values")?;
    validate_period(period, values.len())?;
    Ok(wma_impl(values, period))
}

/// HMA - Hull Moving Average（赫尔移动平均，低延迟）
///
/// 算法：
/// - half_period = period / 2
/// - sqrt_period = sqrt(period)
/// - HMA = WMA(2 * WMA(half_period) - WMA(period), sqrt_period)
///
/// 特点：响应速度快，延迟低
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - 与输入等长的向量
///
/// # 错误
/// - 如果输入为空，返回 `HazeError::EmptyInput`
/// - 如果 period 为 0 或超过数据长度，返回 `HazeError::InvalidPeriod`
pub fn hma(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    let half_period = period / 2;
    let sqrt_period = (period as f64).sqrt() as usize;

    let wma_half = wma_allow_nan(values, half_period)?;
    let wma_full = wma_allow_nan(values, period)?;

    // 2 * WMA(half) - WMA(full)
    let diff: Vec<f64> = wma_half
        .iter()
        .zip(&wma_full)
        .map(|(&a, &b)| {
            if a.is_nan() || b.is_nan() {
                f64::NAN
            } else {
                2.0 * a - b
            }
        })
        .collect();

    let result = wma_allow_nan(&diff, sqrt_period)?;
    if result.iter().all(|v| v.is_nan()) {
        Ok(diff)
    } else {
        Ok(result)
    }
}

/// DEMA - Double Exponential Moving Average（双重指数移动平均）
///
/// 算法：DEMA = 2 * EMA(period) - EMA(EMA(period))
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - 与输入等长的向量
///
/// # 错误
/// - 如果输入为空，返回 `HazeError::EmptyInput`
/// - 如果 period 为 0 或超过数据长度，返回 `HazeError::InvalidPeriod`
pub fn dema(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    let ema1 = ema_allow_nan(values, period)?;
    let ema2 = ema_allow_nan(&ema1, period)?;

    Ok(ema1
        .iter()
        .zip(&ema2)
        .map(|(&e1, &e2)| {
            if e1.is_nan() || e2.is_nan() {
                f64::NAN
            } else {
                2.0 * e1 - e2
            }
        })
        .collect())
}

/// TEMA - Triple Exponential Moving Average（三重指数移动平均）
///
/// 算法：TEMA = 3*EMA - 3*EMA(EMA) + EMA(EMA(EMA))
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - 与输入等长的向量
///
/// # 错误
/// - 如果输入为空，返回 `HazeError::EmptyInput`
/// - 如果 period 为 0 或超过数据长度，返回 `HazeError::InvalidPeriod`
pub fn tema(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    let ema1 = ema_allow_nan(values, period)?;
    let ema2 = ema_allow_nan(&ema1, period)?;
    let ema3 = ema_allow_nan(&ema2, period)?;

    if !ema3.iter().any(|v| !v.is_nan()) {
        return dema(values, period);
    }

    Ok(ema1
        .iter()
        .zip(&ema2)
        .zip(&ema3)
        .map(|((&e1, &e2), &e3)| {
            if e1.is_nan() || e2.is_nan() || e3.is_nan() {
                f64::NAN
            } else {
                3.0 * e1 - 3.0 * e2 + e3
            }
        })
        .collect())
}

/// VWAP - Volume Weighted Average Price（成交量加权平均价）
///
/// 算法：VWAP = sum(typical_price * volume) / sum(volume)
///
/// 使用 Kahan 补偿求和的增量更新并定期重新计算以防止浮点误差累积。
///
/// # 参数
/// - `typical_prices`: 典型价格序列 (H+L+C)/3
/// - `volumes`: 成交量序列
/// - `period`: 周期（0 表示累积 VWAP）
///
/// # 返回
/// - 与输入等长的向量
///
/// # 错误
/// - 如果输入为空，返回 `HazeError::EmptyInput`
/// - 如果两个输入数组长度不匹配，返回 `HazeError::LengthMismatch`
/// - 如果 period 超过数据长度，返回 `HazeError::InvalidPeriod`
pub fn vwap(typical_prices: &[f64], volumes: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    /// 重新计算间隔：每 1000 次迭代重新计算一次以重置累积误差
    const RECALC_INTERVAL: usize = 1000;

    // Fail-Fast 验证
    validate_not_empty(typical_prices, "typical_prices")?;
    validate_same_length(typical_prices, "typical_prices", volumes, "volumes")?;

    let n = typical_prices.len();
    let mut result = init_result!(n);

    if period == 0 {
        // 累积 VWAP（使用 Kahan 求和算法减少浮点误差）
        let mut cum_pv = 0.0;
        let mut cum_v = 0.0;
        let mut pv_comp = 0.0; // Kahan 补偿项
        let mut v_comp = 0.0; // Kahan 补偿项
        for i in 0..n {
            // Kahan 求和 for pv
            let pv = typical_prices[i] * volumes[i];
            let pv_y = pv - pv_comp;
            let pv_t = cum_pv + pv_y;
            pv_comp = (pv_t - cum_pv) - pv_y;
            cum_pv = pv_t;

            // Kahan 求和 for v
            let v = volumes[i];
            let v_y = v - v_comp;
            let v_t = cum_v + v_y;
            v_comp = (v_t - cum_v) - v_y;
            cum_v = v_t;

            result[i] = if is_zero(cum_v) {
                f64::NAN
            } else {
                cum_pv / cum_v
            };
        }
        return Ok(result);
    }

    // 验证滚动 VWAP 的周期
    if period > n {
        validate_period(period, n)?;
    }

    // 滚动 VWAP（使用 Kahan 补偿的增量更新）
    // 初始窗口使用 Kahan 求和
    let mut pv_sum = 0.0;
    let mut v_sum = 0.0;
    let mut pv_comp = 0.0;
    let mut v_comp = 0.0;

    for i in 0..period {
        let pv = typical_prices[i] * volumes[i];
        let y = pv - pv_comp;
        let t = pv_sum + y;
        pv_comp = (t - pv_sum) - y;
        pv_sum = t;

        let y = volumes[i] - v_comp;
        let t = v_sum + y;
        v_comp = (t - v_sum) - y;
        v_sum = t;
    }

    result[period - 1] = if is_zero(v_sum) {
        f64::NAN
    } else {
        pv_sum / v_sum
    };

    for i in period..n {
        // 定期完整重新计算以消除累积浮点误差
        if (i - period + 1) % RECALC_INTERVAL == 0 {
            pv_sum = 0.0;
            v_sum = 0.0;
            pv_comp = 0.0;
            v_comp = 0.0;

            for j in (i + 1 - period)..=i {
                let pv = typical_prices[j] * volumes[j];
                let y = pv - pv_comp;
                let t = pv_sum + y;
                pv_comp = (t - pv_sum) - y;
                pv_sum = t;

                let y = volumes[j] - v_comp;
                let t = v_sum + y;
                v_comp = (t - v_sum) - y;
                v_sum = t;
            }
        } else {
            // 使用 Kahan 补偿进行增量更新
            // 添加新的 pv
            let new_pv = typical_prices[i] * volumes[i];
            let y = new_pv - pv_comp;
            let t = pv_sum + y;
            pv_comp = (t - pv_sum) - y;
            pv_sum = t;

            // 减去旧的 pv
            let old_pv = typical_prices[i - period] * volumes[i - period];
            let y = -old_pv - pv_comp;
            let t = pv_sum + y;
            pv_comp = (t - pv_sum) - y;
            pv_sum = t;

            // 添加新的 volume
            let y = volumes[i] - v_comp;
            let t = v_sum + y;
            v_comp = (t - v_sum) - y;
            v_sum = t;

            // 减去旧的 volume
            let y = -volumes[i - period] - v_comp;
            let t = v_sum + y;
            v_comp = (t - v_sum) - y;
            v_sum = t;
        }

        result[i] = if is_zero(v_sum) {
            f64::NAN
        } else {
            pv_sum / v_sum
        };
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sma() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = sma(&values, 3).unwrap();
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        assert_eq!(result[2], 2.0); // (1+2+3)/3
        assert_eq!(result[3], 3.0); // (2+3+4)/3
        assert_eq!(result[4], 4.0); // (3+4+5)/3
    }

    #[test]
    fn test_ema() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = ema(&values, 3).unwrap();
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        assert_eq!(result[2], 2.0); // 初始值 = SMA
                                    // EMA[3] = 0.5 * 4 + 0.5 * 2 = 3.0
        assert!((result[3] - 3.0).abs() < 1e-10);
    }

    #[test]
    fn test_rma() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = rma(&values, 3).unwrap();
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        assert_eq!(result[2], 2.0); // 初始值 = SMA
    }

    #[test]
    fn test_wma_nan_reset() {
        let values = vec![1.0, 2.0, f64::NAN, 4.0, 5.0, 6.0];
        let result = wma_allow_nan(&values, 3).unwrap();

        // NaN 会重置窗口，直到凑齐 period 个有效值才会输出
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        assert!(result[2].is_nan());
        assert!(result[3].is_nan());
        assert!(result[4].is_nan());

        // 窗口 [4,5,6]，权重 [1,2,3] => (4 + 10 + 18) / 6 = 32/6
        assert!((result[5] - 32.0 / 6.0).abs() < 1e-10);
    }

    #[test]
    fn test_vwap() {
        let prices = vec![100.0, 101.0, 102.0];
        let volumes = vec![1000.0, 1100.0, 1200.0];
        let result = vwap(&prices, &volumes, 0).unwrap(); // 累积 VWAP
        assert_eq!(result[0], 100.0);
        // (100*1000 + 101*1100) / (1000+1100) = 211100 / 2100 ≈ 100.52
        assert!((result[1] - 100.52380952380952).abs() < 1e-10);
    }

    #[test]
    fn test_vwap_rolling() {
        let prices = vec![100.0, 101.0, 102.0, 103.0];
        let volumes = vec![10.0, 10.0, 10.0, 10.0];
        let result = vwap(&prices, &volumes, 2).unwrap();
        assert!(result[0].is_nan());
        assert!((result[1] - 100.5).abs() < 1e-10);
        assert!((result[2] - 101.5).abs() < 1e-10);
        assert!((result[3] - 102.5).abs() < 1e-10);
    }

    #[test]
    fn test_vwap_zero_volume() {
        let prices = vec![100.0, 101.0];
        let volumes = vec![0.0, 0.0];
        let result = vwap(&prices, &volumes, 0).unwrap();
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
    }
}

/// ZLMA (Zero Lag Moving Average) 零延迟移动平均
///
/// 尝试消除 EMA 的延迟，更快响应价格变化
///
/// - `values`: 输入序列
/// - `period`: 周期
///
/// 返回：ZLMA 序列
///
/// # 算法
/// 1. Lag = (period - 1) / 2
/// 2. EMA_Data = 2 * values - values`[lag_ago]`
/// 3. ZLMA = EMA(EMA_Data, period)
///
/// # 错误
/// - 如果输入为空，返回 `HazeError::EmptyInput`
/// - 如果 period 为 0 或超过数据长度，返回 `HazeError::InvalidPeriod`
pub fn zlma(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    let n = values.len();
    let lag = (period - 1) / 2;
    let mut ema_data = init_result!(n);

    for i in lag..n {
        ema_data[i] = 2.0 * values[i] - values[i - lag];
    }

    ema_allow_nan(&ema_data, period)
}

/// T3 (Tillson T3) 移动平均
///
/// 6 重 EMA 平滑，减少噪音同时保持快速响应
///
/// - `values`: 输入序列
/// - `period`: 周期
/// - `v_factor`: 平滑因子（通常 0.7）
///
/// 返回：T3 序列
///
/// # 算法
/// 使用 6 层 EMA 和特殊系数
///
/// # 错误
/// - 如果输入为空，返回 `HazeError::EmptyInput`
/// - 如果 period 为 0 或超过数据长度，返回 `HazeError::InvalidPeriod`
pub fn t3(values: &[f64], period: usize, v_factor: f64) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    let n = values.len();

    // 计算系数
    let c1 = -v_factor * v_factor * v_factor;
    let c2 = 3.0 * v_factor * v_factor + 3.0 * v_factor * v_factor * v_factor;
    let c3 = -6.0 * v_factor * v_factor - 3.0 * v_factor - 3.0 * v_factor * v_factor * v_factor;
    let c4 = 1.0 + 3.0 * v_factor + v_factor * v_factor * v_factor + 3.0 * v_factor * v_factor;

    // 6 层 EMA
    let e1 = ema_allow_nan(values, period)?;
    let e2 = ema_allow_nan(&e1, period)?;
    let e3 = ema_allow_nan(&e2, period)?;
    let e4 = ema_allow_nan(&e3, period)?;
    let e5 = ema_allow_nan(&e4, period)?;
    let e6 = ema_allow_nan(&e5, period)?;

    // 加权组合
    let mut t3_values = init_result!(n);
    for i in 0..n {
        if !e3[i].is_nan() && !e4[i].is_nan() && !e5[i].is_nan() && !e6[i].is_nan() {
            t3_values[i] = c1 * e6[i] + c2 * e5[i] + c3 * e4[i] + c4 * e3[i];
        }
    }

    if t3_values.iter().all(|v| v.is_nan()) {
        ema_allow_nan(values, period)
    } else {
        Ok(t3_values)
    }
}

/// KAMA (Kaufman's Adaptive Moving Average) 考夫曼自适应移动平均
///
/// 根据市场波动性自适应调整平滑度
///
/// - `values`: 输入序列
/// - `period`: 效率比率周期（默认 10）
/// - `fast_period`: 快速 EMA 周期（默认 2）
/// - `slow_period`: 慢速 EMA 周期（默认 30）
///
/// 返回：KAMA 序列
///
/// # 算法
/// 1. Change = |Price`[i]` - Price[i-period]|
/// 2. Volatility = Sum(|Price`[i]` - Price`[i-1]`|, period)
/// 3. ER (Efficiency Ratio) = Change / Volatility
/// 4. SC (Smoothing Constant) = [ER * (Fast_SC - Slow_SC) + Slow_SC]^2
/// 5. KAMA`[i]` = KAMA`[i-1]` + SC * (Price`[i]` - KAMA`[i-1]`)
///
/// # 错误
/// - 如果输入为空，返回 `HazeError::EmptyInput`
/// - 如果 period 为 0 或超过数据长度，返回 `HazeError::InvalidPeriod`
pub fn kama(
    values: &[f64],
    period: usize,
    fast_period: usize,
    slow_period: usize,
) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    let n = values.len();

    // 计算 EMA 平滑常数
    let fast_sc = 2.0 / (fast_period + 1) as f64;
    let slow_sc = 2.0 / (slow_period + 1) as f64;

    let mut kama_values = init_result!(n);
    kama_values[period - 1] = values[period - 1]; // 初始值

    for i in period..n {
        // 1. 计算价格变化
        let change = (values[i] - values[i - period]).abs();

        // 2. 计算波动性（价格变动的绝对值和）
        let mut volatility = 0.0;
        for j in 0..period {
            let idx = i - period + 1 + j;
            volatility += (values[idx] - values[idx - 1]).abs();
        }

        // 3. 效率比率
        let er = if volatility > 0.0 {
            change / volatility
        } else {
            0.0
        };

        // 4. 平滑常数
        let sc = (er * (fast_sc - slow_sc) + slow_sc).powi(2);

        // 5. KAMA
        kama_values[i] = kama_values[i - 1] + sc * (values[i] - kama_values[i - 1]);
    }

    Ok(kama_values)
}

/// FRAMA (Fractal Adaptive Moving Average) 分形自适应移动平均
///
/// 基于分形维度自适应调整
///
/// - `values`: 输入序列
/// - `period`: 周期（必须是偶数，默认 16）
///
/// 返回：FRAMA 序列
///
/// # 算法
/// 使用分形维度计算自适应 alpha
///
/// # 错误
/// - 如果输入为空，返回 `HazeError::EmptyInput`
/// - 如果 period < 2 或非偶数或超过数据长度，返回 `HazeError::InvalidPeriod`
pub fn frama(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;

    let n = values.len();
    if period < 2 || period % 2 != 0 || period > n {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }

    let half = period / 2;
    let mut frama_values = init_result!(n);

    // 初始值
    frama_values[period - 1] = values[period - 1];

    for i in period..n {
        // 计算前半周期和后半周期的最高最低价
        let mut n1_high = f64::NEG_INFINITY;
        let mut n1_low = f64::INFINITY;
        let mut n2_high = f64::NEG_INFINITY;
        let mut n2_low = f64::INFINITY;

        for j in 0..half {
            let idx1 = i - period + j;
            let idx2 = i - half + j;

            n1_high = n1_high.max(values[idx1]);
            n1_low = n1_low.min(values[idx1]);
            n2_high = n2_high.max(values[idx2]);
            n2_low = n2_low.min(values[idx2]);
        }

        let n1 = (n1_high - n1_low) / (half as f64);
        let n2 = (n2_high - n2_low) / (half as f64);

        let mut n3_high = f64::NEG_INFINITY;
        let mut n3_low = f64::INFINITY;
        for j in 0..period {
            let idx = i - period + j;
            n3_high = n3_high.max(values[idx]);
            n3_low = n3_low.min(values[idx]);
        }
        let n3 = (n3_high - n3_low) / (period as f64);

        // 分形维度
        let dimen = if n1 + n2 > 0.0 && n3 > 0.0 {
            ((n1 + n2).ln() - n3.ln()) / 2_f64.ln()
        } else {
            1.0
        };

        // Alpha
        let alpha = (-4.6 * (dimen - 1.0)).exp();
        let alpha_clamped = alpha.clamp(0.01, 1.0);

        // FRAMA
        frama_values[i] = alpha_clamped * values[i] + (1.0 - alpha_clamped) * frama_values[i - 1];
    }

    Ok(frama_values)
}

#[cfg(test)]
mod advanced_ma_tests {
    use super::*;

    #[test]
    fn test_zlma_basic() {
        let values: Vec<f64> = (100..120).map(|x| x as f64).collect();

        let zlma_values = zlma(&values, 10).unwrap();

        // 上升趋势中，ZLMA 应跟随价格上升
        let valid_idx = zlma_values.iter().position(|v| !v.is_nan()).unwrap();
        assert!(zlma_values[valid_idx] > 100.0);
    }

    #[test]
    fn test_t3_basic() {
        let values: Vec<f64> = (100..130).map(|x| x as f64).collect();

        let t3_values = t3(&values, 5, 0.7).unwrap();

        // T3 应该平滑趋势
        let valid_idx = t3_values.iter().position(|v| !v.is_nan()).unwrap();
        assert!(t3_values[valid_idx] > 100.0);
    }

    #[test]
    fn test_kama_basic() {
        let values: Vec<f64> = (100..150).map(|x| x as f64).collect();

        let kama_values = kama(&values, 10, 2, 30).unwrap();

        // KAMA 应该跟随趋势
        let valid_idx = kama_values.iter().position(|v| !v.is_nan()).unwrap();
        assert!(kama_values[valid_idx] > 100.0);
        assert!(kama_values[valid_idx] < 150.0);
    }

    #[test]
    fn test_frama_basic() {
        let values: Vec<f64> = (100..132).map(|x| x as f64).collect();

        let frama_values = frama(&values, 16).unwrap();

        // FRAMA 应该有效
        let valid_idx = frama_values.iter().position(|v| !v.is_nan()).unwrap();
        assert!(frama_values[valid_idx] > 100.0);
    }
}

// ==================== 浮点误差校准测试 ====================

#[cfg(test)]
mod floating_point_error_tests {
    use super::*;

    /// 测试 SMA 在大数据集上的数值精度
    #[test]
    fn test_sma_large_dataset_precision() {
        const N: usize = 100_000;
        const PERIOD: usize = 20;

        // 生成测试数据
        let values: Vec<f64> = (0..N)
            .map(|i| 1000.0 + (i as f64) * 0.001 + 0.0001 * ((i * 7) % 11) as f64)
            .collect();

        let result = sma(&values, PERIOD).unwrap();

        // 在多个点验证精度
        let test_indices = [PERIOD - 1, 1000, 2000, 50_000, N - 1];

        for &i in &test_indices {
            if (PERIOD - 1..N).contains(&i) {
                let expected: f64 = values[i + 1 - PERIOD..=i].iter().sum::<f64>() / PERIOD as f64;
                let actual = result[i];

                let relative_error = (actual - expected).abs() / expected.abs();
                assert!(
                    relative_error < 1e-10,
                    "SMA 在索引 {i} 处精度不足: expected={expected}, actual={actual}, relative_error={relative_error}",
                );
            }
        }
    }

    /// 测试滚动 VWAP 在大数据集上的数值精度
    #[test]
    fn test_vwap_rolling_large_dataset_precision() {
        const N: usize = 100_000;
        const PERIOD: usize = 20;

        // 生成测试数据
        let prices: Vec<f64> = (0..N).map(|i| 100.0 + (i as f64) * 0.001).collect();
        let volumes: Vec<f64> = (0..N).map(|i| 1000.0 + ((i * 3) % 100) as f64).collect();

        let result = vwap(&prices, &volumes, PERIOD).unwrap();

        // 在多个点验证精度
        let test_indices = [PERIOD - 1, 1000, 2000, 50_000, N - 1];

        for &i in &test_indices {
            if (PERIOD - 1..N).contains(&i) {
                let pv_sum: f64 = prices[i + 1 - PERIOD..=i]
                    .iter()
                    .zip(&volumes[i + 1 - PERIOD..=i])
                    .map(|(&p, &v)| p * v)
                    .sum();
                let v_sum: f64 = volumes[i + 1 - PERIOD..=i].iter().sum();
                let expected = pv_sum / v_sum;
                let actual = result[i];

                let relative_error = (actual - expected).abs() / expected.abs();
                assert!(
                    relative_error < 1e-10,
                    "VWAP 在索引 {i} 处精度不足: expected={expected}, actual={actual}, relative_error={relative_error}",
                );
            }
        }
    }

    /// 测试累积 VWAP（使用 Kahan 求和）的精度
    #[test]
    fn test_vwap_cumulative_precision() {
        const N: usize = 100_000;

        // 使用容易产生浮点误差的小数值
        let prices: Vec<f64> = (0..N).map(|i| 0.001 + (i as f64) * 0.0001).collect();
        let volumes: Vec<f64> = (0..N)
            .map(|i| 0.1 + ((i * 3) % 100) as f64 * 0.01)
            .collect();

        let result = vwap(&prices, &volumes, 0).unwrap(); // 累积模式

        // 验证最终结果精度
        let pv_sum: f64 = prices.iter().zip(&volumes).map(|(&p, &v)| p * v).sum();
        let v_sum: f64 = volumes.iter().sum();
        let expected = pv_sum / v_sum;
        let actual = result[N - 1];

        let relative_error = (actual - expected).abs() / expected.abs();
        // Kahan 求和应保持更高精度
        assert!(
            relative_error < 1e-12,
            "累积 VWAP 精度不足: expected={expected}, actual={actual}, relative_error={relative_error}",
        );
    }

    /// 测试 SMA 对 NaN 输入的 Fail-Fast 行为
    #[test]
    fn test_sma_nan_recovery_precision() {
        const PERIOD: usize = 10;

        // 构造带有 NaN 中断的数据
        let mut values: Vec<f64> = (0..1000).map(|i| i as f64 + 0.5).collect();
        values[500] = f64::NAN; // 在中间插入 NaN

        assert!(matches!(
            sma(&values, PERIOD),
            Err(HazeError::InvalidValue { .. })
        ));
    }
}
