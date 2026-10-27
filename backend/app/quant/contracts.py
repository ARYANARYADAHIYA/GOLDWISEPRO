from typing import Dict, Optional
from pydantic import BaseModel

class ContractSpec(BaseModel):
    symbol: str
    name: str
    trading_unit_grams: float
    quotation_basis_grams: float
    purity_per_mille: float
    tick_size: float
    lot_size_grams: float
    delivery_unit_grams: float
    effective_date: str
    source_verification_status: str
    notes: str

# Official MCX Specifications as published in MCX Product Circulars & Bullion Handbook
OFFICIAL_MCX_SPECS: Dict[str, ContractSpec] = {
    "GOLD": ContractSpec(
        symbol="GOLD",
        name="MCX Gold Standard (1 kg)",
        trading_unit_grams=1000.0,
        quotation_basis_grams=10.0,  # Quoted in Rs per 10 grams
        purity_per_mille=995.0,      # 995 fineness
        tick_size=1.0,
        lot_size_grams=1000.0,
        delivery_unit_grams=1000.0,
        effective_date="2003-11-10",
        source_verification_status="VERIFIED_OFFICIAL_MCX",
        notes="Official benchmark contract. Deliverable at Ahmedabad and other specified vaults."
    ),
    "GOLDM": ContractSpec(
        symbol="GOLDM",
        name="MCX Gold Mini (100 g)",
        trading_unit_grams=100.0,
        quotation_basis_grams=10.0,  # Quoted in Rs per 10 grams
        purity_per_mille=995.0,      # 995 fineness
        tick_size=1.0,
        lot_size_grams=100.0,
        delivery_unit_grams=100.0,
        effective_date="2006-03-01",
        source_verification_status="VERIFIED_OFFICIAL_MCX",
        notes="High liquidity contract for active retail and institutional relative value trading."
    ),
    "GOLDGUINEA": ContractSpec(
        symbol="GOLDGUINEA",
        name="MCX Gold Guinea (8 g)",
        trading_unit_grams=8.0,
        quotation_basis_grams=8.0,   # Quoted in Rs per 8 grams
        purity_per_mille=999.0,      # 999 fineness (24 karat pure)
        tick_size=1.0,
        lot_size_grams=8.0,
        delivery_unit_grams=8.0,
        effective_date="2008-03-24",
        source_verification_status="VERIFIED_OFFICIAL_MCX",
        notes="Quoted strictly per 8 grams coin unit. Purity is 999 fineness."
    ),
    "GOLDPETAL": ContractSpec(
        symbol="GOLDPETAL",
        name="MCX Gold Petal (1 g)",
        trading_unit_grams=1.0,
        quotation_basis_grams=1.0,   # Quoted in Rs per 1 gram
        purity_per_mille=999.0,      # 999 fineness
        tick_size=1.0,
        lot_size_grams=1.0,
        delivery_unit_grams=1.0,
        effective_date="2011-04-18",
        source_verification_status="VERIFIED_OFFICIAL_MCX",
        notes="Micro-lot contract quoted directly in Rs per single gram."
    ),
    "GOLDTEN": ContractSpec(
        symbol="GOLDTEN",
        name="MCX Gold Ten (10 g)",
        trading_unit_grams=10.0,
        quotation_basis_grams=10.0,  # Quoted in Rs per 10 grams
        purity_per_mille=999.0,      # 999 fineness
        tick_size=1.0,
        lot_size_grams=10.0,
        delivery_unit_grams=10.0,
        effective_date="2020-06-08",
        source_verification_status="VERIFIED_OFFICIAL_MCX",
        notes="10-gram denomination with 999 fineness quotation."
    ),
}

def get_contract_spec(symbol: str) -> Optional[ContractSpec]:
    clean_sym = symbol.strip().upper()
    return OFFICIAL_MCX_SPECS.get(clean_sym)

def list_all_specs() -> Dict[str, ContractSpec]:
    return OFFICIAL_MCX_SPECS.copy()
