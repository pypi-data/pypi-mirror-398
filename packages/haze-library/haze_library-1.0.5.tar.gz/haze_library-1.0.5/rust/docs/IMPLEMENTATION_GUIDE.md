# Module Documentation Implementation Guide

## Quick Start

This guide explains how to apply the generated module-level documentation to the Haze Rust codebase.

## Generated Documentation Files

All enhanced documentation is in `/Users/zhaoleon/Desktop/haze/haze/rust/docs/`:

```
docs/
├── module_docs_momentum.md          # Momentum indicators documentation
├── module_docs_volatility.md        # Volatility indicators documentation
├── module_docs_trend.md             # Trend indicators documentation
├── module_docs_stats.md             # Statistical utilities documentation
├── module_docs_parallel.md          # Parallel computation documentation
├── module_docs_ml_models.md         # ML models documentation
├── MODULE_DOCUMENTATION_SUMMARY.md  # Overall summary
└── IMPLEMENTATION_GUIDE.md          # This file
```

## Implementation Steps

### Step 1: Review Generated Documentation

Open each `module_docs_*.md` file and review the proposed documentation sections:
- Module purpose and overview
- Main exports listing
- Usage examples
- Performance characteristics
- Error handling guide
- Related modules

### Step 2: Apply Documentation to Source Files

For each module, copy the Rust documentation block from the `.md` file to the corresponding `.rs` file:

#### Example: Momentum Module

**File**: `/Users/zhaoleon/Desktop/haze/haze/rust/src/indicators/momentum.rs`

**Current Documentation** (lines 1-54):
```rust
//! Momentum Indicators Module
//!
//! # Overview
//! This module provides a comprehensive set of momentum-based technical indicators
//! ...
```

**Replace with Enhanced Version**:
Open `docs/module_docs_momentum.md` and copy the entire Rust code block to replace lines 1-54.

#### Repeat for All Modules:

1. **Volatility**: `src/indicators/volatility.rs` ← `docs/module_docs_volatility.md`
2. **Trend**: `src/indicators/trend.rs` ← `docs/module_docs_trend.md`
3. **Stats**: `src/utils/stats.rs` ← `docs/module_docs_stats.md`
4. **Parallel**: `src/utils/parallel.rs` ← `docs/module_docs_parallel.md`
5. **ML Models**: `src/ml/models.rs` ← `docs/module_docs_ml_models.md`

### Step 3: Verify Documentation

Run Rustdoc to verify the documentation renders correctly:

```bash
cd /Users/zhaoleon/Desktop/haze/haze/rust
cargo doc --no-deps --open
```

This will:
1. Generate HTML documentation
2. Open it in your default browser
3. Show any documentation warnings or errors

Check for:
- ✅ All links resolve correctly
- ✅ Code examples display properly
- ✅ No broken cross-references
- ✅ Formatting looks clean

### Step 4: Validate Code Examples

Test that doc examples compile (even though marked `ignore`):

```bash
# Run doc tests (will skip `ignore` examples but check syntax)
cargo test --doc

# Or manually verify examples compile
cargo doc --no-deps --document-private-items
```

For any examples that fail, update them in the source files.

### Step 5: Update CI/CD Pipeline

Add documentation checks to your CI workflow:

**Example GitHub Actions** (`.github/workflows/docs.yml`):
```yaml
name: Documentation

on: [push, pull_request]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          profile: minimal
          toolchain: stable
      - name: Generate documentation
        run: cargo doc --no-deps --all-features
      - name: Check doc tests
        run: cargo test --doc
      - name: Deploy to GitHub Pages
        if: github.ref == 'refs/heads/main'
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./target/doc
```

## Module-by-Module Details

### 1. Momentum Module

**File**: `rust/src/indicators/momentum.rs`

**Lines to Replace**: 1-54 (current module doc)

**Key Additions**:
- Categorized function list (Oscillators, Divergence, Statistical, Advanced)
- RSI overbought/oversold example
- MACD crossover strategy example
- Multi-indicator confirmation pattern

**Validation**:
```bash
# Check RSI example compiles conceptually
# (Actual test is in tests/, doc example is illustrative)
cargo test test_rsi
```

### 2. Volatility Module

**File**: `rust/src/indicators/volatility.rs`

**Lines to Replace**: 1-51 (current module doc)

**Key Additions**:
- Position sizing with ATR example
- Bollinger Band squeeze detection
- Chandelier Exit trailing stop
- Multi-channel confirmation (BB + KC + DC)

**Validation**:
```bash
cargo test test_atr
cargo test test_bollinger_bands
```

### 3. Trend Module

**File**: `rust/src/indicators/trend.rs`

**Lines to Replace**: 1-56 (current module doc)

**Key Additions**:
- SuperTrend trading system
- ADX trend strength filter
- PSAR trailing stop implementation
- Choppiness Index market phase detection
- Signal interpretation guide

**Validation**:
```bash
cargo test test_supertrend
cargo test test_adx
cargo test test_psar
```

### 4. Stats Module

**File**: `rust/src/utils/stats.rs`

**Lines to Replace**: 1-69 (current module doc)

**Key Additions**:
- Pair trading correlation example
- Z-score mean reversion strategy
- Time series forecasting workflow
- Kahan summation precision notes

**Validation**:
```bash
cargo test test_correlation
cargo test test_zscore
cargo test test_linear_regression
```

### 5. Parallel Module

**File**: `rust/src/utils/parallel.rs`

**Lines to Replace**: 1-66 (current module doc)

**Key Additions**:
- Market scanner example (100+ symbols)
- Multi-timeframe analysis pattern
- Parameter optimization workflow
- Performance benchmarks (2/4/8 cores)
- Sequential vs parallel decision guide

**Validation**:
```bash
cargo test test_parallel_sma
cargo test test_parallel_rsi
```

### 6. ML Models Module

**File**: `rust/src/ml/models.rs`

**Lines to Replace**: 1-8 (currently only has dead_code allowances)

**Key Additions**:
- SOLID architecture diagram
- Polymorphic model usage examples
- Model selection and backtesting
- Feature engineering integration
- Performance characteristics

**Validation**:
```bash
cargo test test_linreg_model
cargo test test_sfg_model_container
```

## Verification Checklist

After implementing all documentation:

- [ ] All 6 module files updated
- [ ] `cargo doc --no-deps --open` runs without errors
- [ ] `cargo test --doc` passes
- [ ] All cross-reference links work (click them in rendered docs)
- [ ] Examples render correctly in HTML output
- [ ] Performance notes display in appropriate sections
- [ ] Error handling sections are clear

## Optional Enhancements

### Add Tutorials

Create tutorial files in `docs/tutorials/`:

```
docs/tutorials/
├── 01_getting_started.md
├── 02_momentum_indicators.md
├── 03_volatility_analysis.md
├── 04_trend_following.md
├── 05_statistical_tools.md
├── 06_parallel_processing.md
└── 07_ml_integration.md
```

### Improve Function-Level Docs

Continue enhancing individual function documentation:

```rust
/// RSI - Relative Strength Index
///
/// Calculates the Relative Strength Index using Wilder's smoothing method.
/// RSI measures the magnitude of recent price changes to evaluate overbought
/// or oversold conditions.
///
/// # Algorithm
/// 1. Calculate price changes: `change[i] = close[i] - close[i-1]`
/// 2. Separate gains and losses
/// 3. Apply Wilder's smoothing: `avg = (prev_avg * (period-1) + new) / period`
/// 4. Compute RS = avg_gain / avg_loss
/// 5. RSI = 100 - (100 / (1 + RS))
///
/// # Parameters
/// - `close`: Close price series
/// - `period`: Lookback period (typically 14)
///
/// # Returns
/// `Ok(Vec<f64>)` where:
/// - Values range from 0-100
/// - First `period` values are NaN (warmup period)
/// - RSI > 70 traditionally considered overbought
/// - RSI < 30 traditionally considered oversold
///
/// # Errors
/// - `HazeError::EmptyInput`: `close` is empty
/// - `HazeError::InvalidPeriod`: `period` is 0
/// - `HazeError::InsufficientData`: `period >= close.len()`
///
/// # Examples
/// ```
/// use haze_library::indicators::momentum::rsi;
///
/// let close = vec![44.0, 44.25, 44.5, 44.0, 43.75, 44.0, 44.25, 44.5,
///                  44.75, 45.0, 45.25, 45.0, 44.75, 45.0, 45.25];
///
/// let rsi_values = rsi(&close, 14).unwrap();
///
/// // First valid value at index 14
/// assert!(rsi_values[14] >= 0.0 && rsi_values[14] <= 100.0);
/// ```
///
/// # Performance
/// Time: O(n) | Space: O(n) | Single-pass algorithm
///
/// # References
/// - Wilder, J. Welles (1978). "New Concepts in Technical Trading Systems"
pub fn rsi(close: &[f64], period: usize) -> HazeResult<Vec<f64>> {
    // ... implementation ...
}
```

### Add Benchmarks

Create `benches/indicator_bench.rs`:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use haze_library::indicators::momentum::rsi;

fn benchmark_rsi(c: &mut Criterion) {
    let data: Vec<f64> = (0..10000).map(|i| 100.0 + (i as f64) * 0.01).collect();

    c.bench_function("rsi_10k", |b| {
        b.iter(|| rsi(black_box(&data), black_box(14)))
    });
}

criterion_group!(benches, benchmark_rsi);
criterion_main!(benches);
```

Run benchmarks:
```bash
cargo bench
```

## Common Issues and Solutions

### Issue: Broken Links

**Problem**: Cross-reference links like `[`crate::utils::ma`]` not working

**Solution**: Ensure correct path syntax:
```rust
// ✅ Correct
/// See [`crate::utils::ma::sma`] for details

// ❌ Wrong
/// See [crate::utils::ma::sma] for details
```

### Issue: Example Doesn't Compile

**Problem**: Doc example shows error when running `cargo test --doc`

**Solution**: Mark as `ignore` if example is illustrative:
```rust
/// # Examples
/// ```rust,ignore  // Add ,ignore
/// use haze_library::indicators::momentum::rsi;
/// // ...
/// ```
```

### Issue: Documentation Too Long

**Problem**: Module doc exceeds reasonable length

**Solution**: Move detailed content to separate tutorial:
```rust
//! # Module Name
//! Brief overview...
//!
//! For detailed tutorials, see:
//! - [Getting Started](../../../docs/tutorials/getting_started.md)
//! - [Advanced Usage](../../../docs/tutorials/advanced.md)
```

## Contact and Support

For questions about documentation implementation:
- Review: `MODULE_DOCUMENTATION_SUMMARY.md`
- Check: Individual `module_docs_*.md` files
- Refer to: Rust documentation standards at https://doc.rust-lang.org/rustdoc/

## Next Steps

After completing this implementation:

1. ✅ Run full documentation build: `cargo doc --no-deps --open`
2. ✅ Verify coverage metrics improved: Check Rustdoc output
3. ✅ Commit changes with clear message: "docs: add comprehensive module-level documentation"
4. ✅ Update project README with link to generated docs
5. ✅ Consider publishing docs to docs.rs or GitHub Pages

Estimated time to implement: **1-2 hours** for all 6 modules
