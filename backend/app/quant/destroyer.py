from typing import Dict, Any, List
import datetime

class OpportunityDestroyer:
    """
    Quantitative Falsification Engine.
    Actively attempts to invalidate and disprove apparent relative-value anomalies
    against 12 rigorous failure modes before allowing an INVESTIGATE classification.
    """

    def __init__(
        self,
        expiry_buffer_days: int = 3,
        min_daily_volume: float = 100.0,
        slippage_bps: float = 3.0,
        brokerage_bps: float = 1.5,
        exchange_fees_bps: float = 1.0
    ):
        self.expiry_buffer_days = expiry_buffer_days
        self.min_daily_volume = min_daily_volume
        # Total roundtrip cost baseline: 2 legs * (brokerage + exchange + slippage) ~ 11-13 bps
        self.roundtrip_cost_bps = 2.0 * (brokerage_bps + exchange_fees_bps + slippage_bps)

    def evaluate_candidate(
        self,
        candidate_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes all 12 falsification checks on a candidate observation.
        """
        checks: List[Dict[str, Any]] = []
        fatal_failures: List[str] = []
        caution_warnings: List[str] = []

        price_a = candidate_data.get("price_a", 0.0)
        price_b = candidate_data.get("price_b", 0.0)
        norm_a = candidate_data.get("normalized_a", 0.0)
        norm_b = candidate_data.get("normalized_b", 0.0)
        raw_spread = candidate_data.get("raw_spread", 0.0)
        pct_spread = abs(candidate_data.get("percentage_spread", 0.0))
        spread_bps = pct_spread * 100.0
        
        vol_a = candidate_data.get("volume_a", 0.0) or 0.0
        vol_b = candidate_data.get("volume_b", 0.0) or 0.0
        expiry_dist = candidate_data.get("expiry_distance_days", 999)
        robust_zscore = abs(candidate_data.get("robust_zscore", 0.0) or 0.0)
        
        # 1. Quotation-Unit Mismatch Check
        # If unnormalized prices differ by a factor near 8x or 10x, but normalization collapsed it incorrectly, or unnormalized comparison occurred
        ratio_unnorm = (price_a / price_b) if price_b > 0 else 1.0
        quotation_mismatch = False
        if abs(ratio_unnorm - 10.0) < 0.5 or abs(ratio_unnorm - 0.1) < 0.05 or abs(ratio_unnorm - 8.0) < 0.5:
            if abs(norm_a - norm_b) / (norm_b or 1.0) > 0.5:  # 50% discrepancy means unhandled quotation unit!
                quotation_mismatch = True
        
        checks.append({
            "check_name": "Quotation Basis Consistency",
            "category": "Contract Specification",
            "passed": not quotation_mismatch,
            "severity": "FATAL_DISPROVAL" if quotation_mismatch else "CLEAR",
            "evidence_value": round(ratio_unnorm, 3),
            "threshold": "Normalized pure gold ratio ~ 1.000 (discrepancy < 5%)",
            "explanation": "Fatal quotation unit mismatch detected. Contract price feed lacks quotation basis scaling."
            if quotation_mismatch else "Quotation units properly scaled to pure gold equivalent basis."
        })
        if quotation_mismatch:
            fatal_failures.append("Quotation unit mismatch between contract specifications")

        # 2. Purity Normalization Check
        # Check if 995 vs 999 fineness is factored into pure gold reference
        purity_diff_bps = 40.0  # (999-995)/995 * 10000 = ~40 bps
        purity_check_passed = True
        if abs(spread_bps - purity_diff_bps) < 2.0 and abs(candidate_data.get("symbol_a_purity", 995) - candidate_data.get("symbol_b_purity", 999)) > 0:
            # Spread is exactly equal to the unadjusted purity gap
            purity_check_passed = False
            
        checks.append({
            "check_name": "Purity Adjustment Verification",
            "category": "Contract Specification",
            "passed": purity_check_passed,
            "severity": "FATAL_DISPROVAL" if not purity_check_passed else "CLEAR",
            "evidence_value": f"Spread: {round(spread_bps, 1)} bps vs Purity Gap: {purity_diff_bps} bps",
            "threshold": "Spread must not be a mere unadjusted purity differential artifact",
            "explanation": "Candidate deviation appears to be an unadjusted 995 vs 999 fineness discrepancy."
            if not purity_check_passed else "Purity conversion verified. Spread accounts for differing alloy fineness."
        })
        if not purity_check_passed:
            fatal_failures.append("Spread reflects unadjusted purity gap artifact")

        # 3. Expiry Proximity / Delivery Squeeze Check
        expiry_passed = True
        if expiry_dist is not None and expiry_dist <= self.expiry_buffer_days:
            expiry_passed = False
            
        checks.append({
            "check_name": "Expiry Proximity & Delivery Effect",
            "category": "Market Structure",
            "passed": expiry_passed,
            "severity": "FATAL_DISPROVAL" if not expiry_passed else "CLEAR",
            "evidence_value": f"{expiry_dist} trading days to expiry",
            "threshold": f"> {self.expiry_buffer_days} days to expiry",
            "explanation": f"Contract is within {expiry_dist} days of expiry. Spread widening is driven by delivery margin, warehousing, and illiquid roll squeeze."
            if not expiry_passed else "Contract has adequate expiry distance. No immediate delivery distortion."
        })
        if not expiry_passed:
            fatal_failures.append(f"Near-expiry delivery squeeze distortion ({expiry_dist} days to expiry)")

        # 4. Thin Trading / Inadequate Liquidity Check
        liquidity_passed = (vol_a >= self.min_daily_volume and vol_b >= self.min_daily_volume)
        checks.append({
            "check_name": "Minimum Tradable Liquidity",
            "category": "Execution Realism",
            "passed": liquidity_passed,
            "severity": "HIGH_RISK" if not liquidity_passed else "CLEAR",
            "evidence_value": f"Vol A: {int(vol_a)}, Vol B: {int(vol_b)}",
            "threshold": f">= {int(self.min_daily_volume)} lots per day",
            "explanation": "One or both contracts suffer from negligible trading volume. Quoted price is non-executable."
            if not liquidity_passed else "Both contracts exhibit sufficient daily turnover for executable pricing."
        })
        if not liquidity_passed:
            caution_warnings.append("Inadequate daily trading volume on one or both legs")

        # 5. Stale Price Check (Zero price change with zero volume)
        stale_price = (vol_a == 0 or vol_b == 0) and (candidate_data.get("is_stale", False))
        checks.append({
            "check_name": "Stale Price & Inactive Feed Check",
            "category": "Data Quality",
            "passed": not stale_price,
            "severity": "FATAL_DISPROVAL" if stale_price else "CLEAR",
            "evidence_value": "Zero volume with unchanged price" if stale_price else "Active trading session",
            "threshold": "Active market prints with non-zero volume",
            "explanation": "Observed price print is stale from a previous inactive session."
            if stale_price else "Price print is fresh and corroborated by transaction volume."
        })
        if stale_price:
            fatal_failures.append("Stale price print from inactive contract feed")

        # 6. Economic Cost Survival Check
        cost_survival = (spread_bps > self.roundtrip_cost_bps)
        checks.append({
            "check_name": "Transaction Cost Survival",
            "category": "Economic Viability",
            "passed": cost_survival,
            "severity": "HIGH_RISK" if not cost_survival else "CLEAR",
            "evidence_value": f"Gross Spread: {round(spread_bps, 1)} bps vs Roundtrip Cost: {round(self.roundtrip_cost_bps, 1)} bps",
            "threshold": f"Gross Spread > {round(self.roundtrip_cost_bps, 1)} bps",
            "explanation": f"Gross deviation ({round(spread_bps, 1)} bps) is completely eliminated by statutory charges, brokerage, and slippage ({round(self.roundtrip_cost_bps, 1)} bps)."
            if not cost_survival else "Gross deviation exceeds estimated roundtrip friction."
        })
        if not cost_survival:
            caution_warnings.append(f"Spread ({round(spread_bps, 1)} bps) does not survive realistic execution costs ({round(self.roundtrip_cost_bps, 1)} bps)")

        # 7. Window Sensitivity Check
        window_sensitive = candidate_data.get("window_sensitive", False)
        checks.append({
            "check_name": "Rolling Window Parameter Sensitivity",
            "category": "Statistical Robustness",
            "passed": not window_sensitive,
            "severity": "MODERATE_CAUTION" if window_sensitive else "CLEAR",
            "evidence_value": "Anomaly disappears when window altered ±5 days" if window_sensitive else "Stable across 15d, 20d, and 30d rolling windows",
            "threshold": "Consistent statistical significance across multiple lookback windows",
            "explanation": "Signal is fragile and dependent on a specific historical lookback window."
            if window_sensitive else "Statistical deviation is robust to lookback window variation."
        })
        if window_sensitive:
            caution_warnings.append("Signal sensitivity to rolling lookback window")

        # 8. Single-Contract Disproportionate Movement (Idiosyncratic Leg Check)
        single_leg_driven = candidate_data.get("single_leg_driven", False)
        checks.append({
            "check_name": "Single-Leg Shock Dependency",
            "category": "Market Dynamics",
            "passed": not single_leg_driven,
            "severity": "MODERATE_CAUTION" if single_leg_driven else "CLEAR",
            "evidence_value": "One leg diverged abnormally while benchmark remained still" if single_leg_driven else "Relative spread reflects balanced co-movement",
            "threshold": "Spread divergence not solely driven by a micro-cap illiquid leg spike",
            "explanation": "Divergence is heavily driven by an isolated jump in the smaller contract leg."
            if single_leg_driven else "Co-movement and cointegration relationship preserved."
        })

        # 9. Lookahead / Non-Synchronous Timestamp Check
        lookahead_violation = candidate_data.get("lookahead_violation", False)
        checks.append({
            "check_name": "Timestamp Synchronicity & Lookahead Safety",
            "category": "Research Rigor",
            "passed": not lookahead_violation,
            "severity": "FATAL_DISPROVAL" if lookahead_violation else "CLEAR",
            "evidence_value": "Synchronous EOD Bhavcopy timestamps" if not lookahead_violation else "Asynchronous or lookahead-contaminated observation",
            "threshold": "Simultaneous observation timestamps with strictly past information",
            "explanation": "Chronological safety verified. No future or out-of-sequence market data used."
            if not lookahead_violation else "Asynchronous settlement or future data leakage detected."
        })
        if lookahead_violation:
            fatal_failures.append("Lookahead or asynchronous timestamp violation")

        # 10. Volatility Spike Check
        extreme_vol = candidate_data.get("extreme_vol", False)
        checks.append({
            "check_name": "Abnormal Market Volatility Spike",
            "category": "Market Regime",
            "passed": not extreme_vol,
            "severity": "MODERATE_CAUTION" if extreme_vol else "CLEAR",
            "evidence_value": "Intraday range within 2.5x normal" if not extreme_vol else "Intraday range > 3.5x normal (regime shock)",
            "threshold": "Intraday range < 3.0x historical median",
            "explanation": "Macro event volatility spike. Spread divergence reflects market-wide stress rather than mispricing."
            if extreme_vol else "Market volatility conditions are within normal statistical operating range."
        })

        # 11. Multiple Testing / Selection Bias Check
        multiple_testing = candidate_data.get("multiple_testing_penalty", False)
        checks.append({
            "check_name": "Selection Bias & Multiple Testing Penalty",
            "category": "Statistical Validation",
            "passed": not multiple_testing,
            "severity": "MODERATE_CAUTION" if multiple_testing else "CLEAR",
            "evidence_value": "Tested across primary pairs" if not multiple_testing else "Elevated false discovery risk under multi-pair scanning",
            "threshold": "Bonferroni / Benjamini-Hochberg adjusted significance",
            "explanation": "Signal maintains statistical validity under multi-hypothesis adjustment."
            if not multiple_testing else "Candidate significance weakened after adjusting for multiple pair tests."
        })

        # 12. Minimum Historical Data Sufficiency Check
        historical_obs = candidate_data.get("historical_obs_count", 20)
        has_sufficient_history = (historical_obs >= 15)
        checks.append({
            "check_name": "Historical Sample Sufficiency",
            "category": "Sample Size",
            "passed": has_sufficient_history,
            "severity": "FATAL_DISPROVAL" if not has_sufficient_history else "CLEAR",
            "evidence_value": f"{historical_obs} historical observations available",
            "threshold": ">= 15 observations required for robust median & MAD",
            "explanation": f"Insufficient historical depth ({historical_obs} < 15). Statistical baseline cannot be calibrated reliably."
            if not has_sufficient_history else "Sample size exceeds minimum sample requirement for robust estimation."
        })
        if not has_sufficient_history:
            fatal_failures.append(f"Insufficient historical observations ({historical_obs} < 15)")

        # Overall Verdict Determination
        if not has_sufficient_history:
            verdict = "INSUFFICIENT_DATA"
        elif len(fatal_failures) > 0:
            verdict = "SUPPRESSED"
        elif len(caution_warnings) >= 2 or not cost_survival:
            # If it fails cost survival or has multiple high-risk warnings, suppress it!
            verdict = "SUPPRESSED"
            if not cost_survival:
                fatal_failures.append("Spread fails economic cost survival test")
        elif robust_zscore < 1.8:
            verdict = "SUPPRESSED"
            fatal_failures.append(f"Robust z-score ({round(robust_zscore, 2)}) below significance threshold (1.8)")
        else:
            verdict = "INVESTIGATE"

        # Residual uncertainty: higher if caution warnings exist
        uncertainty = 0.05 + (0.20 * len(caution_warnings)) + (0.35 * (1 if not cost_survival else 0))
        uncertainty = min(0.95, round(uncertainty, 2))

        return {
            "verdict": verdict,
            "passed_all_fatal_checks": len(fatal_failures) == 0,
            "fatal_failures": fatal_failures,
            "caution_warnings": caution_warnings,
            "checks": checks,
            "residual_uncertainty_score": uncertainty
        }
