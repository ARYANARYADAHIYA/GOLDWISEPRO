import pytest
import numpy as np
import pandas as pd

from app.quant.contracts import get_contract_spec, list_all_specs
from app.quant.normalization import compute_pure_gold_price, normalize_price_by_symbol, calculate_spread
from app.quant.spreads import compute_rolling_spread_stats

def test_contract_specifications_lookup():
    gold = get_contract_spec("GOLD")
    assert gold is not None
    assert gold.quotation_basis_grams == 10.0
    assert gold.purity_per_mille == 995.0
    assert gold.trading_unit_grams == 1000.0

    goldm = get_contract_spec("GOLDM")
    assert goldm is not None
    assert goldm.quotation_basis_grams == 10.0
    assert goldm.purity_per_mille == 995.0
    assert goldm.trading_unit_grams == 100.0

    guinea = get_contract_spec("GOLDGUINEA")
    assert guinea is not None
    assert guinea.quotation_basis_grams == 8.0
    assert guinea.purity_per_mille == 999.0

    petal = get_contract_spec("GOLDPETAL")
    assert petal is not None
    assert petal.quotation_basis_grams == 1.0
    assert petal.purity_per_mille == 999.0

def test_hand_calculated_normalization():
    """
    HAND-CALCULATED BENCHMARK 1:
    MCX GOLD (10g quotation, 995 purity):
    Quoted Price: Rs 75,000 / 10g
    Quotation Basis: 10.0 grams
    Alloy price per gram: 75,000 / 10 = 7,500.0
    Purity fraction: 995 / 1000 = 0.995
    Pure gold price per gram = 7,500 / 0.995 = 7,537.688442...
    Pure gold price per 10g reference = 75,376.88
    """
    pure_price = compute_pure_gold_price(
        quoted_price=75000.0,
        quotation_basis_grams=10.0,
        purity_per_mille=995.0
    )
    expected_pure_per_gram = (75000.0 / 10.0) / (995.0 / 1000.0)
    assert abs(pure_price - expected_pure_per_gram) < 1e-6
    assert abs(pure_price - 7537.688442) < 1e-4

    norm_res = normalize_price_by_symbol("GOLDM", 75000.0)
    assert norm_res["normalized_pure_gold_per_gram"] == 7537.6884
    assert norm_res["normalized_pure_gold_per_10g"] == 75376.88

    """
    HAND-CALCULATED BENCHMARK 2:
    MCX GOLDPETAL (1g quotation, 999 purity):
    Quoted Price: Rs 7,530 / 1g
    Quotation Basis: 1.0 gram
    Alloy price per gram: 7,530 / 1 = 7,530.0
    Purity fraction: 999 / 1000 = 0.999
    Pure gold price per gram = 7,530 / 0.999 = 7,537.537537...
    """
    pure_petal = compute_pure_gold_price(
        quoted_price=7530.0,
        quotation_basis_grams=1.0,
        purity_per_mille=999.0
    )
    expected_pure_petal = 7530.0 / 0.999
    assert abs(pure_petal - expected_pure_petal) < 1e-6

def test_spread_calculation_zero_identity():
    # Identical normalized reference prices MUST yield exactly 0 spread
    spread = calculate_spread(7537.6884, 7537.6884)
    assert spread["raw_spread"] == 0.0
    assert spread["percentage_spread"] == 0.0
    assert spread["spread_bps"] == 0.0

def test_spread_calculation_known_divergence():
    # 7550 vs 7500 -> diff 50 -> (50 / 7500) * 100 = 0.6667% = 66.67 bps
    spread = calculate_spread(7550.0, 7500.0)
    assert abs(spread["percentage_spread"] - (50.0 / 7500.0 * 100.0)) < 1e-4
    assert abs(spread["spread_bps"] - (50.0 / 7500.0 * 10000.0)) < 1e-2

def test_rolling_mad_and_robust_zscore():
    # Create test time series
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    df = pd.DataFrame({
        "timestamp": [d.strftime("%Y-%m-%d") for d in dates],
        "normalized_a": [7500.0 + (i * 0.1) for i in range(30)],
        "normalized_b": [7500.0 for _ in range(30)],
    })
    
    # Inject large outlier at index 25
    df.loc[25, "normalized_a"] = 7530.0 # +30.0 jump

    stats_df = compute_rolling_spread_stats(df, window=20)
    assert "rolling_median" in stats_df.columns
    assert "rolling_mad" in stats_df.columns
    assert "robust_zscore" in stats_df.columns
    assert "percentile" in stats_df.columns

    # Outlier at index 25 must have robust_zscore > 2.0
    outlier_z = stats_df.loc[25, "robust_zscore"]
    assert not np.isnan(outlier_z)
    assert abs(outlier_z) > 2.0
