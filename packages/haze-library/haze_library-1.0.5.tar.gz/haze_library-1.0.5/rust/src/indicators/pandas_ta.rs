// indicators/pandas_ta.rs - pandas-ta 独有指标
//
// 包含：Entropy, Aberration, Squeeze, QQE, CTI, ER, Bias, PSL, RVI, Inertia

#![allow(unused_variables)]
// 指标函数需要 OHLCV + 多个参数是行业标准
#![allow(clippy::too_many_arguments)]
#![allow(clippy::needless_range_loop)]

use crate::errors::validation::{
    validate_lengths_match, validate_not_empty, validate_period, validate_same_length,
};
use crate::errors::{HazeError, HazeResult};
use crate::indicators::{atr, bollinger_bands, keltner_channel, rsi};
use crate::init_result;
use crate::utils::ma::{ema_allow_nan, sma_allow_nan};
use crate::utils::math::{is_not_zero, is_zero};
use crate::utils::{
    correlation, ema, linear_regression, rma, rolling_max, rolling_min, rolling_sum_kahan, sma,
    stdev, tsf,
};

/// Entropy - 信息熵指标（价格不确定性度量）
///
/// 算法：基于价格变化的香农信息熵
/// Entropy = -Σ(p_i * log2(p_i))
/// 其中 p_i 是每个价格变化区间的概率
///
/// # 参数
/// - `close`: 收盘价序列
/// - `period`: 计算周期（默认 10）
/// - `bins`: 分箱数量（默认 10）
///
/// # 返回
/// - 信息熵值（越高表示价格越不确定）
pub fn entropy(close: &[f64], period: usize, bins: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    if period == 0 || bins == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: close.len(),
        });
    }
    if period > close.len() {
        return Err(HazeError::InsufficientData {
            required: period,
            actual: close.len(),
        });
    }

    // [2] 原始计算逻辑
    let n = close.len();
    let mut result = init_result!(n);

    for i in period..n {
        let window = &close[i + 1 - period..=i];

        // 计算收益率（跳过除零情况）
        let mut returns = Vec::with_capacity(window.len() - 1);
        for j in 1..window.len() {
            let prev = window[j - 1];
            // 除零保护：跳过前值为 0 或非有限值的情况
            if is_not_zero(prev) && prev.is_finite() {
                let ret = (window[j] - prev) / prev;
                if ret.is_finite() {
                    returns.push(ret);
                }
            }
        }

        if returns.is_empty() {
            continue;
        }

        // 找到 min 和 max 收益率
        let min_return = returns.iter().cloned().fold(f64::INFINITY, f64::min);
        let max_return = returns.iter().cloned().fold(f64::NEG_INFINITY, f64::max);

        if (max_return - min_return).abs() < 1e-10 {
            result[i] = 0.0; // 无变化，熵为 0
            continue;
        }

        // 分箱
        let bin_width = (max_return - min_return) / (bins as f64);
        let mut histogram = vec![0; bins];

        for &ret in &returns {
            let bin_idx = ((ret - min_return) / bin_width).floor() as usize;
            let bin_idx = bin_idx.min(bins - 1);
            histogram[bin_idx] += 1;
        }

        // 计算熵
        let total = returns.len() as f64;
        let mut entropy_val = 0.0;

        for &count in &histogram {
            if count > 0 {
                let p = (count as f64) / total;
                entropy_val -= p * p.log2();
            }
        }

        result[i] = entropy_val;
    }

    Ok(result)
}

/// Aberration - 偏离度（Keltner Channel 变体）
///
/// 算法：测量价格相对于中轴线的偏离程度
/// Aberration = (close - SMA) / ATR
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 计算周期（默认 20）
/// - `atr_period`: ATR 周期（默认 20）
///
/// # 返回
/// - 偏离度值（正值表示向上偏离，负值表示向下偏离）
pub fn aberration(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
    atr_period: usize,
) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(period, close.len())?;
    validate_period(atr_period, close.len())?;

    // [2] 计算逻辑 - 使用?传播错误
    let n = close.len();
    let ma = sma(close, period)?;
    let atr_values = atr(high, low, close, atr_period)?;

    let result = ma
        .iter()
        .zip(&atr_values)
        .zip(close)
        .map(|((&ma_val, &atr_val), &c)| {
            if ma_val.is_nan() || atr_val.is_nan() || is_zero(atr_val) {
                f64::NAN
            } else {
                (c - ma_val) / atr_val
            }
        })
        .collect();

    Ok(result)
}

/// Squeeze - TTM 挤压指标（Bollinger Bands + Keltner Channel）
///
/// 算法：
/// - Bollinger Bands: SMA ± (std_dev * multiplier)
/// - Keltner Channel: EMA ± (ATR * multiplier)
/// - Squeeze On: BB 内部完全在 KC 内部（波动率收缩）
/// - Squeeze Off: BB 外部突破 KC（波动率扩张）
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `bb_period`: Bollinger Bands 周期（默认 20）
/// - `bb_std`: Bollinger Bands 标准差倍数（默认 2.0）
/// - `kc_period`: Keltner Channel 周期（默认 20）
/// - `kc_atr_period`: Keltner Channel ATR 周期（默认 20）
/// - `kc_mult`: Keltner Channel ATR 倍数（默认 1.5）
///
/// # 返回
/// - (squeeze_on, squeeze_off, momentum)
///   - squeeze_on: 1.0 = 挤压中（BB 在 KC 内），0.0 = 无挤压
///   - squeeze_off: 1.0 = 挤压释放（BB 突破 KC），0.0 = 无释放
///   - momentum: 动量值（(highest(close) + lowest(close))/2 - SMA(close)）
pub fn squeeze(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    bb_period: usize,
    bb_std: f64,
    kc_period: usize,
    kc_atr_period: usize,
    kc_mult: f64,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    // [1] 入口验证
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(bb_period, close.len())?;
    validate_period(kc_period, close.len())?;
    validate_period(kc_atr_period, close.len())?;

    // [2] 计算逻辑
    let n = close.len();

    // Bollinger Bands
    let (bb_upper, _, bb_lower) = bollinger_bands(close, bb_period, bb_std)?;

    // Keltner Channel
    let (kc_upper, _, kc_lower) =
        keltner_channel(high, low, close, kc_period, kc_atr_period, kc_mult)?;

    let mut squeeze_on = vec![0.0; n];
    let mut squeeze_off = vec![0.0; n];

    for i in 0..n {
        if bb_upper[i].is_nan() || kc_upper[i].is_nan() {
            squeeze_on[i] = f64::NAN;
            squeeze_off[i] = f64::NAN;
        } else if bb_lower[i] > kc_lower[i] && bb_upper[i] < kc_upper[i] {
            // BB 完全在 KC 内部 -> 挤压中
            squeeze_on[i] = 1.0;
            squeeze_off[i] = 0.0;
        } else {
            // BB 突破 KC -> 挤压释放
            squeeze_on[i] = 0.0;
            squeeze_off[i] = 1.0;
        }
    }

    // 计算动量
    let period = bb_period;
    let highest = rolling_max(close, period);
    let lowest = rolling_min(close, period);
    let basis = sma(close, period)?;

    let momentum: Vec<f64> = highest
        .iter()
        .zip(&lowest)
        .zip(&basis)
        .map(|((&h, &l), &b)| {
            if h.is_nan() || l.is_nan() || b.is_nan() {
                f64::NAN
            } else {
                ((h + l) / 2.0) - b
            }
        })
        .collect();

    Ok((squeeze_on, squeeze_off, momentum))
}

/// QQE - Quantitative Qualitative Estimation（定量定性估计）
///
/// 算法：平滑版 RSI + 动态波动带
/// 1. RSI_EMA = EMA(RSI(close, rsi_period), smooth)
/// 2. RSI_DIFF = ABS(RSI_EMA - RSI_EMA`[1]`)
/// 3. TR = EMA(RSI_DIFF, smooth)
/// 4. Fast_Line = RSI_EMA
/// 5. Slow_Line = Fast_Line ± (TR * multiplier)
///
/// # 参数
/// - `close`: 收盘价序列
/// - `rsi_period`: RSI 周期（默认 14）
/// - `smooth`: 平滑周期（默认 5）
/// - `multiplier`: 波动带倍数（默认 4.236）
///
/// # 返回
/// - (fast_line, slow_line, signal)
///   - fast_line: 平滑 RSI
///   - slow_line: 动态阈值线
///   - signal: 1.0=看涨, -1.0=看跌, 0.0=中性
pub fn qqe(
    close: &[f64],
    rsi_period: usize,
    smooth: usize,
    multiplier: f64,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    validate_period(rsi_period, close.len())?;
    validate_period(smooth, close.len())?;

    // [2] 计算逻辑
    let n = close.len();

    // 1. 计算 RSI
    let rsi_values = rsi(close, rsi_period)?;

    // 2. EMA 平滑 RSI
    let rsi_ema = ema_allow_nan(&rsi_values, smooth)?;

    // 3. 计算 RSI 差值的 EMA
    let mut rsi_diff = init_result!(n);
    for i in 1..n {
        if !rsi_ema[i].is_nan() && !rsi_ema[i - 1].is_nan() {
            rsi_diff[i] = (rsi_ema[i] - rsi_ema[i - 1]).abs();
        }
    }
    let tr_rsi = ema_allow_nan(&rsi_diff, smooth)?;

    // 4. 计算 Fast/Slow Lines (rsi_ema becomes fast_line - no clone needed)
    let fast_line = rsi_ema;
    let mut slow_line = init_result!(n);
    let mut signal = vec![0.0; n];

    for i in 1..n {
        if fast_line[i].is_nan() || tr_rsi[i].is_nan() {
            slow_line[i] = f64::NAN;
            continue;
        }

        let threshold = tr_rsi[i] * multiplier;
        let prev_slow = slow_line.get(i - 1).copied().unwrap_or(50.0);
        let prev_slow = if prev_slow.is_nan() { 50.0 } else { prev_slow };

        // 动态阈值逻辑
        if fast_line[i] > prev_slow {
            slow_line[i] = (prev_slow + threshold).min(fast_line[i]);
            signal[i] = 1.0; // 看涨
        } else if fast_line[i] < prev_slow {
            slow_line[i] = (prev_slow - threshold).max(fast_line[i]);
            signal[i] = -1.0; // 看跌
        } else {
            slow_line[i] = prev_slow;
            signal[i] = 0.0; // 中性
        }
    }

    Ok((fast_line, slow_line, signal))
}

/// CTI - Correlation Trend Indicator（相关趋势指标）
///
/// 算法：价格序列与线性回归直线的皮尔逊相关系数
/// 用于衡量价格是否处于趋势状态
///
/// # 参数
/// - `close`: 收盘价序列
/// - `period`: 计算周期（默认 12）
///
/// # 返回
/// - 相关系数（-1 到 1，接近 1 表示强上升趋势，接近 -1 表示强下降趋势）
pub fn cti(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    validate_period(period, close.len())?;

    // [2] 计算逻辑
    let n = close.len();
    if period == 1 {
        let mut result = init_result!(n);
        for i in 1..n {
            result[i] = 0.0;
        }
        return Ok(result);
    }

    let x: Vec<f64> = (0..n).map(|i| i as f64).collect();
    Ok(correlation(&x, close, period))
}

/// ER - Efficiency Ratio（效率比）
///
/// 算法：考夫曼效率比（Kaufman's Efficiency Ratio）
/// ER = |price_change| / sum(|price_diff|)
/// 其中 price_change = close`[i]` - close[i-period]
///      price_diff = close`[j]` - close`[j-1]`
///
/// # 参数
/// - `close`: 收盘价序列
/// - `period`: 计算周期（默认 10）
///
/// # 返回
/// - 效率比（0 到 1，越接近 1 表示价格变化越有效率）
pub fn er(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    validate_period(period, close.len())?;

    // [2] 计算逻辑
    let n = close.len();
    if period >= n {
        return Err(HazeError::InsufficientData {
            required: period + 1,
            actual: n,
        });
    }

    let mut abs_diff = vec![0.0; n];
    for i in 1..n {
        abs_diff[i] = (close[i] - close[i - 1]).abs();
    }
    let volatility = rolling_sum_kahan(&abs_diff, period);

    let mut result = init_result!(n);

    for i in period..n {
        let change = (close[i] - close[i - period]).abs();
        let denom = volatility[i];
        if denom.is_finite() && denom > 1e-10 {
            result[i] = change / denom;
        } else {
            result[i] = 0.0;
        }
    }

    Ok(result)
}

/// Bias - 乖离率（价格偏离移动平均线的百分比）
///
/// 算法：Bias = ((close - SMA) / SMA) * 100
///
/// # 参数
/// - `close`: 收盘价序列
/// - `period`: SMA 周期（默认 20）
///
/// # 返回
/// - 乖离率（百分比，正值表示高于均线，负值表示低于均线）
pub fn bias(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    validate_period(period, close.len())?;

    // [2] 计算逻辑
    let ma = sma(close, period)?;

    let result = ma
        .iter()
        .zip(close)
        .map(|(&ma_val, &c)| {
            if ma_val.is_nan() || is_zero(ma_val) {
                f64::NAN
            } else {
                ((c - ma_val) / ma_val) * 100.0
            }
        })
        .collect();

    Ok(result)
}

/// PSL - Psychological Line（心理线）
///
/// 算法：PSL = (上涨天数 / 总天数) * 100
/// 用于衡量市场情绪（超买/超卖）
///
/// # 参数
/// - `close`: 收盘价序列
/// - `period`: 计算周期（默认 12）
///
/// # 返回
/// - 心理线值（0 到 100，>75 超买，<25 超卖）
pub fn psl(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    validate_period(period, close.len())?;

    // [2] 计算逻辑
    let n = close.len();
    let mut result = init_result!(n);

    for i in period..n {
        let mut up_days = 0;
        for j in (i - period + 1)..=i {
            if close[j] > close[j - 1] {
                up_days += 1;
            }
        }

        result[i] = (up_days as f64 / period as f64) * 100.0;
    }

    Ok(result)
}

/// RVI - Relative Vigor Index（相对活力指数）
///
/// 算法：
/// 1. Numerator = (close - open) + 2*(close`[1]` - open`[1]`) + 2*(close`[2]` - open`[2]`) + (close`[3]` - open`[3]`)
/// 2. Denominator = (high - low) + 2*(high`[1]` - low`[1]`) + 2*(high`[2]` - low`[2]`) + (high`[3]` - low`[3]`)
/// 3. RVI = SMA(Numerator, period) / SMA(Denominator, period)
/// 4. Signal = SMA(RVI, signal_period)
///
/// # 参数
/// - `open`: 开盘价序列
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 计算周期（默认 10）
/// - `signal_period`: 信号线周期（默认 4）
///
/// # 返回
/// - (rvi, signal)
pub fn rvi(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
    signal_period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    // [1] 入口验证
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;
    validate_period(period, close.len())?;
    validate_period(signal_period, close.len())?;

    // [2] 计算逻辑
    let n = close.len();
    let mut numerator = init_result!(n);
    let mut denominator = init_result!(n);

    // 加权平滑（4 个周期）
    for i in 3..n {
        let num = (close[i] - open[i])
            + 2.0 * (close[i - 1] - open[i - 1])
            + 2.0 * (close[i - 2] - open[i - 2])
            + (close[i - 3] - open[i - 3]);

        let denom = (high[i] - low[i])
            + 2.0 * (high[i - 1] - low[i - 1])
            + 2.0 * (high[i - 2] - low[i - 2])
            + (high[i - 3] - low[i - 3]);

        numerator[i] = num / 6.0;
        denominator[i] = denom / 6.0;
    }

    let num_sma = sma_allow_nan(&numerator, period)?;
    let denom_sma = sma_allow_nan(&denominator, period)?;

    let rvi_values: Vec<f64> = num_sma
        .iter()
        .zip(&denom_sma)
        .map(|(&num, &denom)| {
            if num.is_nan() || denom.is_nan() || is_zero(denom) {
                f64::NAN
            } else {
                num / denom
            }
        })
        .collect();

    let signal = sma_allow_nan(&rvi_values, signal_period)?;

    Ok((rvi_values, signal))
}

/// Inertia - 惯性指标（RVI 变体 + 线性回归）
///
/// 算法：
/// 1. 计算 RVI
/// 2. 对 RVI 进行线性回归
/// 3. Inertia = RVI 的回归直线值
///
/// # 参数
/// - `open`: 开盘价序列
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `rvi_period`: RVI 周期（默认 14）
/// - `regression_period`: 回归周期（默认 20）
///
/// # 返回
/// - 惯性值
pub fn inertia(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    rvi_period: usize,
    regression_period: usize,
) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;
    validate_period(rvi_period, close.len())?;
    validate_period(regression_period, close.len())?;

    // [2] 计算逻辑
    let (rvi_values, _) = rvi(open, high, low, close, rvi_period, 4)?;
    let n = rvi_values.len();
    let mut result = init_result!(n);
    let (slope, intercept, _) = linear_regression(&rvi_values, regression_period);
    let x_last = regression_period as f64 - 1.0;

    for i in regression_period..n {
        let s = slope[i];
        let b = intercept[i];
        if s.is_finite() && b.is_finite() {
            result[i] = s * x_last + b;
        }
    }

    Ok(result)
}

// ==================== Batch 9: pandas-ta 独有指标（第二批）====================

/// Alligator - Bill Williams 鳄鱼指标
///
/// 算法：3 条 SMMA（平滑移动平均）+ 未来偏移
/// - Jaw（下颚）: SMMA(13) 偏移 8 个周期
/// - Teeth（牙齿）: SMMA(8) 偏移 5 个周期
/// - Lips（嘴唇）: SMMA(5) 偏移 3 个周期
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `jaw_period`: Jaw 周期（默认 13）
/// - `teeth_period`: Teeth 周期（默认 8）
/// - `lips_period`: Lips 周期（默认 5）
///
/// # 返回
/// - (jaw, teeth, lips)
pub fn alligator(
    high: &[f64],
    low: &[f64],
    jaw_period: usize,
    teeth_period: usize,
    lips_period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    // [1] 入口验证
    validate_not_empty(high, "high")?;
    validate_same_length(high, "high", low, "low")?;
    validate_period(jaw_period, high.len())?;
    validate_period(teeth_period, high.len())?;
    validate_period(lips_period, high.len())?;

    // [2] 计算逻辑
    let n = high.len();

    // 计算 HL/2
    let hl2: Vec<f64> = high.iter().zip(low).map(|(&h, &l)| (h + l) / 2.0).collect();

    // 使用 RMA (Wilder's SMMA)
    let jaw = rma(&hl2, jaw_period)?;
    let teeth = rma(&hl2, teeth_period)?;
    let lips = rma(&hl2, lips_period)?;

    // 未来偏移（向右移动）
    let jaw_shifted = shift_forward(&jaw, 8);
    let teeth_shifted = shift_forward(&teeth, 5);
    let lips_shifted = shift_forward(&lips, 3);

    Ok((jaw_shifted, teeth_shifted, lips_shifted))
}

/// 向前偏移（未来偏移）
fn shift_forward(values: &[f64], offset: usize) -> Vec<f64> {
    let n = values.len();
    let mut result = init_result!(n);
    let count = n.saturating_sub(offset);
    result[offset..(offset + count)].copy_from_slice(&values[..count]);
    result
}

/// EFI - Elder's Force Index（艾尔德力度指数）
///
/// 算法：Force = (Close - Close`[1]`) × Volume
///      EFI = EMA(Force, period)
///
/// # 参数
/// - `close`: 收盘价序列
/// - `volume`: 成交量序列
/// - `period`: EMA 周期（默认 13）
///
/// # 返回
/// - EFI 值
pub fn efi(close: &[f64], volume: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    validate_same_length(close, "close", volume, "volume")?;
    validate_period(period, close.len())?;

    // [2] 计算逻辑
    let n = close.len();
    let mut force = init_result!(n);

    for i in 1..n {
        force[i] = (close[i] - close[i - 1]) * volume[i];
    }

    ema_allow_nan(&force, period)
}

/// KST - Know Sure Thing（确然指标）
///
/// 算法：4 个不同周期的 ROC 加权求和
/// RCMA1 = SMA(ROC(close, 10), 10)
/// RCMA2 = SMA(ROC(close, 15), 10)
/// RCMA3 = SMA(ROC(close, 20), 10)
/// RCMA4 = SMA(ROC(close, 30), 15)
/// KST = RCMA1*1 + RCMA2*2 + RCMA3*3 + RCMA4*4
///
/// # 参数
/// - `close`: 收盘价序列
/// - `roc1`: ROC1 周期（默认 10）
/// - `roc2`: ROC2 周期（默认 15）
/// - `roc3`: ROC3 周期（默认 20）
/// - `roc4`: ROC4 周期（默认 30）
/// - `signal_period`: 信号线周期（默认 9）
///
/// # 返回
/// - (kst, signal)
pub fn kst(
    close: &[f64],
    roc1: usize,
    roc2: usize,
    roc3: usize,
    roc4: usize,
    signal_period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    let max_roc = roc1.max(roc2).max(roc3).max(roc4);
    validate_period(max_roc, close.len())?;
    validate_period(signal_period, close.len())?;

    // [2] 计算逻辑
    let n = close.len();
    // 计算 4 个 ROC
    let roc_1 = roc_helper(close, roc1);
    let roc_2 = roc_helper(close, roc2);
    let roc_3 = roc_helper(close, roc3);
    let roc_4 = roc_helper(close, roc4);

    // SMA 平滑
    let rcma1 = sma_allow_nan(&roc_1, 10)?;
    let rcma2 = sma_allow_nan(&roc_2, 10)?;
    let rcma3 = sma_allow_nan(&roc_3, 10)?;
    let rcma4 = sma_allow_nan(&roc_4, 15)?;

    // 加权求和
    let kst_values: Vec<f64> = rcma1
        .iter()
        .zip(&rcma2)
        .zip(&rcma3)
        .zip(&rcma4)
        .map(|(((&r1, &r2), &r3), &r4)| {
            if r1.is_nan() || r2.is_nan() || r3.is_nan() || r4.is_nan() {
                f64::NAN
            } else {
                r1 * 1.0 + r2 * 2.0 + r3 * 3.0 + r4 * 4.0
            }
        })
        .collect();

    let signal = sma_allow_nan(&kst_values, signal_period)?;

    Ok((kst_values, signal))
}

/// ROC 辅助函数
fn roc_helper(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut result = init_result!(n);

    for i in period..n {
        if is_not_zero(values[i - period]) {
            result[i] = ((values[i] - values[i - period]) / values[i - period]) * 100.0;
        }
    }

    result
}

/// STC - Schaff Trend Cycle（沙夫趋势周期）
///
/// 算法：对 MACD 应用随机振荡器公式，周期化趋势
/// 1. MACD = EMA(close, fast) - EMA(close, slow)
/// 2. Stoch1 = Stochastic(MACD, cycle)
/// 3. Stoch2 = Stochastic(Stoch1, cycle)
///
/// # 参数
/// - `close`: 收盘价序列
/// - `fast`: 快速 EMA 周期（默认 23）
/// - `slow`: 慢速 EMA 周期（默认 50）
/// - `cycle`: 周期长度（默认 10）
///
/// # 返回
/// - STC 值（0-100）
pub fn stc(close: &[f64], fast: usize, slow: usize, cycle: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    validate_period(fast, close.len())?;
    validate_period(slow, close.len())?;
    validate_period(cycle, close.len())?;

    // [2] 计算逻辑
    let n = close.len();

    // 1. 计算 MACD
    let ema_fast = ema(close, fast)?;
    let ema_slow = ema(close, slow)?;

    let macd: Vec<f64> = ema_fast
        .iter()
        .zip(&ema_slow)
        .map(|(&f, &s)| {
            if f.is_nan() || s.is_nan() {
                f64::NAN
            } else {
                f - s
            }
        })
        .collect();

    // 2. 第一次随机化
    let stoch1 = stochastic_raw(&macd, cycle);

    // 3. 第二次随机化
    Ok(stochastic_raw(&stoch1, cycle))
}

/// 随机振荡器原始计算（返回 %K）
fn stochastic_raw(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut result = init_result!(n);

    for i in period..n {
        let window = &values[i + 1 - period..=i];
        let max_val = window.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let min_val = window.iter().cloned().fold(f64::INFINITY, f64::min);

        if (max_val - min_val).abs() > 1e-10 {
            result[i] = ((values[i] - min_val) / (max_val - min_val)) * 100.0;
        } else {
            result[i] = 50.0; // 无波动时默认 50
        }
    }

    result
}

/// TDFI - Trend Direction Force Index（趋势方向力度指数）
///
/// 算法：
/// 1. TDF = abs(close - close`[period]`)
/// 2. TDFI = EMA(TDF, smooth)
///
/// # 参数
/// - `close`: 收盘价序列
/// - `period`: 计算周期（默认 13）
/// - `smooth`: 平滑周期（默认 3）
///
/// # 返回
/// - TDFI 值
pub fn tdfi(close: &[f64], period: usize, smooth: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    validate_period(period, close.len())?;
    validate_period(smooth, close.len())?;

    // [2] 计算逻辑
    let n = close.len();
    let mut tdf = init_result!(n);

    for i in period..n {
        tdf[i] = (close[i] - close[i - period]).abs();
    }

    ema_allow_nan(&tdf, smooth)
}

/// WAE - Waddah Attar Explosion（瓦达赫爆发指标）
///
/// 算法：
/// 1. MACD = EMA(close, fast) - EMA(close, slow)
/// 2. Trend = MACD - SMA(MACD, signal)
/// 3. Explosion = abs(Trend)
/// 4. Dead Zone = BB_upper - BB_lower (波动带宽)
///
/// # 参数
/// - `close`: 收盘价序列
/// - `fast`: 快速 EMA 周期（默认 20）
/// - `slow`: 慢速 EMA 周期（默认 40）
/// - `signal`: 信号周期（默认 9）
/// - `bb_period`: BB 周期（默认 20）
/// - `multiplier`: BB 倍数（默认 2.0）
///
/// # 返回
/// - (explosion, dead_zone)
pub fn wae(
    close: &[f64],
    fast: usize,
    slow: usize,
    signal: usize,
    bb_period: usize,
    multiplier: f64,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    validate_period(fast, close.len())?;
    validate_period(slow, close.len())?;
    validate_period(signal, close.len())?;
    validate_period(bb_period, close.len())?;

    // [2] 计算逻辑
    let n = close.len();
    // 1. 计算 MACD
    let ema_fast = ema(close, fast)?;
    let ema_slow = ema(close, slow)?;

    let macd: Vec<f64> = ema_fast
        .iter()
        .zip(&ema_slow)
        .map(|(&f, &s)| {
            if f.is_nan() || s.is_nan() {
                f64::NAN
            } else {
                f - s
            }
        })
        .collect();

    // 2. 信号线
    let signal_line = sma_allow_nan(&macd, signal)?;

    // 3. Explosion
    let explosion: Vec<f64> = macd
        .iter()
        .zip(&signal_line)
        .map(|(&m, &s)| {
            if m.is_nan() || s.is_nan() {
                f64::NAN
            } else {
                (m - s).abs()
            }
        })
        .collect();

    // 4. Dead Zone（BB 带宽）
    let std = stdev(close, bb_period);
    let dead_zone: Vec<f64> = std.iter().map(|&s| s * multiplier * 2.0).collect();

    Ok((explosion, dead_zone))
}

/// SMI - Stochastic Momentum Index（随机动量指数）
///
/// 算法：
/// 1. HL_range = (Highest(high, period) + Lowest(low, period)) / 2
/// 2. Distance = Close - HL_range
/// 3. SMI = EMA(EMA(Distance, smooth1), smooth2) / EMA(EMA(HL_diff, smooth1), smooth2) * 100
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 周期（默认 13）
/// - `smooth1`: 第一次平滑（默认 25）
/// - `smooth2`: 第二次平滑（默认 2）
///
/// # 返回
/// - SMI 值
pub fn smi(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
    smooth1: usize,
    smooth2: usize,
) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(period, high.len())?;
    validate_period(smooth1, high.len())?;
    validate_period(smooth2, high.len())?;

    // [2] 计算逻辑
    let n = close.len();

    let highest = rolling_max(high, period);
    let lowest = rolling_min(low, period);

    let hl_range: Vec<f64> = highest
        .iter()
        .zip(&lowest)
        .map(|(&h, &l)| (h + l) / 2.0)
        .collect();

    let distance: Vec<f64> = close
        .iter()
        .zip(&hl_range)
        .map(|(&c, &hl)| c - hl)
        .collect();

    let hl_diff: Vec<f64> = highest
        .iter()
        .zip(&lowest)
        .map(|(&h, &l)| (h - l) / 2.0)
        .collect();

    // 双重 EMA
    let distance_ema1 = ema_allow_nan(&distance, smooth1)?;
    let distance_ema2 = ema_allow_nan(&distance_ema1, smooth2)?;

    let diff_ema1 = ema_allow_nan(&hl_diff, smooth1)?;
    let diff_ema2 = ema_allow_nan(&diff_ema1, smooth2)?;

    // SMI
    let result = distance_ema2
        .iter()
        .zip(&diff_ema2)
        .map(|(&num, &denom)| {
            if num.is_nan() || denom.is_nan() || is_zero(denom) {
                f64::NAN
            } else {
                (num / denom) * 100.0
            }
        })
        .collect();

    Ok(result)
}

/// Coppock Curve - 库波克曲线（长期趋势指标）
///
/// 算法：
/// 1. ROC1 = ROC(close, period1)
/// 2. ROC2 = ROC(close, period2)
/// 3. Coppock = WMA(ROC1 + ROC2, wma_period)
///
/// # 参数
/// - `close`: 收盘价序列
/// - `period1`: ROC1 周期（默认 11）
/// - `period2`: ROC2 周期（默认 14）
/// - `wma_period`: WMA 周期（默认 10）
///
/// # 返回
/// - Coppock 值
pub fn coppock(
    close: &[f64],
    period1: usize,
    period2: usize,
    wma_period: usize,
) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    let max_period = period1.max(period2);
    validate_period(max_period, close.len())?;
    validate_period(wma_period, close.len())?;

    // [2] 计算逻辑
    let roc1 = roc_helper(close, period1);
    let roc2 = roc_helper(close, period2);

    let roc_sum: Vec<f64> = roc1
        .iter()
        .zip(&roc2)
        .map(|(&r1, &r2)| {
            if r1.is_nan() || r2.is_nan() {
                f64::NAN
            } else {
                r1 + r2
            }
        })
        .collect();

    wma(&roc_sum, wma_period)
}

/// WMA - Weighted Moving Average（加权移动平均）
fn wma(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    let n = values.len();
    if period == 0 || period > n {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: n,
        });
    }

    let mut result = init_result!(n);
    let weight_sum: usize = (1..=period).sum();

    for i in (period - 1)..n {
        let mut weighted_sum = 0.0;
        let mut valid = true;

        for j in 0..period {
            let idx = i + 1 + j - period;
            if values[idx].is_nan() {
                valid = false;
                break;
            }
            weighted_sum += values[idx] * (j + 1) as f64;
        }

        if valid {
            result[i] = weighted_sum / (weight_sum as f64);
        }
    }

    Ok(result)
}

/// PGO - Pretty Good Oscillator（优良振荡器）
///
/// 算法：
/// PGO = (Close - SMA(close, period)) / ATR(period)
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 计算周期（默认 14）
///
/// # 返回
/// - PGO 值
pub fn pgo(high: &[f64], low: &[f64], close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(period, close.len())?;

    // [2] 计算逻辑
    let ma = sma(close, period)?;
    let atr_values = atr(high, low, close, period)?;

    let result = ma
        .iter()
        .zip(&atr_values)
        .zip(close)
        .map(|((&ma_val, &atr_val), &c)| {
            if ma_val.is_nan() || atr_val.is_nan() || is_zero(atr_val) {
                f64::NAN
            } else {
                (c - ma_val) / atr_val
            }
        })
        .collect();

    Ok(result)
}

/// VWMA - Volume Weighted Moving Average（成交量加权移动平均）
///
/// 算法：
/// VWMA = SUM(close * volume, period) / SUM(volume, period)
///
/// # 参数
/// - `close`: 收盘价序列
/// - `volume`: 成交量序列
/// - `period`: 计算周期（默认 20）
///
/// # 返回
/// - VWMA 值
pub fn vwma(close: &[f64], volume: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    validate_same_length(close, "close", volume, "volume")?;
    validate_period(period, close.len())?;

    // [2] 计算逻辑
    let n = close.len();
    let mut result = init_result!(n);

    for i in (period - 1)..n {
        let mut pv_sum = 0.0;
        let mut v_sum = 0.0;

        for j in (i + 1 - period)..=i {
            pv_sum += close[j] * volume[j];
            v_sum += volume[j];
        }

        if v_sum > 0.0 {
            result[i] = pv_sum / v_sum;
        }
    }

    Ok(result)
}

// ========== Batch 10: 最终批次（202 → 212 指标，达成 100%）==========

/// ALMA - Arnaud Legoux Moving Average（阿诺·勒古克斯移动平均）
///
/// 算法：使用高斯分布权重的移动平均
/// Weight(i) = exp(-((i - offset) / sigma)^2)
///
/// # 参数
/// - `values`: 价格序列
/// - `period`: 计算周期（默认 9）
/// - `offset`: 高斯偏移（0-1，默认 0.85，值越大越平滑）
/// - `sigma`: 高斯标准差（默认 6.0）
///
/// # 返回
/// - ALMA 值
pub fn alma(values: &[f64], period: usize, offset: f64, sigma: f64) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    // [2] 计算逻辑
    let n = values.len();
    let m = (period as f64 - 1.0) * offset;
    let s = period as f64 / sigma;

    // 计算高斯权重
    let mut weights = vec![0.0; period];
    let mut weight_sum = 0.0;
    for i in 0..period {
        let diff = (i as f64 - m) / s;
        weights[i] = (-diff * diff).exp();
        weight_sum += weights[i];
    }

    // 归一化权重
    for w in &mut weights {
        *w /= weight_sum;
    }

    let mut result = init_result!(n);

    for i in (period - 1)..n {
        let mut alma_val = 0.0;
        for j in 0..period {
            alma_val += values[i + 1 - period + j] * weights[j];
        }
        result[i] = alma_val;
    }

    Ok(result)
}

/// VIDYA - Variable Index Dynamic Average（可变指数动态平均）
///
/// 算法：
/// alpha = 2 / (period + 1)
/// volatility_ratio = abs(STDEV(close, period) / close)
/// adaptive_alpha = alpha * volatility_ratio
/// VIDYA`[i]` = close`[i]` * adaptive_alpha + VIDYA`[i-1]` * (1 - adaptive_alpha)
///
/// # 参数
/// - `close`: 收盘价序列
/// - `period`: 计算周期（默认 14）
///
/// # 返回
/// - VIDYA 值
pub fn vidya(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    validate_period(period, close.len())?;

    // [2] 计算逻辑
    let n = close.len();
    let alpha = 2.0 / (period as f64 + 1.0);
    let std_values = stdev(close, period);

    let mut result = init_result!(n);
    result[period - 1] = close[period - 1];

    for i in period..n {
        if !std_values[i].is_nan() && is_not_zero(close[i]) {
            let volatility_ratio = (std_values[i] / close[i]).abs();
            let adaptive_alpha = alpha * volatility_ratio;
            result[i] = close[i] * adaptive_alpha + result[i - 1] * (1.0 - adaptive_alpha);
        }
    }

    Ok(result)
}

/// PWMA - Pascal's Weighted Moving Average（帕斯卡加权移动平均）
///
/// 算法：使用帕斯卡三角形权重
/// 周期 4: [1, 3, 3, 1] → 权重归一化
///
/// # 参数
/// - `values`: 价格序列
/// - `period`: 计算周期（默认 5）
///
/// # 返回
/// - PWMA 值
pub fn pwma(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    // [2] 计算逻辑
    let n = values.len();

    // 生成帕斯卡三角形权重
    let mut weights = vec![1.0];
    for i in 1..period {
        let mut new_weights = vec![1.0];
        for j in 0..(weights.len() - 1) {
            new_weights.push(weights[j] + weights[j + 1]);
        }
        new_weights.push(1.0);
        weights = new_weights;
    }

    // 归一化权重
    let weight_sum: f64 = weights.iter().sum();
    for w in &mut weights {
        *w /= weight_sum;
    }

    let mut result = init_result!(n);

    for i in (period - 1)..n {
        let mut pwma_val = 0.0;
        for j in 0..period {
            pwma_val += values[i + 1 - period + j] * weights[j];
        }
        result[i] = pwma_val;
    }

    Ok(result)
}

/// SINWMA - Sine Weighted Moving Average（正弦加权移动平均）
///
/// 算法：使用正弦曲线权重
/// Weight(i) = sin(π * i / period)
///
/// # 参数
/// - `values`: 价格序列
/// - `period`: 计算周期（默认 14）
///
/// # 返回
/// - SINWMA 值
pub fn sinwma(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    use std::f64::consts::PI;

    // [1] 入口验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    // [2] 计算逻辑
    let n = values.len();

    // 计算正弦权重
    let mut weights = vec![0.0; period];
    let mut weight_sum = 0.0;
    for i in 0..period {
        weights[i] = (PI * (i as f64 + 1.0) / (period as f64 + 1.0)).sin();
        weight_sum += weights[i];
    }

    // 归一化权重
    for w in &mut weights {
        *w /= weight_sum;
    }

    let mut result = init_result!(n);

    for i in (period - 1)..n {
        let mut sinwma_val = 0.0;
        for j in 0..period {
            sinwma_val += values[i + 1 - period + j] * weights[j];
        }
        result[i] = sinwma_val;
    }

    Ok(result)
}

/// SWMA - Symmetric Weighted Moving Average（对称加权移动平均）
///
/// 算法：对称三角形权重
/// 周期 5: [1, 2, 3, 2, 1] → 权重归一化
///
/// # 参数
/// - `values`: 价格序列
/// - `period`: 计算周期（默认 7）
///
/// # 返回
/// - SWMA 值
pub fn swma(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    // [2] 计算逻辑
    let n = values.len();
    let mid = (period - 1) / 2;

    // 生成对称权重（支持偶数周期）
    let mut weights = vec![0.0; period];
    let mut weight_sum = 0.0;
    for i in 0..period {
        let dist = if i <= mid { i } else { period - 1 - i };
        weights[i] = (dist + 1) as f64;
        weight_sum += weights[i];
    }

    // 归一化权重
    for w in &mut weights {
        *w /= weight_sum;
    }

    let mut result = init_result!(n);

    for i in period..n {
        let mut swma_val = 0.0;
        for j in 0..period {
            swma_val += values[i + 1 - period + j] * weights[j];
        }
        result[i] = swma_val;
    }

    Ok(result)
}

/// BOP - Balance of Power（价格力量平衡）
///
/// 算法：
/// BOP = (close - open) / (high - low)
/// 范围：-1 到 1
/// > 0: 买方力量占优
/// > < 0: 卖方力量占优
///
/// # 参数
/// - `open`: 开盘价序列
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
///
/// # 返回
/// - BOP 值
pub fn bop(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;

    // [2] 计算逻辑
    let result = open
        .iter()
        .zip(high)
        .zip(low)
        .zip(close)
        .map(|(((&o, &h), &l), &c)| {
            let range = h - l;
            if range > 1e-10 {
                (c - o) / range
            } else {
                0.0
            }
        })
        .collect();

    Ok(result)
}

/// SSL - SSL Channel（SSL 通道）
///
/// 算法：
/// 上轨 = SMA(high, period)
/// 下轨 = SMA(low, period)
/// 根据价格穿越决定当前通道方向
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `period`: 计算周期（默认 10）
///
/// # 返回
/// - (ssl_up, ssl_down) 元组
pub fn ssl_channel(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    // [1] 入口验证
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(period, high.len())?;

    // [2] 计算逻辑
    let n = high.len();
    let sma_high = sma(high, period)?;
    let sma_low = sma(low, period)?;

    let mut ssl_up = init_result!(n);
    let mut ssl_down = init_result!(n);

    for i in (period - 1)..n {
        let h = sma_high[i];
        let l = sma_low[i];
        let c = close[i];
        if h.is_nan() || l.is_nan() || c.is_nan() {
            continue;
        }
        if c > h {
            ssl_up[i] = l;
            ssl_down[i] = h;
        } else {
            ssl_up[i] = h;
            ssl_down[i] = l;
        }
    }

    Ok((ssl_up, ssl_down))
}

/// CFO - Chande Forecast Oscillator（钱德预测振荡器）
///
/// 算法：
/// Linear Regression Forecast = slope * period + intercept
/// CFO = ((close - forecast) / close) * 100
///
/// # 参数
/// - `close`: 收盘价序列
/// - `period`: 计算周期（默认 14）
///
/// # 返回
/// - CFO 值（百分比）
pub fn cfo(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(close, "close")?;
    validate_period(period, close.len())?;

    // [2] 计算逻辑
    let forecast = tsf(close, period);
    let result = forecast
        .iter()
        .zip(close)
        .map(|(&f, &c)| {
            if f.is_nan() || is_zero(c) {
                f64::NAN
            } else {
                ((c - f) / c) * 100.0
            }
        })
        .collect();

    Ok(result)
}

/// Slope - Linear Slope Indicator（线性斜率指标）
///
/// 算法：计算滚动窗口内的线性回归斜率
///
/// # 参数
/// - `values`: 价格序列
/// - `period`: 计算周期（默认 14）
///
/// # 返回
/// - 斜率值
pub fn slope(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    // [2] 计算逻辑
    let n = values.len();
    let mut result = init_result!(n);

    for i in (period - 1)..n {
        let window = &values[i + 1 - period..=i];

        let x_mean = (period - 1) as f64 / 2.0;
        let y_mean: f64 = window.iter().sum::<f64>() / period as f64;

        let mut numerator = 0.0;
        let mut denominator = 0.0;

        for (j, &y) in window.iter().enumerate() {
            let x_diff = j as f64 - x_mean;
            numerator += x_diff * (y - y_mean);
            denominator += x_diff * x_diff;
        }

        if denominator > 1e-10 {
            result[i] = numerator / denominator;
        }
    }

    Ok(result)
}

/// Percent Rank - Percentile Rank（百分位排名）
///
/// 算法：
/// Percent Rank = 小于当前值的数量 / (period - 1) * 100
///
/// # 参数
/// - `values`: 价格序列
/// - `period`: 计算周期（默认 14）
///
/// # 返回
/// - 百分位排名（0-100）
pub fn percent_rank(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // [1] 入口验证
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    // [2] 计算逻辑
    let n = values.len();
    let mut result = init_result!(n);

    for i in (period - 1)..n {
        let window = &values[i + 1 - period..=i];
        let current = values[i];

        let count_less: usize = window.iter().filter(|&&v| v < current).count();

        result[i] = (count_less as f64 / (period - 1) as f64) * 100.0;
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_entropy_basic() {
        let close = vec![
            100.0, 101.0, 102.0, 101.5, 103.0, 102.0, 104.0, 103.5, 105.0, 104.0, 106.0,
        ];
        let result = entropy(&close, 10, 5).unwrap();

        // 验证前 10 个值为 NAN
        for i in 0..10 {
            assert!(result[i].is_nan());
        }

        // 第 10 个值应该有效
        assert!(!result[10].is_nan());
        assert!(result[10] >= 0.0); // 熵值非负
    }

    #[test]
    fn test_bias_basic() {
        let close = vec![100.0, 102.0, 104.0, 103.0, 105.0];
        let result = bias(&close, 3).unwrap();

        // bias[2] = ((104 - (100+102+104)/3) / ((100+102+104)/3)) * 100
        // = ((104 - 102) / 102) * 100 = 1.96
        assert!(!result[2].is_nan());
        assert!((result[2] - 1.96).abs() < 0.1);
    }

    #[test]
    fn test_psl_basic() {
        let close = vec![
            100.0, 101.0, 102.0, 101.0, 103.0, 104.0, 103.0, 105.0, 106.0, 105.0,
        ];
        let result = psl(&close, 5).unwrap();

        // psl[5] = (上涨天数 / 5) * 100
        // [101-100=+, 102-101=+, 101-102=-, 103-101=+, 104-103=+] = 4/5 = 80%
        assert!(!result[5].is_nan());
        assert!((result[5] - 80.0).abs() < 0.1);
    }

    #[test]
    fn test_cti_basic() {
        // 完美上升趋势
        let close = vec![
            100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0,
        ];
        let result = cti(&close, 5).unwrap();

        // 完美线性上升应该接近 1.0
        assert!(!result[5].is_nan());
        assert!(result[5] > 0.95);
    }

    #[test]
    fn test_er_basic() {
        let close = vec![100.0, 102.0, 104.0, 106.0, 108.0, 110.0];
        let result = er(&close, 5).unwrap();

        // ER[5] = |110-100| / (|102-100|+|104-102|+|106-104|+|108-106|+|110-108|)
        // = 10 / 10 = 1.0 (完美效率)
        assert!(!result[5].is_nan());
        assert!((result[5] - 1.0).abs() < 0.1);
    }

    #[test]
    fn test_entropy_empty_input() {
        let result = entropy(&[], 10, 5);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_bias_invalid_period() {
        let close = vec![1.0, 2.0, 3.0];
        assert!(matches!(
            bias(&close, 0),
            Err(HazeError::InvalidPeriod { .. })
        ));
    }

    #[test]
    fn test_vwma_valid() {
        let close = vec![100.0, 101.0, 102.0, 103.0, 104.0];
        let volume = vec![1000.0, 1100.0, 1200.0, 1300.0, 1400.0];
        let result = vwma(&close, &volume, 3).unwrap();

        // Warmup期为NaN
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());

        // 有效值检查
        assert!(!result[2].is_nan());
    }
}

/// Comprehensive boundary tests for pandas-ta module
#[cfg(test)]
mod boundary_tests {
    use super::*;
    use crate::errors::HazeError;

    // ==================== Empty Input Tests ====================

    #[test]
    fn test_aberration_empty_input() {
        // aberration(high, low, close, period, atr_period)
        let result = aberration(&[], &[], &[], 10, 10);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_squeeze_empty_input() {
        // squeeze(high, low, close, bb_period, bb_std, kc_period, kc_atr_period, kc_mult)
        let result = squeeze(&[], &[], &[], 20, 2.0, 20, 10, 1.5);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_qqe_empty_input() {
        // qqe(close, rsi_period, smooth: usize, multiplier: f64)
        let result = qqe(&[], 14, 5, 4.236);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_cti_empty_input() {
        let result = cti(&[], 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_er_empty_input() {
        let result = er(&[], 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_rvi_empty_input() {
        // rvi(open, high, low, close, period, signal_period)
        let result = rvi(&[], &[], &[], &[], 10, 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_inertia_empty_input() {
        // inertia(open, high, low, close, rvi_period, regression_period)
        let result = inertia(&[], &[], &[], &[], 10, 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_alligator_empty_input() {
        let result = alligator(&[], &[], 13, 8, 5);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_efi_empty_input() {
        let result = efi(&[], &[], 13);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_kst_empty_input() {
        // kst(close, roc1, roc2, roc3, roc4, signal_period)
        let result = kst(&[], 10, 15, 20, 30, 9);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_stc_empty_input() {
        let result = stc(&[], 23, 50, 10);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_tdfi_empty_input() {
        let result = tdfi(&[], 20, 5);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_wae_empty_input() {
        // wae(close, fast, slow, signal, bb_period, multiplier)
        let result = wae(&[], 20, 40, 20, 20, 2.0);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_smi_empty_input() {
        let result = smi(&[], &[], &[], 13, 25, 2);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_coppock_empty_input() {
        let result = coppock(&[], 14, 11, 10);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_pgo_empty_input() {
        let result = pgo(&[], &[], &[], 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_vwma_empty_input() {
        let result = vwma(&[], &[], 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_alma_empty_input() {
        let result = alma(&[], 9, 0.85, 6.0);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_vidya_empty_input() {
        let result = vidya(&[], 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_pwma_empty_input() {
        let result = pwma(&[], 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_sinwma_empty_input() {
        let result = sinwma(&[], 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_swma_empty_input() {
        let result = swma(&[], 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_bop_empty_input() {
        let result = bop(&[], &[], &[], &[]);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_ssl_channel_empty_input() {
        let result = ssl_channel(&[], &[], &[], 10);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_cfo_empty_input() {
        let result = cfo(&[], 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_slope_empty_input() {
        let result = slope(&[], 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_percent_rank_empty_input() {
        let result = percent_rank(&[], 14);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    // ==================== Invalid Period Tests ====================

    #[test]
    fn test_cti_period_zero() {
        let close = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = cti(&close, 0);
        assert!(matches!(
            result,
            Err(HazeError::InvalidPeriod { period: 0, .. })
        ));
    }

    #[test]
    fn test_er_period_zero() {
        let close = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = er(&close, 0);
        assert!(matches!(
            result,
            Err(HazeError::InvalidPeriod { period: 0, .. })
        ));
    }

    #[test]
    fn test_slope_period_zero() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = slope(&values, 0);
        assert!(matches!(
            result,
            Err(HazeError::InvalidPeriod { period: 0, .. })
        ));
    }

    #[test]
    fn test_pwma_period_zero() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = pwma(&values, 0);
        assert!(matches!(
            result,
            Err(HazeError::InvalidPeriod { period: 0, .. })
        ));
    }

    #[test]
    fn test_sinwma_period_zero() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = sinwma(&values, 0);
        assert!(matches!(
            result,
            Err(HazeError::InvalidPeriod { period: 0, .. })
        ));
    }

    #[test]
    fn test_swma_period_zero() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = swma(&values, 0);
        assert!(matches!(
            result,
            Err(HazeError::InvalidPeriod { period: 0, .. })
        ));
    }

    // ==================== Length Mismatch Tests ====================

    #[test]
    fn test_aberration_length_mismatch() {
        // aberration(high, low, close, period, atr_period)
        let high = vec![105.0, 106.0, 107.0];
        let low = vec![95.0, 96.0]; // shorter
        let close = vec![100.0, 101.0, 102.0];
        let result = aberration(&high, &low, &close, 2, 2);
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }

    #[test]
    fn test_squeeze_length_mismatch() {
        // squeeze(high, low, close, bb_period, bb_std, kc_period, kc_atr_period, kc_mult)
        let high = vec![105.0, 106.0];
        let low = vec![95.0, 96.0, 97.0]; // longer
        let close = vec![100.0, 101.0];
        let result = squeeze(&high, &low, &close, 2, 2.0, 2, 2, 1.5);
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }

    #[test]
    fn test_rvi_length_mismatch() {
        // rvi(open, high, low, close, period, signal_period)
        let open = vec![100.0, 101.0, 102.0];
        let high = vec![105.0, 106.0, 107.0];
        let low = vec![95.0, 96.0]; // shorter
        let close = vec![100.0, 101.0, 102.0];
        let result = rvi(&open, &high, &low, &close, 10, 14);
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }

    #[test]
    fn test_smi_length_mismatch() {
        let high = vec![105.0, 106.0, 107.0];
        let low = vec![95.0, 96.0]; // shorter
        let close = vec![100.0, 101.0, 102.0];
        let result = smi(&high, &low, &close, 13, 25, 2);
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }

    #[test]
    fn test_pgo_length_mismatch() {
        let high = vec![105.0, 106.0, 107.0];
        let low = vec![95.0, 96.0]; // shorter
        let close = vec![100.0, 101.0, 102.0];
        let result = pgo(&high, &low, &close, 14);
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }

    #[test]
    fn test_efi_length_mismatch() {
        let close = vec![100.0, 101.0, 102.0];
        let volume = vec![1000.0, 1100.0]; // shorter
        let result = efi(&close, &volume, 13);
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }

    #[test]
    fn test_vwma_length_mismatch() {
        let close = vec![100.0, 101.0, 102.0];
        let volume = vec![1000.0, 1100.0]; // shorter
        let result = vwma(&close, &volume, 3);
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }

    #[test]
    fn test_bop_length_mismatch() {
        let open = vec![100.0, 101.0, 102.0];
        let high = vec![105.0, 106.0]; // shorter
        let low = vec![95.0, 96.0, 97.0];
        let close = vec![101.0, 102.0, 103.0];
        let result = bop(&open, &high, &low, &close);
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }

    #[test]
    fn test_ssl_channel_length_mismatch() {
        let high = vec![105.0, 106.0, 107.0];
        let low = vec![95.0, 96.0]; // shorter
        let close = vec![100.0, 101.0, 102.0];
        let result = ssl_channel(&high, &low, &close, 10);
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }

    // ==================== Valid Output Tests ====================

    #[test]
    fn test_aberration_valid() {
        // aberration(high, low, close, period, atr_period) -> Vec<f64>
        let high = vec![
            105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0, 115.0,
        ];
        let low = vec![
            95.0, 96.0, 97.0, 98.0, 99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0,
        ];
        let close = vec![
            100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0,
        ];
        let result = aberration(&high, &low, &close, 5, 5).unwrap();
        assert_eq!(result.len(), 11);
    }

    #[test]
    fn test_squeeze_valid() {
        // squeeze(high, low, close, bb_period, bb_std, kc_period, kc_atr_period, kc_mult) -> (Vec, Vec, Vec)
        let data: Vec<f64> = (0..50).map(|i| 100.0 + (i as f64) * 0.5).collect();
        let high: Vec<f64> = data.iter().map(|&x| x + 5.0).collect();
        let low: Vec<f64> = data.iter().map(|&x| x - 5.0).collect();
        let (sqz, sqz_on, sqz_off) = squeeze(&high, &low, &data, 20, 2.0, 20, 10, 1.5).unwrap();
        assert_eq!(sqz.len(), 50);
        assert_eq!(sqz_on.len(), 50);
        assert_eq!(sqz_off.len(), 50);
    }

    #[test]
    fn test_qqe_valid() {
        let close: Vec<f64> = (0..30).map(|i| 100.0 + (i as f64) * 0.5).collect();
        // qqe(close, rsi_period, smooth: usize, multiplier: f64)
        let (qqe_line, qqe_signal, histogram) = qqe(&close, 14, 5, 4.236).unwrap();
        assert_eq!(qqe_line.len(), 30);
        assert_eq!(qqe_signal.len(), 30);
        assert_eq!(histogram.len(), 30);
    }

    #[test]
    fn test_rvi_valid() {
        // rvi(open, high, low, close, period, signal_period)
        let open: Vec<f64> = (0..30).map(|i| 100.0 + i as f64).collect();
        let high: Vec<f64> = (0..30).map(|i| 105.0 + i as f64).collect();
        let low: Vec<f64> = (0..30).map(|i| 95.0 + i as f64).collect();
        let close: Vec<f64> = (0..30).map(|i| 102.0 + i as f64).collect();
        let (rvi_line, signal) = rvi(&open, &high, &low, &close, 10, 14).unwrap();
        assert_eq!(rvi_line.len(), 30);
        assert_eq!(signal.len(), 30);
    }

    #[test]
    fn test_inertia_valid() {
        // inertia(open, high, low, close, rvi_period, regression_period)
        let open: Vec<f64> = (0..30).map(|i| 100.0 + i as f64).collect();
        let high: Vec<f64> = (0..30).map(|i| 105.0 + i as f64).collect();
        let low: Vec<f64> = (0..30).map(|i| 95.0 + i as f64).collect();
        let close: Vec<f64> = (0..30).map(|i| 102.0 + i as f64).collect();
        let result = inertia(&open, &high, &low, &close, 10, 14).unwrap();
        assert_eq!(result.len(), 30);
    }

    #[test]
    fn test_alligator_valid() {
        let high: Vec<f64> = (0..30).map(|i| 105.0 + i as f64).collect();
        let low: Vec<f64> = (0..30).map(|i| 95.0 + i as f64).collect();
        let (jaw, teeth, lips) = alligator(&high, &low, 13, 8, 5).unwrap();
        assert_eq!(jaw.len(), 30);
        assert_eq!(teeth.len(), 30);
        assert_eq!(lips.len(), 30);
    }

    #[test]
    fn test_efi_valid() {
        let close = vec![
            100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0,
        ];
        let volume = vec![
            1000.0, 1100.0, 1050.0, 1200.0, 1150.0, 1300.0, 1250.0, 1400.0, 1350.0, 1500.0,
        ];
        let result = efi(&close, &volume, 5).unwrap();
        assert_eq!(result.len(), 10);
    }

    #[test]
    fn test_kst_valid() {
        let close: Vec<f64> = (0..60).map(|i| 100.0 + (i as f64).sin() * 5.0).collect();
        // kst(close, roc1, roc2, roc3, roc4, signal_period)
        let (kst_line, signal) = kst(&close, 10, 15, 20, 30, 9).unwrap();
        assert_eq!(kst_line.len(), 60);
        assert_eq!(signal.len(), 60);
    }

    #[test]
    fn test_stc_valid() {
        let close: Vec<f64> = (0..70).map(|i| 100.0 + (i as f64).sin() * 10.0).collect();
        let result = stc(&close, 23, 50, 10).unwrap();
        assert_eq!(result.len(), 70);
    }

    #[test]
    fn test_tdfi_valid() {
        let close: Vec<f64> = (0..30).map(|i| 100.0 + i as f64).collect();
        let result = tdfi(&close, 20, 5).unwrap();
        assert_eq!(result.len(), 30);
    }

    #[test]
    fn test_wae_valid() {
        let close: Vec<f64> = (0..50).map(|i| 100.0 + (i as f64).sin() * 5.0).collect();
        // wae(close, fast, slow, signal, bb_period, multiplier)
        let (trend, explosion) = wae(&close, 20, 40, 20, 20, 2.0).unwrap();
        assert_eq!(trend.len(), 50);
        assert_eq!(explosion.len(), 50);
    }

    #[test]
    fn test_smi_valid() {
        let high: Vec<f64> = (0..40).map(|i| 105.0 + (i as f64).sin() * 3.0).collect();
        let low: Vec<f64> = (0..40).map(|i| 95.0 + (i as f64).sin() * 3.0).collect();
        let close: Vec<f64> = (0..40).map(|i| 100.0 + (i as f64).sin() * 3.0).collect();
        // smi returns Vec<f64>, not a tuple
        let result = smi(&high, &low, &close, 13, 25, 2).unwrap();
        assert_eq!(result.len(), 40);
    }

    #[test]
    fn test_coppock_valid() {
        let close: Vec<f64> = (0..50).map(|i| 100.0 + i as f64).collect();
        let result = coppock(&close, 14, 11, 10).unwrap();
        assert_eq!(result.len(), 50);
    }

    #[test]
    fn test_pgo_valid() {
        let high: Vec<f64> = (0..20).map(|i| 105.0 + i as f64).collect();
        let low: Vec<f64> = (0..20).map(|i| 95.0 + i as f64).collect();
        let close: Vec<f64> = (0..20).map(|i| 100.0 + i as f64).collect();
        let result = pgo(&high, &low, &close, 14).unwrap();
        assert_eq!(result.len(), 20);
    }

    #[test]
    fn test_alma_valid() {
        let values: Vec<f64> = (0..20).map(|i| 100.0 + i as f64).collect();
        let result = alma(&values, 9, 0.85, 6.0).unwrap();
        assert_eq!(result.len(), 20);
        // Check warmup period is NaN
        assert!(result[0].is_nan());
        // Check valid values after warmup
        assert!(!result[9].is_nan());
    }

    #[test]
    fn test_vidya_valid() {
        let close: Vec<f64> = (0..30).map(|i| 100.0 + i as f64).collect();
        let result = vidya(&close, 14).unwrap();
        assert_eq!(result.len(), 30);
    }

    #[test]
    fn test_pwma_valid() {
        let values: Vec<f64> = (0..20).map(|i| 100.0 + i as f64).collect();
        let result = pwma(&values, 5).unwrap();
        assert_eq!(result.len(), 20);
        // Check warmup period is NaN
        assert!(result[0].is_nan());
        // Check valid values after warmup
        assert!(!result[4].is_nan());
    }

    #[test]
    fn test_sinwma_valid() {
        let values: Vec<f64> = (0..20).map(|i| 100.0 + i as f64).collect();
        let result = sinwma(&values, 5).unwrap();
        assert_eq!(result.len(), 20);
    }

    #[test]
    fn test_swma_valid() {
        let values: Vec<f64> = (0..20).map(|i| 100.0 + i as f64).collect();
        let result = swma(&values, 5).unwrap();
        assert_eq!(result.len(), 20);
    }

    #[test]
    fn test_bop_valid() {
        let open = vec![100.0, 101.0, 102.0, 103.0, 104.0];
        let high = vec![105.0, 106.0, 107.0, 108.0, 109.0];
        let low = vec![95.0, 96.0, 97.0, 98.0, 99.0];
        let close = vec![103.0, 104.0, 105.0, 106.0, 107.0];
        let result = bop(&open, &high, &low, &close).unwrap();
        assert_eq!(result.len(), 5);
        // BOP should be positive for bullish closes
        assert!(result.iter().all(|&v| v > 0.0));
    }

    #[test]
    fn test_ssl_channel_valid() {
        let high: Vec<f64> = (0..20).map(|i| 105.0 + i as f64).collect();
        let low: Vec<f64> = (0..20).map(|i| 95.0 + i as f64).collect();
        let close: Vec<f64> = (0..20).map(|i| 100.0 + i as f64).collect();
        let (ssl_down, ssl_up) = ssl_channel(&high, &low, &close, 10).unwrap();
        assert_eq!(ssl_down.len(), 20);
        assert_eq!(ssl_up.len(), 20);
    }

    #[test]
    fn test_cfo_valid() {
        let close: Vec<f64> = (0..20).map(|i| 100.0 + i as f64).collect();
        let result = cfo(&close, 14).unwrap();
        assert_eq!(result.len(), 20);
    }

    #[test]
    fn test_slope_valid() {
        let values: Vec<f64> = (0..20).map(|i| 100.0 + i as f64 * 2.0).collect();
        let result = slope(&values, 10).unwrap();
        assert_eq!(result.len(), 20);
        // For perfect linear trend, slope should be approximately constant
        assert!(!result[9].is_nan());
    }

    #[test]
    fn test_percent_rank_valid() {
        let values = vec![10.0, 20.0, 30.0, 25.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0];
        let result = percent_rank(&values, 5).unwrap();
        assert_eq!(result.len(), 10);
        // Percent rank should be between 0 and 100
        for i in 4..10 {
            assert!(!result[i].is_nan());
            assert!(result[i] >= 0.0 && result[i] <= 100.0);
        }
    }

    // ==================== NaN Handling Tests ====================

    #[test]
    fn test_cti_nan_handling() {
        let close = vec![f64::NAN, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0];
        assert!(matches!(
            cti(&close, 3),
            Err(crate::errors::HazeError::InvalidValue { .. })
        ));
    }

    #[test]
    fn test_er_nan_handling() {
        let close = vec![100.0, f64::NAN, 102.0, 103.0, 104.0, 105.0, 106.0];
        assert!(matches!(
            er(&close, 3),
            Err(crate::errors::HazeError::InvalidValue { .. })
        ));
    }

    #[test]
    fn test_slope_nan_handling() {
        let values = vec![100.0, 101.0, f64::NAN, 103.0, 104.0];
        assert!(matches!(
            slope(&values, 3),
            Err(crate::errors::HazeError::InvalidValue { .. })
        ));
    }

    // ==================== Period 1 Tests (Edge Case) ====================

    #[test]
    fn test_cti_period_one() {
        let close = vec![100.0, 101.0, 102.0, 103.0, 104.0];
        let result = cti(&close, 1).unwrap();
        assert_eq!(result.len(), 5);
    }

    #[test]
    fn test_slope_period_one() {
        let values = vec![100.0, 101.0, 102.0, 103.0, 104.0];
        let result = slope(&values, 1).unwrap();
        assert_eq!(result.len(), 5);
    }

    // ==================== Extreme Value Tests ====================

    #[test]
    fn test_bop_zero_range() {
        // When high == low, BOP calculation should handle division by zero
        let open = vec![100.0, 100.0];
        let high = vec![100.0, 100.0]; // Same as low
        let low = vec![100.0, 100.0];
        let close = vec![100.0, 100.0];
        let result = bop(&open, &high, &low, &close).unwrap();
        assert_eq!(result.len(), 2);
        // Should return 0.0 or NaN for zero range, not panic
    }

    #[test]
    fn test_er_constant_price() {
        // ER with constant price should be 0 or NaN (no directional change)
        let close = vec![100.0, 100.0, 100.0, 100.0, 100.0];
        let result = er(&close, 3).unwrap();
        assert_eq!(result.len(), 5);
    }

    #[test]
    fn test_cti_perfect_uptrend() {
        // Perfect linear uptrend should give CTI near 1
        let close: Vec<f64> = (0..10).map(|i| 100.0 + i as f64).collect();
        let result = cti(&close, 5).unwrap();
        // Last values should be close to 1.0 or -1.0 for perfect trend
        assert!(!result[9].is_nan());
    }
}
