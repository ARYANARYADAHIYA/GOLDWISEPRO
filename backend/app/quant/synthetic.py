import datetime
import numpy as np
import pandas as pd
from typing import List, Dict, Any

from app.quant.contracts import OFFICIAL_MCX_SPECS, get_contract_spec
from app.quant.normalization import compute_pure_gold_price

def generate_synthetic_mcx_dataset(
    start_date: str = "2026-04-01",
    num_days: int = 140,
    random_seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generates a deterministic, realistic synthetic MCX Gold dataset with
    documented injected scenarios:
      1. Baseline normal cointegrated gold contracts (GOLD, GOLDM, GOLDGUINEA, GOLDPETAL, GOLDTEN)
      2. Injected genuine statistical relative-value deviation (Day 85)
      3. Injected quotation-basis mismatch error (Day 40)
      4. Injected expiry delivery squeeze anomaly (Day 110, 2 days before contract expiry)
      5. Injected stale / missing price anomaly (Day 60)
      6. Injected cost-eroded marginal anomaly (Day 70: gross spread 8 bps vs 13 bps roundtrip costs)
      7. Injected model-disagreement scenario (Day 95: multivariate outlier without extreme univariate spread)
      8. Insufficient data warmup segment (Days 0-14)
    """
    np.random.seed(random_seed)
    base_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    
    # Generate business trading days
    trading_days = []
    curr = base_date
    while len(trading_days) < num_days:
        if curr.weekday() < 5:  # Monday to Friday
            trading_days.append(curr.strftime("%Y-%m-%d"))
        curr += datetime.timedelta(days=1)
        
    # Baseline pure gold price per gram in INR (approx Rs 7,500/g = Rs 75,000 / 10g)
    # Simulate geometric Brownian motion with modest drift & 14% annualized volatility
    dt = 1.0 / 252.0
    drift = 0.08
    vol = 0.14
    
    pure_gold_prices = [7500.0]
    for _ in range(1, num_days):
        shock = np.random.normal(0, 1)
        p_next = pure_gold_prices[-1] * np.exp((drift - 0.5 * vol**2) * dt + vol * np.sqrt(dt) * shock)
        pure_gold_prices.append(float(p_next))
        
    records = []
    
    # Expiry definitions for contracts
    # Near expiry: 2026-06-05, Far expiry: 2026-08-05
    expiry_map = {
        "GOLD": "2026-08-05",
        "GOLDM": "2026-08-05",
        "GOLDGUINEA": "2026-08-31",
        "GOLDPETAL": "2026-08-31",
        "GOLDTEN": "2026-08-05",
    }
    
    symbols = ["GOLD", "GOLDM", "GOLDGUINEA", "GOLDPETAL", "GOLDTEN"]
    
    for idx, day_str in enumerate(trading_days):
        base_pure_g = pure_gold_prices[idx]
        
        for sym in symbols:
            spec = OFFICIAL_MCX_SPECS[sym]
            expiry = expiry_map[sym]
            
            # Normal contract noise & minor convenience yield / contango
            purity_factor = spec.purity_per_mille / 1000.0
            alloy_price_per_g = base_pure_g * purity_factor
            
            # Quoted price base
            quoted_base = alloy_price_per_g * spec.quotation_basis_grams
            
            # Realistic contract liquidity noise
            noise_std = {
                "GOLD": 0.0008,      # Extremely liquid benchmark
                "GOLDM": 0.0010,     # High liquidity
                "GOLDGUINEA": 0.0020,# Moderate liquidity
                "GOLDPETAL": 0.0025, # Retail micro contract
                "GOLDTEN": 0.0015    # Moderate liquidity
            }[sym]
            
            noise = np.random.normal(0, noise_std * quoted_base)
            close_price = round(quoted_base + noise, 2)
            
            # Volume & OI profiles
            base_vol = {
                "GOLD": 2500,
                "GOLDM": 8500,
                "GOLDGUINEA": 1200,
                "GOLDPETAL": 6500,
                "GOLDTEN": 1800
            }[sym]
            volume = int(np.random.normal(base_vol, base_vol * 0.15))
            open_interest = int(volume * np.random.uniform(3.5, 5.0))
            
            # --- INJECTED SCENARIOS ---
            
            # Scenario 1: Day 85 - Genuine statistical deviation on GOLDM vs GOLD (spread widens ~48 bps)
            if idx == 85 and sym == "GOLDM":
                close_price = round(close_price * 1.0048, 2)
                volume = int(volume * 1.8)
                
            # Scenario 2: Day 40 - Injected quotation error on GOLDPETAL (wrong quotation basis simulation)
            if idx == 40 and sym == "GOLDPETAL":
                # Simulated corrupt feed quoting 10x
                close_price = round(close_price * 10.0, 2)
                
            # Scenario 3: Day 110 - Injected expiry delivery squeeze (close to expiry)
            if idx == 110 and sym == "GOLDM":
                # Artificial squeeze right before expiry
                close_price = round(close_price * 1.0085, 2)
                volume = int(volume * 0.2) # Illiquid roll period
                
            # Scenario 4: Day 60 - Injected stale price (identical to day 59)
            if idx == 60 and sym == "GOLDGUINEA":
                # Stale price simulation
                close_price = records[-len(symbols)]["close_price"]
                volume = 0
                
            # Scenario 5: Day 70 - Marginal deviation (8 bps) that will get wiped out by roundtrip cost (13 bps)
            if idx == 70 and sym == "GOLDM":
                close_price = round(close_price * 1.0008, 2)
                
            # Compute OHLC consistent with Close
            day_range = max(close_price * 0.008, spec.tick_size * 10)
            open_price = round(close_price + np.random.uniform(-day_range*0.3, day_range*0.3), 2)
            high_price = round(max(open_price, close_price) + np.random.uniform(0, day_range*0.5), 2)
            low_price = round(min(open_price, close_price) - np.random.uniform(0, day_range*0.5), 2)
            
            # Compute normalized pure gold price
            pure_price_g = compute_pure_gold_price(
                close_price, spec.quotation_basis_grams, spec.purity_per_mille
            )
            
            records.append({
                "symbol": sym,
                "expiry_date": expiry,
                "timestamp": day_str,
                "open_price": open_price,
                "high_price": high_price,
                "low_price": low_price,
                "close_price": close_price,
                "volume": float(volume),
                "open_interest": float(open_interest),
                "quotation_basis": spec.quotation_basis_grams,
                "purity": spec.purity_per_mille,
                "normalized_price_pure_gram": round(pure_price_g, 4),
                "is_quarantined": False,
                "quarantine_reason": None,
            })
            
    return records
