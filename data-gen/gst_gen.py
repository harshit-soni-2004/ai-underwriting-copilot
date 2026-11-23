"""
GSTR-3B Monthly Return Summaries Generator.
Generates GSTR-3B monthly tax filing summaries (JSON and CSV).
"""

import csv
import json
from decimal import Decimal
from typing import List, Dict, Any
from pathlib import Path

class GstReturnGenerator:

    @staticmethod
    def generate_gstr3b_returns(
        applicant_id: str,
        gstin: str,
        annual_taxable_supplies: Decimal,
        start_date: str,
        end_date: str,
        out_json_path: Path,
        out_csv_path: Path
    ) -> List[Dict[str, Any]]:
        out_json_path.parent.mkdir(parents=True, exist_ok=True)
        # Distribute annual taxable supplies across 12 return periods
        monthly_base = (annual_taxable_supplies / Decimal("12")).quantize(Decimal("0.01"))

        returns = []
        months = [
            "2024-01", "2024-02", "2024-03", "2024-04",
            "2024-05", "2024-06", "2024-07", "2024-08",
            "2024-09", "2024-10", "2024-11", "2024-12"
        ]

        for m in months:
            taxable = monthly_base
            igst = (taxable * Decimal("0.08")).quantize(Decimal("0.01"))
            cgst = (taxable * Decimal("0.05")).quantize(Decimal("0.01"))
            sgst = (taxable * Decimal("0.05")).quantize(Decimal("0.01"))
            itc_avail = ((cgst + sgst + igst) * Decimal("0.75")).quantize(Decimal("0.01"))

            returns.append({
                "return_period": m,
                "gstin": gstin,
                "arn": f"AA{m.replace('-', '')}00123456",
                "status": "FILED",
                "outward_taxable_supplies": str(taxable),
                "igst_amount": str(igst),
                "cgst_amount": str(cgst),
                "sgst_amount": str(sgst),
                "eligible_itc": str(itc_avail),
                "filing_date": f"{m}-20"
            })

        # Save JSON
        with open(out_json_path, "w", encoding="utf-8") as f:
            json.dump({"applicant_id": applicant_id, "gstr3b_filings": returns}, f, indent=2)

        # Save CSV
        with open(out_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Period", "GSTIN", "ARN", "Taxable Supplies", "IGST", "CGST", "SGST", "Eligible ITC", "Status"])
            for r in returns:
                writer.writerow([
                    r["return_period"], r["gstin"], r["arn"],
                    r["outward_taxable_supplies"], r["igst_amount"],
                    r["cgst_amount"], r["sgst_amount"], r["eligible_itc"], r["status"]
                ])

        return returns
