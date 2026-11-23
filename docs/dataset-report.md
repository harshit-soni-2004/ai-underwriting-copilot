# MSME Dataset Integrity & Coverage Report

**Total Applicants Generated:** 120

## 1. Decision Distribution per Archetype

| Archetype | Total | APPROVE | REFER | DECLINE |
|:---|---:|---:|---:|---:|
| `edge_cases` | 15 | 5 | 7 | 3 |
| `healthy` | 30 | 14 | 13 | 3 |
| `high_concentration` | 20 | 4 | 16 | 0 |
| `seasonal` | 20 | 4 | 16 | 0 |
| `stressed` | 20 | 0 | 9 | 11 |
| `thin_file` | 15 | 0 | 9 | 6 |
| **TOTAL** | **120** | **27** | **70** | **23** |

## 2. Policy Clause Coverage Matrix

Policy clauses must be triggered alone by at least 3 distinct applicants to guarantee isolated evaluation.

| Clause ID | Description | Alone Count (>= 3) | With Others Count | Total Triggers |
|:---|:---|---:|---:|---:|
| `ELIG-01` | Vintage >= 6m (DECLINE if <6m, REFER if 6-24m) | **16** | 0 | 16 |
| `ELIG-02` | Annual Turnover >= 25 Lakhs (DECLINE if <25L) | **3** | 0 | 3 |
| `FIN-01` | DSCR Proxy >= 1.25x (REFER if <1.25, DECLINE if <1.0) | **4** | 16 | 20 |
| `FIN-02` | AMB >= 10% of Proposed EMI (REFER if <10%) | **4** | 11 | 15 |
| `FIN-03` | Inward NACH/Cheque Dishonour = 0 (REFER if >0, DECLINE if >3) | **4** | 16 | 20 |
| `FIN-04` | FOIR <= 50.0% (REFER if >50%) | **4** | 11 | 15 |
| `FIN-05` | Top-1 Customer Inflow Concentration <= 40.0% (REFER if >40%) | **16** | 0 | 16 |
| `FIN-06` | Cash Flow Volatility CV <= 0.6000 (REFER if >0.60) | **16** | 0 | 16 |
| `FIN-07` | Round-Trip Excluded Credits <= 2.0% (REFER if >2%) | **5** | 0 | 5 |
| `DOC-02` | Bank vs GSTR-3B Turnover Discrepancy within [0.80, 1.20] (REFER if outside) | **5** | 0 | 5 |

## 3. Redefined Near-Threshold Applicants

Near-threshold rule: $|\text{metric} - \text{threshold}| \le 10\% \times \text{threshold}$ (or $\pm 1$ month for vintage).
Margin sign convention: **Positive** ($>0$) = passing side, **Negative** ($<0$) = failing side.

- **Total Near-Threshold Applicants:** 39 (Minimum requirement: $\ge 10$)
- **Clauses Covered on Both Sides:** 8 (Minimum requirement: $\ge 5$)

| Clause | Passing Applicants | Failing Applicants | Both Sides Covered? |
|:---|---:|---:|:---:|
| `ELIG-01` | 4 | 4 | YES |
| `ELIG-02` | 1 | 0 | NO |
| `FIN-01` | 1 | 1 | YES |
| `FIN-02` | 1 | 1 | YES |
| `FIN-03` | 0 | 0 | NO |
| `FIN-04` | 1 | 1 | YES |
| `FIN-05` | 4 | 6 | YES |
| `FIN-06` | 4 | 6 | YES |
| `FIN-07` | 1 | 1 | YES |
| `DOC-02` | 1 | 1 | YES |

### Detailed Near-Threshold Roster

| Applicant ID | Archetype | Clause | Metric Value | Threshold | Margin | Side | Decision |
|:---|:---|:---|---:|---:|---:|:---|:---|
| `APP-023-HEALTHY-NEAR-VINTAGE-PASS` | `healthy` | `ELIG-01` | 24 | 24 | `+0` | `just-passing` | `APPROVE` |
| `APP-024-HEALTHY-NEAR-VINTAGE-FAIL` | `healthy` | `ELIG-01` | 23 | 24 | `-1` | `just-failing` | `REFER` |
| `APP-025-HEALTHY-NEAR-DSCR-PASS` | `healthy` | `FIN-01` | 1.2625 | 1.2500 | `+0.0125` | `just-passing` | `APPROVE` |
| `APP-026-HEALTHY-NEAR-DSCR-FAIL` | `healthy` | `FIN-01` | 1.2040 | 1.2500 | `-0.0460` | `just-failing` | `REFER` |
| `APP-027-HEALTHY-NEAR-AMB-PASS` | `healthy` | `FIN-02` | 0.1050 | 0.1000 | `+0.0050` | `just-passing` | `APPROVE` |
| `APP-028-HEALTHY-NEAR-AMB-FAIL` | `healthy` | `FIN-02` | 0.0950 | 0.1000 | `-0.0050` | `just-failing` | `REFER` |
| `APP-029-HEALTHY-NEAR-FOIR-PASS` | `healthy` | `FIN-04` | 0.4743 | 0.5000 | `+0.0257` | `just-passing` | `APPROVE` |
| `APP-030-HEALTHY-NEAR-FOIR-FAIL` | `healthy` | `FIN-04` | 0.5263 | 0.5000 | `-0.0263` | `just-failing` | `REFER` |
| `APP-041-SEASONAL-NEAR-PASS-CV` | `seasonal` | `FIN-06` | 0.5689 | 0.6000 | `+0.0311` | `just-passing` | `APPROVE` |
| `APP-042-SEASONAL-NEAR-PASS-CV` | `seasonal` | `FIN-06` | 0.5689 | 0.6000 | `+0.0311` | `just-passing` | `APPROVE` |
| `APP-043-SEASONAL-NEAR-PASS-CV` | `seasonal` | `FIN-06` | 0.5689 | 0.6000 | `+0.0311` | `just-passing` | `APPROVE` |
| `APP-044-SEASONAL-NEAR-PASS-CV` | `seasonal` | `FIN-06` | 0.5689 | 0.6000 | `+0.0311` | `just-passing` | `APPROVE` |
| `APP-045-SEASONAL-NEAR-FAIL-CV` | `seasonal` | `FIN-06` | 0.6203 | 0.6000 | `-0.0203` | `just-failing` | `REFER` |
| `APP-046-SEASONAL-NEAR-FAIL-CV` | `seasonal` | `FIN-06` | 0.6203 | 0.6000 | `-0.0203` | `just-failing` | `REFER` |
| `APP-047-SEASONAL-NEAR-FAIL-CV` | `seasonal` | `FIN-06` | 0.6203 | 0.6000 | `-0.0203` | `just-failing` | `REFER` |
| `APP-048-SEASONAL-NEAR-FAIL-CV` | `seasonal` | `FIN-06` | 0.6203 | 0.6000 | `-0.0203` | `just-failing` | `REFER` |
| `APP-049-SEASONAL-NEAR-FAIL-CV` | `seasonal` | `FIN-06` | 0.6203 | 0.6000 | `-0.0203` | `just-failing` | `REFER` |
| `APP-050-SEASONAL-NEAR-FAIL-CV` | `seasonal` | `FIN-06` | 0.6203 | 0.6000 | `-0.0203` | `just-failing` | `REFER` |
| `APP-061-HIGH_CONCENTRATION-NEAR-PASS-TOP1` | `high_concentration` | `FIN-05` | 0.3750 | 0.4000 | `+0.0250` | `just-passing` | `APPROVE` |
| `APP-062-HIGH_CONCENTRATION-NEAR-PASS-TOP1` | `high_concentration` | `FIN-05` | 0.3750 | 0.4000 | `+0.0250` | `just-passing` | `APPROVE` |
| `APP-063-HIGH_CONCENTRATION-NEAR-PASS-TOP1` | `high_concentration` | `FIN-05` | 0.3750 | 0.4000 | `+0.0250` | `just-passing` | `APPROVE` |
| `APP-064-HIGH_CONCENTRATION-NEAR-PASS-TOP1` | `high_concentration` | `FIN-05` | 0.3750 | 0.4000 | `+0.0250` | `just-passing` | `APPROVE` |
| `APP-065-HIGH_CONCENTRATION-NEAR-FAIL-TOP1` | `high_concentration` | `FIN-05` | 0.4375 | 0.4000 | `-0.0375` | `just-failing` | `REFER` |
| `APP-066-HIGH_CONCENTRATION-NEAR-FAIL-TOP1` | `high_concentration` | `FIN-05` | 0.4375 | 0.4000 | `-0.0375` | `just-failing` | `REFER` |
| `APP-067-HIGH_CONCENTRATION-NEAR-FAIL-TOP1` | `high_concentration` | `FIN-05` | 0.4375 | 0.4000 | `-0.0375` | `just-failing` | `REFER` |
| `APP-068-HIGH_CONCENTRATION-NEAR-FAIL-TOP1` | `high_concentration` | `FIN-05` | 0.4375 | 0.4000 | `-0.0375` | `just-failing` | `REFER` |
| `APP-069-HIGH_CONCENTRATION-NEAR-FAIL-TOP1` | `high_concentration` | `FIN-05` | 0.4375 | 0.4000 | `-0.0375` | `just-failing` | `REFER` |
| `APP-070-HIGH_CONCENTRATION-NEAR-FAIL-TOP1` | `high_concentration` | `FIN-05` | 0.4375 | 0.4000 | `-0.0375` | `just-failing` | `REFER` |
| `APP-093-THIN_FILE-NEAR-DECLINE-VINTAGE` | `thin_file` | `ELIG-01` | 5 | 6 | `-1` | `just-failing` | `DECLINE` |
| `APP-094-THIN_FILE-NEAR-DECLINE-VINTAGE` | `thin_file` | `ELIG-01` | 5 | 6 | `-1` | `just-failing` | `DECLINE` |
| `APP-095-THIN_FILE-NEAR-DECLINE-VINTAGE` | `thin_file` | `ELIG-01` | 5 | 6 | `-1` | `just-failing` | `DECLINE` |
| `APP-096-THIN_FILE-NEAR-PASS-VINTAGE` | `thin_file` | `ELIG-01` | 6 | 6 | `+0` | `just-passing` | `REFER` |
| `APP-097-THIN_FILE-NEAR-PASS-VINTAGE` | `thin_file` | `ELIG-01` | 6 | 6 | `+0` | `just-passing` | `REFER` |
| `APP-098-THIN_FILE-NEAR-PASS-VINTAGE` | `thin_file` | `ELIG-01` | 6 | 6 | `+0` | `just-passing` | `REFER` |
| `APP-116-EDGE-NEAR-ROUNDTRIP-PASS` | `edge_cases` | `FIN-07` | 0.0190 | 0.0200 | `+0.0010` | `just-passing` | `APPROVE` |
| `APP-117-EDGE-NEAR-ROUNDTRIP-FAIL` | `edge_cases` | `FIN-07` | 0.0205 | 0.0200 | `-0.0005` | `just-failing` | `REFER` |
| `APP-118-EDGE-NEAR-DOC02-PASS` | `edge_cases` | `DOC-02` | 1.1900 | 1.2000 | `+0.0100` | `just-passing` | `APPROVE` |
| `APP-119-EDGE-NEAR-DOC02-FAIL` | `edge_cases` | `DOC-02` | 1.2100 | 1.2000 | `-0.0100` | `just-failing` | `REFER` |
| `APP-120-EDGE-NEAR-TURNOVER-PASS` | `edge_cases` | `ELIG-02` | 2584399.68 | 2500000.00 | `+84399.68` | `just-passing` | `APPROVE` |

## 4. Key Financial Metrics Range (Min / Median / Max)

| Archetype | Metric | Min | Median | Max |
|:---|:---|---:|---:|---:|
| `edge_cases` | Volatility CV | 0.0000 | 0.0000 | 0.3015 |
| `edge_cases` | Top-1 Share | 0.1354 | 0.1354 | 0.1364 |
| `edge_cases` | DSCR Proxy | 4.6906 | 6.4701 | 6.8733 |
| `edge_cases` | AMB (INR) | 592,787.23 | 3,150,352.05 | 3,953,751.78 |
| `edge_cases` | FOIR | 0.0691 | 0.0706 | 0.1157 |
| `edge_cases` | Vintage (months) | 39 | 52.0 | 58 |
| `healthy` | Volatility CV | 0.0000 | 0.0000 | 0.0000 |
| `healthy` | Top-1 Share | 0.1354 | 0.1354 | 0.1354 |
| `healthy` | DSCR Proxy | 0.8940 | 4.5633 | 6.8841 |
| `healthy` | AMB (INR) | 20,000.00 | 3,085,174.53 | 4,838,879.13 |
| `healthy` | FOIR | 0.0690 | 0.1621 | 0.5856 |
| `healthy` | Vintage (months) | 23 | 44.0 | 57 |
| `high_concentration` | Volatility CV | 0.0000 | 0.0000 | 0.0000 |
| `high_concentration` | Top-1 Share | 0.3750 | 0.5312 | 0.6250 |
| `high_concentration` | DSCR Proxy | 6.6846 | 6.8054 | 6.8841 |
| `high_concentration` | AMB (INR) | 2,969,827.73 | 3,122,937.91 | 3,223,730.19 |
| `high_concentration` | FOIR | 0.0690 | 0.0698 | 0.0711 |
| `high_concentration` | Vintage (months) | 36 | 49.0 | 58 |
| `seasonal` | Volatility CV | 0.5689 | 0.7324 | 0.8445 |
| `seasonal` | Top-1 Share | 0.1491 | 0.1521 | 0.1538 |
| `seasonal` | DSCR Proxy | 9.2243 | 10.6675 | 11.9708 |
| `seasonal` | AMB (INR) | 2,214,813.36 | 2,389,859.08 | 2,552,090.95 |
| `seasonal` | FOIR | 0.0512 | 0.0553 | 0.0602 |
| `seasonal` | Vintage (months) | 37 | 47.5 | 59 |
| `stressed` | Volatility CV | 0.0000 | 0.0000 | 0.0000 |
| `stressed` | Top-1 Share | 0.1354 | 0.1354 | 0.1354 |
| `stressed` | DSCR Proxy | 0.4373 | 0.4476 | 3.3259 |
| `stressed` | AMB (INR) | -282,538.55 | -118,944.39 | 1,670,755.03 |
| `stressed` | FOIR | 0.0691 | 0.5136 | 0.5256 |
| `stressed` | Vintage (months) | 36 | 53.5 | 59 |
| `thin_file` | Volatility CV | 0.0000 | 0.0000 | 0.0000 |
| `thin_file` | Top-1 Share | 0.1354 | 0.1354 | 0.1354 |
| `thin_file` | DSCR Proxy | 6.7457 | 11.7515 | 12.0377 |
| `thin_file` | AMB (INR) | 2,873,556.15 | 2,946,899.45 | 3,180,625.82 |
| `thin_file` | FOIR | 0.0395 | 0.0404 | 0.0704 |
| `thin_file` | Vintage (months) | 4 | 6.0 | 9 |

## 5. Stressed Archetype Combinations Breakdown

Asserts multiple distinct clause failure profiles among stressed applicants:

| Count | Triggered Clause Combination | Decision |
|---:|:---|:---|
| 4 | `FIN-03` | `DECLINE` |
| 5 | `FIN-01`, `FIN-03` | `DECLINE` |
| 11 | `FIN-01`, `FIN-02`, `FIN-03`, `FIN-04` | `DECLINE` |

