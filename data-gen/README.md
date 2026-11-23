# Synthetic Data Generator for MSME Lending

This module produces 100% synthetic, reproducible MSME loan applicant portfolios with bank statements, tax invoices, GST filings, clean ground-truth transaction logs, and expected financial metrics.

## Design Principles
1. **Zero Real Customer Data**: All PANs, GSTINs, corporate entities, transactions, and addresses are synthetically generated.
2. **Deterministic Seed Derivation**: Each applicant's seed is derived from `hash(master_seed, applicant_id)`. Adding or altering applicants never changes existing ones.
3. **Dual Data Artifacts**:
   - `transactions.json`: Clean, pre-categorized transaction log with string monetary values. Used as the ground truth input to the Java core metrics engine.
   - Bank Statements (CSV & PDF) and Invoices (PDF): Noisy renderings used in Phase 2 for OCR and structured document extraction.
4. **Deterministic PDF Generation**: Uses ReportLab with `invariant=1` and `pageCompression=0` for byte-reproducible PDF creation.

## `transactions.json` Schema & Same-Day Excerpt

`transactions.json` uses an envelope structure containing applicant metadata, opening balance, overdraft limit, and a chronological list of transactions. Each transaction includes a daily sequence number and explicit CREDIT/DEBIT type.

### Schema:
```json
{
  "applicant_id": "string",
  "opening_balance": "string (decimal INR)",
  "od_limit": "string (decimal INR)",
  "transactions": [
    {
      "date": "YYYY-MM-DD",
      "sequence_number": 1,
      "amount": "string (decimal INR)",
      "type": "CREDIT | DEBIT",
      "category": "SALES_RECEIPT | VENDOR_PAYMENT | DEBT_SERVICE | ...",
      "counterparty": "string",
      "narration": "string"
    }
  ]
}
```

### Same-Day Transaction Excerpt (`data/synthetic/applicants/APP-027-HEALTHY-NEAR-AMB-PASS/transactions.json`):
```json
{
  "applicant_id": "APP-027-HEALTHY-NEAR-AMB-PASS",
  "opening_balance": "27500.00",
  "od_limit": "0.00",
  "transactions": [
    {
      "date": "2024-01-03",
      "sequence_number": 1,
      "amount": "100000.00",
      "type": "CREDIT",
      "category": "SALES_RECEIPT",
      "counterparty": "Larsen Heavy Fab",
      "narration": "NEFT CR-Larsen Heavy Fab-INV-102"
    },
    {
      "date": "2024-01-03",
      "sequence_number": 2,
      "amount": "100000.00",
      "type": "DEBIT",
      "category": "OWN_ACCOUNT_TRANSFER",
      "counterparty": "Promoter Sweep Account",
      "narration": "AUTO SWEEP DR TO CURRENT ACC 9921"
    }
  ]
}
```

## Archetypes (120 Applicants)
- **Healthy (30)**: Consistent operating sales growth, zero bounces, DSCR >= 1.50x, FOIR <= 0.40, diversified buyer base. Includes near-threshold variants on Top-1 share and FOIR.
- **Seasonal (20)**: Peak inflows during festive/harvest quarters (Aug-Nov), trough in Q1. Demonstrates cash flow cyclicality. Includes near-threshold variants on CV (0.57 vs 0.65).
- **High Concentration (20)**: Dominant customer accounting for > 40% of banked sales. Includes near-threshold variants (38% vs 43%).
- **Stressed (20)**: Modeled with an Overdraft limit (`od_limit` INR 2 to 4 Lakh). Inward cheque/NACH dishonours due to insufficient funds, low AMB, FOIR > 0.60. Varied bounce patterns (1, 2, or 4 bounces; some just-missing decline).
- **Thin-File / New Business (15)**: 4 to 23 months operating vintage. Near-threshold cases on 5m (decline), 6m (referral boundary), and 23m (mature referral boundary).
- **Edge Cases & Near-Threshold (15)**:
  - Zero-inflow month (`ZERO-INFLOW`): July has 0 sales receipts; CV properly elevated.
  - One-off capital asset liquidation (`LARGE-CREDIT`): INR 15 Lakh `ONE_OFF` excluded credit.
  - Round-trip transaction pair (`ROUND-TRIP`): 4.5 Lakh `ROUND_TRIP` excluded credit (triggers `FIN-07`).
  - Near-threshold tests on both sides for DSCR (1.18 vs 1.26), AMB (9% vs 11%), FOIR (48% vs 52%), Round-Trip (1.4% vs 2.5%), and GST Discrepancy (17% vs 23%).

## Running Data Generation
```bash
# Run full generation of 120 applicants via Make
make seed

# Or run directly via Python CLI
python data-gen/generate_data.py --applicants 120 --seed 42
```
