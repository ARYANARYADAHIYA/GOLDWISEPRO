import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import engine, Base, SessionLocal
from app.services.dataset_service import seed_synthetic_dataset_if_empty

@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_synthetic_dataset_if_empty(db)
    finally:
        db.close()

client = TestClient(app)

def test_api_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["database_connected"] is True
    assert data["total_datasets"] >= 1

def test_api_overview_endpoint():
    response = client.get("/api/overview")
    assert response.status_code == 200
    data = response.json()
    assert "active_dataset" in data
    assert "data_quality" in data
    assert "active_candidates_summary" in data

def test_api_contracts_and_normalize():
    # List specs
    res_specs = client.get("/api/contracts")
    assert res_specs.status_code == 200
    specs = res_specs.json()
    assert len(specs) >= 4
    symbols = [s["symbol"] for s in specs]
    assert "GOLDM" in symbols

    # Normalize breakdown
    norm_res = client.post("/api/contracts/normalize", json={"symbol": "GOLDM", "quoted_price": 75000.0})
    assert norm_res.status_code == 200
    bdown = norm_res.json()["breakdown"]
    assert bdown["normalized_pure_gold_per_gram"] == 7537.6884

def test_api_scan_and_candidate_pipeline():
    # Health check to get active dataset
    h_res = client.get("/api/health")
    ds_id = h_res.json()["active_dataset_id"]

    # Run scan
    scan_res = client.post("/api/scans/run", json={
        "dataset_id": ds_id,
        "pair_symbol_a": "GOLDM",
        "pair_symbol_b": "GOLD",
        "zscore_threshold": 2.0
    })
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["total_candidates"] > 0
    assert "candidates" in scan_data

    # Fetch candidate detail
    first_cand = scan_data["candidates"][0]
    cand_res = client.get(f"/api/candidates/{first_cand['id']}")
    assert cand_res.status_code == 200
    cand_data = cand_res.json()
    assert "destroyer_checks" in cand_data
    assert "autopsy_features" in cand_data

def test_api_backtest_endpoint():
    h_res = client.get("/api/health")
    ds_id = h_res.json()["active_dataset_id"]

    bt_res = client.post("/api/backtests/run", json={
        "dataset_id": ds_id,
        "pair_symbol_a": "GOLDM",
        "pair_symbol_b": "GOLD",
        "entry_zscore": 2.0,
        "holding_period_days": 5
    })
    assert bt_res.status_code == 200
    bt_data = bt_res.json()
    assert "net_return_pct" in bt_data
    assert "sharpe_ratio" in bt_data
    assert "equity_curve" in bt_data
    assert "trades" in bt_data

def test_api_cost_simulator_and_counterfactual():
    # Cost simulator
    cost_res = client.post("/api/cost-simulator", json={
        "quoted_price_per_10g": 75000.0,
        "position_lots": 1
    })
    assert cost_res.status_code == 200
    assert cost_res.json()["total_roundtrip_cost_inr"] > 0

    # Get a candidate from a scan
    h_res = client.get("/api/health")
    ds_id = h_res.json()["active_dataset_id"]
    scan_res = client.post("/api/scans/run", json={
        "dataset_id": ds_id,
        "pair_symbol_a": "GOLDM",
        "pair_symbol_b": "GOLD"
    })
    cand_id = scan_res.json()["candidates"][0]["id"]

    # Counterfactual
    cf_res = client.post("/api/counterfactual", json={
        "candidate_id": cand_id,
        "modified_slippage_bps": 10.0,
        "modified_zscore_threshold": 3.0
    })
    assert cf_res.status_code == 200
    cf_data = cf_res.json()
    assert "counterfactual_verdict" in cf_data
    assert "robustness_assessment" in cf_data

def test_api_casebook_and_report():
    # Create research casebook entry
    cb_res = client.post("/api/casebook", json={
        "symbol_pair": "GOLDM/GOLD",
        "observation_date": "2026-05-15",
        "initial_verdict": "INVESTIGATE",
        "spread_bps": 48.5,
        "rationale": "High statistical divergence with clean destroyer checks.",
        "entry_price_spread": 48.5
    })
    assert cb_res.status_code == 200
    case_id = cb_res.json()["id"]

    # List casebook entries
    cb_list = client.get("/api/casebook")
    assert cb_list.status_code == 200
    assert len(cb_list.json()) >= 1

    # Generate report
    rep_res = client.post("/api/reports/generate")
    assert rep_res.status_code == 200
    assert "markdown_content" in rep_res.json()
    assert "report_id" in rep_res.json()
