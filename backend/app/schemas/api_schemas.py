from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ContractSpecSchema(BaseModel):
    symbol: str
    name: str
    trading_unit_grams: float
    quotation_basis_grams: float
    purity_per_mille: float
    tick_size: float
    lot_size_grams: float
    delivery_unit_grams: float
    effective_date: str
    source_verification_status: str
    notes: Optional[str] = None

class NormalizationBreakdown(BaseModel):
    symbol: str
    quoted_price: float
    quotation_basis_grams: float
    quoted_price_per_gram_alloy: float
    purity_per_mille: float
    purity_fraction: float
    normalized_pure_gold_per_gram: float
    normalized_pure_gold_per_10g: float
    formula_latex: str
    source_status: str

class NormalizationRequest(BaseModel):
    symbol: str
    quoted_price: float

class NormalizationResponse(BaseModel):
    breakdown: NormalizationBreakdown

class DatasetSummarySchema(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    source_type: str
    file_hash: Optional[str] = None
    row_count: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    instruments: Optional[str] = None
    is_active: bool
    validation_status: str
    created_at: str

class ObservationSchema(BaseModel):
    id: int
    dataset_id: str
    symbol: str
    expiry_date: str
    timestamp: str
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: float
    volume: Optional[float] = 0.0
    open_interest: Optional[float] = 0.0
    quotation_basis: float
    purity: float
    normalized_price_pure_gram: float
    is_quarantined: bool
    quarantine_reason: Optional[str] = None

class ScanRequest(BaseModel):
    dataset_id: str
    pair_symbol_a: str = "GOLDM"
    pair_symbol_b: str = "GOLD"
    zscore_threshold: float = 2.0
    percentile_lower: float = 2.5
    percentile_upper: float = 97.5
    rolling_window_days: int = 20
    min_observations: int = 15
    slippage_bps: float = 3.0
    brokerage_bps: float = 1.5
    exchange_fees_bps: float = 1.0
    expiry_buffer_days: int = 3

class AnomalyCandidateSchema(BaseModel):
    id: str
    scan_id: str
    timestamp: str
    symbol_a: str
    symbol_b: str
    expiry_a: str
    expiry_b: str
    price_a: float
    price_b: float
    normalized_a: float
    normalized_b: float
    raw_spread: float
    percentage_spread: float
    rolling_mean: Optional[float] = None
    rolling_std: Optional[float] = None
    rolling_median: Optional[float] = None
    rolling_mad: Optional[float] = None
    robust_zscore: Optional[float] = None
    percentile: Optional[float] = None
    expiry_distance_days: Optional[int] = None
    volume_a: Optional[float] = None
    volume_b: Optional[float] = None
    verdict: str  # INVESTIGATE, SUPPRESSED, INSUFFICIENT_DATA
    rejection_reasons: List[str] = []
    destroyer_checks: Dict[str, Any] = {}
    autopsy_features: Dict[str, Any] = {}
    estimated_cost_bps: float = 6.5

class ScanResponse(BaseModel):
    scan_id: str
    dataset_id: str
    timestamp: str
    total_candidates: int
    investigate_count: int
    suppressed_count: int
    insufficient_count: int
    candidates: List[AnomalyCandidateSchema]

class DestroyerCheckResult(BaseModel):
    check_name: str
    category: str
    passed: bool
    severity: str  # "FATAL_DISPROVAL", "HIGH_RISK", "MODERATE_CAUTION", "CLEAR"
    evidence_value: Any
    threshold: Any
    explanation: str

class DestroyerResponse(BaseModel):
    candidate_id: str
    verdict: str
    passed_all_fatal_checks: bool
    fatal_failures: List[str]
    caution_warnings: List[str]
    checks: List[DestroyerCheckResult]
    residual_uncertainty_score: float  # 0.0 to 1.0

class FeaturePerturbationAttribution(BaseModel):
    feature_name: str
    baseline_value: float
    perturbed_value: float
    score_impact: float
    relative_importance_pct: float
    description: str

class AutopsyResponse(BaseModel):
    candidate_id: str
    timestamp: str
    symbol_pair: str
    verdict: str
    anomaly_score: float
    model_confidence: float
    historical_percentile: float
    robust_zscore: float
    detection_reasons: List[str]
    feature_attributions: List[FeaturePerturbationAttribution]
    alternative_explanations_examined: List[Dict[str, Any]]
    counter_evidence: List[str]
    economic_survival_summary: Dict[str, Any]

class MLModelTrainRequest(BaseModel):
    name: str
    model_type: str = "ISOLATION_FOREST"  # BASELINE_STATISTICAL, ISOLATION_FOREST, SUPERVISED_RIDGE
    dataset_id: str
    train_split_pct: float = 0.70
    val_split_pct: float = 0.15
    contamination: float = 0.05
    n_estimators: int = 100
    random_state: int = 42

class MLModelSchema(BaseModel):
    id: str
    name: str
    model_type: str
    dataset_id: str
    version: str
    status: str
    is_active: bool
    artifact_path: Optional[str] = None
    hyperparameters: Dict[str, Any] = {}
    feature_names: List[str] = []
    train_metrics: Dict[str, Any] = {}
    val_metrics: Dict[str, Any] = {}
    test_metrics: Dict[str, Any] = {}
    split_config: Dict[str, Any] = {}
    logs: Optional[str] = None
    created_at: str

class TournamentModelEntry(BaseModel):
    model_id: str
    model_name: str
    model_type: str
    detection_rate_pct: float
    cross_agreement_score: float
    stability_score: float
    median_anomaly_score: float
    runtime_ms: float
    is_benchmark_baseline: bool
    evaluation_notes: str

class TournamentResponse(BaseModel):
    dataset_id: str
    eligible_observations_count: int
    models: List[TournamentModelEntry]
    pairwise_agreement_matrix: Dict[str, Dict[str, float]]
    recommendation_summary: str

class BacktestRequest(BaseModel):
    dataset_id: str
    model_id: Optional[str] = None
    pair_symbol_a: str = "GOLDM"
    pair_symbol_b: str = "GOLD"
    entry_zscore: float = 2.0
    exit_zscore: float = 0.5
    holding_period_days: int = 5
    position_size_inr: float = 1_000_000.0
    slippage_bps: float = 3.0
    brokerage_bps: float = 1.5
    exchange_fees_bps: float = 1.0
    gst_pct: float = 18.0
    stamp_duty_bps: float = 0.2
    execution_delay_days: int = 1  # T+1 chronological execution to prevent lookahead!

class BacktestTrade(BaseModel):
    trade_id: int
    entry_date: str
    exit_date: str
    signal_date: str
    symbol_a: str
    symbol_b: str
    spread_at_signal_bps: float
    entry_spread_bps: float
    exit_spread_bps: float
    gross_pnl_inr: float
    total_cost_inr: float
    net_pnl_inr: float
    net_return_pct: float
    holding_days: int
    exit_reason: str

class BacktestResponse(BaseModel):
    backtest_id: str
    dataset_id: str
    strategy_name: str
    start_date: str
    end_date: str
    total_signals: int
    executed_trades: int
    gross_return_pct: float
    net_return_pct: float
    total_costs_bps: float
    cost_drag_inr: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    equity_curve: List[Dict[str, Any]]
    trades: List[BacktestTrade]
    execution_realism_disclaimer: str

class CostSimulationRequest(BaseModel):
    quoted_price_per_10g: float = 75000.0
    contract_lot_grams: float = 100.0  # GOLDM
    position_lots: int = 1
    brokerage_bps: float = 1.5
    exchange_fees_bps: float = 1.0
    sebi_turnover_bps: float = 0.1
    stamp_duty_bps: float = 0.2
    gst_on_charges_pct: float = 18.0
    bid_ask_half_spread_bps: float = 2.0
    market_impact_bps: float = 1.0
    slippage_bps: float = 1.5

class CostSimulationResponse(BaseModel):
    turnover_inr: float
    brokerage_inr: float
    exchange_fees_inr: float
    sebi_charges_inr: float
    stamp_duty_inr: float
    gst_inr: float
    statutory_total_inr: float
    bid_ask_cost_inr: float
    slippage_cost_inr: float
    market_impact_cost_inr: float
    total_roundtrip_cost_inr: float
    total_cost_basis_points: float
    break_even_spread_divergence_pct: float
    cost_breakdown_percentages: Dict[str, float]
    sensitivity_table: List[Dict[str, Any]]
    disclaimer: str

class RealityCheckRequest(BaseModel):
    dataset_id: str
    pair_symbol_a: str = "GOLDM"
    pair_symbol_b: str = "GOLD"
    rolling_windows: List[int] = [10, 15, 20, 30, 45]
    zscore_thresholds: List[float] = [1.5, 2.0, 2.5, 3.0]
    num_bootstrap_samples: int = 200

class RealityCheckResponse(BaseModel):
    dataset_id: str
    walk_forward_stability_score: float
    parameter_grid_sensitivity: List[Dict[str, Any]]
    subwindow_results: List[Dict[str, Any]]
    bootstrap_p_value: float
    multiple_testing_penalty_applied: float
    selection_bias_risk_rating: str  # "LOW", "MODERATE", "SEVERE"
    verdict_survival_rating: str

class CounterfactualRequest(BaseModel):
    candidate_id: str
    modified_slippage_bps: Optional[float] = None
    modified_zscore_threshold: Optional[float] = None
    modified_rolling_window: Optional[int] = None
    modified_expiry_buffer_days: Optional[int] = None
    override_quotation_basis: Optional[float] = None

class CounterfactualResponse(BaseModel):
    candidate_id: str
    original_verdict: str
    counterfactual_verdict: str
    original_score: float
    counterfactual_score: float
    verdict_changed: bool
    driver_factors: List[str]
    robustness_assessment: str

class LifecycleContractItem(BaseModel):
    symbol: str
    expiry_date: str
    days_to_expiry: int
    available_observations: int
    data_coverage_pct: float
    average_daily_volume: float
    is_liquid_enough: bool
    is_active_roll: bool
    expiry_warning_level: str  # "NORMAL", "CAUTION", "CRITICAL_DELIVERY_IMMINENT"

class LifecycleResponse(BaseModel):
    contracts: List[LifecycleContractItem]
    roll_schedule_summary: str

class RegimeAnalysisResponse(BaseModel):
    dataset_id: str
    current_regime: str  # "LOW_VOLATILITY_STABLE", "NORMAL_CONTANGO", "HIGH_VOLATILITY_STRESSED", "STRUCTURAL_SHIFT"
    volatility_clusters: List[Dict[str, Any]]
    structural_breaks_detected: List[Dict[str, Any]]
    methodology_notes: str

class PaperResearchCreate(BaseModel):
    candidate_id: Optional[str] = None
    symbol_pair: str
    observation_date: str
    initial_verdict: str
    initial_score: Optional[float] = None
    spread_bps: float
    rationale: str
    expected_horizon_days: int = 5
    entry_price_spread: float
    cost_assumptions: Dict[str, Any] = {}
    tags: Optional[str] = "anomaly,relative_value"

class PaperResearchSchema(BaseModel):
    id: str
    candidate_id: Optional[str] = None
    symbol_pair: str
    observation_date: str
    initial_verdict: str
    initial_score: Optional[float] = None
    spread_bps: float
    rationale: str
    expected_horizon_days: int
    entry_price_spread: float
    exit_observed_spread: Optional[float] = None
    cost_assumptions: Dict[str, Any] = {}
    status: str
    notes: Optional[str] = None
    tags: Optional[str] = None
    updated_at: str
    created_at: str

class AuditEventSchema(BaseModel):
    id: int
    event_type: str
    entity_type: str
    entity_id: Optional[str] = None
    summary: str
    details: Dict[str, Any] = {}
    timestamp: str

class SystemHealthResponse(BaseModel):
    status: str
    database_connected: bool
    active_dataset_id: Optional[str] = None
    dataset_type: Optional[str] = None
    total_datasets: int
    total_observations: int
    trained_models_count: int
    completed_scans_count: int
    system_version: str
    uptime_status: str
