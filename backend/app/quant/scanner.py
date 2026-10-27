import uuid
import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from app.quant.contracts import get_contract_spec
from app.quant.spreads import compute_rolling_spread_stats
from app.quant.destroyer import OpportunityDestroyer
from app.quant.autopsy import generate_signal_autopsy

def run_relative_value_scan(
    df_observations: pd.DataFrame,
    symbol_a: str = "GOLDM",
    symbol_b: str = "GOLD",
    zscore_threshold: float = 2.0,
    percentile_lower: float = 2.5,
    percentile_upper: float = 97.5,
    rolling_window_days: int = 20,
    min_observations: int = 15,
    slippage_bps: float = 3.0,
    brokerage_bps: float = 1.5,
    exchange_fees_bps: float = 1.0,
    expiry_buffer_days: int = 3
) -> Dict[str, Any]:
    """
    Executes an end-to-end relative value scan across aligned contract pair observations.
    Strictly past-looking; no lookahead.
    """
    # Filter observations for symbol_a and symbol_b
    df_a = df_observations[df_observations["symbol"] == symbol_a].copy()
    df_b = df_observations[df_observations["symbol"] == symbol_b].copy()

    if "normalized" not in df_a.columns and "normalized_price_pure_gram" in df_a.columns:
        df_a["normalized"] = df_a["normalized_price_pure_gram"]
    if "normalized" not in df_b.columns and "normalized_price_pure_gram" in df_b.columns:
        df_b["normalized"] = df_b["normalized_price_pure_gram"]

    if df_a.empty or df_b.empty:
        return {
            "scan_id": str(uuid.uuid4()),
            "total_candidates": 0,
            "investigate_count": 0,
            "suppressed_count": 0,
            "insufficient_count": 0,
            "candidates": []
        }

    # Align by date
    merged = pd.merge(
        df_a,
        df_b,
        on="timestamp",
        suffixes=("_a", "_b")
    ).sort_values("timestamp").reset_index(drop=True)

    if merged.empty:
        return {
            "scan_id": str(uuid.uuid4()),
            "total_candidates": 0,
            "investigate_count": 0,
            "suppressed_count": 0,
            "insufficient_count": 0,
            "candidates": []
        }

    # Compute rolling spread statistics
    merged_stats = compute_rolling_spread_stats(merged, window=rolling_window_days)

    destroyer = OpportunityDestroyer(
        expiry_buffer_days=expiry_buffer_days,
        min_daily_volume=100.0,
        slippage_bps=slippage_bps,
        brokerage_bps=brokerage_bps,
        exchange_fees_bps=exchange_fees_bps
    )

    candidates: List[Dict[str, Any]] = []
    investigate_cnt = 0
    suppressed_cnt = 0
    insufficient_cnt = 0
    scan_id = str(uuid.uuid4())

    spec_a = get_contract_spec(symbol_a)
    spec_b = get_contract_spec(symbol_b)

    for idx, row in merged_stats.iterrows():
        # Calculate expiry distance in trading days
        try:
            curr_dt = datetime.datetime.strptime(row["timestamp"], "%Y-%m-%d").date()
            exp_dt = datetime.datetime.strptime(row["expiry_date_a"], "%Y-%m-%d").date()
            expiry_distance = max(0, (exp_dt - curr_dt).days)
        except Exception:
            expiry_distance = 30

        candidate_id = f"cand-{uuid.uuid4().hex[:10]}"
        
        # Prepare destroyer input
        candidate_input = {
            "price_a": float(row["close_price_a"]),
            "price_b": float(row["close_price_b"]),
            "normalized_a": float(row["normalized_a"]),
            "normalized_b": float(row["normalized_b"]),
            "raw_spread": float(row["raw_spread"]),
            "percentage_spread": float(row["percentage_spread"]),
            "robust_zscore": float(row["robust_zscore"]) if not pd.isna(row["robust_zscore"]) else 0.0,
            "percentile": float(row["percentile"]) if not pd.isna(row["percentile"]) else 50.0,
            "expiry_distance_days": expiry_distance,
            "volume_a": float(row.get("volume_a", 0.0) or 0.0),
            "volume_b": float(row.get("volume_b", 0.0) or 0.0),
            "symbol_a_purity": spec_a.purity_per_mille if spec_a else 995.0,
            "symbol_b_purity": spec_b.purity_per_mille if spec_b else 995.0,
            "historical_obs_count": idx + 1,
            "is_stale": (row.get("volume_a", 0) == 0 or row.get("volume_b", 0) == 0),
        }

        # Run Destroyer checks
        destroyer_res = destroyer.evaluate_candidate(candidate_input)
        verdict = destroyer_res["verdict"]

        if verdict == "INVESTIGATE":
            investigate_cnt += 1
        elif verdict == "SUPPRESSED":
            suppressed_cnt += 1
        else:
            insufficient_cnt += 1

        cand_dict = {
            "id": candidate_id,
            "scan_id": scan_id,
            "timestamp": str(row["timestamp"]),
            "symbol_a": symbol_a,
            "symbol_b": symbol_b,
            "expiry_a": str(row["expiry_date_a"]),
            "expiry_b": str(row["expiry_date_b"]),
            "price_a": float(row["close_price_a"]),
            "price_b": float(row["close_price_b"]),
            "normalized_a": round(float(row["normalized_a"]), 4),
            "normalized_b": round(float(row["normalized_b"]), 4),
            "raw_spread": round(float(row["raw_spread"]), 4),
            "percentage_spread": round(float(row["percentage_spread"]), 4),
            "rolling_mean": round(float(row["rolling_mean"]), 4) if not pd.isna(row["rolling_mean"]) else None,
            "rolling_std": round(float(row["rolling_std"]), 4) if not pd.isna(row["rolling_std"]) else None,
            "rolling_median": round(float(row["rolling_median"]), 4) if not pd.isna(row["rolling_median"]) else None,
            "rolling_mad": round(float(row["rolling_mad"]), 4) if not pd.isna(row["rolling_mad"]) else None,
            "robust_zscore": round(float(row["robust_zscore"]), 2) if not pd.isna(row["robust_zscore"]) else None,
            "percentile": round(float(row["percentile"]), 1) if not pd.isna(row["percentile"]) else None,
            "expiry_distance_days": expiry_distance,
            "volume_a": float(row.get("volume_a", 0.0) or 0.0),
            "volume_b": float(row.get("volume_b", 0.0) or 0.0),
            "verdict": verdict,
            "rejection_reasons": destroyer_res["fatal_failures"] + destroyer_res["caution_warnings"],
            "destroyer_checks": destroyer_res,
            "estimated_cost_bps": round(2.0 * (brokerage_bps + exchange_fees_bps + slippage_bps), 1)
        }

        # Generate autopsy breakdown
        autopsy_data = generate_signal_autopsy(cand_dict)
        cand_dict["autopsy_features"] = autopsy_data

        candidates.append(cand_dict)

    return {
        "scan_id": scan_id,
        "total_candidates": len(candidates),
        "investigate_count": investigate_cnt,
        "suppressed_count": suppressed_cnt,
        "insufficient_count": insufficient_cnt,
        "candidates": candidates
    }
