from typing import Dict, Any, Optional
from app.quant.contracts import get_contract_spec

def compute_pure_gold_price(
    quoted_price: float,
    quotation_basis_grams: float,
    purity_per_mille: float
) -> float:
    """
    Computes pure gold equivalent price per gram (1.000 fineness).
    Formula:
      price_per_gram_alloy = quoted_price / quotation_basis_grams
      purity_fraction = purity_per_mille / 1000.0
      pure_gold_price_per_gram = price_per_gram_alloy / purity_fraction
    """
    if quotation_basis_grams <= 0:
        raise ValueError(f"Quotation basis grams must be > 0, got {quotation_basis_grams}")
    if purity_per_mille <= 0 or purity_per_mille > 1000:
        raise ValueError(f"Purity must be in (0, 1000], got {purity_per_mille}")

    price_per_gram_alloy = quoted_price / quotation_basis_grams
    purity_fraction = purity_per_mille / 1000.0
    return price_per_gram_alloy / purity_fraction

def normalize_price_by_symbol(symbol: str, quoted_price: float) -> Dict[str, Any]:
    spec = get_contract_spec(symbol)
    if not spec:
        raise ValueError(f"Contract specification not found for symbol '{symbol}'")

    price_per_gram_alloy = quoted_price / spec.quotation_basis_grams
    purity_fraction = spec.purity_per_mille / 1000.0
    pure_per_gram = price_per_gram_alloy / purity_fraction
    pure_per_10g = pure_per_gram * 10.0

    formula_latex = (
        r"P_{\text{pure/gram}} = \frac{P_{\text{quoted}} / "
        + f"{spec.quotation_basis_grams}"
        + r"}{"
        + f"{spec.purity_per_mille}"
        + r" / 1000}"
    )

    return {
        "symbol": spec.symbol,
        "contract_name": spec.name,
        "quoted_price": quoted_price,
        "quotation_basis_grams": spec.quotation_basis_grams,
        "quoted_price_per_gram_alloy": round(price_per_gram_alloy, 4),
        "purity_per_mille": spec.purity_per_mille,
        "purity_fraction": purity_fraction,
        "normalized_pure_gold_per_gram": round(pure_per_gram, 4),
        "normalized_pure_gold_per_10g": round(pure_per_10g, 2),
        "formula_latex": formula_latex,
        "source_status": spec.source_verification_status,
        "tick_size": spec.tick_size,
    }

def calculate_spread(
    normalized_price_a: float,
    normalized_price_b: float
) -> Dict[str, float]:
    """
    Computes absolute pure-gold spread and percentage spread relative to benchmark B.
    """
    if normalized_price_b == 0:
        raise ValueError("Benchmark price B cannot be zero")
    raw_spread = normalized_price_a - normalized_price_b
    percentage_spread = (raw_spread / normalized_price_b) * 100.0
    spread_bps = percentage_spread * 100.0
    return {
        "raw_spread": round(raw_spread, 4),
        "percentage_spread": round(percentage_spread, 4),
        "spread_bps": round(spread_bps, 2)
    }
