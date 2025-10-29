import argparse
import os
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np 

# Optional fuzzy lib; use if you want
try:
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover
    fuzz = None  # type: ignore


@dataclass
class Match:
    payment_id: str
    invoice_id: str
    confidence: float
    rationale: str


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    return df


def write_out(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)


def baseline_normalize_name(name: Optional[str]) -> str:
    if not isinstance(name, str):
        return ""
    return (
        name.strip()
            .replace("Private Limited", "Pvt Ltd")
            .replace("Pvt. Ltd", "Pvt Ltd")
            .replace("Limited", "Ltd")
            .replace("Ltd.", "Ltd")
            .replace("Industries", "Ind") # FIX: Handle Industries abbreviation
            .replace("Co.", "Co")         # FIX: Handle Co. abbreviation
            .lower()
    )


def match_records(invoices: pd.DataFrame, payments: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Implementation of matching logic using sequential, confidence-based rules.
    """
    
    # --- TODO 1: Add parsed numeric/date columns and normalized names (FIXED) ---
    inv = invoices.copy()
    pay = payments.copy()
    
    # Data Cleaning: Fill NaN/None with empty string for text columns used in matching
    inv['customer_name'] = inv['customer_name'].fillna('')
    pay['payer_name'] = pay['payer_name'].fillna('')
    pay['memo'] = pay['memo'].fillna('')
    pay['reference_number'] = pay['reference_number'].fillna('')
    
    # Data Parsing
    inv['invoice_amount_num'] = pd.to_numeric(inv['invoice_amount'], errors="coerce")
    inv['due_date_parse'] = pd.to_datetime(inv['due_date'], errors="coerce", utc=False)
    inv['invoice_date_parse'] = pd.to_datetime(inv['invoice_date'], errors="coerce", utc=False)
    inv['matched'] = False
    inv['norm_name'] = inv['customer_name'].apply(baseline_normalize_name)
    
    pay['payment_amount_num'] = pd.to_numeric(pay['payment_amount'], errors="coerce")
    pay['payment_date_parse'] = pd.to_datetime(pay['payment_date'], errors='coerce', utc=False)
    pay['matched'] = False
    pay['norm_name'] = pay['payer_name'].apply(baseline_normalize_name)

    all_matches: List[Match] = []
    DATE_WINDOW_DAYS = pd.Timedelta(days=14) # FIX: Increased from 7 to 14 days
    AMOUNT_TOLERANCE = 0.10                  # FIX: Increased from 0.05 to 0.10
    FUZZY_NAME_THRESHOLD = 85 
    EPSILON = 1e-6 

    # --- TODO 2: Deterministic rules (High Confidence) ---
    
    # Rule A: Direct invoice_id in payment memo/reference (Confidence 1.0)
    for p_idx, p_row in pay.iterrows():
        if p_row['matched']: continue
            
        memo_ref = f"{p_row['memo'].upper()} {p_row['reference_number'].upper()}" 
        
        candidates = []
        for i_idx, i_row in inv[~inv['matched']].iterrows():
            
            inv_id_upper = str(i_row['invoice_id']).upper() 
            inv_id_num = inv_id_upper.split('-')[-1]         
            
            is_id_in_memo = (inv_id_upper in memo_ref) or (inv_id_num in memo_ref)
            
            # Match on ID mention, currency, and normalized name
            if is_id_in_memo and \
               (p_row['currency'] == i_row['currency']) and \
               (p_row['norm_name'] == i_row['norm_name']):
                
                amount_match_desc = "Amount mismatch"
                is_exact_amount = abs(p_row['payment_amount_num'] - i_row['invoice_amount_num']) < EPSILON
                if is_exact_amount:
                    amount_match_desc = "Exact amount match"
                elif p_row['payment_amount_num'] < i_row['invoice_amount_num']:
                    amount_match_desc = "Partial payment"
                elif p_row['payment_amount_num'] > i_row['invoice_amount_num']:
                    amount_match_desc = "Overpayment"

                candidates.append((i_idx, i_row, amount_match_desc))
                
        if len(candidates) >= 1:
            best_i_idx, best_i_row, amount_match_desc = min(candidates, key=lambda x: abs(x[1]['due_date_parse'] - p_row['payment_date_parse']))
            
            confidence = 1.0 if len(candidates) == 1 else 0.98
            rationale = (f"Rule A: Invoice ID '{best_i_row['invoice_id']}' explicitly mentioned in memo/reference. "
                         f"Exact name/currency match. ({amount_match_desc})."
                         f"{' (Tie-breaker used)' if len(candidates) > 1 else ''}")
            
            all_matches.append(Match(
                payment_id=p_row['payment_id'],
                invoice_id=best_i_row['invoice_id'],
                confidence=confidence,
                rationale=rationale
            ))
            pay.loc[p_idx, 'matched'] = True
            inv.loc[best_i_idx, 'matched'] = True
            
            
    # Rule B: Exact amount & Near-Date & Same Currency & Exact Normalized Name (Confidence 0.95)
    for p_idx, p_row in pay.iterrows():
        if p_row['matched']: continue
            
        candidates = []
        for i_idx, i_row in inv[~inv['matched']].iterrows():
            is_exact_amount = abs(p_row['payment_amount_num'] - i_row['invoice_amount_num']) < EPSILON
            
            if (p_row['currency'] == i_row['currency']) and \
               (p_row['norm_name'] == i_row['norm_name']) and \
               is_exact_amount and \
               (abs(p_row['payment_date_parse'] - i_row['due_date_parse']) <= DATE_WINDOW_DAYS):
                candidates.append((i_idx, i_row))
                
        if len(candidates) >= 1:
            best_i_idx, best_i_row = min(candidates, key=lambda x: abs(x[1]['due_date_parse'] - p_row['payment_date_parse']))
            
            confidence = 0.95 if len(candidates) == 1 else 0.90
            rationale = (f"Rule B: Exact amount, exact normalized name, and payment date is near due date."
                         f"{' (Tie-breaker used)' if len(candidates) > 1 else ''}")

            all_matches.append(Match(
                payment_id=p_row['payment_id'],
                invoice_id=best_i_row['invoice_id'],
                confidence=confidence,
                rationale=rationale
            ))
            pay.loc[p_idx, 'matched'] = True
            inv.loc[best_i_idx, 'matched'] = True

    # --- TODO 3: Fuzzy rules (Medium Confidence) ---
    
    # Rule C: Fuzzy Name (>= 85%), Amount Proximity (<= 10%), Near-Date (<= 14 days), Same Currency (Confidence 0.70-0.90)
    for p_idx, p_row in pay.iterrows():
        if p_row['matched']: continue
            
        best_match = None
        best_confidence = 0.0
        best_i_idx = -1
        
        for i_idx, i_row in inv[~inv['matched']].iterrows():
            if p_row['currency'] != i_row['currency']: continue
            
            # 1. Amount Proximity Check (Partial/Overpayment)
            if i_row['invoice_amount_num'] == 0 or np.isnan(i_row['invoice_amount_num']) or np.isnan(p_row['payment_amount_num']): continue
                
            amount_diff = abs(p_row['payment_amount_num'] - i_row['invoice_amount_num'])
            is_amount_proximate = (amount_diff / i_row['invoice_amount_num']) <= AMOUNT_TOLERANCE

            # 2. Date Proximity Check
            if pd.isna(p_row['payment_date_parse']) or pd.isna(i_row['due_date_parse']): continue

            is_date_proximate = abs(p_row['payment_date_parse'] - i_row['due_date_parse']) <= DATE_WINDOW_DAYS
            
            if not is_amount_proximate or not is_date_proximate: continue
            
            # 3. Fuzzy Name Score
            name_score = 0.0
            rationale_prefix = "Fuzzy Name Match"
            if fuzz:
                name_score = fuzz.token_sort_ratio(p_row['norm_name'], i_row['norm_name'])
                rationale_prefix = "Fuzzy Name Match (rapidfuzz token_sort_ratio)"
            else:
                if p_row['norm_name'] == i_row['norm_name']:
                    name_score = 100.0
                    rationale_prefix = "Normalized Name Match (rapidfuzz missing)"
                else:
                    name_score = 0.0
                
            is_name_match = name_score >= FUZZY_NAME_THRESHOLD

            if is_name_match:
                confidence = 0.70 + (name_score * 0.2 / 100.0) 
                
                amount_desc = "Exact amount" if abs(amount_diff / i_row['invoice_amount_num']) < EPSILON else f"Amount within {AMOUNT_TOLERANCE*100:.0f}% tolerance"
                
                rationale = (f"Rule C: {rationale_prefix} ({name_score:.1f}). "
                             f"{amount_desc}. "
                             f"Payment date near due date.")
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = Match(
                        payment_id=p_row['payment_id'],
                        invoice_id=i_row['invoice_id'],
                        confidence=confidence,
                        rationale=rationale
                    )
                    best_i_idx = i_idx

        if best_match:
            all_matches.append(best_match)
            pay.loc[p_idx, 'matched'] = True
            inv.loc[best_i_idx, 'matched'] = True


    # Final step: Convert list of Match objects to DataFrame and filter unmatched
    matches_df = pd.DataFrame([m.__dict__ for m in all_matches])

    unmatched_payments = payments[~pay['matched']].copy()
    unmatched_invoices = invoices[~inv['matched']].copy()
    
    return matches_df, unmatched_payments, unmatched_invoices


def main():
    parser = argparse.ArgumentParser(description="Invoice ↔ Payment matching (starter)")
    parser.add_argument("--invoices", required=True, help="path to invoices.csv")
    parser.add_argument("--payments", required=True, help="path to payments.csv")
    parser.add_argument("--out", default="out/", help="output directory (default: out/)")
    args = parser.parse_args()

    invoices = load_csv(args.invoices)
    payments = load_csv(args.payments)

    matches, u_pay, u_inv = match_records(invoices, payments)

    os.makedirs(args.out, exist_ok=True)
    write_out(matches, os.path.join(args.out, "matches.csv"))
    write_out(u_pay, os.path.join(args.out, "unmatched_payments.csv"))
    write_out(u_inv, os.path.join(args.out, "unmatched_invoices.csv"))

    # Also print a quick JSON summary to stdout for visibility
    summary = {
        "matches": len(matches),
        "unmatched_payments": len(u_pay),
        "unmatched_invoices": len(u_inv),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()