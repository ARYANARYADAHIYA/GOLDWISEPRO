import pytest
import io
import pandas as pd

from app.data.importer import parse_and_validate_csv, parse_mcx_date_str
from app.quant.destroyer import OpportunityDestroyer

def test_date_parser_ambiguity():
    # 25/06/2026 -> unambiguously 25th June
    parsed, is_ambig = parse_mcx_date_str("25/06/2026")
    assert parsed == "2026-06-25"
    assert is_ambig is False

    # 05/06/2026 -> both <= 12, ambiguous!
    parsed_dd, is_ambig = parse_mcx_date_str("05/06/2026", preferred_format="DD/MM/YYYY")
    assert parsed_dd == "2026-06-05"
    assert is_ambig is True

    parsed_mm, is_ambig = parse_mcx_date_str("05/06/2026", preferred_format="MM/DD/YYYY")
    assert parsed_mm == "2026-05-06"
    assert is_ambig is True

    # Compact MCX format 05AUG2026
    parsed_mcx, _ = parse_mcx_date_str("05AUG2026")
    assert parsed_mcx == "2026-08-05"

def test_csv_import_pipeline_dedup_and_normalize():
    csv_text = """Symbol,Date,ExpiryDate,ClosePrice,Volume
GOLDM,01/05/2026,05AUG2026,75000,5000
GOLDM,01/05/2026,05AUG2026,75000,5000
GOLD,01/05/2026,05AUG2026,75000,2000
GOLDPETAL,01/05/2026,31AUG2026,7530,1000
"""
    res = parse_and_validate_csv(csv_text.encode("utf-8"), preferred_date_format="DD/MM/YYYY")
    assert res["is_valid"] is True
    # 1 duplicate row was skipped
    assert res["row_count"] == 3
    assert res["duplicate_count"] == 1
    assert "GOLDM" in res["instruments"]
    assert "GOLDPETAL" in res["instruments"]

def test_opportunity_destroyer_falsification_checks():
    destroyer = OpportunityDestroyer(expiry_buffer_days=3)

    # 1. Near expiry candidate (2 days to expiry) MUST be suppressed!
    cand_near_expiry = {
        "price_a": 75000.0, "price_b": 75000.0,
        "normalized_a": 7537.68, "normalized_b": 7500.0,
        "percentage_spread": 0.50, "robust_zscore": 2.5,
        "expiry_distance_days": 2, "volume_a": 5000, "volume_b": 5000,
        "historical_obs_count": 25
    }
    res = destroyer.evaluate_candidate(cand_near_expiry)
    assert res["verdict"] == "SUPPRESSED"
    assert any("expiry" in f.lower() for f in res["fatal_failures"])

    # 2. Candidate with insufficient historical observations (< 15) MUST be INSUFFICIENT_DATA!
    cand_insufficient = {
        "price_a": 75000.0, "price_b": 75000.0,
        "normalized_a": 7537.68, "normalized_b": 7500.0,
        "percentage_spread": 0.50, "robust_zscore": 2.5,
        "expiry_distance_days": 20, "volume_a": 5000, "volume_b": 5000,
        "historical_obs_count": 8
    }
    res2 = destroyer.evaluate_candidate(cand_insufficient)
    assert res2["verdict"] == "INSUFFICIENT_DATA"

    # 3. Clean candidate that survives costs, has adequate history and distance MUST INVESTIGATE!
    cand_clean = {
        "price_a": 75000.0, "price_b": 75000.0,
        "normalized_a": 7537.68, "normalized_b": 7500.0,
        "percentage_spread": 0.50, # 50 bps spread > 11 bps roundtrip cost
        "robust_zscore": 2.4,
        "expiry_distance_days": 25, "volume_a": 5000, "volume_b": 5000,
        "historical_obs_count": 50
    }
    res3 = destroyer.evaluate_candidate(cand_clean)
    assert res3["verdict"] == "INVESTIGATE"
    assert res3["passed_all_fatal_checks"] is True
