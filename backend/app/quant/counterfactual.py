from typing import Dict, Any, Optional, List
from app.quant.destroyer import OpportunityDestroyer

def run_counterfactual_simulation(
    original_candidate: Dict[str, Any],
    modified_slippage_bps: Optional[float] = None,
    modified_zscore_threshold: Optional[float] = None,
    modified_expiry_buffer_days: Optional[int] = None
) -> Dict[str, Any]:
    """
    Module M: Counterfactual Lab.
    Interactively perturbs key assumptions (costs, slippage, expiry thresholds, zscore bars)
    and evaluates whether the research verdict survives or flips.
    """
    original_verdict = original_candidate.get("verdict", "SUPPRESSED")
    robust_zscore = abs(original_candidate.get("robust_zscore", 0.0) or 0.0)
    pct_spread = abs(original_candidate.get("percentage_spread", 0.0) or 0.0)
    spread_bps = pct_spread * 100.0
    expiry_dist = original_candidate.get("expiry_distance_days", 30)

    # Effective parameters
    slip = modified_slippage_bps if modified_slippage_bps is not None else 3.0
    z_bar = modified_zscore_threshold if modified_zscore_threshold is not None else 2.0
    exp_buf = modified_expiry_buffer_days if modified_expiry_buffer_days is not None else 3

    # Instantiate destroyer with modified assumptions
    destroyer = OpportunityDestroyer(
        expiry_buffer_days=exp_buf,
        min_daily_volume=100.0,
        slippage_bps=slip,
        brokerage_bps=1.5,
        exchange_fees_bps=1.0
    )

    destroyer_input = {
        "price_a": original_candidate.get("price_a", 0.0),
        "price_b": original_candidate.get("price_b", 0.0),
        "normalized_a": original_candidate.get("normalized_a", 0.0),
        "normalized_b": original_candidate.get("normalized_b", 0.0),
        "raw_spread": original_candidate.get("raw_spread", 0.0),
        "percentage_spread": pct_spread,
        "robust_zscore": robust_zscore,
        "expiry_distance_days": expiry_dist,
        "volume_a": original_candidate.get("volume_a", 1000.0),
        "volume_b": original_candidate.get("volume_b", 1000.0),
        "historical_obs_count": 25,
    }

    result = destroyer.evaluate_candidate(destroyer_input)
    counter_verdict = result["verdict"]

    driver_factors: List[str] = []
    if modified_slippage_bps is not None:
        driver_factors.append(f"Slippage modified to {modified_slippage_bps} bps (Roundtrip friction: {round(destroyer.roundtrip_cost_bps, 1)} bps)")
    if modified_zscore_threshold is not None:
        driver_factors.append(f"Z-score threshold shifted from 2.0 to {modified_zscore_threshold}")
    if modified_expiry_buffer_days is not None:
        driver_factors.append(f"Expiry delivery buffer expanded from 3 to {modified_expiry_buffer_days} days")

    verdict_changed = (original_verdict != counter_verdict)
    
    if counter_verdict == "INVESTIGATE":
        assessment = "Candidate is robust. Withstands higher friction and tighter thresholds."
    elif original_verdict == "INVESTIGATE" and counter_verdict == "SUPPRESSED":
        assessment = "Candidate is fragile. Edge collapses under conservative execution or parameter assumptions."
    else:
        assessment = "Candidate remains suppressed under altered assumptions."

    return {
        "candidate_id": original_candidate.get("id", "UNKNOWN"),
        "original_verdict": original_verdict,
        "counterfactual_verdict": counter_verdict,
        "original_score": round(robust_zscore, 2),
        "counterfactual_score": round(robust_zscore / (z_bar / 2.0), 2),
        "verdict_changed": verdict_changed,
        "driver_factors": driver_factors,
        "robustness_assessment": assessment
    }
