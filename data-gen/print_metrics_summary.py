import glob
import json
from collections import Counter, defaultdict

files = sorted(glob.glob('data/synthetic/applicants/*/ground_truth.json'))
clauses = ['ELIG-01', 'ELIG-02', 'FIN-01', 'FIN-02', 'FIN-03', 'FIN-04', 'FIN-05', 'FIN-06', 'FIN-07', 'DOC-02']
alone = Counter()
with_others = Counter()
clean = 0
archetypes = defaultdict(lambda: Counter())
near_threshold = []
stressed_records = []

for f in files:
    with open(f, 'r', encoding='utf-8') as fp:
        gt = json.load(fp)
    aid = gt['applicant_id']
    trig = gt.get('policy_clauses_triggered', [])
    arch = gt['archetype']
    dec = gt['expected_decision']
    archetypes[arch][dec] += 1
    if not trig:
        clean += 1
    elif len(trig) == 1:
        alone[trig[0]] += 1
    else:
        for c in trig:
            with_others[c] += 1

    if arch == "stressed":
        stressed_records.append((aid, dec, trig))

    if gt.get('near_threshold'):
        near_threshold.append(gt)

print(f"Total applicants: {len(files)}")
print(f"Clean (no clauses triggered): {clean}")
print("\n### CLAUSE COVERAGE MATRIX:")
print("| Clause | Alone (>=3) | With Others |")
print("|---|---|---|")
for c in clauses:
    print(f"| {c} | {alone[c]} | {with_others[c]} |")

nt_clauses = defaultdict(lambda: {'passing': 0, 'failing': 0})
for nt in near_threshold:
    c = nt['near_threshold_clause']
    s = nt['near_threshold_side']
    if 'pass' in s:
        nt_clauses[c]['passing'] += 1
    else:
        nt_clauses[c]['failing'] += 1

print("\n### NEAR-THRESHOLD TABLE:")
print("| ID | Archetype | Clause | Metric Value | Threshold | Margin | Side | Decision |")
print("|---|---|---|---|---|---|---|---|")
for nt in near_threshold:
    aid = nt['applicant_id']
    arch = nt['archetype']
    c = nt['near_threshold_clause']
    mv = nt['near_threshold_metric_value']
    th = nt['near_threshold_threshold']
    mg = nt['near_threshold_margin']
    sd = nt['near_threshold_side']
    dc = nt['expected_decision']
    print(f"| {aid} | {arch} | {c} | {mv} | {th} | {mg} | {sd} | {dc} |")

print(f"\nTotal near-threshold applicants: {len(near_threshold)}")
both_count = sum(1 for c, s in nt_clauses.items() if s['passing'] > 0 and s['failing'] > 0)
print(f"Distinct clauses with both passing and failing near-threshold: {both_count}")
for c, s in sorted(nt_clauses.items()):
    print(f"  {c}: just-passing={s['passing']}, just-failing={s['failing']}")

print("\n### DECISION DISTRIBUTION PER ARCHETYPE:")
print("| Archetype | APPROVE | REFER | DECLINE | Total |")
print("|---|---|---|---|---|")
for arch, decs in sorted(archetypes.items()):
    tot = sum(decs.values())
    print(f"| {arch} | {decs['APPROVE']} | {decs['REFER']} | {decs['DECLINE']} | {tot} |")

# Check stressed clause sets
stressed_combos = Counter()
for aid, dec, trig in stressed_records:
    stressed_combos[tuple(sorted(trig))] += 1
print(f"\nDistinct clause combinations among STRESSED applicants: {len(stressed_combos)}")
for combo, cnt in stressed_combos.items():
    print(f"  Count: {cnt:2d} | Clauses: {list(combo)}")
