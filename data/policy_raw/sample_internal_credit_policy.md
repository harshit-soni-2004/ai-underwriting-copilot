# Sample Internal Credit Policy for MSME Unsecured Lending
*Classification: Sample Internal Policy - Non-confidential Demonstration*
*Policy Code: POL-MSME-2025-V1*

## 1. Overview and Purpose
This document outlines the credit risk assessment criteria for Micro, Small, and Medium Enterprises (MSMEs) applying for unsecured working capital and short-term term loans up to INR 50,00,000 (Fifty Lakhs).

## 2. Eligibility Criteria
- **Clause ELIG-01 (Entity Vintage):** The applicant enterprise must have a minimum operational history of 24 consecutive months. Applications with vintage between 6 and 23 months require mandatory referral (thin-file review). Applications with vintage strictly under 6 months must be DECLINED.
- **Clause ELIG-02 (Minimum Turnover):** The enterprise must demonstrate an annualized operating turnover of not less than INR 25,00,000 verified through aggregate bank sales deposits or GSTR-3B filings over the preceding 12 months. Turnover below INR 25,00,000 triggers a referral.
- **Clause ELIG-03 (Eligible Entity Types):** Sole proprietorships, partnerships, LLPs, and Private Limited Companies registered in India.

## 3. Financial Metrics & Underwriting Thresholds
- **Clause FIN-01 (Debt Service Coverage Ratio - DSCR Proxy):** The estimated DSCR proxy must be greater than or equal to 1.25x. If DSCR proxy is between 1.10x and 1.24x, loan terms require mandatory committee referral. A DSCR proxy below 1.00x mandates an automatic DECLINE.
- **Clause FIN-02 (Average Monthly Balance - AMB):** The average monthly balance across the applicant's primary operating bank account over the assessment period must equal or exceed 10% of the proposed monthly loan EMI (AMB / Proposed EMI >= 0.10). AMB below 10% of proposed EMI triggers a referral.
- **Clause FIN-03 (Bounced Cheque / Inward Return Threshold):** An applicant must have zero inward return instances due to financial failure (insufficient funds) over the most recent 3 months, and not more than 2 instances in the preceding 12 months. Inward clearing returns between 1 and 2 instances trigger a referral. Inward returns exceeding 3 instances within the evaluation window mandate an automatic DECLINE.
- **Clause FIN-04 (Fixed Obligation to Income Ratio - FOIR):** Total proposed debt obligations (existing verified EMIs plus proposed loan EMI) shall not exceed 50% of the average monthly operating inflow (FOIR <= 0.50). FOIR exceeding 0.50 triggers a referral.
- **Clause FIN-05 (Counterparty Concentration):** Inflow concentration from any single customer/buyer must not exceed 40% of total operating inflows (Top-1 Share <= 0.40). Concentration exceeding 40% triggers a referral.
- **Clause FIN-06 (Cash Flow Volatility):** The coefficient of variation (CV) of monthly operating inflows must not exceed 0.60. Volatility exceeding 0.60 requires mandatory committee referral to evaluate seasonal swings and working capital adequacy.
- **Clause FIN-07 (Round-Trip Disqualification):** If excluded round-trip credits exceed 2.0% of gross credit turnover (Round-Trip Ratio > 0.0200), the application requires mandatory referral to investigate potential artificial turnover inflation.

## 4. Document Verification & Completeness
- **Clause DOC-01 (Verification Requirement):** All critical document fields (Account numbers, GSTIN, Inflow/Outflow aggregates, Invoice totals) must possess an extraction confidence score of >= 0.85. Any field below this threshold must be human-reviewed before memo generation.
- **Clause DOC-02 (Inconsistency Threshold):** Discrepancies between turnover reported in GSTR filings and turnover deposited in bank statements exceeding 20% (|GST Ratio - 1.0| > 0.20) must trigger a referral.

## 5. Delegation of Authority & Approval
- **Clause AUTH-01 (Decision Precedence & Rules):**
  1. **Strict Precedence:** `DECLINE > REFER > APPROVE`.
  2. Any single condition triggering a DECLINE rule forces the final recommendation to **DECLINE**.
  3. In the absence of a DECLINE trigger, any condition triggering a REFER rule forces the final recommendation to **REFER**.
  4. Only applications meeting all eligibility and financial criteria without triggering any referral or decline clauses, with clean banking history (0 bounces) and DSCR >= 1.50x, are recommended for **APPROVAL**.
  5. **Audit Invariant:** All clauses triggered during assessment must be recorded in `policy_clauses_triggered` for full compliance auditing, regardless of the final decision.
- **Clause AUTH-02 (Referral Conditions):** Any condition triggering a referral rule requires a human credit officer sign-off with documented mitigating commentary.
- **Clause AUTH-03 (Decline Rule):** Bounced cheques exceeding 3 instances, DSCR below 1.0x, or business vintage under 6 months mandate an automatic DECLINE recommendation.
