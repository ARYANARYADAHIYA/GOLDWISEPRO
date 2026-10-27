import pandas as pd
import numpy as np
from typing import Tuple, List

FEATURE_NAMES = [
    "norm_spread_pct",
    "robust_zscore",
    "spread_change_1d",
    "spread_change_5d",
    "rolling_vol_20d",
    "volume_ratio",
    "expiry_proximity_ratio",
    "spread_acceleration",
    "daily_return_a",
    "daily_return_b",
    "volume_change_1d_a",
    "volume_change_1d_b",
    "rolling_price_dev_20d"
]

def engineer_timestamp_safe_features(df_aligned: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs timestamp-safe features for ML models.
    STRICT ZERO LOOKAHEAD GUARANTEE:
    Every feature at index t uses only values from index <= t.

    Features implemented:
    - Daily returns (daily_return_a, daily_return_b)
    - Rolling volatility (rolling_vol_20d)
    - Volume changes (volume_change_1d_a, volume_change_1d_b, volume_ratio)
    - Rolling price deviations (rolling_price_dev_20d, robust_zscore)
    - Valid normalized relative-value features (norm_spread_pct, spread_change_1d, spread_change_5d, spread_acceleration)
    """
    df = df_aligned.copy().sort_values("timestamp").reset_index(drop=True)
    
    # 1. Normalized percentage spread
    df["norm_spread_pct"] = df["percentage_spread"].fillna(0.0)
    
    # 2. Robust z-score
    df["robust_zscore"] = df["robust_zscore"].fillna(0.0)
    
    # 3. 1-day change in percentage spread
    df["spread_change_1d"] = df["norm_spread_pct"].diff(1).fillna(0.0)
    
    # 4. 5-day rate of change
    df["spread_change_5d"] = df["norm_spread_pct"].diff(5).fillna(0.0)
    
    # 5. Rolling volatility (std of spread changes)
    df["rolling_vol_20d"] = df["spread_change_1d"].rolling(20, min_periods=5).std().fillna(0.0)
    
    # 6. Volume ratio
    vol_a = np.log1p(df["volume_a"].fillna(100.0).clip(lower=1.0))
    vol_b = np.log1p(df["volume_b"].fillna(100.0).clip(lower=1.0))
    df["volume_ratio"] = (vol_a / (vol_b + 1e-4)).fillna(1.0)
    
    # 7. Expiry proximity ratio (bounded 0 to 1)
    if "expiry_distance_days" in df.columns:
        df["expiry_proximity_ratio"] = (df["expiry_distance_days"].clip(0, 30) / 30.0).fillna(1.0)
    else:
        df["expiry_proximity_ratio"] = 1.0
        
    # 8. Spread acceleration
    rolling_5d_mean_change = df["spread_change_1d"].rolling(5, min_periods=2).mean().fillna(0.0)
    df["spread_acceleration"] = (df["spread_change_1d"] - rolling_5d_mean_change).fillna(0.0)

    # 9 & 10. Daily returns
    price_a = df["price_a"] if "price_a" in df.columns else df["normalized_a"]
    price_b = df["price_b"] if "price_b" in df.columns else df["normalized_b"]
    df["daily_return_a"] = price_a.pct_change(1).fillna(0.0)
    df["daily_return_b"] = price_b.pct_change(1).fillna(0.0)

    # 11 & 12. Volume changes
    raw_vol_a = df["volume_a"].fillna(100.0)
    raw_vol_b = df["volume_b"].fillna(100.0)
    df["volume_change_1d_a"] = raw_vol_a.pct_change(1).replace([np.inf, -np.inf], 0.0).fillna(0.0).clip(-5.0, 5.0)
    df["volume_change_1d_b"] = raw_vol_b.pct_change(1).replace([np.inf, -np.inf], 0.0).fillna(0.0).clip(-5.0, 5.0)

    # 13. Rolling price deviation from 20-day mean
    rolling_20_mean_spread = df["norm_spread_pct"].rolling(20, min_periods=5).mean().fillna(df["norm_spread_pct"])
    df["rolling_price_dev_20d"] = (df["norm_spread_pct"] - rolling_20_mean_spread).fillna(0.0)
    
    return df

def get_feature_matrix(df_features: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    """
    Extracts purely numeric feature matrix X without any identifiers or targets.
    """
    X = df_features[FEATURE_NAMES].to_numpy(dtype=np.float64)
    # Replace any potential NaNs or infs safely
    X = np.nan_to_num(X, nan=0.0, posinf=1.0, neginf=-1.0)
    return X, FEATURE_NAMES
