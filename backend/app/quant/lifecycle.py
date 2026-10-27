import datetime
import pandas as pd
from typing import Dict, Any, List

def compute_contract_lifecycle(
    df_observations: pd.DataFrame
) -> Dict[str, Any]:
    """
    Module N: Contract Lifecycle Radar.
    Monitors days to expiry, roll calendars, liquidity proxies, and comparison eligibility.
    """
    if df_observations.empty:
        return {"contracts": [], "roll_schedule_summary": "No contract observations loaded."}

    contracts = []
    # Group by (symbol, expiry_date)
    grouped = df_observations.groupby(["symbol", "expiry_date"])
    
    # Reference date is max timestamp in dataset
    latest_ts = df_observations["timestamp"].max()
    curr_date = datetime.datetime.strptime(str(latest_ts), "%Y-%m-%d").date()

    for (sym, exp), grp in grouped:
        try:
            exp_date = datetime.datetime.strptime(str(exp), "%Y-%m-%d").date()
            days_to_expiry = (exp_date - curr_date).days
        except Exception:
            days_to_expiry = 30

        obs_count = len(grp)
        avg_vol = float(grp["volume"].mean()) if "volume" in grp.columns else 0.0

        # Warning levels
        if days_to_expiry <= 3:
            warning = "CRITICAL_DELIVERY_IMMINENT"
        elif days_to_expiry <= 10:
            warning = "CAUTION"
        else:
            warning = "NORMAL"

        is_liquid = avg_vol >= 100.0
        is_active_roll = (10 <= days_to_expiry <= 35) and is_liquid

        contracts.append({
            "symbol": str(sym),
            "expiry_date": str(exp),
            "days_to_expiry": max(0, days_to_expiry),
            "available_observations": obs_count,
            "data_coverage_pct": round(min(100.0, (obs_count / 120.0) * 100.0), 1),
            "average_daily_volume": round(avg_vol, 1),
            "is_liquid_enough": is_liquid,
            "is_active_roll": is_active_roll,
            "expiry_warning_level": warning
        })

    # Sort by days_to_expiry ascending
    contracts.sort(key=lambda x: x["days_to_expiry"])

    roll_summary = (
        f"Active evaluation reference date: {latest_ts}. "
        f"{len([c for c in contracts if c['expiry_warning_level'] == 'CRITICAL_DELIVERY_IMMINENT'])} contracts in critical delivery tender window. "
        "Roll transition recommended for contracts under 5 days to settlement."
    )

    return {
        "contracts": contracts,
        "roll_schedule_summary": roll_summary
    }
