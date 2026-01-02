//! Statistical Utilities Module
//!
//! # Overview
//! This module provides fundamental statistical functions for technical analysis,
//! including rolling window calculations, regression analysis, and correlation
//! metrics. These functions serve as building blocks for indicators and risk
//! assessment calculations.
//!
//! # Available Functions
//!
//! ## Basic Statistics
//! - [`stdev`] - Sample standard deviation (n-1 denominator)
//! - [`stdev_population`] - Population standard deviation (n denominator)
//! - [`rolling_max`] - Rolling window maximum (O(n) using monotonic deque)
//! - [`rolling_min`] - Rolling window minimum (O(n) using monotonic deque)
//! - [`rolling_sum`] - Rolling window sum (O(n) incremental)
//! - [`rolling_percentile`] - Rolling percentile/median calculation
//! - [`var`] - Rolling variance
//!
//! ## Momentum Statistics
//! - [`roc`] - Rate of Change (percentage price change)
//! - [`momentum`] - Momentum (absolute price change)
//!
//! ## Regression Analysis
//! - [`linear_regression`] - Linear regression (slope, intercept, R-squared)
//! - [`linearreg`] - Linear regression endpoint value (TA-Lib compatible)
//! - [`linearreg_slope`] - Linear regression slope
//! - [`linearreg_angle`] - Linear regression angle in degrees
//! - [`linearreg_intercept`] - Linear regression intercept
//! - [`standard_error`] - Regression standard error
//! - [`tsf`] - Time Series Forecast (next point prediction)
//!
//! ## Correlation Analysis
//! - [`correlation`] / [`correl`] - Pearson correlation coefficient
//! - [`covariance`] - Rolling covariance between two series
//! - [`beta`] - Beta coefficient (systematic risk measure)
//! - [`zscore`] - Z-Score standardization
//!
//! # Examples
//! ```rust
//! use haze_library::utils::stats::{stdev, rolling_max, linear_regression};
//!
//! let values = vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0];
//!
//! // Calculate 3-period rolling standard deviation
//! let std_values = stdev(&values, 3);
//!
//! // Calculate 3-period rolling maximum
//! let max_values = rolling_max(&values, 3);
//!
//! // Linear regression over 5-period windows
//! let (slope, intercept, r_squared) = linear_regression(&values, 5);
//! ```
//!
//! # Performance Characteristics
//! - Rolling max/min: O(n) amortized using monotonic deque algorithm
//! - Rolling sum: O(n) with incremental updates
//! - Regression: O(n) rolling (periodic recompute to limit drift)
//! - Correlation/Covariance/Beta/Z-Score/Var: O(n) rolling (periodic recompute)
//! - Percentile/precise variants may be O(n * period)
//!
//! # NaN Handling
//! - All functions return NaN for warmup periods (first period-1 values)
//! - NaN values in input propagate appropriately through calculations
//! - Rolling max/min skip NaN values within windows
//!
//! # Cross-References
//! - [`crate::indicators::volatility`] - Uses stdev for Bollinger Bands
//! - [`crate::indicators::momentum`] - Uses rolling_max/min for Stochastic
//! - [`crate::utils::ma`] - Complementary moving average functions

#![allow(dead_code)]

use crate::init_result;
use crate::utils::math::{is_not_zero, kahan_sum, kahan_sum_iter};
use std::cmp::{Ordering, Reverse};
use std::collections::{BinaryHeap, VecDeque};

/// 标准差（样本标准差，使用 n-1 作为分母）
///
/// 使用 Welford 增量算法实现 O(n) 时间复杂度。
/// 定期重新计算以防止浮点误差累积。
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - 与输入等长的向量，前 period-1 个值为 NaN
///
/// # 算法
/// Welford 在线算法的滑动窗口变体：
/// 1. 初始窗口使用标准 Welford 算法计算 mean 和 M2
/// 2. 滑动时，移除旧值并添加新值，增量更新 mean 和 M2
/// 3. 每 1000 次迭代重新计算以重置累积误差
///
/// # 性能
/// - 时间复杂度: O(n) 平均
/// - 空间复杂度: O(n) 用于结果向量
pub fn stdev(values: &[f64], period: usize) -> Vec<f64> {
    stdev_welford(values, period, false)
}

/// 标准差 Welford 增量实现（内部函数）
///
/// # 参数
/// - `population`: true 使用 n 分母（总体），false 使用 n-1 分母（样本）
fn stdev_welford(values: &[f64], period: usize, population: bool) -> Vec<f64> {
    const RECALC_INTERVAL: usize = 1000;

    if period < 2 || period > values.len() {
        return vec![f64::NAN; values.len()];
    }

    let n = values.len();
    let period_f = period as f64;
    let divisor = if population { period_f } else { period_f - 1.0 };
    let mut result = vec![f64::NAN; n];

    // 初始窗口：使用标准 Welford 算法
    let mut mean = 0.0;
    let mut m2 = 0.0; // M2 = Σ(x - mean)²

    for (i, &value) in values.iter().take(period).enumerate() {
        let delta = value - mean;
        mean += delta / (i + 1) as f64;
        let delta2 = value - mean;
        m2 += delta * delta2;
    }

    result[period - 1] = (m2 / divisor).sqrt();

    // 滑动窗口：增量更新
    for i in period..n {
        // 每 RECALC_INTERVAL 次重新计算以重置累积误差
        if (i - period + 1) % RECALC_INTERVAL == 0 {
            // 完整重新计算
            mean = 0.0;
            m2 = 0.0;
            for j in 0..period {
                let idx = i + 1 - period + j;
                let delta = values[idx] - mean;
                mean += delta / (j + 1) as f64;
                let delta2 = values[idx] - mean;
                m2 += delta * delta2;
            }
        } else {
            let old_val = values[i - period];
            let new_val = values[i];

            // 移除旧值：反向 Welford 更新
            let old_mean = mean;
            mean = (period_f * mean - old_val) / (period_f - 1.0);
            m2 -= (old_val - mean) * (old_val - old_mean);

            // 添加新值：正向 Welford 更新（针对固定大小窗口）
            let delta = new_val - mean;
            mean = (mean * (period_f - 1.0) + new_val) / period_f;
            let delta2 = new_val - mean;
            m2 += delta * delta2;
        }

        // 确保 m2 不为负（可能由浮点误差导致）
        result[i] = if m2 > 0.0 { (m2 / divisor).sqrt() } else { 0.0 };
    }

    result
}

/// 标准差（总体标准差，使用 n 作为分母）
///
/// 使用 Welford 增量算法实现 O(n) 时间复杂度。
/// 定期重新计算以防止浮点误差累积。
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - 与输入等长的向量，前 period-1 个值为 NaN
///
/// # 性能
/// - 时间复杂度: O(n) 平均
/// - 空间复杂度: O(n) 用于结果向量
pub fn stdev_population(values: &[f64], period: usize) -> Vec<f64> {
    stdev_welford(values, period, true)
}

/// 同时计算滚动均值和总体标准差（单次遍历）
///
/// 使用 Welford 增量算法在单次遍历中同时计算 mean 和 stdev，
/// 比分别调用 `sma` 和 `stdev_population` 更高效。
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - `(mean, stdev)` 元组，均为与输入等长的向量，前 period-1 个值为 NaN
///
/// # 性能
/// - 时间复杂度: O(n)
/// - 空间复杂度: O(n)
///
/// # 应用
/// - Bollinger Bands 计算（需要同时使用 SMA 和 StdDev）
pub fn mean_and_stdev_population(values: &[f64], period: usize) -> (Vec<f64>, Vec<f64>) {
    const RECALC_INTERVAL: usize = 1000;

    if period < 2 || period > values.len() {
        let nan_vec = vec![f64::NAN; values.len()];
        return (nan_vec.clone(), nan_vec);
    }

    let n = values.len();
    let period_f = period as f64;
    let mut mean_result = vec![f64::NAN; n];
    let mut stdev_result = vec![f64::NAN; n];

    // 初始窗口：使用标准 Welford 算法
    let mut mean = 0.0;
    let mut m2 = 0.0;

    for (i, &value) in values.iter().take(period).enumerate() {
        let delta = value - mean;
        mean += delta / (i + 1) as f64;
        let delta2 = value - mean;
        m2 += delta * delta2;
    }

    mean_result[period - 1] = mean;
    stdev_result[period - 1] = (m2 / period_f).sqrt();

    // 滑动窗口：增量更新
    for i in period..n {
        if (i - period + 1) % RECALC_INTERVAL == 0 {
            // 完整重新计算以重置累积误差
            mean = 0.0;
            m2 = 0.0;
            for j in 0..period {
                let idx = i + 1 - period + j;
                let delta = values[idx] - mean;
                mean += delta / (j + 1) as f64;
                let delta2 = values[idx] - mean;
                m2 += delta * delta2;
            }
        } else {
            let old_val = values[i - period];
            let new_val = values[i];

            // 移除旧值
            let old_mean = mean;
            mean = (period_f * mean - old_val) / (period_f - 1.0);
            m2 -= (old_val - mean) * (old_val - old_mean);

            // 添加新值
            let delta = new_val - mean;
            mean = (mean * (period_f - 1.0) + new_val) / period_f;
            let delta2 = new_val - mean;
            m2 += delta * delta2;
        }

        mean_result[i] = mean;
        stdev_result[i] = if m2 > 0.0 {
            (m2 / period_f).sqrt()
        } else {
            0.0
        };
    }

    (mean_result, stdev_result)
}

/// 最大值（滚动窗口）
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - 与输入等长的向量，前 period-1 个值为 NaN
pub fn rolling_max(values: &[f64], period: usize) -> Vec<f64> {
    if period == 0 || period > values.len() {
        return vec![f64::NAN; values.len()];
    }

    let mut result = vec![f64::NAN; values.len()];
    let mut deque: VecDeque<usize> = VecDeque::new();
    let mut nan_count = 0usize;

    for i in 0..values.len() {
        if values[i].is_nan() {
            nan_count += 1;
        }

        if i >= period {
            let out_idx = i - period;
            if values[out_idx].is_nan() {
                nan_count -= 1;
            }
            if deque.front() == Some(&out_idx) {
                deque.pop_front();
            }
        }

        if !values[i].is_nan() {
            while let Some(&back) = deque.back() {
                if values[back] <= values[i] {
                    deque.pop_back();
                } else {
                    break;
                }
            }
            deque.push_back(i);
        }

        if i + 1 >= period {
            result[i] = if nan_count > 0 {
                f64::NAN
            } else {
                // 安全获取：若 deque 意外为空，返回 NaN
                deque.front().map_or(f64::NAN, |&idx| values[idx])
            };
        }
    }

    result
}

/// 最小值（滚动窗口）
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - 与输入等长的向量，前 period-1 个值为 NaN
pub fn rolling_min(values: &[f64], period: usize) -> Vec<f64> {
    if period == 0 || period > values.len() {
        return vec![f64::NAN; values.len()];
    }

    let mut result = vec![f64::NAN; values.len()];
    let mut deque: VecDeque<usize> = VecDeque::new();
    let mut nan_count = 0usize;

    for i in 0..values.len() {
        if values[i].is_nan() {
            nan_count += 1;
        }

        if i >= period {
            let out_idx = i - period;
            if values[out_idx].is_nan() {
                nan_count -= 1;
            }
            if deque.front() == Some(&out_idx) {
                deque.pop_front();
            }
        }

        if !values[i].is_nan() {
            while let Some(&back) = deque.back() {
                if values[back] >= values[i] {
                    deque.pop_back();
                } else {
                    break;
                }
            }
            deque.push_back(i);
        }

        if i + 1 >= period {
            result[i] = if nan_count > 0 {
                f64::NAN
            } else {
                // 安全获取：若 deque 意外为空，返回 NaN
                deque.front().map_or(f64::NAN, |&idx| values[idx])
            };
        }
    }

    result
}

/// 求和（滚动窗口）
///
/// 使用 Kahan 补偿求和算法的增量更新版本，
/// 并定期重新计算以防止浮点误差累积。
///
/// # 算法特点
/// - 使用 Kahan 补偿减少每次增量更新的误差
/// - 每 1000 次迭代重新计算一次窗口和（使用 Kahan 求和）
/// - 为长序列提供优异的数值稳定性
pub fn rolling_sum(values: &[f64], period: usize) -> Vec<f64> {
    rolling_sum_kahan(values, period)
}

/// Kahan 补偿滚动求和（高精度版本）
///
/// 使用 Kahan 补偿算法进行增量更新，并定期重新计算以确保长期精度。
///
/// # 算法
/// 1. 初始窗口使用 Kahan 求和计算
/// 2. 滚动更新时对新值和旧值分别应用 Kahan 补偿
/// 3. 每 1000 次迭代重新计算窗口和以重置累积误差
///
/// # 性能
/// - 时间复杂度: O(n) 平均，定期重新计算导致最坏情况 O(n * period / 1000)
/// - 空间复杂度: O(n) 用于结果向量
///
/// # 精度
/// - 相对误差通常 < 1e-12（对于典型金融数据）
/// - 适用于大规模数据集（>100k 数据点）
pub fn rolling_sum_kahan(values: &[f64], period: usize) -> Vec<f64> {
    /// 重新计算间隔：每 1000 次迭代重新计算一次以重置累积误差
    const RECALC_INTERVAL: usize = 1000;

    if period == 0 || period > values.len() {
        return vec![f64::NAN; values.len()];
    }

    let mut result = vec![f64::NAN; values.len()];

    // 第一个窗口使用 Kahan 求和
    let first_sum = kahan_sum(&values[..period]);
    result[period - 1] = first_sum;

    // 滚动更新（使用 Kahan 补偿）
    let mut sum = first_sum;
    let mut compensation = 0.0;

    for i in period..values.len() {
        // 每隔 RECALC_INTERVAL 次进行完整 Kahan 重新计算以重置累积误差
        if (i - period + 1) % RECALC_INTERVAL == 0 {
            sum = kahan_sum(&values[i + 1 - period..=i]);
            compensation = 0.0;
            result[i] = sum;
        } else {
            // 增量更新（带 Kahan 补偿）
            // 添加新值
            let y = values[i] - compensation;
            let t = sum + y;
            compensation = (t - sum) - y;
            sum = t;

            // 减去旧值
            let y = -values[i - period] - compensation;
            let t = sum + y;
            compensation = (t - sum) - y;
            sum = t;

            result[i] = sum;
        }
    }

    result
}

/// 百分位数（滚动窗口）
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
/// - `percentile`: 百分位（0.0 - 1.0），如 0.5 表示中位数
///
/// # 返回
/// - 与输入等长的向量
pub fn rolling_percentile(values: &[f64], period: usize, percentile: f64) -> Vec<f64> {
    if period == 0 || period > values.len() || !(0.0..=1.0).contains(&percentile) {
        return vec![f64::NAN; values.len()];
    }

    const DUAL_HEAP_THRESHOLD: usize = 64;
    if period <= DUAL_HEAP_THRESHOLD {
        return rolling_percentile_select(values, period, percentile);
    }

    rolling_percentile_dual_heap(values, period, percentile)
}

fn rolling_percentile_select(values: &[f64], period: usize, percentile: f64) -> Vec<f64> {
    let n = values.len();
    let mut result = vec![f64::NAN; n];
    let mut window_keys = Vec::<i64>::with_capacity(period);

    for i in (period - 1)..n {
        window_keys.clear();
        for &v in &values[i + 1 - period..=i] {
            if v.is_nan() {
                continue;
            }
            window_keys.push(float_total_key(v));
        }

        if window_keys.is_empty() {
            continue;
        }

        let valid_len = window_keys.len();
        let index = ((percentile * (valid_len - 1) as f64).round() as usize).min(valid_len - 1);

        window_keys.select_nth_unstable(index);
        result[i] = float_from_total_key(window_keys[index]);
    }

    result
}

#[derive(Clone, Copy, Debug)]
struct PercentileHeapItem {
    key: i64,
    index: usize,
}

#[inline]
fn float_total_key(value: f64) -> i64 {
    let bits = value.to_bits() as i64;
    bits ^ ((((bits >> 63) as u64) >> 1) as i64)
}

#[inline]
fn float_from_total_key(key: i64) -> f64 {
    let bits = if key < 0 {
        (key ^ i64::MAX) as u64
    } else {
        key as u64
    };
    f64::from_bits(bits)
}

impl PercentileHeapItem {
    #[inline]
    fn value(&self) -> f64 {
        float_from_total_key(self.key)
    }
}

impl PartialEq for PercentileHeapItem {
    fn eq(&self, other: &Self) -> bool {
        self.key == other.key && self.index == other.index
    }
}

impl Eq for PercentileHeapItem {}

impl PartialOrd for PercentileHeapItem {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for PercentileHeapItem {
    fn cmp(&self, other: &Self) -> Ordering {
        match self.key.cmp(&other.key) {
            Ordering::Equal => self.index.cmp(&other.index),
            ord => ord,
        }
    }
}

fn rolling_percentile_dual_heap(values: &[f64], period: usize, percentile: f64) -> Vec<f64> {
    let n = values.len();
    let mut result = vec![f64::NAN; n];
    let mut lower = BinaryHeap::<PercentileHeapItem>::new(); // max-heap
    let mut upper = BinaryHeap::<Reverse<PercentileHeapItem>>::new(); // min-heap
    let mut side = vec![0u8; n]; // 0=lower, 1=upper

    let mut lower_size = 0usize;
    let mut upper_size = 0usize;

    #[inline]
    fn prune_lower(heap: &mut BinaryHeap<PercentileHeapItem>, start: usize) {
        while let Some(top) = heap.peek() {
            if top.index < start {
                heap.pop();
            } else {
                break;
            }
        }
    }

    #[inline]
    fn prune_upper(heap: &mut BinaryHeap<Reverse<PercentileHeapItem>>, start: usize) {
        while let Some(top) = heap.peek() {
            if top.0.index < start {
                heap.pop();
            } else {
                break;
            }
        }
    }

    #[inline]
    fn pop_lower_valid(
        heap: &mut BinaryHeap<PercentileHeapItem>,
        start: usize,
    ) -> Option<PercentileHeapItem> {
        while let Some(item) = heap.pop() {
            if item.index >= start {
                return Some(item);
            }
        }
        None
    }

    #[inline]
    fn pop_upper_valid(
        heap: &mut BinaryHeap<Reverse<PercentileHeapItem>>,
        start: usize,
    ) -> Option<PercentileHeapItem> {
        while let Some(Reverse(item)) = heap.pop() {
            if item.index >= start {
                return Some(item);
            }
        }
        None
    }

    for i in 0..n {
        let start = (i + 1).saturating_sub(period);

        if start > 0 {
            let old_idx = start - 1;
            let old_val = values[old_idx];
            if !old_val.is_nan() {
                if side[old_idx] == 0 {
                    lower_size = lower_size.saturating_sub(1);
                } else {
                    upper_size = upper_size.saturating_sub(1);
                }
            }
        }

        prune_lower(&mut lower, start);

        let new_val = values[i];
        if !new_val.is_nan() {
            let new_key = float_total_key(new_val);
            let push_to_lower = match lower.peek() {
                None => true,
                Some(top) => new_key <= top.key,
            };

            let item = PercentileHeapItem {
                key: new_key,
                index: i,
            };

            if push_to_lower {
                lower.push(item);
                lower_size += 1;
                side[i] = 0;
            } else {
                upper.push(Reverse(item));
                upper_size += 1;
                side[i] = 1;
            }
        }

        let valid_len = lower_size + upper_size;
        if valid_len == 0 {
            continue;
        }

        let index = ((percentile * (valid_len - 1) as f64).round() as usize).min(valid_len - 1);
        let target_lower = index + 1;

        while lower_size > target_lower {
            if let Some(item) = pop_lower_valid(&mut lower, start) {
                lower_size = lower_size.saturating_sub(1);
                upper.push(Reverse(item));
                upper_size += 1;
                side[item.index] = 1;
            } else {
                break;
            }
        }

        while lower_size < target_lower {
            if let Some(item) = pop_upper_valid(&mut upper, start) {
                upper_size = upper_size.saturating_sub(1);
                lower.push(item);
                lower_size += 1;
                side[item.index] = 0;
            } else {
                break;
            }
        }

        prune_lower(&mut lower, start);
        prune_upper(&mut upper, start);

        if let (Some(lower_top), Some(upper_top)) = (lower.peek(), upper.peek()) {
            if lower_top.key > upper_top.0.key {
                let lower_item = lower
                    .pop()
                    .expect("lower.peek() returned Some but lower.pop() returned None");
                let upper_item = upper
                    .pop()
                    .expect("upper.peek() returned Some but upper.pop() returned None")
                    .0;

                upper.push(Reverse(lower_item));
                lower.push(upper_item);

                side[lower_item.index] = 1;
                side[upper_item.index] = 0;
            }
        }

        if i + 1 >= period {
            if let Some(top) = lower.peek() {
                result[i] = top.value();
            }
        }
    }

    result
}

/// 变化率（Rate of Change）
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - ROC`[i]` = (values`[i]` / values[i-period] - 1) * 100
pub fn roc(values: &[f64], period: usize) -> Vec<f64> {
    if period == 0 || period >= values.len() {
        return vec![f64::NAN; values.len()];
    }

    let mut result = vec![f64::NAN; values.len()];

    for i in period..values.len() {
        if is_not_zero(values[i - period]) {
            result[i] = ((values[i] / values[i - period]) - 1.0) * 100.0;
        }
    }

    result
}

/// 动量（Momentum）
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - MOM`[i]` = values`[i]` - values[i-period]
pub fn momentum(values: &[f64], period: usize) -> Vec<f64> {
    if period == 0 || period >= values.len() {
        return vec![f64::NAN; values.len()];
    }

    let mut result = vec![f64::NAN; values.len()];

    for i in period..values.len() {
        result[i] = values[i] - values[i - period];
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stdev() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = stdev(&values, 3);
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        // stdev([1,2,3]) = sqrt(((1-2)^2 + (2-2)^2 + (3-2)^2) / 2) = 1.0
        assert!((result[2] - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_rolling_max() {
        let values = vec![1.0, 3.0, 2.0, 5.0, 4.0];
        let result = rolling_max(&values, 3);
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        assert_eq!(result[2], 3.0); // max([1,3,2])
        assert_eq!(result[3], 5.0); // max([3,2,5])
        assert_eq!(result[4], 5.0); // max([2,5,4])
    }

    #[test]
    fn test_rolling_max_min_with_nan() {
        let values = vec![1.0, f64::NAN, 2.0, 3.0];
        let max_result = rolling_max(&values, 2);
        let min_result = rolling_min(&values, 2);

        assert!(max_result[0].is_nan());
        assert!(max_result[1].is_nan());
        assert!(max_result[2].is_nan());
        assert_eq!(max_result[3], 3.0);

        assert!(min_result[0].is_nan());
        assert!(min_result[1].is_nan());
        assert!(min_result[2].is_nan());
        assert_eq!(min_result[3], 2.0);
    }

    #[test]
    fn test_roc() {
        let values = vec![100.0, 105.0, 110.0, 115.0];
        let result = roc(&values, 1);
        assert!(result[0].is_nan());
        assert!((result[1] - 5.0).abs() < 1e-10); // (105/100 - 1) * 100
        assert!((result[2] - 4.761904761904762).abs() < 1e-10); // (110/105 - 1) * 100
    }

    #[test]
    fn test_rolling_percentile_dual_heap_matches_select() {
        let mut values = Vec::with_capacity(500);
        let mut state = 0x1234_5678_9abc_def0u64;

        for i in 0..500usize {
            state = state
                .wrapping_mul(6364136223846793005u64)
                .wrapping_add(1442695040888963407u64);

            if i % 57 == 0 {
                values.push(f64::NAN);
                continue;
            }

            let raw = (state >> 33) as u32;
            let v = (raw as f64 / (u32::MAX as f64)) * 200.0 - 100.0;

            if i % 13 == 0 {
                values.push(v.round());
            } else {
                values.push(v);
            }
        }

        let period = 200;
        for percentile in [0.0, 0.1, 0.5, 0.9, 1.0] {
            let select = rolling_percentile_select(&values, period, percentile);
            let dual = rolling_percentile_dual_heap(&values, period, percentile);

            assert_eq!(select.len(), dual.len());
            for i in 0..values.len() {
                let a = select[i];
                let b = dual[i];
                if a.is_nan() && b.is_nan() {
                    continue;
                }
                assert_eq!(
                    a.to_bits(),
                    b.to_bits(),
                    "rolling_percentile mismatch: percentile={percentile} i={i} a={a} b={b}"
                );
            }
        }
    }

    #[test]
    fn test_momentum() {
        let values = vec![100.0, 105.0, 110.0, 115.0];
        let result = momentum(&values, 1);
        assert!(result[0].is_nan());
        assert_eq!(result[1], 5.0); // 105 - 100
        assert_eq!(result[2], 5.0); // 110 - 105
        assert_eq!(result[3], 5.0); // 115 - 110
    }
}

/// Internal computed values for rolling linear regression.
#[derive(Debug, Clone, Copy)]
struct LinRegComputed {
    slope: f64,
    intercept: f64,
    r_squared: f64,
    numerator: f64,
    ss_total: f64,
}

#[inline]
fn linreg_constants(period: usize) -> (f64, f64, f64, f64) {
    let period_f = period as f64;
    let p_minus_1 = period_f - 1.0;

    // x = [0, 1, 2, ..., period-1]
    let sum_x = p_minus_1 * period_f / 2.0;
    let x_mean = sum_x / period_f;
    let sum_xx = p_minus_1 * period_f * (2.0 * period_f - 1.0) / 6.0;
    let denom_x = sum_xx - (sum_x * sum_x) / period_f;

    (period_f, sum_x, x_mean, denom_x)
}

/// Rolling linear regression core (O(n))
///
/// Uses incremental updates for `sum_y`, `sum_xy`, `sum_yy` and periodically
/// recomputes the window to limit floating-point drift.
fn rolling_linreg_apply<F>(y_values: &[f64], period: usize, mut f: F)
where
    F: FnMut(usize, Option<LinRegComputed>),
{
    const RECALC_INTERVAL: usize = 1000;

    let n = y_values.len();
    if period < 2 || period > n {
        return;
    }

    let (period_f, sum_x, x_mean, denom_x) = linreg_constants(period);
    debug_assert!(
        denom_x > 0.0,
        "linreg denom_x must be positive for period >= 2"
    );

    #[inline]
    fn kahan_add(sum: &mut f64, compensation: &mut f64, value: f64) {
        let y = value - *compensation;
        let t = *sum + y;
        *compensation = (t - *sum) - y;
        *sum = t;
    }

    let mut sum_y = 0.0;
    let mut sum_y_comp = 0.0;
    let mut sum_xy = 0.0;
    let mut sum_xy_comp = 0.0;
    let mut sum_yy = 0.0;
    let mut sum_yy_comp = 0.0;
    let mut nan_count = 0usize;

    // 初始窗口
    for (j, &raw) in y_values.iter().take(period).enumerate() {
        let y = if raw.is_nan() {
            nan_count += 1;
            0.0
        } else {
            raw
        };

        kahan_add(&mut sum_y, &mut sum_y_comp, y);
        kahan_add(&mut sum_xy, &mut sum_xy_comp, (j as f64) * y);
        kahan_add(&mut sum_yy, &mut sum_yy_comp, y * y);
    }

    let mut steps_since_recalc = 0usize;
    let last_x = period_f - 1.0;

    for i in (period - 1)..n {
        if i >= period {
            if steps_since_recalc >= RECALC_INTERVAL {
                // 完整重新计算当前窗口（重置累积误差）
                sum_y = 0.0;
                sum_y_comp = 0.0;
                sum_xy = 0.0;
                sum_xy_comp = 0.0;
                sum_yy = 0.0;
                sum_yy_comp = 0.0;
                nan_count = 0;

                let start = i + 1 - period;
                for (j, &raw) in y_values[start..=i].iter().enumerate() {
                    let y = if raw.is_nan() {
                        nan_count += 1;
                        0.0
                    } else {
                        raw
                    };

                    kahan_add(&mut sum_y, &mut sum_y_comp, y);
                    kahan_add(&mut sum_xy, &mut sum_xy_comp, (j as f64) * y);
                    kahan_add(&mut sum_yy, &mut sum_yy_comp, y * y);
                }

                steps_since_recalc = 0;
            } else {
                let old_raw = y_values[i - period];
                let new_raw = y_values[i];

                let old_y = if old_raw.is_nan() {
                    nan_count = nan_count.saturating_sub(1);
                    0.0
                } else {
                    old_raw
                };
                let new_y = if new_raw.is_nan() {
                    nan_count += 1;
                    0.0
                } else {
                    new_raw
                };

                let sum_y_old = sum_y;

                // sum_xy 更新（x = 0..period-1）：
                // new_sum_xy = old_sum_xy - (sum_y - y0) + (period-1) * new_y
                kahan_add(&mut sum_xy, &mut sum_xy_comp, -(sum_y_old - old_y));
                kahan_add(&mut sum_xy, &mut sum_xy_comp, last_x * new_y);

                // sum_y 更新
                kahan_add(&mut sum_y, &mut sum_y_comp, -old_y);
                kahan_add(&mut sum_y, &mut sum_y_comp, new_y);

                // sum_yy 更新
                kahan_add(&mut sum_yy, &mut sum_yy_comp, -(old_y * old_y));
                kahan_add(&mut sum_yy, &mut sum_yy_comp, new_y * new_y);

                steps_since_recalc += 1;
            }
        }

        if nan_count > 0 {
            f(i, None);
            continue;
        }

        // numerator = Σ(x - x̄)(y - ȳ) = Σ(xy) - (Σx * Σy) / n
        let numerator = sum_xy - (sum_x * sum_y) / period_f;

        let slope = numerator / denom_x;
        let intercept = (sum_y / period_f) - slope * x_mean;

        // ss_total = Σ(y - ȳ)² = Σ(y²) - (Σy)² / n
        let mut ss_total = sum_yy - (sum_y * sum_y) / period_f;
        if ss_total < 0.0 {
            ss_total = 0.0;
        }

        // r² = numerator² / (denom_x * ss_total)
        let r_squared = if ss_total > 0.0 {
            ((numerator * numerator) / (denom_x * ss_total)).clamp(0.0, 1.0)
        } else {
            1.0
        };

        f(
            i,
            Some(LinRegComputed {
                slope,
                intercept,
                r_squared,
                numerator,
                ss_total,
            }),
        );
    }
}

/// 线性回归（Linear Regression）
///
/// 返回：(slope, intercept, r_squared)
/// - slope: 斜率
/// - intercept: 截距
/// - r_squared: R² 决定系数（0-1，越接近1拟合越好）
pub fn linear_regression(y_values: &[f64], period: usize) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let n = y_values.len();
    let mut slope = init_result!(n);
    let mut intercept = init_result!(n);
    let mut r_squared = init_result!(n);

    if period < 2 || period > n {
        return (slope, intercept, r_squared);
    }

    rolling_linreg_apply(y_values, period, |i, computed| {
        if let Some(stats) = computed {
            slope[i] = stats.slope;
            intercept[i] = stats.intercept;
            r_squared[i] = stats.r_squared;
        }
    });

    (slope, intercept, r_squared)
}

/// Pearson 相关系数（Correlation Coefficient）
///
/// 计算两个序列的滚动相关系数
///
/// # 参数
/// - `x`: 第一个序列
/// - `y`: 第二个序列
/// - `period`: 周期
///
/// # 返回
/// - 相关系数序列（-1 到 1）
///   * 1: 完全正相关
///   * 0: 无相关
///   * -1: 完全负相关
pub fn correlation(x: &[f64], y: &[f64], period: usize) -> Vec<f64> {
    let n = x.len().min(y.len());
    let mut result = init_result!(n);

    if period < 2 || period > n {
        return result;
    }

    /// 重新计算间隔：用于限制增量更新的误差累积
    const RECALC_INTERVAL: usize = 1000;

    #[inline]
    fn kahan_add(sum: &mut f64, compensation: &mut f64, value: f64) {
        let y = value - *compensation;
        let t = *sum + y;
        *compensation = (t - *sum) - y;
        *sum = t;
    }

    let period_f = period as f64;
    let mut sum_x = 0.0;
    let mut sum_x_comp = 0.0;
    let mut sum_y = 0.0;
    let mut sum_y_comp = 0.0;
    let mut sum_xx = 0.0;
    let mut sum_xx_comp = 0.0;
    let mut sum_yy = 0.0;
    let mut sum_yy_comp = 0.0;
    let mut sum_xy = 0.0;
    let mut sum_xy_comp = 0.0;
    let mut nan_count = 0usize;

    // 初始窗口
    for i in 0..period {
        let xr = x[i];
        let yr = y[i];

        if xr.is_nan() || yr.is_nan() {
            nan_count += 1;
        }

        let xv = if xr.is_nan() { 0.0 } else { xr };
        let yv = if yr.is_nan() { 0.0 } else { yr };

        kahan_add(&mut sum_x, &mut sum_x_comp, xv);
        kahan_add(&mut sum_y, &mut sum_y_comp, yv);
        kahan_add(&mut sum_xx, &mut sum_xx_comp, xv * xv);
        kahan_add(&mut sum_yy, &mut sum_yy_comp, yv * yv);
        kahan_add(&mut sum_xy, &mut sum_xy_comp, xv * yv);
    }

    let mut steps_since_recalc = 0usize;

    for i in (period - 1)..n {
        if i >= period {
            if steps_since_recalc >= RECALC_INTERVAL {
                // 重新计算当前窗口（重置误差 + 恢复 NaN 之后的可用结果）
                sum_x = 0.0;
                sum_x_comp = 0.0;
                sum_y = 0.0;
                sum_y_comp = 0.0;
                sum_xx = 0.0;
                sum_xx_comp = 0.0;
                sum_yy = 0.0;
                sum_yy_comp = 0.0;
                sum_xy = 0.0;
                sum_xy_comp = 0.0;
                nan_count = 0;

                let start = i + 1 - period;
                for j in start..=i {
                    let xr = x[j];
                    let yr = y[j];

                    if xr.is_nan() || yr.is_nan() {
                        nan_count += 1;
                    }

                    let xv = if xr.is_nan() { 0.0 } else { xr };
                    let yv = if yr.is_nan() { 0.0 } else { yr };

                    kahan_add(&mut sum_x, &mut sum_x_comp, xv);
                    kahan_add(&mut sum_y, &mut sum_y_comp, yv);
                    kahan_add(&mut sum_xx, &mut sum_xx_comp, xv * xv);
                    kahan_add(&mut sum_yy, &mut sum_yy_comp, yv * yv);
                    kahan_add(&mut sum_xy, &mut sum_xy_comp, xv * yv);
                }

                steps_since_recalc = 0;
            } else {
                let old_xr = x[i - period];
                let old_yr = y[i - period];
                if old_xr.is_nan() || old_yr.is_nan() {
                    nan_count = nan_count.saturating_sub(1);
                }

                let new_xr = x[i];
                let new_yr = y[i];
                if new_xr.is_nan() || new_yr.is_nan() {
                    nan_count += 1;
                }

                let old_x = if old_xr.is_nan() { 0.0 } else { old_xr };
                let old_y = if old_yr.is_nan() { 0.0 } else { old_yr };
                let new_x = if new_xr.is_nan() { 0.0 } else { new_xr };
                let new_y = if new_yr.is_nan() { 0.0 } else { new_yr };

                kahan_add(&mut sum_x, &mut sum_x_comp, -old_x);
                kahan_add(&mut sum_x, &mut sum_x_comp, new_x);
                kahan_add(&mut sum_y, &mut sum_y_comp, -old_y);
                kahan_add(&mut sum_y, &mut sum_y_comp, new_y);

                kahan_add(&mut sum_xx, &mut sum_xx_comp, -(old_x * old_x));
                kahan_add(&mut sum_xx, &mut sum_xx_comp, new_x * new_x);
                kahan_add(&mut sum_yy, &mut sum_yy_comp, -(old_y * old_y));
                kahan_add(&mut sum_yy, &mut sum_yy_comp, new_y * new_y);

                kahan_add(&mut sum_xy, &mut sum_xy_comp, -(old_x * old_y));
                kahan_add(&mut sum_xy, &mut sum_xy_comp, new_x * new_y);

                steps_since_recalc += 1;
            }
        }

        // 与现有实现保持一致：窗口内出现 NaN 时返回 0.0（避免 NaN 扩散）
        if nan_count > 0 {
            result[i] = 0.0;
            continue;
        }

        let cov_num = period_f * sum_xy - sum_x * sum_y;
        let var_x_num = period_f * sum_xx - sum_x * sum_x;
        let var_y_num = period_f * sum_yy - sum_y * sum_y;

        let denom = (var_x_num * var_y_num).sqrt();
        if denom.is_finite() && denom > 0.0 {
            let corr = cov_num / denom;
            // 数值误差可能导致结果略微越界（例如 1.0000000000000286），
            // 这里做 clamp 以满足相关系数定义域 [-1, 1]。
            result[i] = if corr.is_finite() {
                corr.clamp(-1.0, 1.0)
            } else {
                0.0
            };
        } else {
            result[i] = 0.0; // 无方差/无效分母时相关系数为 0
        }
    }

    result
}

/// Z-Score（标准分数）
///
/// 计算标准化分数：z = (x - μ) / σ
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - Z-Score 序列（标准化后的值）
pub fn zscore(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut result = init_result!(n);

    if period < 2 || period > n {
        return result;
    }

    const RECALC_INTERVAL: usize = 1000;

    #[inline]
    fn kahan_add(sum: &mut f64, compensation: &mut f64, value: f64) {
        let y = value - *compensation;
        let t = *sum + y;
        *compensation = (t - *sum) - y;
        *sum = t;
    }

    let period_f = period as f64;
    let denom = period_f * period_f;
    let mut sum = 0.0;
    let mut sum_comp = 0.0;
    let mut sum_sq = 0.0;
    let mut sum_sq_comp = 0.0;
    let mut nan_count = 0usize;

    // 初始窗口
    for &raw in values.iter().take(period) {
        if raw.is_nan() {
            nan_count += 1;
        }

        let v = if raw.is_nan() { 0.0 } else { raw };
        kahan_add(&mut sum, &mut sum_comp, v);
        kahan_add(&mut sum_sq, &mut sum_sq_comp, v * v);
    }

    let mut steps_since_recalc = 0usize;

    for i in (period - 1)..n {
        if i >= period {
            if steps_since_recalc >= RECALC_INTERVAL {
                sum = 0.0;
                sum_comp = 0.0;
                sum_sq = 0.0;
                sum_sq_comp = 0.0;
                nan_count = 0;

                let start = i + 1 - period;
                for &raw in &values[start..=i] {
                    if raw.is_nan() {
                        nan_count += 1;
                    }

                    let v = if raw.is_nan() { 0.0 } else { raw };
                    kahan_add(&mut sum, &mut sum_comp, v);
                    kahan_add(&mut sum_sq, &mut sum_sq_comp, v * v);
                }

                steps_since_recalc = 0;
            } else {
                let old_raw = values[i - period];
                if old_raw.is_nan() {
                    nan_count = nan_count.saturating_sub(1);
                }

                let new_raw = values[i];
                if new_raw.is_nan() {
                    nan_count += 1;
                }

                let old_v = if old_raw.is_nan() { 0.0 } else { old_raw };
                let new_v = if new_raw.is_nan() { 0.0 } else { new_raw };

                kahan_add(&mut sum, &mut sum_comp, -old_v);
                kahan_add(&mut sum, &mut sum_comp, new_v);
                kahan_add(&mut sum_sq, &mut sum_sq_comp, -(old_v * old_v));
                kahan_add(&mut sum_sq, &mut sum_sq_comp, new_v * new_v);

                steps_since_recalc += 1;
            }
        }

        // 与现有实现保持一致：窗口内出现 NaN 时返回 0.0（避免 NaN 扩散）
        if nan_count > 0 {
            result[i] = 0.0;
            continue;
        }

        let mean = sum / period_f;
        let var_num = period_f * sum_sq - sum * sum;
        let variance = if var_num > 0.0 { var_num / denom } else { 0.0 };
        let std = variance.sqrt();

        if std > 0.0 {
            result[i] = (values[i] - mean) / std;
        } else {
            result[i] = 0.0; // 无标准差/无效分母时 Z-Score 为 0
        }
    }

    result
}

/// 协方差（Covariance）
///
/// 计算两个序列的滚动协方差
///
/// # 参数
/// - `x`: 第一个序列
/// - `y`: 第二个序列
/// - `period`: 周期
///
/// # 返回
/// - 协方差序列
pub fn covariance(x: &[f64], y: &[f64], period: usize) -> Vec<f64> {
    let n = x.len().min(y.len());
    let mut result = init_result!(n);

    if period < 2 || period > n {
        return result;
    }

    const RECALC_INTERVAL: usize = 1000;

    #[inline]
    fn kahan_add(sum: &mut f64, compensation: &mut f64, value: f64) {
        let y = value - *compensation;
        let t = *sum + y;
        *compensation = (t - *sum) - y;
        *sum = t;
    }

    let period_f = period as f64;
    let denom = period_f * period_f;
    let mut sum_x = 0.0;
    let mut sum_x_comp = 0.0;
    let mut sum_y = 0.0;
    let mut sum_y_comp = 0.0;
    let mut sum_xy = 0.0;
    let mut sum_xy_comp = 0.0;
    let mut nan_count = 0usize;

    // 初始窗口
    for i in 0..period {
        let xr = x[i];
        let yr = y[i];

        if xr.is_nan() || yr.is_nan() {
            nan_count += 1;
        }

        let xv = if xr.is_nan() { 0.0 } else { xr };
        let yv = if yr.is_nan() { 0.0 } else { yr };

        kahan_add(&mut sum_x, &mut sum_x_comp, xv);
        kahan_add(&mut sum_y, &mut sum_y_comp, yv);
        kahan_add(&mut sum_xy, &mut sum_xy_comp, xv * yv);
    }

    let mut steps_since_recalc = 0usize;

    for i in (period - 1)..n {
        if i >= period {
            if steps_since_recalc >= RECALC_INTERVAL {
                sum_x = 0.0;
                sum_x_comp = 0.0;
                sum_y = 0.0;
                sum_y_comp = 0.0;
                sum_xy = 0.0;
                sum_xy_comp = 0.0;
                nan_count = 0;

                let start = i + 1 - period;
                for j in start..=i {
                    let xr = x[j];
                    let yr = y[j];

                    if xr.is_nan() || yr.is_nan() {
                        nan_count += 1;
                    }

                    let xv = if xr.is_nan() { 0.0 } else { xr };
                    let yv = if yr.is_nan() { 0.0 } else { yr };

                    kahan_add(&mut sum_x, &mut sum_x_comp, xv);
                    kahan_add(&mut sum_y, &mut sum_y_comp, yv);
                    kahan_add(&mut sum_xy, &mut sum_xy_comp, xv * yv);
                }

                steps_since_recalc = 0;
            } else {
                let old_xr = x[i - period];
                let old_yr = y[i - period];
                if old_xr.is_nan() || old_yr.is_nan() {
                    nan_count = nan_count.saturating_sub(1);
                }

                let new_xr = x[i];
                let new_yr = y[i];
                if new_xr.is_nan() || new_yr.is_nan() {
                    nan_count += 1;
                }

                let old_x = if old_xr.is_nan() { 0.0 } else { old_xr };
                let old_y = if old_yr.is_nan() { 0.0 } else { old_yr };
                let new_x = if new_xr.is_nan() { 0.0 } else { new_xr };
                let new_y = if new_yr.is_nan() { 0.0 } else { new_yr };

                kahan_add(&mut sum_x, &mut sum_x_comp, -old_x);
                kahan_add(&mut sum_x, &mut sum_x_comp, new_x);
                kahan_add(&mut sum_y, &mut sum_y_comp, -old_y);
                kahan_add(&mut sum_y, &mut sum_y_comp, new_y);
                kahan_add(&mut sum_xy, &mut sum_xy_comp, -(old_x * old_y));
                kahan_add(&mut sum_xy, &mut sum_xy_comp, new_x * new_y);

                steps_since_recalc += 1;
            }
        }

        if nan_count > 0 {
            result[i] = f64::NAN;
            continue;
        }

        let cov_num = period_f * sum_xy - sum_x * sum_y;
        result[i] = cov_num / denom;
    }

    result
}

/// Beta（贝塔系数）
///
/// 计算资产相对于基准的系统性风险
/// Beta = Cov(asset, benchmark) / Var(benchmark)
///
/// # 参数
/// - `asset_returns`: 资产收益率序列
/// - `benchmark_returns`: 基准收益率序列（如市场指数）
/// - `period`: 周期
///
/// # 返回
/// - Beta 系数序列
///   * Beta > 1: 比市场波动大
///   * Beta = 1: 与市场波动一致
///   * Beta < 1: 比市场波动小
///   * Beta < 0: 与市场负相关
pub fn beta(asset_returns: &[f64], benchmark_returns: &[f64], period: usize) -> Vec<f64> {
    let n = asset_returns.len().min(benchmark_returns.len());
    let mut result = init_result!(n);

    if period < 2 || period > n {
        return result;
    }

    const RECALC_INTERVAL: usize = 1000;

    #[inline]
    fn kahan_add(sum: &mut f64, compensation: &mut f64, value: f64) {
        let y = value - *compensation;
        let t = *sum + y;
        *compensation = (t - *sum) - y;
        *sum = t;
    }

    let period_f = period as f64;
    let mut sum_a = 0.0;
    let mut sum_a_comp = 0.0;
    let mut sum_b = 0.0;
    let mut sum_b_comp = 0.0;
    let mut sum_ab = 0.0;
    let mut sum_ab_comp = 0.0;
    let mut sum_bb = 0.0;
    let mut sum_bb_comp = 0.0;
    let mut nan_count = 0usize;

    // 初始窗口
    for i in 0..period {
        let ar = asset_returns[i];
        let br = benchmark_returns[i];

        if ar.is_nan() || br.is_nan() {
            nan_count += 1;
        }

        let a = if ar.is_nan() { 0.0 } else { ar };
        let b = if br.is_nan() { 0.0 } else { br };

        kahan_add(&mut sum_a, &mut sum_a_comp, a);
        kahan_add(&mut sum_b, &mut sum_b_comp, b);
        kahan_add(&mut sum_ab, &mut sum_ab_comp, a * b);
        kahan_add(&mut sum_bb, &mut sum_bb_comp, b * b);
    }

    let mut steps_since_recalc = 0usize;

    for i in (period - 1)..n {
        if i >= period {
            if steps_since_recalc >= RECALC_INTERVAL {
                sum_a = 0.0;
                sum_a_comp = 0.0;
                sum_b = 0.0;
                sum_b_comp = 0.0;
                sum_ab = 0.0;
                sum_ab_comp = 0.0;
                sum_bb = 0.0;
                sum_bb_comp = 0.0;
                nan_count = 0;

                let start = i + 1 - period;
                for j in start..=i {
                    let ar = asset_returns[j];
                    let br = benchmark_returns[j];

                    if ar.is_nan() || br.is_nan() {
                        nan_count += 1;
                    }

                    let a = if ar.is_nan() { 0.0 } else { ar };
                    let b = if br.is_nan() { 0.0 } else { br };

                    kahan_add(&mut sum_a, &mut sum_a_comp, a);
                    kahan_add(&mut sum_b, &mut sum_b_comp, b);
                    kahan_add(&mut sum_ab, &mut sum_ab_comp, a * b);
                    kahan_add(&mut sum_bb, &mut sum_bb_comp, b * b);
                }

                steps_since_recalc = 0;
            } else {
                let old_ar = asset_returns[i - period];
                let old_br = benchmark_returns[i - period];
                if old_ar.is_nan() || old_br.is_nan() {
                    nan_count = nan_count.saturating_sub(1);
                }

                let new_ar = asset_returns[i];
                let new_br = benchmark_returns[i];
                if new_ar.is_nan() || new_br.is_nan() {
                    nan_count += 1;
                }

                let old_a = if old_ar.is_nan() { 0.0 } else { old_ar };
                let old_b = if old_br.is_nan() { 0.0 } else { old_br };
                let new_a = if new_ar.is_nan() { 0.0 } else { new_ar };
                let new_b = if new_br.is_nan() { 0.0 } else { new_br };

                kahan_add(&mut sum_a, &mut sum_a_comp, -old_a);
                kahan_add(&mut sum_a, &mut sum_a_comp, new_a);
                kahan_add(&mut sum_b, &mut sum_b_comp, -old_b);
                kahan_add(&mut sum_b, &mut sum_b_comp, new_b);
                kahan_add(&mut sum_ab, &mut sum_ab_comp, -(old_a * old_b));
                kahan_add(&mut sum_ab, &mut sum_ab_comp, new_a * new_b);
                kahan_add(&mut sum_bb, &mut sum_bb_comp, -(old_b * old_b));
                kahan_add(&mut sum_bb, &mut sum_bb_comp, new_b * new_b);

                steps_since_recalc += 1;
            }
        }

        // 与现有实现保持一致：窗口内出现 NaN 时返回 0.0
        if nan_count > 0 {
            result[i] = 0.0;
            continue;
        }

        let cov_num = period_f * sum_ab - sum_a * sum_b;
        let var_b_num = period_f * sum_bb - sum_b * sum_b;
        if var_b_num.is_finite() && var_b_num > 0.0 {
            result[i] = cov_num / var_b_num;
        } else {
            result[i] = 0.0;
        }
    }

    result
}

/// 标准误差（Standard Error）
///
/// 线性回归的标准误差：SE = sqrt(Σ(y - ŷ)² / (n - 2))
///
/// # 参数
/// - `y_values`: 实际值序列
/// - `period`: 周期
///
/// # 返回
/// - 标准误差序列
pub fn standard_error(y_values: &[f64], period: usize) -> Vec<f64> {
    let n = y_values.len();
    let mut result = init_result!(n);

    if period < 3 || period > n {
        return result;
    }

    let degrees_of_freedom = (period - 2) as f64;
    rolling_linreg_apply(y_values, period, |i, computed| {
        if let Some(stats) = computed {
            let ss_residual = (stats.ss_total * (1.0 - stats.r_squared)).max(0.0);
            result[i] = (ss_residual / degrees_of_freedom).sqrt();
        }
    });

    result
}

#[cfg(test)]
mod tests_advanced {
    use super::*;

    #[test]
    fn test_linear_regression() {
        // 完美线性关系：y = 2x + 1
        let y = vec![1.0, 3.0, 5.0, 7.0, 9.0];
        let (slope, intercept, r_squared) = linear_regression(&y, 5);

        assert!((slope[4] - 2.0).abs() < 1e-10);
        assert!((intercept[4] - 1.0).abs() < 1e-10);
        assert!((r_squared[4] - 1.0).abs() < 1e-10); // 完美拟合
    }

    #[test]
    fn test_correlation() {
        // 完全正相关
        let x = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let y = vec![2.0, 4.0, 6.0, 8.0, 10.0];
        let result = correlation(&x, &y, 5);

        assert!((result[4] - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_zscore() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = zscore(&values, 5);

        // 标准化后中间值应接近 0
        assert!(result[4].abs() < 2.0);
    }

    #[test]
    fn test_beta() {
        // 资产收益与市场完全一致
        let asset = vec![0.01, 0.02, -0.01, 0.03, 0.01];
        let benchmark = vec![0.01, 0.02, -0.01, 0.03, 0.01];
        let result = beta(&asset, &benchmark, 5);

        assert!((result[4] - 1.0).abs() < 1e-10);
    }
}

// ==================== TA-Lib 兼容统计函数 ====================

/// CORREL - Pearson Correlation Coefficient (TA-Lib compatible)
///
/// 皮尔逊相关系数（TA-Lib 兼容版本）
///
/// # 参数
/// - `values1`: 第一个序列
/// - `values2`: 第二个序列
/// - `period`: 周期
///
/// # 返回
/// - 相关系数序列（-1 到 1）
pub fn correl(values1: &[f64], values2: &[f64], period: usize) -> Vec<f64> {
    // 使用现有的 correlation 函数
    correlation(values1, values2, period)
}

/// LINEARREG - Linear Regression (end point value)
///
/// 线性回归（返回回归线的终点值）
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - 线性回归值序列
pub fn linearreg(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut result = init_result!(n);

    if period < 2 || period > n {
        return result;
    }

    let x_end = (period - 1) as f64;
    rolling_linreg_apply(values, period, |i, computed| {
        if let Some(stats) = computed {
            result[i] = stats.intercept + stats.slope * x_end;
        }
    });

    result
}

/// LINEARREG_SLOPE - Linear Regression Slope
///
/// 线性回归斜率
pub fn linearreg_slope(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut result = init_result!(n);

    if period < 2 || period > n {
        return result;
    }

    rolling_linreg_apply(values, period, |i, computed| {
        if let Some(stats) = computed {
            result[i] = stats.slope;
        }
    });

    result
}

/// LINEARREG_ANGLE - Linear Regression Angle (in degrees)
///
/// 线性回归角度（度数）
pub fn linearreg_angle(values: &[f64], period: usize) -> Vec<f64> {
    let slopes = linearreg_slope(values, period);
    slopes
        .iter()
        .map(|&slope| {
            if slope.is_nan() {
                f64::NAN
            } else {
                slope.atan().to_degrees()
            }
        })
        .collect()
}

/// LINEARREG_INTERCEPT - Linear Regression Intercept
///
/// 线性回归截距
pub fn linearreg_intercept(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut result = init_result!(n);

    if period < 2 || period > n {
        return result;
    }

    rolling_linreg_apply(values, period, |i, computed| {
        if let Some(stats) = computed {
            result[i] = stats.intercept;
        }
    });

    result
}

/// VAR - Variance
///
/// 方差
///
/// Uses Kahan summation for improved precision when period >= threshold.
pub fn var(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut result = init_result!(n);

    if period < 2 || period > n {
        return result;
    }

    const RECALC_INTERVAL: usize = 1000;

    #[inline]
    fn kahan_add(sum: &mut f64, compensation: &mut f64, value: f64) {
        let y = value - *compensation;
        let t = *sum + y;
        *compensation = (t - *sum) - y;
        *sum = t;
    }

    let period_f = period as f64;
    let denom = period_f * period_f;
    let mut sum = 0.0;
    let mut sum_comp = 0.0;
    let mut sum_sq = 0.0;
    let mut sum_sq_comp = 0.0;
    let mut nan_count = 0usize;

    // 初始窗口
    for &raw in values.iter().take(period) {
        if raw.is_nan() {
            nan_count += 1;
        }

        let v = if raw.is_nan() { 0.0 } else { raw };
        kahan_add(&mut sum, &mut sum_comp, v);
        kahan_add(&mut sum_sq, &mut sum_sq_comp, v * v);
    }

    let mut steps_since_recalc = 0usize;

    for i in (period - 1)..n {
        if i >= period {
            if steps_since_recalc >= RECALC_INTERVAL {
                sum = 0.0;
                sum_comp = 0.0;
                sum_sq = 0.0;
                sum_sq_comp = 0.0;
                nan_count = 0;

                let start = i + 1 - period;
                for &raw in &values[start..=i] {
                    if raw.is_nan() {
                        nan_count += 1;
                    }

                    let v = if raw.is_nan() { 0.0 } else { raw };
                    kahan_add(&mut sum, &mut sum_comp, v);
                    kahan_add(&mut sum_sq, &mut sum_sq_comp, v * v);
                }

                steps_since_recalc = 0;
            } else {
                let old_raw = values[i - period];
                if old_raw.is_nan() {
                    nan_count = nan_count.saturating_sub(1);
                }

                let new_raw = values[i];
                if new_raw.is_nan() {
                    nan_count += 1;
                }

                let old_v = if old_raw.is_nan() { 0.0 } else { old_raw };
                let new_v = if new_raw.is_nan() { 0.0 } else { new_raw };

                kahan_add(&mut sum, &mut sum_comp, -old_v);
                kahan_add(&mut sum, &mut sum_comp, new_v);
                kahan_add(&mut sum_sq, &mut sum_sq_comp, -(old_v * old_v));
                kahan_add(&mut sum_sq, &mut sum_sq_comp, new_v * new_v);

                steps_since_recalc += 1;
            }
        }

        if nan_count > 0 {
            result[i] = f64::NAN;
            continue;
        }

        let var_num = period_f * sum_sq - sum * sum;
        if var_num.is_finite() {
            result[i] = if var_num > 0.0 { var_num / denom } else { 0.0 };
        } else {
            result[i] = f64::NAN;
        }
    }

    result
}

/// VAR_PRECISE - High-precision Variance (always uses Kahan summation)
///
/// 高精度方差计算，始终使用 Kahan 求和
///
/// Use this for ML feature calculations and other precision-critical paths.
/// Slightly slower but provides better numerical stability.
pub fn var_precise(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut result = init_result!(n);

    if period < 2 || period > n {
        return result;
    }

    const RECALC_INTERVAL: usize = 1000;

    let period_f = period as f64;
    let mut mean = 0.0;
    let mut m2 = 0.0;
    let mut nan_count = 0usize;

    for (i, &raw) in values.iter().take(period).enumerate() {
        if raw.is_nan() {
            nan_count += 1;
        }

        let value = if raw.is_nan() { 0.0 } else { raw };
        let delta = value - mean;
        mean += delta / (i + 1) as f64;
        let delta2 = value - mean;
        m2 += delta * delta2;
    }

    if nan_count == 0 {
        result[period - 1] = if m2.is_finite() {
            if m2 > 0.0 {
                m2 / period_f
            } else {
                0.0
            }
        } else {
            f64::NAN
        };
    }

    for i in period..n {
        if (i - period + 1) % RECALC_INTERVAL == 0 {
            mean = 0.0;
            m2 = 0.0;
            nan_count = 0;

            let start = i + 1 - period;
            for (j, &raw) in values[start..=i].iter().enumerate() {
                if raw.is_nan() {
                    nan_count += 1;
                }

                let value = if raw.is_nan() { 0.0 } else { raw };
                let delta = value - mean;
                mean += delta / (j + 1) as f64;
                let delta2 = value - mean;
                m2 += delta * delta2;
            }
        } else {
            let old_raw = values[i - period];
            if old_raw.is_nan() {
                nan_count = nan_count.saturating_sub(1);
            }

            let new_raw = values[i];
            if new_raw.is_nan() {
                nan_count += 1;
            }

            let old_val = if old_raw.is_nan() { 0.0 } else { old_raw };
            let new_val = if new_raw.is_nan() { 0.0 } else { new_raw };

            let old_mean = mean;
            mean = (period_f * mean - old_val) / (period_f - 1.0);
            m2 -= (old_val - mean) * (old_val - old_mean);

            let delta = new_val - mean;
            mean = (mean * (period_f - 1.0) + new_val) / period_f;
            let delta2 = new_val - mean;
            m2 += delta * delta2;
        }

        result[i] = if nan_count == 0 && m2.is_finite() {
            if m2 > 0.0 {
                m2 / period_f
            } else {
                0.0
            }
        } else {
            f64::NAN
        };
    }

    result
}

/// STDEV_PRECISE - High-precision Standard Deviation (always uses Kahan summation)
///
/// 高精度标准差计算，始终使用 Kahan 求和
///
/// Use this for ML feature calculations and other precision-critical paths.
pub fn stdev_precise(values: &[f64], period: usize) -> Vec<f64> {
    let mut vars = var_precise(values, period);
    for v in &mut vars {
        if !v.is_nan() {
            *v = v.sqrt();
        }
    }
    vars
}

/// TSF - Time Series Forecast
///
/// 时间序列预测（线性回归外推到下一个点）
pub fn tsf(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut result = init_result!(n);

    if period < 2 || period > n {
        return result;
    }

    let x_next = period as f64;
    rolling_linreg_apply(values, period, |i, computed| {
        if let Some(stats) = computed {
            result[i] = stats.intercept + stats.slope * x_next;
        }
    });

    result
}

// ==================== 浮点误差校准测试 ====================

#[cfg(test)]
mod floating_point_error_tests {
    use super::*;

    /// 测试 rolling_sum 使用 Kahan 算法在大数据集上的数值精度
    /// 验证 Kahan 补偿和定期重新计算机制能有效控制累积误差
    #[test]
    fn test_rolling_sum_large_dataset_precision() {
        const N: usize = 100_000;
        const PERIOD: usize = 20;

        // 生成测试数据：使用可能导致浮点误差累积的值
        let values: Vec<f64> = (0..N)
            .map(|i| {
                // 使用不同量级的值来加剧浮点误差
                let base = 1000.0 + (i as f64) * 0.001;
                // 添加小的波动
                base + 0.0001 * ((i * 7) % 11) as f64
            })
            .collect();

        let result = rolling_sum(&values, PERIOD);

        // 在多个点验证结果精度
        let test_indices = [
            PERIOD - 1, // 第一个有效结果
            1000,       // 第一次重新计算后
            2000,       // 第二次重新计算后
            50_000,     // 中间点
            N - 1,      // 最后一个点
        ];

        for &i in &test_indices {
            if (PERIOD - 1..N).contains(&i) {
                // 使用 Kahan 求和计算期望值（更精确）
                let expected = kahan_sum(&values[i + 1 - PERIOD..=i]);
                let actual = result[i];

                // Kahan 算法应该提供 < 1e-12 的相对误差
                let relative_error = if expected.abs() > 1e-10 {
                    (actual - expected).abs() / expected.abs()
                } else {
                    (actual - expected).abs()
                };

                assert!(
                    relative_error < 1e-12,
                    "rolling_sum_kahan 在索引 {i} 处精度不足: expected={expected}, actual={actual}, relative_error={relative_error}",
                );
            }
        }
    }

    /// 测试 rolling_sum_kahan 与原始实现的精度对比
    #[test]
    fn test_rolling_sum_kahan_vs_naive() {
        const N: usize = 50_000;
        const PERIOD: usize = 10;

        // 使用容易产生浮点误差的数据
        let values: Vec<f64> = (0..N).map(|i| 1.0 + 1e-10 * (i as f64)).collect();

        // Kahan 版本
        let kahan_result = rolling_sum_kahan(&values, PERIOD);

        // 纯增量版本（用于对比）
        let mut naive_result = vec![f64::NAN; N];
        let first_sum: f64 = values[..PERIOD].iter().sum();
        naive_result[PERIOD - 1] = first_sum;
        for i in PERIOD..N {
            naive_result[i] = naive_result[i - 1] + values[i] - values[i - PERIOD];
        }

        // 在最后一个点比较误差
        let expected = kahan_sum(&values[N - PERIOD..N]);

        let kahan_error = (kahan_result[N - 1] - expected).abs();
        let naive_error = (naive_result[N - 1] - expected).abs();

        // Kahan 应该显著优于 naive 或至少相当
        assert!(
            kahan_error <= naive_error * 1.1,
            "Kahan 误差 ({kahan_error}) 应 <= naive 误差 ({naive_error})",
        );

        // Kahan 的相对误差应在可接受范围内
        let relative_error = kahan_error / expected.abs();
        assert!(
            relative_error < 1e-12,
            "Kahan 相对误差 ({relative_error}) 应 < 1e-12",
        );
    }

    /// 测试性能影响：定期重新计算不应显著影响性能
    #[test]
    fn test_rolling_sum_performance_impact() {
        const N: usize = 100_000;
        const PERIOD: usize = 50;

        let values: Vec<f64> = (0..N).map(|i| i as f64).collect();

        // 多次运行以获得稳定的时间测量
        let start = std::time::Instant::now();
        for _ in 0..10 {
            let _ = rolling_sum(&values, PERIOD);
        }
        let elapsed = start.elapsed();

        // 每次运行应在合理时间内完成（50ms 以内对于 100k 元素）
        let per_run_ms = elapsed.as_millis() as f64 / 10.0;
        assert!(
            per_run_ms < 50.0,
            "rolling_sum 每次运行时间 ({per_run_ms:.2}ms) 超过预期",
        );
    }

    /// 测试边界条件：周期等于数据长度
    #[test]
    fn test_rolling_sum_edge_case_period_equals_length() {
        let values: Vec<f64> = (0..1000).map(|i| i as f64).collect();
        let result = rolling_sum(&values, 1000);

        // 只有最后一个值应该有效
        assert!(result[998].is_nan());
        let expected: f64 = values.iter().sum();
        assert!((result[999] - expected).abs() < 1e-10);
    }

    /// 测试边界条件：周期为 1
    #[test]
    fn test_rolling_sum_edge_case_period_one() {
        let values: Vec<f64> = (0..100).map(|i| i as f64 + 0.5).collect();
        let result = rolling_sum(&values, 1);

        for i in 0..100 {
            assert!(
                (result[i] - values[i]).abs() < 1e-15,
                "周期为 1 时，结果应等于输入值"
            );
        }
    }
}
