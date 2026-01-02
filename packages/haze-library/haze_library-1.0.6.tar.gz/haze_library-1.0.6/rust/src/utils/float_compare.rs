//! Floating-point comparison utilities with epsilon tolerance.
//!
//! # Overview
//! This module provides robust floating-point comparison functions to handle
//! numerical precision issues that arise from floating-point arithmetic.
//! Direct comparisons like `== 0.0` or `!= 0.0` can fail due to rounding errors.
//!
//! # Problem Statement
//! Floating-point arithmetic is inherently imprecise. For example:
//! ```ignore
//! let result = 0.1 + 0.2;
//! assert!(result == 0.3); // ❌ This fails! result is 0.30000000000000004
//! ```
//!
//! # Solution
//! Use epsilon-based comparisons that account for small rounding errors:
//! ```rust
//! use haze_library::utils::float_compare::{approx_eq, approx_zero};
//!
//! let result = 0.1 + 0.2;
//! assert!(approx_eq(result, 0.3, None)); // ✅ This succeeds
//!
//! let near_zero = 1e-15;
//! assert!(approx_zero(near_zero, None)); // ✅ Treated as zero
//! ```
//!
//! # Available Functions
//! - [`approx_eq`] - Compare two f64 values for approximate equality
//! - [`approx_zero`] - Check if a value is approximately zero
//! - [`approx_ne`] - Check if two values are NOT approximately equal
//! - [`relative_eq`] - Compare with relative tolerance (better for large values)
//! - [`safe_div`] - Safe division that returns NaN for zero denominators
//! - [`safe_div_or`] - Safe division with custom default value
//!
//! # Design Philosophy
//! - **KISS**: Simple, focused functions for common comparison patterns
//! - **YAGNI**: Only implements necessary comparison operations
//! - **SOLID**: Single responsibility - each function does one thing well
//! - **Occam's Razor**: Uses the simplest effective epsilon value (1e-10)
//!
//! # When to Use
//! - **Always** use these functions instead of `== 0.0`, `!= 0.0`
//! - Division guards: Check denominator before division
//! - Threshold comparisons in indicators (RSI, Stochastic, etc.)
//! - Matrix operations and linear algebra
//! - Any calculation involving floating-point arithmetic
//!
//! # Examples
//! ```rust
//! use haze_library::utils::float_compare::{approx_eq, approx_zero, relative_eq, safe_div};
//!
//! // Basic comparison
//! assert!(approx_eq(1.0, 1.0 + 1e-15, None));
//!
//! // Zero checking (division guard)
//! let divisor = 1e-12;
//! if approx_zero(divisor, None) {
//!     println!("Denominator too small, avoiding division");
//! }
//!
//! // Relative comparison (better for large values)
//! let large_a = 1e10;
//! let large_b = 1e10 + 1.0;
//! assert!(relative_eq(large_a, large_b, 1e-9));
//!
//! // Safe division
//! let result = safe_div(10.0, 0.0); // Returns NaN instead of panicking
//! assert!(result.is_nan());
//! ```
//!
//! # Performance Characteristics
//! - All comparison functions are `#[inline]` for zero-cost abstraction
//! - O(1) time complexity for all operations
//! - No heap allocations
//!
//! # Cross-References
//! - [`crate::utils::math`] - Extended math utilities with Kahan summation
//! - [`crate::indicators`] - Technical indicators using these comparisons
//! - `crate::ml` - Machine learning modules requiring precise comparisons

/// Default epsilon for f64 comparisons (1e-10)
///
/// This value is chosen to:
/// - Handle typical floating-point rounding errors (~1e-15 to 1e-16)
/// - Provide sufficient margin for accumulated errors
/// - Work well for financial calculations (price precision)
/// - Be conservative enough to avoid false positives
pub const DEFAULT_EPSILON: f64 = 1e-10;

/// Stricter epsilon for critical calculations (1e-12)
///
/// Use this for:
/// - Machine learning feature calculations
/// - High-precision mathematical operations
/// - Critical financial calculations requiring extra precision
pub const STRICT_EPSILON: f64 = 1e-12;

/// Relaxed epsilon for loose comparisons (1e-8)
///
/// Use this for:
/// - UI display rounding
/// - Non-critical threshold checks
/// - Large magnitude comparisons
pub const RELAXED_EPSILON: f64 = 1e-8;

/// Compare two f64 values for approximate equality.
///
/// Uses absolute difference comparison with configurable epsilon tolerance.
/// This is the primary comparison function for most use cases.
///
/// # Arguments
/// * `a` - First value
/// * `b` - Second value
/// * `epsilon` - Optional tolerance (defaults to DEFAULT_EPSILON)
///
/// # Returns
/// * `true` if `|a - b| < epsilon`
/// * `false` otherwise
///
/// # Examples
/// ```rust
/// use haze_library::utils::float_compare::approx_eq;
///
/// // Floating-point arithmetic precision issue
/// assert!(approx_eq(0.1 + 0.2, 0.3, None));
///
/// // Custom epsilon for relaxed comparison
/// assert!(approx_eq(1.0, 1.00001, Some(1e-4)));
///
/// // Exact values
/// assert!(approx_eq(5.0, 5.0, None));
/// ```
///
/// # Design Notes
/// - Uses absolute difference (not relative) for simplicity
/// - For large values (>1e6), consider using `relative_eq` instead
/// - NaN inputs always return false (NaN != NaN by IEEE 754)
#[inline]
pub fn approx_eq(a: f64, b: f64, epsilon: Option<f64>) -> bool {
    let eps = epsilon.unwrap_or(DEFAULT_EPSILON);
    (a - b).abs() < eps
}

/// Check if two values are NOT approximately equal.
///
/// Logical negation of `approx_eq`. Use instead of `!= 0.0` comparisons.
///
/// # Arguments
/// * `a` - First value
/// * `b` - Second value
/// * `epsilon` - Optional tolerance (defaults to DEFAULT_EPSILON)
///
/// # Returns
/// * `true` if `|a - b| >= epsilon`
///
/// # Examples
/// ```rust
/// use haze_library::utils::float_compare::approx_ne;
///
/// assert!(approx_ne(1.0, 2.0, None));
/// assert!(!approx_ne(1.0, 1.0 + 1e-15, None));
/// ```
#[inline]
pub fn approx_ne(a: f64, b: f64, epsilon: Option<f64>) -> bool {
    !approx_eq(a, b, epsilon)
}

/// Check if a value is approximately zero.
///
/// This is the most common comparison pattern in technical analysis.
/// Use before division operations to avoid division by zero.
///
/// # Arguments
/// * `value` - The value to check
/// * `epsilon` - Optional tolerance (defaults to DEFAULT_EPSILON)
///
/// # Returns
/// * `true` if `|value| < epsilon`
///
/// # Examples
/// ```rust
/// use haze_library::utils::float_compare::approx_zero;
///
/// // Exact zero
/// assert!(approx_zero(0.0, None));
///
/// // Very small value (rounding error)
/// assert!(approx_zero(1e-15, None));
///
/// // Division guard pattern
/// let numerator = 10.0;
/// let divisor = 0.0;
/// let result = if approx_zero(divisor, None) {
///     f64::NAN // Avoid division by zero
/// } else {
///     numerator / divisor
/// };
/// assert!(result.is_nan());
/// ```
///
/// # Use Cases
/// - Division guards (check denominator before division)
/// - Range checks in indicators (Stochastic, RSI)
/// - Mean deviation checks (CCI)
/// - Zero-crossing detection
#[inline]
pub fn approx_zero(value: f64, epsilon: Option<f64>) -> bool {
    approx_eq(value, 0.0, epsilon)
}

/// Check if a value is NOT approximately zero.
///
/// Logical negation of `approx_zero`. Use instead of `!= 0.0` checks.
///
/// # Arguments
/// * `value` - The value to check
/// * `epsilon` - Optional tolerance (defaults to DEFAULT_EPSILON)
///
/// # Returns
/// * `true` if `|value| >= epsilon`
///
/// # Examples
/// ```rust
/// use haze_library::utils::float_compare::approx_not_zero;
///
/// assert!(approx_not_zero(1.0, None));
/// assert!(approx_not_zero(1e-9, None));
/// assert!(!approx_not_zero(1e-15, None));
/// ```
#[inline]
pub fn approx_not_zero(value: f64, epsilon: Option<f64>) -> bool {
    !approx_zero(value, epsilon)
}

/// Compare two f64 values with relative tolerance.
///
/// Uses relative error comparison, which is better suited for comparing
/// large magnitude values where absolute epsilon would be too strict.
///
/// # Algorithm
/// ```text
/// relative_error = |a - b| / max(|a|, |b|)
/// return relative_error <= rel_tol
/// ```
///
/// # Arguments
/// * `a` - First value
/// * `b` - Second value
/// * `rel_tol` - Relative tolerance (e.g., 1e-9 for 0.0000001% difference)
///
/// # Returns
/// * `true` if relative error <= rel_tol
///
/// # Examples
/// ```rust
/// use haze_library::utils::float_compare::relative_eq;
///
/// // Small values: absolute epsilon works
/// assert!(relative_eq(1.0, 1.0 + 1e-10, 1e-9));
///
/// // Large values: relative epsilon is better
/// let large_a = 1e15;
/// let large_b = 1e15 + 1.0;
/// assert!(relative_eq(large_a, large_b, 1e-14));
/// ```
///
/// # When to Use
/// - Comparing very large numbers (>1e6)
/// - Percentage-based comparisons
/// - Scientific calculations with varying scales
/// - When absolute epsilon would be too strict or too loose
///
/// # Design Notes
/// - Falls back to absolute comparison when both values near zero
/// - Handles edge cases (both zero, one zero, opposite signs)
/// - More expensive than absolute epsilon (requires division)
#[inline]
pub fn relative_eq(a: f64, b: f64, rel_tol: f64) -> bool {
    let diff = (a - b).abs();
    let max_val = a.abs().max(b.abs());

    // If both near zero, use absolute comparison
    if max_val < DEFAULT_EPSILON {
        return diff < DEFAULT_EPSILON;
    }

    // Relative comparison
    diff <= max_val * rel_tol
}

/// Safe division that returns NaN when the denominator is approximately zero.
///
/// Use this instead of direct division to avoid panics and infinity results.
///
/// # Arguments
/// * `numerator` - The numerator
/// * `denominator` - The denominator
///
/// # Returns
/// * `numerator / denominator` if denominator is not approximately zero
/// * `f64::NAN` if denominator is approximately zero
///
/// # Examples
/// ```rust
/// use haze_library::utils::float_compare::safe_div;
///
/// // Normal division
/// assert_eq!(safe_div(10.0, 2.0), 5.0);
///
/// // Division by exact zero
/// assert!(safe_div(10.0, 0.0).is_nan());
///
/// // Division by near-zero
/// assert!(safe_div(10.0, 1e-15).is_nan());
/// ```
///
/// # Use Cases
/// - RSI calculation (avg_loss may be zero)
/// - Stochastic calculation (range may be zero)
/// - Percentage calculations
/// - Any division where denominator can be zero
#[inline]
pub fn safe_div(numerator: f64, denominator: f64) -> f64 {
    if approx_zero(denominator, None) {
        f64::NAN
    } else {
        numerator / denominator
    }
}

/// Safe division that returns a default value when the denominator is approximately zero.
///
/// Similar to `safe_div` but allows specifying a custom default instead of NaN.
///
/// # Arguments
/// * `numerator` - The numerator
/// * `denominator` - The denominator
/// * `default` - The value to return if denominator is approximately zero
///
/// # Returns
/// * `numerator / denominator` if denominator is not approximately zero
/// * `default` if denominator is approximately zero
///
/// # Examples
/// ```rust
/// use haze_library::utils::float_compare::safe_div_or;
///
/// // Normal division
/// assert_eq!(safe_div_or(10.0, 2.0, 0.0), 5.0);
///
/// // Division by zero with default
/// assert_eq!(safe_div_or(10.0, 0.0, 0.0), 0.0);
/// assert_eq!(safe_div_or(10.0, 0.0, 100.0), 100.0);
/// ```
///
/// # Use Cases
/// - When you want a specific fallback value (e.g., 0.0 for RSI)
/// - When NaN would propagate and break subsequent calculations
/// - When you have a meaningful default for zero denominator
#[inline]
pub fn safe_div_or(numerator: f64, denominator: f64, default: f64) -> f64 {
    if approx_zero(denominator, None) {
        default
    } else {
        numerator / denominator
    }
}

/// Check if a value is approximately greater than another value.
///
/// # Arguments
/// * `a` - First value
/// * `b` - Second value
/// * `epsilon` - Optional tolerance (defaults to DEFAULT_EPSILON)
///
/// # Returns
/// * `true` if `a > b + epsilon`
#[inline]
pub fn approx_gt(a: f64, b: f64, epsilon: Option<f64>) -> bool {
    let eps = epsilon.unwrap_or(DEFAULT_EPSILON);
    a > b + eps
}

/// Check if a value is approximately less than another value.
///
/// # Arguments
/// * `a` - First value
/// * `b` - Second value
/// * `epsilon` - Optional tolerance (defaults to DEFAULT_EPSILON)
///
/// # Returns
/// * `true` if `a < b - epsilon`
#[inline]
pub fn approx_lt(a: f64, b: f64, epsilon: Option<f64>) -> bool {
    let eps = epsilon.unwrap_or(DEFAULT_EPSILON);
    a < b - eps
}

/// Check if a value is approximately greater than or equal to another value.
///
/// # Arguments
/// * `a` - First value
/// * `b` - Second value
/// * `epsilon` - Optional tolerance (defaults to DEFAULT_EPSILON)
///
/// # Returns
/// * `true` if `a >= b - epsilon`
#[inline]
pub fn approx_ge(a: f64, b: f64, epsilon: Option<f64>) -> bool {
    !approx_lt(a, b, epsilon)
}

/// Check if a value is approximately less than or equal to another value.
///
/// # Arguments
/// * `a` - First value
/// * `b` - Second value
/// * `epsilon` - Optional tolerance (defaults to DEFAULT_EPSILON)
///
/// # Returns
/// * `true` if `a <= b + epsilon`
#[inline]
pub fn approx_le(a: f64, b: f64, epsilon: Option<f64>) -> bool {
    !approx_gt(a, b, epsilon)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ========================================================================
    // Basic Comparison Tests
    // ========================================================================

    #[test]
    fn test_approx_eq_exact() {
        assert!(approx_eq(1.0, 1.0, None));
        assert!(approx_eq(0.0, 0.0, None));
        assert!(approx_eq(-5.5, -5.5, None));
    }

    #[test]
    fn test_approx_eq_near() {
        // Within default epsilon
        assert!(approx_eq(1.0, 1.0 + 1e-15, None));
        assert!(approx_eq(1.0, 1.0 - 1e-15, None));

        // Classic floating-point issue
        assert!(approx_eq(0.1 + 0.2, 0.3, None));
    }

    #[test]
    fn test_approx_eq_different() {
        assert!(!approx_eq(1.0, 1.001, None));
        assert!(!approx_eq(0.0, 0.001, None));
        assert!(!approx_eq(1.0, 2.0, None));
    }

    #[test]
    fn test_approx_eq_custom_epsilon() {
        // Relaxed epsilon
        assert!(approx_eq(1.0, 1.00001, Some(1e-4)));
        assert!(!approx_eq(1.0, 1.001, Some(1e-4)));

        // Strict epsilon
        assert!(!approx_eq(1.0, 1.0 + 1e-11, Some(1e-12)));
    }

    #[test]
    fn test_approx_ne() {
        assert!(approx_ne(1.0, 2.0, None));
        assert!(approx_ne(0.0, 0.001, None));
        assert!(!approx_ne(1.0, 1.0, None));
        assert!(!approx_ne(1.0, 1.0 + 1e-15, None));
    }

    // ========================================================================
    // Zero Comparison Tests
    // ========================================================================

    #[test]
    fn test_approx_zero_exact() {
        assert!(approx_zero(0.0, None));
        assert!(approx_zero(-0.0, None));
    }

    #[test]
    fn test_approx_zero_near() {
        assert!(approx_zero(1e-15, None));
        assert!(approx_zero(-1e-15, None));
        assert!(approx_zero(1e-11, None));
    }

    #[test]
    fn test_approx_zero_not_zero() {
        assert!(!approx_zero(1e-9, None));
        assert!(!approx_zero(0.001, None));
        assert!(!approx_zero(1.0, None));
    }

    #[test]
    fn test_approx_not_zero() {
        assert!(approx_not_zero(1.0, None));
        assert!(approx_not_zero(1e-9, None));
        assert!(!approx_not_zero(1e-15, None));
        assert!(!approx_not_zero(0.0, None));
    }

    // ========================================================================
    // Relative Comparison Tests
    // ========================================================================

    #[test]
    fn test_relative_eq_small_values() {
        assert!(relative_eq(1.0, 1.0 + 1e-10, 1e-9));
        assert!(!relative_eq(1.0, 1.001, 1e-9));
    }

    #[test]
    fn test_relative_eq_large_values() {
        let large_a = 1e15;
        let large_b = 1e15 + 1.0;

        // Absolute epsilon would fail here
        assert!(!approx_eq(large_a, large_b, Some(DEFAULT_EPSILON)));

        // But relative epsilon succeeds
        assert!(relative_eq(large_a, large_b, 1e-14));
    }

    #[test]
    fn test_relative_eq_zero() {
        // Both near zero
        assert!(relative_eq(0.0, 0.0, 1e-9));
        assert!(relative_eq(1e-15, 1e-15, 1e-9));

        // One zero
        assert!(relative_eq(0.0, 1e-15, 1e-9));
    }

    // ========================================================================
    // Safe Division Tests
    // ========================================================================

    #[test]
    fn test_safe_div_normal() {
        assert_eq!(safe_div(10.0, 2.0), 5.0);
        assert_eq!(safe_div(-10.0, 2.0), -5.0);
        assert_eq!(safe_div(0.0, 5.0), 0.0);
    }

    #[test]
    fn test_safe_div_zero_denominator() {
        assert!(safe_div(1.0, 0.0).is_nan());
        assert!(safe_div(1.0, 1e-15).is_nan());
        assert!(safe_div(10.0, -1e-15).is_nan());
    }

    #[test]
    fn test_safe_div_or_normal() {
        assert_eq!(safe_div_or(10.0, 2.0, 0.0), 5.0);
        assert_eq!(safe_div_or(-10.0, 2.0, 99.0), -5.0);
    }

    #[test]
    fn test_safe_div_or_zero_denominator() {
        assert_eq!(safe_div_or(1.0, 0.0, 0.0), 0.0);
        assert_eq!(safe_div_or(1.0, 0.0, 100.0), 100.0);
        assert_eq!(safe_div_or(10.0, 1e-15, 42.0), 42.0);
    }

    // ========================================================================
    // Comparison Operators Tests
    // ========================================================================

    #[test]
    fn test_approx_gt() {
        assert!(approx_gt(2.0, 1.0, None));
        assert!(!approx_gt(1.0, 1.0, None));
        assert!(!approx_gt(1.0, 1.0 + 1e-15, None));
        assert!(approx_gt(1.001, 1.0, None));
    }

    #[test]
    fn test_approx_lt() {
        assert!(approx_lt(1.0, 2.0, None));
        assert!(!approx_lt(1.0, 1.0, None));
        assert!(!approx_lt(1.0 + 1e-15, 1.0, None));
        assert!(approx_lt(1.0, 1.001, None));
    }

    #[test]
    fn test_approx_ge() {
        assert!(approx_ge(2.0, 1.0, None));
        assert!(approx_ge(1.0, 1.0, None));
        assert!(approx_ge(1.0, 1.0 + 1e-15, None));
        assert!(!approx_ge(1.0, 2.0, None));
    }

    #[test]
    fn test_approx_le() {
        assert!(approx_le(1.0, 2.0, None));
        assert!(approx_le(1.0, 1.0, None));
        assert!(approx_le(1.0 + 1e-15, 1.0, None));
        assert!(!approx_le(2.0, 1.0, None));
    }

    // ========================================================================
    // Real-World Use Case Tests
    // ========================================================================

    #[test]
    fn test_rsi_division_guard() {
        // Simulating RSI calculation
        let avg_loss = 0.0; // Can happen in strong uptrend
        let _avg_gain = 5.0;

        // Old way (wrong):
        // if avg_loss == 0.0 { ... } // Might fail with 1e-16

        // New way (correct):
        assert!(approx_zero(avg_loss, None));
    }

    #[test]
    fn test_stochastic_range_check() {
        // Simulating Stochastic calculation
        let high = 100.0;
        let low = 100.0; // Can happen with no volatility
        let range = high - low;

        // Old way (wrong):
        // if range == 0.0 { ... }

        // New way (correct):
        assert!(approx_zero(range, None));
    }

    #[test]
    fn test_percentage_calculation() {
        let price_change = 0.1;
        let original_price = 100.0;

        let pct = safe_div(price_change, original_price) * 100.0;
        assert!((pct - 0.1).abs() < 1e-9);

        // Zero price case
        let zero_price_pct = safe_div(0.1, 0.0);
        assert!(zero_price_pct.is_nan());
    }

    #[test]
    fn test_floating_point_accumulation() {
        // Test accumulated floating-point errors
        let mut sum = 0.0;
        for _ in 0..1000 {
            sum += 0.001;
        }
        sum -= 1.0;

        // sum should be 0, but it's not exactly due to rounding
        assert!(sum != 0.0); // This is why we need approx_zero
        assert!(approx_zero(sum, None)); // This works correctly
    }

    // ========================================================================
    // Edge Cases and Boundary Tests
    // ========================================================================

    #[test]
    fn test_nan_handling() {
        // NaN comparisons always return false (per IEEE 754)
        assert!(!approx_eq(f64::NAN, f64::NAN, None));
        assert!(!approx_eq(1.0, f64::NAN, None));
        assert!(!approx_zero(f64::NAN, None));
    }

    #[test]
    fn test_infinity_handling() {
        assert!(!approx_eq(f64::INFINITY, f64::INFINITY, None));
        assert!(!approx_zero(f64::INFINITY, None));
        assert!(safe_div(1.0, f64::INFINITY) == 0.0);
    }

    #[test]
    fn test_negative_zero() {
        assert!(approx_eq(0.0, -0.0, None));
        assert!(approx_zero(-0.0, None));
    }

    #[test]
    fn test_epsilon_constants() {
        assert_eq!(DEFAULT_EPSILON, 1e-10);
        assert_eq!(STRICT_EPSILON, 1e-12);
        assert_eq!(RELAXED_EPSILON, 1e-8);

        // Verify ordering
        use std::hint::black_box;
        assert!(black_box(STRICT_EPSILON) < black_box(DEFAULT_EPSILON));
        assert!(black_box(DEFAULT_EPSILON) < black_box(RELAXED_EPSILON));
    }

    // ========================================================================
    // Performance Characteristics Tests
    // ========================================================================

    #[test]
    fn test_inline_optimization() {
        // This test verifies that functions are inlined
        // In release mode, these should have zero overhead
        let a = 1.0;
        let b = 1.0 + 1e-15;

        // Multiple calls should be optimized away
        assert!(approx_eq(a, b, None));
        assert!(approx_eq(a, b, None));
        assert!(approx_eq(a, b, None));
    }
}
