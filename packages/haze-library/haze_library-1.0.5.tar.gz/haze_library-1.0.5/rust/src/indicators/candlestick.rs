//! Candlestick Pattern Recognition Module
//!
//! 实现经典的蜡烛图形态识别，包括：
//! - Doji (十字星)
//! - Hammer / Inverted Hammer (锤子线/倒锤子线)
//! - Hanging Man (上吊线)
//! - Engulfing (吞没形态)
//! - Harami (孕线形态)
//! - Piercing / Dark Cloud (刺透/乌云盖顶)
//! - Morning/Evening Star (早晨之星/黄昏之星)
//! - Three White Soldiers / Three Black Crows (三白兵/三黑鸦)

// TA-Lib 兼容 API: 部分函数需要 high/low 参数但未使用
#![allow(unused_variables)]
// 数值计算中显式索引比迭代器链更清晰
#![allow(clippy::needless_range_loop)]

use crate::errors::HazeResult;
use crate::utils::math::{is_not_zero, is_zero};
use crate::{init_result, validate_full_ohlc, validate_pair};

// 辅助函数：计算蜡烛实体长度
fn body_length(open: f64, close: f64) -> f64 {
    (close - open).abs()
}

/// 辅助函数：计算上影线长度
fn upper_shadow(high: f64, open: f64, close: f64) -> f64 {
    high - open.max(close)
}

/// 辅助函数：计算下影线长度
fn lower_shadow(low: f64, open: f64, close: f64) -> f64 {
    open.min(close) - low
}

/// 辅助函数：计算蜡烛总长度（高-低）
fn total_range(high: f64, low: f64) -> f64 {
    high - low
}

/// 辅助函数：判断是否为看涨蜡烛
fn is_bullish(open: f64, close: f64) -> bool {
    close > open
}

/// 辅助函数：判断是否为看跌蜡烛
fn is_bearish(open: f64, close: f64) -> bool {
    close < open
}

/// 辅助函数：计算一段时间内的平均实体长度
fn average_body_length(open: &[f64], close: &[f64], start_idx: usize, count: usize) -> f64 {
    let mut sum = 0.0;
    let end_idx = (start_idx + count).min(open.len()).min(close.len());

    for i in start_idx..end_idx {
        sum += body_length(open[i], close[i]);
    }

    let actual_count = end_idx - start_idx;
    if actual_count > 0 {
        sum / actual_count as f64
    } else {
        0.0
    }
}

/// Doji（十字星）
///
/// 识别标准：
/// - 实体非常小（< 总长度的 10%）
/// - 上下影线相对较长
///
/// 返回值：1.0 = Doji, 0.0 = 非 Doji, NaN = 数据不足
pub fn doji(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    body_threshold: f64, // 默认 0.1 (10%)
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    for i in 0..n {
        let body = body_length(open[i], close[i]);
        let range = total_range(high[i], low[i]);

        if range > 0.0 && body / range < body_threshold {
            result[i] = 1.0; // Doji
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Hammer（锤子线）
///
/// 识别标准：
/// - 下影线 >= 实体长度的 2 倍
/// - 上影线很小（< 实体长度）
/// - 出现在下跌趋势底部
///
/// 返回值：1.0 = Bullish Hammer, -1.0 = Bearish Hammer, 0.0 = 非 Hammer
pub fn hammer(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    for i in 0..n {
        let body = body_length(open[i], close[i]);
        let lower = lower_shadow(low[i], open[i], close[i]);
        let upper = upper_shadow(high[i], open[i], close[i]);

        if body > 0.0 && lower >= 2.0 * body && upper <= body {
            if is_bullish(open[i], close[i]) {
                result[i] = 1.0; // Bullish Hammer
            } else {
                result[i] = -1.0; // Bearish Hammer
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Inverted Hammer（倒锤子线）
///
/// 识别标准：
/// - 上影线 >= 实体长度的 2 倍
/// - 下影线很小（< 实体长度）
/// - 出现在下跌趋势底部
///
/// 返回值：1.0 = Bullish Inverted Hammer, -1.0 = Bearish, 0.0 = 非倒锤子
pub fn inverted_hammer(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    for i in 0..n {
        let body = body_length(open[i], close[i]);
        let lower = lower_shadow(low[i], open[i], close[i]);
        let upper = upper_shadow(high[i], open[i], close[i]);

        if body > 0.0 && upper >= 2.0 * body && lower <= body {
            if is_bullish(open[i], close[i]) {
                result[i] = 1.0;
            } else {
                result[i] = -1.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Hanging Man（上吊线）
///
/// 与 Hammer 形态相同，但出现在上涨趋势顶部
/// 需要结合趋势判断
///
/// 识别标准：与 Hammer 相同
/// - 下影线 >= 实体长度的 2 倍
/// - 上影线很小（< 实体长度）
///
/// 返回值：-1.0 = Bearish Hanging Man, 0.0 = 非上吊线
pub fn hanging_man(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    // 形态与 Hammer 相同，只是上下文不同
    // 这里返回形态识别，趋势判断由上层逻辑处理
    let hammer_result = hammer(open, high, low, close)?;

    Ok(hammer_result
        .iter()
        .map(|&x| {
            if is_not_zero(x) {
                -1.0 // 潜在的看跌信号
            } else {
                0.0
            }
        })
        .collect())
}

/// Bullish Engulfing（看涨吞没）
///
/// 识别标准：
/// - 前一根为阴线，当前为阳线
/// - 当前阳线实体完全吞没前一根阴线实体
///
/// 返回值：1.0 = Bullish Engulfing, 0.0 = 非吞没, NaN = 数据不足
pub fn bullish_engulfing(open: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_pair!(open, "open", close, "close");
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let prev_bearish = is_bearish(open[i - 1], close[i - 1]);
        let curr_bullish = is_bullish(open[i], close[i]);

        if prev_bearish && curr_bullish {
            // 当前阳线的开盘 < 前一阴线的收盘
            // 当前阳线的收盘 > 前一阴线的开盘
            if open[i] <= close[i - 1] && close[i] >= open[i - 1] {
                result[i] = 1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Bearish Engulfing（看跌吞没）
///
/// 识别标准：
/// - 前一根为阳线，当前为阴线
/// - 当前阴线实体完全吞没前一根阳线实体
///
/// 返回值：-1.0 = Bearish Engulfing, 0.0 = 非吞没, NaN = 数据不足
pub fn bearish_engulfing(open: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_pair!(open, "open", close, "close");
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let prev_bullish = is_bullish(open[i - 1], close[i - 1]);
        let curr_bearish = is_bearish(open[i], close[i]);

        if prev_bullish && curr_bearish {
            // 当前阴线的开盘 > 前一阳线的收盘
            // 当前阴线的收盘 < 前一阳线的开盘
            if open[i] >= close[i - 1] && close[i] <= open[i - 1] {
                result[i] = -1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Bullish Harami（看涨孕线）
///
/// 识别标准：
/// - 前一根为大阴线
/// - 当前为小阳线，实体完全包含在前一根阴线实体内
///
/// 返回值：1.0 = Bullish Harami, 0.0 = 非孕线
pub fn bullish_harami(open: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_pair!(open, "open", close, "close");
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let prev_bearish = is_bearish(open[i - 1], close[i - 1]);
        let curr_bullish = is_bullish(open[i], close[i]);

        if prev_bearish && curr_bullish {
            // 当前小阳线完全在前一大阴线内
            if open[i] > close[i - 1]
                && open[i] < open[i - 1]
                && close[i] > close[i - 1]
                && close[i] < open[i - 1]
            {
                result[i] = 1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Bearish Harami（看跌孕线）
///
/// 识别标准：
/// - 前一根为大阳线
/// - 当前为小阴线，实体完全包含在前一根阳线实体内
///
/// 返回值：-1.0 = Bearish Harami, 0.0 = 非孕线
pub fn bearish_harami(open: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_pair!(open, "open", close, "close");
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let prev_bullish = is_bullish(open[i - 1], close[i - 1]);
        let curr_bearish = is_bearish(open[i], close[i]);

        if prev_bullish && curr_bearish {
            // 当前小阴线完全在前一大阳线内
            if open[i] < close[i - 1]
                && open[i] > open[i - 1]
                && close[i] < close[i - 1]
                && close[i] > open[i - 1]
            {
                result[i] = -1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Piercing Pattern（刺透形态）
///
/// 识别标准：
/// - 前一根为阴线
/// - 当前为阳线，开盘价低于前一阴线最低价
/// - 收盘价刺入前一阴线实体一半以上
///
/// 返回值：1.0 = Piercing, 0.0 = 非刺透
pub fn piercing_pattern(open: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_pair!(low, "low", close, "close");
    crate::errors::validation::validate_same_length(open, "open", close, "close")?;
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let prev_bearish = is_bearish(open[i - 1], close[i - 1]);
        let curr_bullish = is_bullish(open[i], close[i]);

        if prev_bearish && curr_bullish {
            // 当前开盘 < 前一最低
            // 当前收盘 > 前一中点（(开盘+收盘)/2）
            let prev_midpoint = (open[i - 1] + close[i - 1]) / 2.0;

            if open[i] < low[i - 1] && close[i] > prev_midpoint && close[i] < open[i - 1] {
                result[i] = 1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Dark Cloud Cover（乌云盖顶）
///
/// 识别标准：
/// - 前一根为阳线
/// - 当前为阴线，开盘价高于前一阳线最高价
/// - 收盘价深入前一阳线实体一半以上
///
/// 返回值：-1.0 = Dark Cloud, 0.0 = 非乌云盖顶
pub fn dark_cloud_cover(open: &[f64], high: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_pair!(high, "high", close, "close");
    crate::errors::validation::validate_same_length(open, "open", close, "close")?;
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let prev_bullish = is_bullish(open[i - 1], close[i - 1]);
        let curr_bearish = is_bearish(open[i], close[i]);

        if prev_bullish && curr_bearish {
            // 当前开盘 > 前一最高
            // 当前收盘 < 前一中点
            let prev_midpoint = (open[i - 1] + close[i - 1]) / 2.0;

            if open[i] > high[i - 1] && close[i] < prev_midpoint && close[i] > open[i - 1] {
                result[i] = -1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Morning Star（早晨之星）
///
/// 识别标准（三根蜡烛组合）：
/// 1. 第一根：大阴线
/// 2. 第二根：小实体（星线），向下跳空
/// 3. 第三根：大阳线，收盘价深入第一根阴线实体一半以上
///
/// 返回值：1.0 = Morning Star, 0.0 = 非早晨之星
pub fn morning_star(
    open: &[f64],
    _high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, _high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    result[0] = 0.0;
    result[1] = 0.0;

    for i in 2..n {
        let first_bearish = is_bearish(open[i - 2], close[i - 2]);
        let second_small =
            body_length(open[i - 1], close[i - 1]) < body_length(open[i - 2], close[i - 2]) * 0.3;
        let third_bullish = is_bullish(open[i], close[i]);

        if first_bearish && second_small && third_bullish {
            // 第二根向下跳空（最高价 < 第一根最低价）
            let gap_down = low[i - 1] < close[i - 2];
            // 第三根收盘价 > 第一根中点
            let first_midpoint = (open[i - 2] + close[i - 2]) / 2.0;

            if gap_down && close[i] > first_midpoint {
                result[i] = 1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Evening Star（黄昏之星）
///
/// 识别标准（三根蜡烛组合）：
/// 1. 第一根：大阳线
/// 2. 第二根：小实体（星线），向上跳空
/// 3. 第三根：大阴线，收盘价深入第一根阳线实体一半以上
///
/// 返回值：-1.0 = Evening Star, 0.0 = 非黄昏之星
pub fn evening_star(
    open: &[f64],
    high: &[f64],
    _low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, _low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    result[0] = 0.0;
    result[1] = 0.0;

    for i in 2..n {
        let first_bullish = is_bullish(open[i - 2], close[i - 2]);
        let second_small =
            body_length(open[i - 1], close[i - 1]) < body_length(open[i - 2], close[i - 2]) * 0.3;
        let third_bearish = is_bearish(open[i], close[i]);

        if first_bullish && second_small && third_bearish {
            // 第二根向上跳空（最低价 > 第一根最高价）
            let gap_up = high[i - 1] > close[i - 2];
            // 第三根收盘价 < 第一根中点
            let first_midpoint = (open[i - 2] + close[i - 2]) / 2.0;

            if gap_up && close[i] < first_midpoint {
                result[i] = -1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Three White Soldiers（三白兵）
///
/// 识别标准（三根蜡烛组合）：
/// - 连续三根阳线
/// - 每根收盘价高于前一根
/// - 每根开盘价在前一根实体内
/// - 上影线较短
///
/// 返回值：1.0 = Three White Soldiers, 0.0 = 非三白兵
pub fn three_white_soldiers(open: &[f64], high: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_pair!(high, "high", close, "close");
    crate::errors::validation::validate_same_length(open, "open", close, "close")?;
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    result[0] = 0.0;
    result[1] = 0.0;

    for i in 2..n {
        let all_bullish = is_bullish(open[i - 2], close[i - 2])
            && is_bullish(open[i - 1], close[i - 1])
            && is_bullish(open[i], close[i]);

        if all_bullish {
            // 递增收盘价
            let rising_close = close[i - 1] > close[i - 2] && close[i] > close[i - 1];

            // 每根开盘在前一根实体内
            let open_in_body = open[i - 1] > open[i - 2]
                && open[i - 1] < close[i - 2]
                && open[i] > open[i - 1]
                && open[i] < close[i - 1];

            // 上影线较短（< 实体的 30%）
            let short_shadows = upper_shadow(high[i - 2], open[i - 2], close[i - 2])
                < body_length(open[i - 2], close[i - 2]) * 0.3
                && upper_shadow(high[i - 1], open[i - 1], close[i - 1])
                    < body_length(open[i - 1], close[i - 1]) * 0.3
                && upper_shadow(high[i], open[i], close[i]) < body_length(open[i], close[i]) * 0.3;

            if rising_close && open_in_body && short_shadows {
                result[i] = 1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Three Black Crows（三黑鸦）
///
/// 识别标准（三根蜡烛组合）：
/// - 连续三根阴线
/// - 每根收盘价低于前一根
/// - 每根开盘价在前一根实体内
/// - 下影线较短
///
/// 返回值：-1.0 = Three Black Crows, 0.0 = 非三黑鸦
pub fn three_black_crows(open: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_pair!(low, "low", close, "close");
    crate::errors::validation::validate_same_length(open, "open", close, "close")?;
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    result[0] = 0.0;
    result[1] = 0.0;

    for i in 2..n {
        let all_bearish = is_bearish(open[i - 2], close[i - 2])
            && is_bearish(open[i - 1], close[i - 1])
            && is_bearish(open[i], close[i]);

        if all_bearish {
            // 递减收盘价
            let falling_close = close[i - 1] < close[i - 2] && close[i] < close[i - 1];

            // 每根开盘在前一根实体内
            let open_in_body = open[i - 1] < open[i - 2]
                && open[i - 1] > close[i - 2]
                && open[i] < open[i - 1]
                && open[i] > close[i - 1];

            // 下影线较短（< 实体的 30%）
            let short_shadows = lower_shadow(low[i - 2], open[i - 2], close[i - 2])
                < body_length(open[i - 2], close[i - 2]) * 0.3
                && lower_shadow(low[i - 1], open[i - 1], close[i - 1])
                    < body_length(open[i - 1], close[i - 1]) * 0.3
                && lower_shadow(low[i], open[i], close[i]) < body_length(open[i], close[i]) * 0.3;

            if falling_close && open_in_body && short_shadows {
                result[i] = -1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_doji() {
        let open = vec![100.0, 105.0];
        let high = vec![102.0, 110.0];
        let low = vec![98.0, 104.5];
        let close = vec![100.5, 105.2]; // 第二根接近 Doji

        let result = doji(&open, &high, &low, &close, 0.1).unwrap();
        assert_eq!(result[1], 1.0); // 实体 0.2 / 总长度 5.5 < 10%
    }

    #[test]
    fn test_hammer() {
        let open = vec![100.0];
        let high = vec![101.0];
        let low = vec![95.0]; // 长下影线
        let close = vec![100.5];

        let result = hammer(&open, &high, &low, &close).unwrap();
        assert_eq!(result[0], 1.0); // Bullish Hammer
    }

    #[test]
    fn test_bullish_engulfing() {
        let open = vec![100.0, 98.0];
        let close = vec![98.0, 102.0]; // 阳线吞没阴线

        let result = bullish_engulfing(&open, &close).unwrap();
        assert_eq!(result[1], 1.0);
    }

    #[test]
    fn test_morning_star() {
        let open = vec![100.0, 95.0, 96.0];
        let high = vec![100.5, 96.0, 101.0];
        let low = vec![95.0, 94.5, 95.5];
        let close = vec![95.5, 95.5, 100.5]; // 早晨之星

        let result = morning_star(&open, &high, &low, &close).unwrap();
        assert_eq!(result[2], 1.0);
    }

    #[test]
    fn test_three_white_soldiers() {
        let open = vec![100.0, 101.0, 102.5];
        let high = vec![102.0, 103.0, 104.5];
        let close = vec![102.0, 103.0, 104.5];

        let result = three_white_soldiers(&open, &high, &close).unwrap();
        assert_eq!(result[2], 1.0);
    }
}

/// Shooting Star（流星线）
///
/// 识别标准：
/// - 上影线 >= 实体长度的 2 倍
/// - 下影线很小（< 实体长度）
/// - 出现在上涨趋势顶部
///
/// 返回值：-1.0 = Shooting Star, 0.0 = 非流星线
pub fn shooting_star(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    // 形态与 Inverted Hammer 相同，但含义相反（顶部反转）
    let inverted = inverted_hammer(open, high, low, close)?;

    Ok(inverted
        .iter()
        .map(|&x| {
            if is_not_zero(x) {
                -1.0 // 潜在的看跌信号
            } else {
                0.0
            }
        })
        .collect())
}

/// Marubozu（光头光脚）
///
/// 识别标准：
/// - 实体占据几乎全部蜡烛长度（> 95%）
/// - 上下影线都很短或没有
///
/// 返回值：1.0 = Bullish Marubozu, -1.0 = Bearish Marubozu, 0.0 = 非光头光脚
pub fn marubozu(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    for i in 0..n {
        let body = body_length(open[i], close[i]);
        let range = total_range(high[i], low[i]);
        let upper = upper_shadow(high[i], open[i], close[i]);
        let lower = lower_shadow(low[i], open[i], close[i]);

        if range > 0.0
            && body > 0.0
            && body / range > 0.95
            && upper < body * 0.05
            && lower < body * 0.05
        {
            result[i] = if is_bullish(open[i], close[i]) {
                1.0
            } else {
                -1.0
            };
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Spinning Top（陀螺）
///
/// 识别标准：
/// - 实体很小（< 总长度的 25%）
/// - 上下影线都较长
/// - 表示市场犹豫不决
///
/// 返回值：1.0 = Spinning Top, 0.0 = 非陀螺
pub fn spinning_top(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    for i in 0..n {
        let body = body_length(open[i], close[i]);
        let range = total_range(high[i], low[i]);
        let upper = upper_shadow(high[i], open[i], close[i]);
        let lower = lower_shadow(low[i], open[i], close[i]);

        if range > 0.0 && body / range < 0.25 && upper > body && lower > body {
            result[i] = 1.0; // Spinning Top
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Dragonfly Doji（蜻蜓十字）
///
/// 识别标准：
/// - 实体很小（接近 Doji）
/// - 上影线很小或没有
/// - 下影线很长
///
/// 返回值：1.0 = Dragonfly Doji, 0.0 = 非蜻蜓十字
pub fn dragonfly_doji(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    body_threshold: f64,
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    for i in 0..n {
        let body = body_length(open[i], close[i]);
        let range = total_range(high[i], low[i]);
        let upper = upper_shadow(high[i], open[i], close[i]);
        let lower = lower_shadow(low[i], open[i], close[i]);

        if range > 0.0
            && body / range < body_threshold
            && upper < range * 0.1
            && lower > range * 0.6
        {
            result[i] = 1.0; // Dragonfly Doji
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Gravestone Doji（墓碑十字）
///
/// 识别标准：
/// - 实体很小（接近 Doji）
/// - 下影线很小或没有
/// - 上影线很长
///
/// 返回值：-1.0 = Gravestone Doji, 0.0 = 非墓碑十字
pub fn gravestone_doji(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    body_threshold: f64,
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    for i in 0..n {
        let body = body_length(open[i], close[i]);
        let range = total_range(high[i], low[i]);
        let upper = upper_shadow(high[i], open[i], close[i]);
        let lower = lower_shadow(low[i], open[i], close[i]);

        if range > 0.0
            && body / range < body_threshold
            && lower < range * 0.1
            && upper > range * 0.6
        {
            result[i] = -1.0; // Gravestone Doji
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Long Legged Doji（长腿十字）
///
/// 识别标准：
/// - 实体很小（接近 Doji）
/// - 上下影线都很长
///
/// 返回值：1.0 = Long Legged Doji, 0.0 = 非长腿十字
pub fn long_legged_doji(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    body_threshold: f64,
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    for i in 0..n {
        let body = body_length(open[i], close[i]);
        let range = total_range(high[i], low[i]);
        let upper = upper_shadow(high[i], open[i], close[i]);
        let lower = lower_shadow(low[i], open[i], close[i]);

        if range > 0.0
            && body / range < body_threshold
            && upper > range * 0.3
            && lower > range * 0.3
        {
            result[i] = 1.0; // Long Legged Doji
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Tweezers Top（镊子顶）
///
/// 识别标准（两根蜡烛组合）：
/// - 两根蜡烛的最高价几乎相同
/// - 第一根阳线，第二根阴线
/// - 出现在上涨趋势顶部
///
/// 返回值：-1.0 = Tweezers Top, 0.0 = 非镊子顶
pub fn tweezers_top(
    open: &[f64],
    high: &[f64],
    close: &[f64],
    tolerance: f64,
) -> HazeResult<Vec<f64>> {
    let n = validate_pair!(high, "high", close, "close");
    crate::errors::validation::validate_same_length(open, "open", close, "close")?;
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let first_bullish = is_bullish(open[i - 1], close[i - 1]);
        let second_bearish = is_bearish(open[i], close[i]);

        if first_bullish && second_bearish {
            // 两根蜡烛的最高价接近
            let high_diff = (high[i] - high[i - 1]).abs();
            let avg_high = (high[i] + high[i - 1]) / 2.0;

            if avg_high > 0.0 && high_diff / avg_high < tolerance {
                result[i] = -1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Tweezers Bottom（镊子底）
///
/// 识别标准（两根蜡烛组合）：
/// - 两根蜡烛的最低价几乎相同
/// - 第一根阴线，第二根阳线
/// - 出现在下跌趋势底部
///
/// 返回值：1.0 = Tweezers Bottom, 0.0 = 非镊子底
pub fn tweezers_bottom(
    open: &[f64],
    low: &[f64],
    close: &[f64],
    tolerance: f64,
) -> HazeResult<Vec<f64>> {
    let n = validate_pair!(low, "low", close, "close");
    crate::errors::validation::validate_same_length(open, "open", close, "close")?;
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let first_bearish = is_bearish(open[i - 1], close[i - 1]);
        let second_bullish = is_bullish(open[i], close[i]);

        if first_bearish && second_bullish {
            // 两根蜡烛的最低价接近
            let low_diff = (low[i] - low[i - 1]).abs();
            let avg_low = (low[i] + low[i - 1]) / 2.0;

            if avg_low > 0.0 && low_diff / avg_low < tolerance {
                result[i] = 1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Rising Three Methods（上升三法）
///
/// 识别标准（五根蜡烛组合）：
/// - 第一根：大阳线
/// - 第二、三、四根：小阴线，实体在第一根阳线内
/// - 第五根：大阳线，收盘价高于第一根
///
/// 返回值：1.0 = Rising Three Methods, 0.0 = 非上升三法
pub fn rising_three_methods(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 5 {
        return Ok(result);
    }

    for i in 0..4 {
        result[i] = 0.0;
    }

    for i in 4..n {
        let first_bullish = is_bullish(open[i - 4], close[i - 4]);
        let first_body = body_length(open[i - 4], close[i - 4]);

        let second_bearish = is_bearish(open[i - 3], close[i - 3]);
        let third_bearish = is_bearish(open[i - 2], close[i - 2]);
        let fourth_bearish = is_bearish(open[i - 1], close[i - 1]);

        let fifth_bullish = is_bullish(open[i], close[i]);

        if first_bullish && second_bearish && third_bearish && fourth_bearish && fifth_bullish {
            // 中间三根小阴线在第一根阳线范围内
            let middle_in_range = high[i - 3] < close[i - 4]
                && low[i - 3] > open[i - 4]
                && high[i - 2] < close[i - 4]
                && low[i - 2] > open[i - 4]
                && high[i - 1] < close[i - 4]
                && low[i - 1] > open[i - 4];

            // 第五根收盘高于第一根
            let fifth_higher = close[i] > close[i - 4];

            // 中间三根都是小实体
            let small_bodies = body_length(open[i - 3], close[i - 3]) < first_body * 0.5
                && body_length(open[i - 2], close[i - 2]) < first_body * 0.5
                && body_length(open[i - 1], close[i - 1]) < first_body * 0.5;

            if middle_in_range && fifth_higher && small_bodies {
                result[i] = 1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Falling Three Methods（下降三法）
///
/// 识别标准（五根蜡烛组合）：
/// - 第一根：大阴线
/// - 第二、三、四根：小阳线，实体在第一根阴线内
/// - 第五根：大阴线，收盘价低于第一根
///
/// 返回值：-1.0 = Falling Three Methods, 0.0 = 非下降三法
pub fn falling_three_methods(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 5 {
        return Ok(result);
    }

    for i in 0..4 {
        result[i] = 0.0;
    }

    for i in 4..n {
        let first_bearish = is_bearish(open[i - 4], close[i - 4]);
        let first_body = body_length(open[i - 4], close[i - 4]);

        let second_bullish = is_bullish(open[i - 3], close[i - 3]);
        let third_bullish = is_bullish(open[i - 2], close[i - 2]);
        let fourth_bullish = is_bullish(open[i - 1], close[i - 1]);

        let fifth_bearish = is_bearish(open[i], close[i]);

        if first_bearish && second_bullish && third_bullish && fourth_bullish && fifth_bearish {
            // 中间三根小阳线在第一根阴线范围内
            let middle_in_range = high[i - 3] < open[i - 4]
                && low[i - 3] > close[i - 4]
                && high[i - 2] < open[i - 4]
                && low[i - 2] > close[i - 4]
                && high[i - 1] < open[i - 4]
                && low[i - 1] > close[i - 4];

            // 第五根收盘低于第一根
            let fifth_lower = close[i] < close[i - 4];

            // 中间三根都是小实体
            let small_bodies = body_length(open[i - 3], close[i - 3]) < first_body * 0.5
                && body_length(open[i - 2], close[i - 2]) < first_body * 0.5
                && body_length(open[i - 1], close[i - 1]) < first_body * 0.5;

            if middle_in_range && fifth_lower && small_bodies {
                result[i] = -1.0;
            } else {
                result[i] = 0.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Harami Cross（十字孕线）
///
/// 识别标准（两根蜡烛组合）：
/// - 第一根：实体较大
/// - 第二根：十字星，完全在第一根实体内
///
/// 返回值：1.0 = Bullish Harami Cross, -1.0 = Bearish Harami Cross, 0.0 = 非十字孕线
pub fn harami_cross(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    body_threshold: f64, // Doji 阈值，默认 0.1
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let first_body = body_length(open[i - 1], close[i - 1]);
        let second_body = body_length(open[i], close[i]);
        let second_range = total_range(high[i], low[i]);

        // 第二根是十字星
        let is_doji = second_range > 0.0 && second_body / second_range < body_threshold;

        // 第二根完全在第一根实体内
        let second_inside = open[i].max(close[i]) < open[i - 1].max(close[i - 1])
            && open[i].min(close[i]) > open[i - 1].min(close[i - 1]);

        if is_doji && second_inside && first_body > 0.0 {
            if is_bearish(open[i - 1], close[i - 1]) {
                result[i] = 1.0; // Bullish Harami Cross
            } else {
                result[i] = -1.0; // Bearish Harami Cross
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Morning Doji Star（早晨十字星）
///
/// 识别标准（三根蜡烛组合）：
/// - 第一根：大阴线
/// - 第二根：十字星，跳空向下
/// - 第三根：阳线，收盘在第一根实体中部以上
///
/// 返回值：1.0 = Morning Doji Star, 0.0 = 非早晨十字星
pub fn morning_doji_star(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    body_threshold: f64, // Doji 阈值，默认 0.1
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    for i in 0..2 {
        result[i] = 0.0;
    }

    for i in 2..n {
        let first_bearish = is_bearish(open[i - 2], close[i - 2]);
        let first_body = body_length(open[i - 2], close[i - 2]);

        let second_body = body_length(open[i - 1], close[i - 1]);
        let second_range = total_range(high[i - 1], low[i - 1]);
        let is_doji = second_range > 0.0 && second_body / second_range < body_threshold;

        // 第二根跳空向下
        let gap_down = high[i - 1] < close[i - 2].min(open[i - 2]);

        let third_bullish = is_bullish(open[i], close[i]);
        let third_close_high = close[i] > (open[i - 2] + close[i - 2]) / 2.0;

        if first_bearish
            && is_doji
            && gap_down
            && third_bullish
            && third_close_high
            && first_body > 0.0
        {
            result[i] = 1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Evening Doji Star（黄昏十字星）
///
/// 识别标准（三根蜡烛组合）：
/// - 第一根：大阳线
/// - 第二根：十字星，跳空向上
/// - 第三根：阴线，收盘在第一根实体中部以下
///
/// 返回值：-1.0 = Evening Doji Star, 0.0 = 非黄昏十字星
pub fn evening_doji_star(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    body_threshold: f64, // Doji 阈值，默认 0.1
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    for i in 0..2 {
        result[i] = 0.0;
    }

    for i in 2..n {
        let first_bullish = is_bullish(open[i - 2], close[i - 2]);
        let first_body = body_length(open[i - 2], close[i - 2]);

        let second_body = body_length(open[i - 1], close[i - 1]);
        let second_range = total_range(high[i - 1], low[i - 1]);
        let is_doji = second_range > 0.0 && second_body / second_range < body_threshold;

        // 第二根跳空向上
        let gap_up = low[i - 1] > close[i - 2].max(open[i - 2]);

        let third_bearish = is_bearish(open[i], close[i]);
        let third_close_low = close[i] < (open[i - 2] + close[i - 2]) / 2.0;

        if first_bullish
            && is_doji
            && gap_up
            && third_bearish
            && third_close_low
            && first_body > 0.0
        {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Three Inside Up/Down（三内部上涨/下跌）
///
/// 识别标准（三根蜡烛组合）：
/// - 看涨版本：第一根阴线 + 第二根小阳线（孕线）+ 第三根阳线收盘高于第一根最高
/// - 看跌版本：第一根阳线 + 第二根小阴线（孕线）+ 第三根阴线收盘低于第一根最低
///
/// 返回值：1.0 = Three Inside Up, -1.0 = Three Inside Down, 0.0 = 非三内部
pub fn three_inside(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    for i in 0..2 {
        result[i] = 0.0;
    }

    for i in 2..n {
        // Three Inside Up
        let first_bearish = is_bearish(open[i - 2], close[i - 2]);
        let second_bullish = is_bullish(open[i - 1], close[i - 1]);
        let harami_bullish =
            second_bullish && open[i - 1] > close[i - 2] && close[i - 1] < open[i - 2];
        let third_bullish = is_bullish(open[i], close[i]);
        let third_close_above = close[i] > high[i - 2];

        if first_bearish && harami_bullish && third_bullish && third_close_above {
            result[i] = 1.0;
            continue;
        }

        // Three Inside Down
        let first_bullish = is_bullish(open[i - 2], close[i - 2]);
        let second_bearish = is_bearish(open[i - 1], close[i - 1]);
        let harami_bearish =
            second_bearish && open[i - 1] < close[i - 2] && close[i - 1] > open[i - 2];
        let third_bearish = is_bearish(open[i], close[i]);
        let third_close_below = close[i] < low[i - 2];

        if first_bullish && harami_bearish && third_bearish && third_close_below {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Three Outside Up/Down（三外部上涨/下跌）
///
/// 识别标准（三根蜡烛组合）：
/// - 看涨版本：第一根阴线 + 第二根阳线（吞没）+ 第三根阳线收盘高于第二根
/// - 看跌版本：第一根阳线 + 第二根阴线（吞没）+ 第三根阴线收盘低于第二根
///
/// 返回值：1.0 = Three Outside Up, -1.0 = Three Outside Down, 0.0 = 非三外部
pub fn three_outside(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    for i in 0..2 {
        result[i] = 0.0;
    }

    for i in 2..n {
        // Three Outside Up
        let first_bearish = is_bearish(open[i - 2], close[i - 2]);
        let second_bullish = is_bullish(open[i - 1], close[i - 1]);
        let engulfing_bullish =
            second_bullish && open[i - 1] < close[i - 2] && close[i - 1] > open[i - 2];
        let third_bullish = is_bullish(open[i], close[i]);
        let third_close_above = close[i] > close[i - 1];

        if first_bearish && engulfing_bullish && third_bullish && third_close_above {
            result[i] = 1.0;
            continue;
        }

        // Three Outside Down
        let first_bullish = is_bullish(open[i - 2], close[i - 2]);
        let second_bearish = is_bearish(open[i - 1], close[i - 1]);
        let engulfing_bearish =
            second_bearish && open[i - 1] > close[i - 2] && close[i - 1] < open[i - 2];
        let third_bearish = is_bearish(open[i], close[i]);
        let third_close_below = close[i] < close[i - 1];

        if first_bullish && engulfing_bearish && third_bearish && third_close_below {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Abandoned Baby（弃婴）
///
/// 识别标准（三根蜡烛组合）：
/// - 看涨版本：第一根阴线 + 第二根十字星（跳空向下，完全脱离前后）+ 第三根阳线跳空向上
/// - 看跌版本：第一根阳线 + 第二根十字星（跳空向上，完全脱离前后）+ 第三根阴线跳空向下
///
/// 返回值：1.0 = Bullish Abandoned Baby, -1.0 = Bearish Abandoned Baby, 0.0 = 非弃婴
pub fn abandoned_baby(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    body_threshold: f64, // Doji 阈值，默认 0.1
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    for i in 0..2 {
        result[i] = 0.0;
    }

    for i in 2..n {
        let second_body = body_length(open[i - 1], close[i - 1]);
        let second_range = total_range(high[i - 1], low[i - 1]);
        let is_doji = second_range > 0.0 && second_body / second_range < body_threshold;

        // Bullish Abandoned Baby
        let first_bearish = is_bearish(open[i - 2], close[i - 2]);
        let gap_down = high[i - 1] < open[i - 2].min(close[i - 2]);
        let third_bullish = is_bullish(open[i], close[i]);
        let gap_up = low[i] > high[i - 1];

        if first_bearish && is_doji && gap_down && third_bullish && gap_up {
            result[i] = 1.0;
            continue;
        }

        // Bearish Abandoned Baby
        let first_bullish = is_bullish(open[i - 2], close[i - 2]);
        let gap_up_first = low[i - 1] > open[i - 2].max(close[i - 2]);
        let third_bearish = is_bearish(open[i], close[i]);
        let gap_down_second = high[i] < low[i - 1];

        if first_bullish && is_doji && gap_up_first && third_bearish && gap_down_second {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Kicking（踢腿）
///
/// 识别标准（两根蜡烛组合）：
/// - 看涨版本：第一根光头光脚阴线 + 第二根光头光脚阳线，跳空向上
/// - 看跌版本：第一根光头光脚阳线 + 第二根光头光脚阴线，跳空向下
///
/// 返回值：1.0 = Bullish Kicking, -1.0 = Bearish Kicking, 0.0 = 非踢腿
pub fn kicking(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let first_body = body_length(open[i - 1], close[i - 1]);
        let first_range = total_range(high[i - 1], low[i - 1]);
        let first_upper = upper_shadow(high[i - 1], open[i - 1], close[i - 1]);
        let first_lower = lower_shadow(low[i - 1], open[i - 1], close[i - 1]);

        let second_body = body_length(open[i], close[i]);
        let second_range = total_range(high[i], low[i]);
        let second_upper = upper_shadow(high[i], open[i], close[i]);
        let second_lower = lower_shadow(low[i], open[i], close[i]);

        // 判断是否为光头光脚（Marubozu）
        let first_marubozu = first_range > 0.0
            && first_body / first_range > 0.95
            && first_upper < first_range * 0.05
            && first_lower < first_range * 0.05;

        let second_marubozu = second_range > 0.0
            && second_body / second_range > 0.95
            && second_upper < second_range * 0.05
            && second_lower < second_range * 0.05;

        // Bullish Kicking
        let first_bearish = is_bearish(open[i - 1], close[i - 1]);
        let second_bullish = is_bullish(open[i], close[i]);
        let gap_up = open[i] > open[i - 1];

        if first_marubozu && second_marubozu && first_bearish && second_bullish && gap_up {
            result[i] = 1.0;
            continue;
        }

        // Bearish Kicking
        let first_bullish = is_bullish(open[i - 1], close[i - 1]);
        let second_bearish = is_bearish(open[i], close[i]);
        let gap_down = open[i] < open[i - 1];

        if first_marubozu && second_marubozu && first_bullish && second_bearish && gap_down {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Long Line Candle（长线蜡烛）
///
/// 识别标准：
/// - 实体长度是平均实体长度的 2 倍以上
/// - 影线相对较短
///
/// 返回值：1.0 = Bullish Long Line, -1.0 = Bearish Long Line, 0.0 = 非长线蜡烛
pub fn long_line(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    lookback: usize, // 计算平均实体的回看周期，默认 10
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < lookback + 1 {
        for i in 0..n {
            result[i] = 0.0;
        }
        return Ok(result);
    }

    for i in 0..lookback {
        result[i] = 0.0;
    }

    for i in lookback..n {
        // 计算平均实体长度
        let mut avg_body = 0.0;
        for j in (i - lookback)..i {
            avg_body += body_length(open[j], close[j]);
        }
        avg_body /= lookback as f64;

        let current_body = body_length(open[i], close[i]);
        let current_range = total_range(high[i], low[i]);
        let upper = upper_shadow(high[i], open[i], close[i]);
        let lower = lower_shadow(low[i], open[i], close[i]);

        // 实体是平均的 2 倍以上，且影线不超过实体的 50%
        if current_body > avg_body * 2.0 && upper < current_body * 0.5 && lower < current_body * 0.5
        {
            if is_bullish(open[i], close[i]) {
                result[i] = 1.0;
            } else {
                result[i] = -1.0;
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Short Line Candle（短线蜡烛）
///
/// 识别标准：
/// - 实体长度是平均实体长度的 0.5 倍以下
/// - 整体范围较小
///
/// 返回值：1.0 = Bullish Short Line, -1.0 = Bearish Short Line, 0.0 = 非短线蜡烛
pub fn short_line(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    lookback: usize, // 计算平均实体的回看周期，默认 10
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < lookback + 1 {
        for i in 0..n {
            result[i] = 0.0;
        }
        return Ok(result);
    }

    for i in 0..lookback {
        result[i] = 0.0;
    }

    for i in lookback..n {
        // 计算平均实体长度
        let mut avg_body = 0.0;
        for j in (i - lookback)..i {
            avg_body += body_length(open[j], close[j]);
        }
        avg_body /= lookback as f64;

        let current_body = body_length(open[i], close[i]);

        // 实体是平均的 0.5 倍以下
        if current_body < avg_body * 0.5 {
            if is_bullish(open[i], close[i]) {
                result[i] = 1.0;
            } else if is_bearish(open[i], close[i]) {
                result[i] = -1.0;
            } else {
                result[i] = 0.0; // Doji 情况
            }
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Doji Star（十字星）
///
/// 识别标准（两根蜡烛组合）：
/// - 第一根：实体较大
/// - 第二根：十字星，跳空（不重叠第一根实体）
///
/// 返回值：1.0 = Bullish Doji Star (跳空向下), -1.0 = Bearish Doji Star (跳空向上), 0.0 = 非十字星
pub fn doji_star(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    body_threshold: f64, // Doji 阈值，默认 0.1
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let first_body = body_length(open[i - 1], close[i - 1]);
        let second_body = body_length(open[i], close[i]);
        let second_range = total_range(high[i], low[i]);

        // 第二根是十字星
        let is_doji = second_range > 0.0 && second_body / second_range < body_threshold;

        // Bullish Doji Star (第一根阴线，十字星跳空向下)
        let first_bearish = is_bearish(open[i - 1], close[i - 1]);
        let gap_down = high[i] < open[i - 1].min(close[i - 1]);

        if is_doji && first_bearish && gap_down && first_body > 0.0 {
            result[i] = 1.0;
            continue;
        }

        // Bearish Doji Star (第一根阳线，十字星跳空向上)
        let first_bullish = is_bullish(open[i - 1], close[i - 1]);
        let gap_up = low[i] > open[i - 1].max(close[i - 1]);

        if is_doji && first_bullish && gap_up && first_body > 0.0 {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Identical Three Crows（相同三乌鸦）
///
/// 识别标准（三根蜡烛组合）：
/// - 三根连续阴线
/// - 每根开盘价在前一根实体内
/// - 收盘价依次更低
/// - 实体大小相近
///
/// 返回值：-1.0 = Identical Three Crows, 0.0 = 非相同三乌鸦
pub fn identical_three_crows(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    for i in 0..2 {
        result[i] = 0.0;
    }

    for i in 2..n {
        let first_bearish = is_bearish(open[i - 2], close[i - 2]);
        let second_bearish = is_bearish(open[i - 1], close[i - 1]);
        let third_bearish = is_bearish(open[i], close[i]);

        if !first_bearish || !second_bearish || !third_bearish {
            result[i] = 0.0;
            continue;
        }

        let first_body = body_length(open[i - 2], close[i - 2]);
        let second_body = body_length(open[i - 1], close[i - 1]);
        let third_body = body_length(open[i], close[i]);

        // 每根开盘价在前一根实体内
        let second_opens_inside = open[i - 1] < open[i - 2] && open[i - 1] > close[i - 2];
        let third_opens_inside = open[i] < open[i - 1] && open[i] > close[i - 1];

        // 收盘价依次更低
        let descending_closes = close[i - 1] < close[i - 2] && close[i] < close[i - 1];

        // 实体大小相近（相差不超过30%）
        let avg_body = (first_body + second_body + third_body) / 3.0;
        let similar_bodies = (first_body - avg_body).abs() < avg_body * 0.3
            && (second_body - avg_body).abs() < avg_body * 0.3
            && (third_body - avg_body).abs() < avg_body * 0.3;

        if second_opens_inside && third_opens_inside && descending_closes && similar_bodies {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Stick Sandwich（棍子夹心）
///
/// 识别标准（三根蜡烛组合）：
/// - 第一根：阴线
/// - 第二根：阳线，在第一根范围内
/// - 第三根：阴线，收盘价与第一根接近
///
/// 返回值：1.0 = Stick Sandwich, 0.0 = 非棍子夹心
pub fn stick_sandwich(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    tolerance: f64, // 默认 0.01 (1%)
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    for i in 0..2 {
        result[i] = 0.0;
    }

    for i in 2..n {
        let first_bearish = is_bearish(open[i - 2], close[i - 2]);
        let second_bullish = is_bullish(open[i - 1], close[i - 1]);
        let third_bearish = is_bearish(open[i], close[i]);

        if !first_bearish || !second_bullish || !third_bearish {
            result[i] = 0.0;
            continue;
        }

        // 第二根在第一根范围内
        let second_inside = low[i - 1] > close[i - 2] && high[i - 1] < open[i - 2];

        // 第三根收盘价与第一根接近
        let closes_match = (close[i] - close[i - 2]).abs() / close[i - 2] < tolerance;

        if second_inside && closes_match {
            result[i] = 1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Tristar Pattern（三星）
///
/// 识别标准（三根蜡烛组合）：
/// - 三根连续的十字星
/// - 第二根跳空（高于或低于第一、三根）
///
/// 返回值：1.0 = Bullish Tristar, -1.0 = Bearish Tristar, 0.0 = 非三星
pub fn tristar(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    body_threshold: f64, // Doji 阈值，默认 0.1
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    for i in 0..2 {
        result[i] = 0.0;
    }

    for i in 2..n {
        let first_body = body_length(open[i - 2], close[i - 2]);
        let first_range = total_range(high[i - 2], low[i - 2]);
        let first_doji = first_range > 0.0 && first_body / first_range < body_threshold;

        let second_body = body_length(open[i - 1], close[i - 1]);
        let second_range = total_range(high[i - 1], low[i - 1]);
        let second_doji = second_range > 0.0 && second_body / second_range < body_threshold;

        let third_body = body_length(open[i], close[i]);
        let third_range = total_range(high[i], low[i]);
        let third_doji = third_range > 0.0 && third_body / third_range < body_threshold;

        if !first_doji || !second_doji || !third_doji {
            result[i] = 0.0;
            continue;
        }

        // Bullish Tristar: 第二根跳空向下
        let gap_down = high[i - 1] < low[i - 2].min(low[i]);
        if gap_down {
            result[i] = 1.0;
            continue;
        }

        // Bearish Tristar: 第二根跳空向上
        let gap_up = low[i - 1] > high[i - 2].max(high[i]);
        if gap_up {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Upside Gap Two Crows（向上跳空二乌鸦）
///
/// 识别标准（三根蜡烛组合）：
/// - 第一根：大阳线
/// - 第二根：小阴线，跳空向上
/// - 第三根：阴线，吞没第二根但未覆盖第一根
///
/// 返回值：-1.0 = Upside Gap Two Crows, 0.0 = 非向上跳空二乌鸦
pub fn upside_gap_two_crows(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    for i in 0..2 {
        result[i] = 0.0;
    }

    for i in 2..n {
        let first_bullish = is_bullish(open[i - 2], close[i - 2]);
        let first_body = body_length(open[i - 2], close[i - 2]);

        let second_bearish = is_bearish(open[i - 1], close[i - 1]);
        let third_bearish = is_bearish(open[i], close[i]);

        if !first_bullish || !second_bearish || !third_bearish {
            result[i] = 0.0;
            continue;
        }

        // 第二根跳空向上
        let gap_up = open[i - 1] > close[i - 2];

        // 第三根吞没第二根
        let engulfs_second = open[i] > open[i - 1] && close[i] < close[i - 1];

        // 第三根未覆盖第一根
        let not_covers_first = close[i] > close[i - 2];

        // 第一根是大实体
        let large_first = first_body > 0.0;

        if gap_up && engulfs_second && not_covers_first && large_first {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Gap Sidesidewhite（跳空并列白线）
///
/// 识别标准（三根蜡烛组合）：
/// - 第一根：阳线或阴线
/// - 第二、三根：两根相似的阳线，跳空并列
///
/// 返回值：1.0 = Upside Gap Sidesidewhite, -1.0 = Downside, 0.0 = 非跳空并列白线
pub fn gap_sidesidewhite(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    for i in 0..2 {
        result[i] = 0.0;
    }

    for i in 2..n {
        let second_bullish = is_bullish(open[i - 1], close[i - 1]);
        let third_bullish = is_bullish(open[i], close[i]);

        if !second_bullish || !third_bullish {
            result[i] = 0.0;
            continue;
        }

        let second_body = body_length(open[i - 1], close[i - 1]);
        let third_body = body_length(open[i], close[i]);

        // 第二、三根实体相似
        let similar_bodies = (second_body - third_body).abs() < second_body * 0.3;

        // 第二、三根开盘价接近
        let similar_opens = (open[i - 1] - open[i]).abs() < open[i - 1] * 0.02;

        // Upside Gap
        let first_bullish = is_bullish(open[i - 2], close[i - 2]);
        let gap_up = open[i - 1] > close[i - 2];
        if first_bullish && gap_up && similar_bodies && similar_opens {
            result[i] = 1.0;
            continue;
        }

        // Downside Gap
        let first_bearish = is_bearish(open[i - 2], close[i - 2]);
        let gap_down = close[i - 1] < open[i - 2];
        if first_bearish && gap_down && similar_bodies && similar_opens {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Takuri（探水竿）
///
/// 识别标准（单根蜡烛）：
/// - 蜻蜓十字星的增强版
/// - 下影线非常长（>= 实体的 5 倍）
/// - 几乎没有上影线
///
/// 返回值：1.0 = Takuri, 0.0 = 非探水竿
pub fn takuri(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    for i in 0..n {
        let body = body_length(open[i], close[i]);
        let lower = lower_shadow(low[i], open[i], close[i]);
        let upper = upper_shadow(high[i], open[i], close[i]);
        let range = total_range(high[i], low[i]);

        // 下影线非常长
        let long_lower_shadow = lower >= body * 5.0 || (body < range * 0.1 && lower > range * 0.6);

        // 几乎没有上影线
        let minimal_upper = upper < range * 0.1;

        if long_lower_shadow && minimal_upper {
            result[i] = 1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Homing Pigeon（信鸽）
///
/// 识别标准（两根蜡烛组合）：
/// - 第一根：大阴线
/// - 第二根：小阴线，完全在第一根实体内
///
/// 返回值：1.0 = Homing Pigeon, 0.0 = 非信鸽
pub fn homing_pigeon(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let first_bearish = is_bearish(open[i - 1], close[i - 1]);
        let second_bearish = is_bearish(open[i], close[i]);

        if !first_bearish || !second_bearish {
            result[i] = 0.0;
            continue;
        }

        let first_body = body_length(open[i - 1], close[i - 1]);
        let second_body = body_length(open[i], close[i]);

        // 第二根是小阴线
        let small_second = second_body < first_body * 0.5;

        // 第二根完全在第一根实体内
        let second_inside = open[i] < open[i - 1] && close[i] > close[i - 1];

        if small_second && second_inside {
            result[i] = 1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Matching Low（低价匹配）
///
/// 识别标准（两根蜡烛组合）：
/// - 两根连续阴线
/// - 收盘价几乎相同
/// - 出现在下跌趋势中
///
/// 返回值：1.0 = Matching Low, 0.0 = 非低价匹配
pub fn matching_low(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    tolerance: f64, // 默认 0.01 (1%)
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let first_bearish = is_bearish(open[i - 1], close[i - 1]);
        let second_bearish = is_bearish(open[i], close[i]);

        if !first_bearish || !second_bearish {
            result[i] = 0.0;
            continue;
        }

        // 收盘价接近
        let closes_match = (close[i] - close[i - 1]).abs() / close[i - 1] < tolerance;

        if closes_match {
            result[i] = 1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Separating Lines（分离线）
///
/// 识别标准（两根蜡烛组合）：
/// - 看涨版本：第一根阴线 + 第二根阳线，开盘价相同
/// - 看跌版本：第一根阳线 + 第二根阴线，开盘价相同
///
/// 返回值：1.0 = Bullish Separating Lines, -1.0 = Bearish, 0.0 = 非分离线
pub fn separating_lines(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    tolerance: f64, // 默认 0.005 (0.5%)
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        // 开盘价相同
        let opens_match = (open[i] - open[i - 1]).abs() / open[i - 1] < tolerance;

        if !opens_match {
            result[i] = 0.0;
            continue;
        }

        // Bullish Separating Lines
        let first_bearish = is_bearish(open[i - 1], close[i - 1]);
        let second_bullish = is_bullish(open[i], close[i]);
        if first_bearish && second_bullish {
            result[i] = 1.0;
            continue;
        }

        // Bearish Separating Lines
        let first_bullish = is_bullish(open[i - 1], close[i - 1]);
        let second_bearish = is_bearish(open[i], close[i]);
        if first_bullish && second_bearish {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Thrusting Pattern（插入形态）
///
/// 识别标准（两根蜡烛组合）：
/// - 第一根：阴线
/// - 第二根：阳线，开盘低于第一根最低，收盘在第一根实体中部以下
///
/// 返回值：-1.0 = Thrusting Pattern, 0.0 = 非插入形态
pub fn thrusting(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let first_bearish = is_bearish(open[i - 1], close[i - 1]);
        let second_bullish = is_bullish(open[i], close[i]);

        if !first_bearish || !second_bullish {
            result[i] = 0.0;
            continue;
        }

        // 第二根开盘低于第一根最低
        let opens_below = open[i] < low[i - 1];

        // 第二根收盘在第一根实体中部以下
        let midpoint = (open[i - 1] + close[i - 1]) / 2.0;
        let closes_below_mid = close[i] < midpoint && close[i] > close[i - 1];

        if opens_below && closes_below_mid {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// In-Neck Pattern（颈内线）
///
/// 识别标准（两根蜡烛组合）：
/// - 第一根：大阴线
/// - 第二根：阳线，收盘价接近第一根最低
///
/// 返回值：-1.0 = In-Neck Pattern, 0.0 = 非颈内线
pub fn inneck(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    tolerance: f64, // 默认 0.01 (1%)
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let first_bearish = is_bearish(open[i - 1], close[i - 1]);
        let second_bullish = is_bullish(open[i], close[i]);

        if !first_bearish || !second_bullish {
            result[i] = 0.0;
            continue;
        }

        // 第二根收盘价接近第一根最低
        let closes_near_low = (close[i] - low[i - 1]).abs() / low[i - 1] < tolerance;

        if closes_near_low {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// On-Neck Pattern（颈上线）
///
/// 识别标准（两根蜡烛组合）：
/// - 第一根：大阴线
/// - 第二根：小阳线，收盘价接近第一根收盘价
///
/// 返回值：-1.0 = On-Neck Pattern, 0.0 = 非颈上线
pub fn onneck(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    tolerance: f64, // 默认 0.01 (1%)
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 2 {
        return Ok(result);
    }

    result[0] = 0.0;

    for i in 1..n {
        let first_bearish = is_bearish(open[i - 1], close[i - 1]);
        let second_bullish = is_bullish(open[i], close[i]);

        if !first_bearish || !second_bullish {
            result[i] = 0.0;
            continue;
        }

        // 第二根收盘价接近第一根收盘价
        let closes_match = (close[i] - close[i - 1]).abs() / close[i - 1] < tolerance;

        // 第二根是小实体
        let small_second =
            body_length(open[i], close[i]) < body_length(open[i - 1], close[i - 1]) * 0.3;

        if closes_match && small_second {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Advance Block（前进阻挡）
///
/// 识别标准（三根蜡烛组合）：
/// - 三根连续阳线
/// - 每根实体递减
/// - 上影线递增
///
/// 返回值：-1.0 = Advance Block, 0.0 = 非前进阻挡
pub fn advance_block(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    for i in 0..2 {
        result[i] = 0.0;
    }

    for i in 2..n {
        let first_bullish = is_bullish(open[i - 2], close[i - 2]);
        let second_bullish = is_bullish(open[i - 1], close[i - 1]);
        let third_bullish = is_bullish(open[i], close[i]);

        if !first_bullish || !second_bullish || !third_bullish {
            result[i] = 0.0;
            continue;
        }

        let first_body = body_length(open[i - 2], close[i - 2]);
        let second_body = body_length(open[i - 1], close[i - 1]);
        let third_body = body_length(open[i], close[i]);

        let first_upper = upper_shadow(high[i - 2], open[i - 2], close[i - 2]);
        let second_upper = upper_shadow(high[i - 1], open[i - 1], close[i - 1]);
        let third_upper = upper_shadow(high[i], open[i], close[i]);

        // 实体递减
        let decreasing_bodies = second_body < first_body && third_body < second_body;

        // 上影线递增
        let increasing_upper = second_upper > first_upper && third_upper > second_upper;

        if decreasing_bodies && increasing_upper {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Stalled Pattern（停顿形态）
///
/// 识别标准（三根蜡烛组合）：
/// - 三根连续阳线
/// - 第三根实体很小，上影线长
/// - 表示上涨动能减弱
///
/// 返回值：-1.0 = Stalled Pattern, 0.0 = 非停顿形态
pub fn stalled_pattern(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    if n < 3 {
        return Ok(result);
    }

    for i in 0..2 {
        result[i] = 0.0;
    }

    for i in 2..n {
        let first_bullish = is_bullish(open[i - 2], close[i - 2]);
        let second_bullish = is_bullish(open[i - 1], close[i - 1]);
        let third_bullish = is_bullish(open[i], close[i]);

        if !first_bullish || !second_bullish || !third_bullish {
            result[i] = 0.0;
            continue;
        }

        let first_body = body_length(open[i - 2], close[i - 2]);
        let second_body = body_length(open[i - 1], close[i - 1]);
        let third_body = body_length(open[i], close[i]);
        let third_upper = upper_shadow(high[i], open[i], close[i]);

        // 第三根实体很小
        let small_third = third_body < first_body * 0.3 && third_body < second_body * 0.3;

        // 第三根上影线长
        let long_upper = third_upper > third_body * 2.0;

        if small_third && long_upper {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Belt Hold（捉腰带）
///
/// 识别标准（单根蜡烛）：
/// - 看涨版本：大阳线，几乎没有下影线
/// - 看跌版本：大阴线，几乎没有上影线
///
/// 返回值：1.0 = Bullish Belt Hold, -1.0 = Bearish Belt Hold, 0.0 = 非捉腰带
pub fn belthold(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = init_result!(n);

    for i in 0..n {
        let body = body_length(open[i], close[i]);
        let range = total_range(high[i], low[i]);
        let upper = upper_shadow(high[i], open[i], close[i]);
        let lower = lower_shadow(low[i], open[i], close[i]);

        // 实体占比大
        let large_body = body > range * 0.8;

        // Bullish Belt Hold: 几乎没有下影线
        if is_bullish(open[i], close[i]) && large_body && lower < range * 0.1 {
            result[i] = 1.0;
        }
        // Bearish Belt Hold: 几乎没有上影线
        else if is_bearish(open[i], close[i]) && large_body && upper < range * 0.1 {
            result[i] = -1.0;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Concealing Baby Swallow（隐身燕子）- TA-Lib兼容
///
/// 4根蜡烛的看涨反转形态（下降趋势底部）
///
/// 规则：
/// 1. 前两根：两个大跌的黑色蜡烛
/// 2. 第三根：跳空低开的黑色蜡烛
/// 3. 第四根：完全吞没第三根的黑色蜡烛（但收盘价仍低于第二根）
pub fn concealing_baby_swallow(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = vec![0.0; n];

    if n < 4 {
        return Ok(result);
    }

    for i in 3..n {
        let first_bearish = is_bearish(open[i - 3], close[i - 3]);
        let second_bearish = is_bearish(open[i - 2], close[i - 2]);
        let third_bearish = is_bearish(open[i - 1], close[i - 1]);
        let fourth_bearish = is_bearish(open[i], close[i]);

        if !first_bearish || !second_bearish || !third_bearish || !fourth_bearish {
            continue;
        }

        let first_body = body_length(open[i - 3], close[i - 3]);
        let second_body = body_length(open[i - 2], close[i - 2]);
        let avg_body = average_body_length(open, close, i - 3, 2);

        // 前两根是大跌蜡烛
        let large_bearish = first_body >= avg_body && second_body >= avg_body;

        // 第三根跳空低开
        let third_gap_down = open[i - 1] < close[i - 2];

        // 第四根吞没第三根
        let fourth_engulfs_third = open[i] > open[i - 1] && close[i] < close[i - 1];

        // 第四根仍在第二根下方
        let fourth_below_second = close[i] < close[i - 2];

        if large_bearish && third_gap_down && fourth_engulfs_third && fourth_below_second {
            result[i] = 1.0; // 看涨隐身燕子
        }
    }

    Ok(result)
}

/// Counterattack（反击线）- TA-Lib兼容
///
/// 两根蜡烛的反转形态，收盘价相同但方向相反
///
/// tolerance: 价格匹配容差（默认0.005 = 0.5%）
pub fn counterattack(
    open: &[f64],
    _high: &[f64],
    _low: &[f64],
    close: &[f64],
    tolerance: f64,
) -> HazeResult<Vec<f64>> {
    let n = open.len().min(close.len());
    let mut result = vec![0.0; n];

    if n < 2 {
        return Ok(result);
    }

    for i in 1..n {
        let first_range = body_length(open[i - 1], close[i - 1]);
        let second_range = body_length(open[i], close[i]);

        let first_body = body_length(open[i - 1], close[i - 1]);
        let second_body = body_length(open[i], close[i]);

        // 两根都是大实体
        let first_large = first_range > 0.0 && first_body > first_range * 0.7;
        let second_large = second_range > 0.0 && second_body > second_range * 0.7;

        if !first_large || !second_large {
            continue;
        }

        // 收盘价相同（容差范围内）
        let close_match = (close[i] - close[i - 1]).abs() < close[i - 1] * tolerance;

        if !close_match {
            continue;
        }

        // 看涨反击线：第一根大跌，第二根大涨但收盘价相同
        if is_bearish(open[i - 1], close[i - 1]) && is_bullish(open[i], close[i]) {
            result[i] = 1.0;
        }
        // 看跌反击线：第一根大涨，第二根大跌但收盘价相同
        else if is_bullish(open[i - 1], close[i - 1]) && is_bearish(open[i], close[i]) {
            result[i] = -1.0;
        }
    }

    Ok(result)
}

/// High-Wave Candle（高浪线）- TA-Lib兼容
///
/// 小实体、长上下影线的蜡烛，表示市场犹豫
///
/// body_threshold: 实体与总范围比例阈值（默认0.15 = 15%）
pub fn highwave(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    body_threshold: f64,
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = vec![0.0; n];

    for i in 0..n {
        let range = total_range(high[i], low[i]);
        let body = body_length(open[i], close[i]);
        let upper = upper_shadow(high[i], open[i], close[i]);
        let lower = lower_shadow(low[i], open[i], close[i]);

        // 小实体
        let small_body = range > 0.0 && body < range * body_threshold;

        // 上下影线都很长（都超过实体的2倍）
        let long_shadows = upper > body * 2.0 && lower > body * 2.0;

        if small_body && long_shadows {
            result[i] = 1.0; // 高浪线（不分方向）
        }
    }

    Ok(result)
}

/// Hikkake Pattern（陷阱形态）- TA-Lib兼容
///
/// 3根蜡烛的假突破形态
///
/// 规则：
/// 1. 第一根：普通K线
/// 2. 第二根：内包于第一根（范围更小）
/// 3. 第三根：突破第二根但未突破第一根（陷阱）
pub fn hikkake(_open: &[f64], high: &[f64], low: &[f64], _close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = high.len().min(low.len());
    let mut result = vec![0.0; n];

    if n < 3 {
        return Ok(result);
    }

    for i in 2..n {
        // 第二根内包于第一根
        let second_inside_first = high[i - 1] < high[i - 2] && low[i - 1] > low[i - 2];

        if !second_inside_first {
            continue;
        }

        // 看涨陷阱：第三根高点突破第二根但未突破第一根
        let bullish_trap = high[i] > high[i - 1] && high[i] < high[i - 2];

        // 看跌陷阱：第三根低点突破第二根但未突破第一根
        let bearish_trap = low[i] < low[i - 1] && low[i] > low[i - 2];

        if bullish_trap {
            result[i] = 1.0; // 看涨陷阱（假向上突破）
        } else if bearish_trap {
            result[i] = -1.0; // 看跌陷阱（假向下突破）
        }
    }

    Ok(result)
}

/// Modified Hikkake Pattern（改良陷阱形态）- TA-Lib兼容
///
/// Hikkake的改进版本，要求确认蜡烛
pub fn hikkake_mod(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = vec![0.0; n];

    if n < 4 {
        return Ok(result);
    }

    // 先计算基础Hikkake信号
    let basic_hikkake = hikkake(open, high, low, close)?;

    for i in 3..n {
        // 检查前一根是否有Hikkake信号
        if is_zero(basic_hikkake[i - 1]) {
            continue;
        }

        // 看涨确认：当前蜡烛收盘价高于Hikkake蜡烛
        if basic_hikkake[i - 1] == 1.0 && close[i] > close[i - 1] {
            result[i] = 1.0;
        }
        // 看跌确认：当前蜡烛收盘价低于Hikkake蜡烛
        else if basic_hikkake[i - 1] == -1.0 && close[i] < close[i - 1] {
            result[i] = -1.0;
        }
    }

    Ok(result)
}

/// Ladder Bottom（梯底）- TA-Lib兼容
///
/// 5根蜡烛的看涨反转形态（下降趋势底部）
///
/// 规则：
/// 1. 前三根：连续下跌的黑色蜡烛
/// 2. 第四根：继续下跌，出现下影线
/// 3. 第五根：白色蜡烛，跳空高开
pub fn ladder_bottom(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = vec![0.0; n];

    if n < 5 {
        return Ok(result);
    }

    for i in 4..n {
        // 前三根连续下跌的黑色蜡烛
        let first_three_bearish = is_bearish(open[i - 4], close[i - 4])
            && is_bearish(open[i - 3], close[i - 3])
            && is_bearish(open[i - 2], close[i - 2]);

        let descending = close[i - 3] < close[i - 4] && close[i - 2] < close[i - 3];

        if !first_three_bearish || !descending {
            continue;
        }

        // 第四根继续下跌，且有下影线
        let fourth_bearish = is_bearish(open[i - 1], close[i - 1]);
        let fourth_has_lower_shadow = lower_shadow(low[i - 1], open[i - 1], close[i - 1]) > 0.0;
        let fourth_continues_down = close[i - 1] < close[i - 2];

        if !fourth_bearish || !fourth_has_lower_shadow || !fourth_continues_down {
            continue;
        }

        // 第五根白色蜡烛，跳空高开
        let fifth_bullish = is_bullish(open[i], close[i]);
        let fifth_gap_up = open[i] > close[i - 1];

        if fifth_bullish && fifth_gap_up {
            result[i] = 1.0; // 梯底形态
        }
    }

    Ok(result)
}

/// Mat Hold（垫托）- TA-Lib兼容
///
/// 5根蜡烛的持续形态（上升趋势中的回调确认）
pub fn mat_hold(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = vec![0.0; n];

    if n < 5 {
        return Ok(result);
    }

    for i in 4..n {
        // 第一根：大涨的白色蜡烛
        let first_bullish = is_bullish(open[i - 4], close[i - 4]);
        let first_body = body_length(open[i - 4], close[i - 4]);
        let avg_body = average_body_length(open, close, i - 4, 5);
        let first_large = first_body > avg_body * 1.5;

        if !first_bullish || !first_large {
            continue;
        }

        // 中间三根：小幅回调（可以跳空）
        let second_small = body_length(open[i - 3], close[i - 3]) < first_body * 0.5;
        let third_small = body_length(open[i - 2], close[i - 2]) < first_body * 0.5;
        let fourth_small = body_length(open[i - 1], close[i - 1]) < first_body * 0.5;

        // 中间三根收盘价低于第一根收盘价
        let pullback = close[i - 3] < close[i - 4]
            && close[i - 2] < close[i - 4]
            && close[i - 1] < close[i - 4];

        if !second_small || !third_small || !fourth_small || !pullback {
            continue;
        }

        // 第五根：白色蜡烛，收盘价创新高
        let fifth_bullish = is_bullish(open[i], close[i]);
        let fifth_new_high = close[i] > close[i - 4];

        if fifth_bullish && fifth_new_high {
            result[i] = 1.0; // 垫托形态
        }
    }

    Ok(result)
}

/// Rickshaw Man（黄包车夫）- TA-Lib兼容
///
/// Doji的一种，开盘价和收盘价都在K线中间位置
///
/// body_threshold: 实体与总范围比例阈值（默认0.1 = 10%）
pub fn rickshaw_man(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    body_threshold: f64,
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = vec![0.0; n];

    for i in 0..n {
        let range = total_range(high[i], low[i]);
        let body = body_length(open[i], close[i]);

        // 是Doji（小实体）
        let is_doji = range > 0.0 && body < range * body_threshold;

        if !is_doji {
            continue;
        }

        // 开盘价/收盘价在K线中间位置（距离两端都有一定距离）
        let mid_price = (high[i] + low[i]) / 2.0;
        let open_close_avg = (open[i] + close[i]) / 2.0;

        // 平均价格在中间区域（±20%范围内）
        let in_middle = (open_close_avg - mid_price).abs() < range * 0.2;

        if in_middle {
            result[i] = 1.0; // 黄包车夫
        }
    }

    Ok(result)
}

/// Unique 3 River（独特三川）- TA-Lib兼容
///
/// 3根蜡烛的看涨反转形态
///
/// 规则：
/// 1. 第一根：大跌的黑色蜡烛
/// 2. 第二根：小锤子线，创新低
/// 3. 第三根：小白色蜡烛，收盘价在第一根实体内
pub fn unique_3_river(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = vec![0.0; n];

    if n < 3 {
        return Ok(result);
    }

    for i in 2..n {
        // 第一根：大跌的黑色蜡烛
        let first_bearish = is_bearish(open[i - 2], close[i - 2]);
        let first_body = body_length(open[i - 2], close[i - 2]);
        let avg_body = average_body_length(open, close, i - 2, 3);
        let first_large = first_body > avg_body * 1.5;

        if !first_bearish || !first_large {
            continue;
        }

        // 第二根：小黑色蜡烛，类似锤子（长下影线），创新低
        let second_bearish = is_bearish(open[i - 1], close[i - 1]);
        let second_body = body_length(open[i - 1], close[i - 1]);
        let second_lower = lower_shadow(low[i - 1], open[i - 1], close[i - 1]);
        let second_hammer_like = second_lower > second_body * 2.0;
        let second_new_low = low[i - 1] < low[i - 2];

        if !second_bearish || !second_hammer_like || !second_new_low {
            continue;
        }

        // 第三根：小白色蜡烛，收盘价在第一根实体内
        let third_bullish = is_bullish(open[i], close[i]);
        let third_body = body_length(open[i], close[i]);
        let third_small = third_body < avg_body * 0.5;
        let third_in_first_body = close[i] > close[i - 2] && close[i] < open[i - 2];

        if third_bullish && third_small && third_in_first_body {
            result[i] = 1.0; // 独特三川
        }
    }

    Ok(result)
}

/// Upside/Downside Gap Three Methods（跳空三法）- TA-Lib兼容
///
/// 3根蜡烛的持续形态，缺口被第三根K线填补
pub fn xside_gap_3_methods(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = vec![0.0; n];

    if n < 3 {
        return Ok(result);
    }

    for i in 2..n {
        let first_bullish = is_bullish(open[i - 2], close[i - 2]);
        let second_bullish = is_bullish(open[i - 1], close[i - 1]);
        let third_bearish = is_bearish(open[i], close[i]);

        // 向上跳空三法：前两根白色蜡烛有缺口，第三根黑色填补缺口
        if first_bullish && second_bullish && third_bearish {
            let upside_gap = low[i - 1] > high[i - 2]; // 向上缺口
            let gap_filled = close[i] < low[i - 1] && close[i] > high[i - 2]; // 填补缺口

            if upside_gap && gap_filled {
                result[i] = 1.0; // 向上跳空三法（看涨持续）
            }
        }

        let first_bearish = is_bearish(open[i - 2], close[i - 2]);
        let second_bearish = is_bearish(open[i - 1], close[i - 1]);
        let third_bullish = is_bullish(open[i], close[i]);

        // 向下跳空三法：前两根黑色蜡烛有缺口，第三根白色填补缺口
        if first_bearish && second_bearish && third_bullish {
            let downside_gap = high[i - 1] < low[i - 2]; // 向下缺口
            let gap_filled = close[i] > high[i - 1] && close[i] < low[i - 2]; // 填补缺口

            if downside_gap && gap_filled {
                result[i] = -1.0; // 向下跳空三法（看跌持续）
            }
        }
    }

    Ok(result)
}

/// Closing Marubozu（收盘光脚）- TA-Lib兼容
///
/// 一根蜡烛，收盘价等于最高价（看涨）或最低价（看跌）
pub fn closing_marubozu(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = vec![0.0; n];

    for i in 0..n {
        let range = total_range(high[i], low[i]);
        let body = body_length(open[i], close[i]);

        // 大实体
        let large_body = range > 0.0 && body > range * 0.8;

        if !large_body {
            continue;
        }

        // 看涨收盘光脚：收盘价等于最高价（无上影线）
        if is_bullish(open[i], close[i]) && (high[i] - close[i]) < range * 0.05 {
            result[i] = 1.0;
        }
        // 看跌收盘光脚：收盘价等于最低价（无下影线）
        else if is_bearish(open[i], close[i]) && (close[i] - low[i]) < range * 0.05 {
            result[i] = -1.0;
        }
    }

    Ok(result)
}

/// Breakaway（脱离）- TA-Lib兼容
///
/// 5根蜡烛的反转形态
///
/// 规则：
/// 1. 第一根：大蜡烛，设定趋势方向
/// 2. 第二根：跳空同方向
/// 3. 第三、四根：持续同方向但幅度变小
/// 4. 第五根：反向大蜡烛，收盘价填补部分缺口
pub fn breakaway(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    let n = validate_full_ohlc!(open, high, low, close);
    let mut result = vec![0.0; n];

    if n < 5 {
        return Ok(result);
    }

    for i in 4..n {
        let avg_body = average_body_length(open, close, i - 4, 5);

        // 看涨脱离
        let first_bearish_large = is_bearish(open[i - 4], close[i - 4])
            && body_length(open[i - 4], close[i - 4]) > avg_body * 1.2;
        let second_gap_down = open[i - 3] < close[i - 4];
        let second_bearish = is_bearish(open[i - 3], close[i - 3]);
        let third_bearish = is_bearish(open[i - 2], close[i - 2]);
        let fourth_bearish = is_bearish(open[i - 1], close[i - 1]);
        let fifth_bullish_large =
            is_bullish(open[i], close[i]) && body_length(open[i], close[i]) > avg_body * 1.2;
        let fifth_fills_gap = close[i] > close[i - 3] && close[i] < open[i - 4];

        if first_bearish_large
            && second_gap_down
            && second_bearish
            && third_bearish
            && fourth_bearish
            && fifth_bullish_large
            && fifth_fills_gap
        {
            result[i] = 1.0; // 看涨脱离
        }

        // 看跌脱离
        let first_bullish_large = is_bullish(open[i - 4], close[i - 4])
            && body_length(open[i - 4], close[i - 4]) > avg_body * 1.2;
        let second_gap_up = open[i - 3] > close[i - 4];
        let second_bullish = is_bullish(open[i - 3], close[i - 3]);
        let third_bullish = is_bullish(open[i - 2], close[i - 2]);
        let fourth_bullish = is_bullish(open[i - 1], close[i - 1]);
        let fifth_bearish_large =
            is_bearish(open[i], close[i]) && body_length(open[i], close[i]) > avg_body * 1.2;
        let fifth_fills_gap = close[i] < close[i - 3] && close[i] > open[i - 4];

        if first_bullish_large
            && second_gap_up
            && second_bullish
            && third_bullish
            && fourth_bullish
            && fifth_bearish_large
            && fifth_fills_gap
        {
            result[i] = -1.0; // 看跌脱离
        }
    }

    Ok(result)
}

#[cfg(test)]
mod tests_extended {
    use super::*;

    #[test]
    fn test_average_body_length_empty() {
        let open = vec![1.0];
        let close = vec![1.0];
        let avg = average_body_length(&open, &close, 1, 0);
        assert_eq!(avg, 0.0);
    }

    #[test]
    fn test_marubozu() {
        let open = vec![100.0];
        let high = vec![110.0];
        let low = vec![99.9]; // 几乎没有下影线
        let close = vec![109.9]; // 几乎没有上影线

        let result = marubozu(&open, &high, &low, &close).unwrap();
        assert_eq!(result[0], 1.0); // Bullish Marubozu
    }

    #[test]
    fn test_spinning_top() {
        let open = vec![100.0];
        let high = vec![110.0];
        let low = vec![90.0];
        let close = vec![101.0]; // 小实体，长影线

        let result = spinning_top(&open, &high, &low, &close).unwrap();
        assert_eq!(result[0], 1.0);
    }

    #[test]
    fn test_dragonfly_doji() {
        let open = vec![100.0];
        let high = vec![100.5]; // 很短上影线
        let low = vec![90.0]; // 长下影线
        let close = vec![100.2]; // 接近开盘价

        let result = dragonfly_doji(&open, &high, &low, &close, 0.1).unwrap();
        assert_eq!(result[0], 1.0);
    }

    #[test]
    fn test_tweezers_top() {
        let open = vec![100.0, 105.0];
        let high = vec![110.0, 110.1]; // 最高价接近
        let close = vec![108.0, 103.0]; // 第一根阳线，第二根阴线

        let result = tweezers_top(&open, &high, &close, 0.01).unwrap();
        assert_eq!(result[1], -1.0);
    }
}
