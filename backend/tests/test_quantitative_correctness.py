import pytest
import numpy as np
import pandas as pd

from app.quant.synthetic import generate_synthetic_mcx_dataset
from app.quant.scanner import run_relative_value_scan
from app.quant.backtest import run_walk_forward_backtest
from app.quant.cost_simulator import calculate_mcx_transaction_costs

def test_injected_deviation_is_detected():
    """
    In the deterministic synthetic generator, on Day 85 we explicitly injected
    a ~48 bps relative value divergence between GOLDM and GOLD.
    The scanner MUST detect this observation.
    """
    records = generate_synthetic_mcx_dataset(start_date="2026-04-01", num_days=140, random_seed=42)
    df_obs = pd.DataFrame(records)

    scan_res = run_relative_value_scan(
        df_obs,
        symbol_a="GOLDM",
        symbol_b="GOLD",
        zscore_threshold=2.0
    )

    assert scan_res["total_candidates"] > 100
    assert scan_res["investigate_count"] > 0

    # Locate day 85 candidate
    cands = scan_res["candidates"]
    day_85_cand = cands[85]
    assert day_85_cand is not None
    # Day 85 has wide spread and significant robust zscore
    assert abs(day_85_cand["percentage_spread"]) > 0.35
    assert abs(day_85_cand["robust_zscore"]) >= 2.0
    assert day_85_cand["verdict"] == "INVESTIGATE"

def test_zero_lookahead_guarantee_in_backtest():
    """
    Verify that backtest decisions strictly lag signal generation by execution_delay_days (T+1).
    Trade entry date must be strictly after signal date.
    """
    records = generate_synthetic_mcx_dataset(start_date="2026-04-01", num_days=140, random_seed=42)
    df_obs = pd.DataFrame(records)

    bt = run_walk_forward_backtest(
        df_observations=df_obs,
        symbol_a="GOLDM",
        symbol_b="GOLD",
        entry_zscore=2.0,
        execution_delay_days=1
    )

    assert bt["executed_trades"] > 0
    for trade in bt["trades"]:
        # Entry date must be chronologically greater than signal date
        assert trade["entry_date"] > trade["signal_date"]
        # Exit date must be greater than or equal to entry date
        assert trade["exit_date"] >= trade["entry_date"]
        # Gross PnL - Total Cost must equal Net PnL
        expected_net = round(trade["gross_pnl_inr"] - trade["total_cost_inr"], 2)
        assert abs(trade["net_pnl_inr"] - expected_net) <= 0.05

def test_cost_survival_mathematics():
    """
    Verify that transaction costs correctly compute roundtrip turnover and statutory charges.
    """
    cost_res = calculate_mcx_transaction_costs(
        quoted_price_per_10g=75000.0,
        contract_lot_grams=100.0,
        position_lots=1,
        brokerage_bps=1.5,
        exchange_fees_bps=1.0,
        slippage_bps=2.0
    )

    # 1 lot of 100g GOLDM at 75,000 / 10g = Rs 750,000 per leg
    # 4 legs total roundtrip = Rs 3,000,000 turnover
    assert cost_res["turnover_inr"] == 3_000_000.0
    assert cost_res["total_roundtrip_cost_inr"] > 0
    assert cost_res["break_even_spread_divergence_pct"] > 0
