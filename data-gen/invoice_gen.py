"""
Commercial Invoice Generator for MSME applicants.
Generates realistic Indian B2B tax invoices with GSTIN, HSN codes, and taxes (ReportLab invariant mode).
"""

from decimal import Decimal
from typing import Dict, Any, List
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class InvoiceGenerator:

    @staticmethod
    def generate_invoice_pdf(
        invoice_number: str,
        invoice_date: str,
        seller_name: str,
        seller_gstin: str,
        buyer_name: str,
        buyer_gstin: str,
        items: List[Dict[str, Any]],
        out_path: Path
    ):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(out_path), pagesize=letter, invariant=1, pageCompression=0)

        # Header
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, 750, "TAX INVOICE")
        c.setFont("Helvetica", 8)
        c.drawString(40, 735, f"Invoice No: {invoice_number}")
        c.drawString(40, 722, f"Invoice Date: {invoice_date}")

        # Seller Box
        c.rect(40, 640, 250, 75)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(45, 702, "SUPPLIER / SELLER:")
        c.setFont("Helvetica", 8)
        c.drawString(45, 688, seller_name[:35])
        c.drawString(45, 674, f"GSTIN: {seller_gstin}")
        c.drawString(45, 660, "State: Maharashtra (Code: 27)")

        # Buyer Box
        c.rect(310, 640, 250, 75)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(315, 702, "BILL TO / BUYER:")
        c.setFont("Helvetica", 8)
        c.drawString(315, 688, buyer_name[:35])
        c.drawString(315, 674, f"GSTIN: {buyer_gstin}")
        c.drawString(315, 660, "Place of Supply: Inter-State / Intra-State")

        # Table
        c.line(40, 625, 560, 625)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(45, 613, "Item Description")
        c.drawString(240, 613, "HSN")
        c.drawString(300, 613, "Qty")
        c.drawString(360, 613, "Rate (INR)")
        c.drawString(470, 613, "Taxable Total (INR)")
        c.line(40, 605, 560, 605)

        y = 590
        subtotal = Decimal("0.00")
        c.setFont("Helvetica", 8)

        for item in items:
            desc = item.get("description", "Precision Components")
            hsn = item.get("hsn", "8483")
            qty = Decimal(str(item.get("qty", 10)))
            rate = Decimal(str(item.get("rate", 5000)))
            total = qty * rate
            subtotal += total

            c.drawString(45, y, desc[:30])
            c.drawString(240, y, hsn)
            c.drawString(300, y, str(qty))
            c.drawRightString(420, y, f"{rate:,.2f}")
            c.drawRightString(550, y, f"{total:,.2f}")
            y -= 16

        c.line(40, y, 560, y)
        y -= 18

        # Taxes: 18% GST (CGST 9% + SGST 9% or IGST 18%)
        gst_tax = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
        grand_total = subtotal + gst_tax

        c.setFont("Helvetica-Bold", 8)
        c.drawString(340, y, "Taxable Amount:")
        c.drawRightString(550, y, f"INR {subtotal:,.2f}")
        y -= 14
        c.drawString(340, y, "GST @ 18%:")
        c.drawRightString(550, y, f"INR {gst_tax:,.2f}")
        y -= 14
        c.drawString(340, y, "Total Invoice Amount:")
        c.drawRightString(550, y, f"INR {grand_total:,.2f}")

        # Terms
        c.setFont("Helvetica", 7)
        c.drawString(40, 100, "Terms & Conditions: Payment due within 30 days of invoice presentation.")
        c.drawString(40, 88, "Authorized Signatory: Computer generated invoice, physical signature not required.")
        c.save()
