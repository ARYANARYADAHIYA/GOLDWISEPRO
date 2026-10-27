# GoldWise Pro — Model Card & Machine Learning Specifications

This document outlines the machine learning architecture, validation boundaries, evaluation metrics, and operational limitations for the models implemented in **GoldWise Pro**.

---

## 1. Model Overview

GoldWise Pro deploys a tri-tier machine learning hierarchy:

| Model ID | Model Name | Learning Paradigm | Primary Objective |
|---|---|---|---|
| **`BASELINE`** | Robust Statistical Anchor | Non-parametric / Rule-based | Provides zero-parameter explainable benchmark using rolling MAD z-scores. |
| **`ISOLATION_FOREST`** | Unsupervised Subspace Outlier | Ensemble Tree Isolation | Isolates multi-dimensional anomalous basis deviations without label bias. |
| **`SUPERVISED`** | Mean-Reversion Outcome Classifier | Regularized Logistic / Random Forest | Predicts probability that an observed spread will converge profitably after costs within $H$ days. |
| **`FORECASTER_RIDGE`** | Quantitative Return Forecaster | L2-Regularized Lagged Ridge | Benchmarks short-term normalized gold returns against naive persistence ($y_{t+1}=y_t$) under strict chronological holdouts. |

---

## 2. Feature Vectors (Timestamp-Safe)

All features are calculated using historical data strictly prior to or at time $t$:

| Feature Name | Type | Description | Lookback Window |
|---|---|---|---|
| `percentage_spread` | `float` | Relative spread $(P_A - P_B) / P_B$ | Instantaneous |
| `spread_rolling_mean_20` | `float` | 20-day rolling mean of spread | 20 bars |
| `spread_rolling_std_20` | `float` | 20-day rolling volatility of spread | 20 bars |
| `spread_rolling_median_20`| `float` | 20-day rolling median of spread | 20 bars |
| `spread_rolling_mad_20` | `float` | 20-day rolling MAD of spread | 20 bars |
| `robust_zscore_20` | `float` | Robust z-score via Median Absolute Deviation | 20 bars |
| `volume_ratio_a` | `float` | Volume of Leg A / 20-day moving average volume | 20 bars |
| `volume_ratio_b` | `float` | Volume of Leg B / 20-day moving average volume | 20 bars |
| `open_interest_ratio_a` | `float` | OI of Leg A / 20-day moving average OI | 20 bars |
| `open_interest_ratio_b` | `float` | OI of Leg B / 20-day moving average OI | 20 bars |
| `days_to_expiry_a` | `int` | Trading calendar days until Leg A expiry | Instantaneous |
| `days_to_expiry_b` | `int` | Trading calendar days until Leg B expiry | Instantaneous |
| `expiry_distance_delta`| `int` | Difference in calendar days between contract expiries | Instantaneous |

---

## 3. Training & Validation Protocol

- **Validation Split**: Chronological walk-forward split (70% in-sample training, 30% out-of-sample testing). Random k-fold cross validation is strictly disallowed to prevent temporal leakage.
- **Artifact Serialization**: Trained models and preprocessing scalers are bundled into versioned `.joblib` pipelines stored in the configured artifacts directory.
- **Reproducibility**: Random seeds are fixed (`random_state=42`) across all stochastic algorithms.

---

## 4. Evaluation & Drift Monitoring

### 4.1 Performance Metrics
- **Anomaly Detection Precision & Recall**: Precision evaluated on verified profitable post-cost reversions.
- **Brier Score**: Evaluates probability calibration for the supervised outcome classifier:
  $$\text{Brier} = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$$
- **Tournament Scoring**: Automated ranking balancing precision, false positive suppression rate, and operational stability.

### 4.2 Population Stability Index (PSI)
Data drift between baseline training distribution $B$ and operational inference distribution $T$ is tracked via the Population Stability Index:

$$\text{PSI} = \sum_{k=1}^K \left( T_k - B_k \right) \times \ln\left( \frac{T_k}{B_k} \right)$$

- **$\text{PSI} < 0.10$**: Stable distribution; no model retraining required.
- **$0.10 \le \text{PSI} \le 0.25$**: Moderate shift; retraining recommended.
- **$\text{PSI} > 0.25$**: Significant distributional shift; automated alert triggered, suppressing autonomous model execution.

---

## 5. Quantitative Limitations & Out-of-Scope Usage

1. **Not a High-Frequency Trading (HFT) Model**: GoldWise Pro evaluates daily and swing relative-value spreads and return horizons. It does not model sub-millisecond microstructure order queues.
2. **Empirical Return Forecasting Guardrails**: Directional price forecasting (`FORECASTER_RIDGE`) is evaluated strictly against a naive persistence baseline ($y_{t+1}=y_t$). It is intended as an analytical baseline for regime detection and basis carry drift, rather than unhedged speculative trading.
3. **Physical Settlement Risk**: Trades held into the physical tender period are subject to delivery obligations under MCX bye-laws. Models and scanners are tuned to suppress signals inside this window.
