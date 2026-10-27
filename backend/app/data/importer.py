import io
import re
import hashlib
import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

from app.quant.contracts import get_contract_spec
from app.quant.normalization import compute_pure_gold_price

# Known column synonyms in MCX Bhavcopy / CSV / Excel exports
COLUMN_SYNONYMS = {
    "symbol": ["symbol", "commodity", "inst_name", "contract", "instrument", "underlying"],
    "instrument_name": ["instrument", "instrument_name", "inst_name", "instrumentname", "inst type", "inst_type"],
    "option_type": ["option_type", "opt_type", "option type", "opttype", "option"],
    "strike_price": ["strike_price", "strike", "strikeprice", "strike price"],
    "expiry_date": ["expiry", "expiry_date", "exp_date", "expirydate", "maturity", "expiry date", "contract expiry"],
    "timestamp": ["date", "timestamp", "trade_date", "tradedate", "traded_date", "trade date", "datetime"],
    "open_price": ["open", "open_price", "openprice", "open price"],
    "high_price": ["high", "high_price", "highprice", "high price"],
    "low_price": ["low", "low_price", "lowprice", "low price"],
    "close_price": ["close", "close_price", "closeprice", "settlement_price", "settle_price", "settlementprice", "last_price", "ltp", "close price"],
    "previous_close": ["previous_close", "prev_close", "prevclose", "previous close", "prev close", "prev_settle_price", "prev. close", "pc"],
    "volume": ["volume", "traded_qty", "vol", "traded_contracts", "volume_lots", "contracts", "contracts_traded", "volume (lots)", "qty"],
    "turnover": ["turnover", "value", "turnover_lakhs", "traded_value", "value (lacs)", "turnover (lacs)", "turnover_inr", "value (rs. in lakhs)", "turnover (rs. in lakhs)"],
    "open_interest": ["open_interest", "oi", "openinterest", "open_int", "open interest"]
}

MONTH_MAP = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
    "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
}

def parse_mcx_date_str(date_str: Any, preferred_format: Optional[str] = None) -> Tuple[Optional[str], bool]:
    """
    Parses date string safely into standard YYYY-MM-DD.
    Detects ambiguity (e.g. 05/06/2026).
    Returns (parsed_date_iso, is_ambiguous).
    """
    if pd.isna(date_str):
        return None, False

    if isinstance(date_str, (datetime.datetime, datetime.date, pd.Timestamp)):
        return date_str.strftime("%Y-%m-%d"), False

    clean = str(date_str).strip()
    if not clean or clean.lower() in ("nan", "none", "null", "nat"):
        return None, False

    # Check compact MCX format like 05AUG2026 or 05-AUG-2026 or 05-Aug-26
    compact_match = re.match(r"^(\d{1,2})[-/]?([A-Za-z]{3})[-/]?(\d{2,4})$", clean)
    if compact_match:
        day, mon_str, year_str = compact_match.groups()
        mon = MONTH_MAP.get(mon_str.upper())
        if mon:
            year = int(year_str)
            if year < 100:
                year += 2000
            return f"{year:04d}-{mon}-{int(day):02d}", False

    # Check ISO format YYYY-MM-DD
    iso_match = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})", clean)
    if iso_match:
        y, m, d = iso_match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}", False

    # Check slash or dash format DD/MM/YYYY vs MM/DD/YYYY
    slash_match = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})$", clean)
    if slash_match:
        p1, p2, year_str = slash_match.groups()
        v1, v2 = int(p1), int(p2)
        year = int(year_str)
        if year < 100:
            year += 2000
        
        # If one number is > 12, it must be the day
        if v1 > 12 >= v2:
            return f"{year:04d}-{v2:02d}-{v1:02d}", False  # DD/MM/YYYY
        elif v2 > 12 >= v1:
            return f"{year:04d}-{v1:02d}-{v2:02d}", False  # MM/DD/YYYY
        else:
            # Both <= 12 -> Ambiguous!
            if preferred_format == "MM/DD/YYYY":
                return f"{year:04d}-{v1:02d}-{v2:02d}", True
            else:
                # Default Indian convention is DD/MM/YYYY
                return f"{year:04d}-{v2:02d}-{v1:02d}", True

    return None, False

def parse_and_validate_file(
    file_bytes: bytes,
    filename: Optional[str] = None,
    preferred_date_format: str = "DD/MM/YYYY"
) -> Dict[str, Any]:
    """
    Validates, parses, normalizes, and fingerprints an imported MCX dataset.
    Supports CSV and Excel (.xlsx, .xls) formats.
    """
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    is_excel = False

    if filename and (filename.lower().endswith(".xlsx") or filename.lower().endswith(".xls")):
        is_excel = True
    elif file_bytes[:4] == b"PK\x03\x04":  # ZIP signature (xlsx)
        is_excel = True
    elif file_bytes[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":  # OLE signature (xls)
        is_excel = True

    try:
        if is_excel:
            df_raw = pd.read_excel(io.BytesIO(file_bytes))
        else:
            # Try comma then semicolon
            try:
                df_raw = pd.read_csv(io.BytesIO(file_bytes))
            except Exception:
                df_raw = pd.read_csv(io.BytesIO(file_bytes), sep=";")
    except Exception as e:
        return {
            "is_valid": False,
            "errors": [f"File parsing error ({'Excel' if is_excel else 'CSV'}): {str(e)}"],
            "file_hash": file_hash,
            "observations": []
        }

    raw_cols = [str(c).strip().lower() for c in df_raw.columns]
    column_mapping = {}

    for target_col, synonyms in COLUMN_SYNONYMS.items():
        matched = None
        for syn in synonyms:
            if syn in raw_cols:
                matched = df_raw.columns[raw_cols.index(syn)]
                break
        if matched:
            column_mapping[target_col] = matched

    # Required columns
    required = ["symbol", "close_price", "timestamp"]
    missing = [r for r in required if r not in column_mapping]
    if missing:
        return {
            "is_valid": False,
            "errors": [f"Missing required columns: {missing}. Available: {list(df_raw.columns)}"],
            "file_hash": file_hash,
            "observations": []
        }

    errors = []
    warnings = []
    observations = []
    ambiguous_date_count = 0
    seen_keys = set()
    duplicate_count = 0

    for idx, row in df_raw.iterrows():
        # Option filtering: if option_type is specified and not empty / futures placeholder, skip
        if "option_type" in column_mapping:
            opt_type = str(row[column_mapping["option_type"]]).strip().upper()
            if opt_type in ("CE", "PE", "CALL", "PUT"):
                continue  # Filter out options; GoldWise Pro models futures and spot bullion

        # Parse symbol
        raw_sym = str(row[column_mapping["symbol"]]).strip().upper()
        # Common normalization
        sym = raw_sym.replace(" ", "").replace("_", "").replace("-", "")
        if "GOLDMINI" in sym:
            sym = "GOLDM"
        elif "GOLDGUINEA" in sym:
            sym = "GOLDGUINEA"
        elif "GOLDPETAL" in sym:
            sym = "GOLDPETAL"
        elif "GOLDTEN" in sym:
            sym = "GOLDTEN"
        elif sym in ("GOLD", "GOLD1KG", "GOLDSTANDARD"):
            sym = "GOLD"

        spec = get_contract_spec(sym)
        if not spec:
            # Only warn if it looks like a gold commodity or if it's the only type in the file
            if "GOLD" in sym:
                warnings.append(f"Row {idx}: Unrecognized gold contract variant '{raw_sym}'. Skipped.")
            continue

        # Parse timestamp
        raw_ts = row[column_mapping["timestamp"]]
        parsed_ts, is_ambig = parse_mcx_date_str(raw_ts, preferred_format=preferred_date_format)
        if not parsed_ts:
            errors.append(f"Row {idx}: Invalid date value '{raw_ts}'")
            continue
        if is_ambig:
            ambiguous_date_count += 1

        # Parse expiry date
        expiry_str = "2026-08-05"
        if "expiry_date" in column_mapping:
            raw_exp = row[column_mapping["expiry_date"]]
            parsed_exp, _ = parse_mcx_date_str(raw_exp, preferred_format=preferred_date_format)
            if parsed_exp:
                expiry_str = parsed_exp

        # Deduplication check: (symbol, expiry, timestamp)
        dedup_key = (sym, expiry_str, parsed_ts)
        if dedup_key in seen_keys:
            duplicate_count += 1
            continue
        seen_keys.add(dedup_key)

        # Parse numeric prices
        try:
            close_val = float(str(row[column_mapping["close_price"]]).replace(",", "").strip())
            if close_val <= 0 or np.isnan(close_val):
                warnings.append(f"Row {idx}: Non-positive close price '{close_val}' for {sym}")
                continue
        except Exception:
            errors.append(f"Row {idx}: Could not parse numeric close price '{row[column_mapping['close_price']]}'")
            continue

        open_val = None
        if "open_price" in column_mapping:
            try:
                val = float(str(row[column_mapping["open_price"]]).replace(",", "").strip())
                if val > 0 and not np.isnan(val):
                    open_val = val
            except Exception:
                pass

        high_val = None
        if "high_price" in column_mapping:
            try:
                val = float(str(row[column_mapping["high_price"]]).replace(",", "").strip())
                if val > 0 and not np.isnan(val):
                    high_val = val
            except Exception:
                pass

        low_val = None
        if "low_price" in column_mapping:
            try:
                val = float(str(row[column_mapping["low_price"]]).replace(",", "").strip())
                if val > 0 and not np.isnan(val):
                    low_val = val
            except Exception:
                pass

        prev_close_val = None
        if "previous_close" in column_mapping:
            try:
                val = float(str(row[column_mapping["previous_close"]]).replace(",", "").strip())
                if val > 0 and not np.isnan(val):
                    prev_close_val = val
            except Exception:
                pass

        vol_val = 0.0
        if "volume" in column_mapping:
            try:
                val = float(str(row[column_mapping["volume"]]).replace(",", "").strip())
                if not np.isnan(val):
                    vol_val = val
            except Exception:
                vol_val = 0.0

        turnover_val = 0.0
        if "turnover" in column_mapping:
            try:
                val = float(str(row[column_mapping["turnover"]]).replace(",", "").strip())
                if not np.isnan(val):
                    turnover_val = val
            except Exception:
                turnover_val = 0.0

        oi_val = 0.0
        if "open_interest" in column_mapping:
            try:
                val = float(str(row[column_mapping["open_interest"]]).replace(",", "").strip())
                if not np.isnan(val):
                    oi_val = val
            except Exception:
                oi_val = 0.0

        # Compute normalized pure gold equivalent price
        pure_price = compute_pure_gold_price(close_val, spec.quotation_basis_grams, spec.purity_per_mille)

        observations.append({
            "symbol": sym,
            "expiry_date": expiry_str,
            "timestamp": parsed_ts,
            "open_price": open_val or close_val,
            "high_price": high_val or close_val,
            "low_price": low_val or close_val,
            "close_price": close_val,
            "previous_close": prev_close_val or close_val,
            "volume": vol_val,
            "turnover": turnover_val,
            "open_interest": oi_val,
            "quotation_basis": spec.quotation_basis_grams,
            "purity": spec.purity_per_mille,
            "normalized_price_pure_gram": round(pure_price, 4),
            "is_quarantined": False,
            "quarantine_reason": None,
        })

    if ambiguous_date_count > 0:
        warnings.append(
            f"Detected {ambiguous_date_count} rows with potential DD/MM vs MM/DD ambiguity. "
            f"Parsed using configured '{preferred_date_format}' convention."
        )

    if duplicate_count > 0:
        warnings.append(f"Filtered out {duplicate_count} duplicate records.")

    is_valid = len(observations) > 0 and len(errors) < 25

    # Sort observations chronologically
    observations.sort(key=lambda x: (x["timestamp"], x["symbol"]))

    dates = [o["timestamp"] for o in observations]
    start_date = min(dates) if dates else None
    end_date = max(dates) if dates else None
    symbols_present = sorted(list(set(o["symbol"] for o in observations)))

    return {
        "is_valid": is_valid,
        "file_hash": file_hash,
        "row_count": len(observations),
        "start_date": start_date,
        "end_date": end_date,
        "instruments": ",".join(symbols_present),
        "column_mapping": column_mapping,
        "errors": errors[:30],
        "warnings": warnings[:30],
        "duplicate_count": duplicate_count,
        "ambiguous_date_count": ambiguous_date_count,
        "observations": observations
    }

def parse_and_validate_csv(file_bytes: bytes, preferred_date_format: str = "DD/MM/YYYY") -> Dict[str, Any]:
    """Backward compatible wrapper for parse_and_validate_file."""
    return parse_and_validate_file(file_bytes, filename="data.csv", preferred_date_format=preferred_date_format)
