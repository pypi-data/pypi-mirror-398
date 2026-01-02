//! Pandas-TA Compatibility Layer
//!
//! This module provides a **name-level** compatibility surface for indicators
//! in `pandas-ta` by exposing the same indicator names as those listed in
//! `pandas_ta.maps.Category`.
//!
//! Signatures and return shapes follow Haze conventions.

#![allow(clippy::too_many_arguments)]

use std::collections::BTreeMap;

use crate::errors::validation::{
    validate_lengths_match, validate_min_length, validate_not_empty, validate_period,
};
use crate::errors::{HazeError, HazeResult};
use crate::init_result;
use crate::utils::math::{is_not_zero, is_zero};

/// Result type for OHLC (Open, High, Low, Close) candle operations
type OhlcResult = (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>);

// =============================================================================
// Re-exports (already implemented in Haze)
// =============================================================================

// ---- Candle ----
// `cdl_pattern`, `cdl_z`, `ha` are implemented below (Rust does not have a
// dynamic DataFrame, so we return tuples/maps).

// ---- Cycle ----
// `ebsw`, `reflex` are implemented below.

// ---- Momentum ----
pub use crate::indicators::momentum::{apo, cci, cmo, kdj, macd, ppo, rsi, stochrsi, tsi};
pub use crate::indicators::trend::trix;

pub use crate::indicators::pandas_ta::{
    aberration, alligator, alma, bias, bop, cfo, coppock, cti, efi, entropy, er, inertia, kst,
    percent_rank, pgo, psl, pwma, qqe, sinwma, slope, smi, squeeze, stc, swma, vidya, vwma,
};

// ---- Overlap ----
pub use crate::indicators::ichimoku::ichimoku_cloud as ichimoku;
pub use crate::indicators::overlap::{hl2, hlc3, mama, midpoint, midprice, ohlc4, trima};
pub use crate::indicators::price_transform::wclprice as wcp;

// ---- Trend ----
pub use crate::indicators::overlap::sar as psar;
pub use crate::indicators::trend::choppiness_index as chop;
pub use crate::indicators::trend::{adx, aroon, dpo, qstick, supertrend, vhf, vortex};

// ---- Volatility ----
pub use crate::indicators::volatility::bollinger_bands as bbands;
pub use crate::indicators::volatility::donchian_channel as donchian;
pub use crate::indicators::volatility::mass_index as massi;
pub use crate::indicators::volatility::ulcer_index as ui;
pub use crate::indicators::volatility::{atr, chandelier_exit, natr, true_range};

// ---- Volume ----
pub use crate::indicators::volume::accumulation_distribution as ad;
pub use crate::indicators::volume::chaikin_ad_oscillator as adosc;
pub use crate::indicators::volume::ease_of_movement as eom;
pub use crate::indicators::volume::negative_volume_index as nvi;
pub use crate::indicators::volume::positive_volume_index as pvi;
pub use crate::indicators::volume::price_volume_trend as pvt;
pub use crate::indicators::volume::{cmf, mfi, obv, vwap};

// ---- Utilities (moving averages + rolling stats) ----
pub use crate::utils::momentum as mom;
pub use crate::utils::{dema, ema, hma, kama, rma, sma, t3, tema, wma, zlma};
pub use crate::utils::{roc, stdev, stdev_precise, zscore};
pub use crate::utils::{rolling_max, rolling_min, rolling_percentile, rolling_sum};

// =============================================================================
// Aliases (naming differences)
// =============================================================================

pub use crate::indicators::momentum::awesome_oscillator as ao;
pub use crate::indicators::momentum::fisher_transform as fisher;
pub use crate::indicators::momentum::ultimate_oscillator as uo;
pub use crate::indicators::momentum::williams_r as willr;

pub use crate::utils::rma as smma;

// =============================================================================
// Helpers
// =============================================================================

#[inline]
fn bool_to_f64(value: bool) -> f64 {
    if value {
        1.0
    } else {
        0.0
    }
}

#[inline]
fn sign(value: f64) -> f64 {
    if value.is_nan() {
        f64::NAN
    } else if value > 0.0 {
        1.0
    } else if value < 0.0 {
        -1.0
    } else {
        0.0
    }
}

#[inline]
fn non_zero_range(x: f64, y: f64) -> f64 {
    let diff = x - y;
    if diff == 0.0 {
        diff + f64::EPSILON
    } else {
        diff
    }
}

fn shift(values: &[f64], periods: usize) -> Vec<f64> {
    let n = values.len();
    if periods == 0 {
        return values.to_vec();
    }
    let mut out = vec![f64::NAN; n];
    out[periods..n].copy_from_slice(&values[..(n - periods)]);
    out
}

fn diff(values: &[f64], periods: usize) -> Vec<f64> {
    let n = values.len();
    if periods == 0 {
        return vec![0.0; n];
    }
    let mut out = vec![f64::NAN; n];
    for i in periods..n {
        out[i] = values[i] - values[i - periods];
    }
    out
}

fn unsigned_differences(values: &[f64], lag: usize) -> (Vec<f64>, Vec<f64>) {
    let n = values.len();
    let lag = lag.max(1);

    let mut pos = vec![0.0; n];
    let mut neg = vec![0.0; n];

    for i in lag..n {
        let d = values[i] - values[i - lag];
        if d > 0.0 {
            pos[i] = 1.0;
        } else if d < 0.0 {
            neg[i] = 1.0;
        }
    }

    (pos, neg)
}

fn signed_series(values: &[f64], lag: usize) -> Vec<f64> {
    let n = values.len();
    let lag = lag.max(1);
    let mut out = vec![f64::NAN; n];
    for i in lag..n {
        out[i] = sign(values[i] - values[i - lag]);
    }
    out
}

fn ffill_in_place(values: &mut [f64]) {
    let mut last = f64::NAN;
    for v in values.iter_mut() {
        if v.is_nan() {
            *v = last;
        } else {
            last = *v;
        }
    }
}

fn bfill_in_place(values: &mut [f64]) {
    let mut next = f64::NAN;
    for v in values.iter_mut().rev() {
        if v.is_nan() {
            *v = next;
        } else {
            next = *v;
        }
    }
}

fn ma_by_name(mamode: &str, values: &[f64], length: usize) -> HazeResult<Vec<f64>> {
    match mamode.to_ascii_lowercase().as_str() {
        "ema" => crate::utils::ma::ema_allow_nan(values, length),
        "rma" | "smma" => crate::utils::ma::rma_allow_nan(values, length),
        "wma" => crate::utils::ma::wma_allow_nan(values, length),
        _ => crate::utils::ma::sma_allow_nan(values, length),
    }
}

fn shift_signed(values: &[f64], periods: isize) -> Vec<f64> {
    if periods == 0 {
        return values.to_vec();
    }

    let n = values.len();
    let mut out = vec![f64::NAN; n];

    if periods > 0 {
        let k = periods as usize;
        out[k..n].copy_from_slice(&values[..(n - k)]);
    } else {
        let k = (-periods) as usize;
        let end = n.saturating_sub(k);
        out[..end].copy_from_slice(&values[k..(k + end)]);
    }

    out
}

fn rolling_sum_strict(values: &[f64], period: usize) -> Vec<f64> {
    const RECALC_INTERVAL: usize = 1000;

    if period == 0 || period > values.len() {
        return vec![f64::NAN; values.len()];
    }

    let n = values.len();
    let mut out = vec![f64::NAN; n];
    let mut sum = 0.0;
    let mut compensation = 0.0;
    let mut count = 0usize;
    let mut steps_since_recalc = 0usize;

    for i in 0..n {
        let v = values[i];
        if v.is_nan() {
            sum = 0.0;
            compensation = 0.0;
            count = 0;
            steps_since_recalc = 0;
            continue;
        }

        // Add new value (Kahan)
        let y = v - compensation;
        let t = sum + y;
        compensation = (t - sum) - y;
        sum = t;
        count += 1;

        if count > period {
            // Remove old value (Kahan)
            let old = values[i - period];
            let y = -old - compensation;
            let t = sum + y;
            compensation = (t - sum) - y;
            sum = t;
            count = period;

            steps_since_recalc += 1;
            if steps_since_recalc >= RECALC_INTERVAL {
                sum = crate::utils::math::kahan_sum(&values[i + 1 - period..=i]);
                compensation = 0.0;
                steps_since_recalc = 0;
            }
        }

        if count == period {
            out[i] = sum;
        }
    }

    out
}

fn consecutive_streak(values: &[f64]) -> Vec<f64> {
    let n = values.len();
    let mut out = vec![0.0; n];

    for i in 1..n {
        let a = values[i];
        let b = values[i - 1];
        out[i] = if a.is_nan() || b.is_nan() {
            0.0
        } else {
            sign(a - b)
        };
    }

    out
}

fn sum_signed_rolling_deltas(
    open: &[f64],
    close: &[f64],
    length: usize,
    exclusive: bool,
) -> Vec<f64> {
    let n = close.len();
    let mut window = length.max(1);
    if !exclusive {
        window = window.saturating_sub(1);
    }
    if window == 0 || window >= n || open.len() != n {
        return vec![f64::NAN; n];
    }

    let mut out = vec![f64::NAN; n];

    for i in window..n {
        let c = close[i];
        if c.is_nan() {
            continue;
        }

        let mut sum = 0.0;
        for &o in &open[(i - window)..i] {
            if o.is_nan() {
                continue;
            }
            sum += sign(c - o);
        }

        out[i] = sum;
    }

    out
}

// =============================================================================
// Candle
// =============================================================================

/// Heikin-Ashi Candles (`pandas-ta: ha`)
pub fn ha(open: &[f64], high: &[f64], low: &[f64], close: &[f64]) -> HazeResult<OhlcResult> {
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;

    let n = close.len();
    let mut ha_close = vec![0.0; n];
    let mut ha_open = vec![0.0; n];
    let mut ha_high = vec![0.0; n];
    let mut ha_low = vec![0.0; n];

    for i in 0..n {
        ha_close[i] = 0.25 * (open[i] + high[i] + low[i] + close[i]);
    }

    ha_open[0] = 0.5 * (open[0] + close[0]);
    for i in 1..n {
        ha_open[i] = 0.5 * (ha_open[i - 1] + ha_close[i - 1]);
    }

    for i in 0..n {
        let o = ha_open[i];
        let c = ha_close[i];
        ha_high[i] = high[i].max(o.max(c));
        ha_low[i] = low[i].min(o.min(c));
    }

    Ok((ha_open, ha_high, ha_low, ha_close))
}

/// Z Candles (`pandas-ta: cdl_z`)
///
/// Returns the rolling z-score of OHLC with a configurable `ddof` (0 or 1).
pub fn cdl_z(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    period: usize,
    ddof: usize,
) -> HazeResult<OhlcResult> {
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;
    validate_period(period, close.len())?;
    if period < 2 {
        return Err(HazeError::InvalidPeriod {
            period,
            data_len: close.len(),
        });
    }
    if ddof >= period {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("ddof ({ddof}) must be < period ({period})"),
        });
    }

    fn zscore_with_ddof(values: &[f64], period: usize, ddof: usize) -> HazeResult<Vec<f64>> {
        let mean = crate::utils::sma(values, period)?;
        let std = match ddof {
            0 => crate::utils::stdev_precise(values, period),
            1 => crate::utils::stdev(values, period),
            _ => {
                // Compute variance with custom ddof inline
                let n = values.len();
                let divisor = (period - ddof) as f64;
                if divisor <= 0.0 {
                    return Err(HazeError::InvalidPeriod {
                        period,
                        data_len: n,
                    });
                }
                let mut out = vec![f64::NAN; n];
                for i in (period - 1)..n {
                    let window_mean = mean[i];
                    if window_mean.is_nan() {
                        continue;
                    }
                    let mut sum_sq = 0.0;
                    for j in 0..period {
                        let diff = values[i - period + 1 + j] - window_mean;
                        sum_sq += diff * diff;
                    }
                    out[i] = (sum_sq / divisor).sqrt();
                }
                out
            }
        };

        let mut out = vec![f64::NAN; values.len()];
        for i in 0..values.len() {
            if mean[i].is_nan() || std[i].is_nan() {
                continue;
            }
            if std[i] > 0.0 {
                out[i] = (values[i] - mean[i]) / std[i];
            } else {
                out[i] = 0.0;
            }
        }
        Ok(out)
    }

    let z_open = zscore_with_ddof(open, period, ddof)?;
    let z_high = zscore_with_ddof(high, period, ddof)?;
    let z_low = zscore_with_ddof(low, period, ddof)?;
    let z_close = zscore_with_ddof(close, period, ddof)?;

    Ok((z_open, z_high, z_low, z_close))
}

/// Candle Pattern wrapper (`pandas-ta: cdl_pattern`)
///
/// Rust does not have a DataFrame return type in this crate, so this returns a
/// deterministic map from pattern name -> signal series.
pub fn cdl_pattern(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    names: Option<&[&str]>,
) -> HazeResult<BTreeMap<String, Vec<f64>>> {
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;

    let supported: &[&str] = &[
        "3blackcrows",
        "3inside",
        "3outside",
        "3whitesoldiers",
        "abandonedbaby",
        "advanceblock",
        "belthold",
        "breakaway",
        "closingmarubozu",
        "concealbabyswall",
        "counterattack",
        "darkcloudcover",
        "doji",
        "dojistar",
        "dragonflydoji",
        "engulfing",
        "eveningdojistar",
        "eveningstar",
        "gapsidesidewhite",
        "gravestonedoji",
        "hammer",
        "hangingman",
        "harami",
        "haramicross",
        "highwave",
        "hikkake",
        "hikkakemod",
        "homingpigeon",
        "identical3crows",
        "inneck",
        "invertedhammer",
        "kicking",
        "ladderbottom",
        "longleggeddoji",
        "longline",
        "marubozu",
        "matchinglow",
        "mathold",
        "morningdojistar",
        "morningstar",
        "onneck",
        "piercing",
        "rickshawman",
        "risefall3methods",
        "separatinglines",
        "shootingstar",
        "shortline",
        "spinningtop",
        "stalledpattern",
        "sticksandwich",
        "takuri",
        "thrusting",
        "tristar",
        "unique3river",
        "upsidegap2crows",
        "xsidegap3methods",
    ];

    let requested: Vec<&str> = match names {
        None | Some([]) => supported.to_vec(),
        Some(list) if list.len() == 1 && list[0].eq_ignore_ascii_case("all") => supported.to_vec(),
        Some(list) => list.to_vec(),
    };

    let mut out = BTreeMap::<String, Vec<f64>>::new();

    for name in requested {
        let key = format!("CDL_{}", name.to_uppercase());
        let series = match name {
            "doji" => crate::indicators::candlestick::doji(open, high, low, close, 0.1)?,
            "hammer" => crate::indicators::candlestick::hammer(open, high, low, close)?,
            "invertedhammer" => {
                crate::indicators::candlestick::inverted_hammer(open, high, low, close)?
            }
            "hangingman" => crate::indicators::candlestick::hanging_man(open, high, low, close)?,
            "piercing" => crate::indicators::candlestick::piercing_pattern(open, low, close)?,
            "darkcloudcover" => {
                crate::indicators::candlestick::dark_cloud_cover(open, high, close)?
            }
            "morningstar" => crate::indicators::candlestick::morning_star(open, high, low, close)?,
            "eveningstar" => crate::indicators::candlestick::evening_star(open, high, low, close)?,
            "3whitesoldiers" => {
                crate::indicators::candlestick::three_white_soldiers(open, high, close)?
            }
            "3blackcrows" => crate::indicators::candlestick::three_black_crows(open, low, close)?,
            "shootingstar" => {
                crate::indicators::candlestick::shooting_star(open, high, low, close)?
            }
            "marubozu" => crate::indicators::candlestick::marubozu(open, high, low, close)?,
            "spinningtop" => crate::indicators::candlestick::spinning_top(open, high, low, close)?,
            "dragonflydoji" => {
                crate::indicators::candlestick::dragonfly_doji(open, high, low, close, 0.1)?
            }
            "gravestonedoji" => {
                crate::indicators::candlestick::gravestone_doji(open, high, low, close, 0.1)?
            }
            "longleggeddoji" => {
                crate::indicators::candlestick::long_legged_doji(open, high, low, close, 0.1)?
            }
            "abandonedbaby" => {
                crate::indicators::candlestick::abandoned_baby(open, high, low, close, 0.1)?
            }
            "kicking" => crate::indicators::candlestick::kicking(open, high, low, close)?,
            "longline" => crate::indicators::candlestick::long_line(open, high, low, close, 10)?,
            "shortline" => crate::indicators::candlestick::short_line(open, high, low, close, 10)?,
            "dojistar" => crate::indicators::candlestick::doji_star(open, high, low, close, 0.1)?,
            "identical3crows" => {
                crate::indicators::candlestick::identical_three_crows(open, high, low, close)?
            }
            "sticksandwich" => {
                crate::indicators::candlestick::stick_sandwich(open, high, low, close, 0.01)?
            }
            "tristar" => crate::indicators::candlestick::tristar(open, high, low, close, 0.1)?,
            "upsidegap2crows" => {
                crate::indicators::candlestick::upside_gap_two_crows(open, high, low, close)?
            }
            "gapsidesidewhite" => {
                crate::indicators::candlestick::gap_sidesidewhite(open, high, low, close)?
            }
            "takuri" => crate::indicators::candlestick::takuri(open, high, low, close)?,
            "homingpigeon" => {
                crate::indicators::candlestick::homing_pigeon(open, high, low, close)?
            }
            "matchinglow" => {
                crate::indicators::candlestick::matching_low(open, high, low, close, 0.01)?
            }
            "separatinglines" => {
                crate::indicators::candlestick::separating_lines(open, high, low, close, 0.005)?
            }
            "thrusting" => crate::indicators::candlestick::thrusting(open, high, low, close)?,
            "inneck" => crate::indicators::candlestick::inneck(open, high, low, close, 0.01)?,
            "onneck" => crate::indicators::candlestick::onneck(open, high, low, close, 0.01)?,
            "advanceblock" => {
                crate::indicators::candlestick::advance_block(open, high, low, close)?
            }
            "stalledpattern" => {
                crate::indicators::candlestick::stalled_pattern(open, high, low, close)?
            }
            "belthold" => crate::indicators::candlestick::belthold(open, high, low, close)?,
            "concealbabyswall" => {
                crate::indicators::candlestick::concealing_baby_swallow(open, high, low, close)?
            }
            "counterattack" => {
                crate::indicators::candlestick::counterattack(open, high, low, close, 0.005)?
            }
            "highwave" => crate::indicators::candlestick::highwave(open, high, low, close, 0.1)?,
            "hikkake" => crate::indicators::candlestick::hikkake(open, high, low, close)?,
            "hikkakemod" => crate::indicators::candlestick::hikkake_mod(open, high, low, close)?,
            "ladderbottom" => {
                crate::indicators::candlestick::ladder_bottom(open, high, low, close)?
            }
            "mathold" => crate::indicators::candlestick::mat_hold(open, high, low, close)?,
            "rickshawman" => {
                crate::indicators::candlestick::rickshaw_man(open, high, low, close, 0.1)?
            }
            "unique3river" => {
                crate::indicators::candlestick::unique_3_river(open, high, low, close)?
            }
            "xsidegap3methods" => {
                crate::indicators::candlestick::xside_gap_3_methods(open, high, low, close)?
            }
            "closingmarubozu" => {
                crate::indicators::candlestick::closing_marubozu(open, high, low, close)?
            }
            "breakaway" => crate::indicators::candlestick::breakaway(open, high, low, close)?,
            "3inside" => crate::indicators::candlestick::three_inside(open, high, low, close)?,
            "3outside" => crate::indicators::candlestick::three_outside(open, high, low, close)?,
            "eveningdojistar" => {
                crate::indicators::candlestick::evening_doji_star(open, high, low, close, 0.1)?
            }
            "morningdojistar" => {
                crate::indicators::candlestick::morning_doji_star(open, high, low, close, 0.1)?
            }
            "haramicross" => {
                crate::indicators::candlestick::harami_cross(open, high, low, close, 0.1)?
            }
            "engulfing" => {
                let bull = crate::indicators::candlestick::bullish_engulfing(open, close)?;
                let bear = crate::indicators::candlestick::bearish_engulfing(open, close)?;
                bull.iter()
                    .zip(&bear)
                    .map(|(&b, &s)| {
                        if b.is_nan() || s.is_nan() {
                            f64::NAN
                        } else {
                            b - s
                        }
                    })
                    .collect()
            }
            "harami" => {
                let bull = crate::indicators::candlestick::bullish_harami(open, close)?;
                let bear = crate::indicators::candlestick::bearish_harami(open, close)?;
                bull.iter()
                    .zip(&bear)
                    .map(|(&b, &s)| {
                        if b.is_nan() || s.is_nan() {
                            f64::NAN
                        } else {
                            b - s
                        }
                    })
                    .collect()
            }
            "risefall3methods" => {
                let rising =
                    crate::indicators::candlestick::rising_three_methods(open, high, low, close)?;
                let falling =
                    crate::indicators::candlestick::falling_three_methods(open, high, low, close)?;
                rising
                    .iter()
                    .zip(&falling)
                    .map(|(&r, &f)| {
                        if r.is_nan() || f.is_nan() {
                            f64::NAN
                        } else {
                            r - f
                        }
                    })
                    .collect()
            }
            _ => continue,
        };

        out.insert(key, series);
    }

    Ok(out)
}

// =============================================================================
// Cycle
// =============================================================================

/// Even Better SineWave (`pandas-ta: ebsw`)
pub fn ebsw(
    close: &[f64],
    length: usize,
    bars: usize,
    initial_version: bool,
) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;
    if length < 2 {
        return Err(HazeError::InvalidPeriod {
            period: length,
            data_len: close.len(),
        });
    }
    if bars == 0 {
        return Err(HazeError::InvalidPeriod {
            period: bars,
            data_len: close.len(),
        });
    }

    let n = close.len();
    let mut out = vec![f64::NAN; n];
    if n == 0 {
        return Ok(out);
    }

    // Match pandas-ta warmup behavior: first `length-1` NaNs then a 0.
    if length - 1 < n {
        out[length - 1] = 0.0;
    }

    if initial_version {
        // More responsive (pandas-ta "initial_version") branch.
        let length_f = length as f64;
        let bars_f = bars as f64;

        let mut last_close = 0.0;
        let mut last_hp = 0.0;
        let mut filt_hist = [0.0_f64, 0.0_f64];

        for i in length..n {
            let alpha1 = (1.0 - (360.0 / length_f).sin()) / (360.0 / length_f).cos();
            let hp = 0.5 * (1.0 + alpha1) * (close[i] - last_close) + alpha1 * last_hp;

            let a1 = (-((2.0_f64).sqrt() * std::f64::consts::PI / bars_f)).exp();
            let b1 = 2.0 * a1 * ((2.0_f64).sqrt() * 180.0 / bars_f).cos();
            let c2 = b1;
            let c3 = -a1 * a1;
            let c1 = 1.0 - c2 - c3;

            let filter_ = 0.5 * c1 * (hp + last_hp) + c2 * filt_hist[1] + c3 * filt_hist[0];
            let wave = (filter_ + filt_hist[1] + filt_hist[0]) / 3.0;
            let power =
                (filter_ * filter_ + filt_hist[1] * filt_hist[1] + filt_hist[0] * filt_hist[0])
                    / 3.0;
            let wave = if power > 0.0 {
                wave / power.sqrt()
            } else {
                0.0
            };

            out[i] = wave;

            filt_hist[0] = filt_hist[1];
            filt_hist[1] = filter_;
            last_hp = hp;
            last_close = close[i];
        }

        return Ok(out);
    }

    // Default (recommended) branch.
    let length_f = length as f64;
    let bars_f = bars as f64;

    let angle = 2.0 * std::f64::consts::PI / length_f;
    let alpha1 = (1.0 - angle.sin()) / angle.cos();

    let ang = (2.0_f64).sqrt() * std::f64::consts::PI / bars_f;
    let a1 = (-ang).exp();
    let c2 = 2.0 * a1 * ang.cos();
    let c3 = -(a1 * a1);
    let c1 = 1.0 - c2 - c3;

    let mut last_close = 0.0;
    let mut last_hp = 0.0;
    let mut filt = [0.0_f64, 0.0_f64, 0.0_f64];

    for i in length..n {
        let hp = 0.5 * (1.0 + alpha1) * (close[i] - last_close) + alpha1 * last_hp;

        // roll left by 1 then overwrite last element
        let f0 = filt[1];
        let f1 = filt[2];
        let new_f = 0.5 * c1 * (hp + last_hp) + c2 * f1 + c3 * f0;
        filt[0] = f0;
        filt[1] = f1;
        filt[2] = new_f;

        let wave = (filt[0] + filt[1] + filt[2]) / 3.0;
        let rms = ((filt[0] * filt[0] + filt[1] * filt[1] + filt[2] * filt[2]) / 3.0).sqrt();
        out[i] = if rms > 0.0 { wave / rms } else { 0.0 };

        last_hp = hp;
        last_close = close[i];
    }

    Ok(out)
}

/// Reflex (`pandas-ta: reflex`)
pub fn reflex(close: &[f64], length: usize, smooth: usize, alpha: f64) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    if length == 0 || smooth == 0 {
        return Err(HazeError::InvalidPeriod {
            period: length.max(smooth),
            data_len: close.len(),
        });
    }
    validate_min_length(close, length.max(smooth) + 1)?;

    // pandas-ta defaults
    let pi = std::f64::consts::PI;
    let sqrt2 = 1.414;

    let n = close.len();
    let mut f = vec![0.0; n];
    let mut ms = vec![0.0; n];
    let mut out = vec![0.0; n];

    let ratio = 2.0 * sqrt2 / (smooth as f64);
    let a = (-pi * ratio).exp();
    let b = 2.0 * a * (180.0 * ratio).cos();
    let c = a * a - b + 1.0;

    for i in 2..n {
        f[i] = 0.5 * c * (close[i] + close[i - 1]) + b * f[i - 1] - a * a * f[i - 2];
    }

    let length_f = length as f64;
    for i in length..n {
        let slope = (f[i - length] - f[i]) / length_f;
        let mut sum = 0.0;
        for j in 1..length {
            sum += f[i] - f[i - j] + (j as f64) * slope;
        }
        sum /= length_f;

        ms[i] = alpha * sum * sum + (1.0 - alpha) * ms[i - 1];
        if ms[i] != 0.0 {
            out[i] = sum / ms[i].sqrt();
        }
    }

    for v in out.iter_mut().take(length) {
        *v = f64::NAN;
    }

    Ok(out)
}

// =============================================================================
// Momentum
// =============================================================================

/// BRAR (`pandas-ta: brar`)
pub fn brar(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    length: usize,
    scalar: f64,
    drift: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;
    validate_period(length, close.len())?;

    let drift = drift.max(1);
    let n = close.len();

    let close_shift = shift(close, drift);

    let mut high_open = vec![f64::NAN; n];
    let mut open_low = vec![f64::NAN; n];
    let mut hcy = vec![f64::NAN; n];
    let mut cyl = vec![f64::NAN; n];

    for i in 0..n {
        high_open[i] = non_zero_range(high[i], open[i]);
        open_low[i] = non_zero_range(open[i], low[i]);

        let prev_close = close_shift[i];
        hcy[i] = non_zero_range(high[i], prev_close);
        cyl[i] = non_zero_range(prev_close, low[i]);

        if hcy[i].is_finite() && hcy[i] < 0.0 {
            hcy[i] = 0.0;
        }
        if cyl[i].is_finite() && cyl[i] < 0.0 {
            cyl[i] = 0.0;
        }
    }

    let sum_high_open = rolling_sum_strict(&high_open, length);
    let sum_open_low = rolling_sum_strict(&open_low, length);
    let sum_hcy = rolling_sum_strict(&hcy, length);
    let sum_cyl = rolling_sum_strict(&cyl, length);

    let mut ar = vec![f64::NAN; n];
    let mut br = vec![f64::NAN; n];

    for i in 0..n {
        let den_ar = sum_open_low[i];
        let den_br = sum_cyl[i];
        if sum_high_open[i].is_finite() && den_ar.is_finite() && is_not_zero(den_ar) {
            ar[i] = scalar * sum_high_open[i] / den_ar;
        }
        if sum_hcy[i].is_finite() && den_br.is_finite() && is_not_zero(den_br) {
            br[i] = scalar * sum_hcy[i] / den_br;
        }
    }

    Ok((ar, br))
}

/// Center of Gravity (`pandas-ta: cg`)
pub fn cg(close: &[f64], length: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;

    let n = close.len();
    let mut out = vec![f64::NAN; n];
    if length == 0 {
        return Ok(out);
    }

    for i in (length - 1)..n {
        let window = &close[i + 1 - length..=i];
        if window.iter().any(|v| v.is_nan()) {
            continue;
        }

        let mut numerator = 0.0;
        let mut denom = 0.0;
        for (j, &v) in window.iter().enumerate() {
            numerator += (j as f64 + 1.0) * v;
            denom += v;
        }

        let denom = if is_zero(denom) { f64::EPSILON } else { denom };
        out[i] = -numerator / denom;
    }

    Ok(out)
}

/// Connors RSI (`pandas-ta: crsi`)
pub fn crsi(
    close: &[f64],
    rsi_length: usize,
    streak_length: usize,
    rank_length: usize,
) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;

    let rsi_length = rsi_length.max(1);
    let streak_length = streak_length.max(1);
    let rank_length = rank_length.max(2);

    let rsi_main = rsi(close, rsi_length)?;
    let streak = consecutive_streak(close);
    let streak_rsi = rsi(&streak, streak_length)?;
    let pr = percent_rank(close, rank_length)?;

    let n = close.len();
    let mut out = vec![f64::NAN; n];
    for i in 0..n {
        let a = rsi_main[i];
        let b = streak_rsi[i];
        let c = pr[i];
        if a.is_nan() || b.is_nan() || c.is_nan() {
            continue;
        }
        out[i] = (a + b + c) / 3.0;
    }

    Ok(out)
}

/// Elder Ray Index (`pandas-ta: eri`)
pub fn eri(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    length: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(length, close.len())?;

    let ema_ = ema(close, length)?;
    let n = close.len();
    let mut bull = vec![f64::NAN; n];
    let mut bear = vec![f64::NAN; n];

    for i in 0..n {
        let e = ema_[i];
        if e.is_nan() {
            continue;
        }
        bull[i] = high[i] - e;
        bear[i] = low[i] - e;
    }

    Ok((bull, bear))
}

/// Exhaustion Count (`pandas-ta: exhc`)
pub fn exhc(
    close: &[f64],
    length: usize,
    cap: isize,
    asint: bool,
    show_all: bool,
    nozeros: bool,
) -> HazeResult<BTreeMap<String, Vec<f64>>> {
    validate_not_empty(close, "close")?;
    let length = length.max(1);
    validate_min_length(close, length + 1)?;

    let n = close.len();
    let cap = if cap < 0 { 13.0 } else { cap as f64 };

    let mut dn = vec![0.0; n];
    let mut up = vec![0.0; n];

    let mut dn_csum = 0i32;
    let mut up_csum = 0i32;
    let mut last_dn_reset = 0i32;
    let mut last_up_reset = 0i32;

    for i in 0..n {
        let diff = if i >= length {
            close[i] - close[i - length]
        } else {
            f64::NAN
        };
        let neg = diff < 0.0;
        let pos = diff > 0.0;

        if neg {
            dn_csum += 1;
            dn[i] = (dn_csum - last_dn_reset) as f64;
        } else {
            dn[i] = 0.0;
            last_dn_reset = dn_csum;
        }

        if pos {
            up_csum += 1;
            up[i] = (up_csum - last_up_reset) as f64;
        } else {
            up[i] = 0.0;
            last_up_reset = up_csum;
        }
    }

    if cap > 0.0 {
        for v in dn.iter_mut() {
            *v = v.clamp(0.0, cap);
        }
        for v in up.iter_mut() {
            *v = v.clamp(0.0, cap);
        }
    }

    if !show_all {
        for i in 0..n {
            let between = dn[i] >= 6.0 && dn[i] <= 9.0;
            if !between {
                dn[i] = 0.0;
                up[i] = 0.0;
            }
        }
    }

    if nozeros {
        for v in dn.iter_mut() {
            if *v == 0.0 {
                *v = f64::NAN;
            }
        }
        for v in up.iter_mut() {
            if *v == 0.0 {
                *v = f64::NAN;
            }
        }
    }

    if asint {
        // Values are already integral in f64 form.
    }

    let mut out = BTreeMap::<String, Vec<f64>>::new();
    out.insert(
        if show_all {
            "EXHC_DNa".to_string()
        } else {
            "EXHC_DN".to_string()
        },
        dn,
    );
    out.insert(
        if show_all {
            "EXHC_UPa".to_string()
        } else {
            "EXHC_UP".to_string()
        },
        up,
    );
    Ok(out)
}

/// Relative Strength Xtra (`pandas-ta: rsx`)
pub fn rsx(close: &[f64], length: usize, _drift: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;

    let n = close.len();
    let mut out = vec![f64::NAN; n];
    if length == 0 {
        return Ok(out);
    }

    if length >= 1 && (length - 1) < n {
        out[length - 1] = 50.0;
    }

    let mut f0 = 0.0;
    let mut f8 = 0.0;
    let mut f18 = 0.0;
    let mut f20 = 0.0;
    let mut f28 = 0.0;
    let mut f30 = 0.0;
    let mut f38 = 0.0;
    let mut f40 = 0.0;
    let mut f48 = 0.0;
    let mut f50 = 0.0;
    let mut f58 = 0.0;
    let mut f60 = 0.0;
    let mut f68 = 0.0;
    let mut f70 = 0.0;
    let mut f78 = 0.0;
    let mut f80 = 0.0;
    let mut f88 = 0.0;
    let mut f90 = 0.0;

    for i in length..n {
        let v4 = if f90 == 0.0 {
            f90 = 1.0;
            f0 = 0.0;
            f88 = if (length as f64) - 1.0 >= 5.0 {
                (length as f64) - 1.0
            } else {
                5.0
            };
            f8 = 100.0 * close[i];
            f18 = 3.0 / (length as f64 + 2.0);
            f20 = 1.0 - f18;
            50.0
        } else {
            if f88 <= f90 {
                f90 = f88 + 1.0;
            } else {
                f90 += 1.0;
            }

            let f10 = f8;
            f8 = 100.0 * close[i];
            let v8 = f8 - f10;
            f28 = f20 * f28 + f18 * v8;
            f30 = f18 * f28 + f20 * f30;
            let v_c = 1.5 * f28 - 0.5 * f30;
            f38 = f20 * f38 + f18 * v_c;
            f40 = f18 * f38 + f20 * f40;
            let v10 = 1.5 * f38 - 0.5 * f40;
            f48 = f20 * f48 + f18 * v10;
            f50 = f18 * f48 + f20 * f50;
            let v14 = 1.5 * f48 - 0.5 * f50;
            f58 = f20 * f58 + f18 * v8.abs();
            f60 = f18 * f58 + f20 * f60;
            let v18 = 1.5 * f58 - 0.5 * f60;
            f68 = f20 * f68 + f18 * v18;
            f70 = f18 * f68 + f20 * f70;
            let v1_c = 1.5 * f68 - 0.5 * f70;
            f78 = f20 * f78 + f18 * v1_c;
            f80 = f18 * f78 + f20 * f80;
            let v20 = 1.5 * f78 - 0.5 * f80;

            if f88 >= f90 && f8 != f10 {
                f0 = 1.0;
            }
            if f88 == f90 && f0 == 0.0 {
                f90 = 0.0;
            }

            if f88 < f90 && v20 > 1e-10 {
                ((v14 / v20 + 1.0) * 50.0).clamp(0.0, 100.0)
            } else {
                50.0
            }
        };

        out[i] = v4;
    }

    Ok(out)
}

/// Relative Vigor Index (`pandas-ta: rvgi`)
pub fn rvgi(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    length: usize,
    swma_length: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;

    let length = length.max(1);
    let swma_length = swma_length.max(1);

    let n = close.len();
    let mut high_low = vec![f64::NAN; n];
    let mut close_open = vec![f64::NAN; n];

    for i in 0..n {
        high_low[i] = non_zero_range(high[i], low[i]);
        close_open[i] = non_zero_range(close[i], open[i]);
    }

    let num = swma(&close_open, swma_length)?;
    let den = swma(&high_low, swma_length)?;

    let sum_num = rolling_sum_strict(&num, length);
    let sum_den = rolling_sum_strict(&den, length);

    let mut rvgi = vec![f64::NAN; n];
    for i in 0..n {
        let d = sum_den[i];
        if sum_num[i].is_finite() && d.is_finite() && is_not_zero(d) {
            rvgi[i] = sum_num[i] / d;
        }
    }

    let signal = swma(&rvgi, swma_length)?;
    Ok((rvgi, signal))
}

/// Smart Money Concept (`pandas-ta: smc`)
pub fn smc(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    abr_length: usize,
    close_length: usize,
    vol_length: usize,
    percent: usize,
    vol_ratio: f64,
    asint: bool,
    mamode: &str,
) -> HazeResult<BTreeMap<String, Vec<f64>>> {
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;

    let mut abr_length = abr_length.max(1);
    let mut close_length = close_length.max(1);
    let vol_length = vol_length.max(1);

    if close_length < abr_length {
        std::mem::swap(&mut abr_length, &mut close_length);
    }

    let n = close.len();
    let eps = f64::EPSILON;

    let hh = crate::utils::rolling_max(high, abr_length);
    let ll = crate::utils::rolling_min(low, abr_length);

    let low_shift2 = shift(low, 2);
    let high_shift2 = shift(high, 2);

    let mut abr = vec![f64::NAN; n];
    let mut top_imb = vec![f64::NAN; n];
    let mut btm_imb = vec![f64::NAN; n];
    let mut top_pct = vec![f64::NAN; n];
    let mut btm_pct = vec![f64::NAN; n];

    let mut hld = vec![f64::NAN; n];
    for i in 0..n {
        if hh[i].is_nan() || ll[i].is_nan() {
            continue;
        }
        abr[i] = hh[i] - ll[i];

        top_imb[i] = low_shift2[i] - high[i];
        btm_imb[i] = low[i] - high_shift2[i];

        let abr_d = if is_zero(abr[i]) { eps } else { abr[i] };
        top_pct[i] = 100.0 * top_imb[i] / abr_d;
        btm_pct[i] = 100.0 * btm_imb[i] / abr_d;

        hld[i] = high[i] - low[i] + eps;
    }

    let hld_ma = ma_by_name(mamode, &hld, vol_length)?;

    let mut hv = vec![0.0; n];
    let mut btm_flag = vec![0.0; n];
    let mut top_flag = vec![0.0; n];

    for i in 0..n {
        if hld[i].is_nan() || hld_ma[i].is_nan() {
            continue;
        }
        let is_hv = hld[i] > vol_ratio * hld_ma[i];
        // Note: asint parameter currently has no effect as bool_to_f64 always returns 0.0/1.0
        let _ = asint;
        hv[i] = bool_to_f64(is_hv);

        let bf = btm_imb[i].is_finite()
            && btm_imb[i] > 0.0
            && btm_pct[i].is_finite()
            && btm_pct[i] > 1.0;
        let tf = top_imb[i].is_finite()
            && top_imb[i] > 0.0
            && top_pct[i].is_finite()
            && top_pct[i] > 1.0;
        btm_flag[i] = bool_to_f64(bf);
        top_flag[i] = bool_to_f64(tf);
    }

    // Match pandas-ta behavior: fill missing values
    ffill_in_place(&mut hv);
    bfill_in_place(&mut hv);
    ffill_in_place(&mut btm_flag);
    bfill_in_place(&mut btm_flag);
    ffill_in_place(&mut top_flag);
    bfill_in_place(&mut top_flag);
    ffill_in_place(&mut btm_imb);
    bfill_in_place(&mut btm_imb);
    ffill_in_place(&mut btm_pct);
    bfill_in_place(&mut btm_pct);
    ffill_in_place(&mut top_imb);
    bfill_in_place(&mut top_imb);
    ffill_in_place(&mut top_pct);
    bfill_in_place(&mut top_pct);

    let props = format!("_{abr_length}_{close_length}_{vol_length}_{percent}");
    let mut out = BTreeMap::<String, Vec<f64>>::new();
    out.insert(format!("SMChv{props}"), hv);
    out.insert(format!("SMCbf{props}"), btm_flag);
    out.insert(format!("SMCbi{props}"), btm_imb);
    out.insert(format!("SMCbp{props}"), btm_pct);
    out.insert(format!("SMCtf{props}"), top_flag);
    out.insert(format!("SMCti{props}"), top_imb);
    out.insert(format!("SMCtp{props}"), top_pct);

    Ok(out)
}

/// Squeeze Pro (`pandas-ta: squeeze_pro`)
pub fn squeeze_pro(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    bb_length: usize,
    bb_std: f64,
    kc_length: usize,
    kc_scalar_narrow: f64,
    kc_scalar_normal: f64,
    kc_scalar_wide: f64,
    mom_length: usize,
    mom_smooth: usize,
    use_tr: bool,
    mamode: &str,
    prenan: bool,
    asint: bool,
    detailed: bool,
) -> HazeResult<BTreeMap<String, Vec<f64>>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    if !(kc_scalar_wide > kc_scalar_normal && kc_scalar_normal > kc_scalar_narrow) {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: "kc_scalar_wide must be > kc_scalar_normal > kc_scalar_narrow".to_string(),
        });
    }

    let bb_length = bb_length.max(1);
    let kc_length = kc_length.max(1);
    let mom_length = mom_length.max(1);
    let mom_smooth = mom_smooth.max(1);

    let (bb_u, _bb_m, bb_l) = bbands(close, bb_length, bb_std)?;

    // Inline KC computation to avoid calling `kc()` 3 times (wide/normal/narrow).
    let range_ = if use_tr {
        true_range(high, low, close, 1)?
    } else {
        high.iter()
            .zip(low)
            .map(|(&h, &l)| non_zero_range(h, l))
            .collect::<Vec<f64>>()
    };
    let kc_basis = ma_by_name(mamode, close, kc_length)?;
    let kc_band = ma_by_name(mamode, &range_, kc_length)?;

    let momo = crate::utils::momentum(close, mom_length);
    let squeeze = ma_by_name(mamode, &momo, mom_smooth)?;

    let n = close.len();
    let mut on_wide = vec![0.0; n];
    let mut on_normal = vec![0.0; n];
    let mut on_narrow = vec![0.0; n];
    let mut off = vec![0.0; n];
    let mut no = vec![0.0; n];

    for i in 0..n {
        let basis = kc_basis[i];
        let band = kc_band[i];

        let kcw_l = basis - kc_scalar_wide * band;
        let kcw_u = basis + kc_scalar_wide * band;
        let kcn_l = basis - kc_scalar_normal * band;
        let kcn_u = basis + kc_scalar_normal * band;
        let kcs_l = basis - kc_scalar_narrow * band;
        let kcs_u = basis + kc_scalar_narrow * band;

        let on_w = bb_l[i] > kcw_l && bb_u[i] < kcw_u;
        let on_n = bb_l[i] > kcn_l && bb_u[i] < kcn_u;
        let on_s = bb_l[i] > kcs_l && bb_u[i] < kcs_u;
        let off_w = bb_l[i] < kcw_l && bb_u[i] > kcw_u;
        let no_s = !on_w && !off_w;

        on_wide[i] = bool_to_f64(on_w);
        on_normal[i] = bool_to_f64(on_n);
        on_narrow[i] = bool_to_f64(on_s);
        off[i] = bool_to_f64(off_w);
        no[i] = bool_to_f64(no_s);
    }

    if prenan {
        let nanlength = (bb_length.max(kc_length)).saturating_sub(2);
        for i in 0..n.min(nanlength) {
            on_wide[i] = f64::NAN;
            on_normal[i] = f64::NAN;
            on_narrow[i] = f64::NAN;
            off[i] = f64::NAN;
            no[i] = f64::NAN;
        }
    }

    if !asint {
        // Keep 0/1 floats; pandas-ta uses bool unless asint=True.
    }

    let mut out = BTreeMap::<String, Vec<f64>>::new();
    out.insert("SQZPRO_ON_WIDE".to_string(), on_wide);
    out.insert("SQZPRO_ON_NORMAL".to_string(), on_normal);
    out.insert("SQZPRO_ON_NARROW".to_string(), on_narrow);
    out.insert("SQZPRO_OFF".to_string(), off);
    out.insert("SQZPRO_NO".to_string(), no);

    if detailed {
        let inc = increasing(&squeeze, 1)?;
        let dec = decreasing(&squeeze, 1)?;

        let mut sqz_inc = vec![f64::NAN; n];
        let mut sqz_dec = vec![f64::NAN; n];
        for i in 0..n {
            if inc[i] > 0.0 && squeeze[i] != 0.0 && squeeze[i].is_finite() {
                sqz_inc[i] = squeeze[i];
            }
            if dec[i] > 0.0 && squeeze[i] != 0.0 && squeeze[i].is_finite() {
                sqz_dec[i] = squeeze[i];
            }
        }

        let mut pos_squeeze = vec![f64::NAN; n];
        let mut neg_squeeze = vec![f64::NAN; n];
        for i in 0..n {
            let v = squeeze[i];
            if v.is_nan() {
                continue;
            }
            if v >= 0.0 {
                pos_squeeze[i] = v;
            } else {
                neg_squeeze[i] = v;
            }
        }

        let (pos_inc_f, pos_dec_f) = unsigned_differences(&pos_squeeze, 1);
        let (neg_inc_f, neg_dec_f) = unsigned_differences(&neg_squeeze, 1);

        let mut pos_inc = vec![f64::NAN; n];
        let mut pos_dec = vec![f64::NAN; n];
        let mut neg_inc = vec![f64::NAN; n];
        let mut neg_dec = vec![f64::NAN; n];

        for i in 0..n {
            if pos_inc_f[i] > 0.0 && squeeze[i] != 0.0 {
                pos_inc[i] = squeeze[i];
            }
            if pos_dec_f[i] > 0.0 && squeeze[i] != 0.0 {
                pos_dec[i] = squeeze[i];
            }
            if neg_inc_f[i] > 0.0 && squeeze[i] != 0.0 {
                neg_inc[i] = squeeze[i];
            }
            if neg_dec_f[i] > 0.0 && squeeze[i] != 0.0 {
                neg_dec[i] = squeeze[i];
            }
        }

        out.insert("SQZPRO_INC".to_string(), sqz_inc);
        out.insert("SQZPRO_DEC".to_string(), sqz_dec);
        out.insert("SQZPRO_PINC".to_string(), pos_inc);
        out.insert("SQZPRO_PDEC".to_string(), pos_dec);
        out.insert("SQZPRO_NINC".to_string(), neg_inc);
        out.insert("SQZPRO_NDEC".to_string(), neg_dec);
    }

    out.insert("SQZPRO".to_string(), squeeze);
    Ok(out)
}

/// Stochastic (`pandas-ta: stoch`)
pub fn stoch(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    k: usize,
    d: usize,
    smooth_k: usize,
    mamode: &str,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let k = k.max(1);
    let d = d.max(1);
    let smooth_k = smooth_k.max(1);

    let ll = crate::utils::rolling_min(low, k);
    let hh = crate::utils::rolling_max(high, k);

    let n = close.len();
    let mut raw = vec![f64::NAN; n];
    for i in 0..n {
        if ll[i].is_nan() || hh[i].is_nan() {
            continue;
        }
        let range = non_zero_range(hh[i], ll[i]);
        raw[i] = 100.0 * (close[i] - ll[i]) / range;
    }

    let stoch_k = if smooth_k == 1 {
        raw.clone()
    } else {
        ma_by_name(mamode, &raw, smooth_k)?
    };
    let stoch_d = ma_by_name(mamode, &stoch_k, d)?;

    let stoch_h: Vec<f64> = stoch_k
        .iter()
        .zip(&stoch_d)
        .map(|(&k, &d)| {
            if k.is_nan() || d.is_nan() {
                f64::NAN
            } else {
                k - d
            }
        })
        .collect();

    Ok((stoch_k, stoch_d, stoch_h))
}

/// Fast Stochastic (`pandas-ta: stochf`)
pub fn stochf(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    k: usize,
    d: usize,
    mamode: &str,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let k = k.max(1);
    let d = d.max(1);

    let ll = crate::utils::rolling_min(low, k);
    let hh = crate::utils::rolling_max(high, k);

    let n = close.len();
    let mut stoch_k = vec![f64::NAN; n];
    for i in 0..n {
        if ll[i].is_nan() || hh[i].is_nan() {
            continue;
        }
        let range = non_zero_range(hh[i], ll[i]);
        stoch_k[i] = 100.0 * (close[i] - ll[i]) / range;
    }

    let stoch_d = ma_by_name(mamode, &stoch_k, d)?;
    Ok((stoch_k, stoch_d))
}

/// True Momentum Oscillator (`pandas-ta: tmo`)
pub fn tmo(
    open: &[f64],
    close: &[f64],
    tmo_length: usize,
    calc_length: usize,
    smooth_length: usize,
    momentum: bool,
    exclusive: bool,
    mamode: &str,
) -> HazeResult<BTreeMap<String, Vec<f64>>> {
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[(open, "open"), (close, "close")])?;

    let tmo_length = tmo_length.max(1);
    let calc_length = calc_length.max(1);
    let smooth_length = smooth_length.max(1);

    let signed_diff_sum = sum_signed_rolling_deltas(open, close, tmo_length, exclusive);
    let initial_ma = ma_by_name(mamode, &signed_diff_sum, calc_length)?;
    let main = ma_by_name(mamode, &initial_ma, smooth_length)?;
    let smooth = ma_by_name(mamode, &main, smooth_length)?;

    let n = close.len();
    let mut mom_main = vec![0.0; n];
    let mut mom_smooth = vec![0.0; n];

    if momentum {
        for i in tmo_length..n {
            let a = main[i];
            let b = main[i - tmo_length];
            if a.is_nan() || b.is_nan() {
                mom_main[i] = f64::NAN;
            } else {
                mom_main[i] = a - b;
            }

            let a = smooth[i];
            let b = smooth[i - tmo_length];
            if a.is_nan() || b.is_nan() {
                mom_smooth[i] = f64::NAN;
            } else {
                mom_smooth[i] = a - b;
            }
        }
        for i in 0..tmo_length.min(n) {
            mom_main[i] = f64::NAN;
            mom_smooth[i] = f64::NAN;
        }
    }

    let mut out = BTreeMap::<String, Vec<f64>>::new();
    out.insert("TMO".to_string(), main);
    out.insert("TMOs".to_string(), smooth);
    out.insert("TMOM".to_string(), mom_main);
    out.insert("TMOMs".to_string(), mom_smooth);
    Ok(out)
}

// =============================================================================
// Overlap
// =============================================================================

/// Fibonacci Weighted Moving Average (`pandas-ta: fwma`)
pub fn fwma(close: &[f64], length: usize, asc: bool) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;

    let n = close.len();
    let mut out = vec![f64::NAN; n];

    // Fibonacci weights (normalized)
    let mut weights = vec![0.0; length];
    if length >= 1 {
        weights[0] = 1.0;
    }
    if length >= 2 {
        weights[1] = 1.0;
    }
    for i in 2..length {
        weights[i] = weights[i - 1] + weights[i - 2];
    }
    let sum_w: f64 = weights.iter().sum();
    if is_zero(sum_w) {
        return Ok(out);
    }
    for w in weights.iter_mut() {
        *w /= sum_w;
    }
    if !asc {
        weights.reverse();
    }

    for i in (length - 1)..n {
        let window = &close[i + 1 - length..=i];
        if window.iter().any(|v| v.is_nan()) {
            continue;
        }
        let mut acc = 0.0;
        for (w, &v) in weights.iter().zip(window) {
            acc += w * v;
        }
        out[i] = acc;
    }

    Ok(out)
}

/// Gann HiLo Activator (`pandas-ta: hilo`)
pub fn hilo(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    high_length: usize,
    low_length: usize,
    mamode: &str,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let high_length = high_length.max(1);
    let low_length = low_length.max(1);

    let high_ma = ma_by_name(mamode, high, high_length)?;
    let low_ma = ma_by_name(mamode, low, low_length)?;

    let n = close.len();
    let mut hilo = vec![f64::NAN; n];
    let mut long = vec![f64::NAN; n];
    let mut short = vec![f64::NAN; n];

    for i in 1..n {
        if close[i] > high_ma[i - 1] {
            hilo[i] = low_ma[i];
            long[i] = low_ma[i];
        } else if close[i] < low_ma[i - 1] {
            hilo[i] = high_ma[i];
            short[i] = high_ma[i];
        } else {
            hilo[i] = hilo[i - 1];
            long[i] = hilo[i - 1];
            short[i] = hilo[i - 1];
        }
    }

    Ok((hilo, long, short))
}

/// Holt-Winters Moving Average (`pandas-ta: hwma`)
pub fn hwma(close: &[f64], na: f64, nb: f64, nc: f64) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;

    let na = if (0.0..1.0).contains(&na) { na } else { 0.2 };
    let nb = if (0.0..1.0).contains(&nb) { nb } else { 0.1 };
    let nc = if (0.0..1.0).contains(&nc) { nc } else { 0.1 };

    let n = close.len();
    let mut out = vec![0.0; n];

    let mut last_a = 0.0;
    let mut last_v = 0.0;
    let mut last_f = close[0];

    for i in 0..n {
        let f = (1.0 - na) * (last_f + last_v + 0.5 * last_a) + na * close[i];
        let v = (1.0 - nb) * (last_v + last_a) + nb * (f - last_f);
        let a = (1.0 - nc) * last_a + nc * (v - last_v);

        out[i] = f + v + 0.5 * a;
        last_a = a;
        last_f = f;
        last_v = v;
    }

    Ok(out)
}

/// Jurik Moving Average (`pandas-ta: jma`)
pub fn jma(close: &[f64], length: usize, phase: f64) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;

    let n = close.len();
    let mut out = vec![0.0; n];

    let length_f = 0.5 * (length as f64 - 1.0);
    let pr = if phase < -100.0 {
        0.5
    } else if phase > 100.0 {
        2.5
    } else {
        1.5 + phase * 0.01
    };

    let length1 = (((length_f.sqrt()).ln() / 2.0_f64.ln()) + 2.0).max(0.0);
    let pow1 = (length1 - 2.0).max(0.5);
    let length2 = length1 * length_f.sqrt();
    let bet = if length2 + 1.0 != 0.0 {
        length2 / (length2 + 1.0)
    } else {
        0.0
    };
    let beta = 0.45 * (length as f64 - 1.0) / (0.45 * (length as f64 - 1.0) + 2.0);
    let one_minus_beta = 1.0 - beta;

    let sum_length = 10usize;
    let inv_sum_length = 1.0 / (sum_length as f64);
    let mut det0 = 0.0;
    let mut det1 = 0.0;

    let mut ma1 = close[0];
    let mut u_band = close[0];
    let mut l_band = close[0];
    out[0] = close[0];

    // `v_sum[i]` uses `volty[i - sum_length]`, so keep a small ring buffer.
    let mut volty_window = [0.0_f64; 10];
    let mut volty_window_pos = 0usize;
    let mut volty_window_len = 0usize;
    let mut v_sum_prev = 0.0;

    // Rolling average of v_sum over last 66 samples (max)
    let mut vsum_window_sum = 0.0;
    let mut vsum_window = [0.0_f64; 66];
    let mut vsum_window_len = 0usize;
    let mut vsum_window_pos = 0usize;

    let length1_cap = length1.powf(1.0 / pow1);

    for i in 1..n {
        let price = close[i];

        let del1 = price - u_band;
        let del2 = price - l_band;
        let abs1 = del1.abs();
        let abs2 = del2.abs();
        let volty = if (abs1 - abs2).abs() > 0.0 {
            abs1.max(abs2)
        } else {
            0.0
        };

        let volty_back = if volty_window_len < sum_length {
            0.0
        } else {
            volty_window[volty_window_pos]
        };
        let v_sum = v_sum_prev + (volty - volty_back) * inv_sum_length;
        v_sum_prev = v_sum;

        if volty_window_len < sum_length {
            volty_window_len += 1;
        }
        volty_window[volty_window_pos] = volty;
        volty_window_pos = (volty_window_pos + 1) % sum_length;

        // Update rolling mean of v_sum (window up to 66)
        if vsum_window_len < 66 {
            vsum_window[vsum_window_len] = v_sum;
            vsum_window_sum += v_sum;
            vsum_window_len += 1;
        } else {
            let old = vsum_window[vsum_window_pos];
            vsum_window_sum -= old;
            vsum_window[vsum_window_pos] = v_sum;
            vsum_window_sum += v_sum;
            vsum_window_pos = (vsum_window_pos + 1) % 66;
        }

        let avg_volty = if vsum_window_len > 0 {
            vsum_window_sum / (vsum_window_len as f64)
        } else {
            0.0
        };
        let d_volty = if is_zero(avg_volty) {
            0.0
        } else {
            volty / avg_volty
        };
        let r_volty = 1.0_f64.max(length1_cap.min(d_volty));

        let power = r_volty.powf(pow1);
        let kv = bet.powf(power.sqrt());

        u_band = if del1 > 0.0 { price } else { price - kv * del1 };
        l_band = if del2 < 0.0 { price } else { price - kv * del2 };

        let alpha = beta.powf(power);
        let one_minus_alpha = 1.0 - alpha;
        let one_minus_alpha_sq = one_minus_alpha * one_minus_alpha;
        let alpha_sq = alpha * alpha;

        ma1 = one_minus_alpha * price + alpha * ma1;

        det0 = one_minus_beta * (price - ma1) + beta * det0;
        let ma2 = ma1 + pr * det0;

        det1 = (ma2 - out[i - 1]) * one_minus_alpha_sq + (alpha_sq * det1);
        out[i] = out[i - 1] + det1;
    }

    for v in out.iter_mut().take(length.saturating_sub(1)) {
        *v = f64::NAN;
    }

    Ok(out)
}

/// McGinley Dynamic (`pandas-ta: mcgd`)
pub fn mcgd(close: &[f64], length: usize, c: f64) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    let length = length.max(1);

    let c = if (0.0..=1.0).contains(&c) && c > 0.0 {
        c
    } else {
        1.0
    };

    let n = close.len();
    let mut out = vec![f64::NAN; n];
    if n < 2 {
        return Ok(out);
    }

    let mut prev = close[0];
    for i in 1..n {
        let price = close[i];
        if prev.is_nan() || price.is_nan() || is_zero(prev) {
            out[i] = f64::NAN;
            if price.is_finite() {
                prev = price;
            }
            continue;
        }

        let mut d = c * (length as f64) * (price / prev).powi(4);
        if !d.is_finite() || is_zero(d) {
            d = f64::EPSILON;
        }
        prev = prev + (price - prev) / d;
        out[i] = prev;
    }

    Ok(out)
}

/// Super Smoother Filter (`pandas-ta: ssf`)
pub fn ssf(
    close: &[f64],
    length: usize,
    everget: bool,
    pi: f64,
    sqrt2: f64,
) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;

    let n = close.len();
    let mut out = close.to_vec();
    if n < 3 {
        return Ok(out);
    }

    let pi = if pi > 0.0 { pi } else { std::f64::consts::PI };
    let sqrt2 = if sqrt2 > 0.0 { sqrt2 } else { 1.414 };

    if everget {
        let arg = pi * sqrt2 / (length as f64);
        let a = (-arg).exp();
        let b = 2.0 * a * arg.cos();
        let c = 0.5 * (a * a - b + 1.0);
        for i in 2..n {
            out[i] = c * (close[i] + close[i - 1]) + b * out[i - 1] - a * a * out[i - 2];
        }
    } else {
        let ratio = sqrt2 / (length as f64);
        let a = (-pi * ratio).exp();
        let b = 2.0 * a * (180.0 * ratio).cos();
        let c = a * a - b + 1.0;
        for i in 2..n {
            out[i] = 0.5 * c * (close[i] + close[i - 1]) + b * out[i - 1] - a * a * out[i - 2];
        }
    }

    Ok(out)
}

/// 3 Pole Super Smoother Filter (`pandas-ta: ssf3`)
pub fn ssf3(close: &[f64], length: usize, pi: f64, sqrt3: f64) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;

    let n = close.len();
    let mut out = close.to_vec();
    if n < 4 {
        return Ok(out);
    }

    let pi = if pi > 0.0 { pi } else { std::f64::consts::PI };
    let sqrt3 = if sqrt3 > 0.0 { sqrt3 } else { 1.732 };

    let a = (-pi / (length as f64)).exp();
    let b = 2.0 * a * (-pi * sqrt3 / (length as f64)).cos();
    let c = a * a;

    let d4 = c * c;
    let d3 = -c * (1.0 + b);
    let d2 = b + c;
    let d1 = 1.0 - d2 - d3 - d4;

    for i in 3..n {
        out[i] = d1 * close[i] + d2 * out[i - 1] + d3 * out[i - 2] + d4 * out[i - 3];
    }

    Ok(out)
}

/// Linear Regression Moving Average (`pandas-ta: linreg`)
pub fn linreg(close: &[f64], length: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;
    if length < 2 {
        return Err(HazeError::InvalidPeriod {
            period: length,
            data_len: close.len(),
        });
    }
    Ok(crate::utils::linearreg(close, length))
}

/// Pivot Points (`pandas-ta: pivots`)
///
/// Rust: simplified, computes pivots per bar using the previous bar's OHLC.
pub fn pivots(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    method: &str,
) -> HazeResult<BTreeMap<String, Vec<f64>>> {
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;

    let n = close.len();
    let method = method.to_ascii_lowercase();

    let mut p = vec![f64::NAN; n];
    let mut s1 = vec![f64::NAN; n];
    let mut s2 = vec![f64::NAN; n];
    let mut s3 = vec![f64::NAN; n];
    let mut s4 = vec![f64::NAN; n];
    let mut r1 = vec![f64::NAN; n];
    let mut r2 = vec![f64::NAN; n];
    let mut r3 = vec![f64::NAN; n];
    let mut r4 = vec![f64::NAN; n];

    for i in 1..n {
        let o = open[i - 1];
        let h = high[i - 1];
        let l = low[i - 1];
        let c = close[i - 1];

        if o.is_nan() || h.is_nan() || l.is_nan() || c.is_nan() {
            continue;
        }

        let tp;
        let hl_range = non_zero_range(h, l).abs();

        match method.as_str() {
            "camarilla" => {
                tp = (h + l + c) / 3.0;
                p[i] = tp;
                s1[i] = c - 11.0 / 120.0 * hl_range;
                s2[i] = c - 11.0 / 60.0 * hl_range;
                s3[i] = c - 0.275 * hl_range;
                s4[i] = c - 0.55 * hl_range;
                r1[i] = c + 11.0 / 120.0 * hl_range;
                r2[i] = c + 11.0 / 60.0 * hl_range;
                r3[i] = c + 0.275 * hl_range;
                r4[i] = c + 0.55 * hl_range;
            }
            "classic" => {
                tp = (h + l + c) / 3.0;
                p[i] = tp;
                s1[i] = 2.0 * tp - h;
                s2[i] = tp - hl_range;
                s3[i] = tp - 2.0 * hl_range;
                s4[i] = tp - 3.0 * hl_range;
                r1[i] = 2.0 * tp - l;
                r2[i] = tp + hl_range;
                r3[i] = tp + 2.0 * hl_range;
                r4[i] = tp + 3.0 * hl_range;
            }
            "demark" => {
                tp = if (c - o).abs() < f64::EPSILON {
                    0.25 * (h + l + 2.0 * c)
                } else if c > o {
                    0.25 * (2.0 * h + l + c)
                } else {
                    0.25 * (h + 2.0 * l + c)
                };
                p[i] = tp;
                s1[i] = 2.0 * tp - h;
                r1[i] = 2.0 * tp - l;
            }
            "fibonacci" => {
                tp = (h + l + c) / 3.0;
                p[i] = tp;
                s1[i] = tp - 0.382 * hl_range;
                s2[i] = tp - 0.618 * hl_range;
                s3[i] = tp - hl_range;
                r1[i] = tp + 0.382 * hl_range;
                r2[i] = tp + 0.618 * hl_range;
                r3[i] = tp + hl_range;
            }
            "woodie" => {
                tp = (2.0 * o + h + l) / 4.0;
                p[i] = tp;
                s1[i] = 2.0 * tp - h;
                s2[i] = tp - hl_range;
                s3[i] = l - 2.0 * (h - tp);
                s4[i] = s3[i] - hl_range;
                r1[i] = 2.0 * tp - l;
                r2[i] = tp + hl_range;
                r3[i] = h + 2.0 * (tp - l);
                r4[i] = r3[i] + hl_range;
            }
            _ => {
                // Traditional
                tp = (h + l + c) / 3.0;
                p[i] = tp;
                s1[i] = 2.0 * tp - h;
                s2[i] = tp - hl_range;
                s3[i] = tp - 2.0 * hl_range;
                s4[i] = tp - 2.0 * hl_range;
                r1[i] = 2.0 * tp - l;
                r2[i] = tp + hl_range;
                r3[i] = tp + 2.0 * hl_range;
                r4[i] = tp + 2.0 * hl_range;
            }
        }
    }

    let mut out = BTreeMap::<String, Vec<f64>>::new();
    out.insert("P".to_string(), p);
    out.insert("S1".to_string(), s1);
    out.insert("S2".to_string(), s2);
    out.insert("S3".to_string(), s3);
    out.insert("S4".to_string(), s4);
    out.insert("R1".to_string(), r1);
    out.insert("R2".to_string(), r2);
    out.insert("R3".to_string(), r3);
    out.insert("R4".to_string(), r4);
    Ok(out)
}

// =============================================================================
// Performance
// =============================================================================

/// Percent Return (`pandas-ta: percent_return`)
pub fn percent_return(close: &[f64], length: usize, cumulative: bool) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    let length = length.max(1);
    validate_min_length(close, length + 1)?;

    let n = close.len();
    let mut out = vec![f64::NAN; n];

    if cumulative {
        let base = close[0];
        for i in 0..n {
            if is_not_zero(base) {
                out[i] = (close[i] / base) - 1.0;
            }
        }
        return Ok(out);
    }

    for i in length..n {
        let prev = close[i - length];
        if is_not_zero(prev) {
            out[i] = (close[i] / prev) - 1.0;
        }
    }

    Ok(out)
}

/// Log Return (`pandas-ta: log_return`)
pub fn log_return(close: &[f64], length: usize, cumulative: bool) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    let length = length.max(1);
    validate_min_length(close, length + 1)?;

    let n = close.len();
    let mut out = vec![f64::NAN; n];

    if cumulative {
        let base = close[0];
        for i in 0..n {
            if is_not_zero(base) && is_not_zero(close[i]) {
                out[i] = (close[i] / base).ln();
            }
        }
        return Ok(out);
    }

    for i in length..n {
        let prev = close[i - length];
        if is_not_zero(prev) && is_not_zero(close[i]) {
            out[i] = (close[i] / prev).ln();
        }
    }

    Ok(out)
}

// =============================================================================
// Statistics
// =============================================================================

/// Rolling Median (`pandas-ta: median`)
pub fn median(close: &[f64], length: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;
    Ok(crate::utils::rolling_percentile(close, length, 0.5))
}

/// Rolling Quantile (`pandas-ta: quantile`)
pub fn quantile(close: &[f64], length: usize, q: f64) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;
    if !(0.0 < q && q < 1.0) {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("q must be between 0 and 1, got {q}"),
        });
    }
    Ok(crate::utils::rolling_percentile(close, length, q))
}

/// Rolling Mean Absolute Deviation (`pandas-ta: mad`)
pub fn mad(close: &[f64], length: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;

    let n = close.len();
    let mut out = vec![f64::NAN; n];
    let mean = crate::utils::sma(close, length)?;

    for i in (length - 1)..n {
        let m = mean[i];
        if m.is_nan() {
            continue;
        }

        let window = &close[i + 1 - length..=i];
        if window.iter().any(|v| v.is_nan()) {
            continue;
        }

        let mut sum_abs = 0.0;
        for &v in window {
            sum_abs += (v - m).abs();
        }
        out[i] = sum_abs / (length as f64);
    }

    Ok(out)
}

/// Rolling Variance (`pandas-ta: variance`)
pub fn variance(close: &[f64], length: usize, ddof: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;
    if ddof >= length {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("ddof ({ddof}) must be < length ({length})"),
        });
    }

    let n = close.len();
    let mut out = vec![f64::NAN; n];
    let mean = crate::utils::sma(close, length)?;
    let divisor = (length - ddof) as f64;

    for i in (length - 1)..n {
        let m = mean[i];
        if m.is_nan() {
            continue;
        }

        let window = &close[i + 1 - length..=i];
        if window.iter().any(|v| v.is_nan()) {
            continue;
        }

        let mut sum_sq = 0.0;
        for &v in window {
            let d = v - m;
            sum_sq += d * d;
        }
        out[i] = sum_sq / divisor;
    }

    Ok(out)
}

/// Rolling Skew (`pandas-ta: skew`)
pub fn skew(close: &[f64], length: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;
    if length < 2 {
        return Err(HazeError::InvalidPeriod {
            period: length,
            data_len: close.len(),
        });
    }

    let n = close.len();
    let mut out = vec![f64::NAN; n];
    let mean = crate::utils::sma(close, length)?;

    for i in (length - 1)..n {
        let m = mean[i];
        if m.is_nan() {
            continue;
        }
        let window = &close[i + 1 - length..=i];
        if window.iter().any(|v| v.is_nan()) {
            continue;
        }

        let mut m2 = 0.0;
        let mut m3 = 0.0;
        for &v in window {
            let d = v - m;
            let d2 = d * d;
            m2 += d2;
            m3 += d2 * d;
        }
        let k = length as f64;
        m2 /= k;
        m3 /= k;
        if m2 > 0.0 {
            out[i] = m3 / (m2.sqrt() * m2);
        } else {
            out[i] = 0.0;
        }
    }

    Ok(out)
}

/// Rolling Kurtosis (`pandas-ta: kurtosis`)
pub fn kurtosis(close: &[f64], length: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;
    if length < 2 {
        return Err(HazeError::InvalidPeriod {
            period: length,
            data_len: close.len(),
        });
    }

    let n = close.len();
    let mut out = vec![f64::NAN; n];
    let mean = crate::utils::sma(close, length)?;

    for i in (length - 1)..n {
        let m = mean[i];
        if m.is_nan() {
            continue;
        }
        let window = &close[i + 1 - length..=i];
        if window.iter().any(|v| v.is_nan()) {
            continue;
        }

        let mut m2 = 0.0;
        let mut m4 = 0.0;
        for &v in window {
            let d = v - m;
            let d2 = d * d;
            m2 += d2;
            m4 += d2 * d2;
        }
        let k = length as f64;
        m2 /= k;
        m4 /= k;
        if m2 > 0.0 {
            out[i] = (m4 / (m2 * m2)) - 3.0; // excess kurtosis
        } else {
            out[i] = 0.0;
        }
    }

    Ok(out)
}

/// ThinkOrSwim StDevAll (`pandas-ta: tos_stdevall`)
///
/// Rust return: deterministic map of column -> series.
pub fn tos_stdevall(
    close: &[f64],
    length: Option<usize>,
    stds: Option<&[f64]>,
    ddof: usize,
) -> HazeResult<BTreeMap<String, Vec<f64>>> {
    validate_not_empty(close, "close")?;
    validate_min_length(close, 2)?;

    let n_total = close.len();
    let len_window = length.unwrap_or(n_total).min(n_total);
    if len_window < 2 {
        return Err(HazeError::InvalidPeriod {
            period: len_window,
            data_len: n_total,
        });
    }
    if ddof >= len_window {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("ddof ({ddof}) must be < length ({len_window})"),
        });
    }

    let multiples: Vec<f64> = stds
        .map(|s| s.to_vec())
        .unwrap_or_else(|| vec![1.0, 2.0, 3.0]);
    if multiples.is_empty() || multiples.iter().any(|&v| v <= 0.0 || !v.is_finite()) {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: "stds must be positive finite values".to_string(),
        });
    }

    let start = n_total - len_window;
    let window = &close[start..];
    if window.iter().any(|v| v.is_nan()) {
        return Err(HazeError::InvalidValue {
            index: start,
            message: "close contains NaN in selected window".to_string(),
        });
    }

    // Linear regression y ~ x with x = 0..len_window-1
    let n = len_window as f64;
    let sum_x = (len_window as f64 - 1.0) * n / 2.0;
    let sum_xx = (len_window as f64 - 1.0) * n * (2.0 * n - 1.0) / 6.0;
    let mut sum_y = 0.0;
    let mut sum_xy = 0.0;

    for (i, &y) in window.iter().enumerate() {
        let x = i as f64;
        sum_y += y;
        sum_xy += x * y;
    }

    let denom = n * sum_xx - sum_x * sum_x;
    let slope = if denom != 0.0 {
        (n * sum_xy - sum_x * sum_y) / denom
    } else {
        0.0
    };
    let intercept = (sum_y - slope * sum_x) / n;

    // Standard deviation of the window (ddof)
    let mean_y = sum_y / n;
    let mut ss = 0.0;
    for &y in window {
        let d = y - mean_y;
        ss += d * d;
    }
    let stdev = (ss / ((len_window - ddof) as f64)).sqrt();

    let mut lr = vec![f64::NAN; n_total];
    for i in 0..len_window {
        lr[start + i] = slope * (i as f64) + intercept;
    }

    let mut out = BTreeMap::<String, Vec<f64>>::new();
    let base_name = if length.is_some() {
        format!("TOS_STDEVALL_{len_window}")
    } else {
        "TOS_STDEVALL".to_string()
    };

    out.insert(format!("{base_name}_LR"), lr.clone());

    for m in multiples {
        let mut lower = vec![f64::NAN; n_total];
        let mut upper = vec![f64::NAN; n_total];
        for i in 0..len_window {
            let v = lr[start + i];
            if v.is_nan() {
                continue;
            }
            lower[start + i] = v - m * stdev;
            upper[start + i] = v + m * stdev;
        }
        out.insert(format!("{base_name}_L_{m}"), lower);
        out.insert(format!("{base_name}_U_{m}"), upper);
    }

    Ok(out)
}

// =============================================================================
// Trend
// =============================================================================

/// AlphaTrend (`pandas-ta: alphatrend`)
pub fn alphatrend(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    volume: Option<&[f64]>,
    src: &str,
    length: usize,
    multiplier: f64,
    threshold: f64,
    lag: usize,
    _mamode: &str,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;
    if let Some(vol) = volume {
        validate_lengths_match(&[(close, "close"), (vol, "volume")])?;
    }

    let length = length.max(1);
    validate_period(length, close.len())?;

    let src_values = match src.to_ascii_lowercase().as_str() {
        "open" => open,
        "high" => high,
        "low" => low,
        _ => close,
    };

    let atr_ = atr(high, low, close, length)?;

    let n = close.len();
    let mut lower_atr = vec![f64::NAN; n];
    let mut upper_atr = vec![f64::NAN; n];
    for i in 0..n {
        if atr_[i].is_nan() {
            continue;
        }
        lower_atr[i] = low[i] - atr_[i] * multiplier;
        upper_atr[i] = high[i] + atr_[i] * multiplier;
    }

    let momo = if let Some(vol) = volume {
        mfi(high, low, close, vol, length)?
    } else {
        rsi(src_values, length)?
    };

    let mut at = vec![0.0; n];
    for i in 1..n {
        if momo[i] >= threshold {
            let v = lower_atr[i];
            if v < at[i - 1] {
                at[i] = at[i - 1];
            } else {
                at[i] = v;
            }
        } else {
            let v = upper_atr[i];
            if v > at[i - 1] {
                at[i] = at[i - 1];
            } else {
                at[i] = v;
            }
        }
    }
    if !at.is_empty() {
        at[0] = f64::NAN;
    }

    let atl = shift(&at, lag.max(1));
    Ok((at, atl))
}

/// Hilbert Transform TrendLine (`pandas-ta: ht_trendline`)
pub fn ht_trendline(close: &[f64], prenan: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    if prenan > 0 {
        validate_min_length(close, prenan)?;
    }

    let n = close.len();
    let a = 0.0962;
    let b = 0.5769;

    // Keep only the recent values required for the recursive Hilbert transform
    // steps to reduce allocations and improve cache locality.
    let mut wma4 = [0.0_f64; 7];
    let mut dt = [0.0_f64; 7];
    let mut q1 = [0.0_f64; 7];
    let mut i1 = [0.0_f64; 7];
    let mut i_trend = [0.0_f64; 4];

    let mut i2_prev = 0.0;
    let mut q2_prev = 0.0;
    let mut re_prev = 0.0;
    let mut im_prev = 0.0;
    let mut period_prev = 0.0;
    let mut smp_prev = 0.0;

    let mut result = close.to_vec();

    for i in 6..n {
        let adj_prev_period = 0.075 * period_prev + 0.54;

        let wma4_cur =
            0.4 * close[i] + 0.3 * close[i - 1] + 0.2 * close[i - 2] + 0.1 * close[i - 3];
        wma4[i % 7] = wma4_cur;

        let dt_cur = adj_prev_period
            * (a * wma4_cur + b * wma4[(i - 2) % 7]
                - b * wma4[(i - 4) % 7]
                - a * wma4[(i - 6) % 7]);
        dt[i % 7] = dt_cur;

        let q1_cur = adj_prev_period
            * (a * dt_cur + b * dt[(i - 2) % 7] - b * dt[(i - 4) % 7] - a * dt[(i - 6) % 7]);
        q1[i % 7] = q1_cur;

        let i1_cur = dt[(i - 3) % 7];
        i1[i % 7] = i1_cur;

        let ji_cur = adj_prev_period
            * (a * i1_cur + b * i1[(i - 2) % 7] - b * i1[(i - 4) % 7] - a * i1[(i - 6) % 7]);
        let jq_cur = adj_prev_period
            * (a * q1_cur + b * q1[(i - 2) % 7] - b * q1[(i - 4) % 7] - a * q1[(i - 6) % 7]);

        let i2_raw = i1_cur - jq_cur;
        let q2_raw = q1_cur + ji_cur;

        let i2 = 0.2 * i2_raw + 0.8 * i2_prev;
        let q2 = 0.2 * q2_raw + 0.8 * q2_prev;

        let re_raw = i2 * i2_prev + q2 * q2_prev;
        let im_raw = i2 * q2_prev - q2 * i2_prev;

        let re = 0.2 * re_raw + 0.8 * re_prev;
        let im = 0.2 * im_raw + 0.8 * im_prev;

        let mut period = 0.0;
        if re != 0.0 && im != 0.0 {
            let deg = (im / re).atan().to_degrees();
            if deg != 0.0 {
                period = 360.0 / deg;
            }
        }

        if period > 1.5 * period_prev {
            period = 1.5 * period_prev;
        }
        if period < 0.67 * period_prev {
            period = 0.67 * period_prev;
        }
        period = period.clamp(6.0, 50.0);

        period = 0.2 * period + 0.8 * period_prev;
        let smp = 0.33 * period + 0.67 * smp_prev;

        let dc_period = (smp + 0.5).max(1.0) as usize;
        let mut dcp_avg = 0.0;
        for k in 0..dc_period {
            dcp_avg += close[i - k];
        }
        dcp_avg /= dc_period as f64;
        let i_trend_cur = dcp_avg;

        if i > 12 {
            result[i] = 0.4 * i_trend_cur
                + 0.3 * i_trend[(i - 1) % 4]
                + 0.2 * i_trend[(i - 2) % 4]
                + 0.1 * i_trend[(i - 3) % 4];
        }
        i_trend[i % 4] = i_trend_cur;

        i2_prev = i2;
        q2_prev = q2;
        re_prev = re;
        im_prev = im;
        period_prev = period;
        smp_prev = smp;
    }

    if prenan > 0 {
        for v in result.iter_mut().take(n.min(prenan)) {
            *v = f64::NAN;
        }
    }

    Ok(result)
}

/// ZigZag (`pandas-ta: zigzag`)
pub fn zigzag(
    high: &[f64],
    low: &[f64],
    legs: usize,
    deviation: f64,
    backtest: bool,
    offset: isize,
) -> HazeResult<BTreeMap<String, Vec<f64>>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low")])?;

    let legs = legs.max(3);
    validate_min_length(high, legs + 1)?;

    let n = high.len();

    fn rolling_hl(high: &[f64], low: &[f64], legs: usize) -> (Vec<usize>, Vec<i8>, Vec<f64>) {
        let left = (legs as f64 / 2.0).floor() as usize;
        let right = left + 1;

        let mut idx = Vec::<usize>::new();
        let mut swing = Vec::<i8>::new();
        let mut value = Vec::<f64>::new();

        let m = high.len();
        for i in left..m.saturating_sub(right) {
            let low_center = low[i];
            let high_center = high[i];

            let low_window = &low[i - left..i + right];
            let high_window = &high[i - left..i + right];

            if low_center.is_finite() && low_window.iter().all(|&v| low_center <= v) {
                idx.push(i);
                swing.push(-1);
                value.push(low_center);
            }

            if high_center.is_finite() && high_window.iter().all(|&v| high_center >= v) {
                idx.push(i);
                swing.push(1);
                value.push(high_center);
            }
        }

        (idx, swing, value)
    }

    fn find_zz(
        idx: &[usize],
        swing: &[i8],
        value: &[f64],
        deviation: f64,
    ) -> (Vec<usize>, Vec<i8>, Vec<f64>, Vec<f64>) {
        let mut zz_idx = Vec::<usize>::new();
        let mut zz_swing = Vec::<i8>::new();
        let mut zz_value = Vec::<f64>::new();
        let mut zz_dev = Vec::<f64>::new();

        if idx.is_empty() {
            return (zz_idx, zz_swing, zz_value, zz_dev);
        }

        let last = idx.len() - 1;
        zz_idx.push(idx[last]);
        zz_swing.push(swing[last]);
        zz_value.push(value[last]);
        zz_dev.push(0.0);

        for ii in (0..last).rev() {
            let cur_swing = zz_swing[zz_swing.len() - 1];
            let cur_value = zz_value[zz_value.len() - 1];

            if cur_swing == -1 {
                if swing[ii] == -1 {
                    if value[ii] < cur_value && zz_idx.len() > 2 {
                        let prev_value = zz_value[zz_value.len() - 2];
                        let current_dev = (prev_value - value[ii]) / value[ii];
                        *zz_idx.last_mut().unwrap() = idx[ii];
                        *zz_swing.last_mut().unwrap() = swing[ii];
                        *zz_value.last_mut().unwrap() = value[ii];
                        let dev_idx = zz_dev.len() - 2;
                        zz_dev[dev_idx] = 100.0 * current_dev;
                    }
                } else {
                    let current_dev = (value[ii] - cur_value) / value[ii];
                    if current_dev > 0.01 * deviation {
                        if *zz_idx.last().unwrap() == idx[ii] {
                            continue;
                        }
                        zz_idx.push(idx[ii]);
                        zz_swing.push(swing[ii]);
                        zz_value.push(value[ii]);
                        zz_dev.push(0.0);
                        let dev_idx = zz_dev.len() - 2;
                        zz_dev[dev_idx] = 100.0 * current_dev;
                    }
                }
            } else if swing[ii] == 1 {
                if value[ii] > cur_value && zz_idx.len() > 2 {
                    let prev_value = zz_value[zz_value.len() - 2];
                    let current_dev = (value[ii] - prev_value) / value[ii];
                    *zz_idx.last_mut().unwrap() = idx[ii];
                    *zz_swing.last_mut().unwrap() = swing[ii];
                    *zz_value.last_mut().unwrap() = value[ii];
                    let dev_idx = zz_dev.len() - 2;
                    zz_dev[dev_idx] = 100.0 * current_dev;
                }
            } else {
                let current_dev = (cur_value - value[ii]) / value[ii];
                if current_dev > 0.01 * deviation {
                    if *zz_idx.last().unwrap() == idx[ii] {
                        continue;
                    }
                    zz_idx.push(idx[ii]);
                    zz_swing.push(swing[ii]);
                    zz_value.push(value[ii]);
                    zz_dev.push(0.0);
                    let dev_idx = zz_dev.len() - 2;
                    zz_dev[dev_idx] = 100.0 * current_dev;
                }
            }
        }

        (zz_idx, zz_swing, zz_value, zz_dev)
    }

    fn zz_backtest(
        idx: &[usize],
        swing: &[i8],
        value: &[f64],
        deviation: f64,
    ) -> (Vec<usize>, Vec<i8>, Vec<f64>, Vec<f64>) {
        let mut zz_idx = Vec::<usize>::new();
        let mut zz_swing = Vec::<i8>::new();
        let mut zz_value = Vec::<f64>::new();
        let mut zz_dev = Vec::<f64>::new();

        if idx.is_empty() {
            return (zz_idx, zz_swing, zz_value, zz_dev);
        }

        zz_idx.push(idx[0]);
        zz_swing.push(swing[0]);
        zz_value.push(value[0]);
        zz_dev.push(0.0);

        let mut changes = 0usize;

        for i in 1..idx.len() {
            let last_zz_value = *zz_value.last().unwrap();
            let current_dev = (value[i] - last_zz_value) / last_zz_value;

            let base_index = zz_swing.len().saturating_sub(1 + changes);
            let last_confirmed = zz_swing[base_index];

            if last_confirmed == -1 {
                if swing[i] == -1 {
                    if value[i] < *zz_value.last().unwrap() {
                        if zz_idx[base_index] == idx[i] {
                            continue;
                        }
                        zz_idx.push(idx[i]);
                        zz_swing.push(swing[i]);
                        zz_value.push(value[i]);
                        zz_dev.push(100.0 * current_dev);
                        changes += 1;
                    }
                } else if current_dev > 0.01 * deviation {
                    if zz_idx[base_index] == idx[i] {
                        continue;
                    }
                    zz_idx.push(idx[i]);
                    zz_swing.push(swing[i]);
                    zz_value.push(value[i]);
                    zz_dev.push(100.0 * current_dev);
                    changes = 0;
                }
            } else if swing[i] == 1 {
                if value[i] > *zz_value.last().unwrap() {
                    if zz_idx[base_index] == idx[i] {
                        continue;
                    }
                    zz_idx.push(idx[i]);
                    zz_swing.push(swing[i]);
                    zz_value.push(value[i]);
                    zz_dev.push(100.0 * current_dev);
                    changes += 1;
                }
            } else if current_dev < -0.01 * deviation {
                if zz_idx[base_index] == idx[i] {
                    continue;
                }
                zz_idx.push(idx[i]);
                zz_swing.push(swing[i]);
                zz_value.push(value[i]);
                zz_dev.push(100.0 * current_dev);
                changes = 0;
            }
        }

        (zz_idx, zz_swing, zz_value, zz_dev)
    }

    fn map_zz(
        n: usize,
        idx: &[usize],
        swing: &[i8],
        value: &[f64],
        dev: &[f64],
    ) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
        let mut swing_map = vec![0.0; n];
        let mut value_map = vec![0.0; n];
        let mut dev_map = vec![0.0; n];

        for j in 0..idx.len() {
            let i = idx[j];
            if i >= n {
                continue;
            }
            swing_map[i] = swing[j] as f64;
            value_map[i] = value[j];
            dev_map[i] = dev.get(j).copied().unwrap_or(0.0);
        }

        for i in 0..n {
            if swing_map[i] == 0.0 {
                swing_map[i] = f64::NAN;
                value_map[i] = f64::NAN;
                dev_map[i] = f64::NAN;
            }
        }

        (swing_map, value_map, dev_map)
    }

    let (hli, hls, hlv) = rolling_hl(high, low, legs);
    let (zzi, zzs, zzv, zzd) = if backtest {
        zz_backtest(&hli, &hls, &hlv, deviation)
    } else {
        find_zz(&hli, &hls, &hlv, deviation)
    };

    let (mut swing_map, mut value_map, mut dev_map) = map_zz(n, &zzi, &zzs, &zzv, &zzd);

    let mut offset_total = offset;
    if backtest {
        offset_total += ((legs as f64) / 2.0).floor() as isize;
    }

    if offset_total != 0 {
        swing_map = shift_signed(&swing_map, offset_total);
        value_map = shift_signed(&value_map, offset_total);
        dev_map = shift_signed(&dev_map, offset_total);
    }

    let mut out = BTreeMap::<String, Vec<f64>>::new();
    out.insert("ZIGZAGs".to_string(), swing_map);
    out.insert("ZIGZAGv".to_string(), value_map);
    out.insert("ZIGZAGd".to_string(), dev_map);
    Ok(out)
}

/// Increasing (`pandas-ta: increasing`)
///
/// Returns `1.0` when `close.diff(length) > 0`, else `0.0` (matches pandas-ta default `asint=True`).
pub fn increasing(close: &[f64], length: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;

    let n = close.len();
    let mut out = vec![0.0; n];

    for i in length..n {
        let a = close[i];
        let b = close[i - length];
        if a.is_nan() || b.is_nan() {
            out[i] = 0.0;
        } else {
            out[i] = bool_to_f64((a - b) > 0.0);
        }
    }

    Ok(out)
}

/// Decreasing (`pandas-ta: decreasing`)
///
/// Returns `1.0` when `close.diff(length) < 0`, else `0.0` (matches pandas-ta default `asint=True`).
pub fn decreasing(close: &[f64], length: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_period(length, close.len())?;

    let n = close.len();
    let mut out = vec![0.0; n];

    for i in length..n {
        let a = close[i];
        let b = close[i - length];
        if a.is_nan() || b.is_nan() {
            out[i] = 0.0;
        } else {
            out[i] = bool_to_f64((a - b) < 0.0);
        }
    }

    Ok(out)
}

/// Long Run (`pandas-ta: long_run`)
pub fn long_run(fast: &[f64], slow: &[f64], length: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(fast, "fast")?;
    validate_lengths_match(&[(fast, "fast"), (slow, "slow")])?;
    validate_period(length, fast.len())?;

    let inc_fast = increasing(fast, length)?;
    let dec_slow = decreasing(slow, length)?;
    let inc_slow = increasing(slow, length)?;

    let out: Vec<f64> = inc_fast
        .iter()
        .zip(&dec_slow)
        .zip(&inc_slow)
        .map(|((&ifast, &dslow), &islow)| bool_to_f64(ifast > 0.0 && (dslow > 0.0 || islow > 0.0)))
        .collect();

    Ok(out)
}

/// Short Run (`pandas-ta: short_run`)
pub fn short_run(fast: &[f64], slow: &[f64], length: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(fast, "fast")?;
    validate_lengths_match(&[(fast, "fast"), (slow, "slow")])?;
    validate_period(length, fast.len())?;

    let dec_fast = decreasing(fast, length)?;
    let inc_slow = increasing(slow, length)?;
    let dec_slow = decreasing(slow, length)?;

    let out: Vec<f64> = dec_fast
        .iter()
        .zip(&inc_slow)
        .zip(&dec_slow)
        .map(|((&dfast, &islow), &dslow)| bool_to_f64(dfast > 0.0 && (islow > 0.0 || dslow > 0.0)))
        .collect();

    Ok(out)
}

/// Archer Moving Averages Trends (`pandas-ta: amat`)
pub fn amat(
    close: &[f64],
    fast: usize,
    slow: usize,
    lookback: usize,
    mamode: &str,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(close, "close")?;

    let mut fast_p = fast.max(1);
    let mut slow_p = slow.max(1);
    if slow_p < fast_p {
        std::mem::swap(&mut fast_p, &mut slow_p);
    }
    let lookback = lookback.max(1);

    let fast_ma = ma_by_name(mamode, close, fast_p)?;
    let slow_ma = ma_by_name(mamode, close, slow_p)?;

    let lr = long_run(&fast_ma, &slow_ma, lookback)?;
    let sr = short_run(&fast_ma, &slow_ma, lookback)?;

    Ok((lr, sr))
}

/// Chande Kroll Stop (`pandas-ta: cksp`)
pub fn cksp(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    p: usize,
    x: f64,
    q: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(p, close.len())?;
    validate_period(q, close.len())?;
    if x <= 0.0 || !x.is_finite() {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: format!("x must be positive finite, got {x}"),
        });
    }

    let atr_p = crate::indicators::volatility::atr(high, low, close, p)?;
    let hh = crate::utils::rolling_max(high, p);
    let ll = crate::utils::rolling_min(low, p);

    let long_stop_1: Vec<f64> = hh
        .iter()
        .zip(&atr_p)
        .map(|(&h, &a)| {
            if h.is_nan() || a.is_nan() {
                f64::NAN
            } else {
                h - x * a
            }
        })
        .collect();
    let short_stop_1: Vec<f64> = ll
        .iter()
        .zip(&atr_p)
        .map(|(&l, &a)| {
            if l.is_nan() || a.is_nan() {
                f64::NAN
            } else {
                l + x * a
            }
        })
        .collect();

    let long_stop = crate::utils::rolling_max(&long_stop_1, q);
    let short_stop = crate::utils::rolling_min(&short_stop_1, q);

    Ok((long_stop, short_stop))
}

/// Random Walk Index (`pandas-ta: rwi`)
pub fn rwi(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    length: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(length, close.len())?;
    validate_min_length(close, length + 1)?;

    let atr_ = crate::indicators::volatility::atr(high, low, close, length)?;
    let denom_scale = (length as f64).sqrt();

    let low_shift = shift(low, length);
    let high_shift = shift(high, length);

    let mut rwi_high = vec![f64::NAN; close.len()];
    let mut rwi_low = vec![f64::NAN; close.len()];

    for i in 0..close.len() {
        let denom = atr_[i] * denom_scale;
        if high[i].is_nan() || low[i].is_nan() || denom.is_nan() || is_zero(denom) {
            continue;
        }

        if !low_shift[i].is_nan() {
            rwi_high[i] = (high[i] - low_shift[i]) / denom;
        }
        if !high_shift[i].is_nan() {
            rwi_low[i] = (high_shift[i] - low[i]) / denom;
        }
    }

    Ok((rwi_high, rwi_low))
}

/// Decay (`pandas-ta: decay`)
pub fn decay(close: &[f64], length: usize, mode: &str) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    let length = length.max(1);

    let n = close.len();
    let mut out = vec![0.0; n];
    out[0] = close[0];

    let mode = mode.to_ascii_lowercase();
    if mode == "exp" || mode == "exponential" {
        let rate = 1.0 - (1.0 / length as f64);
        for i in 1..n {
            let x = if close[i].is_nan() { 0.0 } else { close[i] };
            out[i] = 0.0_f64.max(x).max(out[i - 1] * rate);
        }
    } else {
        let rate = 1.0 / length as f64;
        for i in 1..n {
            let x = if close[i].is_nan() { 0.0 } else { close[i] };
            out[i] = 0.0_f64.max(x).max(out[i - 1] - rate);
        }
    }

    Ok(out)
}

/// Trendflex (`pandas-ta: trendflex`)
pub fn trendflex(close: &[f64], length: usize, smooth: usize, alpha: f64) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    if length == 0 || smooth == 0 {
        return Err(HazeError::InvalidPeriod {
            period: length.max(smooth),
            data_len: close.len(),
        });
    }
    validate_min_length(close, length.max(smooth) + 1)?;

    // pandas-ta defaults
    let pi = std::f64::consts::PI;
    let sqrt2 = 1.414;

    let n = close.len();
    let mut f = vec![0.0; n];
    let mut ms = vec![0.0; n];
    let mut out = vec![0.0; n];

    let ratio = 2.0 * sqrt2 / (smooth as f64);
    let a = (-pi * ratio).exp();
    let b = 2.0 * a * (180.0 * ratio).cos();
    let c = a * a - b + 1.0;

    for i in 2..n {
        f[i] = 0.5 * c * (close[i] + close[i - 1]) + b * f[i - 1] - a * a * f[i - 2];
    }

    let length_f = length as f64;
    for i in length..n {
        let mut sum = 0.0;
        for j in 1..length {
            sum += f[i] - f[i - j];
        }
        sum /= length_f;

        ms[i] = alpha * sum * sum + (1.0 - alpha) * ms[i - 1];
        if ms[i] != 0.0 {
            out[i] = sum / ms[i].sqrt();
        }
    }

    for v in out.iter_mut().take(length) {
        *v = f64::NAN;
    }

    Ok(out)
}

// =============================================================================
// Volatility
// =============================================================================

/// Acceleration Bands (`pandas-ta: accbands`)
pub fn accbands(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    length: usize,
    c: f64,
    _drift: usize,
    mamode: &str,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_period(length, close.len())?;

    let c = if c.is_finite() { c } else { 4.0 };
    let n = close.len();

    let mut lower_raw = vec![f64::NAN; n];
    let mut upper_raw = vec![f64::NAN; n];

    for i in 0..n {
        let denom = high[i] + low[i];
        if denom.is_nan() {
            continue;
        }
        let denom = if is_zero(denom) { f64::EPSILON } else { denom };

        let hl_range = non_zero_range(high[i], low[i]);
        let mut hl_ratio = hl_range / denom;
        hl_ratio *= c;

        lower_raw[i] = low[i] * (1.0 - hl_ratio);
        upper_raw[i] = high[i] * (1.0 + hl_ratio);
    }

    let lower = ma_by_name(mamode, &lower_raw, length)?;
    let mid = ma_by_name(mamode, close, length)?;
    let upper = ma_by_name(mamode, &upper_raw, length)?;

    Ok((lower, mid, upper))
}

/// ATR Trailing Stop (`pandas-ta: atrts`)
pub fn atrts(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    length: usize,
    ma_length: usize,
    k: f64,
    mamode: &str,
    percent: bool,
) -> HazeResult<Vec<f64>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let length = length.max(1);
    let ma_length = ma_length.max(1);

    let atr_ = atr(high, low, close, length)?;
    let ma_ = ma_by_name(mamode, close, ma_length)?;

    let n = close.len();
    let start = length.max(ma_length);
    let mut out = vec![f64::NAN; n];

    for i in start..n {
        let pr = out[i - 1];
        let is_up = close[i] > ma_[i];
        let atrv = atr_[i] * k;

        if is_up {
            let mut v = close[i] - atrv;
            if pr.is_finite() && v < pr {
                v = pr;
            }
            out[i] = v;
        } else {
            let mut v = close[i] + atrv;
            if pr.is_finite() && v > pr {
                v = pr;
            }
            out[i] = v;
        }

        if percent && out[i].is_finite() && is_not_zero(close[i]) {
            out[i] *= 100.0 / close[i];
        }
    }

    Ok(out)
}

/// Holt-Winter Channel (`pandas-ta: hwc`)
pub fn hwc(
    close: &[f64],
    scalar: f64,
    channels: bool,
    na: f64,
    nb: f64,
    nc: f64,
    nd: f64,
) -> HazeResult<BTreeMap<String, Vec<f64>>> {
    validate_not_empty(close, "close")?;

    let scalar = if scalar.is_finite() { scalar } else { 1.0 };
    let na = if na > 0.0 && na < 1.0 { na } else { 0.2 };
    let nb = if nb > 0.0 && nb < 1.0 { nb } else { 0.1 };
    let nc = if nc > 0.0 && nc < 1.0 { nc } else { 0.1 };
    let nd = if nd > 0.0 && nd < 1.0 { nd } else { 0.1 };

    let n = close.len();
    let mut mid = vec![0.0; n];
    let mut upper = vec![0.0; n];
    let mut lower = vec![0.0; n];
    let mut width = vec![f64::NAN; n];
    let mut pct = vec![f64::NAN; n];

    let mut last_a = 0.0;
    let mut last_v = 0.0;
    let mut last_var = 0.0;
    let mut last_f = close[0];
    let mut last_price = close[0];
    let mut last_result = close[0];

    for i in 0..n {
        let f = (1.0 - na) * (last_f + last_v + 0.5 * last_a) + na * close[i];
        let v = (1.0 - nb) * (last_v + last_a) + nb * (f - last_f);
        let a = (1.0 - nc) * last_a + nc * (v - last_v);
        mid[i] = f + v + 0.5 * a;

        let var =
            (1.0 - nd) * last_var + nd * (last_price - last_result) * (last_price - last_result);
        let stddev = last_var.sqrt();
        upper[i] = mid[i] + scalar * stddev;
        lower[i] = mid[i] - scalar * stddev;

        if channels {
            width[i] = upper[i] - lower[i];
            pct[i] = (close[i] - lower[i]) / (width[i] + f64::EPSILON);
        }

        last_price = close[i];
        last_a = a;
        last_f = f;
        last_v = v;
        last_var = var;
        last_result = mid[i];
    }

    let mut out = BTreeMap::<String, Vec<f64>>::new();
    out.insert("HWM".to_string(), mid);
    out.insert("HWL".to_string(), lower);
    out.insert("HWU".to_string(), upper);
    if channels {
        out.insert("HWW".to_string(), width);
        out.insert("HWPCT".to_string(), pct);
    }
    Ok(out)
}

/// Keltner Channels (`pandas-ta: kc`)
pub fn kc(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    length: usize,
    scalar: f64,
    tr: bool,
    mamode: &str,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;

    let length = length.max(1);
    validate_period(length, close.len())?;

    let range_ = if tr {
        true_range(high, low, close, 1)?
    } else {
        high.iter()
            .zip(low)
            .map(|(&h, &l)| non_zero_range(h, l))
            .collect::<Vec<f64>>()
    };

    let basis = ma_by_name(mamode, close, length)?;
    let band = ma_by_name(mamode, &range_, length)?;

    let n = close.len();
    let mut lower = vec![f64::NAN; n];
    let mut upper = vec![f64::NAN; n];
    for i in 0..n {
        if basis[i].is_nan() || band[i].is_nan() {
            continue;
        }
        lower[i] = basis[i] - scalar * band[i];
        upper[i] = basis[i] + scalar * band[i];
    }

    Ok((lower, basis, upper))
}

/// Price Distance (`pandas-ta: pdist`)
pub fn pdist(
    open: &[f64],
    high: &[f64],
    low: &[f64],
    close: &[f64],
    drift: usize,
) -> HazeResult<Vec<f64>> {
    validate_not_empty(open, "open")?;
    validate_lengths_match(&[
        (open, "open"),
        (high, "high"),
        (low, "low"),
        (close, "close"),
    ])?;

    let drift = drift.max(1);
    let n = close.len();
    let close_shift = shift(close, drift);

    let mut out = vec![f64::NAN; n];
    for i in 0..n {
        let base = 2.0 * non_zero_range(high[i], low[i]);
        let prev_close = close_shift[i];
        let term2 = non_zero_range(open[i], prev_close).abs();
        let term3 = non_zero_range(close[i], open[i]).abs();
        if base.is_nan() || term2.is_nan() || term3.is_nan() {
            continue;
        }
        out[i] = base + term2 - term3;
    }

    Ok(out)
}

/// Relative Volatility Index (`pandas-ta: rvi`)
pub fn rvi(
    close: &[f64],
    high: Option<&[f64]>,
    low: Option<&[f64]>,
    length: usize,
    scalar: f64,
    refined: bool,
    thirds: bool,
    mamode: &str,
    drift: usize,
) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;

    let length = length.max(1);
    let scalar = if scalar.is_finite() { scalar } else { 100.0 };
    let drift = drift.max(1);

    fn rvi_core(
        source: &[f64],
        length: usize,
        scalar: f64,
        mamode: &str,
        drift: usize,
    ) -> HazeResult<Vec<f64>> {
        let std = crate::utils::stdev(source, length);
        let (pos, neg) = unsigned_differences(source, drift);

        let n = source.len();
        let mut pos_std = vec![0.0; n];
        let mut neg_std = vec![0.0; n];
        for i in 0..n {
            if std[i].is_nan() {
                pos_std[i] = f64::NAN;
                neg_std[i] = f64::NAN;
            } else {
                pos_std[i] = pos[i] * std[i];
                neg_std[i] = neg[i] * std[i];
            }
        }

        let pos_avg = ma_by_name(mamode, &pos_std, length)?;
        let neg_avg = ma_by_name(mamode, &neg_std, length)?;

        let mut out = vec![f64::NAN; n];
        for i in 0..n {
            let pa = pos_avg[i];
            let na = neg_avg[i];
            if pa.is_nan() || na.is_nan() {
                continue;
            }
            let denom = pa + na;
            if is_zero(denom) {
                continue;
            }
            out[i] = scalar * pa / denom;
        }

        Ok(out)
    }

    if refined || thirds {
        let high = high.ok_or_else(|| HazeError::InvalidValue {
            index: 0,
            message: "high is required when refined or thirds is true".to_string(),
        })?;
        let low = low.ok_or_else(|| HazeError::InvalidValue {
            index: 0,
            message: "low is required when refined or thirds is true".to_string(),
        })?;
        validate_lengths_match(&[(close, "close"), (high, "high"), (low, "low")])?;

        let high_rvi = rvi_core(high, length, scalar, mamode, drift)?;
        let low_rvi = rvi_core(low, length, scalar, mamode, drift)?;

        if refined {
            return Ok(high_rvi
                .iter()
                .zip(&low_rvi)
                .map(|(&h, &l)| {
                    if h.is_nan() || l.is_nan() {
                        f64::NAN
                    } else {
                        0.5 * (h + l)
                    }
                })
                .collect());
        }

        let close_rvi = rvi_core(close, length, scalar, mamode, drift)?;
        return Ok(high_rvi
            .iter()
            .zip(&low_rvi)
            .zip(&close_rvi)
            .map(|((&h, &l), &c)| {
                if h.is_nan() || l.is_nan() || c.is_nan() {
                    f64::NAN
                } else {
                    (h + l + c) / 3.0
                }
            })
            .collect());
    }

    rvi_core(close, length, scalar, mamode, drift)
}

/// Elders Thermometer (`pandas-ta: thermo`)
pub fn thermo(
    high: &[f64],
    low: &[f64],
    length: usize,
    long: f64,
    short: f64,
    mamode: &str,
    asint: bool,
    drift: usize,
) -> HazeResult<BTreeMap<String, Vec<f64>>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low")])?;

    let length = length.max(1);
    let drift = drift.max(1);

    let n = high.len();
    let low_shift = shift(low, drift);
    let high_shift = shift(high, drift);

    let mut thermo = vec![f64::NAN; n];
    for i in 0..n {
        let tl = (low_shift[i] - low[i]).abs();
        let th = (high[i] - high_shift[i]).abs();
        if tl.is_nan() || th.is_nan() {
            continue;
        }
        thermo[i] = tl.max(th);
    }

    let thermo_ma = ma_by_name(mamode, &thermo, length)?;
    let mut thermo_long = vec![f64::NAN; n];
    let mut thermo_short = vec![f64::NAN; n];

    // Note: asint parameter currently has no effect as bool_to_f64 always returns 0.0/1.0
    let _ = asint;
    for i in 0..n {
        if thermo[i].is_nan() || thermo_ma[i].is_nan() {
            continue;
        }
        let l = thermo[i] < (thermo_ma[i] * long);
        let s = thermo[i] > (thermo_ma[i] * short);
        thermo_long[i] = bool_to_f64(l);
        thermo_short[i] = bool_to_f64(s);
    }

    let mut out = BTreeMap::<String, Vec<f64>>::new();
    out.insert("THERMO".to_string(), thermo);
    out.insert("THERMOma".to_string(), thermo_ma);
    out.insert("THERMOl".to_string(), thermo_long);
    out.insert("THERMOs".to_string(), thermo_short);
    Ok(out)
}

// =============================================================================
// Volume
// =============================================================================

/// Archer On Balance Volume (`pandas-ta: aobv`)
pub fn aobv(
    close: &[f64],
    volume: &[f64],
    fast: usize,
    slow: usize,
    max_lookback: usize,
    min_lookback: usize,
    mamode: &str,
    run_length: usize,
) -> HazeResult<BTreeMap<String, Vec<f64>>> {
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[(close, "close"), (volume, "volume")])?;

    let mut fast = fast.max(1);
    let mut slow = slow.max(1);
    if slow < fast {
        std::mem::swap(&mut fast, &mut slow);
    }

    let run_length = run_length.max(1);
    let max_lookback = max_lookback.max(1);
    let min_lookback = min_lookback.max(1);

    let obv_ = obv(close, volume)?;
    let obv_min = crate::utils::rolling_min(&obv_, min_lookback);
    let obv_max = crate::utils::rolling_max(&obv_, max_lookback);

    let maf = ma_by_name(mamode, &obv_, fast)?;
    let mas = ma_by_name(mamode, &obv_, slow)?;

    let obv_long = long_run(&maf, &mas, run_length)?;
    let obv_short = short_run(&maf, &mas, run_length)?;

    let mut out = BTreeMap::<String, Vec<f64>>::new();
    out.insert("OBV".to_string(), obv_);
    out.insert("OBV_min".to_string(), obv_min);
    out.insert("OBV_max".to_string(), obv_max);
    out.insert("OBV_fast".to_string(), maf);
    out.insert("OBV_slow".to_string(), mas);
    out.insert("AOBV_LR".to_string(), obv_long);
    out.insert("AOBV_SR".to_string(), obv_short);
    Ok(out)
}

/// Klinger Volume Oscillator (`pandas-ta: kvo`)
pub fn kvo(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    volume: &[f64],
    fast: usize,
    slow: usize,
    signal: usize,
    mamode: &str,
    drift: usize,
) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[
        (high, "high"),
        (low, "low"),
        (close, "close"),
        (volume, "volume"),
    ])?;

    let fast = fast.max(1);
    let slow = slow.max(1);
    let signal = signal.max(1);
    let drift = drift.max(1);

    let hlc = hlc3(high, low, close)?;
    let sign_series = signed_series(&hlc, drift);

    let n = close.len();
    let mut signed_volume = vec![f64::NAN; n];
    for i in 0..n {
        if sign_series[i].is_nan() {
            continue;
        }
        signed_volume[i] = volume[i] * sign_series[i];
    }

    let fast_ma = ma_by_name(mamode, &signed_volume, fast)?;
    let slow_ma = ma_by_name(mamode, &signed_volume, slow)?;

    let mut kvo = vec![f64::NAN; n];
    for i in 0..n {
        if fast_ma[i].is_nan() || slow_ma[i].is_nan() {
            continue;
        }
        kvo[i] = fast_ma[i] - slow_ma[i];
    }

    let signal_line = ma_by_name(mamode, &kvo, signal)?;
    Ok((kvo, signal_line))
}

/// Percentage Volume Oscillator (`pandas-ta: pvo`)
pub fn pvo(
    volume: &[f64],
    fast: usize,
    slow: usize,
    signal: usize,
    scalar: f64,
) -> HazeResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
    validate_not_empty(volume, "volume")?;

    let mut fast = fast.max(1);
    let mut slow = slow.max(1);
    if slow < fast {
        std::mem::swap(&mut fast, &mut slow);
    }
    let signal = signal.max(1);
    let scalar = if scalar.is_finite() { scalar } else { 100.0 };

    let fastma = ema(volume, fast)?;
    let slowma = ema(volume, slow)?;

    let n = volume.len();
    let mut pvo = vec![f64::NAN; n];
    for i in 0..n {
        let den = slowma[i];
        if fastma[i].is_nan() || den.is_nan() || is_zero(den) {
            continue;
        }
        pvo[i] = scalar * (fastma[i] - den) / den;
    }

    let signalma = crate::utils::ma::ema_allow_nan(&pvo, signal)?;
    let histogram: Vec<f64> = pvo
        .iter()
        .zip(&signalma)
        .map(|(&p, &s)| {
            if p.is_nan() || s.is_nan() {
                f64::NAN
            } else {
                p - s
            }
        })
        .collect();

    Ok((pvo, histogram, signalma))
}

/// Price-Volume (`pandas-ta: pvol`)
pub fn pvol(close: &[f64], volume: &[f64], signed: bool) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[(close, "close"), (volume, "volume")])?;

    let n = close.len();
    let mut out: Vec<f64> = close.iter().zip(volume).map(|(&c, &v)| c * v).collect();

    if signed {
        let s = signed_series(close, 1);
        for i in 0..n {
            if s[i].is_nan() {
                out[i] = f64::NAN;
            } else {
                out[i] *= s[i];
            }
        }
    }

    Ok(out)
}

/// Price Volume Rank (`pandas-ta: pvr`)
pub fn pvr(close: &[f64], volume: &[f64], drift: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[(close, "close"), (volume, "volume")])?;

    let drift = drift.max(1);
    let n = close.len();
    let mut out = vec![f64::NAN; n];

    for i in 0..n {
        let close_diff = if i >= drift {
            close[i] - close[i - drift]
        } else {
            0.0
        };
        let vol_diff = if i >= drift {
            volume[i] - volume[i - drift]
        } else {
            0.0
        };

        out[i] = if close_diff >= 0.0 && vol_diff >= 0.0 {
            1.0
        } else if close_diff >= 0.0 && vol_diff < 0.0 {
            2.0
        } else if close_diff < 0.0 && vol_diff >= 0.0 {
            3.0
        } else {
            4.0
        };
    }

    Ok(out)
}

/// Time Segmented Volume (`pandas-ta: tsv`)
pub fn tsv(
    close: &[f64],
    volume: &[f64],
    length: usize,
    signal: usize,
    mamode: &str,
    drift: usize,
) -> HazeResult<BTreeMap<String, Vec<f64>>> {
    validate_not_empty(close, "close")?;
    validate_lengths_match(&[(close, "close"), (volume, "volume")])?;

    let length = length.max(1);
    let signal = signal.max(1);
    let drift = drift.max(1);

    let n = close.len();
    let s = signed_series(close, 1);

    let mut signed_volume = vec![f64::NAN; n];
    for i in 0..n {
        if s[i].is_nan() {
            continue;
        }
        let v = volume[i] * s[i];
        signed_volume[i] = if v < 0.0 { -v } else { v };
    }

    let mut cvd = vec![f64::NAN; n];
    for i in drift..n {
        if signed_volume[i].is_nan() {
            continue;
        }
        cvd[i] = signed_volume[i] * (close[i] - close[i - drift]);
    }

    let tsv = rolling_sum_strict(&cvd, length);
    let signal_ = ma_by_name(mamode, &tsv, signal)?;

    let mut ratio = vec![f64::NAN; n];
    for i in 0..n {
        if tsv[i].is_nan() || signal_[i].is_nan() || is_zero(signal_[i]) {
            continue;
        }
        ratio[i] = tsv[i] / signal_[i];
    }

    let mut out = BTreeMap::<String, Vec<f64>>::new();
    out.insert("TSV".to_string(), tsv);
    out.insert("TSVs".to_string(), signal_);
    out.insert("TSVr".to_string(), ratio);
    Ok(out)
}

/// Volume Heatmap (`pandas-ta: vhm`)
pub fn vhm(volume: &[f64], length: usize, std_length: usize, mamode: &str) -> HazeResult<Vec<f64>> {
    validate_not_empty(volume, "volume")?;

    let length = length.max(1);
    let std_length = std_length.max(1);
    validate_min_length(volume, std_length)?;

    let mu = ma_by_name(mamode, volume, length)?;

    let n = volume.len();
    let start = n - std_length;
    let window = &volume[start..];
    if window.iter().any(|v| v.is_nan()) {
        return Err(HazeError::InvalidValue {
            index: start,
            message: "volume contains NaN in selected std_length window".to_string(),
        });
    }

    let mean = window.iter().sum::<f64>() / (std_length as f64);
    let mut var = 0.0;
    for &v in window {
        let d = v - mean;
        var += d * d;
    }
    var /= std_length as f64;
    let std = var.sqrt().max(f64::EPSILON);

    let mut out = vec![f64::NAN; n];
    for i in 0..n {
        if mu[i].is_nan() {
            continue;
        }
        out[i] = (volume[i] - mu[i]) / std;
    }

    Ok(out)
}
