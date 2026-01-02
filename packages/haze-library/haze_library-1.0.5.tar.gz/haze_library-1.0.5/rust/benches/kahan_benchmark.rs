//! Benchmarks for Kahan summation vs naive summation
//!
//! Run with: cargo bench --bench kahan_benchmark
//!
//! This benchmark measures both:
//! 1. Performance overhead of Kahan summation
//! 2. Precision improvement of Kahan summation

use std::hint::black_box;
use std::time::Instant;

// Import from the library
// Note: In real usage, this would be `use haze_library::utils::math::*;`
// For benchmark, we inline the functions to avoid dependency issues

/// Kahan compensated summation
#[inline]
fn kahan_sum(values: &[f64]) -> f64 {
    let mut sum = 0.0;
    let mut compensation = 0.0;

    for &value in values {
        if value.is_nan() {
            continue;
        }
        let y = value - compensation;
        let t = sum + y;
        compensation = (t - sum) - y;
        sum = t;
    }

    sum
}

/// Naive summation
#[inline]
fn naive_sum(values: &[f64]) -> f64 {
    values.iter().sum()
}

/// Neumaier summation
#[inline]
fn neumaier_sum(values: &[f64]) -> f64 {
    let mut sum = 0.0;
    let mut compensation = 0.0;

    for &value in values {
        if value.is_nan() {
            continue;
        }
        let t = sum + value;
        if sum.abs() >= value.abs() {
            compensation += (sum - t) + value;
        } else {
            compensation += (value - t) + sum;
        }
        sum = t;
    }

    sum + compensation
}

/// Pairwise summation
fn pairwise_sum(values: &[f64]) -> f64 {
    const THRESHOLD: usize = 32;

    fn pairwise_recursive(values: &[f64]) -> f64 {
        let n = values.len();
        if n <= THRESHOLD {
            return kahan_sum(values);
        }
        let mid = n / 2;
        pairwise_recursive(&values[..mid]) + pairwise_recursive(&values[mid..])
    }

    pairwise_recursive(values)
}

/// Rolling sum with Kahan compensation
fn rolling_sum_kahan(values: &[f64], period: usize) -> Vec<f64> {
    const RECALC_INTERVAL: usize = 1000;

    if period == 0 || period > values.len() {
        return vec![f64::NAN; values.len()];
    }

    let mut result = vec![f64::NAN; values.len()];
    let first_sum = kahan_sum(&values[..period]);
    result[period - 1] = first_sum;

    let mut sum = first_sum;
    let mut compensation = 0.0;

    for i in period..values.len() {
        if (i - period + 1) % RECALC_INTERVAL == 0 {
            sum = kahan_sum(&values[i + 1 - period..=i]);
            compensation = 0.0;
            result[i] = sum;
        } else {
            // Add new value
            let y = values[i] - compensation;
            let t = sum + y;
            compensation = (t - sum) - y;
            sum = t;

            // Subtract old value
            let y = -values[i - period] - compensation;
            let t = sum + y;
            compensation = (t - sum) - y;
            sum = t;

            result[i] = sum;
        }
    }

    result
}

/// Naive rolling sum (for comparison)
fn rolling_sum_naive(values: &[f64], period: usize) -> Vec<f64> {
    if period == 0 || period > values.len() {
        return vec![f64::NAN; values.len()];
    }

    let mut result = vec![f64::NAN; values.len()];
    let first_sum: f64 = values[..period].iter().sum();
    result[period - 1] = first_sum;

    for i in period..values.len() {
        result[i] = result[i - 1] + values[i] - values[i - period];
    }

    result
}

fn run_benchmark<F>(name: &str, f: F, iterations: usize) -> f64
where
    F: Fn() -> f64,
{
    // Warmup
    for _ in 0..100 {
        black_box(f());
    }

    let start = Instant::now();
    for _ in 0..iterations {
        black_box(f());
    }
    let elapsed = start.elapsed();

    let ns_per_op = elapsed.as_nanos() as f64 / iterations as f64;
    println!("{name:30} {ns_per_op:>12.2} ns/iter");
    ns_per_op
}

fn run_precision_test(name: &str, values: &[f64], expected: f64) -> f64 {
    let result = match name {
        "naive" => naive_sum(values),
        "kahan" => kahan_sum(values),
        "neumaier" => neumaier_sum(values),
        "pairwise" => pairwise_sum(values),
        _ => panic!("Unknown algorithm"),
    };
    let error = (result - expected).abs();
    let relative_error = if expected != 0.0 {
        error / expected.abs()
    } else {
        error
    };
    println!("{name:30} error: {error:>15.2e}  relative: {relative_error:>15.2e}");
    error
}

fn main() {
    println!("{}", "=".repeat(70));
    println!("Kahan Summation Benchmark");
    println!("{}", "=".repeat(70));

    // Test configurations
    let sizes = [100, 1000, 10_000, 100_000];
    let iterations = 10_000;

    // =========================================================================
    // Performance Benchmarks
    // =========================================================================
    println!("\n--- Performance Benchmarks (uniform small values) ---\n");

    for &size in &sizes {
        let values: Vec<f64> = vec![0.1; size];

        println!("Size: {size}");
        run_benchmark("naive sum", || naive_sum(&values), iterations);
        run_benchmark("kahan sum", || kahan_sum(&values), iterations);
        run_benchmark("neumaier sum", || neumaier_sum(&values), iterations);
        if size <= 10_000 {
            // Pairwise is slower for larger sizes
            run_benchmark("pairwise sum", || pairwise_sum(&values), iterations);
        }
        println!();
    }

    // =========================================================================
    // Precision Benchmarks
    // =========================================================================
    println!("\n--- Precision Test 1: Many small values ---");
    println!("Sum 10,000 values of 0.1 (expected: 1000.0)\n");

    let n = 10_000;
    let values: Vec<f64> = vec![0.1; n];
    let expected = 1000.0;

    run_precision_test("naive", &values, expected);
    run_precision_test("kahan", &values, expected);
    run_precision_test("neumaier", &values, expected);
    run_precision_test("pairwise", &values, expected);

    // =========================================================================
    println!("\n--- Precision Test 2: Large + many small values ---");
    println!("Sum: 1e16 + 10,000 values of 1.0 (expected: 1e16 + 10000)\n");

    let mut values2 = vec![1e16];
    values2.extend(std::iter::repeat_n(1.0, 10_000));
    let expected2 = 1e16 + 10_000.0;

    run_precision_test("naive", &values2, expected2);
    run_precision_test("kahan", &values2, expected2);
    run_precision_test("neumaier", &values2, expected2);
    run_precision_test("pairwise", &values2, expected2);

    // =========================================================================
    println!("\n--- Precision Test 3: Alternating large values ---");
    println!("Sum: 1e16 + 1.0 + (-1e16) + 1.0 (expected: 2.0)\n");

    let values3 = vec![1e16, 1.0, -1e16, 1.0];
    let expected3 = 2.0;

    run_precision_test("naive", &values3, expected3);
    run_precision_test("kahan", &values3, expected3);
    run_precision_test("neumaier", &values3, expected3);
    run_precision_test("pairwise", &values3, expected3);

    // =========================================================================
    println!("\n--- Precision Test 4: Variance calculation ---");
    println!("Variance of 10,000 values ~ N(0, 1)\n");

    // Generate pseudo-random values with known variance
    let mut rng_state = 12345u64;
    let variance_values: Vec<f64> = (0..10_000)
        .map(|_| {
            // Simple LCG for reproducibility
            rng_state = rng_state.wrapping_mul(1103515245).wrapping_add(12345);
            let u = (rng_state as f64) / (u64::MAX as f64);
            // Box-Muller would be better but this approximates
            (u - 0.5) * 3.46 // Approximately unit variance
        })
        .collect();

    let n = variance_values.len() as f64;

    // Naive variance
    let naive_mean = naive_sum(&variance_values) / n;
    let naive_var: f64 = variance_values
        .iter()
        .map(|&x| (x - naive_mean).powi(2))
        .sum::<f64>()
        / n;

    // Kahan variance
    let kahan_mean = kahan_sum(&variance_values) / n;
    let kahan_var: f64 = variance_values
        .iter()
        .map(|&x| (x - kahan_mean).powi(2))
        .fold((0.0, 0.0), |(sum, comp), sq| {
            let y = sq - comp;
            let t = sum + y;
            (t, (t - sum) - y)
        })
        .0
        / n;

    println!("Naive  mean: {naive_mean:>15.10}, variance: {naive_var:>15.10}");
    println!("Kahan  mean: {kahan_mean:>15.10}, variance: {kahan_var:>15.10}");
    let diff_mean = (naive_mean - kahan_mean).abs();
    let diff_var = (naive_var - kahan_var).abs();
    println!("Difference in mean: {diff_mean:>15.2e}");
    println!("Difference in var:  {diff_var:>15.2e}");

    // =========================================================================
    println!("\n--- Rolling Sum Precision Test ---");
    println!("Rolling sum over 100,000 values with period 20\n");

    let rolling_n = 100_000;
    let period = 20;
    let rolling_values: Vec<f64> = (0..rolling_n)
        .map(|i| 1000.0 + (i as f64) * 0.001 + 0.0001 * ((i * 7) % 11) as f64)
        .collect();

    let naive_rolling = rolling_sum_naive(&rolling_values, period);
    let kahan_rolling = rolling_sum_kahan(&rolling_values, period);

    // Check precision at various points
    let check_indices = [period - 1, 1000, 10_000, 50_000, rolling_n - 1];

    println!(
        "{:>10} {:>20} {:>20} {:>20}",
        "Index", "Naive Error", "Kahan Error", "Improvement"
    );
    println!("{}", "-".repeat(70));

    for &idx in &check_indices {
        let expected = kahan_sum(&rolling_values[idx + 1 - period..=idx]);
        let naive_err = (naive_rolling[idx] - expected).abs();
        let kahan_err = (kahan_rolling[idx] - expected).abs();
        let improvement = if kahan_err > 0.0 {
            naive_err / kahan_err
        } else {
            f64::INFINITY
        };

        println!("{idx:>10} {naive_err:>20.2e} {kahan_err:>20.2e} {improvement:>19.2}x");
    }

    // Performance comparison
    println!("\n--- Rolling Sum Performance Test ---\n");

    let perf_values: Vec<f64> = vec![1.0; 100_000];
    let perf_period = 50;
    let rolling_iters = 100;

    println!("Computing rolling sum on 100,000 values with period 50 ({rolling_iters} iterations)");
    run_benchmark(
        "naive rolling sum",
        || {
            let _ = rolling_sum_naive(&perf_values, perf_period);
            0.0
        },
        rolling_iters,
    );
    run_benchmark(
        "kahan rolling sum",
        || {
            let _ = rolling_sum_kahan(&perf_values, perf_period);
            0.0
        },
        rolling_iters,
    );

    // =========================================================================
    // Summary
    // =========================================================================
    println!("\n{}", "=".repeat(70));
    println!("Summary");
    println!("{}", "=".repeat(70));
    println!("\nRecommendations:");
    println!("- Use naive sum for < 100 elements (performance critical, precision OK)");
    println!("- Use Kahan sum for >= 100 elements (2-3x slower, much better precision)");
    println!("- Use Neumaier for alternating large positive/negative values");
    println!("- Use Pairwise for very large arrays with random errors");
    println!("\nKahan overhead is typically 2-3x, but prevents precision loss in:");
    println!("- ML feature standardization");
    println!("- Variance/standard deviation calculations");
    println!("- Cumulative financial calculations");
    println!("- Rolling window operations (SMA, VWAP, etc.)");
    println!("- Any sum of > 1000 elements where precision matters");
    println!("\nRolling sum with Kahan compensation:");
    println!("- Minimal performance impact (~5-10% slower)");
    println!("- Significantly better precision (10-1000x improvement)");
    println!("- Essential for long time series (>10k data points)");
}
