"""
Bank Statement Generator for HDFC, SBI, and ICICI layouts.
Generates CSV files and deterministic PDF statements (using ReportLab invariant mode).
"""

import csv
import io
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def format_date_hdfc(d_str: str) -> str:
    # DD/MM/YYYY
    d = date.fromisoformat(d_str)
    return d.strftime("%d/%m/%Y")

def format_date_sbi(d_str: str) -> str:
    # DD Mon YYYY
    d = date.fromisoformat(d_str)
    return d.strftime("%d %b %Y")

def format_date_icici(d_str: str) -> str:
    # YYYY-MM-DD
    return d_str

class BankStatementGenerator:

    @staticmethod
    def generate_hdfc_csv(txns: List[Dict[str, Any]], open_bal: Decimal, out_path: Path):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        running = open_bal
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Narration", "Chq/Ref No", "Value Dt", "Withdrawal Amt", "Deposit Amt", "Closing Balance"])
            for idx, t in enumerate(txns):
                amt = Decimal(t["amount"])
                chq_ref = f"REF{100000 + idx}"
                d_fmt = format_date_hdfc(t["date"])
                if t["type"] == "CREDIT":
                    running += amt
                    writer.writerow([d_fmt, t["narration"], chq_ref, d_fmt, "", str(amt), str(running)])
                else:
                    running -= amt
                    writer.writerow([d_fmt, t["narration"], chq_ref, d_fmt, str(amt), "", str(running)])

    @staticmethod
    def generate_sbi_csv(txns: List[Dict[str, Any]], open_bal: Decimal, out_path: Path):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        running = open_bal
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Txn Date", "Value Date", "Description", "Ref No/Cheque No", "Debit", "Credit", "Balance"])
            for idx, t in enumerate(txns):
                amt = Decimal(t["amount"])
                chq_ref = f"SBIN{200000 + idx}"
                d_fmt = format_date_sbi(t["date"])
                if t["type"] == "CREDIT":
                    running += amt
                    writer.writerow([d_fmt, d_fmt, t["narration"], chq_ref, "", str(amt), str(running)])
                else:
                    running -= amt
                    writer.writerow([d_fmt, d_fmt, t["narration"], chq_ref, str(amt), "", str(running)])

    @staticmethod
    def generate_icici_csv(txns: List[Dict[str, Any]], open_bal: Decimal, out_path: Path):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        running = open_bal
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Tran Date", "Transaction Remarks", "Amount(INR)", "Cr/Dr", "Available Balance(INR)"])
            for t in txns:
                amt = Decimal(t["amount"])
                d_fmt = format_date_icici(t["date"])
                if t["type"] == "CREDIT":
                    running += amt
                    writer.writerow([d_fmt, t["narration"], str(amt), "CR", str(running)])
                else:
                    running -= amt
                    writer.writerow([d_fmt, t["narration"], str(amt), "DR", str(running)])

    @staticmethod
    def generate_pdf_statement(
        bank_name: str,
        applicant_name: str,
        account_no: str,
        txns: List[Dict[str, Any]],
        open_bal: Decimal,
        out_path: Path
    ):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # Invariant canvas for deterministic byte output
        c = canvas.Canvas(str(out_path), pagesize=letter, invariant=1, pageCompression=0)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, 750, f"{bank_name.upper()} BANK - STATEMENT OF ACCOUNT")
        c.setFont("Helvetica", 9)
        c.drawString(40, 735, f"Account Holder: {applicant_name}")
        c.drawString(40, 722, f"Account Number: {account_no} | Currency: INR")
        c.drawString(40, 709, f"Opening Balance: INR {open_bal}")

        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.line(40, 698, 570, 698)

        # Table Header
        c.setFont("Helvetica-Bold", 8)
        c.drawString(45, 685, "Date")
        c.drawString(110, 685, "Narration")
        c.drawString(350, 685, "Type")
        c.drawString(410, 685, "Amount (INR)")
        c.drawString(490, 685, "Balance (INR)")
        c.line(40, 678, 570, 678)

        y = 665
        running = open_bal
        c.setFont("Helvetica", 7)

        # Show representative transactions on first few pages
        for idx, t in enumerate(txns[:60]):  # cap per rendered doc
            amt = Decimal(t["amount"])
            if t["type"] == "CREDIT":
                running += amt
                t_type = "CR"
            else:
                running -= amt
                t_type = "DR"

            c.drawString(45, y, t["date"])
            narr = t["narration"][:45]
            c.drawString(110, y, narr)
            c.drawString(350, y, t_type)
            c.drawRightString(465, y, f"{amt:,.2f}")
            c.drawRightString(560, y, f"{running:,.2f}")

            y -= 14
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 7)
                y = 740

        c.save()
