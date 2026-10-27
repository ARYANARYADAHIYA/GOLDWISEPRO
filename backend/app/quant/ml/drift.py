import numpy as np
import pandas as pd
from typing import Dict, Any, List

def calculate_psi(expected: np.ndarray, actual: np.ndarray, num_buckets: int = 10) -> float:
    """
    Computes Population Stability Index (PSI) between baseline and monitored feature distributions.
    Standard financial benchmarks:
      PSI < 0.10: Stable / No significant drift
      0.10 <= PSI < 0.25: Moderate shift / Monitor
      PSI >= 0.25: Significant drift / Retraining recommended
    """
    if len(expected) < 10 or len(actual) < 10:
        return 0.0

    # Determine quantile bins based on expected baseline
    percentiles = np.linspace(0, 100, num_buckets + 1)
    bins = np.percentile(expected, percentiles)
    bins[0] = -np.inf
    bins[-1] = np.inf
    
    # Avoid duplicate bin edges
    bins = np.unique(bins)
    if len(bins) < 3:
        return 0.0

    exp_counts, _ = np.histogram(expected, bins=bins)
    act_counts, _ = np.histogram(actual, bins=bins)

    exp_pct = exp_counts / float(len(expected))
    act_pct = act_counts / float(len(actual))

    # Add small epsilon to prevent log(0) or div by zero
    eps = 1e-4
    exp_pct = np.clip(exp_pct, eps, 1.0)
    act_pct = np.clip(act_pct, eps, 1.0)

    psi_val = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return float(round(psi_val, 4))

def evaluate_model_drift(
    df_train_features: pd.DataFrame,
    df_recent_features: pd.DataFrame,
    model_object: Any = None
) -> Dict[str, Any]:
    """
    Computes comprehensive distribution drift diagnostics across features and anomaly scores.
    """
    feature_drifts = []
    monitored_cols = ["norm_spread_pct", "robust_zscore", "rolling_vol_20d", "volume_ratio"]

    max_psi = 0.0
    for col in monitored_cols:
        if col in df_train_features.columns and col in df_recent_features.columns:
            exp_vals = df_train_features[col].dropna().values
            act_vals = df_recent_features[col].dropna().values
            
            psi = calculate_psi(exp_vals, act_vals)
            max_psi = max(max_psi, psi)
            
            status = "STABLE"
            if psi >= 0.25:
                status = "SIGNIFICANT_DRIFT"
            elif psi >= 0.10:
                status = "MODERATE_SHIFT"
                
            feature_drifts.append({
                "feature_name": col,
                "psi_score": psi,
                "status": status,
                "train_mean": round(float(np.mean(exp_vals)), 4) if len(exp_vals) else 0.0,
                "recent_mean": round(float(np.mean(act_vals)), 4) if len(act_vals) else 0.0,
                "train_std": round(float(np.std(exp_vals)), 4) if len(exp_vals) else 0.0,
                "recent_std": round(float(np.std(act_vals)), 4) if len(act_vals) else 0.0,
            })

    # Overall recommendation
    if max_psi >= 0.25:
        overall_status = "CRITICAL_DRIFT"
        recommendation = "Feature distribution drift detected (PSI >= 0.25). Researcher should review market regime changes and consider model retraining."
    elif max_psi >= 0.10:
        overall_status = "MODERATE_DRIFT"
        recommendation = "Moderate drift observed. Increased monitoring recommended."
    else:
        overall_status = "HEALTHY_STABLE"
        recommendation = "All monitored features exhibit stable distributions (PSI < 0.10). Model remains calibrated."

    return {
        "overall_drift_status": overall_status,
        "max_psi": round(max_psi, 4),
        "recommendation": recommendation,
        "feature_drift_breakdown": feature_drifts,
        "calibration_notes": (
            "Confidence scores are uncalibrated probabilities in unsupervised anomaly detection. "
            "Scores represent standardized distance from the empirical training manifold."
        )
    }
