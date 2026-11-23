"""
Master Synthetic MSME Applicant and Document Generator.
Generates 120 reproducible synthetic MSME applicants with multi-layout bank statements,
invoices, GST filings, clean transactions.json, and ground-truth metrics.
"""

import argparse
import json
import shutil
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List

from archetypes import ArchetypeGenerator
from bank_statement_gen import BankStatementGenerator
from invoice_gen import InvoiceGenerator
from gst_gen import GstReturnGenerator
from reference_metrics import ReferenceMetricsOracle
from adversarial_gen import AdversarialGenerator

ARCHETYPE_COUNTS = [
    ("healthy", 30),
    ("seasonal", 20),
    ("high_concentration", 20),
    ("stressed", 20),
    ("thin_file", 15),
    ("edge_cases", 15)
]

def generate_applicant_dataset(
    applicant_id: str,
    archetype: str,
    master_seed: int,
    out_dir: Path
) -> Dict[str, Any]:
    app_dir = out_dir / "applicants" / applicant_id
    app_dir.mkdir(parents=True, exist_ok=True)

    # 1. Profile & Transactions
    profile = ArchetypeGenerator.generate_applicant_profile(applicant_id, archetype, master_seed)
    txns, gstr3b_annual = ArchetypeGenerator.generate_transactions(profile)

    # 2. Reference Metrics Ground Truth
    open_bal = Decimal(profile["opening_balance"])
    start_date = date.fromisoformat(profile["statement_start_date"])
    end_date = date.fromisoformat(profile["statement_end_date"])
    existing_emi = Decimal(profile["existing_monthly_emi"])
    proposed_emi = Decimal(profile["proposed_monthly_emi"])

    expected_metrics = ReferenceMetricsOracle.calculate_all(
        transactions=txns,
        opening_balance=open_bal,
        statement_start_date=start_date,
        statement_end_date=end_date,
        existing_monthly_emi=existing_emi,
        proposed_monthly_emi=proposed_emi,
        gstr3b_annual_taxable_supplies=gstr3b_annual
    )

    # 3. Policy Evaluation
    expected_decision, policy_clauses_triggered = ReferenceMetricsOracle.evaluate_policy(
        expected_metrics, profile
    )

    # 4. Clean transactions.json with envelope structure
    transactions_envelope = {
        "applicant_id": applicant_id,
        "opening_balance": profile["opening_balance"],
        "od_limit": profile.get("od_limit", "0.00"),
        "transactions": txns
    }
    with open(app_dir / "transactions.json", "w", encoding="utf-8") as f:
        json.dump(transactions_envelope, f, indent=2)

    # 5. Bank Statements (HDFC CSV + PDF, SBI CSV + PDF, ICICI CSV)
    stmts_dir = app_dir / "bank_statements"
    stmts_dir.mkdir(parents=True, exist_ok=True)

    BankStatementGenerator.generate_hdfc_csv(txns, open_bal, stmts_dir / "statement_hdfc.csv")
    BankStatementGenerator.generate_pdf_statement("HDFC", profile["business_name"], "5010023489102", txns, open_bal, stmts_dir / "statement_hdfc.pdf")

    BankStatementGenerator.generate_sbi_csv(txns, open_bal, stmts_dir / "statement_sbi.csv")
    BankStatementGenerator.generate_pdf_statement("State Bank of India", profile["business_name"], "30924810293", txns, open_bal, stmts_dir / "statement_sbi.pdf")

    BankStatementGenerator.generate_icici_csv(txns, open_bal, stmts_dir / "statement_icici.csv")

    # 6. Invoices
    inv_dir = app_dir / "invoices"
    inv_dir.mkdir(parents=True, exist_ok=True)
    sales_txns = [t for t in txns if t["type"] == "CREDIT" and t["category"] == "SALES_RECEIPT"]
    for i, st in enumerate(sales_txns[:12]):
        inv_no = f"INV-2024-{i+1:03d}"
        InvoiceGenerator.generate_invoice_pdf(
            invoice_number=inv_no,
            invoice_date=st["date"],
            seller_name=profile["business_name"],
            seller_gstin=profile["gstin"],
            buyer_name=st["counterparty"],
            buyer_gstin=f"27AABCU{i+1000}F1Z5",
            items=[{
                "description": f"Industrial Supplies #{i+1}",
                "hsn": "8481",
                "qty": 5,
                "rate": float(Decimal(st["amount"]) / Decimal("5.9"))
            }],
            out_path=inv_dir / f"{inv_no}.pdf"
        )

    # 7. GSTR-3B filings
    gst_dir = app_dir / "gst_returns"
    gst_dir.mkdir(parents=True, exist_ok=True)
    GstReturnGenerator.generate_gstr3b_returns(
        applicant_id=applicant_id,
        gstin=profile["gstin"],
        annual_taxable_supplies=gstr3b_annual,
        start_date=profile["statement_start_date"],
        end_date=profile["statement_end_date"],
        out_json_path=gst_dir / "gstr3b_filings.json",
        out_csv_path=gst_dir / "gstr3b_filings.csv"
    )

    # 8. Ground Truth JSON
    nt_clause = profile.get("near_threshold_clause", "")
    nt_val = profile.get("near_threshold_metric_value", "")
    nt_thresh = profile.get("near_threshold_threshold", "")
    nt_margin = profile.get("near_threshold_margin", "")
    nt_side = profile.get("near_threshold_side", "")

    if profile.get("near_threshold"):
        if nt_clause == "FIN-01":
            nt_val = expected_metrics["dscr_proxy"]
            nt_margin = f"{Decimal(nt_val) - Decimal('1.2500'):+.4f}"
        elif nt_clause == "FIN-02":
            nt_val = expected_metrics["average_monthly_balance"]
            nt_margin = f"{Decimal(nt_val) - Decimal('25000.00'):+.2f}"
        elif nt_clause == "FIN-04":
            nt_val = expected_metrics["foir"]
            nt_margin = f"{Decimal(nt_val) - Decimal('0.5000'):+.4f}"
        elif nt_clause == "FIN-05":
            nt_val = expected_metrics["counterparty_top1_share"]
            nt_margin = f"{Decimal(nt_val) - Decimal('0.4000'):+.4f}"
        elif nt_clause == "FIN-06":
            nt_val = expected_metrics["cash_flow_volatility_cv"]
            nt_margin = f"{Decimal(nt_val) - Decimal('0.6000'):+.4f}"
        elif nt_clause == "FIN-07":
            nt_val = expected_metrics["round_trip_ratio"]
            nt_margin = f"{Decimal(nt_val) - Decimal('0.0200'):+.4f}"
        elif nt_clause == "ELIG-01":
            nt_val = str(profile["vintage_months"])
            nt_margin = f"{int(nt_val) - int(nt_thresh):+d}"
        elif nt_clause == "ELIG-02":
            nt_val = str(Decimal(expected_metrics["avg_monthly_operating_inflow"]) * 12)
            nt_margin = f"{Decimal(nt_val) - Decimal('2500000.00'):+.2f}"
        elif nt_clause == "DOC-02":
            nt_val = expected_metrics["gst_turnover_ratio"]
            nt_margin = f"{Decimal(nt_val) - Decimal('1.2000'):+.4f}"

    ground_truth = {
        "applicant_id": applicant_id,
        "business_name": profile["business_name"],
        "legal_entity_type": profile["legal_entity_type"],
        "archetype": archetype,
        "sector": profile["sector"],
        "vintage_months": profile["vintage_months"],
        "gstin": profile["gstin"],
        "pan": profile["pan"],
        "seed": profile["seed"],
        "opening_balance": profile["opening_balance"],
        "od_limit": profile.get("od_limit", "0.00"),
        "requested_loan_amount": profile["requested_loan_amount"],
        "existing_monthly_emi": profile["existing_monthly_emi"],
        "proposed_monthly_emi": profile["proposed_monthly_emi"],
        "statement_start_date": profile["statement_start_date"],
        "statement_end_date": profile["statement_end_date"],
        "near_threshold": profile.get("near_threshold", False),
        "near_threshold_clause": nt_clause,
        "near_threshold_metric_value": nt_val,
        "near_threshold_threshold": nt_thresh,
        "near_threshold_margin": nt_margin,
        "near_threshold_side": nt_side,
        "expected_decision": expected_decision,
        "policy_clauses_triggered": policy_clauses_triggered,
        "expected_metrics": expected_metrics
    }

    with open(app_dir / "ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    return ground_truth

def get_applicant_id(counter: int, archetype: str, idx: int) -> str:
    if archetype == "healthy":
        if idx in [12, 13, 14]:
            return f"APP-{counter:03d}-HEALTHY-ALONE-FIN01"
        elif idx in [15, 16, 17]:
            return f"APP-{counter:03d}-HEALTHY-ALONE-FIN02"
        elif idx in [18, 19, 20]:
            return f"APP-{counter:03d}-HEALTHY-ALONE-FIN04"
        elif idx in [21, 22, 23]:
            return f"APP-{counter:03d}-HEALTHY-ALONE-DOC02"
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
        if idx in [10, 11, 12, 13]:
            return f"APP-{counter:03d}-SEASONAL-NEAR-PASS-CV"
        elif idx in [14, 15, 16, 17, 18, 19]:
            return f"APP-{counter:03d}-SEASONAL-ALONE-FIN06"
        return f"APP-{counter:03d}-SEASONAL"

    elif archetype == "high_concentration":
        if idx in [10, 11, 12, 13]:
            return f"APP-{counter:03d}-HIGH_CONCENTRATION-NEAR-PASS-TOP1"
        elif idx in [14, 15, 16, 17, 18, 19]:
            return f"APP-{counter:03d}-HIGH_CONCENTRATION-ALONE-FIN05"
        return f"APP-{counter:03d}-HIGH_CONCENTRATION"

    elif archetype == "stressed":
        if idx in [0, 1, 2, 3]:
            return f"APP-{counter:03d}-STRESSED-ALONE-FIN03"
        elif idx in [4, 5, 6, 7, 8]:
            return f"APP-{counter:03d}-STRESSED-MILD"
        elif idx in [9, 10, 11, 12, 13, 14]:
            return f"APP-{counter:03d}-STRESSED-MODERATE"
        else:
            return f"APP-{counter:03d}-STRESSED-HEAVY"

    elif archetype == "thin_file":
        if idx in [0, 1, 2, 3]:
            return f"APP-{counter:03d}-THIN_FILE-ALONE-ELIG01"
        elif idx in [4, 5, 6]:
            return f"APP-{counter:03d}-THIN_FILE-NEAR-DECLINE-VINTAGE"
        elif idx in [7, 8, 9, 10]:
            return f"APP-{counter:03d}-THIN_FILE-NEAR-PASS-VINTAGE"
        else:
            return f"APP-{counter:03d}-THIN_FILE-NEAR-MATURE-VINTAGE"

    elif archetype == "edge_cases":
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
            "NEAR-DOC02-PASS",
            "NEAR-TURNOVER-PASS",
            "NEAR-DOC02-FAIL",
            "NEAR-TURNOVER-FAIL"
        ]
        sub = edge_subtypes[idx] if idx < len(edge_subtypes) else f"EDGE-{idx+1}"
        return f"APP-{counter:03d}-EDGE-{sub}"
    return f"APP-{counter:03d}-{archetype.upper()}"

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic MSME applicant dataset")
    parser.add_argument("--applicants", type=int, default=120, help="Total applicants to generate")
    parser.add_argument("--seed", type=int, default=42, help="Master random seed")
    parser.add_argument("--output-dir", type=str, default="data/synthetic", help="Output directory")
    parser.add_argument("--fixtures-dir", type=str, default="data/fixtures", help="Fixtures directory")
    args = parser.parse_args()

    out_path = Path(args.output_dir)
    fixtures_path = Path(args.fixtures_dir)

    print(f"Starting fresh generation of {args.applicants} synthetic applicants (Seed: {args.seed})...")

    app_base_dir = out_path / "applicants"
    if app_base_dir.exists():
        shutil.rmtree(app_base_dir)
    app_base_dir.mkdir(parents=True, exist_ok=True)

    counter = 1
    generated_profiles = []
    fixtures_selected = []

    for archetype, count in ARCHETYPE_COUNTS:
        for idx in range(count):
            if counter > args.applicants:
                break
            app_id = get_applicant_id(counter, archetype, idx)

            gt = generate_applicant_dataset(app_id, archetype, args.seed, out_path)
            generated_profiles.append(gt)

            if idx < 2:
                fixtures_selected.append((app_id, archetype))

            counter += 1

    # Generate 20 Adversarial Documents
    adv_dir = out_path / "adversarial"
    if adv_dir.exists():
        shutil.rmtree(adv_dir)
    adv_dir.mkdir(parents=True, exist_ok=True)
    print("Generating 20 adversarial injection document variants...")
    for v_idx in range(20):
        base_app = generated_profiles[v_idx % len(generated_profiles)]
        AdversarialGenerator.generate_adversarial_variant(base_app, v_idx, adv_dir)

    # Populate data/fixtures/ with the selected 12 applicants
    print(f"Copying {len(fixtures_selected)} canonical fixtures into {fixtures_path}...")
    fixtures_app_dir = fixtures_path / "applicants"
    if fixtures_app_dir.exists():
        shutil.rmtree(fixtures_app_dir)
    fixtures_app_dir.mkdir(parents=True, exist_ok=True)
    for app_id, arch in fixtures_selected:
        src = out_path / "applicants" / app_id
        dst = fixtures_app_dir / app_id
        shutil.copytree(src, dst)

    dst_adv = fixtures_path / "adversarial"
    if dst_adv.exists():
        shutil.rmtree(dst_adv)
    dst_adv.mkdir(parents=True, exist_ok=True)
    for adv_f in list(adv_dir.glob("*"))[:4]:
        shutil.copy(adv_f, dst_adv / adv_f.name)

    print(f"Data generation complete! Generated {len(generated_profiles)} applicants in {out_path} and {len(fixtures_selected)} fixtures in {fixtures_path}.")

if __name__ == "__main__":
    main()
