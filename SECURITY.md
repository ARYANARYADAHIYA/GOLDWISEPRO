# GoldWise Pro — Security & Compliance Architecture

This document outlines the security architecture, threat models, and vulnerability mitigations implemented in **GoldWise Pro**.

---

## 1. Threat Model & Security Posture

As an institutional quantitative research platform, GoldWise Pro defends against four primary attack surfaces:
1. **Malicious Dataset Ingestion**: Arbitrary file uploads, path traversal, CSV formula injection, and denial-of-service via oversized payloads.
2. **Quantitative Manipulation & Code Injection**: Injection of unvalidated formulas into calculation pipelines.
3. **Data Exfiltration**: Unauthorized access to proprietary research casebook entries and backtest parameters.
4. **State Poisoning**: Invalidation of model artifacts through corrupted training submissions.

---

## 2. Implemented Defense Mechanisms

### 2.1 Secure File Ingestion & Data Quarantine
- **CSV Content Validation**: Uploaded files are verified as valid UTF-8/ASCII CSV streams. File headers are checked against expected schema names before data processing begins.
- **Path Traversal Protection**: Filenames submitted during upload are sanitized; files are isolated in designated storage directories using synthetic UUID identifiers rather than client-supplied paths.
- **SHA-256 Checksum Fingerprinting**: Every uploaded dataset receives a cryptographic SHA-256 fingerprint recorded in the database, ensuring non-repudiation and detecting tampering.

### 2.2 Strict Input Validation & Type Safety
- **Pydantic Schema Enforcement**: All incoming JSON payloads are validated against strict Pydantic schemas. Type coercion, range checks (e.g. $Z$-score thresholds $> 0$, contamination $\in (0, 0.5]$), and enum whitelists are enforced before reaching business logic.
- **SQL Injection Prevention**: All database queries utilize SQLAlchemy 2.0 parameterized expressions. Raw SQL string concatenation is strictly prohibited across the codebase.

### 2.3 Ephemeral Serverless Security (Vercel)
- **Read-Only Root Filesystem**: In Vercel serverless execution, the runtime filesystem is mounted read-only. Temporary scratch data and models are restricted to `/tmp`, which is automatically discarded at function lifecycle termination.
- **No Hardcoded Secrets**: Secrets and environment configurations are loaded strictly via environment variables (`.env`).

### 2.4 Immutable Audit Logging
- **Append-Only Event Ledger**: All critical system actions (scans, model training, parameter updates, casebook resolutions) write structured audit events into the `audit_events` table with UTC timestamps.
- **Operational Non-Repudiation**: The audit log records IP client details, actor identifiers, and serialized configuration snapshots.

---

## 3. Reporting a Vulnerability

If you discover a potential security vulnerability within GoldWise Pro, please notify the security team directly at `security@goldwise-pro.internal`.
Do not disclose vulnerabilities on public issue trackers.
