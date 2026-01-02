//! Streaming/Online Calculation Module
//!
//! # Overview
//! This module provides incremental (online) indicator calculators that maintain
//! internal state and update with O(1) time complexity per data point. These are
//! essential for real-time trading systems where recalculating entire histories
//! on each tick is impractical.
//!
//! # Design Philosophy
//! - **State Machine Pattern**: Each calculator encapsulates its warmup and running state
//! - **Numerical Stability**: Periodic recalculation prevents floating-point error accumulation
//! - **Zero Allocation**: Updates allocate no memory after initialization
//! - **NaN Safety**: Invalid inputs are handled gracefully without corrupting state
//!
//! # Available Calculators
//!
//! ## Moving Averages
//! - [`OnlineSMA`] - Simple Moving Average with O(1) updates
//! - [`OnlineEMA`] - Exponential Moving Average with warmup handling
//!
//! ## Momentum Indicators
//! - [`OnlineRSI`] - Relative Strength Index with Wilder's smoothing
//! - [`OnlineMACD`] - MACD with signal line and histogram
//! - [`OnlineStochastic`] - Stochastic Oscillator (%K, %D)
//!
//! ## Volatility Indicators
//! - [`OnlineATR`] - Average True Range for OHLC data
//! - [`OnlineBollingerBands`] - Bollinger Bands with configurable std dev
//!
//! ## Trend Indicators
//! - [`OnlineSuperTrend`] - SuperTrend with ATR-based dynamic support/resistance
//! - [`OnlineMLSuperTrend`] - Enhanced SuperTrend with confirmation and confidence
//!
//! ## Adaptive Indicators
//! - [`OnlineAdaptiveRSI`] - RSI with volatility-adaptive period
//! - [`OnlineEnsembleSignal`] - Combined signal from multiple indicators
//!
//! # Examples
//! ```rust
//! use haze_library::utils::streaming::{OnlineSMA, OnlineEMA, OnlineRSI};
//!
//! let prices = vec![100.0, 101.0, 102.0, 103.0, 104.0, 105.0];
//!
//! // Real-time SMA calculation
//! let mut sma = OnlineSMA::new(20).unwrap();
//! for price in prices.iter() {
//!     if let Some(value) = sma.update(*price).unwrap() {
//!         println!("SMA(20): {}", value);
//!     }
//! }
//!
//! // Online RSI for momentum tracking
//! let mut rsi = OnlineRSI::new(14).unwrap();
//! for price in prices.iter() {
//!     if let Some(value) = rsi.update(*price).unwrap() {
//!         if value > 70.0 { println!("Overbought!"); }
//!         if value < 30.0 { println!("Oversold!"); }
//!     }
//! }
//! ```
//!
//! # Performance Characteristics
//! - All update operations are O(1) time complexity
//! - Memory usage is O(period) for window-based calculators
//! - OnlineSMA/OnlineBollingerBands recalculate every 1000 updates for numerical stability
//! - Warmup period returns None until sufficient data is accumulated
//!
//! # Cross-References
//! - [`crate::utils::ma`] - Batch moving average implementations
//! - [`crate::indicators::momentum`] - Batch momentum indicators
//! - [`crate::indicators::volatility`] - Batch volatility indicators

// utils/streaming.rs - 流式/在线计算模块
#![allow(dead_code)]
//
// 提供增量更新的指标计算，适用于实时交易系统
// 遵循 KISS 原则：简单状态机设计

use std::collections::VecDeque;

use crate::errors::{HazeError, HazeResult};
use crate::utils::math::{is_zero, kahan_sum, kahan_sum_iter};

#[inline]
fn kahan_add(sum: &mut f64, compensation: &mut f64, value: f64) {
    let y = value - *compensation;
    let t = *sum + y;
    *compensation = (t - *sum) - y;
    *sum = t;
}

/// 在线 SMA 计算器
///
/// 支持增量更新，O(1) 时间复杂度
/// 使用定期重新计算以防止浮点误差累积
#[derive(Debug, Clone)]
pub struct OnlineSMA {
    period: usize,
    window: VecDeque<f64>,
    sum: f64,
    sum_comp: f64,
    /// 自上次完整重新计算以来的更新次数
    updates_since_recalc: usize,
}

/// 重新计算间隔：每 1000 次更新重新计算一次以重置累积误差
const SMA_RECALC_INTERVAL: usize = 1000;

impl OnlineSMA {
    pub fn new(period: usize) -> HazeResult<Self> {
        if period == 0 {
            return Err(HazeError::InvalidPeriod {
                period,
                data_len: 0,
            });
        }
        Ok(Self {
            period,
            window: VecDeque::with_capacity(period),
            sum: 0.0,
            sum_comp: 0.0,
            updates_since_recalc: 0,
        })
    }

    /// 添加新值并返回当前 SMA
    pub fn update(&mut self, value: f64) -> HazeResult<Option<f64>> {
        if !value.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "value must be finite".to_string(),
            });
        }

        self.window.push_back(value);
        kahan_add(&mut self.sum, &mut self.sum_comp, value);

        if self.window.len() > self.period {
            if let Some(old) = self.window.pop_front() {
                kahan_add(&mut self.sum, &mut self.sum_comp, -old);
            }
            self.updates_since_recalc += 1;

            // 定期完整重新计算以消除累积浮点误差
            if self.updates_since_recalc >= SMA_RECALC_INTERVAL {
                self.recalculate_sum();
            }
        }

        if self.window.len() == self.period {
            Ok(Some(self.sum / self.period as f64))
        } else {
            Ok(None)
        }
    }

    /// 完整重新计算窗口和以消除累积浮点误差
    fn recalculate_sum(&mut self) {
        self.sum = kahan_sum(self.window.make_contiguous());
        self.sum_comp = 0.0;
        self.updates_since_recalc = 0;
    }

    /// 重置状态
    pub fn reset(&mut self) {
        self.window.clear();
        self.sum = 0.0;
        self.sum_comp = 0.0;
        self.updates_since_recalc = 0;
    }

    /// 当前窗口大小
    pub fn len(&self) -> usize {
        self.window.len()
    }

    pub fn is_empty(&self) -> bool {
        self.window.is_empty()
    }

    /// 强制重新计算和以消除累积误差（用于关键计算点）
    pub fn force_recalculate(&mut self) {
        if self.window.len() == self.period {
            self.recalculate_sum();
        }
    }
}

/// 在线 EMA 计算器
///
/// 支持增量更新，O(1) 时间复杂度
#[derive(Debug, Clone)]
pub struct OnlineEMA {
    period: usize,
    alpha: f64,
    current: Option<f64>,
    warmup_count: usize,
    warmup_sum: f64,
    warmup_comp: f64,
}

impl OnlineEMA {
    pub fn new(period: usize) -> HazeResult<Self> {
        if period == 0 {
            return Err(HazeError::InvalidPeriod {
                period,
                data_len: 0,
            });
        }
        Ok(Self {
            period,
            alpha: 2.0 / (period as f64 + 1.0),
            current: None,
            warmup_count: 0,
            warmup_sum: 0.0,
            warmup_comp: 0.0,
        })
    }

    /// 添加新值并返回当前 EMA
    pub fn update(&mut self, value: f64) -> HazeResult<Option<f64>> {
        if !value.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "value must be finite".to_string(),
            });
        }

        match self.current {
            None => {
                self.warmup_count += 1;
                kahan_add(&mut self.warmup_sum, &mut self.warmup_comp, value);
                if self.warmup_count == self.period {
                    self.current = Some(self.warmup_sum / self.period as f64);
                }
                Ok(self.current)
            }
            Some(prev) => {
                let new_ema = self.alpha * value + (1.0 - self.alpha) * prev;
                self.current = Some(new_ema);
                Ok(self.current)
            }
        }
    }

    /// 重置状态
    pub fn reset(&mut self) {
        self.current = None;
        self.warmup_count = 0;
        self.warmup_sum = 0.0;
        self.warmup_comp = 0.0;
    }

    /// 是否完成预热
    pub fn is_ready(&self) -> bool {
        self.current.is_some()
    }
}

/// 在线 RSI 计算器
#[derive(Debug, Clone)]
pub struct OnlineRSI {
    period: usize,
    prev_value: Option<f64>,
    avg_gain: Option<f64>,
    avg_loss: Option<f64>,
    warmup_gains: Vec<f64>,
    warmup_losses: Vec<f64>,
}

impl OnlineRSI {
    pub fn new(period: usize) -> HazeResult<Self> {
        if period == 0 {
            return Err(HazeError::InvalidPeriod {
                period,
                data_len: 0,
            });
        }
        Ok(Self {
            period,
            prev_value: None,
            avg_gain: None,
            avg_loss: None,
            warmup_gains: Vec::with_capacity(period),
            warmup_losses: Vec::with_capacity(period),
        })
    }

    pub fn update(&mut self, value: f64) -> HazeResult<Option<f64>> {
        if !value.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "value must be finite".to_string(),
            });
        }

        let prev = match self.prev_value {
            Some(p) => p,
            None => {
                self.prev_value = Some(value);
                return Ok(None);
            }
        };

        let change = value - prev;
        self.prev_value = Some(value);

        let gain = if change > 0.0 { change } else { 0.0 };
        let loss = if change < 0.0 { -change } else { 0.0 };

        match (self.avg_gain, self.avg_loss) {
            (None, None) => {
                self.warmup_gains.push(gain);
                self.warmup_losses.push(loss);

                if self.warmup_gains.len() == self.period {
                    let avg_g: f64 = kahan_sum(&self.warmup_gains) / self.period as f64;
                    let avg_l: f64 = kahan_sum(&self.warmup_losses) / self.period as f64;
                    self.avg_gain = Some(avg_g);
                    self.avg_loss = Some(avg_l);
                    Ok(Some(Self::calc_rsi(avg_g, avg_l)))
                } else {
                    Ok(None)
                }
            }
            (Some(ag), Some(al)) => {
                let new_avg_gain = (ag * (self.period - 1) as f64 + gain) / self.period as f64;
                let new_avg_loss = (al * (self.period - 1) as f64 + loss) / self.period as f64;
                self.avg_gain = Some(new_avg_gain);
                self.avg_loss = Some(new_avg_loss);
                Ok(Some(Self::calc_rsi(new_avg_gain, new_avg_loss)))
            }
            _ => Ok(None),
        }
    }

    fn calc_rsi(avg_gain: f64, avg_loss: f64) -> f64 {
        if is_zero(avg_loss) {
            if is_zero(avg_gain) {
                0.0
            } else {
                100.0
            }
        } else {
            100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
        }
    }

    pub fn reset(&mut self) {
        self.prev_value = None;
        self.avg_gain = None;
        self.avg_loss = None;
        self.warmup_gains.clear();
        self.warmup_losses.clear();
    }
}

/// 在线 ATR 计算器
#[derive(Debug, Clone)]
pub struct OnlineATR {
    period: usize,
    prev_close: Option<f64>,
    atr: Option<f64>,
    warmup_tr: Vec<f64>,
}

impl OnlineATR {
    pub fn new(period: usize) -> HazeResult<Self> {
        if period == 0 {
            return Err(HazeError::InvalidPeriod {
                period,
                data_len: 0,
            });
        }
        Ok(Self {
            period,
            prev_close: None,
            atr: None,
            warmup_tr: Vec::with_capacity(period),
        })
    }

    /// 更新并返回当前 ATR
    pub fn update(&mut self, high: f64, low: f64, close: f64) -> HazeResult<Option<f64>> {
        if !high.is_finite() || !low.is_finite() || !close.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "ohlc values must be finite".to_string(),
            });
        }

        let tr = match self.prev_close {
            Some(pc) => {
                let hl = high - low;
                let hc = (high - pc).abs();
                let lc = (low - pc).abs();
                hl.max(hc).max(lc)
            }
            None => {
                self.prev_close = Some(close);
                return Ok(self.atr);
            }
        };
        self.prev_close = Some(close);

        match self.atr {
            None => {
                self.warmup_tr.push(tr);
                if self.warmup_tr.len() == self.period {
                    let avg: f64 = kahan_sum(&self.warmup_tr) / self.period as f64;
                    self.atr = Some(avg);
                    self.warmup_tr.clear();
                }
                Ok(self.atr)
            }
            Some(prev_atr) => {
                // RMA 更新
                let new_atr = (prev_atr * (self.period - 1) as f64 + tr) / self.period as f64;
                self.atr = Some(new_atr);
                Ok(self.atr)
            }
        }
    }

    pub fn reset(&mut self) {
        self.prev_close = None;
        self.atr = None;
        self.warmup_tr.clear();
    }

    pub fn is_ready(&self) -> bool {
        self.atr.is_some()
    }
}

/// 在线 MACD 计算器
#[derive(Debug, Clone)]
pub struct OnlineMACD {
    fast_ema: OnlineEMA,
    slow_ema: OnlineEMA,
    signal_ema: OnlineEMA,
}

impl OnlineMACD {
    pub fn new(fast: usize, slow: usize, signal: usize) -> HazeResult<Self> {
        if fast == 0 {
            return Err(HazeError::InvalidPeriod {
                period: fast,
                data_len: 0,
            });
        }
        if slow == 0 {
            return Err(HazeError::InvalidPeriod {
                period: slow,
                data_len: 0,
            });
        }
        if signal == 0 {
            return Err(HazeError::InvalidPeriod {
                period: signal,
                data_len: 0,
            });
        }
        if slow <= fast {
            return Err(HazeError::ParameterOutOfRange {
                name: "slow",
                value: slow as f64,
                min: fast as f64 + 1.0,
                max: f64::INFINITY,
            });
        }
        Ok(Self {
            fast_ema: OnlineEMA::new(fast)?,
            slow_ema: OnlineEMA::new(slow)?,
            signal_ema: OnlineEMA::new(signal)?,
        })
    }

    /// 返回 (MACD, Signal, Histogram)
    pub fn update(&mut self, value: f64) -> HazeResult<Option<(f64, f64, f64)>> {
        let fast = match self.fast_ema.update(value)? {
            Some(v) => v,
            None => return Ok(None),
        };
        let slow = match self.slow_ema.update(value)? {
            Some(v) => v,
            None => return Ok(None),
        };
        let macd = fast - slow;
        let signal = match self.signal_ema.update(macd)? {
            Some(v) => v,
            None => return Ok(None),
        };
        let histogram = macd - signal;
        Ok(Some((macd, signal, histogram)))
    }

    pub fn reset(&mut self) {
        self.fast_ema.reset();
        self.slow_ema.reset();
        self.signal_ema.reset();
    }
}

/// 在线 Bollinger Bands 计算器
///
/// 使用定期重新计算以防止浮点误差累积
#[derive(Debug, Clone)]
pub struct OnlineBollingerBands {
    period: usize,
    std_dev: f64,
    window: VecDeque<f64>,
    sum: f64,
    sum_comp: f64,
    sum_sq: f64,
    sum_sq_comp: f64,
    /// 自上次完整重新计算以来的更新次数
    updates_since_recalc: usize,
}

/// 重新计算间隔：每 1000 次更新重新计算一次以重置累积误差
const BB_RECALC_INTERVAL: usize = 1000;

impl OnlineBollingerBands {
    pub fn new(period: usize, std_dev: f64) -> HazeResult<Self> {
        if period == 0 {
            return Err(HazeError::InvalidPeriod {
                period,
                data_len: 0,
            });
        }
        if !std_dev.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "std_dev must be finite".to_string(),
            });
        }
        Ok(Self {
            period,
            std_dev,
            window: VecDeque::with_capacity(period),
            sum: 0.0,
            sum_comp: 0.0,
            sum_sq: 0.0,
            sum_sq_comp: 0.0,
            updates_since_recalc: 0,
        })
    }

    /// 返回 (Upper, Middle, Lower)
    pub fn update(&mut self, value: f64) -> HazeResult<Option<(f64, f64, f64)>> {
        if !value.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "value must be finite".to_string(),
            });
        }

        self.window.push_back(value);
        kahan_add(&mut self.sum, &mut self.sum_comp, value);
        kahan_add(&mut self.sum_sq, &mut self.sum_sq_comp, value * value);

        if self.window.len() > self.period {
            if let Some(old) = self.window.pop_front() {
                kahan_add(&mut self.sum, &mut self.sum_comp, -old);
                kahan_add(&mut self.sum_sq, &mut self.sum_sq_comp, -(old * old));
            }
            self.updates_since_recalc += 1;

            // 定期完整重新计算以消除累积浮点误差
            if self.updates_since_recalc >= BB_RECALC_INTERVAL {
                self.recalculate_sums();
            }
        }

        if self.window.len() == self.period {
            let mean = self.sum / self.period as f64;
            let variance = self.sum_sq / self.period as f64 - mean * mean;
            let std = variance.max(0.0).sqrt();
            let upper = mean + self.std_dev * std;
            let lower = mean - self.std_dev * std;
            Ok(Some((upper, mean, lower)))
        } else {
            Ok(None)
        }
    }

    /// 完整重新计算窗口和以消除累积浮点误差
    fn recalculate_sums(&mut self) {
        let mut sum = 0.0;
        let mut sum_comp = 0.0;
        let mut sum_sq = 0.0;
        let mut sum_sq_comp = 0.0;
        for &value in &self.window {
            kahan_add(&mut sum, &mut sum_comp, value);
            kahan_add(&mut sum_sq, &mut sum_sq_comp, value * value);
        }
        self.sum = sum;
        self.sum_comp = sum_comp;
        self.sum_sq = sum_sq;
        self.sum_sq_comp = sum_sq_comp;
        self.updates_since_recalc = 0;
    }

    pub fn reset(&mut self) {
        self.window.clear();
        self.sum = 0.0;
        self.sum_comp = 0.0;
        self.sum_sq = 0.0;
        self.sum_sq_comp = 0.0;
        self.updates_since_recalc = 0;
    }

    /// 强制重新计算和以消除累积误差（用于关键计算点）
    pub fn force_recalculate(&mut self) {
        if self.window.len() == self.period {
            self.recalculate_sums();
        }
    }
}

// ==================== 新增流式计算器 ====================

/// 在线 Stochastic 计算器
///
/// 计算 slow %K 和 %D 线，用于识别超买超卖状态
/// - fast %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
/// - slow %K = SMA(fast %K, smooth_k)
/// - %D = SMA(slow %K, d_period)
#[derive(Debug, Clone)]
pub struct OnlineStochastic {
    k_period: usize,
    smooth_k: usize,
    d_period: usize,
    high_window: VecDeque<f64>,
    low_window: VecDeque<f64>,
    close_window: VecDeque<f64>,
    fast_k_values: VecDeque<f64>,
    fast_k_sum: f64,
    fast_k_comp: f64,
    slow_k_values: VecDeque<f64>,
    slow_k_sum: f64,
    slow_k_comp: f64,
}

impl OnlineStochastic {
    pub fn new(k_period: usize, smooth_k: usize, d_period: usize) -> HazeResult<Self> {
        if k_period == 0 {
            return Err(HazeError::InvalidPeriod {
                period: k_period,
                data_len: 0,
            });
        }
        if smooth_k == 0 {
            return Err(HazeError::InvalidPeriod {
                period: smooth_k,
                data_len: 0,
            });
        }
        if d_period == 0 {
            return Err(HazeError::InvalidPeriod {
                period: d_period,
                data_len: 0,
            });
        }
        Ok(Self {
            k_period,
            smooth_k,
            d_period,
            high_window: VecDeque::with_capacity(k_period),
            low_window: VecDeque::with_capacity(k_period),
            close_window: VecDeque::with_capacity(k_period),
            fast_k_values: VecDeque::with_capacity(smooth_k),
            fast_k_sum: 0.0,
            fast_k_comp: 0.0,
            slow_k_values: VecDeque::with_capacity(d_period),
            slow_k_sum: 0.0,
            slow_k_comp: 0.0,
        })
    }

    /// 返回 (%K, %D) 或 None（预热期）
    pub fn update(&mut self, high: f64, low: f64, close: f64) -> HazeResult<Option<(f64, f64)>> {
        if !high.is_finite() || !low.is_finite() || !close.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "ohlc values must be finite".to_string(),
            });
        }

        // 更新滑动窗口
        self.high_window.push_back(high);
        self.low_window.push_back(low);
        self.close_window.push_back(close);

        if self.high_window.len() > self.k_period {
            self.high_window.pop_front();
            self.low_window.pop_front();
            self.close_window.pop_front();
        }

        // 计算 fast %K
        if self.high_window.len() < self.k_period {
            return Ok(None);
        }

        let highest = self
            .high_window
            .iter()
            .copied()
            .fold(f64::NEG_INFINITY, f64::max);
        let lowest = self
            .low_window
            .iter()
            .copied()
            .fold(f64::INFINITY, f64::min);

        let range = highest - lowest;
        let fast_k = if is_zero(range) {
            50.0 // 当范围为0时返回中性值
        } else {
            (close - lowest) / range * 100.0
        };

        // 更新 slow %K 计算
        self.fast_k_values.push_back(fast_k);
        kahan_add(&mut self.fast_k_sum, &mut self.fast_k_comp, fast_k);

        if self.fast_k_values.len() > self.smooth_k {
            if let Some(old_k) = self.fast_k_values.pop_front() {
                kahan_add(&mut self.fast_k_sum, &mut self.fast_k_comp, -old_k);
            }
        }

        if self.fast_k_values.len() < self.smooth_k {
            return Ok(None);
        }

        let slow_k = self.fast_k_sum / self.smooth_k as f64;

        // 更新 %D 计算
        self.slow_k_values.push_back(slow_k);
        kahan_add(&mut self.slow_k_sum, &mut self.slow_k_comp, slow_k);

        if self.slow_k_values.len() > self.d_period {
            if let Some(old_k) = self.slow_k_values.pop_front() {
                kahan_add(&mut self.slow_k_sum, &mut self.slow_k_comp, -old_k);
            }
        }

        if self.slow_k_values.len() == self.d_period {
            let d = self.slow_k_sum / self.d_period as f64;
            Ok(Some((slow_k, d)))
        } else {
            Ok(None)
        }
    }

    pub fn reset(&mut self) {
        self.high_window.clear();
        self.low_window.clear();
        self.close_window.clear();
        self.fast_k_values.clear();
        self.fast_k_sum = 0.0;
        self.fast_k_comp = 0.0;
        self.slow_k_values.clear();
        self.slow_k_sum = 0.0;
        self.slow_k_comp = 0.0;
    }
}

// 引用 OnlineATR 类型

/// 在线 SuperTrend 计算器
///
/// 基于 ATR 的动态支撑/阻力指标，用于趋势跟踪
/// - 上轨 = (High + Low) / 2 + multiplier * ATR
/// - 下轨 = (High + Low) / 2 - multiplier * ATR
/// - 趋势方向由价格与轨道的关系决定
#[derive(Debug, Clone)]
pub struct OnlineSuperTrend {
    atr: OnlineATR,
    multiplier: f64,
    prev_upper: Option<f64>,
    prev_lower: Option<f64>,
    prev_supertrend: Option<f64>,
    trend: i8, // 1 = 上涨, -1 = 下跌, 0 = 未确定
}

impl OnlineSuperTrend {
    pub fn new(period: usize, multiplier: f64) -> HazeResult<Self> {
        if period == 0 {
            return Err(HazeError::InvalidPeriod {
                period,
                data_len: 0,
            });
        }
        if !multiplier.is_finite() || multiplier <= 0.0 {
            return Err(HazeError::ParameterOutOfRange {
                name: "multiplier",
                value: multiplier,
                min: 0.0,
                max: f64::INFINITY,
            });
        }
        Ok(Self {
            atr: OnlineATR::new(period)?,
            multiplier,
            prev_upper: None,
            prev_lower: None,
            prev_supertrend: None,
            trend: 0,
        })
    }

    /// 返回 (supertrend_value, trend_direction) 或 None（预热期）
    /// trend_direction: 1 = 上涨趋势, -1 = 下跌趋势
    pub fn update(&mut self, high: f64, low: f64, close: f64) -> HazeResult<Option<(f64, i8)>> {
        if !high.is_finite() || !low.is_finite() || !close.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "ohlc values must be finite".to_string(),
            });
        }

        let atr_val = match self.atr.update(high, low, close)? {
            Some(v) => v,
            None => return Ok(None),
        };

        let hl2 = (high + low) / 2.0;
        let basic_upper = hl2 + self.multiplier * atr_val;
        let basic_lower = hl2 - self.multiplier * atr_val;

        // 计算最终上下轨
        let final_upper = match self.prev_upper {
            Some(prev_u) if basic_upper < prev_u || close > prev_u => basic_upper,
            Some(prev_u) => prev_u,
            None => basic_upper,
        };

        let final_lower = match self.prev_lower {
            Some(prev_l) if basic_lower > prev_l || close < prev_l => basic_lower,
            Some(prev_l) => prev_l,
            None => basic_lower,
        };

        // 确定趋势方向和 SuperTrend 值
        let (supertrend, new_trend) = match self.prev_supertrend {
            Some(prev_st) => {
                if prev_st == self.prev_upper.unwrap_or(f64::MAX) {
                    if close > final_upper {
                        (final_lower, 1)
                    } else {
                        (final_upper, -1)
                    }
                } else if close < final_lower {
                    (final_upper, -1)
                } else {
                    (final_lower, 1)
                }
            }
            None => {
                // 初始趋势判断
                if close > hl2 {
                    (final_lower, 1)
                } else {
                    (final_upper, -1)
                }
            }
        };

        // 更新状态
        self.prev_upper = Some(final_upper);
        self.prev_lower = Some(final_lower);
        self.prev_supertrend = Some(supertrend);
        self.trend = new_trend;

        Ok(Some((supertrend, new_trend)))
    }

    pub fn reset(&mut self) {
        self.atr.reset();
        self.prev_upper = None;
        self.prev_lower = None;
        self.prev_supertrend = None;
        self.trend = 0;
    }

    pub fn current_trend(&self) -> i8 {
        self.trend
    }
}

/// 在线自适应 RSI 计算器
///
/// 根据市场波动率动态调整 RSI 周期
/// - 高波动时使用较短周期（更敏感）
/// - 低波动时使用较长周期（更稳定）
#[derive(Debug, Clone)]
pub struct OnlineAdaptiveRSI {
    min_period: usize,
    max_period: usize,
    volatility_period: usize,
    prev_value: Option<f64>,
    changes: VecDeque<f64>,
    gains: VecDeque<f64>,
    losses: VecDeque<f64>,
}

impl OnlineAdaptiveRSI {
    pub fn new(min_period: usize, max_period: usize, volatility_period: usize) -> HazeResult<Self> {
        if min_period == 0 {
            return Err(HazeError::InvalidPeriod {
                period: min_period,
                data_len: 0,
            });
        }
        if max_period < min_period {
            return Err(HazeError::ParameterOutOfRange {
                name: "max_period",
                value: max_period as f64,
                min: min_period as f64,
                max: f64::INFINITY,
            });
        }
        if volatility_period == 0 {
            return Err(HazeError::InvalidPeriod {
                period: volatility_period,
                data_len: 0,
            });
        }
        Ok(Self {
            min_period,
            max_period,
            volatility_period,
            prev_value: None,
            changes: VecDeque::with_capacity(volatility_period),
            gains: VecDeque::with_capacity(max_period),
            losses: VecDeque::with_capacity(max_period),
        })
    }

    /// 返回 (adaptive_rsi, effective_period) 或 None（预热期）
    pub fn update(&mut self, value: f64) -> HazeResult<Option<(f64, usize)>> {
        if !value.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "value must be finite".to_string(),
            });
        }

        let prev = match self.prev_value {
            Some(p) => p,
            None => {
                self.prev_value = Some(value);
                return Ok(None);
            }
        };

        let change = value - prev;
        self.prev_value = Some(value);

        // 更新变化窗口（用于波动率计算）
        self.changes.push_back(change.abs());
        if self.changes.len() > self.volatility_period {
            self.changes.pop_front();
        }

        // 更新增益/损失窗口
        let gain = if change > 0.0 { change } else { 0.0 };
        let loss = if change < 0.0 { -change } else { 0.0 };
        self.gains.push_back(gain);
        self.losses.push_back(loss);
        if self.gains.len() > self.max_period {
            self.gains.pop_front();
            self.losses.pop_front();
        }

        // 需要足够数据
        if self.changes.len() < self.volatility_period || self.gains.len() < self.min_period {
            return Ok(None);
        }

        // 计算波动率并确定自适应周期
        let volatility: f64 =
            kahan_sum(self.changes.make_contiguous()) / self.volatility_period as f64;
        let max_change: f64 = self
            .changes
            .iter()
            .copied()
            .fold(f64::NEG_INFINITY, f64::max);

        let volatility_ratio = if is_zero(max_change) {
            0.5
        } else {
            (volatility / max_change).clamp(0.0, 1.0)
        };

        // 高波动 -> 短周期，低波动 -> 长周期
        let period_range = (self.max_period - self.min_period) as f64;
        let adaptive_period =
            self.min_period + ((1.0 - volatility_ratio) * period_range).round() as usize;
        let effective_period = adaptive_period.clamp(self.min_period, self.gains.len());

        // 计算自适应 RSI
        let recent_gains: f64 =
            kahan_sum_iter(self.gains.iter().rev().take(effective_period).copied());
        let recent_losses: f64 =
            kahan_sum_iter(self.losses.iter().rev().take(effective_period).copied());
        let avg_gain = recent_gains / effective_period as f64;
        let avg_loss = recent_losses / effective_period as f64;

        let rsi = if is_zero(avg_loss) {
            if is_zero(avg_gain) {
                0.0
            } else {
                100.0
            }
        } else {
            100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
        };

        Ok(Some((rsi, effective_period)))
    }

    pub fn reset(&mut self) {
        self.prev_value = None;
        self.changes.clear();
        self.gains.clear();
        self.losses.clear();
    }
}

// 引用其他在线计算器类型

/// 在线集成信号计算器
///
/// 综合多个技术指标生成统一交易信号
/// 使用加权投票机制，支持 RSI、MACD、Stochastic、SuperTrend
#[derive(Debug, Clone)]
pub struct OnlineEnsembleSignal {
    rsi: OnlineRSI,
    macd: OnlineMACD,
    stochastic: OnlineStochastic,
    supertrend: OnlineSuperTrend,
    weights: [f64; 4], // RSI, MACD, Stochastic, SuperTrend
    overbought: f64,
    oversold: f64,
}

/// 集成信号结果
#[derive(Debug, Clone, Copy)]
pub struct EnsembleResult {
    /// 综合信号强度: -1.0 (强烈卖出) 到 +1.0 (强烈买入)
    pub signal: f64,
    /// RSI 分量贡献
    pub rsi_contrib: f64,
    /// MACD 分量贡献
    pub macd_contrib: f64,
    /// Stochastic 分量贡献
    pub stoch_contrib: f64,
    /// SuperTrend 分量贡献
    pub trend_contrib: f64,
    /// 信号一致性 (0-1)，越高越可靠
    pub confidence: f64,
}

impl OnlineEnsembleSignal {
    /// 创建集成信号计算器
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        rsi_period: usize,
        macd_fast: usize,
        macd_slow: usize,
        macd_signal: usize,
        stoch_k: usize,
        stoch_smooth: usize,
        stoch_d: usize,
        supertrend_period: usize,
        supertrend_multiplier: f64,
        weights: [f64; 4],
        overbought: f64,
        oversold: f64,
    ) -> HazeResult<Self> {
        let weight_sum: f64 = weights.iter().sum();
        if is_zero(weight_sum) {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "weights sum cannot be zero".to_string(),
            });
        }

        Ok(Self {
            rsi: OnlineRSI::new(rsi_period)?,
            macd: OnlineMACD::new(macd_fast, macd_slow, macd_signal)?,
            stochastic: OnlineStochastic::new(stoch_k, stoch_smooth, stoch_d)?,
            supertrend: OnlineSuperTrend::new(supertrend_period, supertrend_multiplier)?,
            weights,
            overbought,
            oversold,
        })
    }

    /// 使用默认参数创建
    pub fn default_params() -> HazeResult<Self> {
        Self::new(
            14,
            12,
            26,
            9,
            14,
            3,
            3,
            10,
            3.0,
            [1.0, 1.0, 1.0, 1.0],
            70.0,
            30.0,
        )
    }

    /// 更新并返回集成信号
    pub fn update(
        &mut self,
        high: f64,
        low: f64,
        close: f64,
    ) -> HazeResult<Option<EnsembleResult>> {
        if !high.is_finite() || !low.is_finite() || !close.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "ohlc values must be finite".to_string(),
            });
        }

        let rsi_val = self.rsi.update(close)?;
        let macd_val = self.macd.update(close)?;
        let stoch_val = self.stochastic.update(high, low, close)?;
        let trend_val = self.supertrend.update(high, low, close)?;

        let (rsi, macd, stoch, trend) = match (rsi_val, macd_val, stoch_val, trend_val) {
            (Some(r), Some(m), Some(s), Some(t)) => (r, m, s, t),
            _ => return Ok(None),
        };

        // 计算各分量信号 (-1 到 +1)
        let rsi_signal = if rsi > self.overbought {
            -((rsi - self.overbought) / (100.0 - self.overbought)).clamp(0.0, 1.0)
        } else if rsi < self.oversold {
            ((self.oversold - rsi) / self.oversold).clamp(0.0, 1.0)
        } else {
            0.0
        };

        let (macd_line, signal_line, histogram) = macd;
        let macd_signal = if histogram > 0.0 && macd_line > signal_line {
            (histogram / macd_line.abs().max(1.0)).clamp(0.0, 1.0)
        } else if histogram < 0.0 && macd_line < signal_line {
            (histogram / macd_line.abs().max(1.0)).clamp(-1.0, 0.0)
        } else {
            0.0
        };

        let (k, d) = stoch;
        let stoch_signal = if k > self.overbought && d > self.overbought {
            -((k + d - 2.0 * self.overbought) / (200.0 - 2.0 * self.overbought)).clamp(0.0, 1.0)
        } else if k < self.oversold && d < self.oversold {
            ((2.0 * self.oversold - k - d) / (2.0 * self.oversold)).clamp(0.0, 1.0)
        } else {
            0.0
        };

        let (_supertrend_val, trend_dir) = trend;
        let trend_signal = trend_dir as f64;

        // 加权合成
        let weight_sum: f64 = self.weights.iter().sum();
        let signals = [rsi_signal, macd_signal, stoch_signal, trend_signal];
        let weighted_sum: f64 = signals
            .iter()
            .zip(self.weights.iter())
            .map(|(s, w)| s * w)
            .sum();
        let final_signal = weighted_sum / weight_sum;

        // 计算一致性
        let positive_count = signals.iter().filter(|&&s| s > 0.0).count();
        let negative_count = signals.iter().filter(|&&s| s < 0.0).count();
        let max_agreement = positive_count.max(negative_count) as f64;
        let active_signals = signals.iter().filter(|&&s| !is_zero(s)).count() as f64;
        let confidence = if active_signals > 0.0 {
            max_agreement / active_signals
        } else {
            0.0
        };

        Ok(Some(EnsembleResult {
            signal: final_signal,
            rsi_contrib: rsi_signal * self.weights[0] / weight_sum,
            macd_contrib: macd_signal * self.weights[1] / weight_sum,
            stoch_contrib: stoch_signal * self.weights[2] / weight_sum,
            trend_contrib: trend_signal * self.weights[3] / weight_sum,
            confidence,
        }))
    }

    pub fn reset(&mut self) {
        self.rsi.reset();
        self.macd.reset();
        self.stochastic.reset();
        self.supertrend.reset();
    }
}

/// 在线 ML-SuperTrend 计算器
///
/// 增强版 SuperTrend，包含：
/// - 确认K线数要求（减少假信号）
/// - 信号置信度评估
/// - 自适应乘数调整
#[derive(Debug, Clone)]
pub struct OnlineMLSuperTrend {
    base_supertrend: OnlineSuperTrend,
    confirmation_bars: usize,
    pending_signal: Option<(i8, usize)>,
    confirmed_trend: i8,
    volatility_window: VecDeque<f64>,
    volatility_period: usize,
    base_multiplier: f64,
}

/// ML-SuperTrend 结果
#[derive(Debug, Clone, Copy)]
pub struct MLSuperTrendResult {
    pub value: f64,
    pub confirmed_trend: i8,
    pub raw_trend: i8,
    pub confidence: f64,
    pub effective_multiplier: f64,
}

impl OnlineMLSuperTrend {
    pub fn new(
        period: usize,
        base_multiplier: f64,
        confirmation_bars: usize,
        volatility_period: usize,
    ) -> HazeResult<Self> {
        if period == 0 {
            return Err(HazeError::InvalidPeriod {
                period,
                data_len: 0,
            });
        }
        if confirmation_bars == 0 {
            return Err(HazeError::InvalidPeriod {
                period: confirmation_bars,
                data_len: 0,
            });
        }
        if volatility_period == 0 {
            return Err(HazeError::InvalidPeriod {
                period: volatility_period,
                data_len: 0,
            });
        }
        if !base_multiplier.is_finite() || base_multiplier <= 0.0 {
            return Err(HazeError::ParameterOutOfRange {
                name: "base_multiplier",
                value: base_multiplier,
                min: 0.0,
                max: f64::INFINITY,
            });
        }
        Ok(Self {
            base_supertrend: OnlineSuperTrend::new(period, base_multiplier)?,
            confirmation_bars,
            pending_signal: None,
            confirmed_trend: 0,
            volatility_window: VecDeque::with_capacity(volatility_period),
            volatility_period,
            base_multiplier,
        })
    }

    pub fn default_params() -> HazeResult<Self> {
        Self::new(10, 3.0, 2, 20)
    }

    pub fn update(
        &mut self,
        high: f64,
        low: f64,
        close: f64,
    ) -> HazeResult<Option<MLSuperTrendResult>> {
        if !high.is_finite() || !low.is_finite() || !close.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "ohlc values must be finite".to_string(),
            });
        }

        let tr = high - low;
        self.volatility_window.push_back(tr);
        if self.volatility_window.len() > self.volatility_period {
            self.volatility_window.pop_front();
        }

        let (st_value, raw_trend) = match self.base_supertrend.update(high, low, close)? {
            Some(v) => v,
            None => return Ok(None),
        };

        // 计算自适应乘数
        let effective_multiplier = if self.volatility_window.len() >= self.volatility_period {
            let avg_tr: f64 =
                kahan_sum(self.volatility_window.make_contiguous()) / self.volatility_period as f64;
            let max_tr: f64 = self
                .volatility_window
                .iter()
                .copied()
                .fold(f64::NEG_INFINITY, f64::max);

            if is_zero(max_tr) {
                self.base_multiplier
            } else {
                let volatility_ratio = avg_tr / max_tr;
                self.base_multiplier * (0.8 + 0.4 * volatility_ratio)
            }
        } else {
            self.base_multiplier
        };

        // 信号确认逻辑
        match self.pending_signal {
            Some((pending_dir, count)) if pending_dir == raw_trend => {
                let new_count = count + 1;
                if new_count >= self.confirmation_bars {
                    self.confirmed_trend = raw_trend;
                    self.pending_signal = None;
                } else {
                    self.pending_signal = Some((pending_dir, new_count));
                }
            }
            Some(_) => {
                self.pending_signal = Some((raw_trend, 1));
            }
            None => {
                if raw_trend != self.confirmed_trend {
                    self.pending_signal = Some((raw_trend, 1));
                }
            }
        }

        // 计算置信度
        let confirmation_progress = match self.pending_signal {
            Some((_, count)) => count as f64 / self.confirmation_bars as f64,
            None => 1.0,
        };

        let volatility_confidence = if self.volatility_window.len() >= self.volatility_period {
            let avg_tr: f64 =
                kahan_sum(self.volatility_window.make_contiguous()) / self.volatility_period as f64;
            let std_tr = {
                let variance: f64 = self
                    .volatility_window
                    .iter()
                    .map(|&x| (x - avg_tr).powi(2))
                    .sum::<f64>()
                    / self.volatility_period as f64;
                variance.sqrt()
            };
            if is_zero(avg_tr) {
                0.5
            } else {
                (1.0 - (std_tr / avg_tr).min(1.0)).max(0.0)
            }
        } else {
            0.5
        };

        let confidence = confirmation_progress * 0.6 + volatility_confidence * 0.4;

        Ok(Some(MLSuperTrendResult {
            value: st_value,
            confirmed_trend: self.confirmed_trend,
            raw_trend,
            confidence,
            effective_multiplier,
        }))
    }

    pub fn reset(&mut self) {
        self.base_supertrend.reset();
        self.pending_signal = None;
        self.confirmed_trend = 0;
        self.volatility_window.clear();
    }

    pub fn confirmed_trend(&self) -> i8 {
        self.confirmed_trend
    }
}

// ==================== OnlineAISuperTrendML ====================

/// AI SuperTrend ML 增量计算器
///
/// 使用滑动窗口进行线性回归预测趋势偏移，提供 ML 增强的 SuperTrend 信号。
///
/// # 设计说明
/// - 组合使用 OnlineSuperTrend 和 OnlineATR 作为基础指标
/// - 维护 train_window 大小的滑动窗口用于 ML 训练
/// - 每次更新时使用简单线性回归预测趋势偏移
/// - 时间复杂度: O(train_window) per update
///
/// # Example
/// ```rust,ignore
/// use haze_library::utils::streaming::OnlineAISuperTrendML;
///
/// let mut ai_st = OnlineAISuperTrendML::new(10, 3.0, 10, 200).unwrap();
/// for (h, l, c) in bars {
///     if let Some(result) = ai_st.update(h, l, c).unwrap() {
///         if result.buy_signal { println!("BUY at {}", c); }
///     }
/// }
/// ```
#[derive(Debug, Clone)]
pub struct OnlineAISuperTrendML {
    // 基础指标
    base_supertrend: OnlineSuperTrend,
    atr: OnlineATR,

    // ML 训练数据缓冲
    close_buffer: VecDeque<f64>,
    atr_buffer: VecDeque<f64>,
    direction_buffer: VecDeque<i8>,

    // 配置参数
    st_length: usize,
    st_multiplier: f64,
    train_window: usize,
    lookback: usize,

    // 信号状态
    prev_direction: i8,
    prev_close: f64,
    update_count: usize,
}

/// AI SuperTrend ML 结果
#[derive(Debug, Clone, Copy)]
pub struct AISuperTrendMLResult {
    /// SuperTrend 值
    pub supertrend: f64,
    /// 趋势方向: -1=看跌, 0=中性, 1=看涨
    pub direction: i8,
    /// ML 预测的趋势偏移量
    pub trend_offset: f64,
    /// 买入信号 (趋势从下跌转为上涨)
    pub buy_signal: bool,
    /// 卖出信号 (趋势从上涨转为下跌)
    pub sell_signal: bool,
    /// 动态止损价位 (基于 ATR)
    pub stop_loss: f64,
    /// 动态止盈价位 (基于 ATR)
    pub take_profit: f64,
}

impl OnlineAISuperTrendML {
    /// 创建新的 AI SuperTrend ML 计算器
    ///
    /// # Arguments
    /// * `st_length` - SuperTrend ATR 周期 (默认 10)
    /// * `st_multiplier` - ATR 乘数 (默认 3.0)
    /// * `lookback` - ML 特征回溯期 (默认 10)
    /// * `train_window` - ML 训练窗口大小 (默认 200)
    pub fn new(
        st_length: usize,
        st_multiplier: f64,
        lookback: usize,
        train_window: usize,
    ) -> HazeResult<Self> {
        if st_length == 0 {
            return Err(HazeError::InvalidPeriod {
                period: st_length,
                data_len: 0,
            });
        }
        if train_window == 0 || train_window < lookback + 10 {
            return Err(HazeError::InvalidPeriod {
                period: train_window,
                data_len: 0,
            });
        }
        if lookback == 0 {
            return Err(HazeError::InvalidPeriod {
                period: lookback,
                data_len: 0,
            });
        }
        if !st_multiplier.is_finite() || st_multiplier <= 0.0 {
            return Err(HazeError::ParameterOutOfRange {
                name: "st_multiplier",
                value: st_multiplier,
                min: 0.0,
                max: f64::INFINITY,
            });
        }

        Ok(Self {
            base_supertrend: OnlineSuperTrend::new(st_length, st_multiplier)?,
            atr: OnlineATR::new(st_length)?,
            close_buffer: VecDeque::with_capacity(train_window),
            atr_buffer: VecDeque::with_capacity(train_window),
            direction_buffer: VecDeque::with_capacity(train_window),
            st_length,
            st_multiplier,
            train_window,
            lookback,
            prev_direction: 0,
            prev_close: f64::NAN,
            update_count: 0,
        })
    }

    /// 使用默认参数创建
    pub fn default_params() -> HazeResult<Self> {
        Self::new(10, 3.0, 10, 200)
    }

    /// 更新计算器并返回结果
    ///
    /// # Returns
    /// - `None` 如果数据量不足 (预热期)
    /// - `Some(AISuperTrendMLResult)` 包含完整的信号和止损止盈
    pub fn update(
        &mut self,
        high: f64,
        low: f64,
        close: f64,
    ) -> HazeResult<Option<AISuperTrendMLResult>> {
        if !high.is_finite() || !low.is_finite() || !close.is_finite() {
            return Err(HazeError::InvalidValue {
                index: 0,
                message: "OHLC values must be finite".to_string(),
            });
        }

        self.update_count += 1;

        // 更新基础 SuperTrend
        let (st_value, direction) = match self.base_supertrend.update(high, low, close)? {
            Some(v) => v,
            None => return Ok(None),
        };

        // 更新 ATR
        let atr_value = match self.atr.update(high, low, close)? {
            Some(v) => v,
            None => return Ok(None),
        };

        // 维护滑动窗口
        self.close_buffer.push_back(close);
        self.atr_buffer.push_back(atr_value);
        self.direction_buffer.push_back(direction);

        if self.close_buffer.len() > self.train_window {
            self.close_buffer.pop_front();
            self.atr_buffer.pop_front();
            self.direction_buffer.pop_front();
        }

        // 检查是否有足够数据进行 ML 预测
        let is_ready = self.close_buffer.len() >= self.lookback + 10;

        // 计算 ML 趋势偏移 (使用简单线性回归)
        let trend_offset = if is_ready {
            self.compute_trend_offset()
        } else {
            0.0
        };

        // 检测信号变化
        let buy_signal = self.prev_direction <= 0 && direction > 0;
        let sell_signal = self.prev_direction >= 0 && direction < 0;

        // 计算动态止损止盈 (基于 ATR)
        let atr_mult = 2.0;
        let (stop_loss, take_profit) = if direction > 0 {
            // 多头: 止损在下方，止盈在上方
            (
                close - atr_value * atr_mult,
                close + atr_value * atr_mult * 1.5,
            )
        } else if direction < 0 {
            // 空头: 止损在上方，止盈在下方
            (
                close + atr_value * atr_mult,
                close - atr_value * atr_mult * 1.5,
            )
        } else {
            (f64::NAN, f64::NAN)
        };

        // 更新状态
        self.prev_direction = direction;
        self.prev_close = close;

        Ok(Some(AISuperTrendMLResult {
            supertrend: st_value,
            direction,
            trend_offset,
            buy_signal,
            sell_signal,
            stop_loss,
            take_profit,
        }))
    }

    /// 使用简单线性回归计算趋势偏移
    fn compute_trend_offset(&self) -> f64 {
        let n = self.close_buffer.len();
        if n < self.lookback + 2 {
            return 0.0;
        }

        // 使用最近 lookback 个价格变化作为特征
        let closes: Vec<f64> = self.close_buffer.iter().copied().collect();
        let recent = &closes[n - self.lookback..];

        // 计算简单的线性回归斜率作为趋势偏移
        let x_mean = (self.lookback as f64 - 1.0) / 2.0;
        let y_mean: f64 = kahan_sum_iter(recent.iter().copied()) / self.lookback as f64;

        let mut numerator = 0.0;
        let mut denominator = 0.0;

        for (i, &y) in recent.iter().enumerate() {
            let x = i as f64;
            numerator += (x - x_mean) * (y - y_mean);
            denominator += (x - x_mean).powi(2);
        }

        if is_zero(denominator) {
            0.0
        } else {
            numerator / denominator
        }
    }

    /// 重置计算器状态
    pub fn reset(&mut self) {
        self.base_supertrend.reset();
        self.atr.reset();
        self.close_buffer.clear();
        self.atr_buffer.clear();
        self.direction_buffer.clear();
        self.prev_direction = 0;
        self.prev_close = f64::NAN;
        self.update_count = 0;
    }

    /// 检查是否已准备好 (有足够的预热数据)
    pub fn is_ready(&self) -> bool {
        self.close_buffer.len() >= self.lookback + 10
    }

    /// 当前趋势方向
    pub fn direction(&self) -> i8 {
        self.prev_direction
    }

    /// 更新计数
    pub fn update_count(&self) -> usize {
        self.update_count
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_online_sma() {
        let mut sma = OnlineSMA::new(3).unwrap();
        assert_eq!(sma.update(1.0).unwrap(), None);
        assert_eq!(sma.update(2.0).unwrap(), None);
        assert_eq!(sma.update(3.0).unwrap(), Some(2.0));
        assert_eq!(sma.update(4.0).unwrap(), Some(3.0));
        assert_eq!(sma.update(5.0).unwrap(), Some(4.0));
    }

    #[test]
    fn test_online_ema() {
        let mut ema = OnlineEMA::new(3).unwrap();
        assert_eq!(ema.update(1.0).unwrap(), None);
        assert_eq!(ema.update(2.0).unwrap(), None);
        let first = ema.update(3.0).unwrap().unwrap();
        assert!((first - 2.0).abs() < 1e-10);
        assert!(ema.is_ready());
    }

    #[test]
    fn test_online_rsi() {
        let mut rsi = OnlineRSI::new(14).unwrap();
        for i in 0..20 {
            let val = 100.0 + (i as f64);
            rsi.update(val).unwrap();
        }
        // 持续上涨，RSI 应该接近 100
        let result = rsi.update(120.0).unwrap().unwrap();
        assert!(result > 90.0);
    }

    #[test]
    fn test_online_atr() {
        let mut atr = OnlineATR::new(3).unwrap();
        assert!(atr.update(102.0, 98.0, 100.0).unwrap().is_none());
        assert!(atr.update(103.0, 99.0, 101.0).unwrap().is_none());
        assert!(atr.update(104.0, 100.0, 102.0).unwrap().is_none());
        let result = atr.update(105.0, 101.0, 103.0).unwrap();
        assert!(result.is_some());
        assert!(atr.is_ready());
    }

    #[test]
    fn test_online_macd() {
        let mut macd = OnlineMACD::new(12, 26, 9).unwrap();
        // MACD 需要 slow_period (26) + signal_period (9) = 35+ 个数据点
        for i in 0..50 {
            let val = 100.0 + (i as f64) * 0.5;
            macd.update(val).unwrap();
        }
        let result = macd.update(125.0).unwrap();
        assert!(result.is_some());
    }

    #[test]
    fn test_online_bollinger() {
        let mut bb = OnlineBollingerBands::new(20, 2.0).unwrap();
        for i in 0..25 {
            let val = 100.0 + ((i % 5) as f64);
            bb.update(val).unwrap();
        }
        let (upper, mid, lower) = bb.update(102.0).unwrap().unwrap();
        assert!(upper > mid);
        assert!(mid > lower);
    }
}

// ==================== 浮点误差校准测试 ====================

#[cfg(test)]
mod floating_point_error_tests {
    use super::*;

    /// 测试 OnlineSMA 在大量更新后的数值精度
    #[test]
    fn test_online_sma_large_update_precision() {
        const N: usize = 100_000;
        const PERIOD: usize = 20;

        let mut sma = OnlineSMA::new(PERIOD).unwrap();

        // 收集所有值以便验证
        let values: Vec<f64> = (0..N)
            .map(|i| 1000.0 + (i as f64) * 0.001 + 0.0001 * ((i * 7) % 11) as f64)
            .collect();

        let mut last_result = None;
        for &val in &values {
            last_result = sma.update(val).unwrap();
        }

        // 计算期望的精确值
        let expected: f64 = values[N - PERIOD..N].iter().sum::<f64>() / PERIOD as f64;
        let actual = last_result.unwrap();

        let relative_error = (actual - expected).abs() / expected.abs();
        assert!(
            relative_error < 1e-10,
            "OnlineSMA 精度不足: expected={expected}, actual={actual}, relative_error={relative_error}",
        );
    }

    /// 测试 OnlineSMA 强制重新计算功能
    #[test]
    fn test_online_sma_force_recalculate() {
        const PERIOD: usize = 5;

        let mut sma = OnlineSMA::new(PERIOD).unwrap();

        // 添加一些值
        for i in 0..PERIOD {
            sma.update(i as f64 + 0.1).unwrap();
        }

        // 强制重新计算
        sma.force_recalculate();

        // 添加更多值并检查
        let result = sma.update(10.0).unwrap().unwrap();
        let expected = (1.1 + 2.1 + 3.1 + 4.1 + 10.0) / 5.0;
        assert!((result - expected).abs() < 1e-10);
    }

    /// 测试 OnlineBollingerBands 在大量更新后的数值精度
    #[test]
    fn test_online_bollinger_large_update_precision() {
        const N: usize = 100_000;
        const PERIOD: usize = 20;

        let mut bb = OnlineBollingerBands::new(PERIOD, 2.0).unwrap();

        // 收集所有值以便验证
        let values: Vec<f64> = (0..N).map(|i| 100.0 + (i as f64) * 0.001).collect();

        let mut last_result = None;
        for &val in &values {
            last_result = bb.update(val).unwrap();
        }

        let (upper, mid, lower) = last_result.unwrap();

        // 计算期望的精确均值
        let expected_mean: f64 = values[N - PERIOD..N].iter().sum::<f64>() / PERIOD as f64;
        let relative_error = (mid - expected_mean).abs() / expected_mean.abs();

        assert!(
            relative_error < 1e-10,
            "OnlineBollingerBands 均值精度不足: expected={expected_mean}, actual={mid}, relative_error={relative_error}",
        );

        // 验证布林带结构正确
        assert!(upper > mid, "上轨应大于中轨");
        assert!(mid > lower, "中轨应大于下轨");
    }

    /// 测试 OnlineBollingerBands 强制重新计算功能
    #[test]
    fn test_online_bollinger_force_recalculate() {
        const PERIOD: usize = 5;

        let mut bb = OnlineBollingerBands::new(PERIOD, 2.0).unwrap();

        // 添加一些值
        for i in 0..PERIOD {
            bb.update(100.0 + i as f64).unwrap();
        }

        // 强制重新计算
        bb.force_recalculate();

        // 添加更多值并检查结构
        let (upper, mid, lower) = bb.update(110.0).unwrap().unwrap();
        assert!(upper > mid);
        assert!(mid > lower);
    }

    /// 对比在线计算与批量计算的一致性
    #[test]
    fn test_online_vs_batch_consistency() {
        use crate::utils::ma::sma;

        const N: usize = 10_000;
        const PERIOD: usize = 20;

        let values: Vec<f64> = (0..N).map(|i| 50.0 + (i as f64).sin() * 10.0).collect();

        // 批量计算
        let batch_result = sma(&values, PERIOD).unwrap();

        // 在线计算
        let mut online_sma = OnlineSMA::new(PERIOD).unwrap();
        let mut online_results = Vec::with_capacity(N);
        for &val in &values {
            online_results.push(online_sma.update(val).unwrap());
        }

        // 比较有效结果
        for i in (PERIOD - 1)..N {
            let batch_val = batch_result[i];
            let online_val = online_results[i].unwrap();

            let diff = (batch_val - online_val).abs();
            assert!(
                diff < 1e-10,
                "索引 {i} 处在线与批量结果不一致: batch={batch_val}, online={online_val}, diff={diff}",
            );
        }
    }
}

// ==================== 边界条件测试 ====================

#[cfg(test)]
mod boundary_tests {
    use super::*;

    // ==================== OnlineSMA 边界测试 ====================

    #[test]
    fn test_online_sma_period_one() {
        let mut sma = OnlineSMA::new(1).unwrap();
        // Period=1 means immediate output
        assert_eq!(sma.update(5.0).unwrap(), Some(5.0));
        assert_eq!(sma.update(10.0).unwrap(), Some(10.0));
        assert_eq!(sma.update(3.0).unwrap(), Some(3.0));
    }

    #[test]
    fn test_online_sma_nan_input() {
        let mut sma = OnlineSMA::new(3).unwrap();
        sma.update(1.0).unwrap();
        sma.update(2.0).unwrap();
        // NaN input should error and not corrupt state
        assert!(sma.update(f64::NAN).is_err());
        // Normal value should still work
        assert_eq!(sma.update(3.0).unwrap(), Some(2.0)); // (1+2+3)/3
    }

    #[test]
    fn test_online_sma_reset() {
        let mut sma = OnlineSMA::new(3).unwrap();
        sma.update(1.0).unwrap();
        sma.update(2.0).unwrap();
        sma.update(3.0).unwrap();
        assert_eq!(sma.len(), 3);

        sma.reset();
        assert!(sma.is_empty());
        assert_eq!(sma.len(), 0);

        // After reset, should behave like new
        assert_eq!(sma.update(10.0).unwrap(), None);
        assert_eq!(sma.update(20.0).unwrap(), None);
        assert_eq!(sma.update(30.0).unwrap(), Some(20.0));
    }

    #[test]
    fn test_online_sma_len_and_is_empty() {
        let mut sma = OnlineSMA::new(5).unwrap();
        assert!(sma.is_empty());
        assert_eq!(sma.len(), 0);

        sma.update(1.0).unwrap();
        assert!(!sma.is_empty());
        assert_eq!(sma.len(), 1);

        sma.update(2.0).unwrap();
        sma.update(3.0).unwrap();
        assert_eq!(sma.len(), 3);

        // After warmup complete
        sma.update(4.0).unwrap();
        sma.update(5.0).unwrap();
        assert_eq!(sma.len(), 5);

        // After window slides
        sma.update(6.0).unwrap();
        assert_eq!(sma.len(), 5); // Still 5 (window size)
    }

    #[test]
    fn test_online_sma_constant_values() {
        let mut sma = OnlineSMA::new(5).unwrap();
        for _ in 0..10 {
            let result = sma.update(100.0).unwrap();
            if let Some(val) = result {
                assert!((val - 100.0).abs() < 1e-10);
            }
        }
    }

    #[test]
    fn test_online_sma_force_recalculate_before_ready() {
        let mut sma = OnlineSMA::new(5).unwrap();
        sma.update(1.0).unwrap();
        sma.update(2.0).unwrap();
        // Force recalculate when not yet ready - should be safe
        sma.force_recalculate();
        sma.update(3.0).unwrap();
        sma.update(4.0).unwrap();
        assert_eq!(sma.update(5.0).unwrap(), Some(3.0)); // (1+2+3+4+5)/5
    }

    #[test]
    fn test_online_sma_large_values() {
        let mut sma = OnlineSMA::new(3).unwrap();
        sma.update(1e15).unwrap();
        sma.update(2e15).unwrap();
        let result = sma.update(3e15).unwrap().unwrap();
        assert!((result - 2e15).abs() < 1e5);
    }

    #[test]
    fn test_online_sma_small_values() {
        let mut sma = OnlineSMA::new(3).unwrap();
        sma.update(1e-15).unwrap();
        sma.update(2e-15).unwrap();
        let result = sma.update(3e-15).unwrap().unwrap();
        assert!((result - 2e-15).abs() < 1e-25);
    }

    // ==================== OnlineEMA 边界测试 ====================

    #[test]
    fn test_online_ema_period_one() {
        let mut ema = OnlineEMA::new(1).unwrap();
        // Period=1 means alpha=1, so EMA = latest value
        assert_eq!(ema.update(5.0).unwrap(), Some(5.0));
        assert_eq!(ema.update(10.0).unwrap(), Some(10.0));
        assert_eq!(ema.update(3.0).unwrap(), Some(3.0));
    }

    #[test]
    fn test_online_ema_nan_input_warmup() {
        let mut ema = OnlineEMA::new(3).unwrap();
        ema.update(1.0).unwrap();
        ema.update(2.0).unwrap();
        // NaN during warmup should error
        assert!(ema.update(f64::NAN).is_err());
    }

    #[test]
    fn test_online_ema_nan_input_ready() {
        let mut ema = OnlineEMA::new(3).unwrap();
        ema.update(1.0).unwrap();
        ema.update(2.0).unwrap();
        ema.update(3.0).unwrap();
        let current = ema.current;

        // NaN input after ready should error and leave state unchanged
        assert!(ema.update(f64::NAN).is_err());
        assert_eq!(ema.current, current);
    }

    #[test]
    fn test_online_ema_reset() {
        let mut ema = OnlineEMA::new(3).unwrap();
        ema.update(1.0).unwrap();
        ema.update(2.0).unwrap();
        ema.update(3.0).unwrap();
        assert!(ema.is_ready());

        ema.reset();
        assert!(!ema.is_ready());

        // After reset, should behave like new
        assert_eq!(ema.update(10.0).unwrap(), None);
        assert_eq!(ema.update(20.0).unwrap(), None);
        let result = ema.update(30.0).unwrap().unwrap();
        assert!((result - 20.0).abs() < 1e-10); // Initial EMA = SMA of warmup
    }

    #[test]
    fn test_online_ema_is_ready() {
        let mut ema = OnlineEMA::new(5).unwrap();
        assert!(!ema.is_ready());

        for i in 1..5 {
            ema.update(i as f64).unwrap();
            assert!(!ema.is_ready());
        }

        ema.update(5.0).unwrap();
        assert!(ema.is_ready());
    }

    #[test]
    fn test_online_ema_constant_values() {
        let mut ema = OnlineEMA::new(5).unwrap();
        for _ in 0..20 {
            let result = ema.update(100.0).unwrap();
            if let Some(val) = result {
                assert!((val - 100.0).abs() < 1e-10);
            }
        }
    }

    #[test]
    fn test_online_ema_alpha_calculation() {
        // For period=10, alpha = 2/(10+1) = 0.1818...
        let ema = OnlineEMA::new(10).unwrap();
        let expected_alpha = 2.0 / 11.0;
        assert!((ema.alpha - expected_alpha).abs() < 1e-10);
    }

    // ==================== OnlineRSI 边界测试 ====================

    #[test]
    fn test_online_rsi_all_gains() {
        let mut rsi = OnlineRSI::new(5).unwrap();
        // First value establishes baseline
        rsi.update(100.0).unwrap();
        // All subsequent values are gains
        for i in 1..10 {
            rsi.update(100.0 + i as f64).unwrap();
        }
        let result = rsi.update(115.0).unwrap().unwrap();
        assert!((result - 100.0).abs() < 1e-10); // All gains -> RSI = 100
    }

    #[test]
    fn test_online_rsi_all_losses() {
        let mut rsi = OnlineRSI::new(5).unwrap();
        // First value establishes baseline
        rsi.update(100.0).unwrap();
        // All subsequent values are losses
        for i in 1..10 {
            rsi.update(100.0 - i as f64).unwrap();
        }
        let result = rsi.update(85.0).unwrap().unwrap();
        assert!(result < 1.0); // All losses -> RSI ≈ 0
    }

    #[test]
    fn test_online_rsi_nan_input() {
        let mut rsi = OnlineRSI::new(5).unwrap();
        for i in 0..10 {
            rsi.update(100.0 + (i as f64)).unwrap();
        }
        // NaN input should error
        assert!(rsi.update(f64::NAN).is_err());
        // Normal update should still work
        assert!(rsi.update(110.0).unwrap().is_some());
    }

    #[test]
    fn test_online_rsi_reset() {
        let mut rsi = OnlineRSI::new(5).unwrap();
        for i in 0..10 {
            rsi.update(100.0 + (i as f64)).unwrap();
        }
        assert!(rsi.update(110.0).unwrap().is_some());

        rsi.reset();

        // After reset, need warmup again
        assert!(rsi.update(100.0).unwrap().is_none());
        assert!(rsi.update(101.0).unwrap().is_none());
    }

    #[test]
    fn test_online_rsi_flat_market() {
        let mut rsi = OnlineRSI::new(5).unwrap();
        rsi.update(100.0).unwrap();
        // Flat market - no change
        for _ in 0..10 {
            rsi.update(100.0).unwrap();
        }
        // RSI should be 0 (avg_gain == avg_loss == 0)
        let result = rsi.update(100.0).unwrap().unwrap();
        assert!((result - 0.0).abs() < 1e-10);
    }

    #[test]
    fn test_online_rsi_oscillating() {
        let mut rsi = OnlineRSI::new(5).unwrap();
        rsi.update(100.0).unwrap();
        // Oscillating market
        for i in 0..20 {
            if i % 2 == 0 {
                rsi.update(101.0).unwrap();
            } else {
                rsi.update(99.0).unwrap();
            }
        }
        let result = rsi.update(100.0).unwrap().unwrap();
        // Oscillating should give RSI around 50
        assert!(result > 30.0 && result < 70.0);
    }

    // ==================== OnlineATR 边界测试 ====================

    #[test]
    fn test_online_atr_nan_input() {
        let mut atr = OnlineATR::new(3).unwrap();
        atr.update(102.0, 98.0, 100.0).unwrap();
        atr.update(103.0, 99.0, 101.0).unwrap();
        atr.update(104.0, 100.0, 102.0).unwrap();
        atr.update(105.0, 101.0, 103.0).unwrap();

        // NaN input should error
        assert!(atr.update(f64::NAN, 101.0, 103.0).is_err());
        // Test with NaN in different positions
        assert!(atr.update(105.0, f64::NAN, 103.0).is_err());
    }

    #[test]
    fn test_online_atr_reset() {
        let mut atr = OnlineATR::new(3).unwrap();
        atr.update(102.0, 98.0, 100.0).unwrap();
        atr.update(103.0, 99.0, 101.0).unwrap();
        atr.update(104.0, 100.0, 102.0).unwrap();
        atr.update(105.0, 101.0, 103.0).unwrap();
        assert!(atr.is_ready());

        atr.reset();
        assert!(!atr.is_ready());

        // After reset, need warmup again
        assert!(atr.update(102.0, 98.0, 100.0).unwrap().is_none());
    }

    #[test]
    fn test_online_atr_is_ready() {
        let mut atr = OnlineATR::new(3).unwrap();
        assert!(!atr.is_ready());

        atr.update(102.0, 98.0, 100.0).unwrap();
        assert!(!atr.is_ready());

        atr.update(103.0, 99.0, 101.0).unwrap();
        assert!(!atr.is_ready());

        atr.update(104.0, 100.0, 102.0).unwrap();
        assert!(!atr.is_ready());

        atr.update(105.0, 101.0, 103.0).unwrap();
        assert!(atr.is_ready());
    }

    #[test]
    fn test_online_atr_first_tr_calculation() {
        let mut atr = OnlineATR::new(1).unwrap();
        // First bar: TR = high - low (no previous close)
        assert!(atr.update(105.0, 95.0, 100.0).unwrap().is_none());
        // Period=1, first ATR uses TR from the second bar
        let result = atr.update(110.0, 100.0, 108.0).unwrap().unwrap();
        assert!((result - 10.0).abs() < 1e-10); // 110-100=10
    }

    #[test]
    fn test_online_atr_gap_up() {
        let mut atr = OnlineATR::new(2).unwrap();
        atr.update(102.0, 98.0, 100.0).unwrap();
        // Gap up: close was 100, now low is 105
        atr.update(110.0, 105.0, 108.0).unwrap();
        let result = atr.update(112.0, 107.0, 111.0).unwrap();
        assert!(result.is_some());
    }

    #[test]
    fn test_online_atr_gap_down() {
        let mut atr = OnlineATR::new(2).unwrap();
        atr.update(102.0, 98.0, 100.0).unwrap();
        // Gap down: close was 100, now high is 95
        atr.update(95.0, 90.0, 92.0).unwrap();
        let result = atr.update(96.0, 91.0, 94.0).unwrap();
        assert!(result.is_some());
    }

    // ==================== OnlineMACD 边界测试 ====================

    #[test]
    fn test_online_macd_reset() {
        let mut macd = OnlineMACD::new(12, 26, 9).unwrap();
        for i in 0..50 {
            macd.update(100.0 + (i as f64) * 0.5).unwrap();
        }
        assert!(macd.update(125.0).unwrap().is_some());

        macd.reset();

        // After reset, need full warmup again
        for _ in 0..35 {
            assert!(macd.update(100.0).unwrap().is_none());
        }
    }

    #[test]
    fn test_online_macd_small_periods() {
        let mut macd = OnlineMACD::new(2, 3, 2).unwrap();
        // With small periods, should be ready faster
        macd.update(100.0).unwrap();
        macd.update(101.0).unwrap();
        macd.update(102.0).unwrap();
        // After 3 values: fast EMA ready (period=2 needs 2)
        // slow EMA ready (period=3 needs 3), signal needs 2 more
        macd.update(103.0).unwrap();
        let result = macd.update(104.0).unwrap();
        assert!(result.is_some());
    }

    #[test]
    fn test_online_macd_trending_market() {
        let mut macd = OnlineMACD::new(12, 26, 9).unwrap();
        // Strong uptrend
        for i in 0..60 {
            macd.update(100.0 + (i as f64) * 2.0).unwrap();
        }
        let (macd_line, _signal, _histogram) = macd.update(220.0).unwrap().unwrap();
        // In uptrend: fast EMA > slow EMA -> positive MACD
        assert!(macd_line > 0.0);
    }

    #[test]
    fn test_online_macd_downtrend() {
        let mut macd = OnlineMACD::new(12, 26, 9).unwrap();
        // Strong downtrend
        for i in 0..60 {
            macd.update(200.0 - (i as f64) * 2.0).unwrap();
        }
        let (macd_line, _signal, _histogram) = macd.update(80.0).unwrap().unwrap();
        // In downtrend: fast EMA < slow EMA -> negative MACD
        assert!(macd_line < 0.0);
    }

    // ==================== OnlineBollingerBands 边界测试 ====================

    #[test]
    fn test_online_bollinger_nan_input() {
        let mut bb = OnlineBollingerBands::new(5, 2.0).unwrap();
        for i in 0..5 {
            bb.update(100.0 + (i as f64)).unwrap();
        }

        // NaN input should error
        assert!(bb.update(f64::NAN).is_err());

        // Normal update should still work
        assert!(bb.update(105.0).unwrap().is_some());
    }

    #[test]
    fn test_online_bollinger_reset() {
        let mut bb = OnlineBollingerBands::new(5, 2.0).unwrap();
        for i in 0..10 {
            bb.update(100.0 + (i as f64)).unwrap();
        }

        bb.reset();
        assert!(bb.window.is_empty());

        // After reset, need warmup again
        for _ in 0..4 {
            assert!(bb.update(100.0).unwrap().is_none());
        }
        assert!(bb.update(100.0).unwrap().is_some());
    }

    #[test]
    fn test_online_bollinger_constant_values() {
        let mut bb = OnlineBollingerBands::new(5, 2.0).unwrap();
        for _ in 0..10 {
            bb.update(100.0).unwrap();
        }
        let (upper, mid, lower) = bb.update(100.0).unwrap().unwrap();
        // Constant values -> zero std dev
        assert!((mid - 100.0).abs() < 1e-10);
        assert!((upper - 100.0).abs() < 1e-10);
        assert!((lower - 100.0).abs() < 1e-10);
    }

    #[test]
    fn test_online_bollinger_different_std_devs() {
        let mut bb1 = OnlineBollingerBands::new(5, 1.0).unwrap();
        let mut bb2 = OnlineBollingerBands::new(5, 2.0).unwrap();
        let mut bb3 = OnlineBollingerBands::new(5, 3.0).unwrap();

        let values = vec![100.0, 102.0, 98.0, 101.0, 99.0, 103.0];
        for &val in &values {
            bb1.update(val).unwrap();
            bb2.update(val).unwrap();
            bb3.update(val).unwrap();
        }

        let (upper1, mid1, lower1) = bb1.update(100.0).unwrap().unwrap();
        let (upper2, mid2, lower2) = bb2.update(100.0).unwrap().unwrap();
        let (upper3, mid3, lower3) = bb3.update(100.0).unwrap().unwrap();

        // All should have same middle
        assert!((mid1 - mid2).abs() < 1e-10);
        assert!((mid2 - mid3).abs() < 1e-10);

        // Wider bands for higher std_dev
        assert!(upper3 > upper2);
        assert!(upper2 > upper1);
        assert!(lower3 < lower2);
        assert!(lower2 < lower1);
    }

    #[test]
    fn test_online_bollinger_period_one() {
        let mut bb = OnlineBollingerBands::new(1, 2.0).unwrap();
        // Period=1 means single value, std=0
        let (upper, mid, lower) = bb.update(100.0).unwrap().unwrap();
        assert!((mid - 100.0).abs() < 1e-10);
        assert!((upper - 100.0).abs() < 1e-10);
        assert!((lower - 100.0).abs() < 1e-10);
    }

    #[test]
    fn test_online_bollinger_volatile_market() {
        let mut bb = OnlineBollingerBands::new(5, 2.0).unwrap();
        // Highly volatile data
        let values = vec![100.0, 120.0, 80.0, 130.0, 70.0, 110.0];
        for &val in &values {
            bb.update(val).unwrap();
        }
        let (upper, _mid, lower) = bb.update(100.0).unwrap().unwrap();
        // High volatility should give wide bands
        let band_width = upper - lower;
        assert!(band_width > 40.0); // Should be quite wide
    }

    // ==================== 集成测试 ====================

    #[test]
    fn test_all_calculators_with_infinity() {
        let mut sma = OnlineSMA::new(3).unwrap();
        let mut ema = OnlineEMA::new(3).unwrap();

        // Test with infinity
        sma.update(1.0).unwrap();
        sma.update(2.0).unwrap();
        assert!(sma.update(f64::INFINITY).is_err());

        ema.update(1.0).unwrap();
        ema.update(2.0).unwrap();
        ema.update(3.0).unwrap();
        assert!(ema.update(f64::INFINITY).is_err());
    }

    #[test]
    fn test_all_calculators_negative_values() {
        let mut sma = OnlineSMA::new(3).unwrap();
        let mut ema = OnlineEMA::new(3).unwrap();
        let mut rsi = OnlineRSI::new(3).unwrap();
        let mut bb = OnlineBollingerBands::new(3, 2.0).unwrap();

        // Negative values should work fine
        sma.update(-100.0).unwrap();
        sma.update(-200.0).unwrap();
        let sma_result = sma.update(-300.0).unwrap().unwrap();
        assert!((sma_result - (-200.0)).abs() < 1e-10);

        ema.update(-100.0).unwrap();
        ema.update(-200.0).unwrap();
        let ema_result = ema.update(-300.0).unwrap().unwrap();
        assert!(ema_result < 0.0);

        rsi.update(-100.0).unwrap();
        rsi.update(-110.0).unwrap();
        rsi.update(-120.0).unwrap();
        let rsi_result = rsi.update(-130.0).unwrap();
        assert!(rsi_result.is_some());
        assert!(rsi_result.unwrap() < 50.0); // All losses

        bb.update(-100.0).unwrap();
        bb.update(-200.0).unwrap();
        let bb_result = bb.update(-300.0).unwrap().unwrap();
        let (upper, mid, lower) = bb_result;
        assert!(mid < 0.0);
        assert!(upper > lower);
    }

    #[test]
    fn test_clone_independence() {
        let mut sma1 = OnlineSMA::new(3).unwrap();
        sma1.update(1.0).unwrap();
        sma1.update(2.0).unwrap();

        let mut sma2 = sma1.clone();

        sma1.update(3.0).unwrap();
        sma2.update(6.0).unwrap();

        let result1 = sma1.update(4.0).unwrap().unwrap();
        let result2 = sma2.update(9.0).unwrap().unwrap();

        // They should be independent
        assert!((result1 - 3.0).abs() < 1e-10); // (2+3+4)/3
        assert!((result2 - 5.666666666666667).abs() < 1e-10); // (2+6+9)/3
    }
}
