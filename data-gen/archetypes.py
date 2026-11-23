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

        state_code = rng.choice(INDIAN_STATES)
        pan_chars = "".join(rng.choices("ABCDE", k=3)) + rng.choice(["C", "P", "F", "H"]) + "".join(rng.choices("0123456789", k=4)) + rng.choice("ABCDE")
        gstin = f"{state_code}{pan_chars}1Z{rng.choice('123456789')}"

        sector = rng.choice(BUSINESS_SECTORS)
        biz_name = f"{fake.company()} {sector}"

        # Baseline parameters per archetype
        vintage_months = rng.randint(24, 84)
        if archetype == "thin_file":
            vintage_months = rng.randint(6, 18)

        if archetype == "healthy":
            loan_req = Decimal(str(rng.randint(20, 50) * 100000))
            existing_emi = Decimal(str(rng.randint(2, 6) * 10000))
            proposed_emi = Decimal(str(int(loan_req * Decimal("0.024"))))
            open_bal = Decimal(str(rng.randint(20, 45) * 10000))
        elif archetype == "seasonal":
            loan_req = Decimal(str(rng.randint(25, 50) * 100000))
            existing_emi = Decimal(str(rng.randint(3, 8) * 10000))
            proposed_emi = Decimal(str(int(loan_req * Decimal("0.025"))))
            open_bal = Decimal(str(rng.randint(10, 25) * 10000))
        elif archetype == "high_concentration":
            loan_req = Decimal(str(rng.randint(15, 40) * 100000))
            existing_emi = Decimal(str(rng.randint(2, 5) * 10000))
            proposed_emi = Decimal(str(int(loan_req * Decimal("0.024"))))
            open_bal = Decimal(str(rng.randint(15, 30) * 10000))
        elif archetype == "stressed":
            loan_req = Decimal(str(rng.randint(10, 30) * 100000))
            existing_emi = Decimal(str(rng.randint(6, 12) * 10000))
            proposed_emi = Decimal(str(int(loan_req * Decimal("0.026"))))
            open_bal = Decimal(str(rng.randint(2, 8) * 10000))
        elif archetype == "thin_file":
            loan_req = Decimal(str(rng.randint(5, 15) * 100000))
            existing_emi = Decimal(str(rng.randint(1, 3) * 10000))
            proposed_emi = Decimal(str(int(loan_req * Decimal("0.025"))))
            open_bal = Decimal(str(rng.randint(5, 12) * 10000))
        else:  # edge_cases
            loan_req = Decimal(str(rng.randint(10, 30) * 100000))
            existing_emi = Decimal(str(rng.randint(2, 5) * 10000))
            proposed_emi = Decimal(str(int(loan_req * Decimal("0.025"))))
            open_bal = Decimal(str(rng.randint(10, 30) * 10000))

        return {
            "applicant_id": applicant_id,
            "business_name": biz_name,
            "legal_entity_type": rng.choice(["PRIVATE_LIMITED", "LIMITED_LIABILITY_PARTNERSHIP", "PROPRIETORSHIP"]),
            "archetype": archetype,
            "sector": sector,
            "vintage_months": vintage_months,
            "gstin": gstin,
            "pan": pan_chars,
            "seed": seed,
            "opening_balance": str(open_bal),
            "requested_loan_amount": str(loan_req),
            "existing_monthly_emi": str(existing_emi),
            "proposed_monthly_emi": str(proposed_emi),
            "statement_start_date": "2024-01-01",
            "statement_end_date": "2024-12-31"
        }

    @staticmethod
    def generate_transactions(profile: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Decimal]:
        seed = profile["seed"]
        rng = random.Random(seed)
        archetype = profile["archetype"]
        applicant_id = profile["applicant_id"]

        start_date = date.fromisoformat(profile["statement_start_date"])
        end_date = date.fromisoformat(profile["statement_end_date"])
        open_bal = Decimal(profile["opening_balance"])
        existing_emi = Decimal(profile["existing_monthly_emi"])

        # Determine buyers and vendors
        buyers = rng.sample(BUYER_CORPORATES, k=min(len(BUYER_CORPORATES), rng.randint(4, 7)))
        vendors = rng.sample(VENDOR_CORPORATES, k=min(len(VENDOR_CORPORATES), rng.randint(4, 6)))

        txns = []
        running_bal = open_bal

        total_days = (end_date - start_date).days + 1
        curr_month = -1

        # Month-by-month factors
        # 12 months: Jan (0) to Dec (11)
        for d in range(total_days):
            txn_date = start_date + timedelta(days=d)
            m_idx = txn_date.month - 1
            date_str = txn_date.isoformat()

            # EMI deduction on day 5 of each month
            if txn_date.day == 5 and existing_emi > 0:
                is_emi_bounce = (archetype == "stressed" and m_idx in [5, 8, 10])
                if is_emi_bounce:
                    # Inward return of EMI debit
                    txns.append({
                        "date": date_str,
                        "amount": str(existing_emi),
                        "type": "DEBIT",
                        "category": "INWARD_NACH_RETURN",
                        "counterparty": "Lending Partner Bank",
                        "narration": f"NACH RET - INSUFFICIENT BALANCE EMI #{m_idx+1}"
                    })
                    # Add penalty fee
                    txns.append({
                        "date": date_str,
                        "amount": "450.00",
                        "type": "DEBIT",
                        "category": "BANK_CHARGES",
                        "counterparty": "Bank",
                        "narration": "CHQ/ECS RETURN CHARGES INCL GST"
                    })
                else:
                    txns.append({
                        "date": date_str,
                        "amount": str(existing_emi),
                        "type": "DEBIT",
                        "category": "DEBT_SERVICE",
                        "counterparty": "Lending Partner Bank",
                        "narration": f"NACH DR TO LENDING PARTNER EMI #{m_idx+1}"
                    })

            # Check archetype special behaviors
            if archetype == "edge_cases":
                if "ZERO-INFLOW" in applicant_id and m_idx == 6:
                    # Zero sales inflow in July (month 6)
                    pass
                elif "LARGE-CREDIT" in applicant_id and m_idx == 4 and txn_date.day == 14:
                    # One-off asset sale credit
                    txns.append({
                        "date": date_str,
                        "amount": "1500000.00",
                        "type": "CREDIT",
                        "category": "ASSET_SALE",
                        "counterparty": "Machinery Liquidator Ltd",
                        "narration": "RTGS CR SALE OF CNC MACHINE"
                    })
                elif "ROUND-TRIP" in applicant_id and m_idx == 2 and txn_date.day == 10:
                    # Simulated round trip
                    txns.append({
                        "date": date_str,
                        "amount": "450000.00",
                        "type": "CREDIT",
                        "category": "SALES_RECEIPT",
                        "counterparty": "Orbit Allied Traders",
                        "narration": "RTGS CR ORBIT ALLIED TRADERS"
                    })
                    txns.append({
                        "date": (txn_date + timedelta(days=2)).isoformat(),
                        "amount": "448000.00",
                        "type": "DEBIT",
                        "category": "VENDOR_PAYMENT",
                        "counterparty": "Orbit Allied Traders",
                        "narration": "RTGS DR ORBIT ALLIED TRADERS"
                    })

            # Daily sales receipt chance
            inflow_prob = 0.28
            monthly_multiplier = Decimal("1.0")

            if archetype == "seasonal":
                # Peak in Q3/festive (Aug-Nov: m_idx 7, 8, 9, 10), trough in Q1 (Jan-Mar: 0, 1, 2)
                if m_idx in [7, 8, 9, 10]:
                    monthly_multiplier = Decimal("2.4")
                    inflow_prob = 0.50
                elif m_idx in [0, 1, 2]:
                    monthly_multiplier = Decimal("0.35")
                    inflow_prob = 0.12
            elif archetype == "stressed":
                monthly_multiplier = Decimal("0.65")
                inflow_prob = 0.18
            elif archetype == "thin_file":
                if m_idx < 6:
                    continue  # Only active in last 6 months

            # Near-threshold variants adjustment
            if "NEAR-DSCR-MIN" in applicant_id:
                monthly_multiplier = Decimal("0.82")
            elif "NEAR-DSCR-REC" in applicant_id:
                monthly_multiplier = Decimal("0.98")

            if rng.random() < inflow_prob:
                if archetype == "high_concentration":
                    # First buyer gets > 55% of all credit
                    buyer = buyers[0] if rng.random() < 0.65 else rng.choice(buyers[1:])
                else:
                    buyer = rng.choice(buyers)

                base_amt = rng.randint(40, 180) * 1000
                cr_amt = Decimal(str(base_amt)) * monthly_multiplier
                cr_amt = cr_amt.quantize(Decimal("0.01"))

                txns.append({
                    "date": date_str,
                    "amount": str(cr_amt),
                    "type": "CREDIT",
                    "category": "SALES_RECEIPT",
                    "counterparty": buyer,
                    "narration": f"NEFT CR-{buyer[:18]}-INV-{rng.randint(1001, 9999)}"
                })

            # Vendor / Operational debits
            outflow_prob = 0.32
            if archetype == "thin_file" and m_idx < 6:
                outflow_prob = 0.0

            if rng.random() < outflow_prob:
                vendor = rng.choice(vendors)
                base_amt = rng.randint(25, 120) * 1000
                dr_amt = Decimal(str(base_amt)) * (Decimal("1.2") if archetype == "stressed" else Decimal("0.9"))
                dr_amt = dr_amt.quantize(Decimal("0.01"))

                txns.append({
                    "date": date_str,
                    "amount": str(dr_amt),
                    "type": "DEBIT",
                    "category": "VENDOR_PAYMENT",
                    "counterparty": vendor,
                    "narration": f"RTGS DR TO {vendor[:16]} MAT SUPPLIES"
                })

            # Occasional outward cheque return in stressed/edge case
            if archetype == "stressed" and rng.random() < 0.008:
                txns.append({
                    "date": date_str,
                    "amount": "75000.00",
                    "type": "DEBIT",
                    "category": "OUTWARD_CHEQUE_RETURN",
                    "counterparty": "Client Customer",
                    "narration": "DEP RET UNPAID - DRAWERS SIGNATURE DIFFERS"
                })

        # Calculate annual GST supplies (roughly matching or varying with banking)
        sales_credits = [Decimal(t["amount"]) for t in txns if t["type"] == "CREDIT" and t["category"] == "SALES_RECEIPT"]
        total_bank_sales = sum(sales_credits, Decimal("0.00"))

        if "DOC02-GST-DISCREPANT" in applicant_id:
            # 30% under-reporting in GST
            gstr3b_annual = total_bank_sales * Decimal("0.70")
        else:
            # realistic small variance (1-3%)
            gstr3b_annual = total_bank_sales * Decimal(str(rng.uniform(0.97, 1.03)))

        gstr3b_annual = gstr3b_annual.quantize(Decimal("0.01"))
        return txns, gstr3b_annual
