from typing import Dict, Any, List

def calculate_mcx_transaction_costs(
    quoted_price_per_10g: float = 75000.0,
    contract_lot_grams: float = 100.0,  # e.g., GOLDM = 100g
    position_lots: int = 1,
    brokerage_bps: float = 1.5,
    exchange_fees_bps: float = 1.0,
    sebi_turnover_bps: float = 0.1,
    stamp_duty_bps: float = 0.2,
    gst_on_charges_pct: float = 18.0,
    bid_ask_half_spread_bps: float = 2.0,
    market_impact_bps: float = 1.0,
    slippage_bps: float = 1.5
) -> Dict[str, Any]:
    """
    Computes rigorous transaction cost breakdown for round-trip pair execution on MCX.
    Includes statutory charges, exchange fees, brokerage, GST, and execution market friction.
    """
    # Turnover per leg in INR
    # Price per gram = quoted_price_per_10g / 10.0
    price_per_gram = quoted_price_per_10g / 10.0
    single_leg_turnover = price_per_gram * contract_lot_grams * position_lots
    # A relative value pair trade involves 2 legs (Long Leg A, Short Leg B)
    # Entry round: 2 legs. Exit round: 2 legs. Total roundtrip volume = 4 * single_leg_turnover
    roundtrip_turnover = 4.0 * single_leg_turnover

    # 1. Brokerage
    brokerage = roundtrip_turnover * (brokerage_bps / 10000.0)

    # 2. Exchange turnover fees
    exchange_fees = roundtrip_turnover * (exchange_fees_bps / 10000.0)

    # 3. SEBI Turnover Charges
    sebi_charges = roundtrip_turnover * (sebi_turnover_bps / 10000.0)

    # 4. Stamp duty (applicable primarily on buy turnover on MCX)
    stamp_duty = (roundtrip_turnover * 0.5) * (stamp_duty_bps / 10000.0)

    # 5. GST (18% on brokerage + exchange fees)
    gst = (brokerage + exchange_fees) * (gst_on_charges_pct / 100.0)

    statutory_total = brokerage + exchange_fees + sebi_charges + stamp_duty + gst

    # Market Microstructure Friction
    # Bid-ask half-spread, market impact, and execution delay slippage (incurred on entry and exit across both legs)
    bid_ask_cost = roundtrip_turnover * (bid_ask_half_spread_bps / 10000.0)
    slippage_cost = roundtrip_turnover * (slippage_bps / 10000.0)
    market_impact_cost = roundtrip_turnover * (market_impact_bps / 10000.0)

    microstructure_total = bid_ask_cost + slippage_cost + market_impact_cost
    total_roundtrip_cost = statutory_total + microstructure_total

    # Cost in total basis points of total roundtrip turnover
    total_cost_bps = (total_roundtrip_cost / roundtrip_turnover) * 10000.0

    # Break-even spread divergence: The relative price spread must be at least this wide for net PnL to be > 0
    # Since roundtrip pairs have 2 legs, the required spread is:
    break_even_spread_pct = (total_roundtrip_cost / (2.0 * single_leg_turnover)) * 100.0

    # Breakdown percentages
    breakdown_pct = {
        "Brokerage": round((brokerage / total_roundtrip_cost) * 100.0, 1),
        "Exchange & Statutory Fees": round(((exchange_fees + sebi_charges + stamp_duty + gst) / total_roundtrip_cost) * 100.0, 1),
        "Bid-Ask Spread Friction": round((bid_ask_cost / total_roundtrip_cost) * 100.0, 1),
        "Slippage & Impact": round(((slippage_cost + market_impact_cost) / total_roundtrip_cost) * 100.0, 1)
    }

    # Sensitivity table: testing different slippage & market impact scenarios
    sensitivity = []
    for slip_mult in [0.5, 1.0, 1.5, 2.0, 3.0]:
        adj_slip = slippage_cost * slip_mult
        adj_impact = market_impact_cost * slip_mult
        adj_total = statutory_total + bid_ask_cost + adj_slip + adj_impact
        adj_breakeven_bps = (adj_total / (2.0 * single_leg_turnover)) * 10000.0
        sensitivity.append({
            "scenario": f"Slippage x{slip_mult}",
            "slippage_bps": round(slippage_bps * slip_mult, 1),
            "total_roundtrip_inr": round(adj_total, 2),
            "break_even_bps": round(adj_breakeven_bps, 1)
        })

    return {
        "turnover_inr": round(roundtrip_turnover, 2),
        "brokerage_inr": round(brokerage, 2),
        "exchange_fees_inr": round(exchange_fees, 2),
        "sebi_charges_inr": round(sebi_charges, 2),
        "stamp_duty_inr": round(stamp_duty, 2),
        "gst_inr": round(gst, 2),
        "statutory_total_inr": round(statutory_total, 2),
        "bid_ask_cost_inr": round(bid_ask_cost, 2),
        "slippage_cost_inr": round(slippage_cost, 2),
        "market_impact_cost_inr": round(market_impact_cost, 2),
        "total_roundtrip_cost_inr": round(total_roundtrip_cost, 2),
        "total_cost_basis_points": round(total_cost_bps, 2),
        "break_even_spread_divergence_pct": round(break_even_spread_pct, 3),
        "cost_breakdown_percentages": breakdown_pct,
        "sensitivity_table": sensitivity,
        "disclaimer": (
            "Hypothetical transaction cost model based on disclosed MCX statutory schedules and estimated friction. "
            "Actual executable fills depend on real-time market depth and order queuing."
        )
    }
