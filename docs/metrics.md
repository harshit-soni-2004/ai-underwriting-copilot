# Deterministic Financial Metrics Specification

*Classification: Technical Specification & Financial Math Standard*  
*Document Version: 1.1.0*  
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
- **Overdraft / Cash Credit (OD/CC) Realism Assumption**: In real banking, accounts with sanctioned OD/CC limits allow ledger balances to drop below zero up to `-OD_LIMIT`. Attempts to draw beyond the OD limit are dishonoured (inward returns) or capped, preventing unbounded mathematical negative drift.

---

### 2.2 Monthly Operating Inflow & Excluded Inflows
- **Operating Inflow Definition**: Measures genuine commercial turnover. Counts **only** credit transactions categorized as `SALES_RECEIPT` (customer payments, collections, receivables).
- **Excluded Credits Breakdown**: The engine must categorize and track all non-operating credits into distinct breakdown buckets:
  1. `ONE_OFF`: One-off asset sales, equipment liquidations, or non-recurring windfalls.
  2. `ROUND_TRIP`: Artificial turnover inflation. Defined as a credit transaction where a matching debit occurs with the same counterparty, within $\pm 2\%$ of the amount, within $N$ days (default $N = 3$).
  3. `LOAN_DISBURSAL`: Disbursal of loans or credit lines.
  4. `CAPITAL_INFUSION`: Owner/equity capital infusion.
  5. `OWN_ACCOUNT_TRANSFER`: Contra transfers from accounts belonging to the same entity.
  6. `REFUND_REVERSAL`: Tax refunds, merchant chargeback reversals, or operational refunds.

---

### 2.3 Monthly Operating Outflow
- **Definition**: Sum of genuine business expenses and operational debits (vendor payments, payroll, utilities, rent, supplies).
- **Exclusion**: **Excludes debt service obligations** (existing loan EMIs, interest debits, credit line repayments) to avoid double-counting in coverage ratios, and excludes inward cheque return penalty fees.
- **Formula**:
  $$\text{Operating Outflow}_m = \sum_{t \in \text{Debits}_m \setminus \text{DEBT\_SERVICE}} \text{Amount}_t$$

---

### 2.4 Cash-Flow Volatility & Zero-Inflow Months
- **Definition**: The Coefficient of Variation ($\text{CV}$) of **monthly operating inflows** over the evaluation period ($M$ months).
- **Formula**:
  $$\text{CV} = \frac{\sigma_{\text{operating\_inflow}}}{\mu_{\text{operating\_inflow}}}$$
  where:
  - $\mu = \frac{1}{M} \sum_{m=1}^M \text{Operating Inflow}_m$
  - $\sigma$ is the **population standard deviation** ($\text{ddof} = 0$):
    $$\sigma = \sqrt{\frac{1}{M} \sum_{m=1}^M (\text{Operating Inflow}_m - \mu)^2}$$
- **Zero-Inflow Months Rule**: A month without any operating sales credit is **never dropped** from the evaluation series. It enters the monthly inflow array with value `INR 0.00`. It contributes to $M$, pulls down the mean $\mu$, and increases $\sigma$, resulting in a naturally elevated CV (e.g. CV $\ge 0.35$).
- **Zero / Negative Inflow Safeguard**: If $\mu \le 0$ or $M < 3$, the engine returns `status: INSUFFICIENT_DATA` with reason `INSUFFICIENT_OR_ZERO_INFLOW_HISTORY`.

---

### 2.5 Bounced Cheque / Inward Return Metrics
1. **Inward Clearing Returns (`inward_clearing_returns_count`)**:
   - Represents cheques, NACH, or ECS debits **issued by the applicant** to vendors, lenders, or third parties that were **dishonoured due to insufficient funds**.
2. **Outward Cheque Returns (`outward_cheque_returns_count`)**:
   - Represents cheques **received from customers** and deposited by the applicant that were returned unpaid by the drawer's bank.
3. **Inward Bounce Rate (`bounce_rate`)**:
   $$\text{Bounce Rate} = \frac{\text{inward\_clearing\_returns\_count}}{\text{total inward cheque + ECS + NACH debit attempts}}$$

---

### 2.6 Debt Service Coverage Ratio (DSCR Proxy)
$$\text{DSCR Proxy} = \frac{\text{Average Monthly Operating Inflow} - \text{Average Monthly Operating Outflow}}{\text{Average Existing Monthly EMIs} + \text{Proposed Monthly Loan EMI}}$$
- **Negative Surplus Handling**: If operational surplus $\le 0$, the engine calculates and returns the real value ($\le 0$) with flag `is_negative_surplus: true`.

---

### 2.7 Fixed Obligation to Income Ratio (FOIR)
$$\text{FOIR} = \frac{\text{Average Existing Monthly EMIs} + \text{Proposed Monthly Loan EMI}}{\text{Average Monthly Operating Inflow}}$$

---

### 2.8 Counterparty Concentration
1. **Top-1 Concentration Share**: Inflows from largest single customer / Total 12-Month Inflows.
2. **Top-3 Concentration Share**: Inflows from top 3 customers combined / Total 12-Month Inflows.
3. **Herfindahl-Hirschman Index (HHI)**: $\sum_{i=1}^K (s_i \times 100)^2$.

---

### 2.9 GST vs Bank Turnover Discrepancy Ratio
$$\text{GST Turnover Ratio} = \frac{\text{Annual GSTR-3B Taxable Supplies}}{\text{Annual Bank Operating Inflow}}$$

---

## 3. Six Hand-Worked Reference Fixtures

### Fixture 1: `FIX-01-CLEAN-GROWTH` (3 Months, Healthy)
- **Period**: 2024-01-01 to 2024-03-31 (91 active days). Opening: `100000.00`.
- Inflows: Jan `50000.00`, Feb `60000.00`, Mar `70000.00`. Outflows: Jan `30000.00`, Feb `25000.00`, Mar `35000.00`.
- Existing EMI: `10000.00`, Proposed EMI: `5000.00`. GSTR-3B: `180000.00`.
- **Results**:
  - AMB: `157912.09`
  - Mean Operating Inflow: `60000.00`, Mean Operating Outflow: `30000.00`
  - Volatility CV: `0.1361`
  - Bounce Rate: `0.0000` (Inward = 0, Outward = 0)
  - DSCR Proxy: `2.0000`, FOIR: `0.2500`
  - Top-1 Share: `0.6667`, Top-3: `1.0000`, HHI: `5555.78`
  - GST Ratio: `1.0000`

---

### Fixture 2: `FIX-02-STRESSED-BOUNCES` (3 Months, High Returns)
- Inflows: `25000.00` avg. Outflows (excl. EMIs/returns): `11666.67` avg.
- Inward returns: `2`, Outward returns: `0`, Attempts: `4`, Bounce Rate: `0.5000`.
- Debt Service: `35000.00`. Surplus: `13333.33`.
- **Results**: DSCR = `0.3810`, FOIR = `1.4000`.

---

### Fixture 3: `FIX-03-ROUND-TRIP-EXCLUSION` (3 Months, Inflow Filtering)
- Round-trip matching pair (`200000.00` Cr, `198000.00` Dr within 2 days) excluded as `ROUND_TRIP`.
- Term loan disbursal (`500000.00`) excluded as `LOAN_DISBURSAL`.
- Valid Operating Inflow: `110000.00` avg.

---

### Fixture 4: `FIX-04-NEGATIVE-SURPLUS` (3 Months, Deficit Cash Flow)
- Mean Inflow: `40000.00`, Mean Outflow: `60000.00`. Debt Service: `20000.00`.
- Surplus: `-20000.00`.
- **Results**: DSCR = `-1.0000`, `is_negative_surplus`: `true`, FOIR = `0.5000`.

---

### Fixture 5: `FIX-05-PARTIAL-MONTH-START` (Mid-Month Start)
- Active days: Jan 16-31 (16 days), Feb (29 days), Mar (31 days) = 76 days.
- **Results**: Weighted AMB = `212039.47`.

---

### Fixture 6: `FIX-06-ZERO-INFLOW-MONTH` (3 Months, Zero-Inflow Month)
- **Period**: 2024-01-01 to 2024-03-31 (91 active days).
- Inflows:
  - Jan: `100000.00` (SALES_RECEIPT)
  - Feb: `0.00` (Zero sales receipts, month strictly preserved in evaluation)
  - Mar: `80000.00` (SALES_RECEIPT)
- Total Inflows: `180000.00`. Total Months $M = 3$.
- Mean Inflow $\mu$: $180000.00 / 3 = \mathbf{60000.00}$.
- **Population Variance ($\text{ddof} = 0$)**:
  - Jan deviation: $(100000 - 60000)^2 = 1,600,000,000$
  - Feb deviation: $(0 - 60000)^2 = 3,600,000,000$
  - Mar deviation: $(80000 - 60000)^2 = 400,000,000$
  - Variance $\sigma^2$: $\frac{1600000000 + 3600000000 + 400000000}{3} = \frac{5600000000}{3} = 1,866,666,666.6667$
  - $\sigma = \sqrt{1866666666.6667} = 43204.9379$
  - $\text{CV} = \frac{43204.9379}{60000.00} = \mathbf{0.7201}$.
