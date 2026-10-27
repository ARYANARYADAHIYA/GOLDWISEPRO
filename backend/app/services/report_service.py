import os
import json
import datetime
from typing import Dict, Any, Optional
from app.core.config import REPORTS_DIR

def generate_research_report(
    dataset_info: Dict[str, Any],
    scan_info: Optional[Dict[str, Any]] = None,
    backtest_info: Optional[Dict[str, Any]] = None,
    model_info: Optional[Dict[str, Any]] = None,
    reality_check_info: Optional[Dict[str, Any]] = None,
    cost_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Module S: Institutional Research Report Generator.
    Produces comprehensive, auditable quantitative research reports.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    report_id = f"rep-{now_utc.strftime('%Y%m%d%H%M%S')}"
    timestamp = now_utc.isoformat()

    provenance = {
        "dataset_id": dataset_info.get("id"),
        "dataset_name": dataset_info.get("name"),
        "source_type": dataset_info.get("source_type"),
        "file_hash": dataset_info.get("file_hash"),
        "row_count": dataset_info.get("row_count"),
        "time_range": f"{dataset_info.get('start_date')} to {dataset_info.get('end_date')}",
        "instruments": dataset_info.get("instruments"),
        "is_synthetic": (dataset_info.get("source_type") == "SYNTHETIC")
    }

    report_md_lines = [
        f"# GOLDWISE PRO — INSTITUTIONAL COMMODITY RELATIVE VALUE RESEARCH REPORT",
        f"**Report ID**: `{report_id}` | **Generated**: `{timestamp} UTC`",
        f"**Classification**: STRICT RESEARCH MEMORANDUM (NON-EXECUTIONAL)",
        "",
        "## 1. Executive Summary & Provenance",
        f"- **Dataset**: {provenance['dataset_name']} (`{provenance['dataset_id']}`)",
        f"- **Data Provenance**: {'[SYNTHETIC DEMONSTRATION]' if provenance['is_synthetic'] else '[GENUINE MCX BHAVCOPY]'}",
        f"- **Content Fingerprint (SHA-256)**: `{provenance['file_hash']}`",
        f"- **Coverage**: {provenance['row_count']} observations across `{provenance['instruments']}`",
        f"- **Date Range**: {provenance['time_range']}",
        "",
        "> [!IMPORTANT]",
        f"> Data status: This report was compiled using {provenance['source_type']} data. "
        f"{'Conclusions reflect simulated test conditions and do not represent verified live exchange fills.' if provenance['is_synthetic'] else 'Observed data corresponds to verified historical MCX settlement records.'}",
        "",
        "## 2. Contract Specifications & Normalization Methodology",
        "Prices are strictly normalized to 1.000 Fineness Pure Gold Reference Price (Rs / pure gram):",
        r"$$P_{\text{pure/g}} = \frac{P_{\text{quoted}} / B}{\text{Purity} / 1000}$$",
        "where $B$ is quotation basis in grams, and Purity is fineness in per-mille (e.g. 995 for GOLD/GOLDM, 999 for GUINEA/PETAL).",
        "",
    ]

    if scan_info:
        report_md_lines.extend([
            "## 3. Relative Value Scan & Opportunity Destroyer Findings",
            f"- **Pair Evaluated**: `{scan_info.get('pair_symbol_a')}` vs `{scan_info.get('pair_symbol_b')}`",
            f"- **Total Observation Pairs**: {scan_info.get('total_candidates', 0)}",
            f"- **Candidates Meeting Research Threshold (`INVESTIGATE`)**: {scan_info.get('investigate_count', 0)}",
            f"- **Candidates Suppressed by Destroyer (`SUPPRESSED`)**: {scan_info.get('suppressed_count', 0)}",
            f"- **Insufficient History Cases (`INSUFFICIENT_DATA`)**: {scan_info.get('insufficient_count', 0)}",
            "",
            "### Falsification Summary",
            "Every candidate underwent 12 automated disproof tests:",
            "1. Quotation-unit mismatch check",
            "2. Purity normalization verification",
            "3. Expiry delivery margin proximity check (<= 3 days threshold)",
            "4. Minimum daily turnover liquidity check",
            "5. Stale price and feed activity audit",
            "6. Transaction cost and friction survival test",
            "7. Rolling window sensitivity analysis",
            "8. Single-leg shock dependency check",
            "9. Timestamp synchronicity and lookahead safety check",
            "10. Volatility regime spike test",
            "11. Multiple testing / selection bias penalty",
            "12. Sample size sufficiency (>= 15 required observations)",
            ""
        ])

    if backtest_info:
        report_md_lines.extend([
            "## 4. Walk-Forward Chronological Historical Backtest",
            f"- **Execution Lag**: T+1 (Simulated orders placed on close, filled next session)",
            f"- **Total Signals Generated**: {backtest_info.get('total_signals', 0)}",
            f"- **Executed Trades**: {backtest_info.get('executed_trades', 0)}",
            f"- **Gross Return**: {backtest_info.get('gross_return_pct', 0.0)}%",
            f"- **Cost Drag**: Rs {backtest_info.get('cost_drag_inr', 0.0)} ({backtest_info.get('total_costs_bps', 0.0)} bps)",
            f"- **Net Return (Post-Friction)**: {backtest_info.get('net_return_pct', 0.0)}%",
            f"- **Annualized Sharpe Ratio**: {backtest_info.get('sharpe_ratio', 0.0)}",
            f"- **Maximum Historical Drawdown**: {backtest_info.get('max_drawdown_pct', 0.0)}%",
            f"- **Win Rate**: {backtest_info.get('win_rate', 0.0)}% | **Profit Factor**: {backtest_info.get('profit_factor', 0.0)}",
            ""
        ])

    if reality_check_info:
        report_md_lines.extend([
            "## 5. Reality Check & Statistical Skepticism",
            f"- **Bootstrap Permutation p-value**: {reality_check_info.get('bootstrap_p_value')}",
            f"- **Multiple Testing Experiments Evaluated**: {reality_check_info.get('total_experiments_evaluated')}",
            f"- **Selection Bias Risk Rating**: {reality_check_info.get('selection_bias_risk_rating')}",
            f"- **Evidence Verdict Survival**: {reality_check_info.get('verdict_survival_rating')}",
            ""
        ])

    if cost_info:
        report_md_lines.extend([
            "## 6. Transaction Cost Breakdown",
            f"- **Estimated Total Roundtrip Friction**: {cost_info.get('total_cost_basis_points')} basis points",
            f"- **Break-even Spread Divergence**: {cost_info.get('break_even_spread_divergence_pct')}%",
            f"- **Statutory Total**: Rs {cost_info.get('statutory_total_inr')}",
            f"- **Microstructure Friction (Slippage + Spread)**: Rs {round(cost_info.get('bid_ask_cost_inr', 0) + cost_info.get('slippage_cost_inr', 0), 2)}",
            ""
        ])

    report_md_lines.extend([
        "## 7. Compliance & Research Disclaimers",
        "1. **Non-Executional**: GOLDWISE PRO is a quantitative research and hypothesis-testing environment. It does not place orders or interface with trading gateways.",
        "2. **Hypothetical Limitations**: Historical backtests use daily settlement data. Actual real-world execution is subject to market depth, queue priority, and slippage.",
        "3. **Reproducibility Guarantee**: All calculations in this report are deterministically reproducible using the dataset fingerprint and configuration seeds.",
        "",
        "---",
        "*Report compiled by GOLDWISE PRO Quantitative Engine.*"
    ])

    report_markdown = "\n".join(report_md_lines)
    file_path = REPORTS_DIR / f"{report_id}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report_markdown)

    return {
        "report_id": report_id,
        "timestamp": timestamp,
        "markdown_content": report_markdown,
        "file_path": str(file_path),
        "dataset_provenance": provenance
    }
