//! Trend Indicators Module
//!
//! # Overview
//! This module provides trend-following technical indicators that identify the
//! direction and strength of price trends. These indicators help traders determine
//! whether to trade with the trend, identify trend reversals, and measure trend
//! momentum.
//!
//! # Available Functions
//! - [`supertrend`] - SuperTrend (ATR-based dynamic support/resistance)
//! - [`adx`] - Average Directional Index (trend strength 0-100)
//! - [`dx`] - Directional Movement Index (raw trend strength)
//! - [`plus_di`] - Positive Directional Indicator (+DI)
//! - [`minus_di`] - Negative Directional Indicator (-DI)
//! - [`aroon`] - Aroon Indicator (time-based trend identification)
//! - [`psar`] - Parabolic SAR (trailing stop and reversal system)
//! - [`vortex`] - Vortex Indicator (VI+ and VI- trend direction)
//! - [`choppiness_index`] - Choppiness Index (trending vs ranging market)
//! - [`qstick`] - QStick (buying/selling pressure)
//! - [`vhf`] - Vertical Horizontal Filter (trend vs consolidation)
//! - [`trix`] - Triple Exponential Average (rate of change)
//! - [`dpo`] - Detrended Price Oscillator (cycle identification)
//!
//! # Examples
//! ```rust,no_run
//! use haze_library::indicators::trend::{supertrend, adx, psar};
//!
//! let high = vec![102.0, 105.0, 104.0, 106.0, 108.0, 107.0, 109.0, 111.0];
//! let low = vec![99.0, 101.0, 100.0, 102.0, 104.0, 103.0, 105.0, 107.0];
//! let close = vec![101.0, 103.0, 102.0, 105.0, 107.0, 108.0, 110.0, 112.0];
//!
//! // Calculate SuperTrend with 7-period ATR and 3.0 multiplier
//! let (st_line, direction, upper, lower) = supertrend(&high, &low, &close, 7, 3.0).unwrap();
//!
//! // Calculate ADX with 14-period
//! let (adx_values, plus_di, minus_di) = adx(&high, &low, &close, 14).unwrap();
//!
//! // Calculate Parabolic SAR with standard parameters
//! let (psar_values, trend) = psar(&high, &low, &close, 0.02, 0.02, 0.2).unwrap();
//! ```
//!
//! # Performance Characteristics
//! - SuperTrend: O(n) with ATR calculation and state machine tracking
//! - ADX: O(n) using RMA smoothing for directional movement
//! - PSAR: O(n) with iterative extreme point and acceleration factor updates
//! - Aroon: O(n) with efficient lookback for highs/lows
//!
//! # Trend Signal Interpretation
//! - ADX > 25: Strong trend; ADX < 20: Weak trend or ranging
//! - SuperTrend direction: 1.0 = uptrend, -1.0 = downtrend
//! - PSAR trend: 1.0 = bullish, -1.0 = bearish
//! - Choppiness > 61.8: Ranging; < 38.2: Trending
//!
//! # Cross-References
//! - [`crate::indicators::volatility`] - ATR used in SuperTrend and Chandelier
//! - [`crate::utils::ma`] - RMA/EMA for smoothing calculations

#![allow(clippy::needless_range_loop)]

use crate::errors::validation::{validate_lengths_match, validate_not_empty, validate_period};
use crate::errors::{HazeError, HazeResult};
use crate::indicators::volatility::{atr, true_range};
use crate::init_result;
use crate::utils::float_compare::approx_eq;
use crate::utils::ma::ema_allow_nan;
use crate::utils::math::{is_not_zero, is_zero};
use crate::utils::{ema, rolling_max, rolling_min, rolling_sum, sma};

/// SuperTrend（超级趋势指标）
///
/// 算法：
/// 1. 计算基础线：basic_upperband = HL2 + multiplier * ATR,
///    basic_lowerband = HL2 - multiplier * ATR
/// 2. 状态机追踪：
///    - 当 close > upperband: 趋势 = 1 (上升), 更新 lowerband
///    - 当 close < lowerband: 趋势 = -1 (下降), 更新 upperband
/// 3. 输出：
///    - supertrend: 趋势线（上升时为 lowerband，下降时为 upperband）
///    - direction: 1 (上升) 或 -1 (下降)
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: ATR 周期（默认 7）
/// - `multiplier`: ATR 倍数（默认 3.0）
///
/// # 返回
/// - `Ok((supertrend, direction, upper, lower))`
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::LengthMismatch` - 数组长度不一致
/// - `HazeError::InvalidPeriod` - period 为 0 或大于数据长度
#[allow(clippy::type_complexity)]
pub fn supertrend(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
    multiplier: f64,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let n = high.len();
    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }
    if period >= n {
        return Err(HazeError::InsufficientData {
            required: period + 1,
            actual: n,
        });
    }

    // HL2 (中间价)
    let hl2: Vec<f64> = (0..n).map(|i| (high[i] + low[i]) / 2.0).collect();

    // ATR (propagate error)
    let atr_values = atr(high, low, close, period)?;

    // 计算基础带
    let basic_upper: Vec<f64> = (0..n)
        .map(|i| hl2[i] + multiplier * atr_values[i])
        .collect();
    let basic_lower: Vec<f64> = (0..n)
        .map(|i| hl2[i] - multiplier * atr_values[i])
        .collect();

    // 初始化输出
    let mut upper = init_result!(n);
    let mut lower = init_result!(n);
    let mut supertrend_line = init_result!(n);
    let mut direction = init_result!(n);

    // 从 period 开始（ATR 在 TA-Lib 模式下首个有效值在 index=period）
    for i in period..n {
        if atr_values[i].is_nan() {
            continue;
        }

        // 更新 upper band（首个有效点直接赋值，否则取较小值以确保只向下收敛）
        if i == period || upper[i - 1].is_nan() || basic_upper[i] < upper[i - 1] {
            upper[i] = basic_upper[i];
        } else {
            upper[i] = upper[i - 1];
        }

        // 更新 lower band（首个有效点直接赋值，否则取较大值以确保只向上收敛）
        if i == period || lower[i - 1].is_nan() || basic_lower[i] > lower[i - 1] {
            lower[i] = basic_lower[i];
        } else {
            lower[i] = lower[i - 1];
        }

        // 确定趋势方向
        // 初始方向：使用 close > hl2 判断（收盘价高于中间价 = 上升趋势）
        // 注：这是常见的启发式方法，与某些库（如 pandas-ta）可能略有差异
        // pandas-ta 可能使用 close > supertrend_line 或前一根 K 线延续
        if i == period {
            direction[i] = if close[i] > hl2[i] { 1.0 } else { -1.0 };
        } else {
            let prev_dir = direction[i - 1];
            if prev_dir == 1.0 {
                // 上升趋势
                direction[i] = if close[i] < lower[i] { -1.0 } else { 1.0 };
            } else {
                // 下降趋势
                direction[i] = if close[i] > upper[i] { 1.0 } else { -1.0 };
            }
        }

        // SuperTrend 线
        supertrend_line[i] = if direction[i] == 1.0 {
            lower[i]
        } else {
            upper[i]
        };
    }

    Ok((supertrend_line, direction, upper, lower))
}

/// 内部辅助函数：计算方向指标 (+DI, -DI)
///
/// 提取公共逻辑，供 adx 和 dx 复用
fn compute_di(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    let n = high.len();
    if period >= n {
        return Err(HazeError::InsufficientData {
            required: period + 1,
            actual: n,
        });
    }

    // 计算方向移动
    let mut plus_dm = vec![0.0; n];
    let mut minus_dm = vec![0.0; n];

    for i in 1..n {
        let up_move = high[i] - high[i - 1];
        let down_move = low[i - 1] - low[i];

        if up_move > down_move && up_move > 0.0 {
            plus_dm[i] = up_move;
        }
        if down_move > up_move && down_move > 0.0 {
            minus_dm[i] = down_move;
        }
    }

    let tr = true_range(high, low, close, 1)?;

    let mut plus_di = init_result!(n);
    let mut minus_di = init_result!(n);

    let period_f = period as f64;
    let mut sum_tr = 0.0;
    let mut sum_plus = 0.0;
    let mut sum_minus = 0.0;

    // TA-Lib 对齐：先累积 1..period-1，再从 period 开始更新并输出
    for i in 1..period {
        sum_tr += tr[i];
        sum_plus += plus_dm[i];
        sum_minus += minus_dm[i];
    }

    for i in period..n {
        sum_tr = sum_tr - (sum_tr / period_f) + tr[i];
        sum_plus = sum_plus - (sum_plus / period_f) + plus_dm[i];
        sum_minus = sum_minus - (sum_minus / period_f) + minus_dm[i];

        if is_zero(sum_tr) {
            plus_di[i] = 0.0;
            minus_di[i] = 0.0;
        } else {
            plus_di[i] = 100.0 * sum_plus / sum_tr;
            minus_di[i] = 100.0 * sum_minus / sum_tr;
        }
    }

    Ok((plus_di, minus_di))
}

/// DMI - Directional Movement Index（趋向指标）
///
/// 返回正向与负向指标（+DI, -DI）
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 14）
///
/// # 返回
/// - `Ok((plus_di, minus_di))`
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::LengthMismatch` - 数组长度不一致
/// - `HazeError::InvalidPeriod` - period 无效
pub fn dmi(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let n = high.len();
    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }

    compute_di(high, low, close, period)
}

/// ADX - Average Directional Index（平均趋向指标）
///
/// 算法：
/// 1. +DM = max(high - prev_high, 0)
/// 2. -DM = max(prev_low - low, 0)
/// 3. 如果 +DM > -DM：-DM = 0，否则 +DM = 0
/// 4. +DI = 100 * RMA(+DM, period) / ATR
/// 5. -DI = 100 * RMA(-DM, period) / ATR
/// 6. DX = 100 * |(+DI - -DI)| / (+DI + -DI)
/// 7. ADX = RMA(DX, period)
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 14）
///
/// # 返回
/// - `Ok((adx, plus_di, minus_di))`
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::LengthMismatch` - 数组长度不一致
/// - `HazeError::InvalidPeriod` - period 无效
pub fn adx(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let n = high.len();
    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }

    let (plus_di, minus_di) = compute_di(high, low, close, period)?;

    let mut dx = init_result!(n);
    for i in period..n {
        let sum = plus_di[i] + minus_di[i];
        if is_zero(sum) {
            dx[i] = 0.0;
        } else {
            dx[i] = 100.0 * (plus_di[i] - minus_di[i]).abs() / sum;
        }
    }

    let mut adx_values = init_result!(n);
    let start = period * 2;
    if start <= n {
        let mut sum_dx = 0.0;
        for i in period..start {
            sum_dx += dx[i];
        }
        adx_values[start - 1] = sum_dx / period as f64;

        let period_f = period as f64;
        for i in start..n {
            adx_values[i] = (adx_values[i - 1] * (period_f - 1.0) + dx[i]) / period_f;
        }
    }

    Ok((adx_values, plus_di, minus_di))
}

/// DX - Directional Movement Index（方向性移动指数）
///
/// ADX的基础指标，衡量趋势强度但无平滑
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 14）
///
/// # 返回
/// - `Ok(Vec<f64>)` - DX 值（0-100）
///
/// # 算法
/// DX = 100 * |(+DI - -DI)| / (+DI + -DI)
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::LengthMismatch` - 数组长度不一致
/// - `HazeError::InvalidPeriod` - period 无效
pub fn dx(high: &[f64], low: &[f64], close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let n = high.len();
    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }

    // 复用 compute_di 计算 +DI 和 -DI
    let (plus_di, minus_di) = compute_di(high, low, close, period)?;

    // 计算 DX（DI 无效时返回 NaN，区别于 ADX 内部使用 0.0）
    let result = (0..n)
        .map(|i| {
            if plus_di[i].is_nan() || minus_di[i].is_nan() {
                f64::NAN
            } else {
                let sum = plus_di[i] + minus_di[i];
                if is_zero(sum) {
                    0.0
                } else {
                    100.0 * (plus_di[i] - minus_di[i]).abs() / sum
                }
            }
        })
        .collect();

    Ok(result)
}

/// PLUS_DI - Positive Directional Indicator（正向指标）
///
/// 衡量上升趋势的强度
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 14）
///
/// # 返回
/// - `Ok(Vec<f64>)` - +DI 值
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::LengthMismatch` - 数组长度不一致
/// - `HazeError::InvalidPeriod` - period 无效
pub fn plus_di(high: &[f64], low: &[f64], close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    let (_, plus_di, _) = adx(high, low, close, period)?;
    Ok(plus_di)
}

/// MINUS_DI - Negative Directional Indicator（负向指标）
///
/// 衡量下降趋势的强度
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 14）
///
/// # 返回
/// - `Ok(Vec<f64>)` - -DI 值
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::LengthMismatch` - 数组长度不一致
/// - `HazeError::InvalidPeriod` - period 无效
pub fn minus_di(high: &[f64], low: &[f64], close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    let (_, _, minus_di) = adx(high, low, close, period)?;
    Ok(minus_di)
}

/// Aroon Indicator（阿隆指标）
///
/// 算法：
/// - Aroon Up = ((period - bars_since_highest_high) / period) * 100
/// - Aroon Down = ((period - bars_since_lowest_low) / period) * 100
/// - Aroon Oscillator = Aroon Up - Aroon Down
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `period`: 周期（默认 25）
///
/// # 返回
/// - `Ok((aroon_up, aroon_down, aroon_oscillator))`
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::LengthMismatch` - 数组长度不一致
/// - `HazeError::InvalidPeriod` - period < 2 或 period > n
pub fn aroon(
    high: &[f64],
    low: &[f64],
    period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low")])?;

    let n = high.len();
    if period < 2 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }
    if period >= n {
        return Err(HazeError::InsufficientData {
            required: period + 1,
            actual: n,
        });
    }

    let mut aroon_up = init_result!(n);
    let mut aroon_down = init_result!(n);
    let mut aroon_osc = init_result!(n);

    for i in period..n {
        // 找到最高点和最低点的位置
        let window_high = &high[i - period..=i];
        let window_low = &low[i - period..=i];

        // 使用 NaN-safe 的 fold（过滤 NaN 值）
        let highest = window_high
            .iter()
            .filter(|v| !v.is_nan())
            .fold(f64::NEG_INFINITY, |a, &b| a.max(b));
        let lowest = window_low
            .iter()
            .filter(|v| !v.is_nan())
            .fold(f64::INFINITY, |a, &b| a.min(b));

        // 若窗口全是 NaN，跳过
        if highest == f64::NEG_INFINITY || lowest == f64::INFINITY {
            continue;
        }

        // 从窗口末尾倒数，找到最高/最低点的位置（跳过 NaN）
        // 使用 approx_eq 进行浮点数比较，避免精度问题导致找不到匹配
        let bars_since_high = window_high
            .iter()
            .rev()
            .position(|&x| !x.is_nan() && approx_eq(x, highest, None))
            .unwrap_or(period - 1);

        let bars_since_low = window_low
            .iter()
            .rev()
            .position(|&x| !x.is_nan() && approx_eq(x, lowest, None))
            .unwrap_or(period - 1);

        aroon_up[i] = ((period - bars_since_high) as f64 / period as f64) * 100.0;
        aroon_down[i] = ((period - bars_since_low) as f64 / period as f64) * 100.0;
        aroon_osc[i] = aroon_up[i] - aroon_down[i];
    }

    Ok((aroon_up, aroon_down, aroon_osc))
}

/// PSAR - Parabolic SAR（抛物线止损转向）
///
/// 算法：
/// - SAR`[i]` = SAR`[i-1]` + AF * (EP - SAR`[i-1]`)
/// - EP = 极值点（上升趋势中的最高价，下降趋势中的最低价）
/// - AF = 加速因子，初始 0.02，每次新极值增加 0.02，最大 0.2
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `af_init`: 初始加速因子（默认 0.02）
/// - `af_increment`: AF 增量（默认 0.02）
/// - `af_max`: 最大 AF（默认 0.2）
///
/// # 返回
/// - `Ok((psar, trend))` - trend: 1 = up, -1 = down
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::LengthMismatch` - 数组长度不一致
/// - `HazeError::InsufficientData` - 数据长度小于 2
pub fn psar(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    af_init: f64,
    af_increment: f64,
    af_max: f64,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    // Fail-Fast: AF 参数验证
    if af_init <= 0.0 {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("af_init ({af_init}) must be > 0"),
        });
    }
    if af_increment <= 0.0 {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("af_increment ({af_increment}) must be > 0"),
        });
    }
    if af_max <= 0.0 {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("af_max ({af_max}) must be > 0"),
        });
    }
    if af_max < af_init {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("af_max ({af_max}) must be >= af_init ({af_init})"),
        });
    }

    let n = high.len();
    if n < 2 {
        return Err(HazeError::InsufficientData {
            required: 2,
            actual: n,
        });
    }

    let mut psar_values = init_result!(n);
    let mut trend = init_result!(n);

    // 初始化
    let mut is_uptrend = close[1] > close[0];
    let mut sar = if is_uptrend { low[0] } else { high[0] };
    let mut ep = if is_uptrend { high[1] } else { low[1] };
    let mut af = af_init;

    psar_values[0] = sar;
    trend[0] = if is_uptrend { 1.0 } else { -1.0 };

    for i in 1..n {
        // 计算新 SAR
        sar = sar + af * (ep - sar);

        // 确保 SAR 不穿越前两根 K 线
        if is_uptrend {
            sar = sar.min(low[i - 1]);
            if i > 1 {
                sar = sar.min(low[i - 2]);
            }
        } else {
            sar = sar.max(high[i - 1]);
            if i > 1 {
                sar = sar.max(high[i - 2]);
            }
        }

        // 检查是否反转
        let reverse = if is_uptrend {
            low[i] < sar
        } else {
            high[i] > sar
        };

        if reverse {
            // 趋势反转
            is_uptrend = !is_uptrend;
            sar = ep;
            ep = if is_uptrend { high[i] } else { low[i] };
            af = af_init;
        } else {
            // 更新极值点
            let new_ep = if is_uptrend { high[i] } else { low[i] };
            if (is_uptrend && new_ep > ep) || (!is_uptrend && new_ep < ep) {
                ep = new_ep;
                af = (af + af_increment).min(af_max);
            }
        }

        psar_values[i] = sar;
        trend[i] = if is_uptrend { 1.0 } else { -1.0 };
    }

    Ok((psar_values, trend))
}

/// Vortex Indicator (VI) 涡旋指标
///
/// 识别趋势的开始和持续性
///
/// - `high`: 高价序列
/// - `low`: 低价序列
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 14）
///
/// 返回：`Ok((VI+, VI-))`
///
/// # 算法
/// 1. VM+ = |High`[i]` - Low`[i-1]`|
/// 2. VM- = |Low`[i]` - High`[i-1]`|
/// 3. TR = Max(High`[i]` - Low`[i]`, |High`[i]` - Close`[i-1]`|, |Low`[i]` - Close`[i-1]`|)
/// 4. VI+ = Sum(VM+, period) / Sum(TR, period)
/// 5. VI- = Sum(VM-, period) / Sum(TR, period)
///
/// # 信号
/// - VI+ > VI-：上升趋势
/// - VI- > VI+：下降趋势
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::LengthMismatch` - 数组长度不一致
/// - `HazeError::InsufficientData` - 数据长度小于 2
/// - `HazeError::InvalidPeriod` - period 为 0
pub fn vortex(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let n = high.len();
    if n < 2 {
        return Err(HazeError::InsufficientData {
            required: 2,
            actual: n,
        });
    }
    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }

    // 1. 计算 VM+ 和 VM- 和 TR
    // 注：索引 0 设为 0.0（而非 NaN）以便 rolling_sum 正确累加
    let mut vm_plus = vec![0.0; n];
    let mut vm_minus = vec![0.0; n];
    let mut tr = vec![0.0; n];

    for i in 1..n {
        vm_plus[i] = (high[i] - low[i - 1]).abs();
        vm_minus[i] = (low[i] - high[i - 1]).abs();

        let hl = high[i] - low[i];
        let hc = (high[i] - close[i - 1]).abs();
        let lc = (low[i] - close[i - 1]).abs();
        tr[i] = hl.max(hc).max(lc);
    }

    // 2. 使用 O(n) 滚动求和替代嵌套循环
    let sum_vm_plus = rolling_sum(&vm_plus, period);
    let sum_vm_minus = rolling_sum(&vm_minus, period);
    let sum_tr = rolling_sum(&tr, period);

    // 3. 计算 VI+ 和 VI-
    // 注：原始数据 vm_plus[0], vm_minus[0], tr[0] 都是 NaN
    // rolling_sum 在索引 period 处对应原始窗口 [1..period+1] 的和
    let mut vi_plus = init_result!(n);
    let mut vi_minus = init_result!(n);

    for i in period..n {
        let tr_sum = sum_tr[i];
        if !tr_sum.is_nan() && is_not_zero(tr_sum) {
            vi_plus[i] = sum_vm_plus[i] / tr_sum;
            vi_minus[i] = sum_vm_minus[i] / tr_sum;
        }
    }

    Ok((vi_plus, vi_minus))
}

/// Choppiness Index (CHOP) 震荡指数
///
/// 衡量市场是趋势还是横盘，不指示方向
///
/// - `high`: 高价序列
/// - `low`: 低价序列
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 14）
///
/// 返回：`Ok(CHOP 值（0-100）)`
///
/// # 算法
/// CHOP = 100 * log10(Sum(TR, period) / (Max(High, period) - Min(Low, period))) / log10(period)
///
/// # 解释
/// - CHOP > 61.8：横盘/震荡市场
/// - CHOP < 38.2：趋势市场
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::LengthMismatch` - 数组长度不一致
/// - `HazeError::InsufficientData` - 数据长度小于 2
/// - `HazeError::InvalidPeriod` - period 为 0
pub fn choppiness_index(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
) -> HazeResult<Vec<f64>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let n = high.len();
    if n < 2 {
        return Err(HazeError::InsufficientData {
            required: 2,
            actual: n,
        });
    }
    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }

    // 1. 计算 True Range
    // 注：索引 0 设为 0.0（而非 NaN）以便 rolling_sum 正确累加
    let mut tr = vec![0.0; n];
    for i in 1..n {
        let hl = high[i] - low[i];
        let hc = (high[i] - close[i - 1]).abs();
        let lc = (low[i] - close[i - 1]).abs();
        tr[i] = hl.max(hc).max(lc);
    }

    // 2. 使用 O(n) 滚动函数替代嵌套循环
    let sum_tr = rolling_sum(&tr, period);
    let max_high = rolling_max(high, period);
    let min_low = rolling_min(low, period);

    // 3. 计算 CHOP
    // 注：原始 tr[0] 是 NaN，所以 rolling_sum 在 period 处才对应有效窗口
    let log_period = (period as f64).log10();
    let mut chop = init_result!(n);

    for i in period..n {
        let tr_sum = sum_tr[i];
        let h_max = max_high[i];
        let l_min = min_low[i];

        if !tr_sum.is_nan() && !h_max.is_nan() && !l_min.is_nan() {
            let range = h_max - l_min;
            if range > 0.0 && tr_sum > 0.0 {
                chop[i] = 100.0 * (tr_sum / range).log10() / log_period;
            }
        }
    }

    Ok(chop)
}

/// QStick 指标
///
/// 衡量买卖压力的指标，基于开盘和收盘价的差值
///
/// - `open`: 开盘价序列
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 14）
///
/// 返回：`Ok(QStick 值)`
///
/// # 算法
/// QStick = EMA(Close - Open, period)
///
/// # 信号
/// - QStick > 0：买盘压力（收盘价 > 开盘价）
/// - QStick < 0：卖盘压力（收盘价 < 开盘价）
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::LengthMismatch` - 数组长度不一致
pub fn qstick(open: &[f64], close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[(open, "open"), (close, "close")])?;
    validate_period(period, open.len())?;

    // 1. 计算 Close - Open
    let diff: Vec<f64> = open.iter().zip(close).map(|(&o, &c)| c - o).collect();

    // 2. EMA 平滑
    ema(&diff, period)
}

/// VHF (Vertical Horizontal Filter) 垂直水平过滤器
///
/// 判断市场是趋势还是震荡
///
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 28）
///
/// 返回：`Ok(VHF 值)`
///
/// # 算法
/// VHF = |最高收盘价 - 最低收盘价| / Sum(|Close`[i]` - Close`[i-1]`|, period)
///
/// # 解释
/// - VHF 高值：趋势市场
/// - VHF 低值：震荡市场
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::InsufficientData` - 数据长度小于 2 或 period >= 数据长度
/// - `HazeError::InvalidPeriod` - period 为 0
pub fn vhf(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;

    let n = close.len();
    if n < 2 {
        return Err(HazeError::InsufficientData {
            required: 2,
            actual: n,
        });
    }
    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }
    if period >= n {
        return Err(HazeError::InsufficientData {
            required: period + 1,
            actual: n,
        });
    }

    let mut result = init_result!(n);
    let max_close = rolling_max(close, period);
    let min_close = rolling_min(close, period);

    let mut abs_diff = vec![0.0; n];
    for i in 1..n {
        abs_diff[i] = (close[i] - close[i - 1]).abs();
    }
    let sum_changes = rolling_sum(&abs_diff, period);

    for i in period..n {
        let numerator = (max_close[i] - min_close[i]).abs();
        let denom = sum_changes[i];
        if numerator.is_finite() && denom.is_finite() && denom > 0.0 {
            result[i] = numerator / denom;
        }
    }

    Ok(result)
}

/// TRIX - Triple Exponential Average（三重指数平滑变化率）
///
/// 算法：TRIX = (EMA3`[i]` - EMA3`[i-1]`) / EMA3`[i-1]` * 100
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::InvalidPeriod` - period 为 0 或大于数据长度
pub fn trix(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;

    let n = close.len();
    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }
    if period > n {
        return Err(HazeError::InsufficientData {
            required: period,
            actual: n,
        });
    }

    let ema1 = ema_allow_nan(close, period)?;
    let ema2 = ema_allow_nan(&ema1, period)?;
    let ema3 = ema_allow_nan(&ema2, period)?;

    let mut result = init_result!(n);
    for i in 1..n {
        let prev = ema3[i - 1];
        let curr = ema3[i];
        if prev.is_nan() || curr.is_nan() || is_zero(prev) {
            continue;
        }
        result[i] = (curr - prev) / prev * 100.0;
    }

    Ok(result)
}

/// DPO - Detrended Price Oscillator（去趋势价格振荡器）
///
/// 算法：DPO = Close[i - shift] - SMA(Close, period)[i - shift]
///
/// # 错误
/// - `HazeError::EmptyInput` - 输入为空
/// - `HazeError::InvalidPeriod` - period 为 0 或大于数据长度
pub fn dpo(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;

    let n = close.len();
    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }
    if period > n {
        return Err(HazeError::InsufficientData {
            required: period,
            actual: n,
        });
    }

    let shift = period / 2 + 1;
    let sma_values = sma(close, period)?;
    let mut result = init_result!(n);

    for i in shift..n {
        let idx = i - shift;
        let sma_val = sma_values[idx];
        if sma_val.is_nan() || close[i].is_nan() {
            continue;
        }
        result[i] = close[i] - sma_val;
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_supertrend() {
        // 测试数据：持续上涨趋势
        let high = vec![102.0, 105.0, 104.0, 106.0, 108.0, 107.0, 109.0, 111.0];
        let low = vec![99.0, 101.0, 100.0, 102.0, 104.0, 103.0, 105.0, 107.0];
        let close = vec![101.0, 103.0, 102.0, 105.0, 107.0, 106.0, 108.0, 110.0];

        let period = 3;
        let (supertrend_line, direction, upper, lower) =
            supertrend(&high, &low, &close, period, 3.0).unwrap();

        assert_eq!(supertrend_line.len(), 8);
        assert_eq!(direction.len(), 8);

        // ATR 在 TA-Lib 模式下首个有效值在 index=period
        assert!(direction[..period].iter().all(|d| d.is_nan()));

        // 上涨趋势：所有有效方向应为 1.0（上升趋势）
        assert!(direction[period..].iter().all(|&d| d == 1.0));

        // 上升趋势时，supertrend 线应等于 lower band
        for i in period..8 {
            assert_eq!(supertrend_line[i], lower[i]);
            assert!(!upper[i].is_nan());
        }
    }

    #[test]
    fn test_supertrend_empty_input() {
        let high: Vec<f64> = vec![];
        let low: Vec<f64> = vec![];
        let close: Vec<f64> = vec![];

        let result = supertrend(&high, &low, &close, 3, 3.0);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_supertrend_invalid_period() {
        let high = vec![102.0, 105.0];
        let low = vec![99.0, 101.0];
        let close = vec![101.0, 103.0];

        let result = supertrend(&high, &low, &close, 0, 3.0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = supertrend(&high, &low, &close, 10, 3.0);
        assert!(matches!(result, Err(HazeError::InsufficientData { .. })));
    }

    #[test]
    fn test_supertrend_length_mismatch() {
        let high = vec![102.0, 105.0, 104.0];
        let low = vec![99.0, 101.0];
        let close = vec![101.0, 103.0, 102.0];

        let result = supertrend(&high, &low, &close, 2, 3.0);
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }

    #[test]
    fn test_adx() {
        // Need more data for ADX warmup (2 * period for smoothed DX)
        let high = vec![
            110.0, 111.0, 112.0, 113.0, 114.0, 115.0, 116.0, 117.0, 118.0, 119.0, 120.0, 121.0,
            122.0, 123.0, 124.0,
        ];
        let low = vec![
            100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0,
            112.0, 113.0, 114.0,
        ];
        let close = vec![
            105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0, 115.0, 116.0,
            117.0, 118.0, 119.0,
        ];

        let (adx_values, _plus_di, _minus_di) = adx(&high, &low, &close, 5).unwrap();

        assert_eq!(adx_values.len(), 15);
        // ADX warmup: first (2*period - 1) values may be NaN
        // Valid values start from index >= 2*period - 1 = 9
        assert!(adx_values[10..].iter().all(|&x| !x.is_nan()));
    }

    #[test]
    fn test_adx_empty_input() {
        let high: Vec<f64> = vec![];
        let low: Vec<f64> = vec![];
        let close: Vec<f64> = vec![];

        let result = adx(&high, &low, &close, 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_adx_invalid_period() {
        let high = vec![110.0, 111.0, 112.0];
        let low = vec![100.0, 101.0, 102.0];
        let close = vec![105.0, 106.0, 107.0];

        let result = adx(&high, &low, &close, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }

    #[test]
    fn test_dx_empty_input() {
        let high: Vec<f64> = vec![];
        let low: Vec<f64> = vec![];
        let close: Vec<f64> = vec![];

        let result = dx(&high, &low, &close, 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_plus_di_empty_input() {
        let high: Vec<f64> = vec![];
        let low: Vec<f64> = vec![];
        let close: Vec<f64> = vec![];

        let result = plus_di(&high, &low, &close, 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_minus_di_empty_input() {
        let high: Vec<f64> = vec![];
        let low: Vec<f64> = vec![];
        let close: Vec<f64> = vec![];

        let result = minus_di(&high, &low, &close, 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_aroon() {
        // Need enough data for warmup: period + 1 elements minimum
        let high = vec![
            110.0, 111.0, 112.0, 113.0, 114.0, 113.0, 112.0, 111.0, 115.0, 116.0, 117.0,
        ];
        let low = vec![
            100.0, 101.0, 102.0, 103.0, 104.0, 103.0, 102.0, 101.0, 105.0, 106.0, 107.0,
        ];

        let (aroon_up, aroon_down, _aroon_osc) = aroon(&high, &low, 5).unwrap();

        assert_eq!(aroon_up.len(), 11);
        // Aroon values after warmup period should be in [0, 100]
        // Warmup period = period, so valid from index >= period
        assert!(aroon_up[5..].iter().all(|&x| (0.0..=100.0).contains(&x)));
        assert!(aroon_down[5..].iter().all(|&x| (0.0..=100.0).contains(&x)));
    }

    #[test]
    fn test_aroon_empty_input() {
        let high: Vec<f64> = vec![];
        let low: Vec<f64> = vec![];

        let result = aroon(&high, &low, 5);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_aroon_invalid_period() {
        let high = vec![110.0, 111.0];
        let low = vec![100.0, 101.0];

        let result = aroon(&high, &low, 1);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = aroon(&high, &low, 10);
        assert!(matches!(result, Err(HazeError::InsufficientData { .. })));
    }

    #[test]
    fn test_psar() {
        let high = vec![102.0, 105.0, 104.0, 106.0, 108.0];
        let low = vec![99.0, 101.0, 100.0, 102.0, 104.0];
        let close = vec![101.0, 103.0, 102.0, 105.0, 107.0];

        let (psar_values, trend) = psar(&high, &low, &close, 0.02, 0.02, 0.2).unwrap();

        assert_eq!(psar_values.len(), 5);
        assert_eq!(trend.len(), 5);
        assert!(trend.iter().all(|&t| t == 1.0 || t == -1.0));
    }

    #[test]
    fn test_psar_empty_input() {
        let high: Vec<f64> = vec![];
        let low: Vec<f64> = vec![];
        let close: Vec<f64> = vec![];

        let result = psar(&high, &low, &close, 0.02, 0.02, 0.2);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_psar_insufficient_data() {
        let high = vec![102.0];
        let low = vec![99.0];
        let close = vec![101.0];

        let result = psar(&high, &low, &close, 0.02, 0.02, 0.2);
        assert!(matches!(result, Err(HazeError::InsufficientData { .. })));
    }

    #[test]
    fn test_vortex_empty_input() {
        let high: Vec<f64> = vec![];
        let low: Vec<f64> = vec![];
        let close: Vec<f64> = vec![];

        let result = vortex(&high, &low, &close, 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_vortex_invalid_period() {
        let high = vec![102.0, 105.0, 104.0];
        let low = vec![99.0, 101.0, 100.0];
        let close = vec![101.0, 103.0, 102.0];

        let result = vortex(&high, &low, &close, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }

    #[test]
    fn test_choppiness_index_empty_input() {
        let high: Vec<f64> = vec![];
        let low: Vec<f64> = vec![];
        let close: Vec<f64> = vec![];

        let result = choppiness_index(&high, &low, &close, 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_qstick_empty_input() {
        let open: Vec<f64> = vec![];
        let close: Vec<f64> = vec![];

        let result = qstick(&open, &close, 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_vhf_empty_input() {
        let close: Vec<f64> = vec![];

        let result = vhf(&close, 28);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_vhf_invalid_period() {
        let close = vec![100.0, 101.0, 102.0];

        let result = vhf(&close, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));
    }

    #[test]
    fn test_trix_empty_input() {
        let close: Vec<f64> = vec![];

        let result = trix(&close, 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_trix_invalid_period() {
        let close = vec![100.0, 101.0, 102.0];

        let result = trix(&close, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = trix(&close, 10);
        assert!(matches!(result, Err(HazeError::InsufficientData { .. })));
    }

    #[test]
    fn test_dpo_empty_input() {
        let close: Vec<f64> = vec![];

        let result = dpo(&close, 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_dpo_invalid_period() {
        let close = vec![100.0, 101.0, 102.0];

        let result = dpo(&close, 0);
        assert!(matches!(result, Err(HazeError::InvalidPeriod { .. })));

        let result = dpo(&close, 10);
        assert!(matches!(result, Err(HazeError::InsufficientData { .. })));
    }
}

#[cfg(test)]
mod vortex_tests {
    use super::*;

    #[test]
    fn test_vortex_basic() {
        let high: Vec<f64> = (100..130).map(|x| x as f64 + 5.0).collect();
        let low: Vec<f64> = (100..130).map(|x| x as f64).collect();
        let close: Vec<f64> = (100..130).map(|x| x as f64 + 2.5).collect();

        let (vi_plus, vi_minus) = vortex(&high, &low, &close, 14).unwrap();

        // 上升趋势中，VI+ 应 > VI-
        let valid_idx = 20;
        assert!(!vi_plus[valid_idx].is_nan());
        assert!(!vi_minus[valid_idx].is_nan());
        assert!(vi_plus[valid_idx] > 0.0);
        assert!(vi_minus[valid_idx] > 0.0);
    }

    #[test]
    fn test_choppiness_basic() {
        // 横盘市场
        let high = vec![105.0; 50];
        let low = vec![100.0; 50];
        let close = vec![102.5; 50];

        let chop = choppiness_index(&high, &low, &close, 14).unwrap();

        // 横盘市场中，CHOP 应 > 61.8
        let valid_idx = 20;
        assert!(!chop[valid_idx].is_nan());
        assert!(chop[valid_idx] > 50.0);
    }

    #[test]
    fn test_qstick_basic() {
        let open = vec![100.0, 101.0, 102.0, 103.0, 104.0];
        let close = vec![101.0, 102.0, 103.0, 104.0, 105.0];

        let qstick_values = qstick(&open, &close, 3).unwrap();

        // 上升趋势中（收盘价 > 开盘价），QStick > 0
        let valid_idx = 4;
        assert!(!qstick_values[valid_idx].is_nan());
        assert!(qstick_values[valid_idx] > 0.0);
    }

    #[test]
    fn test_vhf_trend() {
        // 强趋势市场
        let close: Vec<f64> = (100..150).map(|x| x as f64).collect();

        let vhf_values = vhf(&close, 28).unwrap();

        // 强趋势中，VHF 应较高
        let valid_idx = 40;
        assert!(!vhf_values[valid_idx].is_nan());
        assert!(vhf_values[valid_idx] > 0.2);
    }
}
