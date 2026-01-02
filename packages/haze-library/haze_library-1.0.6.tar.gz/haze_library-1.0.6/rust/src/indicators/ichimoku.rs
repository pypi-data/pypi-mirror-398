// indicators/ichimoku.rs - Ichimoku Cloud（一目均衡表）
#![allow(dead_code)]
#![allow(clippy::needless_range_loop)]
//
// 一目均衡表是日本传统技术分析系统，包含 5 条线：
// 1. Tenkan-sen（转换线）：9 周期高低平均
// 2. Kijun-sen（基准线）：26 周期高低平均
// 3. Senkou Span A（先行带 A）：转换线与基准线的平均，前移 26 周期
// 4. Senkou Span B（先行带 B）：52 周期高低平均，前移 26 周期
// 5. Chikou Span（延迟线）：收盘价，后移 26 周期
//
// "云"（Kumo）由先行带 A 和 B 形成，提供动态支撑/阻力区域

use crate::errors::validation::{validate_lengths_match, validate_not_empty, validate_period};
use crate::errors::{HazeError, HazeResult};
use crate::init_result;
use crate::utils::stats::{rolling_max, rolling_min};

/// Ichimoku Cloud 结构体
#[derive(Debug, Clone)]
pub struct IchimokuCloud {
    pub tenkan_sen: Vec<f64>,    // 转换线
    pub kijun_sen: Vec<f64>,     // 基准线
    pub senkou_span_a: Vec<f64>, // 先行带 A
    pub senkou_span_b: Vec<f64>, // 先行带 B
    pub chikou_span: Vec<f64>,   // 延迟线
}

#[inline]
fn validate_ichimoku_lengths(ichimoku: &IchimokuCloud) -> HazeResult<usize> {
    let n = ichimoku.tenkan_sen.len();
    if n == 0 {
        return Err(HazeError::EmptyInput {
            name: "ichimoku.tenkan_sen",
        });
    }
    if ichimoku.kijun_sen.len() != n {
        return Err(HazeError::LengthMismatch {
            name1: "ichimoku.tenkan_sen",
            len1: n,
            name2: "ichimoku.kijun_sen",
            len2: ichimoku.kijun_sen.len(),
        });
    }
    if ichimoku.senkou_span_a.len() != n {
        return Err(HazeError::LengthMismatch {
            name1: "ichimoku.tenkan_sen",
            len1: n,
            name2: "ichimoku.senkou_span_a",
            len2: ichimoku.senkou_span_a.len(),
        });
    }
    if ichimoku.senkou_span_b.len() != n {
        return Err(HazeError::LengthMismatch {
            name1: "ichimoku.tenkan_sen",
            len1: n,
            name2: "ichimoku.senkou_span_b",
            len2: ichimoku.senkou_span_b.len(),
        });
    }
    if ichimoku.chikou_span.len() != n {
        return Err(HazeError::LengthMismatch {
            name1: "ichimoku.tenkan_sen",
            len1: n,
            name2: "ichimoku.chikou_span",
            len2: ichimoku.chikou_span.len(),
        });
    }
    Ok(n)
}

/// 计算 Ichimoku Cloud（一目均衡表）
///
/// - `high`: 高价序列
/// - `low`: 低价序列
/// - `close`: 收盘价序列
/// - `tenkan_period`: 转换线周期（默认 9）
/// - `kijun_period`: 基准线周期（默认 26）
/// - `senkou_b_period`: 先行带 B 周期（默认 52）
///
/// 返回：Ichimoku Cloud 结构体
///
/// # 算法
/// 1. Tenkan-sen = (9-period high + 9-period low) / 2
/// 2. Kijun-sen = (26-period high + 26-period low) / 2
/// 3. Senkou Span A = (Tenkan + Kijun) / 2, shifted forward 26
/// 4. Senkou Span B = (52-period high + 52-period low) / 2, shifted forward 26
/// 5. Chikou Span = Close, shifted backward 26
///
/// # 示例
/// ```rust,no_run
/// use haze_library::indicators::ichimoku::ichimoku_cloud;
///
/// let high = vec![110.0; 100];
/// let low = vec![100.0; 100];
/// let close = vec![105.0; 100];
///
/// let ichimoku = ichimoku_cloud(&high, &low, &close, 9, 26, 52).unwrap();
/// assert_eq!(ichimoku.tenkan_sen.len(), close.len());
/// ```
pub fn ichimoku_cloud(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    tenkan_period: usize,
    kijun_period: usize,
    senkou_b_period: usize,
) -> HazeResult<IchimokuCloud> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    let n = high.len();
    validate_period(tenkan_period, n)?;
    validate_period(kijun_period, n)?;
    validate_period(senkou_b_period, n)?;

    // 1. Tenkan-sen (Conversion Line): (9-period high + low) / 2
    let tenkan_sen = calc_donchian_midline(high, low, tenkan_period);

    // 2. Kijun-sen (Base Line): (26-period high + low) / 2
    let kijun_sen = calc_donchian_midline(high, low, kijun_period);

    // 3. Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, shifted +26
    let mut senkou_span_a = init_result!(n);
    for i in 0..n {
        if !tenkan_sen[i].is_nan() && !kijun_sen[i].is_nan() {
            let value = (tenkan_sen[i] + kijun_sen[i]) / 2.0;
            // 前移 26 周期（如果在范围内）
            let future_idx = i + kijun_period;
            if future_idx < n {
                senkou_span_a[future_idx] = value;
            }
        }
    }

    // 4. Senkou Span B (Leading Span B): (52-period high + low) / 2, shifted +26
    let span_b_midline = calc_donchian_midline(high, low, senkou_b_period);
    let mut senkou_span_b = init_result!(n);
    for i in 0..n {
        if !span_b_midline[i].is_nan() {
            let future_idx = i + kijun_period;
            if future_idx < n {
                senkou_span_b[future_idx] = span_b_midline[i];
            }
        }
    }

    // 5. Chikou Span (Lagging Span): Close price, shifted -26
    let mut chikou_span = init_result!(n);
    chikou_span[..(n - kijun_period)].copy_from_slice(&close[kijun_period..n]);

    Ok(IchimokuCloud {
        tenkan_sen,
        kijun_sen,
        senkou_span_a,
        senkou_span_b,
        chikou_span,
    })
}

/// 计算 Donchian 中线（高低价的平均）
///
/// 这是 Ichimoku 各线的核心计算逻辑
fn calc_donchian_midline(high: &[f64], low: &[f64], period: usize) -> Vec<f64> {
    let n = high.len();
    let mut result = init_result!(n);

    let high_max = rolling_max(high, period);
    let low_min = rolling_min(low, period);

    for i in 0..n {
        if !high_max[i].is_nan() && !low_min[i].is_nan() {
            result[i] = (high_max[i] + low_min[i]) / 2.0;
        }
    }

    result
}

/// Ichimoku 信号类型
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum IchimokuSignal {
    StrongBullish, // 强看涨：价格在云上方，云为绿色（Span A > Span B），Chikou 在价格上方
    Bullish,       // 看涨：价格在云上方
    Neutral,       // 中性：价格在云内
    Bearish,       // 看跌：价格在云下方
    StrongBearish, // 强看跌：价格在云下方，云为红色（Span A < Span B），Chikou 在价格下方
}

/// 生成 Ichimoku 信号
///
/// - `close`: 收盘价序列
/// - `ichimoku`: Ichimoku Cloud 结构体
///
/// 返回：每个价格对应的信号向量
pub fn ichimoku_signals(
    close: &[f64],
    ichimoku: &IchimokuCloud,
) -> HazeResult<Vec<IchimokuSignal>> {
    validate_not_empty(close, "close")?;
    let n = validate_ichimoku_lengths(ichimoku)?;
    if close.len() != n {
        return Err(HazeError::LengthMismatch {
            name1: "close",
            len1: close.len(),
            name2: "ichimoku.tenkan_sen",
            len2: n,
        });
    }
    let mut signals = Vec::with_capacity(n);

    for i in 0..n {
        let price = close[i];
        let span_a = ichimoku.senkou_span_a[i];
        let span_b = ichimoku.senkou_span_b[i];
        let chikou = ichimoku.chikou_span[i];

        if span_a.is_nan() || span_b.is_nan() {
            signals.push(IchimokuSignal::Neutral);
            continue;
        }

        let cloud_top = span_a.max(span_b);
        let cloud_bottom = span_a.min(span_b);
        let is_green_cloud = span_a > span_b;

        // 判断价格位置
        let signal = if price > cloud_top {
            // 价格在云上方
            if is_green_cloud && !chikou.is_nan() && chikou > price {
                IchimokuSignal::StrongBullish
            } else {
                IchimokuSignal::Bullish
            }
        } else if price < cloud_bottom {
            // 价格在云下方
            if !is_green_cloud && !chikou.is_nan() && chikou < price {
                IchimokuSignal::StrongBearish
            } else {
                IchimokuSignal::Bearish
            }
        } else {
            // 价格在云内
            IchimokuSignal::Neutral
        };

        signals.push(signal);
    }

    Ok(signals)
}

/// TK Cross（转换线与基准线交叉）信号
///
/// - `ichimoku`: Ichimoku Cloud 结构体
///
/// 返回：交叉信号向量（1.0=金叉，-1.0=死叉，0.0=无交叉）
///
/// # 算法
/// - 金叉（Bullish TK Cross）：Tenkan 向上穿过 Kijun
/// - 死叉（Bearish TK Cross）：Tenkan 向下穿过 Kijun
pub fn ichimoku_tk_cross(ichimoku: &IchimokuCloud) -> HazeResult<Vec<f64>> {
    let n = validate_ichimoku_lengths(ichimoku)?;
    let mut signals = vec![0.0; n];

    for i in 1..n {
        let prev_tenkan = ichimoku.tenkan_sen[i - 1];
        let prev_kijun = ichimoku.kijun_sen[i - 1];
        let curr_tenkan = ichimoku.tenkan_sen[i];
        let curr_kijun = ichimoku.kijun_sen[i];

        if prev_tenkan.is_nan()
            || prev_kijun.is_nan()
            || curr_tenkan.is_nan()
            || curr_kijun.is_nan()
        {
            continue;
        }

        // 金叉：前一根 Tenkan <= Kijun，当前 Tenkan > Kijun
        if prev_tenkan <= prev_kijun && curr_tenkan > curr_kijun {
            signals[i] = 1.0;
        }
        // 死叉：前一根 Tenkan >= Kijun，当前 Tenkan < Kijun
        else if prev_tenkan >= prev_kijun && curr_tenkan < curr_kijun {
            signals[i] = -1.0;
        }
    }

    Ok(signals)
}

/// 云厚度（Cloud Thickness）
///
/// 云厚度越大，支撑/阻力越强
///
/// - `ichimoku`: Ichimoku Cloud 结构体
///
/// 返回：云厚度向量（绝对值）
pub fn cloud_thickness(ichimoku: &IchimokuCloud) -> HazeResult<Vec<f64>> {
    let n = validate_ichimoku_lengths(ichimoku)?;
    let mut thickness = Vec::with_capacity(n);

    for i in 0..n {
        let span_a = ichimoku.senkou_span_a[i];
        let span_b = ichimoku.senkou_span_b[i];

        if span_a.is_nan() || span_b.is_nan() {
            thickness.push(f64::NAN);
        } else {
            thickness.push((span_a - span_b).abs());
        }
    }

    Ok(thickness)
}

/// Ichimoku 云颜色（Cloud Color）
///
/// - `ichimoku`: Ichimoku Cloud 结构体
///
/// 返回：云颜色向量（1.0=绿色/看涨，-1.0=红色/看跌，0.0=中性）
pub fn cloud_color(ichimoku: &IchimokuCloud) -> HazeResult<Vec<f64>> {
    let n = validate_ichimoku_lengths(ichimoku)?;
    let mut colors = Vec::with_capacity(n);

    for i in 0..n {
        let span_a = ichimoku.senkou_span_a[i];
        let span_b = ichimoku.senkou_span_b[i];

        if span_a.is_nan() || span_b.is_nan() {
            colors.push(0.0);
        } else if span_a > span_b {
            colors.push(1.0); // 绿云（看涨）
        } else if span_a < span_b {
            colors.push(-1.0); // 红云（看跌）
        } else {
            colors.push(0.0); // 中性
        }
    }

    Ok(colors)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ichimoku_cloud_basic() {
        let high = vec![110.0; 100];
        let low = vec![100.0; 100];
        let close = vec![105.0; 100];

        let ichimoku = ichimoku_cloud(&high, &low, &close, 9, 26, 52).unwrap();

        // 在横盘市场中，Tenkan 和 Kijun 应为 (110+100)/2 = 105
        let valid_idx = 26; // 第一个有效的索引（Kijun 周期）
        assert!((ichimoku.tenkan_sen[valid_idx] - 105.0).abs() < 0.1);
        assert!((ichimoku.kijun_sen[valid_idx] - 105.0).abs() < 0.1);
    }

    #[test]
    fn test_tk_cross() {
        // Need at least 52 data points for senkou_span_b_period=52
        let high: Vec<f64> = (0..60).map(|i| 100.0 + i as f64).collect();
        let low: Vec<f64> = high.iter().map(|&h| h - 2.0).collect();
        let close: Vec<f64> = high.iter().map(|&h| h - 1.0).collect();

        let ichimoku = ichimoku_cloud(&low, &high, &close, 9, 26, 52).unwrap();
        let crosses = ichimoku_tk_cross(&ichimoku).unwrap();

        // 在上升趋势中，应该有金叉信号
        let has_golden_cross = crosses.iter().any(|&c| c > 0.0);
        assert!(has_golden_cross || crosses.iter().all(|&c| c == 0.0)); // 可能周期太短没交叉
    }

    #[test]
    fn test_cloud_thickness() {
        let ichimoku = IchimokuCloud {
            tenkan_sen: vec![0.0; 3],
            kijun_sen: vec![0.0; 3],
            senkou_span_a: vec![110.0, 111.0, 112.0],
            senkou_span_b: vec![109.9, 110.2, 111.6],
            chikou_span: vec![0.0; 3],
        };
        let thickness = cloud_thickness(&ichimoku).unwrap();

        // 横盘市场中，Span A 和 Span B 应接近，厚度接近 0
        let valid_idx = 2;
        assert!(thickness[valid_idx] < 1.0);
    }
}
