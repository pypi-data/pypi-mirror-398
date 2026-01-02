// indicators/harmonics.rs - 谐波形态检测（XABCD Patterns）
//
// 基于 Fibonacci 比率检测经典谐波形态：
// - Gartley, Bat, Butterfly, Crab, DeepCrab, Shark, Cypher, ThreeDrive, AltBat
#![allow(dead_code)]
//
// 算法核心：
// 1. Swing Point Detection（摆动点检测）- 找出局部高点/低点
// 2. XABCD Pattern Matching（模式匹配）- 验证 Fibonacci 比率
// 3. Pattern Validation（有效性验证）- 确认形态完整性
// 4. PRZ Calculation（潜在反转区）- 多Fib投影汇合
// 5. Probability Estimation（概率估算）- 基于Fib吻合度

use crate::errors::validation::{validate_lengths_match, validate_not_empty, validate_range};
use crate::errors::{HazeError, HazeResult};
use crate::init_result;
use crate::types::HarmonicSignals;
use crate::utils::math::is_zero;
use std::collections::HashMap;

// ============================================================================
// 枚举定义
// ============================================================================

/// 谐波形态类型（9种）
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PatternType {
    Gartley,
    Bat,
    Butterfly,
    Crab,
    DeepCrab,
    Shark,
    Cypher,
    ThreeDrive,
    AltBat,
}

impl PatternType {
    /// 获取中文名称
    pub fn name_zh(&self) -> &'static str {
        match self {
            PatternType::Gartley => "伽利形态",
            PatternType::Bat => "蝙蝠形态",
            PatternType::Butterfly => "蝴蝶形态",
            PatternType::Crab => "螃蟹形态",
            PatternType::DeepCrab => "深蟹形态",
            PatternType::Shark => "鲨鱼形态",
            PatternType::Cypher => "赛弗形态",
            PatternType::ThreeDrive => "三驱形态",
            PatternType::AltBat => "变体蝙蝠",
        }
    }

    /// 获取英文名称
    pub fn name_en(&self) -> &'static str {
        match self {
            PatternType::Gartley => "Gartley",
            PatternType::Bat => "Bat",
            PatternType::Butterfly => "Butterfly",
            PatternType::Crab => "Crab",
            PatternType::DeepCrab => "DeepCrab",
            PatternType::Shark => "Shark",
            PatternType::Cypher => "Cypher",
            PatternType::ThreeDrive => "ThreeDrive",
            PatternType::AltBat => "AltBat",
        }
    }

    /// 获取 Fibonacci 比率规则
    pub fn ratios(&self) -> PatternRatios {
        match self {
            PatternType::Gartley => PatternRatios {
                ab_xa: (0.618, 0.618),
                bc_ab: (0.382, 0.886),
                cd_bc: (1.272, 1.618),
                ad_xa: (0.786, 0.786),
                cd_xc: None,
            },
            PatternType::Bat => PatternRatios {
                ab_xa: (0.382, 0.500),
                bc_ab: (0.382, 0.886),
                cd_bc: (1.618, 2.618),
                ad_xa: (0.886, 0.886),
                cd_xc: None,
            },
            PatternType::Butterfly => PatternRatios {
                ab_xa: (0.786, 0.786),
                bc_ab: (0.382, 0.886),
                cd_bc: (1.618, 2.24),
                ad_xa: (1.27, 1.618),
                cd_xc: None,
            },
            PatternType::Crab => PatternRatios {
                ab_xa: (0.382, 0.618),
                bc_ab: (0.382, 0.886),
                cd_bc: (2.24, 3.618),
                ad_xa: (1.618, 1.618),
                cd_xc: None,
            },
            PatternType::DeepCrab => PatternRatios {
                ab_xa: (0.886, 0.886),
                bc_ab: (0.382, 0.886),
                cd_bc: (2.24, 3.618),
                ad_xa: (1.618, 1.618),
                cd_xc: None,
            },
            PatternType::Shark => PatternRatios {
                ab_xa: (0.382, 0.618),
                bc_ab: (1.13, 1.618),
                cd_bc: (1.618, 2.24),
                ad_xa: (0.886, 1.13),
                cd_xc: None,
            },
            PatternType::Cypher => PatternRatios {
                ab_xa: (0.382, 0.618),
                bc_ab: (1.272, 1.414),
                cd_bc: (0.0, 0.0), // Cypher 使用 CD/XC
                ad_xa: (0.786, 0.786),
                cd_xc: Some((0.786, 0.786)),
            },
            PatternType::ThreeDrive => PatternRatios {
                ab_xa: (1.272, 1.618),
                bc_ab: (0.618, 0.786),
                cd_bc: (1.272, 1.618),
                ad_xa: (1.272, 1.618),
                cd_xc: None,
            },
            PatternType::AltBat => PatternRatios {
                ab_xa: (0.382, 0.382),
                bc_ab: (0.382, 0.886),
                cd_bc: (2.0, 3.618),
                ad_xa: (1.13, 1.13),
                cd_xc: None,
            },
        }
    }

    /// 所有形态类型迭代器
    pub fn all() -> &'static [PatternType] {
        &[
            PatternType::Gartley,
            PatternType::Bat,
            PatternType::Butterfly,
            PatternType::Crab,
            PatternType::DeepCrab,
            PatternType::Shark,
            PatternType::Cypher,
            PatternType::ThreeDrive,
            PatternType::AltBat,
        ]
    }
}

/// 形态状态
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PatternState {
    Forming,  // 正在形成（有 XAB 或 XABC）
    Complete, // 已完成（有 XABCD）
}

// ============================================================================
// 结构体定义
// ============================================================================

/// Fibonacci 比率规则
#[derive(Debug, Clone, Copy)]
pub struct PatternRatios {
    pub ab_xa: (f64, f64), // (min, max)
    pub bc_ab: (f64, f64),
    pub cd_bc: (f64, f64),
    pub ad_xa: (f64, f64),
    pub cd_xc: Option<(f64, f64)>, // Cypher 特有
}

/// PRZ - 潜在反转区
#[derive(Debug, Clone, Copy)]
pub struct PrzZone {
    pub price_high: f64,      // PRZ 上边界
    pub price_low: f64,       // PRZ 下边界
    pub price_center: f64,    // PRZ 中心（最佳入场点）
    pub confluence_count: u8, // Fib 汇合数量（越多越强）
}

/// Swing Point - 摆动点结构
#[derive(Debug, Clone, Copy)]
pub struct SwingPoint {
    pub index: usize,
    pub price: f64,
    pub is_high: bool, // true=高点，false=低点
}

/// XABCD Pattern - 谐波形态结构（基础版本，保持向后兼容）
#[derive(Debug, Clone)]
pub struct HarmonicPattern {
    pub pattern_type: String, // "Gartley", "Bat", "Butterfly", etc.
    pub x: SwingPoint,
    pub a: SwingPoint,
    pub b: SwingPoint,
    pub c: SwingPoint,
    pub d: SwingPoint,
    pub is_bullish: bool,
    pub ratios: HashMap<String, f64>, // 实际 Fibonacci 比率
}

/// XABCD Pattern 扩展版本（包含PRZ、概率、目标价位）
#[derive(Debug, Clone)]
pub struct HarmonicPatternExt {
    pub pattern_type: PatternType,
    pub state: PatternState,
    pub x: SwingPoint,
    pub a: SwingPoint,
    pub b: SwingPoint,
    pub c: Option<SwingPoint>, // 形成中可能无 C
    pub d: Option<SwingPoint>, // 形成中可能无 D
    pub is_bullish: bool,
    pub ratios: HashMap<String, f64>,
    pub prz: Option<PrzZone>,        // 预测的 PRZ
    pub completion_probability: f64, // 0.0 ~ 1.0
    pub target_prices: Vec<f64>,     // TP1, TP2, TP3
    pub stop_loss: Option<f64>,      // 止损价位
}

impl HarmonicPatternExt {
    /// 从基础 HarmonicPattern 转换
    pub fn from_basic(p: &HarmonicPattern, pattern_type: PatternType) -> Self {
        Self {
            pattern_type,
            state: PatternState::Complete,
            x: p.x,
            a: p.a,
            b: p.b,
            c: Some(p.c),
            d: Some(p.d),
            is_bullish: p.is_bullish,
            ratios: p.ratios.clone(),
            prz: None,
            completion_probability: 0.0,
            target_prices: Vec::new(),
            stop_loss: None,
        }
    }
}

/// Fibonacci 比率容差（允许 ±3% 误差）
const FIB_TOLERANCE: f64 = 0.03;

/// 检测摆动点（局部极值）
///
/// - `high`: 高价序列
/// - `low`: 低价序列
/// - `left_bars`: 左侧窗口大小
/// - `right_bars`: 右侧窗口大小
///
/// 返回：摆动点向量（按时间顺序）
pub fn detect_swing_points(
    high: &[f64],
    low: &[f64],
    left_bars: usize,
    right_bars: usize,
) -> HazeResult<Vec<SwingPoint>> {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low")])?;
    let n = high.len();
    if left_bars == 0 {
        return Err(HazeError::InvalidPeriod {
            period: left_bars,
            data_len: n,
        });
    }
    if right_bars == 0 {
        return Err(HazeError::InvalidPeriod {
            period: right_bars,
            data_len: n,
        });
    }
    let required = left_bars
        .checked_add(right_bars)
        .and_then(|v| v.checked_add(1))
        .ok_or_else(|| HazeError::InvalidValue {
            index: 0,
            message: "left_bars + right_bars overflow".to_string(),
        })?;
    if n < required {
        return Err(HazeError::InsufficientData {
            required,
            actual: n,
        });
    }

    let mut swings = Vec::new();

    for i in left_bars..(n - right_bars) {
        // 检测高点：当前高价 >= 左右窗口内所有高价
        let is_swing_high = (i - left_bars..i).all(|j| high[i] >= high[j])
            && (i + 1..=i + right_bars).all(|j| high[i] >= high[j]);

        if is_swing_high {
            swings.push(SwingPoint {
                index: i,
                price: high[i],
                is_high: true,
            });
        }

        // 检测低点：当前低价 <= 左右窗口内所有低价
        let is_swing_low = (i - left_bars..i).all(|j| low[i] <= low[j])
            && (i + 1..=i + right_bars).all(|j| low[i] <= low[j]);

        if is_swing_low {
            swings.push(SwingPoint {
                index: i,
                price: low[i],
                is_high: false,
            });
        }
    }

    // 按索引排序
    swings.sort_by_key(|s| s.index);
    Ok(swings)
}

/// 检查 Fibonacci 比率是否在容差范围内
#[inline]
fn check_fib_ratio(actual: f64, expected: f64, tolerance: f64) -> bool {
    (actual - expected).abs() <= tolerance
}

/// 计算两点之间的价格变动比率（回撤或扩展）
#[inline]
fn calc_ratio(
    point1_price: f64,
    point2_price: f64,
    reference_start: f64,
    reference_end: f64,
) -> f64 {
    let point_move = (point2_price - point1_price).abs();
    let reference_move = (reference_end - reference_start).abs();
    if is_zero(reference_move) {
        0.0
    } else {
        point_move / reference_move
    }
}

#[inline]
fn validate_swings_len(swings: &[SwingPoint], required: usize) -> HazeResult<()> {
    if swings.len() < required {
        return Err(HazeError::InsufficientData {
            required,
            actual: swings.len(),
        });
    }
    Ok(())
}

/// 检测 Gartley 形态
///
/// Fibonacci 比率要求：
/// - AB = 0.618 XA
/// - BC = 0.382 ~ 0.886 AB
/// - CD = 1.272 ~ 1.618 BC
/// - AD = 0.786 XA
pub fn detect_gartley(swings: &[SwingPoint]) -> HazeResult<Vec<HarmonicPattern>> {
    validate_swings_len(swings, 5)?;
    let mut patterns = Vec::new();

    // 遍历所有可能的 XABCD 组合
    for i in 0..swings.len() - 4 {
        let x = swings[i];
        let a = swings[i + 1];
        let b = swings[i + 2];
        let c = swings[i + 3];
        let d = swings[i + 4];

        // 验证摆动点交替（高低高低高 或 低高低高低）
        if x.is_high == a.is_high
            || a.is_high == b.is_high
            || b.is_high == c.is_high
            || c.is_high == d.is_high
        {
            continue;
        }

        let is_bullish = !x.is_high; // X 是低点则为看涨

        // 计算 Fibonacci 比率
        let ab_xa = calc_ratio(a.price, b.price, x.price, a.price);
        let bc_ab = calc_ratio(b.price, c.price, a.price, b.price);
        let cd_bc = calc_ratio(c.price, d.price, b.price, c.price);
        let ad_xa = calc_ratio(a.price, d.price, x.price, a.price);

        // Gartley 比率验证
        if check_fib_ratio(ab_xa, 0.618, FIB_TOLERANCE)
            && (0.382 - FIB_TOLERANCE..=0.886 + FIB_TOLERANCE).contains(&bc_ab)
            && (1.272 - FIB_TOLERANCE..=1.618 + FIB_TOLERANCE).contains(&cd_bc)
            && check_fib_ratio(ad_xa, 0.786, FIB_TOLERANCE)
        {
            let mut ratios = HashMap::new();
            ratios.insert("AB/XA".to_string(), ab_xa);
            ratios.insert("BC/AB".to_string(), bc_ab);
            ratios.insert("CD/BC".to_string(), cd_bc);
            ratios.insert("AD/XA".to_string(), ad_xa);

            patterns.push(HarmonicPattern {
                pattern_type: "Gartley".to_string(),
                x,
                a,
                b,
                c,
                d,
                is_bullish,
                ratios,
            });
        }
    }

    Ok(patterns)
}

/// 检测 Bat 形态
///
/// Fibonacci 比率要求：
/// - AB = 0.382 ~ 0.500 XA
/// - BC = 0.382 ~ 0.886 AB
/// - CD = 1.618 ~ 2.618 BC
/// - AD = 0.886 XA
pub fn detect_bat(swings: &[SwingPoint]) -> HazeResult<Vec<HarmonicPattern>> {
    validate_swings_len(swings, 5)?;
    let mut patterns = Vec::new();

    for i in 0..swings.len() - 4 {
        let x = swings[i];
        let a = swings[i + 1];
        let b = swings[i + 2];
        let c = swings[i + 3];
        let d = swings[i + 4];

        if x.is_high == a.is_high
            || a.is_high == b.is_high
            || b.is_high == c.is_high
            || c.is_high == d.is_high
        {
            continue;
        }

        let is_bullish = !x.is_high;

        let ab_xa = calc_ratio(a.price, b.price, x.price, a.price);
        let bc_ab = calc_ratio(b.price, c.price, a.price, b.price);
        let cd_bc = calc_ratio(c.price, d.price, b.price, c.price);
        let ad_xa = calc_ratio(a.price, d.price, x.price, a.price);

        // Bat 比率验证
        if (0.382 - FIB_TOLERANCE..=0.500 + FIB_TOLERANCE).contains(&ab_xa)
            && (0.382 - FIB_TOLERANCE..=0.886 + FIB_TOLERANCE).contains(&bc_ab)
            && (1.618 - FIB_TOLERANCE..=2.618 + FIB_TOLERANCE).contains(&cd_bc)
            && check_fib_ratio(ad_xa, 0.886, FIB_TOLERANCE)
        {
            let mut ratios = HashMap::new();
            ratios.insert("AB/XA".to_string(), ab_xa);
            ratios.insert("BC/AB".to_string(), bc_ab);
            ratios.insert("CD/BC".to_string(), cd_bc);
            ratios.insert("AD/XA".to_string(), ad_xa);

            patterns.push(HarmonicPattern {
                pattern_type: "Bat".to_string(),
                x,
                a,
                b,
                c,
                d,
                is_bullish,
                ratios,
            });
        }
    }

    Ok(patterns)
}

/// 检测 Butterfly 形态
///
/// Fibonacci 比率要求：
/// - AB = 0.786 XA
/// - BC = 0.382 ~ 0.886 AB
/// - CD = 1.618 ~ 2.24 BC
/// - AD = 1.27 ~ 1.618 XA
pub fn detect_butterfly(swings: &[SwingPoint]) -> HazeResult<Vec<HarmonicPattern>> {
    validate_swings_len(swings, 5)?;
    let mut patterns = Vec::new();

    for i in 0..swings.len() - 4 {
        let x = swings[i];
        let a = swings[i + 1];
        let b = swings[i + 2];
        let c = swings[i + 3];
        let d = swings[i + 4];

        if x.is_high == a.is_high
            || a.is_high == b.is_high
            || b.is_high == c.is_high
            || c.is_high == d.is_high
        {
            continue;
        }

        let is_bullish = !x.is_high;

        let ab_xa = calc_ratio(a.price, b.price, x.price, a.price);
        let bc_ab = calc_ratio(b.price, c.price, a.price, b.price);
        let cd_bc = calc_ratio(c.price, d.price, b.price, c.price);
        let ad_xa = calc_ratio(a.price, d.price, x.price, a.price);

        // Butterfly 比率验证
        if check_fib_ratio(ab_xa, 0.786, FIB_TOLERANCE)
            && (0.382 - FIB_TOLERANCE..=0.886 + FIB_TOLERANCE).contains(&bc_ab)
            && (1.618 - FIB_TOLERANCE..=2.24 + FIB_TOLERANCE).contains(&cd_bc)
            && (1.27 - FIB_TOLERANCE..=1.618 + FIB_TOLERANCE).contains(&ad_xa)
        {
            let mut ratios = HashMap::new();
            ratios.insert("AB/XA".to_string(), ab_xa);
            ratios.insert("BC/AB".to_string(), bc_ab);
            ratios.insert("CD/BC".to_string(), cd_bc);
            ratios.insert("AD/XA".to_string(), ad_xa);

            patterns.push(HarmonicPattern {
                pattern_type: "Butterfly".to_string(),
                x,
                a,
                b,
                c,
                d,
                is_bullish,
                ratios,
            });
        }
    }

    Ok(patterns)
}

/// 检测 Crab 形态
///
/// Fibonacci 比率要求：
/// - AB = 0.382 ~ 0.618 XA
/// - BC = 0.382 ~ 0.886 AB
/// - CD = 2.24 ~ 3.618 BC
/// - AD = 1.618 XA
pub fn detect_crab(swings: &[SwingPoint]) -> HazeResult<Vec<HarmonicPattern>> {
    validate_swings_len(swings, 5)?;
    let mut patterns = Vec::new();

    for i in 0..swings.len() - 4 {
        let x = swings[i];
        let a = swings[i + 1];
        let b = swings[i + 2];
        let c = swings[i + 3];
        let d = swings[i + 4];

        if x.is_high == a.is_high
            || a.is_high == b.is_high
            || b.is_high == c.is_high
            || c.is_high == d.is_high
        {
            continue;
        }

        let is_bullish = !x.is_high;

        let ab_xa = calc_ratio(a.price, b.price, x.price, a.price);
        let bc_ab = calc_ratio(b.price, c.price, a.price, b.price);
        let cd_bc = calc_ratio(c.price, d.price, b.price, c.price);
        let ad_xa = calc_ratio(a.price, d.price, x.price, a.price);

        // Crab 比率验证
        if (0.382 - FIB_TOLERANCE..=0.618 + FIB_TOLERANCE).contains(&ab_xa)
            && (0.382 - FIB_TOLERANCE..=0.886 + FIB_TOLERANCE).contains(&bc_ab)
            && (2.24 - FIB_TOLERANCE..=3.618 + FIB_TOLERANCE).contains(&cd_bc)
            && check_fib_ratio(ad_xa, 1.618, FIB_TOLERANCE)
        {
            let mut ratios = HashMap::new();
            ratios.insert("AB/XA".to_string(), ab_xa);
            ratios.insert("BC/AB".to_string(), bc_ab);
            ratios.insert("CD/BC".to_string(), cd_bc);
            ratios.insert("AD/XA".to_string(), ad_xa);

            patterns.push(HarmonicPattern {
                pattern_type: "Crab".to_string(),
                x,
                a,
                b,
                c,
                d,
                is_bullish,
                ratios,
            });
        }
    }

    Ok(patterns)
}

/// 检测 Shark 形态
///
/// Fibonacci 比率要求：
/// - AB = 0.382 ~ 0.618 XA（通常 0.618）
/// - BC = 1.13 ~ 1.618 AB
/// - CD = 1.618 ~ 2.24 BC
/// - AD = 0.886 ~ 1.13 XA
pub fn detect_shark(swings: &[SwingPoint]) -> HazeResult<Vec<HarmonicPattern>> {
    validate_swings_len(swings, 5)?;
    let mut patterns = Vec::new();

    for i in 0..swings.len() - 4 {
        let x = swings[i];
        let a = swings[i + 1];
        let b = swings[i + 2];
        let c = swings[i + 3];
        let d = swings[i + 4];

        if x.is_high == a.is_high
            || a.is_high == b.is_high
            || b.is_high == c.is_high
            || c.is_high == d.is_high
        {
            continue;
        }

        let is_bullish = !x.is_high;

        let ab_xa = calc_ratio(a.price, b.price, x.price, a.price);
        let bc_ab = calc_ratio(b.price, c.price, a.price, b.price);
        let cd_bc = calc_ratio(c.price, d.price, b.price, c.price);
        let ad_xa = calc_ratio(a.price, d.price, x.price, a.price);

        // Shark 比率验证
        if (0.382 - FIB_TOLERANCE..=0.618 + FIB_TOLERANCE).contains(&ab_xa)
            && (1.13 - FIB_TOLERANCE..=1.618 + FIB_TOLERANCE).contains(&bc_ab)
            && (1.618 - FIB_TOLERANCE..=2.24 + FIB_TOLERANCE).contains(&cd_bc)
            && (0.886 - FIB_TOLERANCE..=1.13 + FIB_TOLERANCE).contains(&ad_xa)
        {
            let mut ratios = HashMap::new();
            ratios.insert("AB/XA".to_string(), ab_xa);
            ratios.insert("BC/AB".to_string(), bc_ab);
            ratios.insert("CD/BC".to_string(), cd_bc);
            ratios.insert("AD/XA".to_string(), ad_xa);

            patterns.push(HarmonicPattern {
                pattern_type: "Shark".to_string(),
                x,
                a,
                b,
                c,
                d,
                is_bullish,
                ratios,
            });
        }
    }

    Ok(patterns)
}

/// 检测 Cypher 形态
///
/// Fibonacci 比率要求：
/// - AB = 0.382 ~ 0.618 XA
/// - BC = 1.272 ~ 1.414 AB
/// - CD = 0.786 XC
/// - AD = 0.786 XA
pub fn detect_cypher(swings: &[SwingPoint]) -> HazeResult<Vec<HarmonicPattern>> {
    validate_swings_len(swings, 5)?;
    let mut patterns = Vec::new();

    for i in 0..swings.len() - 4 {
        let x = swings[i];
        let a = swings[i + 1];
        let b = swings[i + 2];
        let c = swings[i + 3];
        let d = swings[i + 4];

        if x.is_high == a.is_high
            || a.is_high == b.is_high
            || b.is_high == c.is_high
            || c.is_high == d.is_high
        {
            continue;
        }

        let is_bullish = !x.is_high;

        let ab_xa = calc_ratio(a.price, b.price, x.price, a.price);
        let bc_ab = calc_ratio(b.price, c.price, a.price, b.price);
        let cd_xc = calc_ratio(c.price, d.price, x.price, c.price);
        let ad_xa = calc_ratio(a.price, d.price, x.price, a.price);

        // Cypher 比率验证（注意 CD 是相对 XC 而非 BC）
        if (0.382 - FIB_TOLERANCE..=0.618 + FIB_TOLERANCE).contains(&ab_xa)
            && (1.272 - FIB_TOLERANCE..=1.414 + FIB_TOLERANCE).contains(&bc_ab)
            && check_fib_ratio(cd_xc, 0.786, FIB_TOLERANCE)
            && check_fib_ratio(ad_xa, 0.786, FIB_TOLERANCE)
        {
            let mut ratios = HashMap::new();
            ratios.insert("AB/XA".to_string(), ab_xa);
            ratios.insert("BC/AB".to_string(), bc_ab);
            ratios.insert("CD/XC".to_string(), cd_xc);
            ratios.insert("AD/XA".to_string(), ad_xa);

            patterns.push(HarmonicPattern {
                pattern_type: "Cypher".to_string(),
                x,
                a,
                b,
                c,
                d,
                is_bullish,
                ratios,
            });
        }
    }

    Ok(patterns)
}

/// 检测所有谐波形态（聚合函数）
pub fn detect_all_harmonics(
    high: &[f64],
    low: &[f64],
    left_bars: usize,
    right_bars: usize,
) -> HazeResult<Vec<HarmonicPattern>> {
    let swings = detect_swing_points(high, low, left_bars, right_bars)?;

    let mut all_patterns = Vec::new();

    all_patterns.extend(detect_gartley(&swings)?);
    all_patterns.extend(detect_bat(&swings)?);
    all_patterns.extend(detect_butterfly(&swings)?);
    all_patterns.extend(detect_crab(&swings)?);
    all_patterns.extend(detect_shark(&swings)?);
    all_patterns.extend(detect_cypher(&swings)?);
    all_patterns.extend(detect_deep_crab(&swings)?);
    all_patterns.extend(detect_three_drive(&swings)?);
    all_patterns.extend(detect_alt_bat(&swings)?);

    // 按 D 点索引排序（时间顺序）
    all_patterns.sort_by_key(|p| p.d.index);

    Ok(all_patterns)
}

// ============================================================================
// 新增形态检测
// ============================================================================

/// 检测 Deep Crab 形态
pub fn detect_deep_crab(swings: &[SwingPoint]) -> HazeResult<Vec<HarmonicPattern>> {
    detect_pattern_generic(swings, PatternType::DeepCrab)
}

/// 检测 Three Drive 形态
pub fn detect_three_drive(swings: &[SwingPoint]) -> HazeResult<Vec<HarmonicPattern>> {
    detect_pattern_generic(swings, PatternType::ThreeDrive)
}

/// 检测 Alt Bat 形态
pub fn detect_alt_bat(swings: &[SwingPoint]) -> HazeResult<Vec<HarmonicPattern>> {
    detect_pattern_generic(swings, PatternType::AltBat)
}

/// 通用形态检测函数
fn detect_pattern_generic(
    swings: &[SwingPoint],
    pattern_type: PatternType,
) -> HazeResult<Vec<HarmonicPattern>> {
    let mut patterns = Vec::new();
    validate_swings_len(swings, 5)?;

    let ratios = pattern_type.ratios();

    for i in 0..swings.len() - 4 {
        let x = swings[i];
        let a = swings[i + 1];
        let b = swings[i + 2];
        let c = swings[i + 3];
        let d = swings[i + 4];

        if x.is_high == a.is_high
            || a.is_high == b.is_high
            || b.is_high == c.is_high
            || c.is_high == d.is_high
        {
            continue;
        }

        let is_bullish = !x.is_high;
        let ab_xa = calc_ratio(a.price, b.price, x.price, a.price);
        let bc_ab = calc_ratio(b.price, c.price, a.price, b.price);
        let cd_bc = calc_ratio(c.price, d.price, b.price, c.price);
        let ad_xa = calc_ratio(a.price, d.price, x.price, a.price);

        if !ratio_in_range(ab_xa, ratios.ab_xa)
            || !ratio_in_range(bc_ab, ratios.bc_ab)
            || !ratio_in_range(cd_bc, ratios.cd_bc)
            || !ratio_in_range(ad_xa, ratios.ad_xa)
        {
            continue;
        }

        if let Some(cd_xc_range) = ratios.cd_xc {
            let cd_xc = calc_ratio(c.price, d.price, x.price, c.price);
            if !ratio_in_range(cd_xc, cd_xc_range) {
                continue;
            }
        }

        let mut ratio_map = HashMap::new();
        ratio_map.insert("AB/XA".to_string(), ab_xa);
        ratio_map.insert("BC/AB".to_string(), bc_ab);
        ratio_map.insert("CD/BC".to_string(), cd_bc);
        ratio_map.insert("AD/XA".to_string(), ad_xa);

        patterns.push(HarmonicPattern {
            pattern_type: pattern_type.name_en().to_string(),
            x,
            a,
            b,
            c,
            d,
            is_bullish,
            ratios: ratio_map,
        });
    }
    Ok(patterns)
}

#[inline]
fn ratio_in_range(actual: f64, range: (f64, f64)) -> bool {
    actual >= range.0 - FIB_TOLERANCE && actual <= range.1 + FIB_TOLERANCE
}

// ============================================================================
// PRZ 计算
// ============================================================================

/// 计算潜在反转区（PRZ）
pub fn calculate_prz(
    x: &SwingPoint,
    a: &SwingPoint,
    b: &SwingPoint,
    c: &SwingPoint,
    pattern_type: PatternType,
) -> PrzZone {
    let ratios = pattern_type.ratios();
    let xa_move = (a.price - x.price).abs();
    let bc_move = (c.price - b.price).abs();
    let direction = if x.is_high { -1.0 } else { 1.0 };

    let mut projections = Vec::new();

    // AD 投影
    let ad_low = a.price + direction * ratios.ad_xa.0 * xa_move;
    let ad_high = a.price + direction * ratios.ad_xa.1 * xa_move;
    projections.push((ad_low.min(ad_high), ad_low.max(ad_high)));

    // CD 投影
    let cd_dir = if b.is_high { 1.0 } else { -1.0 };
    let cd_low = c.price + cd_dir * ratios.cd_bc.0 * bc_move;
    let cd_high = c.price + cd_dir * ratios.cd_bc.1 * bc_move;
    projections.push((cd_low.min(cd_high), cd_low.max(cd_high)));

    if let Some(cd_xc_range) = ratios.cd_xc {
        let xc_move = (c.price - x.price).abs();
        let cd_xc_low = c.price + direction * cd_xc_range.0 * xc_move;
        let cd_xc_high = c.price + direction * cd_xc_range.1 * xc_move;
        projections.push((cd_xc_low.min(cd_xc_high), cd_xc_low.max(cd_xc_high)));
    }

    let prz_low = projections
        .iter()
        .map(|(l, _)| *l)
        .fold(f64::NEG_INFINITY, f64::max);
    let prz_high = projections
        .iter()
        .map(|(_, h)| *h)
        .fold(f64::INFINITY, f64::min);

    let (final_low, final_high) = if prz_low > prz_high {
        let center: f64 =
            projections.iter().map(|(l, h)| (l + h) / 2.0).sum::<f64>() / projections.len() as f64;
        let spread = xa_move * 0.05;
        (center - spread, center + spread)
    } else {
        (prz_low, prz_high)
    };

    let prz_center = (final_low + final_high) / 2.0;
    let confluence = projections
        .iter()
        .filter(|(l, h)| prz_center >= *l && prz_center <= *h)
        .count() as u8;

    PrzZone {
        price_low: final_low,
        price_high: final_high,
        price_center: prz_center,
        confluence_count: confluence,
    }
}

// ============================================================================
// 概率计算
// ============================================================================

/// 计算形态完成概率
pub fn calc_completion_probability(
    ratios: &HashMap<String, f64>,
    pattern_type: PatternType,
) -> f64 {
    let ideal = pattern_type.ratios();
    let mut score = 0.0;

    if let Some(&ab_xa) = ratios.get("AB/XA") {
        let mid = (ideal.ab_xa.0 + ideal.ab_xa.1) / 2.0;
        score += (1.0 - ((ab_xa - mid).abs() / mid.max(0.001)).min(1.0)) * 0.3;
    }
    if let Some(&bc_ab) = ratios.get("BC/AB") {
        let mid = (ideal.bc_ab.0 + ideal.bc_ab.1) / 2.0;
        score += (1.0 - ((bc_ab - mid).abs() / mid.max(0.001)).min(1.0)) * 0.2;
    }
    if let Some(&cd_bc) = ratios.get("CD/BC") {
        let mid = (ideal.cd_bc.0 + ideal.cd_bc.1) / 2.0;
        if mid > 0.0 {
            score += (1.0 - ((cd_bc - mid).abs() / mid).min(1.0)) * 0.2;
        }
    }
    if let Some(&ad_xa) = ratios.get("AD/XA") {
        let mid = (ideal.ad_xa.0 + ideal.ad_xa.1) / 2.0;
        score += (1.0 - ((ad_xa - mid).abs() / mid.max(0.001)).min(1.0)) * 0.3;
    }
    score
}

/// 计算目标价位
pub fn calc_target_prices(pattern: &HarmonicPattern, is_bullish: bool) -> (f64, f64, f64) {
    let cd_move = (pattern.d.price - pattern.c.price).abs();
    let dir = if is_bullish { 1.0 } else { -1.0 };
    (
        pattern.d.price + dir * cd_move * 0.382,
        pattern.d.price + dir * cd_move * 0.618,
        pattern.c.price,
    )
}

// ============================================================================
// 预测性检测
// ============================================================================

/// 检测正在形成的形态（XABC 阶段）
pub fn detect_forming_patterns(
    high: &[f64],
    low: &[f64],
    left_bars: usize,
    right_bars: usize,
    lookback: usize,
) -> HazeResult<Vec<HarmonicPatternExt>> {
    if lookback == 0 {
        return Err(HazeError::InvalidPeriod {
            period: lookback,
            data_len: 1,
        });
    }
    let swings = detect_swing_points(high, low, left_bars, right_bars)?;
    let mut forming = Vec::new();

    validate_swings_len(&swings, 4)?;

    let start_idx = swings.len().saturating_sub(lookback);

    for i in start_idx..swings.len().saturating_sub(3) {
        let x = swings[i];
        let a = swings[i + 1];
        let b = swings[i + 2];
        let c = swings[i + 3];

        if x.is_high == a.is_high || a.is_high == b.is_high || b.is_high == c.is_high {
            continue;
        }

        let is_bullish = !x.is_high;
        let ab_xa = calc_ratio(a.price, b.price, x.price, a.price);
        let bc_ab = calc_ratio(b.price, c.price, a.price, b.price);

        for pattern_type in PatternType::all() {
            let ratios = pattern_type.ratios();
            if ratio_in_range(ab_xa, ratios.ab_xa) && ratio_in_range(bc_ab, ratios.bc_ab) {
                let prz = calculate_prz(&x, &a, &b, &c, *pattern_type);

                let mut partial_ratios = HashMap::new();
                partial_ratios.insert("AB/XA".to_string(), ab_xa);
                partial_ratios.insert("BC/AB".to_string(), bc_ab);

                // 部分概率（最高 70%）
                let ideal = pattern_type.ratios();
                let ab_mid = (ideal.ab_xa.0 + ideal.ab_xa.1) / 2.0;
                let bc_mid = (ideal.bc_ab.0 + ideal.bc_ab.1) / 2.0;
                let prob = ((1.0 - ((ab_xa - ab_mid).abs() / ab_mid.max(0.001)).min(1.0))
                    + (1.0 - ((bc_ab - bc_mid).abs() / bc_mid.max(0.001)).min(1.0)))
                    / 2.0
                    * 0.7;

                forming.push(HarmonicPatternExt {
                    pattern_type: *pattern_type,
                    state: PatternState::Forming,
                    x,
                    a,
                    b,
                    c: Some(c),
                    d: None,
                    is_bullish,
                    ratios: partial_ratios,
                    prz: Some(prz),
                    completion_probability: prob,
                    target_prices: Vec::new(),
                    stop_loss: None,
                });
            }
        }
    }
    Ok(forming)
}

// ============================================================================
// 时间序列 API
// ============================================================================

/// 谐波形态信号（时间序列格式）
///
/// 返回: (signals, prz_upper, prz_lower, probability)
/// - signals: 1=看涨, -1=看跌, 0=无信号
pub fn harmonics_signal(
    high: &[f64],
    low: &[f64],
    close: &[f64],
    left_bars: usize,
    right_bars: usize,
    min_probability: f64,
) -> HarmonicSignals {
    validate_not_empty(high, "high")?;
    validate_lengths_match(&[(high, "high"), (low, "low"), (close, "close")])?;
    validate_range("min_probability", min_probability, 0.0, 1.0)?;
    let n = high.len();

    let mut signals = vec![0.0; n];
    let mut prz_upper = init_result!(n);
    let mut prz_lower = init_result!(n);
    let mut probability = init_result!(n);

    let completed = detect_all_harmonics(high, low, left_bars, right_bars)?;

    for pattern in &completed {
        let d_idx = pattern.d.index;
        if d_idx >= n {
            continue;
        }

        let pattern_type = match pattern.pattern_type.as_str() {
            "Gartley" => PatternType::Gartley,
            "Bat" => PatternType::Bat,
            "Butterfly" => PatternType::Butterfly,
            "Crab" => PatternType::Crab,
            "DeepCrab" => PatternType::DeepCrab,
            "Shark" => PatternType::Shark,
            "Cypher" => PatternType::Cypher,
            "ThreeDrive" => PatternType::ThreeDrive,
            "AltBat" => PatternType::AltBat,
            _ => continue,
        };

        let prob = calc_completion_probability(&pattern.ratios, pattern_type);
        if prob >= min_probability {
            signals[d_idx] = if pattern.is_bullish { 1.0 } else { -1.0 };
            let prz = calculate_prz(&pattern.x, &pattern.a, &pattern.b, &pattern.c, pattern_type);
            prz_upper[d_idx] = prz.price_high;
            prz_lower[d_idx] = prz.price_low;
            probability[d_idx] = prob;
        }
    }

    let forming = detect_forming_patterns(high, low, left_bars, right_bars, 50)?;
    for pattern in &forming {
        if let Some(prz) = &pattern.prz {
            if pattern.completion_probability >= min_probability * 0.5 {
                let last_idx = n - 1;
                if is_zero(signals[last_idx]) && prz_upper[last_idx].is_nan() {
                    prz_upper[last_idx] = prz.price_high;
                    prz_lower[last_idx] = prz.price_low;
                    probability[last_idx] = pattern.completion_probability;
                }
            }
        }
    }

    Ok((signals, prz_upper, prz_lower, probability))
}

/// 检测所有形态（扩展版本）
pub fn detect_all_harmonics_ext(
    high: &[f64],
    low: &[f64],
    left_bars: usize,
    right_bars: usize,
    include_forming: bool,
) -> HazeResult<Vec<HarmonicPatternExt>> {
    let mut results = Vec::new();

    let completed = detect_all_harmonics(high, low, left_bars, right_bars)?;
    for p in &completed {
        let pattern_type = match p.pattern_type.as_str() {
            "Gartley" => PatternType::Gartley,
            "Bat" => PatternType::Bat,
            "Butterfly" => PatternType::Butterfly,
            "Crab" => PatternType::Crab,
            "DeepCrab" => PatternType::DeepCrab,
            "Shark" => PatternType::Shark,
            "Cypher" => PatternType::Cypher,
            "ThreeDrive" => PatternType::ThreeDrive,
            "AltBat" => PatternType::AltBat,
            _ => continue,
        };

        let prz = calculate_prz(&p.x, &p.a, &p.b, &p.c, pattern_type);
        let prob = calc_completion_probability(&p.ratios, pattern_type);
        let (tp1, tp2, tp3) = calc_target_prices(p, p.is_bullish);
        let stop = if p.is_bullish {
            p.d.price * 0.98
        } else {
            p.d.price * 1.02
        };

        let mut ext = HarmonicPatternExt::from_basic(p, pattern_type);
        ext.prz = Some(prz);
        ext.completion_probability = prob;
        ext.target_prices = vec![tp1, tp2, tp3];
        ext.stop_loss = Some(stop);
        results.push(ext);
    }

    if include_forming {
        results.extend(detect_forming_patterns(
            high, low, left_bars, right_bars, 50,
        )?);
    }

    results.sort_by_key(|p| {
        p.d.map(|d| d.index)
            .or_else(|| p.c.map(|c| c.index))
            .unwrap_or(p.b.index)
    });
    Ok(results)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_swing_detection() {
        let high = vec![10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 13.0];
        let low = vec![9.0, 11.0, 10.0, 12.0, 11.0, 13.0, 12.0];
        let swings = detect_swing_points(&high, &low, 1, 1).unwrap();
        assert!(!swings.is_empty());
    }

    #[test]
    fn test_fib_ratio_check() {
        assert!(check_fib_ratio(0.62, 0.618, 0.03));
        assert!(check_fib_ratio(0.615, 0.618, 0.03));
        assert!(!check_fib_ratio(0.70, 0.618, 0.03));
    }

    #[test]
    fn test_pattern_type_names() {
        assert_eq!(PatternType::Gartley.name_zh(), "伽利形态");
        assert_eq!(PatternType::Bat.name_en(), "Bat");
        assert_eq!(PatternType::all().len(), 9);
    }

    #[test]
    fn test_prz_calculation() {
        let x = SwingPoint {
            index: 0,
            price: 100.0,
            is_high: false,
        };
        let a = SwingPoint {
            index: 10,
            price: 150.0,
            is_high: true,
        };
        let b = SwingPoint {
            index: 20,
            price: 119.0,
            is_high: false,
        };
        let c = SwingPoint {
            index: 30,
            price: 140.0,
            is_high: true,
        };
        let prz = calculate_prz(&x, &a, &b, &c, PatternType::Gartley);
        assert!(prz.price_center > 100.0 && prz.price_center < 150.0);
    }

    #[test]
    fn test_harmonics_signal_format() {
        let high: Vec<f64> = (0..100).map(|i| 100.0 + (i as f64).sin() * 10.0).collect();
        let low: Vec<f64> = high.iter().map(|h| h - 2.0).collect();
        let close: Vec<f64> = high.iter().zip(&low).map(|(h, l)| (h + l) / 2.0).collect();

        let (signals, prz_u, prz_l, prob) =
            harmonics_signal(&high, &low, &close, 3, 3, 0.5).unwrap();

        assert_eq!(signals.len(), 100);
        assert_eq!(prz_u.len(), 100);
        assert_eq!(prz_l.len(), 100);
        assert_eq!(prob.len(), 100);
        assert!(signals.iter().all(|&s| s == -1.0 || s == 0.0 || s == 1.0));
    }
}

/// Comprehensive boundary tests for harmonics module
#[cfg(test)]
mod boundary_tests {
    use super::*;

    // ==================== Empty Input Tests ====================

    #[test]
    fn test_detect_swing_points_empty() {
        assert!(detect_swing_points(&[], &[], 1, 1).is_err());
    }

    #[test]
    fn test_detect_gartley_empty() {
        assert!(detect_gartley(&[]).is_err());
    }

    #[test]
    fn test_detect_bat_empty() {
        assert!(detect_bat(&[]).is_err());
    }

    #[test]
    fn test_detect_butterfly_empty() {
        assert!(detect_butterfly(&[]).is_err());
    }

    #[test]
    fn test_detect_crab_empty() {
        assert!(detect_crab(&[]).is_err());
    }

    #[test]
    fn test_detect_shark_empty() {
        assert!(detect_shark(&[]).is_err());
    }

    #[test]
    fn test_detect_cypher_empty() {
        assert!(detect_cypher(&[]).is_err());
    }

    #[test]
    fn test_detect_all_harmonics_empty() {
        assert!(detect_all_harmonics(&[], &[], 3, 3).is_err());
    }

    #[test]
    fn test_detect_forming_patterns_empty() {
        assert!(detect_forming_patterns(&[], &[], 3, 3, 50).is_err());
    }

    // ==================== Insufficient Data Tests ====================

    #[test]
    fn test_detect_swing_points_insufficient() {
        // Need at least left_strength + right_strength + 1 points
        let high = vec![10.0, 11.0];
        let low = vec![9.0, 10.0];
        assert!(detect_swing_points(&high, &low, 2, 2).is_err());
    }

    #[test]
    fn test_detect_patterns_few_swings() {
        // Patterns need at least 5 points (X, A, B, C, D)
        let swings = vec![
            SwingPoint {
                index: 0,
                price: 100.0,
                is_high: false,
            },
            SwingPoint {
                index: 10,
                price: 150.0,
                is_high: true,
            },
            SwingPoint {
                index: 20,
                price: 120.0,
                is_high: false,
            },
        ];

        assert!(detect_gartley(&swings).is_err());
        assert!(detect_bat(&swings).is_err());
        assert!(detect_butterfly(&swings).is_err());
    }

    // ==================== Length Mismatch Tests ====================

    #[test]
    fn test_detect_swing_points_length_mismatch() {
        let high = vec![10.0, 11.0, 12.0];
        let low = vec![9.0, 10.0]; // shorter
        assert!(detect_swing_points(&high, &low, 1, 1).is_err());
    }

    // ==================== Valid Pattern Detection Tests ====================

    #[test]
    fn test_detect_swing_points_basic() {
        // Create alternating pattern that should produce swings
        let high = vec![10.0, 15.0, 12.0, 18.0, 14.0, 20.0, 16.0];
        let low = vec![8.0, 13.0, 10.0, 16.0, 12.0, 18.0, 14.0];
        let swings = detect_swing_points(&high, &low, 1, 1).unwrap();
        assert!(swings.len() >= 2);
    }

    #[test]
    fn test_swing_point_creation() {
        let sp = SwingPoint {
            index: 5,
            price: 100.0,
            is_high: true,
        };
        assert_eq!(sp.index, 5);
        assert_eq!(sp.price, 100.0);
        assert!(sp.is_high);
    }

    #[test]
    fn test_harmonic_pattern_structure() {
        let mut ratios = std::collections::HashMap::new();
        ratios.insert("XAB".to_string(), 0.618);
        ratios.insert("ABC".to_string(), 0.786);
        ratios.insert("BCD".to_string(), 1.27);
        ratios.insert("XAD".to_string(), 0.786);

        let pattern = HarmonicPattern {
            pattern_type: "Gartley".to_string(),
            x: SwingPoint {
                index: 0,
                price: 100.0,
                is_high: false,
            },
            a: SwingPoint {
                index: 10,
                price: 150.0,
                is_high: true,
            },
            b: SwingPoint {
                index: 20,
                price: 119.0,
                is_high: false,
            },
            c: SwingPoint {
                index: 30,
                price: 140.0,
                is_high: true,
            },
            d: SwingPoint {
                index: 40,
                price: 110.0,
                is_high: false,
            },
            is_bullish: true,
            ratios,
        };
        assert_eq!(pattern.pattern_type, "Gartley");
        assert!(pattern.is_bullish);
    }

    // ==================== PRZ Calculation Tests ====================

    #[test]
    fn test_prz_zone_structure() {
        let prz = PrzZone {
            price_center: 110.0,
            price_high: 115.0,
            price_low: 105.0,
            confluence_count: 3,
        };
        assert!(prz.price_high > prz.price_center);
        assert!(prz.price_low < prz.price_center);
        assert!(prz.confluence_count > 0);
    }

    #[test]
    fn test_calculate_prz_bullish() {
        let x = SwingPoint {
            index: 0,
            price: 100.0,
            is_high: false,
        };
        let a = SwingPoint {
            index: 10,
            price: 150.0,
            is_high: true,
        };
        let b = SwingPoint {
            index: 20,
            price: 119.0,
            is_high: false,
        };
        let c = SwingPoint {
            index: 30,
            price: 140.0,
            is_high: true,
        };

        let prz = calculate_prz(&x, &a, &b, &c, PatternType::Gartley);

        // PRZ should be within pattern range
        assert!(prz.price_center >= x.price);
        assert!(prz.price_center <= a.price);
        assert!(prz.price_high > prz.price_low);
    }

    // ==================== Fib Ratio Tests ====================

    #[test]
    fn test_check_fib_ratio_exact() {
        assert!(check_fib_ratio(0.618, 0.618, 0.01));
        assert!(check_fib_ratio(0.382, 0.382, 0.01));
        assert!(check_fib_ratio(0.786, 0.786, 0.01));
    }

    #[test]
    fn test_check_fib_ratio_tolerance() {
        // Within tolerance
        assert!(check_fib_ratio(0.620, 0.618, 0.01));
        assert!(check_fib_ratio(0.616, 0.618, 0.01));

        // Outside tolerance
        assert!(!check_fib_ratio(0.650, 0.618, 0.01));
        assert!(!check_fib_ratio(0.580, 0.618, 0.01));
    }

    #[test]
    fn test_check_fib_ratio_zero_tolerance() {
        assert!(check_fib_ratio(0.618, 0.618, 0.0));
        assert!(!check_fib_ratio(0.619, 0.618, 0.0));
    }

    // ==================== Pattern Type Tests ====================

    #[test]
    fn test_pattern_type_all() {
        let all = PatternType::all();
        assert_eq!(all.len(), 9);
        assert!(all.contains(&PatternType::Gartley));
        assert!(all.contains(&PatternType::Bat));
        assert!(all.contains(&PatternType::Butterfly));
        assert!(all.contains(&PatternType::Crab));
        assert!(all.contains(&PatternType::Shark));
        assert!(all.contains(&PatternType::Cypher));
    }

    #[test]
    fn test_pattern_type_names() {
        assert!(!PatternType::Gartley.name_en().is_empty());
        assert!(!PatternType::Gartley.name_zh().is_empty());
        assert!(!PatternType::Bat.name_en().is_empty());
        assert!(!PatternType::Butterfly.name_en().is_empty());
    }

    // ==================== Completion Probability Tests ====================

    #[test]
    fn test_calc_completion_probability_valid() {
        let mut ratios = std::collections::HashMap::new();
        ratios.insert("AB/XA".to_string(), 0.62);
        ratios.insert("BC/AB".to_string(), 0.38);
        let prob = calc_completion_probability(&ratios, PatternType::Gartley);
        assert!((0.0..=1.0).contains(&prob));
    }

    #[test]
    fn test_calc_completion_probability_exact_ratios() {
        // Perfect Gartley ratios should give higher probability
        let mut ratios = std::collections::HashMap::new();
        ratios.insert("AB/XA".to_string(), 0.618);
        ratios.insert("BC/AB".to_string(), 0.786);
        ratios.insert("CD/BC".to_string(), 1.27);
        ratios.insert("AD/XA".to_string(), 0.786);
        let prob = calc_completion_probability(&ratios, PatternType::Gartley);
        assert!((0.0..=1.0).contains(&prob));
    }

    // ==================== Target Price Tests ====================

    #[test]
    fn test_calc_target_prices_bullish() {
        let pattern = HarmonicPattern {
            pattern_type: "Gartley".to_string(),
            x: SwingPoint {
                index: 0,
                price: 100.0,
                is_high: false,
            },
            a: SwingPoint {
                index: 10,
                price: 150.0,
                is_high: true,
            },
            b: SwingPoint {
                index: 20,
                price: 119.0,
                is_high: false,
            },
            c: SwingPoint {
                index: 30,
                price: 140.0,
                is_high: true,
            },
            d: SwingPoint {
                index: 40,
                price: 107.0,
                is_high: false,
            },
            is_bullish: true,
            ratios: std::collections::HashMap::new(),
        };

        let (t1, t2, t3) = calc_target_prices(&pattern, true);
        // Bullish targets should be above D
        assert!(t1 >= pattern.d.price);
        assert!(t2 >= t1);
        assert!(t3 >= t2);
    }

    #[test]
    fn test_calc_target_prices_bearish() {
        let pattern = HarmonicPattern {
            pattern_type: "Gartley".to_string(),
            x: SwingPoint {
                index: 0,
                price: 150.0,
                is_high: true,
            },
            a: SwingPoint {
                index: 10,
                price: 100.0,
                is_high: false,
            },
            b: SwingPoint {
                index: 20,
                price: 131.0,
                is_high: true,
            },
            c: SwingPoint {
                index: 30,
                price: 110.0,
                is_high: false,
            },
            d: SwingPoint {
                index: 40,
                price: 143.0,
                is_high: true,
            },
            is_bullish: false,
            ratios: std::collections::HashMap::new(),
        };

        let (t1, t2, t3) = calc_target_prices(&pattern, false);
        // Bearish targets should be below D
        assert!(t1 <= pattern.d.price);
        assert!(t2 <= t1);
        assert!(t3 <= t2);
    }

    // ==================== Harmonics Signal Tests ====================

    #[test]
    fn test_harmonics_signal_output_lengths() {
        let n = 50;
        let high: Vec<f64> = (0..n).map(|i| 100.0 + (i as f64).sin() * 10.0).collect();
        let low: Vec<f64> = high.iter().map(|h| h - 3.0).collect();
        let close: Vec<f64> = high.iter().zip(&low).map(|(h, l)| (h + l) / 2.0).collect();

        let (signals, prz_u, prz_l, prob) =
            harmonics_signal(&high, &low, &close, 2, 2, 0.5).unwrap();

        assert_eq!(signals.len(), n);
        assert_eq!(prz_u.len(), n);
        assert_eq!(prz_l.len(), n);
        assert_eq!(prob.len(), n);
    }

    #[test]
    fn test_harmonics_signal_valid_values() {
        let high = vec![10.0, 15.0, 12.0, 18.0, 14.0, 20.0, 16.0, 22.0, 18.0, 24.0];
        let low: Vec<f64> = high.iter().map(|h| h - 2.0).collect();
        let close: Vec<f64> = high.iter().zip(&low).map(|(h, l)| (h + l) / 2.0).collect();

        let (signals, _, _, prob) = harmonics_signal(&high, &low, &close, 1, 1, 0.5).unwrap();

        // Signals should be -1, 0, or 1
        for s in &signals {
            assert!(*s == -1.0 || *s == 0.0 || *s == 1.0 || s.is_nan());
        }

        // Probabilities should be between 0 and 1
        for p in &prob {
            if !p.is_nan() {
                assert!(*p >= 0.0 && *p <= 1.0);
            }
        }
    }

    // ==================== Extended Detection Tests ====================

    #[test]
    fn test_detect_all_harmonics_ext_output() {
        // Create price data that will form enough swing points for harmonic patterns
        // Use a larger dataset with more pronounced oscillations
        let high: Vec<f64> = (0..100)
            .map(|i| 100.0 + (i as f64 * 0.5).sin() * 30.0)
            .collect();
        let low: Vec<f64> = high.iter().map(|h| h - 5.0).collect();

        // First check we have enough swing points
        let swings = detect_swing_points(&high, &low, 2, 2).unwrap();
        if swings.len() >= 5 {
            let results = detect_all_harmonics_ext(&high, &low, 2, 2, true).unwrap();
            // May or may not find patterns, but should not panic
            let _ = results.len();
        }
        // If not enough swings, that's also valid - the test passes
    }

    // ==================== Edge Case Tests ====================

    #[test]
    fn test_detect_swing_points_flat_price() {
        // All prices the same - function should handle gracefully
        let high = vec![100.0; 10];
        let low = vec![99.0; 10];
        let swings = detect_swing_points(&high, &low, 1, 1).unwrap();
        // The key is it should not panic and produce valid SwingPoints
        // Each swing should have valid fields
        for s in &swings {
            assert!(s.price.is_finite());
            assert!(s.index < 10);
        }
    }

    #[test]
    fn test_detect_swing_points_monotonic_increase() {
        // Strictly increasing - minimal swings
        let high: Vec<f64> = (0..10).map(|i| 100.0 + i as f64).collect();
        let low: Vec<f64> = (0..10).map(|i| 99.0 + i as f64).collect();
        let swings = detect_swing_points(&high, &low, 1, 1).unwrap();
        // May find end points only
        assert!(swings.len() <= 2);
    }

    #[test]
    fn test_pattern_with_zero_prices() {
        let swings = vec![
            SwingPoint {
                index: 0,
                price: 0.0,
                is_high: false,
            },
            SwingPoint {
                index: 10,
                price: 100.0,
                is_high: true,
            },
            SwingPoint {
                index: 20,
                price: 50.0,
                is_high: false,
            },
            SwingPoint {
                index: 30,
                price: 80.0,
                is_high: true,
            },
            SwingPoint {
                index: 40,
                price: 30.0,
                is_high: false,
            },
        ];

        // Should handle gracefully without division by zero
        let patterns = detect_gartley(&swings).unwrap();
        // Result may be empty, but should not panic
        // Function returns successfully
        let _ = patterns.len();
    }

    #[test]
    fn test_prz_with_negative_prices() {
        // Some assets can have negative prices (e.g., oil futures)
        let x = SwingPoint {
            index: 0,
            price: -10.0,
            is_high: false,
        };
        let a = SwingPoint {
            index: 10,
            price: 20.0,
            is_high: true,
        };
        let b = SwingPoint {
            index: 20,
            price: 0.0,
            is_high: false,
        };
        let c = SwingPoint {
            index: 30,
            price: 15.0,
            is_high: true,
        };

        let prz = calculate_prz(&x, &a, &b, &c, PatternType::Gartley);
        // Should handle gracefully
        assert!(prz.price_high > prz.price_low);
    }
}
