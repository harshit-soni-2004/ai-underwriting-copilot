import json
from pathlib import Path
from decimal import Decimal

def test_dataset_generation_completeness():
    base_dir = Path(__file__).resolve().parent.parent.parent
    synthetic_dir = base_dir / "data" / "synthetic" / "applicants"
    fixtures_dir = base_dir / "data" / "fixtures" / "applicants"
    adv_dir = base_dir / "data" / "synthetic" / "adversarial"

    # Check 120 applicants in synthetic
    applicants = list(synthetic_dir.glob("APP-*"))
    assert len(applicants) == 120, f"Expected 120 applicants, found {len(applicants)}"

    # Check 12 fixtures committed
    fixtures = list(fixtures_dir.glob("APP-*"))
    assert len(fixtures) == 12, f"Expected 12 fixtures, found {len(fixtures)}"

    # Check 20 adversarial documents
    adv_docs = list(adv_dir.glob("*_adversarial_invoice.pdf"))
    assert len(adv_docs) == 20, f"Expected 20 adversarial PDFs, found {len(adv_docs)}"

def test_ground_truth_and_transactions_schema():
    base_dir = Path(__file__).resolve().parent.parent.parent
    fixtures_dir = base_dir / "data" / "fixtures" / "applicants"

    for app_path in fixtures_dir.glob("APP-*"):
        gt_path = app_path / "ground_truth.json"
        txns_path = app_path / "transactions.json"

        assert gt_path.exists(), f"Missing ground_truth.json in {app_path}"
        assert txns_path.exists(), f"Missing transactions.json in {app_path}"

        with open(gt_path, "r", encoding="utf-8") as f:
            gt = json.load(f)

        assert "applicant_id" in gt
        assert "archetype" in gt
        assert "expected_metrics" in gt
        assert "expected_decision" in gt
        assert "policy_clauses_triggered" in gt

        metrics = gt["expected_metrics"]
        for key in ["average_monthly_balance", "avg_monthly_operating_inflow", "avg_monthly_operating_outflow", "bounce_rate"]:
            assert isinstance(metrics[key], str), f"Metric {key} should be string, got {type(metrics[key])}"
            # Verify can be parsed by Decimal
            Decimal(metrics[key])

        with open(txns_path, "r", encoding="utf-8") as f:
            txns = json.load(f)

        assert len(txns) > 0
        for t in txns:
            assert isinstance(t["amount"], str), f"Transaction amount must be string, got {type(t['amount'])}"
            assert t["type"] in ["CREDIT", "DEBIT"]
            assert "category" in t
            assert "counterparty" in t
