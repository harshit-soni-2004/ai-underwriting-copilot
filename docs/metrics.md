# Deterministic Financial Metrics Specification

*Classification: Technical Specification & Financial Math Standard*  
*Document Version: 1.0.0*  
*Implementation Invariant: All financial numbers are calculated deterministically using decimal arithmetic with explicit rounding. Floating point arithmetic is strictly forbidden.*

---

## 1. Core Principles & Standards

1. **Deterministic Execution**: Given identical transaction records and obligations, calculations in Python and Java must match to the exact integer penny / basis point.
2. **Explicit Decimal Arithmetic**:
   - Currency amounts: `scale = 2`, `RoundingMode.HALF_UP` (e.g. `INR "12450.50"`).
   - Ratios and percentages: `scale = 4`, `RoundingMode.HALF_UP` (e.g. `0.2514` for 25.14%).
   - Index values (HHI): `scale = 2`, `RoundingMode.HALF_UP`.
3. **Canonical Data Representation**: All ground truth values, intermediate exchange schemas, and golden fixtures store monetary amounts and ratios as **strings** (e.g. `"184500.25"`, `"1.4250"`), never IEEE 754 floats.

---

## 2. Metric Definitions & Formulas

### 2.1 Average Monthly Balance (AMB)
- **Definition**: The arithmetic mean of the **Daily Average Balance** across all months in the assessment period.
- **Daily Average Balance Formula**:
  For month $m$ having $D_m$ days:
  $$\text{Daily AMB}_m = \frac{1}{D_m} \sum_{d=1}^{D_m} B_{m, d}$$
  where $B_{m, d}$ is the end-of-day closing ledger balance on day $d$.
- **Carry-Forward Rule**: If no transaction occurs on day $d$, the closing balance is carried forward from day $d-1$:
  $$B_{m, d} = B_{m, d-1}$$
- **Partial Month Handling**:
  If a statement starts on day $k > 1$ or ends before the last day of the month, the daily average for that month is calculated strictly across the active days:
  $$\text{Daily AMB}_{\text{partial}} = \frac{1}{D_{\text{active}}} \sum_{d=k}^{D_{\text{end}}} B_{m, d}$$
  The overall statement AMB is the weighted daily average over the total active days:
  $$\text{Overall AMB} = \frac{\sum_{\text{all active days}} B_d}{\text{Total Active Days}}$$
- **Rationale**: Daily average is the standard required by Indian banking guidelines (RBI / NBFC). Simple month-end averages are vulnerable to artificial window-dressing (temporary deposits on the 30th/31st).

---

### 2.2 Monthly Operating Inflow & Excluded Inflows
- **Operating Inflow Definition**: Measures genuine commercial turnover. Counts **only** credit transactions categorized as `SALES_RECEIPT` (customer payments, collections, receivables).
- **Excluded Credits Breakdown**: The engine must categorize and track all non-operating credits into distinct breakdown buckets:
  1. `LOAN_DISBURSAL`: Disbursal of loans or credit lines.
  2. `CAPITAL_INFUSION`: Owner/equity capital infusion.
  3. `OWN_ACCOUNT_TRANSFER`: Contra transfers from accounts belonging to the same entity.
  4. `REFUND_REVERSAL`: Tax refunds, merchant chargeback reversals, or operational refunds.
  5. `ASSET_SALE`: One-off proceeds from asset liquidation.
  6. `ROUND_TRIP`: Artificial turnover inflation. Defined as a credit transaction where a matching debit occurs with the same counterparty, within $\pm 2\%$ of the amount, within $N$ days (default $N = 3$).
- **Formula**:
  $$\text{Operating Inflow}_m = \sum_{t \in \text{Credits}_m \cap \text{SALES\_RECEIPT}} \text{Amount}_t$$
  $$\text{Excluded Inflow}_m = \sum_{t \in \text{Excluded Credits}_m} \text{Amount}_t$$

---

### 2.3 Monthly Operating Outflow
- **Definition**: Sum of genuine business expenses and operational debits (vendor payments, payroll, utilities, rent, supplies).
- **Exclusion**: **Excludes debt service obligations** (existing loan EMIs, interest debits, credit line repayments) to avoid double-counting in coverage ratios.
- **Formula**:
  $$\text{Operating Outflow}_m = \sum_{t \in \text{Debits}_m \setminus \text{DEBT\_SERVICE}} \text{Amount}_t$$

---

### 2.4 Cash-Flow Volatility
- **Definition**: The Coefficient of Variation ($\text{CV}$) of **monthly operating inflows** over the evaluation period ($M$ months).
- **Formula**:
  $$\text{CV} = \frac{\sigma_{\text{operating\_inflow}}}{\mu_{\text{operating\_inflow}}}$$
  where:
  - $\mu = \frac{1}{M} \sum_{m=1}^M \text{Operating Inflow}_m$
  - $\sigma$ is the **population standard deviation** ($\text{ddof} = 0$):
    $$\sigma = \sqrt{\frac{1}{M} \sum_{m=1}^M (\text{Operating Inflow}_m - \mu)^2}$$
- **Zero / Negative Inflow Safeguard**: If $\mu \le 0$ or $M < 3$, the engine returns `status: INSUFFICIENT_DATA` with reason `INSUFFICIENT_OR_ZERO_INFLOW_HISTORY`.

---

### 2.5 Bounced Cheque / Inward Return Metrics
Financial distress and creditworthiness are tracked using two distinct, direction-specific return metrics:

1. **Inward Clearing Returns (`inward_clearing_returns_count`)**:
   - Represents cheques, NACH, or ECS debits **issued by the applicant** to vendors, lenders, or third parties that were **dishonoured due to insufficient funds**.
   - Directly indicates liquidity shortfalls and distress.
2. **Outward Cheque Returns (`outward_cheque_returns_count`)**:
   - Represents cheques **received from customers** and deposited by the applicant that were returned unpaid by the drawer's bank.
   - Measures buyer risk rather than applicant distress.
3. **Inward Bounce Rate (`bounce_rate`)**:
   $$\text{Bounce Rate} = \frac{\text{inward\_clearing\_returns\_count}}{\text{total inward cheque + ECS + NACH debit attempts}}$$
   - If total inward debit attempts $= 0$, $\text{Bounce Rate} = 0.0000$.

---

### 2.6 Debt Service Coverage Ratio (DSCR Proxy)
- **Definition**: Ratio of net operational cash surplus to total debt obligations.
- **Formula**:
  $$\text{DSCR Proxy} = \frac{\text{Average Monthly Operating Inflow} - \text{Average Monthly Operating Outflow}}{\text{Average Existing Monthly EMIs} + \text{Proposed Monthly Loan EMI}}$$
- **Negative Surplus Handling**:
  If the operational surplus $(\text{Inflow} - \text{Outflow}) \le 0$, the engine calculates and returns the true value ($\le 0$) with flag `is_negative_surplus: true`. It does **not** return `INSUFFICIENT_DATA`.
- **Zero Debt Service Safeguard**:
  If $(\text{Existing EMIs} + \text{Proposed EMI}) = 0$, returns `INSUFFICIENT_DATA: ZERO_DEBT_OBLIGATIONS`.

---

### 2.7 Fixed Obligation to Income Ratio (FOIR)
- **Definition**: The proportion of monthly gross operating income committed to servicing total debt.
- **Formula**:
  $$\text{FOIR} = \frac{\text{Average Existing Monthly EMIs} + \text{Proposed Monthly Loan EMI}}{\text{Average Monthly Operating Inflow}}$$
- **Safeguard**: If Average Monthly Operating Inflow $\le 0$, returns `INSUFFICIENT_DATA: ZERO_OPERATING_INFLOW`.

---

### 2.8 Counterparty Concentration
Evaluates customer dependence across 12 months of operating sales receipts:
1. **Top-1 Concentration Share**:
   $$\text{Top-1 Share} = \frac{\text{Inflows from Largest Single Customer}}{\text{Total 12-Month Operating Inflows}}$$
2. **Top-3 Concentration Share**:
   $$\text{Top-3 Share} = \frac{\text{Inflows from Top 3 Customers Combined}}{\text{Total 12-Month Operating Inflows}}$$
3. **Herfindahl-Hirschman Index (HHI)**:
   $$\text{HHI} = \sum_{i=1}^K (s_i \times 100)^2$$
   where $s_i = \frac{\text{Inflows}_i}{\text{Total Operating Inflows}}$. HHI ranges from $0$ to $10{,}000.00$.

---

### 2.9 GST vs Bank Turnover Discrepancy Ratio
- **Definition**: Cross-checks banked sales collections against official tax filings (GSTR-3B outward taxable supplies).
- **Formula**:
  $$\text{GST Turnover Ratio} = \frac{\text{Annual GSTR-3B Taxable Supplies}}{\text{Annual Bank Operating Inflow}}$$
- **Policy Rule**: An absolute discrepancy $> 20\%$ ($|\text{GST Ratio} - 1.0| > 0.20$) triggers a mandatory referral under policy clause `DOC-02`.

---

## 3. Five Hand-Worked Reference Fixtures

These 5 canonical fixtures were calculated step-by-step by hand. Both the Python oracle (`data-gen/`) and the Java metrics engine (`core-service/`) must match these exact figures.

### Fixture 1: `FIX-01-CLEAN-GROWTH` (3 Months, Healthy)
- **Period**: 2024-01-01 to 2024-03-31 (91 active days: Jan 31, Feb 29 [leap year], Mar 31).
- **Opening Balance (2024-01-01)**: `INR 100000.00`
- **Transactions**:
  - `2024-01-10`: Credit `50000.00`, Category: `SALES_RECEIPT`, Counterparty: "Alpha Corp" (Balance: `150000.00`)
  - `2024-01-20`: Debit `30000.00`, Category: `VENDOR_PAYMENT`, Counterparty: "Vendor X" (Balance: `120000.00`)
  - `2024-02-05`: Credit `60000.00`, Category: `SALES_RECEIPT`, Counterparty: "Beta Ltd" (Balance: `180000.00`)
  - `2024-02-15`: Debit `25000.00`, Category: `VENDOR_PAYMENT`, Counterparty: "Vendor Y" (Balance: `155000.00`)
  - `2024-03-10`: Credit `70000.00`, Category: `SALES_RECEIPT`, Counterparty: "Alpha Corp" (Balance: `225000.00`)
  - `2024-03-20`: Debit `35000.00`, Category: `OPERATING_EXPENSE`, Counterparty: "Utilities" (Balance: `190000.00`)
- **Existing Monthly EMI**: `10000.00`, **Proposed Monthly EMI**: `5000.00` (Total Debt: `15000.00`).
- **GSTR-3B Taxable Supplies**: Jan: `50000.00`, Feb: `60000.00`, Mar: `70000.00` (Total: `180000.00`).

#### Step-by-Step Hand Calculations:
1. **Daily Balances & AMB**:
   - Jan: Days 1-9 (9 days @ 100,000) = 900,000; Days 10-19 (10 days @ 150,000) = 1,500,000; Days 20-31 (12 days @ 120,000) = 1,440,000.
     Total Jan sum = 3,840,000. Jan AMB = 3,840,000 / 31 = `123870.97`
   - Feb (29 days): Days 1-4 (4 days @ 120,000) = 480,000; Days 5-14 (10 days @ 180,000) = 1,800,000; Days 15-29 (15 days @ 155,000) = 2,325,000.
     Total Feb sum = 4,605,000. Feb AMB = 4,605,000 / 29 = `158793.10`
   - Mar (31 days): Days 1-9 (9 days @ 155,000) = 1,395,000; Days 10-19 (10 days @ 225,000) = 2,250,000; Days 20-31 (12 days @ 190,000) = 2,280,000.
     Total Mar sum = 5,925,000. Mar AMB = 5,925,000 / 31 = `191129.03`
   - **Overall AMB (Weighted by 91 days)**:
     Total sum across 91 days = 3,840,000 + 4,605,000 + 5,925,000 = 14,370,000.
     $$\text{Overall AMB} = \frac{14370000}{91} = \mathbf{157912.09}$$
2. **Monthly Operating Inflows**:
   - Jan: `50000.00`, Feb: `60000.00`, Mar: `70000.00`. Total = `180000.00`. Mean $\mu = \mathbf{60000.00}$.
3. **Monthly Operating Outflows**:
   - Jan: `30000.00`, Feb: `25000.00`, Mar: `35000.00`. Total = `90000.00`. Mean = $\mathbf{30000.00}$.
4. **Volatility (Population CV)**:
   - Deviations from 60,000: $(-10000)^2 + (0)^2 + (10000)^2 = 200,000,000$.
   - Population variance = $200,000,000 / 3 = 66,666,666.6667$.
   - $\sigma = \sqrt{66666666.6667} = 8164.9658$.
   - $\text{CV} = 8164.9658 / 60000.00 = \mathbf{0.1361}$.
5. **Bounces**: Inward = `0`, Outward = `0`, Attempts = `0`, Bounce Rate = $\mathbf{0.0000}$.
6. **DSCR Proxy**:
   - Surplus = $60000.00 - 30000.00 = 30000.00$.
   - Debt Service = $10000.00 + 5000.00 = 15000.00$.
   - $\text{DSCR Proxy} = 30000.00 / 15000.00 = \mathbf{2.0000}$.
7. **FOIR**:
   - $\text{FOIR} = 15000.00 / 60000.00 = \mathbf{0.2500}$.
8. **Concentration**:
   - Alpha Corp: $50000 + 70000 = 120000$ (Share = $120000 / 180000 = 0.6667$).
   - Beta Ltd: $60000$ (Share = $60000 / 180000 = 0.3333$).
   - Top-1 Share = $\mathbf{0.6667}$. Top-3 Share = $\mathbf{1.0000}$.
   - $\text{HHI} = (66.67)^2 + (33.33)^2 = 4444.89 + 1110.89 = \mathbf{5555.78}$.
9. **GST vs Bank Turnover Ratio**: $180000.00 / 180000.00 = \mathbf{1.0000}$.

---

### Fixture 2: `FIX-02-STRESSED-BOUNCES` (3 Months, High Returns & Stressed)
- **Period**: 2024-04-01 to 2024-06-30 (91 active days: Apr 30, May 31, Jun 30).
- **Opening Balance**: `INR 25000.00`
- **Transactions**:
  - `2024-04-10`: Credit `30000.00`, Category: `SALES_RECEIPT`, Counterparty: "Buyer A" (Balance: `55000.00`)
  - `2024-04-15`: Debit `40000.00`, Category: `DEBT_SERVICE` (EMI) (Balance: `15000.00`)
  - `2024-05-02`: Debit `20000.00`, Category: `INWARD_CHEQUE_RETURN` (Reason: Insufficient funds, Narration: `CHQ RET INSUFFICIENT FUNDS`) (Balance: `15000.00`, un-debited / charge applied, net balance remains low)
  - `2024-05-10`: Credit `25000.00`, Category: `SALES_RECEIPT`, Counterparty: "Buyer A" (Balance: `40000.00`)
  - `2024-05-20`: Debit `35000.00`, Category: `VENDOR_PAYMENT` (Balance: `5000.00`)
  - `2024-06-05`: Credit `20000.00`, Category: `SALES_RECEIPT`, Counterparty: "Buyer A" (Balance: `25000.00`)
  - `2024-06-15`: Debit `22000.00`, Category: `INWARD_NACH_RETURN` (Narration: `NACH RET - BALANCE INSUFFICIENT`)
- **Inward Clearing Debit Attempts**: 4 (2 cleared EMI/vendor debits + 2 bounced inward returns).
- **Inward Returns Count**: `2`. **Outward Returns Count**: `0`.
- **Bounce Rate**: $2 / 4 = \mathbf{0.5000}$.
- **Average Monthly Operating Inflow**: $(30000 + 25000 + 20000) / 3 = \mathbf{25000.00}$.
- **Operating Outflows (Excluding EMIs)**: Apr: `0.00`, May: `35000.00`, Jun: `0.00`. Average = $\mathbf{11666.67}$.
- **Existing EMI**: `25000.00`, **Proposed EMI**: `10000.00` (Total: `35000.00`).
- **Surplus**: $25000.00 - 11666.67 = 13333.33$.
- **DSCR Proxy**: $13333.33 / 35000.00 = \mathbf{0.3810}$.
- **FOIR**: $35000.00 / 25000.00 = \mathbf{1.4000}$.

---

### Fixture 3: `FIX-03-ROUND-TRIP-EXCLUSION` (3 Months, Inflow Filtering)
- **Period**: 2024-01-01 to 2024-03-31 (91 active days).
- **Opening Balance**: `INR 50000.00`
- **Transactions**:
  - `2024-01-05`: Credit `100000.00`, Category: `SALES_RECEIPT`, Counterparty: "Client Regular" (Valid)
  - `2024-01-15`: Credit `200000.00`, Counterparty: "Entity Circle", Narration: `RTGS CR FROM ENTITY CIRCLE`
  - `2024-01-17`: Debit `198000.00`, Counterparty: "Entity Circle", Narration: `RTGS DR TO ENTITY CIRCLE`
    *(Diff = 1.0% <= 2.0%, within 2 days <= 3 days $\rightarrow$ **ROUND_TRIP EXCLUDED**)*
  - `2024-02-10`: Credit `500000.00`, Category: `LOAN_DISBURSAL`, Narration: `TERM LOAN DISB` (*Excluded: LOAN_DISBURSAL*)
  - `2024-02-20`: Credit `120000.00`, Category: `SALES_RECEIPT`, Counterparty: "Client Regular" (Valid)
  - `2024-03-10`: Credit `110000.00`, Category: `SALES_RECEIPT`, Counterparty: "Client Regular" (Valid)
- **Valid Operating Inflows**:
  - Jan: `100000.00`, Feb: `120000.00`, Mar: `110000.00`.
  - Total Valid Inflow = `330000.00`. Average Monthly Inflow = $\mathbf{110000.00}$.
- **Excluded Inflows**:
  - `ROUND_TRIP`: `200000.00`
  - `LOAN_DISBURSAL`: `500000.00`
  - Total Excluded Inflows = $\mathbf{700000.00}$.

---

### Fixture 4: `FIX-04-NEGATIVE-SURPLUS` (3 Months, Deficit Cash Flow)
- **Period**: 2024-01-01 to 2024-03-31 (91 active days).
- **Opening Balance**: `INR 100000.00`
- **Transactions**:
  - Inflows (SALES_RECEIPT): Jan: `40000.00`, Feb: `35000.00`, Mar: `45000.00`. Mean Inflow = $\mathbf{40000.00}$.
  - Operating Outflows (Vendor/Rent): Jan: `60000.00`, Feb: `55000.00`, Mar: `65000.00`. Mean Outflow = $\mathbf{60000.00}$.
- **Debt Service**: Existing EMI: `15000.00`, Proposed EMI: `5000.00` (Total = `20000.00`).
- **Operating Surplus**: $40000.00 - 60000.00 = -20000.00$.
- **DSCR Proxy**:
  $$\text{DSCR Proxy} = \frac{-20000.00}{20000.00} = \mathbf{-1.0000}$$
  Flag `is_negative_surplus`: `true` (Real negative value returned, not `INSUFFICIENT_DATA`).
- **FOIR**: $20000.00 / 40000.00 = \mathbf{0.5000}$.

---

### Fixture 5: `FIX-05-PARTIAL-MONTH-START` (Statement Starting Mid-Month)
- **Period**: 2024-01-16 to 2024-03-31 (Active days: Jan 16-31 [16 days], Feb [29 days], Mar [31 days] = 76 days).
- **Opening Balance (as of 2024-01-16)**: `INR 80000.00`
- **Transactions**:
  - `2024-01-20`: Credit `40000.00`, Category: `SALES_RECEIPT` (Balance: `120000.00`)
  - `2024-02-10`: Credit `90000.00`, Category: `SALES_RECEIPT` (Balance: `210000.00`)
  - `2024-03-05`: Credit `95000.00`, Category: `SALES_RECEIPT` (Balance: `305000.00`)
- **Daily AMB Calculation**:
  - Jan (16 active days): Days 16-19 (4 days @ 80,000) = 320,000; Days 20-31 (12 days @ 120,000) = 1,440,000.
    Total Jan Sum = 1,760,000. Jan AMB = 1,760,000 / 16 = `110000.00`.
  - Feb (29 active days): Days 1-9 (9 days @ 120,000) = 1,080,000; Days 10-29 (20 days @ 210,000) = 4,200,000.
    Total Feb Sum = 5,280,000. Feb AMB = 5,280,000 / 29 = `182068.97`.
  - Mar (31 active days): Days 1-4 (4 days @ 210,000) = 840,000; Days 5-31 (27 days @ 305,000) = 8,235,000.
    Total Mar Sum = 9,075,000. Mar AMB = 9,075,000 / 31 = `292741.94`.
  - **Overall Weighted AMB**:
    $$\text{Overall AMB} = \frac{1760000 + 5280000 + 9075000}{76} = \frac{16115000}{76} = \mathbf{212039.47}$$
- **Daily Average Carried Forward**: Every inactive day carries the previous day's balance. Partial start month is normalized strictly over active days.
