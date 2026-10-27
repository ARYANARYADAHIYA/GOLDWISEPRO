# GoldWise Pro

> **Institutional-Grade MCX Gold Relative-Value Research & Anomaly Investigation Platform**  
> Explainable ML-assisted surveillance, non-linear pricing normalisation, rigorous Opportunity Destroyer falsification, and walk-forward quantitative backtesting.

---

## Executive Summary

**GoldWise Pro** is a production-engineered quantitative research platform designed specifically for the Multi Commodity Exchange of India (MCX) gold derivatives ecosystem (`GOLD`, `GOLDM`, `GOLDGUINEA`, `GOLDPETAL`, `GOLDTEN`). 

Unlike retail dashboards or speculative "arbitrage bot" claims, GoldWise Pro operates on a foundational tenet of institutional quantitative finance: **All perceived market discrepancies are statistical or operational illusions until proven otherwise.** 

Every apparent pricing anomaly detected across contract specifications, expiries, or purity differences is immediately subjected to a 12-test **Opportunity Destroyer** falsification engine before any prospective trade hypothesis is admitted to the research casebook.

---

## Core Capabilities

1. **Deterministic Unit Normalisation**: Mathematically maps heterogeneous MCX contracts (varying quotation units of 10g, 8g, 1g, 100g, 1kg and purities of 995 vs 999 fineness) into an uncorrupted, uniform **pure gold reference price per gram (INR/g)**.
2. **Robust Relative-Value Statistical Engine**: Calculates rolling spreads, Median Absolute Deviation (MAD), and robust z-scores resistant to non-Gaussian tails and jump discontinuities.
3. **12-Point Opportunity Destroyer Engine**: Automated falsification suite testing tick mismatch, liquidity thresholds, bid-ask cross penalty, roll-risk boundaries, delivery tender period penalties, statutory GST, CTT, exchange turnover costs, and historical persistence.
4. **Signal Autopsy & Explainability Studio**: Feature-attribution decomposition isolating exactly why an anomaly was flagged, decomposed into basis effects, carry/cost of carry, liquidity premia, and purity adjustments.
5. **Reproducible ML Pipeline**: 
   - *Model A*: Robust Rolling Statistical Baseline (Zero-parameter, explainable anchor)
   - *Model B*: Unsupervised Isolation Forest (Non-linear multi-dimensional subspace outlier detector)
   - *Model C*: Supervised Cost-Adjusted Mean-Reversion Outcome Classifier (Predicting post-friction convergence)
   - *Tournament & Drift Monitor*: Out-of-sample benchmarking via Population Stability Index (PSI) and Brier scores.
6. **Walk-Forward Backtesting Lab**: Strict chronological simulation enforcing **T+1 execution delay** (eliminating lookahead/synchronous execution bias), dynamic slippage, and institutional fee schedules.
7. **Paper Research Casebook**: Non-executing research journal maintaining full auditability, hypothesis tracking, and post-event empirical review.
8. **Institutional FinTech Interface**: Single-page institutional workstation built with React, TypeScript, and Tailwind CSS following Bloomberg/FactSet-tier design principles (high data density, monospace tabular numerals, neutral light theme with muted gold `#c5a059` accents).

---

## Quickstart & Local Execution

### Prerequisites
- Python 3.10+ (with virtual environment)
- Node.js 18+ (with npm)

### 1. Backend Setup
```bash
# Clone or open the repository
git clone https://github.com/your-org/goldwise-pro.git
cd goldwise-pro

# Create and activate python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend tests
pytest -v

# Start development backend API server (runs on port 8000)
uvicorn backend.app.main:app --reload --port 8000
```
Backend API interactive OpenAPI documentation will be accessible at: `http://localhost:8000/docs`.

### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Build static assets (TypeScript verification + Vite bundle)
npm run build

# Start local frontend development server (runs on port 5173 with proxy to backend)
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Vercel Deployment

GoldWise Pro is configured out-of-the-box for seamless zero-configuration deployment to **Vercel** as a hybrid serverless application:
- **Serverless API**: Fast Python runtime serving `/api/*` through `api/index.py`.
- **Static Assets**: Pre-compiled Vite single-page application served from `frontend/dist`.
- **Storage Strategy**: Auto-detects serverless cold-start (`IS_VERCEL=1`), automatically provisioning and seeding an ephemeral SQLite instance in `/tmp/goldwise_pro.db` with deterministic synthetic MCX datasets.

To deploy via Vercel CLI:
```bash
npm install -g vercel
vercel
```

---

## Test Suite Verification

Run the automated verification suite covering unit math, Opportunity Destroyer falsification, real MCX data ingestion, ML pipeline training, price forecasting, and API integration:
```bash
pytest -v
```
**Expected Result**: `27 passed in ~4.2s`

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI (Python 3.12, async lifespan) |
| **Data & Modeling** | NumPy, Pandas, Scikit-learn, SciPy, Joblib |
| **ORM & Storage** | SQLAlchemy 2.0, SQLite (WAL mode, foreign keys enforced) |
| **Frontend Framework** | React 19, TypeScript, Vite |
| **Styling** | Tailwind CSS v4, Lucide React icons |
| **Deployment Engine** | Vercel Serverless Python & Static CDN |

---

## License

Proprietary Institutional Quantitative Software. All rights reserved.
