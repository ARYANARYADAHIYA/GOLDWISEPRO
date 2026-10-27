# GoldWise Pro — Testing & Verification Guide

This document describes the automated test architecture, verification procedures, and regression test suites for **GoldWise Pro**.

---

## 1. Test Architecture Pyramid

The test suite is organized into four distinct testing tiers:

```
          / \
         /   \      API Integration Tests (FastAPI TestClient, 4 tests)
        /-----\
       /       \    Machine Learning Tests (Scikit-Learn, Pipelines, 3 tests)
      /---------\
     /           \  Quant & Destroyer Tests (12 checks, Half-life, 6 tests)
    /-------------\
   /               \ Unit Math & Normalization Tests (Pure gram math, 9 tests)
  /-----------------\
```

---

## 2. Test Execution

### 2.1 Backend Automated Verification Suite
Run with the pytest test runner inside the virtual environment:
```bash
# Execute entire test suite with verbose reporting
pytest -v

# Run only quantitative mathematical correctness tests
pytest backend/tests/test_quantitative_correctness.py -v

# Run only Opportunity Destroyer falsification tests
pytest backend/tests/test_opportunity_destroyer.py -v

# Run only ML pipeline training and reload tests
pytest backend/tests/test_ml_pipeline.py -v

# Run API end-to-end integration tests
pytest backend/tests/test_api_integration.py -v
```

### 2.2 Frontend Build & TypeScript Verification
```bash
cd frontend
npm run build
```
This runs `tsc -b && vite build`, enforcing strict type safety (`verbatimModuleSyntax`, `noUnusedLocals`, `noUnusedParameters`).

---

## 3. Test Coverage Matrix

| Test Module | Coverage Scope | Key Assertions Verified |
|---|---|---|
| `test_normalization.py` | Contract Specs & Pure Gram Math | Pure reference price invariant holds across 1kg (995), 100g (995), 8g (999), 1g (999). |
| `test_opportunity_destroyer.py` | 12-Check Falsification Engine | Illiquid lots rejected; expiry tender cliff suppressed; statutory friction breaks net spread; purity delta caught. |
| `test_quantitative_correctness.py` | Statistical & Financial Math | Robust z-score resilience against 50% outliers; cost breakdown matches MCX circulars; T+1 delay strictly enforced. |
| `test_ml_pipeline.py` | Machine Learning Pipeline | Isolation Forest and Logistic models train, serialize to `.joblib`, reload with zero loss of scoring consistency. |
| `test_data_importer.py` | Ingestion & Integrity Engine | Ambiguous date resolution (DD/MM vs MM/DD); SHA-256 fingerprinting; deduplication; data health score 0–100. |
| `test_api_integration.py` | FastAPI Endpoints | Full workflow: health check -> dataset list -> scan run -> candidate autopsy -> backtest -> casebook -> audit log. |

---

## 4. Benchmark Execution Results

All 22 test scenarios consistently execute in $< 4$ seconds on standard developer workstations:
```
======================= 22 passed, 25 warnings in 3.81s =======================
```
*(Warnings pertain to Starlette test client deprecation notices in third-party libraries).*









