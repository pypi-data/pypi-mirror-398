// dataframe.rs - DataFrame 支持模块
#![allow(dead_code)]
//
// 提供类 DataFrame 的批量指标计算接口
// 遵循 KISS 原则：专注于 OHLCV 数据结构

use std::collections::HashMap;

use crate::errors::{HazeError, HazeResult};
use crate::indicators::{momentum, trend, volatility, volume};
use crate::utils::ma;

/// OHLCV DataFrame 结构
///
/// 存储金融时序数据，支持批量指标计算
#[derive(Debug, Clone)]
pub struct OhlcvFrame {
    /// 时间戳序列
    pub timestamps: Vec<i64>,
    /// 开盘价
    pub open: Vec<f64>,
    /// 最高价
    pub high: Vec<f64>,
    /// 最低价
    pub low: Vec<f64>,
    /// 收盘价
    pub close: Vec<f64>,
    /// 成交量
    pub volume: Vec<f64>,
    /// 计算结果缓存
    cache: HashMap<String, Vec<f64>>,
}

impl OhlcvFrame {
    /// 从向量创建 DataFrame
    pub fn new(
        timestamps: Vec<i64>,
        open: Vec<f64>,
        high: Vec<f64>,
        low: Vec<f64>,
        close: Vec<f64>,
        volume: Vec<f64>,
    ) -> HazeResult<Self> {
        let len = timestamps.len();

        // 验证长度一致性
        if open.len() != len {
            return Err(HazeError::LengthMismatch {
                name1: "timestamps",
                len1: len,
                name2: "open",
                len2: open.len(),
            });
        }
        if high.len() != len {
            return Err(HazeError::LengthMismatch {
                name1: "timestamps",
                len1: len,
                name2: "high",
                len2: high.len(),
            });
        }
        if low.len() != len {
            return Err(HazeError::LengthMismatch {
                name1: "timestamps",
                len1: len,
                name2: "low",
                len2: low.len(),
            });
        }
        if close.len() != len {
            return Err(HazeError::LengthMismatch {
                name1: "timestamps",
                len1: len,
                name2: "close",
                len2: close.len(),
            });
        }
        if volume.len() != len {
            return Err(HazeError::LengthMismatch {
                name1: "timestamps",
                len1: len,
                name2: "volume",
                len2: volume.len(),
            });
        }

        Ok(Self {
            timestamps,
            open,
            high,
            low,
            close,
            volume,
            cache: HashMap::new(),
        })
    }

    /// 从切片创建 DataFrame
    pub fn from_slices(
        timestamps: &[i64],
        open: &[f64],
        high: &[f64],
        low: &[f64],
        close: &[f64],
        volume: &[f64],
    ) -> HazeResult<Self> {
        Self::new(
            timestamps.to_vec(),
            open.to_vec(),
            high.to_vec(),
            low.to_vec(),
            close.to_vec(),
            volume.to_vec(),
        )
    }

    /// 数据长度
    #[inline]
    pub fn len(&self) -> usize {
        self.close.len()
    }

    /// 是否为空
    #[inline]
    pub fn is_empty(&self) -> bool {
        self.close.is_empty()
    }

    /// 清除缓存
    pub fn clear_cache(&mut self) {
        self.cache.clear();
    }

    // ==================== 移动平均指标 ====================

    /// SMA - Simple Moving Average
    pub fn sma(&mut self, period: usize) -> HazeResult<&[f64]> {
        let key = format!("sma_{period}");
        if !self.cache.contains_key(&key) {
            let result = ma::sma(&self.close, period)?;
            self.cache.insert(key.clone(), result);
        }
        Ok(self
            .cache
            .get(&key)
            .expect("internal error: cache key should exist after insert"))
    }

    /// EMA - Exponential Moving Average
    pub fn ema(&mut self, period: usize) -> HazeResult<&[f64]> {
        let key = format!("ema_{period}");
        if !self.cache.contains_key(&key) {
            let result = ma::ema(&self.close, period)?;
            self.cache.insert(key.clone(), result);
        }
        Ok(self
            .cache
            .get(&key)
            .expect("internal error: cache key should exist after insert"))
    }

    /// WMA - Weighted Moving Average
    pub fn wma(&mut self, period: usize) -> HazeResult<&[f64]> {
        let key = format!("wma_{period}");
        if !self.cache.contains_key(&key) {
            let result = ma::wma(&self.close, period)?;
            self.cache.insert(key.clone(), result);
        }
        Ok(self
            .cache
            .get(&key)
            .expect("internal error: cache key should exist after insert"))
    }

    /// HMA - Hull Moving Average
    pub fn hma(&mut self, period: usize) -> HazeResult<&[f64]> {
        let key = format!("hma_{period}");
        if !self.cache.contains_key(&key) {
            let result = ma::hma(&self.close, period)?;
            self.cache.insert(key.clone(), result);
        }
        Ok(self
            .cache
            .get(&key)
            .expect("internal error: cache key should exist after insert"))
    }

    // ==================== 波动率指标 ====================

    /// ATR - Average True Range
    pub fn atr(&mut self, period: usize) -> HazeResult<&[f64]> {
        let key = format!("atr_{period}");
        if !self.cache.contains_key(&key) {
            let result = volatility::atr(&self.high, &self.low, &self.close, period)?;
            self.cache.insert(key.clone(), result);
        }
        Ok(self
            .cache
            .get(&key)
            .expect("internal error: cache key should exist after insert"))
    }

    /// True Range
    pub fn true_range(&mut self) -> HazeResult<&[f64]> {
        let key = "true_range".to_string();
        if !self.cache.contains_key(&key) {
            // drift=1 是默认值
            let result = volatility::true_range(&self.high, &self.low, &self.close, 1)?;
            self.cache.insert(key.clone(), result);
        }
        Ok(self
            .cache
            .get(&key)
            .expect("internal error: cache key should exist after insert"))
    }

    /// Bollinger Bands - 返回 (upper, middle, lower)
    pub fn bollinger_bands(
        &mut self,
        period: usize,
        std_dev: f64,
    ) -> HazeResult<(&[f64], &[f64], &[f64])> {
        let key_mid = format!("bb_mid_{period}_{std_dev}");
        let key_upper = format!("bb_upper_{period}_{std_dev}");
        let key_lower = format!("bb_lower_{period}_{std_dev}");

        if !self.cache.contains_key(&key_mid) {
            // volatility::bollinger_bands 返回 (upper, middle, lower)
            let (upper, mid, lower) = volatility::bollinger_bands(&self.close, period, std_dev)?;
            self.cache.insert(key_mid.clone(), mid);
            self.cache.insert(key_upper.clone(), upper);
            self.cache.insert(key_lower.clone(), lower);
        }

        Ok((
            self.cache
                .get(&key_upper)
                .expect("internal error: cache key should exist after insert"),
            self.cache
                .get(&key_mid)
                .expect("internal error: cache key should exist after insert"),
            self.cache
                .get(&key_lower)
                .expect("internal error: cache key should exist after insert"),
        ))
    }

    // ==================== 动量指标 ====================

    /// RSI - Relative Strength Index
    pub fn rsi(&mut self, period: usize) -> HazeResult<&[f64]> {
        let key = format!("rsi_{period}");
        if !self.cache.contains_key(&key) {
            let result = momentum::rsi(&self.close, period)?;
            self.cache.insert(key.clone(), result);
        }
        Ok(self
            .cache
            .get(&key)
            .expect("internal error: cache key should exist after insert"))
    }

    /// MACD - 返回 (macd, signal, histogram)
    pub fn macd(
        &mut self,
        fast: usize,
        slow: usize,
        signal: usize,
    ) -> HazeResult<(&[f64], &[f64], &[f64])> {
        let key_macd = format!("macd_{fast}_{slow}_{signal}");
        let key_signal = format!("macd_signal_{fast}_{slow}_{signal}");
        let key_hist = format!("macd_hist_{fast}_{slow}_{signal}");

        if !self.cache.contains_key(&key_macd) {
            let (macd_line, signal_line, histogram) =
                momentum::macd(&self.close, fast, slow, signal)?;
            self.cache.insert(key_macd.clone(), macd_line);
            self.cache.insert(key_signal.clone(), signal_line);
            self.cache.insert(key_hist.clone(), histogram);
        }

        Ok((
            self.cache
                .get(&key_macd)
                .expect("internal error: cache key should exist after insert"),
            self.cache
                .get(&key_signal)
                .expect("internal error: cache key should exist after insert"),
            self.cache
                .get(&key_hist)
                .expect("internal error: cache key should exist after insert"),
        ))
    }

    /// Stochastic - 返回 (k, d)
    pub fn stochastic(
        &mut self,
        k_period: usize,
        smooth_k: usize,
        d_period: usize,
    ) -> HazeResult<(&[f64], &[f64])> {
        let key_k = format!("stoch_k_{k_period}_{smooth_k}_{d_period}");
        let key_d = format!("stoch_d_{k_period}_{smooth_k}_{d_period}");

        if !self.cache.contains_key(&key_k) {
            let (k, d) = momentum::stochastic(
                &self.high,
                &self.low,
                &self.close,
                k_period,
                smooth_k,
                d_period,
            )?;
            self.cache.insert(key_k.clone(), k);
            self.cache.insert(key_d.clone(), d);
        }

        Ok((
            self.cache
                .get(&key_k)
                .expect("internal error: cache key should exist after insert"),
            self.cache
                .get(&key_d)
                .expect("internal error: cache key should exist after insert"),
        ))
    }

    /// CCI - Commodity Channel Index
    pub fn cci(&mut self, period: usize) -> HazeResult<&[f64]> {
        let key = format!("cci_{period}");
        if !self.cache.contains_key(&key) {
            let result = momentum::cci(&self.high, &self.low, &self.close, period)?;
            self.cache.insert(key.clone(), result);
        }
        Ok(self
            .cache
            .get(&key)
            .expect("internal error: cache key should exist after insert"))
    }

    /// Williams %R
    pub fn williams_r(&mut self, period: usize) -> HazeResult<&[f64]> {
        let key = format!("willr_{period}");
        if !self.cache.contains_key(&key) {
            let result = momentum::williams_r(&self.high, &self.low, &self.close, period)?;
            self.cache.insert(key.clone(), result);
        }
        Ok(self
            .cache
            .get(&key)
            .expect("internal error: cache key should exist after insert"))
    }

    // ==================== 趋势指标 ====================

    /// SuperTrend - 返回 (supertrend, direction, upper_band, lower_band)
    pub fn supertrend(
        &mut self,
        period: usize,
        multiplier: f64,
    ) -> crate::types::SuperTrendSlices<'_> {
        let key_st = format!("supertrend_{period}_{multiplier}");
        let key_dir = format!("supertrend_dir_{period}_{multiplier}");
        let key_upper = format!("supertrend_upper_{period}_{multiplier}");
        let key_lower = format!("supertrend_lower_{period}_{multiplier}");

        if !self.cache.contains_key(&key_st) {
            let (st, dir, upper, lower) =
                trend::supertrend(&self.high, &self.low, &self.close, period, multiplier)?;
            self.cache.insert(key_st.clone(), st);
            self.cache.insert(key_dir.clone(), dir);
            self.cache.insert(key_upper.clone(), upper);
            self.cache.insert(key_lower.clone(), lower);
        }

        Ok((
            self.cache
                .get(&key_st)
                .expect("internal error: cache key should exist after insert"),
            self.cache
                .get(&key_dir)
                .expect("internal error: cache key should exist after insert"),
            self.cache
                .get(&key_upper)
                .expect("internal error: cache key should exist after insert"),
            self.cache
                .get(&key_lower)
                .expect("internal error: cache key should exist after insert"),
        ))
    }

    /// ADX - Average Directional Index，返回 (adx, plus_di, minus_di)
    pub fn adx(&mut self, period: usize) -> HazeResult<(&[f64], &[f64], &[f64])> {
        let key_adx = format!("adx_{period}");
        let key_plus = format!("adx_plus_di_{period}");
        let key_minus = format!("adx_minus_di_{period}");

        if !self.cache.contains_key(&key_adx) {
            let (adx, plus_di, minus_di) = trend::adx(&self.high, &self.low, &self.close, period)?;
            self.cache.insert(key_adx.clone(), adx);
            self.cache.insert(key_plus.clone(), plus_di);
            self.cache.insert(key_minus.clone(), minus_di);
        }

        Ok((
            self.cache
                .get(&key_adx)
                .expect("internal error: cache key should exist after insert"),
            self.cache
                .get(&key_plus)
                .expect("internal error: cache key should exist after insert"),
            self.cache
                .get(&key_minus)
                .expect("internal error: cache key should exist after insert"),
        ))
    }

    // ==================== 成交量指标 ====================

    /// OBV - On Balance Volume
    pub fn obv(&mut self) -> HazeResult<&[f64]> {
        let key = "obv".to_string();
        if !self.cache.contains_key(&key) {
            let result = volume::obv(&self.close, &self.volume)?;
            self.cache.insert(key.clone(), result);
        }
        Ok(self
            .cache
            .get(&key)
            .expect("internal error: cache key should exist after insert"))
    }

    /// VWAP - Volume Weighted Average Price
    pub fn vwap(&mut self, period: usize) -> HazeResult<&[f64]> {
        let key = format!("vwap_{period}");
        if !self.cache.contains_key(&key) {
            let result = volume::vwap(&self.high, &self.low, &self.close, &self.volume, period)?;
            self.cache.insert(key.clone(), result);
        }
        Ok(self
            .cache
            .get(&key)
            .expect("internal error: cache key should exist after insert"))
    }

    /// MFI - Money Flow Index
    pub fn mfi(&mut self, period: usize) -> HazeResult<&[f64]> {
        let key = format!("mfi_{period}");
        if !self.cache.contains_key(&key) {
            let result = volume::mfi(&self.high, &self.low, &self.close, &self.volume, period)?;
            self.cache.insert(key.clone(), result);
        }
        Ok(self
            .cache
            .get(&key)
            .expect("internal error: cache key should exist after insert"))
    }

    // ==================== 批量计算 ====================

    /// 批量计算多个 SMA 周期
    pub fn batch_sma(&mut self, periods: &[usize]) -> HazeResult<HashMap<usize, Vec<f64>>> {
        let mut results = HashMap::new();
        for &period in periods {
            let key = format!("sma_{period}");
            if !self.cache.contains_key(&key) {
                let result = ma::sma(&self.close, period)?;
                self.cache.insert(key.clone(), result);
            }
            results.insert(
                period,
                self.cache
                    .get(&key)
                    .expect("internal error: cache key should exist after insert")
                    .clone(),
            );
        }
        Ok(results)
    }

    /// 批量计算多个 EMA 周期
    pub fn batch_ema(&mut self, periods: &[usize]) -> HazeResult<HashMap<usize, Vec<f64>>> {
        let mut results = HashMap::new();
        for &period in periods {
            let key = format!("ema_{period}");
            if !self.cache.contains_key(&key) {
                let result = ma::ema(&self.close, period)?;
                self.cache.insert(key.clone(), result);
            }
            results.insert(
                period,
                self.cache
                    .get(&key)
                    .expect("internal error: cache key should exist after insert")
                    .clone(),
            );
        }
        Ok(results)
    }

    /// 计算常用指标套件
    ///
    /// 返回包含以下指标的 HashMap:
    /// - sma_20, ema_20
    /// - rsi_14
    /// - macd, macd_signal, macd_hist
    /// - atr_14
    /// - bb_mid, bb_upper, bb_lower
    pub fn compute_common_indicators(&mut self) -> HazeResult<HashMap<String, Vec<f64>>> {
        let mut results = HashMap::new();

        // SMA/EMA
        results.insert("sma_20".to_string(), self.sma(20)?.to_vec());
        results.insert("ema_20".to_string(), self.ema(20)?.to_vec());

        // RSI
        results.insert("rsi_14".to_string(), self.rsi(14)?.to_vec());

        // MACD
        let (macd, signal, hist) = self.macd(12, 26, 9)?;
        results.insert("macd".to_string(), macd.to_vec());
        results.insert("macd_signal".to_string(), signal.to_vec());
        results.insert("macd_hist".to_string(), hist.to_vec());

        // ATR
        results.insert("atr_14".to_string(), self.atr(14)?.to_vec());

        // Bollinger Bands
        let (upper, mid, lower) = self.bollinger_bands(20, 2.0)?;
        results.insert("bb_mid".to_string(), mid.to_vec());
        results.insert("bb_upper".to_string(), upper.to_vec());
        results.insert("bb_lower".to_string(), lower.to_vec());

        Ok(results)
    }

    /// 获取缓存的指标
    pub fn get_cached(&self, name: &str) -> Option<&[f64]> {
        self.cache.get(name).map(|v| v.as_slice())
    }

    /// 列出所有已缓存的指标名称
    pub fn cached_indicators(&self) -> Vec<&String> {
        self.cache.keys().collect()
    }
}

/// 从原始数组创建 DataFrame 的便捷函数
pub fn create_ohlcv_frame(
    timestamps: &[i64],
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    volume: &[f64],
) -> HazeResult<OhlcvFrame> {
    OhlcvFrame::from_slices(timestamps, open, high, low, close, volume)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_frame() -> OhlcvFrame {
        let n = 100;
        let timestamps: Vec<i64> = (0..n).map(|i| i as i64 * 60000).collect();
        let close: Vec<f64> = (0..n).map(|i| 100.0 + (i as f64) * 0.5).collect();
        let high: Vec<f64> = close.iter().map(|&c| c + 1.0).collect();
        let low: Vec<f64> = close.iter().map(|&c| c - 1.0).collect();
        let open: Vec<f64> = close.iter().map(|&c| c - 0.2).collect();
        let volume: Vec<f64> = (0..n).map(|i| 1000.0 + (i as f64) * 10.0).collect();

        OhlcvFrame::new(timestamps, open, high, low, close, volume).unwrap()
    }

    #[test]
    fn test_create_frame() {
        let frame = create_test_frame();
        assert_eq!(frame.len(), 100);
        assert!(!frame.is_empty());
    }

    #[test]
    fn test_sma() {
        let mut frame = create_test_frame();
        let sma = frame.sma(20).unwrap();
        assert_eq!(sma.len(), 100);
        assert!(sma[19].is_finite()); // 第 20 个值应该有效
    }

    #[test]
    fn test_ema() {
        let mut frame = create_test_frame();
        let ema = frame.ema(20).unwrap();
        assert_eq!(ema.len(), 100);
        assert!(ema[19].is_finite());
    }

    #[test]
    fn test_rsi() {
        let mut frame = create_test_frame();
        let rsi = frame.rsi(14).unwrap();
        assert_eq!(rsi.len(), 100);
        // 持续上涨，RSI 应该接近 100
        let valid_rsi = rsi.iter().find(|v| v.is_finite()).unwrap();
        assert!(*valid_rsi > 50.0);
    }

    #[test]
    fn test_macd() {
        let mut frame = create_test_frame();
        let (macd, signal, hist) = frame.macd(12, 26, 9).unwrap();
        assert_eq!(macd.len(), 100);
        assert_eq!(signal.len(), 100);
        assert_eq!(hist.len(), 100);
    }

    #[test]
    fn test_bollinger_bands() {
        let mut frame = create_test_frame();
        let (upper, mid, lower) = frame.bollinger_bands(20, 2.0).unwrap();
        assert_eq!(mid.len(), 100);

        // 检查有有效值
        let valid_count = mid.iter().filter(|v| v.is_finite()).count();
        assert!(valid_count > 0, "Bollinger bands should have valid values");

        // 上轨应该 >= 中轨，中轨应该 >= 下轨
        // 检查所有三个值都有效的情况
        for i in 19..100 {
            if mid[i].is_finite() && upper[i].is_finite() && lower[i].is_finite() {
                assert!(
                    upper[i] >= mid[i],
                    "upper[{}]={} should >= mid[{}]={}",
                    i,
                    upper[i],
                    i,
                    mid[i]
                );
                assert!(
                    mid[i] >= lower[i],
                    "mid[{}]={} should >= lower[{}]={}",
                    i,
                    mid[i],
                    i,
                    lower[i]
                );
            }
        }
    }

    #[test]
    fn test_atr() {
        let mut frame = create_test_frame();
        let atr = frame.atr(14).unwrap();
        assert_eq!(atr.len(), 100);
        // ATR 在 period 之后才有有效值
        let valid_count = atr.iter().filter(|v| v.is_finite()).count();
        assert!(valid_count > 0, "ATR should have valid values");
    }

    #[test]
    fn test_cache() {
        let mut frame = create_test_frame();

        // 第一次计算
        let _ = frame.sma(20).unwrap();
        assert!(frame.cache.contains_key("sma_20"));

        // 第二次应该使用缓存
        let _ = frame.sma(20).unwrap();
        assert_eq!(frame.cached_indicators().len(), 1);

        // 清除缓存
        frame.clear_cache();
        assert!(frame.cache.is_empty());
    }

    #[test]
    fn test_batch_sma() {
        let mut frame = create_test_frame();
        let results = frame.batch_sma(&[5, 10, 20]).unwrap();
        assert_eq!(results.len(), 3);
        assert!(results.contains_key(&5));
        assert!(results.contains_key(&10));
        assert!(results.contains_key(&20));
    }

    #[test]
    fn test_common_indicators() {
        let mut frame = create_test_frame();
        let indicators = frame.compute_common_indicators().unwrap();

        assert!(indicators.contains_key("sma_20"));
        assert!(indicators.contains_key("ema_20"));
        assert!(indicators.contains_key("rsi_14"));
        assert!(indicators.contains_key("macd"));
        assert!(indicators.contains_key("atr_14"));
        assert!(indicators.contains_key("bb_mid"));
    }

    #[test]
    fn test_validation() {
        use crate::errors::HazeError;

        // 长度不一致应该返回错误
        let result = OhlcvFrame::new(
            vec![1, 2, 3],
            vec![1.0, 2.0], // 长度不匹配
            vec![1.0, 2.0, 3.0],
            vec![1.0, 2.0, 3.0],
            vec![1.0, 2.0, 3.0],
            vec![1.0, 2.0, 3.0],
        );
        assert!(matches!(result, Err(HazeError::LengthMismatch { .. })));
    }
}
