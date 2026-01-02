// indicators/sfg.rs - SFG 交易信号指标
#![allow(dead_code)]
// 交易信号函数需要完整 OHLCV + 多个配置参数
#![allow(clippy::too_many_arguments)]
#![allow(clippy::type_complexity)]
#![allow(clippy::needless_range_loop)]
//
// 基于系统指标实现的高级复合交易信号
// 使用纯 Rust ML (linfa) 替代 KNN,获得 42-68% 性能提升
// 参考：SFG_交易信号指标.pdf
//
// 错误处理策略 (遵循 CLAUDE.md):
// - 使用 HazeResult<T> 返回类型
// - 函数入口进行输入验证 (Fail-Fast)
// - 子指标错误使用 ? 传播

use crate::errors::validation::{validate_lengths_match, validate_not_empty, validate_period};
use crate::errors::{HazeError, HazeResult};
use crate::indicators::{atr, rsi, supertrend};
use crate::ml::models::ModelType;
use crate::ml::trainer::{
    online_predict_atr2, online_predict_momentum, online_predict_supertrend, TrainConfig,
};
use crate::utils::ma::{ema_allow_nan, sma_allow_nan, wma_allow_nan};
use crate::utils::math::is_not_zero;
use crate::utils::{ema, sma, wma};
use std::cmp::Ordering;

// ============================================================
// ML 增强版 SFG 指标 (推荐使用)
// ============================================================

/// AI SuperTrend 结果
#[derive(Debug, Clone)]
pub struct AISuperTrendResult {
    /// SuperTrend 值
    pub supertrend: Vec<f64>,
    /// 趋势方向: 1.0=看涨, -1.0=看跌
    pub direction: Vec<f64>,
    /// ML 预测的趋势偏移
    pub trend_offset: Vec<f64>,
    /// 买入信号
    pub buy_signals: Vec<f64>,
    /// 卖出信号
    pub sell_signals: Vec<f64>,
    /// 动态止损
    pub stop_loss: Vec<f64>,
    /// 动态止盈
    pub take_profit: Vec<f64>,
}

/// AI SuperTrend - 使用 ML 增强的 SuperTrend
///
/// 使用 linfa SVR/LinearRegression 替代 KNN,性能提升 42-68%
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `st_length`: SuperTrend 周期（默认 10）
/// - `st_multiplier`: SuperTrend ATR 乘数（默认 3.0）
/// - `model_type`: 模型类型 ("linreg" | "ridge")
/// - `lookback`: ML 特征滞后周期（默认 10）
/// - `train_window`: 训练窗口（默认 200）
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 数组长度不匹配
/// - `InvalidPeriod`: 周期参数无效
pub fn ai_supertrend_ml(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    st_length: usize,
    st_multiplier: f64,
    model_type: &str,
    lookback: usize,
    train_window: usize,
) -> HazeResult<AISuperTrendResult> {
    // 输入验证
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(st_length, close.len())?;
    validate_period(lookback, close.len())?;
    if train_window == 0 {
        return Err(HazeError::InvalidPeriod {
            period: train_window,
            data_len: close.len(),
        });
    }

    let len = close.len();
    let required = train_window
        .checked_add(lookback)
        .ok_or_else(|| HazeError::InvalidValue {
            index: 0,
            message: "train_window + lookback overflow".to_string(),
        })?;
    if len < required {
        return Err(HazeError::InsufficientData {
            required,
            actual: len,
        });
    }

    // 1. 计算传统 SuperTrend
    let (st_values, st_direction, _, _) = supertrend(high, low, close, st_length, st_multiplier)?;

    // 2. 计算 ATR
    let atr_values = atr(high, low, close, st_length)?;

    // 3. ML 预测趋势偏移
    let model_type = match model_type {
        "linreg" => ModelType::LinearRegression,
        "ridge" => ModelType::Ridge,
        other => {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: format!("unknown model_type: {other}"),
            })
        }
    };

    let config = TrainConfig {
        train_window,
        lookback,
        rolling: true,
        model_type,
        ridge_alpha: 1.0,
        use_polynomial: false,
    };

    let trend_offset = online_predict_supertrend(close, &atr_values, &config);

    // 4. 生成增强信号
    let mut buy_signals = vec![0.0; len];
    let mut sell_signals = vec![0.0; len];
    let mut stop_loss = vec![f64::NAN; len];
    let mut take_profit = vec![f64::NAN; len];

    for i in 1..len {
        let prev_dir = st_direction[i - 1];
        let curr_dir = st_direction[i];
        let ml_signal = trend_offset[i];

        // 买入: 方向变为看涨 + ML 预测上涨
        if curr_dir > 0.5 && prev_dir < 0.5 && ml_signal > 0.0 {
            buy_signals[i] = 1.0;
            let atr_val = if atr_values[i].is_nan() {
                0.0
            } else {
                atr_values[i]
            };
            stop_loss[i] = close[i] - 2.0 * atr_val;
            take_profit[i] = close[i] + 3.0 * atr_val;
        }

        // 卖出: 方向变为看跌 + ML 预测下跌
        if curr_dir < -0.5 && prev_dir > -0.5 && ml_signal < 0.0 {
            sell_signals[i] = 1.0;
            let atr_val = if atr_values[i].is_nan() {
                0.0
            } else {
                atr_values[i]
            };
            stop_loss[i] = close[i] + 2.0 * atr_val;
            take_profit[i] = close[i] - 3.0 * atr_val;
        }
    }

    Ok(AISuperTrendResult {
        supertrend: st_values,
        direction: st_direction,
        trend_offset,
        buy_signals,
        sell_signals,
        stop_loss,
        take_profit,
    })
}

/// ATR2 信号结果 (ML 增强版)
#[derive(Debug, Clone)]
pub struct ATR2SignalResult {
    pub rsi: Vec<f64>,
    pub dynamic_buy_threshold: Vec<f64>,
    pub dynamic_sell_threshold: Vec<f64>,
    pub buy_signals: Vec<f64>,
    pub sell_signals: Vec<f64>,
    pub signal_strength: Vec<f64>,
    pub stop_loss: Vec<f64>,
    pub take_profit: Vec<f64>,
}

/// ATR2 信号指标 - ML 增强版
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 数组长度不匹配
/// - `InvalidPeriod`: 周期参数无效
pub fn atr2_signals_ml(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    volume: &[f64],
    rsi_period: usize,
    atr_period: usize,
    ridge_alpha: f64,
    momentum_window: usize,
) -> HazeResult<ATR2SignalResult> {
    // 输入验证
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[
        (high, "high"),
        (low, "low"),
        (close, "close"),
        (volume, "volume"),
    ])?;
    validate_period(rsi_period, close.len())?;
    validate_period(atr_period, close.len())?;
    if momentum_window == 0 {
        return Err(HazeError::InvalidPeriod {
            period: momentum_window,
            data_len: close.len(),
        });
    }

    let len = close.len();
    let required =
        200usize
            .checked_add(momentum_window)
            .ok_or_else(|| HazeError::InvalidValue {
                index: 0,
                message: "train_window + momentum_window overflow".to_string(),
            })?;
    if len < required {
        return Err(HazeError::InsufficientData {
            required,
            actual: len,
        });
    }

    // 1. 计算基础指标
    let rsi_values = rsi(close, rsi_period)?;
    let atr_values = atr(high, low, close, atr_period)?;

    // 2. ML 预测阈值调整
    let config = TrainConfig {
        train_window: 200,
        lookback: momentum_window,
        rolling: true,
        model_type: ModelType::Ridge,
        ridge_alpha,
        use_polynomial: false,
    };

    let threshold_adj = online_predict_atr2(close, &atr_values, volume, &config);

    // 3. 计算动态阈值
    let mut dynamic_buy_threshold = vec![30.0; len];
    let mut dynamic_sell_threshold = vec![70.0; len];

    for i in 0..len {
        let adj = threshold_adj[i].clamp(-10.0, 10.0);
        dynamic_buy_threshold[i] = 30.0 - adj;
        dynamic_sell_threshold[i] = 70.0 + adj;
    }

    // 4. 生成信号
    let mut buy_signals = vec![0.0; len];
    let mut sell_signals = vec![0.0; len];
    let mut signal_strength = vec![0.0; len];
    let mut stop_loss = vec![f64::NAN; len];
    let mut take_profit = vec![f64::NAN; len];

    let volume_ma = sma(volume, atr_period)?;

    for i in atr_period..len {
        let volume_confirmed = if !volume_ma[i].is_nan() && volume_ma[i] > 0.0 {
            volume[i] > volume_ma[i]
        } else {
            true
        };

        // 买入信号
        if !rsi_values[i].is_nan() && rsi_values[i] < dynamic_buy_threshold[i] && volume_confirmed {
            buy_signals[i] = 1.0;
            signal_strength[i] = (dynamic_buy_threshold[i] - rsi_values[i]) / 30.0;
            let atr_val = if atr_values[i].is_nan() {
                0.0
            } else {
                atr_values[i]
            };
            stop_loss[i] = close[i] - 2.0 * atr_val;
            take_profit[i] = close[i] + 3.0 * atr_val;
        }

        // 卖出信号
        if !rsi_values[i].is_nan() && rsi_values[i] > dynamic_sell_threshold[i] && volume_confirmed
        {
            sell_signals[i] = 1.0;
            signal_strength[i] = (rsi_values[i] - dynamic_sell_threshold[i]) / 30.0;
            let atr_val = if atr_values[i].is_nan() {
                0.0
            } else {
                atr_values[i]
            };
            stop_loss[i] = close[i] + 2.0 * atr_val;
            take_profit[i] = close[i] - 3.0 * atr_val;
        }
    }

    Ok(ATR2SignalResult {
        rsi: rsi_values,
        dynamic_buy_threshold,
        dynamic_sell_threshold,
        buy_signals,
        sell_signals,
        signal_strength,
        stop_loss,
        take_profit,
    })
}

/// AI Momentum Index 结果 (ML 增强版)
#[derive(Debug, Clone)]
pub struct AIMomentumResult {
    pub rsi: Vec<f64>,
    pub predicted_momentum: Vec<f64>,
    pub momentum_ma: Vec<f64>,
    pub zero_cross_buy: Vec<f64>,
    pub zero_cross_sell: Vec<f64>,
    pub overbought: Vec<f64>,
    pub oversold: Vec<f64>,
}

/// AI Momentum Index - ML 增强版
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `InvalidPeriod`: 周期参数无效
pub fn ai_momentum_index_ml(
    close: &[f64],
    rsi_period: usize,
    smooth_period: usize,
    use_polynomial: bool,
    lookback: usize,
    train_window: usize,
) -> HazeResult<AIMomentumResult> {
    // 输入验证
    validate_not_empty(close, "close")?;
    validate_period(rsi_period, close.len())?;
    validate_period(smooth_period, close.len())?;
    validate_period(lookback, close.len())?;
    if train_window == 0 {
        return Err(HazeError::InvalidPeriod {
            period: train_window,
            data_len: close.len(),
        });
    }

    let len = close.len();
    let required = train_window
        .checked_add(lookback)
        .ok_or_else(|| HazeError::InvalidValue {
            index: 0,
            message: "train_window + lookback overflow".to_string(),
        })?;
    if len < required {
        return Err(HazeError::InsufficientData {
            required,
            actual: len,
        });
    }

    // 1. 计算 RSI
    let rsi_values = rsi(close, rsi_period)?;

    // 2. ML 预测动量
    let config = TrainConfig {
        train_window,
        lookback,
        rolling: true,
        model_type: ModelType::LinearRegression,
        ridge_alpha: 1.0,
        use_polynomial,
    };

    let predicted_momentum = online_predict_momentum(&rsi_values, &config);

    // 3. 计算动量移动平均
    let momentum_ma = ema_allow_nan(&predicted_momentum, smooth_period)?;

    // 4. 生成信号
    let mut zero_cross_buy = vec![0.0; len];
    let mut zero_cross_sell = vec![0.0; len];
    let mut overbought = vec![0.0; len];
    let mut oversold = vec![0.0; len];

    for i in 1..len {
        let curr_mom = predicted_momentum[i];
        let prev_mom = predicted_momentum[i - 1];

        // 零线交叉
        if curr_mom > 0.0 && prev_mom <= 0.0 {
            zero_cross_buy[i] = 1.0;
        }
        if curr_mom < 0.0 && prev_mom >= 0.0 {
            zero_cross_sell[i] = 1.0;
        }

        // 超买超卖
        if curr_mom > 25.0 {
            overbought[i] = 1.0;
        }
        if curr_mom < -25.0 {
            oversold[i] = 1.0;
        }
    }

    Ok(AIMomentumResult {
        rsi: rsi_values,
        predicted_momentum,
        momentum_ma,
        zero_cross_buy,
        zero_cross_sell,
        overbought,
        oversold,
    })
}

// ============================================================
// General Parameters (通用参数指标)
// ============================================================

/// General Parameters 结果
///
/// EMA 通道 + 网格参数系统
#[derive(Debug, Clone)]
pub struct GeneralParamsResult {
    // EMA 通道
    /// 上轨 (慢 EMA + ATR)
    pub ema_upper: Vec<f64>,
    /// 中轨 (慢 EMA)
    pub ema_middle: Vec<f64>,
    /// 下轨 (慢 EMA - ATR)
    pub ema_lower: Vec<f64>,

    // 快慢 EMA
    /// 快速 EMA
    pub ema_fast: Vec<f64>,
    /// 慢速 EMA
    pub ema_slow: Vec<f64>,

    // ATR 值（避免下游重复计算）
    /// ATR 序列
    pub atr: Vec<f64>,

    // 价格带
    /// 买入区上边界
    pub buy_zone_upper: Vec<f64>,
    /// 买入区下边界
    pub buy_zone_lower: Vec<f64>,
    /// 卖出区上边界
    pub sell_zone_upper: Vec<f64>,
    /// 卖出区下边界
    pub sell_zone_lower: Vec<f64>,

    // 网格入场价 (多头)
    /// 多头入场价 1 (中轨 - 0.5*ATR)
    pub long_entry_1: Vec<f64>,
    /// 多头入场价 2 (中轨 - 1.0*ATR)
    pub long_entry_2: Vec<f64>,
    /// 多头入场价 3 (中轨 - 1.5*ATR)
    pub long_entry_3: Vec<f64>,

    // 网格入场价 (空头)
    /// 空头入场价 1 (中轨 + 0.5*ATR)
    pub short_entry_1: Vec<f64>,
    /// 空头入场价 2 (中轨 + 1.0*ATR)
    pub short_entry_2: Vec<f64>,
    /// 空头入场价 3 (中轨 + 1.5*ATR)
    pub short_entry_3: Vec<f64>,

    // 解套价格
    /// 多头解套价 (平均入场 + 0.5*ATR)
    pub breakeven_long: Vec<f64>,
    /// 空头解套价 (平均入场 - 0.5*ATR)
    pub breakeven_short: Vec<f64>,

    // 趋势方向
    /// 趋势: 1.0=上涨, -1.0=下跌, 0.0=中性
    pub trend: Vec<f64>,
}

impl GeneralParamsResult {
    fn nan(len: usize) -> Self {
        Self {
            ema_upper: vec![f64::NAN; len],
            ema_middle: vec![f64::NAN; len],
            ema_lower: vec![f64::NAN; len],
            ema_fast: vec![f64::NAN; len],
            ema_slow: vec![f64::NAN; len],
            atr: vec![f64::NAN; len],
            buy_zone_upper: vec![f64::NAN; len],
            buy_zone_lower: vec![f64::NAN; len],
            sell_zone_upper: vec![f64::NAN; len],
            sell_zone_lower: vec![f64::NAN; len],
            long_entry_1: vec![f64::NAN; len],
            long_entry_2: vec![f64::NAN; len],
            long_entry_3: vec![f64::NAN; len],
            short_entry_1: vec![f64::NAN; len],
            short_entry_2: vec![f64::NAN; len],
            short_entry_3: vec![f64::NAN; len],
            breakeven_long: vec![f64::NAN; len],
            breakeven_short: vec![f64::NAN; len],
            trend: vec![0.0; len],
        }
    }
}

/// General Parameters - 通用参数指标
///
/// 提供 EMA 通道、网格入场价和解套价格计算
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `ema_fast_period`: 快速 EMA 周期 (默认 20)
/// - `ema_slow_period`: 慢速 EMA 周期 (默认 50)
/// - `atr_period`: ATR 周期 (默认 14)
/// - `grid_multiplier`: 网格乘数 (默认 1.0)
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 数组长度不匹配
/// - `InvalidPeriod`: 周期参数无效
pub fn general_parameters(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    ema_fast_period: usize,
    ema_slow_period: usize,
    atr_period: usize,
    grid_multiplier: f64,
) -> HazeResult<GeneralParamsResult> {
    // 输入验证
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(ema_fast_period, close.len())?;
    validate_period(ema_slow_period, close.len())?;
    validate_period(atr_period, close.len())?;

    let len = close.len();

    // 1. 计算 EMA
    let ema_fast_values = ema(close, ema_fast_period)?;
    let ema_slow_values = ema(close, ema_slow_period)?;

    // 2. 计算 ATR
    let atr_values = atr(high, low, close, atr_period)?;

    // 3. 初始化结果
    let mut result = GeneralParamsResult {
        ema_upper: vec![f64::NAN; len],
        ema_middle: ema_slow_values.clone(),
        ema_lower: vec![f64::NAN; len],
        ema_fast: ema_fast_values.clone(),
        ema_slow: ema_slow_values.clone(),
        atr: atr_values.clone(),
        buy_zone_upper: vec![f64::NAN; len],
        buy_zone_lower: vec![f64::NAN; len],
        sell_zone_upper: vec![f64::NAN; len],
        sell_zone_lower: vec![f64::NAN; len],
        long_entry_1: vec![f64::NAN; len],
        long_entry_2: vec![f64::NAN; len],
        long_entry_3: vec![f64::NAN; len],
        short_entry_1: vec![f64::NAN; len],
        short_entry_2: vec![f64::NAN; len],
        short_entry_3: vec![f64::NAN; len],
        breakeven_long: vec![f64::NAN; len],
        breakeven_short: vec![f64::NAN; len],
        trend: vec![0.0; len],
    };

    // 4. 计算各项指标
    let min_period = ema_slow_period.max(atr_period);

    for i in min_period..len {
        let ema_s = ema_slow_values[i];
        let ema_f = ema_fast_values[i];
        let atr_val = if atr_values[i].is_nan() {
            0.0
        } else {
            atr_values[i]
        };
        let adjusted_atr = atr_val * grid_multiplier;

        // EMA 通道
        result.ema_upper[i] = ema_s + adjusted_atr;
        result.ema_lower[i] = ema_s - adjusted_atr;

        // 趋势判断
        if ema_f > ema_s {
            result.trend[i] = 1.0;
        } else if ema_f < ema_s {
            result.trend[i] = -1.0;
        }

        // 买入区域 (下轨附近)
        result.buy_zone_upper[i] = ema_s - 0.5 * adjusted_atr;
        result.buy_zone_lower[i] = ema_s - 1.5 * adjusted_atr;

        // 卖出区域 (上轨附近)
        result.sell_zone_upper[i] = ema_s + 1.5 * adjusted_atr;
        result.sell_zone_lower[i] = ema_s + 0.5 * adjusted_atr;

        // 多头网格入场价
        result.long_entry_1[i] = ema_s - 0.5 * adjusted_atr;
        result.long_entry_2[i] = ema_s - 1.0 * adjusted_atr;
        result.long_entry_3[i] = ema_s - 1.5 * adjusted_atr;

        // 空头网格入场价
        result.short_entry_1[i] = ema_s + 0.5 * adjusted_atr;
        result.short_entry_2[i] = ema_s + 1.0 * adjusted_atr;
        result.short_entry_3[i] = ema_s + 1.5 * adjusted_atr;

        // 解套价格 (假设3档等仓位)
        let long_avg =
            (result.long_entry_1[i] + result.long_entry_2[i] + result.long_entry_3[i]) / 3.0;
        let short_avg =
            (result.short_entry_1[i] + result.short_entry_2[i] + result.short_entry_3[i]) / 3.0;

        result.breakeven_long[i] = long_avg + 0.5 * adjusted_atr;
        result.breakeven_short[i] = short_avg - 0.5 * adjusted_atr;
    }

    Ok(result)
}

/// General Parameters 信号生成
///
/// 基于 EMA 通道和网格参数生成交易信号
///
/// # 返回
/// - (buy_signals, sell_signals, stop_loss, take_profit)
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 数组长度不匹配
/// - `InvalidPeriod`: 周期参数无效
pub fn general_parameters_signals(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    ema_fast_period: usize,
    ema_slow_period: usize,
    atr_period: usize,
    grid_multiplier: f64,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>)> {
    let len = close.len();
    let mut buy_signals = vec![0.0; len];
    let mut sell_signals = vec![0.0; len];
    let mut stop_loss = vec![f64::NAN; len];
    let mut take_profit = vec![f64::NAN; len];

    let params = general_parameters(
        high,
        low,
        close,
        ema_fast_period,
        ema_slow_period,
        atr_period,
        grid_multiplier,
    )?;
    // 复用 params.atr，避免重复计算

    for i in 1..len {
        let atr_val = if params.atr[i].is_nan() {
            0.0
        } else {
            params.atr[i]
        };

        // 买入条件: 价格进入买入区域 + 上涨趋势
        if !params.buy_zone_upper[i].is_nan()
            && !params.buy_zone_lower[i].is_nan()
            && close[i] <= params.buy_zone_upper[i]
            && close[i] >= params.buy_zone_lower[i]
            && params.trend[i] > 0.5
        {
            buy_signals[i] = 1.0;
            stop_loss[i] = params.ema_lower[i] - atr_val;
            take_profit[i] = params.ema_upper[i];
        }

        // 卖出条件: 价格进入卖出区域 + 下跌趋势
        if !params.sell_zone_upper[i].is_nan()
            && !params.sell_zone_lower[i].is_nan()
            && close[i] >= params.sell_zone_lower[i]
            && close[i] <= params.sell_zone_upper[i]
            && params.trend[i] < -0.5
        {
            sell_signals[i] = 1.0;
            stop_loss[i] = params.ema_upper[i] + atr_val;
            take_profit[i] = params.ema_lower[i];
        }
    }

    Ok((buy_signals, sell_signals, stop_loss, take_profit))
}

/// Pivot 买卖信号结果
#[derive(Debug, Clone)]
pub struct PivotSignalResult {
    pub pivot: Vec<f64>,
    pub r1: Vec<f64>,
    pub r2: Vec<f64>,
    pub s1: Vec<f64>,
    pub s2: Vec<f64>,
    pub buy_signals: Vec<f64>,
    pub sell_signals: Vec<f64>,
}

/// Pivot 买卖信号 - 基于枢轴点
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 数组长度不匹配
/// - `InvalidPeriod`: lookback 参数无效
pub fn pivot_buy_sell(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    lookback: usize,
) -> HazeResult<PivotSignalResult> {
    // 输入验证
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(lookback, close.len())?;

    let len = close.len();

    let mut pivot = vec![f64::NAN; len];
    let mut r1 = vec![f64::NAN; len];
    let mut r2 = vec![f64::NAN; len];
    let mut s1 = vec![f64::NAN; len];
    let mut s2 = vec![f64::NAN; len];
    let mut buy_signals = vec![0.0; len];
    let mut sell_signals = vec![0.0; len];

    for i in lookback..len {
        let period_high = high[(i - lookback)..i]
            .iter()
            .cloned()
            .fold(f64::NEG_INFINITY, f64::max);
        let period_low = low[(i - lookback)..i]
            .iter()
            .cloned()
            .fold(f64::INFINITY, f64::min);
        let period_close = close[i - 1];

        let p = (period_high + period_low + period_close) / 3.0;
        pivot[i] = p;

        r1[i] = 2.0 * p - period_low;
        r2[i] = p + (period_high - period_low);
        s1[i] = 2.0 * p - period_high;
        s2[i] = p - (period_high - period_low);

        if i > 0 && close[i - 1] < s1[i] && close[i] > s1[i] {
            buy_signals[i] = 1.0;
        }

        if i > 0 && close[i - 1] > r1[i] && close[i] < r1[i] {
            sell_signals[i] = 1.0;
        }
    }

    Ok(PivotSignalResult {
        pivot,
        r1,
        r2,
        s1,
        s2,
        buy_signals,
        sell_signals,
    })
}

// ============================================================
// 原始 KNN 版本 (保留向后兼容)
// ============================================================

/// AI SuperTrend - 基于 KNN 机器学习的 SuperTrend 增强版
///
/// 结合 KNN 算法优化趋势识别
///
/// # 参数
/// - `high`: 最高价序列
/// - `low`: 最低价序列
/// - `close`: 收盘价序列
/// - `k`: KNN 邻居数（默认 5）
/// - `n`: 数据点数量（默认 100）
/// - `price_trend`: 价格趋势周期（默认 10）
/// - `predict_trend`: 预测趋势周期（默认 10）
/// - `st_length`: SuperTrend 周期（默认 10）
/// - `st_multiplier`: SuperTrend ATR 乘数（默认 3.0）
///
/// # 返回
/// - (supertrend_values, trend_direction) 元组
///   - supertrend_values: SuperTrend 值
///   - trend_direction: 1.0=看涨, -1.0=看跌
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 数组长度不匹配
/// - `InvalidPeriod`: 周期参数无效
pub fn ai_supertrend(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    k: usize,
    n: usize,
    price_trend: usize,
    predict_trend: usize,
    st_length: usize,
    st_multiplier: f64,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    // 输入验证
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(st_length, close.len())?;
    validate_period(price_trend, close.len())?;
    validate_period(predict_trend, close.len())?;
    validate_period(k, close.len())?;
    validate_period(n, close.len())?;

    let len = close.len();
    let required = n
        .checked_add(k)
        .and_then(|sum| sum.checked_add(1))
        .ok_or_else(|| HazeError::InvalidValue {
            index: 0,
            message: "n + k overflow".to_string(),
        })?;
    if len < required {
        return Err(HazeError::InsufficientData {
            required,
            actual: len,
        });
    }

    // 1. 计算传统 SuperTrend
    let (st_values, st_direction, _basic_upper, _basic_lower) =
        supertrend(high, low, close, st_length, st_multiplier)?;

    // 2. 计算价格加权移动平均（用于 KNN 特征）
    let price_wma = wma(close, price_trend)?;

    // 3. 计算 SuperTrend 加权移动平均
    let st_wma = wma_allow_nan(&st_values, predict_trend)?;

    // 4. KNN 预测优化
    let optimized_st = st_values;
    let mut optimized_dir = st_direction.clone();
    let mut distances: Vec<(usize, f64)> = Vec::new();
    if len > n + k {
        for i in n..len {
            // 提取当前窗口的特征
            let current_price_trend = if !price_wma[i].is_nan() {
                price_wma[i]
            } else {
                close[i]
            };
            let current_st_trend = if !st_wma[i].is_nan() {
                st_wma[i]
            } else {
                optimized_st[i]
            };

            // KNN: 找到最相似的 k 个历史点
            distances.clear();
            let window_end = i.saturating_sub(k);
            let mut window_start = k;
            if n > 0 {
                window_start = window_start.max(i.saturating_sub(n));
            }
            if window_end <= window_start {
                continue;
            }
            distances.reserve(window_end - window_start);

            for j in window_start..window_end {
                if !price_wma[j].is_nan() && !st_wma[j].is_nan() {
                    // 计算欧氏距离
                    let price_diff = current_price_trend - price_wma[j];
                    let st_diff = current_st_trend - st_wma[j];
                    let distance = (price_diff * price_diff + st_diff * st_diff).sqrt();

                    distances.push((j, distance));
                }
            }

            if distances.len() >= k {
                // 选择最近的 k 个邻居，带索引的稳定 tie-break
                distances.select_nth_unstable_by(k - 1, |a, b| {
                    let ord = a.1.partial_cmp(&b.1).unwrap_or(Ordering::Equal);
                    if ord == Ordering::Equal {
                        a.0.cmp(&b.0)
                    } else {
                        ord
                    }
                });

                // 计算邻居的平均趋势方向
                let mut trend_sum = 0.0;
                for idx in 0..k {
                    let neighbor_idx = distances[idx].0;
                    if neighbor_idx + 1 < len {
                        trend_sum += st_direction[neighbor_idx + 1];
                    }
                }

                let predicted_direction = trend_sum / k as f64;

                // 如果 KNN 预测与当前方向不一致，进行平滑
                if predicted_direction.abs() > 0.5 {
                    optimized_dir[i] = if predicted_direction > 0.0 { 1.0 } else { -1.0 };
                }
            }
        }
    }

    Ok((optimized_st, optimized_dir))
}

/// AI Momentum Index - 基于 KNN 和 RSI 的动量指标
///
/// 使用 KNN 算法分析价格与 RSI 的关系预测未来走势
///
/// # 参数
/// - `close`: 收盘价序列
/// - `k`: KNN 预测数据量（默认 50）
/// - `trend_length`: 趋势周期（默认 14）
/// - `smooth`: 平滑周期（默认 3）
///
/// # 返回
/// - (prediction, prediction_ma) 元组
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `InvalidPeriod`: 周期参数无效
pub fn ai_momentum_index(
    close: &[f64],
    k: usize,
    trend_length: usize,
    smooth: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    // 输入验证
    validate_not_empty(close, "close")?;
    validate_period(k, close.len())?;
    validate_period(trend_length, close.len())?;
    validate_period(smooth, close.len())?;

    let len = close.len();
    let required = k
        .checked_add(trend_length)
        .and_then(|sum| sum.checked_add(1))
        .ok_or_else(|| HazeError::InvalidValue {
            index: 0,
            message: "k + trend_length overflow".to_string(),
        })?;
    if len < required {
        return Err(HazeError::InsufficientData {
            required,
            actual: len,
        });
    }

    // 1. 计算 RSI
    let rsi = crate::indicators::rsi(close, trend_length)?;

    // 2. 初始化预测值
    let mut prediction = vec![f64::NAN; len];

    // 3. KNN 预测
    let mut distances: Vec<(usize, f64)> = Vec::new();
    if len > k + trend_length {
        for i in (k + trend_length)..len {
            let current_rsi = if !rsi[i].is_nan() { rsi[i] } else { 50.0 };
            let current_price = close[i];

            // 找到相似的历史点
            distances.clear();
            let window_end = i.saturating_sub(trend_length);
            if window_end <= trend_length {
                continue;
            }
            distances.reserve(window_end - trend_length);

            for j in trend_length..window_end {
                if !rsi[j].is_nan() {
                    // 计算特征距离
                    let rsi_delta = current_rsi - rsi[j];
                    let rsi_diff = rsi_delta * rsi_delta;
                    let price_ratio = if is_not_zero(close[j]) {
                        let ratio = (current_price / close[j]) - 1.0;
                        ratio * ratio
                    } else {
                        0.0
                    };

                    let distance = (rsi_diff + price_ratio * 100.0).sqrt();
                    distances.push((j, distance));
                }
            }

            if distances.len() >= k {
                distances.select_nth_unstable_by(k - 1, |a, b| {
                    let ord = a.1.partial_cmp(&b.1).unwrap_or(Ordering::Equal);
                    if ord == Ordering::Equal {
                        a.0.cmp(&b.0)
                    } else {
                        ord
                    }
                });

                // 计算邻居的平均未来动量
                let mut momentum_sum = 0.0;
                let mut valid_count = 0;

                for idx in 0..k {
                    let neighbor_idx = distances[idx].0;
                    if neighbor_idx + 1 < len && !rsi[neighbor_idx + 1].is_nan() {
                        // 动量 = 未来RSI - 当前RSI
                        momentum_sum += rsi[neighbor_idx + 1] - rsi[neighbor_idx];
                        valid_count += 1;
                    }
                }

                if valid_count > 0 {
                    prediction[i] = momentum_sum / valid_count as f64;
                }
            }
        }
    }

    // 4. 计算预测值的移动平均
    let prediction_ma = sma_allow_nan(&prediction, smooth)?;

    Ok((prediction, prediction_ma))
}

/// Dynamic MACD - 动态 MACD 加平均 K 线
///
/// 结合 Heikin-Ashi 的 MACD 变种
///
/// # 参数
/// - `open`: 开盘价
/// - `high`: 最高价
/// - `low`: 最低价
/// - `close`: 收盘价
/// - `fast_length`: 快线周期（默认 12）
/// - `slow_length`: 慢线周期（默认 26）
/// - `signal_smooth`: 信号线平滑（默认 9）
///
/// # 返回
/// - (macd, signal, histogram, ha_open, ha_close) 元组
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 数组长度不匹配
/// - `InvalidPeriod`: 周期参数无效
pub fn dynamic_macd(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    fast_length: usize,
    slow_length: usize,
    signal_smooth: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>)> {
    // 输入验证
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;
    validate_period(fast_length, close.len())?;
    validate_period(slow_length, close.len())?;
    validate_period(signal_smooth, close.len())?;

    let len = close.len();

    // 1. 计算 Heikin-Ashi K线
    let mut ha_open = vec![f64::NAN; len];
    let mut ha_close = vec![f64::NAN; len];

    ha_open[0] = (open[0] + close[0]) / 2.0;
    ha_close[0] = (open[0] + high[0] + low[0] + close[0]) / 4.0;

    for i in 1..len {
        ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2.0;
        ha_close[i] = (open[i] + high[i] + low[i] + close[i]) / 4.0;
    }

    // 2. 使用 HLCC4 作为数据源
    let mut hlcc4 = vec![0.0; len];
    for i in 0..len {
        hlcc4[i] = (high[i] + low[i] + close[i] + close[i]) / 4.0;
    }

    // 3. 计算 MACD
    let (macd, signal, histogram) =
        crate::indicators::macd(&hlcc4, fast_length, slow_length, signal_smooth)?;

    Ok((macd, signal, histogram, ha_open, ha_close))
}

/// ATR2 信号指标 - 基于 ATR 和动量的交易信号
///
/// # 参数
/// - `high`: 最高价
/// - `low`: 最低价
/// - `close`: 收盘价
/// - `volume`: 成交量
/// - `trend_length`: 趋势周期（默认 14）
/// - `confirmation_threshold`: 确认阈值（默认 2.0）
/// - `momentum_window`: 动量窗口（默认 10）
///
/// # 返回
/// - (signals, stop_loss, take_profit) 元组
///   - signals: 1.0=买入, -1.0=卖出, 0.0=无信号
///   - stop_loss: 止损位
///   - take_profit: 止盈位
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `LengthMismatch`: 数组长度不匹配
/// - `InvalidPeriod`: 周期参数无效
pub fn atr2_signals(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    volume: &[f64],
    trend_length: usize,
    confirmation_threshold: f64,
    momentum_window: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    // 输入验证
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[
        (high, "high"),
        (low, "low"),
        (close, "close"),
        (volume, "volume"),
    ])?;
    validate_period(trend_length, close.len())?;
    validate_period(momentum_window, close.len())?;

    let len = close.len();

    // 1. 计算 ATR
    let atr_values = atr(high, low, close, trend_length)?;

    // 2. 计算动量
    let mut momentum = vec![f64::NAN; len];
    for i in momentum_window..len {
        momentum[i] = close[i] - close[i - momentum_window];
    }

    // 3. 计算成交量均线
    let volume_ma = sma(volume, trend_length)?;

    // 4. 生成信号
    let mut signals = vec![0.0; len];
    let mut stop_loss = vec![f64::NAN; len];
    let mut take_profit = vec![f64::NAN; len];

    for i in trend_length..len {
        if !atr_values[i].is_nan() && !momentum[i].is_nan() {
            let normalized_momentum = if is_not_zero(atr_values[i]) {
                momentum[i] / atr_values[i]
            } else {
                0.0
            };

            // 成交量过滤
            let volume_confirmed = if !volume_ma[i].is_nan() {
                volume[i] > volume_ma[i]
            } else {
                true
            };

            // 买入信号
            if normalized_momentum < -confirmation_threshold && volume_confirmed {
                signals[i] = 1.0;
                stop_loss[i] = close[i] - 2.0 * atr_values[i];
                take_profit[i] = close[i] + 3.0 * atr_values[i];
            }
            // 卖出信号
            else if normalized_momentum > confirmation_threshold && volume_confirmed {
                signals[i] = -1.0;
                stop_loss[i] = close[i] + 2.0 * atr_values[i];
                take_profit[i] = close[i] - 3.0 * atr_values[i];
            }
        }
    }

    Ok((signals, stop_loss, take_profit))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ai_supertrend() {
        let high = vec![
            110.0, 112.0, 115.0, 113.0, 116.0, 118.0, 120.0, 119.0, 121.0, 123.0,
        ];
        let low = vec![
            100.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0,
        ];
        let close = vec![
            105.0, 107.0, 110.0, 108.0, 112.0, 115.0, 117.0, 116.0, 118.0, 120.0,
        ];

        let (st, dir) = ai_supertrend(&high, &low, &close, 3, 5, 3, 3, 3, 2.0).unwrap();

        assert_eq!(st.len(), close.len());
        assert_eq!(dir.len(), close.len());
    }

    #[test]
    fn test_ai_momentum_index() {
        // Need sufficient data: momentum_period + roc_period + smoothing_period - 2 = 10 + 14 + 3 - 2 = 25
        let close = vec![
            100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0, 107.0, 109.0, 110.0, 112.0,
            111.0, 113.0, 115.0, 114.0, 116.0, 118.0, 117.0, 119.0, 120.0, 121.0, 122.0, 123.0,
            124.0, 125.0, 126.0, 127.0, 128.0, 129.0,
        ];

        let (pred, pred_ma) = ai_momentum_index(&close, 10, 14, 3).unwrap();

        assert_eq!(pred.len(), close.len());
        assert_eq!(pred_ma.len(), close.len());
    }

    #[test]
    fn test_dynamic_macd() {
        let open = vec![
            100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 105.0, 107.0, 109.0,
        ];
        let high = vec![
            105.0, 107.0, 106.0, 108.0, 110.0, 109.0, 111.0, 110.0, 112.0, 114.0,
        ];
        let low = vec![
            99.0, 101.0, 100.0, 102.0, 104.0, 103.0, 105.0, 104.0, 106.0, 108.0,
        ];
        let close = vec![
            103.0, 105.0, 104.0, 106.0, 108.0, 107.0, 109.0, 108.0, 110.0, 112.0,
        ];

        let (macd, _signal, _hist, ha_o, ha_c) =
            dynamic_macd(&open, &high, &low, &close, 3, 5, 3).unwrap();

        assert_eq!(macd.len(), close.len());
        assert_eq!(ha_o.len(), close.len());
        assert_eq!(ha_c.len(), close.len());
    }

    // ============================================================
    // General Parameters 测试
    // ============================================================

    #[test]
    fn test_general_parameters() {
        // 生成足够的测试数据 (需要满足 max(ema_slow, atr_period) 的要求)
        let len = 60;
        let high: Vec<f64> = (0..len).map(|i| 105.0 + (i as f64) * 0.5).collect();
        let low: Vec<f64> = (0..len).map(|i| 100.0 + (i as f64) * 0.5).collect();
        let close: Vec<f64> = (0..len).map(|i| 103.0 + (i as f64) * 0.5).collect();

        let result = general_parameters(&high, &low, &close, 20, 50, 14, 1.0).unwrap();

        // 验证所有向量长度
        assert_eq!(result.ema_upper.len(), len);
        assert_eq!(result.ema_middle.len(), len);
        assert_eq!(result.ema_lower.len(), len);
        assert_eq!(result.ema_fast.len(), len);
        assert_eq!(result.ema_slow.len(), len);
        assert_eq!(result.buy_zone_upper.len(), len);
        assert_eq!(result.buy_zone_lower.len(), len);
        assert_eq!(result.sell_zone_upper.len(), len);
        assert_eq!(result.sell_zone_lower.len(), len);
        assert_eq!(result.long_entry_1.len(), len);
        assert_eq!(result.long_entry_2.len(), len);
        assert_eq!(result.long_entry_3.len(), len);
        assert_eq!(result.short_entry_1.len(), len);
        assert_eq!(result.short_entry_2.len(), len);
        assert_eq!(result.short_entry_3.len(), len);
        assert_eq!(result.breakeven_long.len(), len);
        assert_eq!(result.breakeven_short.len(), len);
        assert_eq!(result.trend.len(), len);

        // 验证从 min_period 开始有有效值
        let min_period = 50; // max(20, 50, 14)
        assert!(!result.ema_upper[min_period].is_nan());
        assert!(!result.ema_lower[min_period].is_nan());
        assert!(!result.long_entry_1[min_period].is_nan());
        assert!(!result.short_entry_1[min_period].is_nan());

        // 验证通道关系: lower < middle < upper
        for i in min_period..len {
            if !result.ema_lower[i].is_nan() && !result.ema_upper[i].is_nan() {
                assert!(result.ema_lower[i] < result.ema_middle[i]);
                assert!(result.ema_middle[i] < result.ema_upper[i]);
            }
        }

        // 验证网格入场价关系
        for i in min_period..len {
            if !result.long_entry_1[i].is_nan() {
                // 多头入场: entry_1 > entry_2 > entry_3 (越低越深)
                assert!(result.long_entry_1[i] > result.long_entry_2[i]);
                assert!(result.long_entry_2[i] > result.long_entry_3[i]);
            }
            if !result.short_entry_1[i].is_nan() {
                // 空头入场: entry_1 < entry_2 < entry_3 (越高越深)
                assert!(result.short_entry_1[i] < result.short_entry_2[i]);
                assert!(result.short_entry_2[i] < result.short_entry_3[i]);
            }
        }
    }

    #[test]
    fn test_general_parameters_signals() {
        let len = 60;
        let high: Vec<f64> = (0..len).map(|i| 105.0 + (i as f64) * 0.5).collect();
        let low: Vec<f64> = (0..len).map(|i| 100.0 + (i as f64) * 0.5).collect();
        let close: Vec<f64> = (0..len).map(|i| 103.0 + (i as f64) * 0.5).collect();

        let (buy, sell, sl, tp) =
            general_parameters_signals(&high, &low, &close, 20, 50, 14, 1.0).unwrap();

        assert_eq!(buy.len(), len);
        assert_eq!(sell.len(), len);
        assert_eq!(sl.len(), len);
        assert_eq!(tp.len(), len);

        // 验证信号值只能是 0.0 或 1.0
        for i in 0..len {
            assert!(buy[i] == 0.0 || buy[i] == 1.0);
            assert!(sell[i] == 0.0 || sell[i] == 1.0);
        }
    }

    #[test]
    fn test_general_parameters_grid_multiplier() {
        let len = 60;
        let high: Vec<f64> = (0..len).map(|i| 105.0 + (i as f64) * 0.5).collect();
        let low: Vec<f64> = (0..len).map(|i| 100.0 + (i as f64) * 0.5).collect();
        let close: Vec<f64> = (0..len).map(|i| 103.0 + (i as f64) * 0.5).collect();

        // 测试不同的 grid_multiplier
        let result1 = general_parameters(&high, &low, &close, 20, 50, 14, 1.0).unwrap();
        let result2 = general_parameters(&high, &low, &close, 20, 50, 14, 2.0).unwrap();

        let min_period = 50;
        // 更大的 multiplier 应该产生更宽的通道
        let channel_width_1 = result1.ema_upper[min_period] - result1.ema_lower[min_period];
        let channel_width_2 = result2.ema_upper[min_period] - result2.ema_lower[min_period];

        assert!(channel_width_2 > channel_width_1);
    }
}
