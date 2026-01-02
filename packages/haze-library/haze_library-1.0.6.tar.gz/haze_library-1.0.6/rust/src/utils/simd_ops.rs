//! SIMD-Optimized Mathematical Operations
//!
//! # Overview
//! This module provides SIMD-friendly implementations of common mathematical
//! operations used in technical analysis. Rather than using explicit SIMD
//! intrinsics, the code is structured to enable automatic vectorization by
//! the Rust compiler (LLVM), providing portable performance across architectures.
//!
//! # Design Philosophy
//! - **Compiler-Friendly Code**: Simple loops that LLVM can auto-vectorize
//! - **Chunked Processing**: Uses 8-element chunks matching AVX-512 width
//! - **Zero Dependencies**: No external SIMD libraries required
//! - **Numerical Stability**: Chunked summation reduces floating-point errors
//!
//! # Available Functions
//!
//! ## Vector Arithmetic
//! - [`add_vectors`] - Element-wise vector addition
//! - [`sub_vectors`] - Element-wise vector subtraction
//! - [`mul_vectors`] - Element-wise vector multiplication
//! - [`div_vectors`] - Element-wise vector division (fail-fast on zero)
//! - [`scale_vector`] - Scalar multiplication
//!
//! ## Aggregation Operations
//! - [`sum_vector`] - Chunked summation for numerical stability
//! - [`dot_product`] - Dot product with chunked accumulation
//! - [`max_vector`] - Find maximum value
//! - [`min_vector`] - Find minimum value
//! - [`mean_vector`] - Calculate arithmetic mean
//! - [`std_vector`] - Calculate population standard deviation
//!
//! ## Fast Indicator Implementations
//! - [`fast_sma`] - SMA using cumulative sum optimization
//! - [`fast_ema`] - EMA using recursive formula
//! - [`batch_sma`] - Compute multiple SMA periods efficiently
//!
//! # Examples
//! ```rust
//! use haze_library::utils::simd_ops::{add_vectors, dot_product, fast_sma};
//!
//! // Vector operations
//! let a = vec![1.0, 2.0, 3.0, 4.0];
//! let b = vec![5.0, 6.0, 7.0, 8.0];
//! let sum = add_vectors(&a, &b).unwrap();  // [6.0, 8.0, 10.0, 12.0]
//! let dot = dot_product(&a, &b).unwrap();  // 70.0
//!
//! // Fast SMA calculation
//! let prices = vec![100.0, 101.0, 102.0, 103.0, 104.0];
//! let sma = fast_sma(&prices, 3).unwrap();
//! ```
//!
//! # Performance Characteristics
//! - Vector operations: ~2-4x speedup with auto-vectorization enabled
//! - Chunk size of 8 elements aligns with AVX-512 registers
//! - `fast_sma`/`fast_ema` use O(n) sliding window, not O(n*period)
//! - Compile with `-C target-cpu=native` for best performance
//!
//! # Cross-References
//! - [`crate::utils::ma`] - Standard moving average implementations
//! - [`crate::utils::stats`] - Statistical functions with different trade-offs
//! - [`crate::utils::parallel`] - Multi-threaded parallel processing

// utils/simd_ops.rs - SIMD 优化的数学操作
#![allow(dead_code)]
//
// 使用编译器友好的代码结构启用自动向量化
// 遵循 KISS 原则：利用编译器优化而非手写 SIMD

use crate::errors::validation::{validate_not_empty, validate_period, validate_same_length};
use crate::errors::{HazeError, HazeResult};
use crate::init_result;
use crate::utils::math::{is_not_zero, kahan_sum};
use crate::utils::rolling_sum_kahan;

/// SIMD 友好的向量加法
///
/// 编译器会自动向量化简单的 for 循环
///
#[inline]
pub fn add_vectors(a: &[f64], b: &[f64]) -> HazeResult<Vec<f64>> {
    validate_same_length(a, "a", b, "b")?;
    Ok(a.iter().zip(b.iter()).map(|(&x, &y)| x + y).collect())
}

/// SIMD 友好的向量减法
///
#[inline]
pub fn sub_vectors(a: &[f64], b: &[f64]) -> HazeResult<Vec<f64>> {
    validate_same_length(a, "a", b, "b")?;
    Ok(a.iter().zip(b.iter()).map(|(&x, &y)| x - y).collect())
}

/// SIMD 友好的向量乘法
///
#[inline]
pub fn mul_vectors(a: &[f64], b: &[f64]) -> HazeResult<Vec<f64>> {
    validate_same_length(a, "a", b, "b")?;
    Ok(a.iter().zip(b.iter()).map(|(&x, &y)| x * y).collect())
}

/// SIMD 友好的向量除法
///
#[inline]
pub fn div_vectors(a: &[f64], b: &[f64]) -> HazeResult<Vec<f64>> {
    validate_same_length(a, "a", b, "b")?;
    let mut result = Vec::with_capacity(a.len());
    for (idx, (&x, &y)) in a.iter().zip(b.iter()).enumerate() {
        if !is_not_zero(y) {
            return Err(HazeError::InvalidValue {
                index: idx,
                message: "division by zero".to_string(),
            });
        }
        result.push(x / y);
    }
    Ok(result)
}

/// SIMD 友好的标量乘法
#[inline]
pub fn scale_vector(a: &[f64], scalar: f64) -> HazeResult<Vec<f64>> {
    validate_not_empty(a, "a")?;
    if !scalar.is_finite() {
        return Err(HazeError::InvalidValue {
            index: 0,
            message: "scalar must be finite".to_string(),
        });
    }
    Ok(a.iter().map(|&x| x * scalar).collect())
}

/// SIMD 友好的向量求和
///
/// 使用分块求和以提高数值稳定性和向量化效率
#[inline]
pub fn sum_vector(a: &[f64]) -> HazeResult<f64> {
    validate_not_empty(a, "values")?;
    Ok(kahan_sum(a))
}

/// SIMD 友好的点积
///
#[inline]
pub fn dot_product(a: &[f64], b: &[f64]) -> HazeResult<f64> {
    validate_same_length(a, "a", b, "b")?;
    let mut sum = 0.0;
    let mut compensation = 0.0;
    for (&x, &y) in a.iter().zip(b.iter()) {
        let prod = x * y;
        let y = prod - compensation;
        let t = sum + y;
        compensation = (t - sum) - y;
        sum = t;
    }
    Ok(sum)
}

/// 快速 SMA 计算（SIMD 友好）
///
/// 使用累积和优化，O(n) 时间复杂度
pub fn fast_sma(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    let n = values.len();
    let sums = rolling_sum_kahan(values, period);
    let mut result = init_result!(n);
    let period_f64 = period as f64;
    for i in (period - 1)..n {
        let sum = sums[i];
        if sum.is_finite() {
            result[i] = sum / period_f64;
        }
    }
    Ok(result)
}

/// 快速 EMA 计算（SIMD 友好）
///
/// 使用递推公式，O(n) 时间复杂度
pub fn fast_ema(values: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    validate_not_empty(values, "values")?;
    validate_period(period, values.len())?;

    let n = values.len();
    let alpha = 2.0 / (period as f64 + 1.0);
    let one_minus_alpha = 1.0 - alpha;

    let mut result = init_result!(n);
    let mut warmup_sum = 0.0;
    let mut warmup_comp = 0.0;
    let mut warmup_count = 0usize;
    let mut prev = f64::NAN;

    for i in 0..n {
        let v = values[i];
        if warmup_count < period {
            warmup_count += 1;
            let y = v - warmup_comp;
            let t = warmup_sum + y;
            warmup_comp = (t - warmup_sum) - y;
            warmup_sum = t;

            if warmup_count == period {
                prev = warmup_sum / period as f64;
                result[i] = prev;
            }
            continue;
        }

        prev = alpha * v + one_minus_alpha * prev;
        result[i] = prev;
    }

    Ok(result)
}

/// 批量计算多个 SMA 周期
///
/// 利用缓存局部性优化
pub fn batch_sma(values: &[f64], periods: &[usize]) -> HazeResult<Vec<Vec<f64>>> {
    validate_not_empty(values, "values")?;
    let mut results = Vec::with_capacity(periods.len());
    for &period in periods {
        validate_period(period, values.len())?;
        results.push(fast_sma(values, period)?);
    }
    Ok(results)
}

/// 向量化的最大值查找
#[inline]
pub fn max_vector(values: &[f64]) -> HazeResult<f64> {
    validate_not_empty(values, "values")?;
    Ok(values
        .iter()
        .fold(f64::NEG_INFINITY, |acc, &x| if x > acc { x } else { acc }))
}

/// 向量化的最小值查找
#[inline]
pub fn min_vector(values: &[f64]) -> HazeResult<f64> {
    validate_not_empty(values, "values")?;
    Ok(values
        .iter()
        .fold(f64::INFINITY, |acc, &x| if x < acc { x } else { acc }))
}

/// 向量化的均值计算
#[inline]
pub fn mean_vector(values: &[f64]) -> HazeResult<f64> {
    validate_not_empty(values, "values")?;
    Ok(kahan_sum(values) / values.len() as f64)
}

/// 向量化的标准差计算
#[inline]
pub fn std_vector(values: &[f64]) -> HazeResult<f64> {
    validate_not_empty(values, "values")?;
    if values.len() < 2 {
        return Err(HazeError::InsufficientData {
            required: 2,
            actual: values.len(),
        });
    }

    let mean = kahan_sum(values) / values.len() as f64;
    let mut sum = 0.0;
    let mut comp = 0.0;
    for &value in values {
        let diff = value - mean;
        let y = diff * diff - comp;
        let t = sum + y;
        comp = (t - sum) - y;
        sum = t;
    }
    Ok((sum / values.len() as f64).sqrt())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add_vectors() {
        let a = vec![1.0, 2.0, 3.0, 4.0];
        let b = vec![5.0, 6.0, 7.0, 8.0];
        let result = add_vectors(&a, &b).unwrap();
        assert_eq!(result, vec![6.0, 8.0, 10.0, 12.0]);
    }

    #[test]
    fn test_sum_vector() {
        let values: Vec<f64> = (1..=100).map(|x| x as f64).collect();
        let sum = sum_vector(&values).unwrap();
        assert!((sum - 5050.0).abs() < 1e-10);
    }

    #[test]
    fn test_dot_product() {
        let a = vec![1.0, 2.0, 3.0];
        let b = vec![4.0, 5.0, 6.0];
        let result = dot_product(&a, &b).unwrap();
        assert!((result - 32.0).abs() < 1e-10); // 1*4 + 2*5 + 3*6 = 32
    }

    #[test]
    fn test_fast_sma() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = fast_sma(&values, 3).unwrap();
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        assert!((result[2] - 2.0).abs() < 1e-10);
        assert!((result[3] - 3.0).abs() < 1e-10);
        assert!((result[4] - 4.0).abs() < 1e-10);
    }

    #[test]
    fn test_fast_ema() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = fast_ema(&values, 3).unwrap();
        assert!(result[0].is_nan());
        assert!(result[1].is_nan());
        assert!((result[2] - 2.0).abs() < 1e-10); // 初始值 = SMA
    }

    #[test]
    fn test_batch_sma() {
        let values: Vec<f64> = (1..=20).map(|x| x as f64).collect();
        let periods = vec![3, 5, 10];
        let results = batch_sma(&values, &periods).unwrap();
        assert_eq!(results.len(), 3);
    }

    #[test]
    fn test_statistics() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        assert!((mean_vector(&values).unwrap() - 3.0).abs() < 1e-10);
        assert!((max_vector(&values).unwrap() - 5.0).abs() < 1e-10);
        assert!((min_vector(&values).unwrap() - 1.0).abs() < 1e-10);
    }
}

// ==================== 边界条件测试 ====================

#[cfg(test)]
mod boundary_tests {
    use super::*;

    // ==================== 向量运算边界测试 ====================

    #[test]
    fn test_add_vectors_empty() {
        let a: Vec<f64> = vec![];
        let b: Vec<f64> = vec![];
        assert!(add_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_add_vectors_single() {
        let a = vec![5.0];
        let b = vec![3.0];
        let result = add_vectors(&a, &b).unwrap();
        assert_eq!(result, vec![8.0]);
    }

    #[test]
    fn test_add_vectors_with_nan() {
        let a = vec![1.0, f64::NAN, 3.0];
        let b = vec![4.0, 5.0, 6.0];
        assert!(add_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_add_vectors_with_infinity() {
        let a = vec![f64::INFINITY, f64::NEG_INFINITY, 1.0];
        let b = vec![1.0, 1.0, f64::INFINITY];
        assert!(add_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_add_vectors_length_mismatch() {
        let a = vec![1.0, 2.0];
        let b = vec![1.0];
        assert!(add_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_sub_vectors_empty() {
        let a: Vec<f64> = vec![];
        let b: Vec<f64> = vec![];
        assert!(sub_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_sub_vectors_single() {
        let a = vec![10.0];
        let b = vec![3.0];
        let result = sub_vectors(&a, &b).unwrap();
        assert_eq!(result, vec![7.0]);
    }

    #[test]
    fn test_sub_vectors_with_nan() {
        let a = vec![1.0, f64::NAN, 3.0];
        let b = vec![0.5, 2.0, 1.0];
        assert!(sub_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_sub_vectors_length_mismatch() {
        let a = vec![1.0, 2.0, 3.0];
        let b = vec![1.0, 2.0];
        assert!(sub_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_mul_vectors_empty() {
        let a: Vec<f64> = vec![];
        let b: Vec<f64> = vec![];
        assert!(mul_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_mul_vectors_single() {
        let a = vec![4.0];
        let b = vec![5.0];
        let result = mul_vectors(&a, &b).unwrap();
        assert_eq!(result, vec![20.0]);
    }

    #[test]
    fn test_mul_vectors_with_zero() {
        let a = vec![1.0, 0.0, 3.0];
        let b = vec![0.0, 5.0, 6.0];
        let result = mul_vectors(&a, &b).unwrap();
        assert_eq!(result, vec![0.0, 0.0, 18.0]);
    }

    #[test]
    fn test_mul_vectors_with_nan() {
        let a = vec![1.0, f64::NAN, 3.0];
        let b = vec![2.0, 3.0, 4.0];
        assert!(mul_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_mul_vectors_length_mismatch() {
        let a = vec![1.0];
        let b = vec![1.0, 2.0];
        assert!(mul_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_div_vectors_empty() {
        let a: Vec<f64> = vec![];
        let b: Vec<f64> = vec![];
        assert!(div_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_div_vectors_single() {
        let a = vec![10.0];
        let b = vec![2.0];
        let result = div_vectors(&a, &b).unwrap();
        assert_eq!(result, vec![5.0]);
    }

    #[test]
    fn test_div_vectors_by_zero() {
        let a = vec![10.0, 0.0, 5.0];
        let b = vec![0.0, 0.0, 2.5];
        assert!(div_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_div_vectors_with_nan() {
        let a = vec![f64::NAN, 10.0];
        let b = vec![2.0, f64::NAN];
        assert!(div_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_div_vectors_length_mismatch() {
        let a = vec![1.0, 2.0, 3.0];
        let b = vec![1.0];
        assert!(div_vectors(&a, &b).is_err());
    }

    #[test]
    fn test_scale_vector_empty() {
        let a: Vec<f64> = vec![];
        assert!(scale_vector(&a, 5.0).is_err());
    }

    #[test]
    fn test_scale_vector_by_zero() {
        let a = vec![1.0, 2.0, 3.0];
        let result = scale_vector(&a, 0.0).unwrap();
        assert_eq!(result, vec![0.0, 0.0, 0.0]);
    }

    #[test]
    fn test_scale_vector_by_nan() {
        let a = vec![1.0, 2.0, 3.0];
        assert!(scale_vector(&a, f64::NAN).is_err());
    }

    #[test]
    fn test_scale_vector_with_nan() {
        let a = vec![1.0, f64::NAN, 3.0];
        assert!(scale_vector(&a, 2.0).is_err());
    }

    // ==================== 聚合操作边界测试 ====================

    #[test]
    fn test_sum_vector_empty() {
        let a: Vec<f64> = vec![];
        assert!(sum_vector(&a).is_err());
    }

    #[test]
    fn test_sum_vector_single() {
        let a = vec![42.0];
        let result = sum_vector(&a).unwrap();
        assert!((result - 42.0).abs() < 1e-10);
    }

    #[test]
    fn test_sum_vector_with_nan() {
        let a = vec![1.0, f64::NAN, 3.0];
        assert!(sum_vector(&a).is_err());
    }

    #[test]
    fn test_sum_vector_exact_chunk_size() {
        // Test with exactly 8 elements (one chunk)
        let a = vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0];
        let result = sum_vector(&a).unwrap();
        assert!((result - 36.0).abs() < 1e-10);
    }

    #[test]
    fn test_sum_vector_multiple_chunks_with_remainder() {
        // Test with 17 elements (2 chunks + 1 remainder)
        let a: Vec<f64> = (1..=17).map(|x| x as f64).collect();
        let result = sum_vector(&a).unwrap();
        let expected = 17.0 * 18.0 / 2.0; // Sum 1..17 = n(n+1)/2
        assert!((result - expected).abs() < 1e-10);
    }

    #[test]
    fn test_dot_product_empty() {
        let a: Vec<f64> = vec![];
        let b: Vec<f64> = vec![];
        assert!(dot_product(&a, &b).is_err());
    }

    #[test]
    fn test_dot_product_single() {
        let a = vec![3.0];
        let b = vec![4.0];
        let result = dot_product(&a, &b).unwrap();
        assert!((result - 12.0).abs() < 1e-10);
    }

    #[test]
    fn test_dot_product_with_nan() {
        let a = vec![1.0, f64::NAN, 3.0];
        let b = vec![2.0, 3.0, 4.0];
        assert!(dot_product(&a, &b).is_err());
    }

    #[test]
    fn test_dot_product_exact_chunk_size() {
        let a = vec![1.0; 8];
        let b = vec![2.0; 8];
        let result = dot_product(&a, &b).unwrap();
        assert!((result - 16.0).abs() < 1e-10);
    }

    #[test]
    fn test_dot_product_length_mismatch() {
        let a = vec![1.0, 2.0];
        let b = vec![1.0, 2.0, 3.0];
        assert!(dot_product(&a, &b).is_err());
    }

    #[test]
    fn test_max_vector_empty() {
        let a: Vec<f64> = vec![];
        assert!(max_vector(&a).is_err());
    }

    #[test]
    fn test_max_vector_single() {
        let a = vec![42.0];
        let result = max_vector(&a).unwrap();
        assert!((result - 42.0).abs() < 1e-10);
    }

    #[test]
    fn test_max_vector_all_same() {
        let a = vec![5.0, 5.0, 5.0, 5.0];
        let result = max_vector(&a).unwrap();
        assert!((result - 5.0).abs() < 1e-10);
    }

    #[test]
    fn test_max_vector_with_nan() {
        // NaN comparisons are tricky - NaN is not > any value
        let a = vec![1.0, f64::NAN, 3.0];
        assert!(max_vector(&a).is_err());
    }

    #[test]
    fn test_max_vector_with_infinity() {
        let a = vec![1.0, f64::INFINITY, 3.0];
        assert!(max_vector(&a).is_err());
    }

    #[test]
    fn test_max_vector_with_neg_infinity() {
        let a = vec![f64::NEG_INFINITY, -100.0, -50.0];
        assert!(max_vector(&a).is_err());
    }

    #[test]
    fn test_min_vector_empty() {
        let a: Vec<f64> = vec![];
        assert!(min_vector(&a).is_err());
    }

    #[test]
    fn test_min_vector_single() {
        let a = vec![42.0];
        let result = min_vector(&a).unwrap();
        assert!((result - 42.0).abs() < 1e-10);
    }

    #[test]
    fn test_min_vector_all_same() {
        let a = vec![5.0, 5.0, 5.0, 5.0];
        let result = min_vector(&a).unwrap();
        assert!((result - 5.0).abs() < 1e-10);
    }

    #[test]
    fn test_min_vector_with_nan() {
        let a = vec![1.0, f64::NAN, 3.0];
        assert!(min_vector(&a).is_err());
    }

    #[test]
    fn test_min_vector_with_neg_infinity() {
        let a = vec![1.0, f64::NEG_INFINITY, 3.0];
        assert!(min_vector(&a).is_err());
    }

    #[test]
    fn test_mean_vector_empty() {
        let a: Vec<f64> = vec![];
        assert!(mean_vector(&a).is_err());
    }

    #[test]
    fn test_mean_vector_single() {
        let a = vec![42.0];
        let result = mean_vector(&a).unwrap();
        assert!((result - 42.0).abs() < 1e-10);
    }

    #[test]
    fn test_mean_vector_with_nan() {
        let a = vec![1.0, f64::NAN, 3.0];
        assert!(mean_vector(&a).is_err());
    }

    #[test]
    fn test_std_vector_empty() {
        let a: Vec<f64> = vec![];
        assert!(std_vector(&a).is_err());
    }

    #[test]
    fn test_std_vector_single() {
        let a = vec![42.0];
        assert!(std_vector(&a).is_err());
    }

    #[test]
    fn test_std_vector_two_elements() {
        let a = vec![0.0, 2.0];
        let result = std_vector(&a).unwrap();
        // Mean = 1.0, variance = ((0-1)^2 + (2-1)^2)/2 = 1, std = 1
        assert!((result - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_std_vector_all_same() {
        let a = vec![5.0, 5.0, 5.0, 5.0];
        let result = std_vector(&a).unwrap();
        // All same values -> std = 0
        assert!((result - 0.0).abs() < 1e-10);
    }

    #[test]
    fn test_std_vector_with_nan() {
        let a = vec![1.0, f64::NAN, 3.0];
        assert!(std_vector(&a).is_err());
    }

    // ==================== 快速指标边界测试 ====================

    #[test]
    fn test_fast_sma_empty() {
        let a: Vec<f64> = vec![];
        assert!(fast_sma(&a, 3).is_err());
    }

    #[test]
    fn test_fast_sma_period_zero() {
        let a = vec![1.0, 2.0, 3.0];
        assert!(fast_sma(&a, 0).is_err());
    }

    #[test]
    fn test_fast_sma_period_one() {
        let a = vec![1.0, 2.0, 3.0, 4.0];
        let result = fast_sma(&a, 1).unwrap();
        // Period=1 means each value is its own SMA
        assert!((result[0] - 1.0).abs() < 1e-10);
        assert!((result[1] - 2.0).abs() < 1e-10);
        assert!((result[2] - 3.0).abs() < 1e-10);
        assert!((result[3] - 4.0).abs() < 1e-10);
    }

    #[test]
    fn test_fast_sma_period_equals_length() {
        let a = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = fast_sma(&a, 5).unwrap();
        // Only last value should have SMA
        assert!(result[0..4].iter().all(|v| v.is_nan()));
        assert!((result[4] - 3.0).abs() < 1e-10);
    }

    #[test]
    fn test_fast_sma_period_exceeds_length() {
        let a = vec![1.0, 2.0, 3.0];
        assert!(fast_sma(&a, 10).is_err());
    }

    #[test]
    fn test_fast_sma_with_nan() {
        let a = vec![1.0, 2.0, f64::NAN, 4.0, 5.0];
        assert!(fast_sma(&a, 3).is_err());
    }

    #[test]
    fn test_fast_sma_large_values() {
        let a = vec![1e15, 2e15, 3e15, 4e15, 5e15];
        let result = fast_sma(&a, 3).unwrap();
        assert!((result[2] - 2e15).abs() < 1e5);
        assert!((result[3] - 3e15).abs() < 1e5);
        assert!((result[4] - 4e15).abs() < 1e5);
    }

    #[test]
    fn test_fast_ema_empty() {
        let a: Vec<f64> = vec![];
        assert!(fast_ema(&a, 3).is_err());
    }

    #[test]
    fn test_fast_ema_period_zero() {
        let a = vec![1.0, 2.0, 3.0];
        assert!(fast_ema(&a, 0).is_err());
    }

    #[test]
    fn test_fast_ema_period_one() {
        let a = vec![1.0, 2.0, 3.0, 4.0];
        let result = fast_ema(&a, 1).unwrap();
        // Period=1 means alpha=1, so EMA = each value
        assert!((result[0] - 1.0).abs() < 1e-10);
        assert!((result[1] - 2.0).abs() < 1e-10);
        assert!((result[2] - 3.0).abs() < 1e-10);
        assert!((result[3] - 4.0).abs() < 1e-10);
    }

    #[test]
    fn test_fast_ema_period_equals_length() {
        let a = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = fast_ema(&a, 5).unwrap();
        // Only last value should have EMA (initial = SMA)
        assert!(result[0..4].iter().all(|v| v.is_nan()));
        assert!((result[4] - 3.0).abs() < 1e-10); // SMA of 1-5 = 3
    }

    #[test]
    fn test_fast_ema_period_exceeds_length() {
        let a = vec![1.0, 2.0, 3.0];
        assert!(fast_ema(&a, 10).is_err());
    }

    #[test]
    fn test_fast_ema_constant_values() {
        let a = vec![100.0; 20];
        let result = fast_ema(&a, 5).unwrap();
        // EMA of constant values should equal the constant
        for val in result.iter().skip(4) {
            assert!((*val - 100.0).abs() < 1e-10);
        }
    }

    #[test]
    fn test_batch_sma_empty_values() {
        let a: Vec<f64> = vec![];
        let periods = vec![3, 5, 10];
        assert!(batch_sma(&a, &periods).is_err());
    }

    #[test]
    fn test_batch_sma_empty_periods() {
        let a = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let periods: Vec<usize> = vec![];
        let results = batch_sma(&a, &periods).unwrap();
        assert!(results.is_empty());
    }

    #[test]
    fn test_batch_sma_with_zero_period() {
        let a = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let periods = vec![0, 3, 5];
        assert!(batch_sma(&a, &periods).is_err());
    }

    // ==================== 数值精度测试 ====================

    #[test]
    fn test_sum_vector_precision() {
        // Test numerical precision with many small values
        let a: Vec<f64> = (0..10000).map(|_| 0.0001).collect();
        let result = sum_vector(&a).unwrap();
        let expected = 1.0;
        assert!((result - expected).abs() < 1e-8);
    }

    #[test]
    fn test_dot_product_precision() {
        // Test with large number of elements
        let a: Vec<f64> = (1..=1000).map(|x| x as f64).collect();
        let b = vec![1.0; 1000];
        let result = dot_product(&a, &b).unwrap();
        let expected = 1000.0 * 1001.0 / 2.0; // Sum of 1 to 1000
        assert!((result - expected).abs() < 1e-6);
    }

    #[test]
    fn test_fast_sma_numerical_stability() {
        // Test with values that could cause numerical instability
        let a: Vec<f64> = (0..100).map(|i| 1e10 + i as f64).collect();
        let result = fast_sma(&a, 10).unwrap();
        // Verify the output is reasonable
        for val in result.iter().skip(9) {
            assert!(!val.is_nan());
            assert!(*val >= 1e10);
        }
    }

    // ==================== 集成测试 ====================

    #[test]
    fn test_vector_operations_chain() {
        let a = vec![1.0, 2.0, 3.0, 4.0];
        let b = vec![2.0, 2.0, 2.0, 2.0];

        // (a + b) * 2
        let sum = add_vectors(&a, &b).unwrap();
        let result = scale_vector(&sum, 2.0).unwrap();
        assert_eq!(result, vec![6.0, 8.0, 10.0, 12.0]);
    }

    #[test]
    fn test_fast_sma_vs_manual() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0];
        let result = fast_sma(&values, 3).unwrap();

        // Verify against manual calculation
        assert!((result[2] - (1.0 + 2.0 + 3.0) / 3.0).abs() < 1e-10);
        assert!((result[3] - (2.0 + 3.0 + 4.0) / 3.0).abs() < 1e-10);
        assert!((result[4] - (3.0 + 4.0 + 5.0) / 3.0).abs() < 1e-10);
        assert!((result[5] - (4.0 + 5.0 + 6.0) / 3.0).abs() < 1e-10);
        assert!((result[6] - (5.0 + 6.0 + 7.0) / 3.0).abs() < 1e-10);
    }

    #[test]
    fn test_negative_values() {
        let a = vec![-5.0, -3.0, -1.0, 1.0, 3.0, 5.0];
        let b = vec![1.0, 1.0, 1.0, 1.0, 1.0, 1.0];

        let sum = sum_vector(&a).unwrap();
        assert!((sum - 0.0).abs() < 1e-10);

        let mean = mean_vector(&a).unwrap();
        assert!((mean - 0.0).abs() < 1e-10);

        let result = add_vectors(&a, &b).unwrap();
        assert_eq!(result, vec![-4.0, -2.0, 0.0, 2.0, 4.0, 6.0]);
    }
}
