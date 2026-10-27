# GoldWise Pro — Quantitative Methodology & Mathematical Specifications

This document outlines the theoretical foundations, quantitative statistics, and algorithmic falsification methodology employed across the **GoldWise Pro** platform.

---

## 1. Commodity Relative-Value Principles

Derivatives pricing in physical precious metals differs fundamentally from equity index arbitrage:
1. **Physical Delivery Mechanics**: MCX gold contracts provide for compulsory physical delivery at designated exchange vaults (Ahmedabad, Mumbai, New Delhi). Contracts approaching physical delivery experience exponential margin increases (tender margins rising from ~10% to ~25%+).
2. **Purity Standard Heterogeneity**: Indian market participants trade both LBMA-standard 995 fineness bars (`GOLD`, `GOLDM`) and retail-oriented 999 fineness coins and petals (`GOLDGUINEA`, `GOLDPETAL`). Naive comparison without purity adjustment creates phantom arbitrage opportunities.
3. **Carry Cost & Storage**: Gold exhibits a non-zero convenience yield and safe-vault storage/insurance drag. Spreads between successive calendar expiries reflect domestic interest rates (MIFOR/MIBOR), storage costs, and import parity.

---

## 2. Robust Spread Statistics

Financial time series exhibit fat tails (leptokurtosis) and discontinuous jumps (e.g., geopolitical shocks, tariff announcements). Standard Gaussian estimators ($\mu, \sigma$) break down in the presence of even a single outlier.

GoldWise Pro utilizes **robust non-parametric statistics**:

### 2.1 Rolling Median & Median Absolute Deviation (MAD)
Given a rolling window of relative spreads $S = \{s_1, s_2, \dots, s_N\}$:

$$\text{Median}(S) = \text{med}(S)$$

$$\text{MAD}(S) = \text{med}\left( |s_i - \text{med}(S)| \right)$$

To achieve asymptotic consistency with the standard deviation under a Gaussian distribution, the MAD is scaled by the consistency constant $k \approx 1.4826$:

$$\sigma_{\text{robust}} = 1.4826 \times \text{MAD}(S)$$

### 2.2 Robust Z-Score
The robust z-score measures deviation in units of scaled MAD:

$$Z_{\text{robust}} = \frac{s_t - \text{med}(S)}{\sigma_{\text{robust}}}$$

- Breakdown Point: Standard deviation has a breakdown point of $0\%$ (a single infinite outlier corrupts the estimate). In contrast, the median and MAD possess a **$50\%$ breakdown point**, remaining stable even if up to half the sample is contaminated.

---

## 3. Statutory Cost & Friction Breakdown

Every relative-value trade requires executing opposite legs simultaneously (e.g., Long `GOLDM` vs Short `GOLD`). The net roundtrip trading friction in basis points ($F_{\text{bps}}$) is modeled as:

$$F_{\text{bps}} = 2 \times \left( B_{\text{bps}} + E_{\text{bps}} \times (1 + \text{GST}) + C_{\text{bps}} + S_{\text{bps}} \right)$$

Where:
- $B_{\text{bps}}$: Brokerage fee ($\sim 1.5$ bps per leg).
- $E_{\text{bps}}$: MCX Exchange Turnover fee ($\sim 1.0$ bps per leg).
- $\text{GST}$: Goods & Services Tax on brokerage and exchange fees ($18\%$).
- $C_{\text{bps}}$: Commodities Transaction Tax (CTT) on sell leg ($0.0125\% = 1.25$ bps).
- $S_{\text{bps}}$: Slippage buffer ($1.5$ to $5.0$ bps per leg depending on contract liquidity).

### Net Actionable Spread
$$\text{Net Spread}_{\text{bps}} = |\Delta_{\text{bps}}| - F_{\text{bps}}$$

If $\text{Net Spread}_{\text{bps}} \le 0$, the anomaly is strictly non-actionable regardless of how extreme the nominal robust z-score appears.

---

## 4. Opportunity Destroyer: The 12 Falsification Tests

| # | Test Name | Falsification Trigger | Rationale |
|---|---|---|---|
| 1 | **Unit & Purity Mismatch** | Purity delta unaccounted for | Prevents comparing 995 fineness against 999 fineness directly. |
| 2 | **Tick Size Granularity** | Raw spread $< 2 \times \text{Tick}$ | Apparent spread is smaller than minimum exchange order book step. |
| 3 | **Liquidity Gate** | $\text{Volume} < 10 \text{ lots}$ or $\text{OI} < 25$ | Disregards ghost quotes in illiquid far-month contracts. |
| 4 | **Bid-Ask Cross Penalty** | Half-spread $> 0.5 \times \text{Net Spread}$ | Simulates executing against market orders across the bid-ask queue. |
| 5 | **Expiry Cliff** | $\text{Days to Expiry} \le 3$ | Severe delivery roll-risk and vanishing depth near contract expiry. |
| 6 | **Tender Margin Window** | Within 5 days of expiry tender | Exchange imposes 5% daily escalating delivery margins. |
| 7 | **Statutory Friction Gate** | Gross Spread $\le$ Total statutory fees | Trading friction completely consumes the gross price discrepancy. |
| 8 | **Cost-of-Carry Barrier** | Spread accounted by interest rate | Basis differential is justified by financing differential between expiries. |
| 9 | **Execution Delay (T+1)** | Spread collapses on day $t+1$ | Anomaly does not persist long enough to enter with realistic latency. |
| 10 | **Half-Life Degradation** | Reversion half-life $> 30$ days | Spread exhibits non-stationary wandering rather than mean-reverting basis. |
| 11 | **Structural Break (CUSUM)** | CUSUM test statistic $> 2.5$ | Rejection of structural stationarity (e.g. import tariff revision). |
| 12 | **ML Ensemble Consensus** | ML anomaly score $< 0.50$ | Statistical outlier is not confirmed by non-linear subspace isolation. |

---

## 5. Walk-Forward Backtesting Invariants

To avoid the prevalent backtesting pitfalls identified in academic literature (Bailey, Borwein, López de Prado, Zhu, 2014):

1. **Strict Chronological Sequencing**: No data from $t \ge T$ is accessible when evaluating decisions at time $T$.
2. **T+1 Execution Delay**: Signals generated at close of trading day $T$ enter positions strictly at the close of trading day $T+1$. Synchronous same-day execution is strictly disallowed.
3. **Execution Delay Exit**: Exits triggered at day $T_e$ execute at day $T_e+1$.
4. **Roundtrip Friction Deduction**: Every trade entry and exit deducts statutory exchange fees, brokerage, GST, and user-specified slippage.
5. **Drawdown Attribution**: Peak-to-trough drawdowns are computed continuously on post-cost equity.
