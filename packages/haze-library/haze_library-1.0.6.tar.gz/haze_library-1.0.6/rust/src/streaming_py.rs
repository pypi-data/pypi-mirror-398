//! Python bindings for streaming/online calculators
//!
//! This module provides PyO3 wrappers for the streaming calculators,
//! enabling real-time indicator calculation in Python.

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
use crate::utils::streaming::{
    AISuperTrendMLResult, EnsembleResult, MLSuperTrendResult, OnlineAISuperTrendML, OnlineATR,
    OnlineAdaptiveRSI, OnlineBollingerBands, OnlineEMA, OnlineEnsembleSignal, OnlineMACD,
    OnlineMLSuperTrend, OnlineRSI, OnlineSMA, OnlineStochastic, OnlineSuperTrend,
};

// ==================== OnlineSMA Python Wrapper ====================

#[cfg(feature = "python")]
#[pyclass(name = "OnlineSMA")]
pub struct PyOnlineSMA {
    inner: OnlineSMA,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOnlineSMA {
    #[new]
    pub fn new(period: usize) -> PyResult<Self> {
        Ok(Self {
            inner: OnlineSMA::new(period)?,
        })
    }

    pub fn update(&mut self, value: f64) -> PyResult<Option<f64>> {
        Ok(self.inner.update(value)?)
    }

    pub fn reset(&mut self) {
        self.inner.reset();
    }

    pub fn len(&self) -> usize {
        self.inner.len()
    }

    pub fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }

    pub fn force_recalculate(&mut self) {
        self.inner.force_recalculate();
    }
}

// ==================== OnlineEMA Python Wrapper ====================

#[cfg(feature = "python")]
#[pyclass(name = "OnlineEMA")]
pub struct PyOnlineEMA {
    inner: OnlineEMA,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOnlineEMA {
    #[new]
    pub fn new(period: usize) -> PyResult<Self> {
        Ok(Self {
            inner: OnlineEMA::new(period)?,
        })
    }

    pub fn update(&mut self, value: f64) -> PyResult<Option<f64>> {
        Ok(self.inner.update(value)?)
    }

    pub fn reset(&mut self) {
        self.inner.reset();
    }

    pub fn is_ready(&self) -> bool {
        self.inner.is_ready()
    }
}

// ==================== OnlineRSI Python Wrapper ====================

#[cfg(feature = "python")]
#[pyclass(name = "OnlineRSI")]
pub struct PyOnlineRSI {
    inner: OnlineRSI,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOnlineRSI {
    #[new]
    pub fn new(period: usize) -> PyResult<Self> {
        Ok(Self {
            inner: OnlineRSI::new(period)?,
        })
    }

    pub fn update(&mut self, value: f64) -> PyResult<Option<f64>> {
        Ok(self.inner.update(value)?)
    }

    pub fn reset(&mut self) {
        self.inner.reset();
    }
}

// ==================== OnlineATR Python Wrapper ====================

#[cfg(feature = "python")]
#[pyclass(name = "OnlineATR")]
pub struct PyOnlineATR {
    inner: OnlineATR,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOnlineATR {
    #[new]
    pub fn new(period: usize) -> PyResult<Self> {
        Ok(Self {
            inner: OnlineATR::new(period)?,
        })
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> PyResult<Option<f64>> {
        Ok(self.inner.update(high, low, close)?)
    }

    pub fn reset(&mut self) {
        self.inner.reset();
    }

    pub fn is_ready(&self) -> bool {
        self.inner.is_ready()
    }
}

// ==================== OnlineMACD Python Wrapper ====================

#[cfg(feature = "python")]
#[pyclass(name = "OnlineMACD")]
pub struct PyOnlineMACD {
    inner: OnlineMACD,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOnlineMACD {
    #[new]
    #[pyo3(signature = (fast=12, slow=26, signal=9))]
    pub fn new(fast: usize, slow: usize, signal: usize) -> PyResult<Self> {
        Ok(Self {
            inner: OnlineMACD::new(fast, slow, signal)?,
        })
    }

    /// Returns (MACD, Signal, Histogram) or None if not ready
    pub fn update(&mut self, value: f64) -> PyResult<Option<(f64, f64, f64)>> {
        Ok(self.inner.update(value)?)
    }

    pub fn reset(&mut self) {
        self.inner.reset();
    }
}

// ==================== OnlineBollingerBands Python Wrapper ====================

#[cfg(feature = "python")]
#[pyclass(name = "OnlineBollingerBands")]
pub struct PyOnlineBollingerBands {
    inner: OnlineBollingerBands,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOnlineBollingerBands {
    #[new]
    #[pyo3(signature = (period=20, std_dev=2.0))]
    pub fn new(period: usize, std_dev: f64) -> PyResult<Self> {
        Ok(Self {
            inner: OnlineBollingerBands::new(period, std_dev)?,
        })
    }

    /// Returns (Upper, Middle, Lower) or None if not ready
    pub fn update(&mut self, value: f64) -> PyResult<Option<(f64, f64, f64)>> {
        Ok(self.inner.update(value)?)
    }

    pub fn reset(&mut self) {
        self.inner.reset();
    }

    pub fn force_recalculate(&mut self) {
        self.inner.force_recalculate();
    }
}

// ==================== OnlineStochastic Python Wrapper ====================

#[cfg(feature = "python")]
#[pyclass(name = "OnlineStochastic")]
pub struct PyOnlineStochastic {
    inner: OnlineStochastic,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOnlineStochastic {
    #[new]
    #[pyo3(signature = (k_period=14, smooth_k=3, d_period=3))]
    pub fn new(k_period: usize, smooth_k: usize, d_period: usize) -> PyResult<Self> {
        Ok(Self {
            inner: OnlineStochastic::new(k_period, smooth_k, d_period)?,
        })
    }

    /// Returns (%K, %D) or None if not ready
    pub fn update(&mut self, high: f64, low: f64, close: f64) -> PyResult<Option<(f64, f64)>> {
        Ok(self.inner.update(high, low, close)?)
    }

    pub fn reset(&mut self) {
        self.inner.reset();
    }
}

// ==================== OnlineSuperTrend Python Wrapper ====================

#[cfg(feature = "python")]
#[pyclass(name = "OnlineSuperTrend")]
pub struct PyOnlineSuperTrend {
    inner: OnlineSuperTrend,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOnlineSuperTrend {
    #[new]
    #[pyo3(signature = (period=10, multiplier=3.0))]
    pub fn new(period: usize, multiplier: f64) -> PyResult<Self> {
        Ok(Self {
            inner: OnlineSuperTrend::new(period, multiplier)?,
        })
    }

    /// Returns (supertrend_value, trend_direction) or None if not ready
    /// trend_direction: 1 = uptrend, -1 = downtrend
    pub fn update(&mut self, high: f64, low: f64, close: f64) -> PyResult<Option<(f64, i8)>> {
        Ok(self.inner.update(high, low, close)?)
    }

    pub fn reset(&mut self) {
        self.inner.reset();
    }

    pub fn current_trend(&self) -> i8 {
        self.inner.current_trend()
    }
}

// ==================== OnlineAdaptiveRSI Python Wrapper ====================

#[cfg(feature = "python")]
#[pyclass(name = "OnlineAdaptiveRSI")]
pub struct PyOnlineAdaptiveRSI {
    inner: OnlineAdaptiveRSI,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOnlineAdaptiveRSI {
    #[new]
    #[pyo3(signature = (min_period=7, max_period=21, volatility_period=14))]
    pub fn new(min_period: usize, max_period: usize, volatility_period: usize) -> PyResult<Self> {
        Ok(Self {
            inner: OnlineAdaptiveRSI::new(min_period, max_period, volatility_period)?,
        })
    }

    /// Returns (adaptive_rsi, effective_period) or None if not ready
    pub fn update(&mut self, value: f64) -> PyResult<Option<(f64, usize)>> {
        Ok(self.inner.update(value)?)
    }

    pub fn reset(&mut self) {
        self.inner.reset();
    }
}

// ==================== EnsembleResult Python Class ====================

#[cfg(feature = "python")]
#[pyclass(name = "EnsembleSignalResult")]
#[derive(Clone)]
pub struct PyEnsembleResult {
    #[pyo3(get)]
    pub signal: f64,
    #[pyo3(get)]
    pub rsi_contrib: f64,
    #[pyo3(get)]
    pub macd_contrib: f64,
    #[pyo3(get)]
    pub stoch_contrib: f64,
    #[pyo3(get)]
    pub trend_contrib: f64,
    #[pyo3(get)]
    pub confidence: f64,
}

#[cfg(feature = "python")]
impl From<EnsembleResult> for PyEnsembleResult {
    fn from(r: EnsembleResult) -> Self {
        Self {
            signal: r.signal,
            rsi_contrib: r.rsi_contrib,
            macd_contrib: r.macd_contrib,
            stoch_contrib: r.stoch_contrib,
            trend_contrib: r.trend_contrib,
            confidence: r.confidence,
        }
    }
}

// ==================== OnlineEnsembleSignal Python Wrapper ====================

#[cfg(feature = "python")]
#[pyclass(name = "OnlineEnsembleSignal")]
pub struct PyOnlineEnsembleSignal {
    inner: OnlineEnsembleSignal,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOnlineEnsembleSignal {
    #[new]
    #[pyo3(signature = (
        rsi_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        stoch_k=14,
        stoch_smooth=3,
        stoch_d=3,
        supertrend_period=10,
        supertrend_multiplier=3.0,
        weights=None,
        overbought=70.0,
        oversold=30.0
    ))]
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
        weights: Option<[f64; 4]>,
        overbought: f64,
        oversold: f64,
    ) -> PyResult<Self> {
        let w = weights.unwrap_or([1.0, 1.0, 1.0, 1.0]);
        Ok(Self {
            inner: OnlineEnsembleSignal::new(
                rsi_period,
                macd_fast,
                macd_slow,
                macd_signal,
                stoch_k,
                stoch_smooth,
                stoch_d,
                supertrend_period,
                supertrend_multiplier,
                w,
                overbought,
                oversold,
            )?,
        })
    }

    #[staticmethod]
    pub fn with_defaults() -> PyResult<Self> {
        Ok(Self {
            inner: OnlineEnsembleSignal::default_params()?,
        })
    }

    /// Returns EnsembleSignalResult or None if not ready
    pub fn update(
        &mut self,
        high: f64,
        low: f64,
        close: f64,
    ) -> PyResult<Option<PyEnsembleResult>> {
        Ok(self.inner.update(high, low, close)?.map(Into::into))
    }

    pub fn reset(&mut self) {
        self.inner.reset();
    }
}

// ==================== MLSuperTrendResult Python Class ====================

#[cfg(feature = "python")]
#[pyclass(name = "MLSuperTrendResult")]
#[derive(Clone)]
pub struct PyMLSuperTrendResult {
    #[pyo3(get)]
    pub value: f64,
    #[pyo3(get)]
    pub confirmed_trend: i8,
    #[pyo3(get)]
    pub raw_trend: i8,
    #[pyo3(get)]
    pub confidence: f64,
    #[pyo3(get)]
    pub effective_multiplier: f64,
}

#[cfg(feature = "python")]
impl From<MLSuperTrendResult> for PyMLSuperTrendResult {
    fn from(r: MLSuperTrendResult) -> Self {
        Self {
            value: r.value,
            confirmed_trend: r.confirmed_trend,
            raw_trend: r.raw_trend,
            confidence: r.confidence,
            effective_multiplier: r.effective_multiplier,
        }
    }
}

// ==================== OnlineMLSuperTrend Python Wrapper ====================

#[cfg(feature = "python")]
#[pyclass(name = "OnlineMLSuperTrend")]
pub struct PyOnlineMLSuperTrend {
    inner: OnlineMLSuperTrend,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOnlineMLSuperTrend {
    #[new]
    #[pyo3(signature = (period=10, base_multiplier=3.0, confirmation_bars=2, volatility_period=20))]
    pub fn new(
        period: usize,
        base_multiplier: f64,
        confirmation_bars: usize,
        volatility_period: usize,
    ) -> PyResult<Self> {
        Ok(Self {
            inner: OnlineMLSuperTrend::new(
                period,
                base_multiplier,
                confirmation_bars,
                volatility_period,
            )?,
        })
    }

    #[staticmethod]
    pub fn with_defaults() -> PyResult<Self> {
        Ok(Self {
            inner: OnlineMLSuperTrend::default_params()?,
        })
    }

    /// Returns MLSuperTrendResult or None if not ready
    pub fn update(
        &mut self,
        high: f64,
        low: f64,
        close: f64,
    ) -> PyResult<Option<PyMLSuperTrendResult>> {
        Ok(self.inner.update(high, low, close)?.map(Into::into))
    }

    pub fn reset(&mut self) {
        self.inner.reset();
    }

    pub fn confirmed_trend(&self) -> i8 {
        self.inner.confirmed_trend()
    }
}

// ==================== OnlineAISuperTrendML Python Wrapper ====================

/// Python 结果包装类
#[cfg(feature = "python")]
#[pyclass(name = "AISuperTrendMLResult")]
#[derive(Debug, Clone)]
pub struct PyAISuperTrendMLResult {
    #[pyo3(get)]
    pub supertrend: f64,
    #[pyo3(get)]
    pub direction: i8,
    #[pyo3(get)]
    pub trend_offset: f64,
    #[pyo3(get)]
    pub buy_signal: bool,
    #[pyo3(get)]
    pub sell_signal: bool,
    #[pyo3(get)]
    pub stop_loss: f64,
    #[pyo3(get)]
    pub take_profit: f64,
}

#[cfg(feature = "python")]
impl From<AISuperTrendMLResult> for PyAISuperTrendMLResult {
    fn from(r: AISuperTrendMLResult) -> Self {
        Self {
            supertrend: r.supertrend,
            direction: r.direction,
            trend_offset: r.trend_offset,
            buy_signal: r.buy_signal,
            sell_signal: r.sell_signal,
            stop_loss: r.stop_loss,
            take_profit: r.take_profit,
        }
    }
}

#[cfg(feature = "python")]
#[pyclass(name = "OnlineAISuperTrendML")]
pub struct PyOnlineAISuperTrendML {
    inner: OnlineAISuperTrendML,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyOnlineAISuperTrendML {
    #[new]
    #[pyo3(signature = (st_length=10, st_multiplier=3.0, lookback=10, train_window=200))]
    pub fn new(
        st_length: usize,
        st_multiplier: f64,
        lookback: usize,
        train_window: usize,
    ) -> PyResult<Self> {
        Ok(Self {
            inner: OnlineAISuperTrendML::new(st_length, st_multiplier, lookback, train_window)?,
        })
    }

    #[staticmethod]
    pub fn with_defaults() -> PyResult<Self> {
        Ok(Self {
            inner: OnlineAISuperTrendML::default_params()?,
        })
    }

    /// 更新并返回结果，预热期返回 None
    pub fn update(
        &mut self,
        high: f64,
        low: f64,
        close: f64,
    ) -> PyResult<Option<PyAISuperTrendMLResult>> {
        Ok(self.inner.update(high, low, close)?.map(Into::into))
    }

    pub fn reset(&mut self) {
        self.inner.reset();
    }

    pub fn is_ready(&self) -> bool {
        self.inner.is_ready()
    }

    pub fn direction(&self) -> i8 {
        self.inner.direction()
    }

    pub fn update_count(&self) -> usize {
        self.inner.update_count()
    }
}

// ==================== Module Registration ====================

#[cfg(feature = "python")]
pub fn register_streaming_classes(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Basic streaming calculators
    m.add_class::<PyOnlineSMA>()?;
    m.add_class::<PyOnlineEMA>()?;
    m.add_class::<PyOnlineRSI>()?;
    m.add_class::<PyOnlineATR>()?;
    m.add_class::<PyOnlineMACD>()?;
    m.add_class::<PyOnlineBollingerBands>()?;

    // New advanced streaming calculators
    m.add_class::<PyOnlineStochastic>()?;
    m.add_class::<PyOnlineSuperTrend>()?;
    m.add_class::<PyOnlineAdaptiveRSI>()?;
    m.add_class::<PyOnlineEnsembleSignal>()?;
    m.add_class::<PyEnsembleResult>()?;
    m.add_class::<PyOnlineMLSuperTrend>()?;
    m.add_class::<PyMLSuperTrendResult>()?;

    // AI SuperTrend ML (SFG)
    m.add_class::<PyOnlineAISuperTrendML>()?;
    m.add_class::<PyAISuperTrendMLResult>()?;

    Ok(())
}
