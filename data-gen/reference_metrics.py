"""
Reference Financial Metrics Oracle (Python implementation).
Independent implementation using decimal.Decimal with ROUND_HALF_UP.
Serves as the ground-truth oracle to cross-check the core-service Java engine.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import math

CURRENCY_QUANT = Decimal("0.01")
RATIO_QUANT = Decimal("0.0001")
INDEX_QUANT = Decimal("0.01")

def quantize_money(val: Decimal) -> Decimal:
    return val.quantize(CURRENCY_QUANT, rounding=ROUND_HALF_UP)

def quantize_ratio(val: Decimal) -> Decimal:
    return val.quantize(RATIO_QUANT, rounding=ROUND_HALF_UP)

def quantize_index(val: Decimal) -> Decimal:
    return val.quantize(INDEX_QUANT, rounding=ROUND_HALF_UP)

def decimal_sqrt(d: Decimal) -> Decimal:
    """Exact population standard deviation square root using Decimal."""
    if d <= Decimal("0"):
        return Decimal("0.0")
    # Newton-Raphson for Decimal sqrt
    s = d
    x = (s + Decimal("1")) / Decimal("2")
    for _ in range(50):
        next_x = (x + s / x) / Decimal("2")
        if abs(next_x - x) < Decimal("1e-12"):
            break
        x = next_x
    return x

class ReferenceMetricsOracle:
    """
    Computes verified financial metrics deterministically from transaction records.
    All calculations strictly use decimal.Decimal.
    """

    @classmethod
    def calculate_all(
        cls,
        transactions: List[Dict[str, Any]],
        opening_balance: Decimal,
        statement_start_date: date,
        statement_end_date: date,
        existing_monthly_emi: Decimal,
        proposed_monthly_emi: Decimal,
        gstr3b_annual_taxable_supplies: Optional[Decimal] = None,
        round_trip_window_days: int = 3,
        round_trip_tolerance_pct: Decimal = Decimal("0.02")
    ) -> Dict[str, Any]:
        """
        Main calculation orchestrator matching docs/metrics.md formulas.
        """
        # Parse and sort transactions chronologically
        parsed_txns = []
        for t in transactions:
            t_date = datetime.strptime(t["date"], "%Y-%m-%d").date()
            parsed_txns.append({
                "date": t_date,
                "amount": Decimal(str(t["amount"])),
                "type": t["type"],  # "CREDIT" or "DEBIT"
                "category": t.get("category", "OTHER"),
                "counterparty": t.get("counterparty", "UNKNOWN"),
                "narration": t.get("narration", "")
            })
        parsed_txns.sort(key=lambda x: x["date"])

        # 1. Round-Trip Inflow Filtering
        excluded_inflows_by_reason: Dict[str, Decimal] = defaultdict(Decimal)
        round_trip_indices = set()

        # Identify round trips: credit and debit with same counterparty, within tolerance, within window
        for i, t_cr in enumerate(parsed_txns):
            if t_cr["type"] == "CREDIT":
                c_party = t_cr["counterparty"].strip().upper()
                if c_party and c_party != "UNKNOWN":
                    cr_amt = t_cr["amount"]
                    for j, t_dr in enumerate(parsed_txns):
                        if i != j and t_dr["type"] == "DEBIT":
                            d_party = t_dr["counterparty"].strip().upper()
                            if c_party == d_party:
                                day_diff = abs((t_cr["date"] - t_dr["date"]).days)
                                if day_diff <= round_trip_window_days:
                                    dr_amt = t_dr["amount"]
                                    if cr_amt > 0:
                                        pct_diff = abs(cr_amt - dr_amt) / cr_amt
                                        if pct_diff <= round_trip_tolerance_pct:
                                            round_trip_indices.add(i)
                                            excluded_inflows_by_reason["ROUND_TRIP"] += cr_amt
                                            break

        # 2. Inflow / Outflow Monthly Aggregation & Filtering
        monthly_operating_inflows: Dict[str, Decimal] = defaultdict(Decimal)
        monthly_operating_outflows: Dict[str, Decimal] = defaultdict(Decimal)
        counterparty_inflows: Dict[str, Decimal] = defaultdict(Decimal)

        # Inward/Outward clearing return counts
        inward_clearing_returns_count = 0
        outward_cheque_returns_count = 0
        total_inward_clearing_attempts = 0

        for idx, t in enumerate(parsed_txns):
            month_key = t["date"].strftime("%Y-%m")

            if t["type"] == "CREDIT":
                if idx in round_trip_indices:
                    continue  # already marked as ROUND_TRIP
                
                cat = t["category"]
                if cat == "SALES_RECEIPT":
                    monthly_operating_inflows[month_key] += t["amount"]
                    c_party = t["counterparty"].strip()
                    if c_party:
                        counterparty_inflows[c_party] += t["amount"]
                else:
                    # Categorize excluded reason
                    if cat in ["LOAN_DISBURSAL", "CAPITAL_INFUSION", "OWN_ACCOUNT_TRANSFER", 
                               "REFUND_REVERSAL", "ASSET_SALE"]:
                        excluded_inflows_by_reason[cat] += t["amount"]
                    else:
                        excluded_inflows_by_reason["OTHER_NON_OPERATING"] += t["amount"]

            elif t["type"] == "DEBIT":
                cat = t["category"]
                narr = t["narration"].upper()

                # Check for clearing debit attempts (cheque, ECS, NACH, EMI)
                is_clearing_attempt = any(k in narr for k in ["CHQ", "CHEQUE", "ECS", "NACH", "EMI", "LOAN"]) or \
                                      cat in ["DEBT_SERVICE", "INWARD_CHEQUE_RETURN", "INWARD_NACH_RETURN", "INWARD_ECS_RETURN"]
                if is_clearing_attempt:
                    total_inward_clearing_attempts += 1

                # Check returns
                if cat in ["INWARD_CHEQUE_RETURN", "INWARD_NACH_RETURN", "INWARD_ECS_RETURN"] or \
                   ("CHQ RET" in narr and "INSUFFICIENT" in narr) or ("RETURN" in narr and "INSUFFICIENT" in narr):
                    inward_clearing_returns_count += 1
                elif cat == "OUTWARD_CHEQUE_RETURN" or ("DEP RET" in narr or "OUTWARD RET" in narr):
                    outward_cheque_returns_count += 1

                # Operating outflows exclude DEBT_SERVICE and inward return transactions
                if cat not in ["DEBT_SERVICE", "INWARD_CHEQUE_RETURN", "INWARD_NACH_RETURN", "INWARD_ECS_RETURN"]:
                    monthly_operating_outflows[month_key] += t["amount"]

        # Ensure all months in span are represented (even if 0)
        curr = statement_start_date.replace(day=1)
        all_month_keys = []
        while curr <= statement_end_date:
            m_str = curr.strftime("%Y-%m")
            all_month_keys.append(m_str)
            if m_str not in monthly_operating_inflows:
                monthly_operating_inflows[m_str] = Decimal("0.00")
            if m_str not in monthly_operating_outflows:
                monthly_operating_outflows[m_str] = Decimal("0.00")
            # advance month
            next_m = curr.month % 12 + 1
            next_y = curr.year + (1 if curr.month == 12 else 0)
            curr = date(next_y, next_m, 1)

        total_months = len(all_month_keys)

        # 3. Daily Average Balance & AMB
        # Build day-by-day closing balances with carry-forward
        daily_balances: Dict[date, Decimal] = {}
        curr_day = statement_start_date
        running_bal = opening_balance

        txn_by_date = defaultdict(list)
        for t in parsed_txns:
            txn_by_date[t["date"]].append(t)

        while curr_day <= statement_end_date:
            if curr_day in txn_by_date:
                for t in txn_by_date[curr_day]:
                    if t["type"] == "CREDIT":
                        running_bal += t["amount"]
                    else:
                        running_bal -= t["amount"]
            daily_balances[curr_day] = running_bal
            curr_day += timedelta(days=1)

        total_active_days = len(daily_balances)
        if total_active_days == 0:
            overall_amb = opening_balance
        else:
            sum_daily_balances = sum(daily_balances.values(), Decimal("0.00"))
            overall_amb = sum_daily_balances / Decimal(str(total_active_days))

        # 4. Volatility (CV of monthly operating inflows)
        inflow_values = [monthly_operating_inflows[m] for m in all_month_keys]
        total_operating_inflows = sum(inflow_values, Decimal("0.00"))
        avg_monthly_inflow = total_operating_inflows / Decimal(str(total_months)) if total_months > 0 else Decimal("0.00")

        outflow_values = [monthly_operating_outflows[m] for m in all_month_keys]
        total_operating_outflows = sum(outflow_values, Decimal("0.00"))
        avg_monthly_outflow = total_operating_outflows / Decimal(str(total_months)) if total_months > 0 else Decimal("0.00")

        if total_months < 3 or avg_monthly_inflow <= Decimal("0"):
            volatility_cv = None
            volatility_status = "INSUFFICIENT_DATA"
        else:
            # Population variance (ddof=0)
            variance = sum(((x - avg_monthly_inflow) ** 2 for x in inflow_values), Decimal("0")) / Decimal(str(total_months))
            std_dev = decimal_sqrt(variance)
            volatility_cv = std_dev / avg_monthly_inflow
            volatility_status = "SUCCESS"

        # 5. Bounce Rate
        if total_inward_clearing_attempts > 0:
            bounce_rate = Decimal(str(inward_clearing_returns_count)) / Decimal(str(total_inward_clearing_attempts))
        else:
            bounce_rate = Decimal("0.0000")

        # 6. DSCR Proxy
        total_monthly_debt = existing_monthly_emi + proposed_monthly_emi
        monthly_surplus = avg_monthly_inflow - avg_monthly_outflow
        is_negative_surplus = monthly_surplus < Decimal("0")

        if total_monthly_debt <= Decimal("0"):
            dscr_proxy = None
            dscr_status = "INSUFFICIENT_DATA"
        else:
            dscr_proxy = monthly_surplus / total_monthly_debt
            dscr_status = "SUCCESS"

        # 7. FOIR
        if avg_monthly_inflow <= Decimal("0"):
            foir = None
            foir_status = "INSUFFICIENT_DATA"
        else:
            foir = total_monthly_debt / avg_monthly_inflow
            foir_status = "SUCCESS"

        # 8. Counterparty Concentration
        if total_operating_inflows > Decimal("0"):
            sorted_parties = sorted(counterparty_inflows.values(), reverse=True)
            top1_val = sorted_parties[0] if len(sorted_parties) > 0 else Decimal("0")
            top3_val = sum(sorted_parties[:3], Decimal("0"))
            
            top1_share = top1_val / total_operating_inflows
            top3_share = top3_val / total_operating_inflows

            # HHI: sum of (share_pct)^2
            hhi = sum(((v / total_operating_inflows * Decimal("100")) ** 2 for v in sorted_parties), Decimal("0"))
        else:
            top1_share = Decimal("0.0000")
            top3_share = Decimal("0.0000")
            hhi = Decimal("0.00")

        # 9. GST vs Bank Turnover Discrepancy Ratio
        if gstr3b_annual_taxable_supplies is not None and total_operating_inflows > Decimal("0"):
            gst_turnover_ratio = gstr3b_annual_taxable_supplies / total_operating_inflows
        else:
            gst_turnover_ratio = None

        # 10. Policy Compliance Evaluation (sample_internal_credit_policy.md)
        policy_clauses_triggered = []
        recommendation = "APPROVE"

        # FIN-01: DSCR >= 1.25x. Referral if 1.10 <= DSCR < 1.25. Decline if DSCR < 1.0
        if dscr_proxy is not None:
            if dscr_proxy < Decimal("1.00"):
                policy_clauses_triggered.append("FIN-01")
                recommendation = "DECLINE"
            elif dscr_proxy < Decimal("1.25"):
                policy_clauses_triggered.append("FIN-01")
                if recommendation != "DECLINE":
                    recommendation = "REFER"

        # FIN-02: AMB >= 10% of proposed monthly EMI
        min_required_amb = quantize_money(proposed_monthly_emi * Decimal("0.10"))
        if overall_amb < min_required_amb:
            policy_clauses_triggered.append("FIN-02")
            if recommendation != "DECLINE":
                recommendation = "REFER"

        # FIN-03: Cheque bounce threshold: <= 2 instances in 12m, 0 in last 3m. Decline if > 3 within 6m
        if inward_clearing_returns_count > 3:
            policy_clauses_triggered.append("FIN-03")
            recommendation = "DECLINE"
        elif inward_clearing_returns_count > 2:
            policy_clauses_triggered.append("FIN-03")
            if recommendation != "DECLINE":
                recommendation = "REFER"

        # FIN-04: FOIR <= 0.50 (50%)
        if foir is not None and foir > Decimal("0.5000"):
            policy_clauses_triggered.append("FIN-04")
            if recommendation != "DECLINE":
                recommendation = "REFER"

        # FIN-05: Counterparty concentration Top-1 <= 40% (0.40)
        if top1_share > Decimal("0.4000"):
            policy_clauses_triggered.append("FIN-05")
            if recommendation != "DECLINE":
                recommendation = "REFER"

        # DOC-02: GST vs Bank Discrepancy > 20%
        if gst_turnover_ratio is not None:
            disc = abs(gst_turnover_ratio - Decimal("1.0000"))
            if disc > Decimal("0.2000"):
                policy_clauses_triggered.append("DOC-02")
                if recommendation != "DECLINE":
                    recommendation = "REFER"

        # Construct final canonical string dictionary
        return {
            "average_monthly_balance": str(quantize_money(overall_amb)),
            "avg_monthly_operating_inflow": str(quantize_money(avg_monthly_inflow)),
            "avg_monthly_operating_outflow": str(quantize_money(avg_monthly_outflow)),
            "cash_flow_volatility_cv": str(quantize_ratio(volatility_cv)) if volatility_cv is not None else None,
            "volatility_status": volatility_status,
            "inward_clearing_returns_count": inward_clearing_returns_count,
            "outward_cheque_returns_count": outward_cheque_returns_count,
            "total_inward_clearing_attempts": total_inward_clearing_attempts,
            "bounce_rate": str(quantize_ratio(bounce_rate)),
            "dscr_proxy": str(quantize_ratio(dscr_proxy)) if dscr_proxy is not None else None,
            "dscr_status": dscr_status,
            "is_negative_surplus": is_negative_surplus,
            "foir": str(quantize_ratio(foir)) if foir is not None else None,
            "foir_status": foir_status,
            "counterparty_top1_share": str(quantize_ratio(top1_share)),
            "counterparty_top3_share": str(quantize_ratio(top3_share)),
            "counterparty_hhi": str(quantize_index(hhi)),
            "gst_turnover_ratio": str(quantize_ratio(gst_turnover_ratio)) if gst_turnover_ratio is not None else None,
            "excluded_inflows_breakdown": {
                k: str(quantize_money(v)) for k, v in excluded_inflows_by_reason.items()
            },
            "expected_decision": recommendation,
            "policy_clauses_triggered": sorted(list(set(policy_clauses_triggered)))
        }
