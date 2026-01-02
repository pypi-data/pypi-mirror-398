// indicators/fibonacci.rs - Fibonacci 回撤与扩展
//
// 提供 Fibonacci 比率计算和关键价位标记
// - Retracement Levels（回撤位）：0.236, 0.382, 0.5, 0.618, 0.786
// - Extension Levels（扩展位）：1.272, 1.414, 1.618, 2.0, 2.618
#![allow(dead_code)]

use std::collections::HashMap;

use crate::errors::validation::{validate_not_empty, validate_range};
use crate::errors::{HazeError, HazeResult};
use crate::utils::math::is_zero;

/// Fibonacci Retracement Levels（回撤位）
pub struct FibonacciRetracement {
    pub start_price: f64,
    pub end_price: f64,
    pub levels: HashMap<String, f64>, // "0.382" -> price
}

/// Fibonacci Extension Levels（扩展位）
pub struct FibonacciExtension {
    pub start_price: f64,
    pub end_price: f64,
    pub levels: HashMap<String, f64>,
}

#[inline]
fn validate_finite_value(value: f64, name: &'static str) -> HazeResult<()> {
    if !value.is_finite() {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("{name} contains non-finite value: {value}"),
        });
    }
    Ok(())
}

#[inline]
fn validate_ratios(ratios: &[f64], name: &'static str) -> HazeResult<()> {
    for (idx, ratio) in ratios.iter().enumerate() {
        if !ratio.is_finite() {
            return Err(HazeError::InvalidValue {
                index: idx,
                message: format!("{name} contains non-finite value: {ratio}"),
            });
        }
    }
    Ok(())
}

/// 标准 Fibonacci 回撤比率
pub const FIB_RETRACEMENT_RATIOS: [f64; 7] = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];

/// 标准 Fibonacci 扩展比率
pub const FIB_EXTENSION_RATIOS: [f64; 6] = [1.272, 1.414, 1.618, 2.0, 2.618, 3.618];

/// 计算 Fibonacci 回撤位
///
/// - `start_price`: 起始价格（趋势起点）
/// - `end_price`: 结束价格（趋势终点）
/// - `custom_ratios`: 可选的自定义比率（如为 None 则使用标准比率）
///
/// 返回：回撤价位映射
///
/// # 示例
/// ```rust
/// use haze_library::indicators::fibonacci::fib_retracement;
///
/// let start = 100.0;
/// let end = 150.0;
/// let retracement = fib_retracement(start, end, None);
/// // 0.618 回撤位 = 150 - (150-100)*0.618 = 119.1
/// ```
pub fn fib_retracement(
    start_price: f64,
    end_price: f64,
    custom_ratios: Option<&[f64]>,
) -> HazeResult<FibonacciRetracement> {
    validate_finite_value(start_price, "start_price")?;
    validate_finite_value(end_price, "end_price")?;
    if let Some(ratios) = custom_ratios {
        validate_ratios(ratios, "custom_ratios")?;
    }
    let ratios = custom_ratios.unwrap_or(&FIB_RETRACEMENT_RATIOS);
    let price_range = end_price - start_price;

    let mut levels = HashMap::new();

    for &ratio in ratios {
        let level_price = end_price - (price_range * ratio);
        levels.insert(format!("{ratio:.3}"), level_price);
    }

    Ok(FibonacciRetracement {
        start_price,
        end_price,
        levels,
    })
}

/// 计算 Fibonacci 扩展位
///
/// - `start_price`: 起始价格（A 点）
/// - `end_price`: 结束价格（B 点）
/// - `retracement_price`: 回撤价格（C 点）
/// - `custom_ratios`: 可选的自定义比率
///
/// 返回：扩展价位映射
///
/// # 算法
/// Extension = C + (B - A) * ratio
///
/// # 示例
/// ```rust
/// use haze_library::indicators::fibonacci::fib_extension;
///
/// let a = 100.0;  // 起点
/// let b = 150.0;  // 高点
/// let c = 130.0;  // 回撤点
/// let extension = fib_extension(a, b, c, None);
/// // 1.618 扩展位 = 130 + (150-100)*1.618 = 210.9
/// ```
pub fn fib_extension(
    start_price: f64,
    end_price: f64,
    retracement_price: f64,
    custom_ratios: Option<&[f64]>,
) -> HazeResult<FibonacciExtension> {
    validate_finite_value(start_price, "start_price")?;
    validate_finite_value(end_price, "end_price")?;
    validate_finite_value(retracement_price, "retracement_price")?;
    if let Some(ratios) = custom_ratios {
        validate_ratios(ratios, "custom_ratios")?;
    }
    let ratios = custom_ratios.unwrap_or(&FIB_EXTENSION_RATIOS);
    let initial_move = end_price - start_price;

    let mut levels = HashMap::new();

    for &ratio in ratios {
        let level_price = retracement_price + (initial_move * ratio);
        levels.insert(format!("{ratio:.3}"), level_price);
    }

    Ok(FibonacciExtension {
        start_price,
        end_price,
        levels,
    })
}

/// 计算动态 Fibonacci 回撤（基于价格序列）
///
/// 自动检测最近的趋势（高点→低点 或 低点→高点），然后计算回撤位
///
/// - `prices`: 价格序列（通常是 close）
/// - `lookback`: 回溯周期（检测趋势的窗口）
///
/// 返回：每个价格对应的回撤位向量（7 个回撤位 * n 个价格点）
pub fn dynamic_fib_retracement(
    prices: &[f64],
    lookback: usize,
) -> HazeResult<Vec<HashMap<String, f64>>> {
    validate_not_empty(prices, "prices")?;
    let n = prices.len();
    if lookback == 0 || lookback >= n {
        return Err(HazeError::InvalidPeriod {
            period: lookback,
            data_len: n.saturating_sub(1),
        });
    }
    let mut results = Vec::with_capacity(n);

    for i in 0..n {
        if i < lookback {
            // 数据不足，返回空 HashMap
            results.push(HashMap::new());
            continue;
        }

        let window = &prices[i - lookback..=i];
        let start_idx = window
            .iter()
            .enumerate()
            .min_by(|a, b| a.1.total_cmp(b.1))
            .unwrap()
            .0;
        let end_idx = window
            .iter()
            .enumerate()
            .max_by(|a, b| a.1.total_cmp(b.1))
            .unwrap()
            .0;

        let (start_price, end_price) = if start_idx < end_idx {
            // 上升趋势（低→高）
            (window[start_idx], window[end_idx])
        } else {
            // 下降趋势（高→低）
            (window[end_idx], window[start_idx])
        };

        let fib = fib_retracement(start_price, end_price, None)?;
        results.push(fib.levels);
    }

    Ok(results)
}

/// 检测价格是否触及 Fibonacci 关键位（支撑/阻力）
///
/// - `current_price`: 当前价格
/// - `fib_levels`: Fibonacci 价位映射
/// - `tolerance`: 触及容差（百分比，如 0.001 表示 0.1%）
///
/// 返回：触及的 Fibonacci 比率（如 "0.618"），如果未触及则返回 None
pub fn detect_fib_touch(
    current_price: f64,
    fib_levels: &HashMap<String, f64>,
    tolerance: f64,
) -> HazeResult<Option<String>> {
    validate_finite_value(current_price, "current_price")?;
    validate_range("tolerance", tolerance, 0.0, f64::INFINITY)?;
    if fib_levels.is_empty() {
        return Err(HazeError::EmptyInput { name: "fib_levels" });
    }
    for (ratio, &level_price) in fib_levels {
        if !level_price.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: format!("fib_levels contains non-finite value: {level_price}"),
            });
        }
        if is_zero(level_price) {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "fib_levels contains zero price level".to_string(),
            });
        }
        let diff_pct = ((current_price - level_price) / level_price).abs();
        if diff_pct <= tolerance {
            return Ok(Some(ratio.clone()));
        }
    }
    Ok(None)
}

/// 计算 Fibonacci Fan Lines（扇形线）
///
/// 扇形线基于趋势线的 Fibonacci 角度，用于动态支撑/阻力
///
/// - `start_index`: 起始 K 线索引
/// - `end_index`: 结束 K 线索引
/// - `start_price`: 起始价格
/// - `end_price`: 结束价格
/// - `target_index`: 目标索引（计算扇形线在该位置的价格）
///
/// 返回：三条扇形线的价格（0.382, 0.5, 0.618 角度）
pub fn fib_fan_lines(
    start_index: usize,
    end_index: usize,
    start_price: f64,
    end_price: f64,
    target_index: usize,
) -> HazeResult<(f64, f64, f64)> {
    validate_finite_value(start_price, "start_price")?;
    validate_finite_value(end_price, "end_price")?;
    if start_index >= end_index {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: "start_index must be < end_index".to_string(),
        });
    }
    if target_index <= end_index {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: "target_index must be > end_index".to_string(),
        });
    }

    let time_delta = (end_index - start_index) as f64;
    let price_delta = end_price - start_price;
    let target_time = (target_index - start_index) as f64;

    // 三条扇形线的 Fibonacci 角度
    let fan_382 = start_price + (price_delta * (target_time / time_delta) * 0.382);
    let fan_500 = start_price + (price_delta * (target_time / time_delta) * 0.5);
    let fan_618 = start_price + (price_delta * (target_time / time_delta) * 0.618);

    Ok((fan_382, fan_500, fan_618))
}

/// 计算 Fibonacci Time Zones（时间区域）
///
/// 基于 Fibonacci 数列标记关键时间点：1, 2, 3, 5, 8, 13, 21, 34, 55, 89...
///
/// - `start_index`: 起始索引
/// - `max_zones`: 最大时间区域数量
///
/// 返回：Fibonacci 时间索引向量
pub fn fib_time_zones(start_index: usize, max_zones: usize) -> HazeResult<Vec<usize>> {
    if max_zones == 0 {
        return Err(HazeError::InvalidPeriod {
            period: max_zones,
            data_len: 1,
        });
    }
    let fib_sequence = generate_fibonacci_sequence(max_zones)?;
    let mut zones = Vec::with_capacity(fib_sequence.len());
    for fib in fib_sequence {
        let idx = start_index
            .checked_add(fib)
            .ok_or_else(|| HazeError::InvalidValue {
                index: 0,
                message: "fib_time_zones index overflow".to_string(),
            })?;
        zones.push(idx);
    }
    Ok(zones)
}

/// 生成 Fibonacci 数列
fn generate_fibonacci_sequence(n: usize) -> HazeResult<Vec<usize>> {
    if n == 0 {
        return Err(HazeError::InvalidPeriod {
            period: n,
            data_len: 1,
        });
    }
    if n == 1 {
        return Ok(vec![1]);
    }

    let mut seq: Vec<usize> = vec![1, 2];

    for i in 2..n {
        let next = seq[i - 1]
            .checked_add(seq[i - 2])
            .ok_or_else(|| HazeError::InvalidValue {
                index: i,
                message: "Fibonacci sequence overflow".to_string(),
            })?;
        seq.push(next);
    }

    Ok(seq)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fib_retracement() {
        let start = 100.0;
        let end = 150.0;

        let fib = fib_retracement(start, end, None).unwrap();

        // 0.618 回撤位 = 150 - (150-100)*0.618 = 119.1
        let level_618 = fib.levels.get("0.618").unwrap();
        assert!((level_618 - 119.1).abs() < 0.1);

        // 0.5 回撤位 = 125.0
        let level_50 = fib.levels.get("0.500").unwrap();
        assert!((level_50 - 125.0).abs() < 0.1);
    }

    #[test]
    fn test_fib_extension() {
        let a = 100.0;
        let b = 150.0;
        let c = 130.0;

        let ext = fib_extension(a, b, c, None).unwrap();

        // 1.618 扩展位 = 130 + (150-100)*1.618 = 210.9
        let level_1618 = ext.levels.get("1.618").unwrap();
        assert!((level_1618 - 210.9).abs() < 0.1);
    }

    #[test]
    fn test_fibonacci_sequence() {
        let seq = generate_fibonacci_sequence(8).unwrap();
        assert_eq!(seq, vec![1, 2, 3, 5, 8, 13, 21, 34]);
    }

    #[test]
    fn test_detect_fib_touch() {
        let mut levels = HashMap::new();
        levels.insert("0.618".to_string(), 119.0);
        levels.insert("0.5".to_string(), 125.0);

        // 价格 119.1 应触及 0.618 位（119.0）
        let touched = detect_fib_touch(119.1, &levels, 0.01).unwrap();
        assert!(touched.is_some());
        assert_eq!(touched.unwrap(), "0.618");

        // 价格 120.0 不触及任何位（超过 1% 容差）
        let not_touched = detect_fib_touch(120.0, &levels, 0.001).unwrap();
        assert!(not_touched.is_none());
    }
}
