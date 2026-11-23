"""
MSME Archetypes & Transaction Stream Generator.
Generates realistic Indian MSME financial profiles and daily/monthly transactions.
Seed-derived per applicant for perfect reproducibility.
"""

import random
import hashlib
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Tuple
from collections import defaultdict
from faker import Faker

INDIAN_STATES = ["27", "29", "07", "33", "24", "06"]  # MH, KA, DL, TN, GJ, HR

BUSINESS_SECTORS = [
    "Precision Engineering", "Auto Components", "Textile & Garments",
    "Chemicals & Solvents", "Packaging Solutions", "IT Hardware & Solutions",
    "Food Processing", "Electrical Switchgear", "Pharma Formulations"
]

BUYER_CORPORATES = [
    "Tata Motors Ancillary Ltd", "Mahindra Supplier Hub", "Larsen Heavy Fab",
    "Reliance Retail Distribution", "Godrej Consumer Vendor", "Bajaj Auto Vendor Corp",
    "Adani Logistics Partner", "Bharat Forge Supply", "Infosys Infra vendor"
]

VENDOR_CORPORATES = [
    "Hindalco Metal Suppliers", "JSW Steel Depot", "Tata Power Industrial",
    "Universal Raw Materials", "National Logistics Transport", "Apex Industrial Gases",
    "Shree Cement Distributors", "Standard Packing Material Corp"
]

GSTIN_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def compute_gstin_checksum(gstin14: str) -> str:
    """Calculates official Indian GSTIN 15th checksum character (Mod 36 algorithm)."""
    total = 0
    for i, c in enumerate(gstin14):
        val = GSTIN_CHARS.index(c)
        factor = 1 if (i % 2 == 0) else 2
        prod = val * factor
        quotient, remainder = divmod(prod, 36)
        total += quotient + remainder
    check_code = (36 - (total % 36)) % 36
    return GSTIN_CHARS[check_code]

def derive_seed(master_seed: int, applicant_id: str) -> int:
    h = hashlib.sha256(f"{master_seed}:{applicant_id}".encode("utf-8")).hexdigest()
    return int(h[:8], 16)

class ArchetypeGenerator:

    @staticmethod
    def generate_applicant_profile(applicant_id: str, archetype: str, master_seed: int) -> Dict[str, Any]:
        seed = derive_seed(master_seed, applicant_id)
        rng = random.Random(seed)
        fake = Faker("en_IN")
        fake.seed_instance(seed)

        legal_entity = rng.choice(["PRIVATE_LIMITED", "LIMITED_LIABILITY_PARTNERSHIP", "PROPRIETORSHIP"])
        entity_char = "C" if legal_entity == "PRIVATE_LIMITED" else ("F" if legal_entity == "LIMITED_LIABILITY_PARTNERSHIP" else "P")

        state_code = rng.choice(INDIAN_STATES)
        prefix_3 = "".join(rng.choices("ABCDE", k=3))
        fifth_char = rng.choice("ABCDE")
        digits_4 = f"{rng.randint(1000, 9999)}"
        check_char = rng.choice("ABCDE")
        pan_chars = f"{prefix_3}{entity_char}{fifth_char}{digits_4}{check_char}"

        gstin_base = f"{state_code}{pan_chars}1Z"
        gstin_checksum = compute_gstin_checksum(gstin_base)
        gstin = f"{gstin_base}{gstin_checksum}"

        sector = rng.choice(BUSINESS_SECTORS)
        biz_name = f"{fake.company()} {sector}"

        vintage_months = 36
        loan_req = Decimal(str(rng.randint(20, 45) * 100000))
        existing_emi = Decimal("30000.00")
        proposed_emi = Decimal("40000.00")
        open_bal = Decimal("400000.00")
        od_limit = Decimal("0.00")

        near_threshold = False
        nt_clause = ""
        nt_val = ""
        nt_thresh = ""
        nt_margin = ""
        nt_side = ""

        # Specific profiles for near-threshold and isolated clause triggers
        if "ALONE-FIN01" in applicant_id or "NEAR-DSCR-FAIL" in applicant_id:
            existing_emi = Decimal("125000.00")
            proposed_emi = Decimal("125000.00")
            open_bal = Decimal("500000.00")
            if "NEAR-DSCR-FAIL" in applicant_id:
                near_threshold = True
                nt_clause = "FIN-01"
                nt_thresh = "1.2500"
                nt_side = "just-failing"
        elif "NEAR-DSCR-PASS" in applicant_id:
            existing_emi = Decimal("125000.00")
            proposed_emi = Decimal("125000.00")
            open_bal = Decimal("500000.00")
            near_threshold = True
            nt_clause = "FIN-01"
            nt_thresh = "1.2500"
            nt_side = "just-passing"
        elif "ALONE-FIN02" in applicant_id or "NEAR-AMB-FAIL" in applicant_id:
            # FIN-02: AMB < 10% of proposed EMI
            # proposed EMI = 250,000 -> required AMB = 25,000
            open_bal = Decimal("22500.00")
            existing_emi = Decimal("0.00")
            proposed_emi = Decimal("250000.00")
            if "NEAR-AMB-FAIL" in applicant_id:
                near_threshold = True
                nt_clause = "FIN-02"
                nt_thresh = "25000.00"
                nt_side = "just-failing"
        elif "NEAR-AMB-PASS" in applicant_id:
            open_bal = Decimal("27500.00")
            existing_emi = Decimal("0.00")
            proposed_emi = Decimal("250000.00")
            near_threshold = True
            nt_clause = "FIN-02"
            nt_thresh = "25000.00"
            nt_side = "just-passing"
        elif "ALONE-FIN04" in applicant_id or "NEAR-FOIR-FAIL" in applicant_id:
            # FIN-04: FOIR > 0.50
            existing_emi = Decimal("270000.00")
            proposed_emi = Decimal("270000.00")
            open_bal = Decimal("1500000.00")
            if "NEAR-FOIR-FAIL" in applicant_id:
                near_threshold = True
                nt_clause = "FIN-04"
                nt_thresh = "0.5000"
                nt_side = "just-failing"
        elif "NEAR-FOIR-PASS" in applicant_id:
            existing_emi = Decimal("230000.00")
            proposed_emi = Decimal("230000.00")
            open_bal = Decimal("1500000.00")
            near_threshold = True
            nt_clause = "FIN-04"
            nt_thresh = "0.5000"
            nt_side = "just-passing"
        elif "ALONE-FIN03" in applicant_id:
            existing_emi = Decimal("35000.00")
            proposed_emi = Decimal("35000.00")
            open_bal = Decimal("500000.00")
        elif "STRESSED-MILD" in applicant_id:
            existing_emi = Decimal("80000.00")
            proposed_emi = Decimal("120000.00")
            open_bal = Decimal("200000.00")
        elif "STRESSED-MODERATE" in applicant_id:
            existing_emi = Decimal("260000.00")
            proposed_emi = Decimal("260000.00")
            open_bal = Decimal("150000.00")
        elif "STRESSED-HEAVY" in applicant_id:
            existing_emi = Decimal("260000.00")
            proposed_emi = Decimal("260000.00")
            open_bal = Decimal("15000.00") # AMB < 10% of proposed EMI (26k) -> triggers FIN-02
        elif "ALONE-ELIG01" in applicant_id:
            vintage_months = 18
            open_bal = Decimal("500000.00")
        elif "NEAR-DECLINE-VINTAGE" in applicant_id:
            vintage_months = 5
            near_threshold = True
            nt_clause = "ELIG-01"
            nt_val = "5"
            nt_thresh = "6"
            nt_margin = "-1"
            nt_side = "just-failing"
        elif "NEAR-PASS-VINTAGE" in applicant_id:
            vintage_months = 6
            near_threshold = True
            nt_clause = "ELIG-01"
            nt_val = "6"
            nt_thresh = "6"
            nt_margin = "0"
            nt_side = "just-passing"
        elif "NEAR-MATURE-VINTAGE" in applicant_id:
            vintage_months = 24
            near_threshold = True
            nt_clause = "ELIG-01"
            nt_val = "24"
            nt_thresh = "24"
            nt_margin = "0"
            nt_side = "just-passing"
        elif "ALONE-ELIG02" in applicant_id or "NEAR-TURNOVER-FAIL" in applicant_id:
            existing_emi = Decimal("8000.00")
            proposed_emi = Decimal("12000.00")
            open_bal = Decimal("80000.00")
            if "NEAR-TURNOVER-FAIL" in applicant_id:
                near_threshold = True
                nt_clause = "ELIG-02"
                nt_thresh = "2500000.00"
                nt_side = "just-failing"
        elif "NEAR-TURNOVER-PASS" in applicant_id:
            existing_emi = Decimal("8000.00")
            proposed_emi = Decimal("12000.00")
            open_bal = Decimal("80000.00")
            near_threshold = True
            nt_clause = "ELIG-02"
            nt_thresh = "2500000.00"
            nt_side = "just-passing"
        elif "ALONE-FIN06" in applicant_id:
            open_bal = Decimal("600000.00")
            near_threshold = True
            nt_clause = "FIN-06"
            nt_thresh = "0.6000"
            nt_side = "just-failing"
        elif "NEAR-PASS-CV" in applicant_id:
            open_bal = Decimal("600000.00")
            near_threshold = True
            nt_clause = "FIN-06"
            nt_thresh = "0.6000"
            nt_side = "just-passing"
        elif "ALONE-FIN05" in applicant_id:
            near_threshold = True
            nt_clause = "FIN-05"
            nt_thresh = "0.4000"
            nt_side = "just-failing"
        elif "NEAR-PASS-TOP1" in applicant_id:
            near_threshold = True
            nt_clause = "FIN-05"
            nt_thresh = "0.4000"
            nt_side = "just-passing"
        elif "ALONE-FIN07" in applicant_id:
            open_bal = Decimal("500000.00")
            near_threshold = True
            nt_clause = "FIN-07"
            nt_thresh = "0.0200"
            nt_side = "just-failing"
        elif "NEAR-ROUNDTRIP-PASS" in applicant_id:
            open_bal = Decimal("500000.00")
            near_threshold = True
            nt_clause = "FIN-07"
            nt_thresh = "0.0200"
            nt_side = "just-passing"
        elif "ALONE-DOC02" in applicant_id or "NEAR-DOC02-FAIL" in applicant_id:
            open_bal = Decimal("500000.00")
            if "NEAR-DOC02-FAIL" in applicant_id:
                near_threshold = True
                nt_clause = "DOC-02"
                nt_thresh = "1.2000"
                nt_side = "just-failing"
        elif "NEAR-DOC02-PASS" in applicant_id:
            open_bal = Decimal("500000.00")
            near_threshold = True
            nt_clause = "DOC-02"
            nt_thresh = "1.2000"
            nt_side = "just-passing"

        return {
            "applicant_id": applicant_id,
            "business_name": biz_name,
            "legal_entity_type": legal_entity,
            "archetype": archetype,
            "sector": sector,
            "vintage_months": vintage_months,
            "gstin": gstin,
            "pan": pan_chars,
            "seed": seed,
            "opening_balance": str(open_bal),
            "od_limit": str(od_limit),
            "requested_loan_amount": str(loan_req),
            "existing_monthly_emi": str(existing_emi),
            "proposed_monthly_emi": str(proposed_emi),
            "statement_start_date": "2024-01-01",
            "statement_end_date": "2024-12-31",
            "near_threshold": near_threshold,
            "near_threshold_clause": nt_clause,
            "near_threshold_metric_value": nt_val,
            "near_threshold_threshold": nt_thresh,
            "near_threshold_margin": nt_margin,
            "near_threshold_side": nt_side
        }

    @staticmethod
    def generate_transactions(profile: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Decimal]:
        seed = profile["seed"]
        rng = random.Random(seed)
        applicant_id = profile["applicant_id"]
        archetype = profile["archetype"]
        open_bal = Decimal(profile["opening_balance"])
        existing_emi = Decimal(profile["existing_monthly_emi"])
        od_limit = Decimal(profile.get("od_limit", "0.00"))

        start_date = date.fromisoformat(profile["statement_start_date"])
        end_date = date.fromisoformat(profile["statement_end_date"])
        total_days = (end_date - start_date).days + 1

        buyers = BUYER_CORPORATES
        vendors = VENDOR_CORPORATES
        raw_txns = []
        running_bal = open_bal

        for d in range(total_days):
            txn_date = start_date + timedelta(days=d)
            m_idx = txn_date.month - 1
            date_str = txn_date.isoformat()

            # EMI on 5th of each month
            if txn_date.day == 5 and existing_emi > 0:
                is_bounce = False
                if "ALONE-FIN03" in applicant_id:
                    is_bounce = (m_idx == 5)  # exactly 1 bounce
                elif "STRESSED-MILD" in applicant_id:
                    is_bounce = (m_idx in [4, 9])  # 2 bounces
                elif "STRESSED-MODERATE" in applicant_id:
                    is_bounce = (m_idx in [3, 7, 10])  # 3 bounces
                elif "STRESSED-HEAVY" in applicant_id:
                    is_bounce = (m_idx in [2, 5, 8, 11])  # 4 bounces

                if is_bounce:
                    raw_txns.append({
                        "date": date_str, "amount": str(existing_emi), "type": "DEBIT",
                        "category": "INWARD_NACH_RETURN", "counterparty": "Lending Partner Bank",
                        "narration": f"NACH RET - INSUFFICIENT BALANCE EMI #{m_idx+1}"
                    })
                    raw_txns.append({
                        "date": date_str, "amount": "450.00", "type": "DEBIT",
                        "category": "BANK_CHARGES", "counterparty": "Bank",
                        "narration": "CHQ/ECS RETURN CHARGES INCL GST"
                    })
                    running_bal -= Decimal("450.00")
                else:
                    raw_txns.append({
                        "date": date_str, "amount": str(existing_emi), "type": "DEBIT",
                        "category": "DEBT_SERVICE", "counterparty": "Lending Partner Bank",
                        "narration": f"NACH DR TO LENDING PARTNER EMI #{m_idx+1}"
                    })
                    running_bal -= existing_emi

            # Edge case specific injections
            if "ZERO-INFLOW" in applicant_id and m_idx == 6:
                pass
            elif "LARGE-CREDIT" in applicant_id and m_idx == 4 and txn_date.day == 14:
                raw_txns.append({
                    "date": date_str, "amount": "1500000.00", "type": "CREDIT",
                    "category": "ONE_OFF", "counterparty": "Machinery Liquidator Ltd",
                    "narration": "RTGS CR SALE OF CNC MACHINE"
                })
                running_bal += Decimal("1500000.00")
            elif ("ROUND-TRIP" in applicant_id or "ALONE-FIN07" in applicant_id) and m_idx == 2 and txn_date.day == 10:
                rt_cr = "500000.00" if "ROUND-TRIP" in applicant_id else "280000.00"
                rt_dr = "498000.00" if "ROUND-TRIP" in applicant_id else "278000.00"
                raw_txns.append({
                    "date": date_str, "amount": rt_cr, "type": "CREDIT",
                    "category": "SALES_RECEIPT", "counterparty": "Orbit Allied Traders",
                    "narration": "RTGS CR ORBIT ALLIED TRADERS"
                })
                raw_txns.append({
                    "date": (txn_date + timedelta(days=2)).isoformat(), "amount": rt_dr, "type": "DEBIT",
                    "category": "VENDOR_PAYMENT", "counterparty": "Orbit Allied Traders",
                    "narration": "RTGS DR ORBIT ALLIED TRADERS"
                })
                running_bal += (Decimal(rt_cr) - Decimal(rt_dr))
            elif "NEAR-ROUNDTRIP-PASS" in applicant_id and m_idx == 2 and txn_date.day == 10:
                raw_txns.append({
                    "date": date_str, "amount": "140000.00", "type": "CREDIT",
                    "category": "SALES_RECEIPT", "counterparty": "Orbit Allied Traders",
                    "narration": "RTGS CR ORBIT ALLIED TRADERS"
                })
                raw_txns.append({
                    "date": (txn_date + timedelta(days=2)).isoformat(), "amount": "139000.00", "type": "DEBIT",
                    "category": "VENDOR_PAYMENT", "counterparty": "Orbit Allied Traders",
                    "narration": "RTGS DR ORBIT ALLIED TRADERS"
                })
                running_bal += (Decimal("140000.00") - Decimal("139000.00"))

            # Sales credits schedule: 8 transactions per month (days 3, 7, 11, 15, 18, 22, 25, 28)
            is_zero = ("ZERO-INFLOW" in applicant_id and m_idx == 6)
            if not is_zero:
                if txn_date.day in [3, 7, 11, 15, 18, 22, 25, 28]:
                    mult = Decimal("1.0")
                    if "ALONE-FIN06" in applicant_id:
                        mult = Decimal("2.20") if m_idx in [7, 8, 9, 10] else (Decimal("0.22") if m_idx in [0, 1, 2] else Decimal("1.0"))
                    elif "NEAR-PASS-CV" in applicant_id:
                        mult = Decimal("1.80") if m_idx in [7, 8, 9, 10] else (Decimal("0.38") if m_idx in [0, 1, 2] else Decimal("1.0"))
                    elif archetype == "seasonal":
                        mult = Decimal("1.45") if m_idx in [7, 8, 9, 10] else (Decimal("0.65") if m_idx in [0, 1, 2] else Decimal("1.0"))

                    if "ALONE-ELIG02" in applicant_id:
                        base_inflow = Decimal("21875.00") # 8 * 21875 = 175,000/mo -> 2,100,000/yr (<25L)
                    elif "NEAR-TURNOVER-FAIL" in applicant_id:
                        base_inflow = Decimal("24479.16") # ~195,833/mo -> 2,350,000/yr (<25L)
                    elif "NEAR-TURNOVER-PASS" in applicant_id:
                        base_inflow = Decimal("27604.16") # ~220,833/mo -> 2,650,000/yr (>=25L)
                    elif "ALONE-FIN02" in applicant_id or "NEAR-AMB-FAIL" in applicant_id or "NEAR-AMB-PASS" in applicant_id:
                        base_inflow = Decimal("100000.00")
                    else:
                        base_inflow = Decimal("125000.00")

                    cr_amt = (base_inflow * mult).quantize(Decimal("0.01"))

                    if "ALONE-FIN05" in applicant_id:
                        buyer = buyers[0] if txn_date.day in [3, 7, 11, 15] else rng.choice(buyers[1:])
                    elif "NEAR-PASS-TOP1" in applicant_id:
                        buyer = buyers[0] if txn_date.day in [3, 7, 11] else rng.choice(buyers[1:])
                    elif archetype == "high_concentration":
                        buyer = buyers[0] if txn_date.day in [3, 7, 11, 15, 18] else rng.choice(buyers[1:])
                    else:
                        buyer = buyers[(d % len(buyers))]

                    raw_txns.append({
                        "date": date_str, "amount": str(cr_amt), "type": "CREDIT",
                        "category": "SALES_RECEIPT", "counterparty": buyer,
                        "narration": f"NEFT CR-{buyer[:16]}-INV-{d+100}"
                    })
                    running_bal += cr_amt

                    # For FIN-02 AMB pinning: sweep credit to own account so day-end balance is pinned to open_bal
                    if "ALONE-FIN02" in applicant_id or "NEAR-AMB-FAIL" in applicant_id or "NEAR-AMB-PASS" in applicant_id:
                        raw_txns.append({
                            "date": date_str, "amount": str(cr_amt), "type": "DEBIT",
                            "category": "OWN_ACCOUNT_TRANSFER", "counterparty": "Promoter Sweep Account",
                            "narration": "AUTO SWEEP DR TO CURRENT ACC 9921"
                        })
                        running_bal -= cr_amt

            # Operating Outflows (days 4, 8, 12, 16, 20, 24, 27)
            if txn_date.day in [4, 8, 12, 16, 20, 24, 27]:
                if "NEAR-DSCR-PASS" in applicant_id:
                    dr_amt = Decimal("97142.85") # 7 * 97142.85 = 680,000/mo -> surplus = 320,000 -> DSCR = 320k/250k = 1.28
                elif "NEAR-DSCR-FAIL" in applicant_id:
                    dr_amt = Decimal("99285.71") # 7 * 99285.71 = 695,000/mo -> surplus = 305,000 -> DSCR = 305k/250k = 1.22
                elif "ALONE-FIN01" in applicant_id:
                    dr_amt = Decimal("100714.28") # 7 * 100714.28 = 705,000/mo -> surplus = 295,000 -> DSCR = 295k/250k = 1.18
                elif "ALONE-FIN02" in applicant_id or "NEAR-AMB-FAIL" in applicant_id or "NEAR-AMB-PASS" in applicant_id:
                    dr_amt = Decimal("28571.42") # 200,000/mo -> surplus = 800,000 -> DSCR = 800k/250k = 3.20
                elif "ALONE-FIN04" in applicant_id or "NEAR-FOIR-PASS" in applicant_id or "NEAR-FOIR-FAIL" in applicant_id:
                    dr_amt = Decimal("28571.42") # 200,000/mo -> surplus = 800,000 -> DSCR > 1.25
                elif "ALONE-ELIG02" in applicant_id or "NEAR-TURNOVER" in applicant_id:
                    dr_amt = Decimal("11428.57") # 80,000/mo
                elif archetype == "stressed":
                    dr_amt = Decimal("110000.00") # 770,000/mo
                else:
                    dr_amt = Decimal("75000.00") # 525,000/mo

                vendor = vendors[(d % len(vendors))]
                raw_txns.append({
                    "date": date_str, "amount": str(dr_amt), "type": "DEBIT",
                    "category": "VENDOR_PAYMENT", "counterparty": vendor,
                    "narration": f"RTGS DR TO {vendor[:16]} MAT SUPPLIES"
                })
                running_bal -= dr_amt

                # For FIN-02 AMB pinning: replenish from own account transfer credit on outflow days
                if "ALONE-FIN02" in applicant_id or "NEAR-AMB-FAIL" in applicant_id or "NEAR-AMB-PASS" in applicant_id:
                    raw_txns.append({
                        "date": date_str, "amount": str(dr_amt), "type": "CREDIT",
                        "category": "OWN_ACCOUNT_TRANSFER", "counterparty": "Promoter Sweep Account",
                        "narration": "REPLENISH CR FROM CURRENT ACC 9921"
                    })
                    running_bal += dr_amt

        raw_txns.sort(key=lambda x: x["date"])
        day_counter = defaultdict(int)
        sequenced_txns = []
        for t in raw_txns:
            d_val = t["date"]
            day_counter[d_val] += 1
            t_copy = dict(t)
            t_copy["sequence_number"] = day_counter[d_val]
            sequenced_txns.append(t_copy)

        sales_credits = [Decimal(t["amount"]) for t in sequenced_txns if t["type"] == "CREDIT" and t["category"] == "SALES_RECEIPT"]
        total_bank_sales = sum(sales_credits, Decimal("0.00"))

        if "DOC02-GST-DISCREPANT" in applicant_id or "NEAR-DOC02-FAIL" in applicant_id or "ALONE-DOC02" in applicant_id:
            gstr3b_annual = (total_bank_sales * Decimal("0.78")).quantize(Decimal("0.01"))
        elif "NEAR-DOC02-PASS" in applicant_id:
            gstr3b_annual = (total_bank_sales * Decimal("0.89")).quantize(Decimal("0.01"))
        else:
            gstr3b_annual = (total_bank_sales * Decimal("1.01")).quantize(Decimal("0.01"))

        return sequenced_txns, gstr3b_annual
