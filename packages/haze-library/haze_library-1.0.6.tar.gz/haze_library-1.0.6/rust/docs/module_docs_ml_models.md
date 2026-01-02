# ML Models Module Documentation

## File Path
`/Users/zhaoleon/Desktop/haze/haze/rust/src/ml/models.rs`

## Proposed Module-Level Documentation

```rust
//! # Machine Learning Models Module
//!
//! This module provides machine learning model implementations for adaptive
//! technical indicators and predictive trading signals. It integrates linear
//! regression models from the `linfa` ecosystem to create data-driven
//! enhancements to traditional technical analysis.
//!
//! ## Module Purpose
//!
//! ML models enable:
//! - Adaptive indicator parameters that learn from market conditions
//! - Predictive signals based on historical price patterns
//! - Dynamic threshold adjustments for better signal quality
//! - Non-linear pattern recognition in price movements
//! - Backtested model selection for strategy optimization
//!
//! The module follows SOLID principles with unified `Predictor` trait interface,
//! enabling polymorphic model usage and easy extensibility.
//!
//! ## Main Exports
//!
//! ### Model Types
//! - [`ModelType`] - Enum for model selection (SVR, LinearRegression, Ridge)
//! - [`SFGModelConfig`] - Configuration for model parameters
//!
//! ### Concrete Models
//! - [`AISuperTrendLinReg`] - Linear regression for AI SuperTrend bias prediction
//! - [`ATR2RidgeModel`] - Ridge regression for ATR threshold adaptation
//! - [`MomentumLinRegModel`] - Linear model with polynomial features for momentum
//!
//! ### Model Container
//! - [`SFGModel`] - Unified enum wrapper for polymorphic model usage
//!
//! ### Traits
//! - [`Predictor`] - Common interface for all ML models
//!
//! ## Architecture
//!
//! ```text
//! ┌─────────────────────────────────────────────┐
//! │          Predictor Trait                     │
//! │  - predict(features) -> predictions          │
//! │  - is_trained() -> bool                      │
//! └──────────────────┬──────────────────────────┘
//!                    │
//!        ┌───────────┴───────────┐
//!        │                       │
//!        v                       v
//! ┌──────────────┐      ┌──────────────┐
//! │ AISuperTrend │      │  ATR2Ridge   │
//! │   LinReg     │      │    Model     │
//! └──────────────┘      └──────────────┘
//!        │                       │
//!        └───────────┬───────────┘
//!                    │
//!                    v
//!            ┌──────────────┐
//!            │  SFGModel    │
//!            │   (Enum)     │
//!            └──────────────┘
//! ```
//!
//! ## Usage Examples
//!
//! ### Basic Linear Regression Model
//! ```rust,ignore
//! use haze_library::ml::models::AISuperTrendLinReg;
//! use ndarray::{Array1, Array2};
//!
//! // Prepare training data
//! let features = Array2::from_shape_vec(
//!     (5, 2),
//!     vec![1.0, 2.0, 2.0, 4.0, 3.0, 6.0, 4.0, 8.0, 5.0, 10.0],
//! ).unwrap();
//! let targets = Array1::from_vec(vec![3.0, 6.0, 9.0, 12.0, 15.0]);
//!
//! // Train model
//! let mut model = AISuperTrendLinReg::new();
//! model.train(&features, &targets).expect("Training failed");
//!
//! // Make predictions
//! let test_features = Array2::from_shape_vec(
//!     (2, 2),
//!     vec![6.0, 12.0, 7.0, 14.0],
//! ).unwrap();
//! let predictions = model.predict(&test_features);
//! println!("Predictions: {:?}", predictions);
//! ```
//!
//! ### AI SuperTrend with Adaptive Bias
//! ```rust,ignore
//! use haze_library::ml::models::{AISuperTrendLinReg, Predictor};
//! use ndarray::{Array1, Array2, stack, Axis};
//!
//! // Feature engineering: price momentum + volatility
//! let close = vec![100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0];
//! let atr = vec![2.0, 2.1, 2.0, 2.2, 2.3, 2.1, 2.2, 2.4];
//!
//! let mut features_vec = vec![];
//! let mut targets_vec = vec![];
//!
//! for i in 1..close.len()-1 {
//!     // Features: [momentum, volatility]
//!     let momentum = close[i] - close[i-1];
//!     features_vec.push(vec![momentum, atr[i]]);
//!
//!     // Target: next price change direction
//!     targets_vec.push(close[i+1] - close[i]);
//! }
//!
//! let features = Array2::from_shape_vec(
//!     (features_vec.len(), 2),
//!     features_vec.into_iter().flatten().collect(),
//! ).unwrap();
//! let targets = Array1::from_vec(targets_vec);
//!
//! // Train model
//! let mut model = AISuperTrendLinReg::new();
//! model.train(&features, &targets)?;
//!
//! // Predict bias for current bar
//! let current_momentum = close.last().unwrap() - close[close.len()-2];
//! let current_atr = atr.last().unwrap();
//! let current_features = Array2::from_shape_vec(
//!     (1, 2),
//!     vec![current_momentum, *current_atr],
//! ).unwrap();
//!
//! let predicted_bias = model.predict(&current_features)[0];
//! println!("Predicted trend bias: {:.3}", predicted_bias);
//! ```
//!
//! ### Polymorphic Model Usage with SFGModel
//! ```rust,ignore
//! use haze_library::ml::models::{SFGModel, SFGModelConfig, ModelType};
//!
//! // Create model from configuration
//! let config = SFGModelConfig {
//!     model_type: ModelType::Ridge,
//!     ridge_alpha: 1.0,
//!     use_polynomial: false,
//!     polynomial_degree: 2,
//! };
//!
//! let mut model = SFGModel::from_config(&config);
//!
//! // Train (same interface regardless of model type)
//! model.train(&features, &targets)?;
//!
//! // Predict (polymorphic dispatch)
//! let predictions = model.predict(&test_features);
//! assert_eq!(predictions.len(), test_features.nrows());
//! ```
//!
//! ### Model Selection and Backtesting
//! ```rust,ignore
//! use haze_library::ml::models::{ModelType, SFGModel, SFGModelConfig};
//!
//! let model_types = vec![
//!     ModelType::LinearRegression,
//!     ModelType::Ridge,
//!     ModelType::SVR,  // Falls back to LinReg currently
//! ];
//!
//! let mut best_model = None;
//! let mut best_score = f64::NEG_INFINITY;
//!
//! for model_type in model_types {
//!     let config = SFGModelConfig {
//!         model_type,
//!         ..Default::default()
//!     };
//!
//!     let mut model = SFGModel::from_config(&config);
//!     model.train(&train_features, &train_targets)?;
//!
//!     // Calculate validation score (e.g., negative MSE)
//!     let predictions = model.predict(&val_features);
//!     let mse: f64 = val_targets.iter()
//!         .zip(predictions.iter())
//!         .map(|(y, pred)| (y - pred).powi(2))
//!         .sum::<f64>() / val_targets.len() as f64;
//!     let score = -mse;
//!
//!     if score > best_score {
//!         best_score = score;
//!         best_model = Some(model);
//!     }
//! }
//!
//! println!("Best model MSE: {:.4}", -best_score);
//! ```
//!
//! ## Performance Characteristics
//!
//! ### Training Complexity
//! - **Linear Regression**: O(n * p²) where n = samples, p = features
//! - **Ridge Regression**: O(n * p²) (same as linear, regularization is penalty term)
//! - **Typical training time**: <1ms for n=1000, p=10 on modern CPU
//!
//! ### Prediction Complexity
//! - **All models**: O(p) per sample (matrix-vector multiplication)
//! - **Batch prediction**: O(n * p) for n samples
//! - **Typical latency**: <1 microsecond per prediction
//!
//! ### Memory Footprint
//! - **Model storage**: O(p) for coefficients + intercept
//! - **Training workspace**: O(n * p) for feature matrix
//! - **Minimal overhead**: ~few KB per trained model
//!
//! ## Design Philosophy (SOLID Principles)
//!
//! ### Single Responsibility Principle (SRP)
//! - Each model class focuses on one algorithm implementation
//! - Training logic separated from prediction logic
//! - Feature engineering done outside model classes
//!
//! ### Open/Closed Principle (OCP)
//! - New models added by implementing `Predictor` trait (no modification)
//! - `SFGModel` enum extended without changing existing code
//!
//! ### Liskov Substitution Principle (LSP)
//! - All `Predictor` implementations interchangeable
//! - Consistent error handling across model types
//!
//! ### Interface Segregation Principle (ISP)
//! - `Predictor` trait minimal: only `predict` and `is_trained`
//! - Training methods on concrete types (not in trait)
//!
//! ### Dependency Inversion Principle (DIP)
//! - High-level indicator code depends on `Predictor` trait
//! - Concrete models injected at runtime via `SFGModel::from_config`
//!
//! ## Error Handling
//!
//! Training functions return `Result<(), String>` with descriptive errors:
//! - `"Features and targets length mismatch"` - Dimension mismatch
//! - `"Empty training data"` - Zero samples provided
//! - `"Linear regression training failed: <details>"` - Linfa library errors
//!
//! Prediction never panics:
//! - Untrained models return zero predictions
//! - Invalid feature dimensions handled gracefully
//!
//! ## Integration with Indicators
//!
//! ML models are used in:
//! - **AI SuperTrend** (`indicators::sfg`): Adaptive trend bias
//! - **ATR2** (`indicators::sfg_utils`): Dynamic threshold optimization
//! - **Momentum SFG**: Non-linear momentum pattern detection
//!
//! ## Future Extensions
//!
//! Planned model additions (following OCP):
//! - Polynomial regression (for non-linear trends)
//! - Support Vector Regression (true SVR, not fallback)
//! - Gradient boosting (XGBoost integration)
//! - Neural networks (lightweight PyTorch bindings)
//!
//! ## Related Modules
//!
//! - [`crate::ml::features`] - Feature engineering utilities
//! - [`crate::ml::trainer`] - Training pipeline and cross-validation
//! - [`crate::ml::manager`] - Model lifecycle and persistence
//! - [`crate::indicators::sfg`] - SFG indicator implementations using ML
//! - External: `linfa`, `linfa-linear`, `ndarray` crates
```

## Implementation Notes

- **Current State**: Minimal documentation (dead code allowances only)
- **Improvements**: Complete module overview, SOLID principles explanation, usage examples
- **Coverage Impact**: Adds ~250 lines of comprehensive ML documentation
- **Special focus**: Architecture diagram, polymorphism patterns, backtesting workflow
