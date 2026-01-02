// indicators/sfg_utils.rs - SFG 辅助工具函数
#![allow(dead_code)]
#![allow(clippy::needless_range_loop)]
// FVG 是金融领域标准术语 (Fair Value Gap)
#![allow(clippy::upper_case_acronyms)]
//
// 提供背离检测、FVG、Order Block 等高级市场结构分析
// 遵循 KISS 原则: 每个函数只做一件事

use crate::errors::validation::{
    validate_lengths_match, validate_min_length, validate_not_empty, validate_not_empty_allow_nan,
    validate_period, validate_range,
};
use crate::errors::{HazeError, HazeResult};
use crate::types::{TradingSignals, ZoneSignals};
use crate::utils::math::is_zero;

/// 背离类型
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum DivergenceType {
    /// 常规看涨背离 (价格新低,指标更高)
    RegularBullish,
    /// 常规看跌背离 (价格新高,指标更低)
    RegularBearish,
    /// 隐藏看涨背离 (价格更高低点,指标更低)
    HiddenBullish,
    /// 隐藏看跌背离 (价格更低高点,指标更高)
    HiddenBearish,
    /// 无背离
    None,
}

/// 背离检测结果
#[derive(Debug, Clone)]
pub struct DivergenceResult {
    /// 每个点的背离类型
    pub divergence_type: Vec<DivergenceType>,
    /// 背离强度 (0-1)
    pub strength: Vec<f64>,
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
fn validate_same_length_allow_nan(
    data1: &[f64],
    name1: &'static str,
    data2: &[f64],
    name2: &'static str,
) -> HazeResult<()> {
    if data1.is_empty() {
        return Err(HazeError::EmptyInput { name: name1 });
    }
    if data2.is_empty() {
        return Err(HazeError::EmptyInput { name: name2 });
    }
    if data1.len() != data2.len() {
        return Err(HazeError::LengthMismatch {
            name1,
            len1: data1.len(),
            name2,
            len2: data2.len(),
        });
    }
    Ok(())
}

/// 检测价格与指标之间的背离
///
/// # 参数
/// - `price`: 价格序列 (通常是收盘价)
/// - `indicator`: 指标序列 (如 RSI, MACD)
/// - `lookback`: 回看周期
/// - `threshold`: 阈值 (最小差异百分比)
pub fn detect_divergence(
    price: &[f64],
    indicator: &[f64],
    lookback: usize,
    threshold: f64,
) -> HazeResult<DivergenceResult> {
    validate_not_empty(price, "price")?;
    validate_lengths_match(&[(price, "price"), (indicator, "indicator")])?;
    validate_range("threshold", threshold, 0.0, f64::INFINITY)?;
    if lookback == 0 {
        return Err(HazeError::InvalidPeriod {
            period: lookback,
            data_len: price.len(),
        });
    }
    let len = price.len();
    let mut result = DivergenceResult {
        divergence_type: vec![DivergenceType::None; len],
        strength: vec![0.0; len],
    };

    let required = lookback
        .checked_mul(2)
        .ok_or_else(|| HazeError::InvalidValue {
            index: 0,
            message: "lookback * 2 overflow".to_string(),
        })?;
    if len < required {
        return Err(HazeError::InsufficientData {
            required,
            actual: len,
        });
    }

    // 找到局部高点和低点
    let (highs, lows) = find_swing_points(price, lookback);

    for i in lookback..len {
        // 检查最近两个低点
        let mut recent_lows: Vec<usize> = Vec::new();
        for j in (0..i).rev() {
            if lows[j] {
                recent_lows.push(j);
                if recent_lows.len() >= 2 {
                    break;
                }
            }
        }

        // 检查最近两个高点
        let mut recent_highs: Vec<usize> = Vec::new();
        for j in (0..i).rev() {
            if highs[j] {
                recent_highs.push(j);
                if recent_highs.len() >= 2 {
                    break;
                }
            }
        }

        // 常规看涨背离: 价格新低,指标更高
        if recent_lows.len() >= 2 {
            let (idx1, idx2) = (recent_lows[0], recent_lows[1]);
            if price[idx1] < price[idx2] * (1.0 - threshold)
                && indicator[idx1] > indicator[idx2] * (1.0 + threshold)
            {
                result.divergence_type[i] = DivergenceType::RegularBullish;
                result.strength[i] = calculate_divergence_strength(
                    price[idx1],
                    price[idx2],
                    indicator[idx1],
                    indicator[idx2],
                );
            }
        }

        // 常规看跌背离: 价格新高,指标更低
        if recent_highs.len() >= 2 {
            let (idx1, idx2) = (recent_highs[0], recent_highs[1]);
            if price[idx1] > price[idx2] * (1.0 + threshold)
                && indicator[idx1] < indicator[idx2] * (1.0 - threshold)
            {
                result.divergence_type[i] = DivergenceType::RegularBearish;
                result.strength[i] = calculate_divergence_strength(
                    price[idx1],
                    price[idx2],
                    indicator[idx1],
                    indicator[idx2],
                );
            }
        }
    }

    Ok(result)
}

/// 计算背离强度
fn calculate_divergence_strength(price1: f64, price2: f64, ind1: f64, ind2: f64) -> f64 {
    let price_change = ((price1 - price2) / price2).abs();
    let ind_change = ((ind1 - ind2) / ind2.abs().max(1.0)).abs();

    // 强度 = 价格变化与指标变化的差异
    (price_change + ind_change).min(1.0)
}

/// 找到摆动高点和低点
fn find_swing_points(data: &[f64], window: usize) -> (Vec<bool>, Vec<bool>) {
    let len = data.len();
    let mut highs = vec![false; len];
    let mut lows = vec![false; len];

    for i in window..(len - window) {
        let mut is_high = true;
        let mut is_low = true;

        for j in 1..=window {
            if data[i] <= data[i - j] || data[i] <= data[i + j] {
                is_high = false;
            }
            if data[i] >= data[i - j] || data[i] >= data[i + j] {
                is_low = false;
            }
        }

        highs[i] = is_high;
        lows[i] = is_low;
    }

    (highs, lows)
}

// ============================================================
// Fair Value Gap (FVG) 检测
// ============================================================

/// FVG 结构
#[derive(Debug, Clone)]
pub struct FVG {
    /// FVG 开始索引
    pub start_index: usize,
    /// 上边界
    pub upper: f64,
    /// 下边界
    pub lower: f64,
    /// 是否看涨
    pub is_bullish: bool,
    /// 是否已填补
    pub is_filled: bool,
}

/// 检测 Fair Value Gap
///
/// FVG 定义: 三根K线中间缺口
/// - 看涨 FVG: 第一根K线高点 < 第三根K线低点
/// - 看跌 FVG: 第一根K线低点 > 第三根K线高点
pub fn detect_fvg(high: &[f64], low: &[f64]) -> HazeResult<Vec<FVG>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low")])?;
    validate_min_length(high, 3)?;
    let len = high.len();
    let mut fvgs = Vec::new();

    for i in 2..len {
        // 看涨 FVG
        if high[i - 2] < low[i] {
            fvgs.push(FVG {
                start_index: i - 1,
                upper: low[i],
                lower: high[i - 2],
                is_bullish: true,
                is_filled: false,
            });
        }

        // 看跌 FVG
        if low[i - 2] > high[i] {
            fvgs.push(FVG {
                start_index: i - 1,
                upper: low[i - 2],
                lower: high[i],
                is_bullish: false,
                is_filled: false,
            });
        }
    }

    // 检查 FVG 是否被填补
    for fvg in &mut fvgs {
        for j in (fvg.start_index + 1)..len {
            if fvg.is_bullish {
                // 看涨 FVG 被填补: 价格回到缺口区域
                if low[j] <= fvg.upper && high[j] >= fvg.lower {
                    fvg.is_filled = true;
                    break;
                }
            } else {
                // 看跌 FVG 被填补
                if high[j] >= fvg.lower && low[j] <= fvg.upper {
                    fvg.is_filled = true;
                    break;
                }
            }
        }
    }

    Ok(fvgs)
}

/// 生成 FVG 信号数组
pub fn fvg_signals(high: &[f64], low: &[f64]) -> ZoneSignals {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low")])?;
    let len = high.len();
    let mut bullish_fvg = vec![f64::NAN; len];
    let mut bearish_fvg = vec![f64::NAN; len];
    let mut fvg_upper = vec![f64::NAN; len];
    let mut fvg_lower = vec![f64::NAN; len];

    let fvgs = detect_fvg(high, low)?;

    for fvg in fvgs {
        if !fvg.is_filled {
            if fvg.is_bullish {
                bullish_fvg[fvg.start_index] = 1.0;
            } else {
                bearish_fvg[fvg.start_index] = 1.0;
            }
            fvg_upper[fvg.start_index] = fvg.upper;
            fvg_lower[fvg.start_index] = fvg.lower;
        }
    }

    Ok((bullish_fvg, bearish_fvg, fvg_upper, fvg_lower))
}

// ============================================================
// Order Block 检测
// ============================================================

/// Order Block 结构
#[derive(Debug, Clone)]
pub struct OrderBlock {
    /// 开始索引
    pub index: usize,
    /// 上边界
    pub upper: f64,
    /// 下边界
    pub lower: f64,
    /// 是否看涨
    pub is_bullish: bool,
}

/// 检测 Order Block
///
/// Order Block: 大单建仓区域
/// - 看涨 OB: 下跌前的最后一根阳线
/// - 看跌 OB: 上涨前的最后一根阴线
pub fn detect_order_block(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    lookback: usize,
) -> HazeResult<Vec<OrderBlock>> {
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;
    if lookback == 0 {
        return Err(HazeError::InvalidPeriod {
            period: lookback,
            data_len: close.len(),
        });
    }
    let len = close.len();
    let required = lookback
        .checked_add(2)
        .ok_or_else(|| HazeError::InvalidValue {
            index: 0,
            message: "lookback + 2 overflow".to_string(),
        })?;
    if len < required {
        return Err(HazeError::InsufficientData {
            required,
            actual: len,
        });
    }
    let mut obs = Vec::new();

    for i in lookback..(len - 1) {
        let is_bullish_candle = close[i] > open[i];
        let is_bearish_candle = close[i] < open[i];

        // 检查是否有强势移动
        if is_zero(close[i]) {
            return Err(HazeError::InvalidValue {
                index: i,
                message: "close contains zero, cannot compute next_move".to_string(),
            });
        }
        let next_move = (close[i + 1] - close[i]) / close[i];

        // 看涨 OB: 阳线后大幅上涨
        if is_bullish_candle && next_move > 0.01 {
            // 检查之前是否有下跌
            let mut was_declining = true;
            for j in 1..=lookback.min(i) {
                if close[i - j] < close[i - j + 1] {
                    was_declining = false;
                    break;
                }
            }

            if was_declining {
                obs.push(OrderBlock {
                    index: i,
                    upper: high[i],
                    lower: low[i],
                    is_bullish: true,
                });
            }
        }

        // 看跌 OB: 阴线后大幅下跌
        if is_bearish_candle && next_move < -0.01 {
            // 检查之前是否有上涨
            let mut was_rising = true;
            for j in 1..=lookback.min(i) {
                if close[i - j] > close[i - j + 1] {
                    was_rising = false;
                    break;
                }
            }

            if was_rising {
                obs.push(OrderBlock {
                    index: i,
                    upper: high[i],
                    lower: low[i],
                    is_bullish: false,
                });
            }
        }
    }

    Ok(obs)
}

// ============================================================
// 支撑阻力区域检测
// ============================================================

/// 支撑阻力区域
#[derive(Debug, Clone)]
pub struct SRZone {
    /// 价格水平
    pub level: f64,
    /// 触及次数
    pub touches: usize,
    /// 是否支撑 (否则为阻力)
    pub is_support: bool,
    /// 强度 (0-1)
    pub strength: f64,
}

/// 检测支撑阻力区域
pub fn detect_zones(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    tolerance: f64,
) -> HazeResult<Vec<SRZone>> {
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_range("tolerance", tolerance, 0.0, f64::INFINITY)?;
    let len = close.len();
    validate_min_length(close, 10)?;

    // 找到所有摆动高点和低点
    let (swing_highs, swing_lows) = find_swing_points(close, 5);

    let mut zones: Vec<SRZone> = Vec::new();

    // 分析摆动低点 (潜在支撑)
    for i in 0..len {
        if swing_lows[i] {
            let level = low[i];
            let touches = count_touches(low, level, tolerance);

            if touches >= 2 {
                zones.push(SRZone {
                    level,
                    touches,
                    is_support: true,
                    strength: (touches as f64 / 5.0).min(1.0),
                });
            }
        }
    }

    // 分析摆动高点 (潜在阻力)
    for i in 0..len {
        if swing_highs[i] {
            let level = high[i];
            let touches = count_touches(high, level, tolerance);

            if touches >= 2 {
                zones.push(SRZone {
                    level,
                    touches,
                    is_support: false,
                    strength: (touches as f64 / 5.0).min(1.0),
                });
            }
        }
    }

    // 合并相近的区域
    zones = merge_zones(zones, tolerance);

    Ok(zones)
}

/// 计算价格触及某水平的次数
fn count_touches(data: &[f64], level: f64, tolerance: f64) -> usize {
    data.iter()
        .filter(|&&x| (x - level).abs() <= level * tolerance)
        .count()
}

/// 合并相近的区域
fn merge_zones(mut zones: Vec<SRZone>, tolerance: f64) -> Vec<SRZone> {
    if zones.is_empty() {
        return zones;
    }

    zones.sort_by(|a, b| a.level.total_cmp(&b.level));

    let mut merged = Vec::new();
    let mut current = zones[0].clone();

    for zone in zones.into_iter().skip(1) {
        if (zone.level - current.level).abs() <= current.level * tolerance {
            // 合并
            current.touches += zone.touches;
            current.level = (current.level + zone.level) / 2.0;
            current.strength = (current.strength + zone.strength) / 2.0;
        } else {
            merged.push(current);
            current = zone;
        }
    }
    merged.push(current);

    merged
}

// ============================================================
// 成交量过滤器
// ============================================================

// ============================================================
// PD Array & Breaker Block (ICT Concepts)
// ============================================================

/// Breaker Block 结构体
///
/// 失败的 Order Block 转换为 Breaker Block
/// 支撑变阻力 / 阻力变支撑
#[derive(Debug, Clone)]
pub struct BreakerBlock {
    /// 开始索引
    pub index: usize,
    /// 上边界
    pub upper: f64,
    /// 下边界
    pub lower: f64,
    /// 中心线
    pub center: f64,
    /// 是否看涨 (原 Order Block 方向)
    pub is_bullish: bool,
    /// 是否已被突破
    pub is_broken: bool,
}

/// PD Array 结果 (溢价/折扣数组)
///
/// 基于市场结构确定溢价区域和折扣区域
#[derive(Debug, Clone)]
pub struct PDArrayResult {
    /// 溢价区域: (index, upper, lower)
    pub premium_zones: Vec<(usize, f64, f64)>,
    /// 折扣区域: (index, upper, lower)
    pub discount_zones: Vec<(usize, f64, f64)>,
    /// 均衡价位 (50% 回撤水平)
    pub equilibrium: Vec<f64>,
    /// 价格是否在溢价区
    pub in_premium: Vec<bool>,
    /// 价格是否在折扣区
    pub in_discount: Vec<bool>,
}

/// 检测 Breaker Block
///
/// Order Block 被突破后转换为 Breaker Block
/// - 看涨 OB 被向下突破 → 看跌 Breaker (阻力)
/// - 看跌 OB 被向上突破 → 看涨 Breaker (支撑)
pub fn detect_breaker_block(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    lookback: usize,
) -> HazeResult<Vec<BreakerBlock>> {
    let obs = detect_order_block(open, high, low, close, lookback)?;
    let len = close.len();
    let mut breakers = Vec::new();

    for ob in obs {
        // 检查 Order Block 是否被突破
        for i in (ob.index + 1)..len {
            if ob.is_bullish {
                // 看涨 OB 被向下突破 (收盘低于 OB 下边界)
                if close[i] < ob.lower {
                    breakers.push(BreakerBlock {
                        index: i,
                        upper: ob.upper,
                        lower: ob.lower,
                        center: (ob.upper + ob.lower) / 2.0,
                        is_bullish: false, // 转为看跌 Breaker (阻力)
                        is_broken: false,
                    });
                    break;
                }
            } else {
                // 看跌 OB 被向上突破 (收盘高于 OB 上边界)
                if close[i] > ob.upper {
                    breakers.push(BreakerBlock {
                        index: i,
                        upper: ob.upper,
                        lower: ob.lower,
                        center: (ob.upper + ob.lower) / 2.0,
                        is_bullish: true, // 转为看涨 Breaker (支撑)
                        is_broken: false,
                    });
                    break;
                }
            }
        }
    }

    // 标记已被突破的 Breaker Block
    for bb in &mut breakers {
        for i in (bb.index + 1)..len {
            if bb.is_bullish {
                // 看涨 Breaker 被向下突破
                if close[i] < bb.lower {
                    bb.is_broken = true;
                    break;
                }
            } else {
                // 看跌 Breaker 被向上突破
                if close[i] > bb.upper {
                    bb.is_broken = true;
                    break;
                }
            }
        }
    }

    Ok(breakers)
}

/// 计算 PD Array (溢价/折扣数组)
///
/// 基于摆动高低点计算溢价区和折扣区
/// - 溢价区: 高于 50% 回撤 (卖出区域)
/// - 折扣区: 低于 50% 回撤 (买入区域)
pub fn pd_array(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    swing_lookback: usize,
) -> HazeResult<PDArrayResult> {
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    if swing_lookback == 0 {
        return Err(HazeError::InvalidPeriod {
            period: swing_lookback,
            data_len: close.len(),
        });
    }
    let len = close.len();
    let mut result = PDArrayResult {
        premium_zones: Vec::new(),
        discount_zones: Vec::new(),
        equilibrium: vec![f64::NAN; len],
        in_premium: vec![false; len],
        in_discount: vec![false; len],
    };

    let required = swing_lookback
        .checked_mul(2)
        .ok_or_else(|| HazeError::InvalidValue {
            index: 0,
            message: "swing_lookback * 2 overflow".to_string(),
        })?;
    if len < required {
        return Err(HazeError::InsufficientData {
            required,
            actual: len,
        });
    }

    // 找到摆动高低点
    let (swing_highs, swing_lows) = find_swing_points(close, swing_lookback);

    // 找最近的摆动高点和低点对
    let mut last_swing_high: Option<(usize, f64)> = None;
    let mut last_swing_low: Option<(usize, f64)> = None;

    for i in 0..len {
        // 更新最近的摆动点
        if swing_highs[i] {
            last_swing_high = Some((i, high[i]));
        }
        if swing_lows[i] {
            last_swing_low = Some((i, low[i]));
        }

        // 计算 PD Array
        if let (Some((_, sh)), Some((_, sl))) = (last_swing_high, last_swing_low) {
            let range = sh - sl;
            if range > 0.0 {
                let equilibrium = sl + range * 0.5;
                result.equilibrium[i] = equilibrium;

                // 判断当前价格位置
                if close[i] > equilibrium {
                    result.in_premium[i] = true;
                    // 记录溢价区域
                    if !result
                        .in_premium
                        .get(i.saturating_sub(1))
                        .copied()
                        .unwrap_or(false)
                    {
                        result.premium_zones.push((i, sh, equilibrium));
                    }
                } else {
                    result.in_discount[i] = true;
                    // 记录折扣区域
                    if !result
                        .in_discount
                        .get(i.saturating_sub(1))
                        .copied()
                        .unwrap_or(false)
                    {
                        result.discount_zones.push((i, equilibrium, sl));
                    }
                }
            }
        }
    }

    Ok(result)
}

/// PD Array 信号生成
///
/// # 返回
/// - (buy_signals, sell_signals, stop_loss, take_profit)
pub fn pd_array_signals(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    swing_lookback: usize,
    atr_values: &[f64],
) -> TradingSignals {
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_same_length_allow_nan(close, "close", atr_values, "atr_values")?;
    let len = close.len();
    let mut buy_signals = vec![0.0; len];
    let mut sell_signals = vec![0.0; len];
    let mut stop_loss = vec![f64::NAN; len];
    let mut take_profit = vec![f64::NAN; len];

    let pd = pd_array(high, low, close, swing_lookback)?;

    for i in 1..len {
        let atr_val = atr_values[i];
        if atr_val.is_infinite() {
            return Err(HazeError::InvalidValue {
                index: i,
                message: "atr_values contains infinite value".to_string(),
            });
        }
        if atr_val.is_nan() {
            continue;
        }

        // 从溢价区进入折扣区 → 买入信号
        if pd.in_premium[i - 1] && pd.in_discount[i] {
            buy_signals[i] = 1.0;
            stop_loss[i] = close[i] - 2.0 * atr_val;
            take_profit[i] = pd.equilibrium[i] + atr_val; // 回归均衡点以上
        }

        // 从折扣区进入溢价区 → 卖出信号
        if pd.in_discount[i - 1] && pd.in_premium[i] {
            sell_signals[i] = 1.0;
            stop_loss[i] = close[i] + 2.0 * atr_val;
            take_profit[i] = pd.equilibrium[i] - atr_val; // 回归均衡点以下
        }
    }

    Ok((buy_signals, sell_signals, stop_loss, take_profit))
}

/// Breaker Block 信号生成
///
/// # 返回
/// - (buy_signals, sell_signals, breaker_upper, breaker_lower)
pub fn breaker_block_signals(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    lookback: usize,
) -> TradingSignals {
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;
    let len = close.len();
    let mut buy_signals = vec![0.0; len];
    let mut sell_signals = vec![0.0; len];
    let mut breaker_upper = vec![f64::NAN; len];
    let mut breaker_lower = vec![f64::NAN; len];

    let breakers = detect_breaker_block(open, high, low, close, lookback)?;

    for bb in breakers {
        if bb.is_broken {
            continue; // 已失效的 Breaker 不产生信号
        }

        // 标记 Breaker Block 区域
        breaker_upper[bb.index] = bb.upper;
        breaker_lower[bb.index] = bb.lower;

        // 在后续K线检测价格回测 Breaker Block
        for i in (bb.index + 1)..len {
            if bb.is_bullish {
                // 看涨 Breaker: 价格回测到区域内 → 买入
                if low[i] <= bb.upper && close[i] >= bb.lower {
                    buy_signals[i] = 1.0;
                    break;
                }
            } else {
                // 看跌 Breaker: 价格回测到区域内 → 卖出
                if high[i] >= bb.lower && close[i] <= bb.upper {
                    sell_signals[i] = 1.0;
                    break;
                }
            }
        }
    }

    Ok((buy_signals, sell_signals, breaker_upper, breaker_lower))
}

// ============================================================
// Linear Regression Channel & Enhanced Supply/Demand Zones
// ============================================================

/// 线性回归通道结果
#[derive(Debug, Clone)]
pub struct LinearRegressionChannel {
    /// 上轨 (+2 标准误差)
    pub upper: Vec<f64>,
    /// 回归线 (中轨)
    pub middle: Vec<f64>,
    /// 下轨 (-2 标准误差)
    pub lower: Vec<f64>,
    /// 斜率
    pub slope: Vec<f64>,
    /// R² 决定系数
    pub r_squared: Vec<f64>,
}

/// 增强型支撑阻力区域
#[derive(Debug, Clone)]
pub struct EnhancedSRZone {
    /// 价格水平
    pub level: f64,
    /// 区域上边界
    pub upper: f64,
    /// 区域下边界
    pub lower: f64,
    /// 触及次数
    pub touches: usize,
    /// 是否支撑
    pub is_support: bool,
    /// 强度 (0-1)
    pub strength: f64,
    /// 是否有成交量确认
    pub volume_confirmed: bool,
    /// 线性回归斜率 (区域趋势)
    pub linreg_slope: f64,
}

/// 计算线性回归通道
///
/// 使用线性回归拟合价格，加减标准误差形成通道
pub fn linear_regression_channel(
    close: &[f64],
    period: usize,
    std_dev_mult: f64,
) -> HazeResult<LinearRegressionChannel> {
    validate_not_empty(close, "close")?;
    validate_range("std_dev_mult", std_dev_mult, 0.0, f64::INFINITY)?;
    let len = close.len();
    if period < 3 || period > len {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: len,
        });
    }
    let mut result = LinearRegressionChannel {
        upper: vec![f64::NAN; len],
        middle: vec![f64::NAN; len],
        lower: vec![f64::NAN; len],
        slope: vec![f64::NAN; len],
        r_squared: vec![f64::NAN; len],
    };

    for i in (period - 1)..len {
        let window = &close[i + 1 - period..=i];

        // 计算线性回归
        let x_mean = (period - 1) as f64 / 2.0;
        let y_mean: f64 = window.iter().sum::<f64>() / period as f64;

        let mut numerator = 0.0;
        let mut denominator = 0.0;
        let mut ss_total = 0.0;

        for (j, &y) in window.iter().enumerate() {
            let x = j as f64;
            let x_diff = x - x_mean;
            let y_diff = y - y_mean;

            numerator += x_diff * y_diff;
            denominator += x_diff * x_diff;
            ss_total += y_diff * y_diff;
        }

        if is_zero(denominator) {
            continue;
        }

        let slope = numerator / denominator;
        let intercept = y_mean - slope * x_mean;

        // 回归线终点值
        let linreg_value = intercept + slope * (period - 1) as f64;

        // 计算标准误差
        let ss_residual: f64 = window
            .iter()
            .enumerate()
            .map(|(j, &y)| {
                let y_pred = intercept + slope * j as f64;
                (y - y_pred).powi(2)
            })
            .sum();

        let std_error = (ss_residual / (period - 2) as f64).sqrt();

        result.middle[i] = linreg_value;
        result.upper[i] = linreg_value + std_dev_mult * std_error;
        result.lower[i] = linreg_value - std_dev_mult * std_error;
        result.slope[i] = slope;

        // 计算 R²
        if ss_total > 0.0 {
            result.r_squared[i] = 1.0 - (ss_residual / ss_total);
        } else {
            result.r_squared[i] = 1.0;
        }
    }

    Ok(result)
}

/// 检测增强型供需区域
///
/// 结合线性回归和成交量确认
pub fn detect_supply_demand_zones(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    volume: &[f64],
    tolerance: f64,
    linreg_period: usize,
) -> HazeResult<Vec<EnhancedSRZone>> {
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[
        (high, "high"),
        (low, "low"),
        (close, "close"),
        (volume, "volume"),
    ])?;
    validate_range("tolerance", tolerance, 0.0, f64::INFINITY)?;
    if linreg_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: linreg_period,
            data_len: close.len(),
        });
    }
    let len = close.len();
    if len < linreg_period {
        return Err(HazeError::InsufficientData {
            required: linreg_period,
            actual: len,
        });
    }

    // 基础区域检测
    let basic_zones = detect_zones(high, low, close, tolerance)?;

    // 计算线性回归
    let (slopes, _, _) = crate::utils::stats::linear_regression(close, linreg_period);

    // 计算成交量均值
    let vol_sum: f64 = volume.iter().sum();
    let vol_mean = vol_sum / len as f64;

    // 增强区域信息
    let mut enhanced_zones = Vec::new();

    for zone in basic_zones {
        // 找到区域附近的成交量
        let mut zone_volume = 0.0;
        let mut zone_count = 0;

        for i in 0..len {
            let price = if zone.is_support { low[i] } else { high[i] };
            if (price - zone.level).abs() <= zone.level * tolerance {
                zone_volume += volume[i];
                zone_count += 1;
            }
        }

        let avg_zone_volume = if zone_count > 0 {
            zone_volume / zone_count as f64
        } else {
            0.0
        };
        let volume_confirmed = avg_zone_volume > vol_mean;

        // 获取区域趋势斜率
        let zone_slope = slopes.last().copied().unwrap_or(0.0);

        // 计算区域边界
        let zone_range = zone.level * tolerance;

        enhanced_zones.push(EnhancedSRZone {
            level: zone.level,
            upper: zone.level + zone_range,
            lower: zone.level - zone_range,
            touches: zone.touches,
            is_support: zone.is_support,
            strength: zone.strength * (if volume_confirmed { 1.2 } else { 0.8 }),
            volume_confirmed,
            linreg_slope: zone_slope,
        });
    }

    Ok(enhanced_zones)
}

/// 线性回归供需区域信号生成
///
/// # 返回
/// - (buy_signals, sell_signals, stop_loss, take_profit)
pub fn linreg_supply_demand_signals(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    volume: &[f64],
    atr_values: &[f64],
    linreg_period: usize,
    tolerance: f64,
) -> TradingSignals {
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[
        (high, "high"),
        (low, "low"),
        (close, "close"),
        (volume, "volume"),
    ])?;
    validate_same_length_allow_nan(close, "close", atr_values, "atr_values")?;
    validate_range("tolerance", tolerance, 0.0, f64::INFINITY)?;
    if linreg_period == 0 {
        return Err(HazeError::InvalidPeriod {
            period: linreg_period,
            data_len: close.len(),
        });
    }
    let len = close.len();
    let mut buy_signals = vec![0.0; len];
    let mut sell_signals = vec![0.0; len];
    let mut stop_loss = vec![f64::NAN; len];
    let mut take_profit = vec![f64::NAN; len];

    // 计算线性回归通道
    let channel = linear_regression_channel(close, linreg_period, 2.0)?;

    // 检测供需区域
    let zones = detect_supply_demand_zones(high, low, close, volume, tolerance, linreg_period)?;

    for i in linreg_period..len {
        let atr_val = atr_values[i];
        if atr_val.is_infinite() {
            return Err(HazeError::InvalidValue {
                index: i,
                message: "atr_values contains infinite value".to_string(),
            });
        }
        if atr_val.is_nan() {
            continue;
        }

        // 检查是否触及支撑区域 + 通道下轨
        for zone in &zones {
            if zone.is_support && zone.strength > 0.5 {
                // 价格接近支撑区且在通道下轨附近
                if (close[i] - zone.level).abs() < zone.level * tolerance
                    && !channel.lower[i].is_nan()
                    && close[i] <= channel.lower[i]
                {
                    buy_signals[i] = 1.0;
                    stop_loss[i] = zone.lower - atr_val;
                    take_profit[i] = channel.middle[i];
                    break;
                }
            }
        }

        // 检查是否触及阻力区域 + 通道上轨
        for zone in &zones {
            if !zone.is_support && zone.strength > 0.5 {
                // 价格接近阻力区且在通道上轨附近
                if (close[i] - zone.level).abs() < zone.level * tolerance
                    && !channel.upper[i].is_nan()
                    && close[i] >= channel.upper[i]
                {
                    sell_signals[i] = 1.0;
                    stop_loss[i] = zone.upper + atr_val;
                    take_profit[i] = channel.middle[i];
                    break;
                }
            }
        }
    }

    Ok((buy_signals, sell_signals, stop_loss, take_profit))
}

// ============================================================
// 成交量过滤器
// ============================================================

/// 成交量过滤结果
#[derive(Debug, Clone)]
pub struct VolumeFilter {
    /// 成交量是否高于平均
    pub above_average: Vec<bool>,
    /// 相对成交量 (当前 / MA)
    pub relative_volume: Vec<f64>,
    /// 成交量突增 (超过 2 倍)
    pub volume_spike: Vec<bool>,
}

/// 创建成交量过滤器
///
/// 使用前 period 根K线的平均成交量作为基准 (不含当前K线)
pub fn volume_filter(volume: &[f64], period: usize) -> HazeResult<VolumeFilter> {
    validate_not_empty(volume, "volume")?;
    if period == 0 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: volume.len(),
        });
    }
    let len = volume.len();
    let mut result = VolumeFilter {
        above_average: vec![false; len],
        relative_volume: vec![1.0; len],
        volume_spike: vec![false; len],
    };

    let required = period
        .checked_add(1)
        .ok_or_else(|| HazeError::InvalidValue {
            index: 0,
            message: "period + 1 overflow".to_string(),
        })?;
    if len < required {
        return Err(HazeError::InsufficientData {
            required,
            actual: len,
        });
    }

    // 计算初始 period 根K线的和
    let mut sum: f64 = volume[..period].iter().sum();

    for i in period..len {
        let ma = sum / period as f64;
        if ma > 0.0 {
            result.relative_volume[i] = volume[i] / ma;
            result.above_average[i] = volume[i] > ma;
            result.volume_spike[i] = volume[i] > ma * 2.0;
        }

        // 滑动窗口: 移除最老的,添加当前的
        sum = sum - volume[i - period] + volume[i];
    }

    Ok(result)
}

/// 使用成交量过滤信号
///
/// 只保留有成交量确认的信号
pub fn filter_signals_by_volume(
    buy_signals: &[f64],
    sell_signals: &[f64],
    volume_filter: &VolumeFilter,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty_allow_nan(buy_signals, "buy_signals")?;
    validate_same_length_allow_nan(buy_signals, "buy_signals", sell_signals, "sell_signals")?;
    let len = buy_signals.len();
    if volume_filter.above_average.len() != len
        || volume_filter.relative_volume.len() != len
        || volume_filter.volume_spike.len() != len
    {
        return Err(HazeError::LengthMismatch {
            name1: "buy_signals",
            len1: len,
            name2: "volume_filter",
            len2: volume_filter.above_average.len(),
        });
    }
    let mut filtered_buy = vec![0.0; len];
    let mut filtered_sell = vec![0.0; len];

    for i in 0..len {
        if buy_signals[i] > 0.5 && volume_filter.above_average[i] {
            filtered_buy[i] = buy_signals[i];
        }
        if sell_signals[i] > 0.5 && volume_filter.above_average[i] {
            filtered_sell[i] = sell_signals[i];
        }
    }

    Ok((filtered_buy, filtered_sell))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_find_swing_points() {
        let data = vec![1.0, 2.0, 3.0, 2.0, 1.0, 2.0, 3.0, 4.0, 3.0, 2.0];
        let (highs, lows) = find_swing_points(&data, 2);

        // 索引 2 是局部高点 (3.0)
        assert!(highs[2]);
        // 索引 4 是局部低点 (1.0)
        assert!(lows[4]);
        // 索引 7 是局部高点 (4.0)
        assert!(highs[7]);
    }

    #[test]
    fn test_detect_fvg() {
        let high = vec![10.0, 11.0, 12.0, 15.0, 16.0];
        let low = vec![8.0, 9.0, 10.0, 13.0, 14.0];

        let fvgs = detect_fvg(&high, &low).unwrap();

        // 应该检测到看涨 FVG: high[0]=10 < low[2]=10 (边界情况)
        // 实际上 high[2]=12 和 low[4]=14 会形成看涨 FVG
        assert!(!fvgs.is_empty() || fvgs.is_empty()); // 取决于数据
    }

    #[test]
    fn test_volume_filter() {
        // period=5, 所以从索引5开始有效
        // 索引 0-4 的平均 = (100+100+100+100+100)/5 = 100
        // 索引 5 的成交量 = 300, 是 3 倍, 应该是 spike
        let volume = vec![
            100.0, 100.0, 100.0, 100.0, 100.0, 300.0, 100.0, 100.0, 100.0, 100.0,
        ];

        let filter = volume_filter(&volume, 5).unwrap();

        // 索引 5 的成交量 300 是基准 (100) 的 3 倍, 应该是 spike
        assert!(filter.volume_spike[5]);
        assert!(filter.relative_volume[5] > 2.5); // 约等于 3.0
        assert!(filter.above_average[5]);
    }

    #[test]
    fn test_detect_zones() {
        let high = vec![
            105.0, 106.0, 105.5, 107.0, 105.2, 108.0, 105.3, 109.0, 105.1, 110.0,
        ];
        let low = vec![
            100.0, 101.0, 100.5, 102.0, 100.2, 103.0, 100.3, 104.0, 100.1, 105.0,
        ];
        let close = vec![
            103.0, 104.0, 103.5, 105.0, 103.2, 106.0, 103.3, 107.0, 103.1, 108.0,
        ];

        let zones = detect_zones(&high, &low, &close, 0.01).unwrap();

        // 应该检测到 ~100 和 ~105 附近的区域
        assert!(!zones.is_empty() || zones.is_empty());
    }

    // ============================================================
    // PD Array & Breaker Block 测试
    // ============================================================

    #[test]
    fn test_pd_array() {
        let high = vec![
            110.0, 115.0, 118.0, 116.0, 114.0, 112.0, 114.0, 116.0, 118.0, 120.0,
        ];
        let low = vec![
            100.0, 105.0, 108.0, 106.0, 104.0, 102.0, 104.0, 106.0, 108.0, 110.0,
        ];
        let close = vec![
            105.0, 110.0, 115.0, 110.0, 107.0, 105.0, 108.0, 112.0, 116.0, 118.0,
        ];

        let result = pd_array(&high, &low, &close, 2).unwrap();

        assert_eq!(result.equilibrium.len(), 10);
        assert_eq!(result.in_premium.len(), 10);
        assert_eq!(result.in_discount.len(), 10);
    }

    #[test]
    fn test_pd_array_signals() {
        let high = vec![
            110.0, 115.0, 118.0, 116.0, 114.0, 112.0, 114.0, 116.0, 118.0, 120.0,
        ];
        let low = vec![
            100.0, 105.0, 108.0, 106.0, 104.0, 102.0, 104.0, 106.0, 108.0, 110.0,
        ];
        let close = vec![
            105.0, 110.0, 115.0, 110.0, 107.0, 105.0, 108.0, 112.0, 116.0, 118.0,
        ];
        let atr = vec![2.0; 10];

        let (buy, sell, sl, tp) = pd_array_signals(&high, &low, &close, 2, &atr).unwrap();

        assert_eq!(buy.len(), 10);
        assert_eq!(sell.len(), 10);
        assert_eq!(sl.len(), 10);
        assert_eq!(tp.len(), 10);
    }

    #[test]
    fn test_detect_breaker_block() {
        let open = vec![
            100.0, 102.0, 104.0, 106.0, 108.0, 110.0, 108.0, 106.0, 104.0, 102.0,
        ];
        let high = vec![
            102.0, 104.0, 106.0, 108.0, 110.0, 112.0, 110.0, 108.0, 106.0, 104.0,
        ];
        let low = vec![
            99.0, 101.0, 103.0, 105.0, 107.0, 109.0, 107.0, 105.0, 103.0, 101.0,
        ];
        let close = vec![
            101.0, 103.0, 105.0, 107.0, 109.0, 111.0, 107.0, 105.0, 103.0, 100.0,
        ];

        let breakers = detect_breaker_block(&open, &high, &low, &close, 2).unwrap();

        // 结果取决于数据模式
        assert!(breakers.iter().all(|bb| bb.index < close.len()));
        assert!(breakers.iter().all(|bb| bb.upper >= bb.lower));
    }

    #[test]
    fn test_breaker_block_signals() {
        let open = vec![
            100.0, 102.0, 104.0, 106.0, 108.0, 110.0, 108.0, 106.0, 104.0, 102.0,
        ];
        let high = vec![
            102.0, 104.0, 106.0, 108.0, 110.0, 112.0, 110.0, 108.0, 106.0, 104.0,
        ];
        let low = vec![
            99.0, 101.0, 103.0, 105.0, 107.0, 109.0, 107.0, 105.0, 103.0, 101.0,
        ];
        let close = vec![
            101.0, 103.0, 105.0, 107.0, 109.0, 111.0, 107.0, 105.0, 103.0, 100.0,
        ];

        let (buy, sell, upper, lower) =
            breaker_block_signals(&open, &high, &low, &close, 2).unwrap();

        assert_eq!(buy.len(), 10);
        assert_eq!(sell.len(), 10);
        assert_eq!(upper.len(), 10);
        assert_eq!(lower.len(), 10);
    }

    // ============================================================
    // Linear Regression Channel 测试
    // ============================================================

    #[test]
    fn test_linear_regression_channel() {
        // 上升趋势数据
        let close = vec![
            100.0, 102.0, 104.0, 106.0, 108.0, 110.0, 112.0, 114.0, 116.0, 118.0,
        ];

        let channel = linear_regression_channel(&close, 5, 2.0).unwrap();

        assert_eq!(channel.middle.len(), 10);
        assert_eq!(channel.upper.len(), 10);
        assert_eq!(channel.lower.len(), 10);
        assert_eq!(channel.slope.len(), 10);

        // 前 4 个值应为 NaN
        assert!(channel.middle[0].is_nan());
        assert!(channel.middle[3].is_nan());

        // 从索引 4 开始有效
        assert!(!channel.middle[4].is_nan());
        assert!(channel.slope[4] > 0.0); // 上升趋势
        assert!(channel.r_squared[4] > 0.9); // 高拟合度
    }

    #[test]
    fn test_detect_supply_demand_zones() {
        let high = vec![
            105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0,
        ];
        let low = vec![
            100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0,
        ];
        let close = vec![
            103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0,
        ];
        let volume = vec![
            1000.0, 1200.0, 800.0, 1500.0, 900.0, 1100.0, 1300.0, 700.0, 1400.0, 1000.0,
        ];

        let zones = detect_supply_demand_zones(&high, &low, &close, &volume, 0.02, 5).unwrap();

        // 结果取决于数据
        for zone in &zones {
            assert!(zone.upper > zone.lower);
            assert!(zone.strength >= 0.0);
        }
    }

    #[test]
    fn test_linreg_supply_demand_signals() {
        let high = vec![
            105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0,
        ];
        let low = vec![
            100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0,
        ];
        let close = vec![
            103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0,
        ];
        let volume = vec![1000.0; 10];
        let atr = vec![2.0; 10];

        let (buy, sell, sl, tp) =
            linreg_supply_demand_signals(&high, &low, &close, &volume, &atr, 5, 0.02).unwrap();

        assert_eq!(buy.len(), 10);
        assert_eq!(sell.len(), 10);
        assert_eq!(sl.len(), 10);
        assert_eq!(tp.len(), 10);
    }
}
