// utils/math.rs - High-precision mathematical utilities
//!
//! Provides:
//! 1. Robust floating-point comparison functions (epsilon-based)
//! 2. Compensated summation algorithms (Kahan/Neumaier) for improved numerical precision
//!
//! # Floating-Point Comparisons
//! ```rust
//! use haze_library::utils::math::{approx_eq, is_not_zero, is_zero};
//!
//! let value = 0.0;
//! assert!(is_zero(value));
//! assert!(!is_not_zero(value));
//!
//! let a = 1.0;
//! let b = 1.0 + 1e-15;
//! assert!(approx_eq(a, b));
//! ```
//!
//! # Kahan Summation
//! Use compensated summation for critical calculations where precision matters:
//! - Summing > 100 elements (use `should_use_kahan()` helper)
//! - ML feature calculations
//! - Values with large magnitude differences
//! - Variance/standard deviation calculations

/// Machine epsilon for f64 comparisons.
/// Chosen to be small enough for financial calculations while
/// being large enough to handle typical floating-point rounding errors.
pub const EPSILON: f64 = 1e-10;

/// Check if a value is approximately zero.
///
/// # Arguments
/// * `value` - The value to check
///
/// # Returns
/// * `true` if `|value| < EPSILON`
///
/// # Example
/// ```rust
/// use haze_library::utils::math::is_zero;
///
/// assert!(is_zero(0.0));
/// assert!(is_zero(1e-15));
/// assert!(!is_zero(0.001));
/// ```
#[inline]
pub fn is_zero(value: f64) -> bool {
    value.abs() < EPSILON
}

/// Check if a value is NOT approximately zero.
///
/// This is the logical negation of `is_zero` and should be used
/// instead of `!= 0.0` comparisons.
///
/// # Arguments
/// * `value` - The value to check
///
/// # Returns
/// * `true` if `|value| >= EPSILON`
#[inline]
pub fn is_not_zero(value: f64) -> bool {
    value.abs() >= EPSILON
}

/// Check if two values are approximately equal.
///
/// # Arguments
/// * `a` - First value
/// * `b` - Second value
///
/// # Returns
/// * `true` if `|a - b| < EPSILON`
///
/// # Example
/// ```rust
/// use haze_library::utils::math::approx_eq;
///
/// assert!(approx_eq(1.0, 1.0 + 1e-15));
/// assert!(!approx_eq(1.0, 1.001));
/// ```
#[inline]
pub fn approx_eq(a: f64, b: f64) -> bool {
    (a - b).abs() < EPSILON
}

/// Check if two values are NOT approximately equal.
///
/// This is the logical negation of `approx_eq`.
///
/// # Arguments
/// * `a` - First value
/// * `b` - Second value
///
/// # Returns
/// * `true` if `|a - b| >= EPSILON`
#[inline]
pub fn approx_ne(a: f64, b: f64) -> bool {
    (a - b).abs() >= EPSILON
}

/// Check if a value is approximately greater than zero.
///
/// Useful for division guards where we need positive denominators.
///
/// # Arguments
/// * `value` - The value to check
///
/// # Returns
/// * `true` if `value > EPSILON`
#[inline]
pub fn is_positive(value: f64) -> bool {
    value > EPSILON
}

/// Check if a value is approximately less than zero.
///
/// # Arguments
/// * `value` - The value to check
///
/// # Returns
/// * `true` if `value < -EPSILON`
#[inline]
pub fn is_negative(value: f64) -> bool {
    value < -EPSILON
}

/// Safe division that returns NaN when the denominator is approximately zero.
///
/// # Arguments
/// * `numerator` - The numerator
/// * `denominator` - The denominator
///
/// # Returns
/// * `numerator / denominator` if denominator is not approximately zero
/// * `f64::NAN` if denominator is approximately zero
#[inline]
pub fn safe_div(numerator: f64, denominator: f64) -> f64 {
    if is_zero(denominator) {
        f64::NAN
    } else {
        numerator / denominator
    }
}

/// Safe division that returns a default value when the denominator is approximately zero.
///
/// # Arguments
/// * `numerator` - The numerator
/// * `denominator` - The denominator
/// * `default` - The value to return if denominator is approximately zero
///
/// # Returns
/// * `numerator / denominator` if denominator is not approximately zero
/// * `default` if denominator is approximately zero
#[inline]
pub fn safe_div_or(numerator: f64, denominator: f64, default: f64) -> f64 {
    if is_zero(denominator) {
        default
    } else {
        numerator / denominator
    }
}

// ============================================================================
// Kahan Compensated Summation
// ============================================================================

/// Default threshold for recommending Kahan summation
pub const KAHAN_THRESHOLD_DEFAULT: usize = 100;

/// Threshold for critical precision paths (e.g., ML features)
pub const KAHAN_THRESHOLD_CRITICAL: usize = 50;

/// Decision helper: should Kahan summation be used?
///
/// Returns true if Kahan summation is recommended based on element count.
/// This is a heuristic; for truly critical calculations, always use Kahan.
///
/// # Arguments
/// - `len`: Number of elements to sum
/// - `threshold`: Minimum length to recommend Kahan (default: 100)
#[inline]
pub const fn should_use_kahan(len: usize, threshold: usize) -> bool {
    len >= threshold
}

/// Kahan compensated summation for improved numerical precision
///
/// Reduces floating-point rounding errors compared to naive summation.
/// Use for critical calculations where precision matters, such as:
/// - Summing > 100 elements
/// - ML feature calculations
/// - Values with large magnitude differences
///
/// # Algorithm
/// The Kahan algorithm maintains a running compensation for lost low-order bits.
/// Each addition step:
/// 1. Subtracts the compensation from the new value
/// 2. Adds the compensated value to the sum
/// 3. Updates the compensation based on what was lost
///
/// # Complexity
/// O(n) time, O(1) space
///
/// # NaN Handling
/// NaN values are skipped (not included in the sum).
#[inline]
pub fn kahan_sum(values: &[f64]) -> f64 {
    let mut sum = 0.0;
    let mut compensation = 0.0; // Running compensation for lost low-order bits

    for &value in values {
        if value.is_nan() {
            continue; // Skip NaN values
        }
        let y = value - compensation;
        let t = sum + y;
        compensation = (t - sum) - y;
        sum = t;
    }

    sum
}

/// Kahan summation for iterator
///
/// Provides the same precision benefits as `kahan_sum` but works with any iterator
/// that yields `f64` values. Useful for chained operations without intermediate allocation.
///
/// # Complexity
/// O(n) time, O(1) space
#[inline]
pub fn kahan_sum_iter<I>(iter: I) -> f64
where
    I: Iterator<Item = f64>,
{
    let mut sum = 0.0;
    let mut compensation = 0.0;

    for value in iter {
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

/// Kahan summation with count for calculating mean
///
/// Returns both the compensated sum and the count of valid (non-NaN) values.
/// Useful for computing means with improved precision.
///
/// # Returns
/// - `(sum, count)` tuple where sum is the Kahan-compensated sum
///   and count is the number of valid values
#[inline]
pub fn kahan_sum_with_count(values: &[f64]) -> (f64, usize) {
    let mut sum = 0.0;
    let mut compensation = 0.0;
    let mut count = 0usize;

    for &value in values {
        if value.is_nan() {
            continue;
        }
        count += 1;
        let y = value - compensation;
        let t = sum + y;
        compensation = (t - sum) - y;
        sum = t;
    }

    (sum, count)
}

/// Kahan mean - compute mean with compensated summation
///
/// Computes the arithmetic mean using Kahan summation for improved precision.
/// Returns NaN if the slice is empty or contains only NaN values.
///
/// # Complexity
/// O(n) time, O(1) space
#[inline]
pub fn kahan_mean(values: &[f64]) -> f64 {
    let (sum, count) = kahan_sum_with_count(values);
    if count == 0 {
        f64::NAN
    } else {
        sum / count as f64
    }
}

/// Neumaier summation (improved Kahan)
///
/// A variant of Kahan summation that handles the case where the next term
/// to be added is larger in absolute value than the running sum.
/// Slightly more robust than Kahan for certain edge cases (e.g., alternating
/// large positive and negative values).
///
/// # Complexity
/// O(n) time, O(1) space
#[inline]
pub fn neumaier_sum(values: &[f64]) -> f64 {
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

/// Pairwise summation - divide and conquer approach
///
/// Recursively splits the array in half and sums each half, reducing
/// accumulated error from O(n) to O(log n) for random errors.
/// Falls back to Kahan for small arrays.
///
/// # Complexity
/// O(n) time, O(log n) space (recursion depth)
pub fn pairwise_sum(values: &[f64]) -> f64 {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_zero() {
        // Exact zero
        assert!(is_zero(0.0));
        assert!(is_zero(-0.0));

        // Very small values (should be treated as zero)
        assert!(is_zero(1e-15));
        assert!(is_zero(-1e-15));
        assert!(is_zero(1e-11));
        assert!(is_zero(-1e-11));

        // Values at boundary
        assert!(!is_zero(1e-10)); // Equal to EPSILON, not zero
        assert!(!is_zero(-1e-10));

        // Clearly non-zero
        assert!(!is_zero(0.001));
        assert!(!is_zero(-0.001));
        assert!(!is_zero(1.0));
    }

    #[test]
    fn test_is_not_zero() {
        assert!(!is_not_zero(0.0));
        assert!(!is_not_zero(1e-15));
        assert!(is_not_zero(1e-10));
        assert!(is_not_zero(0.001));
        assert!(is_not_zero(-0.001));
    }

    #[test]
    fn test_approx_eq() {
        // Equal values
        assert!(approx_eq(1.0, 1.0));
        assert!(approx_eq(0.0, 0.0));
        assert!(approx_eq(-5.5, -5.5));

        // Nearly equal values (within epsilon)
        assert!(approx_eq(1.0, 1.0 + 1e-15));
        assert!(approx_eq(1.0, 1.0 - 1e-15));

        // Floating point arithmetic results
        assert!(approx_eq(0.1 + 0.2, 0.3));

        // Clearly different values
        assert!(!approx_eq(1.0, 1.001));
        assert!(!approx_eq(0.0, 0.001));
    }

    #[test]
    fn test_approx_ne() {
        assert!(!approx_ne(1.0, 1.0));
        assert!(!approx_ne(1.0, 1.0 + 1e-15));
        assert!(approx_ne(1.0, 1.001));
        assert!(approx_ne(0.0, 0.001));
    }

    #[test]
    fn test_is_positive() {
        assert!(!is_positive(0.0));
        assert!(!is_positive(1e-15));
        assert!(is_positive(1e-9));
        assert!(is_positive(1.0));
        assert!(!is_positive(-1.0));
    }

    #[test]
    fn test_is_negative() {
        assert!(!is_negative(0.0));
        assert!(!is_negative(-1e-15));
        assert!(is_negative(-1e-9));
        assert!(is_negative(-1.0));
        assert!(!is_negative(1.0));
    }

    #[test]
    fn test_safe_div() {
        // Normal division
        assert!((safe_div(10.0, 2.0) - 5.0).abs() < EPSILON);
        assert!((safe_div(-10.0, 2.0) - (-5.0)).abs() < EPSILON);

        // Division by zero
        assert!(safe_div(1.0, 0.0).is_nan());
        assert!(safe_div(1.0, 1e-15).is_nan());

        // Division of zero
        assert!(is_zero(safe_div(0.0, 5.0)));
    }

    #[test]
    fn test_safe_div_or() {
        assert!((safe_div_or(10.0, 2.0, 0.0) - 5.0).abs() < EPSILON);
        assert!((safe_div_or(1.0, 0.0, 100.0) - 100.0).abs() < EPSILON);
        assert!((safe_div_or(1.0, 1e-15, 42.0) - 42.0).abs() < EPSILON);
    }

    #[test]
    fn test_edge_cases_near_zero() {
        // Test values that are very close to zero from floating-point arithmetic
        let result = 1.0 - 0.9 - 0.1; // This often doesn't equal 0.0 exactly
                                      // We want this to be considered zero
        assert!(is_zero(result) || result.abs() < 1e-14);

        // Test accumulated floating-point errors
        let mut sum: f64 = 0.0;
        for _ in 0..1000 {
            sum += 0.001;
        }
        sum -= 1.0;
        // After accumulation, the error should still be small
        assert!(sum.abs() < 1e-10);
    }

    #[test]
    fn test_financial_calculations() {
        // Simulate typical financial calculations
        let _price = 100.0;
        let quantity = 0.0;

        // Check for zero quantity before division
        assert!(is_zero(quantity));

        // Percentage calculation
        let pct_change = 0.0;
        assert!(is_zero(pct_change));

        // Small but meaningful values
        let small_change = 0.0001; // 1 basis point
        assert!(!is_zero(small_change));

        // Price difference
        let price1 = 100.00;
        let price2 = 100.00;
        assert!(approx_eq(price1, price2));
    }

    // ========================================================================
    // Kahan Summation Tests
    // ========================================================================

    #[test]
    fn test_kahan_sum_basic() {
        let values = [1.0, 2.0, 3.0, 4.0, 5.0];
        let result = kahan_sum(&values);
        assert!((result - 15.0).abs() < 1e-10);
    }

    #[test]
    fn test_kahan_sum_precision() {
        // Demonstrates precision advantage of Kahan summation
        // Adding very small numbers to a large number repeatedly
        let large = 1e16;
        let small = 1.0;
        let count: usize = 10_000;

        let mut values = vec![large];
        values.extend(std::iter::repeat_n(small, count));

        let kahan_result = kahan_sum(&values);
        let naive_result: f64 = values.iter().sum();

        let expected = large + (count as f64);
        let kahan_error = (kahan_result - expected).abs();
        let naive_error = (naive_result - expected).abs();

        // Kahan should have less or equal error
        assert!(kahan_error <= naive_error);
    }

    #[test]
    fn test_kahan_sum_with_nan() {
        let values = [1.0, f64::NAN, 2.0, f64::NAN, 3.0];
        let result = kahan_sum(&values);
        assert!((result - 6.0).abs() < 1e-10);
    }

    #[test]
    fn test_kahan_sum_empty() {
        let result = kahan_sum(&[]);
        assert_eq!(result, 0.0);
    }

    #[test]
    fn test_kahan_sum_iter() {
        let values = [1.0, 2.0, 3.0, 4.0, 5.0];
        let result = kahan_sum_iter(values.iter().copied());
        assert!((result - 15.0).abs() < 1e-10);
    }

    #[test]
    fn test_kahan_sum_iter_with_transform() {
        let values: [f64; 5] = [1.0, 2.0, 3.0, 4.0, 5.0];
        let result = kahan_sum_iter(values.iter().map(|&x| x.powi(2)));
        // 1 + 4 + 9 + 16 + 25 = 55
        assert!((result - 55.0).abs() < 1e-10);
    }

    #[test]
    fn test_kahan_sum_with_count() {
        let values = [1.0, f64::NAN, 2.0, 3.0];
        let (sum, count) = kahan_sum_with_count(&values);
        assert!((sum - 6.0).abs() < 1e-10);
        assert_eq!(count, 3);
    }

    #[test]
    fn test_kahan_mean() {
        let values = [1.0, 2.0, 3.0, 4.0, 5.0];
        let result = kahan_mean(&values);
        assert!((result - 3.0).abs() < 1e-10);
    }

    #[test]
    fn test_kahan_mean_with_nan() {
        let values = vec![1.0, f64::NAN, 3.0, f64::NAN, 5.0];
        let result = kahan_mean(&values);
        // Mean of 1, 3, 5 = 3
        assert!((result - 3.0).abs() < 1e-10);
    }

    #[test]
    fn test_kahan_mean_empty() {
        let values: Vec<f64> = vec![];
        let result = kahan_mean(&values);
        assert!(result.is_nan());
    }

    #[test]
    fn test_neumaier_sum_basic() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = neumaier_sum(&values);
        assert!((result - 15.0).abs() < 1e-10);
    }

    #[test]
    fn test_neumaier_sum_alternating() {
        // Neumaier handles alternating large positive/negative values well
        let values = vec![1e16, 1.0, -1e16, 1.0];
        let result = neumaier_sum(&values);
        // True result is 2.0
        assert!((result - 2.0).abs() < 1e-10);
    }

    #[test]
    fn test_pairwise_sum_basic() {
        let values = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = pairwise_sum(&values);
        assert!((result - 15.0).abs() < 1e-10);
    }

    #[test]
    fn test_pairwise_sum_large() {
        // Test with array larger than threshold
        let values: Vec<f64> = (1..=1000).map(|x| x as f64).collect();
        let result = pairwise_sum(&values);
        let expected = (1000.0 * 1001.0) / 2.0; // Sum formula: n*(n+1)/2
        assert!((result - expected).abs() < 1e-10);
    }

    #[test]
    fn test_should_use_kahan() {
        assert!(!should_use_kahan(50, KAHAN_THRESHOLD_DEFAULT));
        assert!(should_use_kahan(100, KAHAN_THRESHOLD_DEFAULT));
        assert!(should_use_kahan(1000, KAHAN_THRESHOLD_DEFAULT));
        assert!(should_use_kahan(50, KAHAN_THRESHOLD_CRITICAL));
    }

    #[test]
    fn test_kahan_constants() {
        assert_eq!(KAHAN_THRESHOLD_DEFAULT, 100);
        assert_eq!(KAHAN_THRESHOLD_CRITICAL, 50);
    }

    #[test]
    fn test_kahan_vs_naive_many_small_values() {
        // Sum many small values - this is where Kahan shines
        let n = 10_000;
        let small_value = 0.1;

        let values: Vec<f64> = vec![small_value; n];

        let kahan_result = kahan_sum(&values);
        let naive_result: f64 = values.iter().sum();
        let expected = n as f64 * small_value;

        let kahan_error = (kahan_result - expected).abs();
        let naive_error = (naive_result - expected).abs();

        // Kahan should be more accurate (or at least not worse)
        assert!(kahan_error <= naive_error + 1e-14);
    }
}
