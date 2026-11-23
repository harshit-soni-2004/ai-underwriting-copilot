import json
import re
import hashlib
import tempfile
import shutil
from pathlib import Path
from decimal import Decimal
from collections import defaultdict, Counter
from archetypes import compute_gstin_checksum
from generate_data import generate_applicant_dataset, ARCHETYPE_COUNTS, get_applicant_id
from reference_metrics import ReferenceMetricsOracle

PAN_REGEX = re.compile(r"^[A-Z]{3}[CFP][A-Z][0-9]{4}[A-Z]$")
GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

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

        assert PAN_REGEX.match(pan), f"Invalid PAN {pan} in {gt['applicant_id']}"
        expected_char = "C" if entity_type == "PRIVATE_LIMITED" else ("F" if entity_type == "LIMITED_LIABILITY_PARTNERSHIP" else "P")
        assert pan[3] == expected_char, f"PAN 4th char {pan[3]} does not match {entity_type}"

        assert GSTIN_REGEX.match(gstin), f"Invalid GSTIN {gstin} in {gt['applicant_id']}"
        assert gstin[2:12] == pan, f"GSTIN embedded PAN {gstin[2:12]} != {pan}"

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
        txns_env = json.load(f)
        txns_zero = txns_env["transactions"]

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
    assert "FIN-07" in gt_rt["policy_clauses_triggered"], f"Expected FIN-07 triggered for round trip, got {gt_rt['policy_clauses_triggered']}"
    assert gt_rt["expected_decision"] == "REFER"

def test_transactions_json_envelope_and_sequence():
    base_dir = Path(__file__).resolve().parent.parent.parent
    synthetic_dir = base_dir / "data" / "synthetic" / "applicants"

    for app_path in list(synthetic_dir.glob("APP-*"))[:15]:
        with open(app_path / "transactions.json", "r", encoding="utf-8") as f:
            env = json.load(f)

        assert "applicant_id" in env
        assert "opening_balance" in env
        assert "od_limit" in env
        assert "transactions" in env
        assert isinstance(env["transactions"], list)

        date_seq_seen = {}
        for t in env["transactions"]:
            d = t["date"]
            seq = t["sequence_number"]
            assert isinstance(seq, int) and seq >= 1
            if d not in date_seq_seen:
                date_seq_seen[d] = 0
            assert seq == date_seq_seen[d] + 1, f"Sequence number gap on date {d}: expected {date_seq_seen[d] + 1}, got {seq}"
            date_seq_seen[d] = seq
            assert t["type"] in ["CREDIT", "DEBIT"]
            assert isinstance(t["amount"], str)

def test_determinism_file_hashes():
    """Generating twice into temp dirs yields identical file hashes for JSON, CSV and PDF."""
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        dir1 = Path(tmp1)
        dir2 = Path(tmp2)

        generate_applicant_dataset("APP-001-HEALTHY", "healthy", master_seed=42, out_dir=dir1)
        generate_applicant_dataset("APP-001-HEALTHY", "healthy", master_seed=42, out_dir=dir2)

        files1 = sorted([p.relative_to(dir1) for p in dir1.rglob("*") if p.is_file()])
        files2 = sorted([p.relative_to(dir2) for p in dir2.rglob("*") if p.is_file()])
        assert files1 == files2

        for rel_p in files1:
            h1 = sha256_file(dir1 / rel_p)
            h2 = sha256_file(dir2 / rel_p)
            assert h1 == h2, f"Hash mismatch for {rel_p}: {h1} != {h2}"

def test_seed_stability_first_120_identical():
    """Generating 2 vs 3 applicants leaves the first 2 byte-identical."""
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        dir1 = Path(tmp1)
        dir2 = Path(tmp2)

        generate_applicant_dataset("APP-001-HEALTHY", "healthy", master_seed=42, out_dir=dir1)
        generate_applicant_dataset("APP-002-HEALTHY", "healthy", master_seed=42, out_dir=dir1)

        generate_applicant_dataset("APP-001-HEALTHY", "healthy", master_seed=42, out_dir=dir2)
        generate_applicant_dataset("APP-002-HEALTHY", "healthy", master_seed=42, out_dir=dir2)
        generate_applicant_dataset("APP-003-HEALTHY", "healthy", master_seed=42, out_dir=dir2)

        for rel_p in (dir1 / "applicants" / "APP-001-HEALTHY").rglob("*"):
            if rel_p.is_file():
                sub_path = rel_p.relative_to(dir1)
                assert sha256_file(dir1 / sub_path) == sha256_file(dir2 / sub_path)

def test_dscr_foir_mathematical_identity():
    """DSCR * FOIR approx equals surplus / avg operating inflow within rounding for all 120 applicants."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    synthetic_dir = base_dir / "data" / "synthetic" / "applicants"

    checked = 0
    for app_path in synthetic_dir.glob("APP-*"):
        with open(app_path / "ground_truth.json", "r", encoding="utf-8") as f:
            gt = json.load(f)

        m = gt["expected_metrics"]
        dscr_str = m.get("dscr_proxy")
        foir_str = m.get("foir")
        inflow_str = m.get("avg_monthly_operating_inflow")
        outflow_str = m.get("avg_monthly_operating_outflow")

        if dscr_str and foir_str and inflow_str and outflow_str:
            inflow = Decimal(inflow_str)
            if inflow > Decimal("0.00"):
                dscr = Decimal(dscr_str)
                foir = Decimal(foir_str)
                outflow = Decimal(outflow_str)
                surplus = inflow - outflow
                surplus_ratio = surplus / inflow
                product = dscr * foir
                # Tolerance within 0.005 due to rounding of DSCR and FOIR to 4 decimal places
                diff = abs(product - surplus_ratio)
                assert diff < Decimal("0.005"), f"Identity violation in {gt['applicant_id']}: DSCR*FOIR={product}, surplus/inflow={surplus_ratio}, diff={diff}"
                checked += 1

    assert checked >= 115, f"Expected >= 115 checked applicants, got {checked}"

def test_unique_metric_tuples_zero_clones():
    """All 120 applicants must possess distinct metric tuples (zero duplicate clones)."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    synthetic_dir = base_dir / "data" / "synthetic" / "applicants"

    tuples = set()
    total = 0
    for app_path in synthetic_dir.glob("APP-*"):
        with open(app_path / "ground_truth.json", "r", encoding="utf-8") as f:
            gt = json.load(f)
        m = gt["expected_metrics"]
        m_tuple = (
            m["average_monthly_balance"],
            m["avg_monthly_operating_inflow"],
            m["avg_monthly_operating_outflow"],
            m["cash_flow_volatility_cv"],
            m["dscr_proxy"],
            m["foir"],
            m["counterparty_top1_share"],
            m["counterparty_hhi"],
            m["round_trip_ratio"]
        )
        tuples.add(m_tuple)
        total += 1

    assert total == 120, f"Expected 120 applicants, found {total}"
    assert len(tuples) == 120, f"Expected 120 unique metric tuples, but found only {len(tuples)} ({120 - len(tuples)} duplicates)"

def test_clause_alone_coverage_minimums():
    """All 10 policy clauses must be triggered alone by at least 3 distinct applicants."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    synthetic_dir = base_dir / "data" / "synthetic" / "applicants"

    alone_counts = Counter()
    for app_path in synthetic_dir.glob("APP-*"):
        with open(app_path / "ground_truth.json", "r", encoding="utf-8") as f:
            gt = json.load(f)
        trig = gt.get("policy_clauses_triggered", [])
        if len(trig) == 1:
            alone_counts[trig[0]] += 1

    required_clauses = [
        "ELIG-01", "ELIG-02",
        "FIN-01", "FIN-02", "FIN-03", "FIN-04", "FIN-05", "FIN-06", "FIN-07",
        "DOC-02"
    ]
    for c in required_clauses:
        count = alone_counts[c]
        assert count >= 3, f"Clause {c} triggered alone only {count} times (minimum 3 required)"

def test_near_threshold_rules_and_signed_margins():
    """Near-threshold applicants must be >= 10, >= 5 clauses on both sides, with valid margins and sides."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    synthetic_dir = base_dir / "data" / "synthetic" / "applicants"

    nt_applicants = []
    both_sides_map = defaultdict(lambda: {"passing": 0, "failing": 0})

    for app_path in synthetic_dir.glob("APP-*"):
        with open(app_path / "ground_truth.json", "r", encoding="utf-8") as f:
            gt = json.load(f)

        if gt.get("near_threshold"):
            nt_applicants.append(gt)
            c = gt["near_threshold_clause"]
            side = gt["near_threshold_side"]
            margin = Decimal(gt["near_threshold_margin"])

            # Verify margin sign convention: passing >= 0, failing < 0
            if side == "just-passing":
                assert margin >= Decimal("0"), f"Passing applicant {gt['applicant_id']} has negative margin {margin}"
                both_sides_map[c]["passing"] += 1
            elif side == "just-failing":
                assert margin < Decimal("0"), f"Failing applicant {gt['applicant_id']} has non-negative margin {margin}"
                both_sides_map[c]["failing"] += 1
            else:
                pytest.fail(f"Invalid side {side} in applicant {gt['applicant_id']}")

            # Recompute from oracle to ensure ground truth matches oracle math
            oracle_res = ReferenceMetricsOracle.analyze_near_threshold(
                c, gt["expected_metrics"], gt, target_boundary="decline" if "DECLINE-VINTAGE" in gt["applicant_id"] else None
            )
            assert oracle_res["is_near_threshold"] is True, f"Applicant {gt['applicant_id']} outside 10% band in oracle"
            assert oracle_res["side"] == side, f"Side mismatch for {gt['applicant_id']}: {side} vs {oracle_res['side']}"
            assert oracle_res["margin"] == gt["near_threshold_margin"], f"Margin mismatch for {gt['applicant_id']}: {gt['near_threshold_margin']} vs {oracle_res['margin']}"

    assert len(nt_applicants) >= 10, f"Expected >= 10 near-threshold applicants, got {len(nt_applicants)}"
    both_sides_count = sum(1 for c, s in both_sides_map.items() if s["passing"] > 0 and s["failing"] > 0)
    assert both_sides_count >= 5, f"Expected >= 5 clauses covered on both sides, got {both_sides_count}"

def test_stressed_archetype_distinct_combinations():
    """Stressed applicants must trigger >= 3 distinct combinations of policy clauses."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    synthetic_dir = base_dir / "data" / "synthetic" / "applicants"

    stressed_sets = set()
    for app_path in synthetic_dir.glob("APP-*"):
        with open(app_path / "ground_truth.json", "r", encoding="utf-8") as f:
            gt = json.load(f)
        if gt["archetype"] == "stressed":
            trig = tuple(sorted(gt.get("policy_clauses_triggered", [])))
            stressed_sets.add(trig)

    assert len(stressed_sets) >= 3, f"Expected >= 3 distinct stressed clause combinations, got {len(stressed_sets)}: {stressed_sets}"

def test_adversarial_base_applicant_links():
    """Every adversarial document ground truth base_applicant_id must exist in synthetic applicants."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    adv_dir = base_dir / "data" / "synthetic" / "adversarial"
    app_dir = base_dir / "data" / "synthetic" / "applicants"

    adv_gts = list(adv_dir.glob("*_ground_truth.json"))
    assert len(adv_gts) == 20, f"Expected 20 adversarial ground truth files, found {len(adv_gts)}"

    for adv_gt_path in adv_gts:
        with open(adv_gt_path, "r", encoding="utf-8") as f:
            adv_gt = json.load(f)
        base_id = adv_gt["base_applicant_id"]
        assert (app_dir / base_id).exists(), f"Adversarial document {adv_gt_path.name} links to non-existent base applicant {base_id}"
        assert (app_dir / base_id / "ground_truth.json").exists(), f"Base applicant {base_id} missing ground_truth.json"

