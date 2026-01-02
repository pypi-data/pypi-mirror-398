// indicators/cycle.rs - 周期指标（Hilbert Transform）
//
// 基于 Hilbert Transform 的周期分析指标

use crate::errors::validation::{validate_min_length, validate_not_empty};
use crate::errors::HazeResult;
use crate::init_result;
use crate::utils::math::is_not_zero;
use std::f64::consts::PI;

/// HT_DCPERIOD - Hilbert Transform - Dominant Cycle Period
///
/// 主周期检测，识别市场的主导周期
///
/// # 参数
/// - `values`: 输入序列（通常是收盘价）
///
/// # 返回
/// - `HazeResult<Vec<f64>>` 主周期值序列
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `InsufficientData`: 数据长度小于 33
pub fn ht_dcperiod(values: &[f64]) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_min_length(values, 33)?;

    let n = values.len();
    let mut result = init_result!(n);

    // Hilbert Transform requires detrending
    let mut detrended = vec![0.0; n];
    for i in 10..n {
        detrended[i] = (values[i]
            + 2.0 * values[i - 2]
            + 3.0 * values[i - 4]
            + 3.0 * values[i - 6]
            + 2.0 * values[i - 8]
            + values[i - 10])
            / 12.0;
    }

    // InPhase and Quadrature components
    let mut in_phase = vec![0.0; n];
    let mut quadrature = vec![0.0; n];

    for i in 10..n {
        in_phase[i] = detrended[i];
        quadrature[i] = (detrended[i - 2] + 2.0 * detrended[i - 4] + detrended[i - 6]) / 4.0;
    }

    // Smooth the I and Q components
    let mut smooth_i = vec![0.0; n];
    let mut smooth_q = vec![0.0; n];

    for i in 10..n {
        smooth_i[i] =
            (4.0 * in_phase[i] + 3.0 * in_phase[i - 1] + 2.0 * in_phase[i - 2] + in_phase[i - 3])
                / 10.0;
        smooth_q[i] = (4.0 * quadrature[i]
            + 3.0 * quadrature[i - 1]
            + 2.0 * quadrature[i - 2]
            + quadrature[i - 3])
            / 10.0;
    }

    // Homodyne Discriminator
    let mut period = vec![0.0; n];
    for i in 7..n {
        let re = smooth_i[i] * smooth_i[i - 1] + smooth_q[i] * smooth_q[i - 1];
        let im = smooth_i[i] * smooth_q[i - 1] - smooth_q[i] * smooth_i[i - 1];

        let phase = if is_not_zero(im) && is_not_zero(re) {
            (im / re).atan()
        } else {
            0.0
        };

        let delta_phase = (phase - (smooth_i[i - 1] * smooth_q[i - 1]).atan()).abs();

        if delta_phase < 0.1 {
            period[i] = period[i - 1];
        } else if delta_phase > 0.0 {
            period[i] = (2.0 * PI / delta_phase).clamp(6.0, 50.0);
        }
    }

    // Smooth the period
    for i in 32..n {
        result[i] = (period[i] + 2.0 * period[i - 1] + period[i - 2]) / 4.0;
    }

    Ok(result)
}

/// HT_DCPHASE - Hilbert Transform - Dominant Cycle Phase
///
/// 主周期相位
///
/// # 参数
/// - `values`: 输入序列
///
/// # 返回
/// - `HazeResult<Vec<f64>>` 相位值序列（角度，0-360度）
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `InsufficientData`: 数据长度小于 33
pub fn ht_dcphase(values: &[f64]) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_min_length(values, 33)?;

    let n = values.len();
    let mut result = init_result!(n);

    // Detrend
    let mut detrended = vec![0.0; n];
    for i in 10..n {
        detrended[i] = (values[i]
            + 2.0 * values[i - 2]
            + 3.0 * values[i - 4]
            + 3.0 * values[i - 6]
            + 2.0 * values[i - 8]
            + values[i - 10])
            / 12.0;
    }

    // InPhase and Quadrature
    let mut in_phase = vec![0.0; n];
    let mut quadrature = vec![0.0; n];

    for i in 10..n {
        in_phase[i] = detrended[i];
        quadrature[i] = (detrended[i - 2] + 2.0 * detrended[i - 4] + detrended[i - 6]) / 4.0;
    }

    // Smooth
    let mut smooth_i = vec![0.0; n];
    let mut smooth_q = vec![0.0; n];

    for i in 6..n {
        smooth_i[i] =
            (4.0 * in_phase[i] + 3.0 * in_phase[i - 1] + 2.0 * in_phase[i - 2] + in_phase[i - 3])
                / 10.0;
        smooth_q[i] = (4.0 * quadrature[i]
            + 3.0 * quadrature[i - 1]
            + 2.0 * quadrature[i - 2]
            + quadrature[i - 3])
            / 10.0;
    }

    // Calculate phase
    for i in 32..n {
        result[i] = if is_not_zero(smooth_i[i]) {
            (smooth_q[i] / smooth_i[i]).atan().to_degrees()
        } else {
            0.0
        };

        // Normalize to 0-360
        if result[i] < 0.0 {
            result[i] += 360.0;
        }
    }

    Ok(result)
}

/// HT_PHASOR - Hilbert Transform - Phasor Components
///
/// 相量分量（InPhase 和 Quadrature）
///
/// # 参数
/// - `values`: 输入序列
///
/// # 返回
/// - `HazeResult<(Vec<f64>, Vec<f64>)>` (in_phase, quadrature) 元组
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `InsufficientData`: 数据长度小于 33
pub fn ht_phasor(values: &[f64]) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_min_length(values, 33)?;

    let n = values.len();
    let mut in_phase_result = init_result!(n);
    let mut quadrature_result = init_result!(n);

    // Detrend
    let mut detrended = vec![0.0; n];
    for i in 10..n {
        detrended[i] = (values[i]
            + 2.0 * values[i - 2]
            + 3.0 * values[i - 4]
            + 3.0 * values[i - 6]
            + 2.0 * values[i - 8]
            + values[i - 10])
            / 12.0;
    }

    // InPhase and Quadrature
    let mut in_phase = vec![0.0; n];
    let mut quadrature = vec![0.0; n];

    for i in 10..n {
        in_phase[i] = detrended[i];
        quadrature[i] = (detrended[i - 2] + 2.0 * detrended[i - 4] + detrended[i - 6]) / 4.0;
    }

    // Smooth
    for i in 32..n {
        in_phase_result[i] =
            (4.0 * in_phase[i] + 3.0 * in_phase[i - 1] + 2.0 * in_phase[i - 2] + in_phase[i - 3])
                / 10.0;
        quadrature_result[i] = (4.0 * quadrature[i]
            + 3.0 * quadrature[i - 1]
            + 2.0 * quadrature[i - 2]
            + quadrature[i - 3])
            / 10.0;
    }

    Ok((in_phase_result, quadrature_result))
}

/// HT_SINE - Hilbert Transform - SineWave Indicator
///
/// 正弦波指标（LeadSine 和 Sine）
///
/// # 参数
/// - `values`: 输入序列
///
/// # 返回
/// - `HazeResult<(Vec<f64>, Vec<f64>)>` (sine, lead_sine) 元组
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `InsufficientData`: 数据长度小于 33
pub fn ht_sine(values: &[f64]) -> HazeResult<(Vec<f64>, Vec<f64>)> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_min_length(values, 33)?;

    let n = values.len();
    let mut sine = init_result!(n);
    let mut lead_sine = init_result!(n);

    // Get phase (已验证，不会失败)
    let phase = ht_dcphase(values)?;

    for i in 32..n {
        if !phase[i].is_nan() {
            sine[i] = phase[i].to_radians().sin();
            lead_sine[i] = (phase[i] + 45.0).to_radians().sin();
        }
    }

    Ok((sine, lead_sine))
}

/// HT_TRENDMODE - Hilbert Transform - Trend vs Cycle Mode
///
/// 趋势模式检测（0=区间震荡，1=趋势）
///
/// # 参数
/// - `values`: 输入序列
///
/// # 返回
/// - `HazeResult<Vec<f64>>` 模式序列（0 或 1）
///
/// # 错误
/// - `EmptyInput`: 输入为空
/// - `InsufficientData`: 数据长度小于 63
pub fn ht_trendmode(values: &[f64]) -> HazeResult<Vec<f64>> {
    // Fail-Fast 验证
    validate_not_empty(values, "values")?;
    validate_min_length(values, 63)?;

    let n = values.len();
    let mut result = init_result!(n);

    // Get dominant cycle period (已验证，不会失败)
    let period = ht_dcperiod(values)?;

    // Calculate trend indicators
    let mut trend_count = 0;

    for i in 63..n {
        // If period is increasing, likely in trend
        let period_slope = if i > 63 {
            period[i] - period[i - 1]
        } else {
            0.0
        };

        // Trend detection logic
        if period[i] > 40.0 || period_slope > 1.0 {
            trend_count += 1;
        } else if period[i] < 15.0 {
            trend_count = (trend_count - 1).max(0);
        }

        // Smooth the trend mode
        result[i] = if trend_count > 3 { 1.0 } else { 0.0 };
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::errors::HazeError;

    #[test]
    fn test_ht_dcperiod() {
        let values: Vec<f64> = (0..100)
            .map(|i| (i as f64 * 0.1).sin() * 10.0 + 100.0)
            .collect();
        let result = ht_dcperiod(&values).unwrap();

        assert_eq!(result.len(), values.len());
        // First 32 values should be NaN
        assert!(result[0].is_nan());
        assert!(result[31].is_nan());
        // After warmup, should have values
        assert!(result.len() > 40);
        assert!(!result[40].is_nan());
    }

    #[test]
    fn test_ht_phasor() {
        let values: Vec<f64> = (0..100)
            .map(|i| (i as f64 * 0.1).sin() * 10.0 + 100.0)
            .collect();
        let (in_phase, quadrature) = ht_phasor(&values).unwrap();

        assert_eq!(in_phase.len(), values.len());
        assert_eq!(quadrature.len(), values.len());
    }

    #[test]
    fn test_ht_dcperiod_empty_input() {
        let result = ht_dcperiod(&[]);
        assert!(matches!(result, Err(HazeError::EmptyInput { .. })));
    }

    #[test]
    fn test_ht_dcperiod_insufficient_data() {
        let values = vec![1.0; 32]; // 需要 >= 33
        let result = ht_dcperiod(&values);
        assert!(matches!(result, Err(HazeError::InsufficientData { .. })));
    }

    #[test]
    fn test_ht_trendmode_minimum_length() {
        let values = vec![1.0; 62]; // 需要 >= 63
        let result = ht_trendmode(&values);
        assert!(matches!(result, Err(HazeError::InsufficientData { .. })));
    }

    #[test]
    fn test_ht_sine() {
        let values: Vec<f64> = (0..100)
            .map(|i| (i as f64 * 0.1).sin() * 10.0 + 100.0)
            .collect();
        let (sine, lead_sine) = ht_sine(&values).unwrap();

        assert_eq!(sine.len(), values.len());
        assert_eq!(lead_sine.len(), values.len());
        // 有效值应在 [-1, 1] 范围内
        for &sine_value in sine.iter().skip(40) {
            if !sine_value.is_nan() {
                assert!((-1.0..=1.0).contains(&sine_value));
            }
        }
    }
}
