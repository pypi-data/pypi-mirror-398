use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};

// Note: We inline indicator implementations for benchmarking
// In production, these would be imported from haze_library::indicators::overlap

/// Simple Moving Average
#[inline]
fn sma(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut result = vec![f64::NAN; n];

    if period == 0 || period > n {
        return result;
    }

    for i in (period - 1)..n {
        let sum: f64 = values[i - period + 1..=i].iter().sum();
        result[i] = sum / period as f64;
    }

    result
}

/// Exponential Moving Average
#[inline]
fn ema(values: &[f64], period: usize) -> Vec<f64> {
    let n = values.len();
    let mut result = vec![f64::NAN; n];

    if period == 0 || period > n {
        return result;
    }

    let alpha = 2.0 / (period as f64 + 1.0);

    // First value is SMA
    let sum: f64 = values[..period].iter().sum();
    result[period - 1] = sum / period as f64;

    // Subsequent values use EMA formula
    for i in period..n {
        result[i] = alpha * values[i] + (1.0 - alpha) * result[i - 1];
    }

    result
}

/// Benchmark SMA with large numbers and small increments
/// This tests numerical stability with values like 1e10 + small variations
fn benchmark_sma_large_numbers(c: &mut Criterion) {
    let mut group = c.benchmark_group("sma_large_numbers");

    // Test different data sizes
    for size in [1_000, 10_000, 100_000].iter() {
        let data: Vec<f64> = (0..*size).map(|i| 1e10 + (i as f64) * 1e-5).collect();

        group.bench_with_input(BenchmarkId::from_parameter(size), size, |b, _| {
            b.iter(|| sma(black_box(&data), black_box(100)))
        });
    }

    group.finish();
}

/// Benchmark EMA with long sequences
/// Tests cumulative error accumulation over many iterations
fn benchmark_ema_long_sequence(c: &mut Criterion) {
    let mut group = c.benchmark_group("ema_long_sequence");

    for size in [10_000, 100_000, 1_000_000].iter() {
        let data: Vec<f64> = (0..*size)
            .map(|i| 100.0 + (i as f64 * 0.01).sin())
            .collect();

        group.bench_with_input(BenchmarkId::from_parameter(size), size, |b, _| {
            b.iter(|| ema(black_box(&data), black_box(20)))
        });
    }

    group.finish();
}

/// Benchmark with extreme volatility (large value swings)
fn benchmark_extreme_volatility(c: &mut Criterion) {
    let mut group = c.benchmark_group("extreme_volatility");

    // Create data with extreme price swings
    let mut data = vec![100.0];
    for i in 1..10_000 {
        let multiplier = if i % 2 == 0 { 2.0 } else { 0.5 };
        data.push(data[i - 1] * multiplier);
    }

    group.bench_function("sma_volatile", |b| {
        b.iter(|| sma(black_box(&data), black_box(50)))
    });

    group.bench_function("ema_volatile", |b| {
        b.iter(|| ema(black_box(&data), black_box(50)))
    });

    group.finish();
}

/// Benchmark with very small numbers (near underflow)
fn benchmark_small_numbers(c: &mut Criterion) {
    let mut group = c.benchmark_group("small_numbers");

    // Numbers near underflow threshold
    let data: Vec<f64> = (0..10_000).map(|i| 1e-9 + (i as f64) * 1e-12).collect();

    group.bench_function("sma_tiny", |b| {
        b.iter(|| sma(black_box(&data), black_box(100)))
    });

    group.bench_function("ema_tiny", |b| {
        b.iter(|| ema(black_box(&data), black_box(100)))
    });

    group.finish();
}

/// Benchmark with alternating large and small values
fn benchmark_mixed_range(c: &mut Criterion) {
    let mut group = c.benchmark_group("mixed_range");

    // Alternating between very large and very small values
    let data: Vec<f64> = (0..10_000)
        .map(|i| if i % 2 == 0 { 1e10 } else { 1e-10 })
        .collect();

    group.bench_function("sma_mixed", |b| {
        b.iter(|| sma(black_box(&data), black_box(50)))
    });

    group.bench_function("ema_mixed", |b| {
        b.iter(|| ema(black_box(&data), black_box(50)))
    });

    group.finish();
}

/// Benchmark Kahan summation vs naive summation
/// This demonstrates the performance cost of compensated summation
fn benchmark_kahan_summation(c: &mut Criterion) {
    let mut group = c.benchmark_group("kahan_summation");

    let data: Vec<f64> = (0..100_000).map(|i| 1e10 + (i as f64) * 1e-5).collect();

    // Naive summation
    group.bench_function("naive_sum", |b| {
        b.iter(|| black_box(&data).iter().sum::<f64>())
    });

    // Kahan summation (compensated)
    group.bench_function("kahan_sum", |b| {
        b.iter(|| {
            let mut sum = 0.0;
            let mut c = 0.0;

            for &x in black_box(&data) {
                let y = x - c;
                let t = sum + y;
                c = (t - sum) - y;
                sum = t;
            }

            sum
        })
    });

    group.finish();
}

/// Benchmark different period sizes
fn benchmark_period_variations(c: &mut Criterion) {
    let mut group = c.benchmark_group("period_variations");

    let data: Vec<f64> = (0..100_000)
        .map(|i| 100.0 + (i as f64 * 0.01).sin())
        .collect();

    for period in [10, 50, 100, 200, 500].iter() {
        group.bench_with_input(BenchmarkId::new("sma", period), period, |b, &p| {
            b.iter(|| sma(black_box(&data), black_box(p)))
        });

        group.bench_with_input(BenchmarkId::new("ema", period), period, |b, &p| {
            b.iter(|| ema(black_box(&data), black_box(p)))
        });
    }

    group.finish();
}

/// Benchmark memory efficiency with large datasets
fn benchmark_memory_efficiency(c: &mut Criterion) {
    let mut group = c.benchmark_group("memory_efficiency");
    group.sample_size(10); // Reduce sample size for large datasets

    // Test with 1 million data points
    let data: Vec<f64> = (0..1_000_000)
        .map(|i| 100.0 + (i as f64 * 0.001).sin())
        .collect();

    group.bench_function("sma_1m_points", |b| {
        b.iter(|| sma(black_box(&data), black_box(100)))
    });

    group.bench_function("ema_1m_points", |b| {
        b.iter(|| ema(black_box(&data), black_box(100)))
    });

    group.finish();
}

criterion_group!(
    benches,
    benchmark_sma_large_numbers,
    benchmark_ema_long_sequence,
    benchmark_extreme_volatility,
    benchmark_small_numbers,
    benchmark_mixed_range,
    benchmark_kahan_summation,
    benchmark_period_variations,
    benchmark_memory_efficiency,
);

criterion_main!(benches);
