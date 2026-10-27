import numpy as np
import pandas as pd
from typing import List, Dict, Any

def compute_rolling_spread_stats(
    df: pd.DataFrame,
    window: int = 20
) -> pd.DataFrame:
    """
    Computes rolling statistics on aligned pure-gold percentage spread.
    Strictly past-looking: rolling window ends at timestamp t (no future data leakage).
    """
    df = df.sort_values("timestamp").reset_index(drop=True)
    
    # Raw & percentage spreads
    df["raw_spread"] = df["normalized_a"] - df["normalized_b"]
    df["percentage_spread"] = (df["raw_spread"] / df["normalized_b"]) * 100.0
    
    # Rolling standard stats
    df["rolling_mean"] = df["percentage_spread"].rolling(window=window, min_periods=max(5, window // 3)).mean()
    df["rolling_std"] = df["percentage_spread"].rolling(window=window, min_periods=max(5, window // 3)).std()
    
    # Rolling Robust Median & MAD (Median Absolute Deviation)
    def calc_rolling_median_mad(series: pd.Series):
        medians = []
        mads = []
        robust_zscores = []
        percentiles = []
        
        vals = series.values
        n = len(vals)
        for i in range(n):
            start_idx = max(0, i - window + 1)
            window_slice = vals[start_idx : i + 1]
            # Remove any NaNs
            valid_slice = window_slice[~np.isnan(window_slice)]
            
            if len(valid_slice) < 5:
                medians.append(np.nan)
                mads.append(np.nan)
                robust_zscores.append(np.nan)
                percentiles.append(np.nan)
                continue
                
            med = float(np.median(valid_slice))
            abs_devs = np.abs(valid_slice - med)
            mad = float(np.median(abs_devs))
            medians.append(med)
            mads.append(mad)
            
            # Robust sigma = 1.4826 * MAD (asymptotically normal consistent estimator)
            robust_sigma = 1.4826 * mad
            current_val = vals[i]
            if robust_sigma > 1e-6:
                rz = (current_val - med) / robust_sigma
            else:
                rz = 0.0
            robust_zscores.append(float(rz))
            
            # Percentile rank within historical window (0 to 100)
            pct = float((np.sum(valid_slice <= current_val) / len(valid_slice)) * 100.0)
            percentiles.append(pct)
            
        return medians, mads, robust_zscores, percentiles

    meds, mads, rzscores, pcts = calc_rolling_median_mad(df["percentage_spread"])
    df["rolling_median"] = meds
    df["rolling_mad"] = mads
    df["robust_zscore"] = rzscores
    df["percentile"] = pcts
    
    return df
