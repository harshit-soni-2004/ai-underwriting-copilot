from decimal import Decimal
from datetime import date
import pytest
from reference_metrics import ReferenceMetricsOracle

def test_fixture_01_clean_growth():
    transactions = [
        {"date": "2024-01-10", "amount": "50000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Alpha Corp", "narration": "NEFT CR"},
        {"date": "2024-01-20", "amount": "30000.00", "type": "DEBIT", "category": "VENDOR_PAYMENT", "counterparty": "Vendor X", "narration": "NEFT DR"},
        {"date": "2024-02-05", "amount": "60000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Beta Ltd", "narration": "RTGS CR"},
        {"date": "2024-02-15", "amount": "25000.00", "type": "DEBIT", "category": "VENDOR_PAYMENT", "counterparty": "Vendor Y", "narration": "NEFT DR"},
        {"date": "2024-03-10", "amount": "70000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Alpha Corp", "narration": "NEFT CR"},
        {"date": "2024-03-20", "amount": "35000.00", "type": "DEBIT", "category": "OPERATING_EXPENSE", "counterparty": "Utilities", "narration": "BILLPAY"}
    ]
    res = ReferenceMetricsOracle.calculate_all(
        transactions=transactions,
        opening_balance=Decimal("100000.00"),
        statement_start_date=date(2024, 1, 1),
        statement_end_date=date(2024, 3, 31),
        existing_monthly_emi=Decimal("10000.00"),
        proposed_monthly_emi=Decimal("5000.00"),
        gstr3b_annual_taxable_supplies=Decimal("180000.00")
    )
    assert res["average_monthly_balance"] == "157912.09"
    assert res["avg_monthly_operating_inflow"] == "60000.00"
    assert res["avg_monthly_operating_outflow"] == "30000.00"
    assert res["cash_flow_volatility_cv"] == "0.1361"
    assert res["inward_clearing_returns_count"] == 0
    assert res["bounce_rate"] == "0.0000"
    assert res["dscr_proxy"] == "2.0000"
    assert res["foir"] == "0.2500"
    assert res["counterparty_top1_share"] == "0.6667"
    assert res["counterparty_top3_share"] == "1.0000"
    assert res["gst_turnover_ratio"] == "1.0000"
    assert "FIN-05" in res["policy_clauses_triggered"]
    assert res["expected_decision"] == "REFER"

def test_fixture_02_stressed_bounces():
    transactions = [
        {"date": "2024-04-10", "amount": "30000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Buyer A", "narration": "NEFT CR"},
        {"date": "2024-04-15", "amount": "40000.00", "type": "DEBIT", "category": "DEBT_SERVICE", "counterparty": "Bank", "narration": "EMI DEBIT"},
        {"date": "2024-05-02", "amount": "20000.00", "type": "DEBIT", "category": "INWARD_CHEQUE_RETURN", "counterparty": "Third Party", "narration": "CHQ RET INSUFFICIENT FUNDS"},
        {"date": "2024-05-10", "amount": "25000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Buyer A", "narration": "NEFT CR"},
        {"date": "2024-05-20", "amount": "35000.00", "type": "DEBIT", "category": "VENDOR_PAYMENT", "counterparty": "Vendor Z", "narration": "CHQ DEBIT VENDOR"},
        {"date": "2024-06-05", "amount": "20000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Buyer A", "narration": "NEFT CR"},
        {"date": "2024-06-15", "amount": "22000.00", "type": "DEBIT", "category": "INWARD_NACH_RETURN", "counterparty": "Fintech", "narration": "NACH RET - BALANCE INSUFFICIENT"}
    ]
    res = ReferenceMetricsOracle.calculate_all(
        transactions=transactions,
        opening_balance=Decimal("25000.00"),
        statement_start_date=date(2024, 4, 1),
        statement_end_date=date(2024, 6, 30),
        existing_monthly_emi=Decimal("25000.00"),
        proposed_monthly_emi=Decimal("10000.00")
    )
    assert res["avg_monthly_operating_inflow"] == "25000.00"
    assert res["avg_monthly_operating_outflow"] == "11666.67"
    assert res["inward_clearing_returns_count"] == 2
    assert res["outward_cheque_returns_count"] == 0
    assert res["total_inward_clearing_attempts"] == 4
    assert res["bounce_rate"] == "0.5000"
    assert res["dscr_proxy"] == "0.3810"
    assert res["foir"] == "1.4000"
    assert res["expected_decision"] == "DECLINE"
    assert "FIN-01" in res["policy_clauses_triggered"]

def test_fixture_03_round_trip_exclusion():
    transactions = [
        {"date": "2024-01-05", "amount": "100000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Client Regular", "narration": "NEFT CR"},
        {"date": "2024-01-15", "amount": "200000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Entity Circle", "narration": "RTGS CR"},
        {"date": "2024-01-17", "amount": "198000.00", "type": "DEBIT", "category": "VENDOR_PAYMENT", "counterparty": "Entity Circle", "narration": "RTGS DR"},
        {"date": "2024-02-10", "amount": "500000.00", "type": "CREDIT", "category": "LOAN_DISBURSAL", "counterparty": "NBFC Lender", "narration": "LOAN DISBURSAL"},
        {"date": "2024-02-20", "amount": "120000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Client Regular", "narration": "NEFT CR"},
        {"date": "2024-03-10", "amount": "110000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Client Regular", "narration": "NEFT CR"}
    ]
    res = ReferenceMetricsOracle.calculate_all(
        transactions=transactions,
        opening_balance=Decimal("50000.00"),
        statement_start_date=date(2024, 1, 1),
        statement_end_date=date(2024, 3, 31),
        existing_monthly_emi=Decimal("15000.00"),
        proposed_monthly_emi=Decimal("10000.00")
    )
    assert res["avg_monthly_operating_inflow"] == "110000.00"
    assert res["excluded_inflows_breakdown"]["ROUND_TRIP"] == "200000.00"
    assert res["excluded_inflows_breakdown"]["LOAN_DISBURSAL"] == "500000.00"

def test_fixture_04_negative_surplus():
    transactions = [
        {"date": "2024-01-15", "amount": "40000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Client A", "narration": "NEFT CR"},
        {"date": "2024-01-20", "amount": "60000.00", "type": "DEBIT", "category": "VENDOR_PAYMENT", "counterparty": "Vendor A", "narration": "RTGS DR"},
        {"date": "2024-02-15", "amount": "35000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Client A", "narration": "NEFT CR"},
        {"date": "2024-02-20", "amount": "55000.00", "type": "DEBIT", "category": "VENDOR_PAYMENT", "counterparty": "Vendor A", "narration": "RTGS DR"},
        {"date": "2024-03-15", "amount": "45000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Client A", "narration": "NEFT CR"},
        {"date": "2024-03-20", "amount": "65000.00", "type": "DEBIT", "category": "VENDOR_PAYMENT", "counterparty": "Vendor A", "narration": "RTGS DR"}
    ]
    res = ReferenceMetricsOracle.calculate_all(
        transactions=transactions,
        opening_balance=Decimal("100000.00"),
        statement_start_date=date(2024, 1, 1),
        statement_end_date=date(2024, 3, 31),
        existing_monthly_emi=Decimal("15000.00"),
        proposed_monthly_emi=Decimal("5000.00")
    )
    assert res["avg_monthly_operating_inflow"] == "40000.00"
    assert res["avg_monthly_operating_outflow"] == "60000.00"
    assert res["is_negative_surplus"] is True
    assert res["dscr_proxy"] == "-1.0000"
    assert res["foir"] == "0.5000"
    assert res["expected_decision"] == "DECLINE"

def test_fixture_05_partial_month_start():
    transactions = [
        {"date": "2024-01-20", "amount": "40000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Client 1", "narration": "NEFT CR"},
        {"date": "2024-02-10", "amount": "90000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Client 1", "narration": "NEFT CR"},
        {"date": "2024-03-05", "amount": "95000.00", "type": "CREDIT", "category": "SALES_RECEIPT", "counterparty": "Client 1", "narration": "NEFT CR"}
    ]
    res = ReferenceMetricsOracle.calculate_all(
        transactions=transactions,
        opening_balance=Decimal("80000.00"),
        statement_start_date=date(2024, 1, 16),
        statement_end_date=date(2024, 3, 31),
        existing_monthly_emi=Decimal("10000.00"),
        proposed_monthly_emi=Decimal("5000.00")
    )
    assert res["average_monthly_balance"] == "212039.47"
