// ml/features.rs - 特征工程模块
#![allow(dead_code)]
//
// 为 SFG 指标提供特征准备和转换功能
// 遵循 KISS 原则: 专注于三种特征类型

use crate::utils::math::{is_not_zero, kahan_sum_iter, should_use_kahan, KAHAN_THRESHOLD_CRITICAL};
use ndarray::{Array1, Array2};

/// 准备 AI SuperTrend 特征
///
/// 特征组成: 价格滞后序列 + ATR 滞后序列
/// 共 lookback * 2 个特征维度
pub fn prepare_supertrend_features(
    close: &[f64],
    atr: &[f64],
    lookback: usize,
) -> (Array2<f64>, Array1<f64>) {
    let n = close.len().saturating_sub(lookback);
    if n == 0 {
        return (Array2::zeros((0, lookback * 2)), Array1::zeros(0));
    }

    let mut features = Array2::zeros((n, lookback * 2));
    let mut targets = Array1::zeros(n);

    for i in 0..n {
        for j in 0..lookback {
            let idx = i + j;
            // 价格滞后特征
            features[[i, j]] = close[idx];
            // ATR 滞后特征
            features[[i, lookback + j]] = if atr[idx].is_nan() { 0.0 } else { atr[idx] };
        }
        // 目标: 下一期的价格变化 (归一化)
        let target_idx = i + lookback;
        if target_idx < close.len() {
            let prev = close[target_idx - 1];
            if is_not_zero(prev) {
                targets[i] = (close[target_idx] - prev) / prev;
            }
        }
    }

    // 标准化特征
    let features = standardize(&features);

    (features, targets)
}

/// 准备 ATR2 特征
///
/// 特征组成: ATR + 价格变化率 + 成交量比率
/// 共 3 个特征维度
pub fn prepare_atr2_features(
    close: &[f64],
    atr: &[f64],
    volume: &[f64],
    window: usize,
) -> (Array2<f64>, Array1<f64>) {
    let n = close.len().saturating_sub(window);
    if n == 0 {
        return (Array2::zeros((0, 3)), Array1::zeros(0));
    }

    // 计算成交量移动平均
    let volume_ma = simple_ma(volume, window);

    let mut features = Array2::zeros((n, 3));
    let mut targets = Array1::zeros(n);

    for i in 0..n {
        let idx = i + window;

        // 特征 1: ATR 值
        features[[i, 0]] = if atr[idx].is_nan() { 0.0 } else { atr[idx] };

        // 特征 2: 价格变化率
        let prev = close[idx - 1];
        if is_not_zero(prev) {
            features[[i, 1]] = (close[idx] - prev) / prev;
        }

        // 特征 3: 成交量比率
        if !volume_ma[i].is_nan() && is_not_zero(volume_ma[i]) {
            features[[i, 2]] = volume[idx] / volume_ma[i];
        } else {
            features[[i, 2]] = 1.0;
        }

        // 目标: 阈值调整值 (基于未来动量)
        if idx + 1 < close.len() {
            let future_return = (close[idx + 1] - close[idx]) / close[idx];
            // 映射到 [-5, 5] 的阈值调整范围
            targets[i] = (future_return * 100.0).clamp(-5.0, 5.0);
        }
    }

    let features = standardize(&features);

    (features, targets)
}

/// 准备 Momentum 特征
///
/// 特征组成: RSI 滞后序列
/// 共 lookback 个特征维度
pub fn prepare_momentum_features(rsi: &[f64], lookback: usize) -> (Array2<f64>, Array1<f64>) {
    let n = rsi.len().saturating_sub(lookback);
    if n == 0 {
        return (Array2::zeros((0, lookback)), Array1::zeros(0));
    }

    let mut features = Array2::zeros((n, lookback));
    let mut targets = Array1::zeros(n);

    for i in 0..n {
        for j in 0..lookback {
            let val = rsi[i + j];
            features[[i, j]] = if val.is_nan() { 50.0 } else { val };
        }

        // 目标: 未来 RSI 变化
        let target_idx = i + lookback;
        if target_idx < rsi.len() && !rsi[target_idx].is_nan() && !rsi[target_idx - 1].is_nan() {
            targets[i] = rsi[target_idx] - rsi[target_idx - 1];
        }
    }

    let features = standardize(&features);

    (features, targets)
}

/// 多项式特征扩展 (degree=2)
///
/// 扩展: 原始特征 + 二次项 + 交叉项
pub fn polynomial_features(features: &Array2<f64>) -> Array2<f64> {
    let (n, m) = features.dim();
    if n == 0 || m == 0 {
        return Array2::zeros((n, 0));
    }

    // 新列数: 原始 + 二次项 + 交叉项
    // = m + m*(m+1)/2
    let new_cols = m + m * (m + 1) / 2;
    let mut poly = Array2::zeros((n, new_cols));

    for i in 0..n {
        let mut col = 0;

        // 原始特征
        for j in 0..m {
            poly[[i, col]] = features[[i, j]];
            col += 1;
        }

        // 二次项和交叉项
        for j in 0..m {
            for k in j..m {
                poly[[i, col]] = features[[i, j]] * features[[i, k]];
                col += 1;
            }
        }
    }

    poly
}

/// 特征标准化 (Z-score normalization)
///
/// 每列: (x - mean) / std
///
/// Uses Kahan summation for improved numerical precision when n >= KAHAN_THRESHOLD_CRITICAL.
/// This is important for ML features where small errors can compound.
pub fn standardize(features: &Array2<f64>) -> Array2<f64> {
    let (n, m) = features.dim();
    if n == 0 || m == 0 {
        return features.clone();
    }

    let mut result = features.clone();
    let use_kahan = should_use_kahan(n, KAHAN_THRESHOLD_CRITICAL);

    for col in 0..m {
        let column = features.column(col);

        // 计算均值 - use Kahan for large feature sets
        let mean: f64 = if use_kahan {
            kahan_sum_iter(column.iter().copied()) / n as f64
        } else {
            column.iter().sum::<f64>() / n as f64
        };

        // 计算标准差 - use Kahan for large feature sets
        let variance: f64 = if use_kahan {
            kahan_sum_iter(column.iter().map(|x| (x - mean).powi(2))) / n as f64
        } else {
            column.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / n as f64
        };
        let std = variance.sqrt();

        // 标准化
        if std > 1e-10 {
            for i in 0..n {
                result[[i, col]] = (features[[i, col]] - mean) / std;
            }
        } else {
            // 标准差太小,置零
            for i in 0..n {
                result[[i, col]] = 0.0;
            }
        }
    }

    result
}

/// 简单移动平均 (辅助函数)
///
/// 返回与输入等长的向量,前 period-1 个值为 NaN
fn simple_ma(data: &[f64], period: usize) -> Vec<f64> {
    let len = data.len();
    let mut result = vec![f64::NAN; len];

    if period == 0 || period > len {
        return result;
    }

    let mut sum = 0.0;
    for i in 0..len {
        sum += data[i];
        if i >= period {
            sum -= data[i - period];
        }
        if i >= period - 1 {
            // 标准右对齐: 第一个有效值在 index period-1
            result[i] = sum / period as f64;
        }
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_prepare_supertrend_features() {
        let close = vec![
            100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0, 107.0, 109.0,
        ];
        let atr = vec![2.0, 2.1, 2.0, 2.2, 2.3, 2.1, 2.4, 2.5, 2.3, 2.6];

        let (features, targets) = prepare_supertrend_features(&close, &atr, 3);

        assert_eq!(features.dim().0, 7); // 10 - 3 = 7
        assert_eq!(features.dim().1, 6); // 3 * 2 = 6
        assert_eq!(targets.len(), 7);
    }

    #[test]
    fn test_prepare_atr2_features() {
        let close = vec![100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0];
        let atr = vec![2.0, 2.1, 2.0, 2.2, 2.3, 2.1, 2.4, 2.5];
        let volume = vec![
            1000.0, 1100.0, 1050.0, 1200.0, 1150.0, 1300.0, 1250.0, 1400.0,
        ];

        let (features, targets) = prepare_atr2_features(&close, &atr, &volume, 3);

        assert_eq!(features.dim().0, 5); // 8 - 3 = 5
        assert_eq!(features.dim().1, 3); // 3 features
        assert_eq!(targets.len(), 5);
    }

    #[test]
    fn test_prepare_momentum_features() {
        let rsi = vec![50.0, 55.0, 52.0, 58.0, 60.0, 57.0, 62.0, 65.0];

        let (features, targets) = prepare_momentum_features(&rsi, 3);

        assert_eq!(features.dim().0, 5); // 8 - 3 = 5
        assert_eq!(features.dim().1, 3); // lookback = 3
        assert_eq!(targets.len(), 5);
    }

    #[test]
    fn test_polynomial_features() {
        let features = Array2::from_shape_vec((2, 2), vec![1.0, 2.0, 3.0, 4.0]).unwrap();

        let poly = polynomial_features(&features);

        // 2 + 2*(2+1)/2 = 2 + 3 = 5
        assert_eq!(poly.dim().1, 5);
        // Row 0: [1, 2, 1*1, 1*2, 2*2] = [1, 2, 1, 2, 4]
        assert_eq!(poly[[0, 0]], 1.0);
        assert_eq!(poly[[0, 1]], 2.0);
        assert_eq!(poly[[0, 2]], 1.0);
        assert_eq!(poly[[0, 3]], 2.0);
        assert_eq!(poly[[0, 4]], 4.0);
    }

    #[test]
    fn test_standardize() {
        let features = Array2::from_shape_vec((3, 2), vec![1.0, 4.0, 2.0, 5.0, 3.0, 6.0]).unwrap();

        let standardized = standardize(&features);

        // 检查每列均值接近 0
        for col in 0..2 {
            let mean: f64 = (0..3).map(|i| standardized[[i, col]]).sum::<f64>() / 3.0;
            assert!(mean.abs() < 1e-10);
        }
    }
}
