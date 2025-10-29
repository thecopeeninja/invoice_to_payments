# Problem Brief — Invoice ↔ Payment Matching (Interview)

**Context.** You are implementing a core Treasury/AR reconciliation capability: matching inbound bank payments to outstanding customer invoices. Real data are messy: payment memos often omit the invoice id, amounts may include fees, dates drift by a few days, and customer names vary slightly.

**Goal:** Build a small, explainable matcher that links **payments** to **invoices** and returns:
- `matches`: a list of suggested links with a **confidence score** in `[0, 1]` and a short **rationale** string
- `unmatched_payments`
- (optional) `unmatched_invoices`

**Scope.**
- Start with **deterministic rules** (e.g., explicit `invoice_id` in memo/reference; exact amount match).  
- Then extend with **fuzzy/heuristic** rules (e.g., payer name similarity, amount proximity within a tolerance, date windows).
- Make results **re-runnable/idempotent**. If you run twice, it should not double-consume the same invoice/payment.
- Keep the implementation in **one or two files** under `src/`. Any language is fine; Python starter provided.

**Edge cases to consider.**
- Missing invoice id in the payment memo/reference
- Duplicate payments / duplicate bank transaction ids
- **Partial** payments (payment < invoice amount) and **overpayments** (payment > invoice amount)
- Splitting a payment across multiple invoices (optional to implement; at least describe your approach)
- Ambiguity: two invoices with the same amount and similar dates
- Name variants and small typos (e.g., "Acme Pvt Ltd" vs "Acme Private Limited")
- Currency mismatches (should not match unless explicitly handled)

**Input data.**
- `data/invoices.csv`
- `data/payments.csv`

**Output.**
- Print a JSON blob to stdout **or** create files under `out/`:
  - `out/matches.csv` with columns: `payment_id, invoice_id, confidence, rationale`
  - `out/unmatched_payments.csv`
  - `out/unmatched_invoices.csv` (optional)

**What we evaluate.**
- Clear baseline rules → then thoughtful fuzzy scoring
- Handling (or at least deliberate treatment) of partial/over/duplicates
- Deterministic tie-breaking and idempotency story
- Code clarity and small, meaningful tests

