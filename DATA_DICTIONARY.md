# GoldWise Pro — Data Dictionary & Schema Reference

This document provides complete documentation for the relational database schema, quantitative data structures, and synthetic dataset definitions in **GoldWise Pro**.

---

## 1. Relational Database Entities

### 1.1 `datasets`
Tracks imported and synthetic time-series datasets.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | Unique dataset identifier (e.g., `ds-synthetic-mcx-gold-baseline`) |
| `name` | `VARCHAR(128)` | `NOT NULL` | Human-readable dataset title |
| `description` | `TEXT` | `NULLABLE` | Dataset provenance and description |
| `source_type` | `VARCHAR(32)` | `DEFAULT 'SYNTHETIC'` | Source classification (`SYNTHETIC`, `CSV_IMPORT`, `MCX_FEED`) |
| `date_format` | `VARCHAR(32)` | `DEFAULT 'YYYY-MM-DD'` | Date parsing format used during ingestion |
| `sha256_hash` | `VARCHAR(64)` | `NULLABLE` | SHA-256 integrity hash of raw source data |
| `record_count` | `INTEGER` | `DEFAULT 0` | Total market observation records in dataset |
| `start_date` | `DATE` | `NULLABLE` | Earliest observation date in dataset |
| `end_date` | `DATE` | `NULLABLE` | Latest observation date in dataset |
| `created_at` | `DATETIME` | `DEFAULT utcnow()` | Timestamp of ingestion |

---

### 1.2 `market_observations`
Contains raw and normalized price/volume quotes for individual contract expiries.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY, AUTOINCREMENT` | Internal synthetic identifier |
| `dataset_id` | `VARCHAR(64)` | `FOREIGN KEY (datasets.id)` | Parent dataset association |
| `date` | `DATE` | `NOT NULL, INDEX` | Trading session date |
| `symbol` | `VARCHAR(32)` | `NOT NULL, INDEX` | MCX contract root (`GOLD`, `GOLDM`, `GOLDGUINEA`, etc.) |
| `expiry_date` | `DATE` | `NOT NULL` | Contract expiry settlement date |
| `open` | `FLOAT` | `NOT NULL` | Quoted open price |
| `high` | `FLOAT` | `NOT NULL` | Quoted high price |
| `low` | `FLOAT` | `NOT NULL` | Quoted low price |
| `close` | `FLOAT` | `NOT NULL` | Quoted settlement close price |
| `volume` | `FLOAT` | `DEFAULT 0.0` | Trading volume in lots |
| `open_interest`| `FLOAT` | `DEFAULT 0.0` | Outstanding contracts in lots |
| `normalized_price_pure_gram` | `FLOAT` | `NOT NULL` | Normalized price in INR per gram of pure 999.9 gold |

---

### 1.3 `contract_specs`
Exchange specifications for Multi Commodity Exchange of India contracts.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `symbol` | `VARCHAR(32)` | `PRIMARY KEY` | Root contract identifier |
| `name` | `VARCHAR(128)` | `NOT NULL` | Formal contract name |
| `lot_size_grams`| `FLOAT` | `NOT NULL` | Weight of underlying deliverable in grams |
| `quotation_basis_grams` | `FLOAT`| `NOT NULL` | Weight denominator of market price quote (e.g. 10g) |
| `tick_size_inr` | `FLOAT` | `NOT NULL` | Minimum price fluctuation in INR |
| `purity_fineness` | `FLOAT` | `NOT NULL` | Purity rating (995 for 1kg/100g, 999 for Guinea/Petal) |
| `delivery_type`| `VARCHAR(32)` | `NOT NULL` | Physical delivery or cash settled flag |
| `active` | `BOOLEAN` | `DEFAULT TRUE` | Active trading flag |

---

### 1.4 `anomaly_candidates`
Individual relative-value divergence candidates evaluated by the Opportunity Destroyer.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | Unique candidate identifier (e.g. `cand-a1b2c3d4`) |
| `scan_id` | `VARCHAR(64)` | `FOREIGN KEY (scans.id)` | Generating scan run |
| `date` | `DATE` | `NOT NULL` | Signal date |
| `symbol_a` | `VARCHAR(32)` | `NOT NULL` | Trading leg contract symbol |
| `symbol_b` | `VARCHAR(32)` | `NOT NULL` | Benchmark contract symbol |
| `normalized_price_a` | `FLOAT` | `NOT NULL` | Leg A pure gold price / gram |
| `normalized_price_b` | `FLOAT` | `NOT NULL` | Leg B pure gold price / gram |
| `percentage_spread` | `FLOAT` | `NOT NULL` | Relative spread $(P_A - P_B) / P_B$ |
| `robust_zscore`| `FLOAT` | `NULLABLE` | Robust z-score via Median Absolute Deviation |
| `opportunity_cost_bps` | `FLOAT`| `NOT NULL` | Total estimated roundtrip frictions in basis points |
| `net_spread_bps`| `FLOAT` | `NOT NULL` | Spread after all roundtrip frictions deducted |
| `verdict` | `VARCHAR(32)` | `NOT NULL` | Outcome (`INVESTIGATE`, `SUPPRESSED`, `INSUFFICIENT_DATA`) |
| `falsification_score` | `FLOAT` | `NOT NULL` | Fraction of 12 tests cleared (0.0 to 1.0) |
| `failed_checks_json` | `TEXT` | `NOT NULL` | JSON array of failed test identifiers |
| `explanation` | `TEXT` | `NOT NULL` | Human-readable institutional autopsy summary |

---

### 1.5 `paper_research_records`
Casebook journal entries recording quantitative hypotheses and real-world outcomes.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | Unique case identifier |
| `candidate_id` | `VARCHAR(64)` | `NULLABLE` | Optional originating anomaly candidate link |
| `symbol_pair` | `VARCHAR(64)` | `NOT NULL` | Evaluated pair (e.g., `GOLDM/GOLD`) |
| `observation_date` | `DATE` | `NOT NULL` | Initial observation date |
| `initial_verdict` | `VARCHAR(32)` | `NOT NULL` | Initial rating (`INVESTIGATE`, `VALIDATED`, etc.) |
| `spread_bps` | `FLOAT` | `NOT NULL` | Spread at observation in bps |
| `entry_price_spread` | `FLOAT` | `NOT NULL` | Effective entry spread |
| `rationale` | `TEXT` | `NOT NULL` | Quantitative research thesis and rationale |
| `status` | `VARCHAR(32)` | `DEFAULT 'OPEN'` | Workflow state (`OPEN`, `RESOLVED_CONVERGED`, `RESOLVED_DIVERGED`, `DISCARDED`) |
| `notes` | `TEXT` | `NULLABLE` | Post-event audit notes |
| `created_at` | `DATETIME` | `DEFAULT utcnow()` | Ingestion timestamp |
| `updated_at` | `DATETIME` | `DEFAULT utcnow()` | Last modification timestamp |

---

## 2. Synthetic Market Scenarios

The deterministic synthetic generator (`backend/app/quant/synthetic.py`) injects 8 realistic commodity market conditions to test quantitative robustness:

1. **`CLEAN_STATIONARY_PAIR`**: Pure cointegrated baseline with zero structural basis shift.
2. **`GENUINE_TRANSIENT_MISPRICING`**: High-liquidity transient divergence that cleanly reverts within 3–5 trading days.
3. **`ILLIQUIDITY_ILLUSION`**: Wide quote discrepancy accompanied by near-zero open interest and dry order books.
4. **`EXPIRY_TENDER_DISTORTION`**: Spread blowout inside the 5-day pre-expiry tender notice period caused by physical delivery margin surcharges.
5. **`PURITY_CONFUSION`**: Apparent mispricing created by naive unadjusted comparison between 995 fineness (`GOLDM`) and 999 fineness (`GOLDGUINEA`).
6. **`STRUCTURAL_BREAK`**: Step-jump in basis caused by simulated Indian Union Budget import tariff hike (e.g., +250 bps permanent shift).
7. **`DATA_OUTLIER_BAD_TICK`**: Erroneous isolated single-bar data spike (5 standard deviations) to verify bad-tick rejection.
8. **`HIGH_VOLATILITY_EXPANSION`**: Regime transition where rolling variance doubles and bid-ask spreads widen significantly.
