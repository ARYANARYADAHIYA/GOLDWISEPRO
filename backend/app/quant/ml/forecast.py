import math
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
from sklearn.linear_model import Ridge, HuberRegressor
from sklearn.preprocessing import StandardScaler

class GoldPriceForecaster:
    """
    GoldWise Pro Institutional Price Forecasting Engine.
    Strictly implements:
    1. Zero lookahead guarantee with lagged features
    2. Strict chronological holdout validation
    3. Benchmark comparison against persistent/naive baseline (y_{t+1} = y_t)
    4. Genuine empirical metrics: MAE, RMSE, Directional Accuracy (Hit Rate)
    5. INSUFFICIENT_DATA enforcement when observation count < 30
    """
    def __init__(self, min_observations: int = 30, alpha: float = 1.0):
        self.min_observations = min_observations
        self.alpha = alpha
        self.scaler = StandardScaler()
        self.model = Ridge(alpha=alpha, random_state=42)
        self.is_fitted = False
        self.feature_names = [
            "return_lag_1d",
            "return_lag_2d",
            "return_lag_3d",
            "return_lag_5d",
            "rolling_vol_10d",
            "rolling_vol_20d",
            "norm_spread_pct",
            "robust_zscore"
        ]

    def build_lagged_features(self, df_aligned: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
        """
        Builds lagged feature matrix and forward target y = return_{t+1}.
        Strictly prevents lookahead: target is shifted backward (-1) relative to features.
        """
        if len(df_aligned) < self.min_observations:
            return pd.DataFrame(), f"INSUFFICIENT_DATA: {len(df_aligned)} observations available, minimum {self.min_observations} required."

        df = df_aligned.copy().sort_values("timestamp").reset_index(drop=True)
        price_col = "normalized_a" if "normalized_a" in df.columns else ("price_a" if "price_a" in df.columns else "close_price")
        
        # Base daily returns
        df["ret_1d"] = df[price_col].pct_change(1).fillna(0.0)

        # Lagged features
        df["return_lag_1d"] = df["ret_1d"].shift(0).fillna(0.0)
        df["return_lag_2d"] = df["ret_1d"].shift(1).fillna(0.0)
        df["return_lag_3d"] = df["ret_1d"].shift(2).fillna(0.0)
        df["return_lag_5d"] = df["ret_1d"].rolling(5, min_periods=2).mean().shift(0).fillna(0.0)
        df["rolling_vol_10d"] = df["ret_1d"].rolling(10, min_periods=3).std().shift(0).fillna(0.0)
        df["rolling_vol_20d"] = df["ret_1d"].rolling(20, min_periods=5).std().shift(0).fillna(0.0)
        df["norm_spread_pct"] = df.get("percentage_spread", pd.Series(0.0, index=df.index)).fillna(0.0)
        df["robust_zscore"] = df.get("robust_zscore", pd.Series(0.0, index=df.index)).fillna(0.0)

        # Target: Forward 1-day return (next session return)
        df["target_return_fwd1d"] = df["ret_1d"].shift(-1)
        df["target_price_fwd1d"] = df[price_col].shift(-1)
        df["current_price"] = df[price_col]

        # Drop the last row because forward target is unknown
        df_clean = df.dropna(subset=["target_return_fwd1d", "target_price_fwd1d"]).reset_index(drop=True)
        return df_clean, "SUCCESS"

    def train_and_evaluate(
        self,
        df_aligned: pd.DataFrame,
        train_pct: float = 0.70,
        val_pct: float = 0.15
    ) -> Dict[str, Any]:
        """
        Executes chronological validation and baseline benchmarking.
        """
        df_data, status_msg = self.build_lagged_features(df_aligned)
        if df_data.empty:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": status_msg,
                "is_fitted": False,
                "metrics": {}
            }

        n = len(df_data)
        train_end = int(n * train_pct)
        val_end = int(n * (train_pct + val_pct))

        df_train = df_data.iloc[:train_end].copy()
        df_val = df_data.iloc[train_end:val_end].copy()
        df_test = df_data.iloc[val_end:].copy()

        if len(df_train) < 15 or len(df_test) < 5:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"INSUFFICIENT_DATA: Train set has {len(df_train)} rows and Test set has {len(df_test)} rows.",
                "is_fitted": False,
                "metrics": {}
            }

        X_train = df_train[self.feature_names].to_numpy(dtype=np.float64)
        y_train = df_train["target_return_fwd1d"].to_numpy(dtype=np.float64)

        X_test = df_test[self.feature_names].to_numpy(dtype=np.float64)
        y_test = df_test["target_return_fwd1d"].to_numpy(dtype=np.float64)
        price_current_test = df_test["current_price"].to_numpy(dtype=np.float64)
        price_target_test = df_test["target_price_fwd1d"].to_numpy(dtype=np.float64)

        # Scale features using training slice only
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Fit model
        self.model.fit(X_train_scaled, y_train)
        self.is_fitted = True

        # Candidate predictions on test slice
        pred_return_test = self.model.predict(X_test_scaled)
        pred_price_test = price_current_test * (1.0 + pred_return_test)

        # Baseline: Naive persistence (predict return = 0, price = current)
        baseline_pred_return = np.zeros_like(y_test)
        baseline_pred_price = price_current_test

        # Candidate metrics
        cand_mae_ret = float(np.mean(np.abs(pred_return_test - y_test)))
        cand_rmse_ret = float(np.sqrt(np.mean((pred_return_test - y_test) ** 2)))
        cand_mae_price = float(np.mean(np.abs(pred_price_test - price_target_test)))
        cand_rmse_price = float(np.sqrt(np.mean((pred_price_test - price_target_test) ** 2)))

        # Baseline metrics
        base_mae_ret = float(np.mean(np.abs(baseline_pred_return - y_test)))
        base_rmse_ret = float(np.sqrt(np.mean((baseline_pred_return - y_test) ** 2)))
        base_mae_price = float(np.mean(np.abs(baseline_pred_price - price_target_test)))
        base_rmse_price = float(np.sqrt(np.mean((baseline_pred_price - price_target_test) ** 2)))

        # Directional accuracy (Hit rate %)
        # Compare sign of predicted return vs sign of actual return
        valid_dir = np.sign(pred_return_test) == np.sign(y_test)
        directional_accuracy_pct = float(np.mean(valid_dir)) * 100.0

        # Feature importance (normalized absolute regression coefficients)
        coefs = np.abs(self.model.coef_)
        total_coef = np.sum(coefs) or 1.0
        feature_importance = {name: round(float(c / total_coef) * 100.0, 2) for name, c in zip(self.feature_names, coefs)}

        # Build test series for chart visualization
        series = []
        for i in range(len(df_test)):
            row = df_test.iloc[i]
            series.append({
                "timestamp": str(row["timestamp"]),
                "actual_price": round(float(price_target_test[i]), 2),
                "predicted_price": round(float(pred_price_test[i]), 2),
                "baseline_price": round(float(base_pred_price := baseline_pred_price[i]), 2),
                "actual_return_bps": round(float(y_test[i] * 10000.0), 1),
                "predicted_return_bps": round(float(pred_return_test[i] * 10000.0), 1),
            })

        return {
            "status": "TRAINED",
            "message": "Chronological holdout validation completed successfully.",
            "is_fitted": True,
            "sample_counts": {
                "total_observations": n,
                "train_count": len(df_train),
                "val_count": len(df_val),
                "test_count": len(df_test)
            },
            "metrics": {
                "candidate": {
                    "mae_price_inr_per_g": round(cand_mae_price, 3),
                    "rmse_price_inr_per_g": round(cand_rmse_price, 3),
                    "mae_return_bps": round(cand_mae_ret * 10000.0, 2),
                    "rmse_return_bps": round(cand_rmse_ret * 10000.0, 2),
                    "directional_accuracy_pct": round(directional_accuracy_pct, 2)
                },
                "baseline": {
                    "mae_price_inr_per_g": round(base_mae_price, 3),
                    "rmse_price_inr_per_g": round(base_rmse_price, 3),
                    "mae_return_bps": round(base_mae_ret * 10000.0, 2),
                    "rmse_return_bps": round(base_rmse_ret * 10000.0, 2),
                },
                "edge": {
                    "mae_improvement_pct": round(((base_mae_price - cand_mae_price) / (base_mae_price + 1e-6)) * 100.0, 2),
                    "rmse_improvement_pct": round(((base_rmse_price - cand_rmse_price) / (base_rmse_price + 1e-6)) * 100.0, 2)
                }
            },
            "feature_importance": feature_importance,
            "test_series": series[-60:]  # Most recent 60 holdout observations for charting
        }
