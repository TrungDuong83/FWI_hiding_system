# -*- coding: utf-8 -*-
"""ds_features.py — recompute đặc trưng 9 dataset TỪ FILE THẬT + weight histogram 7 FIMI. Read-only."""
import os, json
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
D = os.path.join(ROOT, "datasets")
DSS = ["chess_fimi", "mushroom", "accident", "retail", "bms-pos", "kosarak", "chainstore", "mnc", "rtvcq"]

print("=== FEATURES (từ *_quantities.txt) ===")
print(f"{'dataset':12} {'#txn':>9} {'#item':>7} {'avglen':>7} {'maxlen':>6} {'density%':>8}")
feats = {}
for ds in DSS:
    items_all = set(); ntxn = 0; tot = 0; mx = 0
    for line in open(f"{D}/{ds}_quantities.txt"):
        line = line.strip()
        if not line:
            continue
        its = [p.split(":")[0] for p in line.split()]
        ntxn += 1; tot += len(its); mx = max(mx, len(its)); items_all.update(its)
    ni = len(items_all); avg = tot / ntxn; dens = 100 * avg / ni
    feats[ds] = dict(ntxn=ntxn, nitem=ni, avglen=round(avg, 2), maxlen=mx, density=round(dens, 3))
    print(f"{ds:12} {ntxn:>9} {ni:>7} {avg:>7.2f} {mx:>6} {dens:>8.3f}")

print("\n=== WEIGHT HISTOGRAM (7 FIMI, *_weights.txt raw int) ===")
for ds in ["chess_fimi", "mushroom", "accident", "retail", "bms-pos", "kosarak", "chainstore"]:
    vals = [int(l.split(":")[1]) for l in open(f"{D}/{ds}_weights.txt") if l.strip()]
    n = len(vals); h = Counter(vals)
    dist = " ".join(f"{v}:{100*h.get(v,0)/n:.1f}%" for v in range(1, 11))
    print(f"[{ds}] n={n} mean={sum(vals)/n:.2f} | {dist}")

json.dump(feats, open(f"{ROOT}/coordinator/.ds_features.json", "w"), indent=1)
print("\n(feats saved)")
