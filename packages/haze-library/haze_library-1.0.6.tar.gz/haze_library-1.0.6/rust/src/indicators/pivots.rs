// indicators/pivots.rs - Pivot Points（枢轴点）
#![allow(dead_code)]
//
// Pivot Points 是基于前一周期（通常是日）的高低收盘价计算的支撑/阻力位
// 包含多种计算方法：
// - Standard (Classic) Pivots：经典枢轴点
// - Fibonacci Pivots：基于 Fibonacci 比率
// - Woodie Pivots：更重视收盘价
// - Camarilla Pivots：短线交易者常用
// - DeMark Pivots：考虑开盘价与收盘价关系

use std::collections::HashMap;

use crate::errors::validation::{validate_lengths_match, validate_not_empty, validate_range};
use crate::errors::{HazeError, HazeResult};
use crate::utils::math::is_zero;

/// Pivot 计算结果结构体
#[derive(Debug, Clone)]
pub struct PivotLevels {
    pub pivot: f64,      // 枢轴点（PP）
    pub r1: f64,         // 阻力位 1
    pub r2: f64,         // 阻力位 2
    pub r3: f64,         // 阻力位 3
    pub r4: Option<f64>, // 阻力位 4（Camarilla 专用）
    pub s1: f64,         // 支撑位 1
    pub s2: f64,         // 支撑位 2
    pub s3: f64,         // 支撑位 3
    pub s4: Option<f64>, // 支撑位 4（Camarilla 专用）
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
fn validate_pivot_levels(levels: &PivotLevels) -> HazeResult<()> {
    let values = [
        ("pivot", levels.pivot),
        ("r1", levels.r1),
        ("r2", levels.r2),
        ("r3", levels.r3),
        ("s1", levels.s1),
        ("s2", levels.s2),
        ("s3", levels.s3),
    ];
    for (name, value) in values {
        if value.is_nan() {
            continue;
        }
        validate_finite_value(value, name)?;
    }
    if let Some(r4) = levels.r4 {
        validate_finite_value(r4, "r4")?;
    }
    if let Some(s4) = levels.s4 {
        validate_finite_value(s4, "s4")?;
    }
    Ok(())
}

/// 标准枢轴点（Standard/Classic Pivots）
///
/// - `high`: 前一周期高价
/// - `low`: 前一周期低价
/// - `close`: 前一周期收盘价
///
/// 返回：PivotLevels 结构体
///
/// # 算法
/// ```text
/// PP = (H + L + C) / 3
/// R1 = 2*PP - L
/// R2 = PP + (H - L)
/// R3 = H + 2*(PP - L)
/// S1 = 2*PP - H
/// S2 = PP - (H - L)
/// S3 = L - 2*(H - PP)
/// ```
pub fn standard_pivots(high: f64, low: f64, close: f64) -> HazeResult<PivotLevels> {
    validate_finite_value(high, "high")?;
    validate_finite_value(low, "low")?;
    validate_finite_value(close, "close")?;
    let pp = (high + low + close) / 3.0;
    let range = high - low;

    let r1 = 2.0 * pp - low;
    let r2 = pp + range;
    let r3 = high + 2.0 * (pp - low);

    let s1 = 2.0 * pp - high;
    let s2 = pp - range;
    let s3 = low - 2.0 * (high - pp);

    Ok(PivotLevels {
        pivot: pp,
        r1,
        r2,
        r3,
        r4: None,
        s1,
        s2,
        s3,
        s4: None,
    })
}

/// Fibonacci 枢轴点
///
/// - `high`: 前一周期高价
/// - `low`: 前一周期低价
/// - `close`: 前一周期收盘价
///
/// 返回：PivotLevels 结构体
///
/// # 算法
/// ```text
/// PP = (H + L + C) / 3
/// R1 = PP + 0.382 * (H - L)
/// R2 = PP + 0.618 * (H - L)
/// R3 = PP + 1.000 * (H - L)
/// S1 = PP - 0.382 * (H - L)
/// S2 = PP - 0.618 * (H - L)
/// S3 = PP - 1.000 * (H - L)
/// ```
pub fn fibonacci_pivots(high: f64, low: f64, close: f64) -> HazeResult<PivotLevels> {
    validate_finite_value(high, "high")?;
    validate_finite_value(low, "low")?;
    validate_finite_value(close, "close")?;
    let pp = (high + low + close) / 3.0;
    let range = high - low;

    let r1 = pp + 0.382 * range;
    let r2 = pp + 0.618 * range;
    let r3 = pp + 1.000 * range;

    let s1 = pp - 0.382 * range;
    let s2 = pp - 0.618 * range;
    let s3 = pp - 1.000 * range;

    Ok(PivotLevels {
        pivot: pp,
        r1,
        r2,
        r3,
        r4: None,
        s1,
        s2,
        s3,
        s4: None,
    })
}

/// Woodie 枢轴点
///
/// - `high`: 前一周期高价
/// - `low`: 前一周期低价
/// - `close`: 前一周期收盘价
///
/// 返回：PivotLevels 结构体
///
/// # 算法
/// ```text
/// PP = (H + L + 2*C) / 4  （更重视收盘价）
/// R1 = 2*PP - L
/// R2 = PP + (H - L)
/// S1 = 2*PP - H
/// S2 = PP - (H - L)
/// ```
pub fn woodie_pivots(high: f64, low: f64, close: f64) -> HazeResult<PivotLevels> {
    validate_finite_value(high, "high")?;
    validate_finite_value(low, "low")?;
    validate_finite_value(close, "close")?;
    let pp = (high + low + 2.0 * close) / 4.0;
    let range = high - low;

    let r1 = 2.0 * pp - low;
    let r2 = pp + range;
    let r3 = high + 2.0 * (pp - low); // R3 同标准计算

    let s1 = 2.0 * pp - high;
    let s2 = pp - range;
    let s3 = low - 2.0 * (high - pp); // S3 同标准计算

    Ok(PivotLevels {
        pivot: pp,
        r1,
        r2,
        r3,
        r4: None,
        s1,
        s2,
        s3,
        s4: None,
    })
}

/// Camarilla 枢轴点（短线交易者常用）
///
/// - `high`: 前一周期高价
/// - `low`: 前一周期低价
/// - `close`: 前一周期收盘价
///
/// 返回：PivotLevels 结构体
///
/// # 算法
/// ```text
/// PP = (H + L + C) / 3
/// R1 = C + 1.1/12 * (H - L)
/// R2 = C + 1.1/6 * (H - L)
/// R3 = C + 1.1/4 * (H - L)
/// R4 = C + 1.1/2 * (H - L)
/// S1 = C - 1.1/12 * (H - L)
/// S2 = C - 1.1/6 * (H - L)
/// S3 = C - 1.1/4 * (H - L)
/// S4 = C - 1.1/2 * (H - L)
/// ```
pub fn camarilla_pivots(high: f64, low: f64, close: f64) -> HazeResult<PivotLevels> {
    validate_finite_value(high, "high")?;
    validate_finite_value(low, "low")?;
    validate_finite_value(close, "close")?;
    let pp = (high + low + close) / 3.0;
    let range = high - low;

    let r1 = close + 1.1 / 12.0 * range;
    let r2 = close + 1.1 / 6.0 * range;
    let r3 = close + 1.1 / 4.0 * range;
    let r4 = close + 1.1 / 2.0 * range;

    let s1 = close - 1.1 / 12.0 * range;
    let s2 = close - 1.1 / 6.0 * range;
    let s3 = close - 1.1 / 4.0 * range;
    let s4 = close - 1.1 / 2.0 * range;

    Ok(PivotLevels {
        pivot: pp,
        r1,
        r2,
        r3,
        r4: Some(r4),
        s1,
        s2,
        s3,
        s4: Some(s4),
    })
}

/// DeMark 枢轴点
///
/// - `open`: 前一周期开盘价
/// - `high`: 前一周期高价
/// - `low`: 前一周期低价
/// - `close`: 前一周期收盘价
///
/// 返回：PivotLevels 结构体
///
/// # 算法
/// ```text
/// 如果 Close < Open: X = H + 2*L + C
/// 如果 Close > Open: X = 2*H + L + C
/// 如果 Close = Open: X = H + L + 2*C
/// PP = X / 4
/// R1 = X/2 - L
/// S1 = X/2 - H
/// ```
pub fn demark_pivots(open: f64, high: f64, low: f64, close: f64) -> HazeResult<PivotLevels> {
    validate_finite_value(open, "open")?;
    validate_finite_value(high, "high")?;
    validate_finite_value(low, "low")?;
    validate_finite_value(close, "close")?;
    let x = if close < open {
        high + 2.0 * low + close
    } else if close > open {
        2.0 * high + low + close
    } else {
        high + low + 2.0 * close
    };

    let pp = x / 4.0;
    let r1 = x / 2.0 - low;
    let s1 = x / 2.0 - high;

    // DeMark 通常只有 R1/S1，其余设为 NaN
    Ok(PivotLevels {
        pivot: pp,
        r1,
        r2: f64::NAN,
        r3: f64::NAN,
        r4: None,
        s1,
        s2: f64::NAN,
        s3: f64::NAN,
        s4: None,
    })
}

/// 计算时间序列的 Pivot Points
///
/// 为每个周期计算枢轴点（通常用于日线数据，每日计算一次）
///
/// - `open`: 开盘价序列（仅 DeMark 需要）
/// - `high`: 高价序列
/// - `low`: 低价序列
/// - `close`: 收盘价序列
/// - `method`: 计算方法（"standard", "fibonacci", "woodie", "camarilla", "demark"）
///
/// 返回：每个周期的 PivotLevels 向量
pub fn calc_pivot_series(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    method: &str,
) -> HazeResult<Vec<PivotLevels>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;
    if method.trim().is_empty() {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: "method cannot be empty".to_string(),
        });
    }
    let n = high.len();
    let mut pivots = Vec::with_capacity(n);

    for i in 0..n {
        if i == 0 {
            // 第一个周期没有前一周期数据，使用当前数据
            pivots.push(calc_single_pivot(
                open[i], high[i], low[i], close[i], method,
            )?);
        } else {
            // 使用前一周期的数据计算当前枢轴点
            pivots.push(calc_single_pivot(
                open[i - 1],
                high[i - 1],
                low[i - 1],
                close[i - 1],
                method,
            )?);
        }
    }

    Ok(pivots)
}

/// 计算单个 Pivot（辅助函数）
fn calc_single_pivot(
    open: f64,
    high: f64,
    low: f64,
    close: f64,
    method: &str,
) -> HazeResult<PivotLevels> {
    match method.to_lowercase().as_str() {
        "standard" | "classic" => standard_pivots(high, low, close),
        "fibonacci" | "fib" => fibonacci_pivots(high, low, close),
        "woodie" | "woodies" => woodie_pivots(high, low, close),
        "camarilla" => camarilla_pivots(high, low, close),
        "demark" | "dm" => demark_pivots(open, high, low, close),
        _ => Err(HazeError::InvalidValue {
            index: 0,
            message: format!("unknown pivot method: {method}"),
        }),
    }
}

/// 检测价格是否触及 Pivot 位
///
/// - `current_price`: 当前价格
/// - `pivot_levels`: Pivot 价位
/// - `tolerance`: 触及容差（百分比）
///
/// 返回：触及的价位名称（如 "R1", "S2", "PP"），如果未触及则返回 None
pub fn detect_pivot_touch(
    current_price: f64,
    pivot_levels: &PivotLevels,
    tolerance: f64,
) -> HazeResult<Option<String>> {
    validate_finite_value(current_price, "current_price")?;
    validate_range("tolerance", tolerance, 0.0, f64::INFINITY)?;
    validate_pivot_levels(pivot_levels)?;
    let mut levels = HashMap::new();
    levels.insert("PP", pivot_levels.pivot);
    levels.insert("R1", pivot_levels.r1);
    levels.insert("R2", pivot_levels.r2);
    levels.insert("R3", pivot_levels.r3);
    levels.insert("S1", pivot_levels.s1);
    levels.insert("S2", pivot_levels.s2);
    levels.insert("S3", pivot_levels.s3);

    if let Some(r4) = pivot_levels.r4 {
        levels.insert("R4", r4);
    }
    if let Some(s4) = pivot_levels.s4 {
        levels.insert("S4", s4);
    }

    // 找出最接近的 Pivot 位
    for (name, &level) in &levels {
        if level.is_nan() {
            continue;
        }
        if is_zero(level) {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: format!("pivot level {name} is zero"),
            });
        }
        let diff_pct = ((current_price - level) / level).abs();
        if diff_pct <= tolerance {
            return Ok(Some(name.to_string()));
        }
    }

    Ok(None)
}

/// 判断价格位于 Pivot 哪个区域
///
/// - `current_price`: 当前价格
/// - `pivot_levels`: Pivot 价位
///
/// 返回：价格所在区域（"Above R3", "R2-R3", "R1-R2", "PP-R1", "PP-S1", "S1-S2", "S2-S3", "Below S3"）
pub fn pivot_zone(current_price: f64, pivot_levels: &PivotLevels) -> HazeResult<String> {
    validate_finite_value(current_price, "current_price")?;
    validate_pivot_levels(pivot_levels)?;
    for (name, value) in [
        ("r3", pivot_levels.r3),
        ("r2", pivot_levels.r2),
        ("r1", pivot_levels.r1),
        ("pivot", pivot_levels.pivot),
        ("s1", pivot_levels.s1),
        ("s2", pivot_levels.s2),
        ("s3", pivot_levels.s3),
    ] {
        if value.is_nan() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: format!("pivot level {name} is NaN; pivot_zone requires full levels"),
            });
        }
    }
    if current_price > pivot_levels.r3 {
        Ok("Above R3".to_string())
    } else if current_price > pivot_levels.r2 {
        Ok("R2-R3".to_string())
    } else if current_price > pivot_levels.r1 {
        Ok("R1-R2".to_string())
    } else if current_price > pivot_levels.pivot {
        Ok("PP-R1".to_string())
    } else if current_price > pivot_levels.s1 {
        Ok("PP-S1".to_string())
    } else if current_price > pivot_levels.s2 {
        Ok("S1-S2".to_string())
    } else if current_price > pivot_levels.s3 {
        Ok("S2-S3".to_string())
    } else {
        Ok("Below S3".to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_standard_pivots() {
        let high = 110.0;
        let low = 100.0;
        let close = 105.0;

        let pivots = standard_pivots(high, low, close).unwrap();

        // PP = (110 + 100 + 105) / 3 = 105
        assert!((pivots.pivot - 105.0).abs() < 0.1);

        // R1 = 2*105 - 100 = 110
        assert!((pivots.r1 - 110.0).abs() < 0.1);

        // S1 = 2*105 - 110 = 100
        assert!((pivots.s1 - 100.0).abs() < 0.1);
    }

    #[test]
    fn test_fibonacci_pivots() {
        let high = 110.0;
        let low = 100.0;
        let close = 105.0;

        let pivots = fibonacci_pivots(high, low, close).unwrap();

        // PP = 105
        assert!((pivots.pivot - 105.0).abs() < 0.1);

        // R1 = 105 + 0.382 * 10 = 108.82
        assert!((pivots.r1 - 108.82).abs() < 0.1);

        // S1 = 105 - 0.382 * 10 = 101.18
        assert!((pivots.s1 - 101.18).abs() < 0.1);
    }

    #[test]
    fn test_camarilla_pivots() {
        let high = 110.0;
        let low = 100.0;
        let close = 105.0;

        let pivots = camarilla_pivots(high, low, close).unwrap();

        // 验证有 R4/S4
        assert!(pivots.r4.is_some());
        assert!(pivots.s4.is_some());

        // R1 = 105 + 1.1/12 * 10 ≈ 105.917
        assert!((pivots.r1 - 105.917).abs() < 0.01);
    }

    #[test]
    fn test_demark_pivots() {
        let open = 102.0;
        let high = 110.0;
        let low = 100.0;
        let close = 108.0;

        let pivots = demark_pivots(open, high, low, close).unwrap();

        // Close > Open: X = 2*110 + 100 + 108 = 428
        // PP = 428 / 4 = 107
        assert!((pivots.pivot - 107.0).abs() < 0.1);

        // R1 = 428/2 - 100 = 114
        assert!((pivots.r1 - 114.0).abs() < 0.1);
    }

    #[test]
    fn test_pivot_zone() {
        let high = 110.0;
        let low = 100.0;
        let close = 105.0;

        let pivots = standard_pivots(high, low, close).unwrap();

        // 价格 112 应在 R1-R2 区域
        let zone = pivot_zone(112.0, &pivots).unwrap();
        assert_eq!(zone, "R1-R2");

        // 价格 103 应在 PP-S1 区域
        let zone = pivot_zone(103.0, &pivots).unwrap();
        assert_eq!(zone, "PP-S1");
    }
}
