//! Integration tests for parallel computation correctness
//!
//! These tests verify that Rayon parallel processing produces identical
//! results to sequential processing for all indicators.

use haze_library::indicators::{momentum, overlap, trend, volatility};
use haze_library::HazeResult;
use rayon::prelude::*;

/// Helper function to generate test dataset for a symbol
fn generate_symbol_data(symbol_id: usize, length: usize) -> Vec<f64> {
    (0..length)
        .map(|i| 100.0 + (symbol_id as f64 * 10.0) + ((i + symbol_id) as f64 % 50.0))
        .collect()
}

/// Helper function to generate OHLC data for a symbol
fn generate_ohlc_data(symbol_id: usize, length: usize) -> (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>) {
    let close = generate_symbol_data(symbol_id, length);
    let high: Vec<f64> = close.iter().map(|&c| c + 2.0).collect();
    let low: Vec<f64> = close.iter().map(|&c| c - 2.0).collect();
    let open: Vec<f64> = close.iter().map(|&c| c + 0.5).collect();
    (high, low, close, open)
}

/// Test parallel RSI computation matches sequential
#[test]
fn test_parallel_rsi_correctness() -> HazeResult<()> {
    let symbols_data: Vec<Vec<f64>> = (0..100).map(|i| generate_symbol_data(i, 1000)).collect();

    // Sequential computation
    let sequential: Vec<Vec<f64>> = symbols_data
        .iter()
        .map(|data| momentum::rsi(data, 14).unwrap())
        .collect();

    // Parallel computation using Rayon
    let parallel: Vec<Vec<f64>> = symbols_data
        .par_iter()
        .map(|data| momentum::rsi(data, 14).unwrap())
        .collect();

    // Results should be identical
    assert_eq!(
        sequential.len(),
        parallel.len(),
        "Different number of results"
    );

    for (symbol_id, (seq, par)) in sequential.iter().zip(parallel.iter()).enumerate() {
        assert_eq!(seq.len(), par.len(), "Symbol {symbol_id} length mismatch");

        for (i, (s, p)) in seq.iter().zip(par.iter()).enumerate() {
            if s.is_nan() {
                assert!(
                    p.is_nan(),
                    "Symbol {symbol_id}, index {i}: sequential is NaN, parallel is {p}"
                );
            } else {
                let diff = (s - p).abs();
                assert!(
                    diff < 1e-12,
                    "Symbol {symbol_id}, index {i}: sequential={s}, parallel={p}, diff={diff}"
                );
            }
        }
    }

    Ok(())
}

/// Test parallel SMA computation matches sequential
#[test]
fn test_parallel_sma_correctness() -> HazeResult<()> {
    let symbols_data: Vec<Vec<f64>> = (0..100).map(|i| generate_symbol_data(i, 1000)).collect();

    // Sequential
    let sequential: Vec<Vec<f64>> = symbols_data
        .iter()
        .map(|data| overlap::sma(data, 20).unwrap())
        .collect();

    // Parallel
    let parallel: Vec<Vec<f64>> = symbols_data
        .par_iter()
        .map(|data| overlap::sma(data, 20).unwrap())
        .collect();

    // Verify identical results
    for (symbol_id, (seq, par)) in sequential.iter().zip(parallel.iter()).enumerate() {
        for (i, (s, p)) in seq.iter().zip(par.iter()).enumerate() {
            if s.is_nan() {
                assert!(p.is_nan(), "Symbol {symbol_id}, index {i}: NaN mismatch");
            } else {
                let diff = (s - p).abs();
                assert!(diff < 1e-12, "Symbol {symbol_id}, index {i}: diff={diff}");
            }
        }
    }

    Ok(())
}

/// Test parallel MACD computation matches sequential
#[test]
fn test_parallel_macd_correctness() -> HazeResult<()> {
    let symbols_data: Vec<Vec<f64>> = (0..50).map(|i| generate_symbol_data(i, 1000)).collect();

    // Sequential
    let sequential: Vec<(Vec<f64>, Vec<f64>, Vec<f64>)> = symbols_data
        .iter()
        .map(|data| momentum::macd(data, 12, 26, 9).unwrap())
        .collect();

    // Parallel
    let parallel: Vec<(Vec<f64>, Vec<f64>, Vec<f64>)> = symbols_data
        .par_iter()
        .map(|data| momentum::macd(data, 12, 26, 9).unwrap())
        .collect();

    // Verify all three outputs (MACD, Signal, Histogram)
    for (symbol_id, (seq, par)) in sequential.iter().zip(parallel.iter()).enumerate() {
        let (seq_macd, seq_signal, seq_hist) = seq;
        let (par_macd, par_signal, par_hist) = par;

        // Check MACD
        for (i, (&s, &p)) in seq_macd.iter().zip(par_macd.iter()).enumerate() {
            if s.is_nan() {
                assert!(
                    p.is_nan(),
                    "Symbol {symbol_id}, MACD index {i}: NaN mismatch"
                );
            } else {
                let diff = (s - p).abs();
                assert!(
                    diff < 1e-10,
                    "Symbol {symbol_id}, MACD index {i}: diff={diff}"
                );
            }
        }

        // Check Signal
        for (i, (&s, &p)) in seq_signal.iter().zip(par_signal.iter()).enumerate() {
            if s.is_nan() {
                assert!(
                    p.is_nan(),
                    "Symbol {symbol_id}, Signal index {i}: NaN mismatch"
                );
            } else {
                let diff = (s - p).abs();
                assert!(
                    diff < 1e-10,
                    "Symbol {symbol_id}, Signal index {i}: diff={diff}"
                );
            }
        }

        // Check Histogram
        for (i, (&s, &p)) in seq_hist.iter().zip(par_hist.iter()).enumerate() {
            if s.is_nan() {
                assert!(
                    p.is_nan(),
                    "Symbol {symbol_id}, Histogram index {i}: NaN mismatch"
                );
            } else {
                let diff = (s - p).abs();
                assert!(
                    diff < 1e-10,
                    "Symbol {symbol_id}, Histogram index {i}: diff={diff}"
                );
            }
        }
    }

    Ok(())
}

/// Test parallel Bollinger Bands computation matches sequential
#[test]
fn test_parallel_bollinger_bands_correctness() -> HazeResult<()> {
    let symbols_data: Vec<Vec<f64>> = (0..50).map(|i| generate_symbol_data(i, 1000)).collect();

    // Sequential
    let sequential: Vec<(Vec<f64>, Vec<f64>, Vec<f64>)> = symbols_data
        .iter()
        .map(|data| volatility::bollinger_bands(data, 20, 2.0).unwrap())
        .collect();

    // Parallel
    let parallel: Vec<(Vec<f64>, Vec<f64>, Vec<f64>)> = symbols_data
        .par_iter()
        .map(|data| volatility::bollinger_bands(data, 20, 2.0).unwrap())
        .collect();

    // Verify all three outputs (Upper, Middle, Lower)
    for (symbol_id, (seq, par)) in sequential.iter().zip(parallel.iter()).enumerate() {
        let (seq_upper, seq_middle, seq_lower) = seq;
        let (par_upper, par_middle, par_lower) = par;

        for i in 0..seq_upper.len() {
            // Upper
            if seq_upper[i].is_nan() {
                assert!(par_upper[i].is_nan());
            } else {
                let diff = (seq_upper[i] - par_upper[i]).abs();
                assert!(
                    diff < 1e-10,
                    "Symbol {symbol_id}, Upper index {i}: diff={diff}"
                );
            }

            // Middle
            if seq_middle[i].is_nan() {
                assert!(par_middle[i].is_nan());
            } else {
                let diff = (seq_middle[i] - par_middle[i]).abs();
                assert!(
                    diff < 1e-10,
                    "Symbol {symbol_id}, Middle index {i}: diff={diff}"
                );
            }

            // Lower
            if seq_lower[i].is_nan() {
                assert!(par_lower[i].is_nan());
            } else {
                let diff = (seq_lower[i] - par_lower[i]).abs();
                assert!(
                    diff < 1e-10,
                    "Symbol {symbol_id}, Lower index {i}: diff={diff}"
                );
            }
        }
    }

    Ok(())
}

/// Test parallel ATR computation matches sequential
#[test]
fn test_parallel_atr_correctness() -> HazeResult<()> {
    let symbols_ohlc: Vec<(Vec<f64>, Vec<f64>, Vec<f64>)> = (0..50)
        .map(|i| {
            let (high, low, close, _) = generate_ohlc_data(i, 1000);
            (high, low, close)
        })
        .collect();

    // Sequential
    let sequential: Vec<Vec<f64>> = symbols_ohlc
        .iter()
        .map(|(h, l, c)| volatility::atr(h, l, c, 14).unwrap())
        .collect();

    // Parallel
    let parallel: Vec<Vec<f64>> = symbols_ohlc
        .par_iter()
        .map(|(h, l, c)| volatility::atr(h, l, c, 14).unwrap())
        .collect();

    // Verify results
    for (symbol_id, (seq, par)) in sequential.iter().zip(parallel.iter()).enumerate() {
        for (i, (&s, &p)) in seq.iter().zip(par.iter()).enumerate() {
            if s.is_nan() {
                assert!(p.is_nan());
            } else {
                let diff = (s - p).abs();
                assert!(diff < 1e-10, "Symbol {symbol_id}, index {i}: diff={diff}");
            }
        }
    }

    Ok(())
}

/// Test parallel ADX computation matches sequential
#[test]
fn test_parallel_adx_correctness() -> HazeResult<()> {
    let symbols_ohlc: Vec<(Vec<f64>, Vec<f64>, Vec<f64>)> = (0..30)
        .map(|i| {
            let (high, low, close, _) = generate_ohlc_data(i, 500);
            (high, low, close)
        })
        .collect();

    // Sequential
    let sequential: Vec<(Vec<f64>, Vec<f64>, Vec<f64>)> = symbols_ohlc
        .iter()
        .map(|(h, l, c)| trend::adx(h, l, c, 14).unwrap())
        .collect();

    // Parallel
    let parallel: Vec<(Vec<f64>, Vec<f64>, Vec<f64>)> = symbols_ohlc
        .par_iter()
        .map(|(h, l, c)| trend::adx(h, l, c, 14).unwrap())
        .collect();

    // Verify ADX, +DI, -DI
    for (seq, par) in sequential.iter().zip(parallel.iter()) {
        let (seq_adx, seq_plus, seq_minus) = seq;
        let (par_adx, par_plus, par_minus) = par;

        for i in 0..seq_adx.len() {
            // ADX
            if seq_adx[i].is_nan() {
                assert!(par_adx[i].is_nan());
            } else {
                assert!((seq_adx[i] - par_adx[i]).abs() < 1e-10);
            }

            // +DI
            if seq_plus[i].is_nan() {
                assert!(par_plus[i].is_nan());
            } else {
                assert!((seq_plus[i] - par_plus[i]).abs() < 1e-10);
            }

            // -DI
            if seq_minus[i].is_nan() {
                assert!(par_minus[i].is_nan());
            } else {
                assert!((seq_minus[i] - par_minus[i]).abs() < 1e-10);
            }
        }
    }

    Ok(())
}

/// Test parallel Stochastic computation matches sequential
#[test]
fn test_parallel_stochastic_correctness() -> HazeResult<()> {
    let symbols_ohlc: Vec<(Vec<f64>, Vec<f64>, Vec<f64>)> = (0..50)
        .map(|i| {
            let (high, low, close, _) = generate_ohlc_data(i, 500);
            (high, low, close)
        })
        .collect();

    // Sequential
    let sequential: Vec<(Vec<f64>, Vec<f64>)> = symbols_ohlc
        .iter()
        .map(|(h, l, c)| momentum::stochastic(h, l, c, 14, 3, 3).unwrap())
        .collect();

    // Parallel
    let parallel: Vec<(Vec<f64>, Vec<f64>)> = symbols_ohlc
        .par_iter()
        .map(|(h, l, c)| momentum::stochastic(h, l, c, 14, 3, 3).unwrap())
        .collect();

    // Verify %K and %D
    for (seq, par) in sequential.iter().zip(parallel.iter()) {
        let (seq_k, seq_d) = seq;
        let (par_k, par_d) = par;

        for i in 0..seq_k.len() {
            if seq_k[i].is_nan() {
                assert!(par_k[i].is_nan());
            } else {
                assert!((seq_k[i] - par_k[i]).abs() < 1e-10);
            }

            if seq_d[i].is_nan() {
                assert!(par_d[i].is_nan());
            } else {
                assert!((seq_d[i] - par_d[i]).abs() < 1e-10);
            }
        }
    }

    Ok(())
}

/// Test that parallel processing doesn't cause race conditions
///
/// This test runs the same computation 10 times in parallel and verifies
/// all results are identical
#[test]
fn test_parallel_determinism() -> HazeResult<()> {
    let data = generate_symbol_data(0, 1000);

    // Run RSI 10 times in parallel
    let results: Vec<Vec<f64>> = (0..10)
        .into_par_iter()
        .map(|_| momentum::rsi(&data, 14).unwrap())
        .collect();

    // All results should be identical
    let first = &results[0];
    for (run_id, result) in results.iter().enumerate().skip(1) {
        for (i, (&expected, &actual)) in first.iter().zip(result.iter()).enumerate() {
            if expected.is_nan() {
                assert!(
                    actual.is_nan(),
                    "Run {run_id} index {i}: expected NaN, got {actual}"
                );
            } else {
                let diff = (expected - actual).abs();
                assert!(
                    diff < 1e-15,
                    "Run {run_id} index {i}: expected {expected}, got {actual}, diff={diff}"
                );
            }
        }
    }

    Ok(())
}
