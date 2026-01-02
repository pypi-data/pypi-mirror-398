// errors.rs - 统一错误处理模块
//
// 使用 thiserror 提供清晰的错误类型
// 遵循 SOLID 原则：单一职责，专注错误处理

use thiserror::Error;

#[cfg(feature = "python")]
use pyo3::exceptions::PyValueError;
#[cfg(feature = "python")]
use pyo3::prelude::*;

/// Haze 库核心错误类型
#[derive(Debug, Error)]
pub enum HazeError {
    /// 输入数据长度不足
    #[error("Insufficient data: need at least {required} elements, got {actual}")]
    InsufficientData { required: usize, actual: usize },

    /// 周期参数无效
    #[error("Invalid period: {period} (must be > 0 and <= data length {data_len})")]
    InvalidPeriod { period: usize, data_len: usize },

    /// 数组长度不匹配
    #[error("Length mismatch: {name1}={len1}, {name2}={len2}")]
    LengthMismatch {
        name1: &'static str,
        len1: usize,
        name2: &'static str,
        len2: usize,
    },

    /// 输入包含无效值
    #[error("Invalid value at index {index}: {message}")]
    InvalidValue { index: usize, message: String },

    /// 空输入
    #[error("Empty input: {name} cannot be empty")]
    EmptyInput { name: &'static str },

    /// 参数超出范围
    #[error("Parameter {name} out of range: {value} (valid range: {min}..{max})")]
    ParameterOutOfRange {
        name: &'static str,
        value: f64,
        min: f64,
        max: f64,
    },

    /// ML 模型错误
    #[error("Model error: {0}")]
    ModelError(String),

    /// IO 错误
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
}

/// PyO3 错误转换 - 将 HazeError 转换为 Python ValueError
#[cfg(feature = "python")]
impl From<HazeError> for PyErr {
    fn from(err: HazeError) -> PyErr {
        PyValueError::new_err(err.to_string())
    }
}

/// Result 类型别名
pub type HazeResult<T> = Result<T, HazeError>;

/// 输入验证辅助函数
pub mod validation {
    use super::{HazeError, HazeResult};

    /// 验证输入序列是否全部为有限值（非 NaN/Inf）
    #[inline]
    pub fn validate_finite(data: &[f64], name: &'static str) -> HazeResult<()> {
        for (index, value) in data.iter().enumerate() {
            if !value.is_finite() {
                return Err(HazeError::InvalidValue {
                    index,
                    message: format!("{name} contains non-finite value: {value}"),
                });
            }
        }
        Ok(())
    }

    /// 验证周期参数
    #[inline]
    pub fn validate_period(period: usize, data_len: usize) -> HazeResult<()> {
        if period == 0 || period > data_len {
            return Err(HazeError::InvalidPeriod { period, data_len });
        }
        Ok(())
    }

    /// 验证非空输入
    #[inline]
    pub fn validate_not_empty(data: &[f64], name: &'static str) -> HazeResult<()> {
        if data.is_empty() {
            return Err(HazeError::EmptyInput { name });
        }
        validate_finite(data, name)?;
        Ok(())
    }

    /// 验证非空输入（允许 NaN/Inf 作为内部暖启动数据）
    #[inline]
    pub fn validate_not_empty_allow_nan(data: &[f64], name: &'static str) -> HazeResult<()> {
        if data.is_empty() {
            return Err(HazeError::EmptyInput { name });
        }
        Ok(())
    }

    /// 验证数组长度匹配
    #[inline]
    pub fn validate_same_length(
        data1: &[f64],
        name1: &'static str,
        data2: &[f64],
        name2: &'static str,
    ) -> HazeResult<()> {
        if data1.is_empty() {
            return Err(HazeError::EmptyInput { name: name1 });
        }
        if data2.is_empty() {
            return Err(HazeError::EmptyInput { name: name2 });
        }
        if data1.len() != data2.len() {
            return Err(HazeError::LengthMismatch {
                name1,
                len1: data1.len(),
                name2,
                len2: data2.len(),
            });
        }
        validate_finite(data1, name1)?;
        validate_finite(data2, name2)?;
        Ok(())
    }

    /// 验证多个数组长度匹配
    #[inline]
    pub fn validate_lengths_match(arrays: &[(&[f64], &'static str)]) -> HazeResult<()> {
        if arrays.is_empty() {
            return Ok(());
        }
        let (first, first_name) = arrays[0];
        if first.is_empty() {
            return Err(HazeError::EmptyInput { name: first_name });
        }
        validate_finite(first, first_name)?;
        for &(arr, name) in &arrays[1..] {
            if arr.is_empty() {
                return Err(HazeError::EmptyInput { name });
            }
            if arr.len() != first.len() {
                return Err(HazeError::LengthMismatch {
                    name1: first_name,
                    len1: first.len(),
                    name2: name,
                    len2: arr.len(),
                });
            }
            validate_finite(arr, name)?;
        }
        Ok(())
    }

    /// 验证最小数据长度
    #[inline]
    pub fn validate_min_length(data: &[f64], required: usize) -> HazeResult<()> {
        if data.len() < required {
            return Err(HazeError::InsufficientData {
                required,
                actual: data.len(),
            });
        }
        Ok(())
    }

    /// 验证参数范围
    #[inline]
    pub fn validate_range(name: &'static str, value: f64, min: f64, max: f64) -> HazeResult<()> {
        if value < min || value > max {
            return Err(HazeError::ParameterOutOfRange {
                name,
                value,
                min,
                max,
            });
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use validation::*;

    #[test]
    fn test_validate_period() {
        assert!(validate_period(5, 10).is_ok());
        assert!(validate_period(0, 10).is_err());
        assert!(validate_period(11, 10).is_err());
    }

    #[test]
    fn test_validate_not_empty() {
        assert!(validate_not_empty(&[1.0, 2.0], "data").is_ok());
        assert!(validate_not_empty(&[], "data").is_err());
    }

    #[test]
    fn test_validate_same_length() {
        let a = vec![1.0, 2.0, 3.0];
        let b = vec![4.0, 5.0, 6.0];
        let c = vec![7.0, 8.0];

        assert!(validate_same_length(&a, "a", &b, "b").is_ok());
        assert!(validate_same_length(&a, "a", &c, "c").is_err());
    }

    #[test]
    fn test_validate_range() {
        assert!(validate_range("alpha", 0.5, 0.0, 1.0).is_ok());
        assert!(validate_range("alpha", 1.5, 0.0, 1.0).is_err());
        assert!(validate_range("alpha", -0.5, 0.0, 1.0).is_err());
    }

    #[test]
    fn test_error_display() {
        let err = HazeError::InvalidPeriod {
            period: 100,
            data_len: 50,
        };
        assert!(err.to_string().contains("100"));
        assert!(err.to_string().contains("50"));
    }
}
