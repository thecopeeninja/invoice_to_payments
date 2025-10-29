import pandas as pd
from src.matcher import match_records

def test_amount_and_date_window_baseline():
    invoices = pd.DataFrame([
        {"invoice_id":"I-1","customer_name":"Acme Pvt Ltd","invoice_date":"2025-08-01","due_date":"2025-08-31","currency":"INR","invoice_amount":"100.00","po_number":"","customer_ref":""}
    ])
    payments = pd.DataFrame([
        {"payment_id":"P-1","payer_name":"Acme Pvt Ltd","payment_date":"2025-08-30","currency":"INR","payment_amount":"100.00","memo":"","reference_number":"","bank_txn_id":"T-1"}
    ])
    matches, u_pay, u_inv = match_records(invoices, payments)
    # This is a placeholder assertion. Update after you implement logic.
    assert isinstance(matches, pd.DataFrame)
