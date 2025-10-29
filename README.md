# Invoice ↔ Payment Matching — Interview Scaffold

## Quick start (Python option)

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.matcher --invoices data/invoices.csv --payments data/payments.csv --out out/
```

It will create `out/` with placeholder outputs. Your job: implement the matching logic in `src/matcher.py` (see TODOs).

## Deliverables

- `matches.csv`: `payment_id,invoice_id,confidence,rationale`
- `unmatched_payments.csv`
- `unmatched_invoices.csv` (optional)

## Notes & Hints

- Start with deterministic rules (invoice id in memo/ref, exact amount, date window), then layer fuzzy signals (name similarity, amount proximity, description tokens).
- Pick **stable tie-breakers** (e.g., closest invoice date, earliest due date, smallest absolute amount delta).  
- Keep it **idempotent**: the same input should yield the same output without double-consuming records.
- At least **one unit test** in `tests/` that captures an edge case.


