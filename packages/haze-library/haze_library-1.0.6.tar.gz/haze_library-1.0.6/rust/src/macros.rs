// macros.rs - 通用验证和初始化宏
//
// 消除指标函数中的重复代码
// 遵循 DRY 原则：一次定义，多处复用

/// 验证 OHLC 数据并返回长度
///
/// 检查：
/// - high 不为空
/// - high, low, close 长度匹配
///
/// # 用法
/// ```rust,ignore
/// let n = validate_ohlc!(high, low, close);
/// ```
#[macro_export]
macro_rules! validate_ohlc {
    ($high:expr, $low:expr, $close:expr) => {{
        use $crate::errors::validation;
        validation::validate_not_empty($high, "high")?;
        validation::validate_lengths_match(&[($high, "high"), ($low, "low"), ($close, "close")])?;
        $high.len()
    }};
}

/// 验证完整 OHLC 数据（包括 open）并返回长度
///
/// 检查：
/// - open 不为空
/// - open, high, low, close 长度匹配
///
/// # 用法
/// ```rust,ignore
/// let n = validate_full_ohlc!(open, high, low, close);
/// ```
#[macro_export]
macro_rules! validate_full_ohlc {
    ($open:expr, $high:expr, $low:expr, $close:expr) => {{
        use $crate::errors::validation;
        validation::validate_not_empty($open, "open")?;
        validation::validate_lengths_match(&[
            ($open, "open"),
            ($high, "high"),
            ($low, "low"),
            ($close, "close"),
        ])?;
        $open.len()
    }};
}

/// 验证 OHLCV 数据（含成交量）并返回长度
///
/// 检查：
/// - high 不为空
/// - high, low, close, volume 长度匹配
///
/// # 用法
/// ```rust,ignore
/// let n = validate_ohlcv!(high, low, close, volume);
/// ```
#[macro_export]
macro_rules! validate_ohlcv {
    ($high:expr, $low:expr, $close:expr, $volume:expr) => {{
        use $crate::errors::validation;
        validation::validate_not_empty($high, "high")?;
        validation::validate_lengths_match(&[
            ($high, "high"),
            ($low, "low"),
            ($close, "close"),
            ($volume, "volume"),
        ])?;
        $high.len()
    }};
}

/// 验证单个数组并返回长度
///
/// 检查：
/// - 数组不为空
///
/// # 用法
/// ```rust,ignore
/// let n = validate_single!(values, "close");
/// ```
#[macro_export]
macro_rules! validate_single {
    ($data:expr, $name:expr) => {{
        use $crate::errors::validation;
        validation::validate_not_empty($data, $name)?;
        $data.len()
    }};
}

/// 验证两个数组长度匹配并返回长度
///
/// # 用法
/// ```rust,ignore
/// let n = validate_pair!(x, "x", y, "y");
/// ```
#[macro_export]
macro_rules! validate_pair {
    ($data1:expr, $name1:expr, $data2:expr, $name2:expr) => {{
        use $crate::errors::validation;
        validation::validate_not_empty($data1, $name1)?;
        validation::validate_same_length($data1, $name1, $data2, $name2)?;
        $data1.len()
    }};
}

/// 验证周期参数
///
/// 检查：
/// - period > 0
/// - period <= data_len
///
/// # 用法
/// ```rust,ignore
/// validate_period!(period, n);
/// ```
#[macro_export]
macro_rules! validate_period {
    ($period:expr, $data_len:expr) => {{
        use $crate::errors::validation;
        validation::validate_period($period, $data_len)?;
    }};
}

/// 初始化结果向量（填充 NAN）
///
/// # 用法
/// ```rust,ignore
/// let mut result = init_result!(n);
/// ```
#[macro_export]
macro_rules! init_result {
    ($n:expr) => {
        vec![f64::NAN; $n]
    };
}

/// 初始化多个结果向量
///
/// # 用法
/// ```rust,ignore
/// let (mut r1, mut r2, mut r3) = init_results!(n, 3);
/// ```
#[macro_export]
macro_rules! init_results {
    ($n:expr, 2) => {
        (vec![f64::NAN; $n], vec![f64::NAN; $n])
    };
    ($n:expr, 3) => {
        (vec![f64::NAN; $n], vec![f64::NAN; $n], vec![f64::NAN; $n])
    };
    ($n:expr, 4) => {
        (
            vec![f64::NAN; $n],
            vec![f64::NAN; $n],
            vec![f64::NAN; $n],
            vec![f64::NAN; $n],
        )
    };
    ($n:expr, 5) => {
        (
            vec![f64::NAN; $n],
            vec![f64::NAN; $n],
            vec![f64::NAN; $n],
            vec![f64::NAN; $n],
            vec![f64::NAN; $n],
        )
    };
}

#[cfg(test)]
mod tests {
    use crate::errors::HazeResult;

    fn test_ohlc_validation() -> HazeResult<()> {
        let high = vec![1.0, 2.0, 3.0];
        let low = vec![0.5, 1.5, 2.5];
        let close = vec![0.8, 1.8, 2.8];

        let n = validate_ohlc!(&high, &low, &close);
        assert_eq!(n, 3);
        Ok(())
    }

    fn test_single_validation() -> HazeResult<()> {
        let values = vec![1.0, 2.0, 3.0];
        let n = validate_single!(&values, "values");
        assert_eq!(n, 3);
        Ok(())
    }

    fn test_init_result() {
        let result = init_result!(5);
        assert_eq!(result.len(), 5);
        assert!(result.iter().all(|x| x.is_nan()));
    }

    fn test_init_results() {
        let (r1, r2, r3) = init_results!(3, 3);
        assert_eq!(r1.len(), 3);
        assert_eq!(r2.len(), 3);
        assert_eq!(r3.len(), 3);
    }

    #[test]
    fn run_macro_tests() {
        test_ohlc_validation().unwrap();
        test_single_validation().unwrap();
        test_init_result();
        test_init_results();
    }
}
