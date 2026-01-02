//! Integration tests for multi-indicator workflows
//!
//! These tests verify that indicators work correctly when combined,
//! simulating real trading strategies.

use haze_library::indicators::{momentum, overlap, trend, volatility};
use haze_library::HazeResult;

/// Test Bollinger Bands + RSI strategy
///
/// Strategy: Buy when RSI < 30 AND price below lower Bollinger Band
/// This tests that both indicators work together correctly
#[test]
fn test_bollinger_rsi_strategy() -> HazeResult<()> {
    // Simulate price data with oversold condition
    let close = vec![
        100.0, 102.0, 101.0, 99.0, 98.0, 97.0, 96.0, 95.0, 94.0, 93.0, // Downtrend
        92.0, 91.0, 90.0, 89.0, 88.0, 89.0, 90.0, 91.0, 92.0, 93.0, // Recovery
    ];

    let rsi = momentum::rsi(&close, 14)?;
    let (upper, middle, lower) = volatility::bollinger_bands(&close, 14, 2.0)?;

    // Verify all outputs have same length
    assert_eq!(rsi.len(), close.len());
    assert_eq!(upper.len(), close.len());
    assert_eq!(middle.len(), close.len());
    assert_eq!(lower.len(), close.len());

    // Verify warmup periods (first 13 values should be NaN for period=14)
    for i in 0..13 {
        assert!(rsi[i].is_nan(), "RSI warmup at index {i}");
        assert!(lower[i].is_nan(), "Bollinger lower warmup at index {i}");
    }

    // Verify calculations are finite (no overflow)
    for i in 14..close.len() {
        assert!(rsi[i].is_finite(), "RSI at index {i}");
        assert!(upper[i].is_finite(), "Upper band at index {i}");
        assert!(lower[i].is_finite(), "Lower band at index {i}");

        // Verify Bollinger Bands ordering
        assert!(
            lower[i] <= middle[i] && middle[i] <= upper[i],
            "Bollinger band ordering violated at index {}: lower={}, middle={}, upper={}",
            i,
            lower[i],
            middle[i],
            upper[i]
        );
    }

    // Verify RSI range [0, 100]
    for (i, &value) in rsi.iter().enumerate().skip(14) {
        assert!(
            (0.0..=100.0).contains(&value),
            "RSI out of range at index {i}: {value}"
        );
    }

    Ok(())
}

/// Test MACD signal crossover detection
///
/// Strategy: Bullish when MACD crosses above signal line
/// This tests histogram calculation and crossover detection
#[test]
fn test_macd_signal_crossover() -> HazeResult<()> {
    // Generate sinusoidal price data to create crossovers
    let close: Vec<f64> = (0..100)
        .map(|i| 100.0 + (i as f64 * 0.1).sin() * 10.0)
        .collect();

    let (macd, signal, histogram) = momentum::macd(&close, 12, 26, 9)?;

    // Verify output lengths
    assert_eq!(macd.len(), close.len());
    assert_eq!(signal.len(), close.len());
    assert_eq!(histogram.len(), close.len());

    // Find crossover points (histogram changes sign)
    let mut crossovers = vec![];
    for i in 1..histogram.len() {
        if !histogram[i - 1].is_nan() && !histogram[i].is_nan() {
            if histogram[i - 1] < 0.0 && histogram[i] > 0.0 {
                crossovers.push(("bullish", i));
            } else if histogram[i - 1] > 0.0 && histogram[i] < 0.0 {
                crossovers.push(("bearish", i));
            }
        }
    }

    // Should have at least some crossovers in sinusoidal data
    assert!(
        !crossovers.is_empty(),
        "Expected crossovers in sinusoidal data, but found none"
    );

    // Verify histogram = MACD - Signal
    for i in 0..close.len() {
        if !macd[i].is_nan() && !signal[i].is_nan() {
            let expected_histogram = macd[i] - signal[i];
            assert!(
                (histogram[i] - expected_histogram).abs() < 1e-10,
                "Histogram mismatch at index {}: expected {}, got {}",
                i,
                expected_histogram,
                histogram[i]
            );
        }
    }

    Ok(())
}

/// Test trend confirmation with ADX + moving averages
///
/// Strategy: Strong trend when ADX > 25 AND SMA crossover
/// This tests multi-indicator trend confirmation
#[test]
fn test_trend_confirmation_adx_sma() -> HazeResult<()> {
    // Simulate trending market
    let high: Vec<f64> = (0..50).map(|i| 100.0 + i as f64 + 1.0).collect();
    let low: Vec<f64> = (0..50).map(|i| 100.0 + i as f64 - 1.0).collect();
    let close: Vec<f64> = (0..50).map(|i| 100.0 + i as f64).collect(); // Strong uptrend

    // Calculate ADX to measure trend strength
    // ADX returns (adx_values, plus_di, minus_di)
    let (adx_values, _plus_di, _minus_di) = trend::adx(&high, &low, &close, 14)?;

    // Calculate SMA crossover (fast vs slow)
    let sma_fast = overlap::sma(&close, 5)?;
    let sma_slow = overlap::sma(&close, 20)?;

    assert_eq!(adx_values.len(), close.len());
    assert_eq!(sma_fast.len(), close.len());
    assert_eq!(sma_slow.len(), close.len());

    // In strong uptrend, ADX should eventually be > 25
    let mut found_strong_trend = false;
    for i in 20..close.len() {
        if !adx_values[i].is_nan() && adx_values[i] > 25.0 {
            found_strong_trend = true;
            // In uptrend, fast SMA should be above slow SMA
            if !sma_fast[i].is_nan() && !sma_slow[i].is_nan() {
                assert!(
                    sma_fast[i] > sma_slow[i],
                    "Expected fast SMA > slow SMA in uptrend at index {i}"
                );
            }
        }
    }

    assert!(
        found_strong_trend,
        "Expected ADX > 25 in strong uptrend, but never found it"
    );

    Ok(())
}

/// Test multi-timeframe analysis
///
/// This tests using the same indicator with different periods
/// to simulate multi-timeframe analysis
#[test]
fn test_multi_timeframe_rsi() -> HazeResult<()> {
    let close: Vec<f64> = (0..100).map(|i| 100.0 + (i as f64 % 20.0)).collect();

    // Short, medium, and long timeframes
    let rsi_short = momentum::rsi(&close, 7)?;
    let rsi_medium = momentum::rsi(&close, 14)?;
    let rsi_long = momentum::rsi(&close, 21)?;

    assert_eq!(rsi_short.len(), close.len());
    assert_eq!(rsi_medium.len(), close.len());
    assert_eq!(rsi_long.len(), close.len());

    // Verify all RSI values are in valid range
    for i in 21..close.len() {
        // After longest warmup period
        assert!((0.0..=100.0).contains(&rsi_short[i]));
        assert!((0.0..=100.0).contains(&rsi_medium[i]));
        assert!((0.0..=100.0).contains(&rsi_long[i]));
    }

    // Short-period RSI should be more reactive (higher variance)
    // This is a qualitative test of indicator behavior
    let variance = |values: &[f64]| -> f64 {
        let valid_values: Vec<f64> = values.iter().filter(|v| !v.is_nan()).copied().collect();
        let mean = valid_values.iter().sum::<f64>() / valid_values.len() as f64;
        valid_values.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / valid_values.len() as f64
    };

    let var_short = variance(&rsi_short);
    let var_long = variance(&rsi_long);

    // Short period should have higher variance (more reactive)
    assert!(
        var_short > var_long,
        "Expected short-period RSI to be more reactive than long-period: var_short={var_short}, var_long={var_long}"
    );

    Ok(())
}

/// Test stochastic oscillator with RSI divergence
///
/// This tests combining oscillators for divergence detection
#[test]
fn test_oscillator_combination() -> HazeResult<()> {
    let high: Vec<f64> = (0..50).map(|i| 100.0 + (i as f64 % 20.0)).collect();
    let low: Vec<f64> = (0..50).map(|i| 95.0 + (i as f64 % 20.0)).collect();
    let close: Vec<f64> = (0..50).map(|i| 98.0 + (i as f64 % 20.0)).collect();

    let (stoch_k, stoch_d) = momentum::stochastic(&high, &low, &close, 14, 3, 3)?;
    let rsi = momentum::rsi(&close, 14)?;

    assert_eq!(stoch_k.len(), close.len());
    assert_eq!(stoch_d.len(), close.len());
    assert_eq!(rsi.len(), close.len());

    // Verify both oscillators are in valid ranges
    for i in 20..close.len() {
        if !stoch_k[i].is_nan() {
            let value = stoch_k[i];
            assert!(
                (0.0..=100.0).contains(&value),
                "Stochastic %K out of range at index {i}: {value}"
            );
        }
        if !stoch_d[i].is_nan() {
            let value = stoch_d[i];
            assert!(
                (0.0..=100.0).contains(&value),
                "Stochastic %D out of range at index {i}: {value}"
            );
        }
        if !rsi[i].is_nan() {
            let value = rsi[i];
            assert!(
                (0.0..=100.0).contains(&value),
                "RSI out of range at index {i}: {value}"
            );
        }
    }

    Ok(())
}
