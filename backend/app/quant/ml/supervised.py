import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, Tuple, Optional

class SupervisedOutcomeModel:
    """
    Model C: Supervised Outcome Model (conditional implementation).
    Strictly enforces minimum sample and label validity requirements.
    Refuses to fabricate labels when empirical ground truth is missing.
    """
    def __init__(self, c_param: float = 1.0, min_required_samples: int = 30):
        self.c_param = c_param
        self.min_required_samples = min_required_samples
        self.scaler = StandardScaler()
        self.model = LogisticRegression(C=c_param, class_weight="balanced", random_state=42)
        self.is_fitted = False
        self.validation_message = "Awaiting validated empirical trade labels."

    def validate_dataset_eligibility(self, X: np.ndarray, y: Optional[np.ndarray]) -> Tuple[bool, str]:
        if y is None or len(y) == 0:
            return False, "Labels are not available. Supervised model cannot be trained without empirical forward outcomes."
        if len(y) < self.min_required_samples:
            return False, f"Insufficient sample size: {len(y)} < minimum {self.min_required_samples} required observations."
        unique_classes = np.unique(y)
        if len(unique_classes) < 2:
            return False, f"Degenerate label distribution: Only class {unique_classes[0]} present. Supervised classification requires both classes."
        counts = [np.sum(y == c) for c in unique_classes]
        if min(counts) < 5:
            return False, f"Severe label imbalance: Minor class has only {min(counts)} examples (minimum 5 required)."
        return True, "Eligible for supervised training."

    def fit(self, X: np.ndarray, y: Optional[np.ndarray]):
        is_eligible, reason = self.validate_dataset_eligibility(X, y)
        if not is_eligible:
            self.validation_message = reason
            self.is_fitted = False
            raise ValueError(f"Supervised model validation halted: {reason}")
            
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        self.validation_message = "Model successfully trained on empirical forward outcome labels."
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Validation message: " + self.validation_message)
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Validation message: " + self.validation_message)
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
