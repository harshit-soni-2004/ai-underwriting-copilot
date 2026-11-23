import json
from decimal import Decimal
from datetime import date
from pathlib import Path
import pytest
from reference_metrics import ReferenceMetricsOracle

def test_canonical_hand_worked_fixtures_from_json():
    fixtures_file = Path(__file__).resolve().parent.parent.parent / "data" / "fixtures" / "canonical_hand_worked_fixtures.json"
    with open(fixtures_file, "r", encoding="utf-8") as f:
        fixtures = json.load(f)

    for fix in fixtures:
        f_id = fix["fixture_id"]
        open_bal = Decimal(fix["opening_balance"])
        start_d = date.fromisoformat(fix["statement_start_date"])
        end_d = date.fromisoformat(fix["statement_end_date"])
        ex_emi = Decimal(fix["existing_monthly_emi"])
        pr_emi = Decimal(fix["proposed_monthly_emi"])
        gst_ann = Decimal(fix["gstr3b_annual_taxable_supplies"]) if "gstr3b_annual_taxable_supplies" in fix else None

        res = ReferenceMetricsOracle.calculate_all(
            transactions=fix["transactions"],
            opening_balance=open_bal,
            statement_start_date=start_d,
            statement_end_date=end_d,
            existing_monthly_emi=ex_emi,
            proposed_monthly_emi=pr_emi,
            gstr3b_annual_taxable_supplies=gst_ann
        )

        for key, exp_val in fix["expected_metrics"].items():
            if key == "excluded_inflows_breakdown":
                assert res["excluded_inflows_breakdown"] == exp_val, f"Mismatch in {f_id} excluded inflows"
            else:
                assert res[key] == exp_val, f"Mismatch in {f_id} for key {key}: expected {exp_val}, got {res[key]}"

@pytest.mark.parametrize("clause,metric_key,test_value,applicant_extra,expected_decision,should_trigger", [
    # ELIG-01 (Vintage in months: <6 decline, 6-23 refer, >=24 pass)
    ("ELIG-01", "vintage_months", 5, {}, "DECLINE", True),
    ("ELIG-01", "vintage_months", 6, {}, "REFER", True),
    ("ELIG-01", "vintage_months", 23, {}, "REFER", True),
    ("ELIG-01", "vintage_months", 24, {}, "APPROVE", False),
    ("ELIG-01", "vintage_months", 25, {}, "APPROVE", False),

    # ELIG-02 (Turnover annual: <25L refer, >=25L pass)
    ("ELIG-02", "avg_monthly_operating_inflow", "200000.00", {}, "REFER", True),     # 24.0 Lakh
    ("ELIG-02", "avg_monthly_operating_inflow", "208333.34", {}, "APPROVE", False),   # 25.0 Lakh (>=25L pass)
    ("ELIG-02", "avg_monthly_operating_inflow", "220000.00", {}, "APPROVE", False),   # 26.4 Lakh

    # FIN-01 (DSCR: <1.0 decline, 1.0-1.24 refer, >=1.25 pass)
    ("FIN-01", "dscr_proxy", "0.9900", {}, "DECLINE", True),
    ("FIN-01", "dscr_proxy", "1.0000", {}, "REFER", True),
    ("FIN-01", "dscr_proxy", "1.2400", {}, "REFER", True),
    ("FIN-01", "dscr_proxy", "1.2500", {}, "APPROVE", False),
    ("FIN-01", "dscr_proxy", "1.5500", {}, "APPROVE", False),

    # FIN-02 (AMB vs Proposed EMI >= 10%: <10% refer, >=10% pass)
    ("FIN-02", "average_monthly_balance", "4900.00", {"proposed_monthly_emi": "50000.00"}, "REFER", True),
    ("FIN-02", "average_monthly_balance", "5000.00", {"proposed_monthly_emi": "50000.00"}, "APPROVE", False),
    ("FIN-02", "average_monthly_balance", "5500.00", {"proposed_monthly_emi": "50000.00"}, "APPROVE", False),

    # FIN-03 (Inward Returns: 0 pass, 1-3 refer, >3 decline)
    ("FIN-03", "inward_clearing_returns_count", 0, {}, "APPROVE", False),
    ("FIN-03", "inward_clearing_returns_count", 1, {}, "REFER", True),
    ("FIN-03", "inward_clearing_returns_count", 2, {}, "REFER", True),
    ("FIN-03", "inward_clearing_returns_count", 3, {}, "REFER", True),
    ("FIN-03", "inward_clearing_returns_count", 4, {}, "DECLINE", True),

    # FIN-04 (FOIR: <= 0.50 pass, > 0.50 refer)
    ("FIN-04", "foir", "0.4900", {}, "APPROVE", False),
    ("FIN-04", "foir", "0.5000", {}, "APPROVE", False),
    ("FIN-04", "foir", "0.5100", {}, "REFER", True),

    # FIN-05 (Top-1 Share: <= 0.40 pass, > 0.40 refer)
    ("FIN-05", "counterparty_top1_share", "0.3900", {}, "APPROVE", False),
    ("FIN-05", "counterparty_top1_share", "0.4000", {}, "APPROVE", False),
    ("FIN-05", "counterparty_top1_share", "0.4100", {}, "REFER", True),

    # FIN-06 (Volatility CV: <= 0.60 pass, > 0.60 refer)
    ("FIN-06", "cash_flow_volatility_cv", "0.5900", {}, "APPROVE", False),
    ("FIN-06", "cash_flow_volatility_cv", "0.6000", {}, "APPROVE", False),
    ("FIN-06", "cash_flow_volatility_cv", "0.6100", {}, "REFER", True),

    # FIN-07 (Round-Trip Ratio: <= 0.0200 pass, > 0.0200 refer)
    ("FIN-07", "round_trip_ratio", "0.0190", {}, "APPROVE", False),
    ("FIN-07", "round_trip_ratio", "0.0200", {}, "APPROVE", False),
    ("FIN-07", "round_trip_ratio", "0.0210", {}, "REFER", True),

    # DOC-02 (GST Discrepancy: |ratio - 1.0| <= 0.20 pass, > 0.20 refer)
    ("DOC-02", "gst_turnover_ratio", "1.1900", {}, "APPROVE", False),
    ("DOC-02", "gst_turnover_ratio", "1.2000", {}, "APPROVE", False),
    ("DOC-02", "gst_turnover_ratio", "1.2100", {}, "REFER", True),
    ("DOC-02", "gst_turnover_ratio", "0.8100", {}, "APPROVE", False),
    ("DOC-02", "gst_turnover_ratio", "0.7900", {}, "REFER", True),
])
def test_policy_clauses_parametrized(clause, metric_key, test_value, applicant_extra, expected_decision, should_trigger):
    # Base clean metric setup (would normally APPROVE)
    base_metrics = {
        "average_monthly_balance": "500000.00",
        "avg_monthly_operating_inflow": "400000.00",
        "avg_monthly_operating_outflow": "200000.00",
        "dscr_proxy": "1.6000",
        "inward_clearing_returns_count": 0,
        "foir": "0.2000",
        "counterparty_top1_share": "0.2500",
        "cash_flow_volatility_cv": "0.2000",
        "round_trip_ratio": "0.0000",
        "gst_turnover_ratio": "1.0000"
    }

    base_profile = {
        "vintage_months": 36,
        "proposed_monthly_emi": "20000.00"
    }

    # Inject test value into either metrics or profile
    if metric_key in base_metrics:
        base_metrics[metric_key] = test_value
    elif metric_key in base_profile:
        base_profile[metric_key] = test_value

    base_profile.update(applicant_extra)

    dec, triggered = ReferenceMetricsOracle.evaluate_policy(base_metrics, base_profile)

    if should_trigger:
        assert clause in triggered, f"Clause {clause} should have triggered for {metric_key}={test_value}"
        assert dec == expected_decision, f"Expected {expected_decision}, got {dec} for {metric_key}={test_value}"
    else:
        assert clause not in triggered, f"Clause {clause} should NOT have triggered for {metric_key}={test_value}"
        if not triggered:
            assert dec == "APPROVE"
