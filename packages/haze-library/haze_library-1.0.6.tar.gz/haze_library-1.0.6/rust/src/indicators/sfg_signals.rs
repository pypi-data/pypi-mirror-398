// indicators/sfg_signals.rs - 信号生成器抽象层
#![allow(dead_code)]
//
// 提供统一的信号结构体和信号生成器接口
// 遵循 SOLID 原则: 接口隔离 + 依赖反转

use std::collections::HashMap;

use crate::errors::validation::{validate_not_empty, validate_range};
use crate::errors::{HazeError, HazeResult};

/// SFG 信号结构体
///
/// 统一所有 SFG 指标的信号输出格式
#[derive(Debug, Clone)]
pub struct SFGSignal {
    /// 买入信号: 1.0 = 买入, 0.0 = 无信号
    pub buy_signals: Vec<f64>,
    /// 卖出信号: 1.0 = 卖出, 0.0 = 无信号
    pub sell_signals: Vec<f64>,
    /// 信号强度: 0-1 (多指标一致性评分)
    pub signal_strength: Vec<f64>,
    /// 止损价格
    pub stop_loss: Vec<f64>,
    /// 止盈价格
    pub take_profit: Vec<f64>,
    /// 最大利润追踪
    pub max_profit: Vec<f64>,
    /// 趋势线 (可选)
    pub trend_line: Option<Vec<f64>>,
    /// 上轨 (可选)
    pub upper_band: Option<Vec<f64>>,
    /// 下轨 (可选)
    pub lower_band: Option<Vec<f64>>,
    /// 元数据
    pub metadata: HashMap<String, String>,
}

impl SFGSignal {
    /// 创建空信号
    pub fn new(len: usize) -> Self {
        Self {
            buy_signals: vec![0.0; len],
            sell_signals: vec![0.0; len],
            signal_strength: vec![0.0; len],
            stop_loss: vec![f64::NAN; len],
            take_profit: vec![f64::NAN; len],
            max_profit: vec![f64::NAN; len],
            trend_line: None,
            upper_band: None,
            lower_band: None,
            metadata: HashMap::new(),
        }
    }

    /// 设置买入信号
    pub fn set_buy(&mut self, index: usize, strength: f64) {
        if index < self.buy_signals.len() {
            self.buy_signals[index] = 1.0;
            self.signal_strength[index] = strength.clamp(0.0, 1.0);
        }
    }

    /// 设置卖出信号
    pub fn set_sell(&mut self, index: usize, strength: f64) {
        if index < self.sell_signals.len() {
            self.sell_signals[index] = 1.0;
            self.signal_strength[index] = strength.clamp(0.0, 1.0);
        }
    }

    /// 设置止损止盈
    pub fn set_stops(&mut self, index: usize, stop_loss: f64, take_profit: f64) {
        if index < self.stop_loss.len() {
            self.stop_loss[index] = stop_loss;
            self.take_profit[index] = take_profit;
        }
    }

    /// 添加元数据
    pub fn add_metadata(&mut self, key: &str, value: &str) {
        self.metadata.insert(key.to_string(), value.to_string());
    }

    /// 获取信号数量
    pub fn len(&self) -> usize {
        self.buy_signals.len()
    }

    /// 是否为空
    pub fn is_empty(&self) -> bool {
        self.buy_signals.is_empty()
    }

    /// 统计买入信号数量
    pub fn count_buy_signals(&self) -> usize {
        self.buy_signals.iter().filter(|&&x| x > 0.5).count()
    }

    /// 统计卖出信号数量
    pub fn count_sell_signals(&self) -> usize {
        self.sell_signals.iter().filter(|&&x| x > 0.5).count()
    }
}

fn validate_signal_lengths(signal: &SFGSignal, name: &'static str) -> HazeResult<usize> {
    let len = signal.buy_signals.len();
    if len == 0 {
        return Err(HazeError::EmptyInput { name });
    }
    let fields = [
        ("sell_signals", signal.sell_signals.len()),
        ("signal_strength", signal.signal_strength.len()),
        ("stop_loss", signal.stop_loss.len()),
        ("take_profit", signal.take_profit.len()),
        ("max_profit", signal.max_profit.len()),
    ];
    for (field, field_len) in fields {
        if field_len != len {
            return Err(HazeError::LengthMismatch {
                name1: "buy_signals",
                len1: len,
                name2: field,
                len2: field_len,
            });
        }
    }
    if let Some(ref trend_line) = signal.trend_line {
        if trend_line.len() != len {
            return Err(HazeError::LengthMismatch {
                name1: "buy_signals",
                len1: len,
                name2: "trend_line",
                len2: trend_line.len(),
            });
        }
    }
    if let Some(ref upper_band) = signal.upper_band {
        if upper_band.len() != len {
            return Err(HazeError::LengthMismatch {
                name1: "buy_signals",
                len1: len,
                name2: "upper_band",
                len2: upper_band.len(),
            });
        }
    }
    if let Some(ref lower_band) = signal.lower_band {
        if lower_band.len() != len {
            return Err(HazeError::LengthMismatch {
                name1: "buy_signals",
                len1: len,
                name2: "lower_band",
                len2: lower_band.len(),
            });
        }
    }
    Ok(len)
}

/// 信号生成器 trait
///
/// 所有 SFG 指标实现此接口
pub trait SignalGenerator {
    /// 生成信号
    fn generate(&self, data: &SignalInput) -> SFGSignal;

    /// 获取指标名称
    fn name(&self) -> &str;

    /// 获取最小数据长度要求
    fn min_length(&self) -> usize;
}

/// 信号输入数据
#[derive(Debug, Clone)]
pub struct SignalInput {
    pub open: Vec<f64>,
    pub high: Vec<f64>,
    pub low: Vec<f64>,
    pub close: Vec<f64>,
    pub volume: Vec<f64>,
}

impl SignalInput {
    pub fn new(
        open: Vec<f64>,
        high: Vec<f64>,
        low: Vec<f64>,
        close: Vec<f64>,
        volume: Vec<f64>,
    ) -> Self {
        Self {
            open,
            high,
            low,
            close,
            volume,
        }
    }

    pub fn len(&self) -> usize {
        self.close.len()
    }

    pub fn is_empty(&self) -> bool {
        self.close.is_empty()
    }
}

// ============================================================
// 信号组合器
// ============================================================

/// 组合多个信号源
///
/// # 参数
/// - `signals`: 多个信号源
/// - `weights`: 各信号源权重 (可选,默认等权重)
///
/// # 返回
/// - 组合后的信号
pub fn combine_signals(signals: &[&SFGSignal], weights: Option<&[f64]>) -> HazeResult<SFGSignal> {
    if signals.is_empty() {
        return Err(HazeError::EmptyInput { name: "signals" });
    }

    let len = validate_signal_lengths(signals[0], "signals[0]")?;
    for sig in signals.iter().skip(1) {
        let sig_len = validate_signal_lengths(sig, "signals[n]")?;
        if sig_len != len {
            return Err(HazeError::LengthMismatch {
                name1: "signals[0]",
                len1: len,
                name2: "signals[n]",
                len2: sig_len,
            });
        }
    }

    let n = signals.len();
    let default_weights: Vec<f64> = vec![1.0 / n as f64; n];
    let weights = weights.unwrap_or(&default_weights);
    if weights.len() != n {
        return Err(HazeError::LengthMismatch {
            name1: "signals",
            len1: n,
            name2: "weights",
            len2: weights.len(),
        });
    }
    validate_not_empty(weights, "weights")?;

    let mut combined = SFGSignal::new(len);

    for i in 0..len {
        let mut buy_score = 0.0;
        let mut sell_score = 0.0;
        let mut total_weight = 0.0;

        for (j, sig) in signals.iter().enumerate() {
            let w = weights[j];

            if sig.buy_signals[i] > 0.5 {
                buy_score += w * sig.signal_strength[i];
            }
            if sig.sell_signals[i] > 0.5 {
                sell_score += w * sig.signal_strength[i];
            }
            total_weight += w;
        }

        // 归一化
        if total_weight > 0.0 {
            buy_score /= total_weight;
            sell_score /= total_weight;
        } else {
            return Err(HazeError::InvalidValue {
                index: i,
                message: "total weight is zero".to_string(),
            });
        }

        // 生成组合信号 (阈值 0.5)
        if buy_score > 0.5 {
            combined.set_buy(i, buy_score);
        }
        if sell_score > 0.5 {
            combined.set_sell(i, sell_score);
        }
    }

    Ok(combined)
}

// ============================================================
// 止损止盈计算器
// ============================================================

/// 计算止损止盈
///
/// 基于 ATR 的动态止损止盈
pub fn calculate_stops(
    close: &[f64],
    atr: &[f64],
    signals: &SFGSignal,
    sl_multiplier: f64,
    tp_multiplier: f64,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(close, "close")?;
    validate_range("sl_multiplier", sl_multiplier, 0.0, f64::INFINITY)?;
    validate_range("tp_multiplier", tp_multiplier, 0.0, f64::INFINITY)?;
    let len = close.len();
    if atr.len() != len {
        return Err(HazeError::LengthMismatch {
            name1: "close",
            len1: len,
            name2: "atr",
            len2: atr.len(),
        });
    }
    let sig_len = validate_signal_lengths(signals, "signals")?;
    if sig_len != len {
        return Err(HazeError::LengthMismatch {
            name1: "close",
            len1: len,
            name2: "signals",
            len2: sig_len,
        });
    }
    let mut stop_loss = vec![f64::NAN; len];
    let mut take_profit = vec![f64::NAN; len];

    for i in 0..len {
        let atr_val = atr[i];
        if atr_val.is_infinite() {
            return Err(HazeError::InvalidValue {
                index: i,
                message: "atr contains infinite value".to_string(),
            });
        }
        if atr_val.is_nan() {
            continue;
        }

        // 买入信号
        if signals.buy_signals[i] > 0.5 {
            stop_loss[i] = close[i] - sl_multiplier * atr_val;
            take_profit[i] = close[i] + tp_multiplier * atr_val;
        }
        // 卖出信号
        else if signals.sell_signals[i] > 0.5 {
            stop_loss[i] = close[i] + sl_multiplier * atr_val;
            take_profit[i] = close[i] - tp_multiplier * atr_val;
        }
    }

    Ok((stop_loss, take_profit))
}

/// 计算追踪止损
pub fn trailing_stop(
    close: &[f64],
    atr: &[f64],
    direction: &[f64], // 1.0 = 多, -1.0 = 空
    multiplier: f64,
) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_range("multiplier", multiplier, 0.0, f64::INFINITY)?;
    let len = close.len();
    if atr.len() != len {
        return Err(HazeError::LengthMismatch {
            name1: "close",
            len1: len,
            name2: "atr",
            len2: atr.len(),
        });
    }
    if direction.len() != len {
        return Err(HazeError::LengthMismatch {
            name1: "close",
            len1: len,
            name2: "direction",
            len2: direction.len(),
        });
    }
    let mut trail_stop = vec![f64::NAN; len];

    let mut max_high = close[0];
    let mut min_low = close[0];

    for i in 0..len {
        let atr_val = atr[i];
        if atr_val.is_infinite() {
            return Err(HazeError::InvalidValue {
                index: i,
                message: "atr contains infinite value".to_string(),
            });
        }
        if atr_val.is_nan() {
            continue;
        }

        if direction[i] > 0.5 {
            // 多头追踪
            max_high = max_high.max(close[i]);
            trail_stop[i] = max_high - multiplier * atr_val;
        } else if direction[i] < -0.5 {
            // 空头追踪
            min_low = min_low.min(close[i]);
            trail_stop[i] = min_low + multiplier * atr_val;
        } else {
            // 无持仓,重置
            max_high = close[i];
            min_low = close[i];
        }
    }

    Ok(trail_stop)
}

// ============================================================
// 动量信号结构
// ============================================================

/// 动量信号结果
#[derive(Debug, Clone)]
pub struct MomentumSignals {
    /// 零线交叉买入
    pub zero_cross_buy: Vec<f64>,
    /// 零线交叉卖出
    pub zero_cross_sell: Vec<f64>,
    /// 信号线交叉买入
    pub signal_cross_buy: Vec<f64>,
    /// 信号线交叉卖出
    pub signal_cross_sell: Vec<f64>,
    /// 超买区域
    pub overbought: Vec<f64>,
    /// 超卖区域
    pub oversold: Vec<f64>,
}

impl MomentumSignals {
    pub fn new(len: usize) -> Self {
        Self {
            zero_cross_buy: vec![0.0; len],
            zero_cross_sell: vec![0.0; len],
            signal_cross_buy: vec![0.0; len],
            signal_cross_sell: vec![0.0; len],
            overbought: vec![0.0; len],
            oversold: vec![0.0; len],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sfg_signal_creation() {
        let mut signal = SFGSignal::new(10);

        assert_eq!(signal.len(), 10);
        assert_eq!(signal.count_buy_signals(), 0);
        assert_eq!(signal.count_sell_signals(), 0);

        signal.set_buy(5, 0.8);
        assert_eq!(signal.count_buy_signals(), 1);
        assert_eq!(signal.signal_strength[5], 0.8);
    }

    #[test]
    fn test_combine_signals() {
        let mut sig1 = SFGSignal::new(5);
        let mut sig2 = SFGSignal::new(5);

        sig1.set_buy(2, 0.9);
        sig2.set_buy(2, 0.7);

        let combined = combine_signals(&[&sig1, &sig2], None).unwrap();

        assert_eq!(combined.count_buy_signals(), 1);
        // 平均强度 = (0.9 + 0.7) / 2 = 0.8
        assert!((combined.signal_strength[2] - 0.8).abs() < 0.01);
    }

    #[test]
    fn test_calculate_stops() {
        let close = vec![100.0, 101.0, 102.0, 103.0, 104.0];
        let atr = vec![2.0, 2.0, 2.0, 2.0, 2.0];

        let mut signals = SFGSignal::new(5);
        signals.set_buy(2, 1.0);

        let (sl, tp) = calculate_stops(&close, &atr, &signals, 2.0, 3.0).unwrap();

        // 买入信号: SL = 102 - 2*2 = 98, TP = 102 + 3*2 = 108
        assert_eq!(sl[2], 98.0);
        assert_eq!(tp[2], 108.0);
    }

    #[test]
    fn test_trailing_stop() {
        let close = vec![100.0, 102.0, 105.0, 103.0, 106.0];
        let atr = vec![2.0, 2.0, 2.0, 2.0, 2.0];
        let direction = vec![1.0, 1.0, 1.0, 1.0, 1.0];

        let trail = trailing_stop(&close, &atr, &direction, 2.0).unwrap();

        // 追踪最高点
        // i=0: max=100, trail=100-4=96
        // i=1: max=102, trail=102-4=98
        // i=2: max=105, trail=105-4=101
        // i=3: max=105 (not 103), trail=101
        // i=4: max=106, trail=102
        assert_eq!(trail[0], 96.0);
        assert_eq!(trail[1], 98.0);
        assert_eq!(trail[2], 101.0);
        assert_eq!(trail[3], 101.0);
        assert_eq!(trail[4], 102.0);
    }
}
