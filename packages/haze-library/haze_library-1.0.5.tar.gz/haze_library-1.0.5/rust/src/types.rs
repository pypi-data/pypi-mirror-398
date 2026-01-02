// types.rs - 核心数据类型定义
// 内部辅助函数保留供未来扩展
#![allow(dead_code)]
// OHLCV 元组类型在金融领域是标准模式
#![allow(clippy::type_complexity)]
#![allow(clippy::wrong_self_convention)]

#[cfg(feature = "python")]
use pyo3::prelude::*;

use crate::errors::HazeResult;

// ==================== Type Aliases for Complex Returns ====================

/// SuperTrend indicator result: (supertrend_line, direction, upper_band, lower_band)
pub type SuperTrendResult<T> = HazeResult<(T, T, T, T)>;

/// SuperTrend slices for cached data
pub type SuperTrendSlices<'a> = HazeResult<(&'a [f64], &'a [f64], &'a [f64], &'a [f64])>;

/// SuperTrend owned vectors for Python FFI
#[cfg(feature = "python")]
pub type SuperTrendVecs = PyResult<(Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>)>;

#[cfg(not(feature = "python"))]
type PyResult<T> = Result<T, String>;

// ==================== Signal Type Aliases (消除 type_complexity 警告) ====================

/// Trading signals with stop-loss and take-profit levels
/// Returns: (buy_signals, sell_signals, stop_loss, take_profit)
pub type TradingSignals = HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>)>;

/// Zone-based signals with upper/lower bounds
/// Returns: (bullish_zone, bearish_zone, upper_bound, lower_bound)
pub type ZoneSignals = HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>)>;

/// Harmonic pattern signals with PRZ and probability
/// Returns: (signals, prz_upper, prz_lower, probability)
pub type HarmonicSignals = HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>)>;

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// K线数据结构（OHLCV）
#[cfg(feature = "python")]
#[pyo3::prelude::pyclass]
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Candle {
    #[pyo3(get, set)]
    pub timestamp: i64, // Unix 毫秒时间戳
    #[pyo3(get, set)]
    pub open: f64,
    #[pyo3(get, set)]
    pub high: f64,
    #[pyo3(get, set)]
    pub low: f64,
    #[pyo3(get, set)]
    pub close: f64,
    #[pyo3(get, set)]
    pub volume: f64,
}

#[cfg(not(feature = "python"))]
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Candle {
    pub timestamp: i64,
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    pub volume: f64,
}

#[cfg(feature = "python")]
#[pyo3::pymethods]
impl Candle {
    #[new]
    pub fn new(timestamp: i64, open: f64, high: f64, low: f64, close: f64, volume: f64) -> Self {
        Self {
            timestamp,
            open,
            high,
            low,
            close,
            volume,
        }
    }

    /// 转换为 Python 字典
    pub fn to_dict(&self) -> PyResult<HashMap<String, f64>> {
        let mut map = HashMap::new();
        map.insert("timestamp".to_string(), self.timestamp as f64);
        map.insert("open".to_string(), self.open);
        map.insert("high".to_string(), self.high);
        map.insert("low".to_string(), self.low);
        map.insert("close".to_string(), self.close);
        map.insert("volume".to_string(), self.volume);
        Ok(map)
    }

    /// 获取典型价格 (high + low + close) / 3
    #[getter]
    pub fn typical_price(&self) -> f64 {
        (self.high + self.low + self.close) / 3.0
    }

    /// 获取中间价 (high + low) / 2
    #[getter]
    pub fn median_price(&self) -> f64 {
        (self.high + self.low) / 2.0
    }

    /// 获取加权收盘价 (high + low + 2*close) / 4
    #[getter]
    pub fn weighted_close(&self) -> f64 {
        (self.high + self.low + 2.0 * self.close) / 4.0
    }

    /// 字符串表示
    pub fn __repr__(&self) -> String {
        format!(
            "Candle(O:{:.2}, H:{:.2}, L:{:.2}, C:{:.2}, V:{:.2})",
            self.open, self.high, self.low, self.close, self.volume
        )
    }
}

#[cfg(not(feature = "python"))]
impl Candle {
    pub fn new(timestamp: i64, open: f64, high: f64, low: f64, close: f64, volume: f64) -> Self {
        Self {
            timestamp,
            open,
            high,
            low,
            close,
            volume,
        }
    }

    pub fn to_dict(&self) -> Result<HashMap<String, f64>, String> {
        let mut map = HashMap::new();
        map.insert("timestamp".to_string(), self.timestamp as f64);
        map.insert("open".to_string(), self.open);
        map.insert("high".to_string(), self.high);
        map.insert("low".to_string(), self.low);
        map.insert("close".to_string(), self.close);
        map.insert("volume".to_string(), self.volume);
        Ok(map)
    }

    pub fn typical_price(&self) -> f64 {
        (self.high + self.low + self.close) / 3.0
    }

    pub fn median_price(&self) -> f64 {
        (self.high + self.low) / 2.0
    }

    pub fn weighted_close(&self) -> f64 {
        (self.high + self.low + 2.0 * self.close) / 4.0
    }

    pub fn __repr__(&self) -> String {
        format!(
            "Candle(O:{:.2}, H:{:.2}, L:{:.2}, C:{:.2}, V:{:.2})",
            self.open, self.high, self.low, self.close, self.volume
        )
    }
}

/// 指标计算结果（单序列）
#[cfg(feature = "python")]
#[pyo3::prelude::pyclass]
#[derive(Debug, Clone)]
pub struct IndicatorResult {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub values: Vec<f64>,
    #[pyo3(get)]
    pub metadata: HashMap<String, String>,
}

#[cfg(not(feature = "python"))]
#[derive(Debug, Clone)]
pub struct IndicatorResult {
    pub name: String,
    pub values: Vec<f64>,
    pub metadata: HashMap<String, String>,
}

#[cfg(feature = "python")]
#[pyo3::pymethods]
impl IndicatorResult {
    #[new]
    pub fn new(name: String, values: Vec<f64>) -> Self {
        Self {
            name,
            values,
            metadata: HashMap::new(),
        }
    }

    /// 添加元数据
    pub fn add_metadata(&mut self, key: String, value: String) {
        self.metadata.insert(key, value);
    }

    /// 获取长度
    #[getter]
    pub fn len(&self) -> usize {
        self.values.len()
    }

    pub fn is_empty(&self) -> bool {
        self.values.is_empty()
    }
}

#[cfg(not(feature = "python"))]
impl IndicatorResult {
    pub fn new(name: String, values: Vec<f64>) -> Self {
        Self {
            name,
            values,
            metadata: HashMap::new(),
        }
    }

    pub fn add_metadata(&mut self, key: String, value: String) {
        self.metadata.insert(key, value);
    }

    pub fn len(&self) -> usize {
        self.values.len()
    }

    pub fn is_empty(&self) -> bool {
        self.values.is_empty()
    }
}

/// 多序列指标结果（如 MACD 返回 3 条线）
#[cfg(feature = "python")]
#[pyo3::prelude::pyclass]
#[derive(Debug, Clone)]
pub struct MultiIndicatorResult {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub series: HashMap<String, Vec<f64>>,
    #[pyo3(get)]
    pub metadata: HashMap<String, String>,
}

#[cfg(not(feature = "python"))]
#[derive(Debug, Clone)]
pub struct MultiIndicatorResult {
    pub name: String,
    pub series: HashMap<String, Vec<f64>>,
    pub metadata: HashMap<String, String>,
}

#[cfg(feature = "python")]
#[pyo3::pymethods]
impl MultiIndicatorResult {
    #[new]
    pub fn new(name: String) -> Self {
        Self {
            name,
            series: HashMap::new(),
            metadata: HashMap::new(),
        }
    }

    /// 添加序列
    pub fn add_series(&mut self, key: String, values: Vec<f64>) {
        self.series.insert(key, values);
    }

    /// 添加元数据
    pub fn add_metadata(&mut self, key: String, value: String) {
        self.metadata.insert(key, value);
    }
}

#[cfg(not(feature = "python"))]
impl MultiIndicatorResult {
    pub fn new(name: String) -> Self {
        Self {
            name,
            series: HashMap::new(),
            metadata: HashMap::new(),
        }
    }

    pub fn add_series(&mut self, key: String, values: Vec<f64>) {
        self.series.insert(key, values);
    }

    pub fn add_metadata(&mut self, key: String, value: String) {
        self.metadata.insert(key, value);
    }
}

// ==================== 辅助函数 ====================

/// 将 `Vec<Candle>` 转换为分离的 OHLCV 向量
pub fn candles_to_vectors(
    candles: &[Candle],
) -> (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>) {
    let open: Vec<f64> = candles.iter().map(|c| c.open).collect();
    let high: Vec<f64> = candles.iter().map(|c| c.high).collect();
    let low: Vec<f64> = candles.iter().map(|c| c.low).collect();
    let close: Vec<f64> = candles.iter().map(|c| c.close).collect();
    let volume: Vec<f64> = candles.iter().map(|c| c.volume).collect();
    (open, high, low, close, volume)
}

/// 验证 OHLC 逻辑（high >= max(O,C), low <= min(O,C)）
pub fn validate_ohlc(candles: &[Candle]) -> Result<(), String> {
    for (i, candle) in candles.iter().enumerate() {
        let max_oc = candle.open.max(candle.close);
        let min_oc = candle.open.min(candle.close);

        if candle.high < max_oc {
            return Err(format!(
                "Candle {i} 违反 OHLC 逻辑: high < max(open, close)"
            ));
        }

        if candle.low > min_oc {
            return Err(format!("Candle {i} 违反 OHLC 逻辑: low > min(open, close)"));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_candle_creation() {
        let candle = Candle::new(1704067200000, 100.0, 102.0, 99.0, 101.0, 1000.0);
        assert_eq!(candle.open, 100.0);
        assert_eq!(candle.high, 102.0);
        assert_eq!(candle.typical_price(), 100.66666666666667);
        assert_eq!(candle.median_price(), 100.5);
    }

    #[test]
    fn test_ohlc_validation() {
        let valid_candles = vec![
            Candle::new(0, 100.0, 102.0, 99.0, 101.0, 1000.0),
            Candle::new(1, 101.0, 103.0, 100.0, 102.0, 1100.0),
        ];
        assert!(validate_ohlc(&valid_candles).is_ok());

        let invalid_candles = vec![
            Candle::new(0, 100.0, 99.0, 98.0, 101.0, 1000.0), // high < close
        ];
        assert!(validate_ohlc(&invalid_candles).is_err());
    }
}
