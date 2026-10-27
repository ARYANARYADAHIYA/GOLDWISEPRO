import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, List

def audit_dataset_integrity(df_observations: pd.DataFrame) -> Dict[str, Any]:
    """
    Module P: Data Integrity Guardian.
    Computes an auditable data-quality score (0-100) and detects stale prices,
    abnormal date gaps, OHLC inconsistencies, and corrupt numeric records.
    """
    if df_observations.empty:
        return {
            "overall_quality_score": 0.0,
            "status": "EMPTY_DATASET",
            "issues": [{"category": "Completeness", "description": "Dataset has zero observations"}],
            "quarantined_count": 0,
            "metrics": {}
        }

    issues: List[Dict[str, Any]] = []
    total_rows = len(df_observations)

    # 1. OHLC Physical Inconsistency (High < Low, or Close outside [Low, High])
    invalid_ohlc = df_observations[
        (df_observations["high_price"] < df_observations["low_price"]) |
        (df_observations["close_price"] > df_observations["high_price"] * 1.0001) |
        (df_observations["close_price"] < df_observations["low_price"] * 0.9999)
    ]
    invalid_ohlc_count = len(invalid_ohlc)
    if invalid_ohlc_count > 0:
        issues.append({
            "category": "Price Geometry",
            "severity": "HIGH",
            "description": f"{invalid_ohlc_count} observations violate OHLC physical geometry (High < Low or Close outside bounds).",
            "affected_rows": invalid_ohlc_count
        })

    # 2. Suspicious Pure Gold Outliers (Outside Rs 4,000 to Rs 15,000 per pure gram)
    norm_col = "normalized_price_pure_gram" if "normalized_price_pure_gram" in df_observations.columns else "normalized"
    price_outliers = df_observations[
        (df_observations[norm_col] < 4000.0) |
        (df_observations[norm_col] > 15000.0)
    ]
    outlier_count = len(price_outliers)
    if outlier_count > 0:
        issues.append({
            "category": "Economic Realism",
            "severity": "CRITICAL",
            "description": f"{outlier_count} observations exhibit pure-gold reference prices outside realistic historical boundaries (Rs 4,000 - 15,000/g).",
            "affected_rows": outlier_count
        })

    # 3. Stale Price Check (Consecutive identical prices with zero volume)
    stale_count = 0
    symbols = df_observations["symbol"].unique()
    for sym in symbols:
        sym_df = df_observations[df_observations["symbol"] == sym].sort_values("timestamp")
        price_diff = sym_df["close_price"].diff()
        vols = sym_df["volume"].fillna(0.0)
        # Stale: price didn't change AND volume was 0
        stale_mask = (price_diff == 0.0) & (vols == 0.0)
        stale_count += int(stale_mask.sum())

    if stale_count > 0:
        issues.append({
            "category": "Freshness & Liquidity",
            "severity": "MEDIUM",
            "description": f"{stale_count} observations appear stale (unchanged price with zero trading volume).",
            "affected_rows": stale_count
        })

    # 4. Unexpected Date Gaps (> 4 calendar days between consecutive observations)
    gap_count = 0
    for sym in symbols:
        sym_df = df_observations[df_observations["symbol"] == sym].sort_values("timestamp")
        dates = pd.to_datetime(sym_df["timestamp"])
        day_diffs = dates.diff().dt.days
        abnormal_gaps = (day_diffs > 4)
        gap_count += int(abnormal_gaps.sum())

    if gap_count > 0:
        issues.append({
            "category": "Continuity",
            "severity": "LOW",
            "description": f"{gap_count} unexpected trading date gaps exceeding 4 calendar days.",
            "affected_rows": gap_count
        })

    # Data Quality Score Formula (0 to 100):
    # Base: 100
    # Penalty: 30 * (outlier_pct) + 25 * (invalid_ohlc_pct) + 15 * (stale_pct) + 5 * (gap_pct)
    outlier_pct = outlier_count / float(total_rows)
    invalid_ohlc_pct = invalid_ohlc_count / float(total_rows)
    stale_pct = stale_count / float(total_rows)
    gap_pct = min(1.0, gap_count / 10.0)

    deductions = (40.0 * outlier_pct) + (30.0 * invalid_ohlc_pct) + (20.0 * stale_pct) + (10.0 * gap_pct)
    quality_score = max(0.0, min(100.0, 100.0 - deductions))

    if quality_score >= 90.0:
        status = "EXCELLENT_INTEGRITY"
    elif quality_score >= 75.0:
        status = "ACCEPTABLE_FOR_RESEARCH"
    elif quality_score >= 50.0:
        status = "CAUTION_DATA_QUALITY_WARNINGS"
    else:
        status = "COMPROMISED_QUARANTINE_RECOMMENDED"

    return {
        "overall_quality_score": round(quality_score, 1),
        "status": status,
        "total_observations_audited": total_rows,
        "issues": issues,
        "metrics": {
            "invalid_ohlc_count": invalid_ohlc_count,
            "price_outlier_count": outlier_count,
            "stale_price_count": stale_count,
            "unexpected_gaps_count": gap_count,
            "deductions_applied": round(deductions, 1)
        },
        "score_formula": "Score = 100 - (40*outlier_pct + 30*invalid_ohlc_pct + 20*stale_pct + 10*gap_pct)"
    }
