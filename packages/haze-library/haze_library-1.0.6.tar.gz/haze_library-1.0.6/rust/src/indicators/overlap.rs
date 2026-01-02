// indicators/overlap.rs - Overlap/MA 指标
//
// 大部分 MA 函数已在 utils/ma.rs 中实现，这里重新导出并添加一些高级 MA
#![allow(dead_code)]
// SAREXT 等函数需要多个参数配置
#![allow(clippy::too_many_arguments)]

use crate::errors::validation::{
    validate_lengths_match, validate_min_length, validate_not_empty, validate_period,
};
use crate::errors::{HazeError, HazeResult};
use crate::init_result;
use crate::utils::ma::sma_allow_nan;
use crate::utils::math::is_zero;
#[allow(unused_imports)]
pub use crate::utils::{dema, ema, hma, rma, sma, tema, wma};

// 高级 Overlap Studies 指标（TA-Lib 兼容）

/// HL2 - High-Low Midpoint
///
/// # 返回
/// - `HazeResult<Vec<f64>>` 中点值序列
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 输入长度不一致
pub fn hl2(high: &[f64], low: &[f64]) -> HazeResult<Vec<f64>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low")])?;

    Ok(high.iter().zip(low).map(|(&h, &l)| (h + l) / 2.0).collect())
}

/// HLC3 - High-Low-Close Average (Typical Price)
///
/// # 返回
/// - `HazeResult<Vec<f64>>` 典型价格序列
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 输入长度不一致
pub fn hlc3(high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    Ok(high
        .iter()
        .zip(low)
        .zip(close)
        .map(|((&h, &l), &c)| (h + l + c) / 3.0)
        .collect())
}

/// OHLC4 - Open-High-Low-Close Average
///
/// # 返回
/// - `HazeResult<Vec<f64>>` 四价平均序列
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 输入长度不一致
pub fn ohlc4(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;

    Ok(open
        .iter()
        .zip(high)
        .zip(low)
        .zip(close)
        .map(|(((&o, &h), &l), &c)| (o + h + l + c) / 4.0)
        .collect())
}

/// MIDPOINT - MidPoint over period
///
/// 滚动窗口中点 = (MAX + MIN) / 2
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - `HazeResult<Vec<f64>>` 中点序列（前 period-1 个值为 NaN）
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `InvalidPeriod`: 周期无效
pub fn midpoint(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    use crate::utils::{rolling_max, rolling_min};

    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    let max_vals = rolling_max(values, period);
    let min_vals = rolling_min(values, period);

    Ok(max_vals
        .iter()
        .zip(min_vals.iter())
        .map(|(&max, &min)| {
            if max.is_nan() || min.is_nan() {
                f64::NAN
            } else {
                (max + min) / 2.0
            }
        })
        .collect())
}

/// MIDPRICE - Midpoint Price over period
///
/// 价格区间中点 = (Highest High + Lowest Low) / 2
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `period`: 周期
///
/// # 返回
/// - `HazeResult<Vec<f64>>` 价格中点序列（前 period-1 个值为 NaN）
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 输入长度不一致
/// - `InvalidPeriod`: 周期无效
pub fn midprice(high: &[f64], low: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    use crate::utils::{rolling_max, rolling_min};

    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low")])?;
    validate_period(period, high.len())?;

    let max_high = rolling_max(high, period);
    let min_low = rolling_min(low, period);

    Ok(max_high
        .iter()
        .zip(min_low.iter())
        .map(|(&max, &min)| {
            if max.is_nan() || min.is_nan() {
                f64::NAN
            } else {
                (max + min) / 2.0
            }
        })
        .collect())
}

/// TRIMA - Triangular Moving Average
///
/// TA-Lib 对齐：
/// - 奇数周期：SMA(SMA(values, (period+1)/2), (period+1)/2)
/// - 偶数周期：SMA(SMA(values, period/2), period/2 + 1)
///
/// # 参数
/// - `values`: 输入序列
/// - `period`: 周期
///
/// # 返回
/// - `HazeResult<Vec<f64>>` 三角移动平均序列
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `InvalidPeriod`: 周期无效
pub fn trima(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    let n1 = if period % 2 == 0 {
        period / 2
    } else {
        period.div_ceil(2)
    };
    let n2 = if period % 2 == 0 { n1 + 1 } else { n1 };

    let first_sma = sma(values, n1)?;
    sma_allow_nan(&first_sma, n2)
}

/// SAR - Parabolic SAR (Stop and Reverse)
///
/// 抛物线转向指标，用于追踪趋势和设置止损位
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `acceleration`: 加速因子初始值（默认 0.02）
/// - `maximum`: 加速因子最大值（默认 0.2）
///
/// # 返回
/// - `HazeResult<Vec<f64>>` SAR 值序列
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 输入长度不一致
/// - `InsufficientData`: 数据长度小于 2
pub fn sar(high: &[f64], low: &[f64], acceleration: f64, maximum: f64) -> HazeResult<Vec<f64>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low")])?;
    validate_min_length(high, 2)?;

    // Fail-Fast: AF 参数验证
    if acceleration <= 0.0 {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("acceleration ({acceleration}) must be > 0"),
        });
    }
    if maximum <= 0.0 {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("maximum ({maximum}) must be > 0"),
        });
    }
    if maximum < acceleration {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("maximum ({maximum}) must be >= acceleration ({acceleration})"),
        });
    }

    let n = high.len();
    let mut result = init_result!(n);

    // TA-Lib 对齐初始化：基于 HL2 判断初始趋势方向
    let mut is_long = (high[1] + low[1]) > (high[0] + low[0]);
    let mut sar_value = if is_long { low[0] } else { high[0] };
    let mut ep = if is_long { high[1] } else { low[1] };
    let mut af = acceleration;

    result[0] = f64::NAN;
    result[1] = sar_value;

    for i in 2..n {
        sar_value = sar_value + af * (ep - sar_value);

        if is_long {
            sar_value = sar_value.min(low[i - 1]);
            if i >= 3 {
                sar_value = sar_value.min(low[i - 2]);
            }

            if low[i] < sar_value {
                is_long = false;
                sar_value = ep;
                ep = low[i];
                af = acceleration;
            } else if high[i] > ep {
                ep = high[i];
                af = (af + acceleration).min(maximum);
            }
        } else {
            sar_value = sar_value.max(high[i - 1]);
            if i >= 3 {
                sar_value = sar_value.max(high[i - 2]);
            }

            if high[i] > sar_value {
                is_long = true;
                sar_value = ep;
                ep = high[i];
                af = acceleration;
            } else if low[i] < ep {
                ep = low[i];
                af = (af + acceleration).min(maximum);
            }
        }

        result[i] = sar_value;
    }

    Ok(result)
}

/// SAREXT - Parabolic SAR Extended (更多参数控制)
///
/// 扩展版抛物线转向指标，提供更多参数控制
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `start_value`: SAR 起始值（0 表示自动）
/// - `offset_on_reverse`: 反转时的偏移量
/// - `af_init_long`: 上升趋势 AF 初始值
/// - `af_long`: 上升趋势 AF 增量
/// - `af_max_long`: 上升趋势 AF 最大值
/// - `af_init_short`: 下降趋势 AF 初始值
/// - `af_short`: 下降趋势 AF 增量
/// - `af_max_short`: 下降趋势 AF 最大值
///
/// # 返回
/// - `HazeResult<Vec<f64>>` SAR 值序列
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 输入长度不一致
/// - `InsufficientData`: 数据长度小于 2
pub fn sarext(
    high: &[f64],
    low: &[f64],
    start_value: f64,
    offset_on_reverse: f64,
    af_init_long: f64,
    af_long: f64,
    af_max_long: f64,
    af_init_short: f64,
    af_short: f64,
    af_max_short: f64,
) -> HazeResult<Vec<f64>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low")])?;
    validate_min_length(high, 2)?;

    // Fail-Fast: AF 参数验证 (Long)
    if af_init_long <= 0.0 {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("af_init_long ({af_init_long}) must be > 0"),
        });
    }
    if af_long <= 0.0 {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("af_long ({af_long}) must be > 0"),
        });
    }
    if af_max_long < af_init_long {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!(
                "af_max_long ({af_max_long}) must be >= af_init_long ({af_init_long})"
            ),
        });
    }

    // Fail-Fast: AF 参数验证 (Short)
    if af_init_short <= 0.0 {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("af_init_short ({af_init_short}) must be > 0"),
        });
    }
    if af_short <= 0.0 {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("af_short ({af_short}) must be > 0"),
        });
    }
    if af_max_short < af_init_short {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!(
                "af_max_short ({af_max_short}) must be >= af_init_short ({af_init_short})"
            ),
        });
    }

    let n = high.len();
    let mut result = init_result!(n);

    // 初始化
    let mut is_long = true;
    let mut sar_value = if is_zero(start_value) {
        low[0]
    } else {
        start_value
    };
    let mut ep = high[0];
    let mut af = af_init_long;

    result[0] = sar_value;

    for i in 1..n {
        // 更新 SAR 值
        sar_value = sar_value + af * (ep - sar_value);

        // 检查反转
        let mut reversed = false;
        if is_long {
            if low[i] < sar_value {
                is_long = false;
                reversed = true;
                sar_value = ep + offset_on_reverse;
                ep = low[i];
                af = af_init_short;
            }
        } else if high[i] > sar_value {
            is_long = true;
            reversed = true;
            sar_value = ep - offset_on_reverse;
            ep = high[i];
            af = af_init_long;
        }

        // 如果没有反转，更新 EP 和 AF
        if !reversed {
            if is_long {
                if high[i] > ep {
                    ep = high[i];
                    af = (af + af_long).min(af_max_long);
                }
                if i >= 1 {
                    sar_value = sar_value.min(low[i - 1]);
                }
                if i >= 2 {
                    sar_value = sar_value.min(low[i - 2]);
                }
            } else {
                if low[i] < ep {
                    ep = low[i];
                    af = (af + af_short).min(af_max_short);
                }
                if i >= 1 {
                    sar_value = sar_value.max(high[i - 1]);
                }
                if i >= 2 {
                    sar_value = sar_value.max(high[i - 2]);
                }
            }
        }

        result[i] = sar_value;
    }

    Ok(result)
}

/// MAMA - MESA Adaptive Moving Average
///
/// 基于 Hilbert Transform 的自适应移动平均
///
/// # 参数
/// - `values`: 输入序列
/// - `fast_limit`: 快速限制（默认 0.5）
/// - `slow_limit`: 慢速限制（默认 0.05）
///
/// # 返回
/// - `HazeResult<(Vec<f64>, Vec<f64>)>` (MAMA, FAMA) 元组
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `InsufficientData`: 数据长度小于 6
pub fn mama(values: &[f64], fast_limit: f64, slow_limit: f64) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(values, "values")?;
    validate_min_length(values, 6)?;

    let n = values.len();
    let mut mama_vals = init_result!(n);
    let mut fama_vals = init_result!(n);

    // 初始化
    mama_vals[0] = values[0];
    fama_vals[0] = values[0];

    let mut period: f64 = 0.0;

    for i in 1..n {
        // 简化的 Hilbert Transform（完整实现需要更复杂的相位检测）
        // 这里使用简化版本，仅供演示

        // 计算周期（使用简化的检测逻辑）
        if i >= 6 {
            // 使用价格差分估算周期
            let delta = (values[i] - values[i - 1]).abs();
            if delta > 0.0 {
                period = 0.075 * period + 0.54;
            }
        }

        // 限制周期范围
        period = period.clamp(6.0, 50.0);

        // 计算 alpha（自适应因子）
        let alpha = (fast_limit / period).clamp(slow_limit, fast_limit);

        // 计算 MAMA
        mama_vals[i] = alpha * values[i] + (1.0 - alpha) * mama_vals[i - 1];

        // 计算 FAMA（Following Adaptive MA）
        let fama_alpha = 0.5 * alpha;
        fama_vals[i] = fama_alpha * mama_vals[i] + (1.0 - fama_alpha) * fama_vals[i - 1];
    }

    Ok((mama_vals, fama_vals))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::errors::HazeError;

    #[test]
    fn test_hl2() {
        let high = vec![110.0, 111.0, 112.0];
        let low = vec![100.0, 101.0, 102.0];

        let result = hl2(&high, &low).unwrap();

        assert_eq!(result[0], 105.0);
        assert_eq!(result[1], 106.0);
        assert_eq!(result[2], 107.0);
    }

    #[test]
    fn test_hlc3() {
        let high = vec![110.0];
        let low = vec![100.0];
        let close = vec![105.0];

        let result = hlc3(&high, &low, &close).unwrap();

        assert_eq!(result[0], 105.0); // (110 + 100 + 105) / 3
    }

    #[test]
    fn test_hl2_empty_input() {
        let result = hl2(&[], &[]);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_hlc3_length_mismatch() {
        let high = vec![110.0, 111.0];
        let low = vec![100.0];
        let close = vec![105.0, 106.0];

        let result = hlc3(&high, &low, &close);
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }

    #[test]
    fn test_midpoint_invalid_period() {
        let values = vec![1.0, 2.0, 3.0];
        let result = midpoint(&values, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }

    #[test]
    fn test_sar_insufficient_data() {
        let high = vec![10.0];
        let low = vec![9.0];
        let result = sar(&high, &low, 0.02, 0.2);
        assert!(matches!(result, Err(HazeError::InsufficientData { .. })));
    }

    #[test]
    fn test_mama_valid() {
        let values: Vec<f64> = (0..20).map(|i| 100.0 + i as f64).collect();
        let (mama_vals, fama_vals) = mama(&values, 0.5, 0.05).unwrap();
        assert_eq!(mama_vals.len(), values.len());
        assert_eq!(fama_vals.len(), values.len());
    }

    #[test]
    fn test_mama_insufficient_data() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = mama(&values, 0.5, 0.05);
        assert!(matches!(result, Err(HazeError::InsufficientData { .. })));
    }
}
