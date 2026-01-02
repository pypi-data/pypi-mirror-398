use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};

use haze_library::indicators::pandas_ta_compat as p;
use haze_library::utils;

fn bench_stats_hotspots(c: &mut Criterion) {
    let mut group = c.benchmark_group("stats_hotspots");
    group.sample_size(20);

    let sizes = [10_000usize, 100_000usize];
    let periods = [20usize, 200usize];

    for &n in &sizes {
        let data: Vec<f64> = (0..n)
            .map(|i| 100.0 + (i as f64 * 0.01).sin() + (i as f64 * 0.001).cos())
            .collect();
        let data2: Vec<f64> = (0..n)
            .map(|i| 50.0 + (i as f64 * 0.02).sin() - (i as f64 * 0.003).cos())
            .collect();

        for &period in &periods {
            if period >= n {
                continue;
            }

            group.bench_with_input(
                BenchmarkId::new("linear_regression", format!("{n}_p{period}")),
                &(&data, period),
                |b, (values, p)| {
                    b.iter(|| {
                        let (slope, intercept, r2) =
                            utils::linear_regression(black_box(values), black_box(*p));
                        black_box((slope[n - 1], intercept[n - 1], r2[n - 1]));
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("linearreg", format!("{n}_p{period}")),
                &(&data, period),
                |b, (values, p)| {
                    b.iter(|| {
                        let out = utils::linearreg(black_box(values), black_box(*p));
                        black_box(out[n - 1]);
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("standard_error", format!("{n}_p{period}")),
                &(&data, period),
                |b, (values, p)| {
                    b.iter(|| {
                        let out = utils::standard_error(black_box(values), black_box(*p));
                        black_box(out[n - 1]);
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("correlation", format!("{n}_p{period}")),
                &(&data, &data2, period),
                |b, (x, y, p)| {
                    b.iter(|| {
                        let out = utils::correlation(black_box(x), black_box(y), black_box(*p));
                        black_box(out[n - 1]);
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("covariance", format!("{n}_p{period}")),
                &(&data, &data2, period),
                |b, (x, y, p)| {
                    b.iter(|| {
                        let out = utils::covariance(black_box(x), black_box(y), black_box(*p));
                        black_box(out[n - 1]);
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("beta", format!("{n}_p{period}")),
                &(&data, &data2, period),
                |b, (x, y, p)| {
                    b.iter(|| {
                        let out = utils::beta(black_box(x), black_box(y), black_box(*p));
                        black_box(out[n - 1]);
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("zscore", format!("{n}_p{period}")),
                &(&data, period),
                |b, (values, p)| {
                    b.iter(|| {
                        let out = utils::zscore(black_box(values), black_box(*p));
                        black_box(out[n - 1]);
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("var", format!("{n}_p{period}")),
                &(&data, period),
                |b, (values, p)| {
                    b.iter(|| {
                        let out = utils::var(black_box(values), black_box(*p));
                        black_box(out[n - 1]);
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("var_precise", format!("{n}_p{period}")),
                &(&data, period),
                |b, (values, p)| {
                    b.iter(|| {
                        let out = utils::var_precise(black_box(values), black_box(*p));
                        black_box(out[n - 1]);
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("stdev_precise", format!("{n}_p{period}")),
                &(&data, period),
                |b, (values, p)| {
                    b.iter(|| {
                        let out = utils::stdev_precise(black_box(values), black_box(*p));
                        black_box(out[n - 1]);
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("rolling_percentile_p50", format!("{n}_p{period}")),
                &(&data, period),
                |b, (values, p)| {
                    b.iter(|| {
                        let out = utils::rolling_percentile(black_box(values), black_box(*p), 0.5);
                        black_box(out[n - 1]);
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("rolling_percentile_p90", format!("{n}_p{period}")),
                &(&data, period),
                |b, (values, p)| {
                    b.iter(|| {
                        let out = utils::rolling_percentile(black_box(values), black_box(*p), 0.9);
                        black_box(out[n - 1]);
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("sma", format!("{n}_p{period}")),
                &(&data, period),
                |b, (values, p)| {
                    b.iter(|| {
                        let out = utils::sma(black_box(values), black_box(*p)).unwrap();
                        black_box(out[n - 1]);
                    })
                },
            );

            group.bench_with_input(
                BenchmarkId::new("ema", format!("{n}_p{period}")),
                &(&data, period),
                |b, (values, p)| {
                    b.iter(|| {
                        let out = utils::ema(black_box(values), black_box(*p)).unwrap();
                        black_box(out[n - 1]);
                    })
                },
            );
        }
    }

    group.finish();
}

fn bench_pandas_ta_compat_hotspots(c: &mut Criterion) {
    let mut group = c.benchmark_group("pandas_ta_compat_hotspots");
    group.sample_size(10);

    let n = 100_000usize;
    let close: Vec<f64> = (0..n)
        .map(|i| 100.0 + (i as f64 * 0.01).sin() + (i as f64 * 0.001).cos())
        .collect();
    let high: Vec<f64> = close.iter().map(|&v| v + 1.0).collect();
    let low: Vec<f64> = close.iter().map(|&v| v - 1.0).collect();

    group.bench_function("ht_trendline_prenan63", |b| {
        b.iter(|| {
            let out = p::ht_trendline(black_box(&close), black_box(63)).unwrap();
            black_box(out[n - 1]);
        })
    });

    group.bench_function("jma_len7_phase0", |b| {
        b.iter(|| {
            let out = p::jma(black_box(&close), black_box(7), black_box(0.0)).unwrap();
            black_box(out[n - 1]);
        })
    });

    group.bench_function("zigzag_legs10_dev5", |b| {
        b.iter(|| {
            let out = p::zigzag(black_box(&high), black_box(&low), 10, 5.0, false, 0).unwrap();
            black_box(out.len());
        })
    });

    group.bench_function("squeeze_pro_defaultish", |b| {
        b.iter(|| {
            let out = p::squeeze_pro(
                black_box(&high),
                black_box(&low),
                black_box(&close),
                20,
                2.0,
                20,
                1.0,
                1.5,
                2.0,
                12,
                6,
                true,
                "sma",
                false,
                true,
                false,
            )
            .unwrap();
            black_box(out.len());
        })
    });

    group.finish();
}

criterion_group!(
    benches,
    bench_stats_hotspots,
    bench_pandas_ta_compat_hotspots
);
criterion_main!(benches);
