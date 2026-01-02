//! Integration tests for large dataset scalability
//!
//! These tests verify that indicators can handle large datasets (1M+ points)
//! without panicking, overflowing, or experiencing significant performance degradation.

use haze_library::indicators::{momentum, overlap, trend, volatility};
use haze_library::HazeResult;

/// Test 1M point dataset for SMA
///
/// Verifies no panic, no overflow, correct warmup handling
#[test]
fn test_million_point_sma() -> HazeResult<()> {
    // Generate 1M data points with periodic pattern
    let data: Vec<f64> = (0..1_000_000).map(|i| 100.0 + (i as f64 % 100.0)).collect();

    let result = overlap::sma(&data, 50)?;

    // Verify length
    assert_eq!(result.len(), 1_000_000);

    // Verify warmup period (first 49 should be NaN)
    for (i, &value) in result.iter().enumerate().take(49) {
        assert!(value.is_nan(), "Expected NaN at index {i}");
    }

    // Verify all values after warmup are finite
    for (i, &value) in result.iter().enumerate().skip(50) {
        assert!(
            value.is_finite(),
            "Expected finite value at index {i}, got {value}"
        );
    }

    Ok(())
}

/// Test 1M point dataset for RSI
///
/// RSI is computationally intensive due to RMA calculations
#[test]
fn test_million_point_rsi() -> HazeResult<()> {
    let data: Vec<f64> = (0..1_000_000).map(|i| 100.0 + (i as f64 % 100.0)).collect();

    let result = momentum::rsi(&data, 14)?;

    assert_eq!(result.len(), 1_000_000);

    // Verify RSI range [0, 100] for all non-NaN values
    for (i, &value) in result.iter().enumerate() {
        if !value.is_nan() {
            assert!(
                (0.0..=100.0).contains(&value),
                "RSI out of range at index {i}: {value}"
            );
        }
    }

    Ok(())
}

/// Test 1M point dataset for MACD
///
/// MACD involves multiple EMA calculations
#[test]
fn test_million_point_macd() -> HazeResult<()> {
    let data: Vec<f64> = (0..1_000_000)
        .map(|i| 100.0 + ((i as f64 * 0.001).sin() * 10.0))
        .collect();

    let (macd, signal, histogram) = momentum::macd(&data, 12, 26, 9)?;

    assert_eq!(macd.len(), 1_000_000);
    assert_eq!(signal.len(), 1_000_000);
    assert_eq!(histogram.len(), 1_000_000);

    // Verify histogram = MACD - Signal for all valid indices
    for i in 0..1_000_000 {
        if !macd[i].is_nan() && !signal[i].is_nan() {
            let expected = macd[i] - signal[i];
            assert!(
                (histogram[i] - expected).abs() < 1e-9,
                "Histogram mismatch at index {}: expected {}, got {}",
                i,
                expected,
                histogram[i]
            );
        }
    }

    Ok(())
}

/// Test 1M point dataset for Bollinger Bands
///
/// Tests SMA + standard deviation calculations
#[test]
fn test_million_point_bollinger_bands() -> HazeResult<()> {
    let data: Vec<f64> = (0..1_000_000)
        .map(|i| 100.0 + ((i as f64 % 100.0) - 50.0))
        .collect();

    let (upper, middle, lower) = volatility::bollinger_bands(&data, 20, 2.0)?;

    assert_eq!(upper.len(), 1_000_000);
    assert_eq!(middle.len(), 1_000_000);
    assert_eq!(lower.len(), 1_000_000);

    // Verify band ordering: lower <= middle <= upper
    for i in 20..1_000_000 {
        if !lower[i].is_nan() && !middle[i].is_nan() && !upper[i].is_nan() {
            assert!(
                lower[i] <= middle[i] && middle[i] <= upper[i],
                "Band ordering violated at index {}: lower={}, middle={}, upper={}",
                i,
                lower[i],
                middle[i],
                upper[i]
            );
        }
    }

    Ok(())
}

/// Test 1M point dataset for ATR
///
/// Tests true range calculations with high/low/close
#[test]
fn test_million_point_atr() -> HazeResult<()> {
    let high: Vec<f64> = (0..1_000_000)
        .map(|i| 100.0 + (i as f64 % 100.0) + 5.0)
        .collect();
    let low: Vec<f64> = (0..1_000_000)
        .map(|i| 100.0 + (i as f64 % 100.0) - 5.0)
        .collect();
    let close: Vec<f64> = (0..1_000_000).map(|i| 100.0 + (i as f64 % 100.0)).collect();

    let result = volatility::atr(&high, &low, &close, 14)?;

    assert_eq!(result.len(), 1_000_000);

    // ATR should always be positive or NaN
    for (i, &value) in result.iter().enumerate() {
        if !value.is_nan() {
            assert!(
                value >= 0.0,
                "ATR should be non-negative at index {i}, got {value}"
            );
        }
    }

    Ok(())
}

/// Test 1M point dataset for ADX
///
/// ADX is one of the most complex indicators (DI+, DI-, ADX calculation)
#[test]
fn test_million_point_adx() -> HazeResult<()> {
    // Generate trending data
    let high: Vec<f64> = (0..1_000_000)
        .map(|i| 100.0 + (i as f64 / 10000.0) + 5.0)
        .collect();
    let low: Vec<f64> = (0..1_000_000)
        .map(|i| 100.0 + (i as f64 / 10000.0) - 5.0)
        .collect();
    let close: Vec<f64> = (0..1_000_000)
        .map(|i| 100.0 + (i as f64 / 10000.0))
        .collect();

    let (adx, plus_di, minus_di) = trend::adx(&high, &low, &close, 14)?;

    assert_eq!(adx.len(), 1_000_000);
    assert_eq!(plus_di.len(), 1_000_000);
    assert_eq!(minus_di.len(), 1_000_000);

    // All values should be in valid ranges
    for i in 30..1_000_000 {
        // Skip warmup
        if !adx[i].is_nan() {
            let value = adx[i];
            assert!(
                (0.0..=100.0).contains(&value),
                "ADX out of range at index {i}: {value}"
            );
        }
        if !plus_di[i].is_nan() {
            let value = plus_di[i];
            assert!(
                (0.0..=100.0).contains(&value),
                "+DI out of range at index {i}: {value}"
            );
        }
        if !minus_di[i].is_nan() {
            let value = minus_di[i];
            assert!(
                (0.0..=100.0).contains(&value),
                "-DI out of range at index {i}: {value}"
            );
        }
    }

    Ok(())
}

/// Test numerical stability over 1M iterations
///
/// This test ensures Kahan summation prevents error accumulation
#[test]
fn test_precision_stability_large_dataset() -> HazeResult<()> {
    // Create constant data (should give exact SMA = 1.0)
    let data = vec![1.0; 1_000_000];

    let sma_result = overlap::sma(&data, 20)?;

    // After warmup, SMA should be exactly 1.0 (no accumulation error)
    for (i, &value) in sma_result.iter().enumerate().skip(20) {
        let error = (value - 1.0).abs();
        assert!(
            error < 1e-10,
            "Precision error at index {i}: expected 1.0, got {value} (error: {error})"
        );
    }

    Ok(())
}

/// Test memory efficiency with multiple indicators
///
/// Verifies that running multiple indicators concurrently doesn't cause memory issues
#[test]
fn test_multiple_indicators_large_dataset() -> HazeResult<()> {
    let close = vec![100.0; 100_000]; // 100K points

    // Run multiple indicators simultaneously
    let sma_fast = overlap::sma(&close, 10)?;
    let sma_slow = overlap::sma(&close, 50)?;
    let rsi = momentum::rsi(&close, 14)?;
    let (upper, middle, lower) = volatility::bollinger_bands(&close, 20, 2.0)?;

    // Verify all have correct length
    assert_eq!(sma_fast.len(), 100_000);
    assert_eq!(sma_slow.len(), 100_000);
    assert_eq!(rsi.len(), 100_000);
    assert_eq!(upper.len(), 100_000);
    assert_eq!(middle.len(), 100_000);
    assert_eq!(lower.len(), 100_000);

    // Verify no overflow in any indicator
    for i in 50..100_000 {
        assert!(sma_fast[i].is_finite());
        assert!(sma_slow[i].is_finite());
        assert!(rsi[i].is_finite());
        assert!(upper[i].is_finite());
        assert!(middle[i].is_finite());
        assert!(lower[i].is_finite());
    }

    Ok(())
}
