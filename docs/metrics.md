# MSME Underwriting Financial Metrics Specification & Verification Contract
**Version:** 1.3.0  
**Status:** Approved Reference Standard for Deterministic Metrics Engine (Java & Python)

---

## 1. Core Principles
1. **The LLM Never Does Math**: All ratios, balances, volatility, and policy thresholds are computed deterministically. The LLM only interprets, explains, and cites verified metrics.
2. **Deterministic Arithmetic Precision**:
   - Currency: Scaled to 2 decimal places with `HALF_UP` rounding (INR).
   - Ratios, Shares, and Volatility (CV): Scaled to 4 decimal places with `HALF_UP` rounding.
   - Indices (HHI): Scaled to 2 decimal places with `HALF_UP` rounding.
   - In Java: Exclusively `BigDecimal` and `MathContext.DECIMAL128`. No floating-point (`double`/`float`) for currency or financial ratios.
   - Population Standard Deviation: Evaluated with $N$ denominator ($\text{ddof}=0$).

---

## 2. Transaction Category Treatment Matrix (Java Input Contract)

Every transaction category encountered in `transactions.json` must be processed according to this strict deterministic contract:

| Transaction Category | Direction | Operating Inflow | Operating Outflow | AMB / Running Balance | Inward Clearing Attempts | Inward Dishonour Returns | Outward Cheque Returns | Counterparty Concentration |
|---|---|---|---|---|---|---|---|---|
| `SALES_RECEIPT` | CREDIT | **INCLUDED** (unless round-trip) | Excluded | Credit (+) | No | No | No | **INCLUDED** (Buyer Shares, HHI) |
| `VENDOR_PAYMENT` | DEBIT | Excluded | **INCLUDED** | Debit (-) | No | No | No | Excluded |
| `DEBT_SERVICE` | DEBIT | Excluded | Excluded (in Debt Service denom) | Debit (-) | **Yes (+1)** | No | No | Excluded |
| `INWARD_CHEQUE_RETURN` | DEBIT | Excluded | Excluded | Debit (-) | **Yes (+1)** | **Yes (+1)** | No | Excluded |
| `INWARD_NACH_RETURN` | DEBIT | Excluded | Excluded | Debit (-) | **Yes (+1)** | **Yes (+1)** | No | Excluded |
| `INWARD_ECS_RETURN` | DEBIT | Excluded | Excluded | Debit (-) | **Yes (+1)** | **Yes (+1)** | No | Excluded |
| `OUTWARD_CHEQUE_RETURN` | DEBIT | Excluded | Excluded | Debit (-) | No | No | **Yes (+1)** | Excluded |
| `BANK_CHARGES` | DEBIT | Excluded | **INCLUDED** | Debit (-) | No | No | No | Excluded |
| `TAX_PAYMENT` | DEBIT | Excluded | **INCLUDED** | Debit (-) | No | No | No | Excluded |
| `UTILITIES` / `RENT` / `SALARIES` | DEBIT | Excluded | **INCLUDED** | Debit (-) | No | No | No | Excluded |
| `OWN_ACCOUNT_TRANSFER` | DEBIT | Excluded | Excluded (Treasury Sweep) | Debit (-) | No | No | No | Excluded |
| `OWN_ACCOUNT_TRANSFER` | CREDIT | Excluded (`OWN_ACCOUNT_TRANSFER`) | Excluded | Credit (+) | No | No | No | Excluded |
| `DIVIDEND` / `INVESTMENT` | DEBIT | Excluded | Excluded (Capital Distribution) | Debit (-) | No | No | No | Excluded |
| `ONE_OFF` / `ASSET_SALE` | CREDIT | Excluded (`ONE_OFF`) | Excluded | Credit (+) | No | No | No | Excluded |
| `LOAN_DISBURSAL` | CREDIT | Excluded (`LOAN_DISBURSAL`) | Excluded | Credit (+) | No | No | No | Excluded |
| `CAPITAL_INFUSION` | CREDIT | Excluded (`CAPITAL_INFUSION`) | Excluded | Credit (+) | No | No | No | Excluded |
| `REFUND_REVERSAL` | CREDIT | Excluded (`REFUND_REVERSAL`) | Excluded | Credit (+) | No | No | No | Excluded |

---

## 3. Metric Formulations

### 3.1 Average Monthly Balance (AMB)
$$\text{AMB} = \frac{\sum_{d=1}^D \text{Closing Ledger Balance}_d}{D}$$
- **Daily Carry-Forward**: On days without transactions, the previous day's closing ledger balance is carried forward.
- **Partial First/Last Months**: All calendar days within the statement period ($[\text{start\_date}, \text{end\_date}]$) are included in the denominator $D$.

### 3.2 Operating Cash Inflow & Outflow
- **Operating Inflow**: Sum of `SALES_RECEIPT` credits, excluding verified round-trips.
- **Operating Outflow**: Sum of operating debits (`VENDOR_PAYMENT`, `BANK_CHARGES`, `TAX_PAYMENT`, etc.), excluding debt service, return penalties, and non-operational transfers.
- **Operating Surplus**: $\text{Monthly Operating Surplus} = \text{Average Monthly Operating Inflow} - \text{Average Monthly Operating Outflow}$.

### 3.3 Cash Flow Volatility (CV)
$$\mu = \frac{1}{M} \sum_{m=1}^M \text{Inflow}_m, \quad \sigma = \sqrt{\frac{1}{M} \sum_{m=1}^M (\text{Inflow}_m - \mu)^2}, \quad \text{CV} = \frac{\sigma}{\mu}$$
- **Zero-Inflow Months**: A month with zero sales receipts is assigned $\text{Inflow}_m = \text{INR } 0.00$ and included in $M$. It is never dropped.
- **ddof=0**: Population standard deviation is used in both Python and Java.

### 3.4 Inward vs. Outward Returns & Bounce Rate
1. **Inward Clearing Returns (`inward_clearing_returns_count`)**: Applicant's issued instrument/debit failed (insufficient balance).
2. **Outward Cheque Returns (`outward_cheque_returns_count`)**: Customer's deposited cheque returned unpaid.
3. **Bounce Rate**:
   $$\text{Bounce Rate} = \frac{\text{inward\_clearing\_returns\_count}}{\text{total inward debit attempts}}$$

### 3.5 Debt Service Coverage Ratio (DSCR Proxy)
$$\text{DSCR Proxy} = \frac{\text{Average Monthly Operating Inflow} - \text{Average Monthly Operating Outflow}}{\text{Existing Monthly EMIs} + \text{Proposed Monthly Loan EMI}}$$
- If surplus $\le 0$, the real value ($\le 0$) is returned with `is_negative_surplus: true`.

### 3.6 Fixed Obligation to Income Ratio (FOIR)
$$\text{FOIR} = \frac{\text{Existing Monthly EMIs} + \text{Proposed Monthly Loan EMI}}{\text{Average Monthly Operating Inflow}}$$
- **Mathematical Identity Relation**:
  $$\text{DSCR} \times \text{FOIR} = \frac{\text{Operating Surplus}}{\text{Average Monthly Operating Inflow}}$$

### 3.7 Concentration & Round-Trip Ratio
- **Top-1 Concentration Share**: Inflow from largest single buyer / Total Operating Inflow.
- **Top-3 Concentration Share**: Inflows from top 3 buyers / Total Operating Inflow.
- **HHI**: $\sum (s_i \times 100)^2$ computed with exact unrounded ratios.
- **Round-Trip Ratio (`round_trip_ratio`)**: Excluded Round-Trip Credits / Gross Total Credits.

### 3.8 GST vs Bank Turnover Discrepancy Band (`DOC-02`)
$$\text{GST Turnover Ratio} = \frac{\text{GSTR-3B Annual Taxable Supplies}}{\text{Bank Annual Operating Inflow}}$$
- Acceptable Band: $[0.8000, 1.2000]$ ($|\text{Ratio} - 1.0| \le 0.2000$). Outside band triggers `REFER`.

---

## 4. Policy Decision Hierarchy & Near-Threshold Definitions

### 4.1 Strict Precedence: $\text{DECLINE} > \text{REFER} > \text{APPROVE}$
1. **`DECLINE` Clauses**:
   - `ELIG-01`: Vintage < 6 months
   - `ELIG-02`: Annual turnover < INR 25,00,000
   - `FIN-01`: DSCR proxy < 1.0000
   - `FIN-03`: Inward clearing returns > 3 instances
2. **`REFER` Clauses**:
   - `ELIG-01`: Vintage 6 to 23 months
   - `FIN-01`: DSCR proxy 1.0000 to 1.2499
   - `FIN-02`: AMB to Proposed EMI ratio < 0.1000
   - `FIN-03`: Inward returns 1 to 3 instances
   - `FIN-04`: FOIR > 0.5000
   - `FIN-05`: Top-1 share > 0.4000
   - `FIN-06`: Volatility CV > 0.6000
   - `FIN-07`: Round-trip ratio > 0.0200
   - `DOC-02`: GST turnover ratio < 0.8000 or > 1.2000
3. **`APPROVE`**: Zero decline and zero referral triggers, DSCR $\ge 1.50$, and clean banking history.

### 4.2 Near-Threshold Definition & Margin Sign Convention
- **Continuous Metrics**: An applicant is near-threshold if $|\text{metric} - \text{threshold}| \le 0.10 \times \text{threshold}$.
- **Discrete / Vintage Metrics**:
  - `ELIG-01`: Within $\pm 2$ months of 24m, or $\pm 1$ month of 6m.
  - `FIN-03`: 0 vs 1 returns (referral boundary), 3 vs 4 returns (decline boundary).
  - `DOC-02`: Within $\pm 0.0200$ of band edges ($[0.78, 0.82]$ or $[1.18, 1.22]$).
- **Margin Sign Convention**:
  - $\mathbf{\text{Margin} \ge 0}$: **Passing / compliant side**.
  - $\mathbf{\text{Margin} < 0}$: **Failing / policy-triggering side**.

---

## 5. Canonical Hand-Worked Reference Fixtures (`data/fixtures/handworked/`)

### Fixture 1: `FIX-01-CLEAN-GROWTH` (3 Months, Healthy)
- **Period**: 2024-01-01 to 2024-03-31 (91 active days). Opening: `100000.00`.
- Inflows: Jan `50000.00`, Feb `60000.00`, Mar `70000.00`. Outflows: Jan `30000.00`, Feb `25000.00`, Mar `35000.00`.
- Existing EMI: `10000.00`, Proposed EMI: `5000.00`. GSTR-3B: `180000.00`.
- **Results**: AMB = `157912.09`, Mean Inflow = `60000.00`, Mean Outflow = `30000.00`, CV = `0.1361`, Bounces = 0, DSCR = `2.0000`, FOIR = `0.2500`, Top-1 = `0.6667`, HHI = `5555.56`, GST Ratio = `1.0000`.

### Fixture 2: `FIX-02-STRESSED-BOUNCES` (3 Months, High Returns)
- Inflows: `25000.00` avg. Outflows: `11666.67` avg (excludes inward return debits).
- Inward returns = 2, Outward returns = 0, Attempts = 4, Bounce Rate = `0.5000`.
- Debt Service = `35000.00`. Surplus = `13333.33`.
- **Results**: DSCR = `0.3810`, FOIR = `1.4000`.

### Fixture 3: `FIX-03-ROUND-TRIP-EXCLUSION` (3 Months, Inflow Filtering)
- Round-trip matching pair (`200000.00` Cr, `198000.00` Dr within 2 days) excluded as `ROUND_TRIP`.
- Term loan disbursal (`500000.00`) excluded as `LOAN_DISBURSAL`.
- Valid Operating Inflow: `110000.00` avg.

### Fixture 4: `FIX-04-NEGATIVE-SURPLUS` (3 Months, Deficit Cash Flow)
- Mean Inflow: `40000.00`, Mean Outflow: `60000.00`. Debt Service: `20000.00`.
- Surplus: `-20000.00`.
- **Results**: DSCR = `-1.0000`, `is_negative_surplus`: `true`, FOIR = `0.5000`.

### Fixture 5: `FIX-05-PARTIAL-MONTH-START` (Mid-Month Start)
- Active days: Jan 16-31 (16 days), Feb (29 days), Mar (31 days) = 76 days.
- **Results**: Weighted AMB = `212039.47`.

### Fixture 6: `FIX-06-ZERO-INFLOW-MONTH` (3 Months, Zero-Inflow Month)
- Inflows: Jan `100000.00`, Feb `0.00`, Mar `100000.00` (Equal months with one zero).
- Mean Inflow $\mu = \frac{200000}{3} \approx 66666.67$.
- Deviations: $+33333.33, -66666.67, +33333.33$.
- Sum of Squares: $(10^5/3)^2 + (-2 \times 10^5/3)^2 + (10^5/3)^2 = \frac{6 \times 10^{10}}{9} = \frac{2}{3} \times 10^{10}$.
- Population Variance $\sigma^2 = \frac{2}{9} \times 10^{10}$, Std Dev $\sigma = \frac{\sqrt{2}}{3} \times 10^5 \approx 47140.45$.
- **Exact Closed Form**:
  $$\text{CV} = \frac{\sigma}{\mu} = \frac{\frac{\sqrt{2}}{3}}{\frac{2}{3}} = \frac{1}{\sqrt{2}} \approx \mathbf{0.7071}$$
*(Note: If March inflow is INR 80,000 instead of 100,000, $\mu = 60000.00, \sigma = 43204.94$, giving $\text{CV} = \mathbf{0.7201}$)*.
