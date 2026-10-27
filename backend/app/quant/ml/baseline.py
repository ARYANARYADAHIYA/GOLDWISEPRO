import numpy as np
from typing import Dict, Any

class StatisticalAnomalyBaseline:
    """
    Model A: Transparent, explainable statistical anomaly benchmark.
    Uses rolling median, median absolute deviation (MAD), and historical percentiles.
    """
    def __init__(self, zscore_threshold: float = 2.0, percentile_threshold: float = 2.5):
        self.zscore_threshold = zscore_threshold
        self.percentile_threshold = percentile_threshold
        self.is_fitted = False
        self.threshold_val = zscore_threshold

    def fit(self, X: np.ndarray, y: Any = None):
        # Statistical baseline parameterizes from empirical distribution of robust zscore (col 1)
        zscores = np.abs(X[:, 1])
        self.threshold_val = float(np.percentile(zscores, 95.0)) if len(zscores) > 10 else self.zscore_threshold
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        # Col 0: norm_spread_pct, Col 1: robust_zscore
        zscores = np.abs(X[:, 1])
        return (zscores >= self.zscore_threshold).astype(int)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        # Anomaly score: normalized zscore magnitude
        zscores = np.abs(X[:, 1])
        return zscores / (self.zscore_threshold + 1e-6)
