export interface ContractSpec {
  symbol: string;
  name: string;
  trading_unit_grams: number;
  quotation_basis_grams: number;
  purity_per_mille: number;
  tick_size: number;
  lot_size_grams: number;
  delivery_unit_grams: number;
  effective_date: string;
  source_verification_status: string;
  notes?: string;
}

export interface NormalizationBreakdown {
  symbol: string;
  quoted_price: number;
  quotation_basis_grams: number;
  quoted_price_per_gram_alloy: number;
  purity_per_mille: number;
  purity_fraction: number;
  normalized_pure_gold_per_gram: number;
  normalized_pure_gold_per_10g: number;
  formula_latex: string;
  source_status: string;
  tick_size: number;
}

export interface DatasetSummary {
  id: string;
  name: string;
  description?: string;
  source_type: "SYNTHETIC" | "IMPORTED_CSV" | "REAL_MCX" | "OFFICIAL_MCX_MANUAL_UPLOAD" | string;
  file_hash?: string;
  row_count: number;
  start_date?: string;
  end_date?: string;
  instruments?: string;
  is_active: boolean;
  validation_status: string;
  provenance?: string;
  collection_timestamp?: string;
  created_at: string;
}

export interface AnomalyCandidate {
  id: string;
  scan_id: string;
  timestamp: string;
  symbol_a: string;
  symbol_b: string;
  expiry_a: string;
  expiry_b: string;
  price_a: number;
  price_b: number;
  normalized_a: number;
  normalized_b: number;
  raw_spread: number;
  percentage_spread: number;
  rolling_mean?: number;
  rolling_std?: number;
  rolling_median?: number;
  rolling_mad?: number;
  robust_zscore?: number;
  percentile?: number;
  expiry_distance_days?: number;
  volume_a?: number;
  volume_b?: number;
  verdict: "INVESTIGATE" | "SUPPRESSED" | "INSUFFICIENT_DATA";
  rejection_reasons: string[];
  destroyer_checks: {
    verdict: string;
    passed_all_fatal_checks: boolean;
    fatal_failures: string[];
    caution_warnings: string[];
    checks: Array<{
      check_name: string;
      category: string;
      passed: boolean;
      severity: string;
      evidence_value: any;
      threshold: any;
      explanation: string;
    }>;
    residual_uncertainty_score: number;
  };
  autopsy_features: {
    candidate_id: string;
    timestamp: string;
    symbol_pair: string;
    verdict: string;
    anomaly_score: number;
    model_confidence: number;
    historical_percentile: number;
    robust_zscore: number;
    detection_reasons: string[];
    feature_attributions: Array<{
      feature_name: string;
      baseline_value: number;
      perturbed_value: number;
      score_impact: number;
      relative_importance_pct: number;
      description: string;
    }>;
    alternative_explanations_examined: Array<{
      hypothesis: string;
      status: string;
      evidence: string;
    }>;
    counter_evidence: string[];
    economic_survival_summary: {
      gross_spread_bps: number;
      estimated_friction_bps: number;
      hypothetical_net_bps: number;
      survives_costs: boolean;
      abstention_recommendation: boolean;
    };
  };
  estimated_cost_bps: number;
}

export interface ScanResponse {
  scan_id: string;
  dataset_id: string;
  timestamp: string;
  total_candidates: number;
  investigate_count: number;
  suppressed_count: number;
  insufficient_count: number;
  candidates: AnomalyCandidate[];
}

export interface ExecutiveOverview {
  active_dataset: {
    id: string;
    name: string;
    source_type: string;
    is_synthetic: boolean;
    row_count: number;
    start_date: string;
    end_date: string;
    instruments: string[];
    validation_status: string;
  };
  data_quality: {
    score: number;
    status: string;
    issues_count: number;
  };
  latest_scan: {
    id: string | null;
    timestamp: string | null;
    pair: string;
    total_candidates: number;
    investigate_count: number;
    suppressed_count: number;
    insufficient_count: number;
  };
  active_candidates_summary: {
    investigate: number;
    suppressed: number;
    insufficient: number;
  };
  latest_model: {
    id: string | null;
    name: string;
    model_type: string;
    status: string;
    version: string;
  };
  latest_backtest: {
    id: string | null;
    net_return_pct: number;
    sharpe_ratio: number;
    win_rate: number;
  };
  recent_research_activity: Array<{
    id: number;
    event_type: string;
    entity_type: string;
    entity_id?: string;
    summary: string;
    details: any;
    timestamp: string;
  }>;
}

export interface BacktestResult {
  backtest_id: string;
  dataset_id: string;
  strategy_name: string;
  start_date: string;
  end_date: string;
  total_signals: number;
  executed_trades: number;
  gross_return_pct: number;
  net_return_pct: number;
  total_costs_bps: number;
  cost_drag_inr: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  win_rate: number;
  profit_factor: number;
  equity_curve: Array<{
    date: string;
    equity_inr: number;
    in_position: boolean;
  }>;
  trades: Array<{
    trade_id: number;
    signal_date: string;
    entry_date: string;
    exit_date: string;
    symbol_a: string;
    symbol_b: string;
    spread_at_signal_bps: number;
    entry_spread_bps: number;
    exit_spread_bps: number;
    gross_pnl_inr: number;
    total_cost_inr: number;
    net_pnl_inr: number;
    net_return_pct: number;
    holding_days: number;
    exit_reason: string;
  }>;
  execution_realism_disclaimer: string;
}

export interface CostSimulationResult {
  turnover_inr: number;
  brokerage_inr: number;
  exchange_fees_inr: number;
  sebi_charges_inr: number;
  stamp_duty_inr: number;
  gst_inr: number;
  statutory_total_inr: number;
  bid_ask_cost_inr: number;
  slippage_cost_inr: number;
  market_impact_cost_inr: number;
  total_roundtrip_cost_inr: number;
  total_cost_basis_points: number;
  break_even_spread_divergence_pct: number;
  cost_breakdown_percentages: Record<string, number>;
  sensitivity_table: Array<{
    scenario: string;
    slippage_bps: number;
    total_roundtrip_inr: number;
    break_even_bps: number;
  }>;
  disclaimer: string;
}

export interface RealityCheckResult {
  dataset_id: string;
  walk_forward_stability_score: number;
  parameter_grid_sensitivity: Array<{
    window_days: number;
    zscore_threshold: number;
    anomalies_detected: number;
    anomaly_rate_pct: number;
    stability: string;
  }>;
  subwindow_results: Array<{
    subwindow_name: string;
    sample_count: number;
    spread_mean_bps: number;
    spread_std_bps: number;
    max_divergence_bps: number;
  }>;
  bootstrap_p_value: number;
  total_experiments_evaluated: number;
  multiple_testing_penalty_applied: number;
  selection_bias_risk_rating: string;
  verdict_survival_rating: string;
}

export interface MLModelRecord {
  id: string;
  name: string;
  model_type: string;
  dataset_id: string;
  version: string;
  status: string;
  is_active: boolean;
  artifact_path?: string;
  hyperparameters: Record<string, any>;
  train_metrics: Record<string, any>;
  val_metrics: Record<string, any>;
  test_metrics: Record<string, any>;
  split_config: Record<string, any>;
  created_at: string;
}

export interface TournamentResult {
  dataset_id: string;
  eligible_observations_count: number;
  models: Array<{
    model_id: string;
    model_name: string;
    model_type: string;
    detection_rate_pct: number;
    cross_agreement_score: number;
    stability_score: number;
    median_anomaly_score: number;
    runtime_ms: number;
    is_benchmark_baseline: boolean;
    evaluation_notes: string;
  }>;
  pairwise_agreement_matrix: Record<string, Record<string, number>>;
  recommendation_summary: string;
}

export interface PaperResearchRecord {
  id: string;
  candidate_id?: string;
  symbol_pair: string;
  observation_date: string;
  initial_verdict: string;
  initial_score?: number;
  spread_bps: number;
  rationale: string;
  expected_horizon_days: number;
  entry_price_spread: number;
  exit_observed_spread?: number;
  cost_assumptions: Record<string, any>;
  status: "PROSPECTIVE" | "VALIDATED" | "DISPROVED" | "EXPIRED";
  notes?: string;
  tags?: string;
  updated_at: string;
  created_at: string;
}

export interface LifecycleItem {
  symbol: string;
  expiry_date: string;
  days_to_expiry: number;
  available_observations: number;
  data_coverage_pct: number;
  average_daily_volume: number;
  is_liquid_enough: boolean;
  is_active_roll: boolean;
  expiry_warning_level: "NORMAL" | "CAUTION" | "CRITICAL_DELIVERY_IMMINENT";
  liquidity_status?: string;
  lifecycle_warning?: string;
}

export interface RegimeAnalysisResult {
  dataset_id: string;
  current_regime: string;
  recent_annualized_vol_pct: number;
  volatility_clusters: Array<{
    cluster_name: string;
    volatility_annualized_pct: number;
    market_state: string;
  }>;
  structural_breaks_detected: Array<{
    timestamp: string;
    break_type: string;
    pre_break_mean_bps: number;
    post_break_mean_bps: number;
    confidence: number;
    interpretation: string;
  }>;
  methodology_notes: string;
}

export interface DataIntegrityReport {
  overall_quality_score: number;
  status: string;
  total_observations_audited: number;
  issues: Array<{
    category: string;
    severity: string;
    description: string;
    affected_rows: number;
  }>;
  metrics: {
    invalid_ohlc_count: number;
    price_outlier_count: number;
    stale_price_count: number;
    unexpected_gaps_count: number;
    deductions_applied: number;
  };
  score_formula: string;
}
