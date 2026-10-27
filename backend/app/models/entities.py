import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship

from app.core.database import Base

class DatasetModel(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String, nullable=False)  # "SYNTHETIC" or "IMPORTED_CSV"
    file_hash = Column(String, nullable=True)
    row_count = Column(Integer, default=0)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    instruments = Column(String, nullable=True)  # Comma separated
    is_active = Column(Boolean, default=True)
    validation_status = Column(String, default="VALID")
    validation_report_json = Column(Text, nullable=True)
    provenance = Column(String, nullable=True)
    collection_timestamp = Column(DateTime, nullable=True)
    raw_file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    observations = relationship("ObservationModel", back_populates="dataset", cascade="all, delete-orphan")

class ObservationModel(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    expiry_date = Column(String, nullable=False, index=True)
    timestamp = Column(String, nullable=False, index=True)  # YYYY-MM-DD
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=False)
    previous_close = Column(Float, nullable=True)
    volume = Column(Float, nullable=True, default=0.0)
    turnover = Column(Float, nullable=True, default=0.0)
    open_interest = Column(Float, nullable=True, default=0.0)
    quotation_basis = Column(Float, nullable=False)
    purity = Column(Float, nullable=False)
    normalized_price_pure_gram = Column(Float, nullable=False)
    is_quarantined = Column(Boolean, default=False)
    quarantine_reason = Column(String, nullable=True)

    dataset = relationship("DatasetModel", back_populates="observations")

    __table_args__ = (
        Index("idx_obs_dataset_sym_time", "dataset_id", "symbol", "timestamp"),
        Index("idx_obs_dataset_sym_exp_time", "dataset_id", "symbol", "expiry_date", "timestamp"),
    )

class ContractSpecModel(Base):
    __tablename__ = "contract_specs"

    symbol = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    trading_unit_grams = Column(Float, nullable=False)
    quotation_basis_grams = Column(Float, nullable=False)
    purity_per_mille = Column(Float, nullable=False)
    tick_size = Column(Float, nullable=False)
    lot_size_grams = Column(Float, nullable=False)
    delivery_unit_grams = Column(Float, nullable=False)
    effective_date = Column(String, default="2020-01-01")
    source_verification_status = Column(String, default="VERIFIED_OFFICIAL_MCX")
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class ScanModel(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    pair_symbol_a = Column(String, nullable=False)
    pair_symbol_b = Column(String, nullable=False)
    config_json = Column(Text, nullable=False)
    total_candidates = Column(Integer, default=0)
    investigate_count = Column(Integer, default=0)
    suppressed_count = Column(Integer, default=0)
    insufficient_count = Column(Integer, default=0)

    candidates = relationship("AnomalyCandidateModel", back_populates="scan", cascade="all, delete-orphan")

class AnomalyCandidateModel(Base):
    __tablename__ = "anomaly_candidates"

    id = Column(String, primary_key=True)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False, index=True)
    timestamp = Column(String, nullable=False, index=True)
    symbol_a = Column(String, nullable=False)
    symbol_b = Column(String, nullable=False)
    expiry_a = Column(String, nullable=False)
    expiry_b = Column(String, nullable=False)
    price_a = Column(Float, nullable=False)
    price_b = Column(Float, nullable=False)
    normalized_a = Column(Float, nullable=False)
    normalized_b = Column(Float, nullable=False)
    raw_spread = Column(Float, nullable=False)
    percentage_spread = Column(Float, nullable=False)
    rolling_mean = Column(Float, nullable=True)
    rolling_std = Column(Float, nullable=True)
    rolling_median = Column(Float, nullable=True)
    rolling_mad = Column(Float, nullable=True)
    robust_zscore = Column(Float, nullable=True)
    percentile = Column(Float, nullable=True)
    expiry_distance_days = Column(Integer, nullable=True)
    volume_a = Column(Float, nullable=True)
    volume_b = Column(Float, nullable=True)
    verdict = Column(String, nullable=False)  # "INVESTIGATE", "SUPPRESSED", "INSUFFICIENT_DATA"
    rejection_reasons_json = Column(Text, nullable=True)
    destroyer_checks_json = Column(Text, nullable=True)
    autopsy_features_json = Column(Text, nullable=True)
    estimated_cost_bps = Column(Float, default=6.5)

    scan = relationship("ScanModel", back_populates="candidates")

class MLModelRecord(Base):
    __tablename__ = "ml_models"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # "BASELINE_STATISTICAL", "ISOLATION_FOREST", "SUPERVISED_RIDGE"
    dataset_id = Column(String, nullable=False)
    version = Column(String, nullable=False)
    status = Column(String, default="TRAINED")  # "TRAINED", "TRAINING", "FAILED"
    is_active = Column(Boolean, default=False)
    artifact_path = Column(String, nullable=True)
    hyperparameters_json = Column(Text, nullable=True)
    feature_names_json = Column(Text, nullable=True)
    train_metrics_json = Column(Text, nullable=True)
    val_metrics_json = Column(Text, nullable=True)
    test_metrics_json = Column(Text, nullable=True)
    split_config_json = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BacktestRecord(Base):
    __tablename__ = "backtests"

    id = Column(String, primary_key=True)
    model_id = Column(String, nullable=True)
    dataset_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    strategy_config_json = Column(Text, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    total_signals = Column(Integer, default=0)
    executed_trades = Column(Integer, default=0)
    gross_return_pct = Column(Float, default=0.0)
    net_return_pct = Column(Float, default=0.0)
    total_costs_bps = Column(Float, default=0.0)
    max_drawdown_pct = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    metrics_json = Column(Text, nullable=True)
    equity_curve_json = Column(Text, nullable=True)
    trade_log_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PaperResearchRecord(Base):
    __tablename__ = "paper_research"

    id = Column(String, primary_key=True)
    candidate_id = Column(String, nullable=True)
    symbol_pair = Column(String, nullable=False)
    observation_date = Column(String, nullable=False)
    initial_verdict = Column(String, nullable=False)
    initial_score = Column(Float, nullable=True)
    spread_bps = Column(Float, nullable=False)
    rationale = Column(Text, nullable=False)
    expected_horizon_days = Column(Integer, default=5)
    entry_price_spread = Column(Float, nullable=False)
    exit_observed_spread = Column(Float, nullable=True)
    cost_assumptions_json = Column(Text, nullable=True)
    status = Column(String, default="PROSPECTIVE")  # "PROSPECTIVE", "VALIDATED", "DISPROVED", "EXPIRED"
    notes = Column(Text, nullable=True)
    tags = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=True)
    summary = Column(String, nullable=False)
    details_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class SystemSettingModel(Base):
    __tablename__ = "system_settings"

    key = Column(String, primary_key=True)
    value_json = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
