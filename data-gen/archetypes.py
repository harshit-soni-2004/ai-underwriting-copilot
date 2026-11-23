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

    ARCHETYPE_COUNTS = [
        ("healthy", 30),
        ("seasonal", 20),
        ("high_concentration", 20),
        ("stressed", 20),
        ("thin_file", 15),
        ("edge_cases", 15)
    ]

    @staticmethod
    def get_applicant_id(counter: int, archetype: str, idx: int) -> str:
        if archetype == "healthy":
            # 30 healthy applicants:
            # idx 0..9: Standard clean healthy
            # idx 10..12 (3): ALONE-FIN01 (DSCR = 1.10) (clause isolation)
            # idx 13..15 (3): ALONE-FIN02 (AMB ratio = 0.08) (clause isolation)
            # idx 16..18 (3): ALONE-FIN04 (FOIR = 0.58) (clause isolation)
            # idx 19..21 (3): ALONE-DOC02 (GST ratio = 1.25) (clause isolation)
            # idx 22: NEAR-VINTAGE-PASS (vintage = 24m)
            # idx 23: NEAR-VINTAGE-FAIL (vintage = 23m)
            # idx 24: NEAR-DSCR-PASS (DSCR = 1.28)
            # idx 25: NEAR-DSCR-FAIL (DSCR = 1.22)
            # idx 26: NEAR-AMB-PASS (AMB ratio = 0.105)
            # idx 27: NEAR-AMB-FAIL (AMB ratio = 0.095)
            # idx 28: NEAR-FOIR-PASS (FOIR = 0.48)
            # idx 29: NEAR-FOIR-FAIL (FOIR = 0.52)
            if idx in [10, 11, 12]:
                return f"APP-{counter:03d}-HEALTHY-ALONE-FIN01"
            elif idx in [13, 14, 15]:
                return f"APP-{counter:03d}-HEALTHY-ALONE-FIN02"
            elif idx in [16, 17, 18]:
                return f"APP-{counter:03d}-HEALTHY-ALONE-FIN04"
            elif idx in [19, 20, 21]:
                return f"APP-{counter:03d}-HEALTHY-ALONE-DOC02"
            elif idx == 22:
                return f"APP-{counter:03d}-HEALTHY-NEAR-VINTAGE-PASS"
            elif idx == 23:
                return f"APP-{counter:03d}-HEALTHY-NEAR-VINTAGE-FAIL"
            elif idx == 24:
                return f"APP-{counter:03d}-HEALTHY-NEAR-DSCR-PASS"
            elif idx == 25:
                return f"APP-{counter:03d}-HEALTHY-NEAR-DSCR-FAIL"
            elif idx == 26:
                return f"APP-{counter:03d}-HEALTHY-NEAR-AMB-PASS"
            elif idx == 27:
                return f"APP-{counter:03d}-HEALTHY-NEAR-AMB-FAIL"
            elif idx == 28:
                return f"APP-{counter:03d}-HEALTHY-NEAR-FOIR-PASS"
            elif idx == 29:
                return f"APP-{counter:03d}-HEALTHY-NEAR-FOIR-FAIL"
            return f"APP-{counter:03d}-HEALTHY"

        elif archetype == "seasonal":
            # 20 seasonal:
            # idx 0..9: Standard seasonal with peak concentration (CV >= 0.80) -> REFER via FIN-06
            # idx 10..13 (4): NEAR-PASS-CV (CV = 0.57 <= 0.60) -> APPROVE
            # idx 14..19 (6): NEAR-FAIL-CV (CV = 0.63 > 0.60) -> REFER
            if idx in [10, 11, 12, 13]:
                return f"APP-{counter:03d}-SEASONAL-NEAR-PASS-CV"
            elif idx in [14, 15, 16, 17, 18, 19]:
                return f"APP-{counter:03d}-SEASONAL-NEAR-FAIL-CV"
            return f"APP-{counter:03d}-SEASONAL"

        elif archetype == "high_concentration":
            # 20 high_concentration:
            # idx 0..9: Standard high concentration (Top-1 = 0.55 - 0.70) -> REFER via FIN-05
            # idx 10..13 (4): NEAR-PASS-TOP1 (Top-1 = 0.38 <= 0.40) -> APPROVE
            # idx 14..19 (6): NEAR-FAIL-TOP1 (Top-1 = 0.42 > 0.40) -> REFER
            if idx in [10, 11, 12, 13]:
                return f"APP-{counter:03d}-HIGH_CONCENTRATION-NEAR-PASS-TOP1"
            elif idx in [14, 15, 16, 17, 18, 19]:
                return f"APP-{counter:03d}-HIGH_CONCENTRATION-NEAR-FAIL-TOP1"
            return f"APP-{counter:03d}-HIGH_CONCENTRATION"

        elif archetype == "stressed":
            # 20 stressed:
            # idx 0..3 (4): ALONE-FIN03 (1 bounce, clean finances) -> REFER
            # idx 4..8 (5): STRESSED-MILD (2 bounces + DSCR < 1.0) -> DECLINE {FIN-01, FIN-03}
            # idx 9..14 (6): STRESSED-MODERATE (3 bounces + FOIR > 0.50 + DSCR < 1.0) -> DECLINE {FIN-01, FIN-03, FIN-04}
            # idx 15..19 (5): STRESSED-HEAVY (4 bounces + AMB < 10% + DSCR < 1.0 + FOIR > 0.50) -> DECLINE {FIN-01, FIN-02, FIN-03, FIN-04}
            if idx in [0, 1, 2, 3]:
                return f"APP-{counter:03d}-STRESSED-ALONE-FIN03"
            elif idx in [4, 5, 6, 7, 8]:
                return f"APP-{counter:03d}-STRESSED-MILD"
            elif idx in [9, 10, 11, 12, 13, 14]:
                return f"APP-{counter:03d}-STRESSED-MODERATE"
            else:
                return f"APP-{counter:03d}-STRESSED-HEAVY"

        elif archetype == "thin_file":
            # 15 thin_file (vintage strictly 4-9 months!):
            # idx 0..1 (2): vintage = 4m (DECLINE via ELIG-01)
            # idx 2..4 (3): NEAR-DECLINE-VINTAGE (vintage = 5m, DECLINE via ELIG-01)
            # idx 5..7 (3): NEAR-PASS-VINTAGE (vintage = 6m, REFER via ELIG-01)
            # idx 8..10 (3): vintage = 7m (REFER via ELIG-01)
            # idx 11..12 (2): vintage = 8m (REFER via ELIG-01)
            # idx 13..14 (2): vintage = 9m (REFER via ELIG-01)
            if idx in [2, 3, 4]:
                return f"APP-{counter:03d}-THIN_FILE-NEAR-DECLINE-VINTAGE"
            elif idx in [5, 6, 7]:
                return f"APP-{counter:03d}-THIN_FILE-NEAR-PASS-VINTAGE"
            return f"APP-{counter:03d}-THIN_FILE"

        elif archetype == "edge_cases":
            # 15 edge cases:
            # idx 0: ZERO-INFLOW (Month 7 has 0 inflow, CV high, REFER via FIN-06)
            # idx 1: LARGE-CREDIT (Asset sale 15L excluded, clean APPROVE)
            # idx 2: ROUND-TRIP (5L round trip excluded, REFER via FIN-07)
            # idx 3: DOC02-GST-DISCREPANT (GST ratio 1.35, REFER via DOC-02)
            # idx 4..6 (3): ALONE-ELIG02 (Turnover 21L < 25L, DECLINE via ELIG-02)
            # idx 7..9 (3): ALONE-FIN07 (Round-trip 2.8%, REFER via FIN-07)
            # idx 10: NEAR-ROUNDTRIP-PASS (Round-trip 0.0190 <= 0.0200, APPROVE)
            # idx 11: NEAR-ROUNDTRIP-FAIL (Round-trip 0.0210 > 0.0200, REFER)
            # idx 12: NEAR-DOC02-PASS (GST ratio 1.1900, APPROVE)
            # idx 13: NEAR-DOC02-FAIL (GST ratio 1.2100, REFER)
            # idx 14: NEAR-TURNOVER-PASS (Turnover 26.0L >= 25L, APPROVE)
            # idx 15: NEAR-TURNOVER-FAIL (Turnover 24.0L < 25L, DECLINE)
            edge_subtypes = [
                "ZERO-INFLOW",
                "LARGE-CREDIT",
                "ROUND-TRIP",
                "DOC02-GST-DISCREPANT",
                "ALONE-ELIG02",
                "ALONE-ELIG02",
                "ALONE-ELIG02",
                "ALONE-FIN07",
                "ALONE-FIN07",
                "ALONE-FIN07",
                "NEAR-ROUNDTRIP-PASS",
                "NEAR-ROUNDTRIP-FAIL",
                "NEAR-DOC02-PASS",
                "NEAR-DOC02-FAIL",
                "NEAR-TURNOVER-PASS",
                "NEAR-TURNOVER-FAIL"
            ]
            sub = edge_subtypes[idx] if idx < len(edge_subtypes) else f"EDGE-{idx+1}"
            return f"APP-{counter:03d}-EDGE-{sub}"

        return f"APP-{counter:03d}-{archetype.upper()}"

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

        vintage_months = 36 + (seed % 24)
        loan_req = Decimal(str(2500000 + (seed % 15) * 100000))
        existing_emi = Decimal("30000.00")
        proposed_emi = Decimal("40000.00")
        open_bal = Decimal(str(350000 + (seed % 20) * 10000))
        od_limit = Decimal("0.00")

        near_threshold = False
        clause_isolation = False
        nt_clause = ""
        target_boundary = None

        if "NEAR-VINTAGE-PASS" in applicant_id:
            vintage_months = 24
            near_threshold = True
            nt_clause = "ELIG-01"
        elif "NEAR-VINTAGE-FAIL" in applicant_id:
            vintage_months = 23
            near_threshold = True
            nt_clause = "ELIG-01"
        elif "NEAR-DSCR-PASS" in applicant_id:
            existing_emi = Decimal("125000.00")
            proposed_emi = Decimal("125000.00")
            open_bal = Decimal("500000.00")
            near_threshold = True
            nt_clause = "FIN-01"
        elif "NEAR-DSCR-FAIL" in applicant_id:
            existing_emi = Decimal("125000.00")
            proposed_emi = Decimal("125000.00")
            open_bal = Decimal("500000.00")
            near_threshold = True
            nt_clause = "FIN-01"
        elif "NEAR-AMB-PASS" in applicant_id:
            open_bal = Decimal("26250.00")  # 10.5% of 250k
            existing_emi = Decimal("0.00")
            proposed_emi = Decimal("250000.00")
            near_threshold = True
            nt_clause = "FIN-02"
        elif "NEAR-AMB-FAIL" in applicant_id:
            open_bal = Decimal("23750.00")  # 9.5% of 250k
            existing_emi = Decimal("0.00")
            proposed_emi = Decimal("250000.00")
            near_threshold = True
            nt_clause = "FIN-02"
        elif "NEAR-FOIR-PASS" in applicant_id:
            existing_emi = Decimal("240000.00")
            proposed_emi = Decimal("240000.00")  # 480k total -> FOIR 0.48
            open_bal = Decimal("1500000.00")
            near_threshold = True
            nt_clause = "FIN-04"
        elif "NEAR-FOIR-FAIL" in applicant_id:
            existing_emi = Decimal("260000.00")
            proposed_emi = Decimal("260000.00")  # 520k total -> FOIR 0.52
            open_bal = Decimal("1500000.00")
            near_threshold = True
            nt_clause = "FIN-04"
        elif "NEAR-DOC02-PASS" in applicant_id:
            open_bal = Decimal("500000.00")
            near_threshold = True
            nt_clause = "DOC-02"
        elif "NEAR-DOC02-FAIL" in applicant_id:
            open_bal = Decimal("500000.00")
            near_threshold = True
            nt_clause = "DOC-02"
        elif "NEAR-PASS-CV" in applicant_id:
            open_bal = Decimal("600000.00")
            near_threshold = True
            nt_clause = "FIN-06"
        elif "NEAR-FAIL-CV" in applicant_id:
            open_bal = Decimal("600000.00")
            near_threshold = True
            nt_clause = "FIN-06"
        elif "NEAR-PASS-TOP1" in applicant_id:
            near_threshold = True
            nt_clause = "FIN-05"
        elif "NEAR-FAIL-TOP1" in applicant_id:
            near_threshold = True
            nt_clause = "FIN-05"
        elif "NEAR-DECLINE-VINTAGE" in applicant_id:
            vintage_months = 5
            near_threshold = True
            nt_clause = "ELIG-01"
            target_boundary = "decline"
        elif "NEAR-PASS-VINTAGE" in applicant_id:
            vintage_months = 6
            near_threshold = True
            nt_clause = "ELIG-01"
            target_boundary = "decline"
        elif "NEAR-ROUNDTRIP-PASS" in applicant_id:
            open_bal = Decimal("500000.00")
            near_threshold = True
            nt_clause = "FIN-07"
        elif "NEAR-ROUNDTRIP-FAIL" in applicant_id:
            open_bal = Decimal("500000.00")
            near_threshold = True
            nt_clause = "FIN-07"
        elif "NEAR-TURNOVER-PASS" in applicant_id:
            existing_emi = Decimal("8000.00")
            proposed_emi = Decimal("12000.00")
            open_bal = Decimal("80000.00")
            near_threshold = True
            nt_clause = "ELIG-02"
        elif "NEAR-TURNOVER-FAIL" in applicant_id:
            existing_emi = Decimal("8000.00")
            proposed_emi = Decimal("12000.00")
            open_bal = Decimal("80000.00")
            near_threshold = True
            nt_clause = "ELIG-02"

        # Clause Isolation Profiles
        elif "ALONE-FIN01" in applicant_id:
            clause_isolation = True
            existing_emi = Decimal("150000.00")
            proposed_emi = Decimal("150000.00")
            open_bal = Decimal("500000.00")
        elif "ALONE-FIN02" in applicant_id:
            clause_isolation = True
            open_bal = Decimal("20000.00")  # 8.0% of 250k
            existing_emi = Decimal("0.00")
            proposed_emi = Decimal("250000.00")
        elif "ALONE-FIN03" in applicant_id:
            clause_isolation = True
            existing_emi = Decimal("35000.00")
            proposed_emi = Decimal("35000.00")
            open_bal = Decimal("500000.00")
        elif "ALONE-FIN04" in applicant_id:
            clause_isolation = True
            existing_emi = Decimal("290000.00")
            proposed_emi = Decimal("290000.00")  # FOIR 0.58
            open_bal = Decimal("1500000.00")
        elif "ALONE-FIN05" in applicant_id:
            clause_isolation = True
        elif "ALONE-FIN06" in applicant_id:
            clause_isolation = True
            open_bal = Decimal("600000.00")
        elif "ALONE-FIN07" in applicant_id:
            clause_isolation = True
            open_bal = Decimal("500000.00")
        elif "ALONE-DOC02" in applicant_id:
            clause_isolation = True
            open_bal = Decimal("500000.00")
        elif "ALONE-ELIG02" in applicant_id:
            clause_isolation = True
            existing_emi = Decimal("8000.00")
            proposed_emi = Decimal("12000.00")
            open_bal = Decimal("80000.00")

        # Archetype Defaults
        elif archetype == "stressed":
            open_bal = Decimal("150000.00")
            if "STRESSED-MILD" in applicant_id:
                existing_emi = Decimal("80000.00")
                proposed_emi = Decimal("120000.00")
            elif "STRESSED-MODERATE" in applicant_id:
                existing_emi = Decimal("260000.00")
                proposed_emi = Decimal("260000.00")
            elif "STRESSED-HEAVY" in applicant_id:
                existing_emi = Decimal("260000.00")
                proposed_emi = Decimal("260000.00")
                open_bal = Decimal("15000.00")

        elif archetype == "thin_file":
            # Strictly 4 to 9 months
            tf_vintages = [4, 4, 5, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 9, 9]
            num_part = applicant_id.split("-")[1]
            vintage_months = tf_vintages[int(num_part) % len(tf_vintages)]
            open_bal = Decimal("150000.00")
            existing_emi = Decimal("15000.00")
            proposed_emi = Decimal("25000.00")

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
            "clause_isolation": clause_isolation,
            "near_threshold_clause": nt_clause,
            "target_boundary": target_boundary
        }

    @staticmethod
    def generate_transactions(profile: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Decimal]:
        seed = profile["seed"]
        rng = random.Random(seed)
        applicant_id = profile["applicant_id"]
        archetype = profile["archetype"]
        open_bal = Decimal(profile["opening_balance"])
        existing_emi = Decimal(profile["existing_monthly_emi"])
        od_limit = Decimal(profile["od_limit"])

        start_date = date.fromisoformat("2024-01-01")
        end_date = date.fromisoformat("2024-12-31")
        total_days = (end_date - start_date).days + 1

        buyers = BUYER_CORPORATES
        vendors = VENDOR_CORPORATES
        raw_txns = []
        running_bal = open_bal

        # Micro-jitter multiplier: unique per applicant seed between 0.985 and 1.015
        jitter = Decimal(str(round(0.985 + (rng.random() * 0.030), 4)))

        for d in range(total_days):
            txn_date = start_date + timedelta(days=d)
            m_idx = txn_date.month - 1
            date_str = txn_date.isoformat()

            # EMI on 5th
            if txn_date.day == 5 and existing_emi > 0:
                is_bounce = False
                if "ALONE-FIN03" in applicant_id:
                    is_bounce = (m_idx == 5)
                elif "STRESSED-MILD" in applicant_id:
                    is_bounce = (m_idx in [4, 9])
                elif "STRESSED-MODERATE" in applicant_id:
                    is_bounce = (m_idx in [3, 7, 10])
                elif "STRESSED-HEAVY" in applicant_id:
                    is_bounce = (m_idx in [2, 5, 8, 11])

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

            # Edge cases
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
                    "date": date_str, "amount": "230000.00", "type": "CREDIT",
                    "category": "SALES_RECEIPT", "counterparty": "Orbit Allied Traders",
                    "narration": "RTGS CR ORBIT ALLIED TRADERS"
                })
                raw_txns.append({
                    "date": (txn_date + timedelta(days=2)).isoformat(), "amount": "229000.00", "type": "DEBIT",
                    "category": "VENDOR_PAYMENT", "counterparty": "Orbit Allied Traders",
                    "narration": "RTGS DR ORBIT ALLIED TRADERS"
                })
                running_bal += (Decimal("230000.00") - Decimal("229000.00"))
            elif "NEAR-ROUNDTRIP-FAIL" in applicant_id and m_idx == 2 and txn_date.day == 10:
                raw_txns.append({
                    "date": date_str, "amount": "250000.00", "type": "CREDIT",
                    "category": "SALES_RECEIPT", "counterparty": "Orbit Allied Traders",
                    "narration": "RTGS CR ORBIT ALLIED TRADERS"
                })
                raw_txns.append({
                    "date": (txn_date + timedelta(days=2)).isoformat(), "amount": "248000.00", "type": "DEBIT",
                    "category": "VENDOR_PAYMENT", "counterparty": "Orbit Allied Traders",
                    "narration": "RTGS DR ORBIT ALLIED TRADERS"
                })
                running_bal += (Decimal("250000.00") - Decimal("248000.00"))

            # Operating Inflows (8 days per month)
            is_zero = ("ZERO-INFLOW" in applicant_id and m_idx == 6)
            if not is_zero:
                if txn_date.day in [3, 7, 11, 15, 18, 22, 25, 28]:
                    mult = Decimal("1.0")
                    if "NEAR-PASS-CV" in applicant_id:
                        mult = Decimal("2.05") if m_idx in [7, 8, 9, 10] else (Decimal("0.32") if m_idx in [0, 1, 2] else Decimal("1.0"))
                    elif "NEAR-FAIL-CV" in applicant_id:
                        mult = Decimal("2.15") if m_idx in [7, 8, 9, 10] else (Decimal("0.24") if m_idx in [0, 1, 2] else Decimal("1.0"))
                    elif archetype == "seasonal":
                        mult = Decimal("2.90") if m_idx in [7, 8, 9, 10] else (Decimal("0.05") if m_idx in [0, 1, 2] else Decimal("0.90"))

                    if "ALONE-ELIG02" in applicant_id:
                        base_inflow = Decimal("21875.00")  # 175k/mo -> 2.1M (<25L)
                    elif "NEAR-TURNOVER-FAIL" in applicant_id:
                        base_inflow = Decimal("25000.00")  # 200k/mo -> 2.4M (<25L)
                    elif "NEAR-TURNOVER-PASS" in applicant_id:
                        base_inflow = Decimal("27083.33")  # 216.6k/mo -> 2.6M (>=25L)
                    elif "ALONE-FIN02" in applicant_id or "NEAR-AMB-FAIL" in applicant_id or "NEAR-AMB-PASS" in applicant_id:
                        base_inflow = Decimal("100000.00")
                    else:
                        base_inflow = Decimal("125000.00")

                    cr_amt = (base_inflow * mult * jitter).quantize(Decimal("0.01"))

                    # Buyer selection
                    if "NEAR-FAIL-TOP1" in applicant_id:
                        buyer = buyers[0] if (txn_date.day in [3, 7, 11] or (txn_date.day == 15 and m_idx % 2 == 0)) else rng.choice(buyers[1:])
                    elif "NEAR-PASS-TOP1" in applicant_id:
                        buyer = buyers[0] if txn_date.day in [3, 7, 11] else rng.choice(buyers[1:])
                    elif "ALONE-FIN05" in applicant_id or archetype == "high_concentration":
                        buyer = buyers[0] if txn_date.day in [3, 7, 11, 15, 18] else rng.choice(buyers[1:])
                    else:
                        buyer = buyers[(d % len(buyers))]

                    raw_txns.append({
                        "date": date_str, "amount": str(cr_amt), "type": "CREDIT",
                        "category": "SALES_RECEIPT", "counterparty": buyer,
                        "narration": f"NEFT CR-{buyer[:16]}-INV-{d+100}"
                    })
                    running_bal += cr_amt

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
                    dr_amt = Decimal("97142.85") * jitter
                elif "NEAR-DSCR-FAIL" in applicant_id:
                    dr_amt = Decimal("99285.71") * jitter
                elif "ALONE-FIN01" in applicant_id:
                    dr_amt = Decimal("104000.00") * jitter
                elif "ALONE-FIN02" in applicant_id or "NEAR-AMB-FAIL" in applicant_id or "NEAR-AMB-PASS" in applicant_id:
                    dr_amt = Decimal("28571.42") * jitter
                elif "NEAR-FOIR-PASS" in applicant_id:
                    dr_amt = Decimal("28571.42") * jitter
                elif "NEAR-FOIR-FAIL" in applicant_id:
                    dr_amt = Decimal("28571.42") * jitter
                elif "ALONE-FIN04" in applicant_id:
                    dr_amt = Decimal("28571.42") * jitter
                elif "ALONE-ELIG02" in applicant_id or "NEAR-TURNOVER" in applicant_id:
                    dr_amt = Decimal("11428.57") * jitter
                elif archetype == "stressed":
                    dr_amt = Decimal("110000.00") * jitter
                else:
                    dr_amt = Decimal("75000.00") * jitter

                dr_amt = dr_amt.quantize(Decimal("0.01"))
                vendor = vendors[(d % len(vendors))]
                raw_txns.append({
                    "date": date_str, "amount": str(dr_amt), "type": "DEBIT",
                    "category": "VENDOR_PAYMENT", "counterparty": vendor,
                    "narration": f"RTGS DR TO {vendor[:16]} MAT SUPPLIES"
                })
                running_bal -= dr_amt

                if "ALONE-FIN02" in applicant_id or "NEAR-AMB-FAIL" in applicant_id or "NEAR-AMB-PASS" in applicant_id:
                    raw_txns.append({
                        "date": date_str, "amount": str(dr_amt), "type": "CREDIT",
                        "category": "OWN_ACCOUNT_TRANSFER", "counterparty": "Promoter Sweep Account",
                        "narration": "REPLENISH CR FROM CURRENT ACC 9921"
                    })
                    running_bal += dr_amt

        raw_txns.sort(key=lambda x: (x["date"], x.get("type") == "DEBIT"))
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

        if "DOC02-GST-DISCREPANT" in applicant_id or "ALONE-DOC02" in applicant_id:
            gstr3b_annual = (total_bank_sales * Decimal("0.75")).quantize(Decimal("0.01"))
        elif "NEAR-DOC02-PASS" in applicant_id:
            gstr3b_annual = (total_bank_sales * Decimal("1.19")).quantize(Decimal("0.01"))
        elif "NEAR-DOC02-FAIL" in applicant_id:
            gstr3b_annual = (total_bank_sales * Decimal("1.21")).quantize(Decimal("0.01"))
        else:
            gstr3b_annual = (total_bank_sales * Decimal("1.01")).quantize(Decimal("0.01"))

        return sequenced_txns, gstr3b_annual
