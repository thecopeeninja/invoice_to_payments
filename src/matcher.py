import argparse
import os
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import pandas as pd

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
    # Convert numeric/date-like columns later as needed by you
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
            .lower()
    )


def match_records(invoices: pd.DataFrame, payments: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """TODO: Implement your matching logic.

    Required output schemas:
      matches: columns = [payment_id, invoice_id, confidence, rationale]
      unmatched_payments: any identifying columns for payments
      unmatched_invoices: any identifying columns for invoices (optional)
    """
    # --- TODO 1: Add parsed numeric/date columns if needed ---
    # For example: amounts as float, dates as datetime with utc-naive

    # --- TODO 2: Deterministic rules ---
    # 2a) Direct invoice_id in payment memo/reference
    # 2b) Exact amount & near-date (within a window), same currency
    # 2c) Name normalization to improve confidence/rationale

    # --- TODO 3: Fuzzy rules (optional) ---
    # Use rapidfuzz or simple heuristics for name similarity and memo tokens

    # For now, return empty matches and everything as unmatched (so CLI runs)
    matches = pd.DataFrame(columns=["payment_id", "invoice_id", "confidence", "rationale"])  # type: ignore
    unmatched_payments = payments.copy()
    unmatched_invoices = invoices.copy()
    return matches, unmatched_payments, unmatched_invoices


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
