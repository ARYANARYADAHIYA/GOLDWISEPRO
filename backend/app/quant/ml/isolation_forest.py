import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List

class IsolationForestAnomalyDetector:
    """
    Model B: Unsupervised Machine Learning Model using Scikit-Learn IsolationForest.
    Fitted strictly on chronological training data with standard scaling.
    """
    def __init__(self, contamination: float = 0.05, n_estimators: int = 100, random_state: int = 42):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: Any = None):
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Returns binary labels: 1 for anomaly, 0 for normal.
        (scikit-learn IsolationForest outputs -1 for anomaly and 1 for normal)
        """
        X_scaled = self.scaler.transform(X)
        preds = self.model.predict(X_scaled)
        return (preds == -1).astype(int)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Continuous anomaly score: higher score = more anomalous.
        In scikit-learn, score_samples is negative (lower = more abnormal).
        We invert and scale so higher values indicate greater anomaly.
        """
        X_scaled = self.scaler.transform(X)
        # raw score_samples is in (-inf, 0], e.g. -0.4 is normal, -0.7 is anomaly
        raw_scores = self.model.score_samples(X_scaled)
        # Invert: -raw_scores gives higher for abnormal
        return -raw_scores

    def compute_feature_importance(self, X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
        """
        Permutation-based feature importance for unsupervised anomaly detection.
        Measures the change in mean anomaly score when a feature column is shuffled.
        """
        if not self.is_fitted or len(X) < 5:
            return {name: 1.0 / len(feature_names) for name in feature_names}

        base_scores = self.decision_function(X)
        base_mean = float(np.mean(base_scores))
        
        importances = {}
        for col_idx, name in enumerate(feature_names):
            X_permuted = X.copy()
            # Shuffle the single column
            np.random.seed(42 + col_idx)
            X_permuted[:, col_idx] = np.random.permutation(X_permuted[:, col_idx])
            perm_scores = self.decision_function(X_permuted)
            impact = float(np.mean(np.abs(perm_scores - base_scores)))
            importances[name] = impact

        total = sum(importances.values()) or 1.0
        return {k: round(v / total * 100.0, 2) for k, v in importances.items()}
