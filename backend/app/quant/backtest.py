import uuid
import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

from app.quant.spreads import compute_rolling_spread_stats

def run_walk_forward_backtest(
    df_observations: pd.DataFrame,
    symbol_a: str = "GOLDM",
    symbol_b: str = "GOLD",
    entry_zscore: float = 2.0,
    exit_zscore: float = 0.5,
    max_holding_days: int = 5,
    position_size_inr: float = 1_000_000.0,
    slippage_bps: float = 3.0,
    brokerage_bps: float = 1.5,
    exchange_fees_bps: float = 1.0,
    execution_delay_days: int = 1
) -> Dict[str, Any]:
    """
    Executes a walk-forward chronological backtest with zero lookahead bias.
    Execution delay enforces realistic order fill timing (T+1).
    Friction (statutory + brokerage + slippage) is deducted on every transaction.
    """
    df_a = df_observations[df_observations["symbol"] == symbol_a].copy()
    df_b = df_observations[df_observations["symbol"] == symbol_b].copy()

    if "normalized" not in df_a.columns and "normalized_price_pure_gram" in df_a.columns:
        df_a["normalized"] = df_a["normalized_price_pure_gram"]
    if "normalized" not in df_b.columns and "normalized_price_pure_gram" in df_b.columns:
        df_b["normalized"] = df_b["normalized_price_pure_gram"]

    if df_a.empty or df_b.empty:
        raise ValueError(f"Insufficient observations for backtest between {symbol_a} and {symbol_b}")

    merged = pd.merge(
        df_a, df_b, on="timestamp", suffixes=("_a", "_b")
    ).sort_values("timestamp").reset_index(drop=True)

    if len(merged) < 25:
        raise ValueError("At least 25 chronological observations required for a valid walk-forward backtest")

    merged = compute_rolling_spread_stats(merged, window=20)

    # Cost per single trade leg pair in basis points (entry + exit = 2 * leg_pair_cost)
    # Entry: 2 legs (Long/Short), Exit: 2 legs (Unwind). Total cost = 2 * (slippage + brokerage + fees) * 2
    roundtrip_friction_bps = 2.0 * 2.0 * (brokerage_bps + exchange_fees_bps + slippage_bps)
    roundtrip_friction_factor = roundtrip_friction_bps / 10000.0

    trades: List[Dict[str, Any]] = []
    equity = position_size_inr
    equity_curve = []
    
    in_position = False
    pos_direction = 0  # +1: Long A / Short B (when spread is depressed), -1: Short A / Long B (when spread is elevated)
    entry_idx = -1
    entry_spread = 0.0
    signal_date = ""
    signal_idx = -1
    holding_days = 0

    trade_id_seq = 1
    total_signals = 0

    n = len(merged)
    for i in range(n):
        row = merged.iloc[i]
        date_str = str(row["timestamp"])
        curr_z = row["robust_zscore"]
        curr_pct_spread = row["percentage_spread"]

        if pd.isna(curr_z):
            equity_curve.append({
                "date": date_str,
                "equity_inr": round(equity, 2),
                "in_position": in_position
            })
            continue

        # Signal check (if not in position)
        if not in_position:
            if curr_z >= entry_zscore:
                # Spread is abnormally high -> Short A, Long B (expect spread to narrow)
                total_signals += 1
                signal_idx = i
                signal_date = date_str
                pos_direction = -1
            elif curr_z <= -entry_zscore:
                # Spread is abnormally low -> Long A, Short B (expect spread to widen)
                total_signals += 1
                signal_idx = i
                signal_date = date_str
                pos_direction = 1

            # Check if execution delay requirement is satisfied
            if signal_idx != -1 and (i >= signal_idx + execution_delay_days):
                in_position = True
                entry_idx = i
                entry_spread = curr_pct_spread
                holding_days = 0
                signal_idx = -1  # Reset pending signal

        else:
            # We are currently in position
            holding_days += 1
            # Check exit conditions: mean-reversion or time-stop
            reverted = (pos_direction == -1 and curr_z <= exit_zscore) or (pos_direction == 1 and curr_z >= -exit_zscore)
            time_stopped = (holding_days >= max_holding_days)
            stop_loss = (abs(curr_z) >= 3.8) # Emergency stop if deviation widens to 3.8 sigma

            if reverted or time_stopped or stop_loss:
                # Calculate return
                spread_move_pct = curr_pct_spread - entry_spread
                # If short spread (direction -1), positive PnL when spread narrows (spread_move < 0)
                gross_return_fraction = -pos_direction * (spread_move_pct / 100.0)
                net_return_fraction = gross_return_fraction - roundtrip_friction_factor

                gross_pnl = position_size_inr * gross_return_fraction
                total_cost = position_size_inr * roundtrip_friction_factor
                net_pnl = gross_pnl - total_cost
                equity += net_pnl

                exit_reason = "MEAN_REVERSION" if reverted else ("TIME_STOP" if time_stopped else "STOP_LOSS")

                trades.append({
                    "trade_id": trade_id_seq,
                    "signal_date": signal_date,
                    "entry_date": str(merged.iloc[entry_idx]["timestamp"]),
                    "exit_date": date_str,
                    "symbol_a": symbol_a,
                    "symbol_b": symbol_b,
                    "spread_at_signal_bps": round(float(merged.iloc[entry_idx - execution_delay_days]["percentage_spread"]) * 100.0, 1),
                    "entry_spread_bps": round(entry_spread * 100.0, 1),
                    "exit_spread_bps": round(curr_pct_spread * 100.0, 1),
                    "gross_pnl_inr": round(gross_pnl, 2),
                    "total_cost_inr": round(total_cost, 2),
                    "net_pnl_inr": round(net_pnl, 2),
                    "net_return_pct": round(net_return_fraction * 100.0, 3),
                    "holding_days": holding_days,
                    "exit_reason": exit_reason
                })
                trade_id_seq += 1

                # Reset position
                in_position = False
                pos_direction = 0
                entry_idx = -1
                holding_days = 0

        equity_curve.append({
            "date": date_str,
            "equity_inr": round(equity, 2),
            "in_position": in_position
        })

    # Summary performance metrics
    total_net_pnl = equity - position_size_inr
    net_return_pct = (total_net_pnl / position_size_inr) * 100.0
    total_cost_drag = sum(t["total_cost_inr"] for t in trades)
    gross_pnl_sum = sum(t["gross_pnl_inr"] for t in trades)
    gross_return_pct = (gross_pnl_sum / position_size_inr) * 100.0

    # Max Drawdown
    eq_series = [pt["equity_inr"] for pt in equity_curve]
    peak = eq_series[0]
    max_dd = 0.0
    for val in eq_series:
        if val > peak:
            peak = val
        dd = (peak - val) / peak
        if dd > max_dd:
            max_dd = dd

    # Sharpe ratio (annualized, 252 days)
    trade_returns = [t["net_return_pct"] / 100.0 for t in trades]
    if len(trade_returns) >= 3 and np.std(trade_returns) > 1e-6:
        # Subtract daily risk free (6.5% / 252)
        rf_daily = 0.065 / 252.0
        excess_mean = float(np.mean(trade_returns)) - (rf_daily * max_holding_days)
        sharpe = (excess_mean / float(np.std(trade_returns))) * np.sqrt(252.0 / max_holding_days)
    else:
        sharpe = 0.0

    # Win rate
    wins = [t for t in trades if t["net_pnl_inr"] > 0]
    win_rate = (len(wins) / len(trades) * 100.0) if trades else 0.0

    # Profit factor
    gross_wins = sum(t["net_pnl_inr"] for t in wins)
    gross_losses = abs(sum(t["net_pnl_inr"] for t in trades if t["net_pnl_inr"] < 0))
    profit_factor = round(gross_wins / gross_losses, 2) if gross_losses > 0 else (99.0 if gross_wins > 0 else 0.0)

    return {
        "backtest_id": f"bt-{uuid.uuid4().hex[:8]}",
        "dataset_id": "current",
        "strategy_name": f"Robust Spread Reversion ({symbol_a}/{symbol_b})",
        "start_date": str(merged["timestamp"].min()),
        "end_date": str(merged["timestamp"].max()),
        "total_signals": total_signals,
        "executed_trades": len(trades),
        "gross_return_pct": round(gross_return_pct, 2),
        "net_return_pct": round(net_return_pct, 2),
        "total_costs_bps": round(roundtrip_friction_bps * len(trades), 1),
        "cost_drag_inr": round(total_cost_drag, 2),
        "max_drawdown_pct": round(max_dd * 100.0, 2),
        "sharpe_ratio": round(float(sharpe), 2),
        "win_rate": round(win_rate, 1),
        "profit_factor": profit_factor,
        "equity_curve": equity_curve,
        "trades": trades,
        "execution_realism_disclaimer": (
            "Hypothetical walk-forward historical simulation. Trades executed on T+1 after EOD signal "
            "with realistic roundtrip transaction costs and slippage deducted. Does not constitute an offer "
            "or guarantee of execution at historical settlement prices."
        )
    }
