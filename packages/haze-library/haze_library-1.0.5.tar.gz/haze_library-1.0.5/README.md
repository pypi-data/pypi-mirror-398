# 🌫️ Haze-Library

[![CI](https://github.com/your-org/haze-library/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/haze-library/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/your-org/haze-library/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/haze-library)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Python Version](https://img.shields.io/badge/python-3.14%2B-blue)](https://www.python.org/downloads/)
[![Rust](https://img.shields.io/badge/rust-1.75%2B-orange)](https://www.rust-lang.org/)
[![PyO3](https://img.shields.io/badge/PyO3-0.27-green)](https://pyo3.rs/)

**High-performance quantitative trading indicators library with Rust backend**

**基于 Rust 的高性能量化交易指标库**

---

## 🌍 Language / 语言

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## 📖 English Documentation

### ✨ Key Features

- **🚀 215 Technical Indicators**: Complete coverage of TA-Lib, pandas-ta, harmonic patterns, and custom indicators
- **⚡ Rust Performance**: 5-10x faster than pure Python implementations
- **🎯 High Precision**: < 1e-9 error tolerance vs reference implementations
- **🧩 Minimal Dependencies**: Core indicator algorithms are implemented in Rust; external crates are limited to infrastructure and feature-gated
- **🔒 Type Safe**: Full type annotations
- **📦 Easy Install**: Prebuilt wheels for Linux/Windows/macOS
- **🐍 Pythonic API**: Seamless integration with pandas, numpy, and other Python libraries

### 🧮 Numerical Stability & Performance Policy

- `f64` as the numeric baseline with epsilon-based comparisons in Rust
- Compensated summation (Kahan/Neumaier) for long sums and rolling windows, plus periodic re-normalization to reduce drift
- Welford online variance for stable single-pass statistics
- Correctness before speed: optimizations (Rayon/SIMD) are optional features and must pass precision validation (< 1e-9)

### 📦 Installation

#### From PyPI (Recommended)
```bash
pip install haze-library
```

#### Optional extras
```bash
# CCXT execution helpers
pip install haze-library[execution]
```

#### From Source
```bash
git clone https://github.com/kwannz/haze.git
cd haze
pip install maturin
maturin develop --release
```

#### Prerequisites
- Python 3.14+
- Rust 1.75+ (required only for building from source)

### 🚀 Quick Start

```python
import haze_library as haze

# Price data
close_prices = [100.0, 101.0, 102.0, 101.5, 103.0, 102.5, 104.0]
high_prices = [101.0, 102.0, 103.0, 102.5, 104.0, 103.5, 105.0]
low_prices = [99.0, 100.0, 101.0, 100.5, 102.0, 101.5, 103.0]
volume = [1000, 1200, 1100, 1300, 1250, 1150, 1400]

# Moving Averages
sma = haze.py_sma(close_prices, period=3)
ema = haze.py_ema(close_prices, period=3)

# Volatility Indicators
atr = haze.py_atr(high_prices, low_prices, close_prices, period=3)
upper, middle, lower = haze.py_bollinger_bands(close_prices, period=3, std_dev=2.0)

# Momentum Indicators
rsi = haze.py_rsi(close_prices, period=3)
macd, signal, histogram = haze.py_macd(close_prices, fast=12, slow=26, signal=9)

# Trend Indicators
supertrend, direction = haze.py_supertrend(high_prices, low_prices, close_prices, period=3, multiplier=3.0)
adx = haze.py_adx(high_prices, low_prices, close_prices, period=3)

# Volume Indicators
obv = haze.py_obv(close_prices, volume)
mfi = haze.py_mfi(high_prices, low_prices, close_prices, volume, period=3)

# Harmonic Patterns (XABCD Pattern Detection)
# Returns: signals(1=bullish/-1=bearish), prz_upper, prz_lower, probability
signals, prz_up, prz_lo, prob = haze.py_harmonics(high_prices, low_prices, close_prices)

# Get detailed pattern information
patterns = haze.py_harmonics_patterns(high_prices, low_prices, left_bars=5, right_bars=5, include_forming=True)
for p in patterns:
    print(f"{p.pattern_type_zh}: {p.state}, PRZ={p.prz_center:.2f}, Prob={p.completion_probability:.1%}")
```

### ⚠️ Error Handling

Haze-Library uses Python exceptions for error handling. Most indicator functions will raise `ValueError` when given invalid inputs:

```python
import haze_library as haze

# Example 1: Invalid period (too large)
try:
    prices = [100.0, 101.0, 102.0]
    rsi = haze.py_rsi(prices, period=14)  # Period > data length
except ValueError as e:
    print(f"Error: {e}")
    # Output: Error: Invalid period: 14 (must be > 0 and <= data length 3)

# Example 2: Mismatched array lengths
try:
    high = [101.0, 102.0, 103.0]
    low = [99.0, 100.0]  # Different length
    close = [100.0, 101.0, 102.0]
    atr = haze.py_atr(high, low, close, period=2)
except ValueError as e:
    print(f"Error: {e}")
    # Output: Error: Length mismatch: high=3, low=2

# Example 3: Empty input data
try:
    rsi = haze.py_rsi([], period=14)
except ValueError as e:
    print(f"Error: {e}")
    # Output: Error: Empty input: close cannot be empty

# Best Practice: Validate inputs before calling indicators
def calculate_rsi_safe(prices, period=14):
    """Calculate RSI with proper error handling."""
    if not prices:
        return None
    if period > len(prices):
        period = len(prices)  # Adjust period to data size

    try:
        return haze.py_rsi(prices, period=period)
    except ValueError as e:
        print(f"Failed to calculate RSI: {e}")
        return None
```

**Common Error Types:**
- `ValueError`: Raised for invalid inputs (wrong period, mismatched lengths, empty data, etc.)
- All error messages are descriptive and include details about what went wrong

**When Errors Are Raised:**
- Period is 0 or larger than the data length
- Input arrays have mismatched lengths (for multi-array indicators)
- Input data is empty
- Parameter values are out of valid range
- Data contains insufficient points for calculation

### 🔧 Multi-Framework Support

Haze supports multiple data frameworks for seamless integration:

#### Polars DataFrame
```python
import polars as pl
from haze_library import polars_ta

df = pl.read_csv('ohlcv.csv')

# Add indicators to DataFrame
df = polars_ta.sma(df, 'close', period=20)
df = polars_ta.rsi(df, 'close', period=14)
df = polars_ta.macd(df, 'close')  # Adds macd, macd_signal, macd_histogram columns
df = polars_ta.bollinger_bands(df, 'close')  # Adds bb_upper, bb_middle, bb_lower
```

#### PyTorch Tensors
```python
import torch
from haze_library import torch_ta

close = torch.tensor([100.0, 101.0, 102.0, ...])
high = torch.tensor([101.0, 102.0, 103.0, ...])
low = torch.tensor([99.0, 100.0, 101.0, ...])

# Calculate indicators (returns torch.Tensor)
sma = torch_ta.sma(close, period=20)
rsi = torch_ta.rsi(close, period=14)
macd, signal, hist = torch_ta.macd(close)
upper, middle, lower = torch_ta.bollinger_bands(close)
trend, direction = torch_ta.supertrend(high, low, close)
```

#### NumPy Arrays
```python
import numpy as np
from haze_library import np_ta

close = np.array([100.0, 101.0, 102.0, ...])

# Calculate indicators (returns np.ndarray)
sma = np_ta.sma(close, period=20)
rsi = np_ta.rsi(close, period=14)
```

### 📊 Indicator Categories (215 Total)

<details>
<summary><b>🔹 Volatility (10 indicators)</b></summary>

- **ATR**, **NATR**, True Range, Bollinger Bands, Keltner Channel, Donchian Channel, Chandelier Exit, Historical Volatility, Ulcer Index, Mass Index
</details>

<details>
<summary><b>🔹 Momentum (17 indicators)</b></summary>

- **RSI**, **MACD**, Stochastic, CCI, MFI, Williams %R, ROC, MOM, Fisher Transform, Stochastic RSI, KDJ, TSI, Ultimate Oscillator, Awesome Oscillator, APO, PPO, CMO
</details>

<details>
<summary><b>🔹 Trend (14 indicators)</b></summary>

- **SuperTrend**, **ADX**, Parabolic SAR, Aroon, DMI, TRIX, DPO, Vortex, Choppiness, QStick, VHF, DX, +DI, -DI
</details>

<details>
<summary><b>🔹 Volume (11 indicators)</b></summary>

- **OBV**, **VWAP**, Force Index, CMF, Volume Oscillator, AD, PVT, NVI, PVI, EOM, ADOSC
</details>

<details>
<summary><b>🔹 Moving Averages (16 indicators)</b></summary>

- **SMA**, **EMA**, **WMA**, DEMA, TEMA, T3, KAMA, HMA, RMA, ZLMA, FRAMA, ALMA, VIDYA, PWMA, SINWMA, SWMA
</details>

<details>
<summary><b>🔹 Candlestick Patterns (61 indicators)</b></summary>

- Doji, Hammer, Hanging Man, Engulfing (Bullish/Bearish), Harami, Piercing Pattern, Dark Cloud Cover, Morning Star, Evening Star, Three White Soldiers, Three Black Crows, Shooting Star, Marubozu, and 48 more patterns
</details>

<details>
<summary><b>🔹 Statistical (13 indicators)</b></summary>

- Linear Regression, Correlation, Z-Score, Covariance, Beta, Standard Error, CORREL, LINEARREG (Slope/Angle/Intercept), VAR, TSF
</details>

<details>
<summary><b>🔹 Other Categories</b></summary>

- **Price Transform (4)**: AVGPRICE, MEDPRICE, TYPPRICE, WCLPRICE
- **Math Operations (25)**: MAX, MIN, SUM, SQRT, LN, LOG10, EXP, ABS, CEIL, FLOOR, SIN, COS, TAN, ASIN, ACOS, ATAN, SINH, COSH, TANH, ADD, SUB, MULT, DIV, MINMAX, MINMAXINDEX
- **Overlap Studies (6)**: MIDPOINT, MIDPRICE, TRIMA, SAR, SAREXT, MAMA/FAMA
- **Cycle Indicators (5)**: HT_DCPERIOD, HT_DCPHASE, HT_PHASOR, HT_SINE, HT_TRENDMODE
- **Advanced Trading Signals (4)**: AI SuperTrend, AI Momentum Index, Dynamic MACD, ATR2 Signals
- **pandas-ta Exclusive (25)**: Entropy, Aberration, Squeeze, QQE, CTI, ER, Bias, PSL, RVI, Inertia, Alligator, EFI, KST, STC, TDFI, WAE, SMI, Coppock, PGO, VWMA, BOP, SSL Channel, CFO, Slope, Percent Rank
- **Harmonic Patterns (3)**: py_harmonics (signal), py_harmonics_patterns (detailed), py_harmonics_prz (PRZ calculation)
- **Others (8)**: Fibonacci Retracement/Extension, Ichimoku Cloud, Classic Pivots
</details>

For complete indicator list with parameters, see [IMPLEMENTED_INDICATORS.md](IMPLEMENTED_INDICATORS.md).

**📚 Full API Documentation**: For comprehensive API reference with detailed parameter descriptions, algorithms, examples, and cross-references, see [API_REFERENCE.md](docs/API_REFERENCE.md).

### 🎯 Performance Benchmarks

```
Benchmark: RSI (14-period, 10,000 data points)
─────────────────────────────────────────────
pandas-ta:     12.5 ms
TA-Lib:        8.2 ms
Haze-Library:  1.3 ms  (6.3x faster than TA-Lib)

Benchmark: Bollinger Bands (20-period, 10,000 data points)
───────────────────────────────────────────────────────────
pandas-ta:     15.8 ms
TA-Lib:        10.1 ms
Haze-Library:  2.1 ms  (4.8x faster than TA-Lib)

Benchmark: MACD (12/26/9, 10,000 data points)
─────────────────────────────────────────────
pandas-ta:     18.3 ms
TA-Lib:        11.4 ms
Haze-Library:  1.9 ms  (6.0x faster than TA-Lib)
```

### 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Python Application                     │
│                  (Trading Strategies)                    │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ PyO3 Bindings
                         ▼
┌─────────────────────────────────────────────────────────┐
│              haze_library Module (Python)                │
│     • py_rsi()  • py_macd()  • py_bollinger_bands()     │
│     • py_supertrend()  • py_obv()  • py_kdj()           │
│              (215 Python-callable functions)             │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ Rust FFI
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Rust Core Library                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Indicators Module                                 │  │
│  │  • momentum.rs  • volatility.rs  • trend.rs       │  │
│  │  • volume.rs    • ma.rs          • candlestick.rs │  │
│  │  • harmonics.rs (Harmonic Patterns)               │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### 📜 License

This project is licensed under **CC BY-NC 4.0** (Creative Commons Attribution-NonCommercial 4.0 International).

**⚠️ Non-Commercial Use Only**: This software is free for personal, educational, and research purposes. Commercial use is prohibited without explicit permission.

For commercial licensing inquiries, please contact: team@haze-library.com

### 🙏 Acknowledgments

- **TA-Lib**: Reference implementation for technical analysis
- **pandas-ta**: Inspiration for pandas integration patterns
- **PyO3**: Rust-Python bindings framework
- **Maturin**: Build tool for Rust Python extensions

---

<a name="中文"></a>
## 📖 中文文档

### ✨ 核心特性

- **🚀 215 个技术指标**：完整覆盖 TA-Lib、pandas-ta、谐波形态和自定义指标
- **⚡ Rust 性能**：比纯 Python 实现快 5-10 倍
- **🎯 高精度**：与参考实现相比误差容忍度 < 1e-9
- **🧩 依赖最小化**：核心指标算法自研；外部依赖仅用于基础设施并通过 feature 控制
- **🔒 类型安全**：完整的类型注解
- **📦 安装省心**：Linux/Windows/macOS 预编译 wheels
- **🐍 Pythonic API**：与 pandas、numpy 等 Python 库无缝集成

### 🧮 数值稳定性与性能策略

- 以 `f64` 为数值基线，并使用 epsilon 近似比较处理浮点误差
- 长序列累加与滚动窗口使用 Kahan/Neumaier 补偿求和，并通过定期重算抑制误差累积
- 方差/标准差等统计量使用 Welford 增量算法，避免多次遍历带来的误差放大
- 先正确、后加速：Rayon/SIMD 通过 feature 启用，必须通过精度验证（< 1e-9）

### 📦 安装

#### 从 PyPI 安装（推荐）
```bash
pip install haze-library
```

#### 可选扩展依赖
```bash
# CCXT 交易所执行辅助
pip install haze-library[execution]
```

#### 从源码安装
```bash
git clone https://github.com/kwannz/haze.git
cd haze
pip install maturin
maturin develop --release
```

#### 前置要求
- Python 3.14+
- Rust 1.75+（从源码构建时需要）

### 🚀 快速开始

```python
import haze_library as haze

# 价格数据
close_prices = [100.0, 101.0, 102.0, 101.5, 103.0, 102.5, 104.0]
high_prices = [101.0, 102.0, 103.0, 102.5, 104.0, 103.5, 105.0]
low_prices = [99.0, 100.0, 101.0, 100.5, 102.0, 101.5, 103.0]
volume = [1000, 1200, 1100, 1300, 1250, 1150, 1400]

# 移动平均线
sma = haze.py_sma(close_prices, period=3)
ema = haze.py_ema(close_prices, period=3)

# 波动率指标
atr = haze.py_atr(high_prices, low_prices, close_prices, period=3)
upper, middle, lower = haze.py_bollinger_bands(close_prices, period=3, std_dev=2.0)

# 动量指标
rsi = haze.py_rsi(close_prices, period=3)
macd, signal, histogram = haze.py_macd(close_prices, fast=12, slow=26, signal=9)

# 趋势指标
supertrend, direction = haze.py_supertrend(high_prices, low_prices, close_prices, period=3, multiplier=3.0)
adx = haze.py_adx(high_prices, low_prices, close_prices, period=3)

# 成交量指标
obv = haze.py_obv(close_prices, volume)
mfi = haze.py_mfi(high_prices, low_prices, close_prices, volume, period=3)

# 谐波形态检测（XABCD 形态）
# 返回：信号（1=看涨/-1=看跌）、PRZ 上沿、PRZ 下沿、完成概率
signals, prz_up, prz_lo, prob = haze.py_harmonics(high_prices, low_prices, close_prices)

# 获取详细形态信息
patterns = haze.py_harmonics_patterns(high_prices, low_prices, left_bars=5, right_bars=5, include_forming=True)
for p in patterns:
    print(f"{p.pattern_type_zh}: {p.state}, PRZ={p.prz_center:.2f}, 概率={p.completion_probability:.1%}")
```

### ⚠️ 错误处理

Haze-Library 使用 Python 异常进行错误处理。当输入无效时，大多数指标函数会抛出 `ValueError` 异常：

```python
import haze_library as haze

# 示例 1：无效的周期（过大）
try:
    prices = [100.0, 101.0, 102.0]
    rsi = haze.py_rsi(prices, period=14)  # 周期 > 数据长度
except ValueError as e:
    print(f"错误: {e}")
    # 输出: 错误: Invalid period: 14 (must be > 0 and <= data length 3)

# 示例 2：数组长度不匹配
try:
    high = [101.0, 102.0, 103.0]
    low = [99.0, 100.0]  # 长度不同
    close = [100.0, 101.0, 102.0]
    atr = haze.py_atr(high, low, close, period=2)
except ValueError as e:
    print(f"错误: {e}")
    # 输出: 错误: Length mismatch: high=3, low=2

# 示例 3：空输入数据
try:
    rsi = haze.py_rsi([], period=14)
except ValueError as e:
    print(f"错误: {e}")
    # 输出: 错误: Empty input: close cannot be empty

# 最佳实践：在调用指标前验证输入
def calculate_rsi_safe(prices, period=14):
    """安全地计算 RSI，带有错误处理。"""
    if not prices:
        return None
    if period > len(prices):
        period = len(prices)  # 调整周期以适应数据大小

    try:
        return haze.py_rsi(prices, period=period)
    except ValueError as e:
        print(f"计算 RSI 失败: {e}")
        return None
```

**常见错误类型：**
- `ValueError`：输入无效时抛出（错误的周期、长度不匹配、空数据等）
- 所有错误消息都具有描述性，包含错误详情

**何时会抛出错误：**
- 周期为 0 或大于数据长度
- 输入数组长度不匹配（对于多数组指标）
- 输入数据为空
- 参数值超出有效范围
- 数据点不足以进行计算

### 📊 指标分类（共 215 个）

<details>
<summary><b>🔹 波动率指标（10 个）</b></summary>

- **ATR**（平均真实波幅）、**NATR**（归一化 ATR）、True Range、布林带、肯特纳通道、唐奇安通道、吊灯止损、历史波动率、溃疡指数、质量指数
</details>

<details>
<summary><b>🔹 动量指标（17 个）</b></summary>

- **RSI**（相对强弱指标）、**MACD**、随机指标、CCI、MFI、威廉指标、变化率、动量、费舍尔变换、随机 RSI、KDJ、TSI、终极振荡器、动量震荡指标、APO、PPO、CMO
</details>

<details>
<summary><b>🔹 趋势指标（14 个）</b></summary>

- **SuperTrend**（超级趋势）、**ADX**（平均趋向指数）、抛物线转向指标、阿隆指标、DMI、TRIX、去趋势价格振荡器、涡流指标、震荡指数、量价棒、VHF、DX、+DI、-DI
</details>

<details>
<summary><b>🔹 成交量指标（11 个）</b></summary>

- **OBV**（能量潮）、**VWAP**（成交量加权平均价）、劲道指数、蔡金资金流量、成交量振荡器、累积/派发线、价量趋势、负量指标、正量指标、简易波动指标、蔡金 A/D 振荡器
</details>

<details>
<summary><b>🔹 移动平均线（16 个）</b></summary>

- **SMA**（简单移动平均）、**EMA**（指数移动平均）、**WMA**（加权移动平均）、DEMA、TEMA、T3、KAMA、HMA、RMA、ZLMA、FRAMA、ALMA、VIDYA、PWMA、SINWMA、SWMA
</details>

<details>
<summary><b>🔹 蜡烛图形态（61 个）</b></summary>

- 十字星、锤子线、上吊线、吞没形态（看涨/看跌）、孕线、刺透形态、乌云盖顶、早晨之星、黄昏之星、三白兵、三黑鸦、流星线、光头光脚等 48 种形态
</details>

<details>
<summary><b>🔹 统计指标（13 个）</b></summary>

- 线性回归、相关性、Z 分数、协方差、贝塔系数、标准误差、CORREL、LINEARREG（斜率/角度/截距）、VAR、TSF
</details>

<details>
<summary><b>🔹 其他类别</b></summary>

- **价格变换（4 个）**：平均价格、中间价、典型价格、加权收盘价
- **数学运算（25 个）**：MAX、MIN、SUM、SQRT、LN、LOG10、EXP、ABS、CEIL、FLOOR、三角函数、双曲函数、向量运算
- **重叠研究（6 个）**：MIDPOINT、MIDPRICE、TRIMA、SAR、SAREXT、MAMA/FAMA
- **周期指标（5 个）**：希尔伯特变换系列
- **高级交易信号（4 个）**：AI SuperTrend、AI 动量指数、动态 MACD、ATR2 信号
- **pandas-ta 独有（25 个）**：熵、偏离度、挤压、QQE、CTI、ER、乖离率、心理线、RVI、惯性、鳄鱼、EFI、KST、STC、TDFI、WAE、SMI、Coppock、PGO、VWMA、BOP、SSL 通道、CFO、斜率、百分位排名
- **谐波形态（3 个）**：py_harmonics（信号）、py_harmonics_patterns（详细形态）、py_harmonics_prz（PRZ 计算）
- **其他（8 个）**：斐波那契回撤/扩展、一目均衡表、枢轴点
</details>

完整指标列表及参数请参阅 [IMPLEMENTED_INDICATORS.md](IMPLEMENTED_INDICATORS.md)。

**📚 完整 API 文档**：详细的参数说明、算法解析、使用示例及交叉引用，请参阅 [API_REFERENCE.md](docs/API_REFERENCE.md)。

### 🎯 性能基准

```
基准测试：RSI（14 周期，10,000 个数据点）
─────────────────────────────────────────────
pandas-ta:     12.5 毫秒
TA-Lib:        8.2 毫秒
Haze-Library:  1.3 毫秒（比 TA-Lib 快 6.3 倍）

基准测试：布林带（20 周期，10,000 个数据点）
───────────────────────────────────────────────────────────
pandas-ta:     15.8 毫秒
TA-Lib:        10.1 毫秒
Haze-Library:  2.1 毫秒（比 TA-Lib 快 4.8 倍）

基准测试：MACD（12/26/9，10,000 个数据点）
─────────────────────────────────────────────
pandas-ta:     18.3 毫秒
TA-Lib:        11.4 毫秒
Haze-Library:  1.9 毫秒（比 TA-Lib 快 6.0 倍）
```

### 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                   Python 应用层                          │
│                  （交易策略）                             │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ PyO3 绑定
                         ▼
┌─────────────────────────────────────────────────────────┐
│              haze_library 模块（Python）                 │
│     • py_rsi()  • py_macd()  • py_bollinger_bands()     │
│     • py_supertrend()  • py_obv()  • py_kdj()           │
│              （215 个 Python 可调用函数）                 │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ Rust FFI
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Rust 核心库                             │
│  ┌───────────────────────────────────────────────────┐  │
│  │  指标模块                                          │  │
│  │  • momentum.rs  • volatility.rs  • trend.rs       │  │
│  │  • volume.rs    • ma.rs          • candlestick.rs │  │
│  │  • harmonics.rs（谐波形态）                        │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献指南。

### 📜 许可证

本项目采用 **CC BY-NC 4.0**（知识共享署名-非商业性使用 4.0 国际许可协议）授权。

**⚠️ 仅限非商业用途**：本软件可免费用于个人、教育和研究目的。未经明确许可，禁止商业使用。

商业许可咨询请联系：team@haze-library.com

### 🙏 致谢

- **TA-Lib**：技术分析参考实现
- **pandas-ta**：pandas 集成模式灵感来源
- **PyO3**：Rust-Python 绑定框架
- **Maturin**：Rust Python 扩展构建工具

---

**Made with ❤️ by the Haze Team**

**Last Updated**: 2025-12-26
