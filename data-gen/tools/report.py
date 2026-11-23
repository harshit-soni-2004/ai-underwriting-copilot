"""
Dataset Integrity & Coverage Report Generator.
Reads all generated synthetic applicant ground_truth.json files and writes docs/dataset-report.md.
"""

import json
from pathlib import Path
from decimal import Decimal
from statistics import median
from collections import defaultdict, Counter

def generate_report(data_dir: str = "data/synthetic", output_file: str = "docs/dataset-report.md"):
    base_path = Path(data_dir) / "applicants"
    out_file = Path(output_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    applicants = []
    for app_dir in sorted(base_path.iterdir()):
        gt_path = app_dir / "ground_truth.json"
        if gt_path.exists():
            with open(gt_path, "r", encoding="utf-8") as f:
                applicants.append(json.load(f))

    if not applicants:
        print(f"No applicants found in {base_path}")
        return

    # 1. Decision distribution per archetype
    archetype_decisions = defaultdict(lambda: Counter())
    total_decisions = Counter()
    for app in applicants:
        arch = app["archetype"]
        dec = app["expected_decision"]
        archetype_decisions[arch][dec] += 1
        total_decisions[dec] += 1

    # 2. Clause coverage matrix
    clause_alone = Counter()
    clause_with_others = Counter()
    all_clauses = [
        "ELIG-01", "ELIG-02",
        "FIN-01", "FIN-02", "FIN-03", "FIN-04", "FIN-05", "FIN-06", "FIN-07",
        "DOC-02"
    ]

    for app in applicants:
        trig = app.get("policy_clauses_triggered", [])
        if len(trig) == 1:
            clause_alone[trig[0]] += 1
        elif len(trig) > 1:
            for c in trig:
                clause_with_others[c] += 1

    # 3. Near-threshold applicants
    nt_applicants = [a for a in applicants if a.get("near_threshold")]
    nt_both_sides = defaultdict(lambda: {"passing": 0, "failing": 0})
    for a in nt_applicants:
        c = a.get("near_threshold_clause")
        side = a.get("near_threshold_side")
        if side == "just-passing":
            nt_both_sides[c]["passing"] += 1
        elif side == "just-failing":
            nt_both_sides[c]["failing"] += 1

    both_sides_count = sum(1 for c, s in nt_both_sides.items() if s["passing"] > 0 and s["failing"] > 0)

    # 4. Metrics Min / Median / Max per archetype
    metrics_by_arch = defaultdict(lambda: defaultdict(list))
    for app in applicants:
        arch = app["archetype"]
        em = app["expected_metrics"]
        metrics_by_arch[arch]["cv"].append(float(em["cash_flow_volatility_cv"]))
        metrics_by_arch[arch]["top1"].append(float(em["counterparty_top1_share"]))
        metrics_by_arch[arch]["dscr"].append(float(em["dscr_proxy"]))
        metrics_by_arch[arch]["amb"].append(float(em["average_monthly_balance"]))
        metrics_by_arch[arch]["foir"].append(float(em["foir"]))
        metrics_by_arch[arch]["vintage"].append(int(app["vintage_months"]))

    # 5. Stressed combinations breakdown
    stressed_combos = Counter()
    for app in applicants:
        if app["archetype"] == "stressed":
            trig = tuple(sorted(app.get("policy_clauses_triggered", [])))
            stressed_combos[trig] += 1

    # Write Markdown Report
    lines = []
    lines.append("# MSME Dataset Integrity & Coverage Report")
    lines.append("")
    lines.append(f"**Total Applicants Generated:** {len(applicants)}")
    lines.append("")

    lines.append("## 1. Decision Distribution per Archetype")
    lines.append("")
    lines.append("| Archetype | Total | APPROVE | REFER | DECLINE |")
    lines.append("|:---|---:|---:|---:|---:|")
    for arch in sorted(archetype_decisions.keys()):
        decs = archetype_decisions[arch]
        tot = sum(decs.values())
        lines.append(f"| `{arch}` | {tot} | {decs['APPROVE']} | {decs['REFER']} | {decs['DECLINE']} |")
    lines.append(f"| **TOTAL** | **{len(applicants)}** | **{total_decisions['APPROVE']}** | **{total_decisions['REFER']}** | **{total_decisions['DECLINE']}** |")
    lines.append("")

    lines.append("## 2. Policy Clause Coverage Matrix")
    lines.append("")
    lines.append("Policy clauses must be triggered alone by at least 3 distinct applicants to guarantee isolated evaluation.")
    lines.append("")
    lines.append("| Clause ID | Description | Alone Count (>= 3) | With Others Count | Total Triggers |")
    lines.append("|:---|:---|---:|---:|---:|")
    clause_descriptions = {
        "ELIG-01": "Vintage >= 6m (DECLINE if <6m, REFER if 6-24m)",
        "ELIG-02": "Annual Turnover >= 25 Lakhs (DECLINE if <25L)",
        "FIN-01": "DSCR Proxy >= 1.25x (REFER if <1.25, DECLINE if <1.0)",
        "FIN-02": "AMB >= 10% of Proposed EMI (REFER if <10%)",
        "FIN-03": "Inward NACH/Cheque Dishonour = 0 (REFER if >0, DECLINE if >3)",
        "FIN-04": "FOIR <= 50.0% (REFER if >50%)",
        "FIN-05": "Top-1 Customer Inflow Concentration <= 40.0% (REFER if >40%)",
        "FIN-06": "Cash Flow Volatility CV <= 0.6000 (REFER if >0.60)",
        "FIN-07": "Round-Trip Excluded Credits <= 2.0% (REFER if >2%)",
        "DOC-02": "Bank vs GSTR-3B Turnover Discrepancy within [0.80, 1.20] (REFER if outside)"
    }
    for c in all_clauses:
        alone = clause_alone[c]
        others = clause_with_others[c]
        tot = alone + others
        desc = clause_descriptions.get(c, "")
        lines.append(f"| `{c}` | {desc} | **{alone}** | {others} | {tot} |")
    lines.append("")

    lines.append("## 3. Redefined Near-Threshold Applicants")
    lines.append("")
    lines.append("Near-threshold rule: $|\\text{metric} - \\text{threshold}| \\le 10\\% \\times \\text{threshold}$ (or $\\pm 1$ month for vintage).")
    lines.append("Margin sign convention: **Positive** ($>0$) = passing side, **Negative** ($<0$) = failing side.")
    lines.append("")
    lines.append(f"- **Total Near-Threshold Applicants:** {len(nt_applicants)} (Minimum requirement: $\\ge 10$)")
    lines.append(f"- **Clauses Covered on Both Sides:** {both_sides_count} (Minimum requirement: $\\ge 5$)")
    lines.append("")
    lines.append("| Clause | Passing Applicants | Failing Applicants | Both Sides Covered? |")
    lines.append("|:---|---:|---:|:---:|")
    for c in all_clauses:
        p_cnt = nt_both_sides[c]["passing"]
        f_cnt = nt_both_sides[c]["failing"]
        status = "YES" if (p_cnt > 0 and f_cnt > 0) else "NO"
        lines.append(f"| `{c}` | {p_cnt} | {f_cnt} | {status} |")
    lines.append("")

    lines.append("### Detailed Near-Threshold Roster")
    lines.append("")
    lines.append("| Applicant ID | Archetype | Clause | Metric Value | Threshold | Margin | Side | Decision |")
    lines.append("|:---|:---|:---|---:|---:|---:|:---|:---|")
    for a in sorted(nt_applicants, key=lambda x: x["applicant_id"]):
        app_id = a["applicant_id"]
        arch = a["archetype"]
        c = a["near_threshold_clause"]
        m_val = a["near_threshold_metric_value"]
        thresh = a["near_threshold_threshold"]
        margin = a["near_threshold_margin"]
        side = a["near_threshold_side"]
        dec = a["expected_decision"]
        lines.append(f"| `{app_id}` | `{arch}` | `{c}` | {m_val} | {thresh} | `{margin}` | `{side}` | `{dec}` |")
    lines.append("")

    lines.append("## 4. Key Financial Metrics Range (Min / Median / Max)")
    lines.append("")
    lines.append("| Archetype | Metric | Min | Median | Max |")
    lines.append("|:---|:---|---:|---:|---:|")
    metric_labels = [
        ("cv", "Volatility CV"),
        ("top1", "Top-1 Share"),
        ("dscr", "DSCR Proxy"),
        ("amb", "AMB (INR)"),
        ("foir", "FOIR"),
        ("vintage", "Vintage (months)")
    ]
    for arch in sorted(metrics_by_arch.keys()):
        for m_key, m_label in metric_labels:
            vals = metrics_by_arch[arch][m_key]
            min_v = f"{min(vals):.4f}" if m_key != "vintage" and m_key != "amb" else (f"{min(vals):,.2f}" if m_key == "amb" else f"{min(vals)}")
            med_v = f"{median(vals):.4f}" if m_key != "vintage" and m_key != "amb" else (f"{median(vals):,.2f}" if m_key == "amb" else f"{median(vals):.1f}")
            max_v = f"{max(vals):.4f}" if m_key != "vintage" and m_key != "amb" else (f"{max(vals):,.2f}" if m_key == "amb" else f"{max(vals)}")
            lines.append(f"| `{arch}` | {m_label} | {min_v} | {med_v} | {max_v} |")
    lines.append("")

    lines.append("## 5. Stressed Archetype Combinations Breakdown")
    lines.append("")
    lines.append("Asserts multiple distinct clause failure profiles among stressed applicants:")
    lines.append("")
    lines.append("| Count | Triggered Clause Combination | Decision |")
    lines.append("|---:|:---|:---|")
    for s_set, count in stressed_combos.items():
        clauses_str = ", ".join(f"`{c}`" for c in s_set)
        dec = "DECLINE" if any(c in ["FIN-01", "FIN-03"] for c in s_set) else "REFER"
        lines.append(f"| {count} | {clauses_str} | `{dec}` |")
    lines.append("")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Successfully generated report at {out_file}")

if __name__ == "__main__":
    generate_report()
