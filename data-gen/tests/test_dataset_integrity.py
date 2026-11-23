import json
import re
from pathlib import Path
from decimal import Decimal
from archetypes import compute_gstin_checksum

PAN_REGEX = re.compile(r"^[A-Z]{3}[CFP][A-Z][0-9]{4}[A-Z]$")
GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")

def test_dataset_generation_completeness():
    base_dir = Path(__file__).resolve().parent.parent.parent
    synthetic_dir = base_dir / "data" / "synthetic" / "applicants"
    fixtures_dir = base_dir / "data" / "fixtures" / "applicants"
    adv_dir = base_dir / "data" / "synthetic" / "adversarial"

    applicants = list(synthetic_dir.glob("APP-*"))
    assert len(applicants) == 120, f"Expected 120 applicants, found {len(applicants)}"

    fixtures = list(fixtures_dir.glob("APP-*"))
    assert len(fixtures) == 12, f"Expected 12 fixtures, found {len(fixtures)}"

    adv_docs = list(adv_dir.glob("*_adversarial_invoice.pdf"))
    assert len(adv_docs) == 20, f"Expected 20 adversarial PDFs, found {len(adv_docs)}"

def test_pan_and_gstin_validity_and_checksum():
    base_dir = Path(__file__).resolve().parent.parent.parent
    synthetic_dir = base_dir / "data" / "synthetic" / "applicants"

    for app_path in synthetic_dir.glob("APP-*"):
        gt_path = app_path / "ground_truth.json"
        with open(gt_path, "r", encoding="utf-8") as f:
            gt = json.load(f)

        pan = gt["pan"]
        gstin = gt["gstin"]
        entity_type = gt["legal_entity_type"]

        # Validate PAN structure
        assert PAN_REGEX.match(pan), f"Invalid PAN {pan} in {gt['applicant_id']}"
        expected_char = "C" if entity_type == "PRIVATE_LIMITED" else ("F" if entity_type == "LIMITED_LIABILITY_PARTNERSHIP" else "P")
        assert pan[3] == expected_char, f"PAN 4th char {pan[3]} does not match {entity_type}"

        # Validate GSTIN structure & state + PAN match
        assert GSTIN_REGEX.match(gstin), f"Invalid GSTIN {gstin} in {gt['applicant_id']}"
        assert gstin[2:12] == pan, f"GSTIN embedded PAN {gstin[2:12]} != {pan}"

        # Validate Indian GSTIN Mod 36 Checksum
        calculated_checksum = compute_gstin_checksum(gstin[:14])
        assert gstin[14] == calculated_checksum, f"GSTIN checksum mismatch in {gstin}: expected {calculated_checksum}, got {gstin[14]}"

def test_edge_cases_contain_their_edges():
    base_dir = Path(__file__).resolve().parent.parent.parent
    synthetic_dir = base_dir / "data" / "synthetic" / "applicants"

    # 1. Zero-inflow applicant
    zero_inflow_apps = list(synthetic_dir.glob("*ZERO-INFLOW*"))
    assert len(zero_inflow_apps) > 0
    with open(zero_inflow_apps[0] / "ground_truth.json", "r", encoding="utf-8") as f:
        gt_zero = json.load(f)
    with open(zero_inflow_apps[0] / "transactions.json", "r", encoding="utf-8") as f:
        txns_zero = json.load(f)

    # Prove July (2024-07) has zero sales receipts
    july_sales = [t for t in txns_zero if t["type"] == "CREDIT" and t["category"] == "SALES_RECEIPT" and t["date"].startswith("2024-07")]
    assert len(july_sales) == 0, f"Expected 0 July sales receipts, got {len(july_sales)}"
    cv = Decimal(gt_zero["expected_metrics"]["cash_flow_volatility_cv"])
    assert cv >= Decimal("0.30"), f"Expected CV >= 0.30 for zero-inflow month, got {cv}"

    # 2. Large credit / asset sale applicant
    large_cred_apps = list(synthetic_dir.glob("*LARGE-CREDIT*"))
    assert len(large_cred_apps) > 0
    with open(large_cred_apps[0] / "ground_truth.json", "r", encoding="utf-8") as f:
        gt_large = json.load(f)
    breakdown = gt_large["expected_metrics"]["excluded_inflows_breakdown"]
    assert "ONE_OFF" in breakdown, f"Expected ONE_OFF in excluded breakdown, got {breakdown}"
    assert Decimal(breakdown["ONE_OFF"]) >= Decimal("1000000.00")

    # 3. Round trip applicant
    round_trip_apps = list(synthetic_dir.glob("*ROUND-TRIP*"))
    assert len(round_trip_apps) > 0
    with open(round_trip_apps[0] / "ground_truth.json", "r", encoding="utf-8") as f:
        gt_rt = json.load(f)
    breakdown_rt = gt_rt["expected_metrics"]["excluded_inflows_breakdown"]
    assert "ROUND_TRIP" in breakdown_rt, f"Expected ROUND_TRIP in breakdown, got {breakdown_rt}"
    assert Decimal(breakdown_rt["ROUND_TRIP"]) >= Decimal("400000.00")

def test_near_threshold_count_and_clean_schema():
    base_dir = Path(__file__).resolve().parent.parent.parent
    synthetic_dir = base_dir / "data" / "synthetic" / "applicants"

    near_threshold_count = 0
    for app_path in synthetic_dir.glob("APP-*"):
        gt_path = app_path / "ground_truth.json"
        with open(gt_path, "r", encoding="utf-8") as f:
            gt = json.load(f)

        # Expected decision and policy clauses at top level ONLY
        assert "expected_decision" in gt
        assert "policy_clauses_triggered" in gt
        assert "expected_decision" not in gt["expected_metrics"]
        assert "policy_clauses_triggered" not in gt["expected_metrics"]

        if gt.get("near_threshold", False):
            near_threshold_count += 1

    assert near_threshold_count >= 10, f"Expected >= 10 near_threshold applicants, found {near_threshold_count}"
