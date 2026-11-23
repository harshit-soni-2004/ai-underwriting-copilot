# Apex Lending Corp - MSME Underwriting Credit Policy
**Policy Code:** POL-MSME-2025-V1  
**Effective Date:** 2025-01-01  
**Target Segment:** Micro, Small & Medium Enterprises (MSMEs) in India  
**Maximum Ticket Size:** INR 50,00,000 (INR 50 Lakhs)

---

## 1. Scope & Objective
This document outlines the deterministic credit assessment policy criteria for Micro, Small, and Medium Enterprises (MSMEs) applying for unsecured working capital and business term loans. All quantitative criteria specified in this document are strictly evaluated against deterministically extracted banking and GST metrics.

---

## 2. Eligibility Criteria
- **Clause ELIG-01 (Entity Vintage):**
  - Minimum operating vintage of 24 months is required for automated approval recommendation.
  - Vintage between 6 months and 23 months mandates a committee **REFERRAL** (`REFER`).
  - Business vintage below 6 months mandates an automatic **DECLINE** (`DECLINE`).
- **Clause ELIG-02 (Minimum Annual Turnover):**
  - Minimum annualized banked operating turnover of INR 25,00,000 is mandatory.
  - Annual turnover below INR 25,00,000 mandates an automatic **DECLINE** (`DECLINE`).
- **Clause ELIG-03 (Entity Structure):**
  - Applicant must be a registered Proprietorship, Limited Liability Partnership (LLP), or Private Limited Company incorporated in India with valid PAN and GSTIN.

---

## 3. Financial Metrics & Underwriting Thresholds

| Clause | Metric Evaluated | Pass Threshold | Referral Range | Decline Threshold |
|---|---|---|---|---|
| **FIN-01** | DSCR Proxy | $\ge 1.2500$ | $1.0000 \le \text{DSCR} < 1.2500$ (`REFER`) | $< 1.0000$ (`DECLINE`) |
| **FIN-02** | AMB / Proposed EMI | $\ge 0.1000$ (10%) | $< 0.1000$ (`REFER`) | — |
| **FIN-03** | Inward Clearing Returns | $0$ returns | $1$ to $3$ returns (`REFER`) | $> 3$ returns ($\ge 4$, `DECLINE`) |
| **FIN-04** | FOIR | $\le 0.5000$ (50%) | $> 0.5000$ (`REFER`) | — |
| **FIN-05** | Top-1 Counterparty Share | $\le 0.4000$ (40%) | $> 0.4000$ (`REFER`) | — |
| **FIN-06** | Cash Flow Volatility (CV) | $\le 0.6000$ | $> 0.6000$ (`REFER`) | — |
| **FIN-07** | Excluded Round-Trip Ratio | $\le 0.0200$ (2.0%) | $> 0.0200$ (`REFER`) | — |

- **Clause FIN-01 (Debt Service Coverage Ratio - DSCR Proxy):**
  - Operating Surplus / (Existing Monthly EMIs + Proposed Monthly EMI).
  - $\ge 1.25x$: Fully compliant.
  - $1.00x \le \text{DSCR} < 1.25x$: Mandatory referral (`REFER`).
  - $< 1.00x$: Automatic decline (`DECLINE`).
- **Clause FIN-02 (Average Monthly Balance - AMB):**
  - The ratio of Average Monthly Balance to Proposed Monthly EMI must equal or exceed 10% ($\text{AMB} / \text{Proposed EMI} \ge 0.1000$). Ratio below 0.10 triggers a referral (`REFER`).
- **Clause FIN-03 (Inward Instrument Returns):**
  - Inward debits returned unpaid (bounced cheques, failed NACH/ECS debit attempts).
  - 0 returns: Compliant.
  - 1 to 3 instances: Referral (`REFER`).
  - Exceeding 3 instances ($\ge 4$): Automatic decline (`DECLINE`).
- **Clause FIN-04 (Fixed Obligation to Income Ratio - FOIR):**
  - Total debt service (Existing EMIs + Proposed EMI) must not exceed 50% of average monthly operating inflow ($\text{FOIR} \le 0.5000$). FOIR exceeding 0.50 triggers a referral (`REFER`).
- **Clause FIN-05 (Counterparty Concentration):**
  - Inflow concentration from any single buyer must not exceed 40% of total operating inflows (Top-1 Share $\le 0.4000$). Concentration exceeding 40% triggers a referral (`REFER`).
- **Clause FIN-06 (Cash Flow Volatility):**
  - Population Coefficient of Variation (CV) of monthly operating inflows must not exceed 0.60 ($\text{CV} \le 0.6000$). CV exceeding 0.60 requires committee referral (`REFER`).
- **Clause FIN-07 (Round-Trip Disqualification):**
  - Excluded round-trip credits must not exceed 2.0% of gross banked credits ($\text{Round-Trip Ratio} \le 0.0200$). Exceeding 2.0% triggers a referral (`REFER`).

---

## 4. Document Verification & Integrity
- **Clause DOC-01 (Confidence Threshold):** Extracted document fields must have confidence $\ge 0.85$.
- **Clause DOC-02 (GST vs Bank Turnover Discrepancy Band):**
  - The ratio of GSTR-3B annualized reported taxable turnover to banked operating inflow must lie within the acceptable band $[0.8000, 1.2000]$ ($|\text{Ratio} - 1.0| \le 0.2000$).
  - Turnover ratio below 0.8000 (bank deposits exceed GST by > 20%) or above 1.2000 (GST reported supplies exceed bank deposits by > 20%) triggers a referral (`REFER`).

---

## 5. Near-Threshold Rules & Margin Sign Convention
- **Continuous Metrics:** An applicant is classified as `near_threshold` for a clause if:
  $$|\text{Metric Value} - \text{Threshold}| \le 0.10 \times \text{Threshold}$$
- **Count / Vintage Metrics:**
  - `ELIG-01` (Vintage 24m): within $\pm 2$ months ($22$ to $26$ months).
  - `ELIG-01` (Vintage 6m): within $\pm 1$ month ($5$ to $7$ months).
  - `FIN-03` (Bounces Referral): $0$ or $1$ inward returns.
  - `FIN-03` (Bounces Decline): $3$ or $4$ inward returns.
  - `DOC-02` (Band boundaries): within $\pm 0.0200$ of $0.8000$ ($[0.7800, 0.8200]$) or $1.2000$ ($[1.1800, 1.2200]$).
- **Margin Sign Convention:**
  - **Positive Margin ($> 0$):** Applicant is on the **passing / compliant side** of the threshold.
  - **Negative Margin ($< 0$):** Applicant is on the **failing / policy-triggering side** of the threshold.
  - **Zero Margin ($= 0$):** Applicant is **exactly at the threshold** boundary.

---

## 6. Delegation of Authority & Approval
- **Clause AUTH-01 (Decision Precedence):**
  1. **Strict Hierarchy:** $\mathbf{DECLINE > REFER > APPROVE}$.
  2. Any condition triggering a DECLINE clause results in a final decision of **DECLINE**.
  3. In the absence of a DECLINE trigger, any condition triggering a REFER clause results in a final decision of **REFER**.
  4. Only applicants with zero triggered referral or decline clauses, with clean banking history and DSCR $\ge 1.50x$, receive an **APPROVE** recommendation.
  5. **Audit Invariant:** All clauses triggered must be recorded in `policy_clauses_triggered` for full compliance auditing, regardless of final decision.
- **Clause AUTH-02 (Referral Sign-off):** All referrals mandate human underwriter sign-off with documented mitigating factors.
- **Clause AUTH-03 (Decline Mandate):** Automatic decline cannot be overridden without Senior Credit Committee approval.
